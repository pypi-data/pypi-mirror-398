"""Integration tests for api_testing resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestApiTesting:
    """Test api_testing CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-api-testing"

    @pytest.mark.order(190)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a api_testing."""
        body = SPEC_REGISTRY.get_spec("api_testing", "create", test_namespace)
        result = client.api_testing.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(1301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a api_testing by name."""
        result = client.api_testing.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(1302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing api_testing resources in namespace."""
        items = client.api_testing.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(1303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a api_testing."""
        body = SPEC_REGISTRY.get_spec("api_testing", "replace", test_namespace)
        client.api_testing.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.api_testing.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99810)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the api_testing."""
        client.api_testing.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.api_testing.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
