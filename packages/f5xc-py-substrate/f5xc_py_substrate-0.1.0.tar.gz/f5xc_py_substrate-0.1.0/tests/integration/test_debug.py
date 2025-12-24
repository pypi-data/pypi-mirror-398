"""Integration tests for debug resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDebug:
    """Test debug CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-debug"

    @pytest.mark.skip(reason="No spec template available for debug")
    @pytest.mark.order(670)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a debug."""
        body = SPEC_REGISTRY.get_spec("debug", "create", test_namespace)
        result = client.debug.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for debug")
    @pytest.mark.order(671)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a debug by name."""
        result = client.debug.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for debug")
    @pytest.mark.order(672)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing debug resources in namespace."""
        items = client.debug.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for debug")
    @pytest.mark.order(673)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a debug."""
        body = SPEC_REGISTRY.get_spec("debug", "replace", test_namespace)
        client.debug.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.debug.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME