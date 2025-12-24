"""Integration tests for l3l4 resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestL3l4:
    """Test l3l4 CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-l3l4"

    @pytest.mark.skip(reason="No spec template available for l3l4")
    @pytest.mark.order(1160)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a l3l4."""
        body = SPEC_REGISTRY.get_spec("l3l4", "create", test_namespace)
        result = client.l3l4.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for l3l4")
    @pytest.mark.order(1161)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a l3l4 by name."""
        result = client.l3l4.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for l3l4")
    @pytest.mark.order(1162)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing l3l4 resources in namespace."""
        items = client.l3l4.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for l3l4")
    @pytest.mark.order(1163)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a l3l4."""
        body = SPEC_REGISTRY.get_spec("l3l4", "replace", test_namespace)
        client.l3l4.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.l3l4.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME