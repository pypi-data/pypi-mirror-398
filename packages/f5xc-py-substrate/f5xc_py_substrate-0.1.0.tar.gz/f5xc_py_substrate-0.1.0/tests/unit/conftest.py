"""Unit test fixtures for F5 XC SDK."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from f5xc_py_substrate import Client


@pytest.fixture
def mock_client(httpx_mock: HTTPXMock) -> Client:
    """Create a client with mocked HTTP responses.

    Use httpx_mock to set up expected responses before using this client.

    Example:
        def test_something(httpx_mock, mock_client):
            httpx_mock.add_response(
                url="https://test.console.ves.volterra.io/api/web/namespaces",
                json={"items": []},
            )
            result = mock_client.namespace.list()
            assert result == []
    """
    return Client(
        tenant_url="https://test.console.ves.volterra.io",
        token="test-token-12345",
    )


@pytest.fixture
def sample_namespace_response() -> dict[str, Any]:
    """Sample namespace API response."""
    return {
        "metadata": {
            "name": "test-namespace",
            "namespace": "",
            "uid": "abc-123",
            "creation_timestamp": "2024-01-01T00:00:00Z",
            "modification_timestamp": "2024-01-01T00:00:00Z",
        },
        "spec": {},
        "system_metadata": {},
    }


@pytest.fixture
def sample_list_response() -> dict[str, Any]:
    """Sample list API response."""
    return {
        "items": [
            {
                "metadata": {
                    "name": "item-1",
                    "namespace": "test-ns",
                },
            },
            {
                "metadata": {
                    "name": "item-2",
                    "namespace": "test-ns",
                },
            },
        ],
    }


@pytest.fixture
def sample_error_response() -> dict[str, Any]:
    """Sample error API response."""
    return {
        "message": "Resource not found",
        "code": 404,
    }
