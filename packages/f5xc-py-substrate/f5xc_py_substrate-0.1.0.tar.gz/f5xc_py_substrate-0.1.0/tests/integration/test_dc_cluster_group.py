"""Integration tests for dc_cluster_group resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDcClusterGroup:
    """Test dc_cluster_group CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-dc-cluster-group"

    @pytest.mark.order(660)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a dc_cluster_group."""
        body = SPEC_REGISTRY.get_spec("dc_cluster_group", "create", test_namespace)
        result = client.dc_cluster_group.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a dc_cluster_group by name."""
        result = client.dc_cluster_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing dc_cluster_group resources in namespace."""
        items = client.dc_cluster_group.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a dc_cluster_group."""
        body = SPEC_REGISTRY.get_spec("dc_cluster_group", "replace", test_namespace)
        client.dc_cluster_group.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.dc_cluster_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99340)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the dc_cluster_group."""
        client.dc_cluster_group.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.dc_cluster_group.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
