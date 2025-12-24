"""V1DnsMonitor resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.v1_dns_monitor.models import (
    V1DnsMonitorListItem,
    Empty,
    ProtobufAny,
    ConditionType,
    ErrorType,
    InitializerType,
    StatusType,
    InitializersType,
    ObjectCreateMetaType,
    ObjectGetMetaType,
    ObjectMetaType,
    ObjectRefType,
    ObjectReplaceMetaType,
    StatusMetaType,
    ViewRefType,
    SystemObjectGetMetaType,
    SystemObjectMetaType,
    AWSRegions,
    AWSRegionsExternal,
    DynamicThreshold,
    StaticMaxThreshold,
    StaticMinThreshold,
    HealthPolicy,
    RegionalEdgeExternal,
    RegionalEdgeRegions,
    Source,
    SourceExternal,
    V1DnsMonitornameserver,
    V1DnsMonitorcreatespectype,
    V1DnsMonitorcreaterequest,
    V1DnsMonitorgetspectype,
    V1DnsMonitorcreateresponse,
    V1DnsMonitordeleterequest,
    V1DnsMonitorglobalspectype,
    V1DnsMonitorspectype,
    V1DnsMonitorobject,
    V1DnsMonitorgetfiltereddnsmonitorlistresponse,
    V1DnsMonitorreplacespectype,
    V1DnsMonitorreplacerequest,
    V1DnsMonitorstatusobject,
    V1DnsMonitorgetresponse,
    V1DnsMonitorlistresponseitem,
    V1DnsMonitorlistresponse,
    V1DnsMonitorreplaceresponse,
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


class V1DnsMonitorResource:
    """API methods for v1_dns_monitor.

    
DNS Monitor defines a DNS synthetic monitor.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.v1_dns_monitor.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: Empty | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> V1DnsMonitorcreateresponse:
        """Create a new v1_dns_monitor.

        Create a new DNS Monitor

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
        path = "/api/observability/synthetic_monitor/namespaces/{metadata.namespace}/v1_dns_monitors"
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
            return V1DnsMonitorcreateresponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("v1_dns_monitor", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: Empty | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> V1DnsMonitorreplaceresponse:
        """Replace an existing v1_dns_monitor.

        Replace the contents of a DNS Monitor

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
        path = "/api/observability/synthetic_monitor/namespaces/{metadata.namespace}/v1_dns_monitors/{metadata.name}"
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
            return V1DnsMonitorreplaceresponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("v1_dns_monitor", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[V1DnsMonitorListItem]:
        """List v1_dns_monitor resources in a namespace.

        List the set of v1_dns_monitor in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/v1_dns_monitors"
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
            return [V1DnsMonitorListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("v1_dns_monitor", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> V1DnsMonitorgetresponse:
        """Get a v1_dns_monitor by name.

        Get a DNS Monitor

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
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/v1_dns_monitors/{name}"
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
            return V1DnsMonitorgetresponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("v1_dns_monitor", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a v1_dns_monitor.

        Delete the specified v1_dns_monitor

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/v1_dns_monitors/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def get_filtered_dns_monitor_list(
        self,
        namespace: str,
        filter: str | None = None,
        page: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
    ) -> V1DnsMonitorgetfiltereddnsmonitorlistresponse:
        """Get Filtered Dns Monitor List for v1_dns_monitor.

        List v1_dns_monitor in a namespace based on filter
        """
        path = "/api/observability/synthetic_monitor/namespaces/{namespace}/filtered-dns-monitor-list"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if filter is not None:
            params["filter"] = filter
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if sort is not None:
            params["sort"] = sort

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return V1DnsMonitorgetfiltereddnsmonitorlistresponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("v1_dns_monitor", "get_filtered_dns_monitor_list", e, response) from e

