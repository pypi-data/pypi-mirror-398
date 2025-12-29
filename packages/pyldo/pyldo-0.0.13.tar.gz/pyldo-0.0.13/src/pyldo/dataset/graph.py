"""
RDF Graph wrapper using rdflib.

Provides a clean interface for working with RDF data, including:
- Parsing from various formats (Turtle, JSON-LD, N-Triples)
- Serialization to various formats
- CRUD operations on triples
- Change tracking for transactions
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.term import Node

if TYPE_CHECKING:
    from .transaction import Transaction

# Common namespaces
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")


# Type aliases
Subject = Union[URIRef, BNode]
Predicate = URIRef
Object = Union[URIRef, BNode, Literal]
Triple = tuple[Subject, Predicate, Object]
QuadMatch = tuple[
    Optional[Subject], Optional[Predicate], Optional[Object], Optional[URIRef]
]


class RdfGraph:
    """
    A wrapper around rdflib.Graph with change tracking support.

    This class provides a clean interface for RDF operations and integrates
    with the transaction system for tracking modifications.

    Example:
        >>> graph = RdfGraph()
        >>> graph.parse_turtle('''
        ...     @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        ...     <https://example.org/alice> foaf:name "Alice" .
        ... ''')
        >>> 
        >>> # Query triples
        >>> for s, p, o in graph.triples((None, FOAF.name, None)):
        ...     print(f"{s} has name {o}")
        >>> 
        >>> # Add a triple
        >>> graph.add((
        ...     URIRef("https://example.org/alice"),
        ...     FOAF.age,
        ...     Literal(30)
        ... ))
    """

    def __init__(self, graph: Optional[Graph] = None):
        """
        Initialize an RdfGraph.

        Args:
            graph: Optional existing rdflib.Graph to wrap.
                   If None, a new empty graph is created.
        """
        self._graph = graph if graph is not None else Graph()
        self._transaction: Optional[Transaction] = None

    @property
    def graph(self) -> Graph:
        """Get the underlying rdflib.Graph."""
        return self._graph

    def __len__(self) -> int:
        """Return the number of triples in the graph."""
        return len(self._graph)

    def __contains__(self, triple: Triple) -> bool:
        """Check if a triple exists in the graph."""
        return triple in self._graph

    def __iter__(self) -> Iterator[Triple]:
        """Iterate over all triples in the graph."""
        return iter(self._graph)

    # =========================================================================
    # Parsing methods
    # =========================================================================

    def parse(
        self,
        source: str,
        format: str = "turtle",
        base: Optional[str] = None,
    ) -> RdfGraph:
        """
        Parse RDF data from a string.

        Args:
            source: RDF data as a string
            format: Format of the data (turtle, json-ld, n3, ntriples, xml)
            base: Base IRI for relative IRIs

        Returns:
            self for method chaining
        """
        self._graph.parse(data=source, format=format, publicID=base)
        return self

    def parse_turtle(self, source: str, base: Optional[str] = None) -> RdfGraph:
        """Parse Turtle format RDF data."""
        return self.parse(source, format="turtle", base=base)

    def parse_jsonld(self, source: str, base: Optional[str] = None) -> RdfGraph:
        """Parse JSON-LD format RDF data."""
        return self.parse(source, format="json-ld", base=base)

    def parse_ntriples(self, source: str) -> RdfGraph:
        """Parse N-Triples format RDF data."""
        return self.parse(source, format="ntriples")

    def parse_file(
        self,
        filepath: str,
        format: Optional[str] = None,
        base: Optional[str] = None,
    ) -> RdfGraph:
        """
        Parse RDF data from a file.

        Args:
            filepath: Path to the RDF file
            format: Format of the data (auto-detected if None)
            base: Base IRI for relative IRIs

        Returns:
            self for method chaining
        """
        self._graph.parse(source=filepath, format=format, publicID=base)
        return self

    # =========================================================================
    # Triple operations
    # =========================================================================

    def add(self, triple: Triple) -> None:
        """
        Add a triple to the graph.

        If a transaction is active, the change is tracked.

        Args:
            triple: A tuple of (subject, predicate, object)
        """
        if self._transaction is not None:
            self._transaction.track_add(triple)
        self._graph.add(triple)

    def remove(self, triple: Triple) -> None:
        """
        Remove a triple from the graph.

        If a transaction is active, the change is tracked.

        Args:
            triple: A tuple of (subject, predicate, object)
        """
        if self._transaction is not None:
            self._transaction.track_remove(triple)
        self._graph.remove(triple)

    def set(self, triple: Triple) -> None:
        """
        Set a triple, removing any existing triples with the same subject and predicate.

        This is useful for properties that should have exactly one value.

        Args:
            triple: A tuple of (subject, predicate, object)
        """
        subject, predicate, obj = triple
        # Remove existing values
        for existing in list(self._graph.objects(subject, predicate)):
            self.remove((subject, predicate, existing))
        # Add new value
        self.add(triple)

    def triples(
        self,
        pattern: tuple[
            Optional[Subject], Optional[Predicate], Optional[Object]
        ] = (None, None, None),
    ) -> Iterator[Triple]:
        """
        Iterate over triples matching a pattern.

        Args:
            pattern: A tuple of (subject, predicate, object) where None matches any value

        Yields:
            Matching triples
        """
        return self._graph.triples(pattern)

    def subjects(
        self,
        predicate: Optional[Predicate] = None,
        object: Optional[Object] = None,
    ) -> Iterator[Subject]:
        """Get all subjects matching the given predicate and/or object."""
        return self._graph.subjects(predicate, object)

    def predicates(
        self,
        subject: Optional[Subject] = None,
        object: Optional[Object] = None,
    ) -> Iterator[Predicate]:
        """Get all predicates matching the given subject and/or object."""
        return self._graph.predicates(subject, object)

    def objects(
        self,
        subject: Optional[Subject] = None,
        predicate: Optional[Predicate] = None,
    ) -> Iterator[Object]:
        """Get all objects matching the given subject and/or predicate."""
        return self._graph.objects(subject, predicate)

    def value(
        self,
        subject: Optional[Subject] = None,
        predicate: Optional[Predicate] = None,
        object: Optional[Object] = None,
        default: Optional[Node] = None,
    ) -> Optional[Node]:
        """
        Get a single value matching the pattern.

        Args:
            subject: Subject to match (or None)
            predicate: Predicate to match (or None)
            object: Object to match (or None)
            default: Default value if no match found

        Returns:
            The first matching value, or the default
        """
        return self._graph.value(subject, predicate, object, default)

    # =========================================================================
    # Subject-focused operations
    # =========================================================================

    def get_subject_triples(self, subject: Subject) -> Iterator[Triple]:
        """Get all triples for a given subject."""
        return self.triples((subject, None, None))

    def get_subject_dict(self, subject: Subject) -> dict[str, Any]:
        """
        Get all properties of a subject as a dictionary.

        Args:
            subject: The subject IRI or blank node

        Returns:
            Dictionary mapping predicate IRIs to values (or lists of values)
        """
        result: dict[str, Any] = {"@id": str(subject)}

        for _, predicate, obj in self.triples((subject, None, None)):
            pred_str = str(predicate)

            # Convert object to Python value
            if isinstance(obj, Literal):
                value = obj.toPython()
            else:
                value = str(obj)

            # Handle multiple values for same predicate
            if pred_str in result:
                existing = result[pred_str]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    result[pred_str] = [existing, value]
            else:
                result[pred_str] = value

        return result

    def subjects_of_type(self, rdf_type: URIRef) -> Iterator[Subject]:
        """Get all subjects that have rdf:type of the given type."""
        return self.subjects(RDF.type, rdf_type)

    # =========================================================================
    # Namespace management
    # =========================================================================

    def bind(self, prefix: str, namespace: Union[str, Namespace]) -> None:
        """Bind a prefix to a namespace."""
        if isinstance(namespace, str):
            namespace = Namespace(namespace)
        self._graph.bind(prefix, namespace)

    def bind_common_namespaces(self) -> None:
        """Bind common RDF namespaces (rdf, rdfs, xsd, foaf)."""
        self.bind("rdf", RDF)
        self.bind("rdfs", RDFS)
        self.bind("xsd", XSD)
        self.bind("foaf", FOAF)

    @property
    def namespaces(self) -> Iterator[tuple[str, Namespace]]:
        """Get all bound namespaces."""
        return self._graph.namespaces()

    # =========================================================================
    # Transaction support
    # =========================================================================

    def start_transaction(self) -> "Transaction":
        """
        Start a new transaction.

        Returns:
            A Transaction object for tracking changes

        Raises:
            RuntimeError: If a transaction is already active
        """
        from .transaction import Transaction

        if self._transaction is not None:
            raise RuntimeError("A transaction is already active")

        self._transaction = Transaction(self)
        return self._transaction

    def commit_transaction(self) -> None:
        """Commit the current transaction (changes are already applied)."""
        if self._transaction is None:
            raise RuntimeError("No transaction is active")
        self._transaction = None

    def rollback_transaction(self) -> None:
        """Rollback the current transaction, undoing all changes."""
        if self._transaction is None:
            raise RuntimeError("No transaction is active")

        # Undo changes in reverse order
        self._transaction.rollback(self._graph)
        self._transaction = None

    @property
    def in_transaction(self) -> bool:
        """Check if a transaction is currently active."""
        return self._transaction is not None

    @property
    def transaction(self) -> Optional["Transaction"]:
        """Get the current transaction, if any."""
        return self._transaction

    # =========================================================================
    # Serialization (delegates to serializers module)
    # =========================================================================

    def to_turtle(self, prefixes: Optional[dict[str, str]] = None) -> str:
        """Serialize the graph to Turtle format."""
        from .serializers import to_turtle

        return to_turtle(self, prefixes)

    def to_ntriples(self) -> str:
        """Serialize the graph to N-Triples format."""
        from .serializers import to_ntriples

        return to_ntriples(self)

    def to_jsonld(self, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Serialize the graph to JSON-LD format."""
        from .serializers import to_jsonld

        return to_jsonld(self, context)

    def to_sparql_update(self) -> str:
        """
        Generate SPARQL UPDATE for the current transaction changes.

        Raises:
            RuntimeError: If no transaction is active
        """
        from .serializers import to_sparql_update

        if self._transaction is None:
            raise RuntimeError("No transaction is active")

        return to_sparql_update(self._transaction.changes)

    # =========================================================================
    # Utility methods
    # =========================================================================

    def clear(self) -> None:
        """Remove all triples from the graph."""
        self._graph.remove((None, None, None))

    def copy(self) -> RdfGraph:
        """Create a copy of this graph."""
        new_graph = Graph()
        for triple in self._graph:
            new_graph.add(triple)
        return RdfGraph(new_graph)

    def __repr__(self) -> str:
        return f"RdfGraph({len(self)} triples)"
