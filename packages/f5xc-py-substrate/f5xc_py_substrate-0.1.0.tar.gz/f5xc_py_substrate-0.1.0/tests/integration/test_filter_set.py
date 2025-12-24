"""Integration tests for filter_set resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestFilterSet:
    """Test filter_set CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-filter-set"

    @pytest.mark.skip(reason="No spec template available for filter_set")
    @pytest.mark.order(820)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a filter_set."""
        body = SPEC_REGISTRY.get_spec("filter_set", "create", test_namespace)
        result = client.filter_set.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for filter_set")
    @pytest.mark.order(6601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a filter_set by name."""
        result = client.filter_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for filter_set")
    @pytest.mark.order(6602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing filter_set resources in namespace."""
        items = client.filter_set.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for filter_set")
    @pytest.mark.order(6603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a filter_set."""
        body = SPEC_REGISTRY.get_spec("filter_set", "replace", test_namespace)
        client.filter_set.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.filter_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99180)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the filter_set."""
        client.filter_set.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.filter_set.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
