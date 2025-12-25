"""ASGI application for the preview server."""

import asyncio
import base64
import importlib.resources
import json
import logging
import secrets
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Optional

import httpx
import websockets
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from preview_server.sub_server import SubServerManager
from preview_server import templates


class BasicAuthMixin:
    """Mixin providing HTTP Basic Authentication functionality.

    Classes using this mixin must set:
        - self.basic_auth_user: Optional[str]
        - self.basic_auth_pass: Optional[str]
    """

    basic_auth_user: Optional[str]
    basic_auth_pass: Optional[str]

    def _parse_basic_auth(
        self, basic_auth: Optional[str]
    ) -> tuple[Optional[str], Optional[str]]:
        """Parse and validate basic auth credentials.

        Args:
            basic_auth: Credentials in "user:pass" format, or None

        Returns:
            Tuple of (username, password), or (None, None) if not configured

        Raises:
            ValueError: If format is invalid or credentials are empty
        """
        if not basic_auth:
            return (None, None)

        if ":" not in basic_auth:
            raise ValueError("Basic auth must be in 'user:pass' format")

        user, passwd = basic_auth.split(":", 1)
        if not user or not passwd:
            raise ValueError("Both username and password must be non-empty")

        return (user, passwd)

    def _check_basic_auth(self, request: Request) -> Optional[Response]:
        """Check basic auth credentials if configured.

        Args:
            request: The incoming request

        Returns:
            None if auth passes or not configured, Response with 401 if auth fails
        """
        if self.basic_auth_user is None:
            return None  # No auth configured

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Basic "):
            return self._unauthorized_response()

        try:
            # Decode the base64 credentials
            encoded_credentials = auth_header[6:]  # Remove "Basic " prefix
            decoded = base64.b64decode(encoded_credentials).decode("utf-8")

            if ":" not in decoded:
                return self._unauthorized_response()

            provided_user, provided_pass = decoded.split(":", 1)

            # Use constant-time comparison to prevent timing attacks
            user_matches = secrets.compare_digest(
                provided_user.encode("utf-8"), self.basic_auth_user.encode("utf-8")
            )
            pass_matches = secrets.compare_digest(
                provided_pass.encode("utf-8"), self.basic_auth_pass.encode("utf-8")
            )

            if user_matches and pass_matches:
                return None  # Auth passed

            return self._unauthorized_response()

        except Exception:
            return self._unauthorized_response()

    def _unauthorized_response(self) -> Response:
        """Create a 401 Unauthorized response with WWW-Authenticate header."""
        return Response(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Preview Server"'},
        )


def _load_template(name: str) -> str:
    """Load an HTML template from the templates package.

    Args:
        name: Template filename (e.g., 'status.html')

    Returns:
        The template content as a string
    """
    return (
        importlib.resources.files(templates).joinpath(name).read_text(encoding="utf-8")
    )


def parse_hostname(
    hostname: str, multi_repo: bool = False, base_domain: str = "localhost"
) -> tuple[Optional[str], Optional[str]]:
    """Parse hostname to extract project and ref.

    In single-repo mode:
        - "main.localhost:8000" -> (None, "main")
        - "localhost:8000" -> (None, None)

    In multi-repo mode:
        - "project.localhost:8000" -> ("project", None)  # None ref means default branch
        - "project--main.localhost:8000" -> ("project", "main")
        - "project--a55cb79.localhost:8000" -> ("project", "a55cb79")
        - "proj--feat--test.localhost" -> ("proj", "feat--test")  # First -- is delimiter

    Custom domains are also supported via the base_domain parameter:
        - "main.example.com" with base_domain="example.com" -> (None, "main")
        - "foo--bar.subdomain.example.com" with base_domain="subdomain.example.com"
          -> ("foo", "bar")

    Args:
        hostname: The request hostname (e.g., "main.localhost:8000")
        multi_repo: Whether multi-repo mode is enabled
        base_domain: The base domain to match against (default: "localhost")

    Returns:
        Tuple of (project, ref). In single-repo mode, project is always None.
        If ref is None in multi-repo mode, it means use the default branch.
    """
    if not hostname:
        return (None, None)

    # Remove port
    host_parts = hostname.split(":")
    host = host_parts[0]

    # Build the domain suffix to look for
    domain_suffix = f".{base_domain}"

    # Check for base_domain pattern
    if not host.endswith(domain_suffix) and host != base_domain:
        return (None, None)

    # Extract subdomain (everything before .base_domain)
    if host == base_domain:
        # No subdomain, just the base domain
        return (None, None)

    subdomain = host[: -len(domain_suffix)]
    if not subdomain:
        return (None, None)

    if not multi_repo:
        # Single-repo mode: subdomain is the ref
        return (None, subdomain)

    # Multi-repo mode: parse project--ref pattern
    # First occurrence of -- is the delimiter
    if "--" in subdomain:
        parts = subdomain.split("--", 1)
        project = parts[0]
        ref = parts[1] if len(parts) > 1 else None
        return (project, ref)
    else:
        # No --, subdomain is just the project name, use default ref
        return (subdomain, None)


