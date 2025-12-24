"""Integration tests for ticket_tracking_system resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTicketTrackingSystem:
    """Test ticket_tracking_system CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-ticket-tracking-system"

    @pytest.mark.order(1980)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ticket_tracking_system."""
        body = SPEC_REGISTRY.get_spec("ticket_tracking_system", "create", test_namespace)
        result = client.ticket_tracking_system.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ticket_tracking_system by name."""
        result = client.ticket_tracking_system.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ticket_tracking_system resources in namespace."""
        items = client.ticket_tracking_system.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ticket_tracking_system."""
        body = SPEC_REGISTRY.get_spec("ticket_tracking_system", "replace", test_namespace)
        client.ticket_tracking_system.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ticket_tracking_system.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98020)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the ticket_tracking_system."""
        client.ticket_tracking_system.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.ticket_tracking_system.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
