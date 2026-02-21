import requests
import json
import random
import time

BASE_URL = 'http://127.0.0.1:5000'
session = requests.Session()

def run_tests():
    print("Testing Flask Verification...")
    
    # 1. Test Index redirect 
    try:
        res = session.get(BASE_URL + '/', allow_redirects=False)
        print("GET / -> Status:", res.status_code)
    except Exception as e:
        print("Failed to connect to Flask server. Is it running?", e)
        return

    # 2. Test Register
    test_user = f"testuser_{random.randint(1000,9999)}"
    reg_data = {
        "uid": f"uid_{random.randint(1000,9999)}",
        "uname": test_user,
        "password": "password123",
        "email": f"{test_user}@example.com",
        "phone": "555-1234"
    }
    res = session.post(BASE_URL + '/api/auth/register', json=reg_data)
    print("POST /api/auth/register -> Status:", res.status_code, "Response:", res.text)

    # 3. Test Login
    login_data = {"uname": test_user, "password": "password123"}
    res = session.post(BASE_URL + '/api/auth/login', json=login_data)
    print("POST /api/auth/login -> Status:", res.status_code, "Response:", res.text)

    # 4. Test Balance
    res = session.get(BASE_URL + '/api/user/balance')
    print("GET /api/user/balance -> Status:", res.status_code, "Response:", res.text)

if __name__ == "__main__":
    run_tests()