class BasePreviewServerApp(BasicAuthMixin, ABC):
    """Base class for preview server applications with shared proxy/streaming logic."""

    def __init__(
        self,
        basic_auth: Optional[str] = None,
        secret: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the base preview server app.

        Args:
            basic_auth: Optional basic auth credentials in "user:pass" format
            secret: Optional signing secret for hostname verification
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.client = httpx.AsyncClient(timeout=None)
        self.secret = secret

        # Parse and store basic auth credentials
        self.basic_auth_user, self.basic_auth_pass = self._parse_basic_auth(basic_auth)

    def _check_signature(self, hostname: str) -> tuple[bool, str]:
        """Check hostname signature if secret is configured.

        Args:
            hostname: The subdomain portion of the hostname (e.g., "main--signature")

        Returns:
            Tuple of (is_valid, extracted_ref). If signature is valid or no secret
            configured, returns (True, ref). If invalid, returns (False, "").
        """
        if self.secret is None:
            # No signature checking enabled, pass through as-is
            return (True, hostname)

        # Import signing module
        from preview_server.signing import verify_signature, extract_hostname

        # Verify the signature
        if not verify_signature(hostname, self.secret):
            return (False, "")

        # Extract the original hostname (without signature)
        original = extract_hostname(hostname)
        return (True, original)

    def _forbidden_response(
        self, message: str = "Forbidden: Invalid signature"
    ) -> Response:
        """Create a 403 Forbidden response for signature failures."""
        return Response(message, status_code=403)

    async def _proxy_request(self, request: Request, port: int) -> Response:
        """Proxy a request to a sub-server.

        Args:
            request: The incoming request
            port: The port of the sub-server

        Returns:
            The response from the sub-server
        """
        try:
            # Build the target URL
            target_url = f"http://127.0.0.1:{port}{request.url.path}"
            if request.url.query:
                target_url += f"?{request.url.query}"

            # Build headers with forwarding information
            headers = dict(request.headers)
            headers.pop("host", None)

            # Get client IP and properly chain X-Forwarded-For
            client_ip = request.client.host if request.client else "127.0.0.1"
            existing_xff = headers.get("x-forwarded-for", "")
            if existing_xff:
                headers["x-forwarded-for"] = f"{existing_xff}, {client_ip}"
            else:
                headers["x-forwarded-for"] = client_ip

            # Add other standard proxy headers
            headers["x-forwarded-host"] = request.headers.get("host", "")
            headers["x-forwarded-proto"] = request.url.scheme or "http"
            headers["x-real-ip"] = client_ip

            # Stream the request body instead of buffering
            async def stream_request_body():
                async for chunk in request.stream():
                    yield chunk

            # Forward the request with streaming body
            response = await self.client.request(
                method=request.method,
                url=target_url,
                content=stream_request_body(),
                headers=headers,
            )

            # Stream the response
            return StreamingResponse(
                self._iter_response(response),
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except httpx.ConnectError:
            return Response("Sub-server is not responding", status_code=503)
        except Exception as e:
            self.logger.error(f"Error proxying request to port {port}: {e}")
            return Response(f"Proxy error: {e}", status_code=502)

    async def _iter_response(self, response):
        """Iterate over response bytes for streaming."""
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            await response.aclose()

    async def _handle_status_html(self, request: Request) -> Response:
        """Handle the HTML status dashboard endpoint.

        Args:
            request: The incoming request

        Returns:
            HTML response with status dashboard
        """
        html = _load_template("status.html")
        return Response(html, status_code=200, media_type="text/html")

    def _check_websocket_auth(self, websocket: WebSocket) -> bool:
        """Check WebSocket authentication via query param token.

        Args:
            websocket: The incoming WebSocket connection

        Returns:
            True if auth passes or not configured, False if auth fails
        """
        if self.basic_auth_user is None:
            return True

        auth_token = websocket.query_params.get("token")
        if not auth_token:
            return False

        try:
            decoded = base64.b64decode(auth_token).decode("utf-8")
            if ":" not in decoded:
                return False

            provided_user, provided_pass = decoded.split(":", 1)
            user_matches = secrets.compare_digest(
                provided_user.encode("utf-8"),
                self.basic_auth_user.encode("utf-8"),
            )
            pass_matches = secrets.compare_digest(
                provided_pass.encode("utf-8"),
                self.basic_auth_pass.encode("utf-8"),
            )
            return user_matches and pass_matches
        except Exception:
            return False

    async def _proxy_websocket(
        self, websocket: WebSocket, port: int, path: str, query: str
    ) -> None:
        """Proxy a WebSocket connection to a backend server.

        Args:
            websocket: The accepted WebSocket connection
            port: The port of the sub-server
            path: The request path
            query: The query string
        """
        backend_url = f"ws://127.0.0.1:{port}{path}"
        if query:
            backend_url += f"?{query}"

        try:
            async with websockets.connect(backend_url) as backend_ws:

                async def client_to_backend():
                    """Relay messages from client to backend."""
                    try:
                        while True:
                            message = await websocket.receive()
                            if message["type"] == "websocket.receive":
                                if "text" in message:
                                    await backend_ws.send(message["text"])
                                elif "bytes" in message:
                                    await backend_ws.send(message["bytes"])
                            elif message["type"] == "websocket.disconnect":
                                break
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        self.logger.debug(f"Client to backend relay error: {e}")

                async def backend_to_client():
                    """Relay messages from backend to client."""
                    try:
                        async for message in backend_ws:
                            if isinstance(message, str):
                                await websocket.send_text(message)
                            else:
                                await websocket.send_bytes(message)
                    except Exception as e:
                        self.logger.debug(f"Backend to client relay error: {e}")

                # Run both relay tasks concurrently
                client_task = asyncio.create_task(client_to_backend())
                backend_task = asyncio.create_task(backend_to_client())

                # Wait for either task to complete (connection closed)
                done, pending = await asyncio.wait(
                    [client_task, backend_task], return_when=asyncio.FIRST_COMPLETED
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        except websockets.exceptions.InvalidStatusCode as e:
            self.logger.error(f"Backend WebSocket connection failed: {e}")
            await websocket.close(code=4004, reason="Backend connection failed")
        except Exception as e:
            self.logger.error(f"WebSocket proxy error: {e}")
            try:
                await websocket.close(code=4005, reason="Proxy error")
            except Exception:
                pass

    @abstractmethod
    async def handle_request(self, request: Request) -> Response:
        """Handle incoming HTTP requests."""
        pass

    @abstractmethod
    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle incoming WebSocket connections."""
        pass

    @abstractmethod
    async def _handle_status_json(self, request: Request) -> Response:
        """Handle the JSON status endpoint."""
        pass

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def _build_error_html(ref: str, error_msg: str) -> tuple[int, str]:
    """Build error HTML response for server startup failures.

    Args:
        ref: The git ref that failed
        error_msg: The error message

    Returns:
        Tuple of (status_code, html_content)
    """
    # Determine the status code based on the error message
    if "not found in repository" in error_msg.lower():
        status_code = 404
        title = "Branch Not Found"
        suggestion = """
        <p><strong>This branch does not exist in the repository.</strong></p>
        <p>Please verify:</p>
        <ul>
            <li>The branch name is spelled correctly</li>
            <li>The branch exists in the remote repository</li>
            <li>You have permission to access the repository</li>
        </ul>
        """
    elif "fetch" in error_msg.lower():
        status_code = 503
        title = "Unable to Fetch Branch"
        suggestion = """
        <p><strong>Failed to fetch the branch from the remote repository.</strong></p>
        <p>This could be due to:</p>
        <ul>
            <li>Remote repository being unavailable or slow</li>
            <li>Network connectivity issues</li>
            <li>Authentication problems with the remote</li>
        </ul>
        <p>Please try again shortly.</p>
        """
    else:
        status_code = 503
        title = "Preview Server Error"
        suggestion = """
        <p><strong>Please verify:</strong></p>
        <ul>
            <li>The branch exists and is checked out correctly</li>
            <li>A server.sh script exists in the repository root</li>
            <li>The server.sh script starts your server on the $PORT environment variable</li>
            <li>The server.sh script runs correctly when executed manually</li>
        </ul>
        """

    error_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 900px;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #d32f2f;
            margin-top: 0;
        }}
        .ref {{
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-weight: bold;
        }}
        .error-details {{
            background: #fff3cd;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 20px 0;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 13px;
            color: #333;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Failed to start preview server for branch: <span class="ref">{ref}</span></p>
        <div class="error-details">{error_msg}</div>
        {suggestion}
    </div>
</body>
</html>
"""
    return status_code, error_html


class PreviewServerApp(BasePreviewServerApp):
    """ASGI application for single-repo preview server."""

    def __init__(
        self,
        sub_server_manager: SubServerManager,
        basic_auth: Optional[str] = None,
        secret: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        base_domain: str = "localhost",
    ):
        """Initialize the preview server app.

        Args:
            sub_server_manager: The SubServerManager instance
            basic_auth: Optional basic auth credentials in "user:pass" format
            secret: Optional signing secret for hostname verification
            logger: Optional logger instance
            base_domain: Base domain for hostname parsing (default: localhost)
        """
        super().__init__(basic_auth=basic_auth, secret=secret, logger=logger)
        self.manager = sub_server_manager
        self.base_domain = base_domain

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming requests by proxying to sub-servers."""
        # Check authentication first
        auth_response = self._check_basic_auth(request)
        if auth_response is not None:
            return auth_response

        # Handle status endpoints first (no ref required)
        if request.url.path == "/-/preview-server.json":
            return await self._handle_status_json(request)
        if request.url.path == "/-/preview-server":
            return await self._handle_status_html(request)

        # Get the ref from hostname
        _, raw_ref = parse_hostname(
            request.headers.get("host", ""), base_domain=self.base_domain
        )

        if not raw_ref:
            return Response(
                f"Invalid hostname - use ref.{self.base_domain} format", status_code=400
            )

        # Check signature if secret is configured
        is_valid, ref = self._check_signature(raw_ref)
        if not is_valid:
            return self._forbidden_response()

        # Get or start the server for this ref
        try:
            port = await self.manager.get_port_for_ref(ref)
            self.manager.update_last_request_time(ref)
        except RuntimeError as e:
            self.logger.error(f"Failed to get server for ref '{ref}': {e}")
            status_code, error_html = _build_error_html(ref, str(e))
            return Response(error_html, status_code=status_code, media_type="text/html")

        # Proxy the request
        return await self._proxy_request(request, port)

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle WebSocket connections by proxying to sub-servers."""
        # Check authentication
        if not self._check_websocket_auth(websocket):
            await websocket.close(code=4001, reason="Unauthorized")
            return

        # Get the ref from hostname
        _, ref = parse_hostname(
            websocket.headers.get("host", ""), base_domain=self.base_domain
        )

        if not ref:
            await websocket.close(code=4002, reason="Invalid hostname")
            return

        # Get or start the server for this ref
        try:
            port = await self.manager.get_port_for_ref(ref)
            self.manager.update_last_request_time(ref)
        except RuntimeError as e:
            self.logger.error(f"Failed to get server for ref '{ref}': {e}")
            await websocket.close(code=4003, reason=str(e)[:120])
            return

        # Accept and proxy the WebSocket connection
        await websocket.accept()
        await self._proxy_websocket(
            websocket, port, websocket.url.path, websocket.url.query
        )

    async def _handle_status_json(self, request: Request) -> Response:
        """Handle the JSON status endpoint."""
        import time

        running_refs = self.manager.get_running_refs()
        servers_info = []
        current_time = time.time()

        for ref in running_refs:
            info = self.manager.servers.get(ref)
            if info:
                logs = self.manager._get_recent_logs(info, max_lines=100)
                seconds_since_last_request = current_time - info.last_request_time
                seconds_until_idle = max(
                    0, self.manager.idle_ttl_seconds - seconds_since_last_request
                )

                servers_info.append(
                    {
                        "ref": info.ref,
                        "port": info.port,
                        "pid": info.pid,
                        "uptime_seconds": current_time - info.start_time,
                        "restart_attempts": info.restart_attempts,
                        "command": info.command,
                        "recent_logs": logs,
                        "last_request_seconds_ago": seconds_since_last_request,
                        "idle_ttl_seconds": self.manager.idle_ttl_seconds,
                        "seconds_until_idle": seconds_until_idle,
                    }
                )

        status_data = {
            "status": "ok",
            "running_servers": len(servers_info),
            "idle_ttl_seconds": self.manager.idle_ttl_seconds,
            "sub_servers": servers_info,
        }

        return Response(
            json.dumps(status_data, indent=2),
            status_code=200,
            media_type="application/json",
        )


class MultiRepoPreviewServerApp(BasePreviewServerApp):
    """ASGI application for multi-repo preview server."""

    def __init__(
        self,
        repos: dict[str, str],
        basic_auth: Optional[str] = None,
        idle_ttl_seconds: float = 300.0,
        auto_pull_seconds: Optional[float] = None,
        secret: Optional[str] = None,
        admin_secret: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        base_domain: str = "localhost",
    ):
        """Initialize the multi-repo preview server app.

        Args:
            repos: Mapping of project name to repository path/URL
            basic_auth: Optional basic auth credentials in "user:pass" format
            idle_ttl_seconds: Idle timeout for sub-servers
            auto_pull_seconds: Auto-pull branches if not requested within this many seconds
            secret: Optional signing secret for hostname verification
            admin_secret: Optional secret for admin API access
            logger: Optional logger instance
            base_domain: Base domain for hostname parsing (default: localhost)
        """
        super().__init__(basic_auth=basic_auth, secret=secret, logger=logger)
        self.repos = repos
        self.idle_ttl_seconds = idle_ttl_seconds
        self.auto_pull_seconds = auto_pull_seconds
        self.admin_secret = admin_secret
        self.base_domain = base_domain

        # Will be populated with SubServerManager instances during initialization
        self.managers: dict[str, SubServerManager] = {}

        # Set of paused repo labels
        self.paused_repos: set[str] = set()

    def _check_admin_auth(self, request: Request) -> bool:
        """Check if admin API request is authenticated.

        Args:
            request: The incoming request

        Returns:
            True if authenticated, False otherwise
        """
        if not self.admin_secret:
            return False

        provided_secret = request.headers.get("x-api-secret", "")
        return secrets.compare_digest(provided_secret, self.admin_secret)

    async def _handle_admin_auth_check(self, request: Request) -> Response:
        """Handle auth-check endpoint."""
        is_valid = self._check_admin_auth(request)
        return Response(
            json.dumps({"ok": is_valid}),
            status_code=200,
            media_type="application/json",
        )

    async def _handle_admin_add_repo(self, request: Request) -> Response:
        """Handle repos/add endpoint."""
        if not self._check_admin_auth(request):
            return Response(
                json.dumps({"error": "Unauthorized"}),
                status_code=401,
                media_type="application/json",
            )

        try:
            body = await request.json()
        except Exception:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                media_type="application/json",
            )

        label = body.get("label")
        path = body.get("path")

        if not label or not path:
            return Response(
                json.dumps({"error": "Both 'label' and 'path' are required"}),
                status_code=400,
                media_type="application/json",
            )

        if label in self.managers:
            return Response(
                json.dumps({"error": f"Repo '{label}' already exists"}),
                status_code=409,
                media_type="application/json",
            )

        # Create and initialize the manager
        from pathlib import Path

        clone_path = Path.home() / ".cache" / "preview-server" / "repos" / label
        worktree_base = Path.home() / ".cache" / "preview-server" / "worktrees" / label

        manager = SubServerManager(
            repo_path=path,
            clone_path=str(clone_path),
            worktree_base_path=str(worktree_base),
            idle_ttl_seconds=self.idle_ttl_seconds,
            auto_pull_seconds=self.auto_pull_seconds,
            logger=self.logger,
        )
        await manager.initialize()
        self.managers[label] = manager
        self.repos[label] = path

        return Response(
            json.dumps({"ok": True, "label": label}),
            status_code=201,
            media_type="application/json",
        )

    async def _handle_admin_remove_repo(self, request: Request) -> Response:
        """Handle repos/remove endpoint."""
        if not self._check_admin_auth(request):
            return Response(
                json.dumps({"error": "Unauthorized"}),
                status_code=401,
                media_type="application/json",
            )

        try:
            body = await request.json()
        except Exception:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                media_type="application/json",
            )

        label = body.get("label")
        if not label:
            return Response(
                json.dumps({"error": "'label' is required"}),
                status_code=400,
                media_type="application/json",
            )

        if label not in self.managers:
            return Response(
                json.dumps({"error": f"Repo '{label}' not found"}),
                status_code=404,
                media_type="application/json",
            )

        # Shutdown the manager and remove
        manager = self.managers.pop(label)
        await manager.shutdown()
        self.repos.pop(label, None)
        self.paused_repos.discard(label)

        return Response(
            json.dumps({"ok": True}),
            status_code=200,
            media_type="application/json",
        )

    async def _handle_admin_pause_repo(self, request: Request) -> Response:
        """Handle repos/pause endpoint."""
        if not self._check_admin_auth(request):
            return Response(
                json.dumps({"error": "Unauthorized"}),
                status_code=401,
                media_type="application/json",
            )

        try:
            body = await request.json()
        except Exception:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                media_type="application/json",
            )

        label = body.get("label")
        if not label:
            return Response(
                json.dumps({"error": "'label' is required"}),
                status_code=400,
                media_type="application/json",
            )

        if label not in self.managers:
            return Response(
                json.dumps({"error": f"Repo '{label}' not found"}),
                status_code=404,
                media_type="application/json",
            )

        self.paused_repos.add(label)

        return Response(
            json.dumps({"ok": True}),
            status_code=200,
            media_type="application/json",
        )

    async def _handle_admin_resume_repo(self, request: Request) -> Response:
        """Handle repos/resume endpoint."""
        if not self._check_admin_auth(request):
            return Response(
                json.dumps({"error": "Unauthorized"}),
                status_code=401,
                media_type="application/json",
            )

        try:
            body = await request.json()
        except Exception:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status_code=400,
                media_type="application/json",
            )

        label = body.get("label")
        if not label:
            return Response(
                json.dumps({"error": "'label' is required"}),
                status_code=400,
                media_type="application/json",
            )

        if label not in self.managers:
            return Response(
                json.dumps({"error": f"Repo '{label}' not found"}),
                status_code=404,
                media_type="application/json",
            )

        self.paused_repos.discard(label)

        return Response(
            json.dumps({"ok": True}),
            status_code=200,
            media_type="application/json",
        )

    async def handle_request(self, request: Request) -> Response:
        """Handle incoming requests by routing to correct project's sub-server."""
        # Check authentication first
        auth_response = self._check_basic_auth(request)
        if auth_response is not None:
            return auth_response

        # Handle status endpoints first
        if request.url.path == "/-/preview-server.json":
            return await self._handle_status_json(request)
        if request.url.path == "/-/preview-server":
            return await self._handle_status_html(request)

        # Handle admin API endpoints (POST only)
        if request.method == "POST":
            if request.url.path == "/-/preview-server/auth-check":
                return await self._handle_admin_auth_check(request)
            if request.url.path == "/-/preview-server/repos/add":
                return await self._handle_admin_add_repo(request)
            if request.url.path == "/-/preview-server/repos/remove":
                return await self._handle_admin_remove_repo(request)
            if request.url.path == "/-/preview-server/repos/pause":
                return await self._handle_admin_pause_repo(request)
            if request.url.path == "/-/preview-server/repos/resume":
                return await self._handle_admin_resume_repo(request)

        # Extract the raw subdomain for signature checking
        hostname = request.headers.get("host", "")
        host = hostname.split(":")[0]  # Remove port
        domain_suffix = f".{self.base_domain}"
        if not host.endswith(domain_suffix):
            return Response(
                f"Invalid hostname - use project.{self.base_domain} or project--ref.{self.base_domain} format",
                status_code=400,
            )
        raw_subdomain = host[: -len(domain_suffix)]

        # Check signature if secret is configured
        is_valid, subdomain = self._check_signature(raw_subdomain)
        if not is_valid:
            return self._forbidden_response()

        # Parse project and ref from the (now unsigned) subdomain
        # Reconstruct hostname for parse_hostname
        project, ref = parse_hostname(
            f"{subdomain}.{self.base_domain}",
            multi_repo=True,
            base_domain=self.base_domain,
        )

        if not project:
            return Response(
                f"Invalid hostname - use project.{self.base_domain} or project--ref.{self.base_domain} format",
                status_code=400,
            )

        # Check if project exists
        if project not in self.managers:
            available = ", ".join(sorted(self.managers.keys()))
            return Response(
                f"Project '{project}' not found. Available projects: {available}",
                status_code=404,
            )

        # Check if project is paused
        if project in self.paused_repos:
            return Response(
                f"Traffic to '{project}' is paused",
                status_code=503,
            )

        manager = self.managers[project]

        # Use default branch if ref not specified
        if ref is None:
            ref = "main"

        # Get or start the server for this ref
        try:
            port = await manager.get_port_for_ref(ref)
            manager.update_last_request_time(ref)
        except RuntimeError as e:
            self.logger.error(f"Failed to get server for {project}/{ref}: {e}")
            status_code, error_html = _build_error_html(f"{project}/{ref}", str(e))
            return Response(error_html, status_code=status_code, media_type="text/html")

        # Proxy the request
        return await self._proxy_request(request, port)

    async def handle_websocket(self, websocket: WebSocket) -> None:
        """Handle WebSocket connections in multi-repo mode."""
        # Check authentication
        if not self._check_websocket_auth(websocket):
            await websocket.close(code=4001, reason="Unauthorized")
            return

        # Extract the raw subdomain for signature checking
        hostname = websocket.headers.get("host", "")
        host = hostname.split(":")[0]  # Remove port
        domain_suffix = f".{self.base_domain}"
        if not host.endswith(domain_suffix):
            await websocket.close(code=4002, reason="Invalid hostname")
            return
        raw_subdomain = host[: -len(domain_suffix)]

        # Check signature if secret is configured
        is_valid, subdomain = self._check_signature(raw_subdomain)
        if not is_valid:
            await websocket.close(code=4003, reason="Invalid signature")
            return

        # Parse project and ref from the (now unsigned) subdomain
        project, ref = parse_hostname(
            f"{subdomain}.{self.base_domain}",
            multi_repo=True,
            base_domain=self.base_domain,
        )

        if not project or project not in self.managers:
            await websocket.close(code=4004, reason="Project not found")
            return

        manager = self.managers[project]
        if ref is None:
            ref = "main"

        try:
            port = await manager.get_port_for_ref(ref)
            manager.update_last_request_time(ref)
        except RuntimeError as e:
            self.logger.error(f"Failed to get server for {project}/{ref}: {e}")
            await websocket.close(code=4003, reason=str(e)[:120])
            return

        # Accept and proxy the WebSocket connection
        await websocket.accept()
        await self._proxy_websocket(
            websocket, port, websocket.url.path, websocket.url.query
        )

    async def _handle_status_json(self, request: Request) -> Response:
        """Handle the JSON status endpoint for all repos."""
        import time

        all_servers = []
        for repo_name, manager in self.managers.items():
            for ref in manager.get_running_refs():
                info = manager.servers.get(ref)
                if info:
                    current_time = time.time()
                    uptime = current_time - info.start_time
                    last_request_ago = current_time - info.last_request_time
                    seconds_until_idle = max(
                        0, manager.idle_ttl_seconds - last_request_ago
                    )
                    logs = manager._get_recent_logs(info, max_lines=100)

                    all_servers.append(
                        {
                            "project": repo_name,
                            "ref": ref,
                            "port": info.port,
                            "pid": info.pid,
                            "uptime_seconds": round(uptime, 1),
                            "last_request_seconds_ago": round(last_request_ago, 1),
                            "seconds_until_idle": round(seconds_until_idle, 1),
                            "idle_ttl_seconds": manager.idle_ttl_seconds,
                            "restart_attempts": info.restart_attempts,
                            "command": info.command,
                            "recent_logs": logs,
                        }
                    )

        # Build repos list with paused status
        repos_list = [
            {
                "name": label,
                "path": self.repos.get(label, ""),
                "paused": label in self.paused_repos,
            }
            for label in self.managers.keys()
        ]

        return Response(
            content=json.dumps(
                {
                    "status": "ok",
                    "mode": "multi-repo",
                    "admin_api_enabled": self.admin_secret is not None,
                    "repos": repos_list,
                    "sub_servers": all_servers,
                }
            ),
            status_code=200,
            media_type="application/json",
        )


# ============================================================================
# Application factory functions and route handlers
# ============================================================================


async def handle_request(request: Request) -> Response:
    """Route handler for all requests."""
    app_instance = request.app.state.preview_app
    return await app_instance.handle_request(request)


async def handle_websocket(websocket: WebSocket) -> None:
    """Route handler for WebSocket connections."""
    app_instance = websocket.app.state.preview_app
    await app_instance.handle_websocket(websocket)


def create_app(
    sub_server_manager: SubServerManager,
    basic_auth: Optional[str] = None,
    secret: Optional[str] = None,
    base_domain: str = "localhost",
) -> Starlette:
    """Create the ASGI application for single-repo mode.

    Args:
        sub_server_manager: The SubServerManager instance
        basic_auth: Optional basic auth credentials in "user:pass" format
        secret: Optional signing secret for hostname verification
        base_domain: Base domain for hostname parsing (default: localhost)

    Returns:
        The Starlette ASGI application
    """
    app_instance = PreviewServerApp(
        sub_server_manager,
        basic_auth=basic_auth,
        secret=secret,
        base_domain=base_domain,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette):
        app.state.preview_app = app_instance
        await app_instance.manager.initialize()
        yield
        await app_instance.manager.shutdown()
        await app_instance.close()

    routes = [
        Route(
            "/{path:path}",
            handle_request,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        ),
        WebSocketRoute("/{path:path}", handle_websocket),
    ]

    return Starlette(routes=routes, lifespan=lifespan)


