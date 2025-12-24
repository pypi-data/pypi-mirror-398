"""Pydantic models for signup."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class Policer(F5XCBaseModel):
    """Policer config for bandwidth restrictions"""

    bandwidth_max_mb: Optional[int] = None


class BlindfoldSecretInfoType(F5XCBaseModel):
    """BlindfoldSecretInfoType specifies information about the Secret managed..."""

    decryption_provider: Optional[str] = None
    location: Optional[str] = None
    store_provider: Optional[str] = None


class CRMInfo(F5XCBaseModel):
    """CRM Information"""

    pass


class ClearSecretInfoType(F5XCBaseModel):
    """ClearSecretInfoType specifies information about the Secret that is not encrypted."""

    provider: Optional[str] = None
    url: Optional[str] = None


class ConditionType(F5XCBaseModel):
    """Conditions are used in the object status to describe the current state..."""

    hostname: Optional[str] = None
    last_update_time: Optional[str] = None
    reason: Optional[str] = None
    service_name: Optional[str] = None
    status: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


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


class ObjectMetaType(F5XCBaseModel):
    """ObjectMetaType is metadata(common attributes) of an object that all..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class SecretType(F5XCBaseModel):
    """SecretType is used in an object to indicate a sensitive/confidential field"""

    blindfold_secret_info: Optional[BlindfoldSecretInfoType] = None
    clear_secret_info: Optional[ClearSecretInfoType] = None


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


class ViewRefType(F5XCBaseModel):
    """ViewRefType represents a reference to a view"""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    uid: Optional[str] = None


class SystemObjectMetaType(F5XCBaseModel):
    """SystemObjectMetaType is metadata generated or populated by the system..."""

    creation_timestamp: Optional[str] = None
    creator_class: Optional[str] = None
    creator_cookie: Optional[str] = None
    creator_id: Optional[str] = None
    deletion_timestamp: Optional[str] = None
    direct_ref_hash: Optional[str] = None
    finalizers: Optional[list[str]] = None
    initializers: Optional[InitializersType] = None
    labels: Optional[dict[str, Any]] = None
    modification_timestamp: Optional[str] = None
    namespace: Optional[list[ObjectRefType]] = None
    object_index: Optional[int] = None
    owner_view: Optional[ViewRefType] = None
    revision: Optional[str] = None
    sre_disable: Optional[bool] = None
    tenant: Optional[str] = None
    trace_info: Optional[str] = None
    uid: Optional[str] = None
    vtrp_id: Optional[str] = None
    vtrp_stale: Optional[bool] = None


class GlobalSpecType(F5XCBaseModel):
    """Instance of one single contact that can be used to communicate with..."""

    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    contact_type: Optional[Literal['MAILING', 'BILLING', 'PAYMENT']] = None
    country: Optional[str] = None
    county: Optional[str] = None
    phone_number: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    """Organisation information"""

    arbor_cid: Optional[str] = None
    as_path_choice_full: Optional[Any] = None
    as_path_choice_none: Optional[Any] = None
    as_path_choice_origin: Optional[Any] = None
    asn: Optional[int] = None
    default_tunnel_bgp_secret: Optional[SecretType] = None
    default_tunnel_bgp_secret_none: Optional[Any] = None
    policer: Optional[Policer] = None
    prefixes: Optional[list[str]] = None
    primary_network_name: Optional[str] = None
    reuse_ips: Optional[Any] = None
    route_advertisement_mgmt_not_specified: Optional[Any] = None
    route_advertisement_mgmt_not_using_f5xc: Optional[Any] = None
    route_advertisement_mgmt_using_f5xc: Optional[Any] = None
    use_dedicated_ips: Optional[Any] = None
    uuid: Optional[str] = None


