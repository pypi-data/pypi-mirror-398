"""Error types for the Gatsbie SDK."""

from typing import Optional


# Error codes returned by the Gatsbie API
ERR_AUTH_FAILED = "AUTH_FAILED"
ERR_INSUFFICIENT_CREDITS = "INSUFFICIENT_CREDITS"
ERR_INVALID_REQUEST = "INVALID_REQUEST"
ERR_UPSTREAM_ERROR = "UPSTREAM_ERROR"
ERR_SOLVE_FAILED = "SOLVE_FAILED"
ERR_INTERNAL_ERROR = "INTERNAL_ERROR"


class GatsbieError(Exception):
    """Base exception for Gatsbie SDK errors."""

    pass


class APIError(GatsbieError):
    """Exception raised when the Gatsbie API returns an error response."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[str] = None,
        timestamp: Optional[int] = None,
        http_status: Optional[int] = None,
    ):
        self.code = code
        self.message = message
        self.details = details
        self.timestamp = timestamp
        self.http_status = http_status
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.details:
            return f"gatsbie: {self.code}: {self.message} ({self.details})"
        return f"gatsbie: {self.code}: {self.message}"

    def is_auth_error(self) -> bool:
        """Check if this is an authentication error."""
        return self.code == ERR_AUTH_FAILED

    def is_insufficient_credits(self) -> bool:
        """Check if this error is due to insufficient credits."""
        return self.code == ERR_INSUFFICIENT_CREDITS

    def is_invalid_request(self) -> bool:
        """Check if this error is due to an invalid request."""
        return self.code == ERR_INVALID_REQUEST

    def is_upstream_error(self) -> bool:
        """Check if this error is from an upstream service."""
        return self.code == ERR_UPSTREAM_ERROR

    def is_solve_failed(self) -> bool:
        """Check if the captcha solving failed."""
        return self.code == ERR_SOLVE_FAILED

    def is_internal_error(self) -> bool:
        """Check if this is an internal server error."""
        return self.code == ERR_INTERNAL_ERROR


class RequestError(GatsbieError):
    """Exception raised when a request fails (network error, timeout, etc.)."""

    pass
