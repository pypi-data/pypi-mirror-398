"""Integration tests for app_security resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAppSecurity:
    """Test app_security CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-app-security"

    @pytest.mark.skip(reason="No spec template available for app_security")
    @pytest.mark.order(230)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a app_security."""
        body = SPEC_REGISTRY.get_spec("app_security", "create", test_namespace)
        result = client.app_security.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for app_security")
    @pytest.mark.order(231)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a app_security by name."""
        result = client.app_security.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for app_security")
    @pytest.mark.order(232)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing app_security resources in namespace."""
        items = client.app_security.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for app_security")
    @pytest.mark.order(233)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a app_security."""
        body = SPEC_REGISTRY.get_spec("app_security", "replace", test_namespace)
        client.app_security.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.app_security.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME