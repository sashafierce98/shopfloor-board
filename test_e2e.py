#!/usr/bin/env python3
"""
End-to-End Testing Suite for Shopfloor Board Application
Tests all functionalities as a supervisor would use them.
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"
SESSION = requests.Session()

# Test Results Storage
test_results = {
    "test_run": datetime.now().isoformat(),
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "test_cases": []
}

def log_test(name, passed, details=""):
    """Log individual test result"""
    test_results["total_tests"] += 1
    status = "✓ PASS" if passed else "✗ FAIL"
    
    test_case = {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results["test_cases"].append(test_case)
    
    if passed:
        test_results["passed_tests"] += 1
        print(f"{status}: {name}")
    else:
        test_results["failed_tests"] += 1
        print(f"{status}: {name} - {details}")

def test_initial_login_redirect():
    """TC-1: Test redirect to setup/login when no users exist"""
    try:
        resp = SESSION.get(f"{BASE_URL}/supervisor", allow_redirects=False)
        passed = resp.status_code in [302, 303]  # Redirect status
        log_test("TC-1: Initial redirect to login", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("TC-1: Initial redirect to login", False, str(e))

def test_setup_page_loads():
    """TC-2: Test setup page for new supervisor"""
    try:
        resp = SESSION.get(f"{BASE_URL}/auth/setup")
        passed = resp.status_code == 200 and "setup" in resp.text.lower()
        log_test("TC-2: Setup page loads", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-2: Setup page loads", False, str(e))
        return False

def test_supervisor_setup_with_wrong_token():
    """TC-3: Test supervisor setup fails with wrong token"""
    try:
        data = {
            "token": "wrong-token",
            "username": "testuser",
            "password": "TestPass123!"
        }
        resp = SESSION.post(f"{BASE_URL}/auth/setup", data=data, allow_redirects=False)
        passed = resp.status_code != 302  # Should not redirect (failed auth)
        log_test("TC-3: Setup fails with wrong token", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("TC-3: Setup fails with wrong token", False, str(e))

def test_supervisor_setup_with_correct_token():
    """TC-4: Test supervisor setup succeeds with correct token"""
    try:
        data = {
            "token": "secure-token-change-me",
            "username": "supervisor_admin",
            "password": "AdminPass@123"
        }
        resp = SESSION.post(f"{BASE_URL}/auth/setup", data=data, allow_redirects=True)
        passed = resp.status_code == 200
        log_test("TC-4: Setup succeeds with correct token", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-4: Setup succeeds with correct token", False, str(e))
        return False

def test_supervisor_login_wrong_password():
    """TC-5: Test login fails with wrong password"""
    try:
        data = {
            "username": "supervisor_admin",
            "password": "WrongPassword"
        }
        resp = SESSION.post(f"{BASE_URL}/login", data=data, allow_redirects=False)
        passed = resp.status_code == 200  # Stays on login page (failed auth)
        log_test("TC-5: Login fails with wrong password", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("TC-5: Login fails with wrong password", False, str(e))

def test_supervisor_login_correct():
    """TC-6: Test supervisor login with correct credentials"""
    try:
        data = {
            "username": "supervisor_admin",
            "password": "AdminPass@123"
        }
        resp = SESSION.post(f"{BASE_URL}/login", data=data, allow_redirects=True)
        passed = resp.status_code == 200 and "TGP Bioplastics" in resp.text
        log_test("TC-6: Supervisor login succeeds", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-6: Supervisor login succeeds", False, str(e))
        return False

def test_supervisor_board_loads():
    """TC-7: Test supervisor board loads after login"""
    try:
        resp = SESSION.get(f"{BASE_URL}/supervisor")
        passed = resp.status_code == 200 and "Operations Control Board" in resp.text
        log_test("TC-7: Supervisor board loads", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-7: Supervisor board loads", False, str(e))
        return False

def test_create_task():
    """TC-8: Test creating a new task"""
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = {
            "title": "Test Task 1",
            "description": "This is a test task for QA",
            "priority": "high",
            "due_date": tomorrow,
            "assigned_worker": ""
        }
        resp = SESSION.post(f"{BASE_URL}/supervisor", data=data, allow_redirects=True)
        passed = resp.status_code == 200 and "Test Task 1" in resp.text
        log_test("TC-8: Create task succeeds", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-8: Create task succeeds", False, str(e))
        return False

def test_create_multiple_tasks():
    """TC-9: Test creating multiple tasks with different priorities"""
    try:
        tasks_created = 0
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        priorities = ["low", "medium", "critical"]
        for i, priority in enumerate(priorities):
            data = {
                "title": f"Priority Test {priority.upper()}",
                "description": f"Testing {priority} priority task",
                "priority": priority,
                "due_date": tomorrow,
                "assigned_worker": ""
            }
            resp = SESSION.post(f"{BASE_URL}/supervisor", data=data, allow_redirects=True)
            if resp.status_code == 200 and f"Priority Test {priority.upper()}" in resp.text:
                tasks_created += 1
        
        passed = tasks_created == len(priorities)
        log_test("TC-9: Create multiple tasks with different priorities", passed, 
                f"Created {tasks_created}/{len(priorities)} tasks")
        return passed
    except Exception as e:
        log_test("TC-9: Create multiple tasks with different priorities", False, str(e))
        return False

def test_create_task_with_worker():
    """TC-10: Test creating task assigned to specific worker"""
    try:
        # First check if we need to create workers (they should exist from seed)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = {
            "title": "Assigned Worker Task",
            "description": "Task assigned to a worker",
            "priority": "medium",
            "due_date": tomorrow,
            "assigned_worker": "1"  # Assuming first worker has ID 1
        }
        resp = SESSION.post(f"{BASE_URL}/supervisor", data=data, allow_redirects=True)
        passed = resp.status_code == 200 and "Assigned Worker Task" in resp.text
        log_test("TC-10: Create task with worker assignment", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-10: Create task with worker assignment", False, str(e))
        return False

def test_update_task_status():
    """TC-11: Test updating task status to 'In Progress'"""
    try:
        # First get a task ID from the board
        resp = SESSION.get(f"{BASE_URL}/supervisor")
        # Extract first task ID from the response (simple extraction)
        if "task.id }}" in resp.text or "/task/" in resp.text:
            # Try updating task with ID 1
            data = {"status": "active"}
            resp = SESSION.post(f"{BASE_URL}/task/1/status", data=data, allow_redirects=True)
            passed = resp.status_code == 200
            log_test("TC-11: Update task status to In Progress", passed, f"Status: {resp.status_code}")
            return passed
        else:
            log_test("TC-11: Update task status to In Progress", False, "Could not extract task ID")
            return False
    except Exception as e:
        log_test("TC-11: Update task status to In Progress", False, str(e))
        return False

def test_mark_task_done():
    """TC-12: Test marking task as Done"""
    try:
        data = {"status": "done"}
        resp = SESSION.post(f"{BASE_URL}/task/1/status", data=data, allow_redirects=True)
        passed = resp.status_code == 200
        log_test("TC-12: Mark task as Done", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-12: Mark task as Done", False, str(e))
        return False

def test_create_scheduled_task():
    """TC-13: Test creating a scheduled (backlog) task"""
    try:
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        data = {
            "title": "Scheduled Task for Later",
            "description": "This task will be in the backlog",
            "priority": "low",
            "due_date": tomorrow,
            "assigned_worker": "1"
        }
        resp = SESSION.post(f"{BASE_URL}/supervisor", data=data, allow_redirects=True)
        passed = resp.status_code == 200 and "Scheduled Task for Later" in resp.text
        log_test("TC-13: Create scheduled task", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-13: Create scheduled task", False, str(e))
        return False

def test_delete_task():
    """TC-14: Test deleting a task"""
    try:
        # Try to delete task with ID 2
        resp = SESSION.post(f"{BASE_URL}/task/2/delete", allow_redirects=True)
        passed = resp.status_code == 200
        log_test("TC-14: Delete task", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-14: Delete task", False, str(e))
        return False

def test_public_board_access():
    """TC-15: Test worker/public board is accessible"""
    try:
        resp = SESSION.get(f"{BASE_URL}/board")
        passed = resp.status_code == 200 and "Work Board" in resp.text
        log_test("TC-15: Public/Worker board loads", passed, f"Status: {resp.status_code}")
        return passed
    except Exception as e:
        log_test("TC-15: Public/Worker board loads", False, str(e))
        return False

def test_logout():
    """TC-16: Test logout functionality"""
    try:
        resp = SESSION.get(f"{BASE_URL}/logout", allow_redirects=True)
        passed = resp.status_code == 200
        log_test("TC-16: Logout succeeds", passed, f"Status: {resp.status_code}")
    except Exception as e:
        log_test("TC-16: Logout succeeds", False, str(e))

def test_supervisor_access_after_logout():
    """TC-17: Test supervisor board requires login after logout"""
    try:
        resp = SESSION.get(f"{BASE_URL}/supervisor", allow_redirects=False)
        passed = resp.status_code in [302, 303]  # Should redirect to login
        log_test("TC-17: Supervisor board requires login after logout", passed, 
                f"Status: {resp.status_code}")
    except Exception as e:
        log_test("TC-17: Supervisor board requires login after logout", False, str(e))

def run_all_tests():
    """Execute all test cases"""
    print("\n" + "="*70)
    print("SHOPFLOOR BOARD - END-TO-END TEST SUITE")
    print("="*70 + "\n")
    
    # Test Authentication Flow
    print("\n--- AUTHENTICATION TESTS ---")
    test_initial_login_redirect()
    test_setup_page_loads()
    test_supervisor_setup_with_wrong_token()
    test_supervisor_setup_with_correct_token()
    test_supervisor_login_wrong_password()
    test_supervisor_login_correct()
    
    # Test Supervisor Board Features
    print("\n--- SUPERVISOR BOARD TESTS ---")
    test_supervisor_board_loads()
    test_create_task()
    test_create_multiple_tasks()
    test_create_task_with_worker()
    test_create_scheduled_task()
    
    # Test Task Management
    print("\n--- TASK MANAGEMENT TESTS ---")
    test_update_task_status()
    test_mark_task_done()
    test_delete_task()
    
    # Test Worker Board
    print("\n--- WORKER BOARD TESTS ---")
    test_public_board_access()
    
    # Test Session Management
    print("\n--- SESSION MANAGEMENT TESTS ---")
    test_logout()
    test_supervisor_access_after_logout()
    
    # Print Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {test_results['total_tests']}")
    print(f"Passed: {test_results['passed_tests']} ✓")
    print(f"Failed: {test_results['failed_tests']} ✗")
    pass_rate = (test_results['passed_tests'] / test_results['total_tests'] * 100) if test_results['total_tests'] > 0 else 0
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("="*70 + "\n")
    
    return test_results

if __name__ == "__main__":
    time.sleep(2)  # Give Flask time to start
    results = run_all_tests()
    
    # Save results to JSON
    with open("/Users/mrinmayee/Desktop/shopfloor-board/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Test results saved to test_results.json")
