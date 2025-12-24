"""Event registry module for managing protocol events and listeners.

This module provides a centralized registry system for managing protocol events
and their associated handlers and listeners. It enables dynamic registration
and lookup of event handlers based on event identifiers.

The module defines:

    - EventId: Type alias for event identifiers as (major, minor) version tuples
    - EventFn: Type alias for event handler functions that create decoders
    - ListenerFn: Type alias for event listener functions that process events
    - EventRegistry: Generic registry class for managing events and listeners
    - EVENT_REGISTRY_MSB: Global registry instance for MSB-first bit ordering
    - EVENT_REGISTRY_LSB: Global registry instance for LSB-first bit ordering

The registry maintains two separate mappings:
    - events: Maps event IDs to lists of handler functions that create decoders
    - listeners: Maps event IDs to lists of listener functions that process events

This design allows multiple handlers and listeners to be registered for the
same event ID, enabling flexible event processing and response generation.

Example usage:

    >>> from shdp.protocol.managers.registry import (
    ...     EventRegistry, EVENT_REGISTRY_MSB
    ... )
    >>> from shdp.protocol.args import Arg
    >>>
    >>> # Register an event handler
    >>> def handle_login(decoder: BitDecoder) -> LoginEvent:
    ...     return LoginEvent(decoder)
    >>> EVENT_REGISTRY_MSB.add_event((1, 0), handle_login)
    >>>
    >>> # Register an event listener
    >>> def on_login(event: LoginEvent) -> Result[list[Arg], Error]:
    ...     return Result.Ok([Arg(Arg.TEXT, "user123")])
    >>> EVENT_REGISTRY_MSB.add_listener((1, 0), on_login)
    >>>
    >>> # Retrieve handlers and listeners
    >>> handlers = EVENT_REGISTRY_MSB.get_event((1, 0))
    >>> listeners = EVENT_REGISTRY_MSB.get_listeners((1, 0))
"""

from typing import Callable, Generic

from shdp.utils.bitvec import Lsb, Msb, R
from shdp.utils.result import Result
from ..args import Arg
from ..errors import Error
from .bits.decoder import BitDecoder
from .event import EventDecoder

# Type alias for event identifiers as (major, minor) version tuples
EventId = tuple[int, int]

# Type alias for event handler functions
EventFn = Callable[[BitDecoder[R]], EventDecoder[R]]
# Type alias for event listener functions
ListenerFn = Callable[[EventDecoder[R]], Result[list[Arg], Error]]


class EventRegistry(Generic[R]):
    """Registry for managing protocol events and their listeners.

    This class maintains two registries:
    - events: Maps event IDs to their handler functions
    - listeners: Maps event IDs to their listener functions

    Examples:
        >>> registry = EventRegistry()
        >>> event_id = (1, 0)  # v1.0

        # Register an event handler
        >>> def handle_login(decoder: BitDecoder) -> LoginEvent:
        ...     return LoginEvent
        >>> registry.add_event(event_id, handle_login)

        # Register an event listener
        >>> def on_login(event: LoginEvent) -> list[Arg]:
        ...     return [Arg(Arg.TEXT, "user123")]
        >>> registry.add_listener(event_id, on_login)
    """

    events: dict[EventId, list[EventFn]] = {}
    listeners: dict[EventId, list[ListenerFn]] = {}

    def get_event(self, event_id: EventId) -> list[EventFn] | None:
        """Get all event handlers for a specific event ID.

        Args:
            event_id (EventId): The event identifier (major, minor)

        Returns:
            list[EventFn] | None: List of event handlers or None if not found

        Example:
            >>> handlers = registry.get_event((1, 0))
            >>> if handlers:
            ...     for handler in handlers:
            ...         event = handler(decoder)
        """
        return self.events.get(event_id)

    def get_listeners(self, event_id: EventId) -> list[ListenerFn] | None:
        """Get all listeners for a specific event ID.

        Args:
            event_id (EventId): The event identifier (major, minor)

        Returns:
            list[ListenerFn] | None: List of event listeners or None if not found

        Example:
            >>> listeners = registry.get_listeners((1, 0))
            >>> if listeners:
            ...     for listener in listeners:
            ...         args = listener(event)
        """
        return self.listeners.get(event_id)

    def add_event(self, event_id: EventId, event_fn: EventFn) -> None:
        """Register a new event handler for a specific event ID.

        Args:
            event_id (EventId): The event identifier (major, minor)
            event_fn (EventFn): The event handler function

        Example:
            >>> def handle_message(decoder: BitDecoder) -> MessageEvent:
            ...     return MessageEvent
            >>> registry.add_event((1, 0), handle_message)
        """
        self.events.setdefault(event_id, []).append(event_fn)

    def add_listener(self, event_id: EventId, listener_fn: ListenerFn) -> None:
        """Register a new event listener for a specific event ID.

        Args:
            event_id (EventId): The event identifier (major, minor)
            listener_fn (ListenerFn): The listener function

        Example:
            >>> def on_message(event: MessageEvent) -> list[Arg]:
            ...     return [Arg(Arg.TEXT, "Hello!")]
            >>> registry.add_listener((1, 0), on_message)
        """
        self.listeners.setdefault(event_id, []).append(listener_fn)


EVENT_REGISTRY_MSB: EventRegistry[Msb] = EventRegistry[Msb]()
EVENT_REGISTRY_LSB: EventRegistry[Lsb] = EventRegistry[Lsb]()
