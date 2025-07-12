"""Common fixtures and utilities for integration tests."""

import os
import uuid
import pytest
from typing import Generator

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from storage.redis_store import RedisStore
from memory_manager import MemoryManager


# Mark all tests in this directory as integration tests
def pytest_collection_modifyitems(items):
    """Mark all tests in the integration directory with the 'integration' marker."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)


# Test configuration - can be overridden with environment variables
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379")
TEST_PREFIX = f"test_integration_{uuid.uuid4().hex[:8]}:"  # Unique prefix for this test run


@pytest.fixture(scope="session")
def redis_store() -> Generator[RedisStore, None, None]:
    """Create a Redis store for testing with a unique prefix."""
    store = RedisStore(
        redis_url=REDIS_URL,
        prefix=TEST_PREFIX,
        expire_seconds=60,  # Short expiry for tests
        framework="test_framework"
    )
    
    # Check Redis connection
    try:
        store.client.ping()
    except Exception as e:
        pytest.skip(f"Redis not available at {REDIS_URL}: {e}")
    
    yield store
    
    # Cleanup: delete all keys with our test prefix
    for key in store.client.keys(f"{TEST_PREFIX}*"):
        store.client.delete(key)


@pytest.fixture(scope="session")
def memory_manager(redis_store: RedisStore) -> MemoryManager:
    """Create a memory manager with our test Redis store."""
    return MemoryManager(redis_store=redis_store)


@pytest.fixture
def unique_session_id() -> str:
    """Generate a unique session ID for tests."""
    return f"test_session_{uuid.uuid4().hex[:8]}"
