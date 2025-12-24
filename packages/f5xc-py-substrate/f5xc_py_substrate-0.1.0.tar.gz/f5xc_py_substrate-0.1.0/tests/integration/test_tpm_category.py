"""Integration tests for tpm_category resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTpmCategory:
    """Test tpm_category CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-tpm-category"

    @pytest.mark.order(2010)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tpm_category."""
        body = SPEC_REGISTRY.get_spec("tpm_category", "create", test_namespace)
        result = client.tpm_category.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tpm_category by name."""
        result = client.tpm_category.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tpm_category resources in namespace."""
        items = client.tpm_category.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tpm_category."""
        body = SPEC_REGISTRY.get_spec("tpm_category", "replace", test_namespace)
        client.tpm_category.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tpm_category.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97990)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tpm_category."""
        client.tpm_category.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tpm_category.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
