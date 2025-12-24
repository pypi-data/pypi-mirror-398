"""Integration tests for service_policy_set resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestServicePolicySet:
    """Test service_policy_set CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-service-policy-set"

    @pytest.mark.skip(reason="No spec template available for service_policy_set")
    @pytest.mark.order(1820)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a service_policy_set."""
        body = SPEC_REGISTRY.get_spec("service_policy_set", "create", test_namespace)
        result = client.service_policy_set.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for service_policy_set")
    @pytest.mark.order(1821)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a service_policy_set by name."""
        result = client.service_policy_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for service_policy_set")
    @pytest.mark.order(1822)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing service_policy_set resources in namespace."""
        items = client.service_policy_set.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for service_policy_set")
    @pytest.mark.order(1823)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a service_policy_set."""
        body = SPEC_REGISTRY.get_spec("service_policy_set", "replace", test_namespace)
        client.service_policy_set.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.service_policy_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME