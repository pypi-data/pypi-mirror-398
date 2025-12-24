"""Pydantic models for tpm_provision."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class DeviceInfo(F5XCBaseModel):
    """DeviceInfo defines device parameters like Serial-Number to include in..."""

    name: Optional[str] = None
    serial: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None


class PreauthRequest(F5XCBaseModel):
    """PreauthRequest defines parameters required for pre-flight auth checks..."""

    api_key: Optional[str] = None
    device: Optional[DeviceInfo] = None


class PreauthResponse(F5XCBaseModel):
    """PreauthResponse defines the preauthorization response"""

    status: Optional[Literal['PREAUTH_RSP_SUCCESS', 'PREAUTH_RSP_INVALID_API_KEY', 'PREAUTH_RSP_INVALID_DEVICE_INFO']] = None


class ProvisionRequest(F5XCBaseModel):
    """ProvisionReq defines parameters required for TPM Provisioning Request API."""

    ak_pub_key: Optional[str] = None
    api_key: Optional[str] = None
    csr: Optional[str] = None
    device: Optional[DeviceInfo] = None
    ek_cert: Optional[str] = None
    ek_pub_key: Optional[str] = None


class ProvisionResponse(F5XCBaseModel):
    credential_bundle: Optional[str] = None
    encrypted_ak_cert: Optional[str] = None
    nonce: Optional[str] = None


# Convenience aliases
