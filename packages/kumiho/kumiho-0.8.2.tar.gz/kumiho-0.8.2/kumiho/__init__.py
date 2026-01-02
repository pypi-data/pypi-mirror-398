"""Kumiho Python Client Library.

Kumiho is a graph-native creative and AI asset management system that tracks
revisions, relationships, and lineage without uploading original files to the
cloud. This SDK provides a Pythonic interface to the Kumiho gRPC backend.

Getting Started:
    The simplest way to use Kumiho is with the top-level functions that
    use a default client configured from your environment::

        import kumiho

        # Authenticate and configure (run once per session)
        kumiho.auto_configure_from_discovery() # This can be avoided if env var KUMIHO_AUTO_CONFIGURE=1 is set

        # Create a project
        project = kumiho.create_project("my-vfx-project", "VFX assets for commercial")

        # Create spaces and items
        space = project.create_space("characters")
        item = space.create_item("hero", "model")

        # Create revisions and artifacts
        revision = item.create_revision()
        artifact = revision.create_artifact("main", "/path/to/hero.fbx")

    For more control, you can create a client manually::

        import kumiho

        client = kumiho.connect(
            endpoint="localhost:50051",
            token="your-auth-token"
        )

        with kumiho.use_client(client):
            projects = kumiho.get_projects()

Key Concepts:
    - **Project**: Top-level container for all assets and spaces.
    - **Space**: Hierarchical folder structure within a project.
    - **Item**: A versioned asset (model, texture, workflow, etc.).
    - **Revision**: A specific iteration of an item with artifacts.
    - **Artifact**: A file reference (path/URI) within a revision.
    - **Edge**: A relationship between revisions (dependencies, references).
    - **Kref**: A URI-based unique identifier for any Kumiho object.

Authentication:
    Kumiho uses Firebase authentication. Run the CLI to log in::

        kumiho-auth login

    This caches credentials in ``~/.kumiho/``. Then use
    :func:`auto_configure_from_discovery` to bootstrap the client.

Environment Variables:
    - ``KUMIHO_AUTO_CONFIGURE``: Set to "1" to auto-configure on import.
    - ``KUMIHO_AUTH_TOKEN``: Override the authentication token.
    - ``KUMIHO_CONTROL_PLANE_URL``: Override the control plane URL.
    - ``KUMIHO_ENDPOINT``: Override the gRPC endpoint.

Example:
    Complete workflow example::

        import kumiho

        # Configure client from cached credentials
        kumiho.auto_configure_from_discovery()

        # Get or create project
        project = kumiho.get_project("my-project")
        if not project:
            project = kumiho.create_project("my-project", "My VFX project")

        # Navigate to asset space
        assets = project.get_space("assets") or project.create_space("assets")

        # Create a new model item
        model = assets.create_item("character", "model")

        # Create first revision
        v1 = model.create_revision(metadata={"author": "artist1"})
        v1.create_artifact("mesh", "/projects/char/v1/mesh.fbx")
        v1.create_artifact("textures", "/projects/char/v1/textures.zip")
        v1.tag("approved")
        v1.tag("published") # published tag is reserved tag within Kumiho as revision with immutable semantics

        # Query by kref
        item = kumiho.get_item("kref://my-project/assets/character.model")
        revision = kumiho.get_revision("kref://my-project/assets/character.model?r=1")

        # Search across project
        models = kumiho.item_search(
            context_filter="my-project",
            kind_filter="model"
        )

Note:
    Kumiho follows a "BYO Storage" philosophy—files remain on your local
    or network storage. Kumiho only tracks paths, metadata, and relationships
    in its graph database.

See Also:
    - Kumiho documentation: https://docs.kumiho.cloud
    - GitHub: https://github.com/kumihoclouds/kumiho-python

Attributes:
    __version__ (str): The current version of the kumiho package.
    LATEST_TAG (str): Standard tag name for the latest revision.
    PUBLISHED_TAG (str): Standard tag name for published revisions.
"""

__version__ = "0.3.0"

import contextvars
from typing import Any, Dict, List, Optional, Iterator, Tuple

