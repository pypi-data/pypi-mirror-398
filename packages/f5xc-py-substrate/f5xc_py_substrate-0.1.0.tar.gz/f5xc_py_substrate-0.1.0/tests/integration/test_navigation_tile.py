"""Integration tests for navigation_tile resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNavigationTile:
    """Test navigation_tile CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-navigation-tile"

    @pytest.mark.skip(reason="No spec template available for navigation_tile")
    @pytest.mark.order(1300)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a navigation_tile."""
        body = SPEC_REGISTRY.get_spec("navigation_tile", "create", test_namespace)
        result = client.navigation_tile.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for navigation_tile")
    @pytest.mark.order(1301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a navigation_tile by name."""
        result = client.navigation_tile.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for navigation_tile")
    @pytest.mark.order(1302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing navigation_tile resources in namespace."""
        items = client.navigation_tile.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for navigation_tile")
    @pytest.mark.order(1303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a navigation_tile."""
        body = SPEC_REGISTRY.get_spec("navigation_tile", "replace", test_namespace)
        client.navigation_tile.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.navigation_tile.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME