"""Integration tests for nginx_instance resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNginxInstance:
    """Test nginx_instance CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-nginx-instance"

    @pytest.mark.skip(reason="No spec template available for nginx_instance")
    @pytest.mark.order(1400)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a nginx_instance."""
        body = SPEC_REGISTRY.get_spec("nginx_instance", "create", test_namespace)
        result = client.nginx_instance.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for nginx_instance")
    @pytest.mark.order(1401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a nginx_instance by name."""
        result = client.nginx_instance.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for nginx_instance")
    @pytest.mark.order(1402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing nginx_instance resources in namespace."""
        items = client.nginx_instance.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for nginx_instance")
    @pytest.mark.order(1403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a nginx_instance."""
        body = SPEC_REGISTRY.get_spec("nginx_instance", "replace", test_namespace)
        client.nginx_instance.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.nginx_instance.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME