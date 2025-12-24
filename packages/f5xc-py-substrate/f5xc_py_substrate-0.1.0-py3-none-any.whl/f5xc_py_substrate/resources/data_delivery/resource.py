"""DataDelivery resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.data_delivery.models import (
    DataPoint,
    DataSet,
    EventsReason,
    Feature,
    FlowLabel,
    GetDataDictionaryResponse,
    GetDataSetsResponse,
    Series,
    LineChartData,
    ListDataSetsResponse,
    ListFlowLabelsResponse,
    LoadExecutiveSummaryRequest,
    SummaryPanel,
    LoadExecutiveSummaryResponse,
    TestReceiverRequest,
    TestReceiverResponse,
    UpdateReceiverStatusRequest,
    UpdateReceiverStatusResponse,
    ProtobufAny,
    SuggestValuesReq,
    ObjectRefType,
    SuggestedItem,
    SuggestValuesResp,
    Empty,
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


class DataDeliveryResource:
    """API methods for data_delivery.

    Custom handler in Data Delivery microservice will forward request(s)...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.data_delivery.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get_data_sets(
        self,
    ) -> GetDataSetsResponse:
        """Get Data Sets for data_delivery.

        Get the list of data sets eligible for the tenant
        """
        path = "/api/data-intelligence/namespaces/system/dataSets"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDataSetsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "get_data_sets", e, response) from e

    def get_data_dictionary(
        self,
        dataset: str,
    ) -> GetDataDictionaryResponse:
        """Get Data Dictionary for data_delivery.

        Get the dataset features from Data dictionary API
        """
        path = "/api/data-intelligence/namespaces/system/datadictionary/{dataset}"
        path = path.replace("{dataset}", dataset)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetDataDictionaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "get_data_dictionary", e, response) from e

    def init(
        self,
        body: dict[str, Any] | None = None,
    ) -> Empty:
        """Init for data_delivery.

        Request to enable Data Intelligence for the tenant
        """
        path = "/api/data-intelligence/namespaces/system/init-request"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return Empty(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "init", e, response) from e

    def list_data_sets(
        self,
        namespace: str,
    ) -> ListDataSetsResponse:
        """List Data Sets for data_delivery.

        API to list datasets by tenant
        """
        path = "/api/data-intelligence/namespaces/{namespace}/data-dictionary/datasets"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListDataSetsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "list_data_sets", e, response) from e

    def list_flow_labels(
        self,
        namespace: str,
    ) -> ListFlowLabelsResponse:
        """List Flow Labels for data_delivery.

        ListFlowLabels takes a customer name and returns a list of FlowLabel objects
        """
        path = "/api/data-intelligence/namespaces/{namespace}/di/flowlabels"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListFlowLabelsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "list_flow_labels", e, response) from e

    def load_executive_summary(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> LoadExecutiveSummaryResponse:
        """Load Executive Summary for data_delivery.

        Executive summary page for DI premium customers
        """
        path = "/api/data-intelligence/namespaces/{namespace}/di/summary"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LoadExecutiveSummaryResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "load_executive_summary", e, response) from e

    def update_receiver_status(
        self,
        namespace: str,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> UpdateReceiverStatusResponse:
        """Update Receiver Status for data_delivery.

        Update receiver object status from enable to disable and vice versa
        """
        path = "/api/data-intelligence/namespaces/{namespace}/receivers/{id}/status"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UpdateReceiverStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "update_receiver_status", e, response) from e

    def test_receiver(
        self,
        namespace: str,
        id: str,
        body: dict[str, Any] | None = None,
    ) -> TestReceiverResponse:
        """Test Receiver for data_delivery.

        API to test receiver destination sink connection
        """
        path = "/api/data-intelligence/namespaces/{namespace}/receivers/{id}/test"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{id}", id)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TestReceiverResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "test_receiver", e, response) from e

    def suggest_values(
        self,
        namespace: str,
        body: dict[str, Any] | None = None,
    ) -> SuggestValuesResp:
        """Suggest Values for data_delivery.

        Returns suggested values for the specified field in the given...
        """
        path = "/api/data-intelligence/namespaces/{namespace}/suggest-values"
        path = path.replace("{namespace}", namespace)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SuggestValuesResp(**response)
        except ValidationError as e:
            raise F5XCValidationError("data_delivery", "suggest_values", e, response) from e

