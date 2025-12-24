"""Integration tests for payment_method resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestPaymentMethod:
    """Test payment_method CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-payment-method"

    @pytest.mark.skip(reason="No spec template available for payment_method")
    @pytest.mark.order(1460)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a payment_method."""
        body = SPEC_REGISTRY.get_spec("payment_method", "create", test_namespace)
        result = client.payment_method.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for payment_method")
    @pytest.mark.order(11001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a payment_method by name."""
        result = client.payment_method.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for payment_method")
    @pytest.mark.order(11002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing payment_method resources in namespace."""
        items = client.payment_method.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for payment_method")
    @pytest.mark.order(11003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a payment_method."""
        body = SPEC_REGISTRY.get_spec("payment_method", "replace", test_namespace)
        client.payment_method.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.payment_method.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98540)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the payment_method."""
        client.payment_method.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.payment_method.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
