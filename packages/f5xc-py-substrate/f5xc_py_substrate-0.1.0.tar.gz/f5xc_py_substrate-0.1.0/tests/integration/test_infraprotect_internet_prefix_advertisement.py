"""Integration tests for infraprotect_internet_prefix_advertisement resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectInternetPrefixAdvertisement:
    """Test infraprotect_internet_prefix_advertisement CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-infraprotect-internet-prefix-advertisement"

    @pytest.mark.order(1040)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_internet_prefix_advertisement."""
        body = SPEC_REGISTRY.get_spec("infraprotect_internet_prefix_advertisement", "create", test_namespace)
        result = client.infraprotect_internet_prefix_advertisement.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_internet_prefix_advertisement by name."""
        result = client.infraprotect_internet_prefix_advertisement.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_internet_prefix_advertisement resources in namespace."""
        items = client.infraprotect_internet_prefix_advertisement.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_internet_prefix_advertisement."""
        body = SPEC_REGISTRY.get_spec("infraprotect_internet_prefix_advertisement", "replace", test_namespace)
        client.infraprotect_internet_prefix_advertisement.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_internet_prefix_advertisement.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98960)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the infraprotect_internet_prefix_advertisement."""
        client.infraprotect_internet_prefix_advertisement.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.infraprotect_internet_prefix_advertisement.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
