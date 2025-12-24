"""Integration tests for voltshare resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVoltshare:
    """Test voltshare CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-voltshare"

    @pytest.mark.skip(reason="No spec template available for voltshare")
    @pytest.mark.order(2210)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a voltshare."""
        body = SPEC_REGISTRY.get_spec("voltshare", "create", test_namespace)
        result = client.voltshare.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for voltshare")
    @pytest.mark.order(2211)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a voltshare by name."""
        result = client.voltshare.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for voltshare")
    @pytest.mark.order(2212)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing voltshare resources in namespace."""
        items = client.voltshare.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for voltshare")
    @pytest.mark.order(2213)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a voltshare."""
        body = SPEC_REGISTRY.get_spec("voltshare", "replace", test_namespace)
        client.voltshare.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.voltshare.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME