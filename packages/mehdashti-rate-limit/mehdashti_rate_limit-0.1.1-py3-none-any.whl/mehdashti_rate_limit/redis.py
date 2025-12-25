"""
Redis Rate Limiter

Redis-based rate limiter using sliding window algorithm with sorted sets.
"""

import time
from typing import Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from mehdashti_rate_limit.base import RateLimiter, RateLimitExceeded, RateLimitInfo


class RedisRateLimiter(RateLimiter):
    """
    Redis rate limiter using sliding window algorithm.

    Uses sorted sets for efficient sliding window implementation.
    Suitable for multi-server deployments.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "ratelimit:",
    ):
        """
        Initialize Redis rate limiter.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for namespacing
        """
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"

    async def check(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitInfo:
        """Check if request is allowed under rate limit."""
        redis_key = self._make_key(key)
        current_time = time.time()
        window_start = current_time - window

        try:
            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count current entries
            pipe.zcard(redis_key)

            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]

            # Check if limit is exceeded
            if current_count >= limit:
                # Get oldest timestamp for retry_after calculation
                oldest_entries = await self.redis.zrange(
                    redis_key,
                    0,
                    0,
                    withscores=True,
                )

                if oldest_entries:
                    oldest_timestamp = oldest_entries[0][1]
                    reset_at = int(oldest_timestamp + window)
                    retry_after = max(1, reset_at - int(current_time))
                else:
                    reset_at = int(current_time + window)
                    retry_after = window

                raise RateLimitExceeded(
                    message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    retry_after=retry_after,
                )

            # Add current request
            await self.redis.zadd(
                redis_key,
                {str(current_time): current_time},
            )

            # Set expiration
            await self.redis.expire(redis_key, window)

            # Get oldest timestamp for reset_at
            oldest_entries = await self.redis.zrange(
                redis_key,
                0,
                0,
                withscores=True,
            )

            if oldest_entries:
                oldest_timestamp = oldest_entries[0][1]
                reset_at = int(oldest_timestamp + window)
            else:
                reset_at = int(current_time + window)

            remaining = limit - (current_count + 1)

            return RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
            )

        except RedisError as e:
            print(f"Redis error in check: {e}")
            # Fail open - allow request if Redis is down
            return RateLimitInfo(
                limit=limit,
                remaining=limit - 1,
                reset_at=int(current_time + window),
            )

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        try:
            await self.redis.delete(self._make_key(key))
        except RedisError as e:
            print(f"Redis error in reset: {e}")

    async def get_info(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitInfo:
        """Get rate limit information without incrementing counter."""
        redis_key = self._make_key(key)
        current_time = time.time()
        window_start = current_time - window

        try:
            pipe = self.redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count current entries
            pipe.zcard(redis_key)

            # Get oldest entry
            pipe.zrange(redis_key, 0, 0, withscores=True)

            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]
            oldest_entries = results[2]

            # Calculate reset_at
            if oldest_entries:
                oldest_timestamp = oldest_entries[0][1]
                reset_at = int(oldest_timestamp + window)
            else:
                reset_at = int(current_time + window)

            # Calculate remaining and retry_after
            remaining = max(0, limit - current_count)
            retry_after = None

            if current_count >= limit:
                retry_after = max(1, reset_at - int(current_time))

            return RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        except RedisError as e:
            print(f"Redis error in get_info: {e}")
            return RateLimitInfo(
                limit=limit,
                remaining=limit,
                reset_at=int(current_time + window),
            )

    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return await self.redis.ping()
        except RedisError:
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        await self.redis.aclose()