def create_multi_repo_app(
    repos: dict[str, str],
    basic_auth: Optional[str] = None,
    idle_ttl_seconds: float = 300.0,
    auto_pull_seconds: Optional[float] = None,
    secret: Optional[str] = None,
    admin_secret: Optional[str] = None,
    base_domain: str = "localhost",
) -> Starlette:
    """Create the ASGI application for multi-repo mode.

    Args:
        repos: Mapping of project name to repository path/URL
        basic_auth: Optional basic auth credentials in "user:pass" format
        idle_ttl_seconds: Idle timeout for sub-servers
        auto_pull_seconds: Auto-pull branches if not requested within this many seconds
        secret: Optional signing secret for hostname verification
        admin_secret: Optional secret for admin API access
        base_domain: Base domain for hostname parsing (default: localhost)

    Returns:
        The Starlette ASGI application
    """
    app_instance = MultiRepoPreviewServerApp(
        repos,
        basic_auth=basic_auth,
        idle_ttl_seconds=idle_ttl_seconds,
        auto_pull_seconds=auto_pull_seconds,
        secret=secret,
        admin_secret=admin_secret,
        base_domain=base_domain,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette):
        from pathlib import Path

        app.state.preview_app = app_instance

        # Initialize all managers
        for project_name, repo_path in app_instance.repos.items():
            clone_path = (
                Path.home() / ".cache" / "preview-server" / "repos" / project_name
            )
            worktree_base = (
                Path.home() / ".cache" / "preview-server" / "worktrees" / project_name
            )

            manager = SubServerManager(
                repo_path=repo_path,
                clone_path=str(clone_path),
                worktree_base_path=str(worktree_base),
                idle_ttl_seconds=app_instance.idle_ttl_seconds,
                auto_pull_seconds=app_instance.auto_pull_seconds,
                logger=app_instance.logger,
            )
            await manager.initialize()
            app_instance.managers[project_name] = manager

        yield

        # Shutdown all managers
        for manager in app_instance.managers.values():
            await manager.shutdown()
        await app_instance.close()

    routes = [
        Route(
            "/{path:path}",
            handle_request,
            methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        ),
        WebSocketRoute("/{path:path}", handle_websocket),
    ]

    return Starlette(routes=routes, lifespan=lifespan)
