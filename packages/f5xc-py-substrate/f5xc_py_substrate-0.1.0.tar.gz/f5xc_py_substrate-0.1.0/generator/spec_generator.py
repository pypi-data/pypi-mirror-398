#!/usr/bin/env python3
"""Generate YAML spec files by extracting examples from F5 API documentation.

This script:
1. Extracts example URLs from OAS files in generator/.oas_cache/
2. Fetches example JSON payloads from the F5 documentation pages
3. Anonymizes the data and transforms to YAML spec format
4. Preserves existing dependencies from prior analysis
5. Writes to tests/integration/specs/{resource}.yaml

Usage:
    python generator/spec_generator.py --all              # Generate all specs
    python generator/spec_generator.py --resource foo    # Generate one spec
    python generator/spec_generator.py --list            # List resources with examples
    python generator/spec_generator.py --dry-run         # Show what would be generated
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OAS_CACHE_DIR = PROJECT_ROOT / "generator" / ".oas_cache"
SPECS_DIR = PROJECT_ROOT / "tests" / "integration" / "specs"

# Add scripts to path for anonymizer import
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.anonymizer import anonymize_spec

# Resources that have API doc examples but need special handling
# These still get data generated but are marked with status: blocked
# Format: resource_name -> reason
BLOCKED_RESOURCES: dict[str, str] = {
    "namespace": "Create handled by test_namespace fixture",
}


def load_existing_dependencies(resource_name: str) -> list[str]:
    """Load existing dependencies from spec file if present."""
    spec_file = SPECS_DIR / f"{resource_name}.yaml"
    if spec_file.exists():
        try:
            with open(spec_file) as f:
                existing = yaml.safe_load(f) or {}
            return existing.get("dependencies", [])
        except Exception:
            pass
    return []


def create_replace_variation(spec: dict[str, Any]) -> dict[str, Any]:
    """Create a variation of the spec for replace/update testing.

    Modifies description and numeric values to verify updates work.
    """
    from copy import deepcopy
    replace_spec = deepcopy(spec)

    # Always set description to indicate replacement
    replace_spec["description"] = "SDK test - replaced"

    # Try to modify numeric values
    for key in ["timeout", "interval", "idle_timeout", "burst_multiplier", "total_number"]:
        if key in replace_spec and isinstance(replace_spec[key], (int, float)):
            replace_spec[key] = replace_spec[key] + 1
            return replace_spec

    # Try nested values
    for key, value in replace_spec.items():
        if isinstance(value, dict):
            for subkey in ["timeout", "interval", "burst_multiplier"]:
                if subkey in value and isinstance(value[subkey], (int, float)):
                    value[subkey] = value[subkey] + 1
                    return replace_spec
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            for subkey in ["timeout", "weight", "priority"]:
                if subkey in value[0] and isinstance(value[0][subkey], (int, float)):
                    value[0][subkey] = value[0][subkey] + 1
                    return replace_spec

    return replace_spec


@dataclass
class ResourceExamples:
    """Example URLs for a resource."""

    resource_name: str
    module_path: str
    create_url: str | None = None
    replace_url: str | None = None
    is_namespaced: bool = True


def extract_example_urls() -> dict[str, ResourceExamples]:
    """Extract example URLs from all OAS files."""
    resources: dict[str, ResourceExamples] = {}

    for oas_file in sorted(OAS_CACHE_DIR.glob("*.json")):
        with open(oas_file) as f:
            oas = json.load(f)

        # Get resource info from title
        title = oas.get("info", {}).get("title", "")
        if "for ves.io.schema" not in title:
            continue

        module_path = title.split("for ")[-1]
        resource_name = module_path.split(".")[-1]


        # Check if namespaced by looking at paths
        paths = oas.get("paths", {})
        is_namespaced = any("/namespaces/{" in path for path in paths)

        if not is_namespaced:
            continue

        # Extract example URLs
        create_url = None
        replace_url = None

        for path, path_item in paths.items():
            for method in ["post", "put"]:
                if method not in path_item:
                    continue
                op = path_item[method]
                op_id = op.get("operationId", "")
                ext_docs = op.get("externalDocs", {})
                url = ext_docs.get("url", "")

                if "API.Create" in op_id and url:
                    create_url = url
                elif "API.Replace" in op_id and url:
                    replace_url = url

        if create_url or replace_url:
            resources[resource_name] = ResourceExamples(
                resource_name=resource_name,
                module_path=module_path,
                create_url=create_url,
                replace_url=replace_url,
                is_namespaced=is_namespaced,
            )

    return resources


def fetch_example_json(url: str) -> dict[str, Any] | None:
    """Fetch and parse example JSON from an F5 docs page.

    The doc pages contain JSON examples in HTML code blocks with HTML entities.
    Example: <code>{ &quot;metadata&quot;: { &quot;name&quot;: ... }, &quot;spec&quot;: { ... } }</code>
    """
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            html = response.text

        # The JSON examples are in <code> blocks with HTML entities like &quot;
        # Find code blocks containing the JSON example
        code_pattern = r'<code[^>]*>\s*\{[^<]*&quot;metadata&quot;[^<]*&quot;spec&quot;[^<]*\}\s*</code>'
        matches = re.findall(code_pattern, html, re.DOTALL)

        for match in matches:
            try:
                # Extract just the JSON part (between <code> and </code>)
                json_text = re.sub(r'</?code[^>]*>', '', match).strip()

                # Decode HTML entities
                json_text = json_text.replace("&quot;", '"')
                json_text = json_text.replace("&amp;", "&")
                json_text = json_text.replace("&lt;", "<")
                json_text = json_text.replace("&gt;", ">")
                json_text = json_text.replace("&apos;", "'")
                json_text = json_text.replace("&#39;", "'")

                data = json.loads(json_text)
                if "spec" in data and "metadata" in data:
                    return data
            except json.JSONDecodeError:
                continue

        # Alternative: Find the RequestJSON section and extract the following code block
        req_json_idx = html.find("RequestJSON")
        if req_json_idx >= 0:
            # Look for the next <code> block after RequestJSON
            search_area = html[req_json_idx:req_json_idx + 5000]
            code_match = re.search(r'<code[^>]*>([^<]+)</code>', search_area, re.DOTALL)
            if code_match:
                try:
                    json_text = code_match.group(1).strip()
                    # Decode HTML entities
                    json_text = json_text.replace("&quot;", '"')
                    json_text = json_text.replace("&amp;", "&")
                    json_text = json_text.replace("&lt;", "<")
                    json_text = json_text.replace("&gt;", ">")

                    data = json.loads(json_text)
                    if "spec" in data:
                        return data
                except json.JSONDecodeError:
                    pass

        return None

    except httpx.HTTPError as e:
        print(f"  HTTP error fetching {url}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}", file=sys.stderr)
        return None


def transform_to_yaml_spec(
    resource: ResourceExamples,
    create_json: dict[str, Any] | None,
    replace_json: dict[str, Any] | None,
) -> dict[str, Any]:
    """Transform example JSON to YAML spec format with anonymization."""
    # Load existing dependencies to preserve them
    existing_deps = load_existing_dependencies(resource.resource_name)

    # Determine status based on blocked list and data availability
    blocked_reason = BLOCKED_RESOURCES.get(resource.resource_name)

    spec_data: dict[str, Any] = {
        "resource": resource.resource_name,
        "is_namespaced": resource.is_namespaced,
        "dependencies": existing_deps,
        "status": "blocked" if blocked_reason else "generated",
        "notes": blocked_reason if blocked_reason else "Auto-generated from API docs",
        "spec": {"create": None, "replace": None},
    }

    if create_json and "spec" in create_json:
        # Anonymize the create spec
        raw_spec = create_json["spec"]
        anonymized_spec = anonymize_spec(raw_spec, resource.resource_name)
        spec_data["spec"]["create"] = anonymized_spec

        # Create replace variation from anonymized spec
        spec_data["spec"]["replace"] = create_replace_variation(anonymized_spec)
    else:
        if not blocked_reason:
            spec_data["status"] = "missing"
            spec_data["notes"] = "Could not extract create example from API docs"

    # If we have a dedicated replace example, use it (anonymized)
    if replace_json and "spec" in replace_json:
        replace_raw = replace_json["spec"]
        replace_anon = anonymize_spec(replace_raw, resource.resource_name)
        # Merge with our variation logic
        replace_anon["description"] = "SDK test - replaced"
        spec_data["spec"]["replace"] = replace_anon

    return spec_data


def write_spec_file(resource_name: str, spec_data: dict[str, Any]) -> Path:
    """Write YAML spec file."""
    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    spec_file = SPECS_DIR / f"{resource_name}.yaml"

    # Custom YAML representer for None values
    def represent_none(dumper: yaml.Dumper, data: None) -> yaml.Node:
        return dumper.represent_scalar("tag:yaml.org,2002:null", "null")

    yaml.add_representer(type(None), represent_none)

    with open(spec_file, "w") as f:
        yaml.dump(spec_data, f, default_flow_style=False, sort_keys=False)

    return spec_file


def generate_spec(resource: ResourceExamples, dry_run: bool = False) -> bool:
    """Generate spec for a single resource."""
    print(f"Processing {resource.resource_name}...")

    create_json = None
    replace_json = None

    if resource.create_url:
        print(f"  Fetching create example...")
        create_json = fetch_example_json(resource.create_url)
        if create_json:
            print(f"  Found create example with spec keys: {list(create_json.get('spec', {}).keys())[:5]}...")
        else:
            print(f"  Could not parse create example")

    if resource.replace_url:
        print(f"  Fetching replace example...")
        replace_json = fetch_example_json(resource.replace_url)
        if replace_json:
            print(f"  Found replace example")
        else:
            print(f"  Could not parse replace example")

    spec_data = transform_to_yaml_spec(resource, create_json, replace_json)

    if dry_run:
        print(f"  Would write to tests/integration/specs/{resource.resource_name}.yaml")
        print(f"  Status: {spec_data['status']}")
        return spec_data["status"] != "missing"

    spec_file = write_spec_file(resource.resource_name, spec_data)
    print(f"  Wrote {spec_file.relative_to(PROJECT_ROOT)}")
    return spec_data["status"] != "missing"


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate YAML specs from API docs")
    parser.add_argument("--all", action="store_true", help="Generate specs for all resources")
    parser.add_argument("--resource", type=str, help="Generate spec for specific resource")
    parser.add_argument("--list", action="store_true", help="List resources with examples")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--skip-existing", action="store_true", help="Skip resources with existing specs")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between requests (seconds)")

    args = parser.parse_args()

    if not any([args.all, args.resource, args.list]):
        parser.print_help()
        return 1

    # Extract example URLs from OAS files
    print("Extracting example URLs from OAS files...")
    resources = extract_example_urls()
    print(f"Found {len(resources)} resources with example URLs")

    if args.list:
        print("\nResources with example URLs:")
        for name, res in sorted(resources.items()):
            has_create = "✓" if res.create_url else "✗"
            has_replace = "✓" if res.replace_url else "✗"
            print(f"  {name}: create={has_create} replace={has_replace}")
        return 0

    if args.resource:
        if args.resource not in resources:
            print(f"Resource '{args.resource}' not found or has no example URLs")
            return 1
        success = generate_spec(resources[args.resource], dry_run=args.dry_run)
        return 0 if success else 1

    if args.all:
        success_count = 0
        skip_count = 0
        fail_count = 0
        blocked_count = 0

        for name, resource in sorted(resources.items()):
            # Check if spec already exists
            if args.skip_existing:
                spec_file = SPECS_DIR / f"{name}.yaml"
                if spec_file.exists():
                    print(f"Skipping {name} (spec exists)")
                    skip_count += 1
                    continue

            # Track blocked resources
            if name in BLOCKED_RESOURCES:
                blocked_count += 1

            if generate_spec(resource, dry_run=args.dry_run):
                success_count += 1
            else:
                fail_count += 1

            # Rate limiting
            if not args.dry_run and args.delay > 0:
                time.sleep(args.delay)

        print(f"\nSummary: {success_count} generated, {fail_count} failed, {skip_count} skipped, {blocked_count} blocked")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
