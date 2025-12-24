"""Rrset resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.rrset.models import (
    AFSDBRecordValue,
    CERTRecordValue,
    CERTResourceRecord,
    CertificationAuthorityAuthorization,
    DNSAAAAResourceRecord,
    DNSAFSDBRecord,
    DNSAResourceRecord,
    DNSAliasResourceRecord,
    DNSCAAResourceRecord,
    SHA1Digest,
    SHA256Digest,
    SHA384Digest,
    DSRecordValue,
    DNSCDSRecord,
    DNSCNAMEResourceRecord,
    DNSDSRecord,
    DNSEUI48ResourceRecord,
    DNSEUI64ResourceRecord,
    ObjectRefType,
    DNSLBResourceRecord,
    LOCValue,
    DNSLOCResourceRecord,
    MailExchanger,
    DNSMXResourceRecord,
    NAPTRValue,
    DNSNAPTRResourceRecord,
    DNSNSResourceRecord,
    DNSPTRResourceRecord,
    SRVService,
    DNSSRVResourceRecord,
    DNSTXTResourceRecord,
    SHA1Fingerprint,
    SHA256Fingerprint,
    SSHFPRecordValue,
    SSHFPResourceRecord,
    TLSARecordValue,
    TLSAResourceRecord,
    RRSet,
    CreateRequest,
    ReplaceRequest,
    Response,
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


class RrsetResource:
    """API methods for rrset.

    x-required
APIs to create, update or delete individual records of a...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.rrset.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: AFSDBRecordValue | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> Response:
        """Create a new rrset.

        

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
        path = "/api/config/dns/namespaces/system/dns_zones/{dns_zone_name}/rrsets/{group_name}"
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
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("rrset", "create", e, response) from e

    def get(
        self,
        dns_zone_name: str,
        group_name: str,
        record_name: str,
        type: str,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> Response:
        """Get a rrset by name.

        

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
        path = "/api/config/dns/namespaces/system/dns_zones/{dns_zone_name}/rrsets/{group_name}/{record_name}/{type}"
        path = path.replace("{dns_zone_name}", dns_zone_name)
        path = path.replace("{group_name}", group_name)
        path = path.replace("{record_name}", record_name)
        path = path.replace("{type}", type)

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
            return Response(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("rrset", "get", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: AFSDBRecordValue | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> Response:
        """Replace an existing rrset.

        

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
        path = "/api/config/dns/namespaces/system/dns_zones/{dns_zone_name}/rrsets/{group_name}/{record_name}/{type}"
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
            return Response(**response)
        except ValidationError as e:
            raise F5XCValidationError("rrset", "replace", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a rrset.

        

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/dns/namespaces/system/dns_zones/{dns_zone_name}/rrsets/{group_name}/{record_name}/{type}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

