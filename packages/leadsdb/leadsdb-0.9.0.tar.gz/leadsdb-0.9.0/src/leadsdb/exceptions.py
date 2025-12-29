"""Exceptions for the LeadsDB SDK."""

from __future__ import annotations


class LeadsDBError(Exception):
    """Base exception for LeadsDB errors."""

    pass


class APIError(LeadsDBError):
    """Error response from the LeadsDB API."""

    def __init__(
        self,
        message: str,
        status_code: int,
        code: str = "",
        retry_after: int | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.code = code
        self.retry_after = retry_after
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.code:
            return f"leadsdb: {self.code}: {self.message} (status {self.status_code})"
        return f"leadsdb: {self.message} (status {self.status_code})"


class NotFoundError(APIError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message=message, status_code=404)


class UnauthorizedError(APIError):
    """Invalid or missing API key (401)."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenError(APIError):
    """Access denied (403)."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message=message, status_code=403)


class RateLimitedError(APIError):
    """Too many requests (429)."""

    def __init__(self, message: str = "Rate limited", retry_after: int | None = None) -> None:
        super().__init__(message=message, status_code=429, retry_after=retry_after)


class BadRequestError(APIError):
    """Invalid request (400)."""

    def __init__(self, message: str = "Bad request", code: str = "") -> None:
        super().__init__(message=message, status_code=400, code=code)


class ValidationError(LeadsDBError):
    """Client-side validation error."""

    pass


def raise_for_status(status_code: int, body: dict | None = None) -> None:
    """Raise an appropriate exception based on the HTTP status code."""
    if status_code < 400:
        return

    message = "Unknown error"
    code = ""
    retry_after = None

    if body:
        message = body.get("message") or body.get("error") or message
        code = body.get("code", "")

    if status_code == 400:
        raise BadRequestError(message=message, code=code)
    elif status_code == 401:
        raise UnauthorizedError(message=message)
    elif status_code == 403:
        raise ForbiddenError(message=message)
    elif status_code == 404:
        raise NotFoundError(message=message)
    elif status_code == 429:
        raise RateLimitedError(message=message, retry_after=retry_after)
    else:
        raise APIError(message=message, status_code=status_code, code=code)
