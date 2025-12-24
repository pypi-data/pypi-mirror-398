"""Unit tests for F5XCBaseModel serialization helpers."""

from __future__ import annotations

import json
from typing import Optional

import pytest

from f5xc_py_substrate.models import F5XCBaseModel


class SampleModel(F5XCBaseModel):
    """Sample model for testing."""

    name: str
    value: Optional[int] = None
    nested: Optional["SampleModel"] = None


class TestToDict:
    """Tests for to_dict method."""

    def test_basic_serialization(self) -> None:
        model = SampleModel(name="test", value=42)
        result = model.to_dict()
        assert result == {"name": "test", "value": 42}

    def test_exclude_none_default(self) -> None:
        model = SampleModel(name="test")
        result = model.to_dict()
        assert result == {"name": "test"}
        assert "value" not in result

    def test_include_none(self) -> None:
        model = SampleModel(name="test")
        result = model.to_dict(exclude_none=False)
        assert result == {"name": "test", "value": None, "nested": None}

    def test_exclude_specific_fields(self) -> None:
        model = SampleModel(name="test", value=42)
        result = model.to_dict(exclude={"value"})
        assert result == {"name": "test"}

    def test_nested_model(self) -> None:
        nested = SampleModel(name="inner", value=10)
        model = SampleModel(name="outer", nested=nested)
        result = model.to_dict()
        assert result == {
            "name": "outer",
            "nested": {"name": "inner", "value": 10},
        }


class TestToJson:
    """Tests for to_json method."""

    def test_basic_serialization(self) -> None:
        model = SampleModel(name="test", value=42)
        result = model.to_json()
        parsed = json.loads(result)
        assert parsed == {"name": "test", "value": 42}

    def test_compact_by_default(self) -> None:
        """Test that to_json() returns compact JSON by default (no indentation)."""
        model = SampleModel(name="test", value=42)
        result = model.to_json()
        # Compact JSON should not have newlines
        assert "\n" not in result
        assert result == '{"name":"test","value":42}'

    def test_indent(self) -> None:
        model = SampleModel(name="test")
        result = model.to_json(indent=4)
        assert "    " in result  # 4-space indent
        assert "\n" in result  # Has newlines when indented

    def test_exclude_none_default(self) -> None:
        model = SampleModel(name="test")
        result = model.to_json()
        parsed = json.loads(result)
        assert "value" not in parsed

    def test_exclude_fields(self) -> None:
        model = SampleModel(name="test", value=42)
        result = model.to_json(exclude={"value"})
        parsed = json.loads(result)
        assert parsed == {"name": "test"}


class TestToYaml:
    """Tests for to_yaml method."""

    def test_yaml_not_installed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when pyyaml not installed."""
        # Mock the import to fail
        import builtins

        real_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):
            if name == "yaml":
                raise ImportError("No module named 'yaml'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        model = SampleModel(name="test")
        with pytest.raises(ImportError, match="pyyaml is required"):
            model.to_yaml()

    def test_basic_serialization(self) -> None:
        """Test YAML output when pyyaml is installed."""
        try:
            import yaml  # noqa: F401
        except ImportError:
            pytest.skip("pyyaml not installed")

        model = SampleModel(name="test", value=42)
        result = model.to_yaml()
        assert "name: test" in result
        assert "value: 42" in result

    def test_exclude_none_default(self) -> None:
        """Test that None values are excluded by default."""
        try:
            import yaml  # noqa: F401
        except ImportError:
            pytest.skip("pyyaml not installed")

        model = SampleModel(name="test")
        result = model.to_yaml()
        assert "value" not in result

    def test_exclude_fields(self) -> None:
        """Test field exclusion."""
        try:
            import yaml  # noqa: F401
        except ImportError:
            pytest.skip("pyyaml not installed")

        model = SampleModel(name="test", value=42)
        result = model.to_yaml(exclude={"value"})
        assert "name: test" in result
        assert "value" not in result


class TestModelConfig:
    """Tests for model configuration."""

    def test_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed and preserved."""
        data = {"name": "test", "extra_field": "extra_value"}
        model = SampleModel(**data)
        result = model.to_dict()
        assert result["extra_field"] == "extra_value"

    def test_populate_by_name(self) -> None:
        """Test that fields can be populated by alias."""
        # The base model has populate_by_name=True
        model = SampleModel(name="test")
        assert model.name == "test"
