#!/usr/bin/env python3
"""Analyze crawled resources to discover dependencies.

This script analyzes crawled resource data to discover dependencies by
examining ObjectRefType references (dicts with name+namespace fields).

Usage:
    # Analyze all crawled data
    python scripts/dependency_analyzer.py

    # Analyze specific resource
    python scripts/dependency_analyzer.py --resource http_loadbalancer

    # Show verbose output
    python scripts/dependency_analyzer.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Paths
DATA_DIR = PROJECT_ROOT / "data"
CRAWLED_DIR = DATA_DIR / "crawled"
SPECS_DIR = PROJECT_ROOT / "tests" / "integration" / "specs"
DEPENDENCIES_OUTPUT = DATA_DIR / "discovered_dependencies.yaml"

# Reference patterns: field name -> target resource type
# When we see a dict with {name, namespace} under this key, it references this resource
REFERENCE_PATTERNS = {
    # Direct references
    "pool": "origin_pool",
    "healthcheck": "healthcheck",
    "certificate": "certificate",
    "site": "site",
    "virtual_site": "virtual_site",
    "origin_pool": "origin_pool",
    "origin_pools": "origin_pool",
    "fallback_pool": "dns_lb_pool",
    "waf": "app_firewall",
    "app_firewall": "app_firewall",
    "rate_limiter": "rate_limiter",
    "rate_limiter_policy": "rate_limiter_policy",
    "user_identification": "user_identification",
    "malicious_user_mitigation": "malicious_user_mitigation",
    "ip_prefix_set": "ip_prefix_set",
    "dns_zone": "dns_zone",
    "cdn_cache_rules": "cdn_cache_rule",
    "service_policy": "service_policy",
    "service_policy_set": "service_policy_set",
    "forward_proxy_policy": "forward_proxy_policy",
    "network_policy": "network_policy",
    "network_policy_set": "network_policy_set",
    "trusted_ca_list": "trusted_ca_list",
    "segment": "segment",
    "dc_cluster_group": "dc_cluster_group",
    "virtual_network": "virtual_network",
    "fleet": "fleet",
    "voltstack_site": "voltstack_site",
    "tls_parameters": "certificate",  # TLS params often reference certs
    "secret_info": "secret_policy",
    "blindfold_secret_info": "secret_policy",
}

# Nested patterns: (parent_key, child_key, target_resource)
# For nested structures like origin_pools_weights[].pool
NESTED_PATTERNS = [
    ("origin_pools_weights", "pool", "origin_pool"),
    ("default_route_pools", "pool", "origin_pool"),
    ("routes", "origin_pools", "origin_pool"),
    ("origin_servers", "site", "site"),
    ("origin_servers", "virtual_site", "virtual_site"),
    ("advertise_on_public", "virtual_site", "virtual_site"),
    ("cluster", "site", "site"),
]


class DependencyAnalyzer:
    """Analyze crawled resources for dependency discovery."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.discovered: dict[str, set[str]] = defaultdict(set)
        self.reference_details: dict[str, list[dict]] = defaultdict(list)

    def is_object_ref(self, obj: Any) -> bool:
        """Check if an object looks like an ObjectRefType reference."""
        if not isinstance(obj, dict):
            return False
        # ObjectRefType has name and namespace (and sometimes tenant)
        return "name" in obj and ("namespace" in obj or "tenant" in obj)

    def infer_reference_type(self, key: str, parent_key: str | None = None) -> str | None:
        """Infer the resource type from a reference key."""
        # Check nested patterns first
        if parent_key:
            for p_key, c_key, target in NESTED_PATTERNS:
                if parent_key == p_key and key == c_key:
                    return target

        # Check direct patterns
        return REFERENCE_PATTERNS.get(key)

    def analyze_object(
        self,
        obj: Any,
        resource_type: str,
        path: str = "",
        parent_key: str | None = None,
    ) -> None:
        """Recursively analyze an object for references."""
        if isinstance(obj, dict):
            # Check if this dict is an ObjectRefType
            if self.is_object_ref(obj):
                # Get the key that led us here
                key = path.split(".")[-1] if "." in path else path
                ref_type = self.infer_reference_type(key, parent_key)

                if ref_type and ref_type != resource_type:
                    self.discovered[resource_type].add(ref_type)
                    self.reference_details[resource_type].append({
                        "path": path,
                        "key": key,
                        "target": ref_type,
                        "ref_name": obj.get("name"),
                        "ref_namespace": obj.get("namespace"),
                    })
                    if self.verbose:
                        print(f"  Found reference: {path} -> {ref_type}")

            # Recurse into dict values
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                current_key = path.split(".")[-1] if path else None
                self.analyze_object(value, resource_type, new_path, current_key)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                current_key = path.split(".")[-1] if path else None
                self.analyze_object(item, resource_type, new_path, current_key)

    def analyze_resource(self, resource_type: str) -> set[str]:
        """Analyze a single resource type from crawled data."""
        resource_dir = CRAWLED_DIR / resource_type
        if not resource_dir.exists():
            return set()

        dependencies = set()

        for json_file in resource_dir.glob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)

                # Focus on the spec section
                spec = data.get("spec", {})
                self.analyze_object(spec, resource_type, "spec")

                dependencies = self.discovered[resource_type]
            except (json.JSONDecodeError, OSError) as e:
                if self.verbose:
                    print(f"  Error reading {json_file}: {e}")

        return dependencies

    def analyze_all(self) -> dict[str, set[str]]:
        """Analyze all crawled resources."""
        if not CRAWLED_DIR.exists():
            print(f"Crawled data directory not found: {CRAWLED_DIR}")
            return {}

        resources = sorted([d.name for d in CRAWLED_DIR.iterdir() if d.is_dir()])
        print(f"Analyzing {len(resources)} crawled resources...")

        for resource_type in resources:
            if self.verbose:
                print(f"\nAnalyzing {resource_type}...")
            self.analyze_resource(resource_type)

        return self.discovered

    def get_results(self) -> dict[str, Any]:
        """Get analysis results in a structured format."""
        results = {
            "generated_at": datetime.now().isoformat(),
            "total_resources": len(self.discovered),
            "resources_with_deps": sum(1 for deps in self.discovered.values() if deps),
            "resources": {},
        }

        for resource_type in sorted(self.discovered.keys()):
            deps = sorted(self.discovered[resource_type])
            details = self.reference_details.get(resource_type, [])

            results["resources"][resource_type] = {
                "dependencies": deps,
                "reference_count": len(details),
            }

            if details:
                results["resources"][resource_type]["references"] = [
                    {"path": d["path"], "target": d["target"]}
                    for d in details[:5]  # Limit to first 5 for readability
                ]

        return results

    def save_results(self) -> Path:
        """Save results to YAML file."""
        results = self.get_results()

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEPENDENCIES_OUTPUT, "w") as f:
            yaml.dump(results, f, default_flow_style=False, sort_keys=False)

        return DEPENDENCIES_OUTPUT


