"""Kref module for Kumiho artifact references.

This module provides the :class:`Kref` class, which represents a Kumiho
Artifact Reference—a URI-based unique identifier for any object in the
Kumiho system.

Kref Format:
    The kref URI follows this pattern::

        kref://project/space/item.kind?r=REVISION&a=ARTIFACT

    Components:
        - ``project``: The project name
        - ``space``: The space path (can be nested: ``space/subspace``)
        - ``item.kind``: Item name and kind separated by dot
        - ``?r=REVISION``: Optional revision number (default: 1)
        - ``&a=ARTIFACT``: Optional artifact name

Examples:
    Item kref::

        kref://film-2024/characters/hero.model

    Revision kref::

        kref://film-2024/characters/hero.model?r=3

    Artifact kref::

        kref://film-2024/characters/hero.model?r=3&a=mesh

Usage::

    import kumiho
    from kumiho import Kref

    # Parse a kref
    kref = Kref("kref://project/models/hero.model?r=2&a=mesh")

    # Extract components
    print(kref.get_space())        # "project/models"
    print(kref.get_item_name())    # "hero.model"
    print(kref.get_kind())         # "model"
    print(kref.get_revision())     # 2
    print(kref.get_artifact_name()) # "mesh"

    # Use as string
    print(f"Reference: {kref}")  # Works like a string
"""

from typing import Optional
import re
from .proto import kumiho_pb2


class KrefValidationError(ValueError):
    """Raised when a Kref URI is invalid or contains malicious patterns."""
    pass


# Regex for validating Kref URIs.
# Valid formats:
#   - Item: kref://project/space/item.kind?r=REVISION&a=ARTIFACT
#   - Space: kref://project/space or kref:///space (root-level)
# Each path segment must be alphanumeric with dots, underscores, or hyphens.
_KREF_PATTERN = re.compile(
    r'^kref://'                                    # scheme
    r'(/[a-zA-Z0-9][a-zA-Z0-9._-]*'               # space path starting with / (root-level)
    r'(/[a-zA-Z0-9][a-zA-Z0-9._-]*)*'             # optional nested path segments
    r'|'                                           # OR
    r'[a-zA-Z0-9][a-zA-Z0-9._-]*'                 # project/item path segment
    r'(/[a-zA-Z0-9][a-zA-Z0-9._-]*)*)'            # optional nested path segments
    r'(\?r=\d+(&a=[a-zA-Z0-9._-]+)?)?$'           # optional revision and artifact
)


def validate_kref(uri: str) -> None:
    """Validate a Kref URI for security and correctness.
    
    Checks for:
    - Proper kref:// scheme
    - No path traversal patterns (..)
    - No control characters
    - Valid path segment format
    
    Args:
        uri: The kref URI to validate.
        
    Raises:
        KrefValidationError: If the URI is invalid or contains malicious patterns.
        
    Example::
    
        from kumiho.kref import validate_kref, KrefValidationError
        
        try:
            validate_kref("kref://project/space/item.kind?r=1")
        except KrefValidationError as e:
            print(f"Invalid kref: {e}")
    """
    if not isinstance(uri, str):
        raise KrefValidationError(f"Kref must be a string, got {type(uri).__name__}")
    
    # Check for path traversal attempts
    if '..' in uri:
        raise KrefValidationError(
            f"Invalid kref URI '{uri}': path traversal (..) not allowed"
        )
    
    # Check for control characters
    if any(ord(c) < 32 or c == '\x7f' for c in uri):
        raise KrefValidationError(
            f"Invalid kref URI '{uri}': control characters not allowed"
        )
    
    # Check format with regex
    if not _KREF_PATTERN.match(uri):
        raise KrefValidationError(
            f"Invalid kref URI '{uri}': must be format kref://project/space/item.kind"
        )


def is_valid_kref(uri: str) -> bool:
    """Check if a Kref URI is valid without raising exceptions.
    
    Args:
        uri: The kref URI to validate.
        
    Returns:
        True if the URI is valid, False otherwise.
        
    Example::
    
        from kumiho.kref import is_valid_kref
        
        if is_valid_kref("kref://project/space/item.kind"):
            print("Valid!")
    """
    try:
        validate_kref(uri)
        return True
    except KrefValidationError:
        return False


