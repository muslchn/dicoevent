import requests
import json
import time
from typing import Dict, Any, Optional

class DicoEventAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api"
        self.session = requests.Session()
        self.tokens = {}
        self.test_data = {}
        
    def log_test_result(self, test_name: str, status: str, details: str = ""):
        """Log test results in a structured format"""
        status_icon = "✅" if status == "PASS" else "❌"
        print(f"{status_icon} {test_name} - {status}")
        if details:
            print(f"   Details: {details}")
            
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    headers: Dict = None, expected_status: int = None) -> Optional[requests.Response]:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            
            if expected_status and response.status_code != expected_status:
                self.log_test_result(
                    f"{method} {endpoint}", 
                    "FAIL", 
                    f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}"
                )
                return None
                
            return response
        except Exception as e:
            self.log_test_result(f"{method} {endpoint}", "FAIL", str(e))
            return None
    
    def test_authentication_endpoints(self):
        """Test authentication-related endpoints"""
        print("\n=== Authentication Tests ===")
        
        # Test 1: User Registration
        register_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = self.make_request('POST', '/register/', register_data, expected_status=201)
        if response:
            self.test_data['test_user_id'] = response.json().get('id')
            self.log_test_result("User Registration", "PASS")
        
        # Test 2: User Login
        login_data = {
            "username": "dicoding",
            "password": "1234qwer!@#$"
        }
        
        response = self.make_request('POST', '/login/', login_data, expected_status=200)
        if response:
            tokens = response.json()
            self.tokens['regular_user'] = {
                'access': tokens.get('access'),
                'refresh': tokens.get('refresh')
            }
            self.log_test_result("User Login", "PASS")
        
        # Test 3: Super User Login
        super_login_data = {
            "username": "Aras",
            "password": "1234qwer!@#$"
        }
        
        response = self.make_request('POST', '/login/', super_login_data, expected_status=200)
        if response:
            tokens = response.json()
            self.tokens['super_user'] = {
                'access': tokens.get('access'),
                'refresh': tokens.get('refresh')
            }
            self.log_test_result("Super User Login", "PASS")
    
    def test_user_endpoints(self):
        """Test user management endpoints"""
        print("\n=== User Management Tests ===")
        
        regular_headers = {'Authorization': f"Bearer {self.tokens['regular_user']['access']}"}
        super_headers = {'Authorization': f"Bearer {self.tokens['super_user']['access']}"}
        
        # Test 1: Get Current User Profile (by accessing own user detail)
        # First get the user ID from the token claims or by listing users with super user
        response = self.make_request('GET', '/users/', super_headers, expected_status=200)
        if response:
            users = response.json()
            if isinstance(users, list) and len(users) > 0:
                # Find the regular user
                regular_user = next((u for u in users if u.get('username') == 'dicoding'), None)
                if regular_user:
                    user_id = regular_user.get('id')
                    
                    # Test getting own profile
                    response = self.make_request('GET', f'/users/{user_id}/', regular_headers, expected_status=200)
                    if response:
                        self.log_test_result("Get Own User Profile", "PASS")
                    
                    # Test getting other user profile (should fail for regular user)
                    other_user = next((u for u in users if u.get('username') == 'Aras'), None)
                    if other_user:
                        other_user_id = other_user.get('id')
                        response = self.make_request('GET', f'/users/{other_user_id}/', regular_headers, expected_status=403)
                        if response is None:  # Expected failure
                            self.log_test_result("Access Other User Profile (Forbidden)", "PASS")
                
                    # Test super user accessing any profile
                    response = self.make_request('GET', f'/users/{user_id}/', super_headers, expected_status=200)
                    if response:
                        self.log_test_result("Super User Access Any Profile", "PASS")
        
        # Test 2: List Users (admin/superuser only)
        response = self.make_request('GET', '/users/', super_headers, expected_status=200)
        if response:
            self.log_test_result("List Users (Super User)", "PASS")
        
        # Test 3: Regular user trying to list users (should fail)
        response = self.make_request('GET', '/users/', regular_headers, expected_status=403)
        if response is None:  # Expected failure
            self.log_test_result("List Users (Regular User Forbidden)", "PASS")
    
    def test_event_endpoints(self):
        """Test event management endpoints"""
        print("\n=== Event Management Tests ===")
        
        # Regular user headers
        regular_headers = {'Authorization': f"Bearer {self.tokens['regular_user']['access']}"}
        # Super user headers
        super_headers = {'Authorization': f"Bearer {self.tokens['super_user']['access']}"}
        
        # Test 1: List Events (public endpoint)
        response = self.make_request('GET', '/events/', expected_status=200)
        if response:
            self.log_test_result("List Events", "PASS")
        
        # Test 2: Create Event (should succeed with proper data)
        event_data = {
            "title": f"Test Event {int(time.time())}",
            "description": "Test Event Description",
            "venue": "Test Venue",
            "address": "Test Address",
            "city": "Test City",
            "country": "Test Country",
            "start_date": "2024-12-01T10:00:00Z",
            "end_date": "2024-12-01T18:00:00Z",
            "capacity": 100,
            "price": 50.00,
            "status": "draft"
        }
        
        response = self.make_request('POST', '/events/', event_data, super_headers, expected_status=201)
        if response:
            event_id = response.json().get('id')
            self.test_data['event_id'] = event_id
            self.log_test_result("Create Event", "PASS")
        
        # Test 3: Get Specific Event
        if 'event_id' in self.test_data:
            response = self.make_request('GET', f'/events/{self.test_data["event_id"]}/', super_headers, expected_status=200)
            if response:
                self.log_test_result("Get Event Details", "PASS")
    
    def test_ticket_endpoints(self):
        """Test ticket management endpoints"""
        print("\n=== Ticket Management Tests ===")
        
        super_headers = {'Authorization': f"Bearer {self.tokens['super_user']['access']}"}
        
        # Test 1: Create Ticket Type
        if 'event_id' in self.test_data:
            ticket_data = {
                "event": self.test_data['event_id'],
                "name": "General Admission",
                "description": "General admission ticket",
                "price": 50.00,
                "quantity": 100
            }
            
            response = self.make_request('POST', '/ticket-types/', ticket_data, super_headers, expected_status=201)
            if response:
                ticket_data = response.json()
                ticket_type_id = ticket_data.get('id')
                self.test_data['ticket_type_id'] = ticket_type_id
                self.log_test_result("Create Ticket Type", "PASS")
            
            # Test 2: List Ticket Types
            response = self.make_request('GET', '/ticket-types/', super_headers, expected_status=200)
            if response:
                self.log_test_result("List Ticket Types", "PASS")
    
    def test_registration_endpoints(self):
        """Test registration management endpoints"""
        print("\n=== Registration Management Tests ===")
        
        regular_headers = {'Authorization': f"Bearer {self.tokens['regular_user']['access']}"}
        
        # Test 1: Create Registration
        if 'event_id' in self.test_data and 'ticket_type_id' in self.test_data:
            reg_data = {
                "event": self.test_data['event_id'],
                "ticket_type": self.test_data['ticket_type_id'],
                "quantity": 1,
                "total_amount": 50.00
            }
            
            response = self.make_request('POST', '/registrations/', reg_data, regular_headers, expected_status=201)
            if response:
                reg_data = response.json()
                reg_id = reg_data.get('id')
                self.test_data['registration_id'] = reg_id
                self.log_test_result("Create Registration", "PASS")
            
            # Test 2: List Registrations
            response = self.make_request('GET', '/registrations/', regular_headers, expected_status=200)
            if response:
                self.log_test_result("List Registrations", "PASS")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting DicoEvent API Test Suite")
        print("=" * 50)
        
        try:
            # Run test suites in order
            self.test_authentication_endpoints()
            self.test_user_endpoints()
            self.test_event_endpoints()
            self.test_ticket_endpoints()
            self.test_registration_endpoints()
            
            print("\n" + "=" * 50)
            print("✅ All test suites completed!")
            
        except Exception as e:
            print(f"\n❌ Test suite failed with error: {e}")

def main():
    tester = DicoEventAPITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()