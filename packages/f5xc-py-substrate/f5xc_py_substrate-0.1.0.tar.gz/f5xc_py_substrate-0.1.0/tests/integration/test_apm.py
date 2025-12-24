"""Integration tests for apm resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestApm:
    """Test apm CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual...
    """

    RESOURCE_NAME = "sdk-test-apm"

    @pytest.mark.order(200)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a apm."""
        body = SPEC_REGISTRY.get_spec("apm", "create", test_namespace)
        result = client.apm.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(1401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a apm by name."""
        result = client.apm.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(1402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing apm resources in namespace."""
        items = client.apm.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(1403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a apm."""
        body = SPEC_REGISTRY.get_spec("apm", "replace", test_namespace)
        client.apm.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.apm.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99800)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the apm."""
        client.apm.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.apm.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
