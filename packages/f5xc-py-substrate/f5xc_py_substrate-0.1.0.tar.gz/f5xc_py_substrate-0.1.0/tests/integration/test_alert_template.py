"""Integration tests for alert_template resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAlertTemplate:
    """Test alert_template CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-alert-template"

    @pytest.mark.order(100)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a alert_template."""
        body = SPEC_REGISTRY.get_spec("alert_template", "create", test_namespace)
        result = client.alert_template.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a alert_template by name."""
        result = client.alert_template.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing alert_template resources in namespace."""
        items = client.alert_template.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a alert_template."""
        body = SPEC_REGISTRY.get_spec("alert_template", "replace", test_namespace)
        client.alert_template.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.alert_template.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99900)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the alert_template."""
        client.alert_template.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.alert_template.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
