"""
Pytest configuration and fixtures for the Finance Tracker test suite.

This module provides:
- Custom CLI options (--skip-llm, --skip-external-api)
- Session-scoped authenticated client fixture with lifecycle management
- LLM mocking with max 3 real calls limit
- Debug export on test failure
"""

import os
import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator, Generator, Optional
from unittest.mock import MagicMock, patch
import uuid

import pytest
import httpx
from faker import Faker

# Test configuration from environment
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
DATA_DIR = os.getenv("DATA_DIR", "/app/data")

fake = Faker()

# Track test failures for debug export
_test_failures: list[str] = []


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom CLI options for test control."""
    parser.addoption(
        "--skip-llm",
        action="store_true",
        default=os.getenv("SKIP_LLM", "false").lower() == "true",
        help="Skip all real LLM API calls, use mocks instead",
    )
    parser.addoption(
        "--skip-external-api",
        action="store_true",
        default=os.getenv("SKIP_EXTERNAL_API", "false").lower() == "true",
        help="Skip all external API calls (LLM and Telegram)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "llm: marks tests that use LLM (may be skipped)")
    config.addinivalue_line("markers", "e2e: marks end-to-end tests")
    config.addinivalue_line("markers", "integration: marks integration tests")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator:
    """Hook to track test failures for debug export."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        _test_failures.append(item.name)


# ============================================================================
# LLM Mocking Fixtures
# ============================================================================

class LLMCallTracker:
    """Tracks LLM API calls and enforces the 3-call limit."""
    
    def __init__(self, max_real_calls: int = 3, skip_llm: bool = False):
        self.max_real_calls = max_real_calls
        self.skip_llm = skip_llm
        self.call_count = 0
        self._original_generate_content: Optional[callable] = None
    
    def should_use_real_api(self) -> bool:
        """Returns True if we should use the real API for this call."""
        if self.skip_llm:
            return False
        return self.call_count < self.max_real_calls
    
    def increment_call(self) -> None:
        """Increment the call counter."""
        self.call_count += 1
    
    def get_mock_response(self) -> MagicMock:
        """Return a mock response for LLM calls."""
        mock_response = MagicMock()
        mock_response.text = "Other"  # Default category for mocked calls
        return mock_response


@pytest.fixture(scope="session")
def llm_tracker(request: pytest.FixtureRequest) -> LLMCallTracker:
    """Session-scoped LLM call tracker."""
    skip_llm = request.config.getoption("--skip-llm")
    skip_external = request.config.getoption("--skip-external-api")
    return LLMCallTracker(max_real_calls=3, skip_llm=skip_llm or skip_external)


