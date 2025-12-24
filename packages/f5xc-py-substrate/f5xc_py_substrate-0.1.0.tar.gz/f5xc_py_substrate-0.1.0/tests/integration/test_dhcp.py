"""Integration tests for dhcp resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDhcp:
    """Test dhcp CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-dhcp"

    @pytest.mark.skip(reason="No spec template available for dhcp")
    @pytest.mark.order(680)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a dhcp."""
        body = SPEC_REGISTRY.get_spec("dhcp", "create", test_namespace)
        result = client.dhcp.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for dhcp")
    @pytest.mark.order(681)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a dhcp by name."""
        result = client.dhcp.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for dhcp")
    @pytest.mark.order(682)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing dhcp resources in namespace."""
        items = client.dhcp.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for dhcp")
    @pytest.mark.order(683)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a dhcp."""
        body = SPEC_REGISTRY.get_spec("dhcp", "replace", test_namespace)
        client.dhcp.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.dhcp.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME