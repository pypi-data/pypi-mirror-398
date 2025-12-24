"""Integration tests for enhanced_firewall_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestEnhancedFirewallPolicy:
    """Test enhanced_firewall_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-enhanced-firewall-policy"

    @pytest.mark.order(780)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a enhanced_firewall_policy."""
        body = SPEC_REGISTRY.get_spec("enhanced_firewall_policy", "create", test_namespace)
        result = client.enhanced_firewall_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(6201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a enhanced_firewall_policy by name."""
        result = client.enhanced_firewall_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(6202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing enhanced_firewall_policy resources in namespace."""
        items = client.enhanced_firewall_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(6203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a enhanced_firewall_policy."""
        body = SPEC_REGISTRY.get_spec("enhanced_firewall_policy", "replace", test_namespace)
        client.enhanced_firewall_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.enhanced_firewall_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99220)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the enhanced_firewall_policy."""
        client.enhanced_firewall_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.enhanced_firewall_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
