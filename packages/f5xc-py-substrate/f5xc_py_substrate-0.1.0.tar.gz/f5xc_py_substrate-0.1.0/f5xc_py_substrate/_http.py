"""HTTP client wrapper for F5 XC API."""

from __future__ import annotations

from typing import Any

import httpx

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

# Map HTTP status codes to exception classes
STATUS_TO_EXCEPTION: dict[int, type[F5XCError]] = {
    401: F5XCAuthError,
    403: F5XCForbiddenError,
    404: F5XCNotFoundError,
    409: F5XCConflictError,
    429: F5XCRateLimitError,
    500: F5XCServerError,
    503: F5XCServiceUnavailableError,
    504: F5XCTimeoutError,
}


class HTTPClient:
    """Wrapper around httpx.Client for F5 XC API calls."""

    def __init__(
        self,
        base_url: str,
        token: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._token = token
        self._client = client or httpx.Client(timeout=30.0)

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"APIToken {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle response, raising typed exceptions for errors."""
        if response.is_success:
            if response.status_code == 204 or not response.content:
                return {}
            result: dict[str, Any] = response.json()
            return result

        # Parse error body
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        # Get error message
        message = (
            body.get("message") or body.get("error") or response.reason_phrase or "Unknown error"
        )

        # Raise typed exception (from None suppresses internal traceback)
        exception_class = STATUS_TO_EXCEPTION.get(response.status_code, F5XCError)
        raise exception_class(
            status_code=response.status_code,
            message=message,
            body=body,
        ) from None

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request."""
        response = self._client.get(
            f"{self._base_url}{path}",
            params=params,
            headers=self._headers(),
        )
        return self._handle_response(response)

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request."""
        response = self._client.post(
            f"{self._base_url}{path}",
            json=json,
            headers=self._headers(),
        )
        return self._handle_response(response)

    def put(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a PUT request."""
        response = self._client.put(
            f"{self._base_url}{path}",
            json=json,
            headers=self._headers(),
        )
        return self._handle_response(response)

    def delete(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a DELETE request.

        Note: Some APIs require DELETE with a body (e.g., cascade=True).
        We use httpx.Request to support this since httpx.Client.delete()
        doesn't accept json parameter directly.
        """
        url = f"{self._base_url}{path}"
        if json is not None:
            # httpx.Client.delete doesn't support json param, use request() instead
            import json as json_module
            response = self._client.request(
                "DELETE",
                url,
                content=json_module.dumps(json),
                headers=self._headers(),
            )
        else:
            response = self._client.delete(url, headers=self._headers())
        return self._handle_response(response)
