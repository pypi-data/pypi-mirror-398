"""Custom exceptions for the RevrseAI client."""


class RevrseAIError(Exception):
    """Base exception for all RevrseAI errors."""

    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class AuthenticationError(RevrseAIError):
    """Raised when authentication fails (invalid or missing API key)."""

    def __init__(self, message: str = "Authentication failed", status_code: int | None = 401, detail: str | None = None):
        super().__init__(message, status_code, detail or message)


class AuthorizationError(RevrseAIError):
    """Raised when the user doesn't have permission to access a resource."""

    def __init__(self, message: str = "Access denied", status_code: int | None = 403, detail: str | None = None):
        super().__init__(message, status_code, detail or message)


class NotFoundError(RevrseAIError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", status_code: int | None = 404, detail: str | None = None):
        super().__init__(message, status_code, detail or message)


class ValidationError(RevrseAIError):
    """Raised when request validation fails."""

    def __init__(self, message: str = "Validation error", status_code: int | None = 422, detail: str | None = None):
        super().__init__(message, status_code, detail or message)


class RateLimitError(RevrseAIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", status_code: int | None = 429, detail: str | None = None):
        super().__init__(message, status_code, detail or message)


class ServerError(RevrseAIError):
    """Raised when a server error occurs."""

    def __init__(self, message: str = "Server error", status_code: int | None = 500, detail: str | None = None):
        super().__init__(message, status_code, detail or message)


class APIError(RevrseAIError):
    """Raised for general API errors not covered by other exceptions."""

    def __init__(self, message: str = "API error", status_code: int | None = None, detail: str | None = None):
        super().__init__(message, status_code, detail or message)
