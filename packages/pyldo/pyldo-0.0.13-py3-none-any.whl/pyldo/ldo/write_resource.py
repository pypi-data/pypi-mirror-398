"""
Write Resource Binding - Specify target resource for LDO modifications.

This module provides the ResourceBinder class that enables binding
LinkedDataObject modifications to a specific resource URI.

In Solid, data is stored across multiple resources (documents). This
binding mechanism lets you specify which resource should receive
the changes when you modify an LDO.

Example:
    >>> from pyldo.ldo import ResourceBinder
    >>> 
    >>> # Create a resource binder
    >>> binder = ResourceBinder(solid_client)
    >>> 
    >>> # Bind modifications to a specific resource
    >>> person = binder.using(PersonShapeType).from_subject(subject_uri)
    >>> person._bind_to_resource("https://pod.example.org/profile")
    >>> 
    >>> # Modify and write
    >>> person.name = "New Name"
    >>> await binder.write(person)  # Writes to bound resource
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Optional,
    TypeVar,
)

from pydantic import BaseModel
from rdflib import Graph, URIRef

if TYPE_CHECKING:
    from ..solid import SolidClient


T = TypeVar("T", bound=BaseModel)


@dataclass
class ResourceBinding:
    """Information about a resource binding for an LDO."""
    
    # The resource URI where changes should be written
    resource_uri: str
    
    # Subject URI within the resource
    subject_uri: str
    
    # Whether this is a new resource or existing
    is_new: bool = False
    
    # Track which properties have been modified
    modified_properties: set[str] = field(default_factory=set)
    
    # Original values for change tracking
    original_values: dict[str, Any] = field(default_factory=dict)


class WriteResourceBindingMixin:
    """
    Mixin that adds resource binding capabilities to LinkedDataObject.
    
    This mixin should be applied to LinkedDataObject subclasses to enable
    write resource binding functionality.
    
    Example:
        >>> class BoundPerson(Person, WriteResourceBindingMixin):
        ...     pass
        >>> 
        >>> person = BoundPerson(name="Alice")
        >>> person._bind_to_resource("https://pod.example.org/profile")
        >>> print(person._bound_resource)  # Shows binding info
    """
    
    _binding: Optional[ResourceBinding] = None
    _binder: Optional["ResourceBinder"] = None
    
    def _bind_to_resource(
        self,
        resource_uri: str,
        subject_uri: Optional[str] = None,
        is_new: bool = False,
    ) -> None:
        """
        Bind this LDO to a specific resource for writing.
        
        Args:
            resource_uri: The resource URI where changes will be written
            subject_uri: Subject URI within the resource (defaults to resource_uri)
            is_new: Whether this is a new resource being created
        """
        self._binding = ResourceBinding(
            resource_uri=resource_uri,
            subject_uri=subject_uri or resource_uri,
            is_new=is_new,
        )
        
        # Capture original values for change tracking
        if hasattr(self, "model_dump"):
            self._binding.original_values = self.model_dump()
    
    def _unbind_resource(self) -> None:
        """Remove resource binding from this LDO."""
        self._binding = None
    
    @property
    def _bound_resource(self) -> Optional[str]:
        """Get the bound resource URI, if any."""
        return self._binding.resource_uri if self._binding else None
    
    @property
    def _has_binding(self) -> bool:
        """Check if this LDO has a resource binding."""
        return self._binding is not None
    
    def _mark_modified(self, property_name: str) -> None:
        """Mark a property as modified."""
        if self._binding:
            self._binding.modified_properties.add(property_name)
    
    def _get_modified_triples(self) -> list[tuple[URIRef, URIRef, Any]]:
        """
        Get RDF triples for modified properties.
        
        Returns:
            List of (subject, predicate, object) tuples
        """
        if not self._binding:
            return []
        
        # This would use the context to map property names to predicates
        # and generate proper RDF triples
        triples = []
        subject = URIRef(self._binding.subject_uri)
        
        for prop_name in self._binding.modified_properties:
            if hasattr(self, prop_name):
                value = getattr(self, prop_name)
                # In full implementation, map prop_name to predicate
                # and convert value to proper RDF term
                pass
        
        return triples


class ResourceBinder(Generic[T]):
    """
    Manages resource bindings for LDO objects.
    
    ResourceBinder provides methods to create LDO instances that are
    bound to specific Solid resources, enabling targeted writes.
    
    Example:
        >>> binder = ResourceBinder(solid_client, dataset)
        >>> 
        >>> # Create bound instance for existing resource
        >>> person = binder.from_resource(
        ...     resource_uri="https://pod.example.org/profile/card",
        ...     subject_uri="https://pod.example.org/profile/card#me",
        ...     shape_type=PersonShapeType,
        ... )
        >>> 
        >>> # Modify and write
        >>> person.name = "Alice Updated"
        >>> await binder.write(person)
    """
    
    def __init__(
        self,
        solid_client: Optional["SolidClient"] = None,
        dataset: Optional[Any] = None,  # LdoDataset
    ):
        """
        Initialize the resource binder.
        
        Args:
            solid_client: Optional SolidClient for fetching/writing resources
            dataset: Optional LdoDataset for local operations
        """
        self.solid_client = solid_client
        self.dataset = dataset
        self._tracked_objects: dict[str, Any] = {}  # Track bound objects
    
    async def from_resource(
        self,
        resource_uri: str,
        subject_uri: str,
        shape_type: Any,  # ShapeType[T]
    ) -> T:
        """
        Create a bound LDO instance from an existing resource.
        
        Args:
            resource_uri: The resource document URI
            subject_uri: The subject URI within the document
            shape_type: ShapeType for the data shape
        
        Returns:
            LDO instance bound to the resource
        """
        # Fetch the resource if we have a client
        if self.solid_client:
            content = await self.solid_client.get(resource_uri)
            
            # Parse into graph
            graph = Graph()
            graph.parse(data=content, format="turtle", publicID=resource_uri)
            
            # Add to dataset
            if self.dataset:
                for triple in graph:
                    self.dataset.graph.graph.add(triple)
        
        # Build the object
        obj = self.dataset.using(shape_type.type_class).from_subject(subject_uri)
        
        # Apply binding mixin dynamically
        self._apply_binding(obj, resource_uri, subject_uri, is_new=False)
        
        # Track the object
        self._tracked_objects[subject_uri] = obj
        
        return obj
    
    def create_bound(
        self,
        resource_uri: str,
        subject_uri: str,
        shape_type: Any,
        initial_data: Optional[dict[str, Any]] = None,
    ) -> T:
        """
        Create a new bound LDO instance for a new resource.
        
        Args:
            resource_uri: The resource document URI to create
            subject_uri: The subject URI within the document
            shape_type: ShapeType for the data shape
            initial_data: Initial property values
        
        Returns:
            New LDO instance bound to the resource
        """
        # Create instance
        obj = shape_type.type_class(**(initial_data or {}))
        
        # Apply binding
        self._apply_binding(obj, resource_uri, subject_uri, is_new=True)
        
        # Track
        self._tracked_objects[subject_uri] = obj
        
        return obj
    
    def _apply_binding(
        self,
        obj: Any,
        resource_uri: str,
        subject_uri: str,
        is_new: bool,
    ) -> None:
        """Apply resource binding to an object."""
        # Add binding attributes
        obj._binding = ResourceBinding(
            resource_uri=resource_uri,
            subject_uri=subject_uri,
            is_new=is_new,
        )
        obj._binder = self
        
        # Capture original values
        if hasattr(obj, "model_dump"):
            obj._binding.original_values = obj.model_dump()
    
    async def write(
        self,
        obj: T,
        create_if_missing: bool = True,
    ) -> bool:
        """
        Write changes from a bound LDO to its resource.
        
        Args:
            obj: The bound LDO object to write
            create_if_missing: Create resource if it doesn't exist
        
        Returns:
            True if write was successful
        
        Raises:
            ValueError: If object is not bound to a resource
        """
        binding = getattr(obj, "_binding", None)
        if not binding:
            raise ValueError("Object is not bound to a resource")
        
        if not self.solid_client:
            raise ValueError("No SolidClient configured")
        
        # Generate turtle for the object
        turtle_content = self._serialize_to_turtle(obj, binding)
        
        # Write to resource
        if binding.is_new or create_if_missing:
            await self.solid_client.put(
                binding.resource_uri,
                data=turtle_content,
                content_type="text/turtle",
            )
        else:
            # Use PATCH for existing resources
            await self.solid_client.patch(
                binding.resource_uri,
                data=turtle_content,
                content_type="text/turtle",
            )
        
        # Reset modified tracking
        binding.modified_properties.clear()
        binding.is_new = False
        
        if hasattr(obj, "model_dump"):
            binding.original_values = obj.model_dump()
        
        return True
    
    def _serialize_to_turtle(
        self,
        obj: Any,
        binding: ResourceBinding,
    ) -> str:
        """
        Serialize a bound object to Turtle format.
        
        Args:
            obj: The LDO object
            binding: The resource binding
        
        Returns:
            Turtle formatted string
        """
        graph = Graph()
        subject = URIRef(binding.subject_uri)
        
        # Get model data
        data = obj.model_dump() if hasattr(obj, "model_dump") else {}
        
        # Get context for predicate mapping
        context = getattr(obj, "_context", {})
        type_map = getattr(obj, "_type_map", {})
        
        # Add type triple
        if hasattr(obj, "_rdf_type"):
            from rdflib import RDF
            graph.add((subject, RDF.type, URIRef(obj._rdf_type)))
        
        # Add property triples
        for prop_name, value in data.items():
            if value is None:
                continue
            
            # Map property to predicate
            predicate = None
            if prop_name in context:
                pred_def = context[prop_name]
                if isinstance(pred_def, dict) and "@id" in pred_def:
                    predicate = URIRef(pred_def["@id"])
                elif isinstance(pred_def, str):
                    predicate = URIRef(pred_def)
            
            if not predicate:
                # Skip properties without mapping
                continue
            
            # Convert value to RDF term
            from rdflib import Literal
            if isinstance(value, str):
                if value.startswith("http://") or value.startswith("https://"):
                    graph.add((subject, predicate, URIRef(value)))
                else:
                    graph.add((subject, predicate, Literal(value)))
            elif isinstance(value, (int, float, bool)):
                graph.add((subject, predicate, Literal(value)))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        if item.startswith("http://") or item.startswith("https://"):
                            graph.add((subject, predicate, URIRef(item)))
                        else:
                            graph.add((subject, predicate, Literal(item)))
        
        return graph.serialize(format="turtle")
    
    async def write_all(self) -> dict[str, bool]:
        """
        Write all tracked objects that have been modified.
        
        Returns:
            Dict mapping subject URIs to write success status
        """
        results = {}
        
        for subject_uri, obj in self._tracked_objects.items():
            binding = getattr(obj, "_binding", None)
            if binding and binding.modified_properties:
                try:
                    results[subject_uri] = await self.write(obj)
                except Exception as e:
                    results[subject_uri] = False
            else:
                results[subject_uri] = True  # No changes needed
        
        return results
    
    def get_tracked(self, subject_uri: str) -> Optional[T]:
        """
        Get a tracked object by subject URI.
        
        Args:
            subject_uri: The subject URI
        
        Returns:
            The tracked object or None
        """
        return self._tracked_objects.get(subject_uri)
    
    def track(self, obj: T) -> None:
        """
        Start tracking an object for batch writes.
        
        Args:
            obj: The bound LDO object to track
        """
        binding = getattr(obj, "_binding", None)
        if binding:
            self._tracked_objects[binding.subject_uri] = obj
    
    def untrack(self, subject_uri: str) -> None:
        """
        Stop tracking an object.
        
        Args:
            subject_uri: The subject URI to stop tracking
        """
        self._tracked_objects.pop(subject_uri, None)
    
    def clear_tracking(self) -> None:
        """Stop tracking all objects."""
        self._tracked_objects.clear()
