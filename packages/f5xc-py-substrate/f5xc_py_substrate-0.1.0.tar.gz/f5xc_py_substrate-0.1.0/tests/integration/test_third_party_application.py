"""Integration tests for third_party_application resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestThirdPartyApplication:
    """Test third_party_application CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-third-party-application"

    @pytest.mark.skip(reason="No spec template available for third_party_application")
    @pytest.mark.order(1970)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a third_party_application."""
        body = SPEC_REGISTRY.get_spec("third_party_application", "create", test_namespace)
        result = client.third_party_application.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for third_party_application")
    @pytest.mark.order(14401)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a third_party_application by name."""
        result = client.third_party_application.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for third_party_application")
    @pytest.mark.order(14402)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing third_party_application resources in namespace."""
        items = client.third_party_application.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for third_party_application")
    @pytest.mark.order(14403)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a third_party_application."""
        body = SPEC_REGISTRY.get_spec("third_party_application", "replace", test_namespace)
        client.third_party_application.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.third_party_application.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98030)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the third_party_application."""
        client.third_party_application.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.third_party_application.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
