"""Integration tests for workload resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestWorkload:
    """Test workload CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-workload"

    @pytest.mark.order(2280)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a workload."""
        body = SPEC_REGISTRY.get_spec("workload", "create", test_namespace)
        result = client.workload.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(16501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a workload by name."""
        result = client.workload.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(16502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing workload resources in namespace."""
        items = client.workload.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(16503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a workload."""
        body = SPEC_REGISTRY.get_spec("workload", "replace", test_namespace)
        client.workload.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.workload.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97720)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the workload."""
        client.workload.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.workload.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
