"""Integration tests for namespace_role resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNamespaceRole:
    """Test namespace_role CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-namespace-role"

    @pytest.mark.skip(reason="No spec template available for namespace_role")
    @pytest.mark.order(1280)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a namespace_role."""
        body = SPEC_REGISTRY.get_spec("namespace_role", "create", test_namespace)
        result = client.namespace_role.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for namespace_role")
    @pytest.mark.order(1281)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a namespace_role by name."""
        result = client.namespace_role.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for namespace_role")
    @pytest.mark.order(1282)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing namespace_role resources in namespace."""
        items = client.namespace_role.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for namespace_role")
    @pytest.mark.order(1283)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a namespace_role."""
        body = SPEC_REGISTRY.get_spec("namespace_role", "replace", test_namespace)
        client.namespace_role.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.namespace_role.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME