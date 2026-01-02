"""Space module for Kumiho asset management.

This module provides the :class:`Space` class, which represents hierarchical
containers for organizing items within a project. Spaces form the folder
structure of the Kumiho asset hierarchy.

Example:
    Working with spaces::

        import kumiho

        project = kumiho.get_project("film-2024")

        # Create space hierarchy
        chars = project.create_space("characters")
        heroes = chars.create_space("heroes")
        villains = chars.create_space("villains")

        # Create items in spaces
        hero_model = heroes.create_item("main-hero", "model")

        # Navigate space hierarchy
        parent = heroes.get_parent_space()  # Returns chars
        children = chars.get_child_spaces()  # Returns [heroes, villains]
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from .base import KumihoObject
from .bundle import Bundle
from .kref import Kref
from .proto.kumiho_pb2 import SpaceResponse
from .item import Item

if TYPE_CHECKING:
    from .client import _Client
    from .bundle import Bundle
    from .project import Project


class Space(KumihoObject):
    """A hierarchical container for organizing items in Kumiho.

    Spaces form the folder structure within a project. They can contain
    other spaces (subspaces) and items, allowing you to organize assets
    in a meaningful hierarchy.

    Spaces are identified by their full path (e.g., "/project/characters/heroes")
    and can store custom metadata.

    Attributes:
        path (str): The full path of the space (e.g., "/project/assets").
        name (str): The name of this space (last component of path).
        type (str): The type of space ("root" for project-level, "sub" for nested).
        created_at (Optional[str]): ISO timestamp when the space was created.
        author (str): The user ID who created the space.
        metadata (Dict[str, str]): Custom metadata key-value pairs.
        username (str): Display name of the creator.

    Example:
        Creating and navigating spaces::

            import kumiho

            project = kumiho.get_project("my-project")

            # Create a space
            assets = project.create_space("assets")

            # Create subspaces
            models = assets.create_space("models")
            textures = assets.create_space("textures")

            # Create items
            chair = models.create_item("chair", "model")

            # List items with filters
            all_models = models.get_items()
            wood_textures = textures.get_items(name_filter="wood*")

            # Navigate hierarchy
            parent = models.get_parent_space()  # Returns assets
            project = models.get_project()  # Returns my-project
    """

    def __init__(self, pb_space: SpaceResponse, client: '_Client') -> None:
        """Initialize a Space from a protobuf response.

        Args:
            pb_space: The protobuf SpaceResponse message.
            client: The client instance for making API calls.
        """
        super().__init__(client)
        self.path = pb_space.path
        self.name = pb_space.name
        self.type = pb_space.type
        self.created_at = pb_space.created_at or None
        self.author = pb_space.author
        self.metadata = dict(pb_space.metadata)
        self.username = pb_space.username

    def __repr__(self) -> str:
        """Return a string representation of the Space."""
        return f"<kumiho.Space path='{self.path}'>"

    def create_space(self, name: str) -> 'Space':
        """Create a new subspace within this space.

        Args:
            name: The name of the new subspace.

        Returns:
            Space: The newly created Space object.

        Example:
            >>> assets = project.create_space("assets")
            >>> models = assets.create_space("models")
            >>> textures = assets.create_space("textures")
        """
        return self._client.create_space(parent_path=self.path, space_name=name)

    def get_space(self, name: str) -> 'Space':
        """Get an existing subspace by name.

        Args:
            name: The name of the subspace (not full path).

        Returns:
            Space: The Space object.

        Raises:
            grpc.RpcError: If the space is not found.

        Example:
            >>> assets = project.get_space("assets")
            >>> models = assets.get_space("models")
        """
        path = f"{self.path.rstrip('/')}/{name}"
        return self._client.get_space(path)

    def get_spaces(self, recursive: bool = False) -> List['Space']:
        """List child spaces under this space.

        Args:
            recursive: If True, include all nested spaces. If False (default),
                only direct children.

        Returns:
            List[Space]: A list of Space objects.

        Example:
            >>> # Direct children only
            >>> children = space.get_spaces()

            >>> # All nested spaces
            >>> all_spaces = space.get_spaces(recursive=True)
        """
        return self._client.get_child_spaces(self.path, recursive=recursive)

    def create_item(self, item_name: str, kind: str) -> Item:
        """Create a new item within this space.

        Items are versioned assets that can contain multiple artifacts.
        The combination of name and kind must be unique within the space.

        Args:
            item_name: The name of the item (e.g., "hero-character").
            kind: The kind of item (e.g., "model", "texture", "workflow").

        Returns:
            Item: The newly created Item object.

        Example:
            >>> models = project.get_space("models")
            >>> chair = models.create_item("office-chair", "model")
            >>> wood = textures.create_item("oak-wood", "texture")
        """
        return self._client.create_item(self.path, item_name, kind)

    def create_bundle(
        self,
        bundle_name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Bundle:
        """Create a new bundle within this space.

        Bundles are special items that aggregate other items.
        They provide a way to group related items together and maintain
        an audit trail of membership changes through revision history.

        Args:
            bundle_name: The name of the bundle. Must be unique within
                the space.
            metadata: Optional key-value metadata for the bundle.

        Returns:
            Bundle: The newly created Bundle object with kind "bundle".

        Raises:
            grpc.RpcError: If the bundle name is already taken or if there
                is a connection error.

        See Also:
            :class:`~kumiho.bundle.Bundle`: The Bundle class.
            :meth:`~kumiho.project.Project.create_bundle`: Create bundle in a project.

        Example::

            >>> # Create a bundle for a character bundle
            >>> assets = project.get_space("assets")
            >>> bundle = assets.create_bundle("character-bundle")
            >>>
            >>> # Add items to the bundle
            >>> hero = assets.get_item("hero", "model")
            >>> bundle.add_member(hero)
        """
        return self._client.create_bundle(
            parent_path=self.path,
            bundle_name=bundle_name,
            metadata=metadata
        )

    def get_items(
        self,
        item_name_filter: str = "",
        kind_filter: str = "",
        page_size: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> List[Item]:
        """List items within this space with optional filtering.

        Args:
            item_name_filter: Filter by item name. Supports wildcards.
            kind_filter: Filter by item kind.
            page_size: Optional page size for pagination.
            cursor: Optional cursor for pagination.

        Returns:
            List[Item]: A list of Item objects matching the filters.
            If pagination is used, returns a PagedList with next_cursor.

        Example:
            >>> # All items in space
            >>> items = space.get_items()

            >>> # Only models
            >>> models = space.get_items(kind_filter="model")

            >>> # Items starting with "hero"
            >>> heroes = space.get_items(item_name_filter="hero*")

            >>> # Pagination
            >>> page1 = space.get_items(page_size=10)
            >>> if page1.next_cursor:
            ...     page2 = space.get_items(page_size=10, cursor=page1.next_cursor)
        """
        return self._client.get_items(
            self.path,
            item_name_filter,
            kind_filter,
            page_size=page_size,
            cursor=cursor
        )

    def get_item(self, item_name: str, kind: str) -> Item:
        """Get a specific item by name and kind.

        Args:
            item_name: The name of the item.
            kind: The kind of the item.

        Returns:
            Item: The Item object.

        Raises:
            grpc.RpcError: If the item is not found.

        Example:
            >>> chair = models.get_item("office-chair", "model")
            >>> revisions = chair.get_revisions()
        """
        return self._client.get_item(self.path, item_name, kind)

    def get_bundle(self, bundle_name: str) -> Bundle:
        """Get a bundle by name from this space.

        This is a convenience method that fetches a bundle item and returns
        it as a Bundle object with bundle-specific methods like add_member(),
        get_members(), etc.

        Args:
            bundle_name: The name of the bundle.

        Returns:
            Bundle: The Bundle object.

        Raises:
            grpc.RpcError: If the bundle is not found.

        Example:
            >>> bundle = space.get_bundle("character-bundle")
            >>> members = bundle.get_members()
            >>> for member in members:
            ...     print(member.item_kref)
        """
        # Construct the kref URI for the bundle
        # Space path is like "/project/space", we need "project/space/bundle.bundle"
        path_without_slash = self.path.lstrip("/")
        kref_uri = f"kref://{path_without_slash}/{bundle_name}.bundle"
        return self._client.get_bundle_by_kref(kref_uri)

    def set_metadata(self, metadata: Dict[str, str]) -> 'Space':
        """Set or update metadata for this space.

        Metadata is a dictionary of string key-value pairs that can store
        any custom information about the space.

        Args:
            metadata: Dictionary of metadata to set. Existing keys are
                overwritten, new keys are added.

        Returns:
            Space: The updated Space object.

        Example:
            >>> space.set_metadata({
            ...     "department": "modeling",
            ...     "supervisor": "jane.doe",
            ...     "status": "active"
            ... })
        """
        # For spaces, the server expects the path directly in the kref uri field.
        # We bypass the Kref class validation since paths don't match kref:// format.
        from .proto.kumiho_pb2 import Kref as PbKref, UpdateMetadataRequest
        req = UpdateMetadataRequest(kref=PbKref(uri=self.path), metadata=metadata)
        resp = self._client.stub.UpdateSpaceMetadata(req)
        return Space(resp, self._client)

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
            >>> space.set_attribute("department", "modeling")
            True
        """
        # For spaces, the server expects the path directly in the kref uri field.
        # We bypass the Kref class validation since paths don't match kref:// format.
        from .proto.kumiho_pb2 import Kref as PbKref, SetAttributeRequest
        req = SetAttributeRequest(kref=PbKref(uri=self.path), key=key, value=value)
        resp = self._client.stub.SetAttribute(req)
        if resp.success:
            self.metadata[key] = value
        return resp.success

    def get_attribute(self, key: str) -> Optional[str]:
        """Get a single metadata attribute.

        Args:
            key: The attribute key to retrieve.

        Returns:
            The attribute value if it exists, None otherwise.

        Example:
            >>> space.get_attribute("department")
            "modeling"
        """
        # For spaces, the server expects the path directly in the kref uri field.
        # We bypass the Kref class validation since paths don't match kref:// format.
        from .proto.kumiho_pb2 import Kref as PbKref, GetAttributeRequest
        req = GetAttributeRequest(kref=PbKref(uri=self.path), key=key)
        resp = self._client.stub.GetAttribute(req)
        return resp.value if resp.exists else None

    def delete_attribute(self, key: str) -> bool:
        """Delete a single metadata attribute.

        Args:
            key: The attribute key to delete.

        Returns:
            bool: True if the attribute was deleted successfully.

        Example:
            >>> space.delete_attribute("old_field")
            True
        """
        # For spaces, the server expects the path directly in the kref uri field.
        # We bypass the Kref class validation since paths don't match kref:// format.
        from .proto.kumiho_pb2 import Kref as PbKref, DeleteAttributeRequest
        req = DeleteAttributeRequest(kref=PbKref(uri=self.path), key=key)
        resp = self._client.stub.DeleteAttribute(req)
        if resp.success and key in self.metadata:
            del self.metadata[key]
        return resp.success

    def delete(self, force: bool = False) -> None:
        """Delete this space.

        Args:
            force: If True, force deletion even if the space contains
                items. If False (default), deletion fails if space
                is not empty.

        Raises:
            grpc.RpcError: If deletion fails (e.g., space not empty
                and force=False).

        Example:
            >>> # Delete empty space
            >>> empty_space.delete()

            >>> # Force delete space with contents
            >>> old_space.delete(force=True)
        """
        self._client.delete_space(self.path, force)

    def get_parent_space(self) -> Optional['Space']:
        """Get the parent space of this space.

        Returns:
            Optional[Space]: The parent Space object, or None if this is
                a project-level root space.

        Example:
            >>> heroes = project.get_space("characters/heroes")
            >>> chars = heroes.get_parent_space()  # Returns "characters" space
            >>> root = chars.get_parent_space()  # Returns None (project root)
        """
        if self.path == "/":
            return None
        # Split path and remove the last component
        parts = [p for p in self.path.split('/') if p]  # Remove empty strings
        if len(parts) <= 1:
            return None  # This is a root-level space
        parent_parts = parts[:-1]
        if not parent_parts:
            parent_path = "/"
        else:
            parent_path = "/" + "/".join(parent_parts)
        return self._client.get_space(parent_path)

    def get_child_spaces(self) -> List['Space']:
        """Get immediate child spaces of this space.

        This is a convenience method equivalent to ``get_spaces(recursive=False)``.

        Returns:
            List[Space]: A list of direct child Space objects.

        Example:
            >>> assets = project.get_space("assets")
            >>> children = assets.get_child_spaces()
            >>> for child in children:
            ...     print(child.name)
        """
        return self._client.get_child_spaces(self.path)

    def get_project(self) -> 'Project':
        """Get the project that contains this space.

        Returns:
            Project: The parent Project object.

        Example:
            >>> space = kumiho.get_item("kref://my-project/assets/hero.model").get_space()
            >>> project = space.get_project()
            >>> print(project.name)
            my-project
        """
        # The project name is the first component of the path
        parts = [p for p in self.path.split('/') if p]
        if not parts:
            raise ValueError("Root space has no project")
        project_name = parts[0]
        project = self._client.get_project(project_name)
        if project is None:
            raise ValueError(f"Project '{project_name}' not found")
        return project
