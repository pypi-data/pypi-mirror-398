"""
LdoBuilder - Creates typed Linked Data Objects from RDF graphs.

This is the equivalent of LdoBuilder from the JS LDO library.
It provides a fluent API for querying and creating typed objects from RDF data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Iterator, Optional, Type, TypeVar

from pydantic import BaseModel
from rdflib import RDF, Literal, URIRef

if TYPE_CHECKING:
    from ..dataset.graph import RdfGraph

# Type variable for the shape type
T = TypeVar("T", bound=BaseModel)


class LdoBuilder(Generic[T]):
    """
    Builder for creating Linked Data Objects from an RDF graph.

    The LdoBuilder provides methods for querying the graph and returning
    typed Pydantic model instances.

    Example:
        >>> from pyldo.ldo import LdoDataset
        >>> from .ldo.profile_types import ProfileShape
        >>> 
        >>> dataset = LdoDataset()
        >>> dataset.parse_turtle('''
        ...     @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        ...     <#alice> a foaf:Person ; foaf:name "Alice" .
        ... ''')
        >>> 
        >>> # Get a single subject
        >>> alice = dataset.using(ProfileShape).from_subject("#alice")
        >>> print(alice.name)  # "Alice"
        >>> 
        >>> # Query multiple subjects
        >>> people = dataset.using(ProfileShape).match_subject(
        ...     RDF.type, URIRef("http://xmlns.com/foaf/0.1/Person")
        ... )
        >>> for person in people:
        ...     print(person.name)
    """

    def __init__(
        self,
        graph: "RdfGraph",
        shape_type: Type[T],
        context: Optional[dict[str, Any]] = None,
        write_graphs: Optional[list[str]] = None,
    ):
        """
        Initialize an LdoBuilder.

        Args:
            graph: The RDF graph to query
            shape_type: The Pydantic model class to instantiate
            context: Optional JSON-LD context for mapping
            write_graphs: Optional list of graph IRIs to write to
        """
        self._graph = graph
        self._shape_type = shape_type
        self._context = context or {}
        self._write_graphs = write_graphs or []

    def from_subject(self, subject: str) -> T:
        """
        Get a Linked Data Object for a specific subject IRI.

        Args:
            subject: The subject IRI (can be relative or absolute)

        Returns:
            A Pydantic model instance populated with data from the graph

        Example:
            >>> profile = builder.from_subject("https://example.org/alice#me")
        """
        # Normalize subject to full IRI if needed
        if not subject.startswith("http"):
            # Handle relative IRIs
            base = self._graph.graph.base or "http://example.org/"
            if subject.startswith("#"):
                subject = base + subject
            else:
                subject = base + "#" + subject

        subject_ref = URIRef(subject)

        # Build data dictionary from graph
        data = self._extract_subject_data(subject_ref)

        # Create the model instance
        instance = self._shape_type(**data)

        # Bind to graph if it's a LinkedDataObject
        if hasattr(instance, "bind_to_graph"):
            instance.bind_to_graph(self._graph, subject)

        return instance

    def from_json(self, data: dict[str, Any]) -> T:
        """
        Create a Linked Data Object from JSON data and add it to the graph.

        The data is validated against the shape type, added to the graph,
        and a bound instance is returned.

        Args:
            data: Dictionary containing the data (should include @id)

        Returns:
            A Pydantic model instance bound to the graph

        Example:
            >>> profile = builder.from_json({
            ...     "@id": "https://example.org/alice",
            ...     "name": "Alice",
            ...     "age": 30
            ... })
        """
        # Create the model instance first (validates data)
        instance = self._shape_type(**data)

        # Get the subject IRI
        subject = data.get("@id") or data.get("id")
        if not subject:
            from rdflib import BNode
            subject = str(BNode())  # Generate a blank node

        # Add triples to the graph
        self._add_to_graph(instance, subject)

        # Bind to graph if it's a LinkedDataObject
        if hasattr(instance, "bind_to_graph"):
            instance.bind_to_graph(self._graph, subject)

        return instance

    def match_subject(
        self,
        predicate: Optional[URIRef] = None,
        object: Optional[URIRef | Literal] = None,
    ) -> Iterator[T]:
        """
        Find all subjects matching the given predicate and/or object.

        Args:
            predicate: Optional predicate to match
            object: Optional object to match

        Yields:
            Pydantic model instances for each matching subject

        Example:
            >>> # Find all people
            >>> people = builder.match_subject(
            ...     RDF.type,
            ...     URIRef("http://xmlns.com/foaf/0.1/Person")
            ... )
        """
        seen = set()

        for subject in self._graph.subjects(predicate, object):
            if subject in seen:
                continue
            seen.add(subject)

            subject_str = str(subject)
            data = self._extract_subject_data(subject)

            instance = self._shape_type(**data)

            if hasattr(instance, "bind_to_graph"):
                instance.bind_to_graph(self._graph, subject_str)

            yield instance

    def match_object(
        self,
        subject: Optional[URIRef] = None,
        predicate: Optional[URIRef] = None,
    ) -> Iterator[T]:
        """
        Find all objects matching the given subject and/or predicate,
        then return LDOs for those objects (assumes they are IRIs).

        Args:
            subject: Optional subject to match
            predicate: Optional predicate to match

        Yields:
            Pydantic model instances for each matching object that is an IRI

        Example:
            >>> # Find all people Alice knows
            >>> friends = builder.match_object(
            ...     URIRef("https://example.org/alice"),
            ...     URIRef("http://xmlns.com/foaf/0.1/knows")
            ... )
        """
        seen = set()

        for obj in self._graph.objects(subject, predicate):
            if not isinstance(obj, URIRef):
                continue  # Skip literals and blank nodes

            if obj in seen:
                continue
            seen.add(obj)

            subject_str = str(obj)
            data = self._extract_subject_data(obj)

            instance = self._shape_type(**data)

            if hasattr(instance, "bind_to_graph"):
                instance.bind_to_graph(self._graph, subject_str)

            yield instance

    def write(self, *graphs: str) -> "LdoBuilder[T]":
        """
        Specify which graphs new triples should be written to.

        Args:
            *graphs: Graph IRIs to write to

        Returns:
            A new LdoBuilder configured to write to the specified graphs

        Example:
            >>> builder.write("https://example.org/graph1").from_json(data)
        """
        return LdoBuilder(
            self._graph,
            self._shape_type,
            self._context,
            list(graphs),
        )

    def _extract_subject_data(self, subject: URIRef) -> dict[str, Any]:
        """
        Extract all data for a subject from the graph.

        Args:
            subject: The subject to extract data for

        Returns:
            Dictionary with @id and all properties
        """
        data: dict[str, Any] = {"@id": str(subject)}

        # Get field alias mappings and type info from the shape type
        alias_to_field: dict[str, str] = {}
        field_is_list: dict[str, bool] = {}
        
        for field_name, field_info in self._shape_type.model_fields.items():
            alias = field_info.alias or field_name
            alias_to_field[alias] = field_name
            
            # Check if the field annotation indicates a list type
            annotation = field_info.annotation
            annotation_str = str(annotation) if annotation else ""
            field_is_list[field_name] = "list[" in annotation_str.lower()

        # Extract all predicates for this subject
        for _, predicate, obj in self._graph.triples((subject, None, None)):
            pred_str = str(predicate)

            # Find the field name for this predicate
            field_name = alias_to_field.get(pred_str, pred_str)

            # Convert RDF term to Python value
            value = self._rdf_to_value(obj)

            # Handle multiple values
            if field_name in data:
                existing = data[field_name]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    data[field_name] = [existing, value]
            else:
                # If the field expects a list, wrap single values in a list
                if field_is_list.get(field_name, False):
                    data[field_name] = [value]
                else:
                    data[field_name] = value

        return data

    def _rdf_to_value(self, obj: Any) -> Any:
        """Convert an RDF term to a Python value."""
        if isinstance(obj, Literal):
            return obj.toPython()
        elif isinstance(obj, URIRef):
            return str(obj)
        else:
            return str(obj)

    def _add_to_graph(self, instance: T, subject: str) -> None:
        """
        Add a model instance's data to the graph.

        Args:
            instance: The Pydantic model instance
            subject: The subject IRI
        """
        subject_ref = URIRef(subject)

        for field_name, field_info in self._shape_type.model_fields.items():
            if field_name == "id":
                continue

            # Get the predicate IRI from alias
            predicate_iri = field_info.alias or field_name
            if not predicate_iri.startswith("http"):
                continue

            predicate = URIRef(predicate_iri)

            # Get the value
            value = getattr(instance, field_name, None)
            if value is None:
                continue

            # Add triples
            if isinstance(value, list):
                for item in value:
                    obj = self._value_to_rdf(item)
                    if obj is not None:
                        self._graph.add((subject_ref, predicate, obj))
            else:
                obj = self._value_to_rdf(value)
                if obj is not None:
                    self._graph.add((subject_ref, predicate, obj))

    def _value_to_rdf(self, value: Any) -> Optional[URIRef | Literal]:
        """Convert a Python value to an RDF term."""
        if value is None:
            return None

        # If it's a model with subject_iri, use that
        if hasattr(value, "subject_iri"):
            iri = value.subject_iri
            return URIRef(iri) if iri else None

        # If it looks like an IRI
        if isinstance(value, str):
            if value.startswith("http://") or value.startswith("https://"):
                return URIRef(value)
            return Literal(value)

        return Literal(value)
