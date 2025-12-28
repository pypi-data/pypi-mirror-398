"""
Rate Limiting Middleware for FastMCP.

Implements token bucket rate limiting per client and/or tool.
"""

import time
from collections import defaultdict
from typing import Callable, Optional

try:
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    # Create stub classes for when FastMCP isn't available
    class Middleware:
        pass
    class MiddlewareContext:
        pass


class RateLimitMiddleware(Middleware):
    """
    Token bucket rate limiting middleware.

    Applies rate limits per client_id or globally per tool.

    Usage:
        mcp.add_middleware(RateLimitMiddleware(
            calls_per_minute=60,
            burst_size=10,
            per_client=True,
        ))
    """

    def __init__(
        self,
        calls_per_minute: int = 60,
        burst_size: int = 10,
        per_client: bool = True,
        excluded_tools: Optional[set] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Sustained rate limit
            burst_size: Allow short bursts up to this size
            per_client: If True, rate limit per client_id; if False, global
            excluded_tools: Set of tool names exempt from rate limiting
        """
        self.rate = calls_per_minute / 60.0  # Calls per second
        self.burst_size = burst_size
        self.per_client = per_client
        self.excluded_tools = excluded_tools or {"server_status"}
        self._buckets: dict[str, dict[str, float]] = defaultdict(
            lambda: {"tokens": burst_size, "last_update": time.time()}
        )

    def _get_bucket_key(self, context: MiddlewareContext, tool_name: str) -> str:
        """Generate bucket key based on settings."""
        if self.per_client:
            client_id = getattr(context.fastmcp_context, "client_id", "unknown") if hasattr(context, "fastmcp_context") else "unknown"
            return f"{client_id}:{tool_name}"
        return tool_name

    def _check_rate_limit(self, key: str) -> tuple[bool, float]:
        """
        Check if request is allowed under rate limits.

        Returns:
            Tuple of (allowed: bool, wait_time: float)
        """
        bucket = self._buckets[key]
        now = time.time()

        # Refill tokens based on time elapsed
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            self.burst_size,
            bucket["tokens"] + elapsed * self.rate
        )
        bucket["last_update"] = now

        # Check if we have tokens
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True, 0.0

        wait_time = (1 - bucket["tokens"]) / self.rate
        return False, wait_time

    async def on_call_tool(self, context: MiddlewareContext, call_next: Callable):
        """Apply rate limiting to tool calls."""
        if not FASTMCP_AVAILABLE:
            return await call_next(context)

        # Get tool name from context
        tool_name = getattr(context, "tool_name", None) or "unknown"

        # Skip excluded tools
        if tool_name in self.excluded_tools:
            return await call_next(context)

        # Check rate limit
        key = self._get_bucket_key(context, tool_name)
        allowed, wait_time = self._check_rate_limit(key)

        if not allowed:
            return {
                "error": "rate_limited",
                "message": f"Rate limit exceeded for {tool_name}",
                "retry_after_seconds": round(wait_time, 1),
            }

        return await call_next(context)

