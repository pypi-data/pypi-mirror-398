"""F5 XC SDK exceptions."""

from __future__ import annotations

from typing import Any


class F5XCError(Exception):
    """Base exception for all F5 XC SDK errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        body: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.body = body
        super().__init__(f"{status_code}: {message}")


class F5XCAuthError(F5XCError):
    """401 Unauthorized - authentication failed."""
    pass


class F5XCForbiddenError(F5XCError):
    """403 Forbidden - no permission to access resource."""
    pass


class F5XCNotFoundError(F5XCError):
    """404 Not Found - resource does not exist."""
    pass


class F5XCConflictError(F5XCError):
    """409 Conflict - operation conflicts with current state."""
    pass


class F5XCRateLimitError(F5XCError):
    """429 Too Many Requests - rate limit exceeded."""
    pass


class F5XCServerError(F5XCError):
    """500 Internal Server Error."""
    pass


class F5XCServiceUnavailableError(F5XCError):
    """503 Service Unavailable - temporarily unavailable."""
    pass


class F5XCTimeoutError(F5XCError):
    """504 Gateway Timeout - server timed out."""
    pass


class F5XCPartialResultsError(F5XCError):
    """List operation returned items but also had errors."""

    def __init__(
        self,
        items: list[Any],
        errors: list[dict[str, Any]],
    ) -> None:
        self.items = items
        self.errors = errors
        super().__init__(
            status_code=200,
            message=f"Partial results: {len(items)} items, {len(errors)} errors",
            body={"items": items, "errors": errors},
        )


class F5XCValidationError(F5XCError):
    """Raised when API response fails SDK model validation.

    This typically indicates a mismatch between the SDK's generated models
    and the actual API response format. This can happen when:
    - The API has been updated but SDK hasn't been regenerated
    - The API returns data in an unexpected format
    - Optional fields are populated with unexpected types
    """

    def __init__(
        self,
        resource: str,
        operation: str,
        original_error: Exception,
        response: dict[str, Any] | None = None,
    ) -> None:
        self.resource = resource
        self.operation = operation
        self.original_error = original_error
        self.response = response
        message = (
            f"Failed to parse {resource}.{operation}() response. "
            f"This may indicate an SDK/API schema mismatch. "
            f"Original error: {original_error}"
        )
        super().__init__(
            status_code=0,  # Not an HTTP error
            message=message,
            body=response,
        )
