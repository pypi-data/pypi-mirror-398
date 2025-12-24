"""Integration tests for subnet resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSubnet:
    """Test subnet CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-subnet"

    @pytest.mark.order(1900)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a subnet."""
        body = SPEC_REGISTRY.get_spec("subnet", "create", test_namespace)
        result = client.subnet.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a subnet by name."""
        result = client.subnet.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing subnet resources in namespace."""
        items = client.subnet.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a subnet."""
        body = SPEC_REGISTRY.get_spec("subnet", "replace", test_namespace)
        client.subnet.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.subnet.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98100)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the subnet."""
        client.subnet.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.subnet.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
