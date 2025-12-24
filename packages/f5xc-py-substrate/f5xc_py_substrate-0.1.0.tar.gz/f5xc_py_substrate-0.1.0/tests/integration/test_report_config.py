"""Integration tests for report_config resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestReportConfig:
    """Test report_config CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-report-config"

    @pytest.mark.skip(reason="No spec template available for report_config")
    @pytest.mark.order(1640)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a report_config."""
        body = SPEC_REGISTRY.get_spec("report_config", "create", test_namespace)
        result = client.report_config.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for report_config")
    @pytest.mark.order(12301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a report_config by name."""
        result = client.report_config.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for report_config")
    @pytest.mark.order(12302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing report_config resources in namespace."""
        items = client.report_config.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for report_config")
    @pytest.mark.order(12303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a report_config."""
        body = SPEC_REGISTRY.get_spec("report_config", "replace", test_namespace)
        client.report_config.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.report_config.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98360)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the report_config."""
        client.report_config.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.report_config.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
