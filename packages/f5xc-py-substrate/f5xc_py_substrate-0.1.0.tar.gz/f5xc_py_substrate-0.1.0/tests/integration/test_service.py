"""Integration tests for service resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestService:
    """Test service CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-service"

    @pytest.mark.skip(reason="No spec template available for service")
    @pytest.mark.order(1790)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a service."""
        body = SPEC_REGISTRY.get_spec("service", "create", test_namespace)
        result = client.service.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for service")
    @pytest.mark.order(1791)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a service by name."""
        result = client.service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for service")
    @pytest.mark.order(1792)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing service resources in namespace."""
        items = client.service.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for service")
    @pytest.mark.order(1793)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a service."""
        body = SPEC_REGISTRY.get_spec("service", "replace", test_namespace)
        client.service.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.service.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME