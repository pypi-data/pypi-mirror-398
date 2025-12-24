"""Integration tests for tpm_manager resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTpmManager:
    """Test tpm_manager CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-tpm-manager"

    @pytest.mark.order(2020)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tpm_manager."""
        body = SPEC_REGISTRY.get_spec("tpm_manager", "create", test_namespace)
        result = client.tpm_manager.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tpm_manager by name."""
        result = client.tpm_manager.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tpm_manager resources in namespace."""
        items = client.tpm_manager.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tpm_manager."""
        body = SPEC_REGISTRY.get_spec("tpm_manager", "replace", test_namespace)
        client.tpm_manager.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tpm_manager.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97980)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tpm_manager."""
        client.tpm_manager.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tpm_manager.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
