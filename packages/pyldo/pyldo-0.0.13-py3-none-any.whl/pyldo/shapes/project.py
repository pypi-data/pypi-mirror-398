"""
Project Shape

For project management in Solid Pods.
Links tasks, issues, milestones, and team members.

Namespaces used:
- schema: http://schema.org/
- dcterms: http://purl.org/dc/terms/
- foaf: http://xmlns.com/foaf/0.1/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SCHEMA = "http://schema.org/"
DCTERMS = "http://purl.org/dc/terms/"
FOAF = "http://xmlns.com/foaf/0.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class ProjectStatus:
    """Constants for project status values."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(BaseModel):
    """
    A project for organizing work.
    
    Projects can contain tasks, issues, milestones, and link to team members.
    
    Properties:
        id: Project URI
        name: Project name
        description: Project description
        status: Project status (planning, active, completed, etc.)
        start_date: When the project starts
        end_date: Target completion date
        owner: Project owner (WebID)
        members: Team members (WebIDs)
        tasks: Related tasks
        issues: Related issues
        repository: Link to code repository
    
    Example:
        >>> from pyldo.shapes import Project, ProjectStatus
        >>> 
        >>> project = Project(
        ...     name="Solid App v2.0",
        ...     description="Major redesign of the Solid app",
        ...     status=ProjectStatus.ACTIVE,
        ...     start_date="2024-01-01",
        ...     end_date="2024-06-30",
        ...     owner="https://alice.pod/profile/card#me"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Project URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:Project)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Project name"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Project description"
    )
    
    # Status
    status: Optional[str] = Field(
        default=None,
        alias="http://schema.org/status",
        description="Project status"
    )
    
    # Dates
    start_date: Optional[str] = Field(
        default=None,
        alias="http://schema.org/startDate",
        description="Project start date"
    )
    
    end_date: Optional[str] = Field(
        default=None,
        alias="http://schema.org/endDate",
        description="Target completion date"
    )
    
    # People
    owner: Optional[str] = Field(
        default=None,
        alias="http://schema.org/founder",
        description="Project owner (WebID)"
    )
    
    members: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/member",
        description="Team members (WebIDs)"
    )
    
    # Related items
    tasks: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/hasPart",
        description="Tasks in this project"
    )
    
    issues: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/subjectOf",
        description="Issues related to this project"
    )
    
    milestones: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/significantLink",
        description="Project milestones"
    )
    
    # External links
    repository: Optional[str] = Field(
        default=None,
        alias="http://schema.org/codeRepository",
        description="Link to code repository"
    )
    
    homepage: Optional[str] = Field(
        default=None,
        alias="http://schema.org/url",
        description="Project homepage URL"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the project was created"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the project was last modified"
    )
    
    # Tags
    tags: Optional[list[str]] = Field(
        default=None,
        alias="http://schema.org/keywords",
        description="Project tags"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Milestone(BaseModel):
    """
    A project milestone.
    
    Properties:
        id: Milestone URI
        name: Milestone name
        description: Milestone description
        due_date: Target date
        completed: Whether the milestone is complete
    
    Example:
        >>> milestone = Milestone(
        ...     name="Beta Release",
        ...     due_date="2024-03-15",
        ...     completed=False
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Milestone URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Milestone name"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Milestone description"
    )
    
    due_date: Optional[str] = Field(
        default=None,
        alias="http://schema.org/endDate",
        description="Target date"
    )
    
    completed: Optional[bool] = Field(
        default=None,
        alias="http://schema.org/status",
        description="Whether the milestone is complete"
    )
    
    project: Optional[str] = Field(
        default=None,
        alias="http://schema.org/isPartOf",
        description="Parent project"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Project.model_rebuild()
Milestone.model_rebuild()
