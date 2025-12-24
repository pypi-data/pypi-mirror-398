"""Integration tests for nginx_csg resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNginxCsg:
    """Test nginx_csg CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-nginx-csg"

    @pytest.mark.skip(reason="No spec template available for nginx_csg")
    @pytest.mark.order(1390)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a nginx_csg."""
        body = SPEC_REGISTRY.get_spec("nginx_csg", "create", test_namespace)
        result = client.nginx_csg.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for nginx_csg")
    @pytest.mark.order(1391)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a nginx_csg by name."""
        result = client.nginx_csg.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for nginx_csg")
    @pytest.mark.order(1392)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing nginx_csg resources in namespace."""
        items = client.nginx_csg.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for nginx_csg")
    @pytest.mark.order(1393)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a nginx_csg."""
        body = SPEC_REGISTRY.get_spec("nginx_csg", "replace", test_namespace)
        client.nginx_csg.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.nginx_csg.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME