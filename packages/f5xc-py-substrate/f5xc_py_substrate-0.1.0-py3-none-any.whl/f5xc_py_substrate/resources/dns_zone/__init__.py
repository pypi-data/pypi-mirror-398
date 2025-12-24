"""DnsZone resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.dns_zone.models import *
    from f5xc_py_substrate.resources.dns_zone.resource import DnsZoneResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "DnsZoneResource":
        from f5xc_py_substrate.resources.dns_zone.resource import DnsZoneResource
        return DnsZoneResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.dns_zone.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.dns_zone' has no attribute '{name}'")


__all__ = [
    "DnsZoneResource",
    "AFSDBRecordValue",
    "CERTRecordValue",
    "CERTResourceRecord",
    "CertificationAuthorityAuthorization",
    "CloneReq",
    "CloneResp",
    "ObjectCreateMetaType",
    "DNSAResourceRecord",
    "DNSAAAAResourceRecord",
    "DNSAFSDBRecord",
    "DNSAliasResourceRecord",
    "DNSCAAResourceRecord",
    "SHA1Digest",
    "SHA256Digest",
    "SHA384Digest",
    "DSRecordValue",
    "DNSCDSRecord",
    "DNSCNAMEResourceRecord",
    "DNSDSRecord",
    "DNSEUI48ResourceRecord",
    "DNSEUI64ResourceRecord",
    "ObjectRefType",
    "DNSLBResourceRecord",
    "LOCValue",
    "DNSLOCResourceRecord",
    "MailExchanger",
    "DNSMXResourceRecord",
    "NAPTRValue",
    "DNSNAPTRResourceRecord",
    "DNSNSResourceRecord",
    "DNSPTRResourceRecord",
    "SRVService",
    "DNSSRVResourceRecord",
    "SHA1Fingerprint",
    "SHA256Fingerprint",
    "SSHFPRecordValue",
    "SSHFPResourceRecord",
    "TLSARecordValue",
    "TLSAResourceRecord",
    "DNSTXTResourceRecord",
    "RRSet",
    "Empty",
    "DNSSECModeEnable",
    "DNSSECMode",
    "MessageMetaType",
    "RRSetGroup",
    "SOARecordParameterConfig",
    "PrimaryDNSCreateSpecType",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "SecondaryDNSCreateSpecType",
    "CreateSpecType",
    "CreateRequest",
    "ObjectGetMetaType",
    "PrimaryDNSGetSpecType",
    "SecondaryDNSGetSpecType",
    "GetSpecType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "CreateResponse",
    "DSRecord",
    "DNSSECStatus",
    "DNSZoneStatus",
    "DeleteRequest",
    "MetricsRequest",
    "TrendValue",
    "MetricValue",
    "MetricsData",
    "MetricsResponse",
    "RequestLogRequest",
    "RequestLogsResponseData",
    "RequestLogResponse",
    "ExportZoneFileResponse",
    "F5CSDNSZoneConfiguration",
    "GetLocalZoneFileResponse",
    "GetRemoteZoneFileResponse",
    "ObjectRefType",
    "ObjectReplaceMetaType",
    "ReplaceSpecType",
    "ReplaceRequest",
    "ConditionType",
    "StatusMetaType",
    "StatusObject",
    "GetResponse",
    "TSIGConfiguration",
    "ImportAXFRRequest",
    "ImportAXFRResponse",
    "ImportBINDCreateRequest",
    "InvalidZone",
    "ValidZone",
    "ImportBINDResponse",
    "ImportBINDValidateRequest",
    "ImportF5CSZoneRequest",
    "ImportF5CSZoneResponse",
    "ProtobufAny",
    "ErrorType",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "Spec",
]
