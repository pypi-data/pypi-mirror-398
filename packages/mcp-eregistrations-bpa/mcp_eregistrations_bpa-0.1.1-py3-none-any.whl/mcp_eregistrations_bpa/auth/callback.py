"""Local HTTP server for OAuth callback.

This module provides a lightweight async HTTP server to receive
the authorization code from Keycloak after browser login.
"""

import asyncio
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread
from urllib.parse import parse_qs, urlparse

from mcp_eregistrations_bpa.exceptions import AuthenticationError

# Default timeout for waiting for callback
CALLBACK_TIMEOUT = 60.0  # seconds


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def log_message(self, format: str, *args: object) -> None:
        """Suppress default HTTP logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        # Parse query parameters
        params = parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        error = params.get("error", [None])[0]
        error_description = params.get("error_description", [None])[0]

        # Store results on server instance
        server = self.server
        if hasattr(server, "_callback_result"):
            if error:
                server._callback_result = {
                    "error": error,
                    "error_description": error_description,
                }
            else:
                server._callback_result = {
                    "code": code,
                    "state": state,
                }

        # Send success response to browser
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if error:
            html = f"""<!DOCTYPE html>
<html>
<head><title>Authentication Failed</title></head>
<body>
<h1>Authentication Failed</h1>
<p>Error: {error}</p>
<p>{error_description or ""}</p>
<p>You can close this window.</p>
</body>
</html>"""
        else:
            html = """<!DOCTYPE html>
<html>
<head><title>Authentication Complete</title></head>
<body>
<h1>Authentication Complete</h1>
<p>You have been successfully authenticated.</p>
<p>You can close this window and return to the application.</p>
</body>
</html>"""

        self.wfile.write(html.encode())


class CallbackServer:
    """Local HTTP server to receive OAuth callback.

    This server listens on localhost with a dynamic port and waits
    for the OAuth callback containing the authorization code.
    """

    def __init__(self, port: int = 0) -> None:
        """Initialize callback server.

        Args:
            port: Port to listen on. Use 0 for dynamic port assignment.
        """
        self._requested_port = port
        self._server: TCPServer | None = None
        self._thread: Thread | None = None

    @property
    def port(self) -> int:
        """Get the actual port the server is listening on."""
        if self._server is None:
            raise RuntimeError("Server not started")
        return self._server.server_address[1]

    @property
    def redirect_uri(self) -> str:
        """Get the redirect URI for OAuth configuration."""
        return f"http://127.0.0.1:{self.port}/callback"

    def start(self) -> None:
        """Start the callback server in a background thread."""
        self._server = TCPServer(("127.0.0.1", self._requested_port), CallbackHandler)
        self._server._callback_result = None  # type: ignore[attr-defined]
        self._thread = Thread(target=self._server.handle_request, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the callback server."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    async def wait_for_callback(
        self, expected_state: str, timeout: float = CALLBACK_TIMEOUT
    ) -> str:
        """Wait for OAuth callback and return authorization code.

        Args:
            expected_state: The state parameter to validate against.
            timeout: Maximum time to wait for callback in seconds.

        Returns:
            The authorization code from the callback.

        Raises:
            AuthenticationError: If callback fails or times out.
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            # Check if we have a result
            if self._server and self._server._callback_result:  # type: ignore[attr-defined]
                result = self._server._callback_result  # type: ignore[attr-defined]

                # Handle error response from Keycloak
                if "error" in result:
                    error = result.get("error", "unknown")
                    description = result.get("error_description", "")
                    raise AuthenticationError(
                        f"Authentication failed: {error}. {description}. "
                        "Please try again."
                    )

                # Validate state to prevent CSRF
                if result.get("state") != expected_state:
                    raise AuthenticationError(
                        "Authentication failed: Security validation failed "
                        "(state mismatch). Please try auth_login again."
                    )

                code = result.get("code")
                if not code:
                    raise AuthenticationError(
                        "Authentication failed: No authorization code received. "
                        "Please try again."
                    )

                return str(code)

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise AuthenticationError(
                    f"Authentication timed out: No response received within "
                    f"{int(timeout)} seconds. Please try auth_login again."
                )

            # Wait a bit before checking again
            await asyncio.sleep(0.1)
