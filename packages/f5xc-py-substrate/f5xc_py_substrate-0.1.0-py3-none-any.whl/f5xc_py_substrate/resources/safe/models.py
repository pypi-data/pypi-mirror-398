"""Pydantic models for safe."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class GetSafeBlockAuditCsvResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS Block Audit CSV API"""

    body: Optional[str] = None


class GetSafeBlockAuditResponse(F5XCBaseModel):
    """Any payload to be return by Safe Block audit API"""

    body: Optional[str] = None


class GetSafeBlockDetailsResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS block details API"""

    body: Optional[str] = None


class GetSafeBlockTableCsvResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS Block Table CSV API"""

    body: Optional[str] = None


class GetSafeBlockTableResponse(F5XCBaseModel):
    """Any payload to be return by Safe Block list table API"""

    body: Optional[str] = None


class GetSafeGeneralResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class GetSafeSummaryResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS Summary API"""

    body: Optional[str] = None


class GetSafeTransactionDetailsResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS Transaction Details API"""

    body: Optional[str] = None


class PostFeedbackRequest(F5XCBaseModel):
    comment: Optional[str] = None
    feedback: Optional[str] = None
    namespace: Optional[str] = None
    transaction_id: Optional[str] = None
    version: Optional[str] = None


class PostFeedbackResponse(F5XCBaseModel):
    body: Optional[str] = None


class PostGeneralFeedbackRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe SAS Transactions CSV API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostGeneralFeedbackResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS Transaction Details API"""

    body: Optional[str] = None


class PostSafeBlockFeedbackRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Block Feedback Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeBlockFeedbackResponse(F5XCBaseModel):
    """Any payload to be return by Post API"""

    body: Optional[str] = None


class PostSafeBlockRuleRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Block Rule Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeBlockRuleResponse(F5XCBaseModel):
    """Any payload to be return by Post API"""

    body: Optional[str] = None


class PostSafeEpRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Ep Post API"""

    body: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeEpResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeOverviewRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Dashboard Transaction Breakdown Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeOverviewResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeProvisionRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Provision Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeProvisionResponse(F5XCBaseModel):
    """Any payload to be return by Post API"""

    body: Optional[str] = None


class PostSafeTransactionDetailsRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Transactions Details Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionDetailsResponse(F5XCBaseModel):
    """Any payload to be return by Post API"""

    body: Optional[str] = None


class PostSafeTransactionDeviceHistoryRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Transactions Device Hisotry Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionDeviceHistoryResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeTransactionLocationsRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Transactions Location Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionLocationsResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeTransactionRelatedSessionsRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Transactions Related Sesions Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionRelatedSessionsResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeTransactionTimelineRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Transactions Timeline Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionTimelineResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeTransactionsCsvRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe SAS Transactions CSV API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionsCsvResponse(F5XCBaseModel):
    """Any payload to be return by Safe SAS Transactions CSV API"""

    body: Optional[str] = None


class PostSafeTransactionsOverTimeRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe Dashboard Transaction Over Time Post API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionsOverTimeResponse(F5XCBaseModel):
    """Any payload to be return by Get API"""

    body: Optional[str] = None


class PostSafeTransactionsRequest(F5XCBaseModel):
    """Any payload to be passed on the Safe SAS Transactions API"""

    body: Optional[str] = None
    namespace: Optional[str] = None
    version: Optional[str] = None


class PostSafeTransactionsResponse(F5XCBaseModel):
    """Any payload to be return by the Safe SAS Transactions API"""

    body: Optional[str] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


# Convenience aliases
