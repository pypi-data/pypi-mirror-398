"""PaymentMethod resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.payment_method.models import (
    GlobalSpecType,
    CreatePaymentMethodRequest,
    CreatePaymentMethodResponse,
    PrimaryReq,
    RoleSwapReq,
    SecondaryReq,
)


# Exclusion group mappings for get() method
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            # Allow direct field names for flexibility
            fields.add(group)
    return fields


class PaymentMethodResource:
    """API methods for payment_method.

    This API is used to allow custom operations on payment methods
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.payment_method.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def make_payment_method_primary(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make Payment Method Primary for payment_method.

        Flags a payment method as primary. Nothing changes is the payment...
        """
        path = "/api/web/namespaces/{namespace}/billing/payment_method/{name}/primary"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def make_payment_method_secondary(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make Payment Method Secondary for payment_method.

        Flags a payment method as secondary. Nothing changes is the payment...
        """
        path = "/api/web/namespaces/{namespace}/billing/payment_method/{name}/secondary"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def swap_payment_method_role(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Swap Payment Method Role for payment_method.

        Swaps payment method roles - the payment method used as a parameter...
        """
        path = "/api/web/namespaces/{namespace}/billing/payment_method/{name}/swap-primary"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def create(
        self,
        namespace: str,
        name: str,
        spec: GlobalSpecType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreatePaymentMethodResponse:
        """Create a new payment_method.

        Creates a new payment method with a specific role.

        Args:
            namespace: The namespace to create the resource in.
            name: The name of the resource.
            spec: The resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to create the resource in disabled state.
        """
        path = "/api/web/namespaces/{namespace}/billing/payment_methods"
        path = path.replace("{metadata.namespace}", namespace)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.post(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreatePaymentMethodResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("payment_method", "create", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a payment_method.

        Remove the specified payment_method

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/web/namespaces/{namespace}/billing/payment_methods/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

