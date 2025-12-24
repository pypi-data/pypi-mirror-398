"""Integration tests for lte resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestLte:
    """Test lte CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-lte"

    @pytest.mark.skip(reason="No spec template available for lte")
    @pytest.mark.order(1200)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a lte."""
        body = SPEC_REGISTRY.get_spec("lte", "create", test_namespace)
        result = client.lte.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for lte")
    @pytest.mark.order(1201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a lte by name."""
        result = client.lte.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for lte")
    @pytest.mark.order(1202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing lte resources in namespace."""
        items = client.lte.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for lte")
    @pytest.mark.order(1203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a lte."""
        body = SPEC_REGISTRY.get_spec("lte", "replace", test_namespace)
        client.lte.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.lte.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME