"""Integration tests for srv6_network_slice resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSrv6NetworkSlice:
    """Test srv6_network_slice CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-srv6-network-slice"

    @pytest.mark.order(1860)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a srv6_network_slice."""
        body = SPEC_REGISTRY.get_spec("srv6_network_slice", "create", test_namespace)
        result = client.srv6_network_slice.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(13801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a srv6_network_slice by name."""
        result = client.srv6_network_slice.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(13802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing srv6_network_slice resources in namespace."""
        items = client.srv6_network_slice.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(13803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a srv6_network_slice."""
        body = SPEC_REGISTRY.get_spec("srv6_network_slice", "replace", test_namespace)
        client.srv6_network_slice.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.srv6_network_slice.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98140)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the srv6_network_slice."""
        client.srv6_network_slice.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.srv6_network_slice.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
