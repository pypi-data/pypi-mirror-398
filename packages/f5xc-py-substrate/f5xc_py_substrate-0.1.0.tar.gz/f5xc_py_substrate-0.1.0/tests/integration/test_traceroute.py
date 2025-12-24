"""Integration tests for traceroute resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTraceroute:
    """Test traceroute CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-traceroute"

    @pytest.mark.skip(reason="No spec template available for traceroute")
    @pytest.mark.order(2030)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a traceroute."""
        body = SPEC_REGISTRY.get_spec("traceroute", "create", test_namespace)
        result = client.traceroute.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for traceroute")
    @pytest.mark.order(2031)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a traceroute by name."""
        result = client.traceroute.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for traceroute")
    @pytest.mark.order(2032)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing traceroute resources in namespace."""
        items = client.traceroute.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for traceroute")
    @pytest.mark.order(2033)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a traceroute."""
        body = SPEC_REGISTRY.get_spec("traceroute", "replace", test_namespace)
        client.traceroute.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.traceroute.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME