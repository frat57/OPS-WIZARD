# Frontend (Next.js) — minimal dashboard

This is a very small Next.js (App Router) scaffold intended only to demonstrate integration with the AI Core and n8n webhook.

How to run locally:

1. cd frontend
2. npm install
3. npm run dev

The demo page lets you craft an event and either call the backend directly (`/analyze`) or forward the event to the n8n webhook (by default `http://localhost:5678/webhook/fraud-webhook`).

Set env variables to override targets: `NEXT_PUBLIC_BACKEND_URL`, `NEXT_PUBLIC_N8N_WEBHOOK`.
