"""Integration tests for aws_tgw_site resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestAwsTgwSite:
    """Test aws_tgw_site CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-aws-tgw-site"

    @pytest.mark.order(270)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a aws_tgw_site."""
        body = SPEC_REGISTRY.get_spec("aws_tgw_site", "create", test_namespace)
        result = client.aws_tgw_site.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(2001)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a aws_tgw_site by name."""
        result = client.aws_tgw_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(2002)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing aws_tgw_site resources in namespace."""
        items = client.aws_tgw_site.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(2003)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a aws_tgw_site."""
        body = SPEC_REGISTRY.get_spec("aws_tgw_site", "replace", test_namespace)
        client.aws_tgw_site.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.aws_tgw_site.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99730)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the aws_tgw_site."""
        client.aws_tgw_site.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.aws_tgw_site.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
