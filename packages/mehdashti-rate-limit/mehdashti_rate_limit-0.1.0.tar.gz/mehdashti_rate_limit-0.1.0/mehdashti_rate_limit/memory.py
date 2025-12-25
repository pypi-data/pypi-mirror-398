"""
Memory Rate Limiter

In-memory rate limiter using sliding window algorithm.
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Optional

from mehdashti_rate_limit.base import RateLimiter, RateLimitExceeded, RateLimitInfo


@dataclass
class WindowEntry:
    """Sliding window entry for rate limiting."""

    timestamps: deque = field(default_factory=deque)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class MemoryRateLimiter(RateLimiter):
    """
    In-memory rate limiter using sliding window algorithm.

    Thread-safe rate limiter suitable for single-server deployments.
    """

    def __init__(self, cleanup_interval: int = 300):
        """
        Initialize memory rate limiter.

        Args:
            cleanup_interval: Interval in seconds for cleaning up old entries
        """
        self._windows: Dict[str, WindowEntry] = {}
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._global_lock = asyncio.Lock()

    async def start_cleanup(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Background task to clean up old entries."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_old_windows()
            except asyncio.CancelledError:
                break

    async def _cleanup_old_windows(self) -> None:
        """Remove old window entries."""
        async with self._global_lock:
            keys_to_remove = []
            for key, entry in self._windows.items():
                if not entry.timestamps:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._windows[key]

    def _get_or_create_window(self, key: str) -> WindowEntry:
        """Get or create window entry for key."""
        if key not in self._windows:
            self._windows[key] = WindowEntry()
        return self._windows[key]

    def _clean_old_timestamps(
        self,
        timestamps: deque,
        window: int,
        current_time: float,
    ) -> None:
        """Remove timestamps outside the current window."""
        cutoff_time = current_time - window
        while timestamps and timestamps[0] < cutoff_time:
            timestamps.popleft()

    async def check(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitInfo:
        """Check if request is allowed under rate limit."""
        current_time = time.time()

        async with self._global_lock:
            entry = self._get_or_create_window(key)

        async with entry.lock:
            # Clean old timestamps
            self._clean_old_timestamps(entry.timestamps, window, current_time)

            # Check if limit is exceeded
            current_count = len(entry.timestamps)

            if current_count >= limit:
                # Calculate retry_after
                oldest_timestamp = entry.timestamps[0]
                reset_at = int(oldest_timestamp + window)
                retry_after = max(1, reset_at - int(current_time))

                raise RateLimitExceeded(
                    message=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    retry_after=retry_after,
                )

            # Add current timestamp
            entry.timestamps.append(current_time)

            # Calculate rate limit info
            reset_at = int(entry.timestamps[0] + window) if entry.timestamps else int(current_time + window)
            remaining = limit - len(entry.timestamps)

            return RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
            )

    async def reset(self, key: str) -> None:
        """Reset rate limit for a key."""
        async with self._global_lock:
            if key in self._windows:
                async with self._windows[key].lock:
                    self._windows[key].timestamps.clear()

    async def get_info(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> RateLimitInfo:
        """Get rate limit information without incrementing counter."""
        current_time = time.time()

        async with self._global_lock:
            entry = self._get_or_create_window(key)

        async with entry.lock:
            # Clean old timestamps
            self._clean_old_timestamps(entry.timestamps, window, current_time)

            # Calculate rate limit info
            current_count = len(entry.timestamps)
            reset_at = int(entry.timestamps[0] + window) if entry.timestamps else int(current_time + window)
            remaining = max(0, limit - current_count)
            retry_after = None

            if current_count >= limit:
                oldest_timestamp = entry.timestamps[0]
                retry_after = max(1, int(oldest_timestamp + window - current_time))

            return RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )

    def size(self) -> int:
        """Get number of tracked keys."""
        return len(self._windows)
