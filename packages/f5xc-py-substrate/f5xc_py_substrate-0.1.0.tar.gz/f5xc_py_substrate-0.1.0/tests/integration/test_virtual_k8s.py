"""Integration tests for virtual_k8s resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVirtualK8s:
    """Test virtual_k8s CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-virtual-k8s"

    @pytest.mark.order(2180)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a virtual_k8s."""
        body = SPEC_REGISTRY.get_spec("virtual_k8s", "create", test_namespace)
        result = client.virtual_k8s.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a virtual_k8s by name."""
        result = client.virtual_k8s.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing virtual_k8s resources in namespace."""
        items = client.virtual_k8s.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a virtual_k8s."""
        body = SPEC_REGISTRY.get_spec("virtual_k8s", "replace", test_namespace)
        client.virtual_k8s.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.virtual_k8s.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97820)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the virtual_k8s."""
        client.virtual_k8s.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.virtual_k8s.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
