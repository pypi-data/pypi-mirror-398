class RequestError(Exception):
    """Generic request-level error when communicating with the API."""


class AuthenticationError(RequestError):
    """Raised when authentication fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ApiError(RequestError):
    """Raised when the API returns an error payload."""

    def __init__(self, status_code: int, message: str, payload: dict | None = None):
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.payload = payload or {}
