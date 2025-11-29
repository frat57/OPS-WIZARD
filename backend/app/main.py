from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import random
import os
import asyncio
import asyncpg

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
    amount: float
    currency: str
    merchant: Optional[str] = None
    timestamp: Optional[str] = None
    ip_address: Optional[str] = None
    customer_id: Optional[str] = None


class ExplainEntry(BaseModel):
    feature: str
    importance: float


class AnalysisResult(BaseModel):
    id: Optional[str]
    score: float
    reasoning: str
    suggested_action: str
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


@app.post("/analyze")
async def analyze(tx: TransactionData):
    """Rule-based mock analysis endpoint.

    Business logic (simple rules for MVP):
    - If amount > 5000 => high risk
    - If ip_address starts with '192.' => low risk (local network)
    - Otherwise => medium risk

    Returns structured JSON: { risk_score, reason, suggested_action }
    """

    # rule-based scoring
    if tx.amount is not None and tx.amount > 5000:
        score = 0.9
        reason = "High amount"
    elif tx.ip_address and tx.ip_address.startswith("192."):
        score = 0.1
        reason = "Local network"
    else:
        score = 0.5
        reason = "Default risk"

    # map score to suggested action
    if score >= 0.9:
        action = "BLOCK"
    elif score <= 0.1:
        action = "ALLOW"
    else:
        action = "REVIEW"

    result = {"risk_score": float(score), "reason": reason, "suggested_action": action}

    # persist the result into fraud_logs table (best-effort)
    try:
        if DB_POOL is not None:
            async with DB_POOL.acquire() as conn:
                await conn.execute(
                    "INSERT INTO fraud_logs(id, transaction_id, risk_score, ai_reason, suggested_action) VALUES($1, $2, $3, $4, $5) ON CONFLICT (id) DO NOTHING",
                    f"log-{random.randint(100000,999999)}",
                    f"tx-{random.randint(100000,999999)}",
                    float(score),
                    reason,
                    action,
                )
    except Exception:
        # best-effort swallow for MVP
        pass

    return result


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
