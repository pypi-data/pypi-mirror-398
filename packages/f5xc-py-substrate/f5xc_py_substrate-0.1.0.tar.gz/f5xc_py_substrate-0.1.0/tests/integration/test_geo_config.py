"""Integration tests for geo_config resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestGeoConfig:
    """Test geo_config CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-geo-config"

    @pytest.mark.skip(reason="No spec template available for geo_config")
    @pytest.mark.order(880)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a geo_config."""
        body = SPEC_REGISTRY.get_spec("geo_config", "create", test_namespace)
        result = client.geo_config.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for geo_config")
    @pytest.mark.order(881)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a geo_config by name."""
        result = client.geo_config.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for geo_config")
    @pytest.mark.order(882)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing geo_config resources in namespace."""
        items = client.geo_config.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for geo_config")
    @pytest.mark.order(883)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a geo_config."""
        body = SPEC_REGISTRY.get_spec("geo_config", "replace", test_namespace)
        client.geo_config.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.geo_config.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME