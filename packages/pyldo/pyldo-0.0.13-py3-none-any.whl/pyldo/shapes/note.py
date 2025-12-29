"""
Note Shape

A simple note - lighter weight than Post.
Many Solid apps use notes for quick text storage.

Based on common note-taking vocabularies.

Namespaces used:
- schema: http://schema.org/
- dcterms: http://purl.org/dc/terms/
- sioc: http://rdfs.org/sioc/ns#
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SCHEMA = "http://schema.org/"
DCTERMS = "http://purl.org/dc/terms/"
SIOC = "http://rdfs.org/sioc/ns#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Note(BaseModel):
    """
    A simple note or quick text entry.
    
    Lighter weight than Post - perfect for quick notes, snippets,
    or simple text storage in a Solid Pod.
    
    Properties:
        id: Note URI
        content: The note text content
        title: Optional title/heading
        created: When the note was created
        modified: When the note was last modified
        creator: Who created the note
        tags: Tags/labels for organization
    
    Example:
        >>> from pyldo.shapes import Note
        >>> 
        >>> note = Note(
        ...     title="Meeting Notes",
        ...     content="Discussed project timeline and deliverables.",
        ...     created="2024-01-15T10:30:00Z",
        ...     tags=["work", "meetings"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Note URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:Note)"
    )
    
    # Content
    content: Optional[str] = Field(
        default=None,
        alias="http://schema.org/text",
        description="The note text content"
    )
    
    # Alternative content field (some apps use sioc:content)
    body: Optional[str] = Field(
        default=None,
        alias="http://rdfs.org/sioc/ns#content",
        description="The note body (alternative)"
    )
    
    # Title/name
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Note title or heading"
    )
    
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Note name (alternative)"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the note was created (ISO 8601)"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the note was last modified (ISO 8601)"
    )
    
    # Creator
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="WebID of who created the note"
    )
    
    # Organization
    tags: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Tags or keywords for organization"
    )
    
    # Folder/container
    is_part_of: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/isPartOf",
        description="Parent folder or collection"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class NoteFolder(BaseModel):
    """
    A folder/collection of notes.
    
    Properties:
        id: Folder URI
        title: Folder name
        contains: Notes in this folder
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
        description="Notes in this folder"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Note.model_rebuild()
NoteFolder.model_rebuild()
