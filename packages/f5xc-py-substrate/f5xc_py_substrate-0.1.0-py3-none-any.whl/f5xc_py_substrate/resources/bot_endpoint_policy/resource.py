"""BotEndpointPolicy resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.bot_endpoint_policy.models import (
    BotEndpointPolicyListItem,
    GenericEmptyType,
    CookieMatcherValue,
    CookieMatcherType,
    CookieMatcher,
    Empty,
    Cookie,
    DomainMatcherType,
    DomainMatcher,
    DomainOperator,
    MatcherValue,
    MatcherType,
    HeaderMatcher,
    HeaderNameValuePair,
    HeaderOperatorEmptyType,
    HeaderOperator,
    PathMatcherValue,
    PathMatcherType,
    PathMatcher,
    PathOperator,
    PolicyVersion,
    WebClientBlockMitigationActionType,
    WebClientContinueMitigationHeader,
    WebClientContinueMitigationActionType,
    BotPolicyFlowLabelAccountManagementChoiceType,
    BotPolicyFlowLabelAuthenticationChoiceType,
    BotPolicyFlowLabelCreditCardChoiceType,
    BotPolicyFlowLabelDeliveryServicesChoiceType,
    BotPolicyFlowLabelFinancialServicesChoiceType,
    BotPolicyFlowLabelFlightChoiceType,
    BotPolicyFlowLabelGuestSessionChoiceType,
    BotPolicyFlowLabelLoyaltyChoiceType,
    BotPolicyFlowLabelMailingListChoiceType,
    BotPolicyFlowLabelMediaChoiceType,
    BotPolicyFlowLabelMiscellaneousChoiceType,
    BotPolicyFlowLabelProfileManagementChoiceType,
    BotPolicyFlowLabelQuotesChoiceType,
    BotPolicyFlowLabelSearchChoiceType,
    BotPolicyFlowLabelShoppingGiftCardsChoiceType,
    BotPolicyFlowLabelSocialsChoiceType,
    BotPolicyFlowLabelCategoriesChoiceType,
    MessageMetaType,
    QueryMatcher,
    QueryOperator,
    RequestBodyMatcher,
    RequestBodyOperator,
    ResponseBodyMatcherValue,
    ResponseBodyMatcherType,
    ResponseBodyMatcher,
    ResponseBody,
    ResponseCodeMatcherType,
    ResponseCodeMatcher,
    ResponseCode,
    ResponseHeaderMatcherValue,
    ResponseHeaderMatcherType,
    ResponseHeaderMatcher,
    ResponseHeader,
    TransactionResultType,
    TransactionResult,
    WebClientAddHeaderToRequest,
    WebClientTransformMitigationActionChoiceType,
    UserNameType,
    ProtectedMobileEndpoint,
    ProtectedMobileEndpointList,
    WebClientRedirectMitigationActionType,
    ProtectedWebEndpoint,
    ProtectedWebEndpointList,
    ProtectedEndpoints,
    ReplaceSpecType,
    CustomReplaceRequest,
    CustomReplaceResponse,
    GetContentResponse,
    Policy,
    GetPoliciesAndVersionsListResponse,
    ObjectRefType,
    ObjectGetMetaType,
    ObjectReplaceMetaType,
    ReplaceRequest,
    GetSpecType,
    ConditionType,
    StatusMetaType,
    StatusObject,
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
    PolicyVersionsResponse,
    ReplaceResponse,
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


class BotEndpointPolicyResource:
    """API methods for bot_endpoint_policy.

    Configures Bot Endpoint Policy
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.bot_endpoint_policy.CreateSpecType(...)
    ReplaceSpecType = ReplaceSpecType
    GetSpecType = GetSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def replace(
        self,
        namespace: str,
        name: str,
        spec: GenericEmptyType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing bot_endpoint_policy.

        Replace Bot Endpoint Policy

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
        path = "/api/shape/bot/namespaces/{metadata.namespace}/bot_endpoint_policys/{metadata.name}"
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
            raise F5XCValidationError("bot_endpoint_policy", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[BotEndpointPolicyListItem]:
        """List bot_endpoint_policy resources in a namespace.

        List the set of bot_endpoint_policy in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_endpoint_policys"
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
            return [BotEndpointPolicyListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("bot_endpoint_policy", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a bot_endpoint_policy by name.

        Get Bot Endpoint Policy

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
        path = "/api/shape/bot/namespaces/{namespace}/bot_endpoint_policys/{name}"
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
            raise F5XCValidationError("bot_endpoint_policy", "get", e, response) from e

    def get_endpoint_policies_and_versions_list(
        self,
        namespace: str,
    ) -> GetPoliciesAndVersionsListResponse:
        """Get Endpoint Policies And Versions List for bot_endpoint_policy.

        Get all bot endpoint policies and versions
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_endpoint_policies"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetPoliciesAndVersionsListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_endpoint_policy", "get_endpoint_policies_and_versions_list", e, response) from e

    def custom_replace(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> CustomReplaceResponse:
        """Custom Replace for bot_endpoint_policy.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_endpoint_policys/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.put(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CustomReplaceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_endpoint_policy", "custom_replace", e, response) from e

    def get_endpoint_policy_versions(
        self,
        namespace: str,
        name: str,
    ) -> PolicyVersionsResponse:
        """Get Endpoint Policy Versions for bot_endpoint_policy.

        Get bot endpoint policy versions
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_endpoint_policy/{name}/versions"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return PolicyVersionsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_endpoint_policy", "get_endpoint_policy_versions", e, response) from e

    def get_content(
        self,
        namespace: str,
        name: str,
        number: str,
    ) -> GetContentResponse:
        """Get Content for bot_endpoint_policy.

        Get the content of the specific policy version
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_endpoint_policys/{name}/versions/{number}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)
        path = path.replace("{number}", number)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetContentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_endpoint_policy", "get_content", e, response) from e

