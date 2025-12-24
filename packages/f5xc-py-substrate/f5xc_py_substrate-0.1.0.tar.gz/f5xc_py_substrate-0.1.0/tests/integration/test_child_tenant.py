"""Integration tests for child_tenant resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestChildTenant:
    """Test child_tenant CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-child-tenant"

    @pytest.mark.order(470)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a child_tenant."""
        body = SPEC_REGISTRY.get_spec("child_tenant", "create", test_namespace)
        result = client.child_tenant.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a child_tenant by name."""
        result = client.child_tenant.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing child_tenant resources in namespace."""
        items = client.child_tenant.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a child_tenant."""
        body = SPEC_REGISTRY.get_spec("child_tenant", "replace", test_namespace)
        client.child_tenant.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.child_tenant.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99530)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the child_tenant."""
        client.child_tenant.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.child_tenant.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
