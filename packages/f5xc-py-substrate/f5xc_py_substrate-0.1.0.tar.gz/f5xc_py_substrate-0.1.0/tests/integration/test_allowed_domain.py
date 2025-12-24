"""Integration tests for allowed_domain resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAllowedDomain:
    """Test allowed_domain CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-allowed-domain"

    @pytest.mark.order(110)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a allowed_domain."""
        body = SPEC_REGISTRY.get_spec("allowed_domain", "create", test_namespace)
        result = client.allowed_domain.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a allowed_domain by name."""
        result = client.allowed_domain.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing allowed_domain resources in namespace."""
        items = client.allowed_domain.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a allowed_domain."""
        body = SPEC_REGISTRY.get_spec("allowed_domain", "replace", test_namespace)
        client.allowed_domain.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.allowed_domain.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99890)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the allowed_domain."""
        client.allowed_domain.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.allowed_domain.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
