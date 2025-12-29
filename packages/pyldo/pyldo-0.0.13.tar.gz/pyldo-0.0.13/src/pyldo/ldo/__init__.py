"""
Linked Data Objects (LDO) module for pyldo.

This module provides the core LDO functionality:
- LdoDataset: Main entry point for working with linked data
- LdoBuilder: Creates typed objects from RDF graphs
- LinkQuery: Traverse and fetch linked resources across documents
- ResourceBinder: Bind LDO modifications to specific resources
- LdSet: Set-like collection for multi-valued properties
- Helper methods for serialization and graph operations

Example:
    >>> from pyldo.ldo import LdoDataset
    >>> from .ldo.profile_types import ProfileShape
    >>> 
    >>> # Create dataset and load RDF
    >>> dataset = LdoDataset()
    >>> dataset.parse("profile.ttl", format="turtle")
    >>> 
    >>> # Get typed object from graph
    >>> profile = dataset.using(ProfileShape).from_subject("https://pod.example/alice#me")
    >>> 
    >>> # Use like normal Python object
    >>> print(profile.name)
    >>> profile.nick = "alice123"
    >>> 
    >>> # Serialize changes
    >>> print(dataset.to_turtle())
"""

from .base import LinkedDataObject
from .builder import LdoBuilder
from .factory import LdoDataset
from .ldset import LdSet
from .link_query import (
    FetchedResource,
    LinkQuery,
    LinkQueryOptions,
    explore_links,
)
from .methods import (
    change_data,
    commit_data,
    commit_transaction,
    get_graph,
    get_language_preferences,
    get_subject,
    graph_of,
    languages_of,
    match_object,
    match_subject,
    parse_rdf,
    parse_rdf_async,
    rollback_transaction,
    serialize,
    set_language_preferences,
    set_values,
    start_transaction,
    sync_to_graph,
    to_jsonld,
    to_ntriples,
    to_sparql_update,
    to_turtle,
    transaction_changes,
)
from .write_resource import (
    ResourceBinder,
    ResourceBinding,
    WriteResourceBindingMixin,
)

__all__ = [
    # Core
    "LdoDataset",
    "LdoBuilder",
    "LinkedDataObject",
    "LdSet",
    # Link Query
    "LinkQuery",
    "LinkQueryOptions",
    "FetchedResource",
    "explore_links",
    # Write Resource Binding
    "ResourceBinder",
    "ResourceBinding",
    "WriteResourceBindingMixin",
    # Parsing
    "parse_rdf",
    "parse_rdf_async",
    # Serialization
    "get_graph",
    "get_subject",
    "graph_of",
    "serialize",
    "to_turtle",
    "to_ntriples",
    "to_jsonld",
    "to_sparql_update",
    # Language support
    "languages_of",
    "set_language_preferences",
    "get_language_preferences",
    # Set helper
    "set_values",
    # Transactions
    "start_transaction",
    "commit_transaction",
    "rollback_transaction",
    "transaction_changes",
    "sync_to_graph",
    # Change pattern
    "change_data",
    "commit_data",
    # Match helpers
    "match_subject",
    "match_object",
]
