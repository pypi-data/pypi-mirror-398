"""VirtualHost resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.virtual_host.models import *
    from f5xc_py_substrate.resources.virtual_host.resource import VirtualHostResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "VirtualHostResource":
        from f5xc_py_substrate.resources.virtual_host.resource import VirtualHostResource
        return VirtualHostResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.virtual_host.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.virtual_host' has no attribute '{name}'")


__all__ = [
    "VirtualHostResource",
    "ProtobufAny",
    "HttpBody",
    "APIEPDynExample",
    "AuthenticationTypeLocPair",
    "PDFSpec",
    "PDFStat",
    "APIEPPDFInfo",
    "RiskScore",
    "APIEPInfo",
    "Authentication",
    "SchemaStruct",
    "RequestSchema",
    "DiscoveredSchema",
    "SensitiveData",
    "BlindfoldSecretInfoType",
    "ClearSecretInfoType",
    "SecretType",
    "HMACKeyPair",
    "KMSKeyRefType",
    "CookieParams",
    "Empty",
    "HashAlgorithms",
    "TlsCertificateType",
    "ObjectRefType",
    "TrustedCAList",
    "TlsValidationParamsType",
    "TlsParamsType",
    "DownstreamTlsParamsType",
    "AppFirewallRefType",
    "BufferConfigType",
    "CertificateParamsType",
    "ConditionType",
    "CookieValueOption",
    "CorsPolicy",
    "DomainNameList",
    "CsrfPolicy",
    "ErrorType",
    "HeaderManipulationOptionType",
    "HeaderTransformationType",
    "InitializerType",
    "StatusType",
    "InitializersType",
    "ObjectCreateMetaType",
    "ObjectGetMetaType",
    "ObjectReplaceMetaType",
    "RetryBackOff",
    "RetryPolicyType",
    "SetCookieValueOption",
    "StatusMetaType",
    "ViewRefType",
    "SystemObjectGetMetaType",
    "TLSCoalescingOptions",
    "WafType",
    "ObjectRefType",
    "APIEndpoint",
    "AuthenticationDetails",
    "CaptchaChallengeType",
    "CompressionType",
    "DynamicReverseProxyType",
    "Http1ProtocolOptions",
    "HttpProtocolOptions",
    "JavascriptChallengeType",
    "SlowDDoSMitigation",
    "CreateSpecType",
    "DNSRecord",
    "AutoCertInfoType",
    "CdnServiceType",
    "DnsInfo",
    "GetSpecType",
    "ReplaceSpecType",
    "GlobalSpecType",
    "JiraIssueType",
    "JiraProject",
    "JiraIssueStatusCategory",
    "JiraIssueStatus",
    "JiraIssueFields",
    "JiraIssue",
    "ApiOperation",
    "ApiEndpointWithSchema",
    "APIEPActivityMetrics",
    "APIEPSourceOpenApiSchemaRsp",
    "APIEPSummaryFilter",
    "APIEndpointLearntSchemaRsp",
    "APIEndpointPDFRsp",
    "APIEndpointReq",
    "APIEndpointRsp",
    "APIEndpointsRsp",
    "ApiEndpointsStatsRsp",
    "AssignAPIDefinitionReq",
    "AssignAPIDefinitionResp",
    "CreateJiraIssueRequest",
    "CreateRequest",
    "CreateResponse",
    "CreateTicketRequest",
    "CreateTicketResponse",
    "DeleteRequest",
    "GetAPICallSummaryReq",
    "RequestCountPerResponseClass",
    "GetAPICallSummaryRsp",
    "GetAPIEndpointsSchemaUpdatesReq",
    "GetAPIEndpointsSchemaUpdatesResp",
    "GetDnsInfoResponse",
    "ReplaceRequest",
    "VerStatusType",
    "StatusObject",
    "GetResponse",
    "GetTopAPIEndpointsReq",
    "GetTopAPIEndpointsRsp",
    "GetTopSensitiveDataReq",
    "SensitiveDataCount",
    "GetTopSensitiveDataRsp",
    "GetVulnerabilitiesReq",
    "VulnEvidenceSample",
    "VulnEvidence",
    "VulnRisk",
    "TicketDetails",
    "Vulnerability",
    "GetVulnerabilitiesRsp",
    "ListResponseItem",
    "ListResponse",
    "ReplaceResponse",
    "UnlinkTicketsRequest",
    "UnlinkTicketsResponse",
    "UnmergeAPIEPSourceOpenApiSchemaReq",
    "UpdateAPIEndpointsSchemasReq",
    "UpdateAPIEndpointsSchemasResp",
    "UpdateVulnerabilitiesStateReq",
    "UpdateVulnerabilitiesStateRsp",
    "Spec",
]
