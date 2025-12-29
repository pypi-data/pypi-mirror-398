"""
Bookmark Shape

For storing bookmarks/favorites in a Solid Pod.
Based on common bookmark vocabularies used in the Solid ecosystem.

Namespaces used:
- bookm: http://www.w3.org/2002/01/bookmark#
- dcterms: http://purl.org/dc/terms/
- foaf: http://xmlns.com/foaf/0.1/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
BOOKMARK = "http://www.w3.org/2002/01/bookmark#"
DCTERMS = "http://purl.org/dc/terms/"
FOAF = "http://xmlns.com/foaf/0.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Bookmark(BaseModel):
    """
    A saved bookmark/favorite.
    
    Bookmarks allow users to save and organize links in their Pod.
    Compatible with SolidOS bookmarks and other Solid bookmark apps.
    
    Properties:
        id: Bookmark URI
        title: Title/name of the bookmark
        recalls: The URL being bookmarked
        created: When the bookmark was created
        creator: Who created the bookmark
        topic: Tags or categories
    
    Example:
        >>> from pyldo.shapes import Bookmark
        >>> 
        >>> bookmark = Bookmark(
        ...     title="Solid Project",
        ...     recalls="https://solidproject.org",
        ...     created="2024-01-15T10:30:00Z",
        ...     topic=["solid", "decentralized-web"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Bookmark URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (bookm:Bookmark)"
    )
    
    # The URL being bookmarked
    recalls: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/01/bookmark#recalls",
        description="The URL being bookmarked"
    )
    
    # Metadata
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Title of the bookmark"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/description",
        description="Description or notes about the bookmark"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the bookmark was created (ISO 8601)"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the bookmark was last modified (ISO 8601)"
    )
    
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="WebID of who created the bookmark"
    )
    
    # Organization
    topic: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/01/bookmark#hasTopic",
        description="Tags or topics for organizing bookmarks"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class BookmarkFolder(BaseModel):
    """
    A folder/collection of bookmarks.
    
    Allows organizing bookmarks into hierarchical folders.
    
    Properties:
        id: Folder URI
        title: Folder name
        contains: Bookmarks or subfolders in this folder
    
    Example:
        >>> folder = BookmarkFolder(
        ...     title="Development Resources",
        ...     contains=["https://pod/bookmarks/1", "https://pod/bookmarks/2"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Folder URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Folder name"
    )
    
    contains: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/ldp#contains",
        description="Bookmarks or subfolders in this folder"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Bookmark.model_rebuild()
BookmarkFolder.model_rebuild()
