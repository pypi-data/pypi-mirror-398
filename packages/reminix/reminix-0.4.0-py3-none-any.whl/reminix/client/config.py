"""Configuration management for Reminix SDK"""

from typing import Dict, Optional


class ClientConfig:
    """Configuration for the Reminix SDK client"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize client configuration.

        Args:
            api_key: Your Reminix API key
            base_url: Base URL for the API (defaults to https://api.reminix.com/v1)
            timeout: Request timeout in seconds (defaults to 30)
            headers: Additional headers to include in requests
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.reminix.com/v1"
        self.timeout = timeout or 30
        self.headers = headers or {}
