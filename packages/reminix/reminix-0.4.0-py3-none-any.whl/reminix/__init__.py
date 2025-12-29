"""
Reminix Python SDK - Umbrella package
Re-exports core functionality from reminix.client
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

__version__ = "0.4.0"

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
    "__version__",
]
