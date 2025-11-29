# AI-Powered Operations Wizard — MVP (ops-wizard)

Bu klasör, MVP için hızlı bir başlangıç sağlayan minimal yapı ve docker-compose örneğini içerir. Amaç: Fraud Detection / Risk Compliance için "AI Core + Automation + Dashboard" mimarisi

## 1) Monorepo / proje yapısı (öneri)

- ops-wizard/
  - docker-compose.yml         # n8n, Postgres, backend(api) için
  - backend/                   # FastAPI (AI Core API) örneği
    - Dockerfile
    - requirements.txt
    - app/
      - main.py                # health + analyze (stub)

Bu yapı MVP için yeterli – gerçek prod'da AI core, model storage, XAI pipeline, auth, secrets ayrı servisler olmalı.

## 2) Veri akışı (örnek: Fraud Alert)

1. Ham veri (ör. ödeme event'i, e-posta, log) kaynak sistemlere (ör. payment gateway) ulaşır.
2. Bu veri bir webhook veya ETL enpoint ile n8n'e gelir (n8n Workflows giriş noktası).
3. n8n workflow veriyi temizler / zenginleştirir / normalleştirir (ör. geo IP, device fingerprint) ve `POST` ile AI Core (FastAPI) `/analyze` endpoint'ine gönderir.
4. AI Core:
   - hızlı scoring için lokal ML model veya kuralları çalıştırır (score)
   - karmaşık durumlarda LLM (OpenAI/Claude) çağırarak doğal dilde analiz ve öneri üretir
   - XAI bileşeni (feature importances, example-based justification) sonuçla beraber döner
5. API yanıtı (score + reasoning + suggested_action + explanation) n8n'e döner.
6. n8n bu çıktıya göre branch'ler: otomatik blok, beklet veya insan müdahalesi gerektiriyor ise dashboard'a ve Slack/CRM'e bildirim atar.
7. Dashboard (Next.js) n8n üzerinden veya API'den verileri çekip gösterir; kullanıcı manuel onay/ret yapıp n8n üzerinden follow-up aksiyon tetikler (ör. CRM case, müşteri araması).

## 3) "Wizard" mantığı — API sözleşmesi (MVP)

API, sadece bir sayısal skor dönmez; aynı zamanda insanın anlayacağı bir "reasoning" ve n8n'in kolayca tüketebileceği bir `suggested_action` döndürür.

Response (örnek):
```json
{
  "id": "evt-123",
  "score": 0.87,
  "reasoning": "Model observed high velocity + billing/shipping mismatch...",
  "suggested_action": "HOLD_TRANSACTION_AND_MANUAL_REVIEW",
  "explanation": [ { "feature": "tx_velocity", "importance": 0.62 }, ... ]
}
```

Bu sayede n8n workflow'ları yanıtı parse edip, action enum'una göre branch'leyebilir veya LLM önerisini direkt CRM/SLA eylem talimatına çevirip downstream sistemlere aktarabilir.

## 4) Nasıl çalıştırırsınız (lokal / MVP)

Kök dizinde (bu ops-wizard klasörü) aşağıyı çalıştırın:

```powershell
cd ops-wizard
# kopyalayıp .env içinde gerekli değişiklikleri yapın (varsa):
cp .env.example .env

docker compose up --build
```

- n8n: http://localhost:5678 (basic auth: admin / password)
- API: http://localhost:8000
- Postgres admin UI (Adminer): http://localhost:8080 (db: aiops / aiops_password)
 - Frontend: http://localhost:3000 (if running via docker-compose)

Note: migrations are managed with Alembic (see `backend/alembic`). In local or CI you can run:

```powershell
# run migrations from repo root
docker compose run --rm api alembic -c backend/alembic.ini upgrade head
```

CI: a small GitHub Actions workflow runs migrations and a /health smoke test on push (see `.github/workflows/ci.yml`).

Örnek test: curl ile analiz isteği

```bash
curl -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"id":"evt-1","payload": {"amount": 102.5}}'
```

Ek notlar:
- Backend `app/main.py` artık docker compose sağladığı `DATABASE_URL` üzerinden postgres'e bağlanmaya çalışır ve minimal `events` tablosunu oluşturur.
- Prod için: secrets yönetimi, k8s manifests ve ayrı migration pipeline (Alembic) eklenmelidir.

### Önerilen yerel çalışma adımları (örnek sıralama)

1. Repo kökünde bir `.env` oluşturun (kopyala: `cp .env.example .env`) ve gerekli değişiklikleri yapın.
2. Docker-compose ile core stack'i ayağa kaldırın:

```powershell
docker compose up --build
```

3. n8n UI'ye gidin (http://localhost:5678) ve `n8n_workflows/example_fraud_workflow.json` dosyasını import edin (Workflows > Import). Düzenlemeden önce HTTP Request node içindeki URL'yi istediğiniz hedefe göre kontrol edin (ör. host.docker.internal veya api:8000).

4. Yerel demo frontend'i çalıştırmak isterseniz ayrı terminde aşağıyı çalıştırın:

```powershell
cd frontend
npm install
npm run dev
```

5. Dashboard demo sayfasından bir event gönderin veya `curl` ile /analyze endpoint'ine istek gönderin.

---

### Quick notes — entegrasyon

- Frontend demo sayfası `NEXT_PUBLIC_BACKEND_URL` ve `NEXT_PUBLIC_N8N_WEBHOOK` ile hedefleri değiştirilebilir.
- n8n workflow örneğinde webhook path `fraud-webhook` olarak geçer; n8n import ettikten sonra webhook'u aktif hale getirin ve frontend'den veya dış kaynaklardan test gönderin.


---
Sonraki adım olarak:
- n8n workflow örnekleri (ops-wizard/n8n_workflows/),
- Auth / secrets yönetimi (env/.env, Vault),
- Basit Next.js (dashboard) örneği ekleyip webhook ile entegre edebilirim.
 - n8n workflow örnekleri (ops-wizard/n8n_workflows/) — bakınız `example_fraud_workflow.json` ve README
 - n8n workflow örnekleri (ops-wizard/n8n_workflows/) — bakınız `example_fraud_workflow.json`, `advanced_fraud_workflow.json` ve README
 - Basit Next.js (dashboard) örneği (ops-wizard/frontend/) — lokal olarak çalıştırmak için `cd frontend` -> `npm install` -> `npm run dev`
