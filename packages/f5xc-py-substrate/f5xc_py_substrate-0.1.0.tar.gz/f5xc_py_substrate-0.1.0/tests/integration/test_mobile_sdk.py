"""Integration tests for mobile_sdk resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestMobileSdk:
    """Test mobile_sdk CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-mobile-sdk"

    @pytest.mark.skip(reason="No spec template available for mobile_sdk")
    @pytest.mark.order(1250)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a mobile_sdk."""
        body = SPEC_REGISTRY.get_spec("mobile_sdk", "create", test_namespace)
        result = client.mobile_sdk.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for mobile_sdk")
    @pytest.mark.order(1251)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a mobile_sdk by name."""
        result = client.mobile_sdk.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for mobile_sdk")
    @pytest.mark.order(1252)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing mobile_sdk resources in namespace."""
        items = client.mobile_sdk.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for mobile_sdk")
    @pytest.mark.order(1253)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a mobile_sdk."""
        body = SPEC_REGISTRY.get_spec("mobile_sdk", "replace", test_namespace)
        client.mobile_sdk.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.mobile_sdk.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME