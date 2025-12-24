"""Pydantic models for safeap."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetCurrentFraudRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Current Fraud Request API..."""

    app_key: Optional[str] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class GetCurrentFraudResponse(F5XCBaseModel):
    """Current Fraud response data from CubeJS"""

    response: Optional[str] = None


class GetSafeCubeJSRequest(F5XCBaseModel):
    """Any payload to be passed from the SAFE Dashboard to the Safe CubeJS API"""

    app_key: Optional[str] = None
    query: Optional[str] = None


class GetSafeCubeJSResponse(F5XCBaseModel):
    """Any payload to be return by Safe CubeJS API after processing the request"""

    response: Optional[str] = None


class GetTopRiskyAccountsRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Top 5 Risky Accounts Fraud Request..."""

    app_key: Optional[str] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class GetTopRiskyAccountsResponse(F5XCBaseModel):
    """Get Top 5 Risky Accounts data from CubeJS"""

    response: Optional[str] = None


class GetTopRiskyDevicesRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Top 5 Risky Devices Request API..."""

    app_key: Optional[str] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class GetTopRiskyDevicesResponse(F5XCBaseModel):
    """Get Top 5 Risky Devices data from CubeJS"""

    response: Optional[str] = None


class GetTopRiskyIpAddressesRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Top 5 Risky Ip Addresses Request API..."""

    app_key: Optional[str] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class GetTopRiskyIpAddressesResponse(F5XCBaseModel):
    """Get Top 5 Risky Ip Addresses data from CubeJS"""

    response: Optional[str] = None


class GetTopRiskyReasonsRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Top 5 Risky Reasons Request API..."""

    app_key: Optional[str] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class GetTopRiskyReasonsResponse(F5XCBaseModel):
    """Get Top 5 Risky Reasons data from CubeJS"""

    response: Optional[str] = None


class GetTransactionRequest(F5XCBaseModel):
    """Any payload to be passed on the Get Transaction Request API..."""

    app_key: Optional[str] = None
    end_time: Optional[str] = None
    start_time: Optional[str] = None


class GetTransactionResponse(F5XCBaseModel):
    """Transaction response data from CubeJS"""

    response: Optional[str] = None


class HealthResponse(F5XCBaseModel):
    """HealthResponse"""

    message: Optional[str] = None


class SubscribeRequest(F5XCBaseModel):
    """Any payload to be passed on the Subscribe API"""

    pass


class SubscribeResponse(F5XCBaseModel):
    """Any payload to be returned by Subscribe API"""

    pass


class UnsubscribeRequest(F5XCBaseModel):
    """Any payload to be passed on the Unsubscribe API"""

    pass


class UnsubscribeResponse(F5XCBaseModel):
    """Any payload to be returned by Unsubscribe API"""

    pass


# Convenience aliases
