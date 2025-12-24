"""Integration tests for user_group resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestUserGroup:
    """Test user_group CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-user-group"

    @pytest.mark.skip(reason="No spec template available for user_group")
    @pytest.mark.order(2120)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a user_group."""
        body = SPEC_REGISTRY.get_spec("user_group", "create", test_namespace)
        result = client.user_group.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for user_group")
    @pytest.mark.order(15501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a user_group by name."""
        result = client.user_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for user_group")
    @pytest.mark.order(15502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing user_group resources in namespace."""
        items = client.user_group.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for user_group")
    @pytest.mark.order(15503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a user_group."""
        body = SPEC_REGISTRY.get_spec("user_group", "replace", test_namespace)
        client.user_group.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.user_group.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97880)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the user_group."""
        client.user_group.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.user_group.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
