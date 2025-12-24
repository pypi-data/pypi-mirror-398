"""Integration tests for usb resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestUsb:
    """Test usb CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-usb"

    @pytest.mark.skip(reason="No spec template available for usb")
    @pytest.mark.order(2090)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a usb."""
        body = SPEC_REGISTRY.get_spec("usb", "create", test_namespace)
        result = client.usb.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for usb")
    @pytest.mark.order(2091)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a usb by name."""
        result = client.usb.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for usb")
    @pytest.mark.order(2092)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing usb resources in namespace."""
        items = client.usb.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for usb")
    @pytest.mark.order(2093)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a usb."""
        body = SPEC_REGISTRY.get_spec("usb", "replace", test_namespace)
        client.usb.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.usb.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME