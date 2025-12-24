"""BotDetectionRule resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.bot_detection_rule.models import (
    BotDetectionRuleListItem,
    Config,
    RegionRuleConfig,
    ConfigPerBotInfra,
    ConfigChangeReason,
    ConfigChange,
    BotInfraDeploymentStatusDetails,
    RegionStatus,
    BotInfraDeploymentDetails,
    ConfigDeploymentDetailsPerBotInfra,
    BotInfrastructure,
    BotDetectionRulebotdetectionrulesdeployment,
    DeployBotDetectionRulesResponse,
    DraftRuleCounts,
    RuleStateCounts,
    EnvironmentRuleCounts,
    Empty,
    RuleChangeTypeModification,
    RuleChange,
    GetBotDetectionRuleChangeHistoryResponse,
    GetBotDetectionRulesDeploymentDetailsResponse,
    GetBotDetectionRulesDeploymentsResponse,
    GetBotDetectionRulesDraftResponse,
    RuleSummary,
    GetBotDetectionRulesSummaryResponse,
    ObjectRefType,
    ObjectGetMetaType,
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
    SaveDraftResponse,
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


class BotDetectionRuleResource:
    """API methods for bot_detection_rule.

    Configures Bot Detection Rule
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.bot_detection_rule.CreateSpecType(...)
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
    ) -> list[BotDetectionRuleListItem]:
        """List bot_detection_rule resources in a namespace.

        List the set of bot_detection_rule in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_detection_rules"
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
            return [BotDetectionRuleListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a bot_detection_rule by name.

        Get Bot Detection Rule

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
        path = "/api/shape/bot/namespaces/{namespace}/bot_detection_rules/{name}"
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
            raise F5XCValidationError("bot_detection_rule", "get", e, response) from e

    def deploy_bot_detection_rules(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> DeployBotDetectionRulesResponse:
        """Deploy Bot Detection Rules for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeployBotDetectionRulesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "deploy_bot_detection_rules", e, response) from e

    def get_bot_detection_rules_deployments(
        self,
        namespace: str,
        rules_deployment_status: list | None = None,
    ) -> GetBotDetectionRulesDeploymentsResponse:
        """Get Bot Detection Rules Deployments for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules/deployments"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if rules_deployment_status is not None:
            params["rules_deployment_status"] = rules_deployment_status

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotDetectionRulesDeploymentsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "get_bot_detection_rules_deployments", e, response) from e

    def get_bot_detection_rules_deployment_details(
        self,
        namespace: str,
        deployment_id: str,
    ) -> GetBotDetectionRulesDeploymentDetailsResponse:
        """Get Bot Detection Rules Deployment Details for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules/deployments/{deployment_id}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{deployment_id}", deployment_id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotDetectionRulesDeploymentDetailsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "get_bot_detection_rules_deployment_details", e, response) from e

    def get_bot_detection_rules_draft(
        self,
        namespace: str,
    ) -> GetBotDetectionRulesDraftResponse:
        """Get Bot Detection Rules Draft for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules/draft"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotDetectionRulesDraftResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "get_bot_detection_rules_draft", e, response) from e

    def save_draft(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SaveDraftResponse:
        """Save Draft for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules/draft"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SaveDraftResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "save_draft", e, response) from e

    def discard_draft(
        self,
        namespace: str,
    ) -> Empty:
        """Discard Draft for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules/draft"
        path = path.replace("{namespace}", namespace)


        try:
            self._http.delete(path)
            return {}
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "discard_draft", e, response) from e

    def get_bot_detection_rules_summary(
        self,
        namespace: str,
    ) -> GetBotDetectionRulesSummaryResponse:
        """Get Bot Detection Rules Summary for bot_detection_rule.

        
        """
        path = "/api/shape/bot/custom/namespaces/{namespace}/bot_detection_rules/summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotDetectionRulesSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "get_bot_detection_rules_summary", e, response) from e

    def get_bot_detection_rule_change_history(
        self,
        namespace: str,
        id: str,
    ) -> GetBotDetectionRuleChangeHistoryResponse:
        """Get Bot Detection Rule Change History for bot_detection_rule.

        
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_detection_rules/{id}/history"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetBotDetectionRuleChangeHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_detection_rule", "get_bot_detection_rule_change_history", e, response) from e

