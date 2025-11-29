from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Tuple
from datetime import datetime, timezone
import json
import random
import os
import asyncio
import asyncpg
import requests

app = FastAPI(title="AI Ops Wizard - API (MVP)")

# CORS: allow frontend dev (localhost:3000) and any other dev origin we expect.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # allow container/frontend internal address for dev (if ever fetching from browser inside container)
    "http://api:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins + ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TransactionData(BaseModel):
    """Normalized transaction payload for the Fraud Wizard.

    This model intentionally keeps fields generic so that n8n can map different
    upstream event formats (payment, login, KYC, etc.) into a single schema.
    """

    amount: float
    currency: str
    customer_id: Optional[str] = None
    transaction_id: Optional[str] = None
    merchant: Optional[str] = None
    merchant_id: Optional[str] = None
    channel: Optional[str] = None  # e.g. web, mobile, pos, api
    timestamp: Optional[str] = None
    ip_address: Optional[str] = None
    ip_country: Optional[str] = None
    device_id: Optional[str] = None
    user_agent: Optional[str] = None
    previous_tx_count_24h: Optional[int] = None
    previous_chargebacks_90d: Optional[int] = None


class ExplainEntry(BaseModel):
    """Feature contribution used for explainability in the Fraud Wizard."""

    feature: str
    importance: float


class ScoringResult(BaseModel):
    """Intermediate rule/ML-based scoring result before LLM reasoning.

    This keeps the pure numeric risk model separate from the natural language
    explanation/wizard steps that the LLM generates.
    """

    score: float
    risk_level: str  # LOW | MEDIUM | HIGH
    suggested_action: str  # ALLOW | REVIEW | BLOCK | HOLD_AND_MANUAL_REVIEW etc.
    rules_fired: List[str]


class WizardStep(BaseModel):
    """One step in the Fraud Wizard guidance flow for the human analyst."""

    id: str
    title: str
    message: str
    severity: str  # e.g. HIGH | MEDIUM | LOW | INFO


class AnalysisResult(BaseModel):
    """Final analysis payload returned under `data` in the /analyze envelope."""

    id: Optional[str]
    score: float
    risk_level: str
    reasoning: str
    suggested_action: str
    wizard_steps: List[WizardStep]
    explanation: List[ExplainEntry]


@app.get("/health")
async def health():
    info = {"status": "ok"}
    # simple DB check
    try:
        if DB_POOL is None:
            info["db"] = "disconnected"
        else:
            async with DB_POOL.acquire() as conn:
                res = await conn.fetchval('SELECT 1')
                info["db"] = "ok" if res == 1 else f"unexpected:{res}"
    except Exception as e:
        info["db"] = f"error: {e}"

    return info


@app.get("/alerts")
async def list_alerts(limit: int = 50):
    """Return recent entries from fraud_logs (latest first)."""
    if DB_POOL is None:
        return {"error": "db_unavailable", "alerts": []}

    try:
        async with DB_POOL.acquire() as conn:
            rows = await conn.fetch(
                "SELECT transaction_id, risk_score, ai_reason, suggested_action, created_at FROM fraud_logs ORDER BY created_at DESC LIMIT $1",
                limit,
            )
            out = [dict(r) for r in rows]
            return out
    except Exception as e:
        return {"error": str(e), "alerts": []}


# -------------------------
# Fraud Wizard core logic (scoring + LLM)
# -------------------------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
FRAUD_WIZARD_MODEL = os.environ.get("FRAUD_WIZARD_MODEL", "gpt-4o-mini")

def score_transaction(tx: TransactionData) -> ScoringResult:
    """Lightweight rule-based scorer for Fraud Wizard.

    This is deliberately simple for the MVP. In a real system this would be
    replaced by a trained model (e.g., XGBoost, deep model, or feature service).

    Rules (MVP):
    - High amount and recent activity -> HIGH risk.
    - Private/local IP (192.x) and low amount -> LOW risk.
    - Otherwise -> MEDIUM risk.
    """

    rules: List[str] = []
    score = 0.5

    if tx.amount is not None and tx.amount > 5000:
        score = 0.9
        rules.append("amount_gt_5000")
    if tx.previous_tx_count_24h and tx.previous_tx_count_24h > 20:
        score = max(score, 0.85)
        rules.append("high_velocity_24h")
    if tx.ip_address and tx.ip_address.startswith("192.") and tx.amount <= 100:
        score = min(score, 0.15)
        rules.append("local_ip_low_amount")
    if not rules:
        rules.append("default_rule")

    if score >= 0.8:
        risk_level = "HIGH"
        suggested_action = "BLOCK"
    elif score <= 0.2:
        risk_level = "LOW"
        suggested_action = "ALLOW"
    else:
        risk_level = "MEDIUM"
        suggested_action = "REVIEW"

    return ScoringResult(
        score=float(score),
        risk_level=risk_level,
        suggested_action=suggested_action,
        rules_fired=rules,
    )

