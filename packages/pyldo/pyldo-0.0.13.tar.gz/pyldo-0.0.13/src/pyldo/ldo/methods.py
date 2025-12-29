"""
Helper methods for working with Linked Data Objects.

These functions provide convenient access to common operations
on LDO instances without needing to access internal properties.

This module mirrors the JS LDO helper functions:
- graphOf: Get the graph an LDO belongs to
- languagesOf / setLanguagePreferences: Language tag support
- set: Helper for setting array properties
- startTransaction / commitTransaction / transactionChanges
- toTurtle / toNTriples / toSparqlUpdate / serialize
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, Union

if TYPE_CHECKING:
    from ..dataset.graph import RdfGraph
    from .base import LinkedDataObject
    from .factory import LdoDataset

T = TypeVar("T")


def get_graph(ldo: "LinkedDataObject") -> Optional["RdfGraph"]:
    """
    Get the RDF graph associated with a Linked Data Object.

    Args:
        ldo: A Linked Data Object

    Returns:
        The associated RDF graph, or None if not bound

    Example:
        >>> from pyldo.ldo import get_graph
        >>> graph = get_graph(profile)
    """
    return ldo.graph


def graph_of(ldo: "LinkedDataObject") -> Optional[str]:
    """
    Get the named graph URI that this LDO belongs to.

    In RDF, data can be organized into named graphs. This function
    returns the URI of the graph that the LDO's triples belong to.

    Args:
        ldo: A Linked Data Object

    Returns:
        The graph URI, or None for the default graph

    Example:
        >>> from pyldo.ldo import graph_of
        >>> graph_uri = graph_of(profile)
        >>> print(graph_uri)  # "https://example.com/profile"
    """
    # Check if LDO has a bound graph with a named graph
    if hasattr(ldo, "_graph_uri"):
        return ldo._graph_uri
    return None


def get_subject(ldo: "LinkedDataObject") -> Optional[str]:
    """
    Get the subject IRI of a Linked Data Object.

    Args:
        ldo: A Linked Data Object

    Returns:
        The subject IRI, or None if not bound

    Example:
        >>> from pyldo.ldo import get_subject
        >>> iri = get_subject(profile)
    """
    return ldo.subject_iri


def serialize(
    ldo: "LinkedDataObject",
    format: str = "turtle",
    **kwargs: Any,
) -> str:
    """
    Serialize a Linked Data Object's graph to the specified format.

    Args:
        ldo: A Linked Data Object bound to a graph
        format: Output format (turtle, ntriples, json-ld)
        **kwargs: Additional format-specific arguments

    Returns:
        Serialized RDF as a string

    Raises:
        RuntimeError: If the LDO is not bound to a graph

    Example:
        >>> from pyldo.ldo import serialize
        >>> turtle = serialize(profile, format="turtle")
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")

    from ..dataset.serializers import serialize as _serialize
    return _serialize(graph, format, **kwargs)


def to_turtle(ldo: "LinkedDataObject", prefixes: Optional[dict[str, str]] = None) -> str:
    """
    Serialize a Linked Data Object's graph to Turtle format.

    Args:
        ldo: A Linked Data Object bound to a graph
        prefixes: Optional prefix -> namespace mappings

    Returns:
        Turtle-formatted string
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    return graph.to_turtle(prefixes)


def to_ntriples(ldo: "LinkedDataObject") -> str:
    """
    Serialize a Linked Data Object's graph to N-Triples format.

    Args:
        ldo: A Linked Data Object bound to a graph

    Returns:
        N-Triples formatted string
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    return graph.to_ntriples()


def to_jsonld(
    ldo: "LinkedDataObject",
    context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Serialize a Linked Data Object's graph to JSON-LD format.

    Args:
        ldo: A Linked Data Object bound to a graph
        context: Optional JSON-LD context

    Returns:
        JSON-LD as a dictionary
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    return graph.to_jsonld(context)


def to_sparql_update(ldo: "LinkedDataObject") -> str:
    """
    Generate a SPARQL UPDATE query for the current transaction.

    Args:
        ldo: A Linked Data Object bound to a graph with an active transaction

    Returns:
        SPARQL UPDATE string

    Raises:
        RuntimeError: If not bound to a graph or no transaction is active
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    return graph.to_sparql_update()


def start_transaction(ldo: "LinkedDataObject") -> None:
    """
    Start a transaction on the LDO's graph.

    Args:
        ldo: A Linked Data Object bound to a graph

    Raises:
        RuntimeError: If not bound to a graph or transaction already active
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    graph.start_transaction()


def commit_transaction(ldo: "LinkedDataObject") -> None:
    """
    Commit the transaction on the LDO's graph.

    Args:
        ldo: A Linked Data Object bound to a graph with an active transaction

    Raises:
        RuntimeError: If not bound to a graph or no transaction is active
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    graph.commit_transaction()


def rollback_transaction(ldo: "LinkedDataObject") -> None:
    """
    Rollback the transaction on the LDO's graph.

    Args:
        ldo: A Linked Data Object bound to a graph with an active transaction

    Raises:
        RuntimeError: If not bound to a graph or no transaction is active
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")
    graph.rollback_transaction()


def sync_to_graph(ldo: "LinkedDataObject") -> None:
    """
    Synchronize the LDO's current state to its RDF graph.

    This is a convenience wrapper around ldo.sync_to_graph().

    Args:
        ldo: A Linked Data Object bound to a graph

    Raises:
        RuntimeError: If not bound to a graph
    """
    ldo.sync_to_graph()


# =============================================================================
# Language Tag Support
# =============================================================================


def languages_of(
    ldo: "LinkedDataObject",
    property_name: str,
) -> list[str]:
    """
    Get the available language tags for a property.

    In RDF, literal values can have language tags (e.g., "Hello"@en).
    This function returns all language tags for which a property has values.

    Args:
        ldo: A Linked Data Object
        property_name: The name of the property to check

    Returns:
        List of language tags (e.g., ["en", "de", "fr"])

    Example:
        >>> from pyldo.ldo import languages_of
        >>> langs = languages_of(profile, "name")
        >>> print(langs)  # ["en", "de"]
    """
    graph = ldo.graph
    if graph is None:
        return []

    from rdflib import Literal, URIRef

    subject_uri = ldo.subject_iri
    if not subject_uri:
        return []

    # Get predicate from context
    context = getattr(ldo, "_context", {})
    predicate = None
    if property_name in context:
        pred_def = context[property_name]
        if isinstance(pred_def, dict) and "@id" in pred_def:
            predicate = URIRef(pred_def["@id"])
        elif isinstance(pred_def, str):
            predicate = URIRef(pred_def)

    if not predicate:
        return []

    # Find all language tags for this property
    languages = []
    for obj in graph.graph.objects(URIRef(subject_uri), predicate):
        if isinstance(obj, Literal) and obj.language:
            languages.append(obj.language)

    return list(set(languages))


_language_preferences: list[str] = []


def set_language_preferences(*languages: str) -> None:
    """
    Set the preferred language order for literal values.

    When an LDO property has multiple language-tagged values,
    this preference determines which value is returned first.

    Args:
        *languages: Language tags in order of preference

    Example:
        >>> from pyldo.ldo import set_language_preferences
        >>> set_language_preferences("en", "de", "fr")
        >>> # Now English values will be preferred
    """
    global _language_preferences
    _language_preferences = list(languages)


def get_language_preferences() -> list[str]:
    """
    Get the current language preference order.

    Returns:
        List of language tags in order of preference
    """
    return _language_preferences.copy()


# =============================================================================
# Set Helper
# =============================================================================


def set_values(*values: T) -> list[T]:
    """
    Create a list of values for setting array properties.

    This is a helper function for setting multi-valued properties
    in a clean, explicit way.

    Args:
        *values: Values to include in the list

    Returns:
        List of the provided values

    Example:
        >>> from pyldo.ldo import set_values
        >>> profile.name = set_values("Alice", "Ally")
        >>> # Equivalent to: profile.name = ["Alice", "Ally"]
    """
    return list(values)


# Alias for JS compatibility
set = set_values


# =============================================================================
# Transaction Changes
# =============================================================================


def transaction_changes(ldo: "LinkedDataObject") -> dict[str, Any]:
    """
    Get the changes made during the current transaction.

    Returns a dictionary with 'added' and 'removed' keys containing
    the triples that were added and removed during the transaction.

    Args:
        ldo: A Linked Data Object with an active transaction

    Returns:
        Dictionary with 'added' and 'removed' triple lists

    Example:
        >>> from pyldo.ldo import start_transaction, transaction_changes
        >>> start_transaction(profile)
        >>> profile.name = "New Name"
        >>> profile.sync_to_graph()
        >>> changes = transaction_changes(profile)
        >>> print(changes["added"])
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")

    if not graph.in_transaction:
        return {"added": [], "removed": []}

    # Get changes from the transaction
    tx = graph._transaction
    if tx is None:
        return {"added": [], "removed": []}

    return {
        "added": list(tx.changes.added),
        "removed": list(tx.changes.removed),
    }


# =============================================================================
# Change Data Pattern (matches JS changeData/commitData)
# =============================================================================


def change_data(
    ldo: "LinkedDataObject",
    modifier: Callable[["LinkedDataObject"], None],
) -> "LinkedDataObject":
    """
    Apply changes to an LDO within a transaction context.

    This is a convenience function that:
    1. Starts a transaction if not already in one
    2. Calls the modifier function with the LDO
    3. Syncs changes to the graph

    Args:
        ldo: A Linked Data Object to modify
        modifier: Function that modifies the LDO

    Returns:
        The modified LDO

    Example:
        >>> from pyldo.ldo import change_data
        >>> 
        >>> def update_name(profile):
        ...     profile.name = "New Name"
        >>> 
        >>> profile = change_data(profile, update_name)
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")

    # Start transaction if needed
    was_in_transaction = graph.in_transaction
    if not was_in_transaction:
        graph.start_transaction()

    try:
        # Apply the modification
        modifier(ldo)

        # Sync to graph
        ldo.sync_to_graph()

        return ldo
    except Exception:
        if not was_in_transaction:
            graph.rollback_transaction()
        raise


def commit_data(ldo: "LinkedDataObject") -> dict[str, Any]:
    """
    Commit all pending changes for an LDO.

    This commits the current transaction and returns the changes
    that were applied.

    Args:
        ldo: A Linked Data Object with pending changes

    Returns:
        Dictionary with 'added' and 'removed' changes

    Example:
        >>> from pyldo.ldo import change_data, commit_data
        >>> 
        >>> profile = change_data(profile, lambda p: setattr(p, 'name', 'New'))
        >>> changes = commit_data(profile)
        >>> print(f"Added {len(changes['added'])} triples")
    """
    graph = ldo.graph
    if graph is None:
        raise RuntimeError("LDO is not bound to a graph")

    # Get changes before committing
    changes = transaction_changes(ldo)

    # Commit the transaction
    if graph.in_transaction:
        graph.commit_transaction()

    return changes


# =============================================================================
# Parse RDF - Top-level function
# =============================================================================


def parse_rdf(
    data: str,
    format: str = "turtle",
    base_iri: Optional[str] = None,
) -> "LdoDataset":
    """
    Parse RDF data and return an LdoDataset.

    This is a top-level convenience function that creates an LdoDataset
    and parses the provided RDF data into it.

    Args:
        data: RDF data as a string
        format: Format of the data (turtle, json-ld, ntriples)
        base_iri: Base IRI for relative IRIs

    Returns:
        An LdoDataset containing the parsed data

    Example:
        >>> from pyldo.ldo import parse_rdf
        >>> 
        >>> turtle = '''
        ...     @prefix foaf: <http://xmlns.com/foaf/0.1/> .
        ...     <#me> a foaf:Person ; foaf:name "Alice" .
        ... '''
        >>> 
        >>> dataset = parse_rdf(turtle, base_iri="https://example.com/profile")
        >>> profile = dataset.using(PersonShape).from_subject("#me")
    """
    from .factory import LdoDataset

    dataset = LdoDataset()
    dataset.parse(data, format=format, base=base_iri)
    return dataset


async def parse_rdf_async(
    data: str,
    format: str = "turtle",
    base_iri: Optional[str] = None,
) -> "LdoDataset":
    """
    Async version of parse_rdf for compatibility with async code.

    Args:
        data: RDF data as a string
        format: Format of the data (turtle, json-ld, ntriples)
        base_iri: Base IRI for relative IRIs

    Returns:
        An LdoDataset containing the parsed data
    """
    # Currently just calls the sync version since rdflib is sync
    return parse_rdf(data, format, base_iri)


# =============================================================================
# Match helpers (equivalent to useMatchSubject/useMatchObject)
# =============================================================================


def match_subject(
    dataset: "LdoDataset",
    predicate: str,
    obj: Any,
) -> list[str]:
    """
    Find all subjects that match the given predicate and object.

    This is equivalent to the JS useMatchSubject hook but as a function.

    Args:
        dataset: The LdoDataset to search
        predicate: Predicate URI to match
        obj: Object value to match (URI string or literal)

    Returns:
        List of subject URIs

    Example:
        >>> from pyldo.ldo import match_subject
        >>> people = match_subject(dataset, RDF.type, FOAF.Person)
        >>> for person_uri in people:
        ...     profile = dataset.using(PersonShape).from_subject(person_uri)
    """
    from rdflib import Literal, URIRef

    pred_ref = URIRef(predicate)

    # Determine object type
    if isinstance(obj, str):
        if obj.startswith("http://") or obj.startswith("https://"):
            obj_term = URIRef(obj)
        else:
            obj_term = Literal(obj)
    else:
        obj_term = Literal(obj)

    subjects = []
    for s in dataset.graph.graph.subjects(pred_ref, obj_term):
        subjects.append(str(s))

    return subjects


def match_object(
    dataset: "LdoDataset",
    subject: str,
    predicate: str,
) -> list[Any]:
    """
    Find all objects for the given subject and predicate.

    This is equivalent to the JS useMatchObject hook but as a function.

    Args:
        dataset: The LdoDataset to search
        subject: Subject URI
        predicate: Predicate URI

    Returns:
        List of object values (URIs or literal values)

    Example:
        >>> from pyldo.ldo import match_object
        >>> names = match_object(dataset, "#me", FOAF.name)
        >>> print(names)  # ["Alice", "Ally"]
    """
    from rdflib import Literal, URIRef

    subj_ref = URIRef(subject)
    pred_ref = URIRef(predicate)

    objects = []
    for o in dataset.graph.graph.objects(subj_ref, pred_ref):
        if isinstance(o, Literal):
            objects.append(o.toPython())
        else:
            objects.append(str(o))

    return objects
