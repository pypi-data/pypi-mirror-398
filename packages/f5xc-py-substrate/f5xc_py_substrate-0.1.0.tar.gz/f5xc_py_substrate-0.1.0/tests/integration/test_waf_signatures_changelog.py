"""Integration tests for waf_signatures_changelog resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestWafSignaturesChangelog:
    """Test waf_signatures_changelog CRUD operations.

    Status: missing
    """

    RESOURCE_NAME = "sdk-test-waf-signatures-changelog"

    @pytest.mark.skip(reason="No spec template available for waf_signatures_changelog")
    @pytest.mark.order(2260)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a waf_signatures_changelog."""
        body = SPEC_REGISTRY.get_spec("waf_signatures_changelog", "create", test_namespace)
        result = client.waf_signatures_changelog.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.skip(reason="No spec template available for waf_signatures_changelog")
    @pytest.mark.order(2261)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a waf_signatures_changelog by name."""
        result = client.waf_signatures_changelog.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.skip(reason="No spec template available for waf_signatures_changelog")
    @pytest.mark.order(2262)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing waf_signatures_changelog resources in namespace."""
        items = client.waf_signatures_changelog.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.skip(reason="No spec template available for waf_signatures_changelog")
    @pytest.mark.order(2263)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a waf_signatures_changelog."""
        body = SPEC_REGISTRY.get_spec("waf_signatures_changelog", "replace", test_namespace)
        client.waf_signatures_changelog.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.waf_signatures_changelog.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME