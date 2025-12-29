"""Mattermost API exceptions."""

from typing import Any


class MattermostError(Exception):
    """Base exception for Mattermost API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.args[0]!r}, status_code={self.status_code})"


class MattermostAuthError(MattermostError):
    """Authentication failed (401)."""


class MattermostForbiddenError(MattermostError):
    """Permission denied (403)."""


class MattermostNotFoundError(MattermostError):
    """Resource not found (404)."""


class MattermostRateLimitError(MattermostError):
    """Rate limited (429)."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message, status_code, response_body)
        self.retry_after = retry_after


class MattermostServerError(MattermostError):
    """Server error (5xx)."""


class MattermostConnectionError(MattermostError):
    """Connection failed."""


class MattermostValidationError(ValueError):
    """Invalid parameter value."""
