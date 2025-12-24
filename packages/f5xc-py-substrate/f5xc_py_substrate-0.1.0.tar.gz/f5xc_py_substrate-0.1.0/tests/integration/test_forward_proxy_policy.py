"""Integration tests for forward_proxy_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestForwardProxyPolicy:
    """Test forward_proxy_policy CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-forward-proxy-policy"

    @pytest.mark.skip(reason="No spec template available for forward_proxy_policy")
    @pytest.mark.order(850)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a forward_proxy_policy."""
        body = SPEC_REGISTRY.get_spec("forward_proxy_policy", "create", test_namespace)
        result = client.forward_proxy_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for forward_proxy_policy")
    @pytest.mark.order(851)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a forward_proxy_policy by name."""
        result = client.forward_proxy_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for forward_proxy_policy")
    @pytest.mark.order(852)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing forward_proxy_policy resources in namespace."""
        items = client.forward_proxy_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for forward_proxy_policy")
    @pytest.mark.order(853)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a forward_proxy_policy."""
        body = SPEC_REGISTRY.get_spec("forward_proxy_policy", "replace", test_namespace)
        client.forward_proxy_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.forward_proxy_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME