"""Integration tests for view_internal resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestViewInternal:
    """Test view_internal CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-view-internal"

    @pytest.mark.skip(reason="No spec template available for view_internal")
    @pytest.mark.order(2160)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a view_internal."""
        body = SPEC_REGISTRY.get_spec("view_internal", "create", test_namespace)
        result = client.view_internal.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for view_internal")
    @pytest.mark.order(2161)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a view_internal by name."""
        result = client.view_internal.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for view_internal")
    @pytest.mark.order(2162)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing view_internal resources in namespace."""
        items = client.view_internal.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for view_internal")
    @pytest.mark.order(2163)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a view_internal."""
        body = SPEC_REGISTRY.get_spec("view_internal", "replace", test_namespace)
        client.view_internal.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.view_internal.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME