"""Unit tests for HTTP client and error handling."""

from __future__ import annotations

from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from f5xc_py_substrate import Client
from f5xc_py_substrate.exceptions import (
    F5XCAuthError,
    F5XCConflictError,
    F5XCError,
    F5XCForbiddenError,
    F5XCNotFoundError,
    F5XCRateLimitError,
    F5XCServerError,
    F5XCServiceUnavailableError,
    F5XCTimeoutError,
)


class TestHttpErrorHandling:
    """Test HTTP error handling and exception mapping."""

    @pytest.mark.parametrize(
        "status_code,expected_exception",
        [
            (401, F5XCAuthError),
            (403, F5XCForbiddenError),
            (404, F5XCNotFoundError),
            (409, F5XCConflictError),
            (429, F5XCRateLimitError),
            (500, F5XCServerError),
            (503, F5XCServiceUnavailableError),
            (504, F5XCTimeoutError),
        ],
    )
    def test_status_code_mapping(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
        status_code: int,
        expected_exception: type,
    ) -> None:
        """Test that HTTP status codes map to correct exception types."""
        # Use list endpoint which has no path params to avoid generator path bug
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            status_code=status_code,
            json={"message": f"Error {status_code}"},
        )

        with pytest.raises(expected_exception) as exc_info:
            mock_client.namespace.list()

        assert exc_info.value.status_code == status_code
        assert f"Error {status_code}" in exc_info.value.message

    def test_unknown_error_status(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
    ) -> None:
        """Test that unknown error status codes raise base F5XCError."""
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            status_code=418,  # I'm a teapot
            json={"message": "I'm a teapot"},
        )

        with pytest.raises(F5XCError) as exc_info:
            mock_client.namespace.list()

        assert exc_info.value.status_code == 418

    def test_error_body_preserved(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
    ) -> None:
        """Test that error response body is preserved in exception."""
        error_body = {
            "message": "Validation failed",
            "code": 400,
            "details": {"field": "name", "error": "required"},
        }
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            status_code=400,
            json=error_body,
        )

        with pytest.raises(F5XCError) as exc_info:
            mock_client.namespace.list()

        assert exc_info.value.body == error_body


class TestHttpSuccessResponses:
    """Test successful HTTP responses."""

    def test_list_returns_items(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
        sample_list_response: dict[str, Any],
    ) -> None:
        """Test that list returns items array."""
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            json=sample_list_response,
        )

        result = mock_client.namespace.list()
        assert len(result) == 2
        # List items store extra fields as dicts (model has extra="allow")
        assert result[0].metadata["name"] == "item-1"

    def test_empty_list_response(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
    ) -> None:
        """Test that empty list returns empty array."""
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            json={"items": []},
        )

        result = mock_client.namespace.list()
        assert result == []


class TestHttpHeaders:
    """Test HTTP headers are set correctly."""

    def test_authorization_header(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
    ) -> None:
        """Test that Authorization header is set correctly."""
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            json={"items": []},
        )

        mock_client.namespace.list()

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "APIToken test-token-12345"

    def test_content_type_header(
        self,
        httpx_mock: HTTPXMock,
        mock_client: Client,
    ) -> None:
        """Test that Content-Type header is set for JSON."""
        httpx_mock.add_response(
            url="https://test.console.ves.volterra.io/api/web/namespaces",
            json={"items": []},
        )

        mock_client.namespace.list()

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Content-Type"] == "application/json"
