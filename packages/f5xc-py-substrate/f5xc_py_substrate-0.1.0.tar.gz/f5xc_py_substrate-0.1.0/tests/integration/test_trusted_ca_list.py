"""Integration tests for trusted_ca_list resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTrustedCaList:
    """Test trusted_ca_list CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-trusted-ca-list"

    @pytest.mark.order(2040)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a trusted_ca_list."""
        body = SPEC_REGISTRY.get_spec("trusted_ca_list", "create", test_namespace)
        result = client.trusted_ca_list.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a trusted_ca_list by name."""
        result = client.trusted_ca_list.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing trusted_ca_list resources in namespace."""
        items = client.trusted_ca_list.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a trusted_ca_list."""
        body = SPEC_REGISTRY.get_spec("trusted_ca_list", "replace", test_namespace)
        client.trusted_ca_list.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.trusted_ca_list.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97960)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the trusted_ca_list."""
        client.trusted_ca_list.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.trusted_ca_list.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
