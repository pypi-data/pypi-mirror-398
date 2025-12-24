"""Integration tests for virtual_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVirtualSite:
    """Test virtual_site CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-virtual-site"

    @pytest.mark.order(2200)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a virtual_site."""
        body = SPEC_REGISTRY.get_spec("virtual_site", "create", test_namespace)
        result = client.virtual_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(16101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a virtual_site by name."""
        result = client.virtual_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(16102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing virtual_site resources in namespace."""
        items = client.virtual_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(16103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a virtual_site."""
        body = SPEC_REGISTRY.get_spec("virtual_site", "replace", test_namespace)
        client.virtual_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.virtual_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97800)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the virtual_site."""
        client.virtual_site.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.virtual_site.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