# Import the main classes to make them available at the package level.
from .base import KumihoObject, KumihoError
from .client import _Client
from .bundle import (
    Bundle,
    BundleMember,
    BundleRevisionHistory,
    ReservedKindError,
    RESERVED_KINDS,
)
from .event import Event, EventCapabilities
from .space import Space
from .kref import Kref, KrefValidationError, validate_kref, is_valid_kref
from .edge import (
    Edge,
    EdgeType,
    EdgeDirection,
    EdgeTypeValidationError,
    validate_edge_type,
    is_valid_edge_type,
    PathStep,
    RevisionPath,
    ImpactedRevision,
    TraversalResult,
    ShortestPathResult,
)
from .item import Item
from .project import Project
from .artifact import Artifact
from .proto.kumiho_pb2 import StatusResponse
from .revision import Revision
from .client import ProjectLimitError
from .discovery import client_from_discovery, DiscoveryRecord, DiscoveryCache, DEFAULT_CACHE_PATH, _DEFAULT_CACHE_KEY
from ._bootstrap import bootstrap_default_client

# Expose EdgeType constants for convenience
BELONGS_TO = EdgeType.BELONGS_TO
CREATED_FROM = EdgeType.CREATED_FROM

# Constants
LATEST_TAG = "latest"
"""str: Standard tag name indicating the latest revision of an item."""

PUBLISHED_TAG = "published"
"""str: Standard tag name indicating a published/released revision."""

REFERENCED = EdgeType.REFERENCED
DEPENDS_ON = EdgeType.DEPENDS_ON
DERIVED_FROM = EdgeType.DERIVED_FROM
CONTAINS = EdgeType.CONTAINS

# Expose EdgeDirection constants for convenience
OUTGOING = EdgeDirection.OUTGOING
INCOMING = EdgeDirection.INCOMING
BOTH = EdgeDirection.BOTH

# Instantiate a default client instance for convenience.
_default_client: Optional[_Client] = None
_AUTO_CONFIGURE_ENV = "KUMIHO_AUTO_CONFIGURE"

# Context variable for request-scoped client instances
_client_context_var: contextvars.ContextVar[Optional[_Client]] = contextvars.ContextVar("kumiho_client", default=None)


def get_client() -> _Client:
    """Get the current Kumiho client instance.

    Returns the context-local client if set via :class:`use_client`,
    otherwise returns the global default client (creating one if needed).

    Returns:
        _Client: The active client instance.

    Raises:
        RuntimeError: If no client is configured and auto-bootstrap fails.

    Example:
        >>> client = kumiho.get_client()
        >>> projects = client.get_projects()
    """
    # Check for context-local client first
    local_client = _client_context_var.get()
    if local_client is not None:
        return local_client
        
    # Fallback to global default
    global _default_client
    if _default_client is None:
        _default_client = bootstrap_default_client()
    return _default_client


def configure_default_client(client: _Client) -> _Client:
    """Set the global default client used by top-level helper functions.

    This function allows you to manually configure the default client
    that will be used by functions like :func:`create_project`,
    :func:`get_projects`, etc.

    Args:
        client: The client instance to set as the default.

    Returns:
        _Client: The same client instance (for chaining).

    Example:
        >>> client = kumiho.connect(endpoint="localhost:50051")
        >>> kumiho.configure_default_client(client)
        >>> # Now all top-level functions use this client
        >>> projects = kumiho.get_projects()
    """
    global _default_client
    _default_client = client
    return _default_client


