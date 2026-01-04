#!/usr/bin/env python3
"""
Backend API Testing for Sistema de Reclamos Gremiales UTA
SEGUNDA RONDA - Comprehensive testing of all system components
"""

import requests
import json
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / 'frontend' / '.env')

# Configuration
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://metrofix-1.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test users as specified in review request
TEST_USERS = [
    {"username": "martin", "password": "94017448", "expected_line": "A"},
    {"username": "Mara", "password": "123456", "expected_line": "H"},
    {"username": "Luisina", "password": "123456", "expected_line": "A"}
]

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def log_pass(self, test_name):
        print(f"✅ PASS: {test_name}")
        self.passed += 1
        
    def log_fail(self, test_name, error):
        print(f"❌ FAIL: {test_name} - {error}")
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0

def test_admin_access():
    """Test admin access endpoint"""
    results = TestResults()
    
    try:
        response = requests.get(f"{API_BASE}/admin/access")
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data and 'user' in data:
                results.log_pass("Admin access endpoint returns token and user")
                return data['access_token'], results
            else:
                results.log_fail("Admin access endpoint", "Missing access_token or user in response")
                return None, results
        else:
            results.log_fail("Admin access endpoint", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Admin access endpoint", f"Request failed: {str(e)}")
        return None, results

def test_get_reclamos(token):
    """Get list of reclamos to find one with files"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/reclamos", headers=headers)
        
        if response.status_code == 200:
            reclamos = response.json()
            results.log_pass("Get reclamos endpoint")
            
            # Find a reclamo with files
            reclamo_with_files = None
            for reclamo in reclamos:
                if reclamo.get('archivos') and len(reclamo['archivos']) > 0:
                    reclamo_with_files = reclamo
                    break
                    
            if reclamo_with_files:
                results.log_pass("Found reclamo with attached files")
                return reclamo_with_files, results
            else:
                results.log_fail("Find reclamo with files", "No reclamos found with attached files")
                return None, results
        else:
            results.log_fail("Get reclamos endpoint", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Get reclamos endpoint", f"Request failed: {str(e)}")
        return None, results

def test_file_accessibility(reclamo_with_files):
    """Test that files attached to reclamos are accessible via /api/uploads path"""
    results = TestResults()
    
    if not reclamo_with_files or not reclamo_with_files.get('archivos'):
        results.log_fail("File accessibility test", "No reclamo with files provided")
        return results
        
    for file_path in reclamo_with_files['archivos']:
        try:
            # File path should be in format /api/uploads/filename
            if not file_path.startswith('/api/uploads/'):
                results.log_fail("File path format", f"File path '{file_path}' doesn't start with /api/uploads/")
                continue
                
            # Test file accessibility
            file_url = f"{BASE_URL}{file_path}"
            response = requests.head(file_url)  # Use HEAD to avoid downloading large files
            
            if response.status_code == 200:
                results.log_pass(f"File accessible: {file_path}")
            elif response.status_code == 404:
                results.log_fail("File accessibility", f"File not found: {file_path}")
            else:
                results.log_fail("File accessibility", f"HTTP {response.status_code} for file: {file_path}")
                
        except Exception as e:
            results.log_fail("File accessibility", f"Request failed for {file_path}: {str(e)}")
            
    return results

def test_get_users(token):
    """Get list of users for testing user updates"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            results.log_pass("Get users endpoint")
            
            # Find a non-admin user to test updates on
            test_user = None
            for user in users:
                if user.get('role') != 'ADMIN':
                    test_user = user
                    break
                    
            if test_user:
                results.log_pass("Found non-admin user for testing")
                return test_user, results
            else:
                results.log_fail("Find test user", "No non-admin users found for testing")
                return None, results
        else:
            results.log_fail("Get users endpoint", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Get users endpoint", f"Request failed: {str(e)}")
        return None, results

def test_user_update_endpoint(token, test_user):
    """Test the PUT /api/users/{user_id} endpoint with various scenarios"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    user_id = test_user['id']
    original_username = test_user['username']
    original_email = test_user['email']
    
    # Test 1: Update username only
    try:
        new_username = f"{original_username}_updated"
        payload = {"username": new_username}
        response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('user', {}).get('username') == new_username:
                results.log_pass("Update username only")
            else:
                results.log_fail("Update username only", "Username not updated in response")
        else:
            results.log_fail("Update username only", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("Update username only", f"Request failed: {str(e)}")
    
    # Test 2: Update email only
    try:
        new_email = f"updated_{original_email}"
        payload = {"email": new_email}
        response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('user', {}).get('email') == new_email:
                results.log_pass("Update email only")
            else:
                results.log_fail("Update email only", "Email not updated in response")
        else:
            results.log_fail("Update email only", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("Update email only", f"Request failed: {str(e)}")
    
    # Test 3: Update password (should hash)
    try:
        new_password = "newpassword123"
        payload = {"password": new_password}
        response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
        
        if response.status_code == 200:
            results.log_pass("Update password")
        else:
            results.log_fail("Update password", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("Update password", f"Request failed: {str(e)}")
    
    # Test 4: Update linea_asignada
    try:
        new_linea = "Línea B"
        payload = {"linea_asignada": new_linea}
        response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('user', {}).get('linea_asignada') == new_linea:
                results.log_pass("Update linea_asignada")
            else:
                results.log_fail("Update linea_asignada", "Linea_asignada not updated in response")
        else:
            results.log_fail("Update linea_asignada", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("Update linea_asignada", f"Request failed: {str(e)}")
    
    # Test 5: Validation - password less than 6 chars should fail
    try:
        short_password = "123"
        payload = {"password": short_password}
        response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
        
        if response.status_code == 400:
            results.log_pass("Password validation (too short)")
        else:
            results.log_fail("Password validation (too short)", f"Expected 400, got {response.status_code}")
    except Exception as e:
        results.log_fail("Password validation (too short)", f"Request failed: {str(e)}")
    
    # Test 6: Validation - duplicate username should fail (create another user first)
    try:
        # Get another user to test duplicate username
        users_response = requests.get(f"{API_BASE}/users", headers=headers)
        if users_response.status_code == 200:
            users = users_response.json()
            other_user = None
            for user in users:
                if user['id'] != user_id and user.get('role') != 'ADMIN':
                    other_user = user
                    break
            
            if other_user:
                duplicate_username = other_user['username']
                payload = {"username": duplicate_username}
                response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
                
                if response.status_code == 400:
                    results.log_pass("Username uniqueness validation")
                else:
                    results.log_fail("Username uniqueness validation", f"Expected 400, got {response.status_code}")
            else:
                results.log_fail("Username uniqueness validation", "No other user found for duplicate test")
    except Exception as e:
        results.log_fail("Username uniqueness validation", f"Request failed: {str(e)}")
    
    # Test 7: Validation - duplicate email should fail
    try:
        # Get another user to test duplicate email
        users_response = requests.get(f"{API_BASE}/users", headers=headers)
        if users_response.status_code == 200:
            users = users_response.json()
            other_user = None
            for user in users:
                if user['id'] != user_id and user.get('role') != 'ADMIN':
                    other_user = user
                    break
            
            if other_user:
                duplicate_email = other_user['email']
                payload = {"email": duplicate_email}
                response = requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=payload)
                
                if response.status_code == 400:
                    results.log_pass("Email uniqueness validation")
                else:
                    results.log_fail("Email uniqueness validation", f"Expected 400, got {response.status_code}")
            else:
                results.log_fail("Email uniqueness validation", "No other user found for duplicate test")
    except Exception as e:
        results.log_fail("Email uniqueness validation", f"Request failed: {str(e)}")
    
    # Restore original user data
    try:
        restore_payload = {
            "username": original_username,
            "email": original_email
        }
        requests.put(f"{API_BASE}/users/{user_id}", headers=headers, json=restore_payload)
        results.log_pass("Restored original user data")
    except Exception as e:
        results.log_fail("Restore original user data", f"Failed to restore: {str(e)}")
    
    return results

def test_emisor_login():
    """Test emisor login with Luisina credentials"""
    results = TestResults()
    
    try:
        payload = {
            "username": "Luisina",
            "password": "123456"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if 'access_token' in data and 'user' in data:
                user = data['user']
                if user.get('username') == 'Luisina' and user.get('linea_asignada') == 'A':
                    results.log_pass("Emisor login (Luisina) successful")
                    return data['access_token'], user, results
                else:
                    results.log_fail("Emisor login validation", f"User data incorrect: {user}")
                    return None, None, results
            else:
                results.log_fail("Emisor login", "Missing access_token or user in response")
                return None, None, results
        else:
            results.log_fail("Emisor login", f"HTTP {response.status_code}: {response.text}")
            return None, None, results
            
    except Exception as e:
        results.log_fail("Emisor login", f"Request failed: {str(e)}")
        return None, None, results

def test_create_reclamo_as_emisor(emisor_token):
    """Create a new reclamo as emisor to trigger admin notification"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {emisor_token}", "Content-Type": "application/json"}
    
    try:
        payload = {
            "linea": "A",
            "categoria": "Condiciones de trabajo",
            "sector_estacion": "Estación Central",
            "descripcion": "Test reclamo para verificar notificaciones - problema con ventilación en cabina"
        }
        response = requests.post(f"{API_BASE}/reclamos", headers=headers, json=payload)
        
        if response.status_code == 200:
            reclamo = response.json()
            if reclamo.get('numero_reclamo') and reclamo.get('id'):
                results.log_pass("Create reclamo as emisor")
                return reclamo, results
            else:
                results.log_fail("Create reclamo validation", "Missing numero_reclamo or id in response")
                return None, results
        else:
            results.log_fail("Create reclamo as emisor", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Create reclamo as emisor", f"Request failed: {str(e)}")
        return None, results

def test_admin_notifications_after_reclamo_creation(admin_token, reclamo):
    """Test that admin receives notification after reclamo creation"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        # Get admin notifications
        response = requests.get(f"{API_BASE}/notifications", headers=headers)
        
        if response.status_code == 200:
            notifications = response.json()
            results.log_pass("Get admin notifications endpoint")
            
            # Look for notification about the created reclamo
            reclamo_notification = None
            for notif in notifications:
                if (notif.get('reclamo_id') == reclamo['id'] and 
                    reclamo['numero_reclamo'] in notif.get('message', '')):
                    reclamo_notification = notif
                    break
            
            if reclamo_notification:
                results.log_pass("Admin received notification for new reclamo")
                return reclamo_notification, results
            else:
                results.log_fail("Admin notification check", f"No notification found for reclamo {reclamo['numero_reclamo']}")
                return None, results
        else:
            results.log_fail("Get admin notifications", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Get admin notifications", f"Request failed: {str(e)}")
        return None, results

def test_admin_add_comment_to_reclamo(admin_token, reclamo):
    """Test admin adding comment to reclamo to trigger emisor notification"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    try:
        payload = {
            "text": "Hemos recibido tu reclamo y estamos investigando el problema de ventilación. Te mantendremos informado.",
            "author": "Administrador"
        }
        response = requests.post(f"{API_BASE}/reclamos/{reclamo['id']}/comentarios", headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('message') == 'Comentario agregado':
                results.log_pass("Admin add comment to reclamo")
                return data.get('comentario'), results
            else:
                results.log_fail("Admin comment validation", "Unexpected response message")
                return None, results
        else:
            results.log_fail("Admin add comment", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Admin add comment", f"Request failed: {str(e)}")
        return None, results

def test_emisor_notifications_after_admin_response(emisor_token, reclamo):
    """Test that emisor receives notification after admin responds"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {emisor_token}"}
    
    try:
        # Get emisor notifications
        response = requests.get(f"{API_BASE}/notifications", headers=headers)
        
        if response.status_code == 200:
            notifications = response.json()
            results.log_pass("Get emisor notifications endpoint")
            
            # Look for notification about admin response
            admin_response_notification = None
            for notif in notifications:
                if (notif.get('reclamo_id') == reclamo['id'] and 
                    'administrador ha respondido' in notif.get('message', '').lower()):
                    admin_response_notification = notif
                    break
            
            if admin_response_notification:
                results.log_pass("Emisor received notification for admin response")
                return admin_response_notification, results
            else:
                results.log_fail("Emisor notification check", f"No admin response notification found for reclamo {reclamo['numero_reclamo']}")
                return None, results
        else:
            results.log_fail("Get emisor notifications", f"HTTP {response.status_code}: {response.text}")
            return None, results
            
    except Exception as e:
        results.log_fail("Get emisor notifications", f"Request failed: {str(e)}")
        return None, results

def test_notification_endpoints(admin_token):
    """Test all notification-related endpoints"""
    results = TestResults()
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: GET /api/notifications
    try:
        response = requests.get(f"{API_BASE}/notifications", headers=headers)
        if response.status_code == 200:
            notifications = response.json()
            if isinstance(notifications, list):
                results.log_pass("GET /api/notifications returns list")
            else:
                results.log_fail("GET /api/notifications", "Response is not a list")
        else:
            results.log_fail("GET /api/notifications", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/notifications", f"Request failed: {str(e)}")
    
    # Test 2: GET /api/notifications/unread/count
    try:
        response = requests.get(f"{API_BASE}/notifications/unread/count", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'count' in data and isinstance(data['count'], int):
                results.log_pass("GET /api/notifications/unread/count returns count")
            else:
                results.log_fail("GET /api/notifications/unread/count", "Missing or invalid count field")
        else:
            results.log_fail("GET /api/notifications/unread/count", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("GET /api/notifications/unread/count", f"Request failed: {str(e)}")
    
    # Test 3: PATCH /api/notifications/{id}/read (need to find an unread notification first)
    try:
        # Get notifications to find an unread one
        response = requests.get(f"{API_BASE}/notifications", headers=headers)
        if response.status_code == 200:
            notifications = response.json()
            unread_notification = None
            for notif in notifications:
                if not notif.get('is_read', True):
                    unread_notification = notif
                    break
            
            if unread_notification:
                # Mark as read
                notif_id = unread_notification['id']
                response = requests.patch(f"{API_BASE}/notifications/{notif_id}/read", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('message') == 'Notification marked as read':
                        results.log_pass("PATCH /api/notifications/{id}/read marks notification as read")
                    else:
                        results.log_fail("PATCH /api/notifications/{id}/read", "Unexpected response message")
                else:
                    results.log_fail("PATCH /api/notifications/{id}/read", f"HTTP {response.status_code}: {response.text}")
            else:
                results.log_pass("PATCH /api/notifications/{id}/read (no unread notifications to test)")
    except Exception as e:
        results.log_fail("PATCH /api/notifications/{id}/read", f"Request failed: {str(e)}")
    
    return results

def test_comunicados_system(admin_token, emisor_token):
    """Test the complete comunicados system"""
    results = TestResults()
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    emisor_headers = {"Authorization": f"Bearer {emisor_token}"}
    
    # Get users for testing specific user targeting
    try:
        users_response = requests.get(f"{API_BASE}/users", headers=admin_headers)
        if users_response.status_code != 200:
            results.log_fail("Get users for comunicados test", f"HTTP {users_response.status_code}")
            return results
        users = users_response.json()
        test_user = None
        for user in users:
            if user.get('role') == 'EMISOR_RECLAMO':
                test_user = user
                break
        if not test_user:
            results.log_fail("Find test user for comunicados", "No emisor user found")
            return results
    except Exception as e:
        results.log_fail("Get users for comunicados test", f"Request failed: {str(e)}")
        return results
    
    # Test 1: Create comunicado for "todos" (all users)
    print("  📢 Testing comunicado creation for 'todos'...")
    try:
        params = {
            "titulo": "Comunicado para Todos",
            "mensaje": "Este es un mensaje importante para todos los emisores",
            "tipo_destinatario": "todos"
        }
        response = requests.post(f"{API_BASE}/comunicados", headers=admin_headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'comunicado_id' in data and 'destinatarios' in data:
                results.log_pass("Create comunicado for 'todos'")
                comunicado_todos_id = data['comunicado_id']
            else:
                results.log_fail("Create comunicado for 'todos'", "Missing comunicado_id or destinatarios in response")
                comunicado_todos_id = None
        else:
            results.log_fail("Create comunicado for 'todos'", f"HTTP {response.status_code}: {response.text}")
            comunicado_todos_id = None
    except Exception as e:
        results.log_fail("Create comunicado for 'todos'", f"Request failed: {str(e)}")
        comunicado_todos_id = None
    
    # Test 2: Create comunicado for specific lines
    print("  📢 Testing comunicado creation for specific lines...")
    try:
        params = {
            "titulo": "Comunicado para Líneas A y B",
            "mensaje": "Mensaje específico para las líneas A y B",
            "tipo_destinatario": "lineas",
            "lineas_destino": "A,B"
        }
        response = requests.post(f"{API_BASE}/comunicados", headers=admin_headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'comunicado_id' in data:
                results.log_pass("Create comunicado for specific lines")
                comunicado_lineas_id = data['comunicado_id']
            else:
                results.log_fail("Create comunicado for specific lines", "Missing comunicado_id in response")
                comunicado_lineas_id = None
        else:
            results.log_fail("Create comunicado for specific lines", f"HTTP {response.status_code}: {response.text}")
            comunicado_lineas_id = None
    except Exception as e:
        results.log_fail("Create comunicado for specific lines", f"Request failed: {str(e)}")
        comunicado_lineas_id = None
    
    # Test 3: Create comunicado for specific users
    print("  📢 Testing comunicado creation for specific users...")
    try:
        params = {
            "titulo": "Comunicado para Usuario Específico",
            "mensaje": f"Mensaje específico para {test_user['username']}",
            "tipo_destinatario": "usuarios",
            "usuarios_destino": test_user['id']
        }
        response = requests.post(f"{API_BASE}/comunicados", headers=admin_headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'comunicado_id' in data:
                results.log_pass("Create comunicado for specific users")
                comunicado_usuarios_id = data['comunicado_id']
            else:
                results.log_fail("Create comunicado for specific users", "Missing comunicado_id in response")
                comunicado_usuarios_id = None
        else:
            results.log_fail("Create comunicado for specific users", f"HTTP {response.status_code}: {response.text}")
            comunicado_usuarios_id = None
    except Exception as e:
        results.log_fail("Create comunicado for specific users", f"Request failed: {str(e)}")
        comunicado_usuarios_id = None
    
    # Test 4: List comunicados as admin (should see all)
    print("  📋 Testing list comunicados as admin...")
    try:
        response = requests.get(f"{API_BASE}/comunicados", headers=admin_headers)
        
        if response.status_code == 200:
            comunicados = response.json()
            if isinstance(comunicados, list):
                results.log_pass("List comunicados as admin")
                # Check if we can find our created comunicados
                found_todos = any(c.get('id') == comunicado_todos_id for c in comunicados) if comunicado_todos_id else True
                found_lineas = any(c.get('id') == comunicado_lineas_id for c in comunicados) if comunicado_lineas_id else True
                found_usuarios = any(c.get('id') == comunicado_usuarios_id for c in comunicados) if comunicado_usuarios_id else True
                
                if found_todos and found_lineas and found_usuarios:
                    results.log_pass("Admin can see all created comunicados")
                else:
                    results.log_fail("Admin visibility check", "Some created comunicados not visible to admin")
            else:
                results.log_fail("List comunicados as admin", "Response is not a list")
        else:
            results.log_fail("List comunicados as admin", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("List comunicados as admin", f"Request failed: {str(e)}")
    
    # Test 5: List comunicados as emisor (should only see relevant ones)
    print("  📋 Testing list comunicados as emisor...")
    try:
        response = requests.get(f"{API_BASE}/comunicados", headers=emisor_headers)
        
        if response.status_code == 200:
            comunicados = response.json()
            if isinstance(comunicados, list):
                results.log_pass("List comunicados as emisor")
                
                # Emisor should see comunicados for "todos" and their line (A)
                # Check if emisor can see the "todos" comunicado
                found_todos = any(c.get('id') == comunicado_todos_id for c in comunicados) if comunicado_todos_id else True
                # Check if emisor can see line A comunicado (since Luisina is on line A)
                found_lineas = any(c.get('id') == comunicado_lineas_id for c in comunicados) if comunicado_lineas_id else True
                
                if found_todos and found_lineas:
                    results.log_pass("Emisor can see relevant comunicados (todos and their line)")
                else:
                    results.log_fail("Emisor visibility check", "Emisor cannot see expected comunicados")
            else:
                results.log_fail("List comunicados as emisor", "Response is not a list")
        else:
            results.log_fail("List comunicados as emisor", f"HTTP {response.status_code}: {response.text}")
    except Exception as e:
        results.log_fail("List comunicados as emisor", f"Request failed: {str(e)}")
    
    # Test 6: Emisor responds to comunicado
    print("  💬 Testing emisor response to comunicado...")
    if comunicado_todos_id:
        try:
            payload = {"texto": "Gracias por la información. Mensaje recibido correctamente."}
            response = requests.post(f"{API_BASE}/comunicados/{comunicado_todos_id}/respuestas", 
                                   headers=emisor_headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Respuesta agregada':
                    results.log_pass("Emisor responds to comunicado")
                else:
                    results.log_fail("Emisor response validation", "Unexpected response message")
            else:
                results.log_fail("Emisor responds to comunicado", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            results.log_fail("Emisor responds to comunicado", f"Request failed: {str(e)}")
    else:
        results.log_fail("Emisor responds to comunicado", "No comunicado available to respond to")
    
    # Test 7: Get specific comunicado
    print("  📄 Testing get specific comunicado...")
    if comunicado_todos_id:
        try:
            response = requests.get(f"{API_BASE}/comunicados/{comunicado_todos_id}", headers=admin_headers)
            
            if response.status_code == 200:
                comunicado = response.json()
                if comunicado.get('id') == comunicado_todos_id:
                    results.log_pass("Get specific comunicado")
                    # Check if response was added
                    if comunicado.get('respuestas') and len(comunicado['respuestas']) > 0:
                        results.log_pass("Comunicado contains emisor response")
                    else:
                        results.log_fail("Response verification", "No responses found in comunicado")
                else:
                    results.log_fail("Get specific comunicado", "Wrong comunicado returned")
            else:
                results.log_fail("Get specific comunicado", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            results.log_fail("Get specific comunicado", f"Request failed: {str(e)}")
    
    # Test 8: Delete comunicado (admin only)
    print("  🗑️ Testing delete comunicado (admin only)...")
    if comunicado_usuarios_id:
        try:
            response = requests.delete(f"{API_BASE}/comunicados/{comunicado_usuarios_id}", headers=admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('message') == 'Comunicado eliminado':
                    results.log_pass("Delete comunicado (admin)")
                else:
                    results.log_fail("Delete comunicado validation", "Unexpected response message")
            else:
                results.log_fail("Delete comunicado (admin)", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            results.log_fail("Delete comunicado (admin)", f"Request failed: {str(e)}")
    
    # Test 9: Verify emisor cannot delete comunicado
    print("  🚫 Testing emisor cannot delete comunicado...")
    if comunicado_lineas_id:
        try:
            response = requests.delete(f"{API_BASE}/comunicados/{comunicado_lineas_id}", headers=emisor_headers)
            
            if response.status_code == 403:
                results.log_pass("Emisor cannot delete comunicado (403 Forbidden)")
            else:
                results.log_fail("Emisor delete restriction", f"Expected 403, got {response.status_code}")
        except Exception as e:
            results.log_fail("Emisor delete restriction", f"Request failed: {str(e)}")
    
    return results

def main():
    """Main test execution"""
    print("🚀 Starting Backend API Tests for Sistema de Reclamos Gremiales UTA")
    print("📢 Focus: Comunicados (Messaging) System")
    print(f"Testing against: {BASE_URL}")
    print("="*60)
    
    all_results = TestResults()
    
    # Test 1: Admin Access
    print("\n📋 Testing Admin Access...")
    admin_token, admin_results = test_admin_access()
    all_results.passed += admin_results.passed
    all_results.failed += admin_results.failed
    all_results.errors.extend(admin_results.errors)
    
    if not admin_token:
        print("❌ Cannot proceed without admin token")
        all_results.summary()
        return False
    
    # Test 2: Emisor Login
    print("\n👤 Testing Emisor Login (Luisina)...")
    emisor_token, emisor_user, emisor_results = test_emisor_login()
    all_results.passed += emisor_results.passed
    all_results.failed += emisor_results.failed
    all_results.errors.extend(emisor_results.errors)
    
    if not emisor_token:
        print("❌ Cannot proceed without emisor token")
        all_results.summary()
        return False
    
    # Test 3: Comunicados System (Main Focus)
    print("\n📢 Testing Comunicados (Messaging) System...")
    comunicados_results = test_comunicados_system(admin_token, emisor_token)
    all_results.passed += comunicados_results.passed
    all_results.failed += comunicados_results.failed
    all_results.errors.extend(comunicados_results.errors)
    
    # Final summary
    success = all_results.summary()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)