"""Integration tests for authentication resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAuthentication:
    """Test authentication CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-authentication"

    @pytest.mark.order(260)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a authentication."""
        body = SPEC_REGISTRY.get_spec("authentication", "create", test_namespace)
        result = client.authentication.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(1901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a authentication by name."""
        result = client.authentication.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(1902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing authentication resources in namespace."""
        items = client.authentication.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(1903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a authentication."""
        body = SPEC_REGISTRY.get_spec("authentication", "replace", test_namespace)
        client.authentication.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.authentication.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99740)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the authentication."""
        client.authentication.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.authentication.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
