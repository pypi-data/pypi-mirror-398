"""Integration tests for virtual_host resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVirtualHost:
    """Test virtual_host CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-virtual-host"

    @pytest.mark.skip(reason="No spec template available for virtual_host")
    @pytest.mark.order(2170)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a virtual_host."""
        body = SPEC_REGISTRY.get_spec("virtual_host", "create", test_namespace)
        result = client.virtual_host.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for virtual_host")
    @pytest.mark.order(15801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a virtual_host by name."""
        result = client.virtual_host.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for virtual_host")
    @pytest.mark.order(15802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing virtual_host resources in namespace."""
        items = client.virtual_host.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for virtual_host")
    @pytest.mark.order(15803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a virtual_host."""
        body = SPEC_REGISTRY.get_spec("virtual_host", "replace", test_namespace)
        client.virtual_host.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.virtual_host.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97830)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the virtual_host."""
        client.virtual_host.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.virtual_host.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
