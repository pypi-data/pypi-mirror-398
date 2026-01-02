"""Edge module for Kumiho asset management.

This module provides the :class:`Edge` class and related constants for
tracking relationships between revisions. Edges enable dependency tracking,
lineage visualization, and impact analysis.

Edge Types:
    - ``DEPENDS_ON``: Source depends on target (e.g., model uses texture).
    - ``DERIVED_FROM``: Source was created from target (e.g., LOD from highpoly).
    - ``REFERENCED``: Source references target (soft dependency).
    - ``CONTAINS``: Source contains target (composition).
    - ``CREATED_FROM``: Source was generated from target.
    - ``BELONGS_TO``: Source belongs to target (grouping).

Example::

    import kumiho

    # Get revisions
    model = kumiho.get_revision("kref://project/models/hero.model?r=1")
    texture = kumiho.get_revision("kref://project/tex/skin.texture?r=2")

    # Create a dependency edge
    edge = model.create_edge(texture, kumiho.DEPENDS_ON)

    # Query edges
    deps = model.get_edges(kumiho.DEPENDS_ON, kumiho.OUTGOING)
    for dep in deps:
        print(f"{dep.source_kref} depends on {dep.target_kref}")
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional
import re

from .base import KumihoObject
from .kref import Kref
from .proto.kumiho_pb2 import Edge as PbEdge

if TYPE_CHECKING:
    from .client import _Client


class EdgeTypeValidationError(ValueError):
    """Raised when an edge type is invalid or potentially malicious."""
    pass


# Regex for validating edge types - must match Rust server validation
_EDGE_TYPE_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]{0,49}$')


def validate_edge_type(edge_type: str) -> None:
    """Validate an edge type for security and correctness.
    
    Edge types must:
    - Start with an uppercase letter
    - Contain only uppercase letters, digits, and underscores
    - Be 1-50 characters long
    
    Args:
        edge_type: The edge type to validate.
        
    Raises:
        EdgeTypeValidationError: If the edge type is invalid.
        
    Example::
    
        from kumiho.edge import validate_edge_type, EdgeTypeValidationError
        
        try:
            validate_edge_type("DEPENDS_ON")  # OK
            validate_edge_type("depends_on")  # Raises error
        except EdgeTypeValidationError as e:
            print(f"Invalid edge type: {e}")
    """
    if not isinstance(edge_type, str):
        raise EdgeTypeValidationError(
            f"Edge type must be a string, got {type(edge_type).__name__}"
        )
    
    if not _EDGE_TYPE_PATTERN.match(edge_type):
        raise EdgeTypeValidationError(
            f"Invalid edge_type '{edge_type}'. Must start with uppercase letter, "
            "contain only uppercase letters, digits, underscores, and be 1-50 chars."
        )


def is_valid_edge_type(edge_type: str) -> bool:
    """Check if an edge type is valid without raising exceptions.
    
    Args:
        edge_type: The edge type to validate.
        
    Returns:
        True if the edge type is valid, False otherwise.
    """
    try:
        validate_edge_type(edge_type)
        return True
    except EdgeTypeValidationError:
        return False


class EdgeType:
    """Standard edge types for Kumiho relationships.

    These constants define the semantic meaning of relationships between
    revisions. Use them when creating or querying edges.
    
    All edge types use UPPERCASE format as required by the Neo4j graph database.

    Attributes:
        BELONGS_TO (str): Indicates ownership or grouping relationship.
        CREATED_FROM (str): Indicates the source was generated from target.
        REFERENCED (str): Indicates a soft reference relationship.
        DEPENDS_ON (str): Indicates the source requires the target.
        DERIVED_FROM (str): Indicates the source was derived/modified from target.
        CONTAINS (str): Indicates the source contains or includes the target.

    Example::

        import kumiho

        # Model depends on texture
        model_v1.create_edge(texture_v2, kumiho.DEPENDS_ON)

        # LOD derived from high-poly
        lod_v1.create_edge(highpoly_v1, kumiho.DERIVED_FROM)
    """

    BELONGS_TO = "BELONGS_TO"
    """Ownership or grouping relationship."""

    CREATED_FROM = "CREATED_FROM"
    """Source was generated/created from target."""

    REFERENCED = "REFERENCED"
    """Soft reference relationship."""

    DEPENDS_ON = "DEPENDS_ON"
    """Source requires target to function."""

    DERIVED_FROM = "DERIVED_FROM"
    """Source was derived or modified from target."""

    CONTAINS = "CONTAINS"
    """Source contains or includes target."""

class EdgeDirection:
    """Direction constants for edge traversal queries.

    When querying edges, you can specify which direction to traverse:
    outgoing edges (from source), incoming edges (to target), or both.

    Attributes:
        OUTGOING (int): Edges where the queried revision is the source.
        INCOMING (int): Edges where the queried revision is the target.
        BOTH (int): Edges in either direction.

    Example::

        import kumiho

        # Get dependencies (what this revision depends on)
        deps = revision.get_edges(kumiho.DEPENDS_ON, kumiho.OUTGOING)

        # Get dependents (what depends on this revision)
        dependents = revision.get_edges(kumiho.DEPENDS_ON, kumiho.INCOMING)

        # Get all relationships
        all_edges = revision.get_edges(direction=kumiho.BOTH)
    """

    OUTGOING = 0
    """Edges where the queried revision is the source."""

    INCOMING = 1
    """Edges where the queried revision is the target."""

    BOTH = 2
    """Edges in either direction."""


class Edge(KumihoObject):
    """A relationship between two revisions in the Kumiho system.

    Edges represent semantic relationships between revisions, enabling
    dependency tracking, lineage visualization, and impact analysis.
    They are directional (source -> target) and typed.

    Common use cases:
        - Track which textures a model uses (DEPENDS_ON)
        - Record that a LOD was created from a high-poly model (DERIVED_FROM)
        - Link a render to the scene file that created it (CREATED_FROM)

    Attributes:
        source_kref (Kref): Reference to the source revision.
        target_kref (Kref): Reference to the target revision.
        edge_type (str): The type of relationship (see :class:`EdgeType`).
        metadata (Dict[str, str]): Custom metadata key-value pairs.
        created_at (Optional[str]): ISO timestamp when the edge was created.
        author (str): The user ID who created the edge.
        username (str): Display name of the creator.

    Example::

        import kumiho

        # Get revisions
        model = kumiho.get_revision("kref://project/models/hero.model?r=1")
        texture = kumiho.get_revision("kref://project/tex/skin.texture?r=2")

        # Create edge with metadata
        edge = model.create_edge(texture, kumiho.DEPENDS_ON, {
            "channel": "diffuse",
            "uv_set": "0"
        })

        # Inspect edge
        print(f"Type: {edge.edge_type}")
        print(f"From: {edge.source_kref}")
        print(f"To: {edge.target_kref}")

        # Delete edge
        edge.delete()
    """

    def __init__(self, pb_edge: PbEdge, client: '_Client') -> None:
        """Initialize an Edge from a protobuf message.

        Args:
            pb_edge: The protobuf Edge message.
            client: The client instance for making API calls.
        """
        super().__init__(client)
        self.source_kref = Kref(pb_edge.source_kref.uri)
        self.target_kref = Kref(pb_edge.target_kref.uri)
        self.edge_type = pb_edge.edge_type
        self.metadata = dict(pb_edge.metadata)
        self.created_at = pb_edge.created_at or None
        self.author = pb_edge.author
        self.username = pb_edge.username

    def __repr__(self) -> str:
        """Return a string representation of the Edge."""
        return f"<Edge {self.source_kref.uri} -> {self.target_kref.uri} type={self.edge_type}>"

    def delete(self, force: bool = False) -> None:
        """Delete this edge.

        Args:
            force: Reserved for future use.

        Example:
            >>> edge = model.create_edge(texture, kumiho.DEPENDS_ON)
            >>> edge.delete()  # Remove the relationship
        """
        self._client.delete_edge(self.source_kref, self.target_kref, self.edge_type)


# --- Graph Traversal Result Classes ---

from dataclasses import dataclass, field
from typing import List


@dataclass
class PathStep:
    """A single step in a traversal path.

    Represents one hop in a graph traversal, including the revision
    reached and the edge type used to reach it.

    Attributes:
        revision_kref (Kref): The revision at this step.
        edge_type (str): The relationship type used to reach this revision.
        depth (int): Distance from the origin (0 = origin).

    Example::

        for step in path.steps:
            print(f"Step {step.depth}: {step.revision_kref} via {step.edge_type}")
    """
    revision_kref: Kref
    edge_type: str
    depth: int


@dataclass
class RevisionPath:
    """A complete path between revisions.

    Represents a sequence of steps from one revision to another,
    used in traversal and shortest-path queries.

    Attributes:
        steps (List[PathStep]): The sequence of steps in the path.
        total_depth (int): Total length of the path.

    Example::

        path = source_revision.find_path_to(target_revision)
        if path:
            print(f"Path length: {path.total_depth}")
            for step in path.steps:
                print(f"  -> {step.revision_kref}")
    """
    steps: List[PathStep] = field(default_factory=list)
    total_depth: int = 0


@dataclass
class ImpactedRevision:
    """A revision impacted by changes to another revision.

    Represents a revision that directly or indirectly depends on
    a target revision, used in impact analysis.

    Attributes:
        revision_kref (Kref): The impacted revision.
        item_kref (Kref): The item containing the impacted revision.
        impact_depth (int): How many hops away from the target.
        impact_path_types (List[str]): Edge types in the impact chain.

    Example::

        impact = texture_v1.analyze_impact()
        for iv in impact:
            print(f"{iv.revision_kref} at depth {iv.impact_depth}")
    """
    revision_kref: Kref
    item_kref: Optional[Kref] = None
    impact_depth: int = 0
    impact_path_types: List[str] = field(default_factory=list)


class TraversalResult:
    """Result of a graph traversal query.

    Contains all revisions discovered during a multi-hop traversal,
    along with optional path information.

    Attributes:
        revision_krefs (List[Kref]): Flat list of discovered revision references.
        paths (List[RevisionPath]): Path information if requested.
        edges (List[Edge]): All traversed edges.
        total_count (int): Total number of discovered revisions.
        truncated (bool): True if results were limited by max_depth or limit.

    Example::

        # Get all transitive dependencies
        result = revision.get_all_dependencies(max_depth=5)
        
        print(f"Found {result.total_count} dependencies")
        if result.truncated:
            print("Results were truncated")
        
        for kref in result.revision_krefs:
            print(f"  - {kref}")
    """

    def __init__(
        self,
        revision_krefs: List[Kref],
        paths: List[RevisionPath],
        edges: List['Edge'],
        total_count: int,
        truncated: bool,
        client: '_Client'
    ) -> None:
        self.revision_krefs = revision_krefs
        self.paths = paths
        self.edges = edges
        self.total_count = total_count
        self.truncated = truncated
        self._client = client

    def __repr__(self) -> str:
        return f"<TraversalResult count={self.total_count} truncated={self.truncated}>"

    def get_revisions(self) -> List['Revision']:
        """Fetch full Revision objects for all discovered revisions.

        Returns:
            List[Revision]: List of Revision objects.

        Example::

            result = revision.get_all_dependencies()
            for v in result.get_revisions():
                print(f"{v.kref} - {v.metadata}")
        """
        from .revision import Revision
        return [self._client.get_revision(kref) for kref in self.revision_krefs]


class ShortestPathResult:
    """Result of a shortest path query.

    Contains path(s) between two revisions if found.

    Attributes:
        paths (List[RevisionPath]): One or more shortest paths found.
        path_exists (bool): True if any path was found.
        path_length (int): Length of the shortest path(s).

    Example::

        result = source_revision.find_path_to(target_revision)
        if result.path_exists:
            print(f"Found path of length {result.path_length}")
            for path in result.paths:
                for step in path.steps:
                    print(f"  {step.depth}: {step.revision_kref}")
    """

    def __init__(
        self,
        paths: List[RevisionPath],
        path_exists: bool,
        path_length: int
    ) -> None:
        self.paths = paths
        self.path_exists = path_exists
        self.path_length = path_length

    def __repr__(self) -> str:
        return f"<ShortestPathResult exists={self.path_exists} length={self.path_length}>"

    @property
    def first_path(self) -> Optional[RevisionPath]:
        """Get the first (or only) shortest path.

        Returns:
            RevisionPath if a path exists, None otherwise.
        """
        return self.paths[0] if self.paths else None
