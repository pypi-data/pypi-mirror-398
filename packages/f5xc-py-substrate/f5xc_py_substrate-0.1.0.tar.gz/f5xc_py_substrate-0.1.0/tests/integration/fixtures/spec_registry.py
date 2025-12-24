"""Spec registry for loading test specifications.

The spec registry loads YAML spec templates and provides them to tests
with namespace templating applied.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class SpecRegistry:
    """Registry for loading and templating test specifications."""

    def __init__(self, specs_dir: Path):
        """Initialize the spec registry.

        Args:
            specs_dir: Path to directory containing YAML spec files.
        """
        self.specs_dir = specs_dir
        self._cache: dict[str, dict | None] = {}

    def _load_spec(self, resource: str) -> dict | None:
        """Load spec from YAML file.

        Args:
            resource: Resource name (e.g., 'healthcheck').

        Returns:
            Parsed YAML dict or None if file doesn't exist.
        """
        if resource in self._cache:
            return self._cache[resource]

        spec_file = self.specs_dir / f"{resource}.yaml"
        if not spec_file.exists():
            self._cache[resource] = None
            return None

        data = yaml.safe_load(spec_file.read_text())
        self._cache[resource] = data
        return data

    def has_spec(self, resource: str) -> bool:
        """Check if a usable spec exists for the resource.

        Args:
            resource: Resource name.

        Returns:
            True if spec exists with runnable status.
        """
        data = self._load_spec(resource)
        if not data:
            return False
        return data.get("status") in ("complete", "partial", "generated")

    def get_status(self, resource: str) -> str:
        """Get the status of a resource's spec.

        Args:
            resource: Resource name.

        Returns:
            Status string: 'complete', 'partial', 'missing', or 'blocked'.
        """
        data = self._load_spec(resource)
        if not data:
            return "missing"
        return data.get("status", "missing")

    def get_spec(
        self,
        resource: str,
        operation: str,
        test_namespace: str,
    ) -> dict[str, Any]:
        """Get the spec body for an operation, templated with namespace.

        Loads the spec from YAML, applies namespace templating, and wraps
        in the standard request body format with metadata.

        Args:
            resource: Resource name (e.g., 'healthcheck').
            operation: Operation name ('create' or 'replace').
            test_namespace: Namespace to use for templating.

        Returns:
            Complete request body dict with metadata and spec.

        Raises:
            ValueError: If no spec is available for the resource/operation.
        """
        data = self._load_spec(resource)
        if not data:
            raise ValueError(f"No spec available for {resource}")

        spec_data = data.get("spec", {}).get(operation)
        if not spec_data:
            raise ValueError(f"No {operation} spec for {resource}")

        # Deep copy and template
        result = copy.deepcopy(spec_data)
        self._template_values(
            result,
            {
                "test_namespace": test_namespace,
            },
        )

        # Wrap in standard body format
        resource_name = f"sdk-test-{resource.replace('_', '-')}"
        return {
            "metadata": {
                "name": resource_name,
                "namespace": test_namespace,
                "description": f"SDK integration test {resource}",
            },
            "spec": result,
        }

    def _template_values(self, obj: Any, values: dict[str, str]) -> None:
        """Recursively replace template strings like {test_namespace}.

        Args:
            obj: Object to process (modified in place).
            values: Dict of template key -> replacement value.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    for k, v in values.items():
                        value = value.replace(f"{{{k}}}", v)
                    obj[key] = value
                else:
                    self._template_values(value, values)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    for k, v in values.items():
                        item = item.replace(f"{{{k}}}", v)
                    obj[i] = item
                else:
                    self._template_values(item, values)


# Global registry instance
SPECS_DIR = Path(__file__).parent.parent / "specs"
SPEC_REGISTRY = SpecRegistry(SPECS_DIR)
