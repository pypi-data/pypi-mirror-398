"""
RDF Serializers for pyldo.

Provides serialization to various RDF formats:
- Turtle
- N-Triples
- JSON-LD
- SPARQL UPDATE (for transaction changes)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from .graph import RdfGraph
    from .transaction import TransactionChanges


def to_turtle(graph: "RdfGraph", prefixes: Optional[dict[str, str]] = None) -> str:
    """
    Serialize an RDF graph to Turtle format.

    Args:
        graph: The RDF graph to serialize
        prefixes: Optional dictionary of prefix -> namespace URI mappings

    Returns:
        Turtle-formatted string

    Example:
        >>> turtle = to_turtle(graph, {"foaf": "http://xmlns.com/foaf/0.1/"})
    """
    if prefixes:
        for prefix, namespace in prefixes.items():
            graph.bind(prefix, namespace)

    return graph.graph.serialize(format="turtle")


def to_ntriples(graph: "RdfGraph") -> str:
    """
    Serialize an RDF graph to N-Triples format.

    N-Triples is a simple, line-based format with no prefixes.

    Args:
        graph: The RDF graph to serialize

    Returns:
        N-Triples formatted string
    """
    return graph.graph.serialize(format="ntriples")


def to_jsonld(
    graph: "RdfGraph",
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Serialize an RDF graph to JSON-LD format.

    Args:
        graph: The RDF graph to serialize
        context: Optional JSON-LD context to use

    Returns:
        JSON-LD as a dictionary

    Example:
        >>> jsonld = to_jsonld(graph, {"name": "http://xmlns.com/foaf/0.1/name"})
    """
    # Serialize to JSON-LD string
    jsonld_str = graph.graph.serialize(format="json-ld")

    # Parse the string to a dict
    result = json.loads(jsonld_str)

    # If context provided, we could potentially compact the output
    # For now, just add the context if provided
    if context and isinstance(result, dict):
        result["@context"] = context

    return result


def to_sparql_update(changes: "TransactionChanges") -> str:
    """
    Generate a SPARQL UPDATE query from transaction changes.

    The generated query will DELETE removed triples and INSERT added triples.

    Args:
        changes: The transaction changes containing added and removed triples

    Returns:
        SPARQL UPDATE string

    Example:
        >>> update = to_sparql_update(transaction.changes)
        >>> # DELETE DATA { <s> <p> "old" . }
        >>> # INSERT DATA { <s> <p> "new" . }
    """
    parts = []

    # Generate DELETE clause for removed triples
    if changes.removed:
        delete_triples = _triples_to_turtle_body(changes.removed)
        if delete_triples:
            parts.append(f"DELETE DATA {{\n{delete_triples}}}")

    # Generate INSERT clause for added triples
    if changes.added:
        insert_triples = _triples_to_turtle_body(changes.added)
        if insert_triples:
            parts.append(f"INSERT DATA {{\n{insert_triples}}}")

    if not parts:
        return "# No changes"

    return ";\n".join(parts)


def _triples_to_turtle_body(triples: list[tuple]) -> str:
    """
    Convert a list of triples to Turtle-like syntax for SPARQL.

    Args:
        triples: List of (subject, predicate, object) tuples

    Returns:
        String representation suitable for SPARQL DATA blocks
    """
    from rdflib import BNode, Literal, URIRef

    lines = []
    for subject, predicate, obj in triples:
        # Format subject
        if isinstance(subject, URIRef):
            s = f"<{subject}>"
        elif isinstance(subject, BNode):
            s = f"_:{subject}"
        else:
            s = str(subject)

        # Format predicate
        if isinstance(predicate, URIRef):
            p = f"<{predicate}>"
        else:
            p = str(predicate)

        # Format object
        if isinstance(obj, URIRef):
            o = f"<{obj}>"
        elif isinstance(obj, BNode):
            o = f"_:{obj}"
        elif isinstance(obj, Literal):
            # Handle literals with proper escaping
            value = str(obj).replace("\\", "\\\\").replace('"', '\\"')
            if obj.datatype:
                o = f'"{value}"^^<{obj.datatype}>'
            elif obj.language:
                o = f'"{value}"@{obj.language}'
            else:
                o = f'"{value}"'
        else:
            o = f'"{obj}"'

        lines.append(f"  {s} {p} {o} .")

    return "\n".join(lines) + "\n" if lines else ""


def serialize(
    graph: "RdfGraph",
    format: str = "turtle",
    **kwargs: Any,
) -> str:
    """
    Serialize an RDF graph to the specified format.

    Args:
        graph: The RDF graph to serialize
        format: Output format (turtle, ntriples, json-ld)
        **kwargs: Additional format-specific arguments

    Returns:
        Serialized RDF as a string (or dict for JSON-LD)
    """
    format_lower = format.lower().replace("-", "")

    if format_lower in ("turtle", "ttl"):
        return to_turtle(graph, kwargs.get("prefixes"))
    elif format_lower in ("ntriples", "nt"):
        return to_ntriples(graph)
    elif format_lower in ("jsonld", "json"):
        result = to_jsonld(graph, kwargs.get("context"))
        return json.dumps(result, indent=2)
    else:
        # Fall back to rdflib's serializer
        return graph.graph.serialize(format=format)
