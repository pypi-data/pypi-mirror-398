"""Integration tests for network_policy_set resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestNetworkPolicySet:
    """Test network_policy_set CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-network-policy-set"

    @pytest.mark.skip(reason="No spec template available for network_policy_set")
    @pytest.mark.order(1360)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a network_policy_set."""
        body = SPEC_REGISTRY.get_spec("network_policy_set", "create", test_namespace)
        result = client.network_policy_set.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for network_policy_set")
    @pytest.mark.order(1361)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a network_policy_set by name."""
        result = client.network_policy_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for network_policy_set")
    @pytest.mark.order(1362)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing network_policy_set resources in namespace."""
        items = client.network_policy_set.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for network_policy_set")
    @pytest.mark.order(1363)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a network_policy_set."""
        body = SPEC_REGISTRY.get_spec("network_policy_set", "replace", test_namespace)
        client.network_policy_set.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.network_policy_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME