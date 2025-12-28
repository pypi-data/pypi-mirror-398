"""
Exception classes for Crexperium SDK.
"""


class CRMError(Exception):
    """Base exception for all CRM SDK errors."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CRMError):
    """Raised when authentication fails (401)."""

    def __init__(self, message="Authentication failed", response=None):
        super().__init__(message, status_code=401, response=response)


class ResourceNotFoundError(CRMError):
    """Raised when a requested resource is not found (404)."""

    def __init__(self, message="Resource not found", response=None):
        super().__init__(message, status_code=404, response=response)


class ValidationError(CRMError):
    """Raised when request validation fails (400)."""

    def __init__(self, message="Validation failed", errors=None, response=None):
        super().__init__(message, status_code=400, response=response)
        self.errors = errors or {}

    def __str__(self):
        if self.errors:
            error_details = ", ".join(
                f"{k}: {v}" for k, v in self.errors.items()
            )
            return f"[{self.status_code}] {self.message}: {error_details}"
        return super().__str__()


class RateLimitError(CRMError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message="Rate limit exceeded", retry_after=None, response=None):
        super().__init__(message, status_code=429, response=response)
        self.retry_after = retry_after


class ServerError(CRMError):
    """Raised when server returns 5xx error."""

    def __init__(self, message="Server error", status_code=500, response=None):
        super().__init__(message, status_code=status_code, response=response)


class NetworkError(CRMError):
    """Raised when network/connection errors occur."""

    def __init__(self, message="Network error occurred", original_error=None):
        super().__init__(message)
        self.original_error = original_error
