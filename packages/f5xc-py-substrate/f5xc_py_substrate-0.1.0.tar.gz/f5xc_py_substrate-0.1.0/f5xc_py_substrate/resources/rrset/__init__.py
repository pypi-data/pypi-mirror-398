"""Rrset resource exports."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources.rrset.models import *
    from f5xc_py_substrate.resources.rrset.resource import RrsetResource

# Cache for lazy-loaded modules
_models_module = None


def __getattr__(name: str):
    """Lazy load exports."""
    global _models_module

    if name == "RrsetResource":
        from f5xc_py_substrate.resources.rrset.resource import RrsetResource
        return RrsetResource

    # Load models module once and cache it
    if _models_module is None:
        _models_module = importlib.import_module(
            "f5xc_py_substrate.resources.rrset.models"
        )

    # Try to get attribute from models
    try:
        return getattr(_models_module, name)
    except AttributeError:
        pass

    raise AttributeError(f"module 'f5xc_py_substrate.resources.rrset' has no attribute '{name}'")


__all__ = [
    "RrsetResource",
    "AFSDBRecordValue",
    "CERTRecordValue",
    "CERTResourceRecord",
    "CertificationAuthorityAuthorization",
    "DNSAAAAResourceRecord",
    "DNSAFSDBRecord",
    "DNSAResourceRecord",
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
    "DNSTXTResourceRecord",
    "SHA1Fingerprint",
    "SHA256Fingerprint",
    "SSHFPRecordValue",
    "SSHFPResourceRecord",
    "TLSARecordValue",
    "TLSAResourceRecord",
    "RRSet",
    "CreateRequest",
    "ReplaceRequest",
    "Response",
    "Spec",
]
