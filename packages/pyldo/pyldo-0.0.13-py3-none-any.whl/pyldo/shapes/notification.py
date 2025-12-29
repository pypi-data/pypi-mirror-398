"""
Notification Shapes (Linked Data Notifications)

Based on the LDN (Linked Data Notifications) spec and Activity Streams 2.0.
https://www.w3.org/TR/ldn/
https://www.w3.org/TR/activitystreams-core/

Every Solid Pod has an inbox (ldp:inbox) that receives notifications.
Apps use notifications to communicate with each other and with users.

Namespaces used:
- as: https://www.w3.org/ns/activitystreams#
- ldp: http://www.w3.org/ns/ldp#
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
AS = "https://www.w3.org/ns/activitystreams#"
LDP = "http://www.w3.org/ns/ldp#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class ActivityType:
    """Constants for common Activity Streams activity types."""
    # Core types
    CREATE = "https://www.w3.org/ns/activitystreams#Create"
    UPDATE = "https://www.w3.org/ns/activitystreams#Update"
    DELETE = "https://www.w3.org/ns/activitystreams#Delete"
    
    # Social interactions
    LIKE = "https://www.w3.org/ns/activitystreams#Like"
    FOLLOW = "https://www.w3.org/ns/activitystreams#Follow"
    ACCEPT = "https://www.w3.org/ns/activitystreams#Accept"
    REJECT = "https://www.w3.org/ns/activitystreams#Reject"
    
    # Communication
    ANNOUNCE = "https://www.w3.org/ns/activitystreams#Announce"
    ADD = "https://www.w3.org/ns/activitystreams#Add"
    REMOVE = "https://www.w3.org/ns/activitystreams#Remove"
    INVITE = "https://www.w3.org/ns/activitystreams#Invite"


class Notification(BaseModel):
    """
    A Linked Data Notification (Activity Streams 2.0 Activity).
    
    Notifications are how Solid apps communicate. When you want to tell
    another user or app about something, you send a notification to their inbox.
    
    Properties:
        id: Notification URI
        type_: Activity type (Create, Update, Like, Follow, etc.)
        actor: Who performed the activity (WebID)
        object: What the activity is about (URI or embedded object)
        target: Where the activity is directed
        summary: Human-readable summary
        published: When the notification was created
        updated: When the notification was last updated
    
    Example:
        >>> from pyldo.shapes import Notification, ActivityType
        >>> 
        >>> # Create a "like" notification
        >>> notification = Notification(
        ...     type_=[ActivityType.LIKE],
        ...     actor="https://alice.pod/profile/card#me",
        ...     object="https://bob.pod/posts/1",
        ...     summary="Alice liked your post",
        ...     published="2024-01-15T10:30:00Z"
        ... )
        >>> 
        >>> # Send to Bob's inbox
        >>> requests.post(bob_inbox, data=notification_turtle, headers=auth_headers)
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Notification URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="Activity type (as:Create, as:Like, etc.)"
    )
    
    # Who performed the activity
    actor: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#actor",
        description="WebID of who performed the activity"
    )
    
    # What the activity is about
    object: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#object",
        description="The object of the activity (URI)"
    )
    
    # Where the activity is directed
    target: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#target",
        description="The target of the activity"
    )
    
    # Human-readable info
    summary: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#summary",
        description="Human-readable summary of the activity"
    )
    
    content: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#content",
        description="Content or body of the notification"
    )
    
    name: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#name",
        description="Name/title of the notification"
    )
    
    # Timestamps
    published: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#published",
        description="When the activity was published (ISO 8601)"
    )
    
    updated: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#updated",
        description="When the activity was last updated (ISO 8601)"
    )
    
    # Context/origin
    context: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#context",
        description="Context of the activity (e.g., a conversation)"
    )
    
    origin: Optional[str] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#origin",
        description="Where the activity originated"
    )
    
    # Recipients
    to: Optional[list[str]] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#to",
        description="Primary recipients"
    )
    
    cc: Optional[list[str]] = Field(
        default=None,
        alias="https://www.w3.org/ns/activitystreams#cc",
        description="Secondary recipients"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Inbox(BaseModel):
    """
    A Solid inbox (LDP container for notifications).
    
    Every Solid profile has an inbox where notifications are received.
    The inbox is an LDP container that holds notification resources.
    
    Properties:
        id: Inbox URI
        contains: Notifications in the inbox
    
    Example:
        >>> # Get user's inbox from their profile
        >>> inbox_url = profile.inbox
        >>> 
        >>> # Fetch and parse inbox
        >>> inbox = dataset.using(Inbox).from_subject(inbox_url)
        >>> for notification_uri in inbox.contains:
        ...     # Fetch each notification
        ...     notif = fetch_notification(notification_uri)
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Inbox URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (ldp:Container)"
    )
    
    contains: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/ldp#contains",
        description="Notifications in the inbox"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Notification.model_rebuild()
Inbox.model_rebuild()
