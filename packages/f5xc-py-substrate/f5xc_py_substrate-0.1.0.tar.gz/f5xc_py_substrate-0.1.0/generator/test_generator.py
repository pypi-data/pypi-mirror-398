"""Test generator for F5 XC SDK integration tests.

Generates integration test files for all namespaced resources using
Jinja2 templates and YAML spec definitions.

Usage:
    python generator/test_generator.py --all              # Generate all tests
    python generator/test_generator.py --resource foo     # Generate one test
    python generator/test_generator.py --list             # List namespaced resources
    python generator/test_generator.py --stats            # Show spec coverage stats
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

from generator.transformer import to_pascal_case


@dataclass
class TestSpec:
    """Specification for a resource's test."""

    resource: str
    is_namespaced: bool
    dependencies: list[str]
    create_spec: dict | None
    replace_spec: dict | None
    status: str  # complete, partial, missing, blocked
    notes: str


class TestGenerator:
    """Generator for integration test files."""

    def __init__(
        self,
        specs_dir: Path,
        output_dir: Path,
        templates_dir: Path,
        resources_dir: Path,
    ):
        self.specs_dir = specs_dir
        self.output_dir = output_dir
        self.resources_dir = resources_dir
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_spec(self, resource: str) -> TestSpec:
        """Load spec template for a resource."""
        spec_file = self.specs_dir / f"{resource}.yaml"
        if spec_file.exists():
            data = yaml.safe_load(spec_file.read_text())
            return TestSpec(
                resource=resource,
                is_namespaced=data.get("is_namespaced", True),
                dependencies=data.get("dependencies", []),
                create_spec=data.get("spec", {}).get("create"),
                replace_spec=data.get("spec", {}).get("replace"),
                status=data.get("status", "missing"),
                notes=data.get("notes", ""),
            )
        return TestSpec(
            resource=resource,
            is_namespaced=True,
            dependencies=[],
            create_spec=None,
            replace_spec=None,
            status="missing",
            notes="",
        )

    def generate_test(self, resource: str, order: int) -> str:
        """Generate test file content for a resource."""
        spec = self.load_spec(resource)
        template = self.env.get_template("test_resource.py.j2")
        return template.render(
            resource=resource,
            class_name=to_pascal_case(resource),
            order=order,
            spec=spec,
        )

    # Resources with manually maintained test files (not regenerated)
    MANUAL_TEST_RESOURCES = {"namespace"}

    def generate_all(self, resources: list[str]) -> dict[str, int]:
        """Generate tests for all resources.

        Returns:
            Dict with counts: {'generated': N, 'skipped': N}
        """
        stats = {"generated": 0, "skipped": 0}

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for i, resource in enumerate(resources, start=1):
            # Skip manually maintained test files
            if resource in self.MANUAL_TEST_RESOURCES:
                print(f"  Skipped: test_{resource}.py (manually maintained)")
                stats["skipped"] += 1
                continue

            output_path = self.output_dir / f"test_{resource}.py"

            # Generate content
            content = self.generate_test(resource, order=i)
            output_path.write_text(content)
            stats["generated"] += 1
            print(f"  Generated: test_{resource}.py (order={i})")

        return stats

    def generate_single(self, resource: str, order: int = 999) -> None:
        """Generate test for a single resource."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"test_{resource}.py"
        content = self.generate_test(resource, order=order)
        output_path.write_text(content)
        print(f"Generated: {output_path}")

    def get_spec_stats(self, resources: list[str]) -> dict[str, int]:
        """Get statistics on spec coverage."""
        stats = {"complete": 0, "partial": 0, "missing": 0, "blocked": 0}
        for resource in resources:
            spec = self.load_spec(resource)
            stats[spec.status] = stats.get(spec.status, 0) + 1
        return stats


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate integration tests for F5 XC SDK resources."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate tests for all namespaced resources",
    )
    parser.add_argument(
        "--resource",
        type=str,
        help="Generate test for a specific resource",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all namespaced resources",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show spec coverage statistics",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files",
    )

    args = parser.parse_args()

    # Set up paths
    project_root = Path(__file__).parent.parent
    resources_dir = project_root / "f5xc_py_substrate" / "resources"
    specs_dir = project_root / "tests" / "integration" / "specs"
    output_dir = project_root / "tests" / "integration"
    templates_dir = Path(__file__).parent / "templates"

    # Import resource discovery
    from generator.resource_discovery import (
        build_dependency_order,
        discover_namespaced_resources,
    )

    # Discover resources
    namespaced = discover_namespaced_resources(resources_dir)
    ordered = build_dependency_order(namespaced, specs_dir)

    generator = TestGenerator(
        specs_dir=specs_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        resources_dir=resources_dir,
    )

    if args.list:
        print(f"Namespaced resources ({len(namespaced)}):")
        for i, resource in enumerate(ordered, start=1):
            spec = generator.load_spec(resource)
            status_marker = {
                "complete": "[OK]",
                "partial": "[..] ",
                "missing": "[  ]",
                "blocked": "[XX]",
            }.get(spec.status, "[??]")
            print(f"  {i:3d}. {status_marker} {resource}")

    elif args.stats:
        stats = generator.get_spec_stats(namespaced)
        total = len(namespaced)
        print(f"\nSpec coverage for {total} namespaced resources:")
        print(f"  Complete: {stats['complete']:3d} ({100*stats['complete']/total:.1f}%)")
        print(f"  Partial:  {stats['partial']:3d} ({100*stats['partial']/total:.1f}%)")
        print(f"  Missing:  {stats['missing']:3d} ({100*stats['missing']/total:.1f}%)")
        print(f"  Blocked:  {stats['blocked']:3d} ({100*stats['blocked']/total:.1f}%)")

    elif args.resource:
        if args.resource not in namespaced:
            print(f"Error: '{args.resource}' is not a namespaced resource")
            print("Use --list to see available resources")
            return

        order = ordered.index(args.resource) + 1 if args.resource in ordered else 999

        if args.dry_run:
            content = generator.generate_test(args.resource, order=order)
            print(content)
        else:
            generator.generate_single(args.resource, order=order)

    elif args.all:
        if args.dry_run:
            print(f"Would generate {len(ordered)} test files:")
            for i, resource in enumerate(ordered, start=1):
                if resource in generator.MANUAL_TEST_RESOURCES:
                    print(f"  {i:3d}. test_{resource}.py (skipped - manual)")
                else:
                    print(f"  {i:3d}. test_{resource}.py")
        else:
            print(f"Generating {len(ordered)} test files...")
            stats = generator.generate_all(ordered)
            print(f"\nGenerated: {stats['generated']} files")
            if stats["skipped"] > 0:
                print(f"Skipped: {stats['skipped']} files (manually maintained)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
