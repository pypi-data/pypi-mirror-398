"""
RDF Dataset module for pyldo.

This module provides RDF graph management, serialization, and transaction support.
It wraps rdflib to provide a clean interface for working with RDF data.

Example:
    >>> from pyldo.dataset import RdfGraph
    >>> 
    >>> graph = RdfGraph()
    >>> graph.parse_turtle('''
    ...     @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    ...     <#me> foaf:name "Alice" .
    ... ''')
    >>> print(graph.to_turtle())
"""

from .graph import RdfGraph
from .serializers import (
    to_jsonld,
    to_ntriples,
    to_sparql_update,
    to_turtle,
)
from .subscribable import (
    DatasetEvent,
    EventType,
    SubscribableDataset,
)
from .transaction import Transaction, TransactionChanges

__all__ = [
    "RdfGraph",
    "Transaction",
    "TransactionChanges",
    "SubscribableDataset",
    "DatasetEvent",
    "EventType",
    "to_turtle",
    "to_ntriples",
    "to_jsonld",
    "to_sparql_update",
]
