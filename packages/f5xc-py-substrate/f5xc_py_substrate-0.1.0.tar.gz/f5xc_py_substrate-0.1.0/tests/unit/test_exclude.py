"""Unit tests for get() exclude parameter."""

from __future__ import annotations

# Copy of the function from resource.py for testing
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            fields.add(group)
    return fields


class TestExcludeGroups:
    """Test exclusion group resolution."""

    def test_forms_group(self) -> None:
        result = _resolve_exclude_groups(["forms"])
        assert result == {"create_form", "replace_form"}

    def test_references_group(self) -> None:
        result = _resolve_exclude_groups(["references"])
        assert result == {
            "referring_objects",
            "deleted_referred_objects",
            "disabled_referred_objects",
        }

    def test_system_metadata_group(self) -> None:
        result = _resolve_exclude_groups(["system_metadata"])
        assert result == {"system_metadata"}

    def test_multiple_groups(self) -> None:
        result = _resolve_exclude_groups(["forms", "system_metadata"])
        assert result == {"create_form", "replace_form", "system_metadata"}

    def test_all_groups(self) -> None:
        result = _resolve_exclude_groups(["forms", "references", "system_metadata"])
        assert result == {
            "create_form",
            "replace_form",
            "referring_objects",
            "deleted_referred_objects",
            "disabled_referred_objects",
            "system_metadata",
        }

    def test_direct_field_name(self) -> None:
        result = _resolve_exclude_groups(["custom_field"])
        assert result == {"custom_field"}

    def test_mixed_groups_and_fields(self) -> None:
        result = _resolve_exclude_groups(["forms", "custom_field"])
        assert result == {"create_form", "replace_form", "custom_field"}

    def test_empty_list(self) -> None:
        result = _resolve_exclude_groups([])
        assert result == set()

    def test_unknown_group_treated_as_field(self) -> None:
        """Unknown group names are treated as direct field names."""
        result = _resolve_exclude_groups(["unknown_group"])
        assert result == {"unknown_group"}
