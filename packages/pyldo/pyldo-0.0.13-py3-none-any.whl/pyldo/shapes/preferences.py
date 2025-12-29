"""
Preferences Shape

For storing user and app preferences in a Solid Pod.
Preferences allow apps to persist settings without their own backend.

Namespaces used:
- pref: http://www.w3.org/ns/pim/prefs#
- ui: http://www.w3.org/ns/ui#
- schema: http://schema.org/
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

# Namespace constants
PREF = "http://www.w3.org/ns/pim/prefs#"
UI = "http://www.w3.org/ns/ui#"
SCHEMA = "http://schema.org/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Preference(BaseModel):
    """
    A single preference/setting.
    
    Stores key-value pairs for app or user settings.
    
    Properties:
        id: Preference URI
        name: Setting name/key
        value: Setting value
        description: Human-readable description
    
    Example:
        >>> from pyldo.shapes import Preference
        >>> 
        >>> pref = Preference(
        ...     name="theme",
        ...     value="dark",
        ...     description="UI color theme"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Preference URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    # Key/name
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Setting name/key"
    )
    
    # Value - can be string, number, boolean
    value: Optional[str] = Field(
        default=None,
        alias="http://schema.org/value",
        description="Setting value"
    )
    
    # Description
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Human-readable description of the setting"
    )
    
    # For grouping preferences
    category: Optional[str] = Field(
        default=None,
        alias="http://schema.org/category",
        description="Category for organizing preferences"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class PreferencesFile(BaseModel):
    """
    A preferences file containing multiple settings.
    
    Apps store their preferences in a dedicated file in the user's Pod.
    Common location: /settings/prefs.ttl or /apps/{appname}/preferences.ttl
    
    Properties:
        id: Preferences file URI
        app_name: Name of the app these preferences belong to
        app_origin: Origin URL of the app
        preferences: List of preference URIs
        modified: When preferences were last changed
    
    Example:
        >>> from pyldo.shapes import PreferencesFile
        >>> 
        >>> prefs_file = PreferencesFile(
        ...     app_name="My Solid App",
        ...     app_origin="https://myapp.example.com",
        ...     modified="2024-01-15T10:30:00Z"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Preferences file URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    # App identification
    app_name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Name of the app"
    )
    
    app_origin: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/solid/terms#origin",
        description="Origin URL of the app"
    )
    
    # Preferences
    preferences: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/ns/pim/prefs#setting",
        description="List of preference URIs"
    )
    
    # Timestamp
    modified: Optional[str] = Field(
        default=None,
        alias="http://purl.org/dc/terms/modified",
        description="When preferences were last modified"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class GlobalPreferences(BaseModel):
    """
    Global user preferences (not app-specific).
    
    Stored at a well-known location in the Pod for cross-app settings.
    
    Properties:
        id: Preferences URI
        language: Preferred language
        date_format: Preferred date format
        time_zone: User's timezone
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Global preferences URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    language: Optional[str] = Field(
        default=None,
        alias="http://schema.org/inLanguage",
        description="Preferred language (e.g., 'en', 'fr')"
    )
    
    date_format: Optional[str] = Field(
        default=None,
        alias="http://www.w3.org/ns/ui#dateFormat",
        description="Preferred date format"
    )
    
    time_zone: Optional[str] = Field(
        default=None,
        alias="http://schema.org/timeZone",
        description="User's timezone"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Preference.model_rebuild()
PreferencesFile.model_rebuild()
GlobalPreferences.model_rebuild()
