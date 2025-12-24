"""Integration tests for voltstack_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestVoltstackSite:
    """Test voltstack_site CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-voltstack-site"

    @pytest.mark.order(2230)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a voltstack_site."""
        body = SPEC_REGISTRY.get_spec("voltstack_site", "create", test_namespace)
        result = client.voltstack_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(16301)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a voltstack_site by name."""
        result = client.voltstack_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(16302)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing voltstack_site resources in namespace."""
        items = client.voltstack_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(16303)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a voltstack_site."""
        body = SPEC_REGISTRY.get_spec("voltstack_site", "replace", test_namespace)
        client.voltstack_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.voltstack_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(97770)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the voltstack_site."""
        client.voltstack_site.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.voltstack_site.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
