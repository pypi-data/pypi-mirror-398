"""CustomerSupport resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.customer_support.models import (
    CustomerSupportListItem,
    AttachmentType,
    CloseRequest,
    CloseResponse,
    CommentRequest,
    CommentResponse,
    CommentType,
    ObjectCreateMetaType,
    ObjectRefType,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    EscalationRequest,
    EscalationResponse,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    ProtobufAny,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ListSupportRequest,
    ListSupportResponse,
    PriorityRequest,
    PriorityResponse,
    RaiseTaxExemptVerificationSupportTicketRequest,
    RaiseTaxExemptVerificationSupportTicketResponse,
    ReopenRequest,
    ReopenResponse,
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


class CustomerSupportResource:
    """API methods for customer_support.

    Handles creation and listing of support issues (by tenant and...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.customer_support.CreateSpecType(...)
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: AttachmentType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new customer_support.

        Creates a new customer support ticket in our customer support...

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
        path = "/api/web/namespaces/{metadata.namespace}/customer_supports"
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
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "create", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[CustomerSupportListItem]:
        """List customer_support resources in a namespace.

        List the set of customer_support in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/namespaces/{namespace}/customer_supports"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if label_filter is not None:
            params["label_filter"] = label_filter
        if report_fields is not None:
            params["report_fields"] = report_fields
        if report_status_fields is not None:
            params["report_status_fields"] = report_status_fields

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        items = response.get("items", [])
        errors = response.get("errors", [])

        if errors:
            raise F5XCPartialResultsError(items=items, errors=errors)

        try:
            return [CustomerSupportListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a customer_support by name.

        Support ticket representation we display to customers. There's much...

        By default, excludes verbose fields (forms, references, system_metadata).
        Use include_all=True to get the complete response.

        Args:
            exclude: Additional field groups to exclude from response.
                - 'forms': Excludes create_form, replace_form
                - 'references': Excludes referring_objects, deleted/disabled_referred_objects
                - 'system_metadata': Excludes system_metadata
                You can also pass individual field names directly.
            include_all: If True, return all fields without default exclusions.
        """
        path = "/api/web/namespaces/{namespace}/customer_supports/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if response_format is not None:
            params["response_format"] = response_format

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        # Apply default exclusions unless include_all=True
        if not include_all:
            default_exclude = ["forms", "references", "system_metadata"]
            exclude = (exclude or []) + default_exclude

        if exclude:
            exclude_fields = _resolve_exclude_groups(exclude)
            # Remove excluded fields entirely from response
            filtered_response = {
                k: v for k, v in response.items()
                if k not in exclude_fields
            }
        else:
            filtered_response = response

        try:
            return GetResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "get", e, response) from e

    def list_ct_support_tickets(
        self,
        body: dict[str, Any] | None = None,
    ) -> ListSupportResponse:
        """List Ct Support Tickets for customer_support.

        Return list of support tickets for a given child tenant Note: Direct...
        """
        path = "/api/web/namespaces/system/child_tenant/support_tickets"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListSupportResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "list_ct_support_tickets", e, response) from e

    def raise_tax_exempt_verification_support_ticket(
        self,
        body: dict[str, Any] | None = None,
    ) -> RaiseTaxExemptVerificationSupportTicketResponse:
        """Raise Tax Exempt Verification Support Ticket for customer_support.

        Raises a tax exemption verification request. This will ultimately...
        """
        path = "/api/web/namespaces/system/customer_support/tax_exempt_request"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RaiseTaxExemptVerificationSupportTicketResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "raise_tax_exempt_verification_support_ticket", e, response) from e

    def admin_list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> ListResponse:
        """Admin List for customer_support.

        Similar to the List rpc but returns all tenant tickets regardless of...
        """
        path = "/api/web/namespaces/{namespace}/admin/customer_supports"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if label_filter is not None:
            params["label_filter"] = label_filter
        if report_fields is not None:
            params["report_fields"] = report_fields
        if report_status_fields is not None:
            params["report_status_fields"] = report_status_fields

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "admin_list", e, response) from e

    def close(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CloseResponse:
        """Close for customer_support.

        Closes selected customer support ticket (if not already closed). You...
        """
        path = "/api/web/namespaces/{namespace}/customer_support/{name}/close"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CloseResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "close", e, response) from e

    def comment(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CommentResponse:
        """Comment for customer_support.

        Adds additional comment to a specified customer support ticket. The...
        """
        path = "/api/web/namespaces/{namespace}/customer_support/{name}/comment"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CommentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "comment", e, response) from e

    def escalate(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> EscalationResponse:
        """Escalate for customer_support.

        Escalates a selected ticket. Only certain customers (depending on...
        """
        path = "/api/web/namespaces/{namespace}/customer_support/{name}/escalate"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EscalationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "escalate", e, response) from e

    def priority(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> PriorityResponse:
        """Priority for customer_support.

        Changes priority of a selected ticket. Not possible if ticket's...
        """
        path = "/api/web/namespaces/{namespace}/customer_support/{name}/priority"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PriorityResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "priority", e, response) from e

    def reopen(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> ReopenResponse:
        """Reopen for customer_support.

        Reopens a selected closed customer support ticket.
        """
        path = "/api/web/namespaces/{namespace}/customer_support/{name}/reopen"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReopenResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("customer_support", "reopen", e, response) from e

