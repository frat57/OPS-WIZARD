"""Seed the database with minimal example data for local development.

Usage (from project root):
    docker compose run --rm api python scripts/seed.py

The script reads DATABASE_URL from the environment.
"""
import os
import asyncio
import uuid
import json

import asyncpg


async def run():
    dsn = os.environ.get('DATABASE_URL') or 'postgresql://aiops:aiops_password@postgres:5432/aiops_db'
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        # create some sample users
        await conn.execute("INSERT INTO users(id, email, name, role) VALUES($1,$2,$3,$4) ON CONFLICT (id) DO NOTHING",
                           'user-1', 'alice@example.com', 'Alice', 'analyst')
        await conn.execute("INSERT INTO users(id, email, name, role) VALUES($1,$2,$3,$4) ON CONFLICT (id) DO NOTHING",
                           'user-2', 'bob@example.com', 'Bob', 'ops')

        # create a sample transaction
        tx_id = 'tx-' + uuid.uuid4().hex[:8]
        payload = {'source': 'test', 'amount': 100.0}
        await conn.execute(
            "INSERT INTO transactions(id, user_id, amount, currency, status, raw_payload) VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT (id) DO NOTHING",
            tx_id, 'user-1', 100.0, 'USD', 'pending', json.dumps(payload)
        )

        # create a sample alert (analysis result)
        alert_id = 'alert-' + uuid.uuid4().hex[:8]
        explain = [{'feature': 'tx_velocity', 'importance': 0.5}]
        await conn.execute(
            "INSERT INTO alerts(id, transaction_id, score, reasoning, suggested_action, explanation, status) VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT (id) DO NOTHING",
            alert_id, tx_id, 0.92, 'High-velocity + mismatched shipping', 'HOLD_TRANSACTION_AND_MANUAL_REVIEW', json.dumps(explain), 'open'
        )

        # add investigation
        inv_id = 'inv-' + uuid.uuid4().hex[:8]
        await conn.execute(
            "INSERT INTO investigations(id, alert_id, assigned_to, status, notes) VALUES($1,$2,$3,$4,$5) ON CONFLICT (id) DO NOTHING",
            inv_id, alert_id, 'user-2', 'open', 'Initial triage'
        )

        print('Seeded: user-1, user-2, transaction', tx_id, 'alert', alert_id, 'investigation', inv_id)

    await pool.close()


if __name__ == '__main__':
    asyncio.run(run())
