"""Integration tests for crl resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCrl:
    """Test crl CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-crl"

    @pytest.mark.order(610)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a crl."""
        body = SPEC_REGISTRY.get_spec("crl", "create", test_namespace)
        result = client.crl.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(4801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a crl by name."""
        result = client.crl.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(4802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing crl resources in namespace."""
        items = client.crl.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(4803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a crl."""
        body = SPEC_REGISTRY.get_spec("crl", "replace", test_namespace)
        client.crl.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.crl.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99390)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the crl."""
        client.crl.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.crl.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
