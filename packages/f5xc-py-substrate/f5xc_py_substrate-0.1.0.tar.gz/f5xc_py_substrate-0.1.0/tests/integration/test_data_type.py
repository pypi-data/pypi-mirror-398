"""Integration tests for data_type resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDataType:
    """Test data_type CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-data-type"

    @pytest.mark.order(650)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a data_type."""
        body = SPEC_REGISTRY.get_spec("data_type", "create", test_namespace)
        result = client.data_type.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a data_type by name."""
        result = client.data_type.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing data_type resources in namespace."""
        items = client.data_type.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a data_type."""
        body = SPEC_REGISTRY.get_spec("data_type", "replace", test_namespace)
        client.data_type.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.data_type.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99350)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the data_type."""
        client.data_type.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.data_type.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
