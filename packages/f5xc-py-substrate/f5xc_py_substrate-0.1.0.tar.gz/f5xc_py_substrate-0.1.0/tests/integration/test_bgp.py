"""Integration tests for bgp resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBgp:
    """Test bgp CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-bgp"

    @pytest.mark.order(300)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bgp."""
        body = SPEC_REGISTRY.get_spec("bgp", "create", test_namespace)
        result = client.bgp.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(2201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bgp by name."""
        result = client.bgp.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(2202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bgp resources in namespace."""
        items = client.bgp.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(2203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bgp."""
        body = SPEC_REGISTRY.get_spec("bgp", "replace", test_namespace)
        client.bgp.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bgp.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99700)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bgp."""
        client.bgp.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bgp.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
