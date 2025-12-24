"""Integration tests for protected_application resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestProtectedApplication:
    """Test protected_application CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-protected-application"

    @pytest.mark.skip(reason="No spec template available for protected_application")
    @pytest.mark.order(1510)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a protected_application."""
        body = SPEC_REGISTRY.get_spec("protected_application", "create", test_namespace)
        result = client.protected_application.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for protected_application")
    @pytest.mark.order(11301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a protected_application by name."""
        result = client.protected_application.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for protected_application")
    @pytest.mark.order(11302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing protected_application resources in namespace."""
        items = client.protected_application.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for protected_application")
    @pytest.mark.order(11303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a protected_application."""
        body = SPEC_REGISTRY.get_spec("protected_application", "replace", test_namespace)
        client.protected_application.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.protected_application.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98490)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the protected_application."""
        client.protected_application.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.protected_application.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
