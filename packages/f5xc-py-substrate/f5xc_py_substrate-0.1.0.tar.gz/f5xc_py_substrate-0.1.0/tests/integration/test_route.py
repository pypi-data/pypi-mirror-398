"""Integration tests for route resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestRoute:
    """Test route CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-route"

    @pytest.mark.order(1670)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a route."""
        body = SPEC_REGISTRY.get_spec("route", "create", test_namespace)
        result = client.route.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(12501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a route by name."""
        result = client.route.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(12502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing route resources in namespace."""
        items = client.route.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(12503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a route."""
        body = SPEC_REGISTRY.get_spec("route", "replace", test_namespace)
        client.route.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.route.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98330)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the route."""
        client.route.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.route.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
