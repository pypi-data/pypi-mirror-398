"""
Event and Task Shapes

Based on iCalendar/Schema.org vocabularies for calendar events and tasks.
These shapes support calendar apps and todo list applications.

Namespaces used:
- cal: http://www.w3.org/2002/12/cal/ical#
- schema: http://schema.org/
- dcterms: http://purl.org/dc/terms/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
ICAL = "http://www.w3.org/2002/12/cal/ical#"
SCHEMA = "http://schema.org/"
DCTERMS = "http://purl.org/dc/terms/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Event(BaseModel):
    """
    A calendar event.
    
    Based on iCalendar vocabulary for maximum compatibility with
    calendar apps and standards.
    
    Properties:
        id: Event URI
        summary: Event title/name
        description: Detailed description
        start: Start date/time
        end: End date/time
        location: Event location
        organizer: Event organizer
        attendee: Event attendees
        status: Event status
        all_day: Whether it's an all-day event
    
    Example:
        >>> from pyldo.shapes import Event, EventStatus
        >>> 
        >>> event = Event(
        ...     summary="Team Standup",
        ...     description="Daily standup meeting",
        ...     start="2024-01-15T09:00:00Z",
        ...     end="2024-01-15T09:15:00Z",
        ...     location="Conference Room A",
        ...     status=EventStatus.CONFIRMED
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Event URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (cal:Vevent)"
    )
    
    # Basic info
    summary: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#summary",
        description="Event title/summary"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#description",
        description="Detailed event description"
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
        description="Duration (ISO 8601 duration, e.g., PT1H)"
    )
    
    # Location
    location: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#location",
        description="Event location"
    )
    
    url: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#url",
        description="URL for virtual events or more info"
    )
    
    # Participants
    organizer: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#organizer",
        description="Event organizer"
    )
    
    attendee: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#attendee",
        description="Event attendees"
    )
    
    # Status and priority
    status: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#status",
        description="Event status (CONFIRMED, TENTATIVE, CANCELLED)"
    )
    
    priority: Optional[int] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#priority",
        description="Priority (1-9, 1 is highest)"
    )
    
    # Categories/tags
    categories: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#categories",
        description="Event categories/tags"
    )
    
    # Recurrence
    rrule: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#rrule",
        description="Recurrence rule (iCal RRULE)"
    )
    
    # Reminders
    alarm: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#valarm",
        description="Alarm/reminder"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#created",
        description="When the event was created"
    )
    
    last_modified: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#lastModified",
        description="When the event was last modified"
    )
    
    # Unique identifier
    uid: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#uid",
        description="Unique identifier for the event"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Task(BaseModel):
    """
    A task or to-do item.
    
    Based on iCalendar VTODO for compatibility with task management apps.
    
    Properties:
        id: Task URI
        summary: Task title
        description: Task details
        due: Due date/time
        completed: Completion date/time
        status: Task status (NEEDS-ACTION, IN-PROCESS, COMPLETED, CANCELLED)
        priority: Priority level (1-9)
        percent_complete: Completion percentage (0-100)
    
    Example:
        >>> from pyldo.shapes import Task, TaskStatus
        >>> 
        >>> task = Task(
        ...     summary="Review pull request",
        ...     description="Review and merge the new feature PR",
        ...     due="2024-01-16T17:00:00Z",
        ...     priority=2,
        ...     status=TaskStatus.IN_PROCESS
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Task URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (cal:Vtodo)"
    )
    
    # Basic info
    summary: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#summary",
        description="Task title/summary"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#description",
        description="Task description/details"
    )
    
    # Time
    start: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#dtstart",
        description="Start date/time"
    )
    
    due: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#due",
        description="Due date/time"
    )
    
    completed: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#completed",
        description="Completion date/time"
    )
    
    # Status
    status: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#status",
        description="Task status"
    )
    
    percent_complete: Optional[int] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#percentComplete",
        description="Completion percentage (0-100)"
    )
    
    # Priority
    priority: Optional[int] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#priority",
        description="Priority (1-9, 1 is highest)"
    )
    
    # Organization
    categories: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#categories",
        description="Task categories/tags"
    )
    
    # Related
    related_to: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#relatedTo",
        description="Related task or project"
    )
    
    # Assignee
    organizer: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#organizer",
        description="Task creator"
    )
    
    attendee: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#attendee",
        description="Assigned to (WebIDs)"
    )
    
    # Timestamps
    created: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#created",
        description="When the task was created"
    )
    
    last_modified: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#lastModified",
        description="When the task was last modified"
    )
    
    # Unique identifier
    uid: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2002/12/cal/ical#uid",
        description="Unique identifier for the task"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class EventStatus:
    """Constants for event status values."""
    CONFIRMED = "CONFIRMED"
    TENTATIVE = "TENTATIVE"
    CANCELLED = "CANCELLED"


class TaskStatus:
    """Constants for task status values."""
    NEEDS_ACTION = "NEEDS-ACTION"
    IN_PROCESS = "IN-PROCESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# Rebuild models
Event.model_rebuild()
Task.model_rebuild()
