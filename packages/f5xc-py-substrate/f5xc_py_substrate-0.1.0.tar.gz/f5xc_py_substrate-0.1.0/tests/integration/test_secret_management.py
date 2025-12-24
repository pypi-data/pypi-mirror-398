"""Integration tests for secret_management resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSecretManagement:
    """Test secret_management CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-secret-management"

    @pytest.mark.skip(reason="No spec template available for secret_management")
    @pytest.mark.order(1700)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a secret_management."""
        body = SPEC_REGISTRY.get_spec("secret_management", "create", test_namespace)
        result = client.secret_management.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for secret_management")
    @pytest.mark.order(1701)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a secret_management by name."""
        result = client.secret_management.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for secret_management")
    @pytest.mark.order(1702)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing secret_management resources in namespace."""
        items = client.secret_management.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for secret_management")
    @pytest.mark.order(1703)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a secret_management."""
        body = SPEC_REGISTRY.get_spec("secret_management", "replace", test_namespace)
        client.secret_management.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.secret_management.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME