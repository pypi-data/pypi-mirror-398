"""
Convert between HTTP and Handler formats
"""

import json
from typing import Dict, Any, List, Protocol
from reminix.runtime.types import Request, Response, Message


class HTTPRequest(Protocol):
    """Protocol for HTTP request objects"""

    method: str
    path: str
    headers: Dict[str, str]

    def read_body(self) -> str:
        """Read request body"""
        ...


class HTTPResponse(Protocol):
    """Protocol for HTTP response objects"""

    def set_status(self, status: int) -> None:
        """Set HTTP status code"""
        ...

    def set_header(self, key: str, value: str) -> None:
        """Set HTTP header"""
        ...

    def write(self, data: bytes) -> None:
        """Write response body"""
        ...


def convert_http_to_request(http_request: HTTPRequest) -> Request:
    """
    Convert HTTP request to Handler Request.
    Extracts messages from HTTP request body.

    Args:
        http_request: HTTP request object with method, path, headers, and read_body() method

    Returns:
        Handler Request with messages and metadata
    """
    try:
        # Read request body
        body = http_request.read_body()

        # Parse JSON body
        parsed_body: Dict[str, Any] = {}
        if body:
            try:
                parsed_body = json.loads(body)
            except json.JSONDecodeError:
                # If not JSON, treat as text
                parsed_body = {"content": body}

        # Extract messages from body
        # Expected format: { messages: List[Message] } or { message: Message } or just List[Message]
        messages: List[Message] = []

        if isinstance(parsed_body, list):
            # Body is array of messages
            messages = [Message(**msg) if isinstance(msg, dict) else msg for msg in parsed_body]
        elif isinstance(parsed_body, dict):
            if "messages" in parsed_body and isinstance(parsed_body["messages"], list):
                # Body has messages array
                messages = [
                    Message(**msg) if isinstance(msg, dict) else msg
                    for msg in parsed_body["messages"]
                ]
            elif "message" in parsed_body:
                # Body has single message
                msg = parsed_body["message"]
                messages = [Message(**msg) if isinstance(msg, dict) else msg]
            elif "content" in parsed_body or "role" in parsed_body:
                # Body is a single message object
                messages = [Message(**parsed_body)]

        # Extract metadata from query params and headers
        metadata: Dict[str, Any] = {
            "method": http_request.method,
            "url": http_request.path,
            "headers": http_request.headers,
        }

        # Add query params to metadata
        if "?" in http_request.path:
            path, query_string = http_request.path.split("?", 1)
            query_params = {}
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    query_params[key] = value
            if query_params:
                metadata["query"] = query_params

        # Merge any additional metadata from body
        if isinstance(parsed_body, dict) and "metadata" in parsed_body:
            metadata.update(parsed_body["metadata"])

        return Request(messages=messages, metadata=metadata)
    except Exception as e:
        raise ValueError(f"Failed to convert HTTP request: {str(e)}") from e


def convert_response_to_http(handler_res: Response, http_response: HTTPResponse) -> None:
    """
    Convert Handler Response to HTTP response.

    Args:
        handler_res: Handler response
        http_response: HTTP response object with set_status, set_header, and write methods
    """
    try:
        # Set status code (default 200)
        status_code = handler_res.metadata.get("statusCode", 200) if handler_res.metadata else 200
        http_response.set_status(status_code)

        # Set headers
        headers = handler_res.metadata.get("headers", {}) if handler_res.metadata else {}
        headers.setdefault("Content-Type", "application/json")

        for key, value in headers.items():
            if isinstance(value, str):
                http_response.set_header(key, value)

        # Prepare response body
        response_body: Dict[str, Any] = {
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    **(msg.metadata or {}),
                }
                for msg in handler_res.messages
            ],
        }

        if handler_res.metadata:
            response_body["metadata"] = handler_res.metadata

        if handler_res.tool_calls:
            response_body["toolCalls"] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                for tc in handler_res.tool_calls
            ]

        if handler_res.state_updates:
            response_body["stateUpdates"] = handler_res.state_updates

        # Send response
        response_json = json.dumps(response_body)
        http_response.write(response_json.encode("utf-8"))
    except Exception as e:
        http_response.set_status(500)
        http_response.set_header("Content-Type", "application/json")
        error_body = {"error": str(e)}
        http_response.write(json.dumps(error_body).encode("utf-8"))


def convert_error_to_http(error: Exception, http_response: HTTPResponse) -> None:
    """
    Convert error to HTTP error response.

    Args:
        error: Exception to convert
        http_response: HTTP response object with set_status, set_header, and write methods
    """
    http_response.set_status(500)
    http_response.set_header("Content-Type", "application/json")

    error_body = {"error": str(error)}
    # Add stack trace in development
    import os

    if os.getenv("NODE_ENV") == "development":
        import traceback

        error_body["stack"] = traceback.format_exc()

    http_response.write(json.dumps(error_body).encode("utf-8"))
