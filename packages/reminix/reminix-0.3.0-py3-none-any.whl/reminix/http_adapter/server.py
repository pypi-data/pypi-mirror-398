"""
HTTP server for Reminix handlers
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Callable, Any, Optional
from reminix.runtime.types import Context, MemoryStore, KnowledgeBase
from reminix.runtime import load_handler, is_file, discover_registry, execute_handler
from .converter import (
    convert_http_to_request,
    convert_response_to_http,
    convert_error_to_http,
    HTTPRequest,
    HTTPResponse,
)


class ServerOptions:
    """Server configuration options"""

    def __init__(
        self,
        port: int = 3000,
        host: str = "localhost",
        context: Optional[Callable] = None,
    ):
        self.port = port
        self.host = host
        self.context = context


class HTTPRequestAdapter(HTTPRequest):
    """Adapter to make BaseHTTPRequestHandler compatible with HTTPRequest protocol"""

    def __init__(self, handler: BaseHTTPRequestHandler):
        self.handler = handler
        self._body: Optional[str] = None

    @property
    def method(self) -> str:  # type: ignore[override]
        return self.handler.command

    @property
    def path(self) -> str:  # type: ignore[override]
        return self.handler.path

    @property
    def headers(self) -> Dict[str, str]:  # type: ignore[override]
        return dict(self.handler.headers)

    def read_body(self) -> str:
        """Read request body"""
        if self._body is None:
            content_length = int(self.handler.headers.get("Content-Length", 0))
            if content_length > 0:
                self._body = self.handler.rfile.read(content_length).decode("utf-8")
            else:
                self._body = ""
        return self._body


class HTTPResponseAdapter(HTTPResponse):
    """Adapter to make BaseHTTPRequestHandler compatible with HTTPResponse protocol"""

    def __init__(self, handler: BaseHTTPRequestHandler):
        self.handler = handler

    def set_status(self, status: int) -> None:
        """Set HTTP status code"""
        self.handler.send_response(status)

    def set_header(self, key: str, value: str) -> None:
        """Set HTTP header"""
        self.handler.send_header(key, value)

    def write(self, data: bytes) -> None:
        """Write response body"""
        self.handler.end_headers()
        self.handler.wfile.write(data)


class ReminixHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Reminix"""

    def __init__(self, agents, tools, prompts, context_provider, *args, **kwargs):
        self.agents = agents
        self.tools = tools
        self.prompts = prompts
        self.context_provider = context_provider
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        self.handle_request()

    def do_POST(self):
        """Handle POST requests"""
        self.handle_request()

    def do_PUT(self):
        """Handle PUT requests"""
        self.handle_request()

    def do_DELETE(self):
        """Handle DELETE requests"""
        self.handle_request()

    def handle_request(self):
        """Handle all HTTP requests"""
        try:
            # Parse URL
            parsed_url = urlparse(self.path)
            path_parts = [p for p in parsed_url.path.split("/") if p]

            # Create adapters
            http_req_adapter = HTTPRequestAdapter(self)
            http_res_adapter = HTTPResponseAdapter(self)

            # Route: /agents/:agentId/invoke
            if len(path_parts) >= 3 and path_parts[0] == "agents" and path_parts[2] == "invoke":
                agent_id = path_parts[1]
                agent = self.agents.get(agent_id)

                if not agent:
                    http_res_adapter.set_status(404)
                    http_res_adapter.set_header("Content-Type", "application/json")
                    http_res_adapter.write(
                        json.dumps({"error": f"Agent not found: {agent_id}"}).encode("utf-8")
                    )
                    return

                # Get context
                context = (
                    self.context_provider(self)
                    if self.context_provider
                    else _create_default_context(self)
                )

                # Convert HTTP request to handler request
                handler_req = convert_http_to_request(http_req_adapter)

                # Execute agent handler
                handler_res = execute_handler(agent, context, handler_req)

                # Convert handler response to HTTP response
                convert_response_to_http(handler_res, http_res_adapter)
                return

            # Route: /tools/:toolId/invoke
            if len(path_parts) >= 3 and path_parts[0] == "tools" and path_parts[2] == "invoke":
                tool_id = path_parts[1]
                tool = self.tools.get(tool_id)

                if not tool:
                    http_res_adapter.set_status(404)
                    http_res_adapter.set_header("Content-Type", "application/json")
                    http_res_adapter.write(
                        json.dumps({"error": f"Tool not found: {tool_id}"}).encode("utf-8")
                    )
                    return

                # Get context
                context = (
                    self.context_provider(self)
                    if self.context_provider
                    else _create_default_context(self)
                )

                # Convert HTTP request to handler request
                handler_req = convert_http_to_request(http_req_adapter)

                # Execute tool handler
                handler_res = execute_handler(tool, context, handler_req)

                # Convert handler response to HTTP response
                convert_response_to_http(handler_res, http_res_adapter)
                return

            # Route: /health (health check)
            if path_parts == ["health"] or self.path == "/":
                http_res_adapter.set_status(200)
                http_res_adapter.set_header("Content-Type", "application/json")
                http_res_adapter.write(
                    json.dumps(
                        {
                            "status": "ok",
                            "agents": list(self.agents.keys()),
                            "tools": list(self.tools.keys()),
                            "prompts": list(self.prompts.keys()),
                        }
                    ).encode("utf-8")
                )
                return

            # 404 for unknown routes
            http_res_adapter.set_status(404)
            http_res_adapter.set_header("Content-Type", "application/json")
            http_res_adapter.write(json.dumps({"error": "Not found"}).encode("utf-8"))

        except Exception as e:
            http_res_adapter = HTTPResponseAdapter(self)
            convert_error_to_http(e, http_res_adapter)

    def log_message(self, format, *args):
        """Override to customize logging"""
        pass


