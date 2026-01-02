"""Event module for Kumiho real-time notifications.

This module provides the :class:`Event` class for handling real-time
notifications from the Kumiho server. Events are streamed as changes
occur in the database.

Event Types (routing_key patterns):
    - ``project.created``, ``project.deleted``
    - ``space.created``, ``space.deleted``
    - ``item.created``, ``item.deleted``
    - ``revision.created``, ``revision.deleted``
    - ``revision.tagged``, ``revision.untagged``
    - ``artifact.created``, ``artifact.deleted``
    - ``edge.created``, ``edge.deleted``

Cursor-based Resume (Creator tier and above):
    Events include a ``cursor`` field that can be saved and used to resume
    streaming from that point after a disconnection. This prevents missing
    events during network interruptions.

Example::

    import kumiho

    # Subscribe to all revision events in a project
    last_cursor = None
    for event in kumiho.event_stream(
        routing_key_filter="revision.*",
        kref_filter="kref://my-project/**",
        cursor=last_cursor  # Resume from last position
    ):
        print(f"{event.routing_key}: {event.kref}")
        last_cursor = event.cursor  # Save for reconnection

        if event.routing_key == "revision.tagged":
            tag = event.details.get("tag")
            print(f"  Tagged with: {tag}")
"""

from dataclasses import dataclass
from typing import Dict, Optional

from .kref import Kref
from .proto.kumiho_pb2 import Event as PbEvent


@dataclass
class EventCapabilities:
    """Event streaming capabilities for the current tenant tier.
    
    Attributes:
        supports_replay: Whether this tier supports replaying past events.
        supports_cursor: Whether cursor-based resume is supported.
        supports_consumer_groups: Whether consumer groups are supported (Enterprise only).
        max_retention_hours: Maximum event retention in hours (0 = none, -1 = unlimited).
        max_buffer_size: Maximum events in buffer (0 = none, -1 = unlimited).
        tier: Tier identifier (free, creator, studio, enterprise).
    """
    supports_replay: bool
    supports_cursor: bool
    supports_consumer_groups: bool
    max_retention_hours: int
    max_buffer_size: int
    tier: str


class Event:
    """A real-time notification from the Kumiho server.

    Events represent changes or actions that occurred in the Kumiho system,
    such as creating versions, applying tags, or deleting resources. Use
    :func:`kumiho.event_stream` to subscribe to events.

    Attributes:
        routing_key (str): The event type identifier (e.g., "version.created",
            "version.tagged"). Use wildcards in filters to match patterns.
        kref (Kref): Reference to the affected object.
        timestamp (Optional[str]): ISO timestamp when the event occurred.
        author (str): The user ID who triggered the event.
        details (Dict[str, str]): Additional event-specific information
            (e.g., tag name for tagged events).
        cursor (Optional[str]): Opaque cursor for resumable streaming.
            Save this value and pass it to ``event_stream(cursor=...)`` to
            resume from this event after reconnection. Only available on
            Creator tier and above.

    Example::

        import kumiho

        # React to revision creation with cursor tracking
        last_cursor = None
        try:
            for event in kumiho.event_stream(
                routing_key_filter="revision.created",
                cursor=last_cursor
            ):
                revision = kumiho.get_revision(event.kref)
                print(f"New revision: {revision.item_kref} v{revision.number}")
                print(f"  Created by: {event.author}")
                print(f"  At: {event.timestamp}")
                last_cursor = event.cursor  # Save cursor
        except ConnectionError:
            # Reconnect using saved cursor
            pass

        # Filter by kref pattern
        for event in kumiho.event_stream(
            routing_key_filter="*",
            kref_filter="kref://production-project/**"
        ):
            print(f"Production change: {event.routing_key}")
    """

    def __init__(self, pb_event: PbEvent) -> None:
        """Initialize an Event from a protobuf message.

        Args:
            pb_event: The protobuf Event message from the server.
        """
        self.routing_key = pb_event.routing_key
        self.kref = Kref(pb_event.kref.uri)
        self.timestamp = pb_event.timestamp or None
        self.author = pb_event.author
        self.details = dict(pb_event.details)
        self.cursor: Optional[str] = pb_event.cursor if pb_event.cursor else None

    def __repr__(self) -> str:
        """Return a string representation of the Event."""
        return f"<Event key='{self.routing_key}' kref='{self.kref.uri}' cursor={self.cursor!r}>"
