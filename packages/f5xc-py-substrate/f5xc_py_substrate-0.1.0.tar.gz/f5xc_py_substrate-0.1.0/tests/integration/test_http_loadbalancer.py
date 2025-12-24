"""Integration tests for http_loadbalancer resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestHttpLoadbalancer:
    """Test http_loadbalancer CRUD operations.

    Status: complete
    Notes: References origin_pool via default_route_pools
    """

    RESOURCE_NAME = "sdk-test-http-loadbalancer"

    @pytest.mark.order(1450)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a http_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("http_loadbalancer", "create", test_namespace)
        result = client.http_loadbalancer.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(10901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a http_loadbalancer by name."""
        result = client.http_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(10902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing http_loadbalancer resources in namespace."""
        items = client.http_loadbalancer.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(10903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a http_loadbalancer."""
        body = SPEC_REGISTRY.get_spec("http_loadbalancer", "replace", test_namespace)
        client.http_loadbalancer.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.http_loadbalancer.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98550)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the http_loadbalancer."""
        client.http_loadbalancer.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.http_loadbalancer.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
