"""Integration tests for infraprotect_asn resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectAsn:
    """Test infraprotect_asn CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-infraprotect-asn"

    @pytest.mark.order(970)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_asn."""
        body = SPEC_REGISTRY.get_spec("infraprotect_asn", "create", test_namespace)
        result = client.infraprotect_asn.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_asn by name."""
        result = client.infraprotect_asn.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_asn resources in namespace."""
        items = client.infraprotect_asn.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_asn."""
        body = SPEC_REGISTRY.get_spec("infraprotect_asn", "replace", test_namespace)
        client.infraprotect_asn.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_asn.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99030)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the infraprotect_asn."""
        client.infraprotect_asn.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.infraprotect_asn.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
