"""
FastMCP Middleware for Exarp MCP Server.

Provides:
- RateLimitMiddleware: Token bucket rate limiting per client/tool
- PathValidationMiddleware: Path boundary enforcement on all file operations
- AccessControlMiddleware: Tool-level access control
- LoggingMiddleware: Request/response logging with timing
- SecurityMiddleware: Combined security (rate limit + path + access)
- ToolFilterMiddleware: Dynamic tool loading based on workflow mode

Usage:
    from project_management_automation.middleware import (
        SecurityMiddleware,
        RateLimitMiddleware,
        LoggingMiddleware,
        ToolFilterMiddleware,
    )

    mcp.add_middleware(SecurityMiddleware())
    mcp.add_middleware(ToolFilterMiddleware())  # Context-aware tool curation
    # or individual:
    mcp.add_middleware(RateLimitMiddleware(calls_per_minute=60))
"""

from .access_control import AccessControlMiddleware
from .logging_middleware import LoggingMiddleware
from .path_validation import PathValidationMiddleware
from .rate_limit import RateLimitMiddleware
from .security import SecurityMiddleware
from .tool_filter import ToolFilterMiddleware, filter_tools_by_visibility

__all__ = [
    "RateLimitMiddleware",
    "PathValidationMiddleware",
    "AccessControlMiddleware",
    "LoggingMiddleware",
    "SecurityMiddleware",
    "ToolFilterMiddleware",
    "filter_tools_by_visibility",
]

