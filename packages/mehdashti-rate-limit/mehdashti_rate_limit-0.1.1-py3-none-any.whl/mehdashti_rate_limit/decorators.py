"""
Rate Limit Decorators

Decorators for rate limiting functions and API endpoints.
"""

import functools
from typing import Any, Callable, Optional, TypeVar

from fastapi import Request
from fastapi.responses import JSONResponse

from mehdashti_rate_limit.base import RateLimiter, RateLimitExceeded

F = TypeVar("F", bound=Callable[..., Any])


def rate_limit(
    limiter: RateLimiter,
    limit: int,
    window: int,
    key_func: Optional[Callable[[Request], str]] = None,
) -> Callable[[F], F]:
    """
    Decorator for rate limiting FastAPI endpoints.

    Args:
        limiter: Rate limiter instance
        limit: Maximum requests allowed
        window: Time window in seconds
        key_func: Function to extract rate limit key from request

    Returns:
        Decorated function

    Example:
        ```python
        from mehdashti_rate_limit import MemoryRateLimiter, rate_limit

        limiter = MemoryRateLimiter()

        @app.get("/api/users")
        @rate_limit(limiter, limit=10, window=60)
        async def get_users(request: Request):
            return {"users": []}
        ```
    """

    def _default_key_func(request: Request) -> str:
        """Default key function using client IP."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    key_func = key_func or _default_key_func

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Find request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if request is None:
                request = kwargs.get("request")

            if request is None:
                # If no request found, just call the function
                return await func(*args, **kwargs)

            # Get rate limit key
            key = key_func(request)

            try:
                # Check rate limit
                info = await limiter.check(key, limit, window)

                # Call original function
                response = await func(*args, **kwargs)

                # Add rate limit headers if response supports it
                if hasattr(response, "headers"):
                    response.headers["X-RateLimit-Limit"] = str(info.limit)
                    response.headers["X-RateLimit-Remaining"] = str(info.remaining)
                    response.headers["X-RateLimit-Reset"] = str(info.reset_at)

                return response

            except RateLimitExceeded as e:
                # Return 429 response
                headers = {
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(e.retry_after or window),
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

        return wrapper  # type: ignore

    return decorator


def user_rate_limit(
    limiter: RateLimiter,
    limit: int,
    window: int,
) -> Callable[[F], F]:
    """
    Decorator for rate limiting by user ID.

    Args:
        limiter: Rate limiter instance
        limit: Maximum requests allowed
        window: Time window in seconds

    Returns:
        Decorated function

    Example:
        ```python
        @app.get("/api/profile")
        @user_rate_limit(limiter, limit=20, window=60)
        async def get_profile(request: Request):
            return {"profile": {}}
        ```
    """

    def key_func(request: Request) -> str:
        """Extract user ID from request."""
        user = getattr(request.state, "user", None)
        if user:
            user_id = getattr(user, "id", None) or getattr(user, "sub", None)
            if user_id:
                return f"user:{user_id}"

        # Fall back to IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        if request.client:
            return f"ip:{request.client.host}"

        return "ip:unknown"

    return rate_limit(limiter, limit, window, key_func)


def endpoint_rate_limit(
    limiter: RateLimiter,
    limit: int,
    window: int,
) -> Callable[[F], F]:
    """
    Decorator for rate limiting by endpoint path.

    Args:
        limiter: Rate limiter instance
        limit: Maximum requests allowed
        window: Time window in seconds

    Returns:
        Decorated function

    Example:
        ```python
        @app.post("/api/search")
        @endpoint_rate_limit(limiter, limit=5, window=60)
        async def search(request: Request, query: str):
            return {"results": []}
        ```
    """

    def key_func(request: Request) -> str:
        """Extract endpoint path."""
        # Get client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"

        # Combine with endpoint path
        return f"endpoint:{request.url.path}:{client_ip}"

    return rate_limit(limiter, limit, window, key_func)
