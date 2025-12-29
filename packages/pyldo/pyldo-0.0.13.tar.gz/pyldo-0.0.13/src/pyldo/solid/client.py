"""
Solid client for interacting with Solid Pods.

Provides high-level operations for fetching, updating, and managing
resources in Solid Pods using the Solid Protocol.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Union
from urllib.parse import urljoin, urlparse

import httpx
from rdflib import RDF, Graph, Namespace, URIRef

from .auth import SolidAuth, SolidSession

# Solid-specific namespaces
LDP = Namespace("http://www.w3.org/ns/ldp#")
PIM = Namespace("http://www.w3.org/ns/pim/space#")
SOLID = Namespace("http://www.w3.org/ns/solid/terms#")
ACL = Namespace("http://www.w3.org/ns/auth/acl#")
DCT = Namespace("http://purl.org/dc/terms/")
STAT = Namespace("http://www.w3.org/ns/posix/stat#")


# =============================================================================
# URL Utilities
# =============================================================================

def get_root_url(url: str) -> str:
    """
    Get the root URL (scheme + host) from a URL.
    
    Args:
        url: Any URL
    
    Returns:
        Root URL with trailing slash
    
    Example:
        >>> get_root_url("https://pod.example.org/folder/file.ttl")
        "https://pod.example.org/"
    """
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def get_parent_url(url: str) -> str:
    """
    Get the parent container URL from a resource URL.
    
    Args:
        url: Resource URL
    
    Returns:
        Parent container URL with trailing slash
    
    Example:
        >>> get_parent_url("https://pod.example.org/folder/file.ttl")
        "https://pod.example.org/folder/"
        >>> get_parent_url("https://pod.example.org/folder/")
        "https://pod.example.org/"
    """
    # Remove trailing slash for consistent handling
    url = url.rstrip("/")
    
    parsed = urlparse(url)
    path = parsed.path
    
    # If at root, return root
    if not path or path == "/":
        return f"{parsed.scheme}://{parsed.netloc}/"
    
    # Find last slash and return everything before it
    last_slash = path.rfind("/")
    if last_slash <= 0:
        return f"{parsed.scheme}://{parsed.netloc}/"
    
    parent_path = path[:last_slash + 1]
    return f"{parsed.scheme}://{parsed.netloc}{parent_path}"


def get_item_name(url: str) -> str:
    """
    Get the item name (filename or folder name) from a URL.
    
    Args:
        url: Resource URL
    
    Returns:
        Item name without path
    
    Example:
        >>> get_item_name("https://pod.example.org/folder/file.ttl")
        "file.ttl"
        >>> get_item_name("https://pod.example.org/folder/")
        "folder"
    """
    url = url.rstrip("/")
    
    parsed = urlparse(url)
    path = parsed.path
    
    if not path or path == "/":
        return ""
    
    last_slash = path.rfind("/")
    if last_slash < 0:
        return path
    
    return path[last_slash + 1:]


def ensure_trailing_slash(url: str) -> str:
    """Ensure URL ends with a trailing slash (for containers)."""
    return url if url.endswith("/") else url + "/"


def remove_trailing_slash(url: str) -> str:
    """Remove trailing slash from URL."""
    return url.rstrip("/")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Item:
    """
    Represents an item (file or folder) in a Solid Pod container.
    
    Attributes:
        url: Full URL of the item
        name: Item name (filename or folder name)
        parent: Parent container URL
        item_type: "Container" for folders, "Resource" for files
        content_type: MIME type (for files)
        size: File size in bytes (if available)
        modified: Last modified timestamp (if available)
    """
    url: str
    name: str
    parent: str
    item_type: str  # "Container" or "Resource"
    content_type: Optional[str] = None
    size: Optional[int] = None
    modified: Optional[datetime] = None
    
    @property
    def is_container(self) -> bool:
        """Check if this item is a container (folder)."""
        return self.item_type == "Container"
    
    @property
    def is_file(self) -> bool:
        """Check if this item is a file (resource)."""
        return self.item_type == "Resource"


@dataclass
class FolderData:
    """
    Represents the contents of a folder (container) in a Solid Pod.
    
    Attributes:
        url: Container URL
        name: Container name
        parent: Parent container URL
        folders: List of sub-containers
        files: List of files in the container
    
    Example:
        >>> folder = await client.read_folder("https://pod.example.org/documents/")
        >>> print(f"Folder: {folder.name}")
        >>> for f in folder.files:
        ...     print(f"  - {f.name}")
    """
    url: str
    name: str
    parent: str
    folders: List[Item] = field(default_factory=list)
    files: List[Item] = field(default_factory=list)
    
    @property
    def all_items(self) -> List[Item]:
        """Get all items (folders + files)."""
        return self.folders + self.files
    
    @property
    def is_empty(self) -> bool:
        """Check if folder is empty."""
        return len(self.folders) == 0 and len(self.files) == 0


@dataclass
class SolidResource:
    """
    Represents a resource in a Solid Pod.
    
    Contains the resource's URL, content, metadata, and RDF graph.
    """
    
    url: str
    content: Optional[str] = None
    content_type: str = "text/turtle"
    graph: Optional[Graph] = None
    etag: Optional[str] = None
    wac_allow: Optional[dict] = None  # Access control info
    last_modified: Optional[str] = None
    
    @property
    def is_container(self) -> bool:
        """Check if this resource is a container (folder)."""
        return self.url.endswith("/")
    
    @property
    def name(self) -> str:
        """Get the resource name from the URL."""
        parsed = urlparse(self.url)
        path = parsed.path.rstrip("/")
        return path.split("/")[-1] if path else ""
    
    def parse_graph(self) -> Graph:
        """Parse the content into an RDF graph."""
        if self.graph is None:
            self.graph = Graph()
            if self.content:
                if "json" in self.content_type:
                    self.graph.parse(data=self.content, format="json-ld", publicID=self.url)
                else:
                    self.graph.parse(data=self.content, format="turtle", publicID=self.url)
        return self.graph
    
    def get_contained_resources(self) -> list[str]:
        """
        Get URLs of resources contained in this container.
        
        Returns:
            List of resource URLs if this is a container, empty list otherwise
        """
        if not self.is_container:
            return []
        
        graph = self.parse_graph()
        container = URIRef(self.url)
        
        contained = []
        for obj in graph.objects(container, LDP.contains):
            contained.append(str(obj))
        
        return contained


@dataclass
class SolidContainer(SolidResource):
    """
    Represents a container (folder) in a Solid Pod.
    
    Extends SolidResource with container-specific functionality.
    """
    
    children: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure URL ends with slash for containers."""
        if not self.url.endswith("/"):
            self.url = self.url + "/"


