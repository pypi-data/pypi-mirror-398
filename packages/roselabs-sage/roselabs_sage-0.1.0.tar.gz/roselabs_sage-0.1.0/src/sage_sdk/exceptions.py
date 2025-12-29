"""Sage SDK exceptions."""


class SageError(Exception):
    """Base exception for Sage SDK errors."""
    pass


class SageConfigError(SageError):
    """Raised when SDK configuration is invalid."""
    pass


class SageAPIError(SageError):
    """Raised when the Sage API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {super().__str__()}"
        return super().__str__()


class SageRateLimitError(SageAPIError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
