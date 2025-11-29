# Backend — DB migrations

This folder uses Alembic for schema migrations. The project includes a minimal Alembic config and an initial migration which creates the `events` table.

Common commands (run from repo root or `backend`):

- Create a new migration: `alembic -c backend/alembic.ini revision -m "desc" --autogenerate`
- Apply migrations: `alembic -c backend/alembic.ini upgrade head`

If running inside the `api` container (docker-compose):

```powershell
docker compose run --rm api alembic -c backend/alembic.ini upgrade head
```

The CI workflow runs the migrations during pipeline to ensure schema changes apply cleanly.

## Local Postgres (Windows) & running migrations

You can run Postgres locally in two main ways on Windows:

1) Recommended (Docker): use the project's `docker-compose.yml` which already defines a Postgres service.

```powershell
# from repo root
cp .env.example .env
docker compose up --build

# then run migrations
docker compose run --rm api alembic -c backend/alembic.ini upgrade head
```

2) Native Postgres (Windows installer or Chocolatey):

 - Install PostgreSQL (https://www.postgresql.org/download/windows/ or `choco install postgresql`)
 - Start the service and create a DB & user to match `.env` or edit `.env`.

Example SQL to create DB & user if you installed Postgres and are using psql:

```sql
CREATE ROLE aiops WITH LOGIN PASSWORD 'aiops_password';
CREATE DATABASE aiops_db OWNER aiops;
GRANT ALL PRIVILEGES ON DATABASE aiops_db TO aiops;
```

Then in your terminal (with DATABASE_URL set) run:

```powershell
# from repo root
setx DATABASE_URL "postgres://aiops:aiops_password@localhost:5432/aiops_db"
# If you already have alembic installed in the project container:
alembic -c backend/alembic.ini upgrade head
```

If everything is set up correctly the `events` & core tables will be created.

## Seeding and verification

There are two helper scripts in `backend/scripts/` to make local testing easier:

- `seed.py` — inserts sample users, a transaction, an alert and an investigation.
- `verify_schema.py` — prints row counts for the core tables and lists recent alerts.

Run them from the project root (they respect `DATABASE_URL` or default to the compose DB):

```powershell
# apply migrations then seed
docker compose run --rm api alembic -c backend/alembic.ini upgrade head

docker compose run --rm api python scripts/seed.py

# verify

docker compose run --rm api python scripts/verify_schema.py
```

There's also a convenience helper at `scripts/setup_local_db.ps1` (repo root) which starts the Postgres service, runs migrations and then seeds the DB.

## Troubleshooting migrations

If `alembic upgrade head` fails, here's a quick checklist and commands to debug:

- Make sure your container/service has a usable DATABASE_URL. If you used `docker compose run --rm api ...` the service will read env from `env_file` or `environment` in `docker-compose.yml`.

- Common error: "could not translate host name" or connection refused — Postgres not running or wrong host. Start Postgres with `docker compose up -d postgres` and check `docker compose ps`.

- Common error: wrong URL scheme (SQLAlchemy/Alembic) — Alembic expects a SQLAlchemy-compatible URL. The project auto-normalizes `postgres://` -> `postgresql+psycopg://` but if you still have issues, verify your `DATABASE_URL` (e.g., `postgresql+psycopg://aiops:aiops_password@localhost:5432/aiops_db`).

- Debugging tip: run a shell in the `api` container and try connecting with psycopg or run alembic with verbose logging:

```powershell
docker compose run --rm api /bin/sh
# inside the container:
alembic -c backend/alembic.ini upgrade head --verbose
python -c "import os; print('DB:', os.environ.get('DATABASE_URL'))"
```

If you still hit an error, copy the exact error output and I can help debug further.
