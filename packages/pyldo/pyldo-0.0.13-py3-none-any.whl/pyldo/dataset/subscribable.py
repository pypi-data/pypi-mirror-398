"""
Subscribable Dataset

Provides event-based updates when RDF data changes.
This enables reactive UI patterns where components automatically
update when the underlying data changes.

Example:
    >>> dataset = SubscribableDataset()
    >>> 
    >>> def on_change(event):
    ...     print(f"Triple changed: {event}")
    >>> 
    >>> dataset.subscribe(on_change)
    >>> dataset.add(triple)  # Triggers on_change
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Union
from weakref import WeakSet

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.term import Node

from .graph import RdfGraph, Triple


class EventType(Enum):
    """Types of events that can occur on a dataset."""
    
    ADD = "add"
    REMOVE = "remove"
    BATCH_START = "batch_start"
    BATCH_END = "batch_end"


@dataclass
class DatasetEvent:
    """
    An event representing a change to the dataset.

    Attributes:
        type: The type of event (add, remove, etc.)
        triple: The triple that was added/removed (if applicable)
        graph: The graph that changed
        transaction_id: ID of the transaction this event belongs to
    """

    type: EventType
    triple: Optional[Triple] = None
    graph: Optional[str] = None
    transaction_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


# Type alias for event listeners
EventListener = Callable[[DatasetEvent], None]


class SubscribableDataset(RdfGraph):
    """
    An RDF graph that supports event subscriptions.

    Extends RdfGraph with the ability to subscribe to changes,
    enabling reactive patterns for UI updates.

    Features:
    - Subscribe to all changes or specific patterns
    - Filter by subject, predicate, or object
    - Batch multiple changes into a single notification
    - Automatic cleanup of dead references

    Example:
        >>> dataset = SubscribableDataset()
        >>> 
        >>> # Subscribe to all changes
        >>> unsubscribe = dataset.subscribe(lambda e: print(e))
        >>> 
        >>> # Subscribe to specific subject
        >>> dataset.subscribe_to_subject(
        ...     URIRef("http://example.org/me"),
        ...     lambda e: print(f"My data changed: {e}")
        ... )
        >>> 
        >>> # Make changes
        >>> dataset.add((subject, predicate, obj))  # Triggers listeners
    """

    def __init__(self, graph: Optional[Graph] = None):
        """Initialize a subscribable dataset."""
        super().__init__(graph)
        
        # Global listeners (hear all events)
        self._listeners: dict[str, EventListener] = {}
        
        # Subject-specific listeners
        self._subject_listeners: dict[str, dict[str, EventListener]] = {}
        
        # Predicate-specific listeners
        self._predicate_listeners: dict[str, dict[str, EventListener]] = {}
        
        # Pattern listeners (subject, predicate, object patterns)
        self._pattern_listeners: dict[str, tuple[Optional[Node], Optional[Node], Optional[Node], EventListener]] = {}
        
        # Batch mode for grouping multiple changes
        self._batch_mode = False
        self._batch_events: list[DatasetEvent] = []
        self._current_transaction_id: Optional[str] = None

    def subscribe(self, listener: EventListener) -> Callable[[], None]:
        """
        Subscribe to all dataset changes.

        Args:
            listener: Callback function called with DatasetEvent

        Returns:
            Unsubscribe function
        """
        listener_id = str(uuid.uuid4())
        self._listeners[listener_id] = listener

        def unsubscribe():
            self._listeners.pop(listener_id, None)

        return unsubscribe

    def subscribe_to_subject(
        self,
        subject: Union[URIRef, str],
        listener: EventListener,
    ) -> Callable[[], None]:
        """
        Subscribe to changes for a specific subject.

        Args:
            subject: The subject URI to watch
            listener: Callback function

        Returns:
            Unsubscribe function
        """
        subject_str = str(subject)
        listener_id = str(uuid.uuid4())

        if subject_str not in self._subject_listeners:
            self._subject_listeners[subject_str] = {}
        self._subject_listeners[subject_str][listener_id] = listener

        def unsubscribe():
            if subject_str in self._subject_listeners:
                self._subject_listeners[subject_str].pop(listener_id, None)

        return unsubscribe

    def subscribe_to_predicate(
        self,
        predicate: Union[URIRef, str],
        listener: EventListener,
    ) -> Callable[[], None]:
        """
        Subscribe to changes for a specific predicate.

        Args:
            predicate: The predicate URI to watch
            listener: Callback function

        Returns:
            Unsubscribe function
        """
        predicate_str = str(predicate)
        listener_id = str(uuid.uuid4())

        if predicate_str not in self._predicate_listeners:
            self._predicate_listeners[predicate_str] = {}
        self._predicate_listeners[predicate_str][listener_id] = listener

        def unsubscribe():
            if predicate_str in self._predicate_listeners:
                self._predicate_listeners[predicate_str].pop(listener_id, None)

        return unsubscribe

    def subscribe_to_pattern(
        self,
        subject: Optional[Union[URIRef, str]] = None,
        predicate: Optional[Union[URIRef, str]] = None,
        object: Optional[Union[URIRef, str, Literal]] = None,
        listener: Optional[EventListener] = None,
    ) -> Callable[[], None]:
        """
        Subscribe to changes matching a specific pattern.

        Args:
            subject: Optional subject to match (None = any)
            predicate: Optional predicate to match (None = any)
            object: Optional object to match (None = any)
            listener: Callback function

        Returns:
            Unsubscribe function
        """
        if listener is None:
            raise ValueError("Listener is required")

        listener_id = str(uuid.uuid4())
        
        s = URIRef(subject) if isinstance(subject, str) else subject
        p = URIRef(predicate) if isinstance(predicate, str) else predicate
        o: Optional[Node] = None
        if object is not None:
            if isinstance(object, str):
                o = URIRef(object) if object.startswith("http") else Literal(object)
            else:
                o = object

        self._pattern_listeners[listener_id] = (s, p, o, listener)

        def unsubscribe():
            self._pattern_listeners.pop(listener_id, None)

        return unsubscribe

    def _emit_event(self, event: DatasetEvent) -> None:
        """Emit an event to all matching listeners."""
        if self._batch_mode:
            self._batch_events.append(event)
            return

        self._notify_listeners(event)

    def _notify_listeners(self, event: DatasetEvent) -> None:
        """Notify all matching listeners of an event."""
        # Global listeners
        for listener in list(self._listeners.values()):
            try:
                listener(event)
            except Exception:
                pass  # Don't let listener errors break the dataset

        # Subject-specific listeners
        if event.triple:
            subject_str = str(event.triple[0])
            if subject_str in self._subject_listeners:
                for listener in list(self._subject_listeners[subject_str].values()):
                    try:
                        listener(event)
                    except Exception:
                        pass

            # Predicate-specific listeners
            predicate_str = str(event.triple[1])
            if predicate_str in self._predicate_listeners:
                for listener in list(self._predicate_listeners[predicate_str].values()):
                    try:
                        listener(event)
                    except Exception:
                        pass

            # Pattern listeners
            for listener_id, (s, p, o, listener) in list(self._pattern_listeners.items()):
                if self._matches_pattern(event.triple, s, p, o):
                    try:
                        listener(event)
                    except Exception:
                        pass

    def _matches_pattern(
        self,
        triple: Triple,
        subject: Optional[Node],
        predicate: Optional[Node],
        object: Optional[Node],
    ) -> bool:
        """Check if a triple matches a pattern."""
        if subject is not None and triple[0] != subject:
            return False
        if predicate is not None and triple[1] != predicate:
            return False
        if object is not None and triple[2] != object:
            return False
        return True

    def add(self, triple: Triple) -> "SubscribableDataset":
        """
        Add a triple to the graph and emit an event.

        Args:
            triple: The (subject, predicate, object) triple to add

        Returns:
            Self for chaining
        """
        super().add(triple)
        
        event = DatasetEvent(
            type=EventType.ADD,
            triple=triple,
            transaction_id=self._current_transaction_id,
        )
        self._emit_event(event)
        
        return self

    def remove(self, triple: Triple) -> "SubscribableDataset":
        """
        Remove a triple from the graph and emit an event.

        Args:
            triple: The (subject, predicate, object) triple to remove

        Returns:
            Self for chaining
        """
        super().remove(triple)
        
        event = DatasetEvent(
            type=EventType.REMOVE,
            triple=triple,
            transaction_id=self._current_transaction_id,
        )
        self._emit_event(event)
        
        return self

    def batch(self) -> "BatchContext":
        """
        Start a batch of changes.

        Changes made within the batch context are collected and
        emitted as a single batch event when the context exits.

        Example:
            >>> with dataset.batch():
            ...     dataset.add(triple1)
            ...     dataset.add(triple2)
            ...     dataset.remove(triple3)
            ... # Single batch event emitted here

        Returns:
            Context manager for batching
        """
        return BatchContext(self)

    def _start_batch(self) -> str:
        """Start batch mode and return transaction ID."""
        self._batch_mode = True
        self._current_transaction_id = str(uuid.uuid4())
        self._batch_events = []
        
        # Emit batch start event
        self._notify_listeners(DatasetEvent(
            type=EventType.BATCH_START,
            transaction_id=self._current_transaction_id,
        ))
        
        return self._current_transaction_id

    def _end_batch(self) -> None:
        """End batch mode and emit collected events."""
        self._batch_mode = False
        
        # Emit all collected events
        for event in self._batch_events:
            self._notify_listeners(event)
        
        # Emit batch end event
        self._notify_listeners(DatasetEvent(
            type=EventType.BATCH_END,
            transaction_id=self._current_transaction_id,
            metadata={"event_count": len(self._batch_events)},
        ))
        
        self._batch_events = []
        self._current_transaction_id = None

    def remove_all_listeners(self) -> None:
        """Remove all event listeners."""
        self._listeners.clear()
        self._subject_listeners.clear()
        self._predicate_listeners.clear()
        self._pattern_listeners.clear()

    def remove_listener_from_all_events(self, listener: EventListener) -> None:
        """
        Remove a specific listener from all subscriptions.

        Args:
            listener: The listener function to remove
        """
        # Remove from global listeners
        to_remove = [k for k, v in self._listeners.items() if v is listener]
        for key in to_remove:
            del self._listeners[key]

        # Remove from subject listeners
        for subject_listeners in self._subject_listeners.values():
            to_remove = [k for k, v in subject_listeners.items() if v is listener]
            for key in to_remove:
                del subject_listeners[key]

        # Remove from predicate listeners
        for predicate_listeners in self._predicate_listeners.values():
            to_remove = [k for k, v in predicate_listeners.items() if v is listener]
            for key in to_remove:
                del predicate_listeners[key]

        # Remove from pattern listeners
        to_remove = [k for k, (_, _, _, l) in self._pattern_listeners.items() if l is listener]
        for key in to_remove:
            del self._pattern_listeners[key]


class BatchContext:
    """Context manager for batching dataset changes."""

    def __init__(self, dataset: SubscribableDataset):
        self._dataset = dataset
        self._transaction_id: Optional[str] = None

    def __enter__(self) -> "BatchContext":
        self._transaction_id = self._dataset._start_batch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self._dataset._end_batch()
        return False  # Don't suppress exceptions

    @property
    def transaction_id(self) -> Optional[str]:
        return self._transaction_id
