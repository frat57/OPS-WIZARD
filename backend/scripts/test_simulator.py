"""Test simulator (inside api container) - posts random transactions to /analyze endpoint inside Docker network

Usage (from repo root):
  docker compose run --rm -e API_URL=http://api:8000/analyze api python scripts/test_simulator.py
"""
import os
import random
import requests
from faker import Faker

fake = Faker()
API = os.environ.get('API_URL') or 'http://api:8000/analyze'

transactions = []
for i in range(10):
    amount = random.choice([random.uniform(1, 1000), random.uniform(1000, 6000), random.uniform(10000, 20000)])
    tx = {
        'amount': round(amount, 2),
        'currency': random.choice(['USD','EUR','TRY']),
        'merchant': fake.company(),
        'timestamp': fake.iso8601(),
        'ip_address': random.choice([fake.ipv4_private(), fake.ipv4_public(), '192.168.1.' + str(random.randint(2,200))]),
        'customer_id': fake.uuid4()
    }
    transactions.append(tx)

for tx in transactions:
    print('POST ->', tx)
    try:
        res = requests.post(API, json=tx, timeout=5)
        print('  =>', res.status_code, res.text)
    except Exception as e:
        print('  ERROR:', e)

print('Done')
