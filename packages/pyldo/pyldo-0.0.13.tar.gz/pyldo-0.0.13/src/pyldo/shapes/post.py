"""
Post and SocialMediaPosting Shapes

Based on Schema.org SocialMediaPosting and common Solid chat/blog patterns.
https://schema.org/SocialMediaPosting

This shape is useful for building social applications on Solid,
such as blog posts, social media posts, and chat messages.

Namespaces used:
- schema: https://schema.org/
- dcterms: http://purl.org/dc/terms/
- sioc: http://rdfs.org/sioc/ns#
- foaf: http://xmlns.com/foaf/0.1/
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SCHEMA = "https://schema.org/"
DCTERMS = "http://purl.org/dc/terms/"
SIOC = "http://rdfs.org/sioc/ns#"
FOAF = "http://xmlns.com/foaf/0.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Post(BaseModel):
    """
    A generic post or article.
    
    This is a simplified shape suitable for blog posts, notes, and
    other content items in a Solid pod.
    
    Based on Dublin Core and SIOC vocabularies commonly used in Solid.
    
    Properties:
        id: Post URI
        title: Title of the post (dcterms:title)
        content: Main content/body (sioc:content)
        created: Creation date (dcterms:created)
        modified: Last modified date (dcterms:modified)
        creator: Author WebID (dcterms:creator)
    
    Example:
        >>> from pyldo.shapes import Post
        >>> from pyldo import LdoDataset
        >>> 
        >>> dataset = LdoDataset()
        >>> post = Post(
        ...     title="My First Post",
        ...     content="Hello, Solid world!",
        ...     creator="https://alice.solidcommunity.net/profile/card#me"
        ... )
        >>> dataset.using(Post).create(post, "https://alice.pod/blog/post1")
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Post URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    # Dublin Core properties
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Title of the post"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="Creation date (ISO 8601 format)"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="Last modified date (ISO 8601 format)"
    )
    
    creator: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/creator",
        description="Author WebID"
    )
    
    # SIOC content
    content: Optional[str] = Field(
        default=None,
        alias="http://rdfs.org/sioc/ns#content",
        description="Main content/body text"
    )
    
    # Optional additional properties
    subject: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/subject",
        description="Subject or topic"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/description",
        description="Brief description or summary"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class SocialMediaPosting(BaseModel):
    """
    A social media post (schema.org/SocialMediaPosting).
    
    This is a richer shape based on Schema.org, suitable for
    social networking applications built on Solid.
    
    Properties:
        id: Post URI
        name: Title/name of the post
        article_body: Main content
        date_created: When the post was created
        date_modified: When the post was last updated
        author: Author reference (WebID or Person)
        shared_content: Reference to shared/reposted content
        url: Canonical URL of the post
        image: Image attachment URLs
        comment: Replies/comments on this post
    
    Example:
        >>> from pyldo.shapes import SocialMediaPosting
        >>> 
        >>> post = SocialMediaPosting(
        ...     name="Excited about Solid!",
        ...     article_body="Just deployed my first Solid app. The future is decentralized! 🚀",
        ...     author="https://alice.solidcommunity.net/profile/card#me",
        ...     date_created="2024-01-15T10:30:00Z"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Post URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (typically schema:SocialMediaPosting)"
    )
    
    # Schema.org Article properties
    name: Optional[str] = Field(
        default=None,
        alias="https://schema.org/name",
        description="Title or name of the post"
    )
    
    headline: Optional[str] = Field(
        default=None,
        alias="https://schema.org/headline",
        description="Headline of the post"
    )
    
    article_body: Optional[str] = Field(
        default=None,
        alias="https://schema.org/articleBody",
        description="Main content/body of the post"
    )
    
    text: Optional[str] = Field(
        default=None,
        alias="https://schema.org/text",
        description="Text content (alternative to articleBody)"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="https://schema.org/description",
        description="Brief description or summary"
    )
    
    # Dates
    date_created: Optional[str] = Field(
        default=None,
        alias="https://schema.org/dateCreated",
        description="Date when the post was created (ISO 8601)"
    )
    
    date_modified: Optional[str] = Field(
        default=None,
        alias="https://schema.org/dateModified",
        description="Date when the post was last modified (ISO 8601)"
    )
    
    date_published: Optional[str] = Field(
        default=None,
        alias="https://schema.org/datePublished",
        description="Date when the post was published (ISO 8601)"
    )
    
    # Author and attribution
    author: Optional[str] = Field(
        default=None,
        alias="https://schema.org/author",
        description="Author WebID or reference"
    )
    
    creator: Optional[str] = Field(
        default=None,
        alias="https://schema.org/creator",
        description="Creator WebID (same as author for most cases)"
    )
    
    # URLs and references
    url: Optional[str] = Field(
        default=None,
        alias="https://schema.org/url",
        description="Canonical URL of the post"
    )
    
    shared_content: Optional[str] = Field(
        default=None,
        alias="https://schema.org/sharedContent",
        description="Reference to content being shared/reposted"
    )
    
    # Media
    image: Optional[list[str]] = Field(
        default=None,
        alias="https://schema.org/image",
        description="Image attachment URLs"
    )
    
    video: Optional[list[str]] = Field(
        default=None,
        alias="https://schema.org/video",
        description="Video attachment URLs"
    )
    
    # Social interactions
    comment: Optional[list[str]] = Field(
        default=None,
        alias="https://schema.org/comment",
        description="Comments/replies on this post (URIs)"
    )
    
    comment_count: Optional[int] = Field(
        default=None,
        alias="https://schema.org/commentCount",
        description="Number of comments"
    )
    
    interaction_statistic: Optional[list[str]] = Field(
        default=None,
        alias="https://schema.org/interactionStatistic",
        description="Interaction statistics (likes, shares, etc.)"
    )
    
    # Mentions and tags
    mentions: Optional[list[str]] = Field(
        default=None,
        alias="https://schema.org/mentions",
        description="Entities mentioned in the post (WebIDs)"
    )
    
    keywords: Optional[list[str]] = Field(
        default=None,
        alias="https://schema.org/keywords",
        description="Tags or keywords"
    )
    
    # Thread/conversation
    is_part_of: Optional[str] = Field(
        default=None,
        alias="https://schema.org/isPartOf",
        description="Parent conversation or thread"
    )
    
    in_reply_to: Optional[str] = Field(
        default=None,
        alias="https://schema.org/inReplyTo",
        description="Post this is replying to"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models for forward references
Post.model_rebuild()
SocialMediaPosting.model_rebuild()
