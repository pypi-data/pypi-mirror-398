"""
Solid authentication module.

Implements DPoP (Demonstration of Proof-of-Possession) token authentication,
client credentials flow, and Solid-OIDC browser flow for Solid Pod access.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urlparse

import httpx
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

# Import solid_oidc_client for browser-based OIDC flow
try:
    from solid_oidc_client import MemStore, SolidAuthSession, SolidOidcClient
    SOLID_OIDC_AVAILABLE = True
except ImportError:
    SOLID_OIDC_AVAILABLE = False
    SolidOidcClient = None
    SolidAuthSession = None
    MemStore = None


@dataclass
class ClientCredentials:
    """Client credentials for Solid authentication."""
    
    client_id: str
    client_secret: str
    token_endpoint: Optional[str] = None
    
    @classmethod
    def from_json(cls, data: dict) -> "ClientCredentials":
        """Create credentials from JSON data (e.g., from client registration)."""
        return cls(
            client_id=data["client_id"],
            client_secret=data["client_secret"],
            token_endpoint=data.get("token_endpoint"),
        )
    
    @classmethod
    def from_file(cls, path: str) -> "ClientCredentials":
        """Load credentials from a JSON file."""
        with open(path, "r") as f:
            return cls.from_json(json.load(f))


@dataclass
class DPoPToken:
    """
    DPoP (Demonstration of Proof-of-Possession) token handler.
    
    DPoP is used by Solid servers to bind access tokens to a specific client
    by requiring proof of possession of a private key.
    """
    
    private_key: ec.EllipticCurvePrivateKey = field(default_factory=lambda: None)
    public_key: ec.EllipticCurvePublicKey = field(default=None)
    _jwk_thumbprint: Optional[str] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Generate a new EC key pair if not provided."""
        if self.private_key is None:
            self.private_key = ec.generate_private_key(
                ec.SECP256R1(),
                default_backend()
            )
        if self.public_key is None:
            self.public_key = self.private_key.public_key()
    
    def get_public_jwk(self) -> dict:
        """Get the public key as a JWK (JSON Web Key)."""
        public_numbers = self.public_key.public_numbers()
        
        # Convert coordinates to base64url
        x_bytes = public_numbers.x.to_bytes(32, byteorder="big")
        y_bytes = public_numbers.y.to_bytes(32, byteorder="big")
        
        return {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x_bytes).rstrip(b"=").decode("ascii"),
            "y": base64.urlsafe_b64encode(y_bytes).rstrip(b"=").decode("ascii"),
        }
    
    def get_jwk_thumbprint(self) -> str:
        """Calculate the JWK thumbprint (used for token binding)."""
        if self._jwk_thumbprint is None:
            jwk = self.get_public_jwk()
            # Canonical JSON representation per RFC 7638
            canonical = json.dumps(
                {"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"], "y": jwk["y"]},
                separators=(",", ":"),
                sort_keys=True,
            )
            digest = hashlib.sha256(canonical.encode()).digest()
            self._jwk_thumbprint = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        return self._jwk_thumbprint
    
    def create_proof(self, method: str, url: str, access_token: Optional[str] = None) -> str:
        """
        Create a DPoP proof JWT for the given HTTP method and URL.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            url: Target URL
            access_token: Optional access token to bind (for authenticated requests)
        
        Returns:
            DPoP proof JWT string
        """
        # Parse URL to get just scheme + authority + path (no query/fragment)
        parsed = urlparse(url)
        htu = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        # Build the DPoP proof claims
        claims = {
            "jti": str(uuid.uuid4()),
            "htm": method.upper(),
            "htu": htu,
            "iat": int(time.time()),
        }
        
        # If we have an access token, include its hash (ath claim)
        if access_token:
            token_hash = hashlib.sha256(access_token.encode()).digest()
            claims["ath"] = base64.urlsafe_b64encode(token_hash).rstrip(b"=").decode("ascii")
        
        # Build the header with the public key
        headers = {
            "typ": "dpop+jwt",
            "alg": "ES256",
            "jwk": self.get_public_jwk(),
        }
        
        # Sign the JWT
        return jwt.encode(claims, self.private_key, algorithm="ES256", headers=headers)


@dataclass
class SolidSession:
    """
    Active Solid authentication session.
    
    Holds access tokens and handles token refresh.
    """
    
    access_token: str
    token_type: str = "DPoP"
    expires_at: Optional[float] = None
    refresh_token: Optional[str] = None
    webid: Optional[str] = None
    dpop: Optional[DPoPToken] = None
    _token_endpoint: Optional[str] = None
    _client_id: Optional[str] = None
    _client_secret: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at - 60  # 60 second buffer
    
    def get_auth_headers(self, method: str, url: str) -> dict:
        """
        Get authorization headers for an HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
        
        Returns:
            Dict of headers to add to the request
        """
        headers = {}
        
        if self.token_type == "DPoP" and self.dpop:
            # DPoP authentication
            headers["Authorization"] = f"DPoP {self.access_token}"
            headers["DPoP"] = self.dpop.create_proof(method, url, self.access_token)
        else:
            # Bearer token fallback
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    async def refresh(self, http_client: httpx.AsyncClient) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            True if refresh succeeded, False otherwise
        """
        if not self.refresh_token or not self._token_endpoint:
            return False
        
        try:
            # Prepare DPoP proof for token endpoint
            dpop_proof = None
            if self.dpop:
                dpop_proof = self.dpop.create_proof("POST", self._token_endpoint)
            
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            if dpop_proof:
                headers["DPoP"] = dpop_proof
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self._client_id,
            }
            if self._client_secret:
                data["client_secret"] = self._client_secret
            
            response = await http_client.post(
                self._token_endpoint,
                headers=headers,
                data=data,
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                self.refresh_token = token_data["refresh_token"]
            if "expires_in" in token_data:
                self.expires_at = time.time() + token_data["expires_in"]
            
            return True
            
        except Exception:
            return False


class SolidAuth:
    """
    Solid authentication handler.
    
    Supports client credentials flow with DPoP for machine-to-machine auth.
    """
    
    def __init__(
        self,
        credentials: Optional[ClientCredentials] = None,
        issuer: Optional[str] = None,
    ):
        """
        Initialize Solid auth handler.
        
        Args:
            credentials: Client credentials for authentication
            issuer: OIDC issuer URL (e.g., https://solidcommunityserver.net)
        """
        self.credentials = credentials
        self.issuer = issuer
        self._openid_config: Optional[dict] = None
        self._dpop = DPoPToken()
    
    async def discover_openid_config(self, http_client: httpx.AsyncClient) -> dict:
        """
        Discover OpenID Connect configuration from the issuer.
        
        Returns:
            OpenID configuration dict
        """
        if self._openid_config:
            return self._openid_config
        
        if not self.issuer:
            raise ValueError("No issuer configured for OIDC discovery")
        
        # Fetch .well-known/openid-configuration
        config_url = f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"
        response = await http_client.get(config_url)
        response.raise_for_status()
        
        self._openid_config = response.json()
        return self._openid_config
    
    async def login_with_credentials(
        self,
        http_client: httpx.AsyncClient,
        credentials: Optional[ClientCredentials] = None,
    ) -> SolidSession:
        """
        Authenticate using client credentials flow.
        
        This is typically used for server-to-server authentication where
        a client has been pre-registered with the identity provider.
        
        Args:
            http_client: HTTP client for making requests
            credentials: Optional credentials override
        
        Returns:
            SolidSession with access token
        """
        creds = credentials or self.credentials
        if not creds:
            raise ValueError("No credentials provided")
        
        # Get token endpoint
        token_endpoint = creds.token_endpoint
        if not token_endpoint:
            config = await self.discover_openid_config(http_client)
            token_endpoint = config["token_endpoint"]
        
        # Generate DPoP proof
        dpop_proof = self._dpop.create_proof("POST", token_endpoint)
        
        # Request token
        response = await http_client.post(
            token_endpoint,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "DPoP": dpop_proof,
            },
            data={
                "grant_type": "client_credentials",
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
            },
        )
        response.raise_for_status()
        
        token_data = response.json()
        
        # Calculate expiration time
        expires_at = None
        if "expires_in" in token_data:
            expires_at = time.time() + token_data["expires_in"]
        
        # Extract WebID from id_token if present
        webid = None
        if "id_token" in token_data:
            try:
                # Decode without verification to extract WebID
                id_token = jwt.decode(
                    token_data["id_token"],
                    options={"verify_signature": False}
                )
                webid = id_token.get("webid") or id_token.get("sub")
            except Exception:
                pass
        
        return SolidSession(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "DPoP"),
            expires_at=expires_at,
            refresh_token=token_data.get("refresh_token"),
            webid=webid,
            dpop=self._dpop,
            _token_endpoint=token_endpoint,
            _client_id=creds.client_id,
            _client_secret=creds.client_secret,
        )
    
    @staticmethod
    async def fetch_unauthenticated(
        http_client: httpx.AsyncClient,
        url: str,
    ) -> tuple[str, str]:
        """
        Fetch a public Solid resource without authentication.
        
        Args:
            http_client: HTTP client
            url: Resource URL
        
        Returns:
            Tuple of (content, content_type)
        """
        response = await http_client.get(
            url,
            headers={"Accept": "text/turtle, application/ld+json"},
        )
        response.raise_for_status()
        
        content_type = response.headers.get("content-type", "text/turtle")
        return response.text, content_type


class SolidOidcAuth:
    """
    Solid-OIDC authentication handler for browser-based login flows.
    
    This provides the same user experience as the JavaScript LDO library:
    users enter their Pod provider URL and are redirected to authenticate.
    
    Example (Flask):
        ```python
        from pyldo import SolidOidcAuth
        
        # Create auth handler
        auth = SolidOidcAuth()
        
        # Register with Pod provider
        auth.register("https://solidcommunity.net", ["http://localhost:5000/callback"])
        
        # In login route:
        login_url = auth.create_login_url("/", "http://localhost:5000/callback")
        return redirect(login_url)
        
        # In callback route:
        session = auth.finish_login(code, state, "http://localhost:5000/callback")
        # session.webid, session.get_auth_headers(url, method)
        ```
    
    Example (FastAPI):
        ```python
        from pyldo import SolidOidcAuth
        from fastapi import FastAPI, Request
        from fastapi.responses import RedirectResponse
        
        app = FastAPI()
        auth = SolidOidcAuth()
        
        @app.on_event("startup")
        async def startup():
            auth.register("https://solidcommunity.net", ["http://localhost:8000/callback"])
        
        @app.get("/login")
        async def login():
            login_url = auth.create_login_url("/", "http://localhost:8000/callback")
            return RedirectResponse(login_url)
        
        @app.get("/callback")
        async def callback(code: str, state: str):
            session = auth.finish_login(code, state, "http://localhost:8000/callback")
            # Store session, redirect to app
        ```
    """
    
    def __init__(self, storage=None):
        """
        Initialize the Solid-OIDC auth handler.
        
        Args:
            storage: Optional storage backend for OIDC state (default: MemStore)
        """
        if not SOLID_OIDC_AVAILABLE:
            raise ImportError(
                "solid_oidc_client is required for browser-based Solid-OIDC authentication. "
                "Install it with: pip install solid_oidc_client"
            )
        
        self._storage = storage or MemStore()
        self._client = SolidOidcClient(storage=self._storage)
        self._registered_issuers: set = set()
    
    def register(self, issuer: str, redirect_uris: List[str]) -> None:
        """
        Register this application with a Pod provider (issuer).
        
        This must be called before users can log in with this provider.
        You typically call this once at app startup for each provider you want to support.
        
        Args:
            issuer: The Pod provider URL (e.g., "https://solidcommunity.net")
            redirect_uris: List of allowed callback URLs for your app
        
        Example:
            ```python
            auth.register("https://solidcommunity.net", ["http://localhost:8000/callback"])
            auth.register("https://login.inrupt.com", ["http://localhost:8000/callback"])
            ```
        """
        issuer = issuer.rstrip("/")
        if issuer not in self._registered_issuers:
            self._client.register_client(issuer, redirect_uris)
            self._registered_issuers.add(issuer)
    
    def create_login_url(
        self,
        app_redirect_path: str,
        callback_uri: str,
        issuer: Optional[str] = None,
    ) -> str:
        """
        Create a login URL to redirect the user to their Pod provider.
        
        Args:
            app_redirect_path: Where to redirect in your app after login (e.g., "/")
            callback_uri: The OAuth callback URL (must be in registered redirect_uris)
            issuer: Optional Pod provider URL. If not specified and only one issuer
                   is registered, uses that one.
        
        Returns:
            URL to redirect the user to for authentication
        
        Example:
            ```python
            # User clicks "Log In" with provider "https://solidcommunity.net"
            login_url = auth.create_login_url("/dashboard", "http://localhost:8000/callback")
            return redirect(login_url)
            ```
        """
        if issuer:
            issuer = issuer.rstrip("/")
            if issuer not in self._registered_issuers:
                raise ValueError(
                    f"Issuer {issuer} not registered. Call auth.register() first."
                )
        elif len(self._registered_issuers) == 1:
            issuer = next(iter(self._registered_issuers))
        else:
            raise ValueError(
                "Multiple issuers registered. Please specify which issuer to use."
            )
        
        return self._client.create_login_uri(app_redirect_path, callback_uri)
    
    def finish_login(
        self,
        code: str,
        state: str,
        callback_uri: str,
    ) -> "SolidOidcSession":
        """
        Complete the login after the user returns from the Pod provider.
        
        Call this in your OAuth callback route with the code and state
        from the query parameters.
        
        Args:
            code: The authorization code from the callback query params
            state: The state parameter from the callback query params
            callback_uri: The same callback URI used in create_login_url
        
        Returns:
            SolidOidcSession with authentication details
        
        Example:
            ```python
            @app.get("/callback")
            async def callback(code: str, state: str):
                session = auth.finish_login(code, state, "http://localhost:8000/callback")
                print(f"Logged in as: {session.webid}")
                # Store session.serialize() to persist across requests
            ```
        """
        raw_session = self._client.finish_login(
            code=code,
            state=state,
            callback_uri=callback_uri,
        )
        
        return SolidOidcSession(raw_session)
    
    def get_redirect_path(self, state: str) -> str:
        """
        Get the application redirect path for a given state.
        
        Call this after finish_login to know where to redirect the user
        in your application.
        
        Args:
            state: The state parameter from the callback
        
        Returns:
            The app_redirect_path passed to create_login_url
        """
        return self._client.get_application_redirect_uri(state)


class SolidOidcSession:
    """
    An authenticated Solid-OIDC session.
    
    Provides methods to get authentication headers for making
    authenticated requests to Solid Pods.
    """
    
    def __init__(self, raw_session: "SolidAuthSession"):
        """
        Initialize from a raw solid_oidc_client session.
        
        Args:
            raw_session: The underlying SolidAuthSession from solid_oidc_client
        """
        self._session = raw_session
    
    @property
    def webid(self) -> Optional[str]:
        """Get the authenticated user's WebID."""
        return self._session.get_web_id()
    
    @property
    def is_logged_in(self) -> bool:
        """Check if the session is authenticated."""
        return self.webid is not None
    
    def get_auth_headers(self, url: str, method: str = "GET") -> dict:
        """
        Get authentication headers for an HTTP request.
        
        Use these headers when making requests to Solid Pods.
        
        Args:
            url: The URL you're requesting
            method: The HTTP method (GET, POST, PUT, DELETE, PATCH)
        
        Returns:
            Dict of headers to include in your request
        
        Example:
            ```python
            headers = session.get_auth_headers("https://pod.example.org/private/data.ttl", "GET")
            response = requests.get(url, headers=headers)
            ```
        """
        return self._session.get_auth_headers(url, method)
    
    def serialize(self) -> str:
        """
        Serialize the session to a string for storage.
        
        Use this to persist the session (e.g., in a cookie or server-side store).
        
        Returns:
            JSON string representation of the session
        """
        return self._session.serialize()
    
    @classmethod
    def deserialize(cls, data: str) -> "SolidOidcSession":
        """
        Restore a session from a serialized string.
        
        Args:
            data: The serialized session string from serialize()
        
        Returns:
            Restored SolidOidcSession
        
        Example:
            ```python
            # Restore from cookie/storage
            session = SolidOidcSession.deserialize(stored_session_data)
            if session.is_logged_in:
                headers = session.get_auth_headers(url, "GET")
            ```
        """
        if not SOLID_OIDC_AVAILABLE:
            raise ImportError("solid_oidc_client is required")
        
        raw_session = SolidAuthSession.deserialize(data)
        return cls(raw_session)
