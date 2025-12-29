"""
PyLDO - Linked Data Objects for Python

Making RDF as easy as working with plain Python objects.

Example:
    >>> from pyldo import LdoDataset, parse_rdf
    >>> from pyldo.shapes import SolidProfile, Post, Chat
    >>> 
    >>> # Use pre-built shapes from pyldo.shapes
    >>> dataset = LdoDataset()
    >>> await client.get_resource(webid, dataset)
    >>> profile = dataset.using(SolidProfile).from_subject(webid)
    >>> print(profile.name)
    >>> print(profile.storage)
    >>> 
    >>> # For custom types, generate from ShEx or LinkML schemas
    >>> from pyldo import parse_shex, parse_linkml, generate_python_types
    >>> 
    >>> # From ShEx
    >>> schema = parse_shex(open("custom.shex").read())
    >>> code = generate_python_types(schema)
    >>> 
    >>> # From LinkML (YAML-based, often easier)
    >>> schema = parse_linkml(open("custom.yaml").read())
    >>> code = generate_python_types(schema)
"""

__version__ = "0.0.11"

# Import main components for convenient access
from .converter import (
    generate_jsonld_context,
    generate_python_types,
    linkml_to_shex,
    parse_linkml,
    parse_shex,
)
from .dataset import (
    DatasetEvent,
    EventType,
    RdfGraph,
    SubscribableDataset,
    Transaction,
    TransactionChanges,
)
from .ldo import (
    # Core
    FetchedResource,
    LdoBuilder,
    LdoDataset,
    LdSet,
    LinkedDataObject,
    LinkQuery,
    LinkQueryOptions,
    ResourceBinder,
    ResourceBinding,
    WriteResourceBindingMixin,
    # Helper functions
    change_data,
    commit_data,
    commit_transaction,
    explore_links,
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
from .solid import (
    FolderData,
    Item,
    SolidAuth,
    SolidClient,
    SolidContainer,
    SolidOidcAuth,
    SolidOidcSession,
    SolidResource,
    SolidSession,
    WebIdProfile,
    # URL utilities
    ensure_trailing_slash,
    fetch_webid_profile,
    get_item_name,
    get_parent_url,
    get_root_url,
    remove_trailing_slash,
)

__all__ = [
    "__version__",
    # Converter / Schema parsing
    "parse_shex",
    "parse_linkml",
    "linkml_to_shex",
    "generate_python_types",
    "generate_jsonld_context",
    # Dataset
    "RdfGraph",
    "Transaction",
    "TransactionChanges",
    "SubscribableDataset",
    "DatasetEvent",
    "EventType",
    # LDO Core
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
    # Solid
    "SolidAuth",
    "SolidSession",
    "SolidOidcAuth",
    "SolidOidcSession",
    "SolidClient",
    "SolidResource",
    "SolidContainer",
    "FolderData",
    "Item",
    "WebIdProfile",
    "fetch_webid_profile",
    # URL utilities
    "get_root_url",
    "get_parent_url",
    "get_item_name",
    "ensure_trailing_slash",
    "remove_trailing_slash",
]
