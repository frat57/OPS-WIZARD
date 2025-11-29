# DB Schema — Core tables for Fraud Wizard

This document describes the initial core schema used by the AI Ops Wizard MVP. The PostgreSQL schema is intentionally small and normalized where necessary — ready to be extended as requirements evolve.

Design goals:
- Keep queries simple for typical fraud flows (lookups by id, recent alerts, outstanding investigations)
- Provide JSONB fields for raw payloads and LLM explanations for flexibility
- Include audit trail and integration table placeholders

Tables (initial):

1) users
 - id TEXT PRIMARY KEY (UUID or external SSO id)
 - email TEXT UNIQUE
 - name TEXT
 - role TEXT (e.g., admin, analyst, ops)
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
 - updated_at TIMESTAMP WITH TIME ZONE

2) transactions
 - id TEXT PRIMARY KEY
 - user_id TEXT NULL (references users.id)
 - amount NUMERIC(18,4)
 - currency TEXT
 - status TEXT (eg: pending, settled, failed)
 - raw_payload JSONB
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()

3) alerts
 - id TEXT PRIMARY KEY
 - transaction_id TEXT NULL (references transactions.id)
 - score REAL NOT NULL
 - reasoning TEXT
 - suggested_action TEXT
 - explanation JSONB
 - status TEXT (eg: open, triaged, closed)
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()

4) investigations
 - id TEXT PRIMARY KEY
 - alert_id TEXT NOT NULL (references alerts.id)
 - assigned_to TEXT NULL (users.id)
 - status TEXT (eg: open, in_progress, resolved)
 - notes TEXT
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
 - closed_at TIMESTAMP WITH TIME ZONE NULL

5) decisions
 - id TEXT PRIMARY KEY
 - investigation_id TEXT NOT NULL (references investigations.id)
 - actor TEXT NULL (users.id)
 - action_taken TEXT
 - comment TEXT
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()

6) integrations
 - id TEXT PRIMARY KEY
 - name TEXT
 - type TEXT (eg: slack, crm, webhook)
 - config JSONB
 - enabled BOOLEAN DEFAULT true
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()

7) audit_logs
 - id TEXT PRIMARY KEY
 - entity_type TEXT
 - entity_id TEXT
 - actor TEXT
 - operation TEXT
 - details JSONB
 - created_at TIMESTAMP WITH TIME ZONE DEFAULT now()

Indexes to add later (suggestions):
- alerts (status)
- alerts (transaction_id)
- transactions (user_id)
- investigations (assigned_to, status)

This design allows n8n to create alerts and send them to the AI Core for analysis; the resulting alerts are persisted and can be triaged in the Dashboard.
