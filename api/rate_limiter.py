"""
Rate limiting for API requests.
"""

import asyncio
import time
from typing import Optional

class RateLimiter:
    """Token bucket rate limiter for async operations."""

    def __init__(
        self,
        max_concurrent: int = 5,
        requests_per_minute: int = 20
    ):
        """
        Initialize rate limiter.

        Args:
            max_concurrent: Maximum concurrent requests
            requests_per_minute: Maximum requests per minute
        """
        self.max_concurrent = max_concurrent
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0
        # Primitives are created lazily per event loop to survive multiple asyncio.run() calls
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._lock: Optional[asyncio.Lock] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _ensure_primitives(self) -> None:
        """Recreate semaphore/lock if the event loop has changed (e.g. between Streamlit reruns)."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if current_loop is not self._loop:
            self._semaphore = asyncio.Semaphore(self.max_concurrent)
            self._lock = asyncio.Lock()
            self._loop = current_loop

    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        self._ensure_primitives()

        # Acquire semaphore for concurrent limit
        await self._semaphore.acquire()

        # Enforce rate limit
        async with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time

            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)

            self.last_request_time = time.time()

    def release(self) -> None:
        """Release the semaphore."""
        if self._semaphore is not None:
            self._semaphore.release()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.release()
