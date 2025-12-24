"""Integration tests for dns_compliance_checks resource."""

from __future__ import annotations

import pytest

from f5xc_py_substrate import Client
from tests.integration.fixtures.spec_registry import SPEC_REGISTRY


class TestDnsComplianceChecks:
    """Test dns_compliance_checks CRUD operations.

    Status: generated
    Notes: Auto-generated from API docs, may need manual validation
    """

    RESOURCE_NAME = "sdk-test-dns-compliance-checks"

    @pytest.mark.order(710)
    @pytest.mark.dependency(name="test_create")
    def test_create(self, client: Client, test_namespace: str) -> None:
        """Test creating a dns_compliance_checks."""
        body = SPEC_REGISTRY.get_spec("dns_compliance_checks", "create", test_namespace)
        result = client.dns_compliance_checks.create(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )
        assert result.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(5501)
    def test_get(self, client: Client, test_namespace: str) -> None:
        """Test getting a dns_compliance_checks by name."""
        result = client.dns_compliance_checks.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert result.metadata.name == self.RESOURCE_NAME
        assert result.metadata.namespace == test_namespace

    @pytest.mark.order(5502)
    def test_list(self, client: Client, test_namespace: str) -> None:
        """Test listing dns_compliance_checks resources in namespace."""
        items = client.dns_compliance_checks.list(namespace=test_namespace)
        names = [item.name for item in items if item.name is not None]
        assert self.RESOURCE_NAME in names

    @pytest.mark.order(5503)
    def test_replace(self, client: Client, test_namespace: str) -> None:
        """Test replacing a dns_compliance_checks."""
        body = SPEC_REGISTRY.get_spec("dns_compliance_checks", "replace", test_namespace)
        client.dns_compliance_checks.replace(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
            body=body,
        )

        updated = client.dns_compliance_checks.get(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )
        assert updated.metadata.name == self.RESOURCE_NAME

    @pytest.mark.order(99290)
    @pytest.mark.dependency(depends=["test_create"])
    def test_delete(self, client: Client, test_namespace: str) -> None:
        """Test deleting the dns_compliance_checks."""
        client.dns_compliance_checks.delete(
            namespace=test_namespace,
            name=self.RESOURCE_NAME,
        )

        # Verify deletion
        from f5xc_py_substrate.exceptions import F5XCNotFoundError
        import pytest

        with pytest.raises(F5XCNotFoundError):
            client.dns_compliance_checks.get(
                namespace=test_namespace,
                name=self.RESOURCE_NAME,
            )
