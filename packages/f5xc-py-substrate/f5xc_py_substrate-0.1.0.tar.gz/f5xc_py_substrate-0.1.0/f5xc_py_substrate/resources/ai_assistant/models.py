"""Pydantic models for ai_assistant."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotDefenseEventDetails(F5XCBaseModel):
    """Bot Defense security events details"""

    action: Optional[Literal['ACTION_NONE', 'ALLOW', 'BLOCK', 'REDIRECT']] = None
    automation_type: Optional[str] = None
    bot_type: Optional[str] = None
    method: Optional[str] = None
    request_path: Optional[str] = None


class RequestDetails(F5XCBaseModel):
    """Request details"""

    domain: Optional[str] = None
    rsp_code: Optional[int] = None
    rsp_code_details: Optional[str] = None
    upstream_protocol_error_reason: Optional[str] = None


class SvcPolicyEventDetails(F5XCBaseModel):
    """Service policy security events details"""

    action: Optional[Literal['ACTION_NONE', 'ALLOW', 'BLOCK', 'REDIRECT']] = None
    ip_risk: Optional[Literal['IP_REPUTATION_NONE', 'IP_REPUTATION_LOW', 'IP_REPUTATION_HIGH']] = None
    ip_threat_categories: Optional[list[Literal['SPAM_SOURCES', 'WINDOWS_EXPLOITS', 'WEB_ATTACKS', 'BOTNETS', 'SCANNERS', 'REPUTATION', 'PHISHING', 'PROXY', 'MOBILE_THREATS', 'TOR_PROXY', 'DENIAL_OF_SERVICE', 'NETWORK']]] = None
    ip_trustworthiness: Optional[Literal['IP_REPUTATION_NONE', 'IP_REPUTATION_LOW', 'IP_REPUTATION_HIGH']] = None
    policy: Optional[str] = None
    policy_namespace: Optional[str] = None
    policy_rule: Optional[str] = None


class Bot(F5XCBaseModel):
    """Bot details"""

    classification: Optional[str] = None
    name: Optional[str] = None
    type_: Optional[str] = Field(default=None, alias="type")


class Signature(F5XCBaseModel):
    """Signature details"""

    accuracy: Optional[Literal['ACCURACY_NONE', 'ACCURACY_LOW', 'ACCURACY_MEDIUM', 'ACCURACY_HIGH']] = None
    attack_type: Optional[str] = None
    context: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    matching_info: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None


class ThreatCampaign(F5XCBaseModel):
    """Threat campaign details"""

    attack_type: Optional[str] = None
    id_: Optional[str] = Field(default=None, alias="id")
    name: Optional[str] = None


class Violation(F5XCBaseModel):
    """Violation details"""

    attack_type: Optional[str] = None
    context: Optional[str] = None
    matching_info: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None


class WAFEventDetails(F5XCBaseModel):
    """WAF security events details"""

    action: Optional[Literal['ACTION_NONE', 'ALLOW', 'BLOCK', 'REDIRECT']] = None
    app_firewall: Optional[str] = None
    bot: Optional[Bot] = None
    enforcement_mode: Optional[Literal['ENFORCEMENT_NONE', 'MONITORING', 'BLOCKING']] = None
    signatures: Optional[list[Signature]] = None
    threat_campaigns: Optional[list[ThreatCampaign]] = None
    violations: Optional[list[Violation]] = None


class ExplainLogRecordResponse(F5XCBaseModel):
    """Explain log response"""

    actions: Optional[str] = None
    analysis: Optional[str] = None
    bot_defense_event_details: Optional[BotDefenseEventDetails] = None
    request_details: Optional[RequestDetails] = None
    summary: Optional[str] = None
    svc_policy_event_details: Optional[SvcPolicyEventDetails] = None
    waf_event_details: Optional[WAFEventDetails] = None


class LogFilter(F5XCBaseModel):
    """Log filter for filter query"""

    key: Optional[str] = None
    op: Optional[Literal['IN', 'NOT_IN']] = None
    values: Optional[list[str]] = None


class DashboardLink(F5XCBaseModel):
    """Dashboard link will present common fields like type, namespace, object,..."""

    key: Optional[str] = None
    log_filters: Optional[list[LogFilter]] = None
    namespace: Optional[str] = None
    object_name: Optional[str] = None
    time_range: Optional[str] = None
    title: Optional[str] = None
    type_: Optional[Literal['SECURITY_ANALYTICS_EVENTS', 'REQUESTS_EVENTS', 'SITES', 'CLOUD_CREDENTIALS', 'SITES_UBER', 'SITE_ALERTS', 'SITE_MANAGEMENT_AWS_VPC_SITES', 'SITE_MANAGEMENT_AWS_TGW_SITES', 'SITE_MANAGEMENT_AZURE_VNET_SITES', 'SITE_MANAGEMENT_GCP_VPC_SITES', 'SITE_MANAGEMENT_APP_STACK_SITES', 'SITE_MANAGEMENT_SECURE_MESH_SITES', 'TENANT_OVERVIEW_PAGE', 'SUPPORT']] = Field(default=None, alias="type")


class GenericLink(F5XCBaseModel):
    """Generic link can have external link with full url"""

    key: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None


class Link(F5XCBaseModel):
    """Link for a page"""

    dashboard_link: Optional[DashboardLink] = None
    generic_link: Optional[GenericLink] = None


class GenDashboardFilterResponse(F5XCBaseModel):
    """Generate dashboard filter response"""

    actions: Optional[str] = None
    links: Optional[list[Link]] = None
    summary: Optional[str] = None


class ProtobufAny(F5XCBaseModel):
    """`Any` contains an arbitrary serialized protocol buffer message along..."""

    type_url: Optional[str] = None
    value: Optional[str] = None


class ErrorType(F5XCBaseModel):
    """Information about a error in API operation"""

    code: Optional[Literal['EOK', 'EPERMS', 'EBADINPUT', 'ENOTFOUND', 'EEXISTS', 'EUNKNOWN', 'ESERIALIZE', 'EINTERNAL', 'EPARTIAL']] = None
    error_obj: Optional[ProtobufAny] = None
    message: Optional[str] = None


class GenericResponse(F5XCBaseModel):
    """Generic Response"""

    error: Optional[ErrorType] = None
    is_error: Optional[bool] = None
    summary: Optional[str] = None


class Item(F5XCBaseModel):
    link: Optional[Link] = None


class ListList(F5XCBaseModel):
    item: Optional[list[Item]] = None
    title: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """List response"""

    external_links: Optional[list[Link]] = None
    items: Optional[list[ListList]] = None
    summary: Optional[str] = None


class OverlayData(F5XCBaseModel):
    """Overlay data for creating support ticket"""

    priority: Optional[str] = None
    product_data: Optional[str] = None
    subject: Optional[str] = None
    support_type: Optional[str] = None
    topic: Optional[str] = None
    workspace: Optional[str] = None


class OverlayContent(F5XCBaseModel):
    """Overlay link for creating ticket"""

    data: Optional[OverlayData] = None
    title: Optional[str] = None
    type_: Optional[Literal['SECURITY_ANALYTICS_EVENTS', 'REQUESTS_EVENTS', 'SITES', 'CLOUD_CREDENTIALS', 'SITES_UBER', 'SITE_ALERTS', 'SITE_MANAGEMENT_AWS_VPC_SITES', 'SITE_MANAGEMENT_AWS_TGW_SITES', 'SITE_MANAGEMENT_AZURE_VNET_SITES', 'SITE_MANAGEMENT_GCP_VPC_SITES', 'SITE_MANAGEMENT_APP_STACK_SITES', 'SITE_MANAGEMENT_SECURE_MESH_SITES', 'TENANT_OVERVIEW_PAGE', 'SUPPORT']] = Field(default=None, alias="type")


class Display(F5XCBaseModel):
    colour: Optional[Literal['COLOUR_TYPE_NONE', 'DANGER', 'INFO', 'WARNING', 'AMBER', 'SUCCESS', 'MALIBU']] = None
    display_type: Optional[Literal['DISPLAY_TYPE_NONE', 'ICON', 'DOT_WITH_VALUE', 'PROGRESS_BAR', 'DATE', 'DURATION', 'PROVIDER_ICON']] = None
    formats: Optional[list[Literal['FORMAT_TYPE_NONE', 'INLINE', 'BOLD', 'REVERSE_KEY_VALUE_ORDER', 'WRAP']]] = None


class FieldProperties(F5XCBaseModel):
    data_type: Optional[Literal['COLUMN_TYPE_NONE', 'STRING', 'INT', 'FLOAT', 'BOOL']] = None
    display: Optional[Display] = None
    name: Optional[str] = None
    title: Optional[str] = None
    tooltip: Optional[str] = None
    unit: Optional[Literal['UNIT_TYPE_NONE', 'GB', 'PERCENT', 'BYTE']] = None


class CellProperties(F5XCBaseModel):
    status_style: Optional[Literal['STATUS_STYLE_UNKNOWN', 'STATUS_STYLE_SUCCESS', 'STATUS_STYLE_DANGER', 'STATUS_STYLE_WARNING', 'STATUS_STYLE_INACTIVE', 'STATUS_STYLE_MINOR']] = None


class Cell(F5XCBaseModel):
    link: Optional[Link] = None
    properties: Optional[CellProperties] = None
    value: Optional[str] = None


class Row(F5XCBaseModel):
    """Contains the value for each rows of table"""

    cells: Optional[list[Cell]] = None


class Table(F5XCBaseModel):
    field_properties: Optional[list[FieldProperties]] = None
    rows: Optional[list[Row]] = None
    widget_type: Optional[Literal['WIDGET_TYPE_NONE', 'TWO_VALUE', 'DISTRIBUTION_CHART', 'TABLE', 'LIST', 'GRID', 'PIE']] = None


class WidgetView(F5XCBaseModel):
    item: Optional[Table] = None


class SiteAnalysisResponse(F5XCBaseModel):
    """Site analysis response"""

    external_links: Optional[list[Link]] = None
    internal_links: Optional[list[Link]] = None
    overlay_content: Optional[OverlayContent] = None
    summary: Optional[str] = None
    table_view: Optional[WidgetView] = None


class WidgetResponse(F5XCBaseModel):
    """Widget response"""

    item_links: Optional[list[Link]] = None
    items: Optional[list[WidgetView]] = None
    summary: Optional[str] = None


class AIAssistantQueryResponse(F5XCBaseModel):
    """AI Assistant Query Response"""

    current_query: Optional[str] = None
    explain_log: Optional[ExplainLogRecordResponse] = None
    follow_up_queries: Optional[list[str]] = None
    gen_dashboard_filter: Optional[GenDashboardFilterResponse] = None
    generic_response: Optional[GenericResponse] = None
    list_response: Optional[ListResponse] = None
    query_id: Optional[str] = None
    site_analysis_response: Optional[SiteAnalysisResponse] = None
    widget_response: Optional[WidgetResponse] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


# Convenience aliases
