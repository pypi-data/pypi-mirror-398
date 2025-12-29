"""
Meeting Shape

Based on the meeting vocabulary used in SolidOS.
Meetings are a core feature in SolidOS for scheduling and collaboration.

Namespaces used:
- meeting: http://www.w3.org/ns/pim/meeting#
- cal: http://www.w3.org/2002/12/cal/ical#
- dcterms: http://purl.org/dc/terms/
- foaf: http://xmlns.com/foaf/0.1/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
MEETING = "http://www.w3.org/ns/pim/meeting#"
ICAL = "http://www.w3.org/2002/12/cal/ical#"
DCTERMS = "http://purl.org/dc/terms/"
FOAF = "http://xmlns.com/foaf/0.1/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Meeting(BaseModel):
    """
    A meeting or scheduled event.
    
    Used in SolidOS for scheduling meetings between users.
    Supports attendees, location, and calendar integration.
    
    Properties:
        id: Meeting URI
        name: Meeting title
        description: Meeting description/agenda
        start: Start date/time (ISO 8601)
        end: End date/time (ISO 8601)
        location: Meeting location (physical or URL)
        organizer: WebID of the organizer
        attendee: List of attendee WebIDs
        status: Meeting status
    
    Example:
        >>> from pyldo.shapes import Meeting
        >>> 
        >>> meeting = Meeting(
        ...     name="Project Kickoff",
        ...     description="Initial planning meeting",
        ...     start="2024-01-20T14:00:00Z",
        ...     end="2024-01-20T15:00:00Z",
        ...     location="https://meet.jit.si/solid-project",
        ...     organizer="https://alice.pod/profile/card#me",
        ...     attendee=["https://bob.pod/profile/card#me"]
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Meeting URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (meeting:Meeting)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/pim/meeting#name",
        description="Meeting title/name"
    )
    
    # Alternative name field (some apps use dcterms:title)
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Meeting title (alternative)"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/description",
        description="Meeting description or agenda"
    )
    
    # Time
    start: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#dtstart",
        description="Start date/time (ISO 8601)"
    )
    
    end: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#dtend",
        description="End date/time (ISO 8601)"
    )
    
    duration: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#duration",
        description="Duration (ISO 8601 duration format)"
    )
    
    # Location
    location: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#location",
        description="Meeting location (physical address or URL)"
    )
    
    # Participants
    organizer: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#organizer",
        description="WebID of the meeting organizer"
    )
    
    attendee: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#attendee",
        description="WebIDs of meeting attendees"
    )
    
    # Status
    status: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#status",
        description="Meeting status (CONFIRMED, TENTATIVE, CANCELLED)"
    )
    
    # Recurrence
    rrule: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#rrule",
        description="Recurrence rule (iCal RRULE format)"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the meeting was created"
    )
    
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When the meeting was last modified"
    )
    
    # Related resources
    attachment: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#attach",
        description="Attached files or resources"
    )
    
    # Notes/comments
    comment: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#comment",
        description="Comments or notes about the meeting"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class MeetingStatus:
    """Constants for meeting status values."""
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"


# Rebuild models
Meeting.model_rebuild()
