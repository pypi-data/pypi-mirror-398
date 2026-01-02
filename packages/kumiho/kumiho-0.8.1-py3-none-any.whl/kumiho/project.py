"""Project module for Kumiho asset management.

This module provides the :class:`Project` class, which represents the top-level
container for organizing assets in Kumiho. Projects serve as namespaces that
contain spaces, items, revisions, and artifacts.

Example:
    Creating and working with projects::

        import kumiho

        # Create a new project
        project = kumiho.create_project("film-2024", "Feature film VFX assets")

        # Create space structure
        chars = project.create_space("characters")
        envs = project.create_space("environments")

        # Create items within spaces
        hero = chars.create_item("hero", "model")

        # List all spaces
        for space in project.get_spaces(recursive=True):
            print(space.path)
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from .base import KumihoObject
from .space import Space
from .proto.kumiho_pb2 import ProjectResponse

if TYPE_CHECKING:
    from .client import _Client
    from .bundle import Bundle
    from .item import Item


class Project(KumihoObject):
    """A Kumiho project—the top-level container for assets.

    Projects are the root of the Kumiho hierarchy. Each project has its own
    namespace for spaces and items, and manages access control and settings
    independently.

    Projects support both public and private access modes, allowing you to
    share assets publicly or restrict them to authenticated users.

    Attributes:
        project_id (str): The unique identifier for this project.
        name (str): The URL-safe name of the project (e.g., "film-2024").
        description (str): Human-readable description of the project.
        created_at (Optional[str]): ISO timestamp when the project was created.
        updated_at (Optional[str]): ISO timestamp of the last update.
        deprecated (bool): Whether the project is deprecated (soft-deleted).
        allow_public (bool): Whether anonymous read access is enabled.

    Example:
        Basic project operations::

            import kumiho

            # Get existing project
            project = kumiho.get_project("my-project")

            # Create spaces
            assets = project.create_space("assets")
            shots = project.create_space("shots")

            # Navigate to nested spaces
            char_space = project.get_space("assets/characters")

            # List all spaces recursively
            for space in project.get_spaces(recursive=True):
                print(f"  {space.path}")

            # Update project settings
            project.set_public(True)  # Enable public access
            project.update(description="Updated description")

            # Soft delete (deprecate)
            project.delete()

            # Hard delete (permanent)
            project.delete(force=True)
    """

    def __init__(self, pb: ProjectResponse, client: "_Client") -> None:
        """Initialize a Project from a protobuf response.

        Args:
            pb: The protobuf ProjectResponse message.
            client: The client instance for making API calls.
        """
        super().__init__(client)
        self.project_id = pb.project_id
        self.name = pb.name
        self.description = pb.description
        self.created_at = pb.created_at or None
        self.updated_at = pb.updated_at or None
        self.deprecated = pb.deprecated
        self.allow_public = pb.allow_public

    def __repr__(self) -> str:
        """Return a string representation of the Project."""
        return f"<kumiho.Project id='{self.project_id}' name='{self.name}'>"

    def create_space(self, name: str, parent_path: Optional[str] = None) -> Space:
        """Create a space within this project.

        Args:
            name: The name of the space to create.
            parent_path: Optional parent path. If not provided, creates
                the space at the project root (e.g., "/project-name").

        Returns:
            Space: The newly created Space object.

        Example:
            >>> project = kumiho.get_project("film-2024")
            >>> # Create at root
            >>> chars = project.create_space("characters")
            >>> # Create nested space
            >>> heroes = project.create_space("heroes", parent_path="/film-2024/characters")
        """
        base_parent = parent_path or f"/{self.name}"
        return self._client.create_space(parent_path=base_parent, space_name=name)

    def create_bundle(
        self,
        bundle_name: str,
        parent_path: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> 'Bundle':
        """Create a new bundle within this project.

        Bundles are special items that aggregate other items.
        They provide a way to group related items together and maintain
        an audit trail of membership changes through revision history.

        Args:
            bundle_name: The name of the bundle. Must be unique within
                the parent space.
            parent_path: Optional parent path for the bundle. If not provided,
                creates the bundle at the project root (``/{project_name}``).
            metadata: Optional key-value metadata for the bundle.

        Returns:
            Bundle: The newly created Bundle object with kind "bundle".

        Raises:
            grpc.RpcError: If the bundle name is already taken or if there
                is a connection error.

        See Also:
            :class:`~kumiho.bundle.Bundle`: The Bundle class.
            :meth:`~kumiho.space.Space.create_bundle`: Create bundle in a space.

        Example::

            >>> project = kumiho.get_project("film-2024")
            >>> # Create at project root
            >>> bundle = project.create_bundle("release-bundle")
            >>>
            >>> # Create in specific space
            >>> bundle = project.create_bundle(
            ...     "character-bundle",
            ...     parent_path="/film-2024/assets"
            ... )
            >>>
            >>> # Add items to the bundle
            >>> hero = project.get_space("models").get_item("hero", "model")
            >>> bundle.add_member(hero)
        """
        base_parent = parent_path or f"/{self.name}"
        return self._client.create_bundle(
            parent_path=base_parent,
            bundle_name=bundle_name,
            metadata=metadata
        )

    def create_item(
        self,
        item_name: str,
        kind: str,
        parent_path: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> 'Item':
        """Create a new item within this project.

        Args:
            item_name: The name of the item. Must be unique within
                the parent space combined with the kind.
            kind: The type/kind of the item (e.g., "model", "texture").
            parent_path: Optional parent path for the item. If not provided,
                creates the item at the project root (``/{project_name}``).
            metadata: Optional key-value metadata for the item.

        Returns:
            Item: The newly created Item object.

        Raises:
            grpc.RpcError: If the item name/kind combination is already taken
                or if there is a connection error.

        Example::

            >>> project = kumiho.get_project("film-2024")
            >>> # Create at project root
            >>> item = project.create_item("hero", "model")
            >>>
            >>> # Create in specific space
            >>> item = project.create_item(
            ...     "hero",
            ...     "texture",
            ...     parent_path="/film-2024/assets"
            ... )
        """
        base_parent = parent_path or f"/{self.name}"
        return self._client.create_item(
            parent_path=base_parent,
            item_name=item_name,
            kind=kind,
            metadata=metadata
        )

    def get_item(
        self,
        item_name: str,
        kind: str,
        parent_path: Optional[str] = None
    ) -> 'Item':
        """Get an existing item within this project.

        Args:
            item_name: The name of the item.
            kind: The type/kind of the item (e.g., "model", "texture").
            parent_path: Optional parent path. If not provided,
                looks in the project root (``/{project_name}``).

        Returns:
            Item: The Item object.

        Raises:
            grpc.RpcError: If the item is not found.

        Example::

            >>> project = kumiho.get_project("film-2024")
            >>> # Get from project root
            >>> item = project.get_item("hero", "model")
            >>>
            >>> # Get from specific space
            >>> item = project.get_item(
            ...     "hero",
            ...     "texture",
            ...     parent_path="/film-2024/assets"
            ... )
        """
        base_parent = parent_path or f"/{self.name}"
        kref_uri = f"kref://{base_parent.strip('/')}/{item_name}.{kind}"
        return self._client.get_item_by_kref(kref_uri)

    def get_bundle(
        self,
        bundle_name: str,
        parent_path: Optional[str] = None
    ) -> 'Bundle':
        """Get an existing bundle within this project.

        Args:
            bundle_name: The name of the bundle.
            parent_path: Optional parent path. If not provided,
                looks in the project root (``/{project_name}``).

        Returns:
            Bundle: The Bundle object.

        Raises:
            ValueError: If the item exists but is not a bundle.
            grpc.RpcError: If the bundle is not found.

        Example::

            >>> project = kumiho.get_project("film-2024")
            >>> # Get from project root
            >>> bundle = project.get_bundle("release-bundle")
            >>>
            >>> # Get from specific space
            >>> bundle = project.get_bundle(
            ...     "character-bundle",
            ...     parent_path="/film-2024/assets"
            ... )
            >>> members = bundle.get_members()
        """
        base_parent = parent_path or f"/{self.name}"
        kref_uri = f"kref://{base_parent.strip('/')}/{bundle_name}.bundle"
        return self._client.get_bundle_by_kref(kref_uri)

    def delete(self, force: bool = False):
        """Delete or deprecate this project.

        Args:
            force: If True, permanently delete the project and all its
                contents. If False (default), mark as deprecated.

        Returns:
            StatusResponse: Response indicating success or failure.

        Warning:
            Force deletion is irreversible and removes all spaces, items,
            revisions, artifacts, and edges within the project.

        Example:
            >>> project = kumiho.get_project("old-project")
            >>> # Soft delete (can be recovered)
            >>> project.delete()
            >>> # Hard delete (permanent)
            >>> project.delete(force=True)
        """
        return self._client.delete_project(project_id=self.project_id, force=force)

    def set_public(self, public: bool):
        """Set whether this project allows anonymous read access.

        Args:
            public: True to enable public access, False to require
                authentication for all access.

        Returns:
            Project: The updated Project object.

        Example:
            >>> project.set_public(True)  # Enable public access
            >>> project.set_public(False)  # Require authentication
        """
        return self._client.update_project(project_id=self.project_id, allow_public=public)

    def update(
        self,
        description: Optional[str] = None,
        allow_public: Optional[bool] = None
    ):
        """Update project properties.

        Args:
            description: New description for the project.
            allow_public: New public access setting.

        Returns:
            Project: The updated Project object.

        Example:
            >>> project.update(
            ...     description="Updated project description",
            ...     allow_public=True
            ... )
        """
        return self._client.update_project(
            project_id=self.project_id,
            description=description,
            allow_public=allow_public
        )

    def get_space(self, name: str, parent_path: Optional[str] = None) -> Space:
        """Get an existing space within this project.

        Args:
            name: The name of the space, or an absolute path starting with "/".
            parent_path: Optional parent path if name is a relative name.

        Returns:
            Space: The Space object.

        Raises:
            grpc.RpcError: If the space is not found.

        Example:
            >>> # Get by absolute path
            >>> space = project.get_space("/film-2024/characters")

            >>> # Get by relative name (from project root)
            >>> space = project.get_space("characters")

            >>> # Get nested space with parent path
            >>> heroes = project.get_space("heroes", parent_path="/film-2024/characters")
        """
        if name.startswith("/"):
            path = name
        else:
            base_parent = parent_path or f"/{self.name}"
            path = f"{base_parent.rstrip('/')}/{name}"
        return self._client.get_space(path)

    def get_spaces(
        self,
        parent_path: Optional[str] = None,
        recursive: bool = False
    ) -> List[Space]:
        """List spaces within this project.

        Args:
            parent_path: Optional path to start from. Defaults to project root.
            recursive: If True, include all nested spaces. If False (default),
                only direct children.

        Returns:
            List[Space]: A list of Space objects.

        Example:
            >>> # List direct children only
            >>> spaces = project.get_spaces()
            >>> for s in spaces:
            ...     print(s.name)

            >>> # List all spaces recursively
            >>> all_spaces = project.get_spaces(recursive=True)
            >>> for s in all_spaces:
            ...     print(s.path)
        """
        base_parent = parent_path or f"/{self.name}"
        return self._client.get_child_spaces(base_parent, recursive=recursive)

    def get_items(
        self,
        name_filter: str = "",
        kind_filter: str = "",
        page_size: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> List['Item']:
        """Search for items within this project.

        Args:
            name_filter: Filter by item name. Supports wildcards.
            kind_filter: Filter by item kind.
            page_size: Optional page size for pagination.
            cursor: Optional cursor for pagination.

        Returns:
            List[Item]: A list of Item objects matching the filters.
            If pagination is used, returns a PagedList with next_cursor.

        Example:
            >>> # All items in project
            >>> items = project.get_items()

            >>> # Only models
            >>> models = project.get_items(kind_filter="model")

            >>> # Pagination
            >>> page1 = project.get_items(page_size=10)
            >>> if page1.next_cursor:
            ...     page2 = project.get_items(page_size=10, cursor=page1.next_cursor)
        """
        return self._client.item_search(
            context_filter=self.name,
            item_name_filter=name_filter,
            kind_filter=kind_filter,
            page_size=page_size,
            cursor=cursor
        )
