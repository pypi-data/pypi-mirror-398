"""Integration tests for udp_loadbalancer resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestUdpLoadbalancer:
    """Test udp_loadbalancer CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-udp-loadbalancer"

    @pytest.mark.order(2060)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a udp_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("udp_loadbalancer", "create", test_namespace)
        result = client.udp_loadbalancer.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a udp_loadbalancer by name."""
        result = client.udp_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing udp_loadbalancer resources in namespace."""
        items = client.udp_loadbalancer.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a udp_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("udp_loadbalancer", "replace", test_namespace)
        client.udp_loadbalancer.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.udp_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97940)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the udp_loadbalancer."""
        client.udp_loadbalancer.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.udp_loadbalancer.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
