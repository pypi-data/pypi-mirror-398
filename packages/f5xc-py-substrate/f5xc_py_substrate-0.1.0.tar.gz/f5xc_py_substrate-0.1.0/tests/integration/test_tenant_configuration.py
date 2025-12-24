"""Integration tests for tenant_configuration resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTenantConfiguration:
    """Test tenant_configuration CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-tenant-configuration"

    @pytest.mark.order(1940)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tenant_configuration."""
        body = SPEC_REGISTRY.get_spec("tenant_configuration", "create", test_namespace)
        result = client.tenant_configuration.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tenant_configuration by name."""
        result = client.tenant_configuration.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tenant_configuration resources in namespace."""
        items = client.tenant_configuration.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tenant_configuration."""
        body = SPEC_REGISTRY.get_spec("tenant_configuration", "replace", test_namespace)
        client.tenant_configuration.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tenant_configuration.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98060)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tenant_configuration."""
        client.tenant_configuration.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tenant_configuration.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
