"""Integration tests for dns_load_balancer resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDnsLoadBalancer:
    """Test dns_load_balancer CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-dns-load-balancer"

    @pytest.mark.order(750)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a dns_load_balancer."""
        body = SPEC_REGISTRY.get_spec("dns_load_balancer", "create", test_namespace)
        result = client.dns_load_balancer.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a dns_load_balancer by name."""
        result = client.dns_load_balancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing dns_load_balancer resources in namespace."""
        items = client.dns_load_balancer.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a dns_load_balancer."""
        body = SPEC_REGISTRY.get_spec("dns_load_balancer", "replace", test_namespace)
        client.dns_load_balancer.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.dns_load_balancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99250)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the dns_load_balancer."""
        client.dns_load_balancer.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.dns_load_balancer.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
