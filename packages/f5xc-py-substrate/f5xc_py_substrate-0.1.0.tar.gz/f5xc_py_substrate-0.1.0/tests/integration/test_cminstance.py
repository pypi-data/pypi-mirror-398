"""Integration tests for cminstance resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCminstance:
    """Test cminstance CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-cminstance"

    @pytest.mark.skip(reason="No spec template available for cminstance")
    @pytest.mark.order(560)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cminstance."""
        body = SPEC_REGISTRY.get_spec("cminstance", "create", test_namespace)
        result = client.cminstance.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for cminstance")
    @pytest.mark.order(4401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cminstance by name."""
        result = client.cminstance.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for cminstance")
    @pytest.mark.order(4402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cminstance resources in namespace."""
        items = client.cminstance.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for cminstance")
    @pytest.mark.order(4403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cminstance."""
        body = SPEC_REGISTRY.get_spec("cminstance", "replace", test_namespace)
        client.cminstance.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cminstance.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99440)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cminstance."""
        client.cminstance.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cminstance.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
