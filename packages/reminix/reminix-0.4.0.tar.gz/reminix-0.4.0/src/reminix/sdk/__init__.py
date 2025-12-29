"""
Reminix SDK Core
Re-exports from reminix.client for backward compatibility
"""

from reminix.client import (
    APIError,
    AuthenticationError,
    Client,
    ClientConfig,
    NetworkError,
    ReminixError,
    PaginatedResponse,
    collect_all,
    paginate_all,
)

__all__ = [
    "Client",
    "ClientConfig",
    "ReminixError",
    "APIError",
    "AuthenticationError",
    "NetworkError",
    "PaginatedResponse",
    "paginate_all",
    "collect_all",
]