class SolidClient:
    """
    High-level client for interacting with Solid Pods.
    
    Provides methods for:
    - Fetching resources (GET)
    - Creating resources (POST/PUT)
    - Updating resources (PATCH with SPARQL UPDATE)
    - Deleting resources (DELETE)
    - Managing containers
    """
    
    def __init__(
        self,
        session: Optional[SolidSession] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize the Solid client.
        
        Args:
            session: Optional authenticated session
            http_client: Optional HTTP client (created if not provided)
        """
        self.session = session
        self._http_client = http_client
        self._owns_client = http_client is None
    
    async def __aenter__(self) -> "SolidClient":
        """Async context manager entry."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._owns_client and self._http_client:
            await self._http_client.aclose()
    
    @property
    def http(self) -> httpx.AsyncClient:
        """Get the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            )
            self._owns_client = True
        return self._http_client
    
    def _get_auth_headers(self, method: str, url: str) -> dict:
        """Get authentication headers for a request."""
        if self.session:
            return self.session.get_auth_headers(method, url)
        return {}
    
    async def get(
        self,
        url: str,
        accept: str = "text/turtle",
    ) -> SolidResource:
        """
        Fetch a resource from a Solid Pod.
        
        Args:
            url: Resource URL
            accept: Preferred content type
        
        Returns:
            SolidResource with the fetched content
        """
        headers = {
            "Accept": accept,
            **self._get_auth_headers("GET", url),
        }
        
        response = await self.http.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse WAC-Allow header if present
        wac_allow = None
        if "wac-allow" in response.headers:
            wac_allow = self._parse_wac_allow(response.headers["wac-allow"])
        
        content_type = response.headers.get("content-type", "text/turtle")
        # Strip charset from content type
        if ";" in content_type:
            content_type = content_type.split(";")[0].strip()
        
        return SolidResource(
            url=str(response.url),  # Use final URL after redirects
            content=response.text,
            content_type=content_type,
            etag=response.headers.get("etag"),
            wac_allow=wac_allow,
            last_modified=response.headers.get("last-modified"),
        )
    
    async def get_container(self, url: str) -> SolidContainer:
        """
        Fetch a container from a Solid Pod.
        
        Args:
            url: Container URL (should end with /)
        
        Returns:
            SolidContainer with contained resources
        """
        if not url.endswith("/"):
            url = url + "/"
        
        resource = await self.get(url)
        
        container = SolidContainer(
            url=resource.url,
            content=resource.content,
            content_type=resource.content_type,
            graph=resource.graph,
            etag=resource.etag,
            wac_allow=resource.wac_allow,
            last_modified=resource.last_modified,
        )
        
        # Parse contained resources
        container.children = container.get_contained_resources()
        
        return container
    
    async def put(
        self,
        url: str,
        content: str,
        content_type: str = "text/turtle",
        if_none_match: bool = False,
        if_match: Optional[str] = None,
    ) -> SolidResource:
        """
        Create or replace a resource.
        
        Args:
            url: Resource URL
            content: Resource content
            content_type: Content MIME type
            if_none_match: Set True to only create if resource doesn't exist
            if_match: ETag to match for conditional update
        
        Returns:
            SolidResource representing the created/updated resource
        """
        headers = {
            "Content-Type": content_type,
            **self._get_auth_headers("PUT", url),
        }
        
        if if_none_match:
            headers["If-None-Match"] = "*"
        if if_match:
            headers["If-Match"] = if_match
        
        response = await self.http.put(url, headers=headers, content=content)
        response.raise_for_status()
        
        return SolidResource(
            url=str(response.url),
            content=content,
            content_type=content_type,
            etag=response.headers.get("etag"),
        )
    
    async def post(
        self,
        container_url: str,
        content: str,
        content_type: str = "text/turtle",
        slug: Optional[str] = None,
        link_type: Optional[str] = None,
    ) -> SolidResource:
        """
        Create a new resource in a container.
        
        Args:
            container_url: Container URL
            content: Resource content
            content_type: Content MIME type
            slug: Suggested resource name
            link_type: Resource type (ldp:Resource or ldp:BasicContainer)
        
        Returns:
            SolidResource representing the created resource
        """
        headers = {
            "Content-Type": content_type,
            **self._get_auth_headers("POST", container_url),
        }
        
        if slug:
            headers["Slug"] = slug
        
        if link_type:
            headers["Link"] = f'<{link_type}>; rel="type"'
        
        response = await self.http.post(container_url, headers=headers, content=content)
        response.raise_for_status()
        
        # Get the created resource URL from Location header
        location = response.headers.get("location")
        if location:
            created_url = urljoin(container_url, location)
        else:
            created_url = container_url
        
        return SolidResource(
            url=created_url,
            content=content,
            content_type=content_type,
            etag=response.headers.get("etag"),
        )
    
    async def patch(
        self,
        url: str,
        sparql_update: str,
        if_match: Optional[str] = None,
    ) -> bool:
        """
        Update a resource using SPARQL UPDATE.
        
        Args:
            url: Resource URL
            sparql_update: SPARQL UPDATE query
            if_match: Optional ETag for conditional update
        
        Returns:
            True if update succeeded
        """
        headers = {
            "Content-Type": "application/sparql-update",
            **self._get_auth_headers("PATCH", url),
        }
        
        if if_match:
            headers["If-Match"] = if_match
        
        response = await self.http.patch(url, headers=headers, content=sparql_update)
        response.raise_for_status()
        
        return response.status_code in (200, 204)
    
    async def delete(
        self,
        url: str,
        if_match: Optional[str] = None,
    ) -> bool:
        """
        Delete a resource.
        
        Args:
            url: Resource URL
            if_match: Optional ETag for conditional delete
        
        Returns:
            True if deletion succeeded
        """
        headers = self._get_auth_headers("DELETE", url)
        
        if if_match:
            headers["If-Match"] = if_match
        
        response = await self.http.delete(url, headers=headers)
        response.raise_for_status()
        
        return response.status_code in (200, 204)
    
    async def create_container(
        self,
        parent_url: str,
        name: str,
    ) -> SolidContainer:
        """
        Create a new container (folder).
        
        Args:
            parent_url: Parent container URL
            name: Container name
        
        Returns:
            SolidContainer representing the created container
        """
        if not parent_url.endswith("/"):
            parent_url = parent_url + "/"
        
        resource = await self.post(
            container_url=parent_url,
            content="",
            content_type="text/turtle",
            slug=name,
            link_type=str(LDP.BasicContainer),
        )
        
        return SolidContainer(
            url=resource.url,
            content=resource.content,
            content_type=resource.content_type,
            etag=resource.etag,
        )
    
    async def delete_container(
        self,
        url: str,
        recursive: bool = False,
    ) -> bool:
        """
        Delete a container.
        
        Args:
            url: Container URL
            recursive: If True, delete all contained resources first
        
        Returns:
            True if deletion succeeded
        """
        if recursive:
            container = await self.get_container(url)
            for child_url in container.children:
                if child_url.endswith("/"):
                    await self.delete_container(child_url, recursive=True)
                else:
                    await self.delete(child_url)
        
        return await self.delete(url)
    
    async def resource_exists(self, url: str) -> bool:
        """
        Check if a resource exists.
        
        Args:
            url: Resource URL
        
        Returns:
            True if resource exists
        """
        headers = self._get_auth_headers("HEAD", url)
        
        try:
            response = await self.http.head(url, headers=headers)
            return response.status_code == 200
        except httpx.HTTPStatusError:
            return False
    
    # Alias for compatibility with solid-file-python
    item_exists = resource_exists
    
    # =========================================================================
    # High-Level File Management (inspired by solid-file-python)
    # =========================================================================
    
    async def read_folder(self, url: str) -> FolderData:
        """
        Read the contents of a folder (container).
        
        Returns a FolderData object with lists of sub-folders and files.
        
        Args:
            url: Container URL
        
        Returns:
            FolderData with folders and files lists
        
        Example:
            >>> folder = await client.read_folder("https://pod.example.org/documents/")
            >>> print(f"Folder: {folder.name}")
            >>> print(f"Subfolders: {[f.name for f in folder.folders]}")
            >>> print(f"Files: {[f.name for f in folder.files]}")
        """
        url = ensure_trailing_slash(url)
        
        # Fetch the container
        resource = await self.get(url, accept="text/turtle")
        graph = resource.parse_graph()
        
        container_uri = URIRef(url)
        folders: List[Item] = []
        files: List[Item] = []
        
        # Container types to check
        container_types = [
            LDP.Container,
            LDP.BasicContainer,
        ]
        
        def is_container(uri: URIRef) -> bool:
            """Check if a URI is a container type."""
            for ct in container_types:
                if (uri, RDF.type, ct) in graph:
                    return True
            # Also check if URL ends with /
            return str(uri).endswith("/")
        
        # Iterate over contained resources
        for obj in graph.objects(container_uri, LDP.contains):
            item_url = str(obj)
            item_name = get_item_name(item_url)
            item_parent = get_parent_url(item_url)
            
            # Determine item type
            if is_container(obj):
                item_type = "Container"
            else:
                item_type = "Resource"
            
            # Try to get additional metadata
            modified = None
            size = None
            content_type = None
            
            # Look for dcterms:modified
            for mod in graph.objects(obj, DCT.modified):
                try:
                    modified = datetime.fromisoformat(str(mod).replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            
            # Look for stat:size
            for sz in graph.objects(obj, STAT.size):
                try:
                    size = int(float(str(sz)))
                except (ValueError, TypeError):
                    pass
            
            item = Item(
                url=item_url,
                name=item_name,
                parent=item_parent,
                item_type=item_type,
                content_type=content_type,
                size=size,
                modified=modified,
            )
            
            if item_type == "Container":
                folders.append(item)
            else:
                files.append(item)
        
        return FolderData(
            url=url,
            name=get_item_name(url),
            parent=get_parent_url(url),
            folders=folders,
            files=files,
        )
    
    async def create_folder(
        self,
        url: str,
        create_parents: bool = True,
    ) -> SolidContainer:
        """
        Create a folder (container) at the specified URL.
        
        Args:
            url: Container URL (should end with /)
            create_parents: If True, create parent folders if they don't exist
        
        Returns:
            SolidContainer representing the created container
        
        Example:
            >>> await client.create_folder("https://pod.example.org/a/b/c/")
        """
        url = ensure_trailing_slash(url)
        
        # Check if already exists
        if await self.resource_exists(url):
            return await self.get_container(url)
        
        if create_parents:
            # Get parent URL
            parent_url = get_parent_url(url)
            root_url = get_root_url(url)
            
            # If parent is not root and doesn't exist, create it first
            if parent_url != root_url and not await self.resource_exists(parent_url):
                await self.create_folder(parent_url, create_parents=True)
        
        # Create this folder
        parent_url = get_parent_url(url)
        folder_name = get_item_name(url)
        
        return await self.create_container(parent_url, folder_name)
    
    async def put_file(
        self,
        url: str,
        content: Union[str, bytes],
        content_type: str = "text/plain",
        create_parents: bool = True,
    ) -> SolidResource:
        """
        Upload a file to the Pod.
        
        Args:
            url: File URL (should not end with /)
            content: File content (string or bytes)
            content_type: MIME type of the content
            create_parents: If True, create parent folders if they don't exist
        
        Returns:
            SolidResource representing the uploaded file
        
        Example:
            >>> await client.put_file(
            ...     "https://pod.example.org/documents/hello.txt",
            ...     "Hello, Solid!",
            ...     "text/plain"
            ... )
        """
        if url.endswith("/"):
            raise ValueError(f"Cannot use put_file to create a folder: {url}")
        
        if create_parents:
            parent_url = get_parent_url(url)
            root_url = get_root_url(url)
            
            if parent_url != root_url and not await self.resource_exists(parent_url):
                await self.create_folder(parent_url, create_parents=True)
        
        # Convert bytes to string if needed for the put method
        if isinstance(content, bytes):
            content_str = content.decode("utf-8") if content_type.startswith("text/") else content.decode("latin-1")
        else:
            content_str = content
        
        return await self.put(url, content_str, content_type)
    
    async def get_file(self, url: str) -> tuple[str, str]:
        """
        Download a file from the Pod.
        
        Args:
            url: File URL
        
        Returns:
            Tuple of (content, content_type)
        
        Example:
            >>> content, content_type = await client.get_file("https://pod.example.org/doc.txt")
        """
        resource = await self.get(url)
        return resource.content, resource.content_type
    
    async def patch_file(
        self,
        url: str,
        sparql_update: str,
    ) -> bool:
        """
        Update an RDF file using SPARQL UPDATE.
        
        This is useful for making targeted updates to RDF data without
        replacing the entire file.
        
        Args:
            url: File URL (must be an RDF resource)
            sparql_update: SPARQL UPDATE query
        
        Returns:
            True if update succeeded
        
        Example:
            >>> await client.patch_file(
            ...     "https://pod.example.org/profile/card",
            ...     '''
            ...     DELETE DATA { <#me> <http://xmlns.com/foaf/0.1/name> "Old Name" };
            ...     INSERT DATA { <#me> <http://xmlns.com/foaf/0.1/name> "New Name" }
            ...     '''
            ... )
        """
        if url.endswith("/"):
            raise ValueError(f"Cannot use patch_file on a folder: {url}")
        
        return await self.patch(url, sparql_update)
    
    async def delete_file(self, url: str) -> bool:
        """
        Delete a file from the Pod.
        
        Args:
            url: File URL
        
        Returns:
            True if deletion succeeded
        
        Example:
            >>> await client.delete_file("https://pod.example.org/doc.txt")
        """
        if url.endswith("/"):
            raise ValueError(f"Cannot use delete_file on a folder: {url}")
        
        return await self.delete(url)
    
    async def copy_file(
        self,
        from_url: str,
        to_url: str,
        create_parents: bool = True,
    ) -> SolidResource:
        """
        Copy a file from one location to another.
        
        Args:
            from_url: Source file URL
            to_url: Destination file URL
            create_parents: If True, create parent folders for destination
        
        Returns:
            SolidResource representing the copied file
        """
        # Fetch the source
        content, content_type = await self.get_file(from_url)
        
        # Create at destination
        return await self.put_file(to_url, content, content_type, create_parents)
    
    async def move_file(
        self,
        from_url: str,
        to_url: str,
        create_parents: bool = True,
    ) -> SolidResource:
        """
        Move a file from one location to another.
        
        Args:
            from_url: Source file URL
            to_url: Destination file URL
            create_parents: If True, create parent folders for destination
        
        Returns:
            SolidResource representing the file at new location
        """
        # Copy to new location
        resource = await self.copy_file(from_url, to_url, create_parents)
        
        # Delete original
        await self.delete_file(from_url)
        
        return resource
    
    @staticmethod
    def _parse_wac_allow(header: str) -> dict:
        """
        Parse WAC-Allow header to extract permissions.
        
        Example header: user="read write", public="read"
        """
        permissions = {}
        
        # Parse user="..." and public="..." parts
        pattern = r'(\w+)="([^"]*)"'
        matches = re.findall(pattern, header)
        
        for key, value in matches:
            permissions[key] = value.split()
        
        return permissions
