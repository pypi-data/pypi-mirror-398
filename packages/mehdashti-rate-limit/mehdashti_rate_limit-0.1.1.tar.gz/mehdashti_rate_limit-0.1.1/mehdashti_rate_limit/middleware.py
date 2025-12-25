"""
Rate Limit Middleware

FastAPI middleware for rate limiting requests.
"""

import ipaddress
from typing import Awaitable, Callable, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from mehdashti_rate_limit.base import RateLimiter, RateLimitExceeded


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Applies rate limiting to all requests based on configurable key strategy.

    Security Note:
        The X-Forwarded-For header can be easily spoofed by attackers. Only trust
        this header if you have a trusted reverse proxy (like nginx, Cloudflare, etc.)
        in front of your application. Use the `trusted_proxies` parameter to specify
        which proxy IPs are trusted.
    """

    def __init__(
        self,
        app,
        limiter: RateLimiter,
        limit: int = 100,
        window: int = 60,
        key_func: Optional[Callable[[Request], str]] = None,
        exclude_paths: Optional[list[str]] = None,
        trusted_proxies: Optional[list[str]] = None,
        trust_x_forwarded_for: bool = False,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            limiter: Rate limiter instance
            limit: Maximum requests allowed
            window: Time window in seconds
            key_func: Function to extract rate limit key from request
                     (defaults to client IP with security checks)
            exclude_paths: List of paths to exclude from rate limiting
            trusted_proxies: List of trusted proxy IP addresses or CIDR ranges
                           (e.g., ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"])
                           Only requests from these IPs will have X-Forwarded-For trusted
            trust_x_forwarded_for: If True, trust X-Forwarded-For without proxy validation
                                  ⚠️ SECURITY WARNING: Only enable this if you understand
                                  the risks and have other protections in place

        Example:
            ```python
            # Secure: Only trust X-Forwarded-For from known proxies
            middleware = RateLimitMiddleware(
                app,
                limiter,
                trusted_proxies=["10.0.0.1", "10.0.0.2"]
            )

            # Insecure: Trust all X-Forwarded-For headers (vulnerable to spoofing)
            middleware = RateLimitMiddleware(
                app,
                limiter,
                trust_x_forwarded_for=True  # ⚠️ Not recommended
            )
            ```
        """
        super().__init__(app)
        self.limiter = limiter
        self.limit = limit
        self.window = window
        self.key_func = key_func or self._default_key_func
        self.exclude_paths = exclude_paths or []
        self.trust_x_forwarded_for = trust_x_forwarded_for

        # Parse trusted proxy networks
        self.trusted_proxy_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        if trusted_proxies:
            for proxy in trusted_proxies:
                try:
                    # Parse as network (supports CIDR notation)
                    self.trusted_proxy_networks.append(ipaddress.ip_network(proxy, strict=False))
                except ValueError:
                    # If not a valid network, treat as single IP
                    try:
                        ip = ipaddress.ip_address(proxy)
                        self.trusted_proxy_networks.append(
                            ipaddress.ip_network(f"{ip}/{'128' if ip.version == 6 else '32'}", strict=False)
                        )
                    except ValueError:
                        pass  # Invalid IP, skip

    def _is_trusted_proxy(self, ip: str) -> bool:
        """
        Check if an IP is from a trusted proxy.

        Args:
            ip: IP address to check

        Returns:
            True if the IP is in the trusted proxy list
        """
        if not self.trusted_proxy_networks:
            return False

        try:
            ip_addr = ipaddress.ip_address(ip)
            return any(ip_addr in network for network in self.trusted_proxy_networks)
        except ValueError:
            return False

    def _default_key_func(self, request: Request) -> str:
        """
        Default key function using client IP with security checks.

        This function safely extracts the client IP address:
        1. If the request comes from a trusted proxy, use X-Forwarded-For
        2. Otherwise, use the direct client IP (request.client.host)

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Get the direct client IP (the IP that connected to our server)
        direct_client_ip = request.client.host if request.client else "unknown"

        # Only trust X-Forwarded-For if explicitly enabled OR if from trusted proxy
        if self.trust_x_forwarded_for or self._is_trusted_proxy(direct_client_ip):
            # Try to get real IP from X-Forwarded-For header
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
                # The leftmost IP is the original client
                return forwarded_for.split(",")[0].strip()

            # Try X-Real-IP header (used by some proxies)
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                return real_ip.strip()

        # Use direct client IP (most secure, cannot be spoofed)
        return direct_client_ip

    def _is_excluded(self, path: str) -> bool:
        """
        Check if path is excluded from rate limiting.

        Args:
            path: Request path

        Returns:
            True if path should be excluded
        """
        return any(path.startswith(excluded) for excluded in self.exclude_paths)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response (either rate limit error or next handler response)
        """
        # Skip rate limiting for excluded paths
        if self._is_excluded(request.url.path):
            return await call_next(request)

        # Get rate limit key (usually client IP)
        key = self.key_func(request)

        # Check rate limit
        try:
            self.limiter.check_rate_limit(key, self.limit, self.window)
        except RateLimitExceeded as e:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": str(e),
                    "retry_after": self.window,
                },
                headers={
                    "Retry-After": str(self.window),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self.window),
                },
            )

        # Continue to next handler
        response = await call_next(request)

        # Add rate limit headers
        try:
            remaining = self.limiter.get_remaining(key, self.limit, self.window)
            response.headers["X-RateLimit-Limit"] = str(self.limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        except Exception:
            # Ignore header errors
            pass

        return response
