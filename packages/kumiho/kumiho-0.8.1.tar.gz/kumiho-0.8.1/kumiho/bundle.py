"""Bundle module for Kumiho asset management.

This module provides the :class:`Bundle` class, which represents a special
type of item that aggregates other items. Bundles are used to group
related items together and maintain an audit trail of membership changes.

Bundles are unique in that:
    - The ``bundle`` kind is reserved and cannot be created manually.
    - Use :meth:`Project.create_bundle` or :meth:`Space.create_bundle`.
    - Each membership change (add/remove) creates a new revision for audit trail.
    - Revision metadata is immutable, providing complete change history.

Example::

    import kumiho

    # Create a bundle from a project or space
    project = kumiho.get_project("my-project")
    bundle = project.create_bundle("asset-bundle")

    # Add items to the bundle
    hero_model = kumiho.get_item("kref://my-project/models/hero.model")
    bundle.add_member(hero_model)

    # Get all members
    members = bundle.get_members()
    for member in members:
        print(f"Item: {member.item_kref}")

    # View history of changes (immutable audit trail)
    for entry in bundle.get_history():
        print(f"v{entry.revision_number}: {entry.action} {entry.member_item_kref}")

See Also:
    - :class:`BundleMember`: Data class for bundle members.
    - :class:`BundleRevisionHistory`: Data class for audit trail entries.
    - :exc:`ReservedKindError`: Error for reserved kind violations.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from .kref import Kref
from .item import Item

if TYPE_CHECKING:
    from .client import _Client
    from .revision import Revision
    from .proto.kumiho_pb2 import ItemResponse


# Reserved item kinds that cannot be created manually
RESERVED_KINDS = frozenset(["bundle"])
"""frozenset: Item kinds that are reserved and cannot be created via create_item.

Currently includes:
    - ``bundle``: Use :meth:`Project.create_bundle` or 
      :meth:`Space.create_bundle` instead.