class use_client:
    """Context manager to temporarily set the current client instance.

    This is useful for multi-tenant scenarios or when you need to
    use different clients for different operations within the same
    thread or async context.

    Args:
        client: The client to use within the context.

    Example:
        Using different clients for different tenants::

            import kumiho

            tenant_a_client = kumiho.connect(endpoint="tenant-a.kumiho.cloud:443")
            tenant_b_client = kumiho.connect(endpoint="tenant-b.kumiho.cloud:443")

            with kumiho.use_client(tenant_a_client):
                # All operations here use tenant_a_client
                projects_a = kumiho.get_projects()

            with kumiho.use_client(tenant_b_client):
                # All operations here use tenant_b_client
                projects_b = kumiho.get_projects()

    Note:
        Context-local clients take precedence over the global default.
        This works correctly with async code and concurrent requests.
    """
    
    def __init__(self, client: _Client):
        """Initialize the context manager.

        Args:
            client: The client to use within the context.
        """
        self.client = client
        self.token = None
        
    def __enter__(self):
        """Enter the context and set the client."""
        self.token = _client_context_var.set(self.client)
        return self.client
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore the previous client."""
        if self.token:
            _client_context_var.reset(self.token)


def auto_configure_from_discovery(
    *,
    tenant_hint: Optional[str] = None,
    force_refresh: bool = False,
    interactive: bool = False,
) -> _Client:
    """Configure the default client using cached credentials and discovery.

    This is the recommended way to bootstrap the Kumiho client. It uses
    credentials cached by ``kumiho-auth login`` and calls the control-plane
    discovery endpoint to resolve the correct regional server.

    Args:
        tenant_hint: Optional tenant slug or ID to use for discovery.
            If not provided, the user's default tenant is used.
        force_refresh: If True, bypass the discovery cache and fetch
            fresh routing information from the control plane.
        interactive: If True and no cached credentials exist, prompt
            for interactive login. Defaults to False for script safety.

    Returns:
        _Client: The configured client instance, also set as the default.

    Raises:
        RuntimeError: If no cached credentials exist and interactive
            mode is disabled.

    Example:
        Basic usage::

            import kumiho

            # First, run: kumiho-auth login
            # Then in your code:
            kumiho.auto_configure_from_discovery()

            # Now you can use all kumiho functions
            projects = kumiho.get_projects()

        With tenant hint for multi-tenant access::

            kumiho.auto_configure_from_discovery(tenant_hint="my-studio")

    See Also:
        :func:`connect`: For manual client configuration.
        :class:`use_client`: For temporary client switching.
    """

    from .auth_cli import ensure_token, TokenAcquisitionError  # Lazy import to avoid polluting module attrs
    from ._token_loader import load_bearer_token

    try:
        ensure_token(interactive=interactive)
    except TokenAcquisitionError as exc:
        raise RuntimeError(
            "No cached credentials found. Run 'kumiho-auth login' to "
            "populate ~/.kumiho before calling auto_configure_from_discovery()."
        ) from exc

    token = load_bearer_token()
    if not token:
        raise RuntimeError(
            "Cached credentials missing valid token. Re-run 'kumiho-auth login' "
            "or set KUMIHO_AUTH_TOKEN."
        )

    client = client_from_discovery(
        id_token=token,
        tenant_hint=tenant_hint,
        force_refresh=force_refresh,
    )
    return configure_default_client(client)


def _auto_configure_flag_enabled() -> bool:
    import os

    raw = os.getenv(_AUTO_CONFIGURE_ENV)
    if not raw:
        return False
    return raw.strip().lower() in {"1", "true", "yes"}


def _auto_configure_from_env_if_requested() -> None:
    if not _auto_configure_flag_enabled():
        return
    try:
        auto_configure_from_discovery()
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(
            "KUMIHO_AUTO_CONFIGURE is set, but automatic discovery bootstrap failed."
        ) from exc


# =============================================================================
# Tenant Info Functions
# =============================================================================


def get_tenant_info(tenant_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get information about the current tenant from the discovery cache.

    This retrieves tenant information that was cached during discovery,
    including the tenant ID, tenant name/slug, roles, and region info.

    Args:
        tenant_hint: Optional tenant slug or ID to look up. If not provided,
            looks up the default tenant (using "_default" cache key).

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing tenant info:
            - tenant_id: The unique tenant identifier
            - tenant_name: The tenant slug/name (human-readable identifier)
            - roles: List of roles the user has in this tenant
            - region: Region routing information
        Returns None if no cached info is available.

    Example:
        >>> info = kumiho.get_tenant_info()
        >>> if info:
        ...     print(f"Tenant: {info['tenant_name']}")
        ...     print(f"Roles: {info['roles']}")
        Tenant: kumihoclouds
        Roles: ['owner', 'admin']

    Note:
        This requires that discovery has been performed (either via
        ``auto_configure_from_discovery()`` or ``KUMIHO_AUTO_CONFIGURE=1``).
        If using direct connection without discovery, this will return None.
    """
    cache = DiscoveryCache(DEFAULT_CACHE_PATH)
    cache_key = tenant_hint or _DEFAULT_CACHE_KEY
    record = cache.load(cache_key)
    
    if record is None:
        return None
    
    return {
        "tenant_id": record.tenant_id,
        "tenant_name": record.tenant_name,
        "roles": list(record.roles),
        "region": record.region.to_dict() if record.region else None,
        "guardrails": record.guardrails,
    }


