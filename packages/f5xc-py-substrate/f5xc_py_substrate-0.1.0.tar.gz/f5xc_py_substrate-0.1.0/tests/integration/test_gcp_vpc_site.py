"""Integration tests for gcp_vpc_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestGcpVpcSite:
    """Test gcp_vpc_site CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-gcp-vpc-site"

    @pytest.mark.skip(reason="No spec template available for gcp_vpc_site")
    @pytest.mark.order(870)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a gcp_vpc_site."""
        body = SPEC_REGISTRY.get_spec("gcp_vpc_site", "create", test_namespace)
        result = client.gcp_vpc_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for gcp_vpc_site")
    @pytest.mark.order(871)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a gcp_vpc_site by name."""
        result = client.gcp_vpc_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for gcp_vpc_site")
    @pytest.mark.order(872)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing gcp_vpc_site resources in namespace."""
        items = client.gcp_vpc_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for gcp_vpc_site")
    @pytest.mark.order(873)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a gcp_vpc_site."""
        body = SPEC_REGISTRY.get_spec("gcp_vpc_site", "replace", test_namespace)
        client.gcp_vpc_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.gcp_vpc_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME