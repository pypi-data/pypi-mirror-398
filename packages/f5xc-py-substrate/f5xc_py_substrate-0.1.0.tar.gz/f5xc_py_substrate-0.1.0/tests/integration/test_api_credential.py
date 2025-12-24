"""Integration tests for api_credential resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestApiCredential:
    """Test api_credential CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-api-credential"

    @pytest.mark.skip(reason="No spec template available for api_credential")
    @pytest.mark.order(140)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a api_credential."""
        body = SPEC_REGISTRY.get_spec("api_credential", "create", test_namespace)
        result = client.api_credential.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for api_credential")
    @pytest.mark.order(1001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a api_credential by name."""
        result = client.api_credential.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for api_credential")
    @pytest.mark.order(1002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing api_credential resources in namespace."""
        items = client.api_credential.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for api_credential")
    @pytest.mark.order(1003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a api_credential."""
        body = SPEC_REGISTRY.get_spec("api_credential", "replace", test_namespace)
        client.api_credential.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.api_credential.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99860)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the api_credential."""
        client.api_credential.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.api_credential.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
