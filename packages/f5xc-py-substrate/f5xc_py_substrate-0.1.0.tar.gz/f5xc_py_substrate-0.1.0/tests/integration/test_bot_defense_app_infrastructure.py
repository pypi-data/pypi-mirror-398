"""Integration tests for bot_defense_app_infrastructure resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBotDefenseAppInfrastructure:
    """Test bot_defense_app_infrastructure CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-bot-defense-app-infrastructure"

    @pytest.mark.skip(reason="No spec template available for bot_defense_app_infrastructure")
    @pytest.mark.order(360)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bot_defense_app_infrastructure."""
        body = SPEC_REGISTRY.get_spec("bot_defense_app_infrastructure", "create", test_namespace)
        result = client.bot_defense_app_infrastructure.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for bot_defense_app_infrastructure")
    @pytest.mark.order(2801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bot_defense_app_infrastructure by name."""
        result = client.bot_defense_app_infrastructure.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for bot_defense_app_infrastructure")
    @pytest.mark.order(2802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bot_defense_app_infrastructure resources in namespace."""
        items = client.bot_defense_app_infrastructure.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for bot_defense_app_infrastructure")
    @pytest.mark.order(2803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bot_defense_app_infrastructure."""
        body = SPEC_REGISTRY.get_spec("bot_defense_app_infrastructure", "replace", test_namespace)
        client.bot_defense_app_infrastructure.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bot_defense_app_infrastructure.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99640)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the bot_defense_app_infrastructure."""
        client.bot_defense_app_infrastructure.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.bot_defense_app_infrastructure.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
