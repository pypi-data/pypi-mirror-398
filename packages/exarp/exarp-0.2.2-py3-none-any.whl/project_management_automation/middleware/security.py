"""
Combined Security Middleware for FastMCP.

Combines rate limiting, path validation, and access control into a single middleware.
"""

from pathlib import Path
from typing import Callable, Optional

try:
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    class Middleware:
        pass
    class MiddlewareContext:
        pass

from .access_control import AccessControlMiddleware, AccessLevel
from .path_validation import PathValidationMiddleware
from .rate_limit import RateLimitMiddleware


async def _dummy_continue(ctx):
    """Async dummy call_next that signals to continue processing."""
    return {"_continue": True}


class SecurityMiddleware(Middleware):
    """
    Combined security middleware for FastMCP.

    Applies rate limiting, path validation, and access control
    in a single middleware for convenience.

    Usage:
        mcp.add_middleware(SecurityMiddleware(
            allowed_roots=[project_root],
            calls_per_minute=60,
            read_only=False,
        ))
    """

    def __init__(
        self,
        # Rate limiting
        calls_per_minute: int = 60,
        burst_size: int = 10,
        per_client: bool = True,
        rate_limit_excluded: Optional[set[str]] = None,
        # Path validation
        allowed_roots: Optional[list[Path]] = None,
        allow_symlinks: bool = False,
        blocked_patterns: Optional[list[str]] = None,
        # Access control
        default_access_level: str = AccessLevel.WRITE,
        denied_tools: Optional[set[str]] = None,
        read_only: bool = False,
        tool_levels: Optional[dict[str, str]] = None,
    ):
        """
        Initialize combined security middleware.

        Args:
            calls_per_minute: Rate limit (calls per minute)
            burst_size: Burst allowance
            per_client: Rate limit per client vs global
            rate_limit_excluded: Tools exempt from rate limiting
            allowed_roots: Allowed path roots
            allow_symlinks: Allow symlinks in paths
            blocked_patterns: Blocked path patterns
            default_access_level: Default tool access level
            denied_tools: Explicitly denied tools
            read_only: Read-only mode
            tool_levels: Custom tool access levels
        """
        # Initialize sub-middleware
        self._rate_limiter = RateLimitMiddleware(
            calls_per_minute=calls_per_minute,
            burst_size=burst_size,
            per_client=per_client,
            excluded_tools=rate_limit_excluded,
        )

        self._path_validator = PathValidationMiddleware(
            allowed_roots=allowed_roots,
            allow_symlinks=allow_symlinks,
            blocked_patterns=blocked_patterns,
        )

        self._access_controller = AccessControlMiddleware(
            default_level=default_access_level,
            denied_tools=denied_tools,
            read_only=read_only,
            tool_levels=tool_levels,
        )

    async def on_call_tool(self, context: MiddlewareContext, call_next: Callable):
        """Apply all security checks in order."""
        if not FASTMCP_AVAILABLE:
            return await call_next(context)

        # 1. Check rate limit
        rate_result = await self._rate_limiter.on_call_tool(
            context,
            lambda ctx: {"_continue": True}  # Dummy call_next
        )
        if isinstance(rate_result, dict) and rate_result.get("error"):
            return rate_result

        # 2. Check access control
        access_result = await self._access_controller.on_call_tool(
            context,
            lambda ctx: {"_continue": True}
        )
        if isinstance(access_result, dict) and access_result.get("error"):
            return access_result

        # 3. Validate paths
        path_result = await self._path_validator.on_call_tool(
            context,
            lambda ctx: {"_continue": True}
        )
        if isinstance(path_result, dict) and path_result.get("error"):
            return path_result

        # All checks passed, proceed with actual call
        return await call_next(context)

    # Expose sub-middleware configuration
    @property
    def rate_limiter(self) -> RateLimitMiddleware:
        """Get rate limiter for configuration."""
        return self._rate_limiter

    @property
    def path_validator(self) -> PathValidationMiddleware:
        """Get path validator for configuration."""
        return self._path_validator

    @property
    def access_controller(self) -> AccessControlMiddleware:
        """Get access controller for configuration."""
        return self._access_controller

