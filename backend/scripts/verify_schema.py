"""Verify schema: check counts for key tables and list recent rows.

Usage (from project root):
    docker compose run --rm api python scripts/verify_schema.py

The script reads DATABASE_URL from the environment.
"""
import os
import asyncio

import asyncpg


async def run():
    dsn = os.environ.get('DATABASE_URL') or 'postgresql://aiops:aiops_password@postgres:5432/aiops_db'
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        tables = ['users', 'transactions', 'alerts', 'investigations', 'decisions', 'integrations', 'audit_logs', 'events', 'fraud_logs']
        for t in tables:
            try:
                cnt = await conn.fetchval(f"SELECT count(*) FROM {t}")
            except Exception as e:
                cnt = f'error: {e}'
            print(f"{t}: {cnt}")

        # show last 5 alerts
        print('\nLast 5 alerts:')
        try:
            rows = await conn.fetch("SELECT id, transaction_id, score, suggested_action, status, created_at FROM alerts ORDER BY created_at DESC LIMIT 5")
            for r in rows:
                print(dict(r))
        except Exception as e:
            print('alerts query error', e)

    await pool.close()


if __name__ == '__main__':
    asyncio.run(run())
