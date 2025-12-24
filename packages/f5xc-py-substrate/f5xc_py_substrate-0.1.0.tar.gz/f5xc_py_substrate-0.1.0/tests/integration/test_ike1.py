"""Integration tests for ike1 resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestIke1:
    """Test ike1 CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-ike1"

    @pytest.mark.order(920)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ike1."""
        body = SPEC_REGISTRY.get_spec("ike1", "create", test_namespace)
        result = client.ike1.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ike1 by name."""
        result = client.ike1.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ike1 resources in namespace."""
        items = client.ike1.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ike1."""
        body = SPEC_REGISTRY.get_spec("ike1", "replace", test_namespace)
        client.ike1.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ike1.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99080)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the ike1."""
        client.ike1.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.ike1.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
