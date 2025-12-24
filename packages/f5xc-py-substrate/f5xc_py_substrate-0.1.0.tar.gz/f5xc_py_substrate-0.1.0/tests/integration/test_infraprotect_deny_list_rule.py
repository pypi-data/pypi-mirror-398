"""Integration tests for infraprotect_deny_list_rule resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectDenyListRule:
    """Test infraprotect_deny_list_rule CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-infraprotect-deny-list-rule"

    @pytest.mark.order(990)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_deny_list_rule."""
        body = SPEC_REGISTRY.get_spec("infraprotect_deny_list_rule", "create", test_namespace)
        result = client.infraprotect_deny_list_rule.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_deny_list_rule by name."""
        result = client.infraprotect_deny_list_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_deny_list_rule resources in namespace."""
        items = client.infraprotect_deny_list_rule.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_deny_list_rule."""
        body = SPEC_REGISTRY.get_spec("infraprotect_deny_list_rule", "replace", test_namespace)
        client.infraprotect_deny_list_rule.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_deny_list_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99010)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the infraprotect_deny_list_rule."""
        client.infraprotect_deny_list_rule.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.infraprotect_deny_list_rule.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
