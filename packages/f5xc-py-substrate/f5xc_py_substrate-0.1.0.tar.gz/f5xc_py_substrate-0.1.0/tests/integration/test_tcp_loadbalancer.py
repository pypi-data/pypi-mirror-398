"""Integration tests for tcp_loadbalancer resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTcpLoadbalancer:
    """Test tcp_loadbalancer CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-tcp-loadbalancer"

    @pytest.mark.order(1920)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tcp_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("tcp_loadbalancer", "create", test_namespace)
        result = client.tcp_loadbalancer.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tcp_loadbalancer by name."""
        result = client.tcp_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tcp_loadbalancer resources in namespace."""
        items = client.tcp_loadbalancer.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tcp_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("tcp_loadbalancer", "replace", test_namespace)
        client.tcp_loadbalancer.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tcp_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98080)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tcp_loadbalancer."""
        client.tcp_loadbalancer.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tcp_loadbalancer.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
