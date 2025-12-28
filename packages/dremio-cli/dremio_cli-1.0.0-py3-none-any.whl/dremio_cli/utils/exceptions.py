"""Custom exceptions for Dremio CLI."""


class DremioCliError(Exception):
    """Base exception for Dremio CLI errors."""
    pass


class ProfileNotFoundError(DremioCliError):
    """Raised when a profile is not found."""
    pass


class AuthenticationError(DremioCliError):
    """Raised when authentication fails."""
    pass


class ApiError(DremioCliError):
    """Raised when an API request fails."""
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ValidationError(DremioCliError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(DremioCliError):
    """Raised when configuration is invalid."""
    pass
