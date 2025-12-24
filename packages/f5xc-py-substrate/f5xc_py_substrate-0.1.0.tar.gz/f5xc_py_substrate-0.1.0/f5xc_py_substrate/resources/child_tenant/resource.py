"""ChildTenant resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.child_tenant.models import (
    ChildTenantListItem,
    CustomerInfo,
    DeleteRequest,
    ObjectRefType,
    GroupAssignmentType,
    LinkRefType,
    AllTenantsTicketSummary,
    CTTicketSummary,
    SupportTicketInfo,
    AccessInfo,
    ListChildTenantsResp,
    CTListToCTM,
    MigrateChildTenantsReq,
    ProtobufAny,
    ErrorType,
    MigrateChildTenantsResp,
    ObjectReplaceMetaType,
    GlobalSpecType,
    ReplaceSpecType,
    ReplaceRequest,
    ReplaceResponse,
    AttachmentType,
    CloseResponse,
    CommentResponse,
    CommentType,
    EscalationResponse,
    PriorityResponse,
    ReopenResponse,
    ObjectRefType,
    CRMInfo,
    ConditionType,
    InitializerType,
    StatusType,
    InitializersType,
    ObjectCreateMetaType,
    ObjectGetMetaType,
    StatusMetaType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateSpecType,
    CreateRequest,
    GetSpecType,
    CreateResponse,
    StatusObject,
    ListResponseItem,
    CommentRequest,
    PriorityRequest,
    GetByTpIdResponse,
    ListSupportTicketResponse,
    CreateSpecType,
    CreateRequest,
    GetSpecType,
    CreateResponse,
    StatusObject,
    GetResponse,
    ListResponseItem,
    ListResponse,
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


class ChildTenantResource:
    """API methods for child_tenant.

    
Child Tenant
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.child_tenant.CreateSpecType(...)
    ReplaceSpecType = ReplaceSpecType
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: CustomerInfo | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new child_tenant.

        Creates a child_tenant config instance. Name of the object is the...

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
        path = "/api/web/namespaces/{metadata.namespace}/child_tenants"
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
            raise F5XCValidationError("child_tenant", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: CustomerInfo | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing child_tenant.

        Replaces attributes of a child_tenant configuration

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to replace.
            spec: The new resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to disable the resource.
        """
        path = "/api/web/namespaces/{metadata.namespace}/child_tenants/{metadata.name}"
        path = path.replace("{metadata.namespace}", namespace)
        path = path.replace("{metadata.name}", name)

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
            response = self._http.put(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReplaceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[ChildTenantListItem]:
        """List child_tenant resources in a namespace.

        List the set of child_tenant in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/namespaces/{namespace}/child_tenants"
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
            return [ChildTenantListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a child_tenant by name.

        Get child_tenant reads a given object from storage backend for...

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
        path = "/api/web/namespaces/{namespace}/child_tenants/{name}"
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
            raise F5XCValidationError("child_tenant", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a child_tenant.

        Delete the specified child_tenant

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/web/namespaces/{namespace}/child_tenants/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def list_child_tenants(
        self,
        name: str | None = None,
        ctm: str | None = None,
        page_start: str | None = None,
        page_limit: int | None = None,
    ) -> ListChildTenantsResp:
        """List Child Tenants for child_tenant.

        Get list of child tenants user has access to based on assigned...
        """
        path = "/api/web/namespaces/system/partner-management/child_tenants"

        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if ctm is not None:
            params["ctm"] = ctm
        if page_start is not None:
            params["page_start"] = page_start
        if page_limit is not None:
            params["page_limit"] = page_limit

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListChildTenantsResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "list_child_tenants", e, response) from e

    def migrate_child_tenants(
        self,
        body: dict[str, Any] | None = None,
    ) -> MigrateChildTenantsResp:
        """Migrate Child Tenants for child_tenant.

        Migrate ACTIVE child tenants from existing CTM(s) to a specified new CTM
        """
        path = "/api/web/namespaces/system/partner-management/child_tenants/migrate"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MigrateChildTenantsResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "migrate_child_tenants", e, response) from e

    def list_child_tenant_support_tickets(
        self,
    ) -> ListSupportTicketResponse:
        """List Child Tenant Support Tickets for child_tenant.

        Return list of all support tickets for a child tenant
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListSupportTicketResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "list_child_tenant_support_tickets", e, response) from e

    def custom_create(
        self,
        body: dict[str, Any] | None = None,
    ) -> CreateResponse:
        """Custom Create for child_tenant.

        Creates a new customer support ticket in our customer support...
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "custom_create", e, response) from e

    def custom_get(
        self,
        tp_id: str,
    ) -> GetByTpIdResponse:
        """Custom Get for child_tenant.

        Support ticket representation we display to customers. There's much...
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports/{tp_id}"
        path = path.replace("{tp_id}", tp_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetByTpIdResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "custom_get", e, response) from e

    def close(
        self,
        tp_id: str,
        body: dict[str, Any] | None = None,
    ) -> CloseResponse:
        """Close for child_tenant.

        Closes selected customer support ticket (if not already closed). You...
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports/{tp_id}/close"
        path = path.replace("{tp_id}", tp_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CloseResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "close", e, response) from e

    def comment(
        self,
        tp_id: str,
        body: dict[str, Any] | None = None,
    ) -> CommentResponse:
        """Comment for child_tenant.

        Adds additional comment to a specified customer support ticket. The...
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports/{tp_id}/comment"
        path = path.replace("{tp_id}", tp_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CommentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "comment", e, response) from e

    def escalate(
        self,
        tp_id: str,
        body: dict[str, Any] | None = None,
    ) -> EscalationResponse:
        """Escalate for child_tenant.

        Escalates a selected ticket. Only certain customers (depending on...
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports/{tp_id}/escalate"
        path = path.replace("{tp_id}", tp_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EscalationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "escalate", e, response) from e

    def priority(
        self,
        tp_id: str,
        body: dict[str, Any] | None = None,
    ) -> PriorityResponse:
        """Priority for child_tenant.

        Changes priority of a selected ticket. Not possible if ticket's...
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports/{tp_id}/priority"
        path = path.replace("{tp_id}", tp_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PriorityResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "priority", e, response) from e

    def reopen(
        self,
        tp_id: str,
        body: dict[str, Any] | None = None,
    ) -> ReopenResponse:
        """Reopen for child_tenant.

        Reopens a selected closed customer support ticket.
        """
        path = "/api/web/namespaces/system/partner-management/customer_supports/{tp_id}/reopen"
        path = path.replace("{tp_id}", tp_id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReopenResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("child_tenant", "reopen", e, response) from e

