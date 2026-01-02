"""Low-level gRPC client for the Kumiho Cloud service.

This module provides the internal ``_Client`` class that handles all gRPC
communication with Kumiho Cloud servers. It manages:

- Connection establishment (TLS/insecure, target resolution)
- Authentication (Bearer token injection)
- Discovery-based tenant routing
- All gRPC method calls

The ``_Client`` class is not intended to be used directly by end users.
Instead, use the high-level functions and classes exposed by the ``kumiho``
package, such as :func:`kumiho.connect`, :class:`kumiho.Project`, etc.

Example:
    Internal usage (not recommended for end users)::

        from kumiho.client import _Client

        client = _Client(target="us-central.kumiho.cloud:443")
        space = client.create_space(project_kref, "my-space")

    Preferred high-level usage::

        import kumiho

        kumiho.connect()
        project = kumiho.create_project(name="my-project")

Attributes:
    _LOGGER: Module-level logger for client operations.
    _DISCOVERY_DISABLE_ENV: Environment variable to disable auto-discovery.
    _FORCE_REFRESH_ENV: Environment variable to force discovery cache refresh.

Note:
    This module is considered internal API. The public interface may change
    between minor versions. Use the ``kumiho`` package-level API instead.
"""

import logging
import os
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING
from urllib.parse import urlparse

import grpc

from google.protobuf.json_format import MessageToDict

from ._token_loader import load_bearer_token
from .discovery import DiscoveryError, DiscoveryManager
from .proto import kumiho_pb2
from .proto import kumiho_pb2_grpc
from .event import Event
from .space import Space
from .kref import Kref
from .proto.kumiho_pb2 import (
    CreateSpaceRequest,
    CreateEdgeRequest,
    CreateItemRequest,
    CreateArtifactRequest,
    CreateRevisionRequest,
    CreateProjectRequest,
    DeleteSpaceRequest,
    DeleteEdgeRequest,
    DeleteItemRequest,
    DeleteArtifactRequest,
    DeleteRevisionRequest,
    DeleteProjectRequest,
    DeleteAttributeRequest,
    EventStreamRequest,
    GetAttributeRequest,
    GetChildSpacesRequest,
    GetSpaceRequest,
    GetEdgesRequest,
    GetItemRequest,
    GetItemsRequest,
    GetProjectsRequest,
    GetArtifactRequest,
    GetArtifactsRequest,
    GetArtifactsByLocationRequest,
    GetTenantUsageRequest,
    GetRevisionsRequest,
    GetEventCapabilitiesRequest,
    HasTagRequest,
    KrefRequest,
    Edge as PbEdge,
    EdgeDirection,
    PeekNextRevisionRequest,
    ItemSearchRequest,
    ResolveKrefRequest,
    ResolveLocationRequest,
    SetAttributeRequest,
    SetDefaultArtifactRequest,
    TagRevisionRequest,
    UnTagRevisionRequest,
    UpdateMetadataRequest,
    WasTaggedRequest,
    SetDeprecatedRequest,
    TraverseEdgesRequest,
    ShortestPathRequest,
    ImpactAnalysisRequest,
    CreateBundleRequest,
    AddBundleMemberRequest,
    RemoveBundleMemberRequest,
    GetBundleMembersRequest,
    GetBundleHistoryRequest,
    PaginationRequest,
)
from .edge import Edge, TraversalResult, ImpactedRevision, ShortestPathResult
from .proto.kumiho_pb2 import ProjectResponse, StatusResponse
from .project import Project
from .item import Item
from .artifact import Artifact
from .revision import Revision
from .base import PagedList

if TYPE_CHECKING:
    from .bundle import Bundle, BundleMember, BundleRevisionHistory


_LOGGER = logging.getLogger("kumiho.client")
_DISCOVERY_DISABLE_ENV = "KUMIHO_DISABLE_AUTO_DISCOVERY"
_FORCE_REFRESH_ENV = "KUMIHO_FORCE_DISCOVERY_REFRESH"


class ProjectLimitError(Exception):
    """Raised when guardrails block project creation (e.g., max projects reached)."""


