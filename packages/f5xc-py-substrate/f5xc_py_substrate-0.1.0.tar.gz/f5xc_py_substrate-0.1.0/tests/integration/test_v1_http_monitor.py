"""Integration tests for v1_http_monitor resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestV1HttpMonitor:
    """Test v1_http_monitor CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-v1-http-monitor"

    @pytest.mark.order(2150)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a v1_http_monitor."""
        body = SPEC_REGISTRY.get_spec("v1_http_monitor", "create", test_namespace)
        result = client.v1_http_monitor.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a v1_http_monitor by name."""
        result = client.v1_http_monitor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing v1_http_monitor resources in namespace."""
        items = client.v1_http_monitor.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a v1_http_monitor."""
        body = SPEC_REGISTRY.get_spec("v1_http_monitor", "replace", test_namespace)
        client.v1_http_monitor.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.v1_http_monitor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97850)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the v1_http_monitor."""
        client.v1_http_monitor.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.v1_http_monitor.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
