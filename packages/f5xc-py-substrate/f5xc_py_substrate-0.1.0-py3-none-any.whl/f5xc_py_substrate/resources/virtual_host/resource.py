"""VirtualHost resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.virtual_host.models import (
    VirtualHostListItem,
    ProtobufAny,
    HttpBody,
    APIEPDynExample,
    AuthenticationTypeLocPair,
    PDFSpec,
    PDFStat,
    APIEPPDFInfo,
    RiskScore,
    APIEPInfo,
    Authentication,
    SchemaStruct,
    RequestSchema,
    DiscoveredSchema,
    SensitiveData,
    BlindfoldSecretInfoType,
    ClearSecretInfoType,
    SecretType,
    HMACKeyPair,
    KMSKeyRefType,
    CookieParams,
    Empty,
    HashAlgorithms,
    TlsCertificateType,
    ObjectRefType,
    TrustedCAList,
    TlsValidationParamsType,
    TlsParamsType,
    DownstreamTlsParamsType,
    AppFirewallRefType,
    BufferConfigType,
    CertificateParamsType,
    ConditionType,
    CookieValueOption,
    CorsPolicy,
    DomainNameList,
    CsrfPolicy,
    ErrorType,
    HeaderManipulationOptionType,
    HeaderTransformationType,
    InitializerType,
    StatusType,
    InitializersType,
    ObjectCreateMetaType,
    ObjectGetMetaType,
    ObjectReplaceMetaType,
    RetryBackOff,
    RetryPolicyType,
    SetCookieValueOption,
    StatusMetaType,
    ViewRefType,
    SystemObjectGetMetaType,
    TLSCoalescingOptions,
    WafType,
    ObjectRefType,
    APIEndpoint,
    AuthenticationDetails,
    CaptchaChallengeType,
    CompressionType,
    DynamicReverseProxyType,
    Http1ProtocolOptions,
    HttpProtocolOptions,
    JavascriptChallengeType,
    SlowDDoSMitigation,
    CreateSpecType,
    DNSRecord,
    AutoCertInfoType,
    CdnServiceType,
    DnsInfo,
    GetSpecType,
    ReplaceSpecType,
    GlobalSpecType,
    JiraIssueType,
    JiraProject,
    JiraIssueStatusCategory,
    JiraIssueStatus,
    JiraIssueFields,
    JiraIssue,
    ApiOperation,
    ApiEndpointWithSchema,
    APIEPActivityMetrics,
    APIEPSourceOpenApiSchemaRsp,
    APIEPSummaryFilter,
    APIEndpointLearntSchemaRsp,
    APIEndpointPDFRsp,
    APIEndpointReq,
    APIEndpointRsp,
    APIEndpointsRsp,
    ApiEndpointsStatsRsp,
    AssignAPIDefinitionReq,
    AssignAPIDefinitionResp,
    CreateJiraIssueRequest,
    CreateRequest,
    CreateResponse,
    CreateTicketRequest,
    CreateTicketResponse,
    DeleteRequest,
    GetAPICallSummaryReq,
    RequestCountPerResponseClass,
    GetAPICallSummaryRsp,
    GetAPIEndpointsSchemaUpdatesReq,
    GetAPIEndpointsSchemaUpdatesResp,
    GetDnsInfoResponse,
    ReplaceRequest,
    VerStatusType,
    StatusObject,
    GetResponse,
    GetTopAPIEndpointsReq,
    GetTopAPIEndpointsRsp,
    GetTopSensitiveDataReq,
    SensitiveDataCount,
    GetTopSensitiveDataRsp,
    GetVulnerabilitiesReq,
    VulnEvidenceSample,
    VulnEvidence,
    VulnRisk,
    TicketDetails,
    Vulnerability,
    GetVulnerabilitiesRsp,
    ListResponseItem,
    ListResponse,
    ReplaceResponse,
    UnlinkTicketsRequest,
    UnlinkTicketsResponse,
    UnmergeAPIEPSourceOpenApiSchemaReq,
    UpdateAPIEndpointsSchemasReq,
    UpdateAPIEndpointsSchemasResp,
    UpdateVulnerabilitiesStateReq,
    UpdateVulnerabilitiesStateRsp,
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


class VirtualHostResource:
    """API methods for virtual_host.

    Virtual host is main anchor configuration for a proxy. Primary...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.virtual_host.CreateSpecType(...)
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
        spec: ProtobufAny | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new virtual_host.

        Creates virtual host in a given namespace.

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
        path = "/api/config/namespaces/{metadata.namespace}/virtual_hosts"
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
            raise F5XCValidationError("virtual_host", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: ProtobufAny | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing virtual_host.

        Replace a given virtual host in a given namespace.

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
        path = "/api/config/namespaces/{metadata.namespace}/virtual_hosts/{metadata.name}"
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
            raise F5XCValidationError("virtual_host", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[VirtualHostListItem]:
        """List virtual_host resources in a namespace.

        List the set of virtual_host in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/virtual_hosts"
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
            return [VirtualHostListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a virtual_host by name.

        Get virtual host from a given namespace.

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
        path = "/api/config/namespaces/{namespace}/virtual_hosts/{name}"
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
            raise F5XCValidationError("virtual_host", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a virtual_host.

        Delete the specified virtual_host

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/virtual_hosts/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def assign_api_definition(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> AssignAPIDefinitionResp:
        """Assign Api Definition for virtual_host.

        Set a reference to the API Definition, with an option to create an...
        """
        path = "/api/config/namespaces/{namespace}/virtual_hosts/{name}/api_definitions/assign"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AssignAPIDefinitionResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "assign_api_definition", e, response) from e

    def get_api_endpoint(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> APIEndpointRsp:
        """Get Api Endpoint for virtual_host.

        Get API endpoint for Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoint"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_endpoint", e, response) from e

    def get_api_endpoint_learnt_schema(
        self,
        namespace: str,
        name: str,
        collapsed_url: str | None = None,
        method: str | None = None,
        domains: list | None = None,
        api_endpoint_info_request: list | None = None,
    ) -> APIEndpointLearntSchemaRsp:
        """Get Api Endpoint Learnt Schema for virtual_host.

        Get Learnt Schema per API endpoint for a given auto discovered API...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoint/learnt_schema"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if collapsed_url is not None:
            params["collapsed_url"] = collapsed_url
        if method is not None:
            params["method"] = method
        if domains is not None:
            params["domains"] = domains
        if api_endpoint_info_request is not None:
            params["api_endpoint_info_request"] = api_endpoint_info_request

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointLearntSchemaRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_endpoint_learnt_schema", e, response) from e

    def get_api_endpoint_pdf(
        self,
        namespace: str,
        name: str,
        collapsed_url: str | None = None,
        method: str | None = None,
    ) -> APIEndpointPDFRsp:
        """Get Api Endpoint Pdf for virtual_host.

        Get PDF of all metrics for a given auto discovered API endpoint for...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoint/pdf"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if collapsed_url is not None:
            params["collapsed_url"] = collapsed_url
        if method is not None:
            params["method"] = method

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointPDFRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_endpoint_pdf", e, response) from e

    def get_apiep_source_open_api_schema(
        self,
        namespace: str,
        name: str,
        id_: str | None = None,
        discovery_source_types: list | None = None,
    ) -> APIEPSourceOpenApiSchemaRsp:
        """Get Apiep Source Open Api Schema for virtual_host.

        Get openapi schema per API endpoint for a given source types and Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoint/sources_openapi_schema"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if id_ is not None:
            params["id"] = id_
        if discovery_source_types is not None:
            params["discovery_source_types"] = discovery_source_types

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEPSourceOpenApiSchemaRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_apiep_source_open_api_schema", e, response) from e

    def unmerge_apiep_source_open_api_schema(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Unmerge Apiep Source Open Api Schema for virtual_host.

        Unmerge Source Discovered schema from Api Endpoint merged schema
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoint/unmerge_sources_openapi_schema"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def get_api_endpoints(
        self,
        namespace: str,
        name: str,
        api_endpoint_info_request: list | None = None,
        domains: list | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        apiep_category: list | None = None,
    ) -> APIEndpointsRsp:
        """Get Api Endpoints for virtual_host.

        Get all autodiscovered API endpoints for Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoints"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if api_endpoint_info_request is not None:
            params["api_endpoint_info_request"] = api_endpoint_info_request
        if domains is not None:
            params["domains"] = domains
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        if apiep_category is not None:
            params["apiep_category"] = apiep_category

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return APIEndpointsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_endpoints", e, response) from e

    def get_api_endpoints_stats(
        self,
        namespace: str,
        name: str,
    ) -> ApiEndpointsStatsRsp:
        """Get Api Endpoints Stats for virtual_host.

        Get api endpoints stats for the given Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoints/stats"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ApiEndpointsStatsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_endpoints_stats", e, response) from e

    def get_api_call_summary(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetAPICallSummaryRsp:
        """Get Api Call Summary for virtual_host.

        Get total api calls for the given Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoints/summary/calls_by_response_code"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetAPICallSummaryRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_call_summary", e, response) from e

    def get_top_api_endpoints(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetTopAPIEndpointsRsp:
        """Get Top Api Endpoints for virtual_host.

        Top APIs by requested activity metric. For example most-active APIs...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoints/summary/top_active"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTopAPIEndpointsRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_top_api_endpoints", e, response) from e

    def get_top_sensitive_data(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetTopSensitiveDataRsp:
        """Get Top Sensitive Data for virtual_host.

        Get sensitive data summary for the given Virtual Host. For each...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoints/summary/top_sensitive_data"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTopSensitiveDataRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_top_sensitive_data", e, response) from e

    def get_swagger_spec(
        self,
        namespace: str,
        name: str,
        domains: list | None = None,
    ) -> HttpBody:
        """Get Swagger Spec for virtual_host.

        Get the corresponding Swagger spec for the given app type
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_endpoints/swagger_spec"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if domains is not None:
            params["domains"] = domains

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_swagger_spec", e, response) from e

    def get_api_endpoints_schema_updates(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetAPIEndpointsSchemaUpdatesResp:
        """Get Api Endpoints Schema Updates for virtual_host.

        Get list of schema paiComparablers, current and updated, for each...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_inventory/api_endpoints/get_schema_updates"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetAPIEndpointsSchemaUpdatesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_api_endpoints_schema_updates", e, response) from e

    def update_api_endpoints_schemas(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateAPIEndpointsSchemasResp:
        """Update Api Endpoints Schemas for virtual_host.

        Update the payload schema for the specified endpoints or all pending...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/api_inventory/api_endpoints/update_schemas"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateAPIEndpointsSchemasResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "update_api_endpoints_schemas", e, response) from e

    def create_ticket(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CreateTicketResponse:
        """Create Ticket for virtual_host.

        Create a ticket for the given vulnerability
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/create_ticket"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateTicketResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "create_ticket", e, response) from e

    def get_dns_info(
        self,
        namespace: str,
        name: str,
    ) -> GetDnsInfoResponse:
        """Get Dns Info for virtual_host.

        GetDnsInfo is an API to get DNS information for a given virtual host
        """
        path = "/api/config/namespaces/{namespace}/virtual_hosts/{name}/get-dns-info"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDnsInfoResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_dns_info", e, response) from e

    def unlink_tickets(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> UnlinkTicketsResponse:
        """Unlink Tickets for virtual_host.

        Remove the Ticket from vulnerability in XC platform External ticket...
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/unlink_tickets"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnlinkTicketsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "unlink_tickets", e, response) from e

    def get_vulnerabilities(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetVulnerabilitiesRsp:
        """Get Vulnerabilities for virtual_host.

        Get vulnerabilities for the given Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/vulnerabilities"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetVulnerabilitiesRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "get_vulnerabilities", e, response) from e

    def update_vulnerabilities_state(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateVulnerabilitiesStateRsp:
        """Update Vulnerabilities State for virtual_host.

        Update vulnerabilities for the given Virtual Host
        """
        path = "/api/ml/data/namespaces/{namespace}/virtual_hosts/{name}/vulnerability/update_state"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateVulnerabilitiesStateRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("virtual_host", "update_vulnerabilities_state", e, response) from e

