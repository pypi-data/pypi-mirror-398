"""Revision module for Kumiho asset management.

This module provides the :class:`Revision` class, which represents a specific
iteration of an item. Revisions contain artifacts (file references), tags,
and metadata, and can be linked to other revisions to track dependencies.

Example:
    Working with revisions::

        import kumiho

        # Get a revision
        revision = kumiho.get_revision("kref://project/models/hero.model?r=1")

        # Add artifacts
        revision.create_artifact("mesh", "/assets/hero.fbx")
        revision.create_artifact("textures", "/assets/hero_tex.zip")

        # Tag the revision
        revision.tag("approved")
        revision.tag("ready-for-lighting")

        # Create edges to dependencies
        texture_revision = kumiho.get_revision("kref://project/textures/skin.texture?r=3")
        revision.create_edge(texture_revision, kumiho.DEPENDS_ON)
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from .base import KumihoObject
from .kref import Kref
from .proto.kumiho_pb2 import RevisionResponse
from .artifact import Artifact
from .edge import Edge

if TYPE_CHECKING:
    from .client import _Client
    from .item import Item
    from .space import Space
    from .project import Project
    from .edge import TraversalResult, RevisionPath, ImpactedRevision


class Revision(KumihoObject):
    """A specific iteration of an item in the Kumiho system.

    Revisions are immutable snapshots of an item at a point in time. Each
    revision can have multiple artifacts (file references), tags for
    categorization, and edges to other revisions for dependency tracking.

    The revision's kref includes the revision number:
    ``kref://project/space/item.kind?r=1``

    Revisions support dynamic tag checking—the ``tags`` property automatically
    refreshes from the server if the local data might be stale (older than 5
    seconds). This ensures tags like "latest" are always current.

    Attributes:
        kref (Kref): The unique reference URI for this revision.
        item_kref (Kref): Reference to the parent item.
        number (int): The revision number (1-based).
        latest (bool): Whether this is currently the latest revision.
        tags (List[str]): Tags applied to this revision (auto-refreshes).
        metadata (Dict[str, str]): Custom metadata key-value pairs.
        created_at (Optional[str]): ISO timestamp when the revision was created.
        author (str): The user ID who created the revision.
        deprecated (bool): Whether the revision is deprecated.
        published (bool): Whether the revision is published.
        username (str): Display name of the creator.
        default_artifact (Optional[str]): Name of the default artifact.

    Example:
        Creating and managing revisions::

            import kumiho

            item = kumiho.get_item("kref://project/models/hero.model")

            # Create a revision with metadata
            v1 = item.create_revision(metadata={
                "artist": "jane.doe",
                "software": "maya-2024",
                "notes": "Initial model"
            })

            # Add artifacts
            mesh = v1.create_artifact("mesh", "/assets/hero.fbx")
            rig = v1.create_artifact("rig", "/assets/hero_rig.fbx")

            # Set default artifact (for resolve)
            v1.set_default_artifact("mesh")

            # Tag the revision
            v1.tag("approved")

            # Check tags
            if v1.has_tag("approved"):
                print("Revision is approved!")

            # Get all artifacts
            for r in v1.get_artifacts():
                print(f"  {r.name}: {r.location}")

            # Edge to dependencies
            texture = kumiho.get_revision("kref://project/tex/skin.texture?r=2")
            v1.create_edge(texture, kumiho.DEPENDS_ON)
    """

    def __init__(self, pb_revision: RevisionResponse, client: '_Client') -> None:
        """Initialize a Revision from a protobuf response.

        Args:
            pb_revision: The protobuf RevisionResponse message.
            client: The client instance for making API calls.
        """
        super().__init__(client)
        self.kref = Kref(pb_revision.kref.uri)
        self.item_kref = Kref(pb_revision.item_kref.uri)
        self.number = pb_revision.number
        self.latest = pb_revision.latest
        self._cached_tags = list(pb_revision.tags)
        self.metadata = dict(pb_revision.metadata)
        self.created_at = pb_revision.created_at or None
        self.author = pb_revision.author
        self.deprecated = pb_revision.deprecated
        self.published = pb_revision.published
        self.username = pb_revision.username
        self.default_artifact = pb_revision.default_artifact or None
        self._fetched_at = datetime.now()

    def _is_stale(self) -> bool:
        """Check if this revision's data might be stale.
        
        Returns:
            bool: True if the data is older than 5 seconds, indicating
                that tags like 'latest' might have changed.
        """
        return (datetime.now() - self._fetched_at).total_seconds() > 5

    @property
    def tags(self) -> List[str]:
        """Get the current tags for this revision.

        This property automatically refreshes from the server if the data
        might be stale (older than 5 seconds), ensuring dynamic tags like
        "latest" are always current.

        Returns:
            List[str]: The list of tags on this revision.

        Example:
            >>> revision = item.get_revision(1)
            >>> print(revision.tags)  # ['latest', 'approved']
        """
        if self._is_stale():
            self.refresh()
        return self._cached_tags

    @tags.setter
    def tags(self, value: List[str]) -> None:
        """Set the cached tags (used internally)."""
        self._cached_tags = value

    def __repr__(self) -> str:
        """Return a string representation of the Revision."""
        return f"<Revision number='{self.number}' kref='{self.kref.uri}'>"

    def create_artifact(
        self,
        name: str,
        location: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Artifact:
        """Create a new artifact for this revision.

        Artifacts are file references that point to actual assets on disk
        or network storage. Kumiho tracks the path and metadata but does
        not upload or copy the files.

        Args:
            name: The name of the artifact (e.g., "mesh", "textures", "rig").
            location: The file path or URI where the artifact is stored.
            metadata: Optional key-value metadata for the artifact.

        Returns:
            Artifact: The newly created Artifact object.

        Example:
            >>> mesh = revision.create_artifact("mesh", "/assets/hero.fbx")
            >>> textures = revision.create_artifact("textures", "smb://server/tex/hero.zip",
            ...     metadata={"format": "png", "resolution": "4k"})
        """
        return self._client.create_artifact(self.kref, name, location, metadata=metadata)

    def set_metadata(self, metadata: Dict[str, str]) -> 'Revision':
        """Set or update metadata for this revision.

        Metadata is merged with existing metadata—existing keys are
        overwritten and new keys are added.

        Args:
            metadata: Dictionary of metadata key-value pairs.

        Returns:
            Revision: The updated Revision object.

        Example:
            >>> revision.set_metadata({
            ...     "render_engine": "arnold",
            ...     "frame_range": "1-100",
            ...     "resolution": "4K"
            ... })
        """
        return self._client.update_revision_metadata(self.kref, metadata)

    def set_attribute(self, key: str, value: str) -> bool:
        """Set a single metadata attribute.

        This allows granular updates to metadata without replacing the entire
        metadata map.

        Args:
            key: The attribute key to set.
            value: The attribute value.

        Returns:
            bool: True if the attribute was set successfully.

        Example:
            >>> revision.set_attribute("render_engine", "cycles")
            True
        """
        result = self._client.set_attribute(self.kref, key, value)
        if result:
            self.metadata[key] = value
        return result

    def get_attribute(self, key: str) -> Optional[str]:
        """Get a single metadata attribute.

        Args:
            key: The attribute key to retrieve.

        Returns:
            The attribute value if it exists, None otherwise.

        Example:
            >>> revision.get_attribute("render_engine")
            "cycles"
        """
        return self._client.get_attribute(self.kref, key)

    def delete_attribute(self, key: str) -> bool:
        """Delete a single metadata attribute.

        Args:
            key: The attribute key to delete.

        Returns:
            bool: True if the attribute was deleted successfully.

        Example:
            >>> revision.delete_attribute("old_field")
            True
        """
        result = self._client.delete_attribute(self.kref, key)
        if result and key in self.metadata:
            del self.metadata[key]
        return result

    def has_tag(self, tag: str) -> bool:
        """Check if this revision currently has a specific tag.

        This makes a server call to ensure the tag status is current.

        Args:
            tag: The tag to check for.

        Returns:
            bool: True if the revision has the tag, False otherwise.

        Example:
            >>> if revision.has_tag("approved"):
            ...     print("Ready for production!")
        """
        return self._client.has_tag(self.kref, tag)

    def tag(self, tag: str) -> None:
        """Apply a tag to this revision.

        Tags are used to categorize revisions and mark their status.
        Common tags include "latest", "published", "approved", etc.

        Note:
            The "latest" tag is automatically managed—it always points
            to the newest revision.

        Args:
            tag: The tag to apply.

        Example:
            >>> revision.tag("approved")
            >>> revision.tag("ready-for-lighting")
        """
        self._client.tag_revision(self.kref, tag)
        if tag not in self._cached_tags:
            self._cached_tags.append(tag)
        self._fetched_at = datetime.now()

    def untag(self, tag: str) -> None:
        """Remove a tag from this revision.

        Args:
            tag: The tag to remove.

        Example:
            >>> revision.untag("work-in-progress")
        """
        self._client.untag_revision(self.kref, tag)
        if tag in self._cached_tags:
            self._cached_tags.remove(tag)
        self._fetched_at = datetime.now()

    def was_tagged(self, tag: str) -> bool:
        """Check if this revision was ever tagged with a specific tag.

        This checks the historical record, not just current tags.

        Args:
            tag: The tag to check for.

        Returns:
            bool: True if the revision was ever tagged with this tag.

        Example:
            >>> if revision.was_tagged("approved"):
            ...     print("Was approved at some point")
        """
        return self._client.was_tagged(self.kref, tag)

    def get_artifact(self, name: str) -> Artifact:
        """Get a specific artifact by name from this revision.

        Args:
            name: The name of the artifact.

        Returns:
            Artifact: The Artifact object.

        Raises:
            grpc.RpcError: If the artifact is not found.

        Example:
            >>> mesh = revision.get_artifact("mesh")
            >>> print(mesh.location)
        """
        return self._client.get_artifact(self.kref, name)

    def get_artifacts(self) -> List[Artifact]:
        """Get all artifacts associated with this revision.

        Returns:
            List[Artifact]: A list of Artifact objects.

        Example:
            >>> for artifact in revision.get_artifacts():
            ...     print(f"{artifact.name}: {artifact.location}")
        """
        return self._client.get_artifacts(self.kref)

    def get_locations(self) -> List[str]:
        """Get the file locations of all artifacts in this revision.

        This is a convenience method to quickly get all file paths.

        Returns:
            List[str]: A list of file location strings.

        Example:
            >>> locations = revision.get_locations()
            >>> for loc in locations:
            ...     print(loc)
        """
        return [r.location for r in self.get_artifacts()]

    def get_item(self) -> 'Item':
        """Get the parent item of this revision.

        Returns:
            Item: The Item object that contains this revision.

        Example:
            >>> item = revision.get_item()
            >>> print(item.item_name)
        """
        return self._client.get_item_by_kref(self.item_kref.uri)

    def get_space(self) -> 'Space':
        """Get the space that contains this revision's item.

        Returns:
            Space: The Space object.

        Example:
            >>> space = revision.get_space()
            >>> print(space.path)
        """
        space_segment = self.item_kref.get_space()
        if space_segment:
            # Item is in a nested space: kref://project/space/item.kind
            space_path = f"/{self.item_kref.get_project()}/{space_segment}"
        else:
            # Item is in project root space: kref://project/item.kind
            space_path = f"/{self.item_kref.get_project()}"
        return self._client.get_space(space_path)

    def get_project(self) -> 'Project':
        """Get the project that contains this revision.

        Returns:
            Project: The Project object.

        Example:
            >>> project = revision.get_project()
            >>> print(project.name)
        """
        return self.get_space().get_project()

    def refresh(self) -> None:
        """Refresh this revision's data from the server.
        
        This updates all properties to reflect the current state in the
        database, including tags that may have changed (like "latest").

        Example:
            >>> revision.refresh()
            >>> print(revision.tags)  # Now shows current tags
        """
        fresh_revision = self._client.get_revision(self.kref)
        self.number = fresh_revision.number
        self.latest = fresh_revision.latest
        self._cached_tags = fresh_revision.tags
        self.metadata = fresh_revision.metadata
        self.created_at = fresh_revision.created_at
        self.author = fresh_revision.author
        self.deprecated = fresh_revision.deprecated
        self.published = fresh_revision.published
        self.username = fresh_revision.username
        self.default_artifact = fresh_revision.default_artifact
        self._fetched_at = datetime.now()

    def set_default_artifact(self, artifact_name: str) -> None:
        """Set the default artifact for this revision.

        The default artifact is used when resolving the revision's kref
        without specifying an artifact name.

        Args:
            artifact_name: The name of the artifact to set as default.

        Example:
            >>> revision.set_default_artifact("mesh")
            >>> # Now kref://project/model.kind?r=1 resolves to the mesh
        """
        from .proto.kumiho_pb2 import SetDefaultArtifactRequest
        req = SetDefaultArtifactRequest(
            revision_kref=self.kref.to_pb(),
            artifact_name=artifact_name
        )
        self._client.stub.SetDefaultArtifact(req)
        self.default_artifact = artifact_name

    def delete(self, force: bool = False) -> None:
        """Delete this revision.

        Args:
            force: If True, force deletion even if the revision has
                artifacts. If False (default), deletion may fail.

        Raises:
            grpc.RpcError: If deletion fails.

        Example:
            >>> revision.delete()  # Fails if has artifacts
            >>> revision.delete(force=True)  # Force delete
        """
        self._client.delete_revision(self.kref, force)

    def set_deprecated(self, status: bool) -> None:
        """Set the deprecated status of this revision.

        Deprecated revisions are hidden from default queries but remain
        accessible for historical reference.

        Args:
            status: True to deprecate, False to restore.

        Example:
            >>> revision.set_deprecated(True)  # Hide from queries
        """
        self._client.set_deprecated(self.kref, status)
        self.deprecated = status

    def create_edge(
        self,
        target_revision: 'Revision',
        edge_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> 'Edge':
        """Create an edge from this revision to another revision.

        Edges represent relationships between revisions, such as dependencies,
        references, or derivations. This is useful for tracking asset lineage.

        Args:
            target_revision: The target revision to link to.
            edge_type: The type of edge. Use constants from :class:`kumiho.EdgeType`:
                - ``kumiho.DEPENDS_ON``: This revision depends on target.
                - ``kumiho.DERIVED_FROM``: This revision was derived from target.
                - ``kumiho.REFERENCED``: This revision references target.
                - ``kumiho.CONTAINS``: This revision contains target.
            metadata: Optional metadata for the edge.

        Returns:
            Edge: The created Edge object.

        Example:
            >>> import kumiho

            >>> # Edge to a texture dependency
            >>> texture = kumiho.get_revision("kref://project/tex/skin.texture?r=2")
            >>> revision.create_edge(texture, kumiho.DEPENDS_ON)

            >>> # Edge with metadata
            >>> base = kumiho.get_revision("kref://project/models/base.model?r=1")
            >>> revision.create_edge(base, kumiho.DERIVED_FROM, {
            ...     "modification": "Added details"
            ... })
        """
        return self._client.create_edge(self, target_revision, edge_type, metadata)

    def get_edges(
        self,
        edge_type_filter: Optional[str] = None,
        direction: int = 0
    ) -> List['Edge']:
        """Get edges involving this revision.

        Args:
            edge_type_filter: Optional filter for edge type.
            direction: The direction of edges to retrieve:
                - ``kumiho.OUTGOING`` (0): Edges from this revision.
                - ``kumiho.INCOMING`` (1): Edges to this revision.
                - ``kumiho.BOTH`` (2): Edges in both directions.

        Returns:
            List[Edge]: A list of Edge objects.

        Example:
            >>> import kumiho

            >>> # Get all dependencies
            >>> deps = revision.get_edges(kumiho.DEPENDS_ON, kumiho.OUTGOING)

            >>> # Get all revisions that depend on this one
            >>> dependents = revision.get_edges(kumiho.DEPENDS_ON, kumiho.INCOMING)
        """
        return self._client.get_edges(self.kref, edge_type_filter or "", direction)

    def delete_edge(self, target_revision: 'Revision', edge_type: str) -> None:
        """Delete an edge from this revision.

        Args:
            target_revision: The target revision of the edge.
            edge_type: The type of edge to delete.

        Example:
            >>> revision.delete_edge(texture_revision, kumiho.DEPENDS_ON)
        """
        self._client.delete_edge(self.kref, target_revision.kref, edge_type)

    # --- Graph Traversal Methods ---

    def get_all_dependencies(
        self,
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        limit: int = 100
    ) -> 'TraversalResult':
        """Get all transitive dependencies of this revision.

        Traverses outgoing edges to find all revisions this revision
        depends on, directly or indirectly.

        Args:
            edge_type_filter: Filter by edge types (e.g., [kumiho.DEPENDS_ON]).
            max_depth: Maximum traversal depth (default: 10, max: 20).
            limit: Maximum number of results (default: 100, max: 1000).

        Returns:
            TraversalResult: Contains all discovered revisions and paths.

        Example:
            >>> import kumiho

            >>> # Get all dependencies up to 5 hops
            >>> deps = revision.get_all_dependencies(
            ...     edge_type_filter=[kumiho.DEPENDS_ON],
            ...     max_depth=5
            ... )
            >>> for kref in deps.revision_krefs:
            ...     print(f"Depends on: {kref}")
        """
        from .edge import EdgeDirection
        return self._client.traverse_edges(
            self.kref,
            direction=EdgeDirection.OUTGOING,
            edge_type_filter=edge_type_filter,
            max_depth=max_depth,
            limit=limit
        )

    def get_all_dependents(
        self,
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        limit: int = 100
    ) -> 'TraversalResult':
        """Get all revisions that transitively depend on this revision.

        Traverses incoming edges to find all revisions that depend on
        this revision, directly or indirectly. Useful for impact analysis.

        Args:
            edge_type_filter: Filter by edge types.
            max_depth: Maximum traversal depth.
            limit: Maximum number of results.

        Returns:
            TraversalResult: Contains all dependent revisions.

        Example:
            >>> # Find everything that would be affected by changing this texture
            >>> dependents = texture_v1.get_all_dependents([kumiho.DEPENDS_ON])
            >>> print(f"{len(dependents.revision_krefs)} revisions would be affected")
        """
        from .edge import EdgeDirection
        return self._client.traverse_edges(
            self.kref,
            direction=EdgeDirection.INCOMING,
            edge_type_filter=edge_type_filter,
            max_depth=max_depth,
            limit=limit
        )

    def find_path_to(
        self,
        target: 'Revision',
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        all_paths: bool = False
    ) -> Optional['RevisionPath']:
        """Find the shortest path from this revision to another.

        Uses graph traversal to find how two revisions are connected.

        Args:
            target: The target revision to find a path to.
            edge_type_filter: Filter by edge types.
            max_depth: Maximum path length to search.
            all_paths: If True, returns all shortest paths via result.paths.

        Returns:
            RevisionPath if a path exists, None otherwise.
            Use all_paths=True and access result.paths for multiple paths.

        Example:
            >>> path = model_v1.find_path_to(texture_v3)
            >>> if path:
            ...     print(f"Path length: {path.total_depth}")
            ...     for step in path.steps:
            ...         print(f"  -> {step.revision_kref} via {step.edge_type}")
        """
        result = self._client.find_shortest_path(
            self.kref,
            target.kref,
            edge_type_filter=edge_type_filter,
            max_depth=max_depth,
            all_shortest=all_paths
        )
        if all_paths:
            # Return the result object when all paths requested
            return result  # type: ignore
        return result.first_path

    def analyze_impact(
        self,
        edge_type_filter: Optional[List[str]] = None,
        max_depth: int = 10,
        limit: int = 100
    ) -> List['ImpactedRevision']:
        """Analyze the impact of changes to this revision.

        Returns all revisions that directly or indirectly depend on this
        revision, sorted by impact depth (closest dependencies first).

        Args:
            edge_type_filter: Edge types to follow (default: all).
            max_depth: How far to traverse (default: 10).
            limit: Maximum results (default: 100).

        Returns:
            List[ImpactedRevision]: Revisions that would be impacted.

        Example:
            >>> # Before modifying a shared texture
            >>> impact = texture_v1.analyze_impact()
            >>> print(f"{len(impact)} revisions would need review")
            >>> for iv in impact[:5]:
            ...     print(f"  {iv.revision_kref} (depth {iv.impact_depth})")
        """
        return self._client.analyze_impact(
            self.kref,
            edge_type_filter=edge_type_filter,
            max_depth=max_depth,
            limit=limit
        )
