"""Integration tests for static_component resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestStaticComponent:
    """Test static_component CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-static-component"

    @pytest.mark.skip(reason="No spec template available for static_component")
    @pytest.mark.order(1870)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a static_component."""
        body = SPEC_REGISTRY.get_spec("static_component", "create", test_namespace)
        result = client.static_component.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for static_component")
    @pytest.mark.order(1871)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a static_component by name."""
        result = client.static_component.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for static_component")
    @pytest.mark.order(1872)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing static_component resources in namespace."""
        items = client.static_component.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for static_component")
    @pytest.mark.order(1873)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a static_component."""
        body = SPEC_REGISTRY.get_spec("static_component", "replace", test_namespace)
        client.static_component.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.static_component.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME