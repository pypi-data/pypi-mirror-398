"""Integration tests for voltshare_admin_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVoltshareAdminPolicy:
    """Test voltshare_admin_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-voltshare-admin-policy"

    @pytest.mark.order(2220)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a voltshare_admin_policy."""
        body = SPEC_REGISTRY.get_spec("voltshare_admin_policy", "create", test_namespace)
        result = client.voltshare_admin_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(16201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a voltshare_admin_policy by name."""
        result = client.voltshare_admin_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(16202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing voltshare_admin_policy resources in namespace."""
        items = client.voltshare_admin_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(16203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a voltshare_admin_policy."""
        body = SPEC_REGISTRY.get_spec("voltshare_admin_policy", "replace", test_namespace)
        client.voltshare_admin_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.voltshare_admin_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97780)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the voltshare_admin_policy."""
        client.voltshare_admin_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.voltshare_admin_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
