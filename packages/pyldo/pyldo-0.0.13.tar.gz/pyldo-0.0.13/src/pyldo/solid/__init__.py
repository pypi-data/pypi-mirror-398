"""
Solid integration module for pyldo.

Provides authentication and client functionality for interacting with Solid Pods.
"""

from .auth import (
    ClientCredentials,
    DPoPToken,
    SolidAuth,
    SolidOidcAuth,
    SolidOidcSession,
    SolidSession,
)
from .client import (
    FolderData,
    Item,
    SolidClient,
    SolidContainer,
    SolidResource,
    # URL utilities
    ensure_trailing_slash,
    get_item_name,
    get_parent_url,
    get_root_url,
    remove_trailing_slash,
)
from .webid import (
    WebIdProfile,
    fetch_webid_profile,
)

__all__ = [
    # Authentication (client credentials / server-to-server)
    "SolidAuth",
    "SolidSession",
    "DPoPToken",
    "ClientCredentials",
    # Authentication (Solid-OIDC / browser flow)
    "SolidOidcAuth",
    "SolidOidcSession",
    # Client
    "SolidClient",
    "SolidResource",
    "SolidContainer",
    # File management
    "FolderData",
    "Item",
    # URL utilities
    "get_root_url",
    "get_parent_url",
    "get_item_name",
    "ensure_trailing_slash",
    "remove_trailing_slash",
    # WebID
    "WebIdProfile",
    "fetch_webid_profile",
]
