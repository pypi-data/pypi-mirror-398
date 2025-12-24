"""F5 XC API resources.

Resources are lazy-loaded when accessed via the Client.
Import specific resources directly for type hints:

    from f5xc_py_substrate.resources import http_loadbalancer

    spec = http_loadbalancer.Spec(domains=["example.com"])

Available resources:
- ai_assistant
- api_crawler
- api_definition
- api_discovery
- api_group
- api_group_element
- api_testing
- api_credential
- addon_service
- addon_subscription
- address_allocator
- advertise_policy
- alert_policy
- alert_receiver
- alert
- allowed_tenant
- app_api_group
- app_setting
- app_type
- app_firewall
- app_security
- rule_suggestion
- device_id
- authentication
- bfdp
- subscription
- bgp
- bgp_asn_set
- bgp
- bgp_routing_policy
- apm
- bigip_irule
- bigip_virtual_server
- alert_gen_policy
- alert_template
- bot_defense_app_infrastructure
- bot_detection_rule
- bot_detection_update
- bot_endpoint_policy
- bot_infrastructure
- bot_allowlist_policy
- bot_network_policy
- cdn_loadbalancer
- cdn_cache_rule
- crl
- crl
- catalog
- cminstance
- certificate
- certificate_chain
- certified_hardware
- child_tenant
- child_tenant_manager
- client_side_defense
- allowed_domain
- protected_domain
- mitigated_domain
- subscription
- cloud_connect
- cloud_credentials
- cloud_elastic_ip
- cloud_region
- cloud_link
- cluster
- code_base_integration
- aws_tgw_site
- aws_vpc_site
- voltstack_site
- azure_vnet_site
- dns_compliance_checks
- forward_proxy_policy
- gcp_vpc_site
- http_loadbalancer
- network_policy_view
- protocol_inspection
- securemesh_site
- securemesh_site_v2
- tcp_loadbalancer
- udp_loadbalancer
- irule
- connectivity
- contact
- container_registry
- customer_support
- dc_cluster_group
- dns_domain
- dns_load_balancer
- dns_lb_health_check
- dns_lb_pool
- v1_dns_monitor
- dns_zone
- receiver
- data_delivery
- data_group
- subscription
- data_type
- debug
- dhcp
- discovered_service
- discovery
- endpoint
- enhanced_firewall_policy
- external_connector
- rrset
- subscription
- subscription
- secret_management
- voltshare
- maintenance_status
- fast_acl
- fast_acl_rule
- filter_set
- fleet
- flow_anomaly
- flow
- flow
- forwarding_class
- geo_config
- geo_location_set
- gia
- global_log_receiver
- v1_http_monitor
- healthcheck
- ike1
- ike_phase1_profile
- ike2
- ike_phase2_profile
- ip_prefix_set
- implicit_label
- infraprotect
- infraprotect_asn
- infraprotect_asn_prefix
- infraprotect_deny_list_rule
- infraprotect_firewall_rule
- infraprotect_firewall_rule_group
- infraprotect_firewall_ruleset
- infraprotect_information
- infraprotect_internet_prefix_advertisement
- invoice
- k8s_cluster
- k8s_cluster_role
- k8s_cluster_role_binding
- k8s_pod_security_admission
- k8s_pod_security_policy
- known_label
- known_label_key
- lma_region
- lte
- log_receiver
- log
- malicious_user_mitigation
- managed_tenant
- subscription
- subscription
- mobile_sdk
- mobile_base_config
- module_management
- nat_policy
- nfv_service
- nginx_csg
- nginx_instance
- nginx_server
- subscription
- nginx_service_discovery
- namespace
- namespace_role
- navigation_tile
- network_connector
- network_firewall
- network_interface
- network_policy
- network_policy_rule
- network_policy_set
- subscription
- aws_account
- origin_pool
- payment_method
- ping
- plan
- plan_transition
- policer
- policy_based_routing
- protected_application
- protocol_policer
- proxy
- public_ip
- quota
- rbac_policy
- rate_limiter
- rate_limiter_policy
- registration
- report
- report_config
- role
- trusted_ca_list
- route
- route
- srv6_network_slice
- oidc_provider
- secret_management_access
- secret_policy
- secret_policy_rule
- segment
- segment_connection
- sensitive_data_policy
- service
- service_policy
- service_policy_rule
- service_policy_set
- shape_bot_defense_instance
- reporting
- subscription
- recognize
- safeap
- safe
- signup
- site
- site
- site_mesh_group
- status_at_site
- stored_object
- subnet
- subscription
- subscription
- synthetic_monitor
- scim
- tpm_api_key
- tpm_category
- tpm_manager
- tpm_provision
- tcpdump
- tenant
- tenant_configuration
- tenant_management
- tenant_profile
- third_party_application
- ticket_tracking_system
- token
- topology
- traceroute
- tunnel
- infraprotect_tunnel
- usb
- usb_policy
- static_component
- upgrade_status
- virtual_appliance
- usage
- plan
- user
- user_group
- user_identification
- setting
- view_internal
- terraform_parameters
- virtual_host
- virtual_k8s
- virtual_network
- virtual_site
- voltshare_admin_policy
- waf
- waf_exclusion_policy
- waf_signatures_changelog
- wifi
- user_token
- workload
- workload_flavor
- xc_saas
- l3l4
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from f5xc_py_substrate.resources import ai_assistant
    from f5xc_py_substrate.resources import api_crawler
    from f5xc_py_substrate.resources import api_definition
    from f5xc_py_substrate.resources import api_discovery
    from f5xc_py_substrate.resources import api_group
    from f5xc_py_substrate.resources import api_group_element
    from f5xc_py_substrate.resources import api_testing
    from f5xc_py_substrate.resources import api_credential
    from f5xc_py_substrate.resources import addon_service
    from f5xc_py_substrate.resources import addon_subscription
    from f5xc_py_substrate.resources import address_allocator
    from f5xc_py_substrate.resources import advertise_policy
    from f5xc_py_substrate.resources import alert_policy
    from f5xc_py_substrate.resources import alert_receiver
    from f5xc_py_substrate.resources import alert
    from f5xc_py_substrate.resources import allowed_tenant
    from f5xc_py_substrate.resources import app_api_group
    from f5xc_py_substrate.resources import app_setting
    from f5xc_py_substrate.resources import app_type
    from f5xc_py_substrate.resources import app_firewall
    from f5xc_py_substrate.resources import app_security
    from f5xc_py_substrate.resources import rule_suggestion
    from f5xc_py_substrate.resources import device_id
    from f5xc_py_substrate.resources import authentication
    from f5xc_py_substrate.resources import bfdp
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import bgp
    from f5xc_py_substrate.resources import bgp_asn_set
    from f5xc_py_substrate.resources import bgp
    from f5xc_py_substrate.resources import bgp_routing_policy
    from f5xc_py_substrate.resources import apm
    from f5xc_py_substrate.resources import bigip_irule
    from f5xc_py_substrate.resources import bigip_virtual_server
    from f5xc_py_substrate.resources import alert_gen_policy
    from f5xc_py_substrate.resources import alert_template
    from f5xc_py_substrate.resources import bot_defense_app_infrastructure
    from f5xc_py_substrate.resources import bot_detection_rule
    from f5xc_py_substrate.resources import bot_detection_update
    from f5xc_py_substrate.resources import bot_endpoint_policy
    from f5xc_py_substrate.resources import bot_infrastructure
    from f5xc_py_substrate.resources import bot_allowlist_policy
    from f5xc_py_substrate.resources import bot_network_policy
    from f5xc_py_substrate.resources import cdn_loadbalancer
    from f5xc_py_substrate.resources import cdn_cache_rule
    from f5xc_py_substrate.resources import crl
    from f5xc_py_substrate.resources import crl
    from f5xc_py_substrate.resources import catalog
    from f5xc_py_substrate.resources import cminstance
    from f5xc_py_substrate.resources import certificate
    from f5xc_py_substrate.resources import certificate_chain
    from f5xc_py_substrate.resources import certified_hardware
    from f5xc_py_substrate.resources import child_tenant
    from f5xc_py_substrate.resources import child_tenant_manager
    from f5xc_py_substrate.resources import client_side_defense
    from f5xc_py_substrate.resources import allowed_domain
    from f5xc_py_substrate.resources import protected_domain
    from f5xc_py_substrate.resources import mitigated_domain
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import cloud_connect
    from f5xc_py_substrate.resources import cloud_credentials
    from f5xc_py_substrate.resources import cloud_elastic_ip
    from f5xc_py_substrate.resources import cloud_region
    from f5xc_py_substrate.resources import cloud_link
    from f5xc_py_substrate.resources import cluster
    from f5xc_py_substrate.resources import code_base_integration
    from f5xc_py_substrate.resources import aws_tgw_site
    from f5xc_py_substrate.resources import aws_vpc_site
    from f5xc_py_substrate.resources import voltstack_site
    from f5xc_py_substrate.resources import azure_vnet_site
    from f5xc_py_substrate.resources import dns_compliance_checks
    from f5xc_py_substrate.resources import forward_proxy_policy
    from f5xc_py_substrate.resources import gcp_vpc_site
    from f5xc_py_substrate.resources import http_loadbalancer
    from f5xc_py_substrate.resources import network_policy_view
    from f5xc_py_substrate.resources import protocol_inspection
    from f5xc_py_substrate.resources import securemesh_site
    from f5xc_py_substrate.resources import securemesh_site_v2
    from f5xc_py_substrate.resources import tcp_loadbalancer
    from f5xc_py_substrate.resources import udp_loadbalancer
    from f5xc_py_substrate.resources import irule
    from f5xc_py_substrate.resources import connectivity
    from f5xc_py_substrate.resources import contact
    from f5xc_py_substrate.resources import container_registry
    from f5xc_py_substrate.resources import customer_support
    from f5xc_py_substrate.resources import dc_cluster_group
    from f5xc_py_substrate.resources import dns_domain
    from f5xc_py_substrate.resources import dns_load_balancer
    from f5xc_py_substrate.resources import dns_lb_health_check
    from f5xc_py_substrate.resources import dns_lb_pool
    from f5xc_py_substrate.resources import v1_dns_monitor
    from f5xc_py_substrate.resources import dns_zone
    from f5xc_py_substrate.resources import receiver
    from f5xc_py_substrate.resources import data_delivery
    from f5xc_py_substrate.resources import data_group
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import data_type
    from f5xc_py_substrate.resources import debug
    from f5xc_py_substrate.resources import dhcp
    from f5xc_py_substrate.resources import discovered_service
    from f5xc_py_substrate.resources import discovery
    from f5xc_py_substrate.resources import endpoint
    from f5xc_py_substrate.resources import enhanced_firewall_policy
    from f5xc_py_substrate.resources import external_connector
    from f5xc_py_substrate.resources import rrset
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import secret_management
    from f5xc_py_substrate.resources import voltshare
    from f5xc_py_substrate.resources import maintenance_status
    from f5xc_py_substrate.resources import fast_acl
    from f5xc_py_substrate.resources import fast_acl_rule
    from f5xc_py_substrate.resources import filter_set
    from f5xc_py_substrate.resources import fleet
    from f5xc_py_substrate.resources import flow_anomaly
    from f5xc_py_substrate.resources import flow
    from f5xc_py_substrate.resources import flow
    from f5xc_py_substrate.resources import forwarding_class
    from f5xc_py_substrate.resources import geo_config
    from f5xc_py_substrate.resources import geo_location_set
    from f5xc_py_substrate.resources import gia
    from f5xc_py_substrate.resources import global_log_receiver
    from f5xc_py_substrate.resources import v1_http_monitor
    from f5xc_py_substrate.resources import healthcheck
    from f5xc_py_substrate.resources import ike1
    from f5xc_py_substrate.resources import ike_phase1_profile
    from f5xc_py_substrate.resources import ike2
    from f5xc_py_substrate.resources import ike_phase2_profile
    from f5xc_py_substrate.resources import ip_prefix_set
    from f5xc_py_substrate.resources import implicit_label
    from f5xc_py_substrate.resources import infraprotect
    from f5xc_py_substrate.resources import infraprotect_asn
    from f5xc_py_substrate.resources import infraprotect_asn_prefix
    from f5xc_py_substrate.resources import infraprotect_deny_list_rule
    from f5xc_py_substrate.resources import infraprotect_firewall_rule
    from f5xc_py_substrate.resources import infraprotect_firewall_rule_group
    from f5xc_py_substrate.resources import infraprotect_firewall_ruleset
    from f5xc_py_substrate.resources import infraprotect_information
    from f5xc_py_substrate.resources import infraprotect_internet_prefix_advertisement
    from f5xc_py_substrate.resources import invoice
    from f5xc_py_substrate.resources import k8s_cluster
    from f5xc_py_substrate.resources import k8s_cluster_role
    from f5xc_py_substrate.resources import k8s_cluster_role_binding
    from f5xc_py_substrate.resources import k8s_pod_security_admission
    from f5xc_py_substrate.resources import k8s_pod_security_policy
    from f5xc_py_substrate.resources import known_label
    from f5xc_py_substrate.resources import known_label_key
    from f5xc_py_substrate.resources import lma_region
    from f5xc_py_substrate.resources import lte
    from f5xc_py_substrate.resources import log_receiver
    from f5xc_py_substrate.resources import log
    from f5xc_py_substrate.resources import malicious_user_mitigation
    from f5xc_py_substrate.resources import managed_tenant
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import mobile_sdk
    from f5xc_py_substrate.resources import mobile_base_config
    from f5xc_py_substrate.resources import module_management
    from f5xc_py_substrate.resources import nat_policy
    from f5xc_py_substrate.resources import nfv_service
    from f5xc_py_substrate.resources import nginx_csg
    from f5xc_py_substrate.resources import nginx_instance
    from f5xc_py_substrate.resources import nginx_server
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import nginx_service_discovery
    from f5xc_py_substrate.resources import namespace
    from f5xc_py_substrate.resources import namespace_role
    from f5xc_py_substrate.resources import navigation_tile
    from f5xc_py_substrate.resources import network_connector
    from f5xc_py_substrate.resources import network_firewall
    from f5xc_py_substrate.resources import network_interface
    from f5xc_py_substrate.resources import network_policy
    from f5xc_py_substrate.resources import network_policy_rule
    from f5xc_py_substrate.resources import network_policy_set
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import aws_account
    from f5xc_py_substrate.resources import origin_pool
    from f5xc_py_substrate.resources import payment_method
    from f5xc_py_substrate.resources import ping
    from f5xc_py_substrate.resources import plan
    from f5xc_py_substrate.resources import plan_transition
    from f5xc_py_substrate.resources import policer
    from f5xc_py_substrate.resources import policy_based_routing
    from f5xc_py_substrate.resources import protected_application
    from f5xc_py_substrate.resources import protocol_policer
    from f5xc_py_substrate.resources import proxy
    from f5xc_py_substrate.resources import public_ip
    from f5xc_py_substrate.resources import quota
    from f5xc_py_substrate.resources import rbac_policy
    from f5xc_py_substrate.resources import rate_limiter
    from f5xc_py_substrate.resources import rate_limiter_policy
    from f5xc_py_substrate.resources import registration
    from f5xc_py_substrate.resources import report
    from f5xc_py_substrate.resources import report_config
    from f5xc_py_substrate.resources import role
    from f5xc_py_substrate.resources import trusted_ca_list
    from f5xc_py_substrate.resources import route
    from f5xc_py_substrate.resources import route
    from f5xc_py_substrate.resources import srv6_network_slice
    from f5xc_py_substrate.resources import oidc_provider
    from f5xc_py_substrate.resources import secret_management_access
    from f5xc_py_substrate.resources import secret_policy
    from f5xc_py_substrate.resources import secret_policy_rule
    from f5xc_py_substrate.resources import segment
    from f5xc_py_substrate.resources import segment_connection
    from f5xc_py_substrate.resources import sensitive_data_policy
    from f5xc_py_substrate.resources import service
    from f5xc_py_substrate.resources import service_policy
    from f5xc_py_substrate.resources import service_policy_rule
    from f5xc_py_substrate.resources import service_policy_set
    from f5xc_py_substrate.resources import shape_bot_defense_instance
    from f5xc_py_substrate.resources import reporting
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import recognize
    from f5xc_py_substrate.resources import safeap
    from f5xc_py_substrate.resources import safe
    from f5xc_py_substrate.resources import signup
    from f5xc_py_substrate.resources import site
    from f5xc_py_substrate.resources import site
    from f5xc_py_substrate.resources import site_mesh_group
    from f5xc_py_substrate.resources import status_at_site
    from f5xc_py_substrate.resources import stored_object
    from f5xc_py_substrate.resources import subnet
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import subscription
    from f5xc_py_substrate.resources import synthetic_monitor
    from f5xc_py_substrate.resources import scim
    from f5xc_py_substrate.resources import tpm_api_key
    from f5xc_py_substrate.resources import tpm_category
    from f5xc_py_substrate.resources import tpm_manager
    from f5xc_py_substrate.resources import tpm_provision
    from f5xc_py_substrate.resources import tcpdump
    from f5xc_py_substrate.resources import tenant
    from f5xc_py_substrate.resources import tenant_configuration
    from f5xc_py_substrate.resources import tenant_management
    from f5xc_py_substrate.resources import tenant_profile
    from f5xc_py_substrate.resources import third_party_application
    from f5xc_py_substrate.resources import ticket_tracking_system
    from f5xc_py_substrate.resources import token
    from f5xc_py_substrate.resources import topology
    from f5xc_py_substrate.resources import traceroute
    from f5xc_py_substrate.resources import tunnel
    from f5xc_py_substrate.resources import infraprotect_tunnel
    from f5xc_py_substrate.resources import usb
    from f5xc_py_substrate.resources import usb_policy
    from f5xc_py_substrate.resources import static_component
    from f5xc_py_substrate.resources import upgrade_status
    from f5xc_py_substrate.resources import virtual_appliance
    from f5xc_py_substrate.resources import usage
    from f5xc_py_substrate.resources import plan
    from f5xc_py_substrate.resources import user
    from f5xc_py_substrate.resources import user_group
    from f5xc_py_substrate.resources import user_identification
    from f5xc_py_substrate.resources import setting
    from f5xc_py_substrate.resources import view_internal
    from f5xc_py_substrate.resources import terraform_parameters
    from f5xc_py_substrate.resources import virtual_host
    from f5xc_py_substrate.resources import virtual_k8s
    from f5xc_py_substrate.resources import virtual_network
    from f5xc_py_substrate.resources import virtual_site
    from f5xc_py_substrate.resources import voltshare_admin_policy
    from f5xc_py_substrate.resources import waf
    from f5xc_py_substrate.resources import waf_exclusion_policy
    from f5xc_py_substrate.resources import waf_signatures_changelog
    from f5xc_py_substrate.resources import wifi
    from f5xc_py_substrate.resources import user_token
    from f5xc_py_substrate.resources import workload
    from f5xc_py_substrate.resources import workload_flavor
    from f5xc_py_substrate.resources import xc_saas
    from f5xc_py_substrate.resources import l3l4


# Lazy loading for resource modules
def __getattr__(name: str):
    """Lazy load resource modules."""
    try:
        import importlib
        return importlib.import_module(f"f5xc_py_substrate.resources.{name}")
    except ModuleNotFoundError:
        raise AttributeError(f"module 'f5xc_py_substrate.resources' has no attribute '{name}'")


__all__ = [
    "ai_assistant",
    "api_crawler",
    "api_definition",
    "api_discovery",
    "api_group",
    "api_group_element",
    "api_testing",
    "api_credential",
    "addon_service",
    "addon_subscription",
    "address_allocator",
    "advertise_policy",
    "alert_policy",
    "alert_receiver",
    "alert",
    "allowed_tenant",
    "app_api_group",
    "app_setting",
    "app_type",
    "app_firewall",
    "app_security",
    "rule_suggestion",
    "device_id",
    "authentication",
    "bfdp",
    "subscription",
    "bgp",
    "bgp_asn_set",
    "bgp",
    "bgp_routing_policy",
    "apm",
    "bigip_irule",
    "bigip_virtual_server",
    "alert_gen_policy",
    "alert_template",
    "bot_defense_app_infrastructure",
    "bot_detection_rule",
    "bot_detection_update",
    "bot_endpoint_policy",
    "bot_infrastructure",
    "bot_allowlist_policy",
    "bot_network_policy",
    "cdn_loadbalancer",
    "cdn_cache_rule",
    "crl",
    "crl",
    "catalog",
    "cminstance",
    "certificate",
    "certificate_chain",
    "certified_hardware",
    "child_tenant",
    "child_tenant_manager",
    "client_side_defense",
    "allowed_domain",
    "protected_domain",
    "mitigated_domain",
    "subscription",
    "cloud_connect",
    "cloud_credentials",
    "cloud_elastic_ip",
    "cloud_region",
    "cloud_link",
    "cluster",
    "code_base_integration",
    "aws_tgw_site",
    "aws_vpc_site",
    "voltstack_site",
    "azure_vnet_site",
    "dns_compliance_checks",
    "forward_proxy_policy",
    "gcp_vpc_site",
    "http_loadbalancer",
    "network_policy_view",
    "protocol_inspection",
    "securemesh_site",
    "securemesh_site_v2",
    "tcp_loadbalancer",
    "udp_loadbalancer",
    "irule",
    "connectivity",
    "contact",
    "container_registry",
    "customer_support",
    "dc_cluster_group",
    "dns_domain",
    "dns_load_balancer",
    "dns_lb_health_check",
    "dns_lb_pool",
    "v1_dns_monitor",
    "dns_zone",
    "receiver",
    "data_delivery",
    "data_group",
    "subscription",
    "data_type",
    "debug",
    "dhcp",
    "discovered_service",
    "discovery",
    "endpoint",
    "enhanced_firewall_policy",
    "external_connector",
    "rrset",
    "subscription",
    "subscription",
    "secret_management",
    "voltshare",
    "maintenance_status",
    "fast_acl",
    "fast_acl_rule",
    "filter_set",
    "fleet",
    "flow_anomaly",
    "flow",
    "flow",
    "forwarding_class",
    "geo_config",
    "geo_location_set",
    "gia",
    "global_log_receiver",
    "v1_http_monitor",
    "healthcheck",
    "ike1",
    "ike_phase1_profile",
    "ike2",
    "ike_phase2_profile",
    "ip_prefix_set",
    "implicit_label",
    "infraprotect",
    "infraprotect_asn",
    "infraprotect_asn_prefix",
    "infraprotect_deny_list_rule",
    "infraprotect_firewall_rule",
    "infraprotect_firewall_rule_group",
    "infraprotect_firewall_ruleset",
    "infraprotect_information",
    "infraprotect_internet_prefix_advertisement",
    "invoice",
    "k8s_cluster",
    "k8s_cluster_role",
    "k8s_cluster_role_binding",
    "k8s_pod_security_admission",
    "k8s_pod_security_policy",
    "known_label",
    "known_label_key",
    "lma_region",
    "lte",
    "log_receiver",
    "log",
    "malicious_user_mitigation",
    "managed_tenant",
    "subscription",
    "subscription",
    "mobile_sdk",
    "mobile_base_config",
    "module_management",
    "nat_policy",
    "nfv_service",
    "nginx_csg",
    "nginx_instance",
    "nginx_server",
    "subscription",
    "nginx_service_discovery",
    "namespace",
    "namespace_role",
    "navigation_tile",
    "network_connector",
    "network_firewall",
    "network_interface",
    "network_policy",
    "network_policy_rule",
    "network_policy_set",
    "subscription",
    "aws_account",
    "origin_pool",
    "payment_method",
    "ping",
    "plan",
    "plan_transition",
    "policer",
    "policy_based_routing",
    "protected_application",
    "protocol_policer",
    "proxy",
    "public_ip",
    "quota",
    "rbac_policy",
    "rate_limiter",
    "rate_limiter_policy",
    "registration",
    "report",
    "report_config",
    "role",
    "trusted_ca_list",
    "route",
    "route",
    "srv6_network_slice",
    "oidc_provider",
    "secret_management_access",
    "secret_policy",
    "secret_policy_rule",
    "segment",
    "segment_connection",
    "sensitive_data_policy",
    "service",
    "service_policy",
    "service_policy_rule",
    "service_policy_set",
    "shape_bot_defense_instance",
    "reporting",
    "subscription",
    "recognize",
    "safeap",
    "safe",
    "signup",
    "site",
    "site",
    "site_mesh_group",
    "status_at_site",
    "stored_object",
    "subnet",
    "subscription",
    "subscription",
    "synthetic_monitor",
    "scim",
    "tpm_api_key",
    "tpm_category",
    "tpm_manager",
    "tpm_provision",
    "tcpdump",
    "tenant",
    "tenant_configuration",
    "tenant_management",
    "tenant_profile",
    "third_party_application",
    "ticket_tracking_system",
    "token",
    "topology",
    "traceroute",
    "tunnel",
    "infraprotect_tunnel",
    "usb",
    "usb_policy",
    "static_component",
    "upgrade_status",
    "virtual_appliance",
    "usage",
    "plan",
    "user",
    "user_group",
    "user_identification",
    "setting",
    "view_internal",
    "terraform_parameters",
    "virtual_host",
    "virtual_k8s",
    "virtual_network",
    "virtual_site",
    "voltshare_admin_policy",
    "waf",
    "waf_exclusion_policy",
    "waf_signatures_changelog",
    "wifi",
    "user_token",
    "workload",
    "workload_flavor",
    "xc_saas",
    "l3l4",
]
