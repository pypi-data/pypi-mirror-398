"""Integration tests for usb_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestUsbPolicy:
    """Test usb_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-usb-policy"

    @pytest.mark.order(2100)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a usb_policy."""
        body = SPEC_REGISTRY.get_spec("usb_policy", "create", test_namespace)
        result = client.usb_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(15301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a usb_policy by name."""
        result = client.usb_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(15302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing usb_policy resources in namespace."""
        items = client.usb_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(15303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a usb_policy."""
        body = SPEC_REGISTRY.get_spec("usb_policy", "replace", test_namespace)
        client.usb_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.usb_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97900)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the usb_policy."""
        client.usb_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.usb_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
