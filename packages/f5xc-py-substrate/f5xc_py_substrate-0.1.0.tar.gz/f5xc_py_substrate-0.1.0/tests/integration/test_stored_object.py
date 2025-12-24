"""Integration tests for stored_object resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestStoredObject:
    """Test stored_object CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-stored-object"

    @pytest.mark.skip(reason="No spec template available for stored_object")
    @pytest.mark.order(1890)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a stored_object."""
        body = SPEC_REGISTRY.get_spec("stored_object", "create", test_namespace)
        result = client.stored_object.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for stored_object")
    @pytest.mark.order(13901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a stored_object by name."""
        result = client.stored_object.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for stored_object")
    @pytest.mark.order(13902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing stored_object resources in namespace."""
        items = client.stored_object.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for stored_object")
    @pytest.mark.order(13903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a stored_object."""
        body = SPEC_REGISTRY.get_spec("stored_object", "replace", test_namespace)
        client.stored_object.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.stored_object.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98110)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the stored_object."""
        client.stored_object.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.stored_object.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