def start_server(handler_path: str, options: Optional[ServerOptions] = None) -> None:
    """
    Start HTTP server for handler.

    Args:
        handler_path: Path to handler file or directory
        options: Server configuration options
    """
    if options is None:
        options = ServerOptions()

    # Load handler or discover registry
    agents: Dict[str, Callable] = {}
    tools: Dict[str, Callable] = {}
    prompts: Dict[str, Any] = {}

    if is_file(handler_path):
        # Single file handler
        loaded = load_handler(handler_path)
        agents = loaded.agents or {}
        tools = loaded.tools or {}
        prompts = loaded.prompts or {}
    else:
        # Directory - auto-discover
        registry = discover_registry(handler_path)
        agents = registry.agents
        tools = registry.tools
        prompts = registry.prompts

    # Create HTTP server
    def handler_factory(*args, **kwargs):
        return ReminixHTTPHandler(agents, tools, prompts, options.context, *args, **kwargs)

    server = HTTPServer((options.host, options.port), handler_factory)

    print(f"Reminix HTTP adapter listening on http://{options.host}:{options.port}")
    print(f"Agents: {', '.join(agents.keys()) or 'none'}")
    print(f"Tools: {', '.join(tools.keys()) or 'none'}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


def _create_default_context(http_request: BaseHTTPRequestHandler) -> Context:
    """
    Create default context (for development).
    In production, this would come from the orchestrator.

    Args:
        http_request: HTTP request handler

    Returns:
        Default context
    """
    # Extract chatId from headers or query params
    chat_id = (
        http_request.headers.get("X-Chat-Id")
        or parse_qs(urlparse(http_request.path).query).get("chatId", [None])[0]
        or "default-chat"
    )

    # Return a minimal context (orchestrator will provide full context in production)

    return Context(
        chat_id=chat_id,
        memory=_create_mock_memory_store(),
        knowledge_base=_create_mock_knowledge_base(),
    )


def _create_mock_memory_store() -> MemoryStore:
    """Mock memory store for development"""
    store: Dict[str, Any] = {}

    class MockMemoryStore:
        async def get(self, key: str):
            return store.get(key)

        async def set(self, key: str, value: Any):
            store[key] = value

        async def delete(self, key: str):
            store.pop(key, None)

        async def clear(self):
            store.clear()

    return MockMemoryStore()  # type: ignore


def _create_mock_knowledge_base() -> KnowledgeBase:
    """Mock knowledge base for development"""

    class MockKnowledgeBase:
        async def search(self, query: str, options=None):
            return []

        async def add(self, content: str, metadata=None):
            pass

        async def delete(self, id: str):
            pass

    return MockKnowledgeBase()  # type: ignore
