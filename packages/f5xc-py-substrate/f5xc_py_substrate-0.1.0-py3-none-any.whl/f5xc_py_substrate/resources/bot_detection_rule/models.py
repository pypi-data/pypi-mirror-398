"""Pydantic models for bot_detection_rule."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from f5xc_py_substrate.models import F5XCBaseModel


class BotDetectionRuleListItem(F5XCBaseModel):
    """List item for bot_detection_rule resources."""


class Config(F5XCBaseModel):
    """Rule configuration"""

    mitigation: Optional[bool] = None


class RegionRuleConfig(F5XCBaseModel):
    """Rule config per region"""

    region_config: Optional[dict[str, Any]] = None


class ConfigPerBotInfra(F5XCBaseModel):
    """Bot detection rule configuration per bot infrastructure"""

    bot_detection_rule_config: Optional[Config] = None
    bot_infra_id: Optional[str] = None
    bot_infra_name: Optional[str] = None
    bot_infrastructure_type: Optional[Literal['BOT_INFRA_TYPE_UNKNOWN', 'BOT_INFRA_TYPE_CLOUD_HOSTED', 'BOT_INFRA_TYPE_HOSTED', 'BOT_INFRA_TYPE_ON_PREM']] = None
    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    region_rule_config: Optional[RegionRuleConfig] = None


class ConfigChangeReason(F5XCBaseModel):
    """Reason for changing the bot detection rule configuration"""

    comments: Optional[str] = None
    reasons: Optional[list[Literal['BOT_DETECTION_RULE_CHANGE_REASON_UNKNOWN', 'BOT_DETECTION_RULE_CHANGE_REASON_FALSE_POSITIVE', 'BOT_DETECTION_RULE_CHANGE_REASON_TRUE_POSITIVE', 'BOT_DETECTION_RULE_CHANGE_REASON_TESTING', 'BOT_DETECTION_RULE_CHANGE_REASON_OTHER']]] = None


class ConfigChange(F5XCBaseModel):
    """Bot Detection Rule Config Change"""

    deploy_to: Optional[list[Literal['PRODUCTION', 'TESTING']]] = None
    desired_rule_config: Optional[Config] = None
    desired_rule_config_per_bot_infra: Optional[list[ConfigPerBotInfra]] = None
    existing_rule_config_per_bot_infra: Optional[list[ConfigPerBotInfra]] = None
    last_modified_at: Optional[str] = None
    reason: Optional[ConfigChangeReason] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None


class BotInfraDeploymentStatusDetails(F5XCBaseModel):
    """Bot Infrastructure Deployment Status Details"""

    bot_infra_deployment_status: Optional[Literal['BOT_INFRA_DEPLOYMENT_STATUS_UNKNOWN', 'BOT_INFRA_DEPLOYMENT_STATUS_INITIATED', 'BOT_INFRA_DEPLOYMENT_STATUS_SUCCESS', 'BOT_INFRA_DEPLOYMENT_STATUS_FAILED', 'BOT_INFRA_DEPLOYMENT_STATUS_INITIATION_FAILED']] = None
    status_message: Optional[str] = None


class RegionStatus(F5XCBaseModel):
    """The status of each bot infrastructure per region"""

    region_status_details: Optional[dict[str, Any]] = None


class BotInfraDeploymentDetails(F5XCBaseModel):
    """Bot Infrastructure Deployment Details"""

    bot_infra_name: Optional[str] = None
    bot_infra_status: Optional[BotInfraDeploymentStatusDetails] = None
    bot_infrastructure_type: Optional[Literal['BOT_INFRA_TYPE_UNKNOWN', 'BOT_INFRA_TYPE_CLOUD_HOSTED', 'BOT_INFRA_TYPE_HOSTED', 'BOT_INFRA_TYPE_ON_PREM']] = None
    environment: Optional[Literal['PRODUCTION', 'TESTING']] = None
    region_status: Optional[RegionStatus] = None


class ConfigDeploymentDetailsPerBotInfra(F5XCBaseModel):
    bot_detection_rule_config: Optional[Config] = None
    bot_infra_deployment_details: Optional[BotInfraDeploymentDetails] = None


class BotInfrastructure(F5XCBaseModel):
    """Bot Infrastructure"""

    environment_type: Optional[Literal['PRODUCTION', 'TESTING']] = None
    name: Optional[str] = None


class BotDetectionRulebotdetectionrulesdeployment(F5XCBaseModel):
    """Bot detection rules deployment"""

    bot_infrastructures: Optional[list[BotInfrastructure]] = None
    comments: Optional[str] = None
    deployment_id: Optional[str] = None
    deployment_status: Optional[Literal['BOT_DETECTION_RULES_DEPLOYMENT_STATUS_UNKNOWN', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DRAFT', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_INITIATED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DEPLOYED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_FAILED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_PARTIALLY_DEPLOYED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DISCARDED_DRAFT', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_INITIATION_FAILED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_PARTIALLY_INITIATED']] = None
    deployment_time: Optional[str] = None
    modified_by: Optional[str] = None
    number_of_rules: Optional[int] = None
    rules: Optional[list[str]] = None
    traffic_types: Optional[list[Literal['WEB', 'MOBILE']]] = None


class DeployBotDetectionRulesResponse(F5XCBaseModel):
    """Response for deploy bot detection rules"""

    deployment_status: Optional[Literal['BOT_DETECTION_RULES_DEPLOYMENT_STATUS_UNKNOWN', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DRAFT', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_INITIATED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DEPLOYED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_FAILED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_PARTIALLY_DEPLOYED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DISCARDED_DRAFT', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_INITIATION_FAILED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_PARTIALLY_INITIATED']] = None


class DraftRuleCounts(F5XCBaseModel):
    """Rule summary of bot detection rules in draft state"""

    total: Optional[int] = None


class RuleStateCounts(F5XCBaseModel):
    """Rule summary of bot detection rules for per state"""

    off: Optional[int] = None
    on: Optional[int] = None


class EnvironmentRuleCounts(F5XCBaseModel):
    """Rule summary of bot detection rules in per environment"""

    mobile: Optional[RuleStateCounts] = None
    web: Optional[RuleStateCounts] = None


class Empty(F5XCBaseModel):
    """This can be used for messages where no values are needed"""

    pass


class RuleChangeTypeModification(F5XCBaseModel):
    """Rule change type - Modification"""

    comments: Optional[str] = None
    reasons: Optional[list[str]] = None
    rule_config_deployment_details_per_bot_infra: Optional[list[ConfigDeploymentDetailsPerBotInfra]] = None


class RuleChange(F5XCBaseModel):
    """Rule change holds the details of the changes made to a bot detection rule"""

    change_type: Optional[Literal['BOT_DETECTION_RULE_CHANGE_TYPE_UNKNOWN', 'BOT_DETECTION_RULE_CHANGE_TYPE_CREATION', 'BOT_DETECTION_RULE_CHANGE_TYPE_MODIFICATION', 'BOT_DETECTION_RULE_CHANGE_TYPE_DELETION']] = None
    changed_by: Optional[str] = None
    creation: Optional[Any] = None
    deletion: Optional[Any] = None
    modification: Optional[RuleChangeTypeModification] = None
    timestamp: Optional[str] = None


class GetBotDetectionRuleChangeHistoryResponse(F5XCBaseModel):
    """Response for get bot detection rule change history"""

    rule_changes: Optional[list[RuleChange]] = None


class GetBotDetectionRulesDeploymentDetailsResponse(F5XCBaseModel):
    """Response for get bot detection rules deployment deployment"""

    config_change_per_bot_detection_rule: Optional[list[ConfigChange]] = None
    deploy_to: Optional[list[Literal['PRODUCTION', 'TESTING']]] = None
    deployed_by: Optional[str] = None
    deployment_details_per_bot_infra: Optional[list[BotInfraDeploymentDetails]] = None
    deployment_status: Optional[Literal['BOT_DETECTION_RULES_DEPLOYMENT_STATUS_UNKNOWN', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DRAFT', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_INITIATED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DEPLOYED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_FAILED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_PARTIALLY_DEPLOYED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_DISCARDED_DRAFT', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_INITIATION_FAILED', 'BOT_DETECTION_RULES_DEPLOYMENT_STATUS_PARTIALLY_INITIATED']] = None
    deployment_time: Optional[str] = None


class GetBotDetectionRulesDeploymentsResponse(F5XCBaseModel):
    """Response for get bot detection rules deployments"""

    bot_detection_rules_deployments: Optional[list[BotDetectionRulebotdetectionrulesdeployment]] = None


class GetBotDetectionRulesDraftResponse(F5XCBaseModel):
    """Response for get bot detection rules draft"""

    comments: Optional[str] = None
    config_change_per_bot_detection_rule: Optional[list[ConfigChange]] = None


class RuleSummary(F5XCBaseModel):
    """Rule summary of bot detection rules"""

    draft: Optional[DraftRuleCounts] = None
    prod: Optional[EnvironmentRuleCounts] = None
    test: Optional[EnvironmentRuleCounts] = None


class GetBotDetectionRulesSummaryResponse(F5XCBaseModel):
    """Response for get bot detection rules summary"""

    rule_summary: Optional[RuleSummary] = None


class ObjectRefType(F5XCBaseModel):
    """This type establishes a 'direct reference' from one object(the referrer)..."""

    kind: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ObjectGetMetaType(F5XCBaseModel):
    """ObjectGetMetaType is metadata that can be specified in Get/Create..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disable: Optional[bool] = None
    labels: Optional[dict[str, Any]] = None
    name: Optional[str] = None
    namespace: Optional[str] = None


