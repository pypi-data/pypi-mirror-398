"""Integration tests for status_at_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestStatusAtSite:
    """Test status_at_site CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-status-at-site"

    @pytest.mark.skip(reason="No spec template available for status_at_site")
    @pytest.mark.order(1880)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a status_at_site."""
        body = SPEC_REGISTRY.get_spec("status_at_site", "create", test_namespace)
        result = client.status_at_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for status_at_site")
    @pytest.mark.order(1881)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a status_at_site by name."""
        result = client.status_at_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for status_at_site")
    @pytest.mark.order(1882)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing status_at_site resources in namespace."""
        items = client.status_at_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for status_at_site")
    @pytest.mark.order(1883)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a status_at_site."""
        body = SPEC_REGISTRY.get_spec("status_at_site", "replace", test_namespace)
        client.status_at_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.status_at_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME