"""
Authorization (WAC) Shapes

Based on Web Access Control (WAC) specification for Solid.
https://solid.github.io/web-access-control-spec/

WAC defines how permissions work in Solid. Each resource can have an
associated ACL (Access Control List) that defines who can read, write,
append, or control it.

Namespaces used:
- acl: http://www.w3.org/ns/auth/acl#
- foaf: http://xmlns.com/foaf/0.1/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
ACL = "http://www.w3.org/ns/auth/acl#"
FOAF = "http://xmlns.com/foaf/0.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

# Access mode constants for convenience
class AccessMode:
    """Constants for ACL access modes."""
    READ = "http://www.w3.org/ns/auth/acl#Read"
    WRITE = "http://www.w3.org/ns/auth/acl#Write"
    APPEND = "http://www.w3.org/ns/auth/acl#Append"
    CONTROL = "http://www.w3.org/ns/auth/acl#Control"


class AgentClass:
    """Constants for ACL agent classes."""
    # Any authenticated user
    AUTHENTICATED_AGENT = "http://www.w3.org/ns/auth/acl#AuthenticatedAgent"
    # Anyone (public access)
    AGENT = "http://xmlns.com/foaf/0.1/Agent"


class Authorization(BaseModel):
    """
    An access control authorization rule.
    
    Authorizations define who can do what with a resource. Each authorization
    specifies agents (who), access modes (what), and resources (where).
    
    Properties:
        id: Authorization rule URI
        access_to: The resource this authorization applies to
        default: Container whose contents inherit this authorization
        agent: Specific WebIDs granted access
        agent_group: Groups granted access
        agent_class: Classes of agents (e.g., everyone, authenticated users)
        mode: Access modes granted (Read, Write, Append, Control)
    
    Example:
        >>> from pyldo.shapes import Authorization, AccessMode, AgentClass
        >>> 
        >>> # Grant read access to everyone
        >>> public_read = Authorization(
        ...     access_to="https://alice.pod/public/",
        ...     agent_class=[AgentClass.AGENT],
        ...     mode=[AccessMode.READ]
        ... )
        >>> 
        >>> # Grant full access to owner
        >>> owner_access = Authorization(
        ...     access_to="https://alice.pod/private/",
        ...     agent=["https://alice.pod/profile/card#me"],
        ...     mode=[AccessMode.READ, AccessMode.WRITE, AccessMode.CONTROL]
        ... )
        >>> 
        >>> # Grant write access to a friend
        >>> friend_write = Authorization(
        ...     access_to="https://alice.pod/shared/",
        ...     agent=["https://bob.pod/profile/card#me"],
        ...     mode=[AccessMode.READ, AccessMode.WRITE]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Authorization rule URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (acl:Authorization)"
    )
    
    # What resource(s) this applies to
    access_to: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#accessTo",
        description="The resource this authorization applies to"
    )
    
    default: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#default",
        description="Container whose contents inherit this authorization"
    )
    
    # Who is granted access
    agent: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#agent",
        description="Specific WebIDs granted access"
    )
    
    agent_group: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#agentGroup",
        description="Groups granted access (URIs of vcard:Group resources)"
    )
    
    agent_class: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#agentClass",
        description="Agent classes (acl:AuthenticatedAgent or foaf:Agent for public)"
    )
    
    # What access is granted
    mode: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#mode",
        description="Access modes: Read, Write, Append, Control"
    )
    
    # Origin restrictions (for browser apps)
    origin: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/auth/acl#origin",
        description="Allowed origins for this authorization"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models for forward references
Authorization.model_rebuild()
