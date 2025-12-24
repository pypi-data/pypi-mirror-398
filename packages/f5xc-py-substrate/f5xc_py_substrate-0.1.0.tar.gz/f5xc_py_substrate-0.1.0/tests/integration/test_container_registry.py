"""Integration tests for container_registry resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestContainerRegistry:
    """Test container_registry CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-container-registry"

    @pytest.mark.order(600)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a container_registry."""
        body = SPEC_REGISTRY.get_spec("container_registry", "create", test_namespace)
        result = client.container_registry.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(4701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a container_registry by name."""
        result = client.container_registry.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(4702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing container_registry resources in namespace."""
        items = client.container_registry.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(4703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a container_registry."""
        body = SPEC_REGISTRY.get_spec("container_registry", "replace", test_namespace)
        client.container_registry.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.container_registry.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99400)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the container_registry."""
        client.container_registry.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.container_registry.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
