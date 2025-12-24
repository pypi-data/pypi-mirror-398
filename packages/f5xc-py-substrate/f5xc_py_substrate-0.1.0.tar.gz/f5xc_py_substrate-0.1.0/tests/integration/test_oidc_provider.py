"""Integration tests for oidc_provider resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestOidcProvider:
    """Test oidc_provider CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-oidc-provider"

    @pytest.mark.skip(reason="No spec template available for oidc_provider")
    @pytest.mark.order(1430)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a oidc_provider."""
        body = SPEC_REGISTRY.get_spec("oidc_provider", "create", test_namespace)
        result = client.oidc_provider.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for oidc_provider")
    @pytest.mark.order(10701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a oidc_provider by name."""
        result = client.oidc_provider.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for oidc_provider")
    @pytest.mark.order(10702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing oidc_provider resources in namespace."""
        items = client.oidc_provider.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for oidc_provider")
    @pytest.mark.order(10703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a oidc_provider."""
        body = SPEC_REGISTRY.get_spec("oidc_provider", "replace", test_namespace)
        client.oidc_provider.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.oidc_provider.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98570)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the oidc_provider."""
        client.oidc_provider.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.oidc_provider.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