def get_tenant_slug(tenant_hint: Optional[str] = None) -> Optional[str]:
    """Get the tenant slug/name for use in project naming.

    This is a convenience function that returns just the tenant name/slug,
    which is useful for constructing project names like "ComfyUI@{tenant_slug}".

    If tenant_name contains spaces or special characters, returns a shortened
    tenant_id instead (first 8 characters of the UUID).

    Args:
        tenant_hint: Optional tenant slug or ID to look up.

    Returns:
        Optional[str]: The tenant slug/name, or None if not available.

    Example:
        >>> slug = kumiho.get_tenant_slug()
        >>> project_name = f"ComfyUI@{slug or 'default'}"
        >>> print(project_name)
        ComfyUI@kumihoclouds
    """
    info = get_tenant_info(tenant_hint)
    if not info:
        return None
    
    tenant_name = info.get("tenant_name")
    tenant_id = info.get("tenant_id")
    
    # Check if tenant_name is URL-safe (alphanumeric, hyphens only)
    import re
    if tenant_name and re.match(r'^[a-zA-Z0-9-]+$', tenant_name):
        return tenant_name.lower()
    
    # Fall back to shortened tenant_id (first 8 chars of UUID)
    if tenant_id:
        return tenant_id.split('-')[0]  # First segment of UUID
    
    return tenant_name


# =============================================================================
# Top-level convenience functions
# =============================================================================


def create_project(name: str, description: str = "") -> Project:
    """Create a new project.

    Projects are the top-level containers for all assets. Each project
    has its own namespace for spaces and items.

    Args:
        name: The unique name for the project. Must be URL-safe
            (lowercase letters, numbers, hyphens).
        description: Optional human-readable description.

    Returns:
        Project: The newly created Project object.

    Raises:
        ProjectLimitError: If the tenant has reached their project limit.
        KumihoError: If the project name is invalid or already exists.

    Example:
        >>> project = kumiho.create_project(
        ...     "commercial-2024",
        ...     "Assets for 2024 commercial campaign"
        ... )
        >>> print(project.name)
        commercial-2024
    """
    return get_client().create_project(name=name, description=description)


def get_projects() -> List[Project]:
    """List all projects accessible to the current user.

    Returns:
        List[Project]: A list of Project objects.

    Example:
        >>> projects = kumiho.get_projects()
        >>> for p in projects:
        ...     print(f"{p.name}: {p.description}")
        commercial-2024: Assets for 2024 commercial campaign
        film-project: Feature film VFX assets
    """
    return get_client().get_projects()


def get_project(name: str) -> Optional[Project]:
    """Get a project by name.

    Args:
        name: The name of the project to retrieve.

    Returns:
        Optional[Project]: The Project object if found, None otherwise.

    Example:
        >>> project = kumiho.get_project("commercial-2024")
        >>> if project:
        ...     spaces = project.get_spaces()
    """
    return get_client().get_project(name)


def delete_project(project_id: str, force: bool = False) -> StatusResponse:
    """Delete a project.

    Args:
        project_id: The unique ID of the project to delete.
        force: If True, permanently delete the project and all its
            contents. If False (default), mark as deprecated.

    Returns:
        StatusResponse: A StatusResponse indicating success or failure.

    Warning:
        Force deletion is irreversible and removes all spaces, items,
        revisions, artifacts, and edges within the project.

    Example:
        >>> # Soft delete (deprecate)
        >>> kumiho.delete_project("proj-uuid-here")

        >>> # Hard delete (permanent)
        >>> kumiho.delete_project("proj-uuid-here", force=True)
    """
    return get_client().delete_project(project_id=project_id, force=force)


def item_search(
    context_filter: str = "",
    name_filter: str = "",
    kind_filter: str = ""
) -> List[Item]:
    """Search for items across projects and spaces.

    Args:
        context_filter: Filter by project or space path. Supports glob
            patterns like ``project-*`` or ``*/characters/*``.
        name_filter: Filter by item name. Supports wildcards.
        kind_filter: Filter by item kind (e.g., "model", "texture").

    Returns:
        List[Item]: A list of Item objects matching the filters.

    Example:
        >>> # Find all models in any project
        >>> models = kumiho.item_search(kind_filter="model")

        >>> # Find character assets in a specific project
        >>> chars = kumiho.item_search(
        ...     context_filter="film-project/characters",
        ...     kind_filter="model"
        ... )

        >>> # Wildcard search
        >>> heroes = kumiho.item_search(name_filter="hero*")
    """
    return get_client().item_search(context_filter, name_filter, kind_filter)


