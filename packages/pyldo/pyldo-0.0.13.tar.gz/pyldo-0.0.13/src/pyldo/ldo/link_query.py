"""
Link Query - Traverse and fetch linked resources automatically.

This module provides functionality to follow RDF links across multiple
resources, automatically fetching remote data as needed.

Similar to JavaScript LDO's LinkQuery, this enables traversing
relationships like foaf:knows across multiple Solid Pods.

Example:
    >>> from pyldo.ldo import LinkQuery
    >>> 
    >>> # Create a link query starting from a profile
    >>> query = LinkQuery(
    ...     dataset=my_dataset,
    ...     shape_type=PersonShapeType,
    ...     starting_resource="https://pod.example.org/alice/profile/card",
    ...     starting_subject="https://pod.example.org/alice/profile/card#me",
    ... )
    >>> 
    >>> # Define what to traverse
    >>> result = await query.run({
    ...     "name": True,
    ...     "knows": {
    ...         "name": True,
    ...     }
    ... })
    >>> 
    >>> print(result.name)  # "Alice"
    >>> for friend in result.knows:
    ...     print(friend.name)  # Fetched from remote resources
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
    Union,
)
from urllib.parse import urljoin, urlparse

import httpx
from pydantic import BaseModel
from rdflib import Graph, Namespace, URIRef

from ..dataset import RdfGraph

T = TypeVar("T", bound=BaseModel)

# Common predicates that indicate links to follow
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")


@dataclass
class LinkQueryInput:
    """
    Defines which properties to traverse in a link query.
    
    Can be:
    - True: Include this property's value
    - A nested dict: Traverse into linked resources and include nested properties
    """
    pass


@dataclass
class FetchedResource:
    """A resource that has been fetched during link traversal."""
    
    uri: str
    content: Optional[str] = None
    content_type: str = "text/turtle"
    graph: Optional[Graph] = None
    error: Optional[str] = None
    
    @property
    def is_loaded(self) -> bool:
        return self.graph is not None and self.error is None


@dataclass
class LinkQueryOptions:
    """Options for link query execution."""
    
    # Whether to reload resources that are already cached
    reload: bool = False
    
    # Maximum depth of link traversal
    max_depth: int = 5
    
    # Maximum number of resources to fetch
    max_resources: int = 100
    
    # HTTP client for fetching resources
    http_client: Optional[httpx.AsyncClient] = None
    
    # Callback when a resource is encountered
    on_resource_encountered: Optional[Callable[[str], None]] = None
    
    # Callback when data changes (for subscriptions)
    on_data_changed: Optional[Callable[[Any], None]] = None


class LinkQuery(Generic[T]):
    """
    A query that traverses links across multiple RDF resources.
    
    LinkQuery allows you to define a shape of data to retrieve,
    automatically following links to fetch data from multiple sources.
    
    Example:
        >>> query = LinkQuery(
        ...     dataset=dataset,
        ...     shape_type=PersonShapeType,
        ...     starting_resource="https://pod.example.org/alice/profile",
        ...     starting_subject="https://pod.example.org/alice/profile#me",
        ... )
        >>> 
        >>> result = await query.run({
        ...     "name": True,
        ...     "knows": {
        ...         "name": True,
        ...         "email": True,
        ...     }
        ... })
    """
    
    def __init__(
        self,
        dataset: Any,  # LdoDataset or similar
        shape_type: Any,  # ShapeType[T]
        starting_resource: str,
        starting_subject: str,
        query_input: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize a link query.
        
        Args:
            dataset: The LdoDataset to query and populate
            shape_type: ShapeType defining the shape of objects
            starting_resource: URL of the first resource to fetch
            starting_subject: Subject URI to start traversal from
            query_input: Dict defining which properties to traverse
        """
        self.dataset = dataset
        self.shape_type = shape_type
        self.starting_resource = starting_resource
        self.starting_subject = starting_subject
        self.query_input = query_input or {}
        
        # Track fetched resources
        self._fetched_resources: dict[str, FetchedResource] = {}
        self._subscription_id: Optional[str] = None
    
    async def run(
        self,
        query_input: Optional[dict[str, Any]] = None,
        options: Optional[LinkQueryOptions] = None,
    ) -> T:
        """
        Execute the link query, fetching and traversing resources.
        
        Args:
            query_input: Override the query input for this run
            options: Options for query execution
        
        Returns:
            Typed object with traversed data populated
        """
        opts = options or LinkQueryOptions()
        input_spec = query_input or self.query_input
        
        # Create HTTP client if not provided
        should_close_client = opts.http_client is None
        http_client = opts.http_client or httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
        )
        
        try:
            # Fetch starting resource
            await self._fetch_resource(
                self.starting_resource,
                http_client,
                opts,
            )
            
            # Traverse links based on query input
            await self._traverse_links(
                subject=self.starting_subject,
                query_spec=input_spec,
                http_client=http_client,
                options=opts,
                depth=0,
            )
            
            # Build and return the result object
            return self._build_result()
            
        finally:
            if should_close_client:
                await http_client.aclose()
    
    async def _fetch_resource(
        self,
        uri: str,
        http_client: httpx.AsyncClient,
        options: LinkQueryOptions,
    ) -> FetchedResource:
        """Fetch a single resource and add to dataset."""
        # Check if already fetched
        if uri in self._fetched_resources and not options.reload:
            return self._fetched_resources[uri]
        
        # Check resource limit
        if len(self._fetched_resources) >= options.max_resources:
            return FetchedResource(
                uri=uri,
                error=f"Resource limit ({options.max_resources}) reached",
            )
        
        # Notify callback
        if options.on_resource_encountered:
            options.on_resource_encountered(uri)
        
        # Fetch the resource
        resource = FetchedResource(uri=uri)
        
        try:
            response = await http_client.get(
                uri,
                headers={"Accept": "text/turtle, application/ld+json"},
            )
            response.raise_for_status()
            
            resource.content = response.text
            resource.content_type = response.headers.get("content-type", "text/turtle")
            
            # Parse into graph
            resource.graph = Graph()
            if "json" in resource.content_type:
                resource.graph.parse(data=resource.content, format="json-ld", publicID=uri)
            else:
                resource.graph.parse(data=resource.content, format="turtle", publicID=uri)
            
            # Add to main dataset
            for triple in resource.graph:
                self.dataset.graph.graph.add(triple)
                
        except Exception as e:
            resource.error = str(e)
        
        self._fetched_resources[uri] = resource
        return resource
    
    async def _traverse_links(
        self,
        subject: str,
        query_spec: dict[str, Any],
        http_client: httpx.AsyncClient,
        options: LinkQueryOptions,
        depth: int,
    ) -> None:
        """Recursively traverse links based on query specification."""
        if depth >= options.max_depth:
            return
        
        subject_ref = URIRef(subject)
        
        for prop_name, prop_spec in query_spec.items():
            if prop_spec is True:
                # Just include the value, no traversal needed
                continue
            
            if isinstance(prop_spec, dict):
                # Need to traverse into linked objects
                # Find the predicate for this property
                predicate = self._get_predicate_for_property(prop_name)
                if not predicate:
                    continue
                
                # Get all objects for this predicate
                for obj in self.dataset.graph.graph.objects(subject_ref, predicate):
                    obj_uri = str(obj)
                    
                    # If it's a URI, try to fetch it
                    if obj_uri.startswith("http://") or obj_uri.startswith("https://"):
                        # Determine the resource URI (document, not fragment)
                        resource_uri = obj_uri.split("#")[0]
                        
                        # Fetch the resource
                        await self._fetch_resource(resource_uri, http_client, options)
                        
                        # Recursively traverse
                        await self._traverse_links(
                            subject=obj_uri,
                            query_spec=prop_spec,
                            http_client=http_client,
                            options=options,
                            depth=depth + 1,
                        )
    
    def _get_predicate_for_property(self, prop_name: str) -> Optional[URIRef]:
        """Get the RDF predicate URI for a property name."""
        # Check if shape_type has context with mapping
        if hasattr(self.shape_type, "context") and self.shape_type.context:
            context = self.shape_type.context
            if prop_name in context:
                prop_def = context[prop_name]
                if isinstance(prop_def, dict) and "@id" in prop_def:
                    return URIRef(prop_def["@id"])
                elif isinstance(prop_def, str):
                    return URIRef(prop_def)
        
        # Common predicate mappings
        common_predicates = {
            "name": FOAF.name,
            "knows": FOAF.knows,
            "mbox": FOAF.mbox,
            "nick": FOAF.nick,
            "homepage": FOAF.homepage,
            "seeAlso": RDFS.seeAlso,
            "sameAs": OWL.sameAs,
        }
        
        return common_predicates.get(prop_name)
    
    def _build_result(self) -> T:
        """Build the result object from the dataset."""
        builder = self.dataset.using(self.shape_type.type_class)
        return builder.from_subject(self.starting_subject)
    
    def from_subject(self) -> T:
        """
        Get the current state of the starting subject.
        
        This returns the object without re-fetching any resources.
        
        Returns:
            Typed object from current dataset state
        """
        return self._build_result()
    
    async def subscribe(self) -> str:
        """
        Subscribe to updates for resources in this query.
        
        Returns:
            Subscription ID for later unsubscription
        """
        import uuid
        self._subscription_id = str(uuid.uuid4())
        # In a full implementation, this would set up WebSocket
        # connections or polling for each fetched resource
        return self._subscription_id
    
    async def unsubscribe(self, subscription_id: Optional[str] = None) -> None:
        """
        Unsubscribe from updates.
        
        Args:
            subscription_id: ID returned from subscribe() (optional)
        """
        self._subscription_id = None
    
    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all update subscriptions."""
        self._subscription_id = None
    
    def get_fetched_resources(self) -> list[str]:
        """
        Get list of resource URIs that have been fetched.
        
        Returns:
            List of resource URIs
        """
        return list(self._fetched_resources.keys())
    
    def get_resource_status(self, uri: str) -> Optional[FetchedResource]:
        """
        Get the status of a fetched resource.
        
        Args:
            uri: Resource URI
        
        Returns:
            FetchedResource info or None if not fetched
        """
        return self._fetched_resources.get(uri)


async def explore_links(
    dataset: Any,
    shape_type: Any,
    starting_resource: str,
    starting_subject: str,
    query_input: dict[str, Any],
    options: Optional[LinkQueryOptions] = None,
) -> None:
    """
    Explore and fetch linked resources.
    
    This is a convenience function that creates a LinkQuery and runs it.
    
    Args:
        dataset: The dataset to populate
        shape_type: ShapeType for the data
        starting_resource: URL of first resource
        starting_subject: Subject URI to start from
        query_input: Dict defining traversal
        options: Optional query options
    """
    query = LinkQuery(
        dataset=dataset,
        shape_type=shape_type,
        starting_resource=starting_resource,
        starting_subject=starting_subject,
        query_input=query_input,
    )
    await query.run(options=options)
