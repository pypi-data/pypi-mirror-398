"""Integration tests for ping resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestPing:
    """Test ping CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-ping"

    @pytest.mark.skip(reason="No spec template available for ping")
    @pytest.mark.order(1470)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ping."""
        body = SPEC_REGISTRY.get_spec("ping", "create", test_namespace)
        result = client.ping.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for ping")
    @pytest.mark.order(1471)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ping by name."""
        result = client.ping.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for ping")
    @pytest.mark.order(1472)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ping resources in namespace."""
        items = client.ping.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for ping")
    @pytest.mark.order(1473)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ping."""
        body = SPEC_REGISTRY.get_spec("ping", "replace", test_namespace)
        client.ping.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ping.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME