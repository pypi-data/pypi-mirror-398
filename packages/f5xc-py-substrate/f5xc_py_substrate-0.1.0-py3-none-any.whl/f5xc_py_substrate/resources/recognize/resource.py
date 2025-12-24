"""Recognize resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.recognize.models import (
    ChannelMWItem,
    ChannelItem,
    ChannelData,
    ChannelRequest,
    ChannelResponse,
    ConversionItem,
    ConversionData,
    ConversionRequest,
    ConversionResponse,
    EnjoyLoginItem,
    EnjoyItem,
    EnjoyData,
    EnjoyRequest,
    EnjoyResponse,
    FrictionAggregationItem,
    FrictionAggregationData,
    FrictionAggregationRequest,
    FrictionAggregationResponse,
    FrictionHistogramItem,
    FrictionHistogramData,
    FrictionHistogramRequest,
    FrictionHistogramResponse,
    GetStatusProvisionResponse,
    GetStatusResponse,
    HealthResponse,
    LiftControlItem,
    LiftItem,
    LiftData,
    LiftRequest,
    LiftResponse,
    RescueItem,
    RescueData,
    RescueRequest,
    RescueResponse,
    StateData,
    StateResponse,
    SubscribeRequest,
    SubscribeResponse,
    TopReasonCodesData,
    TopReasonCodesRequest,
    TopReasonCodesResponse,
    UnsubscribeRequest,
    UnsubscribeResponse,
    ValidateSrcTagInjectionRequest,
    ValidateSrcTagInjectionResponse,
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


class RecognizeResource:
    """API methods for recognize.

    Use this API to forward API calls into the Shape APIs
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.recognize.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def channel(
        self,
        body: dict[str, Any] | None = None,
    ) -> ChannelResponse:
        """Channel for recognize.

        Get channel chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/channel"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ChannelResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "channel", e, response) from e

    def conversion(
        self,
        body: dict[str, Any] | None = None,
    ) -> ConversionResponse:
        """Conversion for recognize.

        Get conversion chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/conversion"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ConversionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "conversion", e, response) from e

    def enjoy(
        self,
        body: dict[str, Any] | None = None,
    ) -> EnjoyResponse:
        """Enjoy for recognize.

        Get enjoy chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/enjoy"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EnjoyResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "enjoy", e, response) from e

    def friction_aggregation(
        self,
        body: dict[str, Any] | None = None,
    ) -> FrictionAggregationResponse:
        """Friction Aggregation for recognize.

        Get Friction Aggregation chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/friction_aggregation"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return FrictionAggregationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "friction_aggregation", e, response) from e

    def friction_histogram(
        self,
        body: dict[str, Any] | None = None,
    ) -> FrictionHistogramResponse:
        """Friction Histogram for recognize.

        Get Histogram Aggregation chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/friction_histogram"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return FrictionHistogramResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "friction_histogram", e, response) from e

    def health(
        self,
    ) -> HealthResponse:
        """Health for recognize.

        Health Check
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/health"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HealthResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "health", e, response) from e

    def lift(
        self,
        body: dict[str, Any] | None = None,
    ) -> LiftResponse:
        """Lift for recognize.

        Get lift chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/lift"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LiftResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "lift", e, response) from e

    def rescue(
        self,
        body: dict[str, Any] | None = None,
    ) -> RescueResponse:
        """Rescue for recognize.

        Get rescue chart data from shape recognize api
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/rescue"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RescueResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "rescue", e, response) from e

    def top_reason_codes(
        self,
        body: dict[str, Any] | None = None,
    ) -> TopReasonCodesResponse:
        """Top Reason Codes for recognize.

        Top Reason Codes
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/dashboard/top_reason_code"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopReasonCodesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "top_reason_codes", e, response) from e

    def get_status_addon(
        self,
    ) -> GetStatusResponse:
        """Get Status Addon for recognize.

        Get Recognize provision status as add-on service
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/provision"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetStatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "get_status_addon", e, response) from e

    def state(
        self,
    ) -> StateResponse:
        """State for recognize.

        Get customer State if after or before
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/state"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "state", e, response) from e

    def subscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> SubscribeResponse:
        """Subscribe for recognize.

        Subscribe to Shape Recognize as add-on service
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/subscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "subscribe", e, response) from e

    def unsubscribe(
        self,
        body: dict[str, Any] | None = None,
    ) -> UnsubscribeResponse:
        """Unsubscribe for recognize.

        Unsubscribe to Shape Recognize as add-on service
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/unsubscribe"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return UnsubscribeResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "unsubscribe", e, response) from e

    def validate_src_tag_injection_addon(
        self,
        body: dict[str, Any] | None = None,
    ) -> ValidateSrcTagInjectionResponse:
        """Validate Src Tag Injection Addon for recognize.

        Validate src tag injection in the target url
        """
        path = "/api/shape/recognize/namespaces/system/recognize/addon/validate/src_tag_injection"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ValidateSrcTagInjectionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("recognize", "validate_src_tag_injection_addon", e, response) from e