def get_item(kref: str) -> Item:
    """Get an item by its kref URI.

    Args:
        kref: The kref URI of the item
            (e.g., "kref://project/space/item.kind").

    Returns:
        Item: The Item object.

    Raises:
        grpc.RpcError: If the item is not found.

    Example:
        >>> item = kumiho.get_item(
        ...     "kref://film-project/characters/hero.model"
        ... )
        >>> revisions = item.get_revisions()
    """
    return get_client().get_item_by_kref(kref)


def get_bundle(kref: str) -> Bundle:
    """Get a bundle by its kref URI.

    This is a convenience function that gets an item and verifies it's a bundle.

    Args:
        kref: The kref URI of the bundle item
            (e.g., "kref://project/space/bundle-name.bundle").

    Returns:
        Bundle: The Bundle object.

    Raises:
        ValueError: If the item exists but is not a bundle.
        grpc.RpcError: If the bundle is not found.

    Example:
        >>> bundle = kumiho.get_bundle(
        ...     "kref://film-project/shots/shot001.bundle"
        ... )
        >>> members = bundle.get_members()
    """
    return get_client().get_bundle_by_kref(kref)


def get_revision(kref: str) -> Revision:
    """Get a revision by its kref URI.

    Args:
        kref: The kref URI of the revision
            (e.g., "kref://project/space/item.kind?r=1").

    Returns:
        Revision: The Revision object.

    Raises:
        grpc.RpcError: If the revision is not found.

    Example:
        >>> revision = kumiho.get_revision(
        ...     "kref://film-project/characters/hero.model?r=3"
        ... )
        >>> artifacts = revision.get_artifacts()
        >>> for a in artifacts:
        ...     print(a.location)
    """
    return get_client().get_revision(kref)


def get_artifact(kref: str) -> Artifact:
    """Get an artifact by its kref URI.

    Args:
        kref: The kref URI of the artifact
            (e.g., "kref://project/space/item.kind?r=1&a=main").

    Returns:
        Artifact: The Artifact object.

    Raises:
        grpc.RpcError: If the artifact is not found.
        ValueError: If the kref is missing the artifact name (&a=).

    Example:
        >>> artifact = kumiho.get_artifact(
        ...     "kref://film-project/characters/hero.model?r=3&a=mesh"
        ... )
        >>> print(artifact.location)
        /projects/film/char/hero_v3.fbx
    """
    return get_client().get_artifact_by_kref(kref)


def get_artifacts_by_location(location: str) -> List[Artifact]:
    """Find all artifacts at a specific file location.

    This is useful for reverse lookups—finding which Kumiho artifacts
    reference a particular file path.

    Args:
        location: The file path or URI to search for.

    Returns:
        List[Artifact]: A list of Artifact objects at that location.

    Example:
        >>> artifacts = kumiho.get_artifacts_by_location(
        ...     "/shared/assets/hero_v3.fbx"
        ... )
        >>> for a in artifacts:
        ...     print(f"{a.kref} -> {a.location}")
    """
    return get_client().get_artifacts_by_location(location)


def set_attribute(kref: str, key: str, value: str) -> bool:
    """Set a single metadata attribute on any entity.

    This allows granular updates to metadata without replacing the entire
    metadata map. Works on any entity type (Revision, Item, Artifact,
    or Space) identified by kref.

    Args:
        kref: The kref URI of the entity.
        key: The attribute key to set.
        value: The attribute value.

    Returns:
        bool: True if the attribute was set successfully.

    Raises:
        grpc.RpcError: If the entity is not found or the key is reserved.

    Example:
        >>> kumiho.set_attribute(
        ...     "kref://project/models/hero.model?r=1",
        ...     "render_engine",
        ...     "cycles"
        ... )
        True
    """
    return get_client().set_attribute(Kref(kref), key, value)


def get_attribute(kref: str, key: str) -> Optional[str]:
    """Get a single metadata attribute from any entity.

    Args:
        kref: The kref URI of the entity.
        key: The attribute key to retrieve.

    Returns:
        The attribute value if it exists, None otherwise.

    Example:
        >>> kumiho.get_attribute(
        ...     "kref://project/models/hero.model?r=1",
        ...     "render_engine"
        ... )
        "cycles"
    """
    return get_client().get_attribute(Kref(kref), key)


