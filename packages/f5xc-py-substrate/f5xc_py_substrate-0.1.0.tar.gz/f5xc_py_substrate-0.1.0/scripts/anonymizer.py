#!/usr/bin/env python3
"""Anonymize F5 XC resource configurations for use as test spec templates.

This module provides utilities to sanitize real resource configurations
by replacing sensitive data (domains, IPs, secrets, etc.) with safe
placeholder values suitable for integration tests.
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


# Patterns to match and replace
DOMAIN_PATTERNS = [
    r"[\w.-]+\.f5demos\.com",
    r"[\w.-]+\.myedgedemo\.com",
    r"[\w.-]+\.volterra\.io",
    r"[\w.-]+\.ves\.volterra\.io",
    r"[\w.-]+\.console\.ves\.volterra\.io",
]

# Fields that should use {test_namespace} template
NAMESPACE_FIELDS = {"namespace"}

# Fields that contain resource names to anonymize
NAME_FIELDS = {"name"}

# Fields to completely remove (contain secrets/sensitive data)
REMOVE_FIELDS = {
    "uid",
    "tenant",
    "resource_version",
    "creation_timestamp",
    "modification_timestamp",
    "creator_id",
    "creator_class",
    "finalizers",
    "initializers",
    "owner_references",
    "auto_cert_info",
    "auto_cert_expiry",
    "auto_cert_issuer",
    "auto_cert_state",
    "auto_cert_subject",
    "dns_records",
    "state_start_time",
    "cert_state",
    "system_metadata",
    "create_form",
    "replace_form",
    "referring_objects",
    "deleted_referred_objects",
    "disabled_referred_objects",
}

# Fields that indicate secrets (remove or replace with placeholder)
SECRET_FIELD_PATTERNS = [
    r".*secret.*",
    r".*token.*",
    r".*key.*",
    r".*password.*",
    r".*credential.*",
    r".*certificate.*",
    r".*private.*",
]

# IP address pattern
IP_PATTERN = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

# Email pattern
EMAIL_PATTERN = r"\b[\w.-]+@[\w.-]+\.\w+\b"


def anonymize_spec(
    spec: dict[str, Any],
    resource_name: str = "resource",
    keep_name: bool = False,
) -> dict[str, Any]:
    """Anonymize a resource spec for use as a test template.

    Args:
        spec: The resource spec dictionary (usually from resource.spec)
        resource_name: Name to use in placeholders (e.g., "http_loadbalancer")
        keep_name: If True, don't replace the resource name

    Returns:
        Anonymized copy of the spec
    """
    result = deepcopy(spec)
    _anonymize_recursive(result, resource_name, is_root=True, keep_name=keep_name)
    return result


def _anonymize_recursive(
    obj: Any,
    resource_name: str,
    is_root: bool = False,
    parent_key: str = "",
    keep_name: bool = False,
) -> Any:
    """Recursively anonymize a nested structure."""
    if obj is None:
        return obj

    if isinstance(obj, dict):
        keys_to_remove = set()

        for key, value in list(obj.items()):
            # Check if field should be removed
            if key in REMOVE_FIELDS:
                keys_to_remove.add(key)
                continue

            # Check for secret field patterns
            if _is_secret_field(key):
                keys_to_remove.add(key)
                continue

            # Remove null/None values to keep specs clean
            if value is None:
                keys_to_remove.add(key)
                continue

            # Remove empty lists and dicts (optional cleanup)
            if isinstance(value, (list, dict)) and not value:
                keys_to_remove.add(key)
                continue

            # Handle namespace fields - use template variable
            if key in NAMESPACE_FIELDS and isinstance(value, str):
                obj[key] = "{test_namespace}"
                continue

            # Handle name fields in nested objects (resource references)
            if key in NAME_FIELDS and isinstance(value, str) and not is_root:
                if not keep_name:
                    obj[key] = f"sdk-test-{resource_name}"
                continue

            # Recursively process nested structures
            if isinstance(value, (dict, list)):
                _anonymize_recursive(value, resource_name, is_root=False, parent_key=key, keep_name=keep_name)
                # Remove if became empty after recursion
                if isinstance(value, (dict, list)) and not value:
                    keys_to_remove.add(key)
            elif isinstance(value, str):
                obj[key] = _anonymize_string(value, key)

        # Remove marked fields
        for key in keys_to_remove:
            if key in obj:  # Check in case already removed
                del obj[key]

    elif isinstance(obj, list):
        # Remove None items from lists
        i = 0
        while i < len(obj):
            if obj[i] is None:
                obj.pop(i)
            elif isinstance(obj[i], (dict, list)):
                _anonymize_recursive(obj[i], resource_name, is_root=False, parent_key=parent_key, keep_name=keep_name)
                i += 1
            elif isinstance(obj[i], str):
                obj[i] = _anonymize_string(obj[i], parent_key)
                i += 1
            else:
                i += 1

    return obj


def _is_secret_field(field_name: str) -> bool:
    """Check if a field name indicates secret/sensitive data."""
    field_lower = field_name.lower()
    for pattern in SECRET_FIELD_PATTERNS:
        if re.match(pattern, field_lower):
            return True
    return False


def _anonymize_string(value: str, field_name: str = "") -> str:
    """Anonymize a string value based on its content."""
    # Replace domain names
    for pattern in DOMAIN_PATTERNS:
        value = re.sub(pattern, "sdk-test.example.com", value, flags=re.IGNORECASE)

    # Replace IP addresses (but not in CIDR notation for prefix sets)
    if not field_name.lower().endswith("prefix"):
        value = re.sub(IP_PATTERN, "10.0.0.1", value)

    # Replace email addresses
    value = re.sub(EMAIL_PATTERN, "test@example.com", value)

    # Replace URLs with example.com
    value = re.sub(r"https?://[^\s\"']+", "https://example.com", value)

    return value


def extract_spec_for_template(
    full_response: dict[str, Any],
    resource_name: str,
) -> dict[str, Any]:
    """Extract and anonymize the spec portion for a test template.

    Takes a full API response (with metadata, spec, etc.) and extracts
    just the spec portion, anonymized for use in test templates.

    Args:
        full_response: Full API response dict
        resource_name: Name of the resource type

    Returns:
        Dict with 'create' and 'replace' specs ready for YAML template
    """
    spec = full_response.get("spec", {})
    if not spec:
        return {"create": {}, "replace": {}}

    # Create the anonymized spec
    create_spec = anonymize_spec(spec, resource_name)

    # For replace, make a small modification to verify updates work
    replace_spec = deepcopy(create_spec)
    _add_replace_variation(replace_spec)

    return {
        "create": create_spec,
        "replace": replace_spec,
    }


def _add_replace_variation(spec: dict[str, Any]) -> None:
    """Add a small variation to the replace spec to verify updates work.

    Modifies common fields that are safe to change between create/replace.
    """
    # Try to modify description (add if not present)
    spec["description"] = "SDK test - replaced"

    # Also try to modify numeric values for good measure
    for key in ["timeout", "interval", "idle_timeout", "burst_multiplier", "total_number"]:
        if key in spec and isinstance(spec[key], (int, float)):
            spec[key] = spec[key] + 1
            return

    # Try to modify nested numeric values
    for key, value in spec.items():
        if isinstance(value, dict):
            for subkey in ["timeout", "interval", "burst_multiplier", "total_number"]:
                if subkey in value and isinstance(value[subkey], (int, float)):
                    value[subkey] = value[subkey] + 1
                    return
        elif isinstance(value, list) and value:
            # Try first item in list
            if isinstance(value[0], dict):
                for subkey in ["timeout", "interval", "burst_multiplier", "total_number", "weight", "priority"]:
                    if subkey in value[0] and isinstance(value[0][subkey], (int, float)):
                        value[0][subkey] = value[0][subkey] + 1
                        return


def create_spec_yaml_content(
    resource_name: str,
    spec_data: dict[str, Any],
    is_namespaced: bool = True,
    dependencies: list[str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Create the full YAML spec file content.

    Args:
        resource_name: Name of the resource
        spec_data: Dict with 'create' and 'replace' specs
        is_namespaced: Whether resource is namespace-scoped
        dependencies: List of dependent resource names
        notes: Any notes about the spec

    Returns:
        Complete spec file content ready for YAML serialization
    """
    return {
        "resource": resource_name,
        "is_namespaced": is_namespaced,
        "dependencies": dependencies or [],
        "status": "generated",  # Will be marked 'complete' after tests pass
        "notes": notes or f"Auto-generated from tenant crawl",
        "spec": spec_data,
    }


if __name__ == "__main__":
    # Test the anonymizer
    sample_spec = {
        "metadata": {
            "name": "my-loadbalancer",
            "namespace": "production",
        },
        "spec": {
            "domains": ["app.mycompany.f5demos.com"],
            "default_route_pools": [
                {
                    "pool": {
                        "name": "backend-pool",
                        "namespace": "production",
                        "tenant": "my-tenant-abc123",
                    }
                }
            ],
            "timeout": 30,
            "auto_cert_info": {"should": "be removed"},
        },
    }

    result = extract_spec_for_template(sample_spec, "http_loadbalancer")

    import json
    print("Anonymized spec:")
    print(json.dumps(result, indent=2))
