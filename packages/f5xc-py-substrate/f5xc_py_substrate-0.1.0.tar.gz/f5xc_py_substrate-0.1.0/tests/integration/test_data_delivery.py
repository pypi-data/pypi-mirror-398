"""Integration tests for data_delivery resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDataDelivery:
    """Test data_delivery CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-data-delivery"

    @pytest.mark.skip(reason="No spec template available for data_delivery")
    @pytest.mark.order(630)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a data_delivery."""
        body = SPEC_REGISTRY.get_spec("data_delivery", "create", test_namespace)
        result = client.data_delivery.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for data_delivery")
    @pytest.mark.order(631)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a data_delivery by name."""
        result = client.data_delivery.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for data_delivery")
    @pytest.mark.order(632)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing data_delivery resources in namespace."""
        items = client.data_delivery.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for data_delivery")
    @pytest.mark.order(633)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a data_delivery."""
        body = SPEC_REGISTRY.get_spec("data_delivery", "replace", test_namespace)
        client.data_delivery.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.data_delivery.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME