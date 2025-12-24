"""Integration tests for tenant_profile resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTenantProfile:
    """Test tenant_profile CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-tenant-profile"

    @pytest.mark.order(1950)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tenant_profile."""
        body = SPEC_REGISTRY.get_spec("tenant_profile", "create", test_namespace)
        result = client.tenant_profile.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tenant_profile by name."""
        result = client.tenant_profile.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tenant_profile resources in namespace."""
        items = client.tenant_profile.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tenant_profile."""
        body = SPEC_REGISTRY.get_spec("tenant_profile", "replace", test_namespace)
        client.tenant_profile.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tenant_profile.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98050)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tenant_profile."""
        client.tenant_profile.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tenant_profile.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
