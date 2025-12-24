"""Integration tests for quota resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestQuota:
    """Test quota CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-quota"

    @pytest.mark.skip(reason="No spec template available for quota")
    @pytest.mark.order(1570)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a quota."""
        body = SPEC_REGISTRY.get_spec("quota", "create", test_namespace)
        result = client.quota.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for quota")
    @pytest.mark.order(11801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a quota by name."""
        result = client.quota.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for quota")
    @pytest.mark.order(11802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing quota resources in namespace."""
        items = client.quota.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for quota")
    @pytest.mark.order(11803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a quota."""
        body = SPEC_REGISTRY.get_spec("quota", "replace", test_namespace)
        client.quota.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.quota.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98430)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the quota."""
        client.quota.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.quota.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
