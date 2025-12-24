"""Integration tests for cloud_link resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCloudLink:
    """Test cloud_link CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-cloud-link"

    @pytest.mark.order(530)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cloud_link."""
        body = SPEC_REGISTRY.get_spec("cloud_link", "create", test_namespace)
        result = client.cloud_link.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(4101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cloud_link by name."""
        result = client.cloud_link.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(4102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cloud_link resources in namespace."""
        items = client.cloud_link.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(4103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cloud_link."""
        body = SPEC_REGISTRY.get_spec("cloud_link", "replace", test_namespace)
        client.cloud_link.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cloud_link.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99470)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cloud_link."""
        client.cloud_link.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cloud_link.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
