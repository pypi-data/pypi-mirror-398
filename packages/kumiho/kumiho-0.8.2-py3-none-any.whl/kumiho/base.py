"""Base classes and utilities for Kumiho objects.

This module provides the base classes used by all Kumiho domain objects,
including :class:`KumihoObject` (the base for all high-level objects) and
:class:`KumihoError` (the base exception class).
"""

from typing import TYPE_CHECKING, TypeVar, List, Optional

if TYPE_CHECKING:
    from .client import _Client

T = TypeVar('T')


class PagedList(List[T]):
    """A list that also contains pagination information.

    Attributes:
        next_cursor (Optional[str]): The cursor for the next page of results.
        total_count (Optional[int]): The total number of items available.
    """
    def __init__(self, items: List[T], next_cursor: Optional[str] = None, total_count: Optional[int] = None):
        super().__init__(items)
        self.next_cursor = next_cursor
        self.total_count = total_count


class KumihoError(Exception):
    """Base exception class for all Kumiho errors.

    All custom exceptions raised by the Kumiho SDK inherit from this class,
    making it easy to catch all Kumiho-related errors.

    Example::

        import kumiho

        try:
            project = kumiho.get_project("nonexistent")
        except kumiho.KumihoError as e:
            print(f"Kumiho error: {e}")
    """


class KumihoObject:
    """Base class for all high-level Kumiho domain objects.

    This abstract base class provides common functionality shared by all
    Kumiho objects, including access to the client for making API calls.

    All domain objects (:class:`Project`, :class:`Space`, :class:`Item`,
    :class:`Revision`, :class:`Artifact`, :class:`Edge`) inherit from this class.

    Attributes:
        _client: The client instance for making API calls (internal).

    Note:
        This is an internal base class. Users typically interact with
        concrete subclasses like :class:`Project` or :class:`Version`.
    """

    def __init__(self, client: '_Client') -> None:
        """Initialize the Kumiho object with a client reference.

        Args:
            client: The client instance for making API calls.
        """
        self._client = client

