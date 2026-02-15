#!/usr/bin/env python3
"""
Health Check Script for DicoEvent Platform
Verifies that all services are running correctly
"""

import requests
import sys
from urllib.parse import urljoin

BASE_URL = "http://localhost:8001"
API_PREFIX = "/api"

def check_get_endpoint(url, description, expected_status=200):
    """Check if a GET endpoint responds correctly"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {description}: OK (Status {response.status_code})")
            return True
        else:
            print(f"❌ {description}: FAILED (Status {response.status_code}, expected {expected_status})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}: ERROR ({str(e)})")
        return False

def check_post_endpoint(url, description, data=None, expected_status=200):
    """Check if a POST endpoint responds correctly"""
    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {description}: OK (Status {response.status_code})")
            return True
        else:
            print(f"❌ {description}: FAILED (Status {response.status_code}, expected {expected_status})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}: ERROR ({str(e)})")
        return False

def main():
    print("🏥 DICAEVENT PLATFORM HEALTH CHECK")
    print("=" * 40)
    
    # Check GET endpoints
    get_checks = [
        (BASE_URL, "Server Status"),
        (urljoin(BASE_URL, API_PREFIX + "/users/"), "Users Endpoint (Auth Required)", 401),
        (urljoin(BASE_URL, API_PREFIX + "/events/"), "Events Endpoint (Auth Required)", 401),
        (urljoin(BASE_URL, API_PREFIX + "/tickets/ticket-types/"), "Ticket Types Endpoint (Auth Required)", 401),
        (urljoin(BASE_URL, API_PREFIX + "/registrations/"), "Registrations Endpoint (Auth Required)", 401),
        (urljoin(BASE_URL, API_PREFIX + "/payments/"), "Payments Endpoint (Auth Required)", 401),
    ]
    
    # Check POST endpoints
    post_checks = [
        (urljoin(BASE_URL, API_PREFIX + "/login/"), "Login Endpoint", {}, 400),  # 400 because no valid data
    ]
    
    passed = 0
    total = len(get_checks) + len(post_checks)
    
    # Run GET endpoint checks
    for check in get_checks:
        if len(check) == 3:
            url, description, expected_status = check
        else:
            url, description = check
            expected_status = 200
            
        if check_get_endpoint(url, description, expected_status):
            passed += 1
    
    # Run POST endpoint checks
    for check in post_checks:
        if len(check) == 4:
            url, description, data, expected_status = check
        else:
            url, description, data = check
            expected_status = 200
            
        if check_post_endpoint(url, description, data, expected_status):
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"HEALTH CHECK RESULT: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems operational!")
        return 0
    else:
        print("⚠️  Some services may need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())