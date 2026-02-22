"""
test_flask.py — Comprehensive API test suite for KodBank Flask backend.

Usage:
    1. Start the Flask server: cd server && python app.py
    2. Run this script:         python test_flask.py
"""

import requests
import json
import random
import time

BASE_URL = 'http://127.0.0.1:5000'

# Colour helpers for terminal output
GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
RESET  = '\033[0m'

results = []


def check(label, condition, extra=''):
    status = f'{GREEN}PASS{RESET}' if condition else f'{RED}FAIL{RESET}'
    print(f'  {status}  {label}' + (f'  ({extra})' if extra else ''))
    results.append((label, condition))


def section(title):
    print(f'\n{YELLOW}━━━ {title} ━━━{RESET}')


# ── Session to preserve cookies (session auth) ────────────────────────────────
session = requests.Session()

# ── 0. Connectivity ───────────────────────────────────────────────────────────
section('0. Server Connectivity')
try:
    r = session.get(BASE_URL + '/', allow_redirects=False)
    check('GET / redirects to /register', r.status_code == 302)
except Exception as e:
    print(f'{RED}Cannot reach Flask server at {BASE_URL}{RESET}')
    print(f'  → {e}')
    print('\nIs the server running?  Start it with:  python server/app.py')
    exit(1)

# ── 1. Auth — Register ────────────────────────────────────────────────────────
section('1. Auth — Register')
uid   = f'uid_{random.randint(10000, 99999)}'
uname = f'testuser_{random.randint(10000, 99999)}'
email = f'{uname}@test.example.com'

good_reg = {
    'uid': uid, 'uname': uname, 'password': 'Pass1234!',
    'email': email, 'phone': '555-0100'
}

r = session.post(BASE_URL + '/api/auth/register', json=good_reg)
check('POST /api/auth/register → 201', r.status_code == 201, r.text[:80])

# Duplicate registration
r2 = session.post(BASE_URL + '/api/auth/register', json=good_reg)
check('Duplicate register → 409', r2.status_code == 409, r2.text[:80])

# Missing fields
r3 = session.post(BASE_URL + '/api/auth/register', json={'uname': 'x'})
check('Missing fields → 400', r3.status_code == 400, r3.text[:80])

# ── 2. Auth — Login ───────────────────────────────────────────────────────────
section('2. Auth — Login')
r = session.post(BASE_URL + '/api/auth/login',
                 json={'uname': uname, 'password': 'Pass1234!'})
check('POST /api/auth/login → 200', r.status_code == 200, r.text[:80])

r_bad = session.post(BASE_URL + '/api/auth/login',
                     json={'uname': uname, 'password': 'WrongPassword'})
check('Bad password → 401', r_bad.status_code == 401, r_bad.text[:80])

r_nof = session.post(BASE_URL + '/api/auth/login', json={'uname': uname})
check('Missing password → 400', r_nof.status_code == 400, r_nof.text[:80])

# ── 3. Balance ────────────────────────────────────────────────────────────────
section('3. Balance')
r = session.get(BASE_URL + '/api/user/balance')
check('GET /api/user/balance → 200', r.status_code == 200)
if r.status_code == 200:
    bal = r.json().get('balance')
    check('Balance field present', bal is not None, f'balance={bal}')

# Unauthenticated (new session)
anon = requests.Session()
r_u = anon.get(BASE_URL + '/api/user/balance')
check('Unauthenticated balance → 401', r_u.status_code == 401)

# ── 4. Deposit ────────────────────────────────────────────────────────────────
section('4. Deposit')
r = session.post(BASE_URL + '/api/user/deposit', json={'amount': 500})
check('POST /api/user/deposit 500 → 200', r.status_code == 200, r.text[:80])

r = session.post(BASE_URL + '/api/user/deposit', json={'amount': 0})
check('Deposit 0 → 400', r.status_code == 400)

r = session.post(BASE_URL + '/api/user/deposit', json={'amount': -100})
check('Deposit negative → 400', r.status_code == 400)

r = session.post(BASE_URL + '/api/user/deposit', json={'amount': 'abc'})
check('Deposit non-numeric → 400', r.status_code == 400)

