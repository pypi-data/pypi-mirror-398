"""Integration tests for bot_allowlist_policy resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBotAllowlistPolicy:
    """Test bot_allowlist_policy CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-bot-allowlist-policy"

    @pytest.mark.skip(reason="No spec template available for bot_allowlist_policy")
    @pytest.mark.order(350)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bot_allowlist_policy."""
        body = SPEC_REGISTRY.get_spec("bot_allowlist_policy", "create", test_namespace)
        result = client.bot_allowlist_policy.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for bot_allowlist_policy")
    @pytest.mark.order(2701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bot_allowlist_policy by name."""
        result = client.bot_allowlist_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for bot_allowlist_policy")
    @pytest.mark.order(2702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bot_allowlist_policy resources in namespace."""
        items = client.bot_allowlist_policy.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for bot_allowlist_policy")
    @pytest.mark.order(2703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bot_allowlist_policy."""
        body = SPEC_REGISTRY.get_spec("bot_allowlist_policy", "replace", test_namespace)
        client.bot_allowlist_policy.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bot_allowlist_policy.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99650)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bot_allowlist_policy."""
        client.bot_allowlist_policy.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bot_allowlist_policy.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
