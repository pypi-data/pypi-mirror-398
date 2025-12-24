"""Integration tests for cloud_region resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCloudRegion:
    """Test cloud_region CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-cloud-region"

    @pytest.mark.skip(reason="No spec template available for cloud_region")
    @pytest.mark.order(540)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cloud_region."""
        body = SPEC_REGISTRY.get_spec("cloud_region", "create", test_namespace)
        result = client.cloud_region.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for cloud_region")
    @pytest.mark.order(4201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cloud_region by name."""
        result = client.cloud_region.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for cloud_region")
    @pytest.mark.order(4202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cloud_region resources in namespace."""
        items = client.cloud_region.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for cloud_region")
    @pytest.mark.order(4203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cloud_region."""
        body = SPEC_REGISTRY.get_spec("cloud_region", "replace", test_namespace)
        client.cloud_region.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cloud_region.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99460)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cloud_region."""
        client.cloud_region.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cloud_region.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
