"""Integration tests for usage resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestUsage:
    """Test usage CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-usage"

    @pytest.mark.skip(reason="No spec template available for usage")
    @pytest.mark.order(2080)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a usage."""
        body = SPEC_REGISTRY.get_spec("usage", "create", test_namespace)
        result = client.usage.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for usage")
    @pytest.mark.order(2081)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a usage by name."""
        result = client.usage.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for usage")
    @pytest.mark.order(2082)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing usage resources in namespace."""
        items = client.usage.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for usage")
    @pytest.mark.order(2083)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a usage."""
        body = SPEC_REGISTRY.get_spec("usage", "replace", test_namespace)
        client.usage.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.usage.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME