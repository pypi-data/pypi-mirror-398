"""
TypeIndex Shapes

Based on the Solid Type Index specification used for app interoperability.
https://solid.github.io/type-indexes/

TypeIndex enables apps to discover where different types of data are stored.
When an app creates data (e.g., posts, contacts), it registers them in the
user's TypeIndex so other apps can find and use that data.

Every Solid profile has two TypeIndex documents:
- Public TypeIndex: Listed types visible to everyone
- Private TypeIndex: Types only visible to the user

Namespaces used:
- solid: http://www.w3.org/ns/solid/terms#
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SOLID = "http://www.w3.org/ns/solid/terms#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class TypeIndex(BaseModel):
    """
    A TypeIndex document that lists type registrations.
    
    Every Solid Pod has a public and private TypeIndex. Apps register
    data types here so other apps can discover where data is stored.
    
    Properties:
        id: TypeIndex document URI
        type_: RDF types (solid:TypeIndex, solid:ListedDocument or solid:UnlistedDocument)
    
    The TypeIndex itself is just a document marker - the actual registrations
    are separate TypeRegistration resources that reference this index.
    
    Example:
        >>> from pyldo.shapes import TypeIndex
        >>> # The public type index is at profile.public_type_index
        >>> type_index = dataset.using(TypeIndex).from_subject(profile.public_type_index)
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="TypeIndex document URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (solid:TypeIndex, solid:ListedDocument)"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class TypeRegistration(BaseModel):
    """
    A registration linking a data type to its storage location.
    
    TypeRegistrations tell apps where to find specific types of data.
    For example, a registration might say "Contact data is stored in /contacts/".
    
    Properties:
        id: Registration URI
        for_class: The RDF class being registered (e.g., vcard:AddressBook)
        instance: Specific resources containing this class
        instance_container: Containers holding resources of this class
    
    Example:
        >>> from pyldo.shapes import TypeRegistration
        >>> 
        >>> # Register where posts are stored
        >>> registration = TypeRegistration(
        ...     for_class="http://schema.org/SocialMediaPosting",
        ...     instance_container=["https://alice.pod/posts/"]
        ... )
        >>> 
        >>> # Find where contacts are stored
        >>> for reg in type_registrations:
        ...     if reg.for_class == "http://www.w3.org/2006/vcard/ns#AddressBook":
        ...         print(f"Contacts at: {reg.instance_container}")
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Registration URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (solid:TypeRegistration)"
    )
    
    for_class: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#forClass",
        description="The RDF class this registration is for"
    )
    
    instance: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#instance",
        description="Specific resources containing this class"
    )
    
    instance_container: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#instanceContainer",
        description="Containers holding resources of this class"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models for forward references
TypeIndex.model_rebuild()
TypeRegistration.model_rebuild()
