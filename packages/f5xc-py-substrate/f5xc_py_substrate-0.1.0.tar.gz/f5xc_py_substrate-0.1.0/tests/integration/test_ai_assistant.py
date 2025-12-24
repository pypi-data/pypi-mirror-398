"""Integration tests for ai_assistant resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAiAssistant:
    """Test ai_assistant CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-ai-assistant"

    @pytest.mark.skip(reason="No spec template available for ai_assistant")
    @pytest.mark.order(50)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ai_assistant."""
        body = SPEC_REGISTRY.get_spec("ai_assistant", "create", test_namespace)
        result = client.ai_assistant.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for ai_assistant")
    @pytest.mark.order(51)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ai_assistant by name."""
        result = client.ai_assistant.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for ai_assistant")
    @pytest.mark.order(52)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ai_assistant resources in namespace."""
        items = client.ai_assistant.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for ai_assistant")
    @pytest.mark.order(53)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ai_assistant."""
        body = SPEC_REGISTRY.get_spec("ai_assistant", "replace", test_namespace)
        client.ai_assistant.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ai_assistant.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME