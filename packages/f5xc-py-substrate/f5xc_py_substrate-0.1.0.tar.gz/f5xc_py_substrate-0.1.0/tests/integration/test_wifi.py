"""Integration tests for wifi resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestWifi:
    """Test wifi CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-wifi"

    @pytest.mark.skip(reason="No spec template available for wifi")
    @pytest.mark.order(2270)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a wifi."""
        body = SPEC_REGISTRY.get_spec("wifi", "create", test_namespace)
        result = client.wifi.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for wifi")
    @pytest.mark.order(2271)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a wifi by name."""
        result = client.wifi.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for wifi")
    @pytest.mark.order(2272)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing wifi resources in namespace."""
        items = client.wifi.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for wifi")
    @pytest.mark.order(2273)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a wifi."""
        body = SPEC_REGISTRY.get_spec("wifi", "replace", test_namespace)
        client.wifi.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.wifi.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME