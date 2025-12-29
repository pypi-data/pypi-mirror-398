"""
Transaction support for RDF graphs.

Provides change tracking and rollback capabilities for RDF operations.
This is essential for generating SPARQL UPDATE queries and for
optimistic concurrency control.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rdflib import Graph

if TYPE_CHECKING:
    from .graph import RdfGraph, Triple


@dataclass
class TransactionChanges:
    """
    Container for changes made during a transaction.

    Attributes:
        added: List of triples that were added
        removed: List of triples that were removed
    """

    added: list[Triple] = field(default_factory=list)
    removed: list[Triple] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if there are no changes."""
        return len(self.added) == 0 and len(self.removed) == 0

    def clear(self) -> None:
        """Clear all tracked changes."""
        self.added.clear()
        self.removed.clear()

    def __repr__(self) -> str:
        return f"TransactionChanges(added={len(self.added)}, removed={len(self.removed)})"


class Transaction:
    """
    Tracks changes to an RDF graph during a transaction.

    Transactions allow you to:
    - Track what triples were added and removed
    - Generate SPARQL UPDATE queries from the changes
    - Rollback all changes if needed

    Example:
        >>> graph = RdfGraph()
        >>> graph.parse_turtle('<#me> <http://xmlns.com/foaf/0.1/name> "Alice" .')
        >>> 
        >>> # Start a transaction
        >>> tx = graph.start_transaction()
        >>> 
        >>> # Make changes
        >>> graph.remove((URIRef("#me"), FOAF.name, Literal("Alice")))
        >>> graph.add((URIRef("#me"), FOAF.name, Literal("Alicia")))
        >>> 
        >>> # Check changes
        >>> print(tx.changes)  # TransactionChanges(added=1, removed=1)
        >>> 
        >>> # Generate SPARQL UPDATE
        >>> print(graph.to_sparql_update())
        >>> 
        >>> # Commit or rollback
        >>> graph.commit_transaction()  # or graph.rollback_transaction()
    """

    def __init__(self, graph: "RdfGraph"):
        """
        Initialize a transaction for the given graph.

        Args:
            graph: The RDF graph to track changes for
        """
        self._graph = graph
        self._changes = TransactionChanges()
        self._committed = False
        self._rolled_back = False

    @property
    def changes(self) -> TransactionChanges:
        """Get the changes made during this transaction."""
        return self._changes

    @property
    def is_active(self) -> bool:
        """Check if the transaction is still active (not committed or rolled back)."""
        return not self._committed and not self._rolled_back

    def track_add(self, triple: "Triple") -> None:
        """
        Track a triple addition.

        If the triple was previously removed in this transaction,
        the removal is cancelled out instead of adding a new addition.

        Args:
            triple: The triple being added
        """
        if not self.is_active:
            raise RuntimeError("Transaction is no longer active")

        # Check if this cancels out a previous removal
        if triple in self._changes.removed:
            self._changes.removed.remove(triple)
        else:
            self._changes.added.append(triple)

    def track_remove(self, triple: "Triple") -> None:
        """
        Track a triple removal.

        If the triple was previously added in this transaction,
        the addition is cancelled out instead of adding a new removal.

        Args:
            triple: The triple being removed
        """
        if not self.is_active:
            raise RuntimeError("Transaction is no longer active")

        # Check if this cancels out a previous addition
        if triple in self._changes.added:
            self._changes.added.remove(triple)
        else:
            self._changes.removed.append(triple)

    def rollback(self, underlying_graph: Graph) -> None:
        """
        Rollback all changes made during this transaction.

        This directly modifies the underlying rdflib Graph to undo changes.

        Args:
            underlying_graph: The rdflib Graph to modify
        """
        if not self.is_active:
            raise RuntimeError("Transaction is no longer active")

        # Undo additions (remove them)
        for triple in self._changes.added:
            underlying_graph.remove(triple)

        # Undo removals (add them back)
        for triple in self._changes.removed:
            underlying_graph.add(triple)

        self._rolled_back = True
        self._changes.clear()

    def commit(self) -> None:
        """
        Mark the transaction as committed.

        The changes are already applied to the graph, so this just
        marks the transaction as complete.
        """
        if not self.is_active:
            raise RuntimeError("Transaction is no longer active")

        self._committed = True

    def __repr__(self) -> str:
        status = "active" if self.is_active else ("committed" if self._committed else "rolled back")
        return f"Transaction({status}, {self._changes})"


class TransactionContext:
    """
    Context manager for transactions.

    Provides a convenient way to use transactions with the `with` statement.
    Automatically commits on success or rolls back on exception.

    Example:
        >>> with TransactionContext(graph) as tx:
        ...     graph.add((subject, predicate, obj))
        ...     # Changes are committed at the end
        >>> 
        >>> with TransactionContext(graph) as tx:
        ...     graph.add((subject, predicate, obj))
        ...     raise ValueError("Something went wrong")
        ...     # Changes are rolled back due to exception
    """

    def __init__(self, graph: "RdfGraph", auto_commit: bool = True):
        """
        Initialize a transaction context.

        Args:
            graph: The RDF graph to start a transaction on
            auto_commit: If True, automatically commit on successful exit
        """
        self._graph = graph
        self._auto_commit = auto_commit
        self._transaction: Transaction | None = None

    def __enter__(self) -> Transaction:
        """Start the transaction and return it."""
        self._transaction = self._graph.start_transaction()
        return self._transaction

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Commit or rollback the transaction."""
        if exc_type is not None:
            # Exception occurred, rollback
            self._graph.rollback_transaction()
            return False  # Re-raise the exception

        if self._auto_commit:
            self._graph.commit_transaction()

        return False
