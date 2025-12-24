"""Integration tests for geo_location_set resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestGeoLocationSet:
    """Test geo_location_set CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-geo-location-set"

    @pytest.mark.order(890)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a geo_location_set."""
        body = SPEC_REGISTRY.get_spec("geo_location_set", "create", test_namespace)
        result = client.geo_location_set.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(6901)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a geo_location_set by name."""
        result = client.geo_location_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(6902)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing geo_location_set resources in namespace."""
        items = client.geo_location_set.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(6903)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a geo_location_set."""
        body = SPEC_REGISTRY.get_spec("geo_location_set", "replace", test_namespace)
        client.geo_location_set.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.geo_location_set.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99110)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the geo_location_set."""
        client.geo_location_set.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.geo_location_set.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
