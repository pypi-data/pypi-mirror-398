"""Rate limiter for API requests."""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests_per_second: float = 5.0
    burst: int = 10
    initial_tokens: int = 10


class TokenBucket:
    """Token bucket rate limiter implementation.

    Uses a token bucket algorithm for smooth rate limiting.
    Tokens are added at a constant rate and consumed on each request.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize the token bucket.

        Args:
            config: Rate limit configuration.
        """
        self.config = config or RateLimitConfig()
        self.tokens = float(self.config.initial_tokens)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> float:
        """Acquire a token from the bucket.

        Returns:
            Time to wait until the request can proceed.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update

            # Add tokens based on elapsed time
            tokens_to_add = elapsed * self.config.requests_per_second
            self.tokens = min(
                self.tokens + tokens_to_add,
                float(self.config.burst)
            )
            self.last_update = now

            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0

            # Need to wait for more tokens
            wait_time = (1 - self.tokens) / self.config.requests_per_second
            return wait_time

    async def wait(self) -> None:
        """Wait until a token is available."""
        wait_time = await self.acquire()
        if wait_time > 0:
            await asyncio.sleep(wait_time)


class RateLimiter:
    """Rate limiter for API requests.

    Supports multiple rate limit configurations and per-endpoint limiting.
    """

    def __init__(
        self,
        default_config: Optional[RateLimitConfig] = None,
        per_host: bool = True,
    ):
        """Initialize the rate limiter.

        Args:
            default_config: Default rate limit configuration.
            per_host: Whether to track rate limits per host.
        """
        self.default_config = default_config or RateLimitConfig()
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        self._per_host = per_host

    def _get_bucket_key(self, host: str) -> str:
        """Get the bucket key for a host.

        Args:
            host: Target host.

        Returns:
            Bucket key.
        """
        return host if self._per_host else "_global_"

    async def get_bucket(self, host: str) -> TokenBucket:
        """Get or create a token bucket for a host.

        Args:
            host: Target host.

        Returns:
            Token bucket for the host.
        """
        key = self._get_bucket_key(host)
        async with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(self.default_config)
            return self._buckets[key]

    async def acquire(self, host: str) -> float:
        """Acquire a token for a request.

        Args:
            host: Target host.

        Returns:
            Time to wait until the request can proceed.
        """
        bucket = await self.get_bucket(host)
        return await bucket.acquire()

    async def wait(self, host: str) -> None:
        """Wait until a token is available for a request.

        Args:
            host: Target host.
        """
        wait_time = await self.acquire(host)
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    def get_wait_time(self, host: str) -> float:
        """Get the current wait time for a host (non-async).

        This is a snapshot and may be stale when actually called.

        Args:
            host: Target host.

        Returns:
            Estimated wait time in seconds, or 0 if available.
        """
        key = self._get_bucket_key(host)
        bucket = self._buckets.get(key)
        if bucket:
            if bucket.tokens >= 1:
                return 0.0
            return (1 - bucket.tokens) / self.default_config.requests_per_second
        return 0.0
