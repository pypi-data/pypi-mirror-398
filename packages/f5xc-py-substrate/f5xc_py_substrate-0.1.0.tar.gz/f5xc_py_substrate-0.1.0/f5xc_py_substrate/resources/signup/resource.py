"""Signup resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.signup.models import (
    Policer,
    BlindfoldSecretInfoType,
    CRMInfo,
    ClearSecretInfoType,
    ConditionType,
    Empty,
    InitializerType,
    StatusType,
    InitializersType,
    ObjectMetaType,
    ObjectRefType,
    SecretType,
    StatusMetaType,
    ViewRefType,
    SystemObjectMetaType,
    GlobalSpecType,
    GlobalSpecType,
    GlobalSpecType,
    GlobalSpecType,
    CityItem,
    CountryItem,
    SpecType,
    Object,
    StatusObject,
    GetResponse,
    ListCitiesResponse,
    ListCountriesResponse,
    StateItem,
    ListStatesResponse,
    SendPasswordEmailRequest,
    SendPasswordEmailResponse,
    ValidateContactRequest,
    ValidationErrorField,
    ValidateContactResponse,
    ValidateRegistrationRequest,
    ValidateRegistrationResponse,
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


class SignupResource:
    """API methods for signup.

    Use this API to signup for F5XC service.
one can signup to use...
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.signup.CreateSpecType(...)
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def list_states(
        self,
        country_code: str,
        prefix: str,
    ) -> ListStatesResponse:
        """List States for signup.

        Returns a list of known states of a country. List will be empty if...
        """
        path = "/no_auth/countries/{country_code}/states/{prefix}"
        path = path.replace("{country_code}", country_code)
        path = path.replace("{prefix}", prefix)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListStatesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "list_states", e, response) from e

    def list_cities(
        self,
        country_code: str,
        state_code: str,
        prefix: str,
    ) -> ListCitiesResponse:
        """List Cities for signup.

        Returns a list of known cities of a country/state.
        """
        path = "/no_auth/countries/{country_code}/states/{state_code}/cities/{prefix}"
        path = path.replace("{country_code}", country_code)
        path = path.replace("{state_code}", state_code)
        path = path.replace("{prefix}", prefix)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListCitiesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "list_cities", e, response) from e

    def list_countries(
        self,
        prefix: str,
    ) -> ListCountriesResponse:
        """List Countries for signup.

        Returns a list of supported countries along with with additional...
        """
        path = "/no_auth/countries/{prefix}"
        path = path.replace("{prefix}", prefix)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListCountriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "list_countries", e, response) from e

    def validate_registration(
        self,
        body: dict[str, Any] | None = None,
    ) -> ValidateRegistrationResponse:
        """Validate Registration for signup.

        ValidateRegistration validates if the signup registration request is...
        """
        path = "/no_auth/login/validate_registration"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ValidateRegistrationResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "validate_registration", e, response) from e

    def send_password_email(
        self,
        body: dict[str, Any] | None = None,
    ) -> SendPasswordEmailResponse:
        """Send Password Email for signup.

        SendPasswordEmail enables resetting the password at the time of...
        """
        path = "/no_auth/send_password_email"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SendPasswordEmailResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "send_password_email", e, response) from e

    def get(
        self,
        name: str,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a signup by name.

        Get allows users to query signup and its status. Use this to query...

        By default, excludes verbose fields (forms, references, system_metadata).
        Use include_all=True to get the complete response.

        Args:
            exclude: Additional field groups to exclude from response.
                - 'forms': Excludes create_form, replace_form
                - 'references': Excludes referring_objects, deleted/disabled_referred_objects
                - 'system_metadata': Excludes system_metadata
                You can also pass individual field names directly.
            include_all: If True, return all fields without default exclusions.
        """
        path = "/no_auth/signup/{name}"
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        # Apply default exclusions unless include_all=True
        if not include_all:
            default_exclude = ["forms", "references", "system_metadata"]
            exclude = (exclude or []) + default_exclude

        if exclude:
            exclude_fields = _resolve_exclude_groups(exclude)
            # Remove excluded fields entirely from response
            filtered_response = {
                k: v for k, v in response.items()
                if k not in exclude_fields
            }
        else:
            filtered_response = response

        try:
            return GetResponse(**filtered_response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "get", e, response) from e

    def validate_contact(
        self,
        body: dict[str, Any] | None = None,
    ) -> ValidateContactResponse:
        """Validate Contact for signup.

        It validates that: * the provided country and zip code are not empty...
        """
        path = "/no_auth/validate_contact"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ValidateContactResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "validate_contact", e, response) from e

    def custom_list_states(
        self,
        country_code: str,
        prefix: str,
    ) -> ListStatesResponse:
        """Custom List States for signup.

        Returns a list of known states of a country. List will be empty if...
        """
        path = "/api/web/custom/countries/{country_code}/states/{prefix}"
        path = path.replace("{country_code}", country_code)
        path = path.replace("{prefix}", prefix)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListStatesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "custom_list_states", e, response) from e

    def custom_list_cities(
        self,
        country_code: str,
        state_code: str,
        prefix: str,
    ) -> ListCitiesResponse:
        """Custom List Cities for signup.

        Returns a list of known cities of a country/state.
        """
        path = "/api/web/custom/countries/{country_code}/states/{state_code}/cities/{prefix}"
        path = path.replace("{country_code}", country_code)
        path = path.replace("{state_code}", state_code)
        path = path.replace("{prefix}", prefix)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListCitiesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "custom_list_cities", e, response) from e

    def custom_list_countries(
        self,
        prefix: str,
    ) -> ListCountriesResponse:
        """Custom List Countries for signup.

        Returns a list of supported countries along with with additional...
        """
        path = "/api/web/custom/countries/{prefix}"
        path = path.replace("{prefix}", prefix)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListCountriesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("signup", "custom_list_countries", e, response) from e

