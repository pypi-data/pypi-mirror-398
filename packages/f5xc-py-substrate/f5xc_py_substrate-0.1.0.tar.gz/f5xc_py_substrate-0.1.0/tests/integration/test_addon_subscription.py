"""Integration tests for addon_subscription resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAddonSubscription:
    """Test addon_subscription CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-addon-subscription"

    @pytest.mark.order(20)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a addon_subscription."""
        body = SPEC_REGISTRY.get_spec("addon_subscription", "create", test_namespace)
        result = client.addon_subscription.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a addon_subscription by name."""
        result = client.addon_subscription.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing addon_subscription resources in namespace."""
        items = client.addon_subscription.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a addon_subscription."""
        body = SPEC_REGISTRY.get_spec("addon_subscription", "replace", test_namespace)
        client.addon_subscription.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.addon_subscription.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99980)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the addon_subscription."""
        client.addon_subscription.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.addon_subscription.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
