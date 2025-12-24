"""Integration tests for infraprotect_information resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestInfraprotectInformation:
    """Test infraprotect_information CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-infraprotect-information"

    @pytest.mark.skip(reason="No spec template available for infraprotect_information")
    @pytest.mark.order(1030)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a infraprotect_information."""
        body = SPEC_REGISTRY.get_spec("infraprotect_information", "create", test_namespace)
        result = client.infraprotect_information.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for infraprotect_information")
    @pytest.mark.order(1031)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a infraprotect_information by name."""
        result = client.infraprotect_information.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for infraprotect_information")
    @pytest.mark.order(1032)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing infraprotect_information resources in namespace."""
        items = client.infraprotect_information.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for infraprotect_information")
    @pytest.mark.order(1033)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a infraprotect_information."""
        body = SPEC_REGISTRY.get_spec("infraprotect_information", "replace", test_namespace)
        client.infraprotect_information.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.infraprotect_information.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME