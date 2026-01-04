#!/usr/bin/env python3
"""
Backend API Testing for Sistema de Reclamos Gremiales UTA
Testing focus: File/Image viewing fix and User update endpoint
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

def main():
    """Main test execution"""
    print("🚀 Starting Backend API Tests for Sistema de Reclamos Gremiales UTA")
    print(f"Testing against: {BASE_URL}")
    print("="*60)
    
    all_results = TestResults()
    
    # Test 1: Admin Access
    print("\n📋 Testing Admin Access...")
    token, admin_results = test_admin_access()
    all_results.passed += admin_results.passed
    all_results.failed += admin_results.failed
    all_results.errors.extend(admin_results.errors)
    
    if not token:
        print("❌ Cannot proceed without admin token")
        all_results.summary()
        return False
    
    # Test 2: File/Image Accessibility
    print("\n📁 Testing File/Image Accessibility...")
    reclamo_with_files, reclamo_results = test_get_reclamos(token)
    all_results.passed += reclamo_results.passed
    all_results.failed += reclamo_results.failed
    all_results.errors.extend(reclamo_results.errors)
    
    if reclamo_with_files:
        file_results = test_file_accessibility(reclamo_with_files)
        all_results.passed += file_results.passed
        all_results.failed += file_results.failed
        all_results.errors.extend(file_results.errors)
    else:
        print("⚠️  No reclamos with files found - skipping file accessibility tests")
    
    # Test 3: User Update Endpoint
    print("\n👤 Testing User Update Endpoint...")
    test_user, user_results = test_get_users(token)
    all_results.passed += user_results.passed
    all_results.failed += user_results.failed
    all_results.errors.extend(user_results.errors)
    
    if test_user:
        update_results = test_user_update_endpoint(token, test_user)
        all_results.passed += update_results.passed
        all_results.failed += update_results.failed
        all_results.errors.extend(update_results.errors)
    else:
        print("⚠️  No test user found - skipping user update tests")
    
    # Final summary
    success = all_results.summary()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)