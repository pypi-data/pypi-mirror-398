"""Integration test fixtures for F5 XC SDK."""

from __future__ import annotations

import atexit
import os
import time
from collections.abc import Generator

import pytest
from dotenv import load_dotenv

from f5xc_py_substrate import Client
from f5xc_py_substrate.exceptions import F5XCError

# Track namespace for cleanup on unexpected exit
_cleanup_namespace: str | None = None
_cleanup_client: Client | None = None


def _emergency_cleanup() -> None:
    """Clean up test namespace on unexpected exit (atexit handler)."""
    if _cleanup_namespace and _cleanup_client:
        print(f"\nEmergency cleanup: deleting namespace {_cleanup_namespace}")
        try:
            _cleanup_client.namespace.cascade_delete(name=_cleanup_namespace)
        except Exception as e:
            print(f"Emergency cleanup failed: {e}")


atexit.register(_emergency_cleanup)


@pytest.fixture(scope="session")
def client() -> Client:
    """Create SDK client from env vars or env file.

    Credentials are loaded from --env-file (default: .env) in pytest_configure.

    Required variables:
    - F5XC_TENANT_URL: Full tenant URL (e.g., https://example.console.ves.volterra.io)
    - F5XC_API_TOKEN: API token with appropriate permissions

    Usage:
        pytest tests/integration/ --env-file=.env.test
    """
    tenant_url = os.environ.get("F5XC_TENANT_URL")
    token = os.environ.get("F5XC_API_TOKEN")

    if not tenant_url or not token:
        pytest.skip(
            "F5XC credentials not configured. "
            "Set F5XC_TENANT_URL and F5XC_API_TOKEN environment variables "
            "or create a .env file."
        )

    return Client(tenant_url=tenant_url, token=token)


@pytest.fixture(scope="session")
def test_namespace(client: Client, request: pytest.FixtureRequest) -> Generator[str, None, None]:
    """Create test namespace, yield it, cascade delete on teardown.

    Creates a unique namespace for test isolation. All namespaced resources
    created during tests should use this namespace. On teardown, the namespace
    is deleted with cascade=True to clean up all contained resources.

    Uses both pytest finalizer and atexit for robust cleanup even on crashes.
    """
    global _cleanup_namespace, _cleanup_client

    ns_name = f"sdk-test-{int(time.time())}"

    # Register for emergency cleanup
    _cleanup_namespace = ns_name
    _cleanup_client = client

    def cleanup() -> None:
        """Delete the test namespace with cascade."""
        global _cleanup_namespace
        print(f"\nDeleting test namespace: {ns_name}")
        try:
            client.namespace.cascade_delete(name=ns_name)
            _cleanup_namespace = None  # Clear so atexit doesn't double-delete
        except F5XCError as e:
            print(f"WARNING: Failed to delete test namespace {ns_name}: {e}")
            print("Manual cleanup may be required.")

    # Register finalizer - runs even if tests fail
    request.addfinalizer(cleanup)

    print(f"\nCreating test namespace: {ns_name}")

    # Create namespace (namespace parameter is empty string for namespace objects)
    client.namespace.create(
        namespace="", name=ns_name, description="SDK integration test namespace"
    )

    yield ns_name


@pytest.fixture
def unique_name() -> str:
    """Generate a unique resource name for tests."""
    return f"test-{int(time.time() * 1000) % 100000}"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        "--env-file",
        action="store",
        default=".env",
        help="Path to env file for credentials (default: .env)",
    )
    parser.addoption(
        "--cleanup-stale",
        action="store_true",
        default=False,
        help="Clean up stale sdk-test-* namespaces from previous failed runs",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest: register markers, load env file, handle cleanup."""
    # Register custom markers
    config.addinivalue_line(
        "markers",
        "order(index): Set test execution order. Lower numbers run first.",
    )

    env_file = config.getoption("--env-file", default=".env")
    load_dotenv(env_file, override=True)

    if config.getoption("--cleanup-stale"):
        tenant_url = os.environ.get("F5XC_TENANT_URL")
        token = os.environ.get("F5XC_API_TOKEN")

        if not tenant_url or not token:
            print("Cannot cleanup: F5XC credentials not configured")
            return

        client = Client(tenant_url=tenant_url, token=token)
        namespaces = client.namespace.list()

        stale_ns = [
            ns.name for ns in namespaces
            if ns.name and ns.name.startswith("sdk-test-")
        ]

        if not stale_ns:
            print("No stale sdk-test-* namespaces found")
            return

        print(f"Found {len(stale_ns)} stale namespace(s): {stale_ns}")
        for ns_name in stale_ns:
            print(f"  Deleting {ns_name}...")
            try:
                client.namespace.cascade_delete(name=ns_name)
                print(f"  Deleted {ns_name}")
            except F5XCError as e:
                print(f"  Failed to delete {ns_name}: {e}")
