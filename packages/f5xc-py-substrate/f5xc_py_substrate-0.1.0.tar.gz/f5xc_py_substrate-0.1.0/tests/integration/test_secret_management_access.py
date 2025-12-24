"""Integration tests for secret_management_access resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSecretManagementAccess:
    """Test secret_management_access CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-secret-management-access"

    @pytest.mark.order(1710)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a secret_management_access."""
        body = SPEC_REGISTRY.get_spec("secret_management_access", "create", test_namespace)
        result = client.secret_management_access.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(12601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a secret_management_access by name."""
        result = client.secret_management_access.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(12602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing secret_management_access resources in namespace."""
        items = client.secret_management_access.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(12603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a secret_management_access."""
        body = SPEC_REGISTRY.get_spec("secret_management_access", "replace", test_namespace)
        client.secret_management_access.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.secret_management_access.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98290)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the secret_management_access."""
        client.secret_management_access.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.secret_management_access.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
