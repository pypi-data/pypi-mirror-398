"""Integration tests for nfv_service resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNfvService:
    """Test nfv_service CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-nfv-service"

    @pytest.mark.order(1380)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a nfv_service."""
        body = SPEC_REGISTRY.get_spec("nfv_service", "create", test_namespace)
        result = client.nfv_service.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(10501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a nfv_service by name."""
        result = client.nfv_service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(10502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing nfv_service resources in namespace."""
        items = client.nfv_service.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(10503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a nfv_service."""
        body = SPEC_REGISTRY.get_spec("nfv_service", "replace", test_namespace)
        client.nfv_service.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.nfv_service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98620)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the nfv_service."""
        client.nfv_service.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.nfv_service.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
