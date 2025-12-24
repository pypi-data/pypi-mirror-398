"""Pydantic models for namespace."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class NamespaceListItem(F5XCBaseModel):
    """List item for namespace resources."""


class ObjectRefType(F5XCBaseModel):
    """This type establishes a direct reference from one object(the referrer)..."""

    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None


class AlertPolicyStatus(F5XCBaseModel):
    policy: Optional[ObjectRefType] = None
    reason: Optional[list[str]] = None
    status: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class APIItemReq(F5XCBaseModel):
    """A request API item."""

    method: Optional[str] = None
    path: Optional[str] = None


class APIItemListReq(F5XCBaseModel):
    """A request API item list."""

    items: Optional[list[APIItemReq]] = None
    list_id: Optional[str] = None


class AccessEnablerAddonService(F5XCBaseModel):
    """An addon service details schema"""

    addon_service_names: Optional[list[str]] = None


class APIItemResp(F5XCBaseModel):
    """A response API item."""

    addon_services: Optional[AccessEnablerAddonService] = None
    method: Optional[str] = None
    none: Optional[Any] = None
    path: Optional[str] = None
    result: Optional[bool] = None


class APIItemListResp(F5XCBaseModel):
    """A response API item list. result will show combined AND output from the..."""

    items: Optional[list[APIItemResp]] = None
    list_id: Optional[str] = None
    result: Optional[bool] = None


class BIGIPVirtualServerInventoryFilterType(F5XCBaseModel):
    """BIGIP Virtual Server Inventory Filter"""

    api_discovery: Optional[bool] = None
    waf_configured: Optional[bool] = None


class HTTPLoadbalancerInventoryFilterType(F5XCBaseModel):
    """HTTP Loadbalancer Inventory Filter"""

    api_definition: Optional[bool] = None
    api_discovery: Optional[bool] = None
    api_protection: Optional[bool] = None
    api_schema_validation: Optional[bool] = None
    bot_protection: Optional[bool] = None
    client_blocking: Optional[bool] = None
    client_side_defense: Optional[bool] = None
    cookie_protection: Optional[bool] = None
    cors_policy: Optional[bool] = None
    csrf_protection: Optional[bool] = None
    data_guard: Optional[bool] = None
    ddos_auto_mitigation: Optional[bool] = None
    ddos_mitigation: Optional[bool] = None
    ddos_protection: Optional[bool] = None
    default_loadbalancer: Optional[bool] = None
    graph_ql_inspection: Optional[bool] = None
    http_only: Optional[bool] = None
    ip_reputation: Optional[bool] = None
    malicious_user_detection: Optional[bool] = None
    malicious_user_mitigation: Optional[bool] = None
    malware_protection: Optional[bool] = None
    mutual_tls: Optional[bool] = None
    namespace_service_policy: Optional[bool] = None
    origin_server_subset: Optional[bool] = None
    private_advertisement: Optional[bool] = None
    public_advertisment: Optional[bool] = None
    routes: Optional[bool] = None
    service_policy: Optional[bool] = None
    slow_ddos_mitigation: Optional[bool] = None
    trusted_client: Optional[bool] = None
    trusted_client_ip_headers: Optional[bool] = None
    waf: Optional[bool] = None
    waf_exclusion: Optional[bool] = None


class NGINXOneServerInventoryFilterType(F5XCBaseModel):
    """NGINX One Server Inventory Filter"""

    api_discovery: Optional[bool] = None
    waf_configured: Optional[bool] = None


class TCPLoadbalancerInventoryFilterType(F5XCBaseModel):
    """TCP Loadbalancer inventory Filter"""

    namespace_service_policy: Optional[bool] = None
    private_advertisement: Optional[bool] = None
    public_advertisment: Optional[bool] = None
    service_policy: Optional[bool] = None
    tls_encryption: Optional[bool] = None


class ThirdPartyApplicationFilterType(F5XCBaseModel):
    """Third Party Application Inventory Filter"""

    api_discovery: Optional[bool] = None


class UDPLoadbalancerInventoryFilterType(F5XCBaseModel):
    """UDP Loadbalancer inventory Filter"""

    private_advertisement: Optional[bool] = None
    public_advertisment: Optional[bool] = None


class AllApplicationInventoryRequest(F5XCBaseModel):
    """Request for inventory of application related objects"""

    bigip_virtual_server_filter: Optional[BIGIPVirtualServerInventoryFilterType] = None
    cdn_load_balancer_filter: Optional[HTTPLoadbalancerInventoryFilterType] = None
    http_load_balancer_filter: Optional[HTTPLoadbalancerInventoryFilterType] = None
    nginx_one_server_filter: Optional[NGINXOneServerInventoryFilterType] = None
    tcp_load_balancer_filter: Optional[TCPLoadbalancerInventoryFilterType] = None
    third_party_application_filter: Optional[ThirdPartyApplicationFilterType] = None
    udp_load_balancer_filter: Optional[UDPLoadbalancerInventoryFilterType] = None


class AllApplicationInventoryWafFilterRequest(F5XCBaseModel):
    """Request for inventory of application related objects with WAF Filter"""

    exclusion_signature_id: Optional[int] = None
    exclusion_violation_type: Optional[Literal['VIOL_NONE', 'VIOL_FILETYPE', 'VIOL_METHOD', 'VIOL_MANDATORY_HEADER', 'VIOL_HTTP_RESPONSE_STATUS', 'VIOL_REQUEST_MAX_LENGTH', 'VIOL_FILE_UPLOAD', 'VIOL_FILE_UPLOAD_IN_BODY', 'VIOL_XML_MALFORMED', 'VIOL_JSON_MALFORMED', 'VIOL_ASM_COOKIE_MODIFIED', 'VIOL_HTTP_PROTOCOL_MULTIPLE_HOST_HEADERS', 'VIOL_HTTP_PROTOCOL_BAD_HOST_HEADER_VALUE', 'VIOL_HTTP_PROTOCOL_UNPARSABLE_REQUEST_CONTENT', 'VIOL_HTTP_PROTOCOL_NULL_IN_REQUEST', 'VIOL_HTTP_PROTOCOL_BAD_HTTP_VERSION', 'VIOL_HTTP_PROTOCOL_CRLF_CHARACTERS_BEFORE_REQUEST_START', 'VIOL_HTTP_PROTOCOL_NO_HOST_HEADER_IN_HTTP_1_1_REQUEST', 'VIOL_HTTP_PROTOCOL_BAD_MULTIPART_PARAMETERS_PARSING', 'VIOL_HTTP_PROTOCOL_SEVERAL_CONTENT_LENGTH_HEADERS', 'VIOL_HTTP_PROTOCOL_CONTENT_LENGTH_SHOULD_BE_A_POSITIVE_NUMBER', 'VIOL_EVASION_DIRECTORY_TRAVERSALS', 'VIOL_MALFORMED_REQUEST', 'VIOL_EVASION_MULTIPLE_DECODING', 'VIOL_DATA_GUARD', 'VIOL_EVASION_APACHE_WHITESPACE', 'VIOL_COOKIE_MODIFIED', 'VIOL_EVASION_IIS_UNICODE_CODEPOINTS', 'VIOL_EVASION_IIS_BACKSLASHES', 'VIOL_EVASION_PERCENT_U_DECODING', 'VIOL_EVASION_BARE_BYTE_DECODING', 'VIOL_EVASION_BAD_UNESCAPE', 'VIOL_HTTP_PROTOCOL_BAD_MULTIPART_FORMDATA_REQUEST_PARSING', 'VIOL_HTTP_PROTOCOL_BODY_IN_GET_OR_HEAD_REQUEST', 'VIOL_HTTP_PROTOCOL_HIGH_ASCII_CHARACTERS_IN_HEADERS', 'VIOL_ENCODING', 'VIOL_COOKIE_MALFORMED', 'VIOL_GRAPHQL_FORMAT', 'VIOL_GRAPHQL_MALFORMED', 'VIOL_GRAPHQL_INTROSPECTION_QUERY']] = None


class HTTPLoadbalancerWafFilterResultType(F5XCBaseModel):
    """HTTP Loadbalancer Waf Filter Inventory Results"""

    name: Optional[str] = None
    namespace: Optional[str] = None


class AllApplicationInventoryWafFilterResponse(F5XCBaseModel):
    """Response for inventory of application related objects"""

    cdn_loadbalancers: Optional[list[HTTPLoadbalancerWafFilterResultType]] = None
    http_loadbalancers: Optional[list[HTTPLoadbalancerWafFilterResultType]] = None


class ApiEndpointsStatsAllNSReq(F5XCBaseModel):
    """Request shape for GET Api Endpoints Stats All Namespaces"""

    namespace: Optional[str] = None


class ApiEndpointsStatsNSReq(F5XCBaseModel):
    """Request shape for GET Api Endpoints Stats"""

    namespace: Optional[str] = None
    vhosts_filter: Optional[list[str]] = None
    vhosts_types_filter: Optional[list[Literal['VIRTUAL_SERVICE', 'HTTP_LOAD_BALANCER', 'API_GATEWAY', 'TCP_LOAD_BALANCER', 'PROXY', 'CDN_LOAD_BALANCER', 'NGINX_SERVER', 'UDP_LOAD_BALANCER']]] = None


class ApiEndpointsStatsNSRsp(F5XCBaseModel):
    """Response shape for GET API endpoints Stats."""

    discovered: Optional[int] = None
    inventory: Optional[int] = None
    pii_detected: Optional[int] = None
    shadow: Optional[int] = None
    total_endpoints: Optional[int] = None


class ApplicationInventoryRequest(F5XCBaseModel):
    """Request for inventory of application related objects from all namespaces"""

    bigip_virtual_server_filter: Optional[BIGIPVirtualServerInventoryFilterType] = None
    cdn_load_balancer_filter: Optional[HTTPLoadbalancerInventoryFilterType] = None
    http_load_balancer_filter: Optional[HTTPLoadbalancerInventoryFilterType] = None
    namespace: Optional[str] = None
    nginx_one_server_filter: Optional[NGINXOneServerInventoryFilterType] = None
    tcp_load_balancer_filter: Optional[TCPLoadbalancerInventoryFilterType] = None
    third_party_application_filter: Optional[ThirdPartyApplicationFilterType] = None
    udp_load_balancer_filter: Optional[UDPLoadbalancerInventoryFilterType] = None


class BIGIPVirtualServerResultType(F5XCBaseModel):
    """BIGIP Virtual Server Inventory Results"""

    api_discovery_enabled: Optional[Any] = None
    description: Optional[str] = None
    host_name: Optional[str] = None
    name: Optional[str] = None
    server_name: Optional[str] = None
    version: Optional[str] = None
    waf_enforcement_mode: Optional[str] = None
    waf_policy_name: Optional[str] = None


class BIGIPVirtualServerInventoryType(F5XCBaseModel):
    """BIGIP Virtual Server inventory"""

    api_discovery: Optional[int] = None
    bigiplb_results: Optional[list[BIGIPVirtualServerResultType]] = None
    waf_configured: Optional[int] = None


class HTTPLoadbalancerResultType(F5XCBaseModel):
    """HTTP Loadbalancer Inventory Results"""

    api_definition_enabled: Optional[Any] = None
    api_discovery_enabled: Optional[Any] = None
    api_protection_enabled: Optional[Any] = None
    api_schema_validation_enabled: Optional[Any] = None
    bot_protection_enabled: Optional[Any] = None
    certification_expiration_date: Optional[str] = None
    certification_status: Optional[str] = None
    client_blocking_enabled: Optional[Any] = None
    client_side_defense_enabled: Optional[Any] = None
    connection_idle_timeout: Optional[int] = None
    cookie_protection_enabled: Optional[Any] = None
    cors_policy_enabled: Optional[Any] = None
    csrf_protection_enabled: Optional[Any] = None
    data_guard_enabled: Optional[Any] = None
    ddos_auto_mitigation_enabled: Optional[Any] = None
    ddos_mitigation_enabled: Optional[Any] = None
    ddos_protection_enabled: Optional[Any] = None
    default_loadbalancer_enabled: Optional[Any] = None
    dns_info: Optional[str] = None
    domains: Optional[list[str]] = None
    graph_ql_inspection_enabled: Optional[Any] = None
    http_enabled: Optional[Any] = None
    http_listen_port_choice: Optional[str] = None
    idle_timeout: Optional[int] = None
    ip_reputation_enabled: Optional[Any] = None
    loadbalancer_algorithm: Optional[str] = None
    malicious_user_detection_enabled: Optional[Any] = None
    malicious_user_mitigation_enabled: Optional[Any] = None
    malware_protection_enabled: Optional[Any] = None
    mutual_tls_enabled: Optional[Any] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_service_policy_enabled: Optional[Any] = None
    origin_server_subset_enabled: Optional[Any] = None
    private_advertisement_enabled: Optional[Any] = None
    public_advertisment_enabled: Optional[Any] = None
    rate_limit: Optional[Any] = None
    routes_enabled: Optional[Any] = None
    service_policy_enabled: Optional[Any] = None
    slow_ddos_mitigation_enabled: Optional[Any] = None
    tls_security_level: Optional[str] = None
    trusted_client_enabled: Optional[Any] = None
    trusted_client_ip_headers_enabled: Optional[Any] = None
    vip_type: Optional[str] = None
    waf_enabled: Optional[Any] = None
    waf_enforcement_mode: Optional[str] = None
    waf_exclusion_enabled: Optional[Any] = None
    waf_policy_ref: Optional[list[ObjectRefType]] = None


class HTTPLoadbalancerInventoryType(F5XCBaseModel):
    """HTTP Loadbalancer inventory"""

    api_discovery: Optional[int] = None
    api_protection: Optional[int] = None
    bot_protection: Optional[int] = None
    cdnlb_results: Optional[list[HTTPLoadbalancerResultType]] = None
    client_side_defense: Optional[int] = None
    ddos_protection: Optional[int] = None
    http_only: Optional[int] = None
    httplb_results: Optional[list[HTTPLoadbalancerResultType]] = None
    ip_reputation: Optional[int] = None
    malicious_user_detection: Optional[int] = None
    malware_protection: Optional[int] = None
    namespace_service_policy: Optional[int] = None
    private_advertisement: Optional[int] = None
    public_advertisment: Optional[int] = None
    service_policy: Optional[int] = None
    waf: Optional[int] = None


class NGINXOneServerResultType(F5XCBaseModel):
    api_discovery_enabled: Optional[Any] = None
    domains: Optional[list[str]] = None
    name: Optional[str] = None
    nginx_one_object_id: Optional[str] = None
    nginx_one_object_name: Optional[str] = None
    nginx_one_server_name: Optional[str] = None
    total_routes: Optional[int] = None
    waf_enforcement_mode: Optional[str] = None
    waf_policy_file_name: Optional[str] = None
    waf_policy_management_platform: Optional[str] = None
    waf_policy_name: Optional[str] = None
    waf_security_log_enabled: Optional[bool] = None
    waf_security_log_file_names: Optional[list[str]] = None


class NGINXOneServerInventoryType(F5XCBaseModel):
    """Inventory of configured NGINX One Servers"""

    api_discovery_enabled_server_count: Optional[int] = None
    nginx_server_results: Optional[list[NGINXOneServerResultType]] = None
    waf_enabled_server_count: Optional[int] = None


class TCPLoadbalancerResultType(F5XCBaseModel):
    """TCP Loadbalancer Inventory Results"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    namespace_service_policy: Optional[Any] = None
    private_advertisement: Optional[Any] = None
    public_advertisment: Optional[Any] = None
    rate_limit: Optional[Any] = None
    service_policy: Optional[Any] = None
    tls_encryption: Optional[Any] = None


class TCPLoadbalancerInventoryType(F5XCBaseModel):
    """TCP Loadbalancer inventory"""

    namespace_service_policy: Optional[int] = None
    private_advertisement: Optional[int] = None
    public_advertisment: Optional[int] = None
    service_policy: Optional[int] = None
    tcplb_results: Optional[list[TCPLoadbalancerResultType]] = None
    tls_encryption: Optional[int] = None


class ThirdPartyApplicationResultType(F5XCBaseModel):
    """Third Party Application Inventory Results"""

    api_discovery_enabled: Optional[Any] = None
    name: Optional[str] = None


class ThirdPartyApplicationInventoryType(F5XCBaseModel):
    """Third Party Application inventory"""

    api_discovery: Optional[int] = None
    third_party_application_results: Optional[list[ThirdPartyApplicationResultType]] = None


class UDPLoadbalancerResultType(F5XCBaseModel):
    """UDP Loadbalancer Inventory Results"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    private_advertisement: Optional[Any] = None
    public_advertisment: Optional[Any] = None


class UDPLoadbalancerInventoryType(F5XCBaseModel):
    """UDP Loadbalancer inventory"""

    private_advertisement: Optional[int] = None
    public_advertisment: Optional[int] = None
    udplb_results: Optional[list[UDPLoadbalancerResultType]] = None


class ApplicationInventoryResponse(F5XCBaseModel):
    """Response for inventory of application related objects"""

    bigip_virtual_servers: Optional[BIGIPVirtualServerInventoryType] = None
    cdn_loadbalancers: Optional[HTTPLoadbalancerInventoryType] = None
    http_loadbalancers: Optional[HTTPLoadbalancerInventoryType] = None
    loadbalancers: Optional[int] = None
    nginx_one_servers: Optional[NGINXOneServerInventoryType] = None
    origin_pools: Optional[int] = None
    services_discovered: Optional[int] = None
    tcp_loadbalancers: Optional[TCPLoadbalancerInventoryType] = None
    third_party_applications: Optional[ThirdPartyApplicationInventoryType] = None
    udp_loadbalancers: Optional[UDPLoadbalancerInventoryType] = None


class CascadeDeleteItemType(F5XCBaseModel):
    """CascadeDeleteItemType is details of object that was handled as part of..."""

    error_message: Optional[str] = None
    object_name: Optional[str] = None
    object_type: Optional[str] = None
    object_uid: Optional[str] = None


class CascadeDeleteRequest(F5XCBaseModel):
    """CascadeDeleteRequest contains the name of the namespace that has to be..."""

    name: Optional[str] = None


class CascadeDeleteResponse(F5XCBaseModel):
    """CascadeDeleteResponse contains a list of objects in the namespace that..."""

    items: Optional[list[CascadeDeleteItemType]] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class CreateSpecType(F5XCBaseModel):
    """Creates a new namespace. Name of the object is name of the name space."""

    pass


class CreateRequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[Any] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """This is the read representation of the namespace object."""

    pass


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InitializersType(F5XCBaseModel):
    """Initializers tracks the progress of initialization of a configuration object"""

    pending: Optional[list[InitializerType]] = None
    result: Optional[StatusType] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectGetMetaType(F5XCBaseModel):
    """SystemObjectGetMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class CreateResponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[Any] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class EvaluateAPIAccessReq(F5XCBaseModel):
    """Request body of Evaluate API Access"""

    access_control_type: Optional[Literal['RBAC', 'PBAC', 'ALL']] = None
    item_lists: Optional[list[APIItemListReq]] = None
    namespace: Optional[str] = None


class EvaluateAPIAccessResp(F5XCBaseModel):
    """Response body of Evaluate API Access"""

    item_lists: Optional[list[APIItemListResp]] = None


class APIListReq(F5XCBaseModel):
    """NamespaceAPIListReq holds the namespace and its associated APIs"""

    item_lists: Optional[list[APIItemListReq]] = None
    namespace: Optional[str] = None


class EvaluateBatchAPIAccessReq(F5XCBaseModel):
    """Request body of Evaluate Batch API Access"""

    batch_namespace_api_list: Optional[list[APIListReq]] = None


class APIListResp(F5XCBaseModel):
    """NamespaceAPIListResp holds the namespace and its associated APIs"""

    item_lists: Optional[list[APIItemListResp]] = None
    namespace: Optional[str] = None


class EvaluateBatchAPIAccessResp(F5XCBaseModel):
    """Response body of Evaluate Batch API Access"""

    batch_namespace_api_list: Optional[list[APIListResp]] = None


class GetActiveAlertPoliciesResponse(F5XCBaseModel):
    """GetActiveAlertPoliciesResponse is the shape of the response for..."""

    alert_policies: Optional[list[ObjectRefType]] = None
    alert_policies_status: Optional[list[AlertPolicyStatus]] = None


class GetActiveNetworkPoliciesResponse(F5XCBaseModel):
    """GetActiveNetworkPoliciesResponse is the shape of the response for..."""

    network_policies: Optional[list[ObjectRefType]] = None


