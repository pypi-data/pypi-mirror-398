"""Integration tests for segment_connection resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestSegmentConnection:
    """Test segment_connection CRUD operations.

    Status: missing
    Notes: Could not extract create example from API docs
    """

    RESOURCE_NAME = "sdk-test-segment-connection"

    @pytest.mark.skip(reason="No spec template available for segment_connection")
    @pytest.mark.order(1770)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a segment_connection."""
        body = SPEC_REGISTRY.get_spec("segment_connection", "create", test_namespace)
        result = client.segment_connection.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for segment_connection")
    @pytest.mark.order(13201)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a segment_connection by name."""
        result = client.segment_connection.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for segment_connection")
    @pytest.mark.order(13202)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing segment_connection resources in namespace."""
        items = client.segment_connection.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for segment_connection")
    @pytest.mark.order(13203)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a segment_connection."""
        body = SPEC_REGISTRY.get_spec("segment_connection", "replace", test_namespace)
        client.segment_connection.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.segment_connection.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(98230)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the segment_connection."""
        client.segment_connection.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.segment_connection.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
