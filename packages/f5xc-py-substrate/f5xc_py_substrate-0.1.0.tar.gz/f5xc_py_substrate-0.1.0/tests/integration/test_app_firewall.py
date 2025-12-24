"""Integration tests for app_firewall resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAppFirewall:
    """Test app_firewall CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-app-firewall"

    @pytest.mark.order(220)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a app_firewall."""
        body = SPEC_REGISTRY.get_spec("app_firewall", "create", test_namespace)
        result = client.app_firewall.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(1601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a app_firewall by name."""
        result = client.app_firewall.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(1602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing app_firewall resources in namespace."""
        items = client.app_firewall.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(1603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a app_firewall."""
        body = SPEC_REGISTRY.get_spec("app_firewall", "replace", test_namespace)
        client.app_firewall.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.app_firewall.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99780)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the app_firewall."""
        client.app_firewall.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.app_firewall.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
