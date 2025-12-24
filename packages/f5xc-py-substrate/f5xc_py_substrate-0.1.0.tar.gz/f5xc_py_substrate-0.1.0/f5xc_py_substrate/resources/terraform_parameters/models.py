"""Pydantic models for terraform_parameters."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class StatusMetaType(F5XCBaseModel):
    """StatusMetaType is metadata that all status must have."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    publish: Optional[Literal['STATUS_DO_NOT_PUBLISH', 'STATUS_PUBLISH']] = None
    status_id: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class ApplyStatus(F5XCBaseModel):
    apply_state: Optional[Literal['APPLIED', 'APPLY_ERRORED', 'APPLY_INIT_ERRORED', 'APPLYING', 'APPLY_PLANNING', 'APPLY_PLAN_ERRORED', 'APPLY_QUEUED']] = None
    container_version: Optional[str] = None
    destroy_state: Optional[Literal['DESTROYED', 'DESTROY_ERRORED', 'DESTROYING', 'DESTROY_QUEUED']] = None
    error_output: Optional[str] = None
    infra_state: Optional[Literal['PROVISIONED', 'TIMED_OUT', 'ERRORED', 'PROVISIONING']] = None
    modification_timestamp: Optional[str] = None
    suggested_action: Optional[str] = None
    tf_output: Optional[str] = None
    tf_stdout: Optional[str] = None


class ForceDeleteRequest(F5XCBaseModel):
    """Force delete view request"""

    namespace: Optional[str] = None
    view_kind: Optional[str] = None
    view_name: Optional[str] = None


class ForceDeleteResponse(F5XCBaseModel):
    """Force delete view response"""

    pass


class GlobalSpecType(F5XCBaseModel):
    """Shape of the view terraform parameters specification"""

    container_version: Optional[str] = None
    creds: Optional[list[ObjectRefType]] = None
    tf_objects: Optional[list[ProtobufAny]] = None


class GetResponse(F5XCBaseModel):
    """Response for Get API"""

    terraform_parameters: Optional[GlobalSpecType] = None


class PlanStatus(F5XCBaseModel):
    error_output: Optional[str] = None
    infra_state: Optional[Literal['PROVISIONED', 'TIMED_OUT', 'ERRORED', 'PROVISIONING']] = None
    modification_timestamp: Optional[str] = None
    plan_state: Optional[Literal['PLANNING', 'PLAN_ERRORED', 'NO_CHANGES', 'HAS_CHANGES', 'DISCARDED', 'PLAN_INIT_ERRORED', 'PLAN_QUEUED']] = None
    suggested_action: Optional[str] = None
    tf_plan_output: Optional[str] = None


class StatusObject(F5XCBaseModel):
    """view terraform parameters status object"""

    apply_status: Optional[ApplyStatus] = None
    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    plan_status: Optional[PlanStatus] = None


class GetStatusResponse(F5XCBaseModel):
    """Response for GetStatus API"""

    status: Optional[StatusObject] = None


class RunRequest(F5XCBaseModel):
    """perform terraform actions for a given view. Supported actions are apply and plan."""

    action: Optional[Literal['APPLY', 'PLAN', 'DESTROY']] = None
    namespace: Optional[str] = None
    view_kind: Optional[str] = None
    view_name: Optional[str] = None


class RunResponse(F5XCBaseModel):
    """Response for Run API"""

    pass


# Convenience aliases
Spec = GlobalSpecType
