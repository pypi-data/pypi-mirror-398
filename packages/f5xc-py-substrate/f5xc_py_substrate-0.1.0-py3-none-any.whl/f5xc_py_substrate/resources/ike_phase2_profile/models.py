"""Pydantic models for ike_phase2_profile."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class IkePhase2ProfileListItem(F5XCBaseModel):
    """List item for ike_phase2_profile resources."""


class IkePhase1Profileinputhours(F5XCBaseModel):
    """Input Hours"""

    duration: Optional[int] = None


class IkePhase1Profileinputminutes(F5XCBaseModel):
    """Set IKE Key Lifetime in minutes"""

    duration: Optional[int] = None


class ObjectCreateMetaType(F5XCBaseModel):
    """ObjectCreateMetaType is metadata that can be specified in Create request..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class IkePhase2Profiledhgroups(F5XCBaseModel):
    """Choose the acceptable Diffie Hellman(DH) Group or Groups that you are..."""

    dh_groups: Optional[list[Literal['DH_GROUP_DEFAULT', 'DH_GROUP_14', 'DH_GROUP_15', 'DH_GROUP_16', 'DH_GROUP_17', 'DH_GROUP_18', 'DH_GROUP_19', 'DH_GROUP_20', 'DH_GROUP_21', 'DH_GROUP_26']]] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class ViewsikePhase2Profilecreatespectype(F5XCBaseModel):
    """Shape of the IKE Phase2 profile specification"""

    authentication_algos: Optional[list[Literal['AUTH_ALG_DEFAULT', 'SHA256_HMAC', 'SHA384_HMAC', 'SHA512_HMAC', 'AUTH_ALG_NONE']]] = None
    dh_group_set: Optional[IkePhase2Profiledhgroups] = None
    disable_pfs: Optional[Any] = None
    encryption_algos: Optional[list[Literal['ENC_ALG_DEFAULT', 'AES128_CBC', 'AES192_CBC', 'AES256_CBC', 'TRIPLE_DES_CBC', 'AES128_GCM', 'AES192_GCM', 'AES256_GCM']]] = None
    ike_keylifetime_hours: Optional[IkePhase1Profileinputhours] = None
    ike_keylifetime_minutes: Optional[IkePhase1Profileinputminutes] = None
    use_default_keylifetime: Optional[Any] = None


class IkePhase2Profilecreaterequest(F5XCBaseModel):
    """This is the input message of the 'Create' RPC"""

    metadata: Optional[ObjectCreateMetaType] = None
    spec: Optional[ViewsikePhase2Profilecreatespectype] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ViewsikePhase2Profilegetspectype(F5XCBaseModel):
    """Shape of the IKE Phase2 Profile  configuration specification"""

    authentication_algos: Optional[list[Literal['AUTH_ALG_DEFAULT', 'SHA256_HMAC', 'SHA384_HMAC', 'SHA512_HMAC', 'AUTH_ALG_NONE']]] = None
    dh_group_set: Optional[IkePhase2Profiledhgroups] = None
    disable_pfs: Optional[Any] = None
    encryption_algos: Optional[list[Literal['ENC_ALG_DEFAULT', 'AES128_CBC', 'AES192_CBC', 'AES256_CBC', 'TRIPLE_DES_CBC', 'AES128_GCM', 'AES192_GCM', 'AES256_GCM']]] = None
    ike_keylifetime_hours: Optional[IkePhase1Profileinputhours] = None
    ike_keylifetime_minutes: Optional[IkePhase1Profileinputminutes] = None
    use_default_keylifetime: Optional[Any] = None


class InitializerType(F5XCBaseModel):
    """Initializer is information about an initializer that has not yet completed."""

    name: Optional[str] = None


class StatusType(F5XCBaseModel):
    """Status is a return value for calls that don't return other objects."""

    code: Optional[int] = None
    reason: Optional[str] = None
    status: Optional[str] = None


class InitializersType(F5XCBaseModel):
    """Initializers tracks the progress of initialization of a configuration object"""

    pending: Optional[list[InitializerType]] = None
    result: Optional[StatusType] = None


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectGetMetaType(F5XCBaseModel):
    """SystemObjectGetMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class IkePhase2Profilecreateresponse(F5XCBaseModel):
    metadata: Optional[ObjectGetMetaType] = None
    spec: Optional[ViewsikePhase2Profilegetspectype] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class IkePhase2Profiledeleterequest(F5XCBaseModel):
    """This is the input message of the 'Delete' RPC."""

    fail_if_referred: Optional[bool] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectReplaceMetaType(F5XCBaseModel):
    """ObjectReplaceMetaType is metadata that can be specified in Replace..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class ViewsikePhase2Profilereplacespectype(F5XCBaseModel):
    """Shape of the IKE Phase2 profile  configuration specification"""

    authentication_algos: Optional[list[Literal['AUTH_ALG_DEFAULT', 'SHA256_HMAC', 'SHA384_HMAC', 'SHA512_HMAC', 'AUTH_ALG_NONE']]] = None
    dh_group_set: Optional[IkePhase2Profiledhgroups] = None
    disable_pfs: Optional[Any] = None
    encryption_algos: Optional[list[Literal['ENC_ALG_DEFAULT', 'AES128_CBC', 'AES192_CBC', 'AES256_CBC', 'TRIPLE_DES_CBC', 'AES128_GCM', 'AES192_GCM', 'AES256_GCM']]] = None
    ike_keylifetime_hours: Optional[IkePhase1Profileinputhours] = None
    ike_keylifetime_minutes: Optional[IkePhase1Profileinputminutes] = None
    use_default_keylifetime: Optional[Any] = None


class IkePhase2Profilereplacerequest(F5XCBaseModel):
    """This is the input message of the 'Replace' RPC"""

    metadata: Optional[ObjectReplaceMetaType] = None
    spec: Optional[ViewsikePhase2Profilereplacespectype] = None


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


class IkePhase2Profilestatusobject(F5XCBaseModel):
    """Most recently observed status of object"""

    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None


class IkePhase2Profilegetresponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    create_form: Optional[IkePhase2Profilecreaterequest] = None
    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    replace_form: Optional[IkePhase2Profilereplacerequest] = None
    spec: Optional[ViewsikePhase2Profilegetspectype] = None
    status: Optional[list[IkePhase2Profilestatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class IkePhase2Profilelistresponseitem(F5XCBaseModel):
    """By default a summary of ike_phase2_profile is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[ViewsikePhase2Profilegetspectype] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    status_set: Optional[list[IkePhase2Profilestatusobject]] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class IkePhase2Profilelistresponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[IkePhase2Profilelistresponseitem]] = None


class IkePhase2Profilereplaceresponse(F5XCBaseModel):
    pass


# Convenience aliases
