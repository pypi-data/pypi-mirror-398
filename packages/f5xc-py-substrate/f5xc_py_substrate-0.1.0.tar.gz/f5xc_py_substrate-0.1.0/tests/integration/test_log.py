"""Integration tests for log resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestLog:
    """Test log CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-log"

    @pytest.mark.skip(reason="No spec template available for log")
    @pytest.mark.order(1180)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a log."""
        body = SPEC_REGISTRY.get_spec("log", "create", test_namespace)
        result = client.log.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for log")
    @pytest.mark.order(1181)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a log by name."""
        result = client.log.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for log")
    @pytest.mark.order(1182)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing log resources in namespace."""
        items = client.log.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for log")
    @pytest.mark.order(1183)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a log."""
        body = SPEC_REGISTRY.get_spec("log", "replace", test_namespace)
        client.log.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.log.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME