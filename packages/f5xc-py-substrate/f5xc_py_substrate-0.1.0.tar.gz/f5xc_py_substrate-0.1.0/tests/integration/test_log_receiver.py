"""Integration tests for log_receiver resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestLogReceiver:
    """Test log_receiver CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-log-receiver"

    @pytest.mark.order(1190)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a log_receiver."""
        body = SPEC_REGISTRY.get_spec("log_receiver", "create", test_namespace)
        result = client.log_receiver.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(9301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a log_receiver by name."""
        result = client.log_receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(9302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing log_receiver resources in namespace."""
        items = client.log_receiver.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(9303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a log_receiver."""
        body = SPEC_REGISTRY.get_spec("log_receiver", "replace", test_namespace)
        client.log_receiver.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.log_receiver.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98810)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the log_receiver."""
        client.log_receiver.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.log_receiver.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
