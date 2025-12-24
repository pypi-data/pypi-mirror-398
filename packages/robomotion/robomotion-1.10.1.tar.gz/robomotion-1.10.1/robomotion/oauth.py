"""
OAuth2 Dialog Support for Robomotion Python SDK.

This module provides OAuth2 authentication flow support with a local callback server
for external packages like Google Calendar, Google Sheets, etc.
"""

import socket
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple
from dataclasses import dataclass

# OAuth2 Constants - must match robomotion-go
OAUTH2_REDIRECT_URL = "http://localhost:9876/oauth2/callback"
OAUTH2_CALLBACK_PORT = 9876

# Timing constants
OAUTH2_PORT_RETRY_INTERVAL = 5  # seconds
OAUTH2_PORT_MAX_TIMEOUT = 300  # seconds (5 minutes)
OAUTH2_AUTH_TIMEOUT = 300  # seconds (5 minutes)

# Module-level lock for OAuth operations
_oauth_mutex = threading.Lock()
_active_oauth_server: Optional[HTTPServer] = None


@dataclass
class OAuth2Config:
    """OAuth2 configuration matching Go's oauth2.Config structure."""
    client_id: str
    client_secret: str
    scopes: list
    auth_url: str
    token_url: str
    redirect_url: str = OAUTH2_REDIRECT_URL


class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth2 callback."""

    code: Optional[str] = None
    error: Optional[str] = None

    def log_message(self, format, *args):
        """Suppress HTTP server logging."""
        pass

    def do_GET(self):
        """Handle GET request for OAuth2 callback."""
        parsed = urlparse(self.path)

        if parsed.path != "/oauth2/callback":
            self.send_error(404)
            return

        params = parse_qs(parsed.query)

        # Check for authorization code
        if "code" in params:
            self.server.oauth_code = params["code"][0]
            self._send_success_page()
        else:
            # Handle error
            error_msg = params.get("error", ["no authorization code received"])[0]
            error_desc = params.get("error_description", [""])[0]
            if error_desc:
                error_msg = f"{error_msg}: {error_desc}"
            self.server.oauth_error = error_msg
            self._send_error_page(error_msg)

    def _send_success_page(self):
        """Send HTML success page to browser."""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>Authorization Successful</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
        .container { text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #4CAF50; margin-bottom: 16px; }
        p { color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Authorization Successful</h1>
        <p>You can close this window and return to the application.</p>
    </div>
</body>
</html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_error_page(self, error_msg: str):
        """Send HTML error page to browser."""
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Authorization Failed</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
        .container {{ text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #f44336; margin-bottom: 16px; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Authorization Failed</h1>
        <p>{error_msg}</p>
        <p>You can close this window and try again.</p>
    </div>
</body>
</html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


class OAuth2Server(HTTPServer):
    """Custom HTTP server for OAuth2 callback with result storage."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.oauth_code: Optional[str] = None
        self.oauth_error: Optional[str] = None


def _is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except (socket.error, OSError):
        return False


def _acquire_oauth_port() -> Tuple[Optional[OAuth2Server], Optional[str]]:
    """
    Attempt to bind to the OAuth callback port with retry logic.
    Returns (server, error_message) tuple.
    """
    start_time = time.time()
    attempt = 0

    while True:
        attempt += 1

        try:
            server = OAuth2Server(
                ('127.0.0.1', OAUTH2_CALLBACK_PORT),
                OAuth2CallbackHandler
            )

            if attempt > 1:
                elapsed = time.time() - start_time
                print(f"OAuth: Successfully acquired port {OAUTH2_CALLBACK_PORT} after {attempt} attempts (elapsed: {elapsed:.0f}s)")

            return server, None

        except OSError:
            # Port is busy
            elapsed = time.time() - start_time

            if elapsed >= OAUTH2_PORT_MAX_TIMEOUT:
                return None, (
                    f"OAuth failed: could not bind to port {OAUTH2_CALLBACK_PORT} after {OAUTH2_PORT_MAX_TIMEOUT}s "
                    f"({attempt} attempts). Port is in use by another process. "
                    "Please wait for the other OAuth flow to complete or restart the application."
                )

            remaining = OAUTH2_PORT_MAX_TIMEOUT - elapsed

            if attempt == 1:
                print(f"OAuth: Port {OAUTH2_CALLBACK_PORT} is busy, waiting for it to become available "
                      f"(will retry every {OAUTH2_PORT_RETRY_INTERVAL}s, timeout in {remaining:.0f}s)...")
            elif attempt % 6 == 0:  # Log every 30 seconds
                print(f"OAuth: Still waiting for port {OAUTH2_CALLBACK_PORT}... "
                      f"(attempt {attempt}, {remaining:.0f}s remaining)")

            time.sleep(OAUTH2_PORT_RETRY_INTERVAL)


def _build_auth_url(config: OAuth2Config, state: str = "state") -> str:
    """Build the OAuth2 authorization URL with proper parameters."""
    from urllib.parse import urlencode

    params = {
        "client_id": config.client_id,
        "redirect_uri": OAUTH2_REDIRECT_URL,
        "response_type": "code",
        "scope": " ".join(config.scopes),
        "state": state,
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Always show consent screen to get refresh_token
    }

    return f"{config.auth_url}?{urlencode(params)}"


def open_oauth_dialog(config: OAuth2Config) -> Tuple[Optional[str], Optional[str]]:
    """
    Open a browser for OAuth2 authorization and wait for the callback.

    Implements a retry mechanism for port binding: if the port is busy
    (e.g., another OAuth flow is in progress), it will retry every 5 seconds
    up to 300 seconds total. The server is always stopped after the OAuth
    flow completes (success or failure).

    Args:
        config: OAuth2Config with client credentials and endpoints

    Returns:
        Tuple of (authorization_code, error_message)
        On success: (code, None)
        On failure: (None, error_message)

    Usage:
        config = OAuth2Config(
            client_id="your-client-id",
            client_secret="your-client-secret",
            scopes=["scope1", "scope2"],
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
        )
        code, err = open_oauth_dialog(config)
        if err:
            raise Exception(err)
        # Exchange code for token using config.token_url
    """
    global _active_oauth_server

    # Ensure redirect URL is set correctly
    config.redirect_url = OAUTH2_REDIRECT_URL

    # Try to acquire the port with retry logic
    server, error = _acquire_oauth_port()
    if error:
        return None, error

    try:
        with _oauth_mutex:
            _active_oauth_server = server

        # Start server in a background thread
        server_thread = threading.Thread(target=server.handle_request)
        server_thread.daemon = True
        server_thread.start()

        # Build and open the authorization URL
        auth_url = _build_auth_url(config)

        if not webbrowser.open(auth_url):
            return None, "Failed to open browser for OAuth authorization"

        # Wait for callback with timeout
        server_thread.join(timeout=OAUTH2_AUTH_TIMEOUT)

        if server_thread.is_alive():
            return None, f"OAuth authorization timed out after {OAUTH2_AUTH_TIMEOUT}s waiting for user to complete authorization in browser"

        # Check results
        if server.oauth_code:
            return server.oauth_code, None
        elif server.oauth_error:
            return None, f"OAuth error: {server.oauth_error}"
        else:
            return None, "OAuth failed: no response received"

    finally:
        # Always clean up
        with _oauth_mutex:
            if _active_oauth_server:
                try:
                    _active_oauth_server.server_close()
                except Exception:
                    pass
                _active_oauth_server = None
