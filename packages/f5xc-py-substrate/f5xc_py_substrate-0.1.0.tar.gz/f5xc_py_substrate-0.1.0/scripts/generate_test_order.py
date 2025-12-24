#!/usr/bin/env python3
"""Generate and update test order values based on dependency graph.

This script:
1. Builds a dependency graph from spec files
2. Topologically sorts resources (dependencies first)
3. Updates @pytest.mark.order() values in test files

Usage:
    # Show what would be updated (dry run)
    python scripts/generate_test_order.py --dry-run

    # Update all test files
    python scripts/generate_test_order.py

    # Update a specific file
    python scripts/generate_test_order.py --file tests/integration/test_origin_pool.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.integration.fixtures.dependency_graph import (
    build_dependency_graph,
    topological_sort,
)

TESTS_DIR = Path(__file__).parent.parent / "tests" / "integration"

# Method names and their order within a resource
CRUD_METHODS = ["test_create", "test_get", "test_list", "test_replace"]
DELETE_METHOD = "test_delete"


def calculate_orders(sorted_resources: list[str], base_multiplier: int = 10) -> dict[str, dict[str, int]]:
    """Calculate order numbers for all resources.

    Args:
        sorted_resources: Resources in dependency order
        base_multiplier: Multiplier for spacing (default: 10)

    Returns:
        Mapping of resource -> {method: order_number}
    """
    orders: dict[str, dict[str, int]] = {}

    for idx, resource in enumerate(sorted_resources):
        # Base order for this resource (1-indexed, multiplied for spacing)
        base = (idx + 1) * base_multiplier * base_multiplier

        orders[resource] = {}

        # CRUD methods get sequential orders starting from base
        for method_idx, method in enumerate(CRUD_METHODS):
            orders[resource][method] = base + method_idx

        # Delete gets reverse order (100000 - base)
        orders[resource][DELETE_METHOD] = 100000 - base

    return orders


def update_test_file(
    file_path: Path,
    orders: dict[str, dict[str, int]],
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    """Update order values in a test file.

    Args:
        file_path: Path to test file
        orders: Mapping of resource -> {method: order_number}
        dry_run: If True, don't write changes

    Returns:
        Tuple of (was_modified, list of changes)
    """
    content = file_path.read_text()
    original_content = content
    changes: list[str] = []

    # Extract resource name from file name
    resource = file_path.stem.replace("test_", "")

    if resource not in orders:
        return False, []

    resource_orders = orders[resource]

    # Update each method's order
    for method, new_order in resource_orders.items():
        # Pattern to find existing order decorator for this method
        pattern = rf'(@pytest\.mark\.order\()(\d+)(\)\s*\n\s*def {method}\()'

        match = re.search(pattern, content)
        if match:
            old_order = int(match.group(2))
            if old_order != new_order:
                content = re.sub(pattern, rf'\g<1>{new_order}\g<3>', content)
                changes.append(f"  {method}: {old_order} -> {new_order}")

    if content == original_content:
        return False, []

    if not dry_run:
        file_path.write_text(content)

    return True, changes


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate and update test order values based on dependency graph"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Update a single file instead of all",
    )
    parser.add_argument(
        "--show-graph",
        action="store_true",
        help="Show dependency graph and calculated orders",
    )
    args = parser.parse_args()

    # Build dependency graph and sort
    print("Building dependency graph...")
    graph = build_dependency_graph()
    sorted_resources = topological_sort(graph)

    print(f"Found {len(sorted_resources)} resources")

    # Show resources with dependencies
    deps_resources = [r for r in sorted_resources if graph.get(r)]
    if deps_resources:
        print(f"\nResources with dependencies ({len(deps_resources)}):")
        for r in deps_resources:
            deps = graph[r]
            r_idx = sorted_resources.index(r)
            deps_indices = [sorted_resources.index(d) for d in deps if d in sorted_resources]
            print(f"  {r} (order {r_idx}): depends on {deps} (orders {deps_indices})")

    # Calculate orders
    orders = calculate_orders(sorted_resources)

    if args.show_graph:
        print("\nCalculated orders (first 10):")
        for r in sorted_resources[:10]:
            o = orders[r]
            print(f"  {r}:")
            print(f"    CRUD: {o['test_create']}-{o['test_replace']}")
            print(f"    delete: {o['test_delete']}")
        print("\nCalculated orders (last 10):")
        for r in sorted_resources[-10:]:
            o = orders[r]
            print(f"  {r}:")
            print(f"    CRUD: {o['test_create']}-{o['test_replace']}")
            print(f"    delete: {o['test_delete']}")
        return 0

    # Get files to update
    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(TESTS_DIR.glob("test_*.py"))

    # Update files
    modified_count = 0
    for file_path in files:
        was_modified, changes = update_test_file(file_path, orders, dry_run=args.dry_run)
        if was_modified:
            modified_count += 1
            action = "Would update" if args.dry_run else "Updated"
            print(f"\n{action}: {file_path.name}")
            for change in changes:
                print(change)

    action = "Would modify" if args.dry_run else "Modified"
    print(f"\n{action} {modified_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
