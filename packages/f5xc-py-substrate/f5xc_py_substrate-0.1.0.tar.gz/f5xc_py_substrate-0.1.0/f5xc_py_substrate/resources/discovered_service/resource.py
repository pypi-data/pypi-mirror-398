"""DiscoveredService resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.discovered_service.models import (
    DiscoveredServiceListItem,
    ObjectRefType,
    PodInfoType,
    PortInfoType,
    ConsulService,
    Empty,
    ObjectRefType,
    WhereSite,
    WhereVirtualSite,
    ProxyTypeHttp,
    ProxyTypeHttps,
    HTTPLBRequest,
    CreateHTTPLoadBalancerRequest,
    CreateHTTPLoadBalancerResponse,
    AdvertisePublic,
    WhereSite,
    WhereVirtualNetwork,
    WhereVirtualSite,
    WhereVirtualSiteSpecifiedVIP,
    WhereVK8SService,
    WhereType,
    AdvertiseCustom,
    TCPLBRequest,
    CreateTCPLoadBalancerRequest,
    CreateTCPLoadBalancerResponse,
    DisableVisibilityRequest,
    DisableVisibilityResponse,
    TrendValue,
    MetricValue,
    VirtualServerPoolHealthStatusListResponseItem,
    VirtualServerPoolMemberHealth,
    HealthStatusResponse,
    EnableVisibilityRequest,
    EnableVisibilityResponse,
    ObjectGetMetaType,
    K8sService,
    NginxOneDiscoveredServer,
    ThirdPartyApplicationDiscovery,
    VirtualServer,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    GetResponse,
    ProtobufAny,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ConditionType,
    StatusMetaType,
    StatusObject,
    ListServicesResponseItem,
    ListServicesResponse,
    SuggestValuesReq,
    SuggestedItem,
    SuggestValuesResp,
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


class DiscoveredServiceResource:
    """API methods for discovered_service.

    Discovered Services represents the services (virtual-servers, k8s...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.discovered_service.CreateSpecType(...)
    GetSpecType = GetSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[DiscoveredServiceListItem]:
        """List discovered_service resources in a namespace.

        List the set of discovered_service in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/discovery/namespaces/{namespace}/discovered_services"
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
            return [DiscoveredServiceListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a discovered_service by name.

        Get Discovered Service Object.

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
        path = "/api/discovery/namespaces/{namespace}/discovered_services/{name}"
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
            raise F5XCValidationError("discovered_service", "get", e, response) from e

    def discovered_service_health_status(
        self,
        namespace: str,
        name: str,
    ) -> HealthStatusResponse:
        """Discovered Service Health Status for discovered_service.

        Get Discovered Service Health status
        """
        path = "/api/data/namespaces/{namespace}/discovered_services/{name}/health_status"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HealthStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "discovered_service_health_status", e, response) from e

    def list_discovered_services(
        self,
        namespace: str,
        service_type: str | None = None,
        discovery_name: str | None = None,
    ) -> ListServicesResponse:
        """List Discovered Services for discovered_service.

        List the discovered services of specific type like virtual-servers,...
        """
        path = "/api/discovery/custom/namespaces/{namespace}/discovered_services"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if service_type is not None:
            params["service_type"] = service_type
        if discovery_name is not None:
            params["discovery_name"] = discovery_name

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListServicesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "list_discovered_services", e, response) from e

    def create_http_load_balancer(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CreateHTTPLoadBalancerResponse:
        """Create Http Load Balancer for discovered_service.

        Create HTTP/HTTPS load balancer using the discovered virtual server...
        """
        path = "/api/discovery/namespaces/{namespace}/discovered_services/{name}/create_http_load_balancer"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateHTTPLoadBalancerResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "create_http_load_balancer", e, response) from e

    def create_tcp_load_balancer(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CreateTCPLoadBalancerResponse:
        """Create Tcp Load Balancer for discovered_service.

        Create TCP load balancer using the discovered virtual server as an...
        """
        path = "/api/discovery/namespaces/{namespace}/discovered_services/{name}/create_tcp_load_balancer"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateTCPLoadBalancerResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "create_tcp_load_balancer", e, response) from e

    def disable_visibility(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> DisableVisibilityResponse:
        """Disable Visibility for discovered_service.

        Disable Visibility of the service in all workspaces. This will...
        """
        path = "/api/discovery/namespaces/{namespace}/discovered_services/{name}/disable_visibility"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DisableVisibilityResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "disable_visibility", e, response) from e

    def enable_visibility(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> EnableVisibilityResponse:
        """Enable Visibility for discovered_service.

        Enable Visibility of the service in all workspaces. This action will...
        """
        path = "/api/discovery/namespaces/{namespace}/discovered_services/{name}/enable_visibility"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EnableVisibilityResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "enable_visibility", e, response) from e

    def suggest_values(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Suggest Values for discovered_service.

        SuggestValues returns suggested values for the specified field in...
        """
        path = "/api/discovery/namespaces/{namespace}/suggest-values"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("discovered_service", "suggest_values", e, response) from e

