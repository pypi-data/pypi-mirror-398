"""Pydantic models for client_side_defense."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class AddToAllowedDomains(F5XCBaseModel):
    """Add To Allowed Domains"""

    domains: Optional[list[str]] = None


class AddToMitigatedDomains(F5XCBaseModel):
    """Add To Mitigated Domains"""

    domains: Optional[list[str]] = None


class AffectedUser(F5XCBaseModel):
    """Information about the affected user"""

    channel: Optional[str] = None
    device_id: Optional[str] = None
    geolocation: Optional[str] = None
    ip_address: Optional[str] = None
    last_seen: Optional[str] = None
    user_agent: Optional[str] = None


class AffectedUserDeviceIDFilter(F5XCBaseModel):
    """Filter by affected user device ID"""

    device_ids: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class AffectedUserGeolocationFilter(F5XCBaseModel):
    """Filter by affected user geolocation"""

    geolocations: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class AffectedUserIPAddressFilter(F5XCBaseModel):
    """Filter by affected user IP address"""

    ip_addresses: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class AffectedUserFilters(F5XCBaseModel):
    """ListAffectedUsers API query filters"""

    affected_user_device_id_filter: Optional[AffectedUserDeviceIDFilter] = None
    affected_user_geolocation_filter: Optional[AffectedUserGeolocationFilter] = None
    affected_user_ip_address_filter: Optional[AffectedUserIPAddressFilter] = None


class Analysis(F5XCBaseModel):
    """Analysis of the form field by Client Side Defense"""

    updated_by: Optional[str] = None
    value: Optional[str] = None


class BehaviorByScript(F5XCBaseModel):
    """Behavior info"""

    category: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    name: Optional[str] = None
    recommendation: Optional[str] = None
    risk_level: Optional[str] = None
    users_affected: Optional[int] = None


class DeleteScriptJustificationResponse(F5XCBaseModel):
    """Response to delete script justification"""

    pass


class DeviceIDFilter(F5XCBaseModel):
    """Query Filter by device id filter strings"""

    device_id_strings: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class Location(F5XCBaseModel):
    """Location scripts pair"""

    associated_scripts: Optional[list[str]] = Field(default=None, alias="associatedScripts")
    location: Optional[str] = None


class DomainDetails(F5XCBaseModel):
    """Client-Side defense usage details per domain."""

    action_date: Optional[str] = Field(default=None, alias="actionDate")
    category: Optional[str] = None
    domain: Optional[str] = None
    first_seen_date: Optional[str] = Field(default=None, alias="firstSeenDate")
    latest_seen_date: Optional[str] = Field(default=None, alias="latestSeenDate")
    locations: Optional[list[Location]] = None
    risk_reason: Optional[list[str]] = Field(default=None, alias="riskReason")
    risk_score: Optional[int] = Field(default=None, alias="riskScore")
    status: Optional[str] = None


class UpdatedCount(F5XCBaseModel):
    """Pair of count and last updated timestamp, used to provided aggregated..."""

    count: Optional[int] = None
    last_updated: Optional[str] = Field(default=None, alias="lastUpdated")


class DomainSummary(F5XCBaseModel):
    """Collection of aggregated details"""

    action_needed_count: Optional[UpdatedCount] = Field(default=None, alias="actionNeededCount")
    allowed_domains: Optional[UpdatedCount] = Field(default=None, alias="allowedDomains")
    mitigated_domains: Optional[UpdatedCount] = Field(default=None, alias="mitigatedDomains")
    total_domains: Optional[UpdatedCount] = Field(default=None, alias="totalDomains")


class EnterpriseInfo(F5XCBaseModel):
    """Additional Information about the Enterprise"""

    transaction_count: Optional[int] = Field(default=None, alias="transactionCount")


class Event(F5XCBaseModel):
    """Event Info"""

    date: Optional[str] = None
    existing_behavior: Optional[int] = None
    new_behavior: Optional[int] = None


class IPFilter(F5XCBaseModel):
    """Query Filter by ip address filter strings"""

    ip_strings: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class RiskLevelFilter(F5XCBaseModel):
    """Query Filter by risk level filter strings"""

    op: Optional[Literal['IN']] = None
    risk_level_strings: Optional[list[str]] = None


class ScriptNameFilter(F5XCBaseModel):
    """Query Filter by script name filter strings"""

    op: Optional[Literal['IN']] = None
    script_name_strings: Optional[list[str]] = None


class ScriptStatusFilter(F5XCBaseModel):
    """Query Filter by script status filter strings"""

    op: Optional[Literal['IN']] = None
    script_status_strings: Optional[list[str]] = None


class Filters(F5XCBaseModel):
    """ListScripts API query filters"""

    device_id_filter: Optional[DeviceIDFilter] = None
    ip_filter: Optional[IPFilter] = None
    risk_level_filter: Optional[RiskLevelFilter] = None
    script_name_filter: Optional[ScriptNameFilter] = None
    script_status_filter: Optional[ScriptStatusFilter] = None


class FormField(F5XCBaseModel):
    """Form field info of all the scripts"""

    analysis: Optional[Analysis] = None
    associated_scripts: Optional[list[str]] = None
    first_read: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    last_read: Optional[str] = None
    locations: Optional[list[str]] = None
    name: Optional[str] = None


class FormFieldAnalysisFilter(F5XCBaseModel):
    """Query Filter by form field analysis filter strings"""

    analysis_strings: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class FormFieldByScript(F5XCBaseModel):
    """Form field information filtered by script"""

    first_read: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    last_read: Optional[str] = None
    name: Optional[str] = None
    risk_level: Optional[str] = None


class FormFieldNameFilter(F5XCBaseModel):
    """Query Filter by form field name filter strings"""

    name_strings: Optional[list[str]] = None
    op: Optional[Literal['IN']] = None


class FormFieldsFilters(F5XCBaseModel):
    """ListFormFields API query filters"""

    form_field_analysis_filter: Optional[FormFieldAnalysisFilter] = None
    form_field_name_filter: Optional[FormFieldNameFilter] = None


class GetDetectedDomainsResponse(F5XCBaseModel):
    """Get detected domains monitoring data"""

    customer: Optional[EnterpriseInfo] = None
    domain_summary: Optional[DomainSummary] = Field(default=None, alias="domainSummary")
    domains_list: Optional[list[DomainDetails]] = Field(default=None, alias="domainsList")
    location_list: Optional[dict[str, Any]] = Field(default=None, alias="locationList")


class GetDomainDetailsResponse(F5XCBaseModel):
    """Get domain details for the domain"""

    action_date: Optional[str] = Field(default=None, alias="actionDate")
    category: Optional[str] = None
    domain: Optional[str] = None
    first_seen_date: Optional[str] = Field(default=None, alias="firstSeenDate")
    latest_seen_date: Optional[str] = Field(default=None, alias="latestSeenDate")
    locations: Optional[list[Location]] = None
    risk_reason: Optional[list[str]] = Field(default=None, alias="riskReason")
    risk_score: Optional[int] = Field(default=None, alias="riskScore")
    status: Optional[str] = None


class GetFormFieldResponse(F5XCBaseModel):
    """Response to get form field"""

    associated_scripts: Optional[list[str]] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None


class GetJsInjectionConfigurationResponse(F5XCBaseModel):
    """Response to a get injection script request"""

    script_tag: Optional[str] = Field(default=None, alias="scriptTag")


class Summary(F5XCBaseModel):
    """Summary of the dashboard"""

    domain: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    risk_level: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class GetScriptOverviewResponse(F5XCBaseModel):
    """Response to get script overview"""

    events: Optional[list[Event]] = None
    summary: Optional[Summary] = None


class GetStatusResponse(F5XCBaseModel):
    """Get status of Client-Side Defense Configuration"""

    is_configured: Optional[bool] = Field(default=None, alias="isConfigured")
    is_enabled: Optional[bool] = Field(default=None, alias="isEnabled")


class GetSummaryResponse(F5XCBaseModel):
    """Response to get summary"""

    blocked_scripts: Optional[int] = None
    mitigated_domains: Optional[int] = None
    suspicious_scripts: Optional[int] = None


class InitRequest(F5XCBaseModel):
    """Any payload to be passed on the Provision API"""

    email: Optional[str] = None
    namespace: Optional[str] = None
    service_type: Optional[str] = Field(default=None, alias="serviceType")


class InitResponse(F5XCBaseModel):
    """Any payload to be return by Provision API"""

    is_configured: Optional[bool] = Field(default=None, alias="isConfigured")


class Justification(F5XCBaseModel):
    """User-provided script justification"""

    create_time: Optional[str] = None
    justification: Optional[str] = None
    justification_id: Optional[str] = None
    user_id: Optional[str] = None


class Sort(F5XCBaseModel):
    """API query sort criteria"""

    field: Optional[str] = None
    order: Optional[Literal['DESCENDING', 'ASCENDING']] = None


class ListAffectedUsersRequest(F5XCBaseModel):
    """Request to list affected users who have loaded this particular script"""

    end_time: Optional[str] = None
    filters: Optional[AffectedUserFilters] = None
    namespace: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    page_token: Optional[str] = None
    script_id: Optional[str] = None
    sorts: Optional[list[Sort]] = None
    start_time: Optional[str] = None


class ListAffectedUsersResponse(F5XCBaseModel):
    """Response to list affected users who have loaded this particular script"""

    affected_users: Optional[list[AffectedUser]] = None
    next_page_token: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None


class ListBehaviorsByScriptResponse(F5XCBaseModel):
    """Response to list behaviors by script"""

    behaviors: Optional[list[BehaviorByScript]] = None
    total_size: Optional[int] = None


class ListFormFieldsByScriptResponse(F5XCBaseModel):
    """Response to list form fields for input script"""

    form_fields: Optional[list[FormFieldByScript]] = None
    status: Optional[str] = None
    total_size: Optional[int] = None


class ListFormFieldsGetResponse(F5XCBaseModel):
    """Response to list form fields of all the scripts with GET method"""

    form_fields: Optional[list[FormField]] = None
    total_size: Optional[int] = None


class ListFormFieldsRequest(F5XCBaseModel):
    """Request to list form fields of all the scripts"""

    end_time: Optional[str] = None
    filters: Optional[FormFieldsFilters] = None
    namespace: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    page_token: Optional[str] = None
    sorts: Optional[list[Sort]] = None
    start_time: Optional[str] = None


class ListFormFieldsResponse(F5XCBaseModel):
    """Response to list form fields of all the scripts"""

    form_fields: Optional[list[FormField]] = None
    next_page_token: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None
    total_size: Optional[int] = None


class NetworkInteractionByScript(F5XCBaseModel):
    """Network interaction information by script"""

    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    name: Optional[str] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None


class ListNetworkInteractionsByScriptResponse(F5XCBaseModel):
    """Response to list network interactions by script"""

    network_interactions: Optional[list[NetworkInteractionByScript]] = None
    total_size: Optional[int] = None


class ScriptInfo(F5XCBaseModel):
    """Script information"""

    affected_users_count: Optional[int] = None
    first_seen: Optional[str] = None
    form_fields_read: Optional[int] = None
    id_: Optional[str] = Field(default=None, alias="id")
    justifications: Optional[list[Justification]] = None
    last_seen: Optional[str] = None
    locations: Optional[list[str]] = None
    network_interactions: Optional[int] = None
    new_behaviors: Optional[int] = None
    risk_level: Optional[str] = None
    script_name: Optional[str] = None
    status: Optional[str] = None


class ListScriptsLegacyResponse(F5XCBaseModel):
    """Response to list scripts"""

    next_page_token: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    scripts: Optional[list[ScriptInfo]] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None


class ListScriptsRequest(F5XCBaseModel):
    """Request to list scripts"""

    end_time: Optional[str] = None
    filters: Optional[Filters] = None
    namespace: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    page_token: Optional[str] = None
    sorts: Optional[list[Sort]] = None
    start_time: Optional[str] = None


class ListScriptsResponse(F5XCBaseModel):
    """Response to list scripts"""

    next_page_token: Optional[str] = None
    page_number: Optional[int] = None
    page_size: Optional[int] = None
    scripts: Optional[list[ScriptInfo]] = None
    total_count: Optional[int] = None
    total_pages: Optional[int] = None


class TestJSRequest(F5XCBaseModel):
    """Request to get injected JS tag status"""

    domain: Optional[str] = None
    namespace: Optional[str] = None
    page_url: Optional[str] = Field(default=None, alias="pageURL")


class TestJSResponse(F5XCBaseModel):
    """Get the page url JS status"""

    message: Optional[str] = None
    status: Optional[Literal['DETECTED', 'NOT_DETECTED', 'FAILED']] = None


class UpdateDomainsRequest(F5XCBaseModel):
    """Request to update domain"""

    add_to_allowed_domains: Optional[AddToAllowedDomains] = None
    add_to_mitigated_domains: Optional[AddToMitigatedDomains] = None
    namespace: Optional[str] = None


class UpdateDomainsResponse(F5XCBaseModel):
    """Response to update domain"""

    pass


class UpdateFieldAnalysisRequest(F5XCBaseModel):
    """Request to patch analysis of fields across scripts"""

    name: Optional[str] = None
    namespace: Optional[str] = None
    type_: Optional[Literal['SENSITIVE', 'NOT_SENSITIVE']] = Field(default=None, alias="type")


class UpdateFieldAnalysisResponse(F5XCBaseModel):
    status: Optional[str] = None


class UpdateScriptJustificationRequest(F5XCBaseModel):
    """Request to update script justification"""

    justification: Optional[str] = None
    namespace: Optional[str] = None
    script_id: Optional[str] = None
    user_id: Optional[str] = None


class UpdateScriptJustificationResponse(F5XCBaseModel):
    """Response to update script justification"""

    justification_id: Optional[str] = None


class UpdateScriptReadStatusRequest(F5XCBaseModel):
    """Request to update"""

    id_: Optional[str] = Field(default=None, alias="id")
    namespace: Optional[str] = None
    type_: Optional[Literal['BLOCK', 'ALLOW']] = Field(default=None, alias="type")


class UpdateScriptReadStatusResponse(F5XCBaseModel):
    """Payload about status of script read status result"""

    id_: Optional[str] = Field(default=None, alias="id")
    script_name: Optional[str] = None
    status: Optional[str] = None


# Convenience aliases
