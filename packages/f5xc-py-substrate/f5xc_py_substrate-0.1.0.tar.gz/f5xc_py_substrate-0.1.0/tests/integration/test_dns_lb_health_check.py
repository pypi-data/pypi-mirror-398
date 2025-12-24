"""Integration tests for dns_lb_health_check resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDnsLbHealthCheck:
    """Test dns_lb_health_check CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-dns-lb-health-check"

    @pytest.mark.order(730)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a dns_lb_health_check."""
        body = SPEC_REGISTRY.get_spec("dns_lb_health_check", "create", test_namespace)
        result = client.dns_lb_health_check.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a dns_lb_health_check by name."""
        result = client.dns_lb_health_check.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing dns_lb_health_check resources in namespace."""
        items = client.dns_lb_health_check.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a dns_lb_health_check."""
        body = SPEC_REGISTRY.get_spec("dns_lb_health_check", "replace", test_namespace)
        client.dns_lb_health_check.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.dns_lb_health_check.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99270)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the dns_lb_health_check."""
        client.dns_lb_health_check.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.dns_lb_health_check.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
