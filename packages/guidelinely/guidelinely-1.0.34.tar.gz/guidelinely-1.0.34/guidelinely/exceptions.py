"""Custom exceptions for the Guidelinely API client.

Provides structured error handling for API communication failures,
allowing callers to catch specific exception types and access
error details like HTTP status codes.
"""

__all__ = [
    "GuidelinelyError",
    "GuidelinelyAPIError",
    "GuidelinelyTimeoutError",
    "GuidelinelyConnectionError",
]


class GuidelinelyError(Exception):
    """Base exception for all Guidelinely client errors.

    All exceptions raised by the guidelinely package inherit from this class,
    making it easy to catch all library-specific errors.

    Example:
        try:
            result = calculate_guidelines(...)
        except GuidelinelyError as e:
            print(f"Guidelinely error: {e}")
    """

    pass


class GuidelinelyAPIError(GuidelinelyError):
    """Raised when the API returns an error response.

    Provides access to both the error message and HTTP status code
    for detailed error handling.

    Attributes:
        message: Human-readable error description from the API.
        status_code: HTTP status code returned by the API.

    Example:
        try:
            result = calculate_guidelines(...)
        except GuidelinelyAPIError as e:
            if e.status_code == 404:
                print("Parameter not found")
            elif e.status_code == 401:
                print("Invalid API key")
            else:
                print(f"API error {e.status_code}: {e.message}")
    """

    def __init__(self, message: str, status_code: int) -> None:
        """Initialize the API error.

        Args:
            message: Error message from the API response.
            status_code: HTTP status code from the response.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        """Return formatted error string with status code."""
        return f"[{self.status_code}] {self.message}"

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"GuidelinelyAPIError(message={self.message!r}, status_code={self.status_code})"


class GuidelinelyTimeoutError(GuidelinelyError):
    """Raised when an API request times out.

    This exception wraps httpx.TimeoutException to provide a consistent
    exception hierarchy for the library.

    Example:
        try:
            result = calculate_guidelines(...)
        except GuidelinelyTimeoutError:
            print("Request timed out, please try again")
    """

    pass


class GuidelinelyConnectionError(GuidelinelyError):
    """Raised when unable to connect to the API.

    This exception wraps httpx.TransportError (which includes ConnectError,
    NetworkError, ReadError, etc.) to provide a consistent exception hierarchy.

    Example:
        try:
            result = calculate_guidelines(...)
        except GuidelinelyConnectionError:
            print("Could not connect to the API, check your network connection")
    """

    pass
