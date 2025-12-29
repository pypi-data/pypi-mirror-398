"""
File and Media Metadata Shapes

For storing metadata about files, images, videos, and documents in Solid Pods.
Useful for file manager apps, photo galleries, and media libraries.

Namespaces used:
- schema: http://schema.org/
- dcterms: http://purl.org/dc/terms/
- exif: http://www.w3.org/2003/12/exif/ns#
- nfo: http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SCHEMA = "http://schema.org/"
DCTERMS = "http://purl.org/dc/terms/"
EXIF = "http://www.w3.org/2003/12/exif/ns#"
NFO = "http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class File(BaseModel):
    """
    Generic file metadata.
    
    Base shape for any file stored in a Solid Pod.
    
    Properties:
        id: File URI
        name: File name
        content_type: MIME type
        content_size: File size in bytes
        created: Creation date
        modified: Last modified date
        creator: Who uploaded/created the file
    
    Example:
        >>> from pyldo.shapes import File
        >>> 
        >>> file = File(
        ...     name="document.pdf",
        ...     content_type="application/pdf",
        ...     content_size=1048576,
        ...     created="2024-01-15T10:30:00Z"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="File URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (nfo:FileDataObject)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="File name"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/description",
        description="File description"
    )
    
    # File properties
    content_type: Optional[str] = Field(
        default=None,
        alias="http://schema.org/encodingFormat",
        description="MIME type (e.g., 'application/pdf')"
    )
    
    content_size: Optional[int] = Field(
        default=None,
        alias="http://schema.org/contentSize",
        description="File size in bytes"
    )
    
    # URL to the actual file content
    content_url: Optional[str] = Field(
        default=None,
        alias="http://schema.org/contentUrl",
        description="URL to download the file"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the file was created/uploaded"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the file was last modified"
    )
    
    # Creator/owner
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="WebID of who created/uploaded the file"
    )
    
    # Organization
    tags: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Tags for organization"
    )
    
    is_part_of: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/isPartOf",
        description="Parent folder or collection"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Image(BaseModel):
    """
    Image file metadata with EXIF-style properties.
    
    For photo galleries and image management apps.
    
    Properties:
        id: Image URI
        name: Image filename
        content_type: MIME type (image/jpeg, image/png, etc.)
        width: Image width in pixels
        height: Image height in pixels
        thumbnail: URL to thumbnail version
        date_taken: When the photo was taken
        camera: Camera make/model
        location: Where the photo was taken
    
    Example:
        >>> from pyldo.shapes import Image
        >>> 
        >>> image = Image(
        ...     name="vacation.jpg",
        ...     content_type="image/jpeg",
        ...     width=4032,
        ...     height=3024,
        ...     date_taken="2024-01-15T14:30:00Z",
        ...     location="Paris, France"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Image URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:ImageObject)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Image filename"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Image description/caption"
    )
    
    # File properties
    content_type: Optional[str] = Field(
        default=None,
        alias="http://schema.org/encodingFormat",
        description="MIME type (image/jpeg, image/png, etc.)"
    )
    
    content_size: Optional[int] = Field(
        default=None,
        alias="http://schema.org/contentSize",
        description="File size in bytes"
    )
    
    content_url: Optional[str] = Field(
        default=None,
        alias="http://schema.org/contentUrl",
        description="URL to the full image"
    )
    
    # Dimensions
    width: Optional[int] = Field(
        default=None,
        alias="http://schema.org/width",
        description="Image width in pixels"
    )
    
    height: Optional[int] = Field(
        default=None,
        alias="http://schema.org/height",
        description="Image height in pixels"
    )
    
    # Thumbnail
    thumbnail: Optional[str] = Field(
        default=None,
        alias="http://schema.org/thumbnail",
        description="URL to thumbnail version"
    )
    
    # EXIF-style metadata
    date_taken: Optional[str] = Field(
        default=None,
        alias="http://schema.org/dateCreated",
        description="When the photo was taken"
    )
    
    camera: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2003/12/exif/ns#model",
        description="Camera make/model"
    )
    
    # Location
    location: Optional[str] = Field(
        default=None,
        alias="http://schema.org/contentLocation",
        description="Where the photo was taken"
    )
    
    latitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/latitude",
        description="GPS latitude"
    )
    
    longitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/longitude",
        description="GPS longitude"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When uploaded to Pod"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When last modified"
    )
    
    # Creator
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="WebID of uploader"
    )
    
    # Organization
    tags: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Tags for organization"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Video(BaseModel):
    """
    Video file metadata.
    
    For video libraries and media management apps.
    
    Properties:
        id: Video URI
        name: Video filename
        duration: Video duration
        width: Video width in pixels
        height: Video height in pixels
        thumbnail: URL to thumbnail/poster
    
    Example:
        >>> from pyldo.shapes import Video
        >>> 
        >>> video = Video(
        ...     name="presentation.mp4",
        ...     content_type="video/mp4",
        ...     duration="PT5M30S",  # 5 minutes 30 seconds
        ...     width=1920,
        ...     height=1080
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Video URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:VideoObject)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Video filename"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Video description"
    )
    
    # File properties
    content_type: Optional[str] = Field(
        default=None,
        alias="http://schema.org/encodingFormat",
        description="MIME type (video/mp4, etc.)"
    )
    
    content_size: Optional[int] = Field(
        default=None,
        alias="http://schema.org/contentSize",
        description="File size in bytes"
    )
    
    content_url: Optional[str] = Field(
        default=None,
        alias="http://schema.org/contentUrl",
        description="URL to the video file"
    )
    
    # Video properties
    duration: Optional[str] = Field(
        default=None,
        alias="http://schema.org/duration",
        description="Duration (ISO 8601, e.g., 'PT5M30S')"
    )
    
    width: Optional[int] = Field(
        default=None,
        alias="http://schema.org/width",
        description="Video width in pixels"
    )
    
    height: Optional[int] = Field(
        default=None,
        alias="http://schema.org/height",
        description="Video height in pixels"
    )
    
    # Thumbnail/poster
    thumbnail: Optional[str] = Field(
        default=None,
        alias="http://schema.org/thumbnail",
        description="URL to thumbnail/poster image"
    )
    
    # Timestamps
    date_created: Optional[str] = Field(
        default=None,
        alias="http://schema.org/dateCreated",
        description="When the video was recorded"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When uploaded to Pod"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When last modified"
    )
    
    # Creator
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="WebID of uploader"
    )
    
    # Organization
    tags: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Tags for organization"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Document(BaseModel):
    """
    Document file metadata (PDF, Word, etc.).
    
    Properties:
        id: Document URI
        name: Document filename
        title: Document title
        author: Document author
        page_count: Number of pages
    
    Example:
        >>> from pyldo.shapes import Document
        >>> 
        >>> doc = Document(
        ...     name="report.pdf",
        ...     title="Annual Report 2024",
        ...     author="Alice Smith",
        ...     page_count=42
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Document URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:DigitalDocument)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Document filename"
    )
    
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Document title"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Document description"
    )
    
    # File properties
    content_type: Optional[str] = Field(
        default=None,
        alias="http://schema.org/encodingFormat",
        description="MIME type (application/pdf, etc.)"
    )
    
    content_size: Optional[int] = Field(
        default=None,
        alias="http://schema.org/contentSize",
        description="File size in bytes"
    )
    
    content_url: Optional[str] = Field(
        default=None,
        alias="http://schema.org/contentUrl",
        description="URL to download the document"
    )
    
    # Document properties
    author: Optional[str] = Field(
        default=None,
        alias="http://schema.org/author",
        description="Document author"
    )
    
    page_count: Optional[int] = Field(
        default=None,
        alias="http://schema.org/numberOfPages",
        description="Number of pages"
    )
    
    # Timestamps
    date_published: Optional[str] = Field(
        default=None,
        alias="http://schema.org/datePublished",
        description="Publication date"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When uploaded to Pod"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When last modified"
    )
    
    # Creator (uploader)
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="WebID of uploader"
    )
    
    # Organization
    tags: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Tags for organization"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
File.model_rebuild()
Image.model_rebuild()
Video.model_rebuild()
Document.model_rebuild()
