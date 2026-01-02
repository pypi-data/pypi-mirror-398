"""Item module for Kumiho asset management.

This module provides the :class:`Item` class, which represents a versioned
asset in the Kumiho system. Items are the core entities that get versioned,
and each revision can have multiple artifacts (file references).

Example:
    Working with items and revisions::

        import kumiho

        # Get an item
        item = kumiho.get_item("kref://my-project/models/hero.model")

        # Create a new revision
        v1 = item.create_revision(metadata={"artist": "john"})

        # Add artifacts to the revision
        v1.create_artifact("mesh", "/assets/hero_v1.fbx")
        v1.create_artifact("rig", "/assets/hero_v1_rig.fbx")

        # Tag the revision
        v1.tag("approved")

        # Get all revisions
        for revision in item.get_revisions():
            print(f"v{revision.number}: {revision.tags}")
"""

import grpc
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Union

from .base import KumihoObject
from .kref import Kref
from .proto.kumiho_pb2 import ItemResponse, ResolveKrefRequest
from .revision import Revision

if TYPE_CHECKING:
    from .client import _Client
    from .space import Space
    from .project import Project


class Item(KumihoObject):
    """A versioned asset in the Kumiho system.

    Items represent assets that can have multiple revisions, such as 3D models,
    textures, workflows, or any other type of creative content. Each item
    belongs to a space and is identified by a combination of name and kind.

    The item's kref (Kumiho Reference) is a URI that uniquely identifies it:
    ``kref://project/space/item.kind``

    Attributes:
        kref (Kref): The unique reference URI for this item.
        name (str): The full name including kind (e.g., "hero.model").
        item_name (str): The base name of the item (e.g., "hero").
        kind (str): The kind of item (e.g., "model", "texture").
        project (str): The project name this item belongs to.
        space (str): The space path this item belongs to.
        created_at (Optional[str]): ISO timestamp when the item was created.
        author (str): The user ID who created the item.
        metadata (Dict[str, str]): Custom metadata key-value pairs.
        deprecated (bool): Whether the item is deprecated.
        username (str): Display name of the creator.

    Example:
        Basic item operations::

            import kumiho

            # Get item by kref
            item = kumiho.get_item("kref://film/chars/hero.model")

            # Create revisions
            v1 = item.create_revision()
            v2 = item.create_revision(metadata={"notes": "Updated mesh"})

            # Get specific revision
            v1 = item.get_revision(1)
            latest = item.get_latest_revision()

            # Get revision by tag
            approved = item.get_revision_by_tag("approved")

            # Get revision at a specific time
            historical = item.get_revision_by_time("202312011200")

            # Set metadata
            item.set_metadata({"status": "final", "priority": "high"})

            # Deprecate the item
            item.set_deprecated(True)
    """

    def __init__(self, pb_item: ItemResponse, client: '_Client') -> None:
        """Initialize an Item from a protobuf response.

        Args:
            pb_item: The protobuf ItemResponse message.
            client: The client instance for making API calls.
        """
        super().__init__(client)
        self.kref = Kref(pb_item.kref.uri)
        self.name = pb_item.name
        self.item_name = pb_item.item_name
        self.kind = pb_item.kind
        self.created_at = pb_item.created_at or None
        self.author = pb_item.author
        self.metadata = dict(pb_item.metadata)
        self.deprecated = pb_item.deprecated
        
        # Extract project and space from kref for convenience
        self._project = self.kref.get_project()
        self._space = self.kref.get_space()
        self.username = pb_item.username

    def __repr__(self) -> str:
        """Return a string representation of the Item."""
        return f"<Item kref='{self.kref.uri}'>"

    @property
    def project(self) -> str:
        """Get the project name this item belongs to.
        
        Returns:
            str: The project name (e.g., "my-project").
            
        Example:
            >>> item = kumiho.get_item("kref://my-project/models/hero.model")
            >>> item.project
            'my-project'
        """
        return self._project

    @property
    def space(self) -> str:
        """Get the space path this item belongs to.
        
        Returns:
            str: The space path (e.g., "models" or "models/characters").
            
        Example:
            >>> item = kumiho.get_item("kref://my-project/models/hero.model")
            >>> item.space
            'models'
        """
        return self._space

    def create_revision(
        self,
        metadata: Optional[Dict[str, str]] = None,
        number: int = 0
    ) -> Revision:
        """Create a new revision of this item.

        Revisions are automatically numbered sequentially. Each revision starts
        with the "latest" tag, which moves to the newest revision.

        Args:
            metadata: Optional metadata for the revision (e.g., artist notes,
                render settings, software versions).
            number: Specific revision number to use. If 0 (default), auto-assigns
                the next available number.

        Returns:
            Revision: The newly created Revision object.

        Example:
            >>> # Auto-numbered revision
            >>> v1 = item.create_revision()
            >>> v2 = item.create_revision(metadata={"artist": "jane"})

            >>> # Specific revision number (use with caution)
            >>> v5 = item.create_revision(number=5)
        """
        return self._client.create_revision(self.kref, metadata, number)

    def get_revisions(self) -> List[Revision]:
        """Get all revisions of this item.

        Returns:
            List[Revision]: A list of Revision objects, ordered by revision number.

        Example:
            >>> revisions = item.get_revisions()
            >>> for v in revisions:
            ...     print(f"v{v.number}: created {v.created_at}")
        """
        return self._client.get_revisions(self.kref)

    def get_revision(self, revision_number: int) -> Optional[Revision]:
        """Get a specific revision by its number.

        Args:
            revision_number: The revision number to retrieve (1-based).

        Returns:
            Optional[Revision]: The Revision object if found, None otherwise.

        Example:
            >>> v3 = item.get_revision(3)
            >>> if v3:
            ...     artifacts = v3.get_artifacts()
        """
        kref_uri = f"{self.kref.uri}?r={revision_number}"
        return self._client.get_revision(kref_uri)

    def get_latest_revision(self) -> Optional[Revision]:
        """Get the latest revision of this item.

        The latest revision is the one with the "latest" tag, or if none
        exists, the revision with the highest number.

        Returns:
            Optional[Revision]: The latest Revision object, or None if no
                revisions exist.

        Example:
            >>> latest = item.get_latest_revision()
            >>> if latest:
            ...     print(f"Latest: v{latest.number}")
        """
        revisions = self.get_revisions()
        if not revisions:
            return None
        # Find the revision with latest=True, or fallback to highest number
        latest_revisions = [v for v in revisions if hasattr(v, 'latest') and v.latest]
        if latest_revisions:
            return latest_revisions[0]
        return max(revisions, key=lambda v: v.number)

    def get_space(self) -> 'Space':
        """Get the space that contains this item.

        Returns:
            Space: The parent Space object.

        Example:
            >>> item = kumiho.get_item("kref://project/chars/hero.model")
            >>> space = item.get_space()
            >>> print(space.path)  # "/project/chars"
        """
        space_segment = self.kref.get_space()
        if space_segment:
            # Item is in a nested space: kref://project/space/item.kind
            space_path = f"/{self.kref.get_project()}/{space_segment}"
        else:
            # Item is in project root space: kref://project/item.kind
            space_path = f"/{self.kref.get_project()}"
        return self._client.get_space(space_path)

    def get_project(self) -> 'Project':
        """Get the project that contains this item.

        Returns:
            Project: The parent Project object.

        Example:
            >>> project = item.get_project()
            >>> print(project.name)
        """
        return self.get_space().get_project()

    def get_revision_by_tag(self, tag: str) -> Optional[Revision]:
        """Get a revision by its tag.

        Common tags include "latest", "published", "approved", etc.
        Custom tags can be applied to revisions using :meth:`Revision.tag`.

        Args:
            tag: The tag to search for.

        Returns:
            Optional[Revision]: The Revision object if found, None otherwise.

        Example:
            >>> approved = item.get_revision_by_tag("approved")
            >>> published = item.get_revision_by_tag("published")
        """
        request = ResolveKrefRequest(kref=self.kref.uri, tag=tag)
        try:
            response = self._client.stub.ResolveKref(request)
            return Revision(response, self._client)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise

    def get_revision_by_time(
        self,
        time: Union[str, datetime],
        tag: Optional[str] = None
    ) -> Optional[Revision]:
        """Get the revision that had a specific tag at a given time.

        This is essential for reproducible builds and historical queries.
        By combining a tag (like "published") with a timestamp, you can
        answer questions like "What was the published version on June 1st?"

        Args:
            time: The time as a datetime object, or a string in either
                YYYYMMDDHHMM format (e.g., "202312251430") or RFC3339
                format (e.g., "2023-12-25T14:30:00Z").
            tag: Optional tag to filter by. Common values:
                - "published": Find the published revision at that time
                - "approved": Find the approved revision at that time
                - None (default): Find the latest revision at that time

        Returns:
            Optional[Revision]: The Revision that had the specified tag
                at that time, or None if not found.

        Example:
            >>> from datetime import datetime, timezone

            >>> # Get the published revision as of June 1st, 2024
            >>> june_1 = datetime(2024, 6, 1, tzinfo=timezone.utc)
            >>> rev = item.get_revision_by_time(june_1, tag="published")

            >>> # Get whatever was latest at a specific time
            >>> rev = item.get_revision_by_time("202312251430")

            >>> # Using RFC3339 format with published tag
            >>> rev = item.get_revision_by_time(
            ...     "2024-06-01T00:00:00Z",
            ...     tag="published"
            ... )

        Note:
            This is particularly useful with the "published" tag since
            published revisions are immutable and represent stable,
            approved versions suitable for downstream consumption.
        """
        if isinstance(time, datetime):
            # Send full ISO timestamp for sub-minute precision
            time_str = time.isoformat()
        elif isinstance(time, str):
            # Check if it's RFC3339/ISO format (contains T)
            if 'T' in time:
                # Already in ISO format, pass through
                time_str = time
            else:
                # Assume it's in YYYYMMDDHHMM format, convert to ISO
                # This preserves backward compatibility
                if len(time) >= 12:
                    time_str = f"{time[0:4]}-{time[4:6]}-{time[6:8]}T{time[8:10]}:{time[10:12]}:59+00:00"
                else:
                    time_str = time
        else:
            raise ValueError("time must be a datetime object or string")

        request = ResolveKrefRequest(kref=self.kref.uri, time=time_str)
        if tag:
            request = ResolveKrefRequest(kref=self.kref.uri, time=time_str, tag=tag)

        try:
            response = self._client.stub.ResolveKref(request)
            return Revision(response, self._client)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            raise

    def peek_next_revision(self) -> int:
        """Get the next revision number that would be assigned.

        This is useful for previewing revision numbers before creating
        revisions, such as for naming files or planning workflows.

        Returns:
            int: The next revision number.

        Example:
            >>> next_num = item.peek_next_revision()
            >>> print(f"Next revision will be v{next_num}")
        """
        return self._client.peek_next_revision(self.kref)

    def set_metadata(self, metadata: Dict[str, str]) -> 'Item':
        """Set or update metadata for this item.

        Metadata is merged with existing metadata—existing keys are
        overwritten and new keys are added.

        Args:
            metadata: Dictionary of metadata key-value pairs.

        Returns:
            Item: The updated Item object.

        Example:
            >>> item.set_metadata({
            ...     "status": "final",
            ...     "department": "modeling",
            ...     "complexity": "high"
            ... })
        """
        return self._client.update_item_metadata(self.kref, metadata)

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
            >>> item.set_attribute("status", "final")
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
            >>> item.get_attribute("status")
            "final"
        """
        return self._client.get_attribute(self.kref, key)

    def delete_attribute(self, key: str) -> bool:
        """Delete a single metadata attribute.

        Args:
            key: The attribute key to delete.

        Returns:
            bool: True if the attribute was deleted successfully.

        Example:
            >>> item.delete_attribute("old_field")
            True
        """
        result = self._client.delete_attribute(self.kref, key)
        if result and key in self.metadata:
            del self.metadata[key]
        return result

    def delete(self, force: bool = False) -> None:
        """Delete this item.

        Args:
            force: If True, permanently delete the item and all its
                revisions. If False (default), deletion may fail if the
                item has revisions.

        Raises:
            grpc.RpcError: If deletion fails.

        Example:
            >>> # Delete item (fails if has revisions)
            >>> item.delete()

            >>> # Force delete with all revisions
            >>> item.delete(force=True)
        """
        self._client.delete_item(self.kref, force)

    def set_deprecated(self, status: bool) -> None:
        """Set the deprecated status of this item.

        Deprecated items are hidden from default searches but remain
        accessible for historical reference.

        Args:
            status: True to deprecate, False to restore.

        Example:
            >>> item.set_deprecated(True)  # Hide from searches
            >>> item.set_deprecated(False)  # Restore visibility
        """
        self._client.set_deprecated(self.kref, status)
        self.deprecated = status
