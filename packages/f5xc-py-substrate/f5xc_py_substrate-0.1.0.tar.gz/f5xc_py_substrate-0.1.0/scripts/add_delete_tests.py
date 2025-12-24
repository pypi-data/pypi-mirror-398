#!/usr/bin/env python3
"""Add test_delete methods to integration test classes.

This script adds a test_delete method to each test class that:
1. Deletes the resource created during test_create
2. Uses a high order number (reverse dependency order - dependents delete first)
3. Skips for non-namespaced resources (only namespace itself)

Delete order calculation:
- CRUD tests use order base*10 to base*10+3
- Delete tests use 100000 - base*10 (reverse order)
- This ensures dependents (higher base order) delete before dependencies (lower base order)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

SPECS_DIR = Path(__file__).parent.parent / "tests" / "integration" / "specs"
TESTS_DIR = Path(__file__).parent.parent / "tests" / "integration"

# Template for namespaced resource delete test
DELETE_TEST_TEMPLATE = '''

    @pytest.mark.order({order})
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the {resource}."""
        client.{resource_attr}.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.{resource_attr}.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
'''

# Template for non-namespaced resource (skip)
DELETE_TEST_SKIP_TEMPLATE = '''
    @pytest.mark.order({order})
    @pytest.mark.skip(reason="Non-namespaced resource - delete testing skipped for safety")
    def test_delete(self, client: Client) -> None:
        """Test deleting the {resource} - SKIPPED for safety."""
        pass
'''


def get_spec_info(resource_name: str) -> dict | None:
    """Load spec file and return info."""
    spec_file = SPECS_DIR / f"{resource_name}.yaml"
    if not spec_file.exists():
        return None
    return yaml.safe_load(spec_file.read_text())


def get_base_order(content: str) -> int | None:
    """Extract base order from the first @pytest.mark.order in file."""
    match = re.search(r'@pytest\.mark\.order\((\d+)\)', content)
    if match:
        return int(match.group(1)) // 10  # Convert back to base order
    return None


def resource_name_from_test_file(test_file: Path) -> str:
    """Extract resource name from test file name."""
    # test_origin_pool.py -> origin_pool
    return test_file.stem.replace("test_", "")


def add_delete_test(file_path: Path, dry_run: bool = False) -> bool:
    """Add test_delete method to a test file.

    Returns True if file was modified, False otherwise.
    """
    content = file_path.read_text()

    # Skip if already has test_delete
    if "def test_delete(" in content:
        return False

    resource_name = resource_name_from_test_file(file_path)
    spec = get_spec_info(resource_name)

    if not spec:
        # No spec file found, skip
        return False

    base_order = get_base_order(content)
    if base_order is None:
        # No order found, skip
        return False

    is_namespaced = spec.get("is_namespaced", True)

    # Calculate delete order: 100000 - base*10 (reverse order)
    delete_order = 100000 - (base_order * 10)

    # Use resource name as attribute (replace _ with nothing for attr access)
    resource_attr = resource_name

    if is_namespaced:
        delete_test = DELETE_TEST_TEMPLATE.format(
            order=delete_order,
            resource=resource_name,
            resource_attr=resource_attr,
        )
    else:
        delete_test = DELETE_TEST_SKIP_TEMPLATE.format(
            order=delete_order,
            resource=resource_name,
        )

    # Find the end of the class (last method's end) and append
    # Look for the last method in the class
    # Pattern: find the last "        assert" or "        updated" or similar
    # and add after the next blank line or end of file

    # Simpler approach: append before the final newlines
    content = content.rstrip()
    new_content = content + delete_test

    if dry_run:
        print(f"Would modify: {file_path}")
        print(f"  Resource: {resource_name}")
        print(f"  Base order: {base_order}, Delete order: {delete_order}")
        print(f"  Namespaced: {is_namespaced}")
        return True

    file_path.write_text(new_content)
    print(f"Modified: {file_path}")
    print(f"  Resource: {resource_name}, Delete order: {delete_order}")
    return True


def main() -> int:
    """Run on all test files."""
    import argparse

    parser = argparse.ArgumentParser(description="Add test_delete methods to test files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--file", type=str, help="Process a single file")
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(TESTS_DIR.glob("test_*.py"))

    modified_count = 0
    for file_path in files:
        if add_delete_test(file_path, dry_run=args.dry_run):
            modified_count += 1

    action = "Would modify" if args.dry_run else "Modified"
    print(f"\n{action} {modified_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
