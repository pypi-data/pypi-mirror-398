"""Integration tests for k8s_cluster_role resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestK8sClusterRole:
    """Test k8s_cluster_role CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-k8s-cluster-role"

    @pytest.mark.order(1100)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a k8s_cluster_role."""
        body = SPEC_REGISTRY.get_spec("k8s_cluster_role", "create", test_namespace)
        result = client.k8s_cluster_role.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a k8s_cluster_role by name."""
        result = client.k8s_cluster_role.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing k8s_cluster_role resources in namespace."""
        items = client.k8s_cluster_role.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a k8s_cluster_role."""
        body = SPEC_REGISTRY.get_spec("k8s_cluster_role", "replace", test_namespace)
        client.k8s_cluster_role.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.k8s_cluster_role.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98900)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the k8s_cluster_role."""
        client.k8s_cluster_role.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.k8s_cluster_role.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
