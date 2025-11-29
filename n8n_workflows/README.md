# n8n workflows — example

This folder contains an example n8n workflow export demonstrating the ingest -> call AI -> branch pattern.

File: `example_fraud_workflow.json` — high-level flow:

- Webhook In (POST /webhook/fraud-webhook)
- Set Meta (normalize incoming payload)
- Call AI-Core (/analyze)
- Branch based on `suggested_action` or `score` (HOLD, MANUAL_REVIEW, AUTO_APPROVE)
- Example actions: Notify Slack or return response to source

How to import into n8n (local UI):

1. Open n8n UI on http://localhost:5678
2. Go to Workflows > Import
3. Paste the JSON in `example_fraud_workflow.json` or upload the file
4. Adjust node URLs (the HTTP Request node references `http://api:8000/analyze` for compose) — set to `http://host.docker.internal:8000/analyze` if you use Docker Desktop and want to reach the host from a container.

Notes:
- This is an example to show how to branch on `suggested_action`; replace the Slack/HTTP nodes with your real downstream integrations.
- For production, secure your webhook and n8n instance and manage secrets via Vault / Kubernetes secrets.

## Advanced workflow

- `advanced_fraud_workflow.json` illustrates a safer production-ready pattern:
	- Rate limiting / sequential execution (basic example with Wait node)
	- Retry pattern on failed downstream calls (Wait + retry loop)
	- Notifications to Slack + placeholder HTTP request to CRM
	- Error branching to avoid silent failures

Import the advanced file the same way as above and adjust the CRM URL / Slack credentials for your environment.
