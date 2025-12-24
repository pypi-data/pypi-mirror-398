"""Integration tests for cdn_loadbalancer resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCdnLoadbalancer:
    """Test cdn_loadbalancer CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-cdn-loadbalancer"

    @pytest.mark.order(430)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cdn_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("cdn_loadbalancer", "create", test_namespace)
        result = client.cdn_loadbalancer.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cdn_loadbalancer by name."""
        result = client.cdn_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cdn_loadbalancer resources in namespace."""
        items = client.cdn_loadbalancer.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cdn_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("cdn_loadbalancer", "replace", test_namespace)
        client.cdn_loadbalancer.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cdn_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99570)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cdn_loadbalancer."""
        client.cdn_loadbalancer.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cdn_loadbalancer.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
