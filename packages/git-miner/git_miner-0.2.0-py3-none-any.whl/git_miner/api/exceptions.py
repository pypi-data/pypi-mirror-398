class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""


class RateLimitError(GitHubAPIError):
    """Raised when GitHub API rate limit is exceeded."""

    def __init__(self, limit: int, remaining: int, reset_at: int):
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        super().__init__(
            f"Rate limit exceeded. Limit: {limit}, Remaining: {remaining}, Resets at: {reset_at}"
        )


class AuthenticationError(GitHubAPIError):
    """Raised when GitHub API authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class ResourceNotFoundError(GitHubAPIError):
    """Raised when requested resource is not found on GitHub."""

    def __init__(self, resource: str):
        super().__init__(f"Resource not found: {resource}")


class InvalidResponseError(GitHubAPIError):
    """Raised when GitHub API response is invalid."""
