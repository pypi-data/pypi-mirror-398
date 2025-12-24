"""Integration tests for tpm_api_key resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTpmApiKey:
    """Test tpm_api_key CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-tpm-api-key"

    @pytest.mark.order(2000)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a tpm_api_key."""
        body = SPEC_REGISTRY.get_spec("tpm_api_key", "create", test_namespace)
        result = client.tpm_api_key.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(14701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a tpm_api_key by name."""
        result = client.tpm_api_key.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(14702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing tpm_api_key resources in namespace."""
        items = client.tpm_api_key.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(14703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a tpm_api_key."""
        body = SPEC_REGISTRY.get_spec("tpm_api_key", "replace", test_namespace)
        client.tpm_api_key.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.tpm_api_key.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98000)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the tpm_api_key."""
        client.tpm_api_key.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.tpm_api_key.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