def _fallback_reasoning_and_steps(scoring: ScoringResult, tx: TransactionData) -> Tuple[str, List[WizardStep]]:
    """Deterministic explanation when LLM is unavailable.

    This keeps the Fraud Wizard usable even without external AI.
    """

    reason_parts = [
        f"Risk level is {scoring.risk_level} because rules fired: {', '.join(scoring.rules_fired)}.",
    ]
    if tx.amount is not None:
        reason_parts.append(f"Transaction amount is {tx.amount} {tx.currency}.")
    if tx.ip_country:
        reason_parts.append(f"IP country is {tx.ip_country}.")

    reasoning = " ".join(reason_parts)

    steps = [
        WizardStep(
            id="initial_assessment",
            title="İlk risk değerlendirmesi",
            message=reasoning,
            severity="HIGH" if scoring.risk_level == "HIGH" else ("LOW" if scoring.risk_level == "LOW" else "MEDIUM"),
        ),
        WizardStep(
            id="next_best_action",
            title="Önerilen sonraki adım",
            message=(
                "İşlemi bloklayın ve müşteriye risk iletişimi yapın."
                if scoring.suggested_action == "BLOCK"
                else "İşlemi bekletin ve ek doğrulama isteyin."
                if scoring.suggested_action == "REVIEW"
                else "İşlemi onaylayın ancak izlemeye devam edin."
            ),
            severity="INFO",
        ),
    ]

    return reasoning, steps


def call_llm_for_wizard(tx: TransactionData, scoring: ScoringResult) -> Tuple[str, List[WizardStep]]:
    """Call LLM to generate human-friendly reasoning and wizard steps.

    Returns (reasoning, wizard_steps). If the LLM or API key is not
    available, falls back to a deterministic explanation.
    """

    if not OPENAI_API_KEY:
        return _fallback_reasoning_and_steps(scoring, tx)

    prompt_payload = {
        "transaction": tx.dict(),
        "scoring": scoring.dict(),
    }

    system_msg = (
        "You are a Fraud Wizard assistant for a fraud detection dashboard. "
        "Your job is to explain WHY a transaction is risky or safe and to "
        "propose clear next steps for a human analyst. Always reply ONLY "
        "with a single JSON object matching the given schema. Do not add "
        "any extra text. Language for end-user messages should be Turkish."
    )

    user_msg = (
        "Aşağıda normalize edilmiş bir işlem (transaction) ve ona ait risk "
        "skoru / kurallar var. Lütfen bunlara göre kısa ama iş anlamında "
        "açıklayıcı bir özet üret ve wizard adımları tanımla.\n\n"
        f"PAYLOAD_JSON: {json.dumps(prompt_payload, ensure_ascii=False)}\n\n"
        "Dönüş formatın tam olarak şu JSON şemasında olmalı:\n"
        "{\n"
        "  \"reasoning\": \"...neden risk yüksek/orta/düşük...\",\n"
        "  \"wizard_steps\": [\n"
        "    {\n"
        "      \"id\": \"initial_assessment\",\n"
        "      \"title\": \"Kısa başlık\",\n"
        "      \"message\": \"Operasyon ekibine açıklama metni\",\n"
        "      \"severity\": \"HIGH|MEDIUM|LOW|INFO\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
    )

    try:
        resp = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": FRAUD_WIZARD_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                "temperature": 0.2,
            },
            timeout=20,
        )
        resp.raise_for_status()
        body = resp.json()
        content = body["choices"][0]["message"]["content"]

        parsed = json.loads(content)
        reasoning = str(parsed.get("reasoning") or "")
        steps_raw = parsed.get("wizard_steps") or []

        steps: List[WizardStep] = []
        for s in steps_raw:
            try:
                steps.append(
                    WizardStep(
                        id=str(s.get("id") or "step"),
                        title=str(s.get("title") or "Adım"),
                        message=str(s.get("message") or ""),
                        severity=str(s.get("severity") or "INFO"),
                    )
                )
            except Exception:
                continue

        if not reasoning or not steps:
            return _fallback_reasoning_and_steps(scoring, tx)

        return reasoning, steps

    except Exception:
        # Any failure in LLM path falls back to deterministic wizard.
        return _fallback_reasoning_and_steps(scoring, tx)


