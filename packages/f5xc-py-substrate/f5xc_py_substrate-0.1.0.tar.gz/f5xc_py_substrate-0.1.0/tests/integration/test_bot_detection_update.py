"""Integration tests for bot_detection_update resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestBotDetectionUpdate:
    """Test bot_detection_update CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-bot-detection-update"

    @pytest.mark.skip(reason="No spec template available for bot_detection_update")
    @pytest.mark.order(380)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a bot_detection_update."""
        body = SPEC_REGISTRY.get_spec("bot_detection_update", "create", test_namespace)
        result = client.bot_detection_update.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for bot_detection_update")
    @pytest.mark.order(381)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a bot_detection_update by name."""
        result = client.bot_detection_update.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for bot_detection_update")
    @pytest.mark.order(382)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing bot_detection_update resources in namespace."""
        items = client.bot_detection_update.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for bot_detection_update")
    @pytest.mark.order(383)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a bot_detection_update."""
        body = SPEC_REGISTRY.get_spec("bot_detection_update", "replace", test_namespace)
        client.bot_detection_update.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.bot_detection_update.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME