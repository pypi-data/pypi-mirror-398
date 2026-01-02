"""Artifact module for Kumiho asset management.

This module provides the :class:`Artifact` class, which represents a file
reference within a revision. Artifacts are the leaf nodes of the Kumiho
hierarchy and point to actual files on local or network storage.

Kumiho follows a "BYO Storage" (Bring Your Own Storage) philosophy—it tracks
file paths and metadata but does not upload or copy files.

Example:
    Working with artifacts::

        import kumiho

        # Get an artifact
        artifact = kumiho.get_artifact(
            "kref://project/models/hero.model?r=1&a=mesh"
        )

        # Check the file location
        print(f"File: {artifact.location}")

        # Set metadata
        artifact.set_metadata({
            "file_size": "125MB",
            "format": "FBX",
            "triangles": "2.5M"
        })

        # Navigate to parent objects
        revision = artifact.get_revision()
        item = artifact.get_item()
"""

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

from .base import KumihoObject
from .kref import Kref
from .proto.kumiho_pb2 import ArtifactResponse

if TYPE_CHECKING:
    from .client import _Client
    from .revision import Revision
    from .item import Item
    from .space import Space
    from .project import Project


class Artifact(KumihoObject):
    """A file reference within a revision in the Kumiho system.

    Artifacts are the leaf nodes of the Kumiho hierarchy. They point to
    actual files on local disk, network storage, or cloud URIs. Kumiho
    tracks the path and metadata but does not upload or modify the files.

    The artifact's kref includes both revision and artifact name:
    ``kref://project/space/item.kind?r=1&a=artifact_name``

    Attributes:
        kref (Kref): The unique reference URI for this artifact.
        location (str): The file path or URI where the artifact is stored.
        revision_kref (Kref): Reference to the parent revision.
        item_kref (Optional[Kref]): Reference to the parent item.
        created_at (Optional[str]): ISO timestamp when the artifact was created.
        author (str): The user ID who created the artifact.
        metadata (Dict[str, str]): Custom metadata key-value pairs.
        deprecated (bool): Whether the artifact is deprecated.
        username (str): Display name of the creator.

    Example:
        Working with artifacts::

            import kumiho

            revision = kumiho.get_revision("kref://project/models/hero.model?r=1")

            # Create artifacts
            mesh = revision.create_artifact("mesh", "/assets/hero.fbx")
            rig = revision.create_artifact("rig", "/assets/hero_rig.fbx")
            textures = revision.create_artifact("textures", "smb://server/tex/hero/")

            # Set metadata
            mesh.set_metadata({
                "triangles": "2.5M",
                "format": "FBX 2020",
                "units": "centimeters"
            })

            # Set as default artifact
            mesh.set_default()

            # Get artifact by name
            retrieved = revision.get_artifact("mesh")
            print(f"Location: {retrieved.location}")

            # Navigate hierarchy
            item = mesh.get_item()
            project = mesh.get_project()
    """

    def __init__(self, pb_artifact: ArtifactResponse, client: '_Client') -> None:
        """Initialize an Artifact from a protobuf response.

        Args:
            pb_artifact: The protobuf ArtifactResponse message.
            client: The client instance for making API calls.
        """
        super().__init__(client)
        self.kref = Kref(pb_artifact.kref.uri)
        self.location = pb_artifact.location
        self.revision_kref = Kref(pb_artifact.revision_kref.uri)
        self.item_kref = (
            Kref(pb_artifact.item_kref.uri)
            if pb_artifact.HasField('item_kref') else None
        )
        self.created_at = pb_artifact.created_at or None
        self.author = pb_artifact.author
        self.metadata = dict(pb_artifact.metadata)
        self.deprecated = pb_artifact.deprecated
        self.username = pb_artifact.username

    def __repr__(self) -> str:
        """Return a string representation of the Artifact."""
        return f"<Artifact kref='{self.kref.uri}'>"

    @property
    def name(self) -> str:
        """Get the artifact name from its kref.

        Returns:
            str: The artifact name extracted from the kref URI.

        Example:
            >>> artifact = revision.get_artifact("mesh")
            >>> print(artifact.name)  # "mesh"
        """
        return self.kref.uri.split('&a=')[-1]

    def set_metadata(self, metadata: Dict[str, str]) -> 'Artifact':
        """Set or update metadata for this artifact.

        Metadata is merged with existing metadata—existing keys are
        overwritten and new keys are added.

        Args:
            metadata: Dictionary of metadata key-value pairs.

        Returns:
            Artifact: The updated Artifact object.

        Example:
            >>> artifact.set_metadata({
            ...     "file_size": "125MB",
            ...     "format": "FBX 2020",
            ...     "triangles": "2.5M",
            ...     "software": "Maya 2024"
            ... })
        """
        return self._client.update_artifact_metadata(self.kref, metadata)

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
            >>> artifact.set_attribute("file_size", "125MB")
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
            >>> artifact.get_attribute("file_size")
            "125MB"
        """
        return self._client.get_attribute(self.kref, key)

    def delete_attribute(self, key: str) -> bool:
        """Delete a single metadata attribute.

        Args:
            key: The attribute key to delete.

        Returns:
            bool: True if the attribute was deleted successfully.

        Example:
            >>> artifact.delete_attribute("old_field")
            True
        """
        result = self._client.delete_attribute(self.kref, key)
        if result and key in self.metadata:
            del self.metadata[key]
        return result

    def delete(self, force: bool = False) -> None:
        """Delete this artifact.

        Args:
            force: If True, force deletion. If False (default), normal
                deletion rules apply.

        Raises:
            grpc.RpcError: If deletion fails.

        Example:
            >>> artifact.delete()
        """
        self._client.delete_artifact(self.kref, force)

    def set_deprecated(self, status: bool) -> None:
        """Set the deprecated status of this artifact.

        Deprecated artifacts are hidden from default queries but remain
        accessible for historical reference.

        Args:
            status: True to deprecate, False to restore.

        Example:
            >>> artifact.set_deprecated(True)  # Hide from queries
            >>> artifact.set_deprecated(False)  # Restore visibility
        """
        self._client.set_deprecated(self.kref, status)
        self.deprecated = status

    def set_default(self) -> None:
        """Set this artifact as the default for its revision.

        The default artifact is used when resolving the revision's kref
        without specifying an artifact name.

        Example:
            >>> mesh = revision.create_artifact("mesh", "/assets/model.fbx")
            >>> mesh.set_default()
            >>> # Now resolving the revision kref returns this artifact's location
        """
        self.get_revision().set_default_artifact(self.name)

    def get_revision(self) -> 'Revision':
        """Get the parent revision of this artifact.

        Returns:
            Revision: The Revision object that contains this artifact.

        Example:
            >>> revision = artifact.get_revision()
            >>> print(f"Revision {revision.number}")
        """
        return self._client.get_revision(self.revision_kref.uri)

    def get_item(self) -> 'Item':
        """Get the item that contains this artifact.

        Returns:
            Item: The Item object.

        Example:
            >>> item = artifact.get_item()
            >>> print(item.item_name)
        """
        if self.item_kref:
            return self._client.get_item_by_kref(self.item_kref.uri)
        # Fallback via revision
        return self.get_revision().get_item()

    def get_space(self) -> 'Space':
        """Get the space containing this artifact's item.

        Returns:
            Space: The Space object.

        Example:
            >>> space = artifact.get_space()
            >>> print(space.path)
        """
        return self.get_item().get_space()

    def get_project(self) -> 'Project':
        """Get the project containing this artifact.

        Returns:
            Project: The Project object.

        Example:
            >>> project = artifact.get_project()
            >>> print(project.name)
        """
        return self.get_space().get_project()