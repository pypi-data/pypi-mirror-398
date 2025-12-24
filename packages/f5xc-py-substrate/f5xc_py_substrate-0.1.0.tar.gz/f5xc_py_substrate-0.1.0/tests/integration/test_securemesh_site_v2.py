"""Integration tests for securemesh_site_v2 resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSecuremeshSiteV2:
    """Test securemesh_site_v2 CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-securemesh-site-v2"

    @pytest.mark.order(1750)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a securemesh_site_v2."""
        body = SPEC_REGISTRY.get_spec("securemesh_site_v2", "create", test_namespace)
        result = client.securemesh_site_v2.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(13001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a securemesh_site_v2 by name."""
        result = client.securemesh_site_v2.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(13002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing securemesh_site_v2 resources in namespace."""
        items = client.securemesh_site_v2.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(13003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a securemesh_site_v2."""
        body = SPEC_REGISTRY.get_spec("securemesh_site_v2", "replace", test_namespace)
        client.securemesh_site_v2.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.securemesh_site_v2.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98250)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the securemesh_site_v2."""
        client.securemesh_site_v2.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.securemesh_site_v2.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
