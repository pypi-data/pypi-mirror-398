"""
SolidProfile Shape

Based on the ShapeRepo solidProfile schema:
https://shaperepo.com/schemas/solidProfile

This shape represents a WebID profile document with properties like:
- Basic info: name, photo, homepage
- Solid-specific: storage locations, inbox
- Contact: addresses, emails
- Social: trusted apps, knows (friends)

Namespaces used:
- foaf: http://xmlns.com/foaf/0.1/
- vcard: http://www.w3.org/2006/vcard/ns#
- pim: http://www.w3.org/ns/pim/space#
- solid: http://www.w3.org/ns/solid/terms#
- ldp: http://www.w3.org/ns/ldp#
- acl: http://www.w3.org/ns/auth/acl#
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants for convenience
FOAF = "http://xmlns.com/foaf/0.1/"
VCARD = "http://www.w3.org/2006/vcard/ns#"
PIM = "http://www.w3.org/ns/pim/space#"
SOLID = "http://www.w3.org/ns/solid/terms#"
LDP = "http://www.w3.org/ns/ldp#"
ACL = "http://www.w3.org/ns/auth/acl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Address(BaseModel):
    """
    Postal address (vcard:Address).
    
    Based on vCard ontology for representing postal addresses.
    
    Example:
        >>> address = Address(
        ...     street_address="123 Main St",
        ...     locality="Springfield",
        ...     region="IL",
        ...     postal_code="62701",
        ...     country_name="USA"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Address node IRI"
    )
    
    street_address: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#street-address",
        description="Street address"
    )
    
    locality: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#locality",
        description="City or locality"
    )
    
    region: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#region",
        description="State, province, or region"
    )
    
    postal_code: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#postal-code",
        description="Postal or ZIP code"
    )
    
    country_name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#country-name",
        description="Country name"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class TrustedApp(BaseModel):
    """
    Trusted application for a Solid pod.
    
    Represents an application that has been granted certain access modes
    to the user's pod.
    
    Example:
        >>> app = TrustedApp(
        ...     origin="https://my-app.example.com",
        ...     mode=["http://www.w3.org/ns/auth/acl#Read", "http://www.w3.org/ns/auth/acl#Write"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Trusted app node IRI"
    )
    
    origin: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#origin",
        description="Origin URL of the trusted application"
    )
    
    mode: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#mode",
        description="Access modes granted (acl:Read, acl:Write, acl:Append, acl:Control)"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class SolidProfile(BaseModel):
    """
    WebID Profile for a Solid Pod user.
    
    Based on the ShapeRepo solidProfile schema. This represents the user's
    WebID document containing identity information and Solid-specific
    configuration.
    
    Properties:
        id: The WebID URI (e.g., https://alice.solidcommunity.net/profile/card#me)
        name: Full name (foaf:name)
        fn: Formatted name from vCard (vcard:fn)
        nickname: Nickname (foaf:nick)
        img: Profile image URL (foaf:img)
        has_photo: Profile photo URL (vcard:hasPhoto)
        homepage: Personal homepage URL (foaf:homepage)
        storage: Pod storage locations (pim:storage)
        inbox: LDP inbox container (ldp:inbox)
        preferences_file: User preferences file (pim:preferencesFile)
        account: Solid account URL (solid:account)
        private_type_index: Private type index URL
        public_type_index: Public type index URL
        has_address: Postal addresses
        has_email: Email addresses
        has_telephone: Phone numbers
        knows: WebIDs of friends/contacts
        trusted_app: Authorized applications
    
    Example:
        >>> from pyldo import LdoDataset
        >>> from pyldo.shapes import SolidProfile
        >>> 
        >>> dataset = LdoDataset()
        >>> await client.get_resource(webid, dataset)
        >>> 
        >>> profile = dataset.using(SolidProfile).from_subject(webid)
        >>> print(f"Name: {profile.name}")
        >>> print(f"Storage: {profile.storage}")
        >>> print(f"Inbox: {profile.inbox}")
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="WebID URI"
    )
    
    # RDF type (foaf:Person, etc.)
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (typically foaf:Person)"
    )
    
    # Basic identity - FOAF
    name: Optional[str] = Field(
        default=None,
        alias="http://xmlns.com/foaf/0.1/name",
        description="Full name"
    )
    
    nickname: Optional[str] = Field(
        default=None,
        alias="http://xmlns.com/foaf/0.1/nick",
        description="Nickname"
    )
    
    img: Optional[str] = Field(
        default=None,
        alias="http://xmlns.com/foaf/0.1/img",
        description="Profile image URL"
    )
    
    homepage: Optional[str] = Field(
        default=None,
        alias="http://xmlns.com/foaf/0.1/homepage",
        description="Personal homepage URL"
    )
    
    # vCard properties
    fn: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#fn",
        description="Formatted name (vCard)"
    )
    
    has_photo: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasPhoto",
        description="Profile photo URL"
    )
    
    has_address: Optional[list["Address"]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasAddress",
        description="Postal addresses"
    )
    
    has_email: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasEmail",
        description="Email addresses (as mailto: URIs or objects)"
    )
    
    has_telephone: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#hasTelephone",
        description="Phone numbers (as tel: URIs or objects)"
    )
    
    organization_name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#organization-name",
        description="Organization name"
    )
    
    role: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#role",
        description="Role or job title"
    )
    
    note: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2006/vcard/ns#note",
        description="Notes or bio"
    )
    
    # Solid-specific properties
    storage: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/pim/space#storage",
        description="Pod storage root URLs"
    )
    
    preferences_file: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/pim/space#preferencesFile",
        description="User preferences file URL"
    )
    
    inbox: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/ldp#inbox",
        description="LDP inbox container URL"
    )
    
    account: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#account",
        description="Solid account URL"
    )
    
    oidc_issuer: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#oidcIssuer",
        description="OIDC identity provider URL"
    )
    
    private_type_index: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#privateTypeIndex",
        description="Private type index URL"
    )
    
    public_type_index: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#publicTypeIndex",
        description="Public type index URL"
    )
    
    trusted_app: Optional[list["TrustedApp"]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#trustedApp",
        description="Trusted applications with access to the pod"
    )
    
    # Social connections
    knows: Optional[list[str]] = Field(
        default=None,
        alias="http://xmlns.com/foaf/0.1/knows",
        description="WebIDs of known contacts/friends"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models for forward references
Address.model_rebuild()
TrustedApp.model_rebuild()
SolidProfile.model_rebuild()
