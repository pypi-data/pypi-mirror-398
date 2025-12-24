"""Integration tests for client_side_defense resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestClientSideDefense:
    """Test client_side_defense CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-client-side-defense"

    @pytest.mark.skip(reason="No spec template available for client_side_defense")
    @pytest.mark.order(490)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a client_side_defense."""
        body = SPEC_REGISTRY.get_spec("client_side_defense", "create", test_namespace)
        result = client.client_side_defense.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for client_side_defense")
    @pytest.mark.order(491)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a client_side_defense by name."""
        result = client.client_side_defense.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for client_side_defense")
    @pytest.mark.order(492)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing client_side_defense resources in namespace."""
        items = client.client_side_defense.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for client_side_defense")
    @pytest.mark.order(493)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a client_side_defense."""
        body = SPEC_REGISTRY.get_spec("client_side_defense", "replace", test_namespace)
        client.client_side_defense.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.client_side_defense.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME