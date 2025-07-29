"""
Test script for the Azentiq Memory Manager API.

This script will create a test session, add memories,
retrieve them, and test various API endpoints.
"""
import requests
import json
from typing import Dict, Any
import uuid
import sys
import time

# Define base URL - adjust if needed
BASE_URL = "http://localhost:8000"

# Define request timeout (in seconds)
TIMEOUT = 5

# Whether to continue tests after a failure
CONTINUE_ON_ERROR = False


def print_header(message: str) -> None:
    """Print a formatted header for test sections."""
    print("\n" + "=" * 80)
    print(f"  {message}")
    print("=" * 80)


def print_response(response: requests.Response) -> None:
    """Print formatted response details."""
    print(f"Status: {response.status_code}")
    print("Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print("Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print(response.text)
    except Exception as e:
        print(f"Error processing response: {str(e)}")
    print("-" * 80)


def test_health() -> None:
    """Test the health check endpoint."""
    print_header("Testing Health Check Endpoint")
    response = safe_request(requests.get, f"{BASE_URL}/health")
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_version() -> None:
    """Test the version endpoint."""
    print_header("Testing Version Endpoint")
    response = safe_request(requests.get, f"{BASE_URL}/version")
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_set_context() -> None:
    """Test setting component context."""
    print_header("Testing Set Context")
    data = {
        "component_id": "test_component",
        "session_id": "test_session_001"
    }
    response = safe_request(requests.post, f"{BASE_URL}/context", json=data)
    if response:
        print_response(response)
        assert response.status_code == 204
        return True
    return False


def test_create_memory() -> None:
    """Test creating a memory."""
    print_header("Testing Create Memory")
    data = {
        "content": "This is a test memory",
        "metadata": {
            "type": "test",
            "source": "api_test"
        },
        "importance": 0.8,
        "tier": "working",
        "session_id": "test_session_001"
    }
    print(f"Sending data: {json.dumps(data, indent=2)}")
    response = safe_request(requests.post, f"{BASE_URL}/memories", json=data)
    if response:
        print_response(response)
        try:
            assert response.status_code == 201
            memory_id = response.json().get("memory_id")
            if memory_id:
                print(f"Successfully created memory with ID: {memory_id}")
                return memory_id
            else:
                print("ERROR: Response status was 201 but no memory_id in response!")
                print(f"Full response: {response.text}")
        except AssertionError:
            print(f"ERROR: Expected status code 201 but got {response.status_code}")
        except Exception as e:
            print(f"ERROR processing create memory response: {str(e)}")
    else:
        print("ERROR: Failed to get response from create memory endpoint")
    return None


def test_get_memory(memory_id: str) -> None:
    """Test retrieving a memory by ID."""
    print_header(f"Testing Get Memory: {memory_id}")
    response = safe_request(requests.get, f"{BASE_URL}/memories/{memory_id}")
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_update_memory(memory_id: str) -> None:
    """Test updating a memory."""
    print_header(f"Testing Update Memory: {memory_id}")
    data = {
        "content": "This memory has been updated",
        "importance": 0.9
    }
    response = safe_request(requests.put, f"{BASE_URL}/memories/{memory_id}", json=data)
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_list_memories() -> None:
    """Test listing memories."""
    print_header("Testing List Memories")
    response = safe_request(requests.get, f"{BASE_URL}/memories?limit=10&offset=0")
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_search_memories() -> None:
    """Test searching memories by metadata."""
    print_header("Testing Search Memories")
    data = {
        "query": {
            "type": "test"
        },
        "limit": 10
    }
    response = safe_request(requests.post, f"{BASE_URL}/memories/search", json=data)
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_add_conversation_turn() -> None:
    """Test adding a conversation turn."""
    print_header("Testing Add Conversation Turn")
    data = {
        "content": "This is a test message",
        "role": "user",
        "importance": 0.7
    }
    response = safe_request(requests.post, f"{BASE_URL}/sessions/test_session_001/turns", json=data)
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_get_conversation_turns() -> None:
    """Test getting conversation history."""
    print_header("Testing Get Conversation Turns")
    response = safe_request(requests.get, f"{BASE_URL}/sessions/test_session_001/turns?n_turns=5")
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_generate_prompt() -> None:
    """Test generating a prompt with memory integration."""
    print_header("Testing Generate Prompt")
    data = {
        "system_message": "You are a helpful assistant.",
        "user_query": "What do you know about me?",
        "max_short_term_turns": 5,
        "include_working_memory": True
    }
    response = safe_request(requests.post, f"{BASE_URL}/sessions/test_session_001/prompt", json=data)
    if response:
        print_response(response)
        assert response.status_code == 200
        return True
    return False


def test_delete_memory(memory_id: str) -> None:
    """Test deleting a memory."""
    print_header(f"Testing Delete Memory: {memory_id}")
    response = safe_request(requests.delete, f"{BASE_URL}/memories/{memory_id}")
    if response:
        print_response(response)
        assert response.status_code == 204
        return True
    return False


def safe_request(method, url, **kwargs):
    """Make a safe request with error handling."""
    if 'timeout' not in kwargs:
        kwargs['timeout'] = TIMEOUT
        
    try:
        return method(url, **kwargs)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}. Make sure the API server is running!")
        if not CONTINUE_ON_ERROR:
            sys.exit(1)
        return None
    except requests.exceptions.Timeout:
        print(f"ERROR: Connection to {url} timed out after {TIMEOUT} seconds!")
        if not CONTINUE_ON_ERROR:
            sys.exit(1)
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error making request to {url}: {str(e)}")
        if not CONTINUE_ON_ERROR:
            sys.exit(1)
        return None

def run_all_tests() -> None:
    """Run all API tests."""
    try:
        # First verify the API is reachable
        print_header("Checking API connectivity")
        response = safe_request(requests.get, f"{BASE_URL}/health")
        if not response:
            print("Cannot continue tests - API is not responding")
            return
        print("API is responding! Proceeding with tests...\n")
            
        test_health()
        test_version()
        test_set_context()
        memory_id = test_create_memory()
        
        if memory_id:
            test_get_memory(memory_id)
            test_update_memory(memory_id)
            test_list_memories()
            test_search_memories()
            test_add_conversation_turn()
            test_get_conversation_turns()
            test_generate_prompt()
            test_delete_memory(memory_id)
        else:
            print("Skipping remaining tests due to failure creating memory")
        
        print_header("All Tests Completed Successfully! ✅")
    except AssertionError as e:
        print_header(f"❌ Test Failed: {str(e)}")
    except Exception as e:
        print_header(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
