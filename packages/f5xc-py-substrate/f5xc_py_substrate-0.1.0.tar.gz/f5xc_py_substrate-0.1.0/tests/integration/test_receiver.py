"""Integration tests for receiver resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestReceiver:
    """Test receiver CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-receiver"

    @pytest.mark.order(1610)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a receiver."""
        body = SPEC_REGISTRY.get_spec("receiver", "create", test_namespace)
        result = client.receiver.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(12101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a receiver by name."""
        result = client.receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(12102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing receiver resources in namespace."""
        items = client.receiver.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(12103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a receiver."""
        body = SPEC_REGISTRY.get_spec("receiver", "replace", test_namespace)
        client.receiver.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98390)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the receiver."""
        client.receiver.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.receiver.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
