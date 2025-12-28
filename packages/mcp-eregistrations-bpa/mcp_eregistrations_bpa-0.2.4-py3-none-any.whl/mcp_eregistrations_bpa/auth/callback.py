"""Local HTTP server for OAuth callback.

This module provides a lightweight async HTTP server to receive
the authorization code from Keycloak after browser login.
"""
# ruff: noqa: E501, N802  # E501: HTML templates contain long lines, N802: do_GET required by BaseHTTPRequestHandler

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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Denied - eRegistrations BPA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #ffffff;
            --text-primary: #1a1a1a;
            --text-secondary: #5e5e5e;
            --brand-red: #e60000;
            --border-color: #dcdcdc;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f4f4f4;
            color: var(--text-primary);
            padding: 24px;
        }}
        .container {{
            background: var(--bg-color);
            width: 100%;
            max-width: 480px;
            padding: 48px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border-top: 4px solid var(--brand-red);
        }}
        .header {{
            margin-bottom: 32px;
        }}
        h1 {{
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.1;
            margin-bottom: 16px;
        }}
        .status-line {{
            display: inline-block;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}
        p {{
            font-size: 18px;
            line-height: 1.5;
            color: var(--text-secondary);
            margin-bottom: 32px;
        }}
        .error-code {{
            font-family: monospace;
            background: #f0f0f0;
            padding: 8px 12px;
            font-size: 14px;
            color: var(--text-primary);
            display: inline-block;
            margin-top: 16px;
        }}
        .footer {{
            margin-top: 48px;
            border-top: 1px solid var(--border-color);
            padding-top: 24px;
            font-size: 12px;
            color: #999;
            display: flex;
            justify-content: space-between;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="status-line">Authorization Status</span>
            <h1>Access Denied</h1>
        </div>
        <p>The system could not verify your credentials. Ensure your security token is valid and try again.</p>

        <div class="error-details">
            <div class="status-line" style="font-size: 12px;">System Response</div>
            <div style="font-weight: 600;">{error_description or "Unknown Error"}</div>
            {f'<div class="error-code">{error}</div>' if error else ""}
        </div>

        <div class="footer">
            <span>AI-Native Digital Government System</span>
            <span>BPA MCP</span>
        </div>
    </div>
</body>
</html>"""
        else:
            html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Access Authorized - eRegistrations BPA</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #ffffff;
            --text-primary: #1a1a1a;
            --text-secondary: #5e5e5e;
            --brand-green: #107c10;
            --border-color: #dcdcdc;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f4f4f4;
            color: var(--text-primary);
            padding: 24px;
        }
        .container {
            background: var(--bg-color);
            width: 100%;
            max-width: 480px;
            padding: 48px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border-top: 4px solid var(--brand-green);
        }
        .header {
            margin-bottom: 32px;
        }
        h1 {
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.02em;
            line-height: 1.1;
            margin-bottom: 16px;
        }
        .status-line {
            display: inline-block;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }
        p {
            font-size: 18px;
            line-height: 1.5;
            color: var(--text-secondary);
            margin-bottom: 32px;
        }
        .footer {
            margin-top: 64px;
            border-top: 1px solid var(--border-color);
            padding-top: 24px;
            font-size: 12px;
            color: #999;
            display: flex;
            justify-content: space-between;
        }
        /* USB-style clean chevron */
        .check-icon {
            display: inline-block;
            width: 16px;
            height: 16px;
            background-color: var(--brand-green);
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 16px;
            font-size: 10px;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="status-line">Authorization Status</span>
            <h1>Access Authorized</h1>
        </div>
        <p>Your AI agent now has secure access to BPA backend functions.</p>

        <div style="font-size: 15px; color: var(--text-secondary); display: flex; align-items: center;">
            <span class="check-icon">✓</span> You can close this window.
        </div>

        <div class="footer">
            <span>AI-Native Digital Government System</span>
            <span>BPA MCP</span>
        </div>
    </div>
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
