"""Simple endpoint-by-endpoint API testing script."""
import requests
import json
import time
import sys

# API base URL
BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, url, data=None, expected_status=200, show_response=True):
    """Test a single endpoint and print results."""
    print(f"\n{'=' * 80}")
    print(f"  Testing {name}")
    print(f"{'=' * 80}")
    
    full_url = f"{BASE_URL}/{url}"
    print(f"URL: {full_url}")
    print(f"Method: {method}")
    
    if data:
        print(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        start_time = time.time()
        
        if method.upper() == 'GET':
            response = requests.get(full_url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(full_url, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(full_url, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(full_url, timeout=10)
        else:
            print(f"ERROR: Unknown method {method}")
            return False
        
        elapsed_time = time.time() - start_time
        print(f"Response time: {elapsed_time:.2f}s")
        print(f"Status code: {response.status_code} (Expected: {expected_status})")
        
        if show_response and response.text:
            try:
                formatted_json = json.dumps(response.json(), indent=2)
                print(f"Response: {formatted_json}")
            except:
                print(f"Response: {response.text}")
        
        success = response.status_code == expected_status
        print(f"Test {'PASSED' if success else 'FAILED'} ✓" if success else "Test FAILED ✗")
        return success, response
        
    except requests.exceptions.ConnectionError as e:
        print(f"ERROR: Connection failed - {str(e)}")
        return False, None
    except requests.exceptions.Timeout:
        print(f"ERROR: Request timed out after 10 seconds")
        return False, None
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def main():
    """Run all tests in sequence."""
    tests = [
        # System endpoints
        ("Health Check", "GET", "health", None, 200),
        ("Version", "GET", "version", None, 200),
        
        # Memory CRUD operations
        ("Create Memory", "POST", "memories", {
            "content": "Test memory",
            "metadata": {"source": "endpoint_test"},
            "importance": 0.7,
            "tier": "working"
        }, 201),
    ]
    
    print("\nAPI Endpoint Test Runner")
    print("=" * 80)
    
    # Test connectivity first
    print("Checking API connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"API is responsive with status code: {response.status_code}")
    except Exception as e:
        print(f"ERROR: Cannot connect to API at {BASE_URL}")
        print(f"Exception: {str(e)}")
        sys.exit(1)
    
    # Run all tests
    results = []
    memory_id = None
    
    for test in tests:
        name, method, url, data, expected_status = test
        success, response = test_endpoint(name, method, url, data, expected_status)
        results.append((name, success))
        
        # Save memory_id from create operation for subsequent tests
        if success and name == "Create Memory" and response:
            try:
                memory_id = response.json().get("memory_id")
                if memory_id:
                    print(f"Created memory with ID: {memory_id}")
                    
                    # Add additional memory-specific tests that need the memory_id
                    if memory_id:
                        # Test get memory
                        get_success, _ = test_endpoint("Get Memory", "GET", f"memories/{memory_id}", None, 200)
                        results.append(("Get Memory", get_success))
                        
                        # Test update memory
                        update_data = {
                            "content": "Updated test memory",
                            "importance": 0.8
                        }
                        update_success, _ = test_endpoint("Update Memory", "PUT", f"memories/{memory_id}", update_data, 200)
                        results.append(("Update Memory", update_success))
                        
                        # Test delete memory
                        delete_success, _ = test_endpoint("Delete Memory", "DELETE", f"memories/{memory_id}", None, 204, False)
                        results.append(("Delete Memory", delete_success))
            except Exception as e:
                print(f"Error extracting memory_id: {str(e)}")
    
    # Test memory listing
    list_success, _ = test_endpoint("List Memories", "GET", "memories", None, 200)
    results.append(("List Memories", list_success))
    
    # Test metadata search
    search_data = {
        "query": {"source": "endpoint_test"},
        "limit": 5
    }
    search_success, _ = test_endpoint("Search Memories", "POST", "memories/search", search_data, 200)
    results.append(("Search Memories", search_success))
    
    # Test set context
    context_success, _ = test_endpoint("Set Context", "POST", "context", {
        "component_id": "test_component",
        "session_id": "test_session_002"
    }, 204, False)
    results.append(("Set Context", context_success))
    
    # Print summary
    print("\n" + "=" * 80)
    print("  Test Summary")
    print("=" * 80)
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name}: {status}")
    
    print("-" * 80)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    print(f"Overall Status: {'✓ PASSED' if passed == total else '✗ FAILED'}")

if __name__ == "__main__":
    main()
