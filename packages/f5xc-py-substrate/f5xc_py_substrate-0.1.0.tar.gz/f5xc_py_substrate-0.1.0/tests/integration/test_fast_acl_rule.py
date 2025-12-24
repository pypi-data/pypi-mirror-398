"""Integration tests for fast_acl_rule resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestFastAclRule:
    """Test fast_acl_rule CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-fast-acl-rule"

    @pytest.mark.order(810)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a fast_acl_rule."""
        body = SPEC_REGISTRY.get_spec("fast_acl_rule", "create", test_namespace)
        result = client.fast_acl_rule.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(6501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a fast_acl_rule by name."""
        result = client.fast_acl_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(6502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing fast_acl_rule resources in namespace."""
        items = client.fast_acl_rule.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(6503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a fast_acl_rule."""
        body = SPEC_REGISTRY.get_spec("fast_acl_rule", "replace", test_namespace)
        client.fast_acl_rule.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.fast_acl_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99190)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the fast_acl_rule."""
        client.fast_acl_rule.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.fast_acl_rule.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