# ── 5. Withdraw ───────────────────────────────────────────────────────────────
section('5. Withdraw')
r = session.post(BASE_URL + '/api/user/withdraw', json={'amount': 100})
check('POST /api/user/withdraw 100 → 200', r.status_code == 200, r.text[:80])

r = session.post(BASE_URL + '/api/user/withdraw', json={'amount': 99999999})
check('Insufficient funds → 400', r.status_code == 400)

r = session.post(BASE_URL + '/api/user/withdraw', json={'amount': 0})
check('Withdraw 0 → 400', r.status_code == 400)

# ── 6. Transactions ───────────────────────────────────────────────────────────
section('6. Transactions')
r = session.get(BASE_URL + '/api/user/transactions')
check('GET /api/user/transactions → 200', r.status_code == 200)
if r.status_code == 200:
    txns = r.json().get('transactions', [])
    check('Transactions list returned', isinstance(txns, list), f'{len(txns)} records')

# ── 7. News ───────────────────────────────────────────────────────────────────
section('7. News')
r = session.get(BASE_URL + '/api/news?category=latest')
check('GET /api/news?category=latest → 200', r.status_code == 200)
if r.status_code == 200:
    arts = r.json().get('articles', [])
    check('Articles array present', isinstance(arts, list), f'{len(arts)} articles')

r = session.get(BASE_URL + '/api/news?category=bitcoin')
check('GET /api/news?category=bitcoin → 200', r.status_code == 200)

r_anon = anon.get(BASE_URL + '/api/news')
check('Unauthenticated news → 401', r_anon.status_code == 401)

# ── 8. Stock Analytics ────────────────────────────────────────────────────────
section('8. Stock Analytics')
r = session.get(BASE_URL + '/api/analytics/tickers')
check('GET /api/analytics/tickers → 200', r.status_code == 200)
if r.status_code == 200:
    tickers = r.json()
    check('Tickers list not empty', len(tickers) > 0, f'{len(tickers)} tickers')

# ── 9. Fundamental Analysis ───────────────────────────────────────────────────
section('9. Fundamental Analysis (without real PDF)')

# Docs list (empty is fine — just verify the endpoint works)
r = session.get(BASE_URL + '/api/fundamental/documents')
check('GET /api/fundamental/documents → 200', r.status_code == 200)
if r.status_code == 200:
    docs = r.json().get('documents', [])
    check('Documents key present', 'documents' in r.json())

# Upload without a file → 400
r = session.post(BASE_URL + '/api/fundamental/upload')
check('Upload with no file → 400', r.status_code == 400)

# Chat without docs (should still 200 with a polite message)
r = session.post(BASE_URL + '/api/fundamental/chat',
                 json={'message': 'What is the revenue?', 'history': []})
check('Fundamental chat (no docs) → 200', r.status_code == 200)
if r.status_code == 200:
    resp = r.json().get('response', '')
    check('Response contains meaningful text', len(resp) > 10, resp[:80])

# Unauthenticated fundamental
for endpoint in ['/api/fundamental/documents',
                 '/api/fundamental/chat']:
    r_a = anon.get(BASE_URL + endpoint) if 'documents' in endpoint \
          else anon.post(BASE_URL + endpoint, json={'message': 'x'})
    check(f'Unauth {endpoint} → 401', r_a.status_code == 401)

# ── 10. Frontend Routes ───────────────────────────────────────────────────────
section('10. Frontend Routes')
for path, expected in [('/register', 200), ('/login', 200), ('/dashboard', 200)]:
    r = session.get(BASE_URL + path)
    check(f'GET {path} → {expected}', r.status_code == expected)

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(1 for _, ok in results if ok)
total  = len(results)
failed = total - passed
print(f'\n{"━"*50}')
print(f'Results: {GREEN}{passed} passed{RESET}  '
      f'{(RED+str(failed)+RESET) if failed else str(failed)} failed  '
      f'/ {total} total')
if failed:
    print(f'\n{RED}Failed tests:{RESET}')
    for label, ok in results:
        if not ok:
            print(f'  ✗ {label}')
print('━'*50)
