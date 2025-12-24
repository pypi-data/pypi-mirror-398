"""TerraformParameters resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.terraform_parameters.models import (
    ObjectRefType,
    ProtobufAny,
    ConditionType,
    StatusMetaType,
    ApplyStatus,
    ForceDeleteRequest,
    ForceDeleteResponse,
    GlobalSpecType,
    GetResponse,
    PlanStatus,
    StatusObject,
    GetStatusResponse,
    RunRequest,
    RunResponse,
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


class TerraformParametersResource:
    """API methods for terraform_parameters.

    View Terraform Parameters is set of parameters that are used by...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.terraform_parameters.CreateSpecType(...)
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def force_delete(
        self,
        namespace: str,
        view_kind: str,
        view_name: str,
        body: dict[str, Any] | None = None,
    ) -> ForceDeleteResponse:
        """Force Delete for terraform_parameters.

        force delete view object. This can result in staled objects in cloud...
        """
        path = "/api/terraform/namespaces/{namespace}/terraform/{view_kind}/{view_name}/force-delete"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{view_kind}", view_kind)
        path = path.replace("{view_name}", view_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ForceDeleteResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("terraform_parameters", "force_delete", e, response) from e

    def run(
        self,
        namespace: str,
        view_kind: str,
        view_name: str,
        body: dict[str, Any] | None = None,
    ) -> RunResponse:
        """Run for terraform_parameters.

        perform terraform actions for a given view. Supported actions are...
        """
        path = "/api/terraform/namespaces/{namespace}/terraform/{view_kind}/{view_name}/run"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{view_kind}", view_kind)
        path = path.replace("{view_name}", view_name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RunResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("terraform_parameters", "run", e, response) from e

    def get(
        self,
        namespace: str,
        view_kind: str,
        view_name: str,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a terraform_parameters by name.

        returned from list of terraform parameter objects for a given view.

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
        path = "/api/config/namespaces/{namespace}/terraform_parameters/{view_kind}/{view_name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{view_kind}", view_kind)
        path = path.replace("{view_name}", view_name)

        params: dict[str, Any] = {}

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
            raise F5XCValidationError("terraform_parameters", "get", e, response) from e

    def get_status(
        self,
        namespace: str,
        view_kind: str,
        view_name: str,
    ) -> GetStatusResponse:
        """Get Status for terraform_parameters.

        returned from list of terraform parameter status objects for a given view.
        """
        path = "/api/config/namespaces/{namespace}/terraform_parameters/{view_kind}/{view_name}/status"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{view_kind}", view_kind)
        path = path.replace("{view_name}", view_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("terraform_parameters", "get_status", e, response) from e

