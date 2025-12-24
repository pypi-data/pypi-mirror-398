"""Integration tests for policy_based_routing resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestPolicyBasedRouting:
    """Test policy_based_routing CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-policy-based-routing"

    @pytest.mark.order(1500)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a policy_based_routing."""
        body = SPEC_REGISTRY.get_spec("policy_based_routing", "create", test_namespace)
        result = client.policy_based_routing.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(11201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a policy_based_routing by name."""
        result = client.policy_based_routing.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(11202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing policy_based_routing resources in namespace."""
        items = client.policy_based_routing.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(11203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a policy_based_routing."""
        body = SPEC_REGISTRY.get_spec("policy_based_routing", "replace", test_namespace)
        client.policy_based_routing.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.policy_based_routing.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98500)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the policy_based_routing."""
        client.policy_based_routing.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.policy_based_routing.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
