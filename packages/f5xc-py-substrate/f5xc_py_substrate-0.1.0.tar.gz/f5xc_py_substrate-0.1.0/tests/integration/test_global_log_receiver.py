"""Integration tests for global_log_receiver resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestGlobalLogReceiver:
    """Test global_log_receiver CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-global-log-receiver"

    @pytest.mark.order(900)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a global_log_receiver."""
        body = SPEC_REGISTRY.get_spec("global_log_receiver", "create", test_namespace)
        result = client.global_log_receiver.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a global_log_receiver by name."""
        result = client.global_log_receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing global_log_receiver resources in namespace."""
        items = client.global_log_receiver.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a global_log_receiver."""
        body = SPEC_REGISTRY.get_spec("global_log_receiver", "replace", test_namespace)
        client.global_log_receiver.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.global_log_receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99100)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the global_log_receiver."""
        client.global_log_receiver.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.global_log_receiver.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
