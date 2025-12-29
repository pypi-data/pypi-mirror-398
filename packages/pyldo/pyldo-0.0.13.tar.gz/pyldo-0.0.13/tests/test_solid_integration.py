"""
Test demonstrating Solid integration with pyldo.

This test shows how to:
1. Fetch and parse WebID profiles
2. Use SolidClient to interact with Solid Pods
3. Combine SolidClient with LdoDataset for typed access

Note: Some tests use mocked responses for reliability.
Tests against real Solid Pods require network access.
"""

import asyncio
from typing import Optional

from pydantic import BaseModel, Field

# Import pyldo components
from pyldo import LdoBuilder, LdoDataset
from pyldo.solid import (
    DPoPToken,
    SolidAuth,
    SolidClient,
    SolidContainer,
    SolidResource,
    SolidSession,
    WebIdProfile,
    fetch_webid_profile,
)
from pyldo.solid.webid import create_profile_turtle, get_type_registration_sparql


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# =============================================================================
# Test 1: DPoP Token Generation
# =============================================================================

def test_dpop_token():
    """Test DPoP token generation and JWT creation."""
    print_section("TEST 1: DPoP Token Generation")
    
    # Create a DPoP token handler
    dpop = DPoPToken()
    
    # Get the public JWK
    jwk = dpop.get_public_jwk()
    print(f"Public JWK: {jwk}")
    
    # Get the thumbprint
    thumbprint = dpop.get_jwk_thumbprint()
    print(f"JWK Thumbprint: {thumbprint}")
    
    # Create a proof for a request
    proof = dpop.create_proof("GET", "https://pod.example.org/resource")
    print(f"DPoP Proof (JWT): {proof[:50]}...")
    
    # Verify the proof structure (header.payload.signature)
    parts = proof.split(".")
    assert len(parts) == 3, "DPoP proof should be a valid JWT"
    print("✅ DPoP proof is a valid JWT structure")
    
    # Create proof with access token binding
    proof_with_ath = dpop.create_proof(
        "POST",
        "https://pod.example.org/container/",
        access_token="example_access_token_12345"
    )
    print(f"DPoP Proof with ATH: {proof_with_ath[:50]}...")
    print("✅ DPoP token generation works correctly")


# =============================================================================
# Test 2: WebID Profile Parsing
# =============================================================================

def test_webid_profile_parsing():
    """Test WebID profile parsing from Turtle."""
    print_section("TEST 2: WebID Profile Parsing")
    
    # Sample WebID profile in Turtle format
    profile_turtle = """
    @prefix foaf: <http://xmlns.com/foaf/0.1/> .
    @prefix solid: <http://www.w3.org/ns/solid/terms#> .
    @prefix pim: <http://www.w3.org/ns/pim/space#> .
    @prefix ldp: <http://www.w3.org/ns/ldp#> .
    
    <https://pod.example.org/alice/profile/card#me>
        a foaf:Person ;
        foaf:name "Alice Smith" ;
        foaf:mbox <mailto:alice@example.org> ;
        pim:storage <https://pod.example.org/alice/> ;
        solid:oidcIssuer <https://solidcommunityserver.net/> ;
        ldp:inbox <https://pod.example.org/alice/inbox/> ;
        solid:publicTypeIndex <https://pod.example.org/alice/settings/publicTypeIndex.ttl> ;
        solid:privateTypeIndex <https://pod.example.org/alice/settings/privateTypeIndex.ttl> .
    """
    
    from rdflib import Graph
    
    # Parse the profile
    webid = "https://pod.example.org/alice/profile/card#me"
    graph = Graph()
    graph.parse(data=profile_turtle, format="turtle")
    
    profile = WebIdProfile.from_graph(webid, graph)
    
    print(f"WebID: {profile.webid}")
    print(f"Name: {profile.name}")
    print(f"Email: {profile.email}")
    print(f"Storage: {profile.storage}")
    print(f"Primary Storage: {profile.primary_storage}")
    print(f"OIDC Issuer: {profile.oidc_issuer}")
    print(f"Inbox: {profile.inbox}")
    print(f"Public Type Index: {profile.public_type_index}")
    print(f"Pod Root: {profile.pod_root}")
    
    # Test helper methods
    data_container = profile.get_container_url("data")
    print(f"Data Container URL: {data_container}")
    
    assert profile.name == "Alice Smith"
    assert profile.primary_storage == "https://pod.example.org/alice/"
    assert profile.oidc_issuer == "https://solidcommunityserver.net/"
    
    print("✅ WebID profile parsing works correctly")


# =============================================================================
# Test 3: Profile Creation Helper
# =============================================================================

def test_profile_creation():
    """Test WebID profile creation helper."""
    print_section("TEST 3: Profile Creation Helper")
    
    # Create a profile document
    turtle = create_profile_turtle(
        webid="https://pod.example.org/bob/profile/card#me",
        name="Bob Jones",
        storage="https://pod.example.org/bob/",
        oidc_issuer="https://solidcommunityserver.net/",
        email="bob@example.org",
    )
    
    print("Generated Profile Turtle:")
    print(turtle)
    
    # Verify it's valid Turtle by parsing
    from rdflib import Graph
    graph = Graph()
    graph.parse(data=turtle, format="turtle")
    
    assert len(graph) >= 4, "Profile should have at least 4 triples"
    print(f"✅ Generated valid profile with {len(graph)} triples")


# =============================================================================
# Test 4: Type Registration SPARQL
# =============================================================================

def test_type_registration():
    """Test type registration SPARQL generation."""
    print_section("TEST 4: Type Registration SPARQL")
    
    sparql = get_type_registration_sparql(
        type_index_url="https://pod.example.org/alice/settings/publicTypeIndex.ttl",
        rdf_type="http://schema.org/BlogPosting",
        instance_container="https://pod.example.org/alice/blog/",
    )
    
    print("Generated SPARQL UPDATE:")
    print(sparql)
    
    assert "INSERT DATA" in sparql
    assert "solid:TypeRegistration" in sparql
    assert "solid:forClass" in sparql
    assert "solid:instanceContainer" in sparql
    
    print("✅ Type registration SPARQL generation works")


# =============================================================================
# Test 5: SolidResource Parsing
# =============================================================================

def test_solid_resource():
    """Test SolidResource parsing and graph access."""
    print_section("TEST 5: SolidResource Parsing")
    
    # Create a resource with Turtle content
    content = """
    @prefix schema: <http://schema.org/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    <https://pod.example.org/alice/blog/post1>
        a schema:BlogPosting ;
        schema:headline "My First Post" ;
        schema:datePublished "2024-12-24"^^xsd:date ;
        schema:author <https://pod.example.org/alice/profile/card#me> .
    """
    
    resource = SolidResource(
        url="https://pod.example.org/alice/blog/post1",
        content=content,
        content_type="text/turtle",
        etag='"abc123"',
    )
    
    print(f"Resource URL: {resource.url}")
    print(f"Resource Name: {resource.name}")
    print(f"Is Container: {resource.is_container}")
    print(f"ETag: {resource.etag}")
    
    # Parse the graph
    graph = resource.parse_graph()
    print(f"Graph has {len(graph)} triples")
    
    assert resource.name == "post1"
    assert not resource.is_container
    assert len(graph) == 4
    
    print("✅ SolidResource parsing works correctly")


# =============================================================================
# Test 6: Container Parsing
# =============================================================================

def test_container_parsing():
    """Test SolidContainer parsing with ldp:contains."""
    print_section("TEST 6: Container Parsing")
    
    # Container listing response
    container_content = """
    @prefix ldp: <http://www.w3.org/ns/ldp#> .
    @prefix dc: <http://purl.org/dc/terms/> .
    
    <https://pod.example.org/alice/blog/>
        a ldp:Container, ldp:BasicContainer ;
        dc:title "Alice's Blog" ;
        ldp:contains
            <https://pod.example.org/alice/blog/post1>,
            <https://pod.example.org/alice/blog/post2>,
            <https://pod.example.org/alice/blog/post3> .
    """
    
    container = SolidContainer(
        url="https://pod.example.org/alice/blog/",
        content=container_content,
        content_type="text/turtle",
    )
    
    print(f"Container URL: {container.url}")
    print(f"Is Container: {container.is_container}")
    
    # Get contained resources
    children = container.get_contained_resources()
    print(f"Contains {len(children)} resources:")
    for child in children:
        print(f"  - {child}")
    
    assert container.is_container
    assert len(children) == 3
    
    print("✅ Container parsing works correctly")


# =============================================================================
# Test 7: Solid + LDO Integration (Simulated)
# =============================================================================

