"""
WebID profile handling for Solid.

Provides utilities for fetching and parsing WebID profiles,
extracting Pod storage locations, and working with profile data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import httpx
from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

from .auth import SolidAuth

# Common namespaces used in WebID profiles
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SOLID = Namespace("http://www.w3.org/ns/solid/terms#")
PIM = Namespace("http://www.w3.org/ns/pim/space#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
LDPT = Namespace("http://www.w3.org/ns/ldp#")


@dataclass
class WebIdProfile:
    """
    Parsed WebID profile information.
    
    Contains identity, storage locations, and profile data
    extracted from a WebID document.
    """
    
    webid: str
    name: Optional[str] = None
    nickname: Optional[str] = None
    email: Optional[str] = None
    photo: Optional[str] = None
    
    # Solid-specific
    storage: list[str] = field(default_factory=list)
    oidc_issuer: Optional[str] = None
    inbox: Optional[str] = None
    preferences_file: Optional[str] = None
    
    # Type index locations
    public_type_index: Optional[str] = None
    private_type_index: Optional[str] = None
    
    # Raw graph for advanced queries
    graph: Optional[Graph] = field(default=None, repr=False)
    
    @property
    def primary_storage(self) -> Optional[str]:
        """Get the primary storage location."""
        return self.storage[0] if self.storage else None
    
    @property
    def pod_root(self) -> Optional[str]:
        """
        Guess the Pod root URL from the WebID or storage.
        
        This is a heuristic that works for common Pod structures.
        """
        if self.storage:
            return self.storage[0]
        
        # Try to infer from WebID structure
        # e.g., https://pod.example.org/alice/profile/card#me -> https://pod.example.org/alice/
        parsed = urlparse(self.webid)
        path_parts = parsed.path.rstrip("/").split("/")
        
        # Common patterns: /profile/card, /public/profile
        for i, part in enumerate(path_parts):
            if part in ("profile", "public", "private"):
                root_path = "/".join(path_parts[:i]) + "/"
                return f"{parsed.scheme}://{parsed.netloc}{root_path}"
        
        return None
    
    def get_container_url(self, container_name: str) -> Optional[str]:
        """
        Get URL for a named container in the Pod.
        
        Args:
            container_name: Container name (e.g., "public", "inbox", "data")
        
        Returns:
            Full container URL or None if storage location unknown
        """
        root = self.pod_root
        if not root:
            return None
        
        if not root.endswith("/"):
            root = root + "/"
        
        return f"{root}{container_name}/"
    
    @classmethod
    def from_graph(cls, webid: str, graph: Graph) -> "WebIdProfile":
        """
        Parse a WebID profile from an RDF graph.
        
        Args:
            webid: The WebID URI
            graph: RDF graph containing the profile
        
        Returns:
            Parsed WebIdProfile
        """
        subject = URIRef(webid)
        
        def get_literal(predicate) -> Optional[str]:
            """Get first literal value for predicate."""
            for obj in graph.objects(subject, predicate):
                if isinstance(obj, Literal):
                    return str(obj)
                elif isinstance(obj, URIRef) and predicate in (FOAF.mbox,):
                    # Handle mailto: URIs
                    uri = str(obj)
                    if uri.startswith("mailto:"):
                        return uri[7:]
                    return uri
            return None
        
        def get_uri(predicate) -> Optional[str]:
            """Get first URI value for predicate."""
            for obj in graph.objects(subject, predicate):
                if isinstance(obj, URIRef):
                    return str(obj)
            return None
        
        def get_all_uris(predicate) -> list[str]:
            """Get all URI values for predicate."""
            return [
                str(obj) for obj in graph.objects(subject, predicate)
                if isinstance(obj, URIRef)
            ]
        
        # Extract profile information
        return cls(
            webid=webid,
            name=get_literal(FOAF.name) or get_literal(VCARD.fn),
            nickname=get_literal(FOAF.nick),
            email=get_literal(FOAF.mbox),
            photo=get_uri(FOAF.img) or get_uri(VCARD.hasPhoto),
            storage=get_all_uris(PIM.storage),
            oidc_issuer=get_uri(SOLID.oidcIssuer),
            inbox=get_uri(LDPT.inbox),
            preferences_file=get_uri(PIM.preferencesFile),
            public_type_index=get_uri(SOLID.publicTypeIndex),
            private_type_index=get_uri(SOLID.privateTypeIndex),
            graph=graph,
        )


async def fetch_webid_profile(
    webid: str,
    http_client: Optional[httpx.AsyncClient] = None,
) -> WebIdProfile:
    """
    Fetch and parse a WebID profile.
    
    Args:
        webid: WebID URL (e.g., https://pod.example.org/alice/profile/card#me)
        http_client: Optional HTTP client
    
    Returns:
        Parsed WebIdProfile
    
    Example:
        >>> profile = await fetch_webid_profile("https://pod.example.org/alice/profile/card#me")
        >>> print(f"Name: {profile.name}")
        >>> print(f"Storage: {profile.primary_storage}")
    """
    # Strip fragment to get the document URL
    doc_url = webid.split("#")[0]
    
    should_close = http_client is None
    if http_client is None:
        http_client = httpx.AsyncClient(follow_redirects=True, timeout=30.0)
    
    try:
        content, content_type = await SolidAuth.fetch_unauthenticated(http_client, doc_url)
        
        # Parse the RDF
        graph = Graph()
        if "json" in content_type:
            graph.parse(data=content, format="json-ld", publicID=doc_url)
        else:
            graph.parse(data=content, format="turtle", publicID=doc_url)
        
        return WebIdProfile.from_graph(webid, graph)
    
    finally:
        if should_close:
            await http_client.aclose()


def create_profile_turtle(
    webid: str,
    name: str,
    storage: Optional[str] = None,
    oidc_issuer: Optional[str] = None,
    email: Optional[str] = None,
) -> str:
    """
    Create a minimal WebID profile document in Turtle format.
    
    Args:
        webid: The WebID URI
        name: Display name
        storage: Pod storage URL
        oidc_issuer: OIDC issuer URL
        email: Email address
    
    Returns:
        Turtle string for the profile document
    """
    lines = [
        "@prefix foaf: <http://xmlns.com/foaf/0.1/> .",
        "@prefix solid: <http://www.w3.org/ns/solid/terms#> .",
        "@prefix pim: <http://www.w3.org/ns/pim/space#> .",
        "",
        f"<{webid}>",
        "    a foaf:Person ;",
        f'    foaf:name "{name}" ;',
    ]
    
    if email:
        lines.append(f"    foaf:mbox <mailto:{email}> ;")
    
    if storage:
        lines.append(f"    pim:storage <{storage}> ;")
    
    if oidc_issuer:
        lines.append(f"    solid:oidcIssuer <{oidc_issuer}> ;")
    
    # Remove trailing semicolon from last predicate and add period
    lines[-1] = lines[-1].rstrip(" ;") + " ."
    
    return "\n".join(lines)


def get_type_registration_sparql(
    type_index_url: str,
    rdf_type: str,
    instance_container: str,
) -> str:
    """
    Generate SPARQL UPDATE to register a type in a type index.
    
    Type registrations tell Solid apps where to find instances of a type.
    
    Args:
        type_index_url: URL of the type index document
        rdf_type: RDF type URI to register
        instance_container: URL of container holding instances
    
    Returns:
        SPARQL UPDATE query string
    """
    import uuid
    
    registration_uri = f"{type_index_url}#registration-{uuid.uuid4().hex[:8]}"
    
    return f"""
PREFIX solid: <http://www.w3.org/ns/solid/terms#>

INSERT DATA {{
    <{registration_uri}>
        a solid:TypeRegistration ;
        solid:forClass <{rdf_type}> ;
        solid:instanceContainer <{instance_container}> .
}}
""".strip()
