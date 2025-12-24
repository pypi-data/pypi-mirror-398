"""Integration tests for app_type resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAppType:
    """Test app_type CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-app-type"

    @pytest.mark.order(250)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a app_type."""
        body = SPEC_REGISTRY.get_spec("app_type", "create", test_namespace)
        result = client.app_type.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(1801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a app_type by name."""
        result = client.app_type.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(1802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing app_type resources in namespace."""
        items = client.app_type.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(1803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a app_type."""
        body = SPEC_REGISTRY.get_spec("app_type", "replace", test_namespace)
        client.app_type.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.app_type.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99750)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the app_type."""
        client.app_type.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.app_type.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
