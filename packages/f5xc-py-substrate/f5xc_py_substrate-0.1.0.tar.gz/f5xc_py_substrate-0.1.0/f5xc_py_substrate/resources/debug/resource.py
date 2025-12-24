"""Debug resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.debug.models import (
    ProtobufAny,
    HttpBody,
    BlindfoldSecretInfoType,
    ClearSecretInfoType,
    SecretType,
    ChangePasswordRequest,
    CheckDebugInfoCollectionResponse,
    DiagnosisResponse,
    ExecLogResponse,
    ExecResponse,
    Bios,
    Board,
    Chassis,
    Cpu,
    GPUDevice,
    GPU,
    Kernel,
    Memory,
    NetworkDevice,
    OS,
    Product,
    StorageDevice,
    USBDevice,
    OsInfo,
    HealthResponse,
    HostPingRequest,
    HostPingResponse,
    Service,
    ListServicesResponse,
    LogResponse,
    RebootRequest,
    RebootResponse,
    SoftRestartRequest,
    SoftRestartResponse,
    Status,
    StatusResponse,
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


class DebugResource:
    """API methods for debug.

    Proto definitions for debugging site
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.debug.CreateSpecType(...)

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def check_debug_info_collection(
        self,
        site: str,
    ) -> CheckDebugInfoCollectionResponse:
        """Check Debug Info Collection for debug.

        Check if the zip file of debug info from node is available
        """
        path = "/api/operate/namespaces/system/sites/{site}/vpm/debug/global/check-debug-info-collection"
        path = path.replace("{site}", site)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CheckDebugInfoCollectionResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "check_debug_info_collection", e, response) from e

    def diagnosis_public(
        self,
        site: str,
        console_user: str | None = None,
    ) -> DiagnosisResponse:
        """Diagnosis Public for debug.

        Get VPM network information
        """
        path = "/api/operate/namespaces/system/sites/{site}/vpm/debug/global/diagnosis"
        path = path.replace("{site}", site)

        params: dict[str, Any] = {}
        if console_user is not None:
            params["console_user"] = console_user

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DiagnosisResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "diagnosis_public", e, response) from e

    def download_debug_info_collection(
        self,
        site: str,
    ) -> HttpBody:
        """Download Debug Info Collection for debug.

        Download the zip file of debug info from node if available
        """
        path = "/api/operate/namespaces/system/sites/{site}/vpm/debug/global/download-debug-info-collection"
        path = path.replace("{site}", site)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HttpBody(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "download_debug_info_collection", e, response) from e

    def health_public(
        self,
        site: str,
        console_user: str | None = None,
    ) -> HealthResponse:
        """Health Public for debug.

        Get VPM health information
        """
        path = "/api/operate/namespaces/system/sites/{site}/vpm/debug/global/health"
        path = path.replace("{site}", site)

        params: dict[str, Any] = {}
        if console_user is not None:
            params["console_user"] = console_user

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HealthResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "health_public", e, response) from e

    def change_password_public(
        self,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Change Password Public for debug.

        Change host user password
        """
        path = "/api/operate/namespaces/system/sites/{site}/vpm/debug/{node}/change-password"
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def start_debug_info_collection(
        self,
        site: str,
        node: str,
    ) -> dict[str, Any]:
        """Start Debug Info Collection for debug.

        Start collecting a zip file of debug info from node
        """
        path = "/api/operate/namespaces/system/sites/{site}/vpm/debug/{node}/start-debug-info-collection"
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        return response

    def list_volterra_services(
        self,
        namespace: str,
        site: str,
    ) -> ListServicesResponse:
        """List Volterra Services for debug.

        Get List of services managed by Volterra
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/global/list-service"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListServicesResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "list_volterra_services", e, response) from e

    def status(
        self,
        namespace: str,
        site: str,
        vesnamespace: str,
        cached: bool | None = None,
    ) -> StatusResponse:
        """Status for debug.

        Get Status of F5XC components
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/global/{vesnamespace}/status"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{vesnamespace}", vesnamespace)

        params: dict[str, Any] = {}
        if cached is not None:
            params["cached"] = cached

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return StatusResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "status", e, response) from e

    def exec(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> ExecResponse:
        """Exec for debug.

        Run supported exec command on node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/exec"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ExecResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "exec", e, response) from e

    def exec_log(
        self,
        namespace: str,
        site: str,
        node: str,
        line_count: int | None = None,
    ) -> ExecLogResponse:
        """Exec Log for debug.

        Retrieve exec history on node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/exec-log"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)

        params: dict[str, Any] = {}
        if line_count is not None:
            params["line_count"] = line_count

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ExecLogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "exec_log", e, response) from e

    def exec_user(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> ExecResponse:
        """Exec User for debug.

        Run supported exec command on node with lower privilege
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/exec-user"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ExecResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "exec_user", e, response) from e

    def host_ping(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> HostPingResponse:
        """Host Ping for debug.

        Ping intiated from host kernel
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/host-ping"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return HostPingResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "host_ping", e, response) from e

    def reboot(
        self,
        namespace: str,
        site: str,
        node: str,
        body: dict[str, Any] | None = None,
    ) -> RebootResponse:
        """Reboot for debug.

        Reboot specific node in site
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/reboot"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return RebootResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "reboot", e, response) from e

    def log(
        self,
        namespace: str,
        site: str,
        node: str,
        service: str,
        last_lines: int | None = None,
    ) -> LogResponse:
        """Log for debug.

        Get logs for given service from the specific node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/{service}/log"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)
        path = path.replace("{service}", service)

        params: dict[str, Any] = {}
        if last_lines is not None:
            params["last_lines"] = last_lines

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return LogResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "log", e, response) from e

    def soft_restart(
        self,
        namespace: str,
        site: str,
        node: str,
        service: str,
        body: dict[str, Any] | None = None,
    ) -> SoftRestartResponse:
        """Soft Restart for debug.

        Soft restart reloads VER instance on the node
        """
        path = "/api/operate/namespaces/{namespace}/sites/{site}/vpm/debug/{node}/{service}/soft-restart"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{site}", site)
        path = path.replace("{node}", node)
        path = path.replace("{service}", service)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return SoftRestartResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("debug", "soft_restart", e, response) from e

