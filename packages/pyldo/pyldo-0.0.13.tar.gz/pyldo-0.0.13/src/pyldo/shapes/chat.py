"""
Chat and LongChat Shapes

Based on the ShapeRepo chat schemas commonly used in Solid chat applications.
https://shaperepo.com/schemas/longChat

These shapes support real-time messaging applications built on Solid,
including the popular SolidOS chat and other Solid chat apps.

Namespaces used:
- flow: http://www.w3.org/2005/01/wf/flow#
- terms: http://purl.org/dc/terms/
- meeting: http://www.w3.org/ns/pim/meeting#
- sioc: http://rdfs.org/sioc/ns#
- foaf: http://xmlns.com/foaf/0.1/
- ui: http://www.w3.org/ns/ui#
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
FLOW = "http://www.w3.org/2005/01/wf/flow#"
DCTERMS = "http://purl.org/dc/terms/"
MEETING = "http://www.w3.org/ns/pim/meeting#"
SIOC = "http://rdfs.org/sioc/ns#"
FOAF = "http://xmlns.com/foaf/0.1/"
UI = "http://www.w3.org/ns/ui#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
LDP = "http://www.w3.org/ns/ldp#"


class ChatMessage(BaseModel):
    """
    A single chat message.
    
    Based on the flow ontology used in Solid chat applications.
    
    Properties:
        id: Message URI
        content: The message text (sioc:content)
        created: When the message was sent (dcterms:created)
        maker: Who sent the message (foaf:maker)
    
    Example:
        >>> message = ChatMessage(
        ...     content="Hello everyone!",
        ...     created="2024-01-15T10:30:00Z",
        ...     maker="https://alice.solidcommunity.net/profile/card#me"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Message URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    content: Optional[str] = Field(
        default=None,
        alias="http://rdfs.org/sioc/ns#content",
        description="Message text content"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the message was sent (ISO 8601)"
    )
    
    maker: Optional[str] = Field(
        default=None,
        alias="http://xmlns.com/foaf/0.1/maker",
        description="WebID of the message author"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class Chat(BaseModel):
    """
    A basic chat channel or conversation.
    
    This represents a simple chat that stores messages in a single document.
    For chats with many messages, use LongChat instead.
    
    Properties:
        id: Chat URI
        title: Chat/channel name (dcterms:title)
        created: When the chat was created
        author: Who created the chat
        message: List of messages in this chat
        participation: Users participating in this chat
    
    Example:
        >>> from pyldo.shapes import Chat
        >>> 
        >>> chat = Chat(
        ...     title="Team Discussion",
        ...     author="https://alice.solidcommunity.net/profile/card#me"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Chat URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (typically meeting:Chat)"
    )
    
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Chat title or channel name"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the chat was created (ISO 8601)"
    )
    
    author: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/author",
        description="WebID of the chat creator"
    )
    
    # Messages in this chat
    message: Optional[list["ChatMessage"]] = Field(
        default=None,
        alias="http://www.w3.org/2005/01/wf/flow#message",
        description="Messages in this chat"
    )
    
    # Participants
    participation: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2005/01/wf/flow#participation",
        description="Participation records for users in this chat"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class LongChat(BaseModel):
    """
    A long chat that spans multiple files.
    
    Based on the ShapeRepo longChat schema. LongChat splits messages across
    multiple files (typically by date) to handle large conversations efficiently.
    
    The chat index document contains metadata and references to message files.
    
    Properties:
        id: Chat index URI
        title: Chat/channel name
        created: When the chat was created
        author: Who created the chat
        date_index: References to dated message files
        participation: Users participating in this chat
        shared_preferences: Shared UI preferences
    
    Example:
        >>> from pyldo.shapes import LongChat
        >>> from pyldo import LdoDataset, parse_rdf
        >>> 
        >>> dataset = LdoDataset()
        >>> # Load chat index...
        >>> chat = dataset.using(LongChat).from_subject(chat_uri)
        >>> print(chat.title)
        >>> # Messages are in separate dated files referenced by date_index
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Chat index URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (typically meeting:LongChat)"
    )
    
    title: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/title",
        description="Chat title or channel name"
    )
    
    created: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the chat was created (ISO 8601)"
    )
    
    author: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/author",
        description="WebID of the chat creator"
    )
    
    # Reference to dated message files
    date_index: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2005/01/wf/flow#dateIndex",
        description="URIs of dated message files"
    )
    
    # Participants
    participation: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/2005/01/wf/flow#participation",
        description="Participation records for users in this chat"
    )
    
    # UI preferences
    shared_preferences: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/ui#sharedPreferences",
        description="Shared UI preferences document"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class ChatParticipation(BaseModel):
    """
    A user's participation in a chat.
    
    Tracks when a user joined/left and their preferences for the chat.
    
    Properties:
        id: Participation record URI
        participant: WebID of the participant
        date_joined: When they joined the chat
        references: Reference to the chat
    
    Example:
        >>> participation = ChatParticipation(
        ...     participant="https://bob.solidcommunity.net/profile/card#me",
        ...     date_joined="2024-01-10T08:00:00Z"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Participation record URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    participant: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/2005/01/wf/flow#participant",
        description="WebID of the participant"
    )
    
    date_joined: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/created",
        description="When the user joined (ISO 8601)"
    )
    
    references: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/references",
        description="Reference to the chat"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models for forward references
ChatMessage.model_rebuild()
Chat.model_rebuild()
LongChat.model_rebuild()
ChatParticipation.model_rebuild()
