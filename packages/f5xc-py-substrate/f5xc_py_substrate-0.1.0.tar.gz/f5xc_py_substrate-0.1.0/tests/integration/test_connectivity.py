"""Integration tests for connectivity resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestConnectivity:
    """Test connectivity CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-connectivity"

    @pytest.mark.skip(reason="No spec template available for connectivity")
    @pytest.mark.order(580)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a connectivity."""
        body = SPEC_REGISTRY.get_spec("connectivity", "create", test_namespace)
        result = client.connectivity.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for connectivity")
    @pytest.mark.order(581)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a connectivity by name."""
        result = client.connectivity.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for connectivity")
    @pytest.mark.order(582)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing connectivity resources in namespace."""
        items = client.connectivity.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for connectivity")
    @pytest.mark.order(583)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a connectivity."""
        body = SPEC_REGISTRY.get_spec("connectivity", "replace", test_namespace)
        client.connectivity.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.connectivity.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME