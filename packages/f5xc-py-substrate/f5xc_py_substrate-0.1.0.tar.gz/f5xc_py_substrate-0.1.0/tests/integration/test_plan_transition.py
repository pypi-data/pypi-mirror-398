"""Integration tests for plan_transition resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestPlanTransition:
    """Test plan_transition CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-plan-transition"

    @pytest.mark.skip(reason="No spec template available for plan_transition")
    @pytest.mark.order(1480)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a plan_transition."""
        body = SPEC_REGISTRY.get_spec("plan_transition", "create", test_namespace)
        result = client.plan_transition.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for plan_transition")
    @pytest.mark.order(1481)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a plan_transition by name."""
        result = client.plan_transition.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for plan_transition")
    @pytest.mark.order(1482)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing plan_transition resources in namespace."""
        items = client.plan_transition.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for plan_transition")
    @pytest.mark.order(1483)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a plan_transition."""
        body = SPEC_REGISTRY.get_spec("plan_transition", "replace", test_namespace)
        client.plan_transition.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.plan_transition.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME