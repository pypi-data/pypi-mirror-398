"""Integration tests for cdn_cache_rule resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestCdnCacheRule:
    """Test cdn_cache_rule CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-cdn-cache-rule"

    @pytest.mark.order(420)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a cdn_cache_rule."""
        body = SPEC_REGISTRY.get_spec("cdn_cache_rule", "create", test_namespace)
        result = client.cdn_cache_rule.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(3201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a cdn_cache_rule by name."""
        result = client.cdn_cache_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(3202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing cdn_cache_rule resources in namespace."""
        items = client.cdn_cache_rule.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(3203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a cdn_cache_rule."""
        body = SPEC_REGISTRY.get_spec("cdn_cache_rule", "replace", test_namespace)
        client.cdn_cache_rule.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.cdn_cache_rule.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99580)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the cdn_cache_rule."""
        client.cdn_cache_rule.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.cdn_cache_rule.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
