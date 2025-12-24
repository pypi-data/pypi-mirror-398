"""Integration tests for api_group resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestApiGroup:
    """Test api_group CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-api-group"

    @pytest.mark.skip(reason="No spec template available for api_group")
    @pytest.mark.order(170)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a api_group."""
        body = SPEC_REGISTRY.get_spec("api_group", "create", test_namespace)
        result = client.api_group.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for api_group")
    @pytest.mark.order(171)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a api_group by name."""
        result = client.api_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for api_group")
    @pytest.mark.order(172)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing api_group resources in namespace."""
        items = client.api_group.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for api_group")
    @pytest.mark.order(173)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a api_group."""
        body = SPEC_REGISTRY.get_spec("api_group", "replace", test_namespace)
        client.api_group.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.api_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME