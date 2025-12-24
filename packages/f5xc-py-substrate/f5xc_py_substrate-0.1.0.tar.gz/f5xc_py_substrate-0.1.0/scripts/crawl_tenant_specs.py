#!/usr/bin/env python3
"""Crawl F5 XC tenant to extract resource configurations for test specs.

This script connects to an F5 XC tenant and extracts real resource
configurations, anonymizes them, and saves as YAML spec templates
for integration tests.

Usage:
    # Discover namespaces with resources
    python scripts/crawl_tenant_specs.py --discover

    # Crawl specific resources from a namespace
    python scripts/crawl_tenant_specs.py --namespace ns1 --resources http_loadbalancer,origin_pool

    # Crawl all failing resources (Tier 1)
    python scripts/crawl_tenant_specs.py --tier1

    # List resources that need specs
    python scripts/crawl_tenant_specs.py --list-needed
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.anonymizer import (
    create_spec_yaml_content,
    extract_spec_for_template,
)

# Paths
SPECS_DIR = PROJECT_ROOT / "tests" / "integration" / "specs"
COVERAGE_FILE = PROJECT_ROOT / "docs" / "test-results" / "coverage.json"

# Default rate limiting
DEFAULT_DELAY = 0.5  # seconds between API calls

# Resources that should NOT be auto-generated (manually maintained or special)
SKIP_RESOURCES = {
    "namespace",  # Special handling
    "healthcheck",  # Already complete
    "origin_pool",  # Already complete
    "http_loadbalancer",  # Already complete
}

# Tier 1: Currently failing resources that are likely easy to fix
TIER1_RESOURCES = [
    "tcp_loadbalancer",
    "udp_loadbalancer",
    "dns_zone",
    "dns_load_balancer",
    "dns_lb_pool",
    "dns_lb_health_check",
    "rate_limiter",
    "virtual_network",
    "virtual_site",
    "token",
    "role",
    "segment",
    "tunnel",
    "route",
    "bgp",
    "bgp_routing_policy",
    "network_connector",
    "network_firewall",
    "network_interface",
    "nat_policy",
    "fleet",
    "cluster",
    "discovery",
    "endpoint",
    "proxy",
    "fast_acl",
    "advertise_policy",
    "alert_policy",
    "alert_template",
]

# Tier 2: Currently skipped resources that might exist in tenants
TIER2_RESOURCES = [
    "alert",
    "api_credential",
    "forward_proxy_policy",
    "known_label",
    "known_label_key",
    "geo_config",
    "bot_allowlist_policy",
    "bot_endpoint_policy",
    "bot_network_policy",
]


def load_client(env_file: str = ".env"):
    """Load the F5 XC client with environment credentials.

    Args:
        env_file: Path to env file for credentials (default: .env)
    """
    load_dotenv(env_file)
    from f5xc_py_substrate import Client

    return Client()


def discover_namespaces_with_resources(
    client,
    resource_type: str = "http_loadbalancer",
    limit: int = 50,
    delay: float = DEFAULT_DELAY,
) -> list[tuple[str, int]]:
    """Discover namespaces that have resources of the given type.

    Returns list of (namespace, count) tuples sorted by count descending.
    """
    namespaces = client.namespace.list()
    results = []

    resource = getattr(client, resource_type, None)
    if not resource:
        print(f"Warning: Resource type '{resource_type}' not found")
        return results

    for ns in namespaces[:limit]:
        try:
            items = resource.list(namespace=ns.name)
            if items:
                results.append((ns.name, len(items)))
            time.sleep(delay)
        except Exception:
            pass  # Skip errors

    return sorted(results, key=lambda x: x[1], reverse=True)


def get_resource_config(
    client,
    resource_type: str,
    namespace: str,
    name: str | None = None,
) -> dict[str, Any] | None:
    """Get a resource configuration from the tenant.

    If name is None, gets the first available resource of that type.
    """
    resource = getattr(client, resource_type, None)
    if not resource:
        return None

    try:
        if name:
            result = resource.get(namespace=namespace, name=name)
        else:
            # List and get the first one
            items = resource.list(namespace=namespace)
            if not items:
                return None
            first_name = items[0].name
            result = resource.get(namespace=namespace, name=first_name)

        # Convert to dict
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return result.__dict__
    except Exception as e:
        print(f"  Error getting {resource_type}: {e}")
        return None


def crawl_resource(
    client,
    resource_type: str,
    namespaces: list[str],
    delay: float = DEFAULT_DELAY,
) -> dict[str, Any] | None:
    """Crawl namespaces to find and extract a resource config.

    Tries each namespace in order until a resource is found.
    """
    for ns in namespaces:
        config = get_resource_config(client, resource_type, ns)
        if config:
            return config
        time.sleep(delay)
    return None


def write_spec_file(
    resource_name: str,
    spec_content: dict[str, Any],
    overwrite: bool = False,
) -> Path | None:
    """Write a spec YAML file.

    Returns the path if written, None if skipped.
    """
    spec_file = SPECS_DIR / f"{resource_name}.yaml"

    # Check if exists and has complete status
    if spec_file.exists() and not overwrite:
        with open(spec_file) as f:
            existing = yaml.safe_load(f)
        if existing and existing.get("status") == "complete":
            print(f"  Skipping {resource_name} (status=complete)")
            return None

    # Ensure directory exists
    SPECS_DIR.mkdir(parents=True, exist_ok=True)

    # Write the file
    with open(spec_file, "w") as f:
        yaml.dump(spec_content, f, default_flow_style=False, sort_keys=False)

    return spec_file


def get_resources_needing_specs() -> dict[str, str]:
    """Get list of resources that need specs based on coverage report.

    Returns dict of resource_name -> status (failing, skipped, partial).
    """
    if not COVERAGE_FILE.exists():
        print(f"Warning: Coverage file not found at {COVERAGE_FILE}")
        return {}

    with open(COVERAGE_FILE) as f:
        coverage = json.load(f)

    resources = coverage.get("resources", {})
    needed = {}

    for name, data in resources.items():
        if name in SKIP_RESOURCES:
            continue

        status = data.get("status", "unknown")
        if status in ("failing", "skipped", "partial"):
            needed[name] = status

    return needed


def crawl_and_save_resources(
    client,
    resources: list[str],
    namespaces: list[str],
    delay: float = DEFAULT_DELAY,
    overwrite: bool = False,
) -> dict[str, str]:
    """Crawl and save specs for multiple resources.

    Returns dict of resource_name -> result (success, skipped, error).
    """
    results = {}

    for resource_type in resources:
        print(f"Crawling {resource_type}...")

        if resource_type in SKIP_RESOURCES:
            print(f"  Skipping (in skip list)")
            results[resource_type] = "skipped"
            continue

        # Try to get a config from one of the namespaces
        config = crawl_resource(client, resource_type, namespaces, delay)

        if not config:
            print(f"  No config found in any namespace")
            results[resource_type] = "not_found"
            continue

        # Extract and anonymize the spec
        spec_data = extract_spec_for_template(config, resource_type)

        if not spec_data.get("create"):
            print(f"  Empty spec extracted")
            results[resource_type] = "empty"
            continue

        # Create full spec content
        spec_content = create_spec_yaml_content(
            resource_name=resource_type,
            spec_data=spec_data,
            is_namespaced=True,
            notes=f"Auto-generated from tenant crawl",
        )

        # Write the file
        path = write_spec_file(resource_type, spec_content, overwrite)
        if path:
            print(f"  Wrote {path.name}")
            results[resource_type] = "success"
        else:
            results[resource_type] = "skipped"

        time.sleep(delay)

    return results


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Crawl F5 XC tenant for test specs"
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover namespaces with resources",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        help="Target namespace(s), comma-separated",
    )
    parser.add_argument(
        "--resources",
        type=str,
        help="Resource types to crawl, comma-separated",
    )
    parser.add_argument(
        "--tier1",
        action="store_true",
        help="Crawl Tier 1 (failing) resources",
    )
    parser.add_argument(
        "--tier2",
        action="store_true",
        help="Crawl Tier 2 (skipped) resources",
    )
    parser.add_argument(
        "--list-needed",
        action="store_true",
        help="List resources that need specs",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Delay between API calls (default: {DEFAULT_DELAY}s)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing specs (even if complete)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max namespaces to scan for discovery",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to env file for credentials (default: .env)",
    )

    args = parser.parse_args()

    if args.list_needed:
        needed = get_resources_needing_specs()
        if not needed:
            print("No resources need specs (or coverage file not found)")
            return 0

        print(f"Resources needing specs: {len(needed)}")
        for status in ["failing", "partial", "skipped"]:
            items = [k for k, v in needed.items() if v == status]
            if items:
                print(f"\n{status.upper()} ({len(items)}):")
                for name in sorted(items):
                    print(f"  - {name}")
        return 0

    # Load client
    print(f"Connecting to F5 XC tenant (using {args.env_file})...")
    try:
        client = load_client(args.env_file)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return 1

    if args.discover:
        print("Discovering namespaces with resources...")
        results = discover_namespaces_with_resources(
            client,
            limit=args.limit,
            delay=args.delay,
        )
        print(f"\nNamespaces with http_loadbalancers:")
        for ns, count in results[:20]:
            print(f"  {ns}: {count}")
        return 0

    # Determine namespaces to crawl
    if args.namespace:
        namespaces = [n.strip() for n in args.namespace.split(",")]
    else:
        # Use discovery to find good namespaces
        print("Discovering namespaces...")
        discovered = discover_namespaces_with_resources(client, limit=30, delay=0.3)
        namespaces = [ns for ns, _ in discovered[:10]]
        if not namespaces:
            print("No namespaces with resources found")
            return 1
        print(f"Using namespaces: {', '.join(namespaces[:5])}...")

    # Determine resources to crawl
    if args.resources:
        resources = [r.strip() for r in args.resources.split(",")]
    elif args.tier1:
        resources = TIER1_RESOURCES
    elif args.tier2:
        resources = TIER2_RESOURCES
    else:
        parser.print_help()
        return 1

    print(f"\nCrawling {len(resources)} resources from {len(namespaces)} namespaces...")
    results = crawl_and_save_resources(
        client,
        resources,
        namespaces,
        delay=args.delay,
        overwrite=args.overwrite,
    )

    # Summary
    success = sum(1 for v in results.values() if v == "success")
    not_found = sum(1 for v in results.values() if v == "not_found")
    skipped = sum(1 for v in results.values() if v == "skipped")
    errors = sum(1 for v in results.values() if v not in ("success", "not_found", "skipped"))

    print(f"\nSummary: {success} written, {not_found} not found, {skipped} skipped, {errors} errors")

    return 0


if __name__ == "__main__":
    sys.exit(main())
