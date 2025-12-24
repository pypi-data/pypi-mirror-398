"""Integration tests for child_tenant_manager resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestChildTenantManager:
    """Test child_tenant_manager CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-child-tenant-manager"

    @pytest.mark.order(480)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a child_tenant_manager."""
        body = SPEC_REGISTRY.get_spec("child_tenant_manager", "create", test_namespace)
        result = client.child_tenant_manager.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a child_tenant_manager by name."""
        result = client.child_tenant_manager.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing child_tenant_manager resources in namespace."""
        items = client.child_tenant_manager.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a child_tenant_manager."""
        body = SPEC_REGISTRY.get_spec("child_tenant_manager", "replace", test_namespace)
        client.child_tenant_manager.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.child_tenant_manager.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99520)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the child_tenant_manager."""
        client.child_tenant_manager.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.child_tenant_manager.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
