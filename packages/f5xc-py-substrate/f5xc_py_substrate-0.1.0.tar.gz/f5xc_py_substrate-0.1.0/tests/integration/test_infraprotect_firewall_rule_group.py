"""Integration tests for infraprotect_firewall_rule_group resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectFirewallRuleGroup:
    """Test infraprotect_firewall_rule_group CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-infraprotect-firewall-rule-group"

    @pytest.mark.order(1010)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_firewall_rule_group."""
        body = SPEC_REGISTRY.get_spec("infraprotect_firewall_rule_group", "create", test_namespace)
        result = client.infraprotect_firewall_rule_group.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(8001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_firewall_rule_group by name."""
        result = client.infraprotect_firewall_rule_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(8002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_firewall_rule_group resources in namespace."""
        items = client.infraprotect_firewall_rule_group.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(8003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_firewall_rule_group."""
        body = SPEC_REGISTRY.get_spec("infraprotect_firewall_rule_group", "replace", test_namespace)
        client.infraprotect_firewall_rule_group.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_firewall_rule_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98990)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the infraprotect_firewall_rule_group."""
        client.infraprotect_firewall_rule_group.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.infraprotect_firewall_rule_group.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
