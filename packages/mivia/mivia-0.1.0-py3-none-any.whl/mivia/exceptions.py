"""MiViA API client exceptions."""


class MiviaError(Exception):
    """Base exception for MiViA API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(MiviaError):
    """Invalid or missing API key (401)."""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class NotFoundError(MiviaError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(MiviaError):
    """Request validation failed (400)."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)


class ServerError(MiviaError):
    """Server error (5xx)."""

    def __init__(self, message: str = "Server error"):
        super().__init__(message, status_code=500)


class JobTimeoutError(MiviaError):
    """Job polling timeout."""

    def __init__(self, message: str = "Job timeout"):
        super().__init__(message, status_code=None)
