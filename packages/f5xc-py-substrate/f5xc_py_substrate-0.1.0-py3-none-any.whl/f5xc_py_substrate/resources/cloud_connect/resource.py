"""CloudConnect resource API."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from f5xc_py_substrate._http import HTTPClient
from f5xc_py_substrate.exceptions import F5XCError, F5XCPartialResultsError, F5XCValidationError
from f5xc_py_substrate.resources.cloud_connect.models import (
    CloudConnectListItem,
    AWSRouteTableType,
    AWSRouteTableListType,
    SubnetStatusType,
    AWSAttachmentsStatusType,
    AWSConnectPeerStatusType,
    AWSConnectAttachmentStatusType,
    AWSTGWResourceReference,
    AWSTGWRouteTableStatusType,
    AWSAttachmentsListStatusType,
    AWSDefaultRoutesRouteTable,
    ObjectRefType,
    Ipv4AddressType,
    Ipv6AddressType,
    IpAddressType,
    NodeType,
    PeerType,
    Empty,
    DefaultRoute,
    AWSVPCAttachmentType,
    AWSVPCAttachmentListType,
    AWSTGWSiteType,
    AzureRouteTableWithStaticRoute,
    AzureRouteTableWithStaticRouteListType,
    AzureAttachmentsStatusType,
    AzureAttachmentsListStatusType,
    AzureRouteTables,
    AzureDefaultRoute,
    AzureVNETAttachmentType,
    AzureVnetAttachmentListType,
    AzureVNETSiteType,
    TrendValue,
    MetricValue,
    MetricData,
    Data,
    StatusType,
    CreateAWSTGWSiteType,
    ObjectCreateMetaType,
    CreateSpecType,
    CreateRequest,
    ObjectGetMetaType,
    GetSpecType,
    InitializerType,
    StatusType,
    InitializersType,
    ViewRefType,
    SystemObjectGetMetaType,
    CreateResponse,
    CredentialsRequest,
    CredentialsResponse,
    CustomerEdge,
    DeleteRequest,
    ObjectRefType,
    DiscoverVPCRequest,
    DiscoveredVPCType,
    DiscoverVPCResponse,
    SegmentationData,
    EdgeData,
    Coordinates,
    EdgeSite,
    EdgeListResponse,
    FieldData,
    GetMetricsRequest,
    GetMetricsResponse,
    ObjectReplaceMetaType,
    ReplaceAWSTGWSiteType,
    ReplaceAzureVNETSiteType,
    ReplaceSpecType,
    ReplaceRequest,
    ConditionType,
    StatusMetaType,
    StatusObject,
    GetResponse,
    LabelFilter,
    ListMetricsRequest,
    ListMetricsResponse,
    ProtobufAny,
    ErrorType,
    ListResponseItem,
    ListResponse,
    ListSegmentMetricsRequest,
    ListSegmentMetricsResponse,
    ReApplyVPCAttachmentRequest,
    ReApplyVPCAttachmentResponse,
    ReplaceResponse,
    TopCloudConnectData,
    TopCloudConnectRequest,
    TopCloudConnectResponse,
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


class CloudConnectResource:
    """API methods for cloud_connect.

    Cloud Connect Represents connection endpoint for cloud.
    """

    # Expose commonly-used models as class attributes for convenient access
    # Usage: client.cloud_connect.CreateSpecType(...)
    CreateSpecType = CreateSpecType
    GetSpecType = GetSpecType
    ReplaceSpecType = ReplaceSpecType
    GetResponse = GetResponse

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def create(
        self,
        namespace: str,
        name: str,
        spec: AWSRouteTableType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> CreateResponse:
        """Create a new cloud_connect.

        Shape of the Cloud Connect specification

        Args:
            namespace: The namespace to create the resource in.
            name: The name of the resource.
            spec: The resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to create the resource in disabled state.
        """
        path = "/api/config/namespaces/{metadata.namespace}/cloud_connects"
        path = path.replace("{metadata.namespace}", namespace)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.post(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CreateResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "create", e, response) from e

    def replace(
        self,
        namespace: str,
        name: str,
        spec: AWSRouteTableType | None = None,
        *,
        body: dict[str, Any] | None = None,
        labels: dict[str, str] | None = None,
        annotations: dict[str, str] | None = None,
        description: str | None = None,
        disable: bool | None = None,
    ) -> ReplaceResponse:
        """Replace an existing cloud_connect.

        Shape of the Cloud Connect specification

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to replace.
            spec: The new resource specification (typed model).
            body: Raw JSON body (alternative to spec, for advanced use).
            labels: Optional labels for the resource.
            annotations: Optional annotations for the resource.
            description: Optional description.
            disable: Whether to disable the resource.
        """
        path = "/api/config/namespaces/{metadata.namespace}/cloud_connects/{metadata.name}"
        path = path.replace("{metadata.namespace}", namespace)
        path = path.replace("{metadata.name}", name)

        if body is not None:
            request_body = body
        else:
            request_body: dict[str, Any] = {
                "metadata": {
                    "name": name,
                    "namespace": namespace,
                },
            }
            if labels:
                request_body["metadata"]["labels"] = labels
            if annotations:
                request_body["metadata"]["annotations"] = annotations
            if description:
                request_body["metadata"]["description"] = description
            if disable is not None:
                request_body["metadata"]["disable"] = disable
            # Always include spec - API requires it even if empty
            if spec is not None:
                request_body["spec"] = spec.model_dump(by_alias=True, exclude_none=True)
            else:
                request_body["spec"] = {}

        try:
            response = self._http.put(path, json=request_body)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReplaceResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "replace", e, response) from e

    def list(
        self,
        namespace: str,
        label_filter: str | None = None,
        report_fields: list | None = None,
        report_status_fields: list | None = None,
    ) -> list[CloudConnectListItem]:
        """List cloud_connect resources in a namespace.

        List the set of cloud_connect in a namespace

        Raises:
            F5XCPartialResultsError: If the response contains errors alongside items.
        """
        path = "/api/config/namespaces/{namespace}/cloud_connects"
        path = path.replace("{namespace}", namespace)

        params: dict[str, Any] = {}
        if label_filter is not None:
            params["label_filter"] = label_filter
        if report_fields is not None:
            params["report_fields"] = report_fields
        if report_status_fields is not None:
            params["report_status_fields"] = report_status_fields

        try:
            response = self._http.get(path, params=params if params else None)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

        items = response.get("items", [])
        errors = response.get("errors", [])

        if errors:
            raise F5XCPartialResultsError(items=items, errors=errors)

        try:
            return [CloudConnectListItem(**item) for item in items]
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "list", e, response) from e

    def get(
        self,
        namespace: str,
        name: str,
        response_format: str | None = None,
        *,
        exclude: list[str] | None = None,
        include_all: bool = False,
    ) -> GetResponse:
        """Get a cloud_connect by name.

        Shape of the Cloud Connect specification

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
        path = "/api/config/namespaces/{namespace}/cloud_connects/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        params: dict[str, Any] = {}
        if response_format is not None:
            params["response_format"] = response_format

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
            raise F5XCValidationError("cloud_connect", "get", e, response) from e

    def delete(
        self,
        namespace: str,
        name: str,
    ) -> None:
        """Delete a cloud_connect.

        Delete the specified cloud_connect

        Args:
            namespace: The namespace of the resource.
            name: The name of the resource to delete.
        """
        path = "/api/config/namespaces/{namespace}/cloud_connects/{name}"
        path = path.replace("{namespace}", namespace)
        path = path.replace("{name}", name)

        try:
            self._http.delete(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None

    def re_apply_vpc_attachment(
        self,
        body: dict[str, Any] | None = None,
    ) -> ReApplyVPCAttachmentResponse:
        """Re Apply Vpc Attachment for cloud_connect.

        Re-applies VPC attachment in a cloud connect config.
        """
        path = "/api/sync-cloud-data/namespaces/system/cloud_connect_reapply_vpc_attachment"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ReApplyVPCAttachmentResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "re_apply_vpc_attachment", e, response) from e

    def list_metrics(
        self,
        body: dict[str, Any] | None = None,
    ) -> ListMetricsResponse:
        """List Metrics for cloud_connect.

        Cloud Connect APIs are used to get the data for cloud connect.
        """
        path = "/api/data/namespaces/system/cloud_connects/metrics"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListMetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "list_metrics", e, response) from e

    def list_segment_metrics(
        self,
        body: dict[str, Any] | None = None,
    ) -> ListSegmentMetricsResponse:
        """List Segment Metrics for cloud_connect.

        Cloud Connect APIs are used to get the segment data for cloud connect.
        """
        path = "/api/data/namespaces/system/cloud_connects/segment_metrics"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return ListSegmentMetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "list_segment_metrics", e, response) from e

    def get_metrics(
        self,
        name: str,
        body: dict[str, Any] | None = None,
    ) -> GetMetricsResponse:
        """Get Metrics for cloud_connect.

        Cloud Connect Metrics queries metrics for a specified cloud connect.
        """
        path = "/api/data/namespaces/system/cloud_connects/{name}/metrics"
        path = path.replace("{name}", name)


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return GetMetricsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "get_metrics", e, response) from e

    def discover_vpc(
        self,
        body: dict[str, Any] | None = None,
    ) -> DiscoverVPCResponse:
        """Discover Vpc for cloud_connect.

        Returns all the vpcs for a specified cloud provider, region and...
        """
        path = "/api/sync-cloud-data/namespaces/system/discover_vpc"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return DiscoverVPCResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "discover_vpc", e, response) from e

    def edge_credentials(
        self,
        body: dict[str, Any] | None = None,
    ) -> CredentialsResponse:
        """Edge Credentials for cloud_connect.

        Returns the cloud credential for the matching edge type
        """
        path = "/api/config/namespaces/system/edge_credentials"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return CredentialsResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "edge_credentials", e, response) from e

    def edge_list(
        self,
    ) -> EdgeListResponse:
        """Edge List for cloud_connect.

        Returns the online edge sites (Both Customer Edge and Cloud Edge)
        """
        path = "/api/config/namespaces/system/edge_list"


        try:
            response = self._http.get(path)
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return EdgeListResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "edge_list", e, response) from e

    def top_cloud_connect(
        self,
        body: dict[str, Any] | None = None,
    ) -> TopCloudConnectResponse:
        """Top Cloud Connect for cloud_connect.

        Request to get top cloud connect from the AWS Cloudwatch metrics
        """
        path = "/api/data/namespaces/system/top/cloud_connects"


        try:
            response = self._http.post(path, json=body or {})
        except F5XCError as e:
            raise type(e)(e.status_code, e.message, e.body) from None
        try:
            return TopCloudConnectResponse(**response)
        except ValidationError as e:
            raise F5XCValidationError("cloud_connect", "top_cloud_connect", e, response) from e

