"""Integration tests for report resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestReport:
    """Test report CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-report"

    @pytest.mark.skip(reason="No spec template available for report")
    @pytest.mark.order(1630)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a report."""
        body = SPEC_REGISTRY.get_spec("report", "create", test_namespace)
        result = client.report.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for report")
    @pytest.mark.order(1631)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a report by name."""
        result = client.report.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for report")
    @pytest.mark.order(1632)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing report resources in namespace."""
        items = client.report.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for report")
    @pytest.mark.order(1633)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a report."""
        body = SPEC_REGISTRY.get_spec("report", "replace", test_namespace)
        client.report.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.report.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME