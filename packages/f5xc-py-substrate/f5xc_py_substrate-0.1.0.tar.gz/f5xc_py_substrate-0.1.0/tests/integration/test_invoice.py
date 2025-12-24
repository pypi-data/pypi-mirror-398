"""Integration tests for invoice resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInvoice:
    """Test invoice CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-invoice"

    @pytest.mark.skip(reason="No spec template available for invoice")
    @pytest.mark.order(1060)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a invoice."""
        body = SPEC_REGISTRY.get_spec("invoice", "create", test_namespace)
        result = client.invoice.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for invoice")
    @pytest.mark.order(1061)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a invoice by name."""
        result = client.invoice.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for invoice")
    @pytest.mark.order(1062)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing invoice resources in namespace."""
        items = client.invoice.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for invoice")
    @pytest.mark.order(1063)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a invoice."""
        body = SPEC_REGISTRY.get_spec("invoice", "replace", test_namespace)
        client.invoice.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.invoice.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME