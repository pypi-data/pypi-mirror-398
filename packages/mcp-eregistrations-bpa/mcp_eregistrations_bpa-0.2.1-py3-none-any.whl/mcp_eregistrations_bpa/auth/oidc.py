"""OIDC Discovery and PKCE flow implementation.

This module handles Keycloak OIDC endpoint discovery and PKCE flow
for secure browser-based authentication.
"""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from mcp_eregistrations_bpa.exceptions import AuthenticationError

# PKCE constants
PKCE_VERIFIER_LENGTH = 32  # bytes, produces 43 char base64url string


class OIDCConfig(BaseModel):
    """OIDC configuration discovered from well-known endpoint."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str | None = None


async def discover_oidc_config(base_url: str) -> OIDCConfig:
    """Discover OIDC configuration from well-known endpoint.

    Args:
        base_url: The base URL for OIDC discovery. This is typically:
            - For Keycloak: https://login.example.org/realms/my-realm
            - Falls back to BPA URL if Keycloak URL not configured

    Returns:
        OIDCConfig with discovered endpoints.

    Raises:
        AuthenticationError: If discovery fails.
    """
    discovery_url = f"{base_url.rstrip('/')}/.well-known/openid-configuration"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(discovery_url, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AuthenticationError(
                f"Cannot discover Keycloak at {discovery_url}: "
                f"HTTP {e.response.status_code}. "
                "Verify KEYCLOAK_URL and KEYCLOAK_REALM are correct."
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(
                f"Cannot connect to Keycloak at {discovery_url}: {e}. "
                "Verify network connectivity and that Keycloak is accessible."
            ) from e

        try:
            data = response.json()
            return OIDCConfig(
                issuer=data["issuer"],
                authorization_endpoint=data["authorization_endpoint"],
                token_endpoint=data["token_endpoint"],
                userinfo_endpoint=data.get("userinfo_endpoint"),
            )
        except (KeyError, ValueError) as e:
            raise AuthenticationError(
                f"Invalid OIDC configuration response: {e}. "
                "The URL may not be a valid Keycloak realm endpoint."
            ) from e


def generate_pkce_pair() -> tuple[str, str]:
    """Generate PKCE code_verifier and code_challenge.

    Returns:
        Tuple of (code_verifier, code_challenge).
        The challenge is computed using S256 method.
    """
    # code_verifier: 43-128 characters, [A-Za-z0-9-._~]
    code_verifier = secrets.token_urlsafe(PKCE_VERIFIER_LENGTH)

    # code_challenge: SHA256(code_verifier) then base64url encode (no padding)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")

    return code_verifier, code_challenge


def generate_state() -> str:
    """Generate a cryptographically secure state parameter.

    Returns:
        A random state string for CSRF protection.
    """
    return secrets.token_urlsafe(16)


def build_authorization_url(
    authorization_endpoint: str,
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    state: str,
    scope: str = "openid email profile",
) -> str:
    """Build Keycloak authorization URL with PKCE.

    Args:
        authorization_endpoint: The Keycloak authorization endpoint.
        client_id: The OIDC client ID.
        redirect_uri: The local callback URL.
        code_challenge: The PKCE code challenge (S256).
        state: The state parameter for CSRF protection.
        scope: OAuth scopes to request.

    Returns:
        The complete authorization URL to open in browser.
    """
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return f"{authorization_endpoint}?{urlencode(params)}"


async def perform_browser_login() -> dict[str, object]:
    """Perform browser-based OIDC login flow.

    This is the core login implementation that can be called from
    both the auth_login tool and auto-auth in ensure_authenticated.

    Returns:
        dict: Authentication result with user email and session duration.

    Raises:
        AuthenticationError: If authentication fails.
    """
    import webbrowser

    from mcp_eregistrations_bpa.auth.callback import CallbackServer
    from mcp_eregistrations_bpa.auth.token_manager import exchange_code_for_tokens
    from mcp_eregistrations_bpa.config import load_config

    # Load configuration
    config = load_config()

    # Discover OIDC endpoints
    oidc_config = await discover_oidc_config(config.oidc_discovery_url)

    # Generate PKCE pair and state
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()

    # Start callback server
    callback_server = CallbackServer()
    callback_server.start()

    try:
        # Build authorization URL
        auth_url = build_authorization_url(
            authorization_endpoint=oidc_config.authorization_endpoint,
            client_id=config.keycloak_client_id,
            redirect_uri=callback_server.redirect_uri,
            code_challenge=code_challenge,
            state=state,
        )

        # Open browser
        if not webbrowser.open(auth_url):
            return {
                "error": True,
                "message": (
                    "Cannot open browser for authentication. "
                    f"Please open this URL manually: {auth_url}"
                ),
            }

        # Wait for callback
        code = await callback_server.wait_for_callback(expected_state=state)

        # Exchange code for tokens
        token_response = await exchange_code_for_tokens(
            token_endpoint=oidc_config.token_endpoint,
            code=code,
            code_verifier=code_verifier,
            redirect_uri=callback_server.redirect_uri,
            client_id=config.keycloak_client_id,
        )

        # Get token manager and store tokens
        from mcp_eregistrations_bpa.server import get_token_manager

        token_manager = get_token_manager()
        token_manager.store_tokens(
            access_token=token_response.access_token,
            refresh_token=token_response.refresh_token,
            expires_in=token_response.expires_in,
            token_endpoint=oidc_config.token_endpoint,
            client_id=config.keycloak_client_id,
        )

        return {
            "success": True,
            "message": (
                f"Authenticated as {token_manager.user_email}. "
                f"Session valid for {token_manager.expires_in_minutes} minutes."
            ),
            "user_email": token_manager.user_email,
            "session_expires_in_minutes": token_manager.expires_in_minutes,
        }

    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(
            f"Authentication failed: {e}. Please try again."
        ) from e
    finally:
        callback_server.stop()
