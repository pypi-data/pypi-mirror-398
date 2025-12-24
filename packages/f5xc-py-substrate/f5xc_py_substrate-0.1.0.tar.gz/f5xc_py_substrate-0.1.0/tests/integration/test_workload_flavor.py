"""Integration tests for workload_flavor resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestWorkloadFlavor:
    """Test workload_flavor CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-workload-flavor"

    @pytest.mark.order(2290)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a workload_flavor."""
        body = SPEC_REGISTRY.get_spec("workload_flavor", "create", test_namespace)
        result = client.workload_flavor.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(16601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a workload_flavor by name."""
        result = client.workload_flavor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(16602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing workload_flavor resources in namespace."""
        items = client.workload_flavor.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(16603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a workload_flavor."""
        body = SPEC_REGISTRY.get_spec("workload_flavor", "replace", test_namespace)
        client.workload_flavor.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.workload_flavor.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97710)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the workload_flavor."""
        client.workload_flavor.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.workload_flavor.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
