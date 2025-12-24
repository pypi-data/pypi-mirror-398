#!/usr/bin/env python3
"""Migrate @pytest.mark.order from class level to method level.

This script transforms test classes from:

    @pytest.mark.order(144)
    class TestOriginPool:
        def test_create(self, ...): ...
        def test_get(self, ...): ...
        def test_list(self, ...): ...
        def test_replace(self, ...): ...

To:

    class TestOriginPool:
        @pytest.mark.order(1440)
        def test_create(self, ...): ...
        @pytest.mark.order(1441)
        def test_get(self, ...): ...
        @pytest.mark.order(1442)
        def test_list(self, ...): ...
        @pytest.mark.order(1443)
        def test_replace(self, ...): ...

The order numbers are multiplied by 10 to leave room for future interleaving.
Methods within a class get sequential numbers (base*10, base*10+1, etc.).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Method order within each test class
METHOD_ORDER = ["test_create", "test_get", "test_list", "test_replace"]


def migrate_file(file_path: Path, dry_run: bool = False) -> bool:
    """Migrate a single test file.

    Returns True if file was modified, False otherwise.
    """
    content = file_path.read_text()

    # Find class-level order decorator
    class_order_match = re.search(
        r'^@pytest\.mark\.order\((\d+)\)\s*\nclass (Test\w+)',
        content,
        re.MULTILINE
    )

    if not class_order_match:
        return False

    base_order = int(class_order_match.group(1))
    class_name = class_order_match.group(2)

    # Remove class-level order decorator
    new_content = re.sub(
        r'^@pytest\.mark\.order\(\d+\)\s*\n(class Test\w+)',
        r'\1',
        content,
        flags=re.MULTILINE
    )

    # Add method-level decorators
    # We need to find each def test_X and add the decorator
    for idx, method_name in enumerate(METHOD_ORDER):
        method_order = base_order * 10 + idx

        # Pattern to match the method definition
        # Handles both with and without existing decorators
        pattern = rf'(    )(def {method_name}\(self)'

        # Check if method exists
        if re.search(pattern, new_content):
            replacement = rf'\1@pytest.mark.order({method_order})\n\1\2'
            new_content = re.sub(pattern, replacement, new_content)

    if content == new_content:
        return False

    if dry_run:
        print(f"Would modify: {file_path}")
        print(f"  Class: {class_name}, base order: {base_order}")
        return True

    file_path.write_text(new_content)
    print(f"Modified: {file_path}")
    print(f"  Class: {class_name}, base order: {base_order} -> method orders {base_order*10}-{base_order*10+3}")
    return True


def main() -> int:
    """Run migration on all test files."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate pytest.mark.order to method level")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--file", type=str, help="Migrate a single file instead of all")
    args = parser.parse_args()

    test_dir = Path(__file__).parent.parent / "tests" / "integration"

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(test_dir.glob("test_*.py"))

    modified_count = 0
    for file_path in files:
        if migrate_file(file_path, dry_run=args.dry_run):
            modified_count += 1

    action = "Would modify" if args.dry_run else "Modified"
    print(f"\n{action} {modified_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
