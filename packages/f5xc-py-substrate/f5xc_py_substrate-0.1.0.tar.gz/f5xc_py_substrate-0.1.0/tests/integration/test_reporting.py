"""Integration tests for reporting resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestReporting:
    """Test reporting CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-reporting"

    @pytest.mark.skip(reason="No spec template available for reporting")
    @pytest.mark.order(1650)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a reporting."""
        body = SPEC_REGISTRY.get_spec("reporting", "create", test_namespace)
        result = client.reporting.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for reporting")
    @pytest.mark.order(1651)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a reporting by name."""
        result = client.reporting.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for reporting")
    @pytest.mark.order(1652)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing reporting resources in namespace."""
        items = client.reporting.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for reporting")
    @pytest.mark.order(1653)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a reporting."""
        body = SPEC_REGISTRY.get_spec("reporting", "replace", test_namespace)
        client.reporting.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.reporting.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME