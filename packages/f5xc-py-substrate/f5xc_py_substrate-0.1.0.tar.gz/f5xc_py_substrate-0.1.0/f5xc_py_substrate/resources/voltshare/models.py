"""Pydantic models for voltshare."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class VoltShareAccessId(F5XCBaseModel):
    """VoltShareAccessId uniquely identifies an entry in the response...."""

    country: Optional[str] = None
    operation: Optional[str] = None
    result: Optional[str] = None
    user_tenant: Optional[str] = None


class VoltShareMetricValue(F5XCBaseModel):
    """Value returned for a VoltShare Access Metrics query"""

    timestamp: Optional[float] = None
    value: Optional[str] = None


class VoltShareAccessCounter(F5XCBaseModel):
    """VoltShareAccessCounter contains the access count for each unique..."""

    id_: Optional[VoltShareAccessId] = Field(default=None, alias="id")
    metric: Optional[list[VoltShareMetricValue]] = None


class VoltShareMetricLabelFilter(F5XCBaseModel):
    """VoltShare Access metric is tagged with labels mentioned in MetricLabel...."""

    label: Optional[Literal['OPERATION', 'RESULT', 'USER_TENANT', 'COUNTRY']] = None
    op: Optional[Literal['EQ', 'NEQ']] = None
    value: Optional[str] = None


class AuditLogAggregationRequest(F5XCBaseModel):
    """Request to get only aggregation data for audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    start_time: Optional[str] = None


class AuditLogAggregationResponse(F5XCBaseModel):
    """Response message for AuditLogAggregationRequest"""

    aggs: Optional[dict[str, Any]] = None
    total_hits: Optional[str] = None


class AuditLogRequest(F5XCBaseModel):
    """Request to fetch voltshare audit logs"""

    aggs: Optional[dict[str, Any]] = None
    end_time: Optional[str] = None
    limit: Optional[int] = None
    namespace: Optional[str] = None
    query: Optional[str] = None
    scroll: Optional[bool] = None
    sort: Optional[Literal['DESCENDING', 'ASCENDING']] = None
    start_time: Optional[str] = None


class AuditLogResponse(F5XCBaseModel):
    """Response message for AuditLogRequest/LogScrollRequest"""

    aggs: Optional[dict[str, Any]] = None
    logs: Optional[list[str]] = None
    scroll_id: Optional[str] = None
    total_hits: Optional[str] = None


class AuditLogScrollRequest(F5XCBaseModel):
    """Scroll request is used to fetch large number of log messages in multiple..."""

    namespace: Optional[str] = None
    scroll_id: Optional[str] = None


class UserRecordType(F5XCBaseModel):
    """UserRecordType contains information about a user"""

    email: Optional[str] = None
    tenant: Optional[str] = None


class PolicyType(F5XCBaseModel):
    """Policy contains user defined policy. It contains list of allowed users..."""

    allowed_users: Optional[list[UserRecordType]] = None
    expiration_timestamp: Optional[str] = None


class PolicyInformationType(F5XCBaseModel):
    """PolicyInformation contains user defined policy and metadata added by the..."""

    author: Optional[UserRecordType] = None
    blindfold_key_version: Optional[int] = None
    creation_time: Optional[str] = None
    policy: Optional[PolicyType] = None
    policy_id: Optional[str] = None
    secret_name: Optional[str] = None


class DecryptSecretRequest(F5XCBaseModel):
    """DecryptSecretRequest contains parameters for DecryptSecret API"""

    blinded_encrypted_key_base64: Optional[str] = None
    policy_document: Optional[PolicyInformationType] = None
    policy_document_hmac_base64: Optional[str] = None


class DecryptSecretResponse(F5XCBaseModel):
    """DecryptSecretResponse contains the response of DecryptSecret API"""

    blinded_key_base64: Optional[str] = None


class ProcessPolicyRequest(F5XCBaseModel):
    """ProcessPolicyRequest contains parameters ProcessPolicyInformation API"""

    policy: Optional[PolicyType] = None
    secret_name: Optional[str] = None


class ProcessPolicyResponse(F5XCBaseModel):
    """Response of the ProcessPolicyInformation API. It contains Processed..."""

    policy_document: Optional[PolicyInformationType] = None
    policy_document_hmac_base64: Optional[str] = None
    public_key: Optional[str] = None


class VoltShareAccessCountRequest(F5XCBaseModel):
    """Request to get number of VoltShare API calls aggregated across multiple..."""

    end_time: Optional[str] = None
    group_by: Optional[list[Literal['OPERATION', 'RESULT', 'USER_TENANT', 'COUNTRY']]] = None
    label_filter: Optional[list[VoltShareMetricLabelFilter]] = None
    namespace: Optional[str] = None
    start_time: Optional[str] = None
    step: Optional[str] = None


class VoltShareAccessCountResponse(F5XCBaseModel):
    """VoltShare access count for each unique combination of group_by labels in..."""

    data: Optional[list[VoltShareAccessCounter]] = None
    step: Optional[str] = None


# Convenience aliases
