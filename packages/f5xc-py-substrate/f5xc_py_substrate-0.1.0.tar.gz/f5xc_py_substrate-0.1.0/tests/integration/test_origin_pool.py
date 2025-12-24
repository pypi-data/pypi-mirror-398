"""Integration tests for origin_pool resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestOriginPool:
    """Test origin_pool CRUD operations.

    Status: complete
    Notes: Uses public_name DNS, no healthcheck dependency
    """

    RESOURCE_NAME = "sdk-test-origin-pool"

    @pytest.mark.order(1440)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a origin_pool."""
        body = SPEC_REGISTRY.get_spec("origin_pool", "create", test_namespace)
        result = client.origin_pool.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(10801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a origin_pool by name."""
        result = client.origin_pool.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(10802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing origin_pool resources in namespace."""
        items = client.origin_pool.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(10803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a origin_pool."""
        body = SPEC_REGISTRY.get_spec("origin_pool", "replace", test_namespace)
        client.origin_pool.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.origin_pool.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98560)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the origin_pool."""
        client.origin_pool.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.origin_pool.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
