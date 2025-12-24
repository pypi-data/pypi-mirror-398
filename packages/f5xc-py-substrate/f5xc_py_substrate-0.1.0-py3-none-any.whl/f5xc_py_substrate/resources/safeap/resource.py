"""Safeap resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.safeap.models import (
    GetCurrentFraudRequest,
    GetCurrentFraudResponse,
    GetSafeCubeJSRequest,
    GetSafeCubeJSResponse,
    GetTopRiskyAccountsRequest,
    GetTopRiskyAccountsResponse,
    GetTopRiskyDevicesRequest,
    GetTopRiskyDevicesResponse,
    GetTopRiskyIpAddressesRequest,
    GetTopRiskyIpAddressesResponse,
    GetTopRiskyReasonsRequest,
    GetTopRiskyReasonsResponse,
    GetTransactionRequest,
    GetTransactionResponse,
    HealthResponse,
    SubscribeRequest,
    SubscribeResponse,
    UnsubscribeRequest,
    UnsubscribeResponse,
)


# Exclusion group mappings for get() method
_EXCLUDE_GROUPS: dict[str, set[str]] = {
    "forms": {"create_form", "replace_form"},
    "references": {"referring_objects", "deleted_referred_objects", "disabled_referred_objects"},
    "system_metadata": {"system_metadata"},
}


def _resolve_exclude_groups(groups: list[str]) -> set[str]:
    """Resolve exclusion group names to field names."""
    fields: set[str] = set()
    for group in groups:
        if group in _EXCLUDE_GROUPS:
            fields.update(_EXCLUDE_GROUPS[group])
        else:
            # Allow direct field names for flexibility
            fields.add(group)
    return fields


class SafeapResource:
    """API methods for safeap.

    Use this API to interact with SAFE Account Protection endpoints.
All...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.safeap.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def subscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> SubscribeResponse:
        """Subscribe for safeap.

        Subscribe to Safe AP as add-on service
        """
        path = "/api/shape/safeap/namespaces/system/safeap/addon/subscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "subscribe", e, response) from e

    def unsubscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> UnsubscribeResponse:
        """Unsubscribe for safeap.

        Unsubscribe to Safe AP as add-on service
        """
        path = "/api/shape/safeap/namespaces/system/safeap/addon/unsubscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnsubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "unsubscribe", e, response) from e

    def get_current_fraud_data(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetCurrentFraudResponse:
        """Get Current Fraud Data for safeap.

        Get Current Fraud data request for a time range
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/getcurrentfrauddata"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetCurrentFraudResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_current_fraud_data", e, response) from e

    def get_top_risky_accounts(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetTopRiskyAccountsResponse:
        """Get Top Risky Accounts for safeap.

        Get top risky accounts data request in a time range
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/gettopriskyaccounts"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTopRiskyAccountsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_top_risky_accounts", e, response) from e

    def get_top_risky_devices(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetTopRiskyDevicesResponse:
        """Get Top Risky Devices for safeap.

        Get top risky devices data request in a time range
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/gettopriskydevices"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTopRiskyDevicesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_top_risky_devices", e, response) from e

    def get_top_risky_ip_addresses(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetTopRiskyIpAddressesResponse:
        """Get Top Risky Ip Addresses for safeap.

        Get top risky ip addresses data request in a time range
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/gettopriskyipaddresses"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTopRiskyIpAddressesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_top_risky_ip_addresses", e, response) from e

    def get_top_risky_reasons(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetTopRiskyReasonsResponse:
        """Get Top Risky Reasons for safeap.

        Get top risky reasons data request for a time range
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/gettopriskyreasons"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTopRiskyReasonsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_top_risky_reasons", e, response) from e

    def get_transaction_data(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetTransactionResponse:
        """Get Transaction Data for safeap.

        Get Transaction data request for a time range
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/gettransactiondata"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetTransactionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_transaction_data", e, response) from e

    def health(
        self,
    ) -> HealthResponse:
        """Health for safeap.

        Health Check
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/health"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HealthResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "health", e, response) from e

    def get_safe_cube_js_data(
        self,
        body: dict[str, Any] | None = None,
    ) -> GetSafeCubeJSResponse:
        """Get Safe Cube Js Data for safeap.

        Get Safe CubeJS data request for a given query
        """
        path = "/api/shape/safeap/namespaces/system/safeap/dashboard/safecubejsdata"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetSafeCubeJSResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("safeap", "get_safe_cube_js_data", e, response) from e

