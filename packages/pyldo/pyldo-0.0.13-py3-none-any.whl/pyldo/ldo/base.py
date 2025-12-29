"""
LinkedDataObject base class.

This module provides the base class that bridges Pydantic models with RDF graphs.
Generated Pydantic models can work with this to enable bidirectional sync
between Python objects and RDF triples.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict
from rdflib import Literal, URIRef

if TYPE_CHECKING:
    from ..dataset.graph import RdfGraph


class LinkedDataObject(BaseModel):
    """
    Base class for Linked Data Objects.

    This class extends Pydantic's BaseModel to add RDF-specific functionality:
    - Tracks the associated RDF graph
    - Tracks the subject IRI this object represents
    - Provides methods for syncing changes back to the graph

    Generated Pydantic models can inherit from this to get LDO capabilities.

    Example:
        >>> class PersonShape(LinkedDataObject):
        ...     name: str = Field(..., alias="http://xmlns.com/foaf/0.1/name")
        ...     age: Optional[int] = Field(None, alias="http://xmlns.com/foaf/0.1/age")
        >>> 
        >>> # Create from graph
        >>> person = PersonShape.from_graph(graph, "https://example.org/alice")
        >>> print(person.name)
        >>> 
        >>> # Modify and sync back
        >>> person.name = "Alicia"
        >>> person.sync_to_graph()
    """

    # Class-level attributes for RDF mapping
    _rdf_type: ClassVar[Optional[str]] = None  # rdf:type IRI for this shape
    _shape_iri: ClassVar[Optional[str]] = None  # ShEx shape IRI

    # Instance-level tracking (private attributes)
    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        arbitrary_types_allowed=True,
    )

    # These are stored as private attributes, not fields
    _graph: Optional["RdfGraph"] = None
    _subject: Optional[str] = None
    _context: Optional[dict[str, Any]] = None

    def __init__(self, **data: Any):
        """Initialize the LinkedDataObject."""
        # Extract private attributes before passing to Pydantic
        graph = data.pop("_graph", None)
        subject = data.pop("_subject", None)
        context = data.pop("_context", None)

        super().__init__(**data)

        # Store private attributes
        object.__setattr__(self, "_graph", graph)
        object.__setattr__(self, "_subject", subject)
        object.__setattr__(self, "_context", context)

    @property
    def subject_iri(self) -> Optional[str]:
        """Get the subject IRI this object represents."""
        # Try the @id field first
        id_value = getattr(self, "id", None)
        if id_value:
            return id_value
        return self._subject

    @property
    def graph(self) -> Optional["RdfGraph"]:
        """Get the associated RDF graph."""
        return self._graph

    def bind_to_graph(self, graph: "RdfGraph", subject: str) -> None:
        """
        Bind this object to an RDF graph.

        Args:
            graph: The RDF graph to bind to
            subject: The subject IRI this object represents
        """
        object.__setattr__(self, "_graph", graph)
        object.__setattr__(self, "_subject", subject)

    def sync_to_graph(self) -> None:
        """
        Synchronize this object's current state to the RDF graph.

        This will update the graph to match the object's current property values.
        Requires the object to be bound to a graph.

        Raises:
            RuntimeError: If not bound to a graph
        """
        if self._graph is None or self._subject is None:
            raise RuntimeError("Object is not bound to a graph")

        subject = URIRef(self._subject)

        # Get all field aliases (predicate IRIs) from the model
        for field_name, field_info in self.model_fields.items():
            if field_name == "id":
                continue  # Skip the @id field

            # Get the predicate IRI from the alias
            predicate_iri = field_info.alias or field_name
            if not predicate_iri.startswith("http"):
                continue  # Skip non-IRI aliases

            predicate = URIRef(predicate_iri)

            # Get the current value
            value = getattr(self, field_name, None)

            # Remove existing triples for this predicate
            for existing in list(self._graph.objects(subject, predicate)):
                self._graph.remove((subject, predicate, existing))

            # Add new value(s)
            if value is not None:
                if isinstance(value, list):
                    for item in value:
                        obj = self._value_to_rdf(item)
                        if obj is not None:
                            self._graph.add((subject, predicate, obj))
                else:
                    obj = self._value_to_rdf(value)
                    if obj is not None:
                        self._graph.add((subject, predicate, obj))

    def _value_to_rdf(self, value: Any) -> Optional[URIRef | Literal]:
        """
        Convert a Python value to an RDF term.

        Args:
            value: The Python value to convert

        Returns:
            An RDF term (URIRef or Literal), or None if conversion fails
        """
        if value is None:
            return None

        # If it's another LinkedDataObject, use its subject IRI
        if isinstance(value, LinkedDataObject):
            iri = value.subject_iri
            return URIRef(iri) if iri else None

        # If it's a string that looks like an IRI, make it a URIRef
        if isinstance(value, str):
            if value.startswith("http://") or value.startswith("https://"):
                return URIRef(value)
            return Literal(value)

        # Otherwise, create a Literal
        return Literal(value)

    @classmethod
    def from_graph(
        cls,
        graph: "RdfGraph",
        subject: str,
        context: Optional[dict[str, Any]] = None,
    ) -> "LinkedDataObject":
        """
        Create a LinkedDataObject from an RDF graph.

        Args:
            graph: The RDF graph containing the data
            subject: The subject IRI to extract data for
            context: Optional JSON-LD context for mapping

        Returns:
            A new LinkedDataObject populated with data from the graph
        """
        from rdflib import URIRef

        subject_ref = URIRef(subject)
        data: dict[str, Any] = {"@id": subject}

        # Get all triples for this subject
        for _, predicate, obj in graph.triples((subject_ref, None, None)):
            pred_str = str(predicate)

            # Find the field that maps to this predicate
            field_name = None
            for name, field_info in cls.model_fields.items():
                alias = field_info.alias or name
                if alias == pred_str:
                    field_name = name
                    break

            if field_name is None:
                # No matching field, store with predicate as key
                field_name = pred_str

            # Convert RDF term to Python value
            if isinstance(obj, Literal):
                value = obj.toPython()
            elif isinstance(obj, URIRef):
                value = str(obj)
            else:
                value = str(obj)

            # Handle multiple values (lists)
            if field_name in data:
                existing = data[field_name]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    data[field_name] = [existing, value]
            else:
                data[field_name] = value

        # Create the object
        instance = cls(**data)
        instance.bind_to_graph(graph, subject)
        return instance

    def to_dict(self, by_alias: bool = True) -> dict[str, Any]:
        """
        Convert to a dictionary.

        Args:
            by_alias: If True, use field aliases (predicate IRIs) as keys

        Returns:
            Dictionary representation of the object
        """
        return self.model_dump(by_alias=by_alias, exclude_none=True)

    def to_json(self, by_alias: bool = True, indent: int = 2) -> str:
        """
        Convert to a JSON string.

        Args:
            by_alias: If True, use field aliases (predicate IRIs) as keys
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return self.model_dump_json(by_alias=by_alias, exclude_none=True, indent=indent)
