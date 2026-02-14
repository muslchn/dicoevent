import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_endpoint(url, method='GET', data=None, headers=None):
    """Test an API endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method == 'PATCH':
            response = requests.patch(url, json=data, headers=headers)
        
        print(f"{method} {url} - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.text[:200]}...")
        return response
    except Exception as e:
        print(f"Error testing {method} {url}: {e}")
        return None

def main():
    print("=== DicoEvent API Test ===\n")
    
    # Test 1: User Registration
    print("1. Testing User Registration")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "User"
    }
    response = test_endpoint(f"{BASE_URL}/register/", 'POST', register_data)
    
    # Test 2: User Login
    print("\n2. Testing User Login")
    login_data = {
        "username": "dicoding",
        "password": "1234qwer!@#$"
    }
    response = test_endpoint(f"{BASE_URL}/login/", 'POST', login_data)
    
    if response and response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Test 3: Get User Profile
        print("\n3. Testing Get User Profile")
        test_endpoint(f"{BASE_URL}/users/me/", 'GET', headers=headers)
        
        # Test 4: List Events
        print("\n4. Testing List Events")
        test_endpoint(f"{BASE_URL}/events/", 'GET', headers=headers)
        
        # Test 5: Create Event (should fail for regular user)
        print("\n5. Testing Create Event (should fail)")
        event_data = {
            "title": "Test Event",
            "description": "Test Description",
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
        test_endpoint(f"{BASE_URL}/events/", 'POST', event_data, headers=headers)
    
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    main()