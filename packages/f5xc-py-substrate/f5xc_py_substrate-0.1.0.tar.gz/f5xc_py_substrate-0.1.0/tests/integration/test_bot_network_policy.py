"""Integration tests for bot_network_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBotNetworkPolicy:
    """Test bot_network_policy CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-bot-network-policy"

    @pytest.mark.skip(reason="No spec template available for bot_network_policy")
    @pytest.mark.order(410)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bot_network_policy."""
        body = SPEC_REGISTRY.get_spec("bot_network_policy", "create", test_namespace)
        result = client.bot_network_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for bot_network_policy")
    @pytest.mark.order(3101)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bot_network_policy by name."""
        result = client.bot_network_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for bot_network_policy")
    @pytest.mark.order(3102)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bot_network_policy resources in namespace."""
        items = client.bot_network_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for bot_network_policy")
    @pytest.mark.order(3103)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bot_network_policy."""
        body = SPEC_REGISTRY.get_spec("bot_network_policy", "replace", test_namespace)
        client.bot_network_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bot_network_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99590)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bot_network_policy."""
        client.bot_network_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bot_network_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
