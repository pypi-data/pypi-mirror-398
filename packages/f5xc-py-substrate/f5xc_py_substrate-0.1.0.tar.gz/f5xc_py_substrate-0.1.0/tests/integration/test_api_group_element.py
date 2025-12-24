"""Integration tests for api_group_element resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestApiGroupElement:
    """Test api_group_element CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-api-group-element"

    @pytest.mark.skip(reason="No spec template available for api_group_element")
    @pytest.mark.order(180)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a api_group_element."""
        body = SPEC_REGISTRY.get_spec("api_group_element", "create", test_namespace)
        result = client.api_group_element.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for api_group_element")
    @pytest.mark.order(181)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a api_group_element by name."""
        result = client.api_group_element.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for api_group_element")
    @pytest.mark.order(182)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing api_group_element resources in namespace."""
        items = client.api_group_element.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for api_group_element")
    @pytest.mark.order(183)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a api_group_element."""
        body = SPEC_REGISTRY.get_spec("api_group_element", "replace", test_namespace)
        client.api_group_element.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.api_group_element.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME