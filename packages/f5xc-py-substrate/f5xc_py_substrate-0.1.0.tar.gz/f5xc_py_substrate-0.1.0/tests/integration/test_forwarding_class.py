"""Integration tests for forwarding_class resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestForwardingClass:
    """Test forwarding_class CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-forwarding-class"

    @pytest.mark.order(860)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a forwarding_class."""
        body = SPEC_REGISTRY.get_spec("forwarding_class", "create", test_namespace)
        result = client.forwarding_class.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(6801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a forwarding_class by name."""
        result = client.forwarding_class.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(6802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing forwarding_class resources in namespace."""
        items = client.forwarding_class.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(6803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a forwarding_class."""
        body = SPEC_REGISTRY.get_spec("forwarding_class", "replace", test_namespace)
        client.forwarding_class.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.forwarding_class.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99140)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the forwarding_class."""
        client.forwarding_class.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.forwarding_class.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
