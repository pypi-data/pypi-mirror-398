"""
Reminix HTTP Adapter
"""

# Re-export runtime utilities for convenience
from reminix.runtime import (
    load_handler,
    is_file,
    discover_registry,
    LoadedHandler,
    Registry,
)

from .converter import (
    convert_http_to_request,
    convert_response_to_http,
    convert_error_to_http,
    HTTPRequest,
    HTTPResponse,
)
from .server import start_server, ServerOptions

__all__ = [
    # Runtime utilities (re-exported)
    "load_handler",
    "is_file",
    "discover_registry",
    "LoadedHandler",
    "Registry",
    # HTTP-specific
    "convert_http_to_request",
    "convert_response_to_http",
    "convert_error_to_http",
    "HTTPRequest",
    "HTTPResponse",
    "start_server",
    "ServerOptions",
]
