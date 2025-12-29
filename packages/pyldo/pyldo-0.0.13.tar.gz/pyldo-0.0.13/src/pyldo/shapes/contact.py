"""
Contact and AddressBook Shapes

Based on vCard ontology for storing contacts in Solid Pods.
http://www.w3.org/2006/vcard/ns#

These shapes are compatible with SolidOS contacts and other
Solid address book applications.

Namespaces used:
- vcard: http://www.w3.org/2006/vcard/ns#
- foaf: http://xmlns.com/foaf/0.1/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
VCARD = "http://www.w3.org/2006/vcard/ns#"
FOAF = "http://xmlns.com/foaf/0.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Email(BaseModel):
    """
    An email address entry.
    
    Properties:
        id: Email node URI
        value: The email address (as mailto: URI)
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Email node URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="Email type (vcard:Home, vcard:Work, etc.)"
    )
    
    value: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#value",
        description="Email address as mailto: URI"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Phone(BaseModel):
    """
    A phone number entry.
    
    Properties:
        id: Phone node URI
        value: The phone number (as tel: URI)
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Phone node URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="Phone type (vcard:Home, vcard:Work, vcard:Cell, etc.)"
    )
    
    value: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#value",
        description="Phone number as tel: URI"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Contact(BaseModel):
    """
    A contact/person in an address book.
    
    Based on vCard vocabulary. Compatible with SolidOS contacts app.
    
    Properties:
        id: Contact URI
        fn: Full formatted name
        given_name: First name
        family_name: Last name
        nickname: Nickname
        organization_name: Company/organization
        role: Job title/role
        has_email: Email addresses
        has_telephone: Phone numbers
        has_address: Postal addresses
        has_photo: Profile photo URL
        url: Website URL
        note: Notes about the contact
        webid: Link to their WebID profile (if they have one)
    
    Example:
        >>> from pyldo.shapes import Contact
        >>> 
        >>> contact = Contact(
        ...     fn="Alice Smith",
        ...     given_name="Alice",
        ...     family_name="Smith",
        ...     organization_name="Solid Project",
        ...     webid="https://alice.solidcommunity.net/profile/card#me"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Contact URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (vcard:Individual)"
    )
    
    # Name fields
    fn: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#fn",
        description="Full formatted name"
    )
    
    given_name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#given-name",
        description="First/given name"
    )
    
    family_name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#family-name",
        description="Last/family name"
    )
    
    additional_name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#additional-name",
        description="Middle name"
    )
    
    honorific_prefix: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#honorific-prefix",
        description="Title prefix (Mr., Dr., etc.)"
    )
    
    honorific_suffix: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#honorific-suffix",
        description="Title suffix (Jr., PhD, etc.)"
    )
    
    nickname: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#nickname",
        description="Nickname"
    )
    
    # Organization
    organization_name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#organization-name",
        description="Company or organization name"
    )
    
    role: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#role",
        description="Job title or role"
    )
    
    # Contact info
    has_email: Optional[list["Email"]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasEmail",
        description="Email addresses"
    )
    
    has_telephone: Optional[list["Phone"]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasTelephone",
        description="Phone numbers"
    )
    
    has_address: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasAddress",
        description="Postal addresses (URIs to Address objects)"
    )
    
    # Media
    has_photo: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasPhoto",
        description="Profile photo URL"
    )
    
    url: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#url",
        description="Website URL"
    )
    
    # Notes
    note: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#note",
        description="Notes about the contact"
    )
    
    # Solid-specific - link to WebID
    webid: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasUID",
        description="Link to their Solid WebID profile"
    )
    
    # Birthday
    bday: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#bday",
        description="Birthday (ISO 8601 date)"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class AddressBook(BaseModel):
    """
    An address book containing contacts.
    
    Properties:
        id: AddressBook URI
        title: Name of the address book
        name_email_index: Index of contacts for quick lookup
        groups_index: Index of contact groups
    
    Example:
        >>> from pyldo.shapes import AddressBook
        >>> 
        >>> address_book = AddressBook(
        ...     title="Personal Contacts",
        ...     name_email_index="https://alice.pod/contacts/index.ttl"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="AddressBook URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (vcard:AddressBook)"
    )
    
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Name of the address book"
    )
    
    name_email_index: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#nameEmailIndex",
        description="Index of contacts for quick lookup"
    )
    
    groups_index: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#groupIndex",
        description="Index of contact groups"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class ContactGroup(BaseModel):
    """
    A group of contacts.
    
    Properties:
        id: Group URI
        fn: Group name
        has_member: Contacts in this group
    
    Example:
        >>> group = ContactGroup(
        ...     fn="Work Colleagues",
        ...     has_member=["https://pod/contacts/alice", "https://pod/contacts/bob"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Group URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (vcard:Group)"
    )
    
    fn: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#fn",
        description="Group name"
    )
    
    has_member: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasMember",
        description="Contacts in this group (URIs)"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models for forward references
Email.model_rebuild()
Phone.model_rebuild()
Contact.model_rebuild()
AddressBook.model_rebuild()
ContactGroup.model_rebuild()
