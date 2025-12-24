"""Integration tests for virtual_network resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVirtualNetwork:
    """Test virtual_network CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-virtual-network"

    @pytest.mark.order(2190)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a virtual_network."""
        body = SPEC_REGISTRY.get_spec("virtual_network", "create", test_namespace)
        result = client.virtual_network.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(16001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a virtual_network by name."""
        result = client.virtual_network.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(16002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing virtual_network resources in namespace."""
        items = client.virtual_network.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(16003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a virtual_network."""
        body = SPEC_REGISTRY.get_spec("virtual_network", "replace", test_namespace)
        client.virtual_network.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.virtual_network.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97810)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the virtual_network."""
        client.virtual_network.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.virtual_network.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