class GetActiveServicePoliciesResponse(F5XCBaseModel):
    """GetActiveServicePoliciesResponse is the shape of the response for..."""

    service_policies: Optional[list[ObjectRefType]] = None


class GetFastACLsForInternetVIPsResponse(F5XCBaseModel):
    """GetFastACLsForInternetVIPsResponse contains list of FastACLs refs that..."""

    fast_acls: Optional[list[ObjectRefType]] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ReplaceSpecType(F5XCBaseModel):
    """Replaces attributes of a namespace including its metadata like labels,..."""

    pass


class ReplaceRequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[Any] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class StatusMetaType(F5XCBaseModel):
    """StatusMetaType is metadata that all status must have."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    publish: Optional[Literal['STATUS_DO_NOT_PUBLISH', 'STATUS_PUBLISH']] = None
    status_id: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of object."""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[CreateRequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[ReplaceRequest] = None
    spec: Optional[Any] = None
    status: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class ListResponseItem(F5XCBaseModel):
    """By default a summary of namespace is returned in 'List'. By setting..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[Any] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[StatusObject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class LookupUserRolesReq(F5XCBaseModel):
    """Request body of LookupUserRoles request"""

    namespace: Optional[str] = None


class LookupUserRolesResp(F5XCBaseModel):
    """Response body of LookupUserRoles request"""

    roles: Optional[list[str]] = None


class NetworkingInventoryRequest(F5XCBaseModel):
    """Request for inventory of networking related objects"""

    pass


class NetworkingInventoryResponse(F5XCBaseModel):
    """Response for inventory of networking related objects"""

    cloud_links: Optional[int] = None
    dc_cluster_groups: Optional[int] = None
    global_networks: Optional[int] = None
    segments: Optional[int] = None
    site_mesh_groups: Optional[int] = None
    sites: Optional[int] = None


class ReplaceResponse(F5XCBaseModel):
    pass


class SetActiveAlertPoliciesRequest(F5XCBaseModel):
    """SetActiveAlertPoliciesRequest is the shape of the request for..."""

    alert_policies: Optional[list[ObjectRefType]] = None
    namespace: Optional[str] = None


class SetActiveAlertPoliciesResponse(F5XCBaseModel):
    """SetActiveAlertPoliciesResponse is the shape of the response for..."""

    pass


class SetActiveNetworkPoliciesRequest(F5XCBaseModel):
    """SetActiveNetworkPoliciesRequest is the shape of the request for..."""

    namespace: Optional[str] = None
    network_policies: Optional[list[ObjectRefType]] = None


class SetActiveNetworkPoliciesResponse(F5XCBaseModel):
    """SetActiveNetworkPoliciesResponse is the shape of the response for..."""

    pass


class SetActiveServicePoliciesRequest(F5XCBaseModel):
    """SetActiveServicePoliciesRequest is the shape of the request for..."""

    namespace: Optional[str] = None
    service_policies: Optional[list[ObjectRefType]] = None


class SetActiveServicePoliciesResponse(F5XCBaseModel):
    """SetActiveServicePoliciesResponse is the shape of the response for..."""

    pass


class SetFastACLsForInternetVIPsRequest(F5XCBaseModel):
    """SetFastACLsForInternetVIPsRequest contains list of FastACLs refs that..."""

    fast_acls: Optional[list[ObjectRefType]] = None
    namespace: Optional[str] = None


class SetFastACLsForInternetVIPsResponse(F5XCBaseModel):
    """SetFastACLsForInternetVIPsResponse is empty"""

    pass


class UpdateAllowAdvertiseOnPublicReq(F5XCBaseModel):
    """Request body of UpdateAllowAdvertiseOnPublic request"""

    allow_advertise_on_public: Optional[Literal['Default', 'Enable', 'Disable']] = None
    namespace: Optional[str] = None


class UpdateAllowAdvertiseOnPublicResp(F5XCBaseModel):
    """Response body of UpdateAllowAdvertiseOnPublic request"""

    result: Optional[bool] = None


class ValidateRulesReq(F5XCBaseModel):
    """Request body of ValidateRulesReq request"""

    namespace: Optional[str] = None
    validator_evaluation: Optional[dict[str, Any]] = None
    value: Optional[str] = None


class ValidationResult(F5XCBaseModel):
    message: Optional[str] = None
    severity: Optional[Literal['ERROR', 'INFO', 'WARNING', 'SUCCESS']] = None


class ValidateRulesResponse(F5XCBaseModel):
    """Response body of ValidateRulesReq request"""

    error: Optional[str] = None
    success: Optional[bool] = None
    validation_results: Optional[list[ValidationResult]] = None


class SuggestedItem(F5XCBaseModel):
    """A tuple with a suggested value and it's description."""

    description: Optional[str] = None
    ref_value: Optional[ObjectRefType] = None
    str_value: Optional[str] = None
    title: Optional[str] = None
    value: Optional[str] = None


class SuggestValuesResp(F5XCBaseModel):
    """Response body of SuggestValues request"""

    items: Optional[list[SuggestedItem]] = None


# Convenience aliases
Spec = CreateSpecType
Spec = GetSpecType
Spec = ReplaceSpecType
