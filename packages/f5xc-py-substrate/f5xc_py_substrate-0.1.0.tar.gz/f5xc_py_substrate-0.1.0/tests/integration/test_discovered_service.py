"""Integration tests for discovered_service resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDiscoveredService:
    """Test discovered_service CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-discovered-service"

    @pytest.mark.skip(reason="No spec template available for discovered_service")
    @pytest.mark.order(690)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a discovered_service."""
        body = SPEC_REGISTRY.get_spec("discovered_service", "create", test_namespace)
        result = client.discovered_service.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for discovered_service")
    @pytest.mark.order(5301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a discovered_service by name."""
        result = client.discovered_service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for discovered_service")
    @pytest.mark.order(5302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing discovered_service resources in namespace."""
        items = client.discovered_service.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for discovered_service")
    @pytest.mark.order(5303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a discovered_service."""
        body = SPEC_REGISTRY.get_spec("discovered_service", "replace", test_namespace)
        client.discovered_service.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.discovered_service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99310)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the discovered_service."""
        client.discovered_service.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.discovered_service.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
