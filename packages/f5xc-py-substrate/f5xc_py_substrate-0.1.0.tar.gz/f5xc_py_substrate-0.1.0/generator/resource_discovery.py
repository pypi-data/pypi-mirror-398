"""Discover resources and determine test ordering."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml


def discover_namespaced_resources(resources_dir: Path) -> list[str]:
    """Find all namespaced resources by checking API paths.

    A resource is considered namespaced if it has paths containing
    '/namespaces/{namespace}/' or '/namespaces/{metadata.namespace}/'.

    Args:
        resources_dir: Path to the resources directory.

    Returns:
        Sorted list of namespaced resource names.
    """
    namespaced = []

    for resource_dir in resources_dir.iterdir():
        if not resource_dir.is_dir() or resource_dir.name.startswith("_"):
            continue

        resource_py = resource_dir / "resource.py"
        if not resource_py.exists():
            continue

        content = resource_py.read_text()

        # Check for namespaced path pattern
        if re.search(r"/namespaces/\{", content):
            namespaced.append(resource_dir.name)

    return sorted(namespaced)


def discover_all_resources(resources_dir: Path) -> list[str]:
    """Find all resources in the resources directory.

    Args:
        resources_dir: Path to the resources directory.

    Returns:
        Sorted list of all resource names.
    """
    resources = []

    for resource_dir in resources_dir.iterdir():
        if not resource_dir.is_dir() or resource_dir.name.startswith("_"):
            continue

        resource_py = resource_dir / "resource.py"
        if resource_py.exists():
            resources.append(resource_dir.name)

    return sorted(resources)


def build_dependency_order(
    resources: list[str],
    specs_dir: Path,
) -> list[str]:
    """Order resources by dependencies using topological sort.

    Resources with dependencies are ordered after their dependencies.
    Resources without specs are placed at the end.

    Args:
        resources: List of resource names to order.
        specs_dir: Path to the specs directory containing YAML files.

    Returns:
        Ordered list of resource names.
    """
    # Load dependencies from spec files
    deps: dict[str, list[str]] = defaultdict(list)
    for resource in resources:
        spec_file = specs_dir / f"{resource}.yaml"
        if spec_file.exists():
            data = yaml.safe_load(spec_file.read_text())
            deps[resource] = data.get("dependencies", [])
        else:
            deps[resource] = []

    # Topological sort using Kahn's algorithm
    # Count incoming edges
    in_degree: dict[str, int] = {r: 0 for r in resources}
    for resource in resources:
        for dep in deps.get(resource, []):
            if dep in in_degree:
                in_degree[resource] += 1

    # Start with nodes that have no dependencies
    queue = [r for r in resources if in_degree[r] == 0]
    queue.sort()  # Alphabetical for determinism
    result = []

    while queue:
        resource = queue.pop(0)
        result.append(resource)

        # Reduce in-degree for dependents
        for other in resources:
            if resource in deps.get(other, []):
                in_degree[other] -= 1
                if in_degree[other] == 0:
                    # Insert in sorted order for determinism
                    queue.append(other)
                    queue.sort()

    # Add any remaining resources (circular deps or missing deps)
    remaining = [r for r in resources if r not in result]
    remaining.sort()
    result.extend(remaining)

    return result


def get_resource_methods(resource_dir: Path) -> list[str]:
    """Extract available method names from a resource.py file.

    Args:
        resource_dir: Path to the resource directory.

    Returns:
        List of method names (e.g., ['create', 'get', 'list', 'replace', 'delete']).
    """
    resource_py = resource_dir / "resource.py"
    if not resource_py.exists():
        return []

    content = resource_py.read_text()

    # Find method definitions
    methods = []
    for match in re.finditer(r"def (\w+)\(self,", content):
        method_name = match.group(1)
        if not method_name.startswith("_"):
            methods.append(method_name)

    return methods


if __name__ == "__main__":
    # Quick test
    import sys

    project_root = Path(__file__).parent.parent
    resources_dir = project_root / "f5xc_py_substrate" / "resources"

    all_resources = discover_all_resources(resources_dir)
    namespaced = discover_namespaced_resources(resources_dir)

    print(f"Total resources: {len(all_resources)}")
    print(f"Namespaced resources: {len(namespaced)}")
    print(f"Non-namespaced: {len(all_resources) - len(namespaced)}")

    if "--list" in sys.argv:
        print("\nNamespaced resources:")
        for r in namespaced:
            print(f"  {r}")
