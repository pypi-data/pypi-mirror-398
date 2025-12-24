"""Integration tests for shape_bot_defense_instance resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestShapeBotDefenseInstance:
    """Test shape_bot_defense_instance CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-shape-bot-defense-instance"

    @pytest.mark.skip(reason="No spec template available for shape_bot_defense_instance")
    @pytest.mark.order(1830)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a shape_bot_defense_instance."""
        body = SPEC_REGISTRY.get_spec("shape_bot_defense_instance", "create", test_namespace)
        result = client.shape_bot_defense_instance.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for shape_bot_defense_instance")
    @pytest.mark.order(1831)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a shape_bot_defense_instance by name."""
        result = client.shape_bot_defense_instance.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for shape_bot_defense_instance")
    @pytest.mark.order(1832)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing shape_bot_defense_instance resources in namespace."""
        items = client.shape_bot_defense_instance.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for shape_bot_defense_instance")
    @pytest.mark.order(1833)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a shape_bot_defense_instance."""
        body = SPEC_REGISTRY.get_spec("shape_bot_defense_instance", "replace", test_namespace)
        client.shape_bot_defense_instance.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.shape_bot_defense_instance.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME