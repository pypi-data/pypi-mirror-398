"""Integration tests for securemesh_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSecuremeshSite:
    """Test securemesh_site CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-securemesh-site"

    @pytest.mark.order(1740)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a securemesh_site."""
        body = SPEC_REGISTRY.get_spec("securemesh_site", "create", test_namespace)
        result = client.securemesh_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(12901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a securemesh_site by name."""
        result = client.securemesh_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(12902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing securemesh_site resources in namespace."""
        items = client.securemesh_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(12903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a securemesh_site."""
        body = SPEC_REGISTRY.get_spec("securemesh_site", "replace", test_namespace)
        client.securemesh_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.securemesh_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98260)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the securemesh_site."""
        client.securemesh_site.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.securemesh_site.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
