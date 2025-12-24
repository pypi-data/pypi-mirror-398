"""Integration tests for managed_tenant resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestManagedTenant:
    """Test managed_tenant CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-managed-tenant"

    @pytest.mark.order(1220)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a managed_tenant."""
        body = SPEC_REGISTRY.get_spec("managed_tenant", "create", test_namespace)
        result = client.managed_tenant.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(9501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a managed_tenant by name."""
        result = client.managed_tenant.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(9502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing managed_tenant resources in namespace."""
        items = client.managed_tenant.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(9503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a managed_tenant."""
        body = SPEC_REGISTRY.get_spec("managed_tenant", "replace", test_namespace)
        client.managed_tenant.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.managed_tenant.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98780)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the managed_tenant."""
        client.managed_tenant.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.managed_tenant.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
