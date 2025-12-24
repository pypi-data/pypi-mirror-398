"""BotInfrastructure resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.bot_infrastructure.models import (
    BotInfrastructureListItem,
    PolicyMetadata,
    EndpointPolicyMetadata,
    Egress,
    Ingress,
    InfraCloudHosted,
    IPInfo,
    Device,
    InfraF5HostedOnPrem,
    GetSpecType,
    ReplaceSpecType,
    ObjectCreateMetaType,
    Production,
    Testing,
    CreateSpecInfraCloudHosted,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    DeployPolicyMetadata,
    DeployPoliciesRequest,
    DeployPoliciesResponse,
    DeploymentData,
    DeploymentHistoryData,
    DeploymentHistoryResponse,
    DeploymentStatusResponse,
    ObjectRefType,
    ObjectReplaceMetaType,
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
    SuggestValuesReq,
    ObjectRefType,
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


class BotInfrastructureResource:
    """API methods for bot_infrastructure.

    Configures Bot Infrastructure by bot infrastructure
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.bot_infrastructure.CreateSpecType(...)
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    CreateSpecType = CreateSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: PolicyMetadata | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new bot_infrastructure.

        Create Bot Infrastructure

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
        path = "/api/shape/bot/namespaces/{metadata.namespace}/bot_infrastructures"
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
            raise F5XCValidationError("bot_infrastructure", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: PolicyMetadata | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing bot_infrastructure.

        Replace Bot Infrastructure

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
        path = "/api/shape/bot/namespaces/{metadata.namespace}/bot_infrastructures/{metadata.name}"
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
            raise F5XCValidationError("bot_infrastructure", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[BotInfrastructureListItem]:
        """List bot_infrastructure resources in a namespace.

        List the set of bot_infrastructure in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_infrastructures"
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
            return [BotInfrastructureListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("bot_infrastructure", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a bot_infrastructure by name.

        Get Bot Infrastructure

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
        path = "/api/shape/bot/namespaces/{namespace}/bot_infrastructures/{name}"
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
            raise F5XCValidationError("bot_infrastructure", "get", e, response) from e

    def deployment_history(
        self,
        namespace: str,
        name: str,
    ) -> DeploymentHistoryResponse:
        """Deployment History for bot_infrastructure.

        Get deployment history
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_infrastructures/{name}/deployment_history"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeploymentHistoryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_infrastructure", "deployment_history", e, response) from e

    def deployment_status_overview(
        self,
        namespace: str,
        name: str,
    ) -> DeploymentStatusResponse:
        """Deployment Status Overview for bot_infrastructure.

        Get deployment status
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_infrastructures/{name}/deployment_status"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeploymentStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_infrastructure", "deployment_status_overview", e, response) from e

    def deploy_policies_to_bot_infra(
        self,
        namespace: str,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> DeployPoliciesResponse:
        """Deploy Policies To Bot Infra for bot_infrastructure.

        Deploy Policies to Bot Infrastructure
        """
        path = "/api/shape/bot/namespaces/{namespace}/bot_infrastructures/{name}/policies"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DeployPoliciesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_infrastructure", "deploy_policies_to_bot_infra", e, response) from e

    def suggest_values(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Suggest Values for bot_infrastructure.

        Returns suggested values for the specified field in the given...
        """
        path = "/api/shape/bot/namespaces/{namespace}/suggest-values"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("bot_infrastructure", "suggest_values", e, response) from e

