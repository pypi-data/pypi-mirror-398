"""Namespace resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.namespace.models import (
    NamespaceListItem,
    ObjectRefType,
    AlertPolicyStatus,
    Empty,
    ObjectRefType,
    APIItemReq,
    APIItemListReq,
    AccessEnablerAddonService,
    APIItemResp,
    APIItemListResp,
    BIGIPVirtualServerInventoryFilterType,
    HTTPLoadbalancerInventoryFilterType,
    NGINXOneServerInventoryFilterType,
    TCPLoadbalancerInventoryFilterType,
    ThirdPartyApplicationFilterType,
    UDPLoadbalancerInventoryFilterType,
    AllApplicationInventoryRequest,
    AllApplicationInventoryWafFilterRequest,
    HTTPLoadbalancerWafFilterResultType,
    AllApplicationInventoryWafFilterResponse,
    ApiEndpointsStatsAllNSReq,
    ApiEndpointsStatsNSReq,
    ApiEndpointsStatsNSRsp,
    ApplicationInventoryRequest,
    BIGIPVirtualServerResultType,
    BIGIPVirtualServerInventoryType,
    HTTPLoadbalancerResultType,
    HTTPLoadbalancerInventoryType,
    NGINXOneServerResultType,
    NGINXOneServerInventoryType,
    TCPLoadbalancerResultType,
    TCPLoadbalancerInventoryType,
    ThirdPartyApplicationResultType,
    ThirdPartyApplicationInventoryType,
    UDPLoadbalancerResultType,
    UDPLoadbalancerInventoryType,
    ApplicationInventoryResponse,
    CascadeDeleteItemType,
    CascadeDeleteRequest,
    CascadeDeleteResponse,
    ObjectCreateMetaType,
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
    EvaluateAPIAccessReq,
    EvaluateAPIAccessResp,
    APIListReq,
    EvaluateBatchAPIAccessReq,
    APIListResp,
    EvaluateBatchAPIAccessResp,
    GetActiveAlertPoliciesResponse,
    GetActiveNetworkPoliciesResponse,
    GetActiveServicePoliciesResponse,
    GetFastACLsForInternetVIPsResponse,
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
    LookupUserRolesReq,
    LookupUserRolesResp,
    NetworkingInventoryRequest,
    NetworkingInventoryResponse,
    ReplaceResponse,
    SetActiveAlertPoliciesRequest,
    SetActiveAlertPoliciesResponse,
    SetActiveNetworkPoliciesRequest,
    SetActiveNetworkPoliciesResponse,
    SetActiveServicePoliciesRequest,
    SetActiveServicePoliciesResponse,
    SetFastACLsForInternetVIPsRequest,
    SetFastACLsForInternetVIPsResponse,
    UpdateAllowAdvertiseOnPublicReq,
    UpdateAllowAdvertiseOnPublicResp,
    ValidateRulesReq,
    ValidationResult,
    ValidateRulesResponse,
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


class NamespaceResource:
    """API methods for namespace.

    namespace creates logical independent workspace within a tenant....
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.namespace.CreateSpecType(...)
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list(
        self,
        namespace: str | None = None,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[NamespaceListItem]:
        """List namespace resources in a namespace.

        List the set of namespace in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/web/namespaces"

        params: dict[str, Any] = {}
        if namespace is not None:
            params["namespace"] = namespace
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
            return [NamespaceListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("namespace", "list", e, response) from e

    def create(
        self,
        namespace: str,
        name: str,
        spec: ObjectRefType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new namespace.

        Creates a new namespace. Name of the object is name of the name space.

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
        path = "/api/web/namespaces"
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
            raise F5XCValidationError("namespace", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: ObjectRefType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing namespace.

        Replaces attributes of a namespace including its metadata like...

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
        path = "/api/web/namespaces/{metadata.name}"
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
            raise F5XCValidationError("namespace", "replace", e, response) from e

    def get(
        self,
        name: str,
        namespace: str | None = None,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a namespace by name.

        This is the read representation of the namespace object.

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
        path = "/api/web/namespaces/{name}"
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if namespace is not None:
            params["namespace"] = namespace
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
            raise F5XCValidationError("namespace", "get", e, response) from e

    def all_application_inventory(
        self,
        body: dict[str, Any] | None = None,
    ) -> ApplicationInventoryResponse:
        """All Application Inventory for namespace.

        AllApplicationInventory returns inventory of configured application...
        """
        path = "/api/config/namespaces/system/all_application_inventory"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ApplicationInventoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "all_application_inventory", e, response) from e

    def all_application_inventory_waf(
        self,
        body: dict[str, Any] | None = None,
    ) -> AllApplicationInventoryWafFilterResponse:
        """All Application Inventory Waf for namespace.

        AllApplicationInventoryWaf returns inventory of configured...
        """
        path = "/api/config/namespaces/system/all_application_inventory_waf_filters"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return AllApplicationInventoryWafFilterResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "all_application_inventory_waf", e, response) from e

    def get_api_endpoints_stats_all_namespaces(
        self,
        body: dict[str, Any] | None = None,
    ) -> ApiEndpointsStatsNSRsp:
        """Get Api Endpoints Stats All Namespaces for namespace.

        Get api endpoints stats for all Namespaces. This API is specific to...
        """
        path = "/api/ml/data/namespaces/system/api_endpoints/all_ns_stats"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ApiEndpointsStatsNSRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "get_api_endpoints_stats_all_namespaces", e, response) from e

    def evaluate_api_access(
        self,
        body: dict[str, Any] | None = None,
    ) -> EvaluateAPIAccessResp:
        """Evaluate Api Access for namespace.

        EvaluateAPIAccess can evaluate multiple lists of API url, method...
        """
        path = "/api/web/namespaces/system/evaluate-api-access"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EvaluateAPIAccessResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "evaluate_api_access", e, response) from e

    def evaluate_batch_api_access(
        self,
        body: dict[str, Any] | None = None,
    ) -> EvaluateBatchAPIAccessResp:
        """Evaluate Batch Api Access for namespace.

        EvaluateBatchAPIAccess can evaluate multiple lists of API url,...
        """
        path = "/api/web/namespaces/system/evaluate-batch-api-access"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EvaluateBatchAPIAccessResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "evaluate_batch_api_access", e, response) from e

    def lookup_user_roles(
        self,
        body: dict[str, Any] | None = None,
    ) -> LookupUserRolesResp:
        """Lookup User Roles for namespace.

        LookupUserRoles returns roles for the the given user, namespace
        """
        path = "/api/web/namespaces/system/lookup-user-roles"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LookupUserRolesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "lookup_user_roles", e, response) from e

    def networking_inventory(
        self,
        body: dict[str, Any] | None = None,
    ) -> NetworkingInventoryResponse:
        """Networking Inventory for namespace.

        NetworkingInventory returns inventory of configured networking...
        """
        path = "/api/config/namespaces/system/networking_inventory"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return NetworkingInventoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "networking_inventory", e, response) from e

    def suggest_values(
        self,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Suggest Values for namespace.

        Returns suggested values for the specified field in the given...
        """
        path = "/api/cloud-data/namespaces/system/suggest-values"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "suggest_values", e, response) from e

    def update_allow_advertise_on_public(
        self,
        body: dict[str, Any] | None = None,
    ) -> UpdateAllowAdvertiseOnPublicResp:
        """Update Allow Advertise On Public for namespace.

        UpdateAllowAdvertiseOnPublic can update a config to allow advertise...
        """
        path = "/api/config/namespaces/system/update_allow_advertise_on_public"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateAllowAdvertiseOnPublicResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "update_allow_advertise_on_public", e, response) from e

    def validate_rules(
        self,
        body: dict[str, Any] | None = None,
    ) -> ValidateRulesResponse:
        """Validate Rules for namespace.

        ValidateRules returns whether the value is valid or not for the...
        """
        path = "/api/config/namespaces/system/validate_rules"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ValidateRulesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "validate_rules", e, response) from e

    def get_active_alert_policies(
        self,
        namespace: str,
    ) -> GetActiveAlertPoliciesResponse:
        """Get Active Alert Policies for namespace.

        GetActiveAlertPolicies returns the list of active alert policies for...
        """
        path = "/api/config/namespaces/{namespace}/active_alert_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetActiveAlertPoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "get_active_alert_policies", e, response) from e

    def set_active_alert_policies(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SetActiveAlertPoliciesResponse:
        """Set Active Alert Policies for namespace.

        SetActiveAlertPolicies sets the active alert policies for the...
        """
        path = "/api/config/namespaces/{namespace}/active_alert_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SetActiveAlertPoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "set_active_alert_policies", e, response) from e

    def get_active_network_policies(
        self,
        namespace: str,
    ) -> GetActiveNetworkPoliciesResponse:
        """Get Active Network Policies for namespace.

        GetActiveNetworkPolicies resturn the list of active network policies...
        """
        path = "/api/config/namespaces/{namespace}/active_network_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetActiveNetworkPoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "get_active_network_policies", e, response) from e

    def set_active_network_policies(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SetActiveNetworkPoliciesResponse:
        """Set Active Network Policies for namespace.

        SetActiveNetworkPolicies sets the active network policies for the...
        """
        path = "/api/config/namespaces/{namespace}/active_network_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SetActiveNetworkPoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "set_active_network_policies", e, response) from e

    def get_active_service_policies(
        self,
        namespace: str,
    ) -> GetActiveServicePoliciesResponse:
        """Get Active Service Policies for namespace.

        GetActiveServicePolicies resturn the list of active service policies...
        """
        path = "/api/config/namespaces/{namespace}/active_service_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetActiveServicePoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "get_active_service_policies", e, response) from e

    def set_active_service_policies(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SetActiveServicePoliciesResponse:
        """Set Active Service Policies for namespace.

        SetActiveServicePolicies sets the active service policies for the...
        """
        path = "/api/config/namespaces/{namespace}/active_service_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SetActiveServicePoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "set_active_service_policies", e, response) from e

    def get_api_endpoints_stats(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ApiEndpointsStatsNSRsp:
        """Get Api Endpoints Stats for namespace.

        Get api endpoints stats for the given Namespace
        """
        path = "/api/ml/data/namespaces/{namespace}/api_endpoints/stats"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ApiEndpointsStatsNSRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "get_api_endpoints_stats", e, response) from e

    def application_inventory(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> ApplicationInventoryResponse:
        """Application Inventory for namespace.

        ApplicationInventory returns inventory of configured application...
        """
        path = "/api/config/namespaces/{namespace}/application_inventory"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ApplicationInventoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "application_inventory", e, response) from e

    def get_fast_ac_ls_for_internet_vi_ps(
        self,
        namespace: str,
    ) -> GetFastACLsForInternetVIPsResponse:
        """Get Fast Ac Ls For Internet Vi Ps for namespace.

        GetFastACLsForInternetVIPs Returns the list of Active FastACLs for...
        """
        path = "/api/config/namespaces/{namespace}/fast_acls_for_internet_vips"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetFastACLsForInternetVIPsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "get_fast_ac_ls_for_internet_vi_ps", e, response) from e

    def set_fast_ac_ls_for_internet_vi_ps(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SetFastACLsForInternetVIPsResponse:
        """Set Fast Ac Ls For Internet Vi Ps for namespace.

        SetFastACLsForInternetVIPs activates the passed list of FastACLs for...
        """
        path = "/api/config/namespaces/{namespace}/fast_acls_for_internet_vips"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SetFastACLsForInternetVIPsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "set_fast_ac_ls_for_internet_vi_ps", e, response) from e

    def custom_suggest_values(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Custom Suggest Values for namespace.

        SuggestValues returns suggested values for the specified field in...
        """
        path = "/api/web/namespaces/{namespace}/suggest-values"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "custom_suggest_values", e, response) from e

    def cascade_delete(
        self,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CascadeDeleteResponse:
        """Cascade Delete for namespace.

        CascadeDelete will delete the namespace and all configuration...
        """
        path = "/api/web/namespaces/{name}/cascade_delete"
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CascadeDeleteResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("namespace", "cascade_delete", e, response) from e

