"""Integration tests for addon_service resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAddonService:
    """Test addon_service CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-addon-service"

    @pytest.mark.skip(reason="No spec template available for addon_service")
    @pytest.mark.order(10)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a addon_service."""
        body = SPEC_REGISTRY.get_spec("addon_service", "create", test_namespace)
        result = client.addon_service.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for addon_service")
    @pytest.mark.order(11)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a addon_service by name."""
        result = client.addon_service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for addon_service")
    @pytest.mark.order(12)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing addon_service resources in namespace."""
        items = client.addon_service.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for addon_service")
    @pytest.mark.order(13)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a addon_service."""
        body = SPEC_REGISTRY.get_spec("addon_service", "replace", test_namespace)
        client.addon_service.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.addon_service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME