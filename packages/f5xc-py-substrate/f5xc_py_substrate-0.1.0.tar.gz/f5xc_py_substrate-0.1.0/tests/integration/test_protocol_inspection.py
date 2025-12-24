"""Integration tests for protocol_inspection resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestProtocolInspection:
    """Test protocol_inspection CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-protocol-inspection"

    @pytest.mark.order(1530)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a protocol_inspection."""
        body = SPEC_REGISTRY.get_spec("protocol_inspection", "create", test_namespace)
        result = client.protocol_inspection.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(11501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a protocol_inspection by name."""
        result = client.protocol_inspection.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(11502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing protocol_inspection resources in namespace."""
        items = client.protocol_inspection.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(11503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a protocol_inspection."""
        body = SPEC_REGISTRY.get_spec("protocol_inspection", "replace", test_namespace)
        client.protocol_inspection.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.protocol_inspection.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98470)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the protocol_inspection."""
        client.protocol_inspection.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.protocol_inspection.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
