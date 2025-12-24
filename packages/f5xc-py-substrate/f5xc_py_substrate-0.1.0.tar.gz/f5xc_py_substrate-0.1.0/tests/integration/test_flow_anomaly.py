"""Integration tests for flow_anomaly resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestFlowAnomaly:
    """Test flow_anomaly CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-flow-anomaly"

    @pytest.mark.skip(reason="No spec template available for flow_anomaly")
    @pytest.mark.order(840)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a flow_anomaly."""
        body = SPEC_REGISTRY.get_spec("flow_anomaly", "create", test_namespace)
        result = client.flow_anomaly.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for flow_anomaly")
    @pytest.mark.order(841)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a flow_anomaly by name."""
        result = client.flow_anomaly.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for flow_anomaly")
    @pytest.mark.order(842)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing flow_anomaly resources in namespace."""
        items = client.flow_anomaly.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for flow_anomaly")
    @pytest.mark.order(843)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a flow_anomaly."""
        body = SPEC_REGISTRY.get_spec("flow_anomaly", "replace", test_namespace)
        client.flow_anomaly.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.flow_anomaly.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME