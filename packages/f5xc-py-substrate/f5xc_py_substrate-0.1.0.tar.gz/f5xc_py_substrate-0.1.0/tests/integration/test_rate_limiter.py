"""Integration tests for rate_limiter resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestRateLimiter:
    """Test rate_limiter CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-rate-limiter"

    @pytest.mark.order(1580)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a rate_limiter."""
        body = SPEC_REGISTRY.get_spec("rate_limiter", "create", test_namespace)
        result = client.rate_limiter.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(11901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a rate_limiter by name."""
        result = client.rate_limiter.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(11902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing rate_limiter resources in namespace."""
        items = client.rate_limiter.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(11903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a rate_limiter."""
        body = SPEC_REGISTRY.get_spec("rate_limiter", "replace", test_namespace)
        client.rate_limiter.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.rate_limiter.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98420)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the rate_limiter."""
        client.rate_limiter.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.rate_limiter.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