class GlobalSpecType(F5XCBaseModel):
    contacts: Optional[list[ObjectRefType]] = None
    domain_owner: Optional[bool] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    groups: Optional[list[ObjectRefType]] = None
    idm_type: Optional[Literal['SSO', 'VOLTERRA_MANAGED', 'UNDEFINED']] = None
    last_login_timestamp: Optional[str] = None
    last_name: Optional[str] = None
    locale: Optional[str] = None
    state: Optional[Literal['StateUndefined', 'StateCreating', 'StateCreateFailed', 'StateActive', 'StateDisabled']] = None
    sync_mode: Optional[Literal['SELF', 'SCIM']] = None
    tos_accepted: Optional[str] = None
    tos_accepted_at: Optional[str] = None
    tos_version: Optional[str] = None
    type_: Optional[Literal['USER', 'SERVICE', 'DEBUG']] = Field(default=None, alias="type")


class GlobalSpecType(F5XCBaseModel):
    """desired state of Signup"""

    billing_address: Optional[GlobalSpecType] = None
    billing_provider_account_id: Optional[str] = None
    company: Optional[GlobalSpecType] = None
    company_contact: Optional[GlobalSpecType] = None
    company_name: Optional[str] = None
    contact_number: Optional[str] = None
    crm_details: Optional[Any] = None
    currency: Optional[str] = None
    customer: Optional[GlobalSpecType] = None
    customer_contact: Optional[GlobalSpecType] = None
    domain: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    infraprotect_info: Optional[GlobalSpecType] = None
    last_name: Optional[str] = None
    locale: Optional[str] = None
    payment_provider_token: Optional[str] = None
    support_plan_name: Optional[str] = None
    tax_exempt: Optional[Literal['TAX_UNKNOWN', 'TAX_REGULAR', 'TAX_EXEMPT_UNVERIFIED', 'TAX_EXEMPT_VERIFIED', 'TAX_EXEMPT_VERIFICATION_FAILED', 'TAX_EXEMPT_VERIFICATION_PENDING']] = None
    token: Optional[str] = None
    tos_accepted: Optional[str] = None
    tos_accepted_at: Optional[str] = None
    tos_version: Optional[str] = None
    type_: Optional[Literal['UNKNOWN', 'FREEMIUM', 'ENTERPRISE']] = Field(default=None, alias="type")
    usage_plan_name: Optional[str] = None


class CityItem(F5XCBaseModel):
    """CityItem contains a single element of city list response."""

    additional_info: Optional[dict[str, Any]] = None
    city_name: Optional[str] = None


class CountryItem(F5XCBaseModel):
    """CountryItem contains a single element of country list response."""

    additional_info: Optional[dict[str, Any]] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None


class SpecType(F5XCBaseModel):
    """Shape of the signup specification"""

    gc_spec: Optional[GlobalSpecType] = None


class Object(F5XCBaseModel):
    """signup object"""

    metadata: Optional[ObjectMetaType] = None
    spec: Optional[SpecType] = None
    system_metadata: Optional[SystemObjectMetaType] = None


class StatusObject(F5XCBaseModel):
    """Most recently observed status of signup object"""

    billing_account: Optional[list[ObjectRefType]] = Field(default=None, alias="billingAccount")
    conditions: Optional[list[ConditionType]] = None
    metadata: Optional[StatusMetaType] = None
    object_refs: Optional[list[ObjectRefType]] = None
    tenant: Optional[list[ObjectRefType]] = None
    user: Optional[list[ObjectRefType]] = None


class GetResponse(F5XCBaseModel):
    """Signup object including its status. Use it when you want to see the..."""

    object_: Optional[Object] = Field(default=None, alias="object")
    status: Optional[list[StatusObject]] = None


class ListCitiesResponse(F5XCBaseModel):
    """ListCitiesResponse contains a list of cities (for a country) supported..."""

    cities: Optional[list[CityItem]] = None
    error_code: Optional[Literal['EUNKNOWN', 'ETOKEN_OK', 'ETOKEN_FAILED', 'ETOKEN_NOTFOUND', 'ETOKEN_USED', 'ETOKEN_EXPIRED', 'EUSER_OK', 'EUSER_EXISTS', 'EUSER_FAILED', 'ECONTACT_VALIDATE_OK', 'ECONTACT_EMPTY_COUNTRY', 'ECONTACT_EMPTY_ZIP_CODE', 'ECONTACT_UNKNOWN_COUNTRY', 'ECONTACT_INVALID_ZIP', 'EOK', 'ENO_STATES', 'ENO_CITIES']] = None


