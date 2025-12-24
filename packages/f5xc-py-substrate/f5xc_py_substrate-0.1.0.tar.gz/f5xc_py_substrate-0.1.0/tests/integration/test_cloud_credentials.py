"""Integration tests for cloud_credentials resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCloudCredentials:
    """Test cloud_credentials CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-cloud-credentials"

    @pytest.mark.order(510)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cloud_credentials."""
        body = SPEC_REGISTRY.get_spec("cloud_credentials", "create", test_namespace)
        result = client.cloud_credentials.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cloud_credentials by name."""
        result = client.cloud_credentials.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cloud_credentials resources in namespace."""
        items = client.cloud_credentials.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cloud_credentials."""
        body = SPEC_REGISTRY.get_spec("cloud_credentials", "replace", test_namespace)
        client.cloud_credentials.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cloud_credentials.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99490)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cloud_credentials."""
        client.cloud_credentials.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cloud_credentials.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
