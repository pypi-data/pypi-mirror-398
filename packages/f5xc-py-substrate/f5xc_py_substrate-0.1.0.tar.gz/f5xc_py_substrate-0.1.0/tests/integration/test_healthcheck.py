"""Integration tests for healthcheck resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestHealthcheck:
    """Test healthcheck CRUD operations.

    Status: complete
    Notes: Simple standalone resource, no dependencies
    """

    RESOURCE_NAME = "sdk-test-healthcheck"

    @pytest.mark.order(910)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a healthcheck."""
        body = SPEC_REGISTRY.get_spec("healthcheck", "create", test_namespace)
        result = client.healthcheck.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a healthcheck by name."""
        result = client.healthcheck.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing healthcheck resources in namespace."""
        items = client.healthcheck.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a healthcheck."""
        body = SPEC_REGISTRY.get_spec("healthcheck", "replace", test_namespace)
        client.healthcheck.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.healthcheck.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99090)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the healthcheck."""
        client.healthcheck.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.healthcheck.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
