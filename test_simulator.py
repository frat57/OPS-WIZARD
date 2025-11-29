"""Simple test simulator that posts random transactions to POST /analyze

Usage:
    python test_simulator.py

Ensure your API is running at http://localhost:8000
"""
import random
import requests
from faker import Faker

fake = Faker()
import os

API = os.environ.get('API_URL') or 'http://localhost:8000/analyze'

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
