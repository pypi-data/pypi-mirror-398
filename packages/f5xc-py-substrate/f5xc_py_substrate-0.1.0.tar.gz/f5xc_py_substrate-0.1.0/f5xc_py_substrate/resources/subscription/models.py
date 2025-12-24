"""Pydantic models for subscription."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class SubscribeRequest(F5XCBaseModel):
    """Request to subscribe to one of addon services"""

    f5xc_appstack_standard: Optional[Any] = None
    f5xc_big_ip_irule_standard: Optional[Any] = None
    f5xc_bigip_utilities_standard: Optional[Any] = None
    f5xc_content_delivery_network_advanced: Optional[Any] = None
    f5xc_content_delivery_network_standard: Optional[Any] = None
    f5xc_delegated_access_standard: Optional[Any] = None
    f5xc_securemesh_advanced: Optional[Any] = None
    f5xc_securemesh_standard: Optional[Any] = None
    f5xc_site_management_standard: Optional[Any] = None
    f5xc_synthetic_monitoring_standard: Optional[Any] = None
    f5xc_waap_advanced: Optional[Any] = None
    f5xc_waap_standard: Optional[Any] = None
    f5xc_web_app_scanning_standard: Optional[Any] = None


class SubscribeResponse(F5XCBaseModel):
    """Response for subscribe"""

    pass


class UnsubscribeRequest(F5XCBaseModel):
    """Request to unsubscribe to one of addon services"""

    f5xc_appstack_standard: Optional[Any] = None
    f5xc_big_ip_irule_standard: Optional[Any] = None
    f5xc_bigip_utilities_standard: Optional[Any] = None
    f5xc_content_delivery_network_advanced: Optional[Any] = None
    f5xc_content_delivery_network_standard: Optional[Any] = None
    f5xc_delegated_access_standard: Optional[Any] = None
    f5xc_securemesh_advanced: Optional[Any] = None
    f5xc_securemesh_standard: Optional[Any] = None
    f5xc_site_management_standard: Optional[Any] = None
    f5xc_synthetic_monitoring_standard: Optional[Any] = None
    f5xc_waap_advanced: Optional[Any] = None
    f5xc_waap_standard: Optional[Any] = None
    f5xc_web_app_scanning_standard: Optional[Any] = None


class UnsubscribeResponse(F5XCBaseModel):
    """Response for unsubscribe"""

    pass


# Convenience aliases