class ListCountriesResponse(F5XCBaseModel):
    """ListCountriesResponse contains a list of countries supported by the platform"""

    countries: Optional[list[CountryItem]] = None


class StateItem(F5XCBaseModel):
    """CountryItem contains a single element of country list response."""

    additional_info: Optional[dict[str, Any]] = None
    state_code: Optional[str] = None
    state_name: Optional[str] = None


class ListStatesResponse(F5XCBaseModel):
    """ListStatesResponse contains a list of states supported by the platform"""

    error_code: Optional[Literal['EUNKNOWN', 'ETOKEN_OK', 'ETOKEN_FAILED', 'ETOKEN_NOTFOUND', 'ETOKEN_USED', 'ETOKEN_EXPIRED', 'EUSER_OK', 'EUSER_EXISTS', 'EUSER_FAILED', 'ECONTACT_VALIDATE_OK', 'ECONTACT_EMPTY_COUNTRY', 'ECONTACT_EMPTY_ZIP_CODE', 'ECONTACT_UNKNOWN_COUNTRY', 'ECONTACT_INVALID_ZIP', 'EOK', 'ENO_STATES', 'ENO_CITIES']] = None
    states: Optional[list[StateItem]] = None


class SendPasswordEmailRequest(F5XCBaseModel):
    """SendPasswordEmailRequest is the request format for resetting the..."""

    cname: Optional[str] = None
    email: Optional[str] = None


class SendPasswordEmailResponse(F5XCBaseModel):
    """SendPasswordEmailResponse is an empty response after an email had been sent.."""

    pass


class ValidateContactRequest(F5XCBaseModel):
    """Validate contacts request"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    spec: Optional[GlobalSpecType] = None


class ValidationErrorField(F5XCBaseModel):
    """Contains information on a single validation error"""

    error_field: Optional[str] = None
    error_message: Optional[str] = None


class ValidateContactResponse(F5XCBaseModel):
    """ValidateRegistrationResponse is the response that indicates if the..."""

    err: Optional[Literal['EUNKNOWN', 'ETOKEN_OK', 'ETOKEN_FAILED', 'ETOKEN_NOTFOUND', 'ETOKEN_USED', 'ETOKEN_EXPIRED', 'EUSER_OK', 'EUSER_EXISTS', 'EUSER_FAILED', 'ECONTACT_VALIDATE_OK', 'ECONTACT_EMPTY_COUNTRY', 'ECONTACT_EMPTY_ZIP_CODE', 'ECONTACT_UNKNOWN_COUNTRY', 'ECONTACT_INVALID_ZIP', 'EOK', 'ENO_STATES', 'ENO_CITIES']] = None
    is_valid: Optional[bool] = None
    validation_errors: Optional[list[ValidationErrorField]] = None


class ValidateRegistrationRequest(F5XCBaseModel):
    """ValidateRegistrationRequest is the request body parameeters required to..."""

    email: Optional[str] = None
    tenant_type: Optional[Literal['UNKNOWN', 'FREEMIUM', 'ENTERPRISE']] = None
    token: Optional[str] = None


class ValidateRegistrationResponse(F5XCBaseModel):
    """ValidateRegistrationResponse is the response that indicates if the..."""

    err: Optional[Literal['EUNKNOWN', 'ETOKEN_OK', 'ETOKEN_FAILED', 'ETOKEN_NOTFOUND', 'ETOKEN_USED', 'ETOKEN_EXPIRED', 'EUSER_OK', 'EUSER_EXISTS', 'EUSER_FAILED', 'ECONTACT_VALIDATE_OK', 'ECONTACT_EMPTY_COUNTRY', 'ECONTACT_EMPTY_ZIP_CODE', 'ECONTACT_UNKNOWN_COUNTRY', 'ECONTACT_INVALID_ZIP', 'EOK', 'ENO_STATES', 'ENO_CITIES']] = None
    valid_registration: Optional[bool] = None


# Convenience aliases
Spec = GlobalSpecType
Spec = GlobalSpecType
Spec = GlobalSpecType
Spec = GlobalSpecType
Spec = SpecType
