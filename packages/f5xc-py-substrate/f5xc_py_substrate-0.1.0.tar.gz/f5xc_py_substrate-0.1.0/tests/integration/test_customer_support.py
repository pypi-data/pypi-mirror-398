"""Integration tests for customer_support resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCustomerSupport:
    """Test customer_support CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-customer-support"

    @pytest.mark.order(620)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a customer_support."""
        body = SPEC_REGISTRY.get_spec("customer_support", "create", test_namespace)
        result = client.customer_support.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(4901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a customer_support by name."""
        result = client.customer_support.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(4902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing customer_support resources in namespace."""
        items = client.customer_support.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(4903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a customer_support."""
        body = SPEC_REGISTRY.get_spec("customer_support", "replace", test_namespace)
        client.customer_support.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.customer_support.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99380)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the customer_support."""
        client.customer_support.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.customer_support.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
