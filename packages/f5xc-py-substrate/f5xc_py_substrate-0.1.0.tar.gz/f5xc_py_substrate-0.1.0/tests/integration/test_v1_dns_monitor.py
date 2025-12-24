"""Integration tests for v1_dns_monitor resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestV1DnsMonitor:
    """Test v1_dns_monitor CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-v1-dns-monitor"

    @pytest.mark.order(2140)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a v1_dns_monitor."""
        body = SPEC_REGISTRY.get_spec("v1_dns_monitor", "create", test_namespace)
        result = client.v1_dns_monitor.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a v1_dns_monitor by name."""
        result = client.v1_dns_monitor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing v1_dns_monitor resources in namespace."""
        items = client.v1_dns_monitor.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a v1_dns_monitor."""
        body = SPEC_REGISTRY.get_spec("v1_dns_monitor", "replace", test_namespace)
        client.v1_dns_monitor.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.v1_dns_monitor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97860)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the v1_dns_monitor."""
        client.v1_dns_monitor.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.v1_dns_monitor.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
