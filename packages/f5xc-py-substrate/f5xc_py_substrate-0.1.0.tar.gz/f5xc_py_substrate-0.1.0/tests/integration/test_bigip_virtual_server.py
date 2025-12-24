"""Integration tests for bigip_virtual_server resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBigipVirtualServer:
    """Test bigip_virtual_server CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-bigip-virtual-server"

    @pytest.mark.skip(reason="No spec template available for bigip_virtual_server")
    @pytest.mark.order(340)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bigip_virtual_server."""
        body = SPEC_REGISTRY.get_spec("bigip_virtual_server", "create", test_namespace)
        result = client.bigip_virtual_server.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for bigip_virtual_server")
    @pytest.mark.order(2601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bigip_virtual_server by name."""
        result = client.bigip_virtual_server.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for bigip_virtual_server")
    @pytest.mark.order(2602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bigip_virtual_server resources in namespace."""
        items = client.bigip_virtual_server.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for bigip_virtual_server")
    @pytest.mark.order(2603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bigip_virtual_server."""
        body = SPEC_REGISTRY.get_spec("bigip_virtual_server", "replace", test_namespace)
        client.bigip_virtual_server.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bigip_virtual_server.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99660)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bigip_virtual_server."""
        client.bigip_virtual_server.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bigip_virtual_server.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
