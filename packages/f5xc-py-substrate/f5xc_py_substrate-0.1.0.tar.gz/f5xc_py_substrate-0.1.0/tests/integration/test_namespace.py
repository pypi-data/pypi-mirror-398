"""Integration tests for namespace resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client


class TestNamespace:
    """Test namespace CRUD operations.

    Note: The test_namespace fixture handles namespace creation/deletion,
    so these tests focus on additional namespace operations.
    """

    @pytest.mark.order(9801)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a namespace by name."""
        ns = client.namespace.get(name=test_namespace)
        assert ns.metadata.name == test_namespace

    @pytest.mark.order(9802)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing namespaces."""
        namespaces = client.namespace.list()
        # List items have name at top level (not nested in metadata)
        names = [ns.name for ns in namespaces if ns.name is not None]
        assert test_namespace in names

    @pytest.mark.order(9803)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing/updating a namespace."""
        # Replace returns empty response, so just call and verify via get
        client.namespace.replace(
            namespace="",
            name=test_namespace,
            description="Updated by SDK integration test",
        )

        # Verify the update
        updated = client.namespace.get(name=test_namespace)
        assert updated.metadata.name == test_namespace
        assert "Updated by SDK" in (updated.metadata.description or "")
    @pytest.mark.order(99990)
    @pytest.mark.skip(reason="Non-namespaced resource - delete testing skipped for safety")
    def test_delete(self, client: Client) -> None:
        """Test deleting the namespace - SKIPPED for safety."""
        pass
