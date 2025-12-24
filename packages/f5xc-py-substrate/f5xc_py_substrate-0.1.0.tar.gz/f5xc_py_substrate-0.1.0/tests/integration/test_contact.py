"""Integration tests for contact resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestContact:
    """Test contact CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-contact"

    @pytest.mark.order(590)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a contact."""
        body = SPEC_REGISTRY.get_spec("contact", "create", test_namespace)
        result = client.contact.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(4601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a contact by name."""
        result = client.contact.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(4602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing contact resources in namespace."""
        items = client.contact.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(4603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a contact."""
        body = SPEC_REGISTRY.get_spec("contact", "replace", test_namespace)
        client.contact.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.contact.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99410)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the contact."""
        client.contact.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.contact.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