class _Client:
    """Low-level gRPC client for interacting with the Kumiho Cloud service.

    This client provides direct access to all Kumiho gRPC endpoints for
    managing projects, spaces, items, revisions, artifacts, and edges.
    It handles connection management, authentication, and discovery-based
    tenant routing automatically.

    The client is typically not instantiated directly. Instead, use
    :func:`kumiho.connect` which manages a context-variable-scoped client
    instance.

    Attributes:
        channel (grpc.Channel): The gRPC channel to the Kumiho server.
        stub (KumihoGraphStub): The gRPC stub for making service calls.

    Example:
        Using the client directly (not recommended)::

            from kumiho.client import _Client

            client = _Client(
                target="us-central.kumiho.cloud:443",
                auth_token="eyJhbG..."
            )
            projects = client.get_projects()

        Using via kumiho.connect (recommended)::

            import kumiho

            kumiho.connect()
            projects = kumiho.list_projects()

    Note:
        This class is considered internal API. Use the public ``kumiho``
        module functions instead for stable interfaces.
    """

    def __init__(
        self,
        target: Optional[str] = None,
        *,
        auth_token: Optional[str] = None,
        default_metadata: Optional[Sequence[Tuple[str, str]]] = None,
        use_discovery: Optional[bool] = None,
        tenant_hint: Optional[str] = None,
        force_discovery_refresh: Optional[bool] = None,
        enable_auto_login: bool = True,
    ) -> None:
        """Initialize the gRPC client with connection and authentication settings.

        The client resolves the target server using the following priority:

        1. Explicit ``target`` parameter
        2. Discovery endpoint (if enabled and token available)
        3. ``KUMIHO_SERVER_ENDPOINT`` environment variable
        4. ``KUMIHO_SERVER_ADDRESS`` environment variable (legacy)
        5. ``localhost:8080`` (default for local development)

        Args:
            target: Server endpoint. Accepts formats:

                - ``host:port`` — plain gRPC
                - ``https://host`` — secure gRPC on port 443
                - ``grpcs://host:port`` — secure gRPC on custom port

                If None, the client attempts discovery or falls back to
                environment variables.
            auth_token: Bearer token for authentication. Sent as
                ``Authorization: Bearer <token>`` on every RPC. If not
                provided, falls back to:

                - ``KUMIHO_AUTH_TOKEN`` environment variable
                - Token file from ``kumiho-auth`` CLI cache
            default_metadata: Additional gRPC metadata to attach to all
                outbound RPCs. Each entry is a ``(key, value)`` tuple.
            use_discovery: Whether to use the discovery endpoint for
                tenant routing. Defaults to True unless disabled via
                ``KUMIHO_DISABLE_AUTO_DISCOVERY=true``.
            tenant_hint: Optional tenant ID hint for discovery or direct
                tenant header injection when discovery is disabled.
            force_discovery_refresh: Force refresh of discovery cache.
                Overrides ``KUMIHO_FORCE_DISCOVERY_REFRESH`` env var.
            enable_auto_login: Whether to enable auto-login when no
                credentials are available. Defaults to True.

        Raises:
            grpc.RpcError: If the connection cannot be established.
            DiscoveryError: If discovery fails and no fallback is available.

        Example:
            Basic initialization::

                client = _Client()  # Uses defaults

            With explicit settings::

                client = _Client(
                    target="us-central.kumiho.cloud:443",
                    auth_token="eyJhbG...",
                    default_metadata=[("x-custom-header", "value")]
                )
        """
        metadata: List[Tuple[str, str]] = list(default_metadata or [])
        resolved_token = auth_token or load_bearer_token()

        discovery = self._maybe_resolve_via_discovery(
            explicit_target=target,
            use_discovery=use_discovery,
            id_token=resolved_token,
            tenant_hint=tenant_hint,
            force_discovery_refresh=force_discovery_refresh,
        )
        tenant_header_set = False

        if discovery:
            target = discovery[0]
            if len(discovery) > 1 and discovery[1]:
                metadata.append(("x-tenant-id", discovery[1]))
                tenant_header_set = True
        elif tenant_hint:
            # Fallback: if discovery didn't run (e.g. no token), use the hint directly
            metadata.append(("x-tenant-id", tenant_hint))
            tenant_header_set = True

        if target is None:
            target = (
                os.getenv("KUMIHO_SERVER_ENDPOINT")
                or os.getenv("KUMIHO_SERVER_ADDRESS")
                or "localhost:8080"
            )

        authority_override = os.getenv("KUMIHO_SERVER_AUTHORITY")
        ssl_override = os.getenv("KUMIHO_SSL_TARGET_OVERRIDE")
        ca_bundle = os.getenv("KUMIHO_SERVER_CA_FILE")
        use_tls_env = os.getenv("KUMIHO_SERVER_USE_TLS")

        address, authority, use_tls = self._normalise_target(target)
        if use_tls_env:
            use_tls = use_tls_env.lower() in {"1", "true", "yes"}

        if authority_override:
            authority = authority_override

        if use_tls:
            credentials = self._build_ssl_credentials(ca_bundle)
            options = [("grpc.default_authority", authority)]
            if ssl_override:
                options.append(("grpc.ssl_target_name_override", ssl_override))
            channel = grpc.secure_channel(address, credentials, options=options)
        else:
            channel = grpc.insecure_channel(address)

        if resolved_token:
            metadata.append(("authorization", f"Bearer {resolved_token}"))

        # Apply interceptors in order: correlation ID, auto-login, then metadata injection
        channel = grpc.intercept_channel(channel, _CorrelationIdInterceptor())
        if enable_auto_login:
            channel = grpc.intercept_channel(channel, _AutoLoginInterceptor())
        if metadata:
            channel = grpc.intercept_channel(channel, _MetadataInjector(metadata))

        self.channel = channel
        self.stub = kumiho_pb2_grpc.KumihoServiceStub(self.channel)


    @staticmethod
    def _env_flag(name: str, *, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() not in {"0", "false", "no"}

    def _maybe_resolve_via_discovery(
        self,
        *,
        explicit_target: Optional[str],
        use_discovery: Optional[bool],
        id_token: Optional[str],
        tenant_hint: Optional[str],
        force_discovery_refresh: Optional[bool],
    ) -> Optional[Tuple[str, Optional[str]]]:
        if explicit_target:
            return None

        should_use = use_discovery
        if should_use is None:
            should_use = not self._env_flag(_DISCOVERY_DISABLE_ENV)

        if not should_use:
            return None

        if not id_token:
            _LOGGER.debug("Discovery skipped: no Firebase token available")
            return None

        hint = tenant_hint or None
        force_refresh = (
            force_discovery_refresh
            if force_discovery_refresh is not None
            else self._env_flag(_FORCE_REFRESH_ENV, default=False)
        )

        manager = DiscoveryManager()
        try:
            record = manager.resolve(
                id_token=id_token,
                tenant_hint=hint,
                force_refresh=force_refresh,
            )
        except DiscoveryError as exc:
            _LOGGER.info("Discovery failed (%s); falling back to legacy target", exc)
            return None
        except Exception:  # pragma: no cover - defensive logging
            _LOGGER.exception("Unexpected discovery failure; falling back to legacy target")
            return None

        target = record.region.grpc_authority or record.region.server_url
        tenant_id = record.tenant_id
        _LOGGER.debug(
            "Resolved Kumiho endpoint via discovery: target=%s tenant=%s", target, tenant_id
        )
        return target, tenant_id

    @staticmethod
    def _normalise_target(raw_target: str) -> Tuple[str, str, bool]:
        """Convert the provided target into an address, authority, and TLS flag."""

        target = raw_target.strip()
        if not target:
            raise ValueError("Kumiho client target cannot be empty")

        scheme = ""
        host = ""
        port: Optional[int] = None

        if "://" in target:
            parsed = urlparse(target)
            scheme = parsed.scheme.lower()
            host = parsed.hostname or ""
            port = parsed.port
            if not host:
                raise ValueError(f"Invalid Kumiho endpoint: {target}")
            if port is None:
                if scheme in {"https", "grpcs"}:
                    port = 443
                elif scheme in {"http", "grpc"}:
                    port = 80
        else:
            scheme = ""
            # Strip any trailing path components
            if "/" in target:
                target = target.split("/", 1)[0]
            if ":" in target:
                host, port_str = target.split(":", 1)
                port = int(port_str) if port_str else None
            else:
                host = target
            if not host:
                raise ValueError(f"Invalid Kumiho endpoint: {raw_target}")

        if port is None:
            port = 443 if scheme in {"https", "grpcs"} else 8080

        authority = host
        address = f"{host}:{port}"
        use_tls = scheme in {"https", "grpcs"} or port == 443
        
        # Security: Warn if connecting to non-localhost without TLS
        is_localhost = host.lower() in {"localhost", "127.0.0.1", "::1"}
        require_tls = os.getenv("KUMIHO_REQUIRE_TLS", "").lower() in {"1", "true", "yes"}
        if not is_localhost and not use_tls:
            if require_tls:
                raise ValueError(
                    f"TLS is required but connecting to {host} without TLS. "
                    f"Use https:// or set port 443."
                )
            import warnings
            warnings.warn(
                f"Connecting to {host} without TLS. Credentials may be transmitted "
                f"in plaintext. Set KUMIHO_SERVER_USE_TLS=true or use https:// for production.",
                UserWarning,
                stacklevel=3,
            )
        
        return address, authority, use_tls

    @staticmethod
    def _build_ssl_credentials(ca_file: Optional[str]) -> grpc.ChannelCredentials:
        """Create SSL credentials, optionally using a custom CA bundle."""

        if ca_file:
            with open(ca_file, "rb") as handle:
                root_certs = handle.read()
            return grpc.ssl_channel_credentials(root_certificates=root_certs)
        return grpc.ssl_channel_credentials()

    # Project methods
    def create_project(self, name: str, description: str = "") -> Project:
        req = CreateProjectRequest(name=name, description=description)
        try:
            resp = self.stub.CreateProject(req)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
                raise ProjectLimitError(exc.details()) from None
            raise
        return Project(resp, self)

    def get_projects(self) -> List[Project]:
        req = GetProjectsRequest()
        resp = self.stub.GetProjects(req)
        return [Project(pb, self) for pb in resp.projects]

    def get_project(self, name: str) -> Optional[Project]:
        """Return the first project matching the given name, or None if not found."""
        for project in self.get_projects():
            if project.name == name:
                return project
        return None

    def delete_project(self, project_id: str, force: bool = False) -> StatusResponse:
        req = DeleteProjectRequest(project_id=project_id, force=force)
        resp = self.stub.DeleteProject(req)
        return resp

    def update_project(
        self,
        project_id: str,
        allow_public: Optional[bool] = None,
        description: Optional[str] = None
    ) -> Project:
        kwargs: Dict[str, Any] = {"project_id": project_id}
        if allow_public is not None:
            kwargs["allow_public"] = allow_public
        if description is not None:
            kwargs["description"] = description
        req = kumiho_pb2.UpdateProjectRequest(**kwargs)
        resp = self.stub.UpdateProject(req)
        return Project(resp, self)

    # Space methods
    def create_space(self, parent_path: str, space_name: str) -> Space:
        """Create a new space.

        Args:
            parent_path: The path of the parent space.
            space_name: The name of the new space.

        Returns:
            The created Space object.
        """
        req = CreateSpaceRequest(parent_path=parent_path, space_name=space_name)
        resp = self.stub.CreateSpace(req)
        return Space(resp, self)

    def get_space(self, path: str) -> Space:
        """Get a space by its path.

        Args:
            path: The path of the space to retrieve.

        Returns:
            The Space object.
        """
        req = GetSpaceRequest(path_or_kref=path)
        resp = self.stub.GetSpace(req)
        return Space(resp, self)

    def get_child_spaces(self, parent_path: str = "", recursive: bool = False) -> List[Space]:
        """Get child spaces of a parent space.

        Args:
            parent_path: The path of the parent space. If empty or "/",
                         returns root-level spaces.
            recursive: Whether to fetch all descendant spaces recursively.

        Returns:
            A list of Space objects that are direct children of the parent.
        """
        req = GetChildSpacesRequest(parent_path=parent_path, recursive=recursive)
        resp = self.stub.GetChildSpaces(req)
        return [Space(space_resp, self) for space_resp in resp.spaces]

    def update_space_metadata(self, kref: Kref, metadata: Dict[str, str]) -> Space:
        """Update metadata for a space.

        Args:
            kref: The kref of the space.
            metadata: The metadata to update.

        Returns:
            The updated Space object.
        """
        req = UpdateMetadataRequest(kref=kref.to_pb(), metadata=metadata)
        resp = self.stub.UpdateSpaceMetadata(req)
        return Space(resp, self)

    # Item methods
    def create_item(self, parent_path: str, item_name: str, kind: str, metadata: Optional[Dict[str, str]] = None) -> Item:
        """Create a new item.

        Args:
            parent_path: The path of the parent space.
            item_name: The name of the item.
            kind: The kind of the item (e.g., "model", "texture").
            metadata: Metadata dictionary for the item.

        Returns:
            The created Item object.

        Raises:
            ReservedKindError: If kind is reserved (e.g., 'bundle').
        """
        from .bundle import RESERVED_KINDS, ReservedKindError
        
        if kind.lower() in RESERVED_KINDS:
            raise ReservedKindError(
                f"Item kind '{kind}' is reserved. "
                f"Use the dedicated create_bundle() method instead."
            )
        
        req = CreateItemRequest(parent_path=parent_path, item_name=item_name, kind=kind)
        resp = self.stub.CreateItem(req)
        if metadata and isinstance(metadata, dict):
            self.update_item_metadata(resp.kref, metadata)
        return Item(resp, self)

    def get_item(self, parent_path: str, item_name: str, kind: str) -> Item:
        """Get an item by its parent path, name, and kind.

        Args:
            parent_path: The path of the parent space.
            item_name: The name of the item.
            kind: The kind of the item.

        Returns:
            The Item object.
        """
        req = GetItemRequest(parent_path=parent_path, item_name=item_name, kind=kind)
        resp = self.stub.GetItem(req)
        return Item(resp, self)

    def get_item_by_kref(self, kref_uri: str) -> Item:
        """Get an item by its kref URI.

        Args:
            kref_uri: The kref URI of the item.

        Returns:
            The Item object.
        """
        kref = Kref(kref_uri)
        item_path = kref.get_path()  # e.g., "projectA/modelA.asset"
        if "/" not in item_path:
            raise ValueError(f"Invalid item kref format: {kref}")
        
        space_path, item_name_kind = item_path.split("/", 1)
        parent_path = f"/{space_path}"  # Add leading slash
        if "." not in item_name_kind:
            raise ValueError(f"Invalid item name.kind format: {item_name_kind}")
        
        item_name, kind = item_name_kind.split(".", 1)
        
        return self.get_item(parent_path, item_name, kind)

    def get_bundle_by_kref(self, kref_uri: str) -> "Bundle":
        """Get a bundle by its kref URI.

        This method retrieves an item and verifies it is a bundle (kind='bundle').
        If the item exists but is not a bundle, raises a ValueError.

        Args:
            kref_uri: The kref URI of the bundle
                (e.g., "kref://project/space/mybundle.bundle").

        Returns:
            Bundle: The Bundle object.

        Raises:
            ValueError: If the item exists but is not a bundle (kind != 'bundle').
            grpc.RpcError: If the item is not found.

        Example:
            >>> bundle = client.get_bundle_by_kref(
            ...     "kref://my-project/assets/character-bundle.bundle"
            ... )
            >>> members = bundle.get_members()
        """
        from .bundle import Bundle
        
        # First get the item
        item = self.get_item_by_kref(kref_uri)
        
        # Verify it's a bundle
        if item.kind != "bundle":
            raise ValueError(
                f"Item '{kref_uri}' is not a bundle (kind='{item.kind}'). "
                f"Use get_item() for non-bundle items."
            )
        
        # Re-fetch as Bundle to get the Bundle wrapper with bundle-specific methods
        kref = Kref(kref_uri)
        item_path = kref.get_path()
        space_path, item_name_kind = item_path.split("/", 1)
        parent_path = f"/{space_path}"
        bundle_name, _ = item_name_kind.split(".", 1)
        
        # Use GetItem to get the raw response and wrap as Bundle
        req = GetItemRequest(parent_path=parent_path, item_name=bundle_name, kind="bundle")
        resp = self.stub.GetItem(req)
        return Bundle(resp, self)

    def get_items(
        self,
        parent_path: str,
        item_name_filter: str = "",
        kind_filter: str = "",
        page_size: Optional[int] = None,
        cursor: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Item]:
        """Get items within a space with optional filtering.

        Args:
            parent_path: The path of the parent space.
            item_name_filter: Optional filter for item names.
            kind_filter: Optional filter for item kinds.
            page_size: Optional page size for pagination.
            cursor: Optional cursor for pagination.
            include_deprecated: Whether to include deprecated items.

        Returns:
            A list of Item objects matching the filters.
            If pagination is used, returns a PagedList.
        """
        pagination = None
        if page_size is not None or cursor is not None:
            pagination = PaginationRequest(page_size=page_size or 100, cursor=cursor or "")

        req = GetItemsRequest(
            parent_path=parent_path,
            item_name_filter=item_name_filter,
            kind_filter=kind_filter,
            pagination=pagination,
            include_deprecated=include_deprecated
        )
        resp = self.stub.GetItems(req)
        items = [Item(p, self) for p in resp.items]

        if resp.HasField("pagination"):
            return PagedList(
                items,
                next_cursor=resp.pagination.next_cursor,
                total_count=resp.pagination.total_count
            )
        return items

    def item_search(
        self,
        context_filter: str = "",
        item_name_filter: str = "",
        kind_filter: str = "",
        page_size: Optional[int] = None,
        cursor: Optional[str] = None,
        include_deprecated: bool = False
    ) -> List[Item]:
        """Search for items across the system.

        Args:
            context_filter: Filter by context/path.
            item_name_filter: Filter by item name.
            kind_filter: Filter by item kind.
            page_size: Optional page size for pagination.
            cursor: Optional cursor for pagination.
            include_deprecated: Whether to include deprecated items.

        Returns:
            A list of Item objects matching the search criteria.
            If pagination is used, returns a PagedList.
        """
        pagination = None
        if page_size is not None or cursor is not None:
            pagination = PaginationRequest(page_size=page_size or 100, cursor=cursor or "")

        req = ItemSearchRequest(
            context_filter=context_filter,
            item_name_filter=item_name_filter,
            kind_filter=kind_filter,
            pagination=pagination,
            include_deprecated=include_deprecated
        )
        resp = self.stub.ItemSearch(req)
        items = [Item(p, self) for p in resp.items]

        if resp.HasField("pagination"):
            return PagedList(
                items,
                next_cursor=resp.pagination.next_cursor,
                total_count=resp.pagination.total_count
            )
        return items

    def update_item_metadata(self, kref: Kref, metadata: Dict[str, str]) -> Item:
        """Update metadata for an item.

        Args:
            kref: The kref of the item.
            metadata: The metadata to update.

        Returns:
            The updated Item object.
        """
        req = UpdateMetadataRequest(kref=kref.to_pb(), metadata=metadata)
        resp = self.stub.UpdateItemMetadata(req)
        return Item(resp, self)

    def create_revision(self, item_kref: Kref, metadata: Optional[Dict[str, str]] = None, number: int = 0) -> Revision:
        """Create a new revision for an item.

        Args:
            item_kref: The kref of the item.
            metadata: Optional metadata for the revision.
            number: Specific revision number to use (0 for auto-increment).

        Returns:
            The created Revision object.
        """
        req = CreateRevisionRequest(item_kref=item_kref.to_pb(), metadata=metadata or {}, number=number)
        resp = self.stub.CreateRevision(req)
        return Revision(resp, self)

    def get_revision(self, kref_uri: str) -> Revision:
        """Get a revision by its kref URI, with optional tag/time resolution.

        Args:
            kref_uri: The kref URI of the revision. Can include ?t=tag or ?time=timestamp
                     for tag/time resolution.

        Returns:
            The Revision object.
        """
        # Parse kref_uri for tag/time parameters
        base_kref = kref_uri
        tag = None
        time = None
        
        if '?' in kref_uri:
            base_kref, params = kref_uri.split('?', 1)
            for param in params.split('&'):
                if param.startswith('t=') or param.startswith('tag='):
                    tag = param.split('=')[1]
                elif param.startswith('time='):
                    time = param.split('=')[1]
                    # Validate time format (YYYYMMDDHHMM)
                    import re
                    if not re.match(r"^\d{12}$", time):
                        raise ValueError("time must be in YYYYMMDDHHMM format")
        
        if tag is not None or time is not None:
            # Use ResolveKref to find the specific revision
            # We pass the base_kref (Item Kref) and the constraints
            req = ResolveKrefRequest(kref=base_kref, tag=tag, time=time)
            try:
                resp = self.stub.ResolveKref(req)
                return Revision(resp, self)
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    # Re-raise as NOT_FOUND
                    context = grpc.RpcError()
                    context.code = lambda: grpc.StatusCode.NOT_FOUND
                    context.details = lambda: "Revision not found"
                    raise context
                raise
        else:
            req = KrefRequest(kref=kumiho_pb2.Kref(uri=kref_uri))
        
        resp = self.stub.GetRevision(req)
        return Revision(resp, self)

    def get_item_from_revision(self, revision_kref: str) -> Item:
        """Get the item that contains a specific revision.

        Args:
            revision_kref: The kref URI of the revision.

        Returns:
            The Item object that contains the revision.
        """
        # First get the revision to find its item relationship
        revision = self.get_revision(revision_kref)
        # Parse the item_kref to extract parent_path, item_name, and kind
        item_path = revision.item_kref.get_path()  # e.g., "space/item.kind"
        if "/" not in item_path:
            raise ValueError(f"Invalid item kref format: {revision.item_kref}")
        
        parent_path, item_name_kind = item_path.split("/", 1)
        parent_path = f"/{parent_path}"  # Add leading slash
        if "." not in item_name_kind:
            raise ValueError(f"Invalid item name.kind format: {item_name_kind}")
        
        item_name, kind = item_name_kind.split(".", 1)
        
        return self.get_item(parent_path, item_name, kind)

    def get_revisions(self, item_kref: Kref) -> List[Revision]:
        """Get all revisions of an item.

        Args:
            item_kref: The kref of the item.

        Returns:
            A list of Revision objects for the item.
        """
        req = GetRevisionsRequest(item_kref=item_kref.to_pb())
        resp = self.stub.GetRevisions(req)
        return [Revision(v, self) for v in resp.revisions]

    def get_latest_revision(self, item_kref: Kref) -> Optional[Revision]:
        """Get the latest revision of an item.

        Args:
            item_kref: The kref of the item.

        Returns:
            The latest Revision object, or None if no revisions exist.
        """
        req = ResolveKrefRequest(kref=item_kref.uri)
        try:
            resp = self.stub.ResolveKref(req)
            return Revision(resp, self)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise

    def delete_revision(self, kref: Kref, force: bool) -> None:
        """Delete a revision.

        Args:
            kref: The kref of the revision to delete.
            force: Whether to force deletion.
        """
        req = DeleteRevisionRequest(kref=kref.to_pb(), force=force)
        self.stub.DeleteRevision(req)

    def delete_space(self, path: str, force: bool) -> None:
        """Delete a space.

        Args:
            path: The path of the space to delete.
            force: Whether to force deletion.
        """
        req = DeleteSpaceRequest(path=path, force=force)
        self.stub.DeleteSpace(req)

    def delete_item(self, kref: Kref, force: bool) -> None:
        """Delete an item.

        Args:
            kref: The kref of the item to delete.
            force: Whether to force deletion.
        """
        req = DeleteItemRequest(kref=kref.to_pb(), force=force)
        self.stub.DeleteItem(req)

    def update_revision_metadata(self, kref: Kref, metadata: Dict[str, str]) -> Revision:
        """Update metadata for a revision.

        Args:
            kref: The kref of the revision.
            metadata: The metadata to update.

        Returns:
            The updated Revision object.
        """
        req = UpdateMetadataRequest(kref=kref.to_pb(), metadata=metadata)
        resp = self.stub.UpdateRevisionMetadata(req)
        return Revision(resp, self)

    def peek_next_revision(self, item_kref: Kref) -> int:
        """Get the next revision number that would be assigned to an item.

        Args:
            item_kref: The kref of the item.

        Returns:
            The next revision number.
        """
        req = PeekNextRevisionRequest(item_kref=item_kref.to_pb())
        resp = self.stub.PeekNextRevision(req)
        return resp.number

    # Tagging methods
    def tag_revision(self, kref: Kref, tag: str) -> None:
        """Apply a tag to a revision.

        Args:
            kref: The kref of the revision.
            tag: The tag to apply.
        """
        req = TagRevisionRequest(kref=kref.to_pb(), tag=tag)
        self.stub.TagRevision(req)

    def untag_revision(self, kref: Kref, tag: str) -> None:
        """Remove a tag from a revision.

        Args:
            kref: The kref of the revision.
            tag: The tag to remove.
        """
        req = UnTagRevisionRequest(kref=kref.to_pb(), tag=tag)
        self.stub.UnTagRevision(req)

    def has_tag(self, kref: Kref, tag: str) -> bool:
        """Check if a revision has a specific tag.

        Args:
            kref: The kref of the revision.
            tag: The tag to check for.

        Returns:
            True if the revision has the tag, False otherwise.
        """
        req = HasTagRequest(kref=kref.to_pb(), tag=tag)
        resp = self.stub.HasTag(req)
        return resp.has_tag

    def was_tagged(self, kref: Kref, tag: str) -> bool:
        """Check if a revision was ever tagged with a specific tag.

        Args:
            kref: The kref of the revision.
            tag: The tag to check for.

        Returns:
            True if the revision was ever tagged with the given tag.
        """
        req = WasTaggedRequest(kref=kref.to_pb(), tag=tag)
        resp = self.stub.WasTagged(req)
        return resp.was_tagged

    def set_default_artifact(self, revision_kref: Kref, artifact_name: str) -> None:
        """Set the default artifact for a revision.

        Args:
            revision_kref: The kref of the revision.
            artifact_name: The name of the artifact to set as default.
        """
        req = SetDefaultArtifactRequest(revision_kref=revision_kref.to_pb(), artifact_name=artifact_name)
        self.stub.SetDefaultArtifact(req)

    # Artifact methods
    def create_artifact(
        self,
        revision_kref: Kref,
        name: str,
        location: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Artifact:
        """Create a new artifact for a revision.

        Args:
            revision_kref: The kref of the parent revision.
            name: The name of the artifact.
            location: The storage location of the artifact.
            metadata: Optional key-value metadata for the artifact.

        Returns:
            The created Artifact object.
        """
        req = CreateArtifactRequest(
            revision_kref=revision_kref.to_pb(),
            name=name,
            location=location,
            metadata=metadata or {},
        )
        resp = self.stub.CreateArtifact(req)
        return Artifact(resp, self)

    def get_artifact(self, revision_kref: Kref, name: str) -> Artifact:
        """Get an artifact by revision kref and name.

        Args:
            revision_kref: The kref of the parent revision.
            name: The name of the artifact.

        Returns:
            The Artifact object.
        """
        req = GetArtifactRequest(revision_kref=revision_kref.to_pb(), name=name)
        resp = self.stub.GetArtifact(req)
        return Artifact(resp, self)

    def get_artifact_by_kref(self, kref_uri: str) -> Artifact:
        """Get an artifact by its kref URI.

        Args:
            kref_uri: The kref URI of the artifact (e.g., "kref://space/item.kind?r=1&a=artifact_name").

        Returns:
            The Artifact object.

        Raises:
            ValueError: If the kref URI does not contain an artifact name.
        """
        kref = Kref(kref_uri)
        artifact_name = kref.get_artifact_name()
        if not artifact_name:
            raise ValueError(f"Invalid artifact kref format: {kref_uri} (missing &a=artifact_name)")
        
        # Build the revision kref by removing the artifact part
        revision_kref_uri = kref_uri.split("&a=")[0]
        revision_kref = Kref(revision_kref_uri)
        
        return self.get_artifact(revision_kref, artifact_name)

    def get_artifacts(self, revision_kref: Kref) -> List[Artifact]:
        """Get all artifacts for a revision.

        Args:
            revision_kref: The kref of the revision.

        Returns:
            A list of Artifact objects.
        """
        req = GetArtifactsRequest(revision_kref=revision_kref.to_pb())
        resp = self.stub.GetArtifacts(req)
        return [Artifact(r, self) for r in resp.artifacts]

    def get_artifacts_by_location(self, location: str) -> List[Artifact]:
        """Get all artifacts at a specific location.

        Args:
            location: The location to search for artifacts.

        Returns:
            A list of Artifact objects at the location.
        """
        req = GetArtifactsByLocationRequest(location=location)
        resp = self.stub.GetArtifactsByLocation(req)
        return [Artifact(r, self) for r in resp.artifacts]

    def delete_artifact(self, kref: Kref, force: bool) -> None:
        """Delete an artifact.

        Args:
            kref: The kref of the artifact to delete.
            force: Whether to force deletion.
        """
        req = DeleteArtifactRequest(kref=kref.to_pb(), force=force)
        self.stub.DeleteArtifact(req)

    def set_deprecated(self, kref: Kref, deprecated: bool) -> None:
        """Set the deprecated status of a node (Item, Revision, Artifact).

        Args:
            kref: The kref of the node.
            deprecated: True to deprecate, False to un-deprecate.
        """
        req = SetDeprecatedRequest(kref=kref.to_pb(), deprecated=deprecated)
        self.stub.SetDeprecated(req)

    def update_artifact_metadata(self, kref: Kref, metadata: Dict[str, str]) -> Artifact:
        """Update metadata for an artifact.

        Args:
            kref: The kref of the artifact.
            metadata: The metadata to update.

        Returns:
            The updated Artifact object.
        """
        req = UpdateMetadataRequest(kref=kref.to_pb(), metadata=metadata)
        resp = self.stub.UpdateArtifactMetadata(req)
        return Artifact(resp, self)

    def get_tenant_usage(self) -> Dict[str, Any]:
        """Get the current tenant's usage and limits.

        Returns:
            A dictionary containing node_count, node_limit, and tenant_id.
        """
        req = GetTenantUsageRequest()
        resp = self.stub.GetTenantUsage(req)
        return MessageToDict(resp, preserving_proto_field_name=True, always_print_fields_with_no_presence=True)

    def resolve(self, kref: str) -> Optional[str]:
        """
        Resolves a Kref to a file location using the server-side ResolveLocation RPC.
        
        Args:
            kref: The Kref URI to resolve. Can include query parameters like ?r=, ?t=, ?time=.
            
        Returns:
            The resolved file location string, or None if resolution fails.
        """
        try:
            # Parse tag/time from kref if present to pass explicitly
            tag = None
            time = None
            
            if '?' in kref:
                _, params = kref.split('?', 1)
                for param in params.split('&'):
                    if param.startswith('t=') or param.startswith('tag='):
                        tag = param.split('=')[1]
                    elif param.startswith('time='):
                        time = param.split('=')[1]

            req = ResolveLocationRequest(kref=kref, tag=tag, time=time)
            resp = self.stub.ResolveLocation(req)
            return resp.location
        except grpc.RpcError:
            return None
        except Exception:
            return None

    # Attribute methods (granular metadata operations)
    def set_attribute(self, kref: Kref, key: str, value: str) -> bool:
        """Set a single metadata attribute on any entity.

        This allows granular updates to metadata without replacing the entire
        metadata map. The attribute key cannot be a reserved system field.

        Args:
            kref: The kref of the entity (Revision, Item, Artifact, or Space).
            key: The attribute key to set.
            value: The attribute value.

        Returns:
            True if the attribute was set successfully.

        Raises:
            grpc.RpcError: If the entity is not found or the key is reserved.

        Example:
            >>> client.set_attribute(revision.kref, "render_engine", "cycles")
            True
        """
        req = SetAttributeRequest(kref=kref.to_pb(), key=key, value=value)
        resp = self.stub.SetAttribute(req)
        return resp.success

    def get_attribute(self, kref: Kref, key: str) -> Optional[str]:
        """Get a single metadata attribute from any entity.

        Args:
            kref: The kref of the entity (Revision, Item, Artifact, or Space).
            key: The attribute key to retrieve.

        Returns:
            The attribute value if it exists, None otherwise.

        Raises:
            grpc.RpcError: If the entity is not found.

        Example:
            >>> client.get_attribute(revision.kref, "render_engine")
            "cycles"
            >>> client.get_attribute(revision.kref, "nonexistent")
            None
        """
        req = GetAttributeRequest(kref=kref.to_pb(), key=key)
        resp = self.stub.GetAttribute(req)
        return resp.value if resp.exists else None

    def delete_attribute(self, kref: Kref, key: str) -> bool:
        """Delete a single metadata attribute from any entity.

        Args:
            kref: The kref of the entity (Revision, Item, Artifact, or Space).
            key: The attribute key to delete.

        Returns:
            True if the attribute was deleted successfully.

        Raises:
            grpc.RpcError: If the entity is not found or the key is reserved.

        Example:
            >>> client.delete_attribute(revision.kref, "deprecated_field")
            True
        """
        req = DeleteAttributeRequest(kref=kref.to_pb(), key=key)
        resp = self.stub.DeleteAttribute(req)
        return resp.success

    # Edge methods
    def create_edge(
        self,
        source_revision: Revision,
        target_revision: Revision,
        edge_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Edge:
        """Create an edge between two revisions.

        Args:
            source_revision: The source revision of the edge.
            target_revision: The target revision of the edge.
            edge_type: The type of relationship (e.g., kumiho.EdgeType.DEPENDS_ON).
                       See kumiho.EdgeType for standard types.
                       Must be UPPERCASE with letters, digits, underscores only.
            metadata: Optional metadata for the edge.

        Returns:
            The created Edge object.
            
        Raises:
            EdgeTypeValidationError: If edge_type is invalid.
        """
        from .edge import validate_edge_type
        validate_edge_type(edge_type)
        
        req = CreateEdgeRequest(
            source_revision_kref=source_revision.kref.to_pb(),
            target_revision_kref=target_revision.kref.to_pb(),
            edge_type=edge_type,
            metadata=metadata or {}
        )
        self.stub.CreateEdge(req)
        # Construct Edge object client-side since RPC returns only status
        pb_edge = PbEdge(
            source_kref=source_revision.kref.to_pb(),
            target_kref=target_revision.kref.to_pb(),
            edge_type=edge_type,
            metadata=metadata or {},
        )
        return Edge(pb_edge, self)

    def get_edges(self, kref: Kref, edge_type_filter: str = "", direction: int = 0) -> List[Edge]:
        """Get edges associated with a kref.

        Args:
            kref: The kref to get edges for.
            edge_type_filter: Optional filter for edge types.
            direction: The direction of edges to retrieve (0=OUTGOING, 1=INCOMING, 2=BOTH).
                       See kumiho.EdgeDirection.

        Returns:
            A list of Edge objects.
        """
        req = GetEdgesRequest(kref=kref.to_pb(), edge_type_filter=edge_type_filter, direction=direction)
        resp = self.stub.GetEdges(req)
        return [Edge(pb, self) for pb in resp.edges]

    def delete_edge(self, source_kref: Kref, target_kref: Kref, edge_type: str) -> None:
        """Delete an edge between revisions.

        Args:
            source_kref: The source revision kref.
            target_kref: The target revision kref.
            edge_type: The type of edge to delete.
            
        Raises:
            EdgeTypeValidationError: If edge_type is invalid.
        """
        from .edge import validate_edge_type
        validate_edge_type(edge_type)
        
        req = DeleteEdgeRequest(
            source_kref=source_kref.to_pb(),
            target_kref=target_kref.to_pb(),
            edge_type=edge_type
        )
        self.stub.DeleteEdge(req)

    # Graph Traversal Methods

    def traverse_edges(
        self,
        origin_kref: Kref,
        direction: int = 0,
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        limit: int = 100,
        include_path: bool = False
    ) -> 'TraversalResult':
        """Traverse edges transitively from an origin revision.

        Args:
            origin_kref: The starting revision kref.
            direction: Traversal direction (0=OUTGOING, 1=INCOMING, 2=BOTH).
            edge_type_filter: Filter by edge types (empty = all).
            max_depth: Maximum traversal depth (default: 10, max: 20).
            limit: Maximum results to return (default: 100, max: 1000).
            include_path: Whether to include full path information.

        Returns:
            TraversalResult containing discovered revisions and paths.
        """
        from .edge import TraversalResult, RevisionPath, PathStep
        
        req = TraverseEdgesRequest(
            origin_kref=origin_kref.to_pb(),
            direction=direction,
            edge_type_filter=edge_type_filter or [],
            max_depth=max_depth,
            limit=limit,
            include_path=include_path
        )
        resp = self.stub.TraverseEdges(req)
        
        revision_krefs = [Kref(k.uri) for k in resp.revision_krefs]
        paths = []
        for p in resp.paths:
            steps = [PathStep(
                revision_kref=Kref(s.revision_kref.uri),
                edge_type=s.edge_type,
                depth=s.depth
            ) for s in p.steps]
            paths.append(RevisionPath(steps=steps, total_depth=p.total_depth))
        
        edges = [Edge(pb, self) for pb in resp.edges]
        
        return TraversalResult(
            revision_krefs=revision_krefs,
            paths=paths,
            edges=edges,
            total_count=resp.total_count,
            truncated=resp.truncated,
            client=self
        )

    def find_shortest_path(
        self,
        source_kref: Kref,
        target_kref: Kref,
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        all_shortest: bool = False
    ) -> 'ShortestPathResult':
        """Find the shortest path between two revisions.

        Args:
            source_kref: The source revision kref.
            target_kref: The target revision kref.
            edge_type_filter: Filter by edge types (empty = all).
            max_depth: Maximum path length to search (default: 10).
            all_shortest: Return all shortest paths, not just one.

        Returns:
            ShortestPathResult containing path(s) if found.
        """
        from .edge import RevisionPath, PathStep
        
        req = ShortestPathRequest(
            source_kref=source_kref.to_pb(),
            target_kref=target_kref.to_pb(),
            edge_type_filter=edge_type_filter or [],
            max_depth=max_depth,
            all_shortest=all_shortest
        )
        resp = self.stub.FindShortestPath(req)
        
        paths = []
        for p in resp.paths:
            steps = [PathStep(
                revision_kref=Kref(s.revision_kref.uri),
                edge_type=s.edge_type,
                depth=s.depth
            ) for s in p.steps]
            paths.append(RevisionPath(steps=steps, total_depth=p.total_depth))
        
        return ShortestPathResult(
            paths=paths,
            path_exists=resp.path_exists,
            path_length=resp.path_length
        )

    def analyze_impact(
        self,
        revision_kref: Kref,
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        limit: int = 100
    ) -> List['ImpactedRevision']:
        """Analyze what would be impacted by changes to a revision.

        Finds all revisions that directly or indirectly depend on the
        given revision.

        Args:
            revision_kref: The revision to analyze impact for.
            edge_type_filter: Filter by edge types (default: DEPENDS_ON).
            max_depth: Maximum traversal depth (default: 10).
            limit: Maximum results (default: 100).

        Returns:
            List of ImpactedRevision objects.
        """
        from .edge import ImpactedRevision
        
        req = ImpactAnalysisRequest(
            revision_kref=revision_kref.to_pb(),
            edge_type_filter=edge_type_filter or [],
            max_depth=max_depth,
            limit=limit
        )
        resp = self.stub.AnalyzeImpact(req)
        
        return [
            ImpactedRevision(
                revision_kref=Kref(iv.revision_kref.uri),
                item_kref=Kref(iv.item_kref.uri) if iv.item_kref.uri else None,
                impact_depth=iv.impact_depth,
                impact_path_types=list(iv.impact_path_types)
            )
            for iv in resp.impacted_revisions
        ]

    # Bundle Methods

    def create_bundle(
        self,
        parent_path: str,
        bundle_name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> "Bundle":
        """Create a new bundle item.

        Bundles are special items that aggregate other items.
        The ``bundle`` kind is reserved and can only be created
        through this method (not via :meth:`create_item`).

        Note:
            This is a low-level client method. Prefer using
            :meth:`~kumiho.project.Project.create_bundle` or
            :meth:`~kumiho.space.Space.create_bundle` for a higher-level API.

        Args:
            parent_path: The path to the parent space (e.g., ``/project/space``).
            bundle_name: The name of the bundle. Must be unique within
                the parent space.
            metadata: Optional key-value metadata for the bundle.

        Returns:
            Bundle: The created Bundle object with ``kind='bundle'``.

        Raises:
            grpc.RpcError: If the bundle name is already taken or connection fails.
        """
        from .bundle import Bundle
        req = CreateBundleRequest(
            parent_path=parent_path,
            bundle_name=bundle_name,
            metadata=metadata or {}
        )
        resp = self.stub.CreateBundle(req)
        return Bundle(resp, self)

    def add_bundle_member(
        self,
        bundle_kref: Kref,
        member_item_kref: Kref,
        metadata: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, Optional[Revision]]:
        """Add an item to a bundle.

        Creates a new revision of the bundle to track the change with
        full audit trail.

        Note:
            This is a low-level client method. Prefer using
            :meth:`~kumiho.bundle.Bundle.add_member` for a higher-level API.

        Args:
            bundle_kref: The kref pointing to the bundle item.
            member_item_kref: The kref pointing to the item to add.
            metadata: Optional key-value metadata to store in the revision.

        Returns:
            Tuple[bool, str, Optional[Revision]]: A tuple containing:
                - success: Whether the operation succeeded.
                - message: Status message (e.g., "Added" or error details).
                - new_revision: The new bundle revision, or None on failure.

        Raises:
            grpc.RpcError: If the bundle or member item is not found.
        """
        req = AddBundleMemberRequest(
            bundle_kref=bundle_kref.to_pb(),
            member_item_kref=member_item_kref.to_pb(),
            metadata=metadata or {}
        )
        resp = self.stub.AddBundleMember(req)
        new_revision = Revision(resp.new_revision, self) if resp.new_revision else None
        return resp.success, resp.message, new_revision

    def remove_bundle_member(
        self,
        bundle_kref: Kref,
        member_item_kref: Kref,
        metadata: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, Optional[Revision]]:
        """Remove an item from a bundle.

        Creates a new revision of the bundle to track the change with
        full audit trail.

        Note:
            This is a low-level client method. Prefer using
            :meth:`~kumiho.bundle.Bundle.remove_member` for a higher-level API.

        Args:
            bundle_kref: The kref pointing to the bundle item.
            member_item_kref: The kref pointing to the item to remove.
            metadata: Optional key-value metadata to store in the revision.

        Returns:
            Tuple[bool, str, Optional[Revision]]: A tuple containing:
                - success: Whether the operation succeeded.
                - message: Status message (e.g., "Removed" or error details).
                - new_revision: The new bundle revision, or None on failure.

        Raises:
            grpc.RpcError: If the bundle or member item is not found.
        """
        req = RemoveBundleMemberRequest(
            bundle_kref=bundle_kref.to_pb(),
            member_item_kref=member_item_kref.to_pb(),
            metadata=metadata or {}
        )
        resp = self.stub.RemoveBundleMember(req)
        new_revision = Revision(resp.new_revision, self) if resp.new_revision else None
        return resp.success, resp.message, new_revision

    def get_bundle_members(
        self,
        bundle_kref: Kref,
        revision_number: Optional[int] = None
    ) -> Tuple[List['BundleMember'], int, int]:
        """Get all members of a bundle.

        Retrieves the list of items that belong to a bundle at
        a specific revision (or the latest revision if not specified).

        Note:
            This is a low-level client method. Prefer using
            :meth:`~kumiho.bundle.Bundle.get_members` for a higher-level API.

        Args:
            bundle_kref: The kref pointing to the bundle item.
            revision_number: Optional specific revision to query. If not provided,
                returns members from the latest revision.

        Returns:
            Tuple[List[BundleMember], int, int]: A tuple containing:
                - members: List of :class:`~kumiho.bundle.BundleMember` objects.
                - revision_number: The revision number queried.
                - total_count: Total number of members.

        Raises:
            grpc.RpcError: If the bundle is not found.
        """
        from .bundle import BundleMember
        
        req = GetBundleMembersRequest(
            bundle_kref=bundle_kref.to_pb(),
            revision_number=revision_number
        )
        resp = self.stub.GetBundleMembers(req)
        
        members = [
            BundleMember(
                item_kref=Kref(m.item_kref.uri),
                added_at=m.added_at,
                added_by=m.added_by,
                added_by_username=m.added_by_username,
                added_in_revision=m.added_in_revision
            )
            for m in resp.members
        ]
        return members, resp.revision_number, resp.total_count

    def get_bundle_history(
        self,
        bundle_kref: Kref
    ) -> List['BundleRevisionHistory']:
        """Get the history of changes to a bundle's membership.

        Returns a chronological list of membership changes (adds/removes)
        with full audit trail including author information and timestamps.

        Note:
            This is a low-level client method. Prefer using
            :meth:`~kumiho.bundle.Bundle.get_history` for a higher-level API.

        Args:
            bundle_kref: The kref pointing to the bundle item.

        Returns:
            List[BundleRevisionHistory]: List of
                :class:`~kumiho.bundle.BundleRevisionHistory` objects
                documenting each membership change.

        Raises:
            grpc.RpcError: If the bundle is not found.
        """
        from .bundle import BundleRevisionHistory
        
        req = GetBundleHistoryRequest(
            bundle_kref=bundle_kref.to_pb()
        )
        resp = self.stub.GetBundleHistory(req)
        
        return [
            BundleRevisionHistory(
                revision_number=h.revision_number,
                action=h.action,
                member_item_kref=Kref(h.member_item_kref.uri) if h.member_item_kref.uri else None,
                author=h.author,
                username=h.username,
                created_at=h.created_at,
                metadata=dict(h.metadata)
            )
            for h in resp.history
        ]

    # Event Streaming
    def event_stream(
        self,
        routing_key_filter: str = "",
        kref_filter: str = "",
        cursor: Optional[str] = None,
        consumer_group: Optional[str] = None,
        from_beginning: bool = False,
        timeout: Optional[float] = None,
    ) -> Iterator[Event]:
        """Subscribe to the event stream from the Kumiho server.

        Args:
            routing_key_filter: A filter for the events to receive.
                                Supports wildcards, e.g., "item.model.*"
            kref_filter: A filter for the kref URIs to receive events for.
                        Supports wildcards, e.g., "kref://projectA/**/*.model"
            cursor: Resume from a previous cursor position (Creator tier+).
                    Pass the cursor from the last received event to continue
                    from that point after reconnection.
            consumer_group: Consumer group name for load-balanced delivery
                           (Enterprise tier only). Multiple consumers in the
                           same group each receive different events.
            from_beginning: Start from earliest available events instead of
                           live-only (Creator tier+, subject to retention).
            timeout: Optional timeout in seconds for the gRPC stream.
                    If reached, the iterator will raise grpc.RpcError with
                    StatusCode.DEADLINE_EXCEEDED.

        Yields:
            Event objects representing changes in the database. Each event
            includes a ``cursor`` field that can be saved for resumption.

        Example::

            last_cursor = load_cursor_from_disk()  # Load previous position
            try:
                for event in client.event_stream(
                    routing_key_filter="revision.*",
                    cursor=last_cursor,
                    timeout=30
                ):
                    process_event(event)
                    save_cursor_to_disk(event.cursor)  # Save for next run
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    print("Stream timed out")
                else:
                    raise
        """
        req = EventStreamRequest(
            routing_key_filter=routing_key_filter,
            kref_filter=kref_filter,
        )
        if cursor:
            req.cursor = cursor
        if consumer_group:
            req.consumer_group = consumer_group
        if from_beginning:
            req.from_beginning = True
        
        for pb_event in self.stub.EventStream(req, timeout=timeout):
            yield Event(pb_event)

    def get_event_capabilities(self) -> "EventCapabilities":
        """Get event streaming capabilities for the current tenant tier.

        Returns the capabilities available based on the authenticated tenant's
        subscription tier. Use this to determine which features are available
        before using cursor-based resume or consumer groups.

        Returns:
            EventCapabilities with the following attributes:
                - supports_replay: Can replay past events
                - supports_cursor: Can resume from cursor
                - supports_consumer_groups: Can use consumer groups (Enterprise)
                - max_retention_hours: Event retention period (-1 = unlimited)
                - max_buffer_size: Max events in buffer (-1 = unlimited)
                - tier: Tier name (free, creator, studio, enterprise)

        Example::

            caps = client.get_event_capabilities()
            if caps.supports_cursor:
                # Use cursor-based streaming
                last_cursor = load_saved_cursor()
                for event in client.event_stream(cursor=last_cursor):
                    ...
            else:
                # Free tier - no cursor support
                for event in client.event_stream():
                    ...
        """
        from .event import EventCapabilities
        req = GetEventCapabilitiesRequest()
        resp = self.stub.GetEventCapabilities(req)
        return EventCapabilities(
            supports_replay=resp.supports_replay,
            supports_cursor=resp.supports_cursor,
            supports_consumer_groups=resp.supports_consumer_groups,
            max_retention_hours=resp.max_retention_hours,
            max_buffer_size=resp.max_buffer_size,
            tier=resp.tier,
        )


class _ClientCallDetails(grpc.ClientCallDetails):
    """Mutable wrapper that lets us override metadata on outbound RPCs."""

    def __init__(
        self,
        method: str,
        timeout: Optional[float],
        metadata: Optional[Sequence[Tuple[str, str]]],
        credentials: Optional[grpc.CallCredentials],
        wait_for_ready: Optional[bool],
        compression: Optional[grpc.Compression],
    ) -> None:
        self.method = method
        self.timeout = timeout
        self.metadata: Optional[Tuple[Tuple[str, Union[str, bytes]], ...]] = (
            tuple((k, v) for k, v in metadata) if metadata is not None else None
        )
        self.credentials = credentials
        self.wait_for_ready = wait_for_ready
        self.compression = compression


def _augment_call_details(
    client_call_details: grpc.ClientCallDetails,
    metadata: Sequence[Tuple[str, str]],
) -> _ClientCallDetails:
    existing: List[Tuple[str, str]] = []
    for k, v in (client_call_details.metadata or []):
        if isinstance(v, str):
            existing.append((k, v))
        elif isinstance(v, bytes):
            existing.append((k, v.decode("utf-8")))
        else:
            existing.append((k, bytes(v).decode("utf-8")))
    existing.extend(metadata)
    return _ClientCallDetails(
        method=client_call_details.method,
        timeout=client_call_details.timeout,
        metadata=existing,
        credentials=client_call_details.credentials,
        wait_for_ready=getattr(client_call_details, "wait_for_ready", None),
        compression=getattr(client_call_details, "compression", None),
    )


class _MetadataInjector(
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
    grpc.StreamUnaryClientInterceptor,
    grpc.StreamStreamClientInterceptor,
):
    """Client interceptor that injects static metadata such as auth tokens."""

    def __init__(self, metadata: Sequence[Tuple[str, str]]) -> None:
        self._metadata = tuple(metadata)

    def intercept_unary_unary(self, continuation, client_call_details, request):
        _LOGGER.debug(f"Injecting metadata (keys: {[k for k, v in self._metadata]})")
        updated = _augment_call_details(client_call_details, self._metadata)
        return continuation(updated, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        updated = _augment_call_details(client_call_details, self._metadata)
        return continuation(updated, request)

    def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        updated = _augment_call_details(client_call_details, self._metadata)
        return continuation(updated, request_iterator)

    def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        updated = _augment_call_details(client_call_details, self._metadata)
        return continuation(updated, request_iterator)


class _CorrelationIdInterceptor(
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
    grpc.StreamUnaryClientInterceptor,
    grpc.StreamStreamClientInterceptor,
):
    """Client interceptor that generates a unique correlation ID per request.
    
    This enables end-to-end tracing across Control Plane and Data Plane.
    The correlation ID is sent as the 'x-correlation-id' header.
    """

    @staticmethod
    def _generate_correlation_id() -> str:
        import uuid
        return f"kumiho-{uuid.uuid4().hex[:16]}"

    def _add_correlation_id(self, client_call_details):
        correlation_id = self._generate_correlation_id()
        _LOGGER.debug(f"Adding correlation ID: {correlation_id}")
        return _augment_call_details(
            client_call_details, 
            [("x-correlation-id", correlation_id)]
        )

    def intercept_unary_unary(self, continuation, client_call_details, request):
        updated = self._add_correlation_id(client_call_details)
        return continuation(updated, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        updated = self._add_correlation_id(client_call_details)
        return continuation(updated, request)

    def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        updated = self._add_correlation_id(client_call_details)
        return continuation(updated, request_iterator)

    def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        updated = self._add_correlation_id(client_call_details)
        return continuation(updated, request_iterator)


class _AutoLoginInterceptor(
    grpc.UnaryUnaryClientInterceptor,
    grpc.UnaryStreamClientInterceptor,
):
    """Client interceptor that automatically prompts for login on auth failures."""

    def intercept_unary_unary(self, continuation, client_call_details, request):
        response = continuation(client_call_details, request)
        
        # Check if this is an auth error
        try:
            # Force the response to be evaluated
            if hasattr(response, 'code'):
                code = response.code()
                if code in (grpc.StatusCode.UNAUTHENTICATED, grpc.StatusCode.PERMISSION_DENIED):
                    _LOGGER.info("Authentication error detected, prompting for login...")
                    try:
                        from . import auth_cli
                        new_token, _ = auth_cli.ensure_token(interactive=True)
                        
                        # Update the authorization header with the new token
                        existing_metadata: List[Tuple[str, str]] = []
                        for k, v in (client_call_details.metadata or []):
                            if isinstance(v, str):
                                existing_metadata.append((k, v))
                            elif isinstance(v, bytes):
                                existing_metadata.append((k, v.decode("utf-8")))
                            else:
                                # memoryview or other buffer-like object
                                existing_metadata.append((k, bytes(v).decode("utf-8")))
                        # Remove old authorization header
                        existing_metadata = [(k, v) for k, v in existing_metadata if k.lower() != "authorization"]
                        # Add new token
                        existing_metadata.append(("authorization", f"Bearer {new_token}"))
                        
                        updated_details = _ClientCallDetails(
                            method=client_call_details.method,
                            timeout=client_call_details.timeout,
                            metadata=existing_metadata,
                            credentials=client_call_details.credentials,
                            wait_for_ready=getattr(client_call_details, "wait_for_ready", None),
                            compression=getattr(client_call_details, "compression", None),
                        )
                        
                        # Retry the RPC with the new token
                        _LOGGER.debug("Retrying RPC with refreshed credentials")
                        return continuation(updated_details, request)
                    except Exception as e:
                        _LOGGER.error(f"Auto-login failed: {e}")
                        return response
        except Exception:
            # If we can't check the error, just return the original response
            pass
        
        return response

    def intercept_unary_stream(self, continuation, client_call_details, request):
        # For streaming responses, we can't easily retry, so just pass through
        # The first error will be caught and user will be prompted to re-run
        return continuation(client_call_details, request)

