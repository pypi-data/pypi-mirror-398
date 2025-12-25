"""Exception classes for Power Switch Pro library."""


class PowerSwitchError(Exception):
    """Base exception for all Power Switch Pro errors."""

    pass


class AuthenticationError(PowerSwitchError):
    """Raised when authentication fails."""

    pass


class ConnectionError(PowerSwitchError):
    """Raised when connection to device fails."""

    pass


class APIError(PowerSwitchError):
    """Raised when API returns an error response."""

    def __init__(self, message, status_code=None, response=None):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response: Full response object
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ValidationError(PowerSwitchError):
    """Raised when input validation fails."""

    pass


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found."""

    pass


class ConflictError(APIError):
    """Raised when there is a conflict (409 status)."""

    pass
