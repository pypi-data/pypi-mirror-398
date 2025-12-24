"""Integration tests for address_allocator resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAddressAllocator:
    """Test address_allocator CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-address-allocator"

    @pytest.mark.skip(reason="No spec template available for address_allocator")
    @pytest.mark.order(30)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a address_allocator."""
        body = SPEC_REGISTRY.get_spec("address_allocator", "create", test_namespace)
        result = client.address_allocator.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for address_allocator")
    @pytest.mark.order(31)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a address_allocator by name."""
        result = client.address_allocator.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for address_allocator")
    @pytest.mark.order(32)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing address_allocator resources in namespace."""
        items = client.address_allocator.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for address_allocator")
    @pytest.mark.order(33)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a address_allocator."""
        body = SPEC_REGISTRY.get_spec("address_allocator", "replace", test_namespace)
        client.address_allocator.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.address_allocator.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME