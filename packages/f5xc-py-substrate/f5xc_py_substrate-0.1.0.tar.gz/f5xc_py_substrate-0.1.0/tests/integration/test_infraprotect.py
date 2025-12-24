"""Integration tests for infraprotect resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotect:
    """Test infraprotect CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-infraprotect"

    @pytest.mark.skip(reason="No spec template available for infraprotect")
    @pytest.mark.order(960)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect."""
        body = SPEC_REGISTRY.get_spec("infraprotect", "create", test_namespace)
        result = client.infraprotect.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for infraprotect")
    @pytest.mark.order(961)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect by name."""
        result = client.infraprotect.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for infraprotect")
    @pytest.mark.order(962)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect resources in namespace."""
        items = client.infraprotect.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for infraprotect")
    @pytest.mark.order(963)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect."""
        body = SPEC_REGISTRY.get_spec("infraprotect", "replace", test_namespace)
        client.infraprotect.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME