"""Integration tests for alert_receiver resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAlertReceiver:
    """Test alert_receiver CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-alert-receiver"

    @pytest.mark.order(90)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a alert_receiver."""
        body = SPEC_REGISTRY.get_spec("alert_receiver", "create", test_namespace)
        result = client.alert_receiver.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a alert_receiver by name."""
        result = client.alert_receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing alert_receiver resources in namespace."""
        items = client.alert_receiver.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a alert_receiver."""
        body = SPEC_REGISTRY.get_spec("alert_receiver", "replace", test_namespace)
        client.alert_receiver.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.alert_receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99910)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the alert_receiver."""
        client.alert_receiver.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.alert_receiver.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
