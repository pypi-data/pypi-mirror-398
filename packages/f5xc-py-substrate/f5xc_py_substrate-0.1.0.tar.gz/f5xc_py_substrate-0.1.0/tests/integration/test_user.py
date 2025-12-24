"""Integration tests for user resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestUser:
    """Test user CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-user"

    @pytest.mark.skip(reason="No spec template available for user")
    @pytest.mark.order(2110)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a user."""
        body = SPEC_REGISTRY.get_spec("user", "create", test_namespace)
        result = client.user.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for user")
    @pytest.mark.order(15401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a user by name."""
        result = client.user.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for user")
    @pytest.mark.order(15402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing user resources in namespace."""
        items = client.user.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for user")
    @pytest.mark.order(15403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a user."""
        body = SPEC_REGISTRY.get_spec("user", "replace", test_namespace)
        client.user.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.user.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97890)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the user."""
        client.user.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.user.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