@pytest.fixture
def llm_mock(llm_tracker: LLMCallTracker):
    """
    Fixture that manages LLM mocking with a 3-call limit.
    
    First 3 calls go through to the real API (unless --skip-llm is set).
    Subsequent calls return mocked responses.
    """
    original_generate_content = None
    
    def patched_generate_content(self, *args, **kwargs):
        """Wrapper that enforces the call limit."""
        nonlocal original_generate_content
        
        if llm_tracker.should_use_real_api():
            llm_tracker.increment_call()
            if original_generate_content:
                return original_generate_content(self, *args, **kwargs)
            return llm_tracker.get_mock_response()
        else:
            return llm_tracker.get_mock_response()
    
    try:
        from google.genai import models
        original_generate_content = models.Model.generate_content
        
        with patch.object(models.Model, 'generate_content', patched_generate_content):
            yield llm_tracker
    except ImportError:
        # google.genai not installed or available
        yield llm_tracker


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def api_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async HTTP client for making API requests."""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def test_user_credentials() -> dict:
    """Generate random credentials for the test user."""
    return {
        "username": f"test_user_{uuid.uuid4().hex[:8]}",
        "password": f"TestPassword_{uuid.uuid4().hex[:12]}!",
    }


@pytest.fixture(scope="session")
async def auth_user(
    test_user_credentials: dict,
    request: pytest.FixtureRequest,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Session-scoped authenticated user fixture.
    
    Lifecycle:
    1. Register a unique test user
    2. Login and get JWT token
    3. Yield authenticated client for tests
    4. On failure: Export user data for debugging
    5. Always: Delete the test user
    """
    credentials = test_user_credentials
    token: Optional[str] = None
    
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0) as client:
        # Step 1: Register the test user
        register_response = await client.post(
            "/api/auth/register",
            json=credentials,
        )
        
        if register_response.status_code != 200:
            pytest.fail(f"Failed to register test user: {register_response.text}")
        
        # Step 2: Login to get the token
        login_response = await client.post(
            "/api/auth/token",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if login_response.status_code != 200:
            pytest.fail(f"Failed to login test user: {login_response.text}")
        
        token_data = login_response.json()
        token = token_data["access_token"]
        
        # Create authenticated client
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=30.0,
            headers=auth_headers,
        ) as auth_client:
            try:
                yield auth_client
            finally:
                # Step 4: Export data if tests failed
                if _test_failures:
                    await _export_debug_data(auth_client, credentials["username"])
                
                # Step 5: Always delete the test user
                try:
                    delete_response = await auth_client.delete("/api/auth/me")
                    if delete_response.status_code not in (200, 204):
                        print(f"Warning: Failed to delete test user: {delete_response.text}")
                except Exception as e:
                    print(f"Warning: Exception during user cleanup: {e}")


async def _export_debug_data(client: httpx.AsyncClient, username: str) -> None:
    """Export user configuration data for debugging failed tests."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = os.path.join(DATA_DIR, f"debug_{username}_{timestamp}.json")
        
        # Export configuration
        config_response = await client.get("/api/config/export")
        if config_response.status_code == 200:
            debug_data = {
                "username": username,
                "timestamp": timestamp,
                "failed_tests": _test_failures,
                "config": config_response.json() if config_response.headers.get("content-type", "").startswith("application/json") else config_response.text,
            }
            
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(debug_file, "w") as f:
                json.dump(debug_data, f, indent=2)
            
            print(f"Debug data exported to: {debug_file}")
    except Exception as e:
        print(f"Warning: Failed to export debug data: {e}")


# ============================================================================
# Synchronous Client Fixtures (for non-async tests)
# ============================================================================

@pytest.fixture
def sync_api_client() -> Generator[httpx.Client, None, None]:
    """Synchronous HTTP client for making API requests."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="module")
def sync_auth_user() -> Generator[httpx.Client, None, None]:
    """
    Module-scoped synchronous authenticated user fixture.
    
    Similar to auth_user but for synchronous tests.
    """
    credentials = {
        "username": f"test_user_{uuid.uuid4().hex[:8]}",
        "password": f"TestPassword_{uuid.uuid4().hex[:12]}!",
    }
    
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        # Register the test user
        register_response = client.post(
            "/api/auth/register",
            json=credentials,
        )
        
        if register_response.status_code != 200:
            pytest.fail(f"Failed to register test user: {register_response.text}")
        
        # Login to get the token
        login_response = client.post(
            "/api/auth/token",
            data={
                "username": credentials["username"],
                "password": credentials["password"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if login_response.status_code != 200:
            pytest.fail(f"Failed to login test user: {login_response.text}")
        
        token = login_response.json()["access_token"]
        
        # Create authenticated client
        with httpx.Client(
            base_url=API_BASE_URL,
            timeout=30.0,
            headers={"Authorization": f"Bearer {token}"},
        ) as auth_client:
            try:
                yield auth_client
            finally:
                # Always delete the test user
                try:
                    auth_client.delete("/api/auth/me")
                except Exception as e:
                    print(f"Warning: Exception during user cleanup: {e}")


# ============================================================================
# Playwright Fixtures for E2E Tests
# ============================================================================

@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    """Configure Playwright browser context for tests."""
    return {
        "base_url": FRONTEND_URL,
        "viewport": {"width": 1280, "height": 720},
    }
