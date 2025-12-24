"""DnsZone resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.dns_zone.models import (
    DnsZoneListItem,
    AFSDBRecordValue,
    CERTRecordValue,
    CERTResourceRecord,
    CertificationAuthorityAuthorization,
    CloneReq,
    CloneResp,
    ObjectCreateMetaType,
    DNSAResourceRecord,
    DNSAAAAResourceRecord,
    DNSAFSDBRecord,
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
    SHA1Fingerprint,
    SHA256Fingerprint,
    SSHFPRecordValue,
    SSHFPResourceRecord,
    TLSARecordValue,
    TLSAResourceRecord,
    DNSTXTResourceRecord,
    RRSet,
    Empty,
    DNSSECModeEnable,
    DNSSECMode,
    MessageMetaType,
    RRSetGroup,
    SOARecordParameterConfig,
    PrimaryDNSCreateSpecType,
    BlindfoldSecretInfoType,
    ClearSecretInfoType,
    SecretType,
    SecondaryDNSCreateSpecType,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    PrimaryDNSGetSpecType,
    SecondaryDNSGetSpecType,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    DSRecord,
    DNSSECStatus,
    DNSZoneStatus,
    DeleteRequest,
    MetricsRequest,
    TrendValue,
    MetricValue,
    MetricsData,
    MetricsResponse,
    RequestLogRequest,
    RequestLogsResponseData,
    RequestLogResponse,
    ExportZoneFileResponse,
    F5CSDNSZoneConfiguration,
    GetLocalZoneFileResponse,
    GetRemoteZoneFileResponse,
    ObjectRefType,
    ObjectReplaceMetaType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    TSIGConfiguration,
    ImportAXFRRequest,
    ImportAXFRResponse,
    ImportBINDCreateRequest,
    InvalidZone,
    ValidZone,
    ImportBINDResponse,
    ImportBINDValidateRequest,
    ImportF5CSZoneRequest,
    ImportF5CSZoneResponse,
    ProtobufAny,
    ErrorType,
    ListResponseItem,
    ListResponse,
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


class DnsZoneResource:
    """API methods for dns_zone.

    DNS Zone object is used for configuring Primary and Secondary DNS...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.dns_zone.CreateSpecType(...)
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
        spec: AFSDBRecordValue | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new dns_zone.

        Create DNS Zone in a given namespace. If one already exist it will...

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
        path = "/api/config/dns/namespaces/{metadata.namespace}/dns_zones"
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
            raise F5XCValidationError("dns_zone", "create", e, response) from e

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
    ) -> ReplaceResponse:
        """Replace an existing dns_zone.

        Replace DNS Zone in a given namespace.

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
        path = "/api/config/dns/namespaces/{metadata.namespace}/dns_zones/{metadata.name}"
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
            raise F5XCValidationError("dns_zone", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[DnsZoneListItem]:
        """List dns_zone resources in a namespace.

        List the set of dns_zone in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/dns/namespaces/{namespace}/dns_zones"
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
            return [DnsZoneListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "list", e, response) from e

    def dns_zone_metrics(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> MetricsResponse:
        """Dns Zone Metrics for dns_zone.

        Request to get dns zone metrics data
        """
        path = "/api/data/namespaces/{namespace}/dns_zones/metrics"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return MetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "dns_zone_metrics", e, response) from e

    def dns_zone_request_logs(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> RequestLogResponse:
        """Dns Zone Request Logs for dns_zone.

        Retrieve Dns Zone Request Logs
        """
        path = "/api/data/namespaces/{namespace}/dns_zones/request_logs"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RequestLogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "dns_zone_request_logs", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a dns_zone by name.

        Get DNS Zone details.

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
        path = "/api/config/dns/namespaces/{namespace}/dns_zones/{name}"
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
            raise F5XCValidationError("dns_zone", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a dns_zone.

        Delete the specified dns_zone

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/dns/namespaces/{namespace}/dns_zones/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def clone_from_dns_domain(
        self,
        body: dict[str, Any] | None = None,
    ) -> CloneResp:
        """Clone From Dns Domain for dns_zone.

        cloning dns domain to DNSZone.
        """
        path = "/api/config/dns/namespaces/system/dns_zone/clone_from_dns_domain"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CloneResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "clone_from_dns_domain", e, response) from e

    def import_f5_cs_zone(
        self,
        body: dict[str, Any] | None = None,
    ) -> ImportF5CSZoneResponse:
        """Import F5 Cs Zone for dns_zone.

        Import F5 Cloud Services DNS Zone
        """
        path = "/api/config/dns/namespaces/system/dns_zone/import"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ImportF5CSZoneResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "import_f5_cs_zone", e, response) from e

    def import_axfr(
        self,
        body: dict[str, Any] | None = None,
    ) -> ImportAXFRResponse:
        """Import Axfr for dns_zone.

        Import DNS Zone via AXFR
        """
        path = "/api/config/dns/namespaces/system/dns_zone/import_axfr"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ImportAXFRResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "import_axfr", e, response) from e

    def import_bind_create(
        self,
        body: dict[str, Any] | None = None,
    ) -> ImportBINDResponse:
        """Import Bind Create for dns_zone.

        Import BIND Files to Create DNS Zones
        """
        path = "/api/config/dns/namespaces/system/dns_zone/import_bind_create"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ImportBINDResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "import_bind_create", e, response) from e

    def import_bind_validate(
        self,
        body: dict[str, Any] | None = None,
    ) -> ImportBINDResponse:
        """Import Bind Validate for dns_zone.

        Validate BIND Files for Import
        """
        path = "/api/config/dns/namespaces/system/dns_zone/import_bind_validate"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ImportBINDResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "import_bind_validate", e, response) from e

    def get_local_zone_file(
        self,
        namespace: str,
        dns_zone_name: str,
    ) -> GetLocalZoneFileResponse:
        """Get Local Zone File for dns_zone.

        get local zone file from secondary dns
        """
        path = "/api/config/dns/namespaces/{namespace}/dns_zone/{dns_zone_name}/local_zone_file"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{dns_zone_name}", dns_zone_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetLocalZoneFileResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "get_local_zone_file", e, response) from e

    def get_remote_zone_file(
        self,
        namespace: str,
        dns_zone_name: str,
    ) -> GetRemoteZoneFileResponse:
        """Get Remote Zone File for dns_zone.

        get remote zone file from primary dns
        """
        path = "/api/config/dns/namespaces/{namespace}/dns_zone/{dns_zone_name}/remote_zone_file"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{dns_zone_name}", dns_zone_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetRemoteZoneFileResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "get_remote_zone_file", e, response) from e

    def export_zone_file(
        self,
        namespace: str,
        dns_zone_name: str,
    ) -> ExportZoneFileResponse:
        """Export Zone File for dns_zone.

        Export Zone File
        """
        path = "/api/config/dns/namespaces/{namespace}/dns_zone/{dns_zone_name}/zone_file/export"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{dns_zone_name}", dns_zone_name)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ExportZoneFileResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("dns_zone", "export_zone_file", e, response) from e