class Kref(str):
    """A Kumiho Artifact Reference (URI-based unique identifier).

    Kref is a subclass of ``str``, so it behaves like a string but provides
    utility methods for parsing and extracting components from the URI.

    The kref format is::

        kref://project/space/item.kind?r=REVISION&a=ARTIFACT

    Attributes:
        uri (str): The URI string (for backward compatibility).

    Example::

        from kumiho import Kref

        # Create from string
        kref = Kref("kref://my-project/assets/hero.model?r=2")

        # Use as string (since Kref extends str)
        print(kref)  # kref://my-project/assets/hero.model?r=2

        # Parse components
        print(kref.get_space())    # "my-project/assets"
        print(kref.get_revision()) # 2

        # Compare with strings
        if kref == "kref://my-project/assets/hero.model?r=2":
            print("Match!")

    Note:
        Since Kref is a string subclass, you can use it anywhere a string
        is expected. All string methods work normally.
    """

    def __new__(cls, uri: str, *, validate: bool = True) -> 'Kref':
        """Create a new Kref instance.

        Args:
            uri: The kref URI string.
            validate: Whether to validate the URI (default: True).
                      Set to False for trusted internal sources.

        Returns:
            Kref: A Kref instance that is also a string.
            
        Raises:
            KrefValidationError: If validate=True and the URI is invalid.

        Example:
            >>> kref = Kref("kref://project/space/item.kind?r=1")
            >>> isinstance(kref, str)
            True
        """
        if validate:
            validate_kref(uri)
        return str.__new__(cls, uri)
    
    @classmethod
    def from_pb(cls, pb_kref: kumiho_pb2.Kref) -> 'Kref':
        """Create a Kref from a protobuf message.
        
        This is used for krefs received from the server, which are trusted.
        
        Args:
            pb_kref: The protobuf Kref message.
            
        Returns:
            Kref: A Kref instance.
        """
        # Don't validate server-returned krefs - they're trusted
        return cls(pb_kref.uri, validate=False)

    @property
    def uri(self) -> str:
        """Get the URI string.

        This property exists for backward compatibility with older code
        that accessed ``.uri`` directly.

        Returns:
            str: The kref URI string.
        """
        return str(self)

    def to_pb(self) -> kumiho_pb2.Kref:
        """Convert to a protobuf Kref object.

        Used internally for gRPC communication.

        Returns:
            kumiho_pb2.Kref: A protobuf Kref message.
        """
        return kumiho_pb2.Kref(uri=str(self))

    def get_path(self) -> str:
        """Extract the path component from the URI.

        Returns the part after ``kref://`` and before any query parameters.

        Returns:
            str: The path (e.g., "project/space/item.kind").

        Example:
            >>> Kref("kref://project/models/hero.model?r=1").get_path()
            'project/models/hero.model'
        """
        if "://" not in self:
            return self
        return self.split("://", 1)[1].split("?", 1)[0]

    def get_project(self) -> str:
        """Extract the project name from the URI.

        Returns the first path component (project name).

        Returns:
            str: The project name (e.g., "my-project").

        Example:
            >>> Kref("kref://my-project/models/hero.model").get_project()
            'my-project'
        """
        path = self.get_path()
        if "/" not in path:
            return path
        return path.split("/", 1)[0]

    def get_space(self) -> str:
        """Extract the space path from the URI (without project).

        Returns the path between project and item name.

        Returns:
            str: The space path (e.g., "models" or "models/characters").

        Example:
            >>> Kref("kref://project/models/hero.model").get_space()
            'models'
            >>> Kref("kref://project/models/characters/hero.model").get_space()
            'models/characters'
        """
        path = self.get_path()
        if "/" not in path:
            return ""
        # Remove project (first segment) and item (last segment)
        parts = path.split("/")
        if len(parts) <= 2:
            # Only project/item.kind - no space
            return ""
        # Return everything between project and item
        return "/".join(parts[1:-1])

    def get_item_name(self) -> str:
        """Extract the item name with kind from the URI.

        Returns:
            str: The item name including kind (e.g., "hero.model").

        Example:
            >>> Kref("kref://project/models/hero.model").get_item_name()
            'hero.model'
        """
        path = self.get_path()
        if "/" not in path:
            return ""
        return path.rsplit("/", 1)[1]

    def get_kind(self) -> str:
        """Extract the item kind from the URI.

        Returns:
            str: The item kind (e.g., "model", "texture").

        Example:
            >>> Kref("kref://project/models/hero.model").get_kind()
            'model'
        """
        name = self.get_item_name()
        if "." not in name:
            return ""
        return name.split(".", 1)[1]

    def get_revision(self) -> int:
        """Extract the revision number from the URI query string.

        Returns:
            int: The revision number, or 1 if not specified.

        Example:
            >>> Kref("kref://project/models/hero.model?r=3").get_revision()
            3
            >>> Kref("kref://project/models/hero.model").get_revision()
            1
        """
        match = re.search(r'\?r=(\d+)', self)
        return int(match.group(1)) if match else 1

    def get_artifact_name(self) -> Optional[str]:
        """Extract the artifact name from the URI query string.

        Returns:
            Optional[str]: The artifact name if present, None otherwise.

        Example:
            >>> Kref("kref://project/models/hero.model?r=1&a=mesh").get_artifact_name()
            'mesh'
            >>> Kref("kref://project/models/hero.model?r=1").get_artifact_name()
            None
        """
        match = re.search(r'&a=([^&]+)', self)
        return match.group(1) if match else None

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"Kref('{self}')"

    def __eq__(self, other: object) -> bool:
        """Compare with another Kref or string."""
        if isinstance(other, str):
            return str(self) == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        return str.__hash__(self)