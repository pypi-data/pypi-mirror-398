"""
Pre-built shapes for common Solid data types.

This module provides ready-to-use Pydantic models for common Solid Pod data shapes.
These shapes are based on schemas from ShapeRepo (shaperepo.com) and standard
Solid specifications.

Instead of writing ShEx schemas manually, you can import these shapes directly:

Example:
    >>> from pyldo.shapes import SolidProfile, Chat, Contact, Task, Note
    >>> from pyldo import LdoDataset
    >>> 
    >>> dataset = LdoDataset()
    >>> # Load profile data...
    >>> profile = dataset.using(SolidProfile).from_subject(webid)
    >>> print(profile.name)

Available Shapes:
    Profile & Identity:
        - SolidProfile: WebID profile with name, storage, inbox, etc.
        - TrustedApp: Trusted application with origin and modes
        - Address: Postal address (vcard)
    
    Social & Content:
        - Post: Blog posts and notes (Dublin Core/SIOC)
        - SocialMediaPosting: Rich social media posts (Schema.org)
        - Note: Simple notes (lighter than Post)
        - NoteFolder: Folder of notes
    
    Chat & Messaging:
        - Chat: Basic chat/conversation
        - LongChat: Chat spanning multiple files (for large conversations)
        - ChatMessage: Individual chat message
        - ChatParticipation: Chat participant
    
    Notifications (LDN):
        - Notification: Linked Data Notification (Activity Streams 2.0)
        - Inbox: Container for notifications
        - ActivityType: Constants for activity types (Create, Like, Follow, etc.)
    
    Calendar & Tasks:
        - Event: Calendar event (iCalendar)
        - Task: Todo item (iCalendar VTODO)
        - Meeting: Meeting (SolidOS compatible)
        - EventStatus: Constants for event status
        - TaskStatus: Constants for task status
        - MeetingStatus: Constants for meeting status
    
    Files & Media:
        - File: Generic file metadata
        - Image: Image with EXIF-style metadata
        - Video: Video file metadata
        - Document: Document metadata (PDF, Word, etc.)
    
    Type Index (App Interoperability):
        - TypeIndex: Type index document
        - TypeRegistration: Data type registration for discovery
    
    Access Control (WAC):
        - Authorization: Access control rule
        - AccessMode: Constants for Read/Write/Append/Control
        - AgentClass: Constants for public/authenticated access
    
    Bookmarks:
        - Bookmark: Saved bookmark/link
        - BookmarkFolder: Folder of bookmarks
    
    Contacts:
        - Contact: Address book contact
        - AddressBook: Collection of contacts
        - ContactGroup: Group of contacts
        - Email: Email address entry
        - Phone: Phone number entry
    
    Preferences:
        - Preference: Single preference/setting
        - PreferencesFile: App preferences file
        - GlobalPreferences: Cross-app user preferences
    
    Project Management:
        - Project: Project with tasks, issues, milestones
        - Milestone: Project milestone
        - ProjectStatus: Constants for project status
    
    Location:
        - Place: Physical location or venue
        - GeoCoordinates: Lat/long coordinates
        - CheckIn: Location check-in
    
    Issue Tracking:
        - Issue: Bug report or feature request
        - IssueComment: Comment on an issue
        - IssueStatus: Constants for issue status
        - IssuePriority: Constants for priority levels
        - IssueType: Constants for issue types (bug, feature, etc.)

For custom shapes, you can still use the `pyldo generate` command with ShEx files.
"""

from .authorization import AccessMode, AgentClass, Authorization
from .bookmark import Bookmark, BookmarkFolder
from .chat import Chat, ChatMessage, ChatParticipation, LongChat
from .contact import AddressBook, Contact, ContactGroup, Email, Phone
from .event import Event, EventStatus, Task, TaskStatus
from .issue import Issue, IssueComment, IssuePriority, IssueStatus, IssueType
from .location import CheckIn, GeoCoordinates, Place
from .media import Document, File, Image, Video
from .meeting import Meeting, MeetingStatus
from .note import Note, NoteFolder
from .notification import ActivityType, Inbox, Notification
from .post import Post, SocialMediaPosting
from .preferences import GlobalPreferences, Preference, PreferencesFile
from .project import Milestone, Project, ProjectStatus
from .solid_profile import Address, SolidProfile, TrustedApp
from .type_index import TypeIndex, TypeRegistration

__all__ = [
    # Solid Profile shapes
    "SolidProfile",
    "TrustedApp",
    "Address",
    # Social media / blog shapes
    "Post",
    "SocialMediaPosting",
    # Note shapes
    "Note",
    "NoteFolder",
    # Chat shapes
    "Chat",
    "LongChat",
    "ChatMessage",
    "ChatParticipation",
    # Notification shapes (LDN)
    "Notification",
    "Inbox",
    "ActivityType",
    # Calendar & Task shapes
    "Event",
    "EventStatus",
    "Task",
    "TaskStatus",
    "Meeting",
    "MeetingStatus",
    # File & Media shapes
    "File",
    "Image",
    "Video",
    "Document",
    # Type Index shapes (app interoperability)
    "TypeIndex",
    "TypeRegistration",
    # Authorization (WAC) shapes
    "Authorization",
    "AccessMode",
    "AgentClass",
    # Bookmark shapes
    "Bookmark",
    "BookmarkFolder",
    # Contact shapes
    "Contact",
    "AddressBook",
    "ContactGroup",
    "Email",
    "Phone",
    # Preferences shapes
    "Preference",
    "PreferencesFile",
    "GlobalPreferences",
    # Project management shapes
    "Project",
    "Milestone",
    "ProjectStatus",
    # Location shapes
    "Place",
    "GeoCoordinates",
    "CheckIn",
    # Issue tracking shapes
    "Issue",
    "IssueComment",
    "IssueStatus",
    "IssuePriority",
    "IssueType",
]

