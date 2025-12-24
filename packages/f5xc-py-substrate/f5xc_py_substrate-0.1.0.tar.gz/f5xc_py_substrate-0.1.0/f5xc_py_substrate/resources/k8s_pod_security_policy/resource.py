"""K8sPodSecurityPolicy resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.k8s_pod_security_policy.models import (
    K8sPodSecurityPolicyListItem,
    Empty,
    K8sPodSecurityPolicycapabilitylisttype,
    ObjectCreateMetaType,
    K8sPodSecurityPolicyhostpathtype,
    K8sPodSecurityPolicyidrangetype,
    K8sPodSecurityPolicyidstrategyoptionstype,
    K8sPodSecurityPolicypodsecuritypolicyspectype,
    K8sPodSecurityPolicycreatespectype,
    K8sPodSecurityPolicycreaterequest,
    ObjectGetMetaType,
    K8sPodSecurityPolicygetspectype,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    K8sPodSecurityPolicycreateresponse,
    K8sPodSecurityPolicydeleterequest,
    ObjectRefType,
    ObjectReplaceMetaType,
    K8sPodSecurityPolicyreplacespectype,
    K8sPodSecurityPolicyreplacerequest,
    ConditionType,
    StatusMetaType,
    K8sPodSecurityPolicystatusobject,
    K8sPodSecurityPolicygetresponse,
    ProtobufAny,
    ErrorType,
    K8sPodSecurityPolicylistresponseitem,
    K8sPodSecurityPolicylistresponse,
    K8sPodSecurityPolicyreplaceresponse,
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


class K8sPodSecurityPolicyResource:
    """API methods for k8s_pod_security_policy.

    Pod Security Policies enable fine-grained authorization of pod...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.k8s_pod_security_policy.CreateSpecType(...)

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
    ) -> K8sPodSecurityPolicycreateresponse:
        """Create a new k8s_pod_security_policy.

        Create k8s_pod_security_policy will create the object in the storage...

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
        path = "/api/config/namespaces/{metadata.namespace}/k8s_pod_security_policys"
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
            return K8sPodSecurityPolicycreateresponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("k8s_pod_security_policy", "create", e, response) from e

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
    ) -> K8sPodSecurityPolicyreplaceresponse:
        """Replace an existing k8s_pod_security_policy.

        Replacing an k8s_pod_security_policy object will update the object...

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
        path = "/api/config/namespaces/{metadata.namespace}/k8s_pod_security_policys/{metadata.name}"
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
            return K8sPodSecurityPolicyreplaceresponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("k8s_pod_security_policy", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[K8sPodSecurityPolicyListItem]:
        """List k8s_pod_security_policy resources in a namespace.

        List the set of k8s_pod_security_policy in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/k8s_pod_security_policys"
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
            return [K8sPodSecurityPolicyListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("k8s_pod_security_policy", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> K8sPodSecurityPolicygetresponse:
        """Get a k8s_pod_security_policy by name.

        Get k8s_pod_security_policy will get the object from the storage...

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
        path = "/api/config/namespaces/{namespace}/k8s_pod_security_policys/{name}"
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
            return K8sPodSecurityPolicygetresponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("k8s_pod_security_policy", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a k8s_pod_security_policy.

        Delete the specified k8s_pod_security_policy

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/k8s_pod_security_policys/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

