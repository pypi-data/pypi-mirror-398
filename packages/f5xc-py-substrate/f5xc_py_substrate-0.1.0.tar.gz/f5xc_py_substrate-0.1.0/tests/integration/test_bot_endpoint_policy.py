"""Integration tests for bot_endpoint_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBotEndpointPolicy:
    """Test bot_endpoint_policy CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-bot-endpoint-policy"

    @pytest.mark.skip(reason="No spec template available for bot_endpoint_policy")
    @pytest.mark.order(390)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bot_endpoint_policy."""
        body = SPEC_REGISTRY.get_spec("bot_endpoint_policy", "create", test_namespace)
        result = client.bot_endpoint_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for bot_endpoint_policy")
    @pytest.mark.order(2901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bot_endpoint_policy by name."""
        result = client.bot_endpoint_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for bot_endpoint_policy")
    @pytest.mark.order(2902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bot_endpoint_policy resources in namespace."""
        items = client.bot_endpoint_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for bot_endpoint_policy")
    @pytest.mark.order(2903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bot_endpoint_policy."""
        body = SPEC_REGISTRY.get_spec("bot_endpoint_policy", "replace", test_namespace)
        client.bot_endpoint_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bot_endpoint_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99610)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bot_endpoint_policy."""
        client.bot_endpoint_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bot_endpoint_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
