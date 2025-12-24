"""Integration tests for certified_hardware resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCertifiedHardware:
    """Test certified_hardware CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-certified-hardware"

    @pytest.mark.skip(reason="No spec template available for certified_hardware")
    @pytest.mark.order(460)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a certified_hardware."""
        body = SPEC_REGISTRY.get_spec("certified_hardware", "create", test_namespace)
        result = client.certified_hardware.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for certified_hardware")
    @pytest.mark.order(461)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a certified_hardware by name."""
        result = client.certified_hardware.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for certified_hardware")
    @pytest.mark.order(462)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing certified_hardware resources in namespace."""
        items = client.certified_hardware.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for certified_hardware")
    @pytest.mark.order(463)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a certified_hardware."""
        body = SPEC_REGISTRY.get_spec("certified_hardware", "replace", test_namespace)
        client.certified_hardware.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.certified_hardware.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME