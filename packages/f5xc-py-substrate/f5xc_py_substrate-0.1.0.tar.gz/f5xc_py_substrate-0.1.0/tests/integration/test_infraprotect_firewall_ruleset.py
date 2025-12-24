"""Integration tests for infraprotect_firewall_ruleset resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectFirewallRuleset:
    """Test infraprotect_firewall_ruleset CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-infraprotect-firewall-ruleset"

    @pytest.mark.skip(reason="No spec template available for infraprotect_firewall_ruleset")
    @pytest.mark.order(1020)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_firewall_ruleset."""
        body = SPEC_REGISTRY.get_spec("infraprotect_firewall_ruleset", "create", test_namespace)
        result = client.infraprotect_firewall_ruleset.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for infraprotect_firewall_ruleset")
    @pytest.mark.order(8101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_firewall_ruleset by name."""
        result = client.infraprotect_firewall_ruleset.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for infraprotect_firewall_ruleset")
    @pytest.mark.order(8102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_firewall_ruleset resources in namespace."""
        items = client.infraprotect_firewall_ruleset.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for infraprotect_firewall_ruleset")
    @pytest.mark.order(8103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_firewall_ruleset."""
        body = SPEC_REGISTRY.get_spec("infraprotect_firewall_ruleset", "replace", test_namespace)
        client.infraprotect_firewall_ruleset.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_firewall_ruleset.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98980)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the infraprotect_firewall_ruleset."""
        client.infraprotect_firewall_ruleset.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.infraprotect_firewall_ruleset.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
