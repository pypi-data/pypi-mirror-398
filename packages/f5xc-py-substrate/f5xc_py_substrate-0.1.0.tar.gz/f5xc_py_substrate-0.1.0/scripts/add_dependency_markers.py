#!/usr/bin/env python3
"""Add pytest-dependency markers to test files.

This script:
1. Adds @pytest.mark.dependency(name="test_create") to test_create methods
2. Adds @pytest.mark.dependency(depends=["test_create"]) to test_delete methods

This ensures test_delete is skipped when test_create fails.

Usage:
    # Show what would be updated (dry run)
    python scripts/add_dependency_markers.py --dry-run

    # Update all test files
    python scripts/add_dependency_markers.py

    # Update a specific file
    python scripts/add_dependency_markers.py --file tests/integration/test_origin_pool.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent.parent / "tests" / "integration"


def add_dependency_markers(
    file_path: Path,
    dry_run: bool = False,
) -> tuple[bool, list[str]]:
    """Add dependency markers to a test file.

    Args:
        file_path: Path to test file
        dry_run: If True, don't write changes

    Returns:
        Tuple of (was_modified, list of changes)
    """
    content = file_path.read_text()
    original_content = content
    changes: list[str] = []

    # Skip namespace test - it doesn't have test_create
    if file_path.name == "test_namespace.py":
        return False, []

    # Pattern 1: Add dependency marker to test_create
    # Match: @pytest.mark.order(N)\n    def test_create(
    # But NOT if already has @pytest.mark.dependency
    create_pattern = r'(@pytest\.mark\.order\(\d+\)\n)(\s*def test_create\()'

    def replace_create(match: re.Match) -> str:
        order_line = match.group(1)
        def_line = match.group(2)
        indent = re.match(r'\s*', def_line).group()
        return f'{order_line}{indent}@pytest.mark.dependency(name="test_create")\n{def_line}'

    # Check if already has dependency marker for test_create
    if '@pytest.mark.dependency(name="test_create")' not in content:
        new_content = re.sub(create_pattern, replace_create, content)
        if new_content != content:
            content = new_content
            changes.append("  Added @pytest.mark.dependency(name=\"test_create\")")

    # Pattern 2: Add dependency marker to test_delete
    # Match: @pytest.mark.order(N)\n    def test_delete(
    # But NOT if already has @pytest.mark.dependency
    delete_pattern = r'(@pytest\.mark\.order\(\d+\)\n)(\s*def test_delete\()'

    def replace_delete(match: re.Match) -> str:
        order_line = match.group(1)
        def_line = match.group(2)
        indent = re.match(r'\s*', def_line).group()
        return f'{order_line}{indent}@pytest.mark.dependency(depends=["test_create"])\n{def_line}'

    # Check if already has dependency marker for test_delete
    if '@pytest.mark.dependency(depends=["test_create"])' not in content:
        new_content = re.sub(delete_pattern, replace_delete, content)
        if new_content != content:
            content = new_content
            changes.append("  Added @pytest.mark.dependency(depends=[\"test_create\"])")

    if content == original_content:
        return False, []

    if not dry_run:
        file_path.write_text(content)

    return True, changes


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add pytest-dependency markers to test files"
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
    args = parser.parse_args()

    # Get files to update
    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(TESTS_DIR.glob("test_*.py"))

    # Update files
    modified_count = 0
    for file_path in files:
        was_modified, changes = add_dependency_markers(file_path, dry_run=args.dry_run)
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
