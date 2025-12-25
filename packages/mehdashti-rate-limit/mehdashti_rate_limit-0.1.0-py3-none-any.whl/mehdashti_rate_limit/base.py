"""
Base Rate Limiter

Abstract base class for rate limiter providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds until rate limit resets
        """
        self.retry_after = retry_after
        super().__init__(message)


@dataclass
class RateLimitInfo:
    """Rate limit information."""

    limit: int  # Maximum requests allowed
    remaining: int  # Remaining requests
    reset_at: int  # Unix timestamp when limit resets
    retry_after: Optional[int] = None  # Seconds until reset


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def check(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitInfo:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Unique identifier (e.g., user ID, IP address)
            limit: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            Rate limit information

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """
        Reset rate limit for a key.

        Args:
            key: Unique identifier
        """
        pass

    @abstractmethod
    async def get_info(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitInfo:
        """
        Get rate limit information without incrementing counter.

        Args:
            key: Unique identifier
            limit: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            Rate limit information
        """
        pass
