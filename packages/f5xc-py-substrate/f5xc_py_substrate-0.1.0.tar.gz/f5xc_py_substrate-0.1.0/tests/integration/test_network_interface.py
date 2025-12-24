"""Integration tests for network_interface resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNetworkInterface:
    """Test network_interface CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-network-interface"

    @pytest.mark.order(1330)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a network_interface."""
        body = SPEC_REGISTRY.get_spec("network_interface", "create", test_namespace)
        result = client.network_interface.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(10201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a network_interface by name."""
        result = client.network_interface.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(10202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing network_interface resources in namespace."""
        items = client.network_interface.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(10203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a network_interface."""
        body = SPEC_REGISTRY.get_spec("network_interface", "replace", test_namespace)
        client.network_interface.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.network_interface.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98670)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the network_interface."""
        client.network_interface.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.network_interface.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
