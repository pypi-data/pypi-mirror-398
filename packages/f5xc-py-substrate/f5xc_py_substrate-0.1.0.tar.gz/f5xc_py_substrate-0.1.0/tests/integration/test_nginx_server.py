"""Integration tests for nginx_server resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNginxServer:
    """Test nginx_server CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-nginx-server"

    @pytest.mark.skip(reason="No spec template available for nginx_server")
    @pytest.mark.order(1410)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a nginx_server."""
        body = SPEC_REGISTRY.get_spec("nginx_server", "create", test_namespace)
        result = client.nginx_server.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for nginx_server")
    @pytest.mark.order(1411)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a nginx_server by name."""
        result = client.nginx_server.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for nginx_server")
    @pytest.mark.order(1412)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing nginx_server resources in namespace."""
        items = client.nginx_server.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for nginx_server")
    @pytest.mark.order(1413)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a nginx_server."""
        body = SPEC_REGISTRY.get_spec("nginx_server", "replace", test_namespace)
        client.nginx_server.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.nginx_server.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME