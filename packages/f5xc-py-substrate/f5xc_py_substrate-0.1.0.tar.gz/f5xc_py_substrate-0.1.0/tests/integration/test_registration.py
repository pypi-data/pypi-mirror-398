"""Integration tests for registration resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestRegistration:
    """Test registration CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-registration"

    @pytest.mark.order(1620)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a registration."""
        body = SPEC_REGISTRY.get_spec("registration", "create", test_namespace)
        result = client.registration.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(12201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a registration by name."""
        result = client.registration.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(12202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing registration resources in namespace."""
        items = client.registration.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(12203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a registration."""
        body = SPEC_REGISTRY.get_spec("registration", "replace", test_namespace)
        client.registration.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.registration.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98380)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the registration."""
        client.registration.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.registration.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
