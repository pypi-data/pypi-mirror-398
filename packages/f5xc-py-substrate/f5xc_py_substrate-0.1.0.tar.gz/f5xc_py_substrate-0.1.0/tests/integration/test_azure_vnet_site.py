"""Integration tests for azure_vnet_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAzureVnetSite:
    """Test azure_vnet_site CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-azure-vnet-site"

    @pytest.mark.skip(reason="No spec template available for azure_vnet_site")
    @pytest.mark.order(290)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a azure_vnet_site."""
        body = SPEC_REGISTRY.get_spec("azure_vnet_site", "create", test_namespace)
        result = client.azure_vnet_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for azure_vnet_site")
    @pytest.mark.order(291)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a azure_vnet_site by name."""
        result = client.azure_vnet_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for azure_vnet_site")
    @pytest.mark.order(292)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing azure_vnet_site resources in namespace."""
        items = client.azure_vnet_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for azure_vnet_site")
    @pytest.mark.order(293)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a azure_vnet_site."""
        body = SPEC_REGISTRY.get_spec("azure_vnet_site", "replace", test_namespace)
        client.azure_vnet_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.azure_vnet_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME