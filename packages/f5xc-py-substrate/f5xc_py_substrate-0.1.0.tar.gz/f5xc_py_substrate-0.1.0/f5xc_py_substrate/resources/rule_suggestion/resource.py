"""RuleSuggestion resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.rule_suggestion.models import (
    Empty,
    APIProtectionRuleAction,
    HttpMethodMatcherType,
    AsnMatchList,
    ObjectRefType,
    AsnMatcherType,
    LabelSelectorType,
    IpMatcherType,
    PrefixMatchList,
    IPThreatCategoryListType,
    TlsFingerprintMatcherType,
    ClientMatcher,
    MessageMetaType,
    MatcherType,
    CookieMatcherType,
    HeaderMatcherType,
    JWTClaimMatcherType,
    QueryParameterMatcherType,
    RequestMatcher,
    APIEndpointProtectionRule,
    ApiEndpointDetails,
    ObjectRefType,
    InlineRateLimiter,
    ApiEndpointRule,
    FallThroughRule,
    CustomFallThroughMode,
    OpenApiFallThroughMode,
    ValidationSettingForQueryParameters,
    ValidationPropertySetting,
    OpenApiValidationCommonSettings,
    OpenApiValidationModeActiveResponse,
    OpenApiValidationModeActive,
    OpenApiValidationMode,
    OpenApiValidationAllSpecEndpointsSettings,
    OpenApiValidationRule,
    BodySectionMaskingOptions,
    SensitiveDataTypes,
    GetSuggestedAPIEndpointProtectionRuleReq,
    GetSuggestedAPIEndpointProtectionRuleRsp,
    GetSuggestedOasValidationRuleReq,
    GetSuggestedOasValidationRuleRsp,
    GetSuggestedRateLimitRuleReq,
    GetSuggestedRateLimitRuleRsp,
    GetSuggestedSensitiveDataRuleReq,
    GetSuggestedSensitiveDataRuleRsp,
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


class RuleSuggestionResource:
    """API methods for rule_suggestion.

    APIs to get rule suggestions from App Security Monitoring pages
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.rule_suggestion.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_suggested_api_endpoint_protection_rule(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedAPIEndpointProtectionRuleRsp:
        """Get Suggested Api Endpoint Protection Rule for rule_suggestion.

        Suggest API endpoint protection rule for a given path
        """
        path = "/api/config/namespaces/{namespace}/api_sec/rule_suggestion/api_endpoint_protection"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedAPIEndpointProtectionRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("rule_suggestion", "get_suggested_api_endpoint_protection_rule", e, response) from e

    def get_suggested_sensitive_data_rule(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedSensitiveDataRuleRsp:
        """Get Suggested Sensitive Data Rule for rule_suggestion.

        Suggest sensitive data rule for a given path
        """
        path = "/api/config/namespaces/{namespace}/api_sec/rule_suggestion/data_exposure"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedSensitiveDataRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("rule_suggestion", "get_suggested_sensitive_data_rule", e, response) from e

    def get_suggested_oas_validation_rule(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedOasValidationRuleRsp:
        """Get Suggested Oas Validation Rule for rule_suggestion.

        Suggest Open API specification validation rule for a given path
        """
        path = "/api/config/namespaces/{namespace}/api_sec/rule_suggestion/oas_validation"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedOasValidationRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("rule_suggestion", "get_suggested_oas_validation_rule", e, response) from e

    def get_suggested_rate_limit_rule(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> GetSuggestedRateLimitRuleRsp:
        """Get Suggested Rate Limit Rule for rule_suggestion.

        Suggest rate limit rule for a given path
        """
        path = "/api/config/namespaces/{namespace}/api_sec/rule_suggestion/rate_limit"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSuggestedRateLimitRuleRsp(**response)
        except ValidationError as e:
            raise F5XCValidationError("rule_suggestion", "get_suggested_rate_limit_rule", e, response) from e

