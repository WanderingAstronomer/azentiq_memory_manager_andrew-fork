"""Simple test script to check basic API connectivity."""
import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except requests.exceptions.Timeout:
        print("Request timed out")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_memory_create():
    """Test creating a memory."""
    print("\nTesting memory creation...")
    data = {
        "content": "This is a test memory",
        "metadata": {"source": "simple_test"},
        "tier": "working",
        "importance": 0.5
    }
    
    try:
        print("Sending POST request to /memories...")
        start = time.time()
        response = requests.post(f"{BASE_URL}/memories", json=data, timeout=10)
        elapsed = time.time() - start
        print(f"Request completed in {elapsed:.2f} seconds")
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response: {response.text}")
        return True
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    except requests.exceptions.Timeout:
        print("Request timed out after 10 seconds")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Run the simple tests."""
    print("=== Simple API Test ===\n")
    
    if not test_health():
        print("Health check failed, aborting other tests")
        return
        
    print("\nHealth check succeeded!")
    
    test_memory_create()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
