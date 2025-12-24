"""Integration tests for rbac_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestRbacPolicy:
    """Test rbac_policy CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-rbac-policy"

    @pytest.mark.skip(reason="No spec template available for rbac_policy")
    @pytest.mark.order(1600)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a rbac_policy."""
        body = SPEC_REGISTRY.get_spec("rbac_policy", "create", test_namespace)
        result = client.rbac_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for rbac_policy")
    @pytest.mark.order(1601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a rbac_policy by name."""
        result = client.rbac_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for rbac_policy")
    @pytest.mark.order(1602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing rbac_policy resources in namespace."""
        items = client.rbac_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for rbac_policy")
    @pytest.mark.order(1603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a rbac_policy."""
        body = SPEC_REGISTRY.get_spec("rbac_policy", "replace", test_namespace)
        client.rbac_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.rbac_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME