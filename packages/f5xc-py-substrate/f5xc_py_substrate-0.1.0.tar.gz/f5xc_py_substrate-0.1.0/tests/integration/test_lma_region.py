"""Integration tests for lma_region resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestLmaRegion:
    """Test lma_region CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-lma-region"

    @pytest.mark.skip(reason="No spec template available for lma_region")
    @pytest.mark.order(1170)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a lma_region."""
        body = SPEC_REGISTRY.get_spec("lma_region", "create", test_namespace)
        result = client.lma_region.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for lma_region")
    @pytest.mark.order(1171)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a lma_region by name."""
        result = client.lma_region.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for lma_region")
    @pytest.mark.order(1172)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing lma_region resources in namespace."""
        items = client.lma_region.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for lma_region")
    @pytest.mark.order(1173)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a lma_region."""
        body = SPEC_REGISTRY.get_spec("lma_region", "replace", test_namespace)
        client.lma_region.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.lma_region.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME