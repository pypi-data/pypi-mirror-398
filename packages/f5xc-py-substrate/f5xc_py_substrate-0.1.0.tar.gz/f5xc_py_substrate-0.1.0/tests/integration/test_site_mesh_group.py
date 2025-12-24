"""Integration tests for site_mesh_group resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSiteMeshGroup:
    """Test site_mesh_group CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-site-mesh-group"

    @pytest.mark.order(1850)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a site_mesh_group."""
        body = SPEC_REGISTRY.get_spec("site_mesh_group", "create", test_namespace)
        result = client.site_mesh_group.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(13701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a site_mesh_group by name."""
        result = client.site_mesh_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(13702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing site_mesh_group resources in namespace."""
        items = client.site_mesh_group.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(13703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a site_mesh_group."""
        body = SPEC_REGISTRY.get_spec("site_mesh_group", "replace", test_namespace)
        client.site_mesh_group.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.site_mesh_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98150)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the site_mesh_group."""
        client.site_mesh_group.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.site_mesh_group.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
