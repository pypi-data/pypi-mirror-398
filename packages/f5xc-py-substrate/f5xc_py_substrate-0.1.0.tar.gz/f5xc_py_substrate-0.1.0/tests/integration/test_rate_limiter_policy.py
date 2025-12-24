"""Integration tests for rate_limiter_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestRateLimiterPolicy:
    """Test rate_limiter_policy CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-rate-limiter-policy"

    @pytest.mark.order(1590)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a rate_limiter_policy."""
        body = SPEC_REGISTRY.get_spec("rate_limiter_policy", "create", test_namespace)
        result = client.rate_limiter_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(12001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a rate_limiter_policy by name."""
        result = client.rate_limiter_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(12002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing rate_limiter_policy resources in namespace."""
        items = client.rate_limiter_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(12003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a rate_limiter_policy."""
        body = SPEC_REGISTRY.get_spec("rate_limiter_policy", "replace", test_namespace)
        client.rate_limiter_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.rate_limiter_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98410)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the rate_limiter_policy."""
        client.rate_limiter_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.rate_limiter_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