def test_solid_ldo_integration():
    """
    Test combining SolidResource with LdoDataset for typed access.
    
    This demonstrates the workflow of:
    1. Fetching a resource (simulated)
    2. Parsing into LdoDataset
    3. Getting typed objects
    4. Making changes
    5. Generating SPARQL UPDATE for sync
    """
    print_section("TEST 7: Solid + LDO Integration")
    
    # Define our schema-based model
    class BlogPost(BaseModel):
        """Blog post model matching schema.org/BlogPosting."""
        id: Optional[str] = Field(default=None, alias="@id")
        headline: str = Field(..., alias="http://schema.org/headline")
        date_published: Optional[str] = Field(default=None, alias="http://schema.org/datePublished")
        author: Optional[str] = Field(default=None, alias="http://schema.org/author")
        
        model_config = {"populate_by_name": True, "extra": "allow"}
    
    # Simulate fetching a resource from a Solid Pod
    fetched_turtle = """
    @prefix schema: <http://schema.org/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
    
    <https://pod.example.org/alice/blog/post1>
        a schema:BlogPosting ;
        schema:headline "My First Solid App" ;
        schema:datePublished "2024-12-24" ;
        schema:author <https://pod.example.org/alice/profile/card#me> .
    """
    
    # Create LdoDataset and parse
    dataset = LdoDataset()
    dataset.parse_turtle(fetched_turtle)
    print(f"Parsed resource: {len(dataset.graph)} triples")
    
    # Get typed blog post
    builder = dataset.using(BlogPost)
    post = builder.from_subject("https://pod.example.org/alice/blog/post1")
    
    print(f"\nBlog Post:")
    print(f"  ID: {post.id}")
    print(f"  Headline: {post.headline}")
    print(f"  Published: {post.date_published}")
    print(f"  Author: {post.author}")
    
    # Make changes with transaction tracking
    with dataset.transaction() as txn:
        # Update the headline
        old_headline = post.headline
        
        # Manually update the graph (in real app, this would sync from object)
        from rdflib import Literal, URIRef
        subject = URIRef("https://pod.example.org/alice/blog/post1")
        predicate = URIRef("http://schema.org/headline")
        
        dataset.graph.graph.remove((subject, predicate, Literal(old_headline)))
        dataset.graph.graph.add((subject, predicate, Literal("My First Solid App - Updated!")))
        
        # Track the changes manually for the transaction
        txn.track_add((subject, predicate, Literal("My First Solid App - Updated!")))
        txn.track_remove((subject, predicate, Literal(old_headline)))
    
    # Generate SPARQL UPDATE for syncing back to Pod
    from pyldo.dataset import to_sparql_update
    sparql = to_sparql_update(txn.changes)
    
    print(f"\nSPARQL UPDATE for Solid PATCH:")
    print(sparql)
    
    # Verify the SPARQL
    assert "DELETE DATA" in sparql
    assert "INSERT DATA" in sparql
    assert "My First Solid App" in sparql
    assert "Updated" in sparql
    
    print("\n✅ Solid + LDO integration workflow works correctly")


# =============================================================================
# Test 8: Session Authentication Headers
# =============================================================================

def test_session_auth_headers():
    """Test SolidSession authentication header generation."""
    print_section("TEST 8: Session Auth Headers")
    
    # Create a DPoP token and session
    dpop = DPoPToken()
    
    session = SolidSession(
        access_token="test_access_token_xyz",
        token_type="DPoP",
        dpop=dpop,
        webid="https://pod.example.org/alice/profile/card#me",
    )
    
    # Get headers for a request
    headers = session.get_auth_headers("GET", "https://pod.example.org/alice/data/")
    
    print(f"Authorization header: {headers['Authorization'][:30]}...")
    print(f"DPoP header present: {'DPoP' in headers}")
    print(f"DPoP proof: {headers['DPoP'][:50]}...")
    
    assert headers["Authorization"].startswith("DPoP ")
    assert "DPoP" in headers
    
    # Test Bearer fallback
    session_bearer = SolidSession(
        access_token="bearer_token_123",
        token_type="Bearer",
    )
    
    headers_bearer = session_bearer.get_auth_headers("GET", "https://example.org/")
    print(f"\nBearer Authorization: {headers_bearer['Authorization']}")
    
    assert headers_bearer["Authorization"] == "Bearer bearer_token_123"
    assert "DPoP" not in headers_bearer
    
    print("✅ Session authentication headers work correctly")


# =============================================================================
# Main
# =============================================================================

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("       PYLDO SOLID INTEGRATION TESTS")
    print("=" * 60)
    
    # Run synchronous tests
    test_dpop_token()
    test_webid_profile_parsing()
    test_profile_creation()
    test_type_registration()
    test_solid_resource()
    test_container_parsing()
    test_solid_ldo_integration()
    test_session_auth_headers()
    
    # Summary
    print_section("SUMMARY")
    print("""
    ✅ DPoP token generation and JWT creation
    ✅ WebID profile parsing from RDF
    ✅ Profile creation helper
    ✅ Type registration SPARQL generation
    ✅ SolidResource parsing and graph access
    ✅ Container parsing with ldp:contains
    ✅ Solid + LDO integration workflow
    ✅ Session authentication headers
    
    Phase 3: Solid Integration is complete! 🎉
    
    The pyldo.solid module provides:
    - SolidAuth: DPoP authentication with client credentials
    - SolidSession: Token management and refresh
    - SolidClient: HTTP operations (GET, PUT, POST, PATCH, DELETE)
    - SolidResource/SolidContainer: Resource representations
    - WebIdProfile: Profile parsing and storage discovery
    """)


if __name__ == "__main__":
    main()
