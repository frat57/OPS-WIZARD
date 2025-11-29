#!/usr/bin/env bash
# Import workflows into local n8n instance (docker-compose) via REST API
# Usage: ./scripts/n8n_import_workflows.sh <username> <password>
# Example: ./scripts/n8n_import_workflows.sh admin password

set -euo pipefail

USER=${1:-admin}
PASS=${2:-password}

BASE=http://localhost:5678

for f in ../n8n_workflows/*.json; do
  echo "Importing $f ..."
  curl -sS -X POST "$BASE/rest/workflows/import" \
    -u "$USER:$PASS" \
    -H 'Content-Type: application/json' \
    --data-binary "@$f" | jq .
done

echo "Import complete. You may need to activate workflows in the n8n UI or via API."
