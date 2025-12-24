"""Integration tests for network_connector resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNetworkConnector:
    """Test network_connector CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-network-connector"

    @pytest.mark.order(1310)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a network_connector."""
        body = SPEC_REGISTRY.get_spec("network_connector", "create", test_namespace)
        result = client.network_connector.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(10001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a network_connector by name."""
        result = client.network_connector.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(10002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing network_connector resources in namespace."""
        items = client.network_connector.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(10003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a network_connector."""
        body = SPEC_REGISTRY.get_spec("network_connector", "replace", test_namespace)
        client.network_connector.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.network_connector.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98690)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the network_connector."""
        client.network_connector.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.network_connector.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
