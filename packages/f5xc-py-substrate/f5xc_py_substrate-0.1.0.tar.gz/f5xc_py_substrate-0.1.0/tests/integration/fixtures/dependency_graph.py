"""Dependency graph utilities for test ordering.

This module provides tools for:
1. Building a dependency graph from spec files
2. Topological sorting for proper execution order
3. Generating test order numbers based on dependencies

Usage:
    from tests.integration.fixtures.dependency_graph import (
        build_dependency_graph,
        topological_sort,
        generate_test_orders,
    )

    graph = build_dependency_graph()
    sorted_resources = topological_sort(graph)
    orders = generate_test_orders(sorted_resources)
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

SPECS_DIR = Path(__file__).parent.parent / "specs"


def build_dependency_graph() -> dict[str, list[str]]:
    """Build a dependency graph from spec files.

    Returns a mapping of resource -> list of dependencies.
    Dependencies are resources that must exist BEFORE the resource can be created.

    Example:
        {
            'origin_pool': [],  # no dependencies
            'tcp_loadbalancer': ['origin_pool'],  # depends on origin_pool
            'http_loadbalancer': ['origin_pool'],  # depends on origin_pool
        }
    """
    graph: dict[str, list[str]] = {}

    for spec_file in SPECS_DIR.glob("*.yaml"):
        try:
            spec = yaml.safe_load(spec_file.read_text())
            if not spec:
                continue

            resource = spec.get("resource")
            if not resource:
                continue

            dependencies = spec.get("dependencies", [])
            graph[resource] = dependencies
        except (yaml.YAMLError, OSError):
            # Skip files that can't be parsed
            continue

    return graph


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Topologically sort resources by dependencies.

    Uses Kahn's algorithm to produce a linear ordering where
    dependencies come before dependents.

    Args:
        graph: Mapping of resource -> list of dependencies

    Returns:
        List of resources in dependency order (dependencies first)

    Raises:
        ValueError: If a circular dependency is detected
    """
    # Build in-degree count and adjacency list
    in_degree: dict[str, int] = defaultdict(int)
    adjacency: dict[str, list[str]] = defaultdict(list)

    # Initialize all nodes
    all_nodes = set(graph.keys())
    for node, deps in graph.items():
        for dep in deps:
            # Add unknown dependencies to the graph
            if dep not in graph:
                all_nodes.add(dep)
            adjacency[dep].append(node)
            in_degree[node] += 1

    # Start with nodes that have no dependencies (in_degree = 0)
    queue = [node for node in all_nodes if in_degree[node] == 0]
    queue.sort()  # Alphabetical for deterministic ordering

    result: list[str] = []
    while queue:
        # Take the first node (alphabetically sorted)
        node = queue.pop(0)
        result.append(node)

        # Reduce in-degree for dependent nodes
        for dependent in sorted(adjacency[node]):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
                queue.sort()

    # Check for cycles
    if len(result) != len(all_nodes):
        remaining = all_nodes - set(result)
        raise ValueError(f"Circular dependency detected involving: {remaining}")

    return result


def reverse_topological_sort(graph: dict[str, list[str]]) -> list[str]:
    """Reverse topological sort for delete ordering.

    Returns resources in reverse dependency order - dependents first,
    so they can be deleted before their dependencies.

    Args:
        graph: Mapping of resource -> list of dependencies

    Returns:
        List of resources in reverse dependency order (dependents first)
    """
    return list(reversed(topological_sort(graph)))


def generate_test_orders(
    sorted_resources: list[str],
    base_multiplier: int = 10,
    methods_per_resource: int = 4,
) -> dict[str, dict[str, int]]:
    """Generate test order numbers for each resource.

    Args:
        sorted_resources: Resources in dependency order
        base_multiplier: Multiplier for order spacing (default: 10)
        methods_per_resource: Number of CRUD methods per resource (default: 4)

    Returns:
        Mapping of resource -> {method: order_number}

    Example:
        {
            'origin_pool': {
                'test_create': 1440,
                'test_get': 1441,
                'test_list': 1442,
                'test_replace': 1443,
            },
            'tcp_loadbalancer': {
                'test_create': 1920,
                ...
            },
        }
    """
    method_names = ["test_create", "test_get", "test_list", "test_replace"]
    orders: dict[str, dict[str, int]] = {}

    for idx, resource in enumerate(sorted_resources):
        base_order = (idx + 1) * base_multiplier
        orders[resource] = {}
        for method_idx, method in enumerate(method_names):
            orders[resource][method] = base_order * base_multiplier + method_idx

    return orders


def generate_delete_orders(
    sorted_resources: list[str],
    delete_phase_start: int = 100000,
    base_multiplier: int = 10,
) -> dict[str, int]:
    """Generate delete test order numbers (reverse dependency order).

    Args:
        sorted_resources: Resources in dependency order
        delete_phase_start: Base number for delete phase (default: 100000)
        base_multiplier: Multiplier used for CRUD orders (default: 10)

    Returns:
        Mapping of resource -> delete order number

    Example:
        {
            'tcp_loadbalancer': 98080,  # Deletes first (depends on origin_pool)
            'origin_pool': 98560,       # Deletes second
        }
    """
    orders: dict[str, int] = {}

    for idx, resource in enumerate(sorted_resources):
        # Use same formula as CRUD ordering, but subtract from delete_phase_start
        base_order = (idx + 1) * base_multiplier
        orders[resource] = delete_phase_start - (base_order * base_multiplier)

    return orders


def get_spec_info(resource: str) -> dict[str, Any] | None:
    """Load spec file for a resource.

    Args:
        resource: Resource name

    Returns:
        Parsed spec dict, or None if not found
    """
    spec_file = SPECS_DIR / f"{resource}.yaml"
    if not spec_file.exists():
        return None

    try:
        return yaml.safe_load(spec_file.read_text())
    except (yaml.YAMLError, OSError):
        return None


def get_resources_with_dependencies() -> list[str]:
    """Get list of resources that have dependencies.

    Returns:
        List of resource names that depend on other resources
    """
    graph = build_dependency_graph()
    return [r for r, deps in graph.items() if deps]


def get_dependency_chain(resource: str) -> list[str]:
    """Get full dependency chain for a resource.

    Returns all resources that must be created before this resource,
    in the order they should be created.

    Args:
        resource: Resource name

    Returns:
        List of dependencies in creation order
    """
    graph = build_dependency_graph()
    visited: set[str] = set()
    chain: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        visited.add(node)

        for dep in graph.get(node, []):
            visit(dep)

        chain.append(node)

    visit(resource)

    # Remove the resource itself from the chain
    if chain and chain[-1] == resource:
        chain.pop()

    return chain


if __name__ == "__main__":
    # Example usage
    print("Building dependency graph...")
    graph = build_dependency_graph()

    resources_with_deps = [r for r, deps in graph.items() if deps]
    print(f"\nResources with dependencies ({len(resources_with_deps)}):")
    for resource in sorted(resources_with_deps):
        deps = graph[resource]
        print(f"  {resource}: {deps}")

    print("\nTopological sort:")
    try:
        sorted_resources = topological_sort(graph)
        print(f"  {len(sorted_resources)} resources in dependency order")

        # Show first 10 and last 10
        print("\n  First 10:")
        for r in sorted_resources[:10]:
            print(f"    {r}")
        print("\n  Last 10:")
        for r in sorted_resources[-10:]:
            print(f"    {r}")
    except ValueError as e:
        print(f"  Error: {e}")
