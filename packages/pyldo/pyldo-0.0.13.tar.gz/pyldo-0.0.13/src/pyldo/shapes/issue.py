"""
Issue Shape

For bug tracking and feature requests in Solid Pods.
Compatible with project management workflows.

Namespaces used:
- schema: http://schema.org/
- dcterms: http://purl.org/dc/terms/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SCHEMA = "http://schema.org/"
DCTERMS = "http://purl.org/dc/terms/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class IssueStatus:
    """Constants for issue status values."""
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WONT_FIX = "wont-fix"
    DUPLICATE = "duplicate"


class IssuePriority:
    """Constants for issue priority values."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType:
    """Constants for issue type values."""
    BUG = "bug"
    FEATURE = "feature"
    ENHANCEMENT = "enhancement"
    TASK = "task"
    QUESTION = "question"
    DOCUMENTATION = "documentation"


class Issue(BaseModel):
    """
    A bug report or feature request.
    
    For tracking issues in projects stored in Solid Pods.
    
    Properties:
        id: Issue URI
        title: Issue title
        description: Detailed description
        issue_type: Type (bug, feature, enhancement, etc.)
        status: Current status (open, in-progress, resolved, closed)
        priority: Priority level (critical, high, medium, low)
        reporter: Who reported the issue (WebID)
        assignee: Who is assigned to fix it (WebID)
        project: Related project
        labels: Labels/tags
        created: When the issue was created
        updated: When last updated
        closed: When the issue was closed
    
    Example:
        >>> from pyldo.shapes import Issue, IssueStatus, IssuePriority, IssueType
        >>> 
        >>> issue = Issue(
        ...     title="Login button not working on mobile",
        ...     description="When tapping the login button on iOS Safari...",
        ...     issue_type=IssueType.BUG,
        ...     status=IssueStatus.OPEN,
        ...     priority=IssuePriority.HIGH,
        ...     reporter="https://alice.pod/profile/card#me",
        ...     labels=["mobile", "authentication"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Issue URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    # Basic info
    title: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Issue title"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Detailed description of the issue"
    )
    
    # Classification
    issue_type: Optional[str] = Field(
        default=None,
        alias="http://schema.org/additionalType",
        description="Type (bug, feature, enhancement, etc.)"
    )
    
    status: Optional[str] = Field(
        default=None,
        alias="http://schema.org/status",
        description="Current status"
    )
    
    priority: Optional[str] = Field(
        default=None,
        alias="http://schema.org/priority",
        description="Priority level"
    )
    
    # People
    reporter: Optional[str] = Field(
        default=None,
        alias="http://schema.org/author",
        description="Who reported the issue (WebID)"
    )
    
    assignee: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/participant",
        description="Who is assigned to work on it (WebIDs)"
    )
    
    # Relationships
    project: Optional[str] = Field(
        default=None,
        alias="http://schema.org/isPartOf",
        description="Related project"
    )
    
    milestone: Optional[str] = Field(
        default=None,
        alias="http://schema.org/significantLink",
        description="Target milestone"
    )
    
    related_issues: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/relatedLink",
        description="Related issues"
    )
    
    blocks: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/isBasedOn",
        description="Issues this blocks"
    )
    
    blocked_by: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/citation",
        description="Issues blocking this"
    )
    
    # Labels/tags
    labels: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Labels/tags"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the issue was created"
    )
    
    updated: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the issue was last updated"
    )
    
    closed: Optional[str] = Field(
        default=None,
        alias="http://schema.org/endDate",
        description="When the issue was closed"
    )
    
    # Resolution
    resolution: Optional[str] = Field(
        default=None,
        alias="http://schema.org/result",
        description="How the issue was resolved"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class IssueComment(BaseModel):
    """
    A comment on an issue.
    
    Properties:
        id: Comment URI
        content: Comment text
        author: Who wrote the comment (WebID)
        created: When the comment was posted
        issue: The issue this comment is on
    
    Example:
        >>> comment = IssueComment(
        ...     content="I can reproduce this on iOS 17.2",
        ...     author="https://bob.pod/profile/card#me",
        ...     issue="https://pod/issues/123"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Comment URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:Comment)"
    )
    
    content: Optional[str] = Field(
        default=None,
        alias="http://schema.org/text",
        description="Comment text"
    )
    
    author: Optional[str] = Field(
        default=None,
        alias="http://schema.org/author",
        description="Who wrote the comment (WebID)"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the comment was posted"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the comment was edited"
    )
    
    issue: Optional[str] = Field(
        default=None,
        alias="http://schema.org/about",
        description="The issue this comment is on"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Issue.model_rebuild()
IssueComment.model_rebuild()