class GetSpecType(F5XCBaseModel):
    """Get Bot Detection Rule"""

    bot_detection_rule_configs_per_bot_infras: Optional[list[ConfigPerBotInfra]] = None
    classification: Optional[list[str]] = None
    cluster_groups: Optional[list[str]] = None
    created_at: Optional[str] = None
    description: Optional[str] = None
    last_modified_at: Optional[str] = None
    last_modified_by: Optional[str] = None
    rule_name: Optional[str] = None
    rule_type: Optional[Literal['BOT_DETECTION_RULE_TYPE_UNKNOWN', 'BOT_DETECTION_RULE_TYPE_ENFORCED_BLOCKING', 'BOT_DETECTION_RULE_TYPE_CONTROL_BLOCKING']] = None
    traffic_type: Optional[Literal['WEB', 'MOBILE']] = None
    version: Optional[int] = None


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


class GetResponse(F5XCBaseModel):
    """This is the output message of the 'Get' RPC"""

    deleted_referred_objects: Optional[list[ObjectRefType]] = None
    disabled_referred_objects: Optional[list[ObjectRefType]] = None
    metadata: Optional[ObjectGetMetaType] = None
    referring_objects: Optional[list[ObjectRefType]] = None
    spec: Optional[GetSpecType] = None
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


class ListResponseItem(F5XCBaseModel):
    """By default a summary of bot_detection_rule is returned in 'List'. By..."""

    annotations: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    disabled: Optional[bool] = None
    get_spec: Optional[GetSpecType] = None
    labels: Optional[dict[str, Any]] = None
    metadata: Optional[ObjectGetMetaType] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
    owner_view: Optional[ViewRefType] = None
    system_metadata: Optional[SystemObjectGetMetaType] = None
    tenant: Optional[str] = None
    uid: Optional[str] = None


class ListResponse(F5XCBaseModel):
    """This is the output message of 'List' RPC."""

    errors: Optional[list[ErrorType]] = None
    items: Optional[list[ListResponseItem]] = None


class SaveDraftResponse(F5XCBaseModel):
    """Response for save draft"""

    pass


# Convenience aliases
Spec = GetSpecType
