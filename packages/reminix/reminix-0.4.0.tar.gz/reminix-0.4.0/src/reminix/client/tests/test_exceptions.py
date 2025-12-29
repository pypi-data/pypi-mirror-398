"""Unit tests for Reminix SDK exceptions"""

from reminix.client import ReminixError, APIError, AuthenticationError, NetworkError


class TestExceptions:
    """Test exception classes"""

    def test_reminix_error(self):
        """Test base ReminixError"""
        error = ReminixError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.cause is None

    def test_reminix_error_with_cause(self):
        """Test ReminixError with cause"""
        cause = ValueError("Original error")
        error = ReminixError("Test error", cause)
        assert error.cause == cause

    def test_api_error(self):
        """Test APIError"""
        error = APIError("API failed", 500, "Internal Server Error", {"error": "details"})
        assert error.status == 500
        assert error.status_text == "Internal Server Error"
        assert error.response == {"error": "details"}

    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError()
        assert error.status == 401
        assert error.status_text == "Unauthorized"
        assert "API key" in error.message

    def test_authentication_error_custom(self):
        """Test AuthenticationError with custom message"""
        error = AuthenticationError("Custom auth error", 403)
        assert error.status == 403
        assert error.message == "Custom auth error"

    def test_network_error(self):
        """Test NetworkError"""
        cause = ConnectionError("Connection failed")
        error = NetworkError("Network error", cause)
        assert error.message == "Network error"
        assert error.cause == cause
