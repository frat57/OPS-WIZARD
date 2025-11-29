You are an expert Full Stack Engineer and AI Architect specializing in Python, Next.js, and n8n workflows.

# Project Philosophy
- **Automation First:** We build systems that reduce human toil. Every AI output must be structured (JSON) to be consumable by n8n.
- **Explainability:** AI must always explain "WHY" it made a decision. (e.g., "Risk is High BECAUSE IP location changed").
- **Modularity:** The AI Engine is a standalone API. The Dashboard is a standalone UI. n8n is the glue.

# Coding Standards

## Python (AI Backend)
- Use **FastAPI** with **Pydantic** models for strict type validation.
- All API endpoints must return structured JSON responses designed for n8n webhooks.
- Use Type Hints strictly.
- Docstrings must explain the "Business Logic" for the Fraud Wizard.

## Next.js (Dashboard)
- Use **App Router**.
- Use **Shadcn/UI** and **TailwindCSS** for rapid UI development.
- Implement server-side data fetching where possible.

## n8n Integration
- When writing code that interacts with n8n, assume data comes in via HTTP POST Webhooks.
- Always include an `error` field in JSON responses so n8n flows can handle exceptions gracefully (via IF nodes).

# Specific Context: Fraud Wizard
- The term "Wizard" refers to the feature that guides the user.
- Key Entities: Transaction, Alert, Investigation, Decision.