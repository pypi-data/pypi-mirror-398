"""Integration tests for discovery resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDiscovery:
    """Test discovery CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-discovery"

    @pytest.mark.order(700)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a discovery."""
        body = SPEC_REGISTRY.get_spec("discovery", "create", test_namespace)
        result = client.discovery.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a discovery by name."""
        result = client.discovery.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing discovery resources in namespace."""
        items = client.discovery.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a discovery."""
        body = SPEC_REGISTRY.get_spec("discovery", "replace", test_namespace)
        client.discovery.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.discovery.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99300)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the discovery."""
        client.discovery.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.discovery.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
