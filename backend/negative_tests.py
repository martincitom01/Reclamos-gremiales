#!/usr/bin/env python3
import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / 'frontend' / '.env')
BASE = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8000')
API = f"{BASE}/api"

def check(desc, func):
    try:
        ok, msg = func()
        print(f"{'✅' if ok else '❌'} {desc} - {msg}")
        return ok
    except Exception as e:
        print(f"❌ {desc} - Exception: {e}")
        return False

def test_invalid_login_existing_user():
    payload = {"username": "martin", "password": "wrongpass"}
    r = requests.post(f"{API}/auth/login", json=payload)
    return (r.status_code == 401, f"HTTP {r.status_code}: {r.text}")

def test_invalid_login_nonexistent_user():
    payload = {"username": "no_user", "password": "nopass"}
    r = requests.post(f"{API}/auth/login", json=payload)
    return (r.status_code == 401, f"HTTP {r.status_code}: {r.text}")

def get_emisor_token():
    r = requests.post(f"{API}/auth/login", json={"username":"martin","password":"94017448"})
    if r.status_code == 200:
        return r.json().get('access_token')
    return None

def test_emisor_access_admin_endpoint():
    token = get_emisor_token()
    if not token:
        return (False, "Could not obtain emisor token")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API}/users", headers=headers)
    return (r.status_code == 403, f"HTTP {r.status_code}: {r.text}")

def test_create_reclamo_wrong_line():
    token = get_emisor_token()
    if not token:
        return (False, "Could not obtain emisor token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"linea": "H", "categoria": "Condiciones de trabajo", "sector_estacion": "X", "descripcion": "Test wrong line"}
    r = requests.post(f"{API}/reclamos", headers=headers, json=payload)
    return (r.status_code == 403, f"HTTP {r.status_code}: {r.text}")

def test_invalid_invitation_token():
    r = requests.get(f"{API}/invitations/invalid-token-123")
    return (r.status_code == 404, f"HTTP {r.status_code}: {r.text}")

def main():
    tests = [
        ("Invalid login for existing user", test_invalid_login_existing_user),
        ("Invalid login for nonexistent user", test_invalid_login_nonexistent_user),
        ("Emisor cannot access admin endpoint", test_emisor_access_admin_endpoint),
        ("Emisor cannot create reclamo for other line", test_create_reclamo_wrong_line),
        ("Invalid invitation token returns 404", test_invalid_invitation_token),
    ]

    all_ok = True
    for desc, fn in tests:
        ok = check(desc, fn)
        all_ok = all_ok and ok

    if all_ok:
        print('\nAll negative tests behaved as expected')
        return 0
    else:
        print('\nSome negative tests did NOT behave as expected')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