@app.post("/analyze")
async def analyze(tx: TransactionData) -> dict:
    """AI-driven Fraud Wizard analysis endpoint.

    Business logic (MVP):
    - Normalize transaction into `TransactionData`.
    - Run a lightweight rule-based scorer to compute numeric risk.
    - Call an LLM to turn features + rules into human-friendly reasoning and
      wizard steps (the "Wizard" that guides the analyst).

    Response contract for n8n:
    {
      "data": {
        "transaction": { ...TransactionData... },
        "id": null,
        "score": 0.87,
        "risk_level": "HIGH",
        "reasoning": "...",
        "suggested_action": "BLOCK|REVIEW|ALLOW|HOLD_AND_MANUAL_REVIEW",
        "wizard_steps": [ ... ],
        "explanation": [ {"feature": "amount", "importance": 0.62}, ... ]
      },
      "meta": {
        "engine_version": "fraud-wizard-mvp-1",
        "rules_fired": ["amount_gt_5000", ...],
        "llm_model": "gpt-4o-mini",
        "timestamp": "2025-01-01T00:00:00Z",
        "request_id": "req-123456"
      },
      "error": null | { "code": "...", "message": "..." }
    }
    """

    try:
        scoring = score_transaction(tx)
        reasoning, wizard_steps = call_llm_for_wizard(tx, scoring)

        analysis = AnalysisResult(
            id=None,
            score=scoring.score,
            risk_level=scoring.risk_level,
            reasoning=reasoning,
            suggested_action=scoring.suggested_action,
            wizard_steps=wizard_steps,
            explanation=[
                ExplainEntry(
                    feature="amount",
                    importance=min(abs(tx.amount or 0) / 10000.0, 1.0)
                    if tx.amount is not None
                    else 0.0,
                ),
                ExplainEntry(
                    feature="ip_address",
                    importance=0.2 if tx.ip_address else 0.0,
                ),
            ],
        )

        envelope = {
            "data": {
                "transaction": tx.dict(),
                **analysis.dict(),
            },
            "meta": {
                "engine_version": "fraud-wizard-mvp-1",
                "rules_fired": scoring.rules_fired,
                "llm_model": FRAUD_WIZARD_MODEL if OPENAI_API_KEY else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": f"req-{random.randint(100000, 999999)}",
            },
            "error": None,
        }

        # persist the result into fraud_logs table (best-effort)
        try:
            if DB_POOL is not None:
                async with DB_POOL.acquire() as conn:
                    await conn.execute(
                        "INSERT INTO fraud_logs(id, transaction_id, risk_score, ai_reason, suggested_action) VALUES($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING",
                        f"log-{random.randint(100000,999999)}",
                        tx.transaction_id or f"tx-{random.randint(100000,999999)}",
                        float(scoring.score),
                        reasoning,
                        scoring.suggested_action,
                    )
        except Exception:
            # best-effort swallow for MVP
            pass

        return envelope

    except Exception as e:
        # Hard failure path: still return envelope with error for n8n.
        error_envelope = {
            "data": None,
            "meta": {
                "engine_version": "fraud-wizard-mvp-1",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "error": {
                "code": "analyze_unexpected_error",
                "message": str(e),
            },
        }
        return JSONResponse(status_code=500, content=error_envelope)


# -------------------------
# DB connection management (tiny, MVP-friendly)
# -------------------------
DB_POOL: Optional[asyncpg.pool.Pool] = None


@app.on_event("startup")
async def startup_db():
    global DB_POOL
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        # try a default local URL for dev
        DATABASE_URL = "postgres://aiops:aiops_password@postgres:5432/aiops_db"

    try:
        DB_POOL = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=5)
        # ensure minimal table exists
        async with DB_POOL.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id TEXT PRIMARY KEY,
                  payload JSONB,
                  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                )
                """
            )
    except Exception:
        DB_POOL = None


@app.on_event("shutdown")
async def shutdown_db():
    global DB_POOL
    try:
        if DB_POOL is not None:
            await DB_POOL.close()
    finally:
        DB_POOL = None
