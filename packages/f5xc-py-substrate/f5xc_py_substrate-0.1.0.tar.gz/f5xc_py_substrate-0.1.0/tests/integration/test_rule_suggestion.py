"""Integration tests for rule_suggestion resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestRuleSuggestion:
    """Test rule_suggestion CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-rule-suggestion"

    @pytest.mark.skip(reason="No spec template available for rule_suggestion")
    @pytest.mark.order(1680)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a rule_suggestion."""
        body = SPEC_REGISTRY.get_spec("rule_suggestion", "create", test_namespace)
        result = client.rule_suggestion.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for rule_suggestion")
    @pytest.mark.order(1681)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a rule_suggestion by name."""
        result = client.rule_suggestion.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for rule_suggestion")
    @pytest.mark.order(1682)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing rule_suggestion resources in namespace."""
        items = client.rule_suggestion.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for rule_suggestion")
    @pytest.mark.order(1683)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a rule_suggestion."""
        body = SPEC_REGISTRY.get_spec("rule_suggestion", "replace", test_namespace)
        client.rule_suggestion.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.rule_suggestion.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME