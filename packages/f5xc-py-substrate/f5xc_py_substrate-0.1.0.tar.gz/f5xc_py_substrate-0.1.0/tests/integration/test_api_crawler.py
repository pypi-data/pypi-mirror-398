"""Integration tests for api_crawler resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestApiCrawler:
    """Test api_crawler CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-api-crawler"

    @pytest.mark.order(130)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a api_crawler."""
        body = SPEC_REGISTRY.get_spec("api_crawler", "create", test_namespace)
        result = client.api_crawler.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a api_crawler by name."""
        result = client.api_crawler.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing api_crawler resources in namespace."""
        items = client.api_crawler.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a api_crawler."""
        body = SPEC_REGISTRY.get_spec("api_crawler", "replace", test_namespace)
        client.api_crawler.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.api_crawler.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99870)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the api_crawler."""
        client.api_crawler.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.api_crawler.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
