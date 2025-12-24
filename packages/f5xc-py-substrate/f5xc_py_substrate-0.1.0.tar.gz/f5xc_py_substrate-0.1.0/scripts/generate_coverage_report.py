#!/usr/bin/env python3
"""Generate coverage report from pytest JSON output.

Reads pytest-report.json and spec files, generates:
- coverage.md: Simple coverage matrix in repo root
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).parent.parent
SPECS_DIR = PROJECT_ROOT / "tests" / "integration" / "specs"
RESULTS_DIR = PROJECT_ROOT / "docs" / "test-results"


def extract_resource_operation(nodeid: str) -> tuple[str | None, str | None]:
    """Extract resource name and operation from test nodeid.

    Example nodeid: tests/integration/test_http_loadbalancer.py::TestHttpLoadbalancer::test_create
    Returns: ("http_loadbalancer", "create")
    """
    match = re.search(r"test_(\w+)\.py::Test\w+::test_(\w+)", nodeid)
    if match:
        return match.group(1), match.group(2)
    return None, None


def load_blocked_resources() -> dict[str, str]:
    """Load blocked resources from spec files.

    Returns dict of resource_name -> reason
    """
    blocked: dict[str, str] = {}
    for spec_file in SPECS_DIR.glob("*.yaml"):
        try:
            with open(spec_file) as f:
                spec = yaml.safe_load(f) or {}
            if spec.get("status") == "blocked":
                reason = spec.get("notes", "No reason provided")
                blocked[spec_file.stem] = reason
        except Exception:
            continue
    return blocked


def load_pytest_report(path: Path) -> dict[str, Any]:
    """Load pytest JSON report."""
    with open(path) as f:
        return json.load(f)


def build_coverage_data(pytest_report: dict[str, Any]) -> dict[str, Any]:
    """Build structured coverage data from pytest report."""
    created = pytest_report.get("created", datetime.now(timezone.utc).timestamp())
    summary = pytest_report.get("summary", {})

    # Build resource coverage
    resources: dict[str, dict[str, str]] = {}

    for test in pytest_report.get("tests", []):
        nodeid = test.get("nodeid", "")
        resource, operation = extract_resource_operation(nodeid)

        if not resource or not operation:
            continue

        if resource not in resources:
            resources[resource] = {}

        resources[resource][operation] = test.get("outcome", "unknown")

    return {
        "timestamp": datetime.fromtimestamp(created, tz=timezone.utc).isoformat(),
        "summary": {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
        },
        "resources": resources,
    }


def generate_markdown(
    coverage_data: dict[str, Any],
    blocked_resources: dict[str, str],
) -> str:
    """Generate simplified Markdown report."""
    lines: list[str] = []

    # Header
    lines.append("# Test Coverage")
    lines.append("")

    # Metadata
    timestamp = coverage_data.get("timestamp", "unknown")
    # Parse ISO timestamp to just date
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
    except Exception:
        date_str = timestamp

    lines.append(f"**Generated:** {date_str}")

    # Coverage percentage
    summary = coverage_data.get("summary", {})
    passed = summary.get("passed", 0)
    total = summary.get("total", 0)
    pct = round(passed / total * 100) if total > 0 else 0
    lines.append(f"**Coverage:** {pct}% ({passed}/{total} tests passing)")
    lines.append("")

    # Legend
    lines.append("**Legend:** ✅ passed · ❌ failed · ⏭️ skipped · - no test")
    lines.append("")

    # Blocked resources
    if blocked_resources:
        lines.append("## Blocked Resources")
        lines.append("")
        for resource, reason in sorted(blocked_resources.items()):
            lines.append(f"- `{resource}` - {reason}")
        lines.append("")

    # Resource coverage matrix
    resources = coverage_data.get("resources", {})
    if resources:
        lines.append("## Coverage Matrix")
        lines.append("")

        # Fixed operations order
        operations = ["create", "delete", "get", "list", "replace"]

        # Build header
        header = "| Resource | " + " | ".join(operations) + " |"
        separator = "|----------|" + "|".join(["------"] * len(operations)) + "|"
        lines.append(header)
        lines.append(separator)

        def status_icon(status: str) -> str:
            if status == "passed":
                return "✅"
            elif status == "failed":
                return "❌"
            elif status == "skipped":
                return "⏭️"
            else:
                return "❔"

        for resource in sorted(resources.keys()):
            ops = resources[resource]
            row = f"| {resource} |"
            for op in operations:
                if op in ops:
                    row += f" {status_icon(ops[op])} |"
                else:
                    row += " - |"
            lines.append(row)

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Main entry point."""
    pytest_report_path = RESULTS_DIR / "pytest-report.json"
    coverage_md_path = PROJECT_ROOT / "coverage.md"

    if not pytest_report_path.exists():
        print(f"Error: {pytest_report_path} not found")
        print("Run integration tests first: ./scripts/run-integration-tests.sh")
        return

    # Load data
    pytest_report = load_pytest_report(pytest_report_path)
    blocked_resources = load_blocked_resources()

    # Build coverage data
    coverage_data = build_coverage_data(pytest_report)

    # Write Markdown to repo root
    markdown = generate_markdown(coverage_data, blocked_resources)
    with open(coverage_md_path, "w") as f:
        f.write(markdown)
    print(f"Wrote {coverage_md_path}")


if __name__ == "__main__":
    main()