def update_spec_dependencies(
    dependencies: dict[str, set[str]],
    dry_run: bool = False,
) -> dict[str, str]:
    """Update spec YAML files with discovered dependencies.

    Returns dict of resource -> result (updated, skipped, not_found).
    """
    results = {}

    for resource_type, deps in dependencies.items():
        spec_file = SPECS_DIR / f"{resource_type}.yaml"

        if not spec_file.exists():
            results[resource_type] = "no_spec"
            continue

        try:
            with open(spec_file) as f:
                spec = yaml.safe_load(f) or {}

            # Get existing dependencies
            existing_deps = set(spec.get("dependencies", []))

            # Merge with discovered
            new_deps = sorted(existing_deps | deps)

            if set(new_deps) == existing_deps:
                results[resource_type] = "unchanged"
                continue

            # Update spec
            spec["dependencies"] = new_deps

            if not dry_run:
                with open(spec_file, "w") as f:
                    yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

            results[resource_type] = "updated"
            print(f"  {resource_type}: added {deps - existing_deps}")

        except Exception as e:
            results[resource_type] = f"error: {e}"

    return results


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze crawled resources for dependencies"
    )
    parser.add_argument(
        "--resource",
        type=str,
        help="Analyze specific resource",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--update-specs",
        action="store_true",
        help="Update spec YAML files with discovered dependencies",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    analyzer = DependencyAnalyzer(verbose=args.verbose)

    if args.resource:
        print(f"Analyzing {args.resource}...")
        deps = analyzer.analyze_resource(args.resource)
        if deps:
            print(f"\nDependencies for {args.resource}:")
            for dep in sorted(deps):
                print(f"  - {dep}")
        else:
            print("No dependencies found")
        return 0

    # Analyze all
    discovered = analyzer.analyze_all()

    # Print summary
    resources_with_deps = [(r, d) for r, d in discovered.items() if d]
    print(f"\n{'=' * 50}")
    print(f"Dependency Analysis Complete")
    print(f"{'=' * 50}")
    print(f"Total resources analyzed: {len(discovered)}")
    print(f"Resources with dependencies: {len(resources_with_deps)}")

    if resources_with_deps:
        print(f"\nDependencies discovered:")
        for resource, deps in sorted(resources_with_deps):
            print(f"  {resource}: {', '.join(sorted(deps))}")

    # Save results
    output_path = analyzer.save_results()
    print(f"\nResults saved to: {output_path}")

    # Update specs if requested
    if args.update_specs:
        print(f"\nUpdating spec files...")
        results = update_spec_dependencies(discovered, dry_run=args.dry_run)

        updated = sum(1 for v in results.values() if v == "updated")
        unchanged = sum(1 for v in results.values() if v == "unchanged")
        no_spec = sum(1 for v in results.values() if v == "no_spec")

        action = "Would update" if args.dry_run else "Updated"
        print(f"\n{action}: {updated}, Unchanged: {unchanged}, No spec: {no_spec}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