def delete_attribute(kref: str, key: str) -> bool:
    """Delete a single metadata attribute from any entity.

    Args:
        kref: The kref URI of the entity.
        key: The attribute key to delete.

    Returns:
        bool: True if the attribute was deleted successfully.

    Raises:
        grpc.RpcError: If the entity is not found or the key is reserved.

    Example:
        >>> kumiho.delete_attribute(
        ...     "kref://project/models/hero.model?r=1",
        ...     "old_field"
        ... )
        True
    """
    return get_client().delete_attribute(Kref(kref), key)


def event_stream(
    routing_key_filter: str = "",
    kref_filter: str = "",
    cursor: Optional[str] = None,
    consumer_group: Optional[str] = None,
    from_beginning: bool = False,
    timeout: Optional[float] = None,
) -> Iterator[Event]:
    """Subscribe to real-time events from the Kumiho server.

    Events are streamed as they occur, allowing you to react to changes
    in the database such as new revisions, tag changes, or deletions.

    Args:
        routing_key_filter: Filter events by routing key pattern.
            Supports wildcards (e.g., ``item.model.*``, ``revision.#``).
        kref_filter: Filter events by kref pattern.
            Supports glob patterns (e.g., ``kref://projectA/**/*.model``).
        cursor: Resume from a previous cursor position (Creator tier+).
            Pass the cursor from the last received event to continue
            from that point after reconnection.
        consumer_group: Consumer group name for load-balanced delivery
            (Enterprise tier only). Multiple consumers in the same group
            each receive different events.
        from_beginning: Start from earliest available events instead of
            live-only (Creator tier+, subject to retention limits).

    Yields:
        Event: Event objects as they occur. Each event includes a ``cursor``
            field that can be saved for resumption.

    Example:
        >>> # Watch for all revision events with cursor tracking
        >>> last_cursor = None
        >>> try:
        ...     for event in kumiho.event_stream(
        ...         routing_key_filter="revision.*",
        ...         kref_filter="kref://film-project/**",
        ...         cursor=last_cursor
        ...     ):
        ...         print(f"{event.routing_key}: {event.kref}")
        ...         last_cursor = event.cursor  # Save for reconnection
        ...         if event.routing_key == "revision.tagged":
        ...             print(f"  Tag: {event.details.get('tag')}")
        ... except ConnectionError:
        ...     # Reconnect using saved cursor
        ...     pass

    Note:
        This is a blocking iterator. Use in a separate thread or
        async context for production applications.
        
        Cursor-based resume requires Creator tier or above. Use
        :func:`get_event_capabilities` to check your tier's capabilities.
    """
    return get_client().event_stream(
        routing_key_filter,
        kref_filter,
        cursor,
        consumer_group,
        from_beginning,
        timeout=timeout,
    )


def get_event_capabilities() -> EventCapabilities:
    """Get event streaming capabilities for the current tenant tier.

    Returns the capabilities available based on the authenticated tenant's
    subscription tier. Use this to determine which features (cursor resume,
    consumer groups, replay) are available before using them.

    Returns:
        EventCapabilities: Object with capability flags and limits:
            - supports_replay: Can replay past events
            - supports_cursor: Can resume from cursor
            - supports_consumer_groups: Can use consumer groups (Enterprise)
            - max_retention_hours: Event retention period (-1 = unlimited)
            - max_buffer_size: Max events in buffer (-1 = unlimited)
            - tier: Tier name (free, creator, studio, enterprise)

    Example:
        >>> caps = kumiho.get_event_capabilities()
        >>> print(f"Tier: {caps.tier}")
        Tier: creator
        >>> if caps.supports_cursor:
        ...     # Use cursor-based streaming
        ...     last_cursor = load_saved_cursor()
        ...     for event in kumiho.event_stream(cursor=last_cursor):
        ...         process(event)
        ...         save_cursor(event.cursor)
        ... else:
        ...     # Free tier - no cursor support
        ...     for event in kumiho.event_stream():
        ...         process(event)
    """
    return get_client().get_event_capabilities()


