"""
LdSet - A set collection for multi-valued Linked Data relationships.

Similar to JavaScript LDO's LdSet, this provides a set-like interface
for managing collections of linked data objects, with RDF-aware operations.

Example:
    >>> profile.knows  # Returns LdSet[PersonShape]
    >>> profile.knows.add(alice)
    >>> profile.knows.remove(bob)
    >>> for friend in profile.knows:
    ...     print(friend.name)
"""

from __future__ import annotations

from typing import (
    Any,
    Generic,
    Iterator,
    MutableSet,
    Optional,
    TypeVar,
    Union,
    overload,
)
from weakref import ref

from pydantic import BaseModel
from rdflib import Graph, Literal, URIRef

T = TypeVar("T", bound=BaseModel)


class LdSet(MutableSet[T], Generic[T]):
    """
    A set-like collection for multi-valued Linked Data relationships.

    LdSet provides a familiar Python set interface while maintaining
    the connection to the underlying RDF graph for synchronization.

    Features:
    - Add/remove items with automatic RDF triple management
    - Iteration over typed Linked Data Objects
    - Conversion to list/set for standard Python operations
    - Optional binding to RDF graph for automatic sync

    Example:
        >>> from pyldo import LdSet
        >>> 
        >>> # Create a standalone LdSet
        >>> friends: LdSet[Person] = LdSet()
        >>> friends.add(alice)
        >>> friends.add(bob)
        >>> 
        >>> # Or bind to an RDF graph
        >>> friends = LdSet.from_graph(
        ...     graph=my_graph,
        ...     subject=URIRef("http://example.org/me"),
        ...     predicate=URIRef("http://xmlns.com/foaf/0.1/knows"),
        ...     item_type=Person,
        ... )
    """

    def __init__(
        self,
        items: Optional[list[T]] = None,
        *,
        graph: Optional[Graph] = None,
        subject: Optional[URIRef] = None,
        predicate: Optional[URIRef] = None,
        item_type: Optional[type[T]] = None,
    ):
        """
        Initialize an LdSet.

        Args:
            items: Initial items to add to the set
            graph: Optional RDF graph for synchronization
            subject: Subject URI for the relationship
            predicate: Predicate URI for the relationship
            item_type: The Pydantic model type for items
        """
        self._items: dict[str, T] = {}  # id -> item
        self._graph = graph
        self._subject = subject
        self._predicate = predicate
        self._item_type = item_type
        self._change_callbacks: list[callable] = []

        if items:
            for item in items:
                self._add_item(item)

    def _get_item_id(self, item: T) -> str:
        """Get the unique identifier for an item."""
        if hasattr(item, "id") and item.id:
            return item.id
        # Use object id as fallback
        return str(id(item))

    def _add_item(self, item: T, notify: bool = True) -> None:
        """Internal method to add an item."""
        item_id = self._get_item_id(item)
        if item_id not in self._items:
            self._items[item_id] = item
            if notify:
                self._notify_change("add", item)

    def _remove_item(self, item: T, notify: bool = True) -> None:
        """Internal method to remove an item."""
        item_id = self._get_item_id(item)
        if item_id in self._items:
            del self._items[item_id]
            if notify:
                self._notify_change("remove", item)

    def _notify_change(self, action: str, item: T) -> None:
        """Notify callbacks of a change."""
        for callback in self._change_callbacks:
            try:
                callback(action, item)
            except Exception:
                pass

    # MutableSet interface

    def add(self, item: T) -> None:
        """
        Add an item to the set.

        If the LdSet is bound to an RDF graph, this will also add
        the corresponding triple.

        Args:
            item: The item to add
        """
        item_id = self._get_item_id(item)
        if item_id in self._items:
            return  # Already present

        self._add_item(item)

        # Sync to graph if bound
        if self._graph is not None and self._subject and self._predicate:
            obj = URIRef(item_id) if item_id.startswith("http") else Literal(item_id)
            self._graph.add((self._subject, self._predicate, obj))

    def discard(self, item: T) -> None:
        """
        Remove an item from the set if present.

        Unlike remove(), this does not raise an error if the item is not present.

        Args:
            item: The item to remove
        """
        item_id = self._get_item_id(item)
        if item_id not in self._items:
            return

        self._remove_item(item)

        # Sync to graph if bound
        if self._graph is not None and self._subject and self._predicate:
            obj = URIRef(item_id) if item_id.startswith("http") else Literal(item_id)
            self._graph.remove((self._subject, self._predicate, obj))

    def remove(self, item: T) -> None:
        """
        Remove an item from the set.

        Raises KeyError if the item is not present.

        Args:
            item: The item to remove
        """
        item_id = self._get_item_id(item)
        if item_id not in self._items:
            raise KeyError(item)
        self.discard(item)

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the set."""
        if not isinstance(item, BaseModel):
            return False
        item_id = self._get_item_id(item)  # type: ignore
        return item_id in self._items

    def __iter__(self) -> Iterator[T]:
        """Iterate over items in the set."""
        return iter(self._items.values())

    def __len__(self) -> int:
        """Return the number of items in the set."""
        return len(self._items)

    # Additional useful methods

    def clear(self) -> None:
        """Remove all items from the set."""
        items_to_remove = list(self._items.values())
        for item in items_to_remove:
            self.discard(item)

    def to_list(self) -> list[T]:
        """
        Convert the set to a list.

        Returns:
            List of all items in the set
        """
        return list(self._items.values())

    def to_array(self) -> list[T]:
        """
        Convert the set to an array (alias for to_list).

        This matches the JavaScript LDO API.

        Returns:
            List of all items in the set
        """
        return self.to_list()

    @property
    def size(self) -> int:
        """
        Return the number of items (JavaScript Set API compatibility).

        Returns:
            Number of items in the set
        """
        return len(self)

    def first(self) -> Optional[T]:
        """
        Get the first item in the set, or None if empty.

        Returns:
            First item or None
        """
        if self._items:
            return next(iter(self._items.values()))
        return None

    def get_by_id(self, item_id: str) -> Optional[T]:
        """
        Get an item by its ID.

        Args:
            item_id: The ID to look up

        Returns:
            The item if found, None otherwise
        """
        return self._items.get(item_id)

    def filter(self, predicate: callable) -> list[T]:
        """
        Filter items based on a predicate function.

        Args:
            predicate: Function that takes an item and returns bool

        Returns:
            List of items that match the predicate
        """
        return [item for item in self._items.values() if predicate(item)]

    def map(self, func: callable) -> list[Any]:
        """
        Apply a function to all items.

        Args:
            func: Function to apply to each item

        Returns:
            List of results
        """
        return [func(item) for item in self._items.values()]

    def on_change(self, callback: callable) -> callable:
        """
        Register a callback for when the set changes.

        Args:
            callback: Function called with (action, item) on changes

        Returns:
            Function to unregister the callback
        """
        self._change_callbacks.append(callback)

        def unsubscribe():
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)

        return unsubscribe

    # Class methods for creation

    @classmethod
    def from_items(cls, items: list[T]) -> "LdSet[T]":
        """
        Create an LdSet from a list of items.

        Args:
            items: Items to add to the set

        Returns:
            New LdSet containing the items
        """
        return cls(items=items)

    @classmethod
    def from_graph(
        cls,
        graph: Graph,
        subject: URIRef,
        predicate: URIRef,
        item_type: type[T],
        builder: Optional[Any] = None,
    ) -> "LdSet[T]":
        """
        Create an LdSet bound to an RDF graph.

        This will load existing items from the graph and sync
        future changes back to the graph.

        Args:
            graph: The RDF graph
            subject: Subject URI
            predicate: Predicate URI
            item_type: Pydantic model type for items
            builder: Optional LdoBuilder for creating typed objects

        Returns:
            New LdSet bound to the graph
        """
        ldset: LdSet[T] = cls(
            graph=graph,
            subject=subject,
            predicate=predicate,
            item_type=item_type,
        )

        # Load existing items from graph
        for obj in graph.objects(subject, predicate):
            obj_str = str(obj)
            if builder:
                # Use builder to create typed object
                item = builder.from_subject(obj_str)
                ldset._add_item(item, notify=False)
            else:
                # Create minimal item with just ID
                item = item_type(id=obj_str)  # type: ignore
                ldset._add_item(item, notify=False)

        return ldset

    def __repr__(self) -> str:
        count = len(self)
        type_name = self._item_type.__name__ if self._item_type else "Any"
        return f"LdSet[{type_name}]({count} items)"

    def __str__(self) -> str:
        items_str = ", ".join(str(self._get_item_id(item)) for item in self._items.values())
        return f"LdSet([{items_str}])"
