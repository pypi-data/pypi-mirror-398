"""Integration tests for cloud_elastic_ip resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCloudElasticIp:
    """Test cloud_elastic_ip CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-cloud-elastic-ip"

    @pytest.mark.order(520)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cloud_elastic_ip."""
        body = SPEC_REGISTRY.get_spec("cloud_elastic_ip", "create", test_namespace)
        result = client.cloud_elastic_ip.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(4001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cloud_elastic_ip by name."""
        result = client.cloud_elastic_ip.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(4002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cloud_elastic_ip resources in namespace."""
        items = client.cloud_elastic_ip.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(4003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cloud_elastic_ip."""
        body = SPEC_REGISTRY.get_spec("cloud_elastic_ip", "replace", test_namespace)
        client.cloud_elastic_ip.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cloud_elastic_ip.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99480)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cloud_elastic_ip."""
        client.cloud_elastic_ip.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cloud_elastic_ip.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
