<#
Run this PowerShell helper from the repo root to quickly prepare the local DB using docker-compose.

Usage:
  .\scripts\setup_local_db.ps1

This will:
 - copy .env.example to .env if needed
 - start the postgres service
 - run Alembic migrations inside the `api` container
 - run the seed script inside the `api` container
#>

if (-Not (Test-Path .env)) {
  Write-Host "Creating .env from .env.example"
  Copy-Item .env.example .env
}

Write-Host "Starting Postgres (docker-compose)..."
docker compose up -d postgres

Write-Host "Waiting for Postgres to be ready..."
for ($i=0; $i -lt 30; $i++) {
  $ready = docker compose exec -T postgres pg_isready -U ${env:POSTGRES_USER:-aiops} 2>&1
  if ($LASTEXITCODE -eq 0) { break }
  Start-Sleep -Seconds 1
}

Write-Host "Applying Alembic migrations..."
docker compose run --rm api alembic -c backend/alembic.ini upgrade head

Write-Host "Seeding DB with example data..."
docker compose run --rm api python scripts/seed.py

Write-Host "Done. Run: docker compose run --rm api python scripts/verify_schema.py to inspect tables."
