"""Integration tests for data_group resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDataGroup:
    """Test data_group CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-data-group"

    @pytest.mark.order(640)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a data_group."""
        body = SPEC_REGISTRY.get_spec("data_group", "create", test_namespace)
        result = client.data_group.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a data_group by name."""
        result = client.data_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing data_group resources in namespace."""
        items = client.data_group.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a data_group."""
        body = SPEC_REGISTRY.get_spec("data_group", "replace", test_namespace)
        client.data_group.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.data_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99360)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the data_group."""
        client.data_group.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.data_group.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
