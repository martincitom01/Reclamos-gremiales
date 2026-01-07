import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / 'frontend' / '.env')
BASE = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8000')
API = f"{BASE}/api"


def test_invalid_login_existing_user():
    r = requests.post(f"{API}/auth/login", json={"username": "martin", "password": "wrongpass"})
    assert r.status_code == 401


def test_invalid_login_nonexistent_user():
    r = requests.post(f"{API}/auth/login", json={"username": "no_user", "password": "nopass"})
    assert r.status_code == 401


def get_emisor_token():
    r = requests.post(f"{API}/auth/login", json={"username": "martin", "password": "94017448"})
    assert r.status_code == 200
    return r.json().get('access_token')


def test_emisor_cannot_access_admin_endpoint():
    token = get_emisor_token()
    r = requests.get(f"{API}/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_emisor_cannot_create_reclamo_for_other_line():
    token = get_emisor_token()
    payload = {"linea": "H", "categoria": "Condiciones de trabajo", "sector_estacion": "X", "descripcion": "test"}
    r = requests.post(f"{API}/reclamos", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload)
    assert r.status_code == 403


def test_invalid_invitation_token():
    r = requests.get(f"{API}/invitations/invalid-token-123")
    assert r.status_code == 404
