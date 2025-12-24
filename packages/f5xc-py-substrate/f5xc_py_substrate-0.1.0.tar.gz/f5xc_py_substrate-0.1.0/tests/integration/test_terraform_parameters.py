"""Integration tests for terraform_parameters resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestTerraformParameters:
    """Test terraform_parameters CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-terraform-parameters"

    @pytest.mark.skip(reason="No spec template available for terraform_parameters")
    @pytest.mark.order(1960)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a terraform_parameters."""
        body = SPEC_REGISTRY.get_spec("terraform_parameters", "create", test_namespace)
        result = client.terraform_parameters.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for terraform_parameters")
    @pytest.mark.order(1961)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a terraform_parameters by name."""
        result = client.terraform_parameters.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for terraform_parameters")
    @pytest.mark.order(1962)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing terraform_parameters resources in namespace."""
        items = client.terraform_parameters.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for terraform_parameters")
    @pytest.mark.order(1963)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a terraform_parameters."""
        body = SPEC_REGISTRY.get_spec("terraform_parameters", "replace", test_namespace)
        client.terraform_parameters.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.terraform_parameters.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME