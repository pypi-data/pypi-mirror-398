"""In-memory token storage and automatic refresh.

This module handles token lifecycle management including storage,
refresh, and expiry checks. Tokens are stored in memory only
(never persisted to disk) per NFR2 and NFR6.
"""

import base64
import json
from datetime import UTC, datetime, timedelta

import httpx
from pydantic import BaseModel

from mcp_eregistrations_bpa.exceptions import AuthenticationError

# Refresh tokens 5 minutes before expiry (NFR3)
REFRESH_THRESHOLD_SECONDS = 300


class TokenResponse(BaseModel):
    """Response from token endpoint."""

    access_token: str
    refresh_token: str | None = None
    expires_in: int
    token_type: str = "Bearer"


class TokenManager:
    """In-memory token storage with automatic refresh.

    Tokens are stored in memory only and never persisted to disk.
    Automatic refresh is triggered when the access token is within
    5 minutes of expiry (NFR3).
    """

    def __init__(self) -> None:
        """Initialize token manager with empty state."""
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._expires_at: datetime | None = None
        self._token_endpoint: str | None = None
        self._client_id: str | None = None
        self._user_email: str | None = None
        self._permissions: list[str] = []

    @property
    def user_email(self) -> str | None:
        """Get the authenticated user's email."""
        return self._user_email

    @property
    def expires_in_minutes(self) -> int:
        """Get remaining session time in minutes."""
        if self._expires_at is None:
            return 0
        remaining = self._expires_at - datetime.now(UTC)
        return max(0, int(remaining.total_seconds() / 60))

    @property
    def permissions(self) -> list[str]:
        """Get the authenticated user's permissions/roles.

        Returns a copy to prevent external mutation of internal state.
        """
        return list(self._permissions)

    def is_token_expired(self) -> bool:
        """Check if a stored token has already expired (without triggering refresh).

        This method should only be called after verifying is_authenticated() is True.
        When no token exists (_expires_at is None), returns False because there's
        nothing to consider "expired" - use is_authenticated() to check presence.

        Returns:
            True if token exists AND is expired, False otherwise.
        """
        if self._expires_at is None:
            return False
        return datetime.now(UTC) >= self._expires_at

    def is_authenticated(self) -> bool:
        """Check if we have valid tokens.

        Returns:
            True if we have tokens (may need refresh), False if not authenticated.
        """
        return self._access_token is not None

    def store_tokens(
        self,
        access_token: str,
        refresh_token: str | None,
        expires_in: int,
        token_endpoint: str | None = None,
        client_id: str | None = None,
    ) -> None:
        """Store tokens in memory.

        Args:
            access_token: The access token from Keycloak.
            refresh_token: The refresh token from Keycloak.
            expires_in: Token lifetime in seconds.
            token_endpoint: The token endpoint for refresh (optional).
            client_id: The client ID for refresh (optional).
        """
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        if token_endpoint:
            self._token_endpoint = token_endpoint
        if client_id:
            self._client_id = client_id

        # Extract user email and permissions from access token
        self._user_email = self._extract_email_from_token(access_token)
        self._permissions = self._extract_permissions_from_token(access_token)

    def clear_tokens(self) -> None:
        """Clear all stored tokens (logout)."""
        self._access_token = None
        self._refresh_token = None
        self._expires_at = None
        self._user_email = None
        self._permissions = []

    def _needs_refresh(self) -> bool:
        """Check if token needs refresh (within 5 minutes of expiry).

        Returns:
            True if token should be refreshed, False otherwise.
        """
        if self._expires_at is None:
            return False
        threshold = datetime.now(UTC) + timedelta(seconds=REFRESH_THRESHOLD_SECONDS)
        return self._expires_at <= threshold

    async def get_access_token(self) -> str:
        """Get valid access token, refreshing if needed.

        Returns:
            A valid access token.

        Raises:
            AuthenticationError: If not authenticated or refresh fails.
        """
        if self._access_token is None:
            raise AuthenticationError("Not authenticated. Run auth_login first.")

        if self._needs_refresh():
            await self._refresh()

        if self._access_token is None:
            raise AuthenticationError("Session expired. Please run auth_login again.")

        return self._access_token

    async def _refresh(self) -> None:
        """Refresh the access token using refresh token.

        Raises:
            AuthenticationError: If refresh fails.
        """
        if self._refresh_token is None:
            raise AuthenticationError("Session expired. Please run auth_login again.")

        if self._token_endpoint is None or self._client_id is None:
            raise AuthenticationError("Session expired. Please run auth_login again.")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self._token_endpoint,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self._refresh_token,
                        "client_id": self._client_id,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Refresh token is invalid/expired
                self.clear_tokens()
                raise AuthenticationError(
                    "Session expired. Please run auth_login again."
                ) from e
            except httpx.RequestError as e:
                raise AuthenticationError(
                    f"Cannot refresh session: {e}. Please try again."
                ) from e

            data = response.json()
            self.store_tokens(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", self._refresh_token),
                expires_in=data["expires_in"],
            )

    def _decode_jwt_payload(self, token: str) -> dict[str, object] | None:
        """Decode and return JWT payload claims.

        Args:
            token: The JWT access token.

        Returns:
            Decoded claims dict, or None if decoding fails.
        """
        try:
            # JWT is three base64-encoded parts separated by dots
            parts = token.split(".")
            if len(parts) != 3:
                return None

            # Decode the payload (second part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding

            decoded = base64.urlsafe_b64decode(payload)
            claims: dict[str, object] = json.loads(decoded)
            return claims
        except Exception:
            return None

    def _extract_email_from_token(self, token: str) -> str | None:
        """Extract user email from JWT access token.

        Args:
            token: The JWT access token.

        Returns:
            The user email if found, None otherwise.
        """
        claims = self._decode_jwt_payload(token)
        if claims is None:
            return None

        # Try common email claim names
        email = claims.get("email") or claims.get("preferred_username")
        return str(email) if email else None

    def _extract_permissions_from_token(self, token: str) -> list[str]:
        """Extract permissions/roles from JWT access token.

        Parses Keycloak standard claims for realm and resource access roles.

        Args:
            token: The JWT access token.

        Returns:
            List of role names from realm_access and resource_access claims.
        """
        claims = self._decode_jwt_payload(token)
        if claims is None:
            return []

        roles: list[str] = []

        # Extract realm roles (Keycloak standard)
        realm_access = claims.get("realm_access")
        if isinstance(realm_access, dict) and "roles" in realm_access:
            roles.extend(realm_access["roles"])

        # Extract client-specific roles (Keycloak resource_access)
        resource_access = claims.get("resource_access")
        if isinstance(resource_access, dict):
            for _client, access in resource_access.items():
                if isinstance(access, dict) and "roles" in access:
                    roles.extend(access["roles"])

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_roles: list[str] = []
        for role in roles:
            if role not in seen:
                seen.add(role)
                unique_roles.append(role)

        return unique_roles


async def exchange_code_for_tokens(
    token_endpoint: str,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
) -> TokenResponse:
    """Exchange authorization code for tokens.

    Args:
        token_endpoint: The Keycloak token endpoint.
        code: The authorization code from callback.
        code_verifier: The PKCE code verifier.
        redirect_uri: The redirect URI used in authorization.
        client_id: The OIDC client ID.

    Returns:
        TokenResponse with access and refresh tokens.

    Raises:
        AuthenticationError: If token exchange fails.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "code_verifier": code_verifier,
                },
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get(
                    "error_description", error_data.get("error", "")
                )
            except Exception:
                pass
            raise AuthenticationError(
                f"Authentication failed: {error_detail or 'Token exchange failed'}. "
                "Please try again."
            ) from e
        except httpx.RequestError as e:
            raise AuthenticationError(
                f"Authentication failed: {e}. Please try again."
            ) from e

        data = response.json()
        return TokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data["expires_in"],
            token_type=data.get("token_type", "Bearer"),
        )
