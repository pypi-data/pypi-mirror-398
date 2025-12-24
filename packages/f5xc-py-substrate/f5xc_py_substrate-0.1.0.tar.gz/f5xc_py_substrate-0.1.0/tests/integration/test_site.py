"""Integration tests for site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSite:
    """Test site CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-site"

    @pytest.mark.skip(reason="No spec template available for site")
    @pytest.mark.order(1840)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a site."""
        body = SPEC_REGISTRY.get_spec("site", "create", test_namespace)
        result = client.site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for site")
    @pytest.mark.order(13601)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a site by name."""
        result = client.site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for site")
    @pytest.mark.order(13602)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing site resources in namespace."""
        items = client.site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for site")
    @pytest.mark.order(13603)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a site."""
        body = SPEC_REGISTRY.get_spec("site", "replace", test_namespace)
        client.site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98160)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the site."""
        client.site.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.site.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
