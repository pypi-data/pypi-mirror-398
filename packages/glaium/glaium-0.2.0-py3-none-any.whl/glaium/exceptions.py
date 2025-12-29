"""Exception hierarchy for Glaium SDK."""

from __future__ import annotations

from typing import Any


class GlaiumError(Exception):
    """Base exception for all Glaium SDK errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# Authentication Errors
class AuthenticationError(GlaiumError):
    """Invalid API key or token."""

    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired. Re-registration required."""

    pass


# API Errors
class APIError(GlaiumError):
    """Base for API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ):
        super().__init__(message, {"status_code": status_code, "response": response_body})
        self.status_code = status_code
        self.response_body = response_body


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        **kwargs: Any,
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class ServerError(APIError):
    """Server error (5xx)."""

    pass


class ValidationError(APIError):
    """Invalid request data (400)."""

    pass


class NotFoundError(APIError):
    """Resource not found (404)."""

    pass


# Agent Errors
class AgentError(GlaiumError):
    """Base for agent framework errors."""

    pass


class NotRegisteredError(AgentError):
    """Agent has not been registered yet."""

    pass


class AlreadyRunningError(AgentError):
    """Agent is already running."""

    pass


class CycleError(AgentError):
    """Error occurred during cycle execution."""

    def __init__(self, message: str, cycle_number: int | None = None, **kwargs: Any):
        super().__init__(message, {"cycle_number": cycle_number, **kwargs})
        self.cycle_number = cycle_number


# Network Errors
class ConnectionError(GlaiumError):
    """Cannot reach the optimizer service."""

    pass


class TimeoutError(GlaiumError):
    """Request timed out after all retries."""

    pass
