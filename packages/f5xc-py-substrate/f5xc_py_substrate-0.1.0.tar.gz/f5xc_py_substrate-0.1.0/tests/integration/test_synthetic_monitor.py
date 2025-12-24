"""Integration tests for synthetic_monitor resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSyntheticMonitor:
    """Test synthetic_monitor CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-synthetic-monitor"

    @pytest.mark.skip(reason="No spec template available for synthetic_monitor")
    @pytest.mark.order(1910)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a synthetic_monitor."""
        body = SPEC_REGISTRY.get_spec("synthetic_monitor", "create", test_namespace)
        result = client.synthetic_monitor.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for synthetic_monitor")
    @pytest.mark.order(1911)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a synthetic_monitor by name."""
        result = client.synthetic_monitor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for synthetic_monitor")
    @pytest.mark.order(1912)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing synthetic_monitor resources in namespace."""
        items = client.synthetic_monitor.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for synthetic_monitor")
    @pytest.mark.order(1913)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a synthetic_monitor."""
        body = SPEC_REGISTRY.get_spec("synthetic_monitor", "replace", test_namespace)
        client.synthetic_monitor.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.synthetic_monitor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME