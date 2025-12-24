"""Integration tests for infraprotect_tunnel resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectTunnel:
    """Test infraprotect_tunnel CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-infraprotect-tunnel"

    @pytest.mark.order(1050)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_tunnel."""
        body = SPEC_REGISTRY.get_spec("infraprotect_tunnel", "create", test_namespace)
        result = client.infraprotect_tunnel.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_tunnel by name."""
        result = client.infraprotect_tunnel.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_tunnel resources in namespace."""
        items = client.infraprotect_tunnel.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_tunnel."""
        body = SPEC_REGISTRY.get_spec("infraprotect_tunnel", "replace", test_namespace)
        client.infraprotect_tunnel.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_tunnel.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98950)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the infraprotect_tunnel."""
        client.infraprotect_tunnel.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.infraprotect_tunnel.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
