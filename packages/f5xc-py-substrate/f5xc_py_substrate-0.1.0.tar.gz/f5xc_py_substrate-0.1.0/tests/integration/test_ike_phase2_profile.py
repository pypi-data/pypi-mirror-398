"""Integration tests for ike_phase2_profile resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestIkePhase2Profile:
    """Test ike_phase2_profile CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-ike-phase2-profile"

    @pytest.mark.order(950)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a ike_phase2_profile."""
        body = SPEC_REGISTRY.get_spec("ike_phase2_profile", "create", test_namespace)
        result = client.ike_phase2_profile.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(7501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a ike_phase2_profile by name."""
        result = client.ike_phase2_profile.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(7502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing ike_phase2_profile resources in namespace."""
        items = client.ike_phase2_profile.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(7503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a ike_phase2_profile."""
        body = SPEC_REGISTRY.get_spec("ike_phase2_profile", "replace", test_namespace)
        client.ike_phase2_profile.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.ike_phase2_profile.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99050)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the ike_phase2_profile."""
        client.ike_phase2_profile.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.ike_phase2_profile.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
