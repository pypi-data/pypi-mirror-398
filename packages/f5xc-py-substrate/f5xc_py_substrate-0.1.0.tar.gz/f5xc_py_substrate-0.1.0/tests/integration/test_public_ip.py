"""Integration tests for public_ip resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestPublicIp:
    """Test public_ip CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-public-ip"

    @pytest.mark.skip(reason="No spec template available for public_ip")
    @pytest.mark.order(1560)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a public_ip."""
        body = SPEC_REGISTRY.get_spec("public_ip", "create", test_namespace)
        result = client.public_ip.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for public_ip")
    @pytest.mark.order(1561)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a public_ip by name."""
        result = client.public_ip.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for public_ip")
    @pytest.mark.order(1562)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing public_ip resources in namespace."""
        items = client.public_ip.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for public_ip")
    @pytest.mark.order(1563)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a public_ip."""
        body = SPEC_REGISTRY.get_spec("public_ip", "replace", test_namespace)
        client.public_ip.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.public_ip.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME