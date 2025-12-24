"""Base model with serialization helpers for F5 XC SDK."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class F5XCBaseModel(BaseModel):
    """Base model for all F5 XC SDK models with serialization helpers.

    Provides convenience methods for serializing models to dict, JSON, and YAML
    with sensible defaults for API-compatible output.

    All SDK models inherit from this class, giving them access to:
    - to_dict(): Convert to Python dictionary
    - to_json(): Convert to JSON string
    - to_yaml(): Convert to YAML string (requires pyyaml)
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def to_dict(
        self,
        *,
        exclude_none: bool = True,
        by_alias: bool = False,
        exclude: set[str] | None = None,
    ) -> dict[str, Any]:
        """Serialize model to dictionary.

        Args:
            exclude_none: Exclude fields with None values (default: True)
            by_alias: Use field aliases for keys (default: False)
            exclude: Set of field names to exclude

        Returns:
            Dictionary representation of the model

        Example:
            >>> lb.to_dict()
            {'metadata': {...}, 'spec': {...}}
            >>> lb.to_dict(exclude={'status'})
            {'metadata': {...}, 'spec': {...}}
        """
        return self.model_dump(
            exclude_none=exclude_none,
            by_alias=by_alias,
            exclude=exclude,
        )

    def to_json(
        self,
        *,
        indent: int | None = None,
        exclude_none: bool = True,
        by_alias: bool = True,
        exclude: set[str] | None = None,
    ) -> str:
        """Serialize model to JSON string.

        Args:
            indent: JSON indentation level (default: None for compact output)
            exclude_none: Exclude fields with None values (default: True)
            by_alias: Use field aliases for keys (default: True for API compatibility)
            exclude: Set of field names to exclude

        Returns:
            JSON string representation of the model

        Example:
            >>> lb.to_json()
            '{"metadata": {...}, "spec": {...}}'
            >>> lb.to_json(indent=2)  # Pretty print
            '{\\n  "metadata": {...}\\n}'
        """
        return self.model_dump_json(
            indent=indent,
            exclude_none=exclude_none,
            by_alias=by_alias,
            exclude=exclude,
        )

    def to_yaml(
        self,
        *,
        exclude_none: bool = True,
        by_alias: bool = True,
        exclude: set[str] | None = None,
        default_flow_style: bool = False,
    ) -> str:
        """Serialize model to YAML string.

        Requires pyyaml to be installed: pip install f5xc-py-substrate[yaml]

        Args:
            exclude_none: Exclude fields with None values (default: True)
            by_alias: Use field aliases for keys (default: True for API compatibility)
            exclude: Set of field names to exclude
            default_flow_style: Use flow style for collections (default: False)

        Returns:
            YAML string representation of the model

        Raises:
            ImportError: If pyyaml is not installed

        Example:
            >>> print(lb.to_yaml())
            metadata:
              name: my-lb
            spec:
              domains:
                - example.com
        """
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "pyyaml is required for YAML serialization. "
                "Install it with: pip install f5xc-py-substrate[yaml]"
            ) from None

        data = self.model_dump(
            exclude_none=exclude_none,
            by_alias=by_alias,
            exclude=exclude,
        )
        result: str = yaml.dump(data, default_flow_style=default_flow_style, sort_keys=False)
        return result
