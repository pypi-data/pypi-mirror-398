"""
LdoDataset factory - the main entry point for pyldo.

This module provides the LdoDataset class, which is the primary interface
for working with Linked Data Objects in Python.
"""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from ..dataset.graph import RdfGraph
from ..dataset.transaction import TransactionContext
from .builder import LdoBuilder

# Type variable for shape types
T = TypeVar("T", bound=BaseModel)


class LdoDataset:
    """
    Main entry point for working with Linked Data Objects.

    LdoDataset wraps an RDF graph and provides methods for:
    - Parsing RDF data from various formats
    - Creating typed Linked Data Objects using shape types
    - Serializing data back to RDF formats
    - Transaction support for tracking changes

    Example:
        >>> from pyldo.ldo import LdoDataset
        >>> from .ldo.profile_types import ProfileShape
        >>> 
        >>> # Create dataset
        >>> dataset = LdoDataset()
        >>> 
        >>> # Parse some RDF
        >>> dataset.parse_turtle('''
        ...     @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        ...     <#alice> a foaf:Person ; foaf:name "Alice" .
        ... ''')
        >>> 
        >>> # Get typed object
        >>> profile = dataset.using(ProfileShape).from_subject("#alice")
        >>> print(profile.name)  # "Alice"
        >>> 
        >>> # Modify and serialize
        >>> profile.name = "Alicia"
        >>> profile.sync_to_graph()
        >>> print(dataset.to_turtle())
    """

    def __init__(self, graph: Optional[RdfGraph] = None):
        """
        Initialize an LdoDataset.

        Args:
            graph: Optional existing RdfGraph. If None, a new empty graph is created.
        """
        self._graph = graph if graph is not None else RdfGraph()

    @property
    def graph(self) -> RdfGraph:
        """Get the underlying RdfGraph."""
        return self._graph

    # =========================================================================
    # Parsing methods
    # =========================================================================

    def parse(
        self,
        source: str,
        format: str = "turtle",
        base: Optional[str] = None,
    ) -> "LdoDataset":
        """
        Parse RDF data from a string.

        Args:
            source: RDF data as a string
            format: Format of the data (turtle, json-ld, ntriples)
            base: Base IRI for relative IRIs

        Returns:
            self for method chaining
        """
        self._graph.parse(source, format, base)
        return self

    def parse_turtle(self, source: str, base: Optional[str] = None) -> "LdoDataset":
        """Parse Turtle format RDF data."""
        self._graph.parse_turtle(source, base)
        return self

    def parse_jsonld(self, source: str, base: Optional[str] = None) -> "LdoDataset":
        """Parse JSON-LD format RDF data."""
        self._graph.parse_jsonld(source, base)
        return self

    def parse_file(
        self,
        filepath: str,
        format: Optional[str] = None,
        base: Optional[str] = None,
    ) -> "LdoDataset":
        """
        Parse RDF data from a file.

        Args:
            filepath: Path to the RDF file
            format: Format of the data (auto-detected if None)
            base: Base IRI for relative IRIs

        Returns:
            self for method chaining
        """
        self._graph.parse_file(filepath, format, base)
        return self

    # =========================================================================
    # LDO Builder interface
    # =========================================================================

    def using(self, shape_type: Type[T]) -> LdoBuilder[T]:
        """
        Create an LdoBuilder for the given shape type.

        This is the main method for working with typed Linked Data Objects.
        It returns a builder that can query the graph and return instances
        of the specified Pydantic model.

        Args:
            shape_type: A Pydantic model class (generated from ShEx)

        Returns:
            An LdoBuilder for creating typed objects

        Example:
            >>> from .ldo.profile_types import ProfileShape
            >>> 
            >>> profile = dataset.using(ProfileShape).from_subject("#alice")
            >>> people = dataset.using(ProfileShape).match_subject(RDF.type, FOAF.Person)
        """
        return LdoBuilder(self._graph, shape_type)

    # =========================================================================
    # Serialization methods
    # =========================================================================

    def to_turtle(self, prefixes: Optional[dict[str, str]] = None) -> str:
        """
        Serialize the dataset to Turtle format.

        Args:
            prefixes: Optional prefix -> namespace mappings

        Returns:
            Turtle-formatted string
        """
        return self._graph.to_turtle(prefixes)

    def to_ntriples(self) -> str:
        """Serialize the dataset to N-Triples format."""
        return self._graph.to_ntriples()

    def to_jsonld(self, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """
        Serialize the dataset to JSON-LD format.

        Args:
            context: Optional JSON-LD context

        Returns:
            JSON-LD as a dictionary
        """
        return self._graph.to_jsonld(context)

    # =========================================================================
    # Transaction support
    # =========================================================================

    def start_transaction(self) -> "LdoDataset":
        """
        Start a transaction for tracking changes.

        Returns:
            self for method chaining

        Example:
            >>> dataset.start_transaction()
            >>> profile.name = "New Name"
            >>> profile.sync_to_graph()
            >>> print(dataset.to_sparql_update())
            >>> dataset.commit()
        """
        self._graph.start_transaction()
        return self

    def commit(self) -> None:
        """Commit the current transaction."""
        self._graph.commit_transaction()

    def rollback(self) -> None:
        """Rollback the current transaction, undoing all changes."""
        self._graph.rollback_transaction()

    def to_sparql_update(self) -> str:
        """
        Generate a SPARQL UPDATE query for the current transaction.

        Returns:
            SPARQL UPDATE string with DELETE and INSERT clauses

        Raises:
            RuntimeError: If no transaction is active
        """
        return self._graph.to_sparql_update()

    @property
    def in_transaction(self) -> bool:
        """Check if a transaction is currently active."""
        return self._graph.in_transaction

    def transaction(self) -> TransactionContext:
        """
        Get a context manager for a transaction.

        Example:
            >>> with dataset.transaction():
            ...     profile.name = "New Name"
            ...     profile.sync_to_graph()
            ...     # Auto-commits on success, rollbacks on exception
        """
        return TransactionContext(self._graph)

    # =========================================================================
    # Utility methods
    # =========================================================================

    def __len__(self) -> int:
        """Return the number of triples in the dataset."""
        return len(self._graph)

    def clear(self) -> None:
        """Remove all triples from the dataset."""
        self._graph.clear()

    def copy(self) -> "LdoDataset":
        """Create a copy of this dataset."""
        return LdoDataset(self._graph.copy())

    def __repr__(self) -> str:
        return f"LdoDataset({len(self)} triples)"
