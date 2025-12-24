"""Integration tests for tunnel resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTunnel:
    """Test tunnel CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-tunnel"

    @pytest.mark.order(2050)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tunnel."""
        body = SPEC_REGISTRY.get_spec("tunnel", "create", test_namespace)
        result = client.tunnel.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tunnel by name."""
        result = client.tunnel.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tunnel resources in namespace."""
        items = client.tunnel.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tunnel."""
        body = SPEC_REGISTRY.get_spec("tunnel", "replace", test_namespace)
        client.tunnel.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tunnel.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97950)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tunnel."""
        client.tunnel.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tunnel.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
