"""InfraprotectAsnPrefix resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.infraprotect_asn_prefix.models import (
    InfraprotectAsnPrefixListItem,
    ObjectCreateMetaType,
    ObjectRefType,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    Empty,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    DeleteRequest,
    ObjectRefType,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    ProtobufAny,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ReplaceResponse,
    UpdateASNPrefixIRROverrideRequest,
    UpdateASNPrefixIRROverrideResponse,
    UpdateASNPrefixReviewStatusRequest,
    UpdateASNPrefixReviewStatusResponse,
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


class InfraprotectAsnPrefixResource:
    """API methods for infraprotect_asn_prefix.

    DDoS transit Prefix Information
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.infraprotect_asn_prefix.CreateSpecType(...)
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: ObjectCreateMetaType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new infraprotect_asn_prefix.

        Creates a DDoS transit Prefix

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
        path = "/api/infraprotect/namespaces/{metadata.namespace}/infraprotect_asn_prefixs"
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
            raise F5XCValidationError("infraprotect_asn_prefix", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: ObjectCreateMetaType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing infraprotect_asn_prefix.

        Amends a DDoS transit Prefix

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
        path = "/api/infraprotect/namespaces/{metadata.namespace}/infraprotect_asn_prefixs/{metadata.name}"
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
            raise F5XCValidationError("infraprotect_asn_prefix", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[InfraprotectAsnPrefixListItem]:
        """List infraprotect_asn_prefix resources in a namespace.

        List the set of infraprotect_asn_prefix in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect_asn_prefixs"
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
            return [InfraprotectAsnPrefixListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("infraprotect_asn_prefix", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a infraprotect_asn_prefix by name.

        Get DDoS transit Prefix

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
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect_asn_prefixs/{name}"
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
            raise F5XCValidationError("infraprotect_asn_prefix", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a infraprotect_asn_prefix.

        Delete the specified infraprotect_asn_prefix

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect_asn_prefixs/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def update_asn_prefix_irr_override(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateASNPrefixIRROverrideResponse:
        """Update Asn Prefix Irr Override for infraprotect_asn_prefix.

        Update Infraprotect ASN Prefix IRR Override
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect_asn_prefixes/update-asn-prefix-irr-override"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateASNPrefixIRROverrideResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect_asn_prefix", "update_asn_prefix_irr_override", e, response) from e

    def update_asn_prefix_review_status(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateASNPrefixReviewStatusResponse:
        """Update Asn Prefix Review Status for infraprotect_asn_prefix.

        Update Infraprotect ASN Prefix Review Status
        """
        path = "/api/infraprotect/namespaces/{namespace}/infraprotect_asn_prefixes/update-asn-prefix-review-status"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateASNPrefixReviewStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("infraprotect_asn_prefix", "update_asn_prefix_review_status", e, response) from e

