"""Integration tests for alert resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAlert:
    """Test alert CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-alert"

    @pytest.mark.skip(reason="No spec template available for alert")
    @pytest.mark.order(60)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a alert."""
        body = SPEC_REGISTRY.get_spec("alert", "create", test_namespace)
        result = client.alert.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for alert")
    @pytest.mark.order(61)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a alert by name."""
        result = client.alert.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for alert")
    @pytest.mark.order(62)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing alert resources in namespace."""
        items = client.alert.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for alert")
    @pytest.mark.order(63)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a alert."""
        body = SPEC_REGISTRY.get_spec("alert", "replace", test_namespace)
        client.alert.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.alert.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME