"""Integration tests for dns_zone resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDnsZone:
    """Test dns_zone CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-dns-zone"

    @pytest.mark.order(760)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a dns_zone."""
        body = SPEC_REGISTRY.get_spec("dns_zone", "create", test_namespace)
        result = client.dns_zone.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(6001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a dns_zone by name."""
        result = client.dns_zone.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(6002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing dns_zone resources in namespace."""
        items = client.dns_zone.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(6003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a dns_zone."""
        body = SPEC_REGISTRY.get_spec("dns_zone", "replace", test_namespace)
        client.dns_zone.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.dns_zone.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99240)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the dns_zone."""
        client.dns_zone.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.dns_zone.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
