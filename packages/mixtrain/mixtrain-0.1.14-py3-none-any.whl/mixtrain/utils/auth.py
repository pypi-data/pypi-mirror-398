"""Authentication utilities for Mixtrain CLI."""

import http.server
import os
import socketserver
import threading
import webbrowser
from logging import getLogger
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, quote, urlparse

logger = getLogger(__name__)


class TokenHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for receiving OAuth token from browser."""

    def __init__(self, *args, token_received_callback=None, **kwargs):
        self.token_received_callback = token_received_callback
        super().__init__(*args, **kwargs)

    def log_request(self, format, *args):
        pass # no logging

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        # Parse query parameters for token data
        
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Check if this is a callback with token
        if 'access_token' in query_params:
            try:
                # Extract simple token data
                access_token = query_params.get('access_token', [None])[0]
                workspaces_param = query_params.get('workspaces', [''])[0]
                default_workspace = query_params.get('default_workspace', [None])[0]
                
                if access_token:
                    # Parse workspaces from comma-separated format
                    workspaces = []
                    if workspaces_param:
                        workspace_names = workspaces_param.split('&')
                        for name in workspace_names:
                            if name.startswith('workspace='):
                                name = name.split('=')[1]
                                workspaces.append({'name': name.strip()})
                    
                    # Create auth data
                    auth_data = {
                        'access_token': access_token,
                        'workspaces': workspaces,
                        'default_workspace': default_workspace
                    }
                    
                    # Call the token callback
                    if self.token_received_callback:
                        self.token_received_callback(auth_data)
                    

                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"Token received")
                    # Send basic HTML redirecting to mixtrain.ai, dashboard redirect runs into issues
                    self.wfile.write(b"""
                    <html>
                    <body>
                    <script>
                        window.close();
                        window.location.href = 'https://mixtrain.ai';
                    </script>
                    </body>
                    </html>""")
                    return
                    
            except Exception as e:
                logger.error(f"Error processing token from callback: {e}")
        
        # Default GET response for non-callback requests
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Waiting for token...")


def start_local_server(port: int = 8001) -> Tuple[socketserver.TCPServer, threading.Event, list]:
    """Start a local server to receive the OAuth callback."""
    ready_event = threading.Event()
    received_data = []
    
    def token_callback(data):
        received_data.append(data)
        ready_event.set()
    
    # Allow reuse of the port in case of previous failed attempts
    socketserver.TCPServer.allow_reuse_address = True
    
    class Handler(TokenHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, token_received_callback=token_callback, **kwargs)
    
    try:
        server = socketserver.TCPServer(('localhost', port), Handler)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server, ready_event, received_data
    except Exception as e:
        logger.error(f"Error starting local server: {e}")
        raise Exception(f"Failed to start local server: {e}")


def authenticate_with_server(token: str, provider: str, call_api_func) -> Dict[str, Any]:
    """Authenticate with the server and get workspace info."""
    response = call_api_func(
        "POST",
        f"/auth/verify/{provider}",
        json={"token": token}
    )
    return response.json()


def authenticate_browser(get_config_func, call_api_func) -> str:
    """Authenticate using browser-based OAuth flow."""
    from .config import WorkspaceConfig
    
    config = get_config_func()
    cli_login_url = os.getenv("FRONTEND_URL", "https://app.mixtrain.ai") + "/auth/cli-login"

    # Start local server to receive the token
    server, ready_event, received_data = start_local_server()
    
    try:
        # Get the actual port from the server and construct callback URL
        server_port = server.server_address[1]
        callback_url = f"http://localhost:{server_port}"
        auth_url = f"{cli_login_url}?callback_url={quote(callback_url)}"
        
        print(f"Opening browser to authenticate: {auth_url}")
        webbrowser.open(auth_url)
        
        # Wait for token
        ready_event.wait(timeout=300)  # 5 minute timeout
        if not received_data:
            raise Exception("Authentication timeout or cancelled")
        
        # Process response data
        auth_data = received_data[0]
        token = auth_data.get("access_token")
        workspaces = auth_data.get("workspaces", [])
        default_workspace = auth_data.get("default_workspace")
        
        if not token:
            raise Exception("No token received")
        
        # Store token and workspaces info
        config = get_config_func()
        config.set_auth_token(token)
        config.workspaces = [WorkspaceConfig(name=w['name'], active=False) for w in workspaces]
        
        if workspaces:
            # Select default workspace when provided
            selected = None
            if default_workspace:
                selected = next((w for w in workspaces if w.get("name") == default_workspace), None)
            if not selected:
                selected = workspaces[0]

            # set active workspace
            config.set_workspace(selected["name"])
        return token
    finally:
        server.shutdown()
        server.server_close()


def authenticate_with_token(token: str, provider: str, get_config_func, call_api_func) -> str:
    """Authenticate using OAuth token (GitHub or Google)."""
    # Get workspace info from server
    auth_data = authenticate_with_server(token, provider, call_api_func)
    
    # Store token and workspace info
    access_token = auth_data.get("access_token")
    workspaces = auth_data.get("workspaces", [])
    default_workspace = auth_data.get("default_workspace")
    
    if not access_token:
        raise Exception("No token received")
    
    config = get_config_func()
    if workspaces:
        # Select default workspace when provided
        selected = None
        if default_workspace:
            selected = next((w for w in workspaces if w.get("name") == default_workspace), None)
        if not selected:
            selected = workspaces[0]
        config.set_auth_token(access_token, {
            "name": selected["name"]
        })
    else:
        config.set_auth_token(access_token)
    
    return access_token


def authenticate_github(access_token: str, get_config_func, call_api_func) -> str:
    """Authenticate using GitHub access token."""
    return authenticate_with_token(access_token, "github", get_config_func, call_api_func)


def authenticate_google(id_token: str, get_config_func, call_api_func) -> str:
    """Authenticate using Google ID token."""
    return authenticate_with_token(id_token, "google", get_config_func, call_api_func)