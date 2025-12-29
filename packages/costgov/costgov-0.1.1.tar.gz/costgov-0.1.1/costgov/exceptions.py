"""Custom exceptions for CostGov SDK."""


class CostGovError(Exception):
    """Base exception for all CostGov SDK errors."""
    pass


class APIError(CostGovError):
    """Raised when API request fails."""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class ConfigError(CostGovError):
    """Raised when SDK configuration is invalid."""
    pass
