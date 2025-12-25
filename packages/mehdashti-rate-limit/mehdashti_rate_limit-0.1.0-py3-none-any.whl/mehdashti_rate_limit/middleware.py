"""
Rate Limit Middleware

FastAPI middleware for rate limiting requests.
"""

from typing import Awaitable, Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from mehdashti_rate_limit.base import RateLimiter, RateLimitExceeded


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Applies rate limiting to all requests based on configurable key strategy.
    """

    def __init__(
        self,
        app,
        limiter: RateLimiter,
        limit: int = 100,
        window: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[list[str]] = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            limiter: Rate limiter instance
            limit: Maximum requests allowed
            window: Time window in seconds
            key_func: Function to extract rate limit key from request
                     (defaults to client IP)
            exclude_paths: List of paths to exclude from rate limiting
        """
        super().__init__(app)
        self.limiter = limiter
        self.limit = limit
        self.window = window
        self.key_func = key_func or self._default_key_func
        self.exclude_paths = exclude_paths or []

    def _default_key_func(self, request: Request) -> str:
        """
        Default key function using client IP.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Try to get real IP from X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Try X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _is_excluded(self, path: str) -> bool:
        """
        Check if path is excluded from rate limiting.

        Args:
            path: Request path

        Returns:
            True if excluded, False otherwise
        """
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting for excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

        # Get rate limit key
        key = self.key_func(request)

        try:
            # Check rate limit
            info = await self.limiter.check(key, self.limit, self.window)

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(info.limit)
            response.headers["X-RateLimit-Remaining"] = str(info.remaining)
            response.headers["X-RateLimit-Reset"] = str(info.reset_at)

            return response

        except RateLimitExceeded as e:
            # Return 429 Too Many Requests
            headers = {
                "X-RateLimit-Limit": str(self.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(e.retry_after or self.window),
            }

            if e.retry_after:
                headers["Retry-After"] = str(e.retry_after)

            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": str(e),
                    "retry_after": e.retry_after,
                },
                headers=headers,
            )


def get_user_key(request: Request) -> str:
    """
    Extract user ID from request for rate limiting.

    Args:
        request: FastAPI request

    Returns:
        User ID from request state or IP as fallback
    """
    # Try to get user ID from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user:
        user_id = getattr(user, "id", None) or getattr(user, "sub", None)
        if user_id:
            return f"user:{user_id}"

    # Fall back to IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return f"ip:{real_ip}"

    if request.client:
        return f"ip:{request.client.host}"

    return "ip:unknown"


def get_endpoint_key(request: Request) -> str:
    """
    Extract endpoint path for rate limiting.

    Args:
        request: FastAPI request

    Returns:
        Endpoint path with client IP
    """
    # Get client IP
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    elif request.headers.get("X-Real-IP"):
        client_ip = request.headers.get("X-Real-IP")
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"

    # Combine with endpoint path
    return f"endpoint:{request.url.path}:{client_ip}"