"""


class ReservedKindError(Exception):
    """Raised when attempting to create an item with a reserved kind.

    This error is raised when calling :meth:`Space.create_item` or the
    low-level client ``create_item`` with a reserved kind such
    as ``bundle``.

    Example::

        import kumiho

        space = project.get_space("assets")

        # This will raise ReservedKindError
        try:
            space.create_item("my-bundle", "bundle")
        except kumiho.ReservedKindError as e:
            print(f"Error: {e}")
            # Use create_bundle instead
            bundle = space.create_bundle("my-bundle")
    """
    pass


@dataclass
class BundleMember:
    """An item that is a member of a bundle.

    Represents the membership relationship between an item and a bundle,
    including metadata about when and by whom the item was added.

    Attributes:
        item_kref (Kref): The kref of the member item.
        added_at (str): ISO timestamp when the item was added.
        added_by (str): UUID of the user who added the item.
        added_by_username (str): Display name of the user who added the item.
        added_in_revision (int): The bundle revision when this item was added.

    Example::

        members = bundle.get_members()
        for member in members:
            print(f"Item: {member.item_kref}")
            print(f"Added by: {member.added_by_username}")
            print(f"Added at: {member.added_at}")
            print(f"In revision: {member.added_in_revision}")
    """
    item_kref: Kref
    """Kref: The kref of the member item."""
    
    added_at: str
    """str: ISO timestamp when the item was added to the bundle."""
    
    added_by: str
    """str: UUID of the user who added the item."""
    
    added_by_username: str
    """str: Display name of the user who added the item."""
    
    added_in_revision: int
    """int: The bundle revision number when this item was added."""


@dataclass
class BundleRevisionHistory:
    """A historical change to a bundle's membership.

    Each entry captures a single add or remove operation, providing
    an immutable audit trail of all membership changes. The metadata
    is immutable once created, ensuring complete traceability.

    Attributes:
        revision_number (int): The bundle revision number for this change.
        action (str): The action performed: ``"CREATED"``, ``"ADDED"``, or ``"REMOVED"``.
        member_item_kref (Optional[Kref]): The item that was added/removed.
            None for the initial ``"CREATED"`` action.
        author (str): UUID of the user who made the change.
        username (str): Display name of the user who made the change.
        created_at (str): ISO timestamp of the change.
        metadata (Dict[str, str]): Immutable metadata captured at the time of change.

    Example::

        history = bundle.get_history()
        for entry in history:
            print(f"Revision {entry.revision_number}: {entry.action}")
            if entry.member_item_kref:
                print(f"  Item: {entry.member_item_kref}")
            print(f"  By: {entry.username} at {entry.created_at}")
    """
    revision_number: int
    """int: The bundle revision number for this change."""
    
    action: str
    """str: The action performed: ``"CREATED"``, ``"ADDED"``, or ``"REMOVED"``."""
    
    member_item_kref: Optional[Kref]
    """Optional[Kref]: The item that was added/removed (None for CREATED)."""
    
    author: str
    """str: UUID of the user who made the change."""
    
    username: str
    """str: Display name of the user who made the change."""
    
    created_at: str
    """str: ISO timestamp of when the change was made."""
    
    metadata: Dict[str, str]
    """Dict[str, str]: Immutable metadata captured at the time of the change."""


class Bundle(Item):
    """A special item type that aggregates other items.

    Bundles provide a way to group related items together. Unlike regular
    items, bundles cannot be created using the standard ``create_item``
    method—the ``bundle`` kind is reserved.

    Use :meth:`Project.create_bundle` or :meth:`Space.create_bundle`
    to create bundles.

    Key features:
        - Aggregates items (not revisions) via ``COLLECTS`` relationships.
        - Each membership change creates a new revision for audit trail.
        - Revision metadata is immutable, providing complete history.
        - Cannot contain itself (self-reference protection).

    Attributes:
        kref (Kref): The unique identifier for this bundle.
        name (str): The combined name (e.g., "my-bundle.bundle").
        item_name (str): The bundle name (e.g., "my-bundle").
        kind (str): Always "bundle".
        metadata (Dict[str, str]): Custom metadata key-value pairs.
        created_at (str): ISO timestamp when the bundle was created.
        author (str): The user ID who created the bundle.
        username (str): Display name of the creator.
        deprecated (bool): Whether the bundle is deprecated.

    Example::

        import kumiho

        # Create a bundle from a project
        project = kumiho.get_project("film-2024")
        bundle = project.create_bundle("release-v1")

        # Add items
        model = kumiho.get_item("kref://film-2024/models/hero.model")
        texture = kumiho.get_item("kref://film-2024/textures/hero.texture")
        bundle.add_member(model)
        bundle.add_member(texture)

        # List current members
        for member in bundle.get_members():
            print(f"{member.item_kref} added by {member.added_by_username}")

        # Remove a member
        bundle.remove_member(model)

        # View complete audit history
        for entry in bundle.get_history():
            print(f"v{entry.revision_number}: {entry.action}")

    See Also:
        :meth:`Project.create_bundle`: Create a bundle in a project.
        :meth:`Space.create_bundle`: Create a bundle in a space.
        :class:`BundleMember`: Data class for member information.
        :class:`BundleRevisionHistory`: Data class for audit entries.
    """

    def __init__(self, pb: 'ItemResponse', client: '_Client') -> None:
        """Initialize a Bundle from a protobuf response.

        Args:
            pb: The ItemResponse protobuf message.
            client: The client instance for making subsequent calls.

        Raises:
            ValueError: If the kind is not 'bundle'.
        """
        super().__init__(pb, client)
        if self.kind != "bundle":
            raise ValueError(
                f"Cannot create Bundle from kind '{self.kind}'. "
                "Expected 'bundle'."
            )

    def add_member(
        self,
        member: 'Item',
        metadata: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, Optional['Revision']]:
        """Add an item to this bundle.

        Creates a new revision of the bundle to track the change.
        The revision metadata will include the action (``"ADDED"``) and
        the member item kref for audit purposes.

        Args:
            member: The item to add to the bundle.
            metadata: Optional additional metadata to store in the revision.
                This metadata becomes part of the immutable audit trail.

        Returns:
            Tuple[bool, str, Optional[Revision]]: A tuple containing:
                - success: Whether the operation succeeded.
                - message: A status message.
                - new_revision: The new bundle revision created for this change.

        Raises:
            ValueError: If trying to add the bundle to itself.
            grpc.RpcError: If the member is already in the bundle
                (status code ``ALREADY_EXISTS``).

        Example::

            hero_model = kumiho.get_item("kref://project/models/hero.model")
            
            # Add with optional metadata
            success, msg, revision = bundle.add_member(
                hero_model,
                metadata={"reason": "character bundle", "approved_by": "director"}
            )
            
            if success:
                print(f"Added in revision {revision.number}")
        """
        return self._client.add_bundle_member(
            self.kref,
            member.kref,
            metadata=metadata
        )

    def remove_member(
        self,
        member: 'Item',
        metadata: Optional[Dict[str, str]] = None
    ) -> Tuple[bool, str, Optional['Revision']]:
        """Remove an item from this bundle.

        Creates a new revision of the bundle to track the change.
        The revision metadata will include the action (``"REMOVED"``) and
        the member item kref for audit purposes.

        Args:
            member: The item to remove from the bundle.
            metadata: Optional additional metadata to store in the revision.
                This metadata becomes part of the immutable audit trail.

        Returns:
            Tuple[bool, str, Optional[Revision]]: A tuple containing:
                - success: Whether the operation succeeded.
                - message: A status message.
                - new_revision: The new bundle revision created for this change.

        Raises:
            grpc.RpcError: If the member is not in the bundle
                (status code ``NOT_FOUND``).

        Example::

            # Remove an item from the bundle
            success, msg, revision = bundle.remove_member(hero_model)
            
            if success:
                print(f"Removed in revision {revision.number}")
        """
        return self._client.remove_bundle_member(
            self.kref,
            member.kref,
            metadata=metadata
        )

    def get_members(
        self,
        revision_number: Optional[int] = None
    ) -> List[BundleMember]:
        """Get all items that are members of this bundle.

        Returns information about each member item, including when
        it was added and by whom.

        Args:
            revision_number: Optional specific revision to query.
                If not provided, returns current membership.

        Returns:
            List[BundleMember]: List of member information objects.

        Example::

            # Get current members
            members = bundle.get_members()
            for member in members:
                print(f"{member.item_kref}")
                print(f"  Added by: {member.added_by_username}")
                print(f"  In revision: {member.added_in_revision}")

            # Get empty list if no members
            if not members:
                print("Bundle is empty")
        """
        members, _, _ = self._client.get_bundle_members(
            self.kref,
            revision_number=revision_number
        )
        return members

    def get_history(self) -> List[BundleRevisionHistory]:
        """Get the full history of membership changes.

        Returns all revisions with their associated actions, providing
        a complete and immutable audit trail of all adds and removes.

        The history is ordered by revision number, starting with the
        initial ``"CREATED"`` action.

        Returns:
            List[BundleRevisionHistory]: List of history entries, ordered
                by revision number (oldest first).

        Example::

            history = bundle.get_history()
            
            for entry in history:
                print(f"Revision {entry.revision_number}:")
                print(f"  Action: {entry.action}")
                print(f"  By: {entry.username}")
                print(f"  At: {entry.created_at}")
                if entry.member_item_kref:
                    print(f"  Item: {entry.member_item_kref}")
        """
        return self._client.get_bundle_history(self.kref)

    def __repr__(self) -> str:
        """Return a string representation of the Bundle."""
        return f"Bundle(kref={self.kref!r}, name={self.name!r})"