def resolve(kref: str) -> Optional[str]:
    """Resolve a kref URI to a file location.

    This is a convenience function to get the file path for an artifact
    or the default artifact of a revision.

    Args:
        kref: The kref URI to resolve.

    Returns:
        Optional[str]: The file location string, or None if not resolvable.

    Example:
        >>> # Resolve a specific artifact
        >>> path = kumiho.resolve(
        ...     "kref://film-project/chars/hero.model?r=3&a=mesh"
        ... )
        >>> print(path)
        /projects/film/char/hero_v3.fbx

        >>> # Resolve revision's default artifact
        >>> path = kumiho.resolve(
        ...     "kref://film-project/chars/hero.model?r=3"
        ... )
    """
    return get_client().resolve(kref)


def connect(
    endpoint: Optional[str] = None,
    token: Optional[str] = None,
    *,
    enable_auto_login: bool = True,
    use_discovery: Optional[bool] = None,
    default_metadata: Optional[List[Tuple[str, str]]] = None,
    tenant_hint: Optional[str] = None,
) -> _Client:
    """Create a new Kumiho client with explicit configuration.

    Use this when you need more control over the client configuration,
    such as connecting to a specific server or using a custom token.

    Args:
        endpoint: The gRPC server endpoint (e.g., "localhost:50051"
            or "https://us-central.kumiho.cloud").
        token: The authentication token. If not provided and
            enable_auto_login is True, attempts to load from cache.
        enable_auto_login: If True, automatically use cached credentials
            when no token is provided.
        use_discovery: If True, use the discovery service to find the
            regional server. If None, auto-detect.
        default_metadata: Additional gRPC metadata to include with all
            requests (e.g., custom headers).
        tenant_hint: Tenant slug or ID for multi-tenant routing.

    Returns:
        _Client: A configured client instance.

    Example:
        Connect to a local development server::

            client = kumiho.connect(
                endpoint="localhost:50051",
                token=None  # No auth for local dev
            )

        Connect to production with explicit token::

            client = kumiho.connect(
                endpoint="https://us-central.kumiho.cloud",
                token=os.environ["KUMIHO_TOKEN"]
            )

        Use with context manager for temporary switching::

            client = kumiho.connect(endpoint="localhost:50051")
            with kumiho.use_client(client):
                local_projects = kumiho.get_projects()

    See Also:
        :func:`auto_configure_from_discovery`: Recommended for production.
        :func:`configure_default_client`: Set as global default.
    """
    return _Client(
        target=endpoint,
        auth_token=token,
        enable_auto_login=enable_auto_login,
        use_discovery=use_discovery,
        default_metadata=default_metadata,
        tenant_hint=tenant_hint,
    )


__all__ = [
    # Core classes
    "KumihoObject",
    "KumihoError",
    "Project",
    "Space",
    "Item",
    "Revision",
    "Artifact",
    "Edge",
    "Kref",
    "Event",
    "ProjectLimitError",
    # Bundle classes
    "Bundle",
    "BundleMember",
    "BundleRevisionHistory",
    "ReservedKindError",
    "RESERVED_KINDS",
    # Validation
    "KrefValidationError",
    "EdgeTypeValidationError",
    "validate_kref",
    "validate_edge_type",
    "is_valid_kref",
    "is_valid_edge_type",
    # Connection
    "connect",
    "use_client",
    "get_client",
    "configure_default_client",
    "auto_configure_from_discovery",
    # Constants
    "LATEST_TAG",
    "PUBLISHED_TAG",
    # Edge types
    "EdgeType",
    "BELONGS_TO",
    "CREATED_FROM",
    "REFERENCED",
    "DEPENDS_ON",
    "DERIVED_FROM",
    "CONTAINS",
    # Edge directions
    "EdgeDirection",
    "OUTGOING",
    "INCOMING",
    "BOTH",
    # Tenant info
    "get_tenant_info",
    "get_tenant_slug",
    # Top-level functions
    "create_project",
    "get_projects",
    "get_project",
    "delete_project",
    "item_search",
    "get_item",
    "get_bundle",
    "get_revision",
    "get_artifact",
    "get_artifacts_by_location",
    "set_attribute",
    "get_attribute",
    "delete_attribute",
    "event_stream",
    "get_event_capabilities",
    "EventCapabilities",
    "resolve",
]

# Remove typing imports from public namespace
del Any, Dict, List, Optional, Iterator, Tuple


_auto_configure_from_env_if_requested()
