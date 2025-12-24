"""Integration tests for ike2 resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestIke2:
    """Test ike2 CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-ike2"

    @pytest.mark.order(930)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ike2."""
        body = SPEC_REGISTRY.get_spec("ike2", "create", test_namespace)
        result = client.ike2.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ike2 by name."""
        result = client.ike2.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ike2 resources in namespace."""
        items = client.ike2.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ike2."""
        body = SPEC_REGISTRY.get_spec("ike2", "replace", test_namespace)
        client.ike2.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ike2.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99070)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the ike2."""
        client.ike2.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.ike2.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
