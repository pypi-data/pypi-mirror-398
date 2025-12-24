"""Integration tests for safe resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSafe:
    """Test safe CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-safe"

    @pytest.mark.skip(reason="No spec template available for safe")
    @pytest.mark.order(1690)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a safe."""
        body = SPEC_REGISTRY.get_spec("safe", "create", test_namespace)
        result = client.safe.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for safe")
    @pytest.mark.order(1691)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a safe by name."""
        result = client.safe.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for safe")
    @pytest.mark.order(1692)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing safe resources in namespace."""
        items = client.safe.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for safe")
    @pytest.mark.order(1693)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a safe."""
        body = SPEC_REGISTRY.get_spec("safe", "replace", test_namespace)
        client.safe.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.safe.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME