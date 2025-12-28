"""
Tool Filter Middleware for Dynamic Tool Loading.

Intercepts tools/list requests and filters based on the DynamicToolManager.
This enables context-aware tool curation without modifying tool registration.

MCP Spec Reference (2025-06-18):
- tools/list returns visible tools
- tools/list_changed notification triggers re-fetch

Philosophy: Reduce context pollution by showing only relevant tools.
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("exarp.middleware.tool_filter")


class ToolFilterMiddleware:
    """
    Middleware that filters tools based on dynamic visibility settings.

    For FastMCP 2.x, middleware can intercept requests/responses:
    - tools/list → filter response to only visible tools
    - Other requests → pass through unchanged

    Usage:
        from middleware.tool_filter import ToolFilterMiddleware
        mcp.add_middleware(ToolFilterMiddleware())
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize middleware.

        Args:
            enabled: If False, all tools are visible (bypass filtering)
        """
        self.enabled = enabled
        self._filter_count = 0
        self._total_calls = 0

    async def __call__(
        self,
        request: Any,
        call_next: Callable,
        context: Optional[Any] = None,
    ) -> Any:
        """
        Process request, filtering tools/list responses.

        Note: FastMCP middleware signature may vary by version.
        This is designed for FastMCP 2.x style middleware.
        """
        self._total_calls += 1

        # Pass through if filtering disabled
        if not self.enabled:
            return await call_next(request)

        # Get response first
        response = await call_next(request)

        # Check if this is a tools/list response to filter
        if self._is_tools_list_response(request, response):
            response = await self._filter_tools_response(response)

        return response

    def _is_tools_list_response(self, request: Any, response: Any) -> bool:
        """Check if this is a tools/list response."""
        # Check request method
        if hasattr(request, "method"):
            if request.method == "tools/list":
                return True

        # Check request params
        if hasattr(request, "params"):
            if getattr(request.params, "method", None) == "tools/list":
                return True

        # Check if response has tools attribute
        if hasattr(response, "tools") and isinstance(response.tools, list):
            return True

        return False

    async def _filter_tools_response(self, response: Any) -> Any:
        """Filter tools in response based on visibility."""
        try:
            from ..tools.dynamic_tools import get_tool_manager

            manager = get_tool_manager()

            if not hasattr(response, "tools"):
                return response

            original_count = len(response.tools)

            # Filter tools by visibility
            visible_tools = [
                tool for tool in response.tools
                if manager.is_tool_visible(getattr(tool, "name", str(tool)))
            ]

            filtered_count = original_count - len(visible_tools)
            if filtered_count > 0:
                self._filter_count += filtered_count
                logger.debug(
                    f"Filtered {filtered_count}/{original_count} tools "
                    f"(mode={manager.current_mode.value})"
                )

            # Update response
            response.tools = visible_tools

        except ImportError:
            logger.warning("Dynamic tools module not available - showing all tools")
        except Exception as e:
            logger.error(f"Error filtering tools: {e}")

        return response

    def get_stats(self) -> dict[str, Any]:
        """Get middleware statistics."""
        return {
            "enabled": self.enabled,
            "total_calls": self._total_calls,
            "tools_filtered": self._filter_count,
        }


def create_tool_filter_middleware(enabled: bool = True) -> ToolFilterMiddleware:
    """Factory function for creating middleware."""
    return ToolFilterMiddleware(enabled=enabled)


# For direct use without middleware (e.g., in list_tools handler)
def filter_tools_by_visibility(tools: list[Any]) -> list[Any]:
    """
    Filter a list of tools by current visibility settings.

    Use this in custom list_tools handlers:

        @server.list_tools()
        async def list_tools():
            all_tools = get_all_tool_definitions()
            return filter_tools_by_visibility(all_tools)
    """
    try:
        from ..tools.dynamic_tools import get_tool_manager

        manager = get_tool_manager()
        return [
            tool for tool in tools
            if manager.is_tool_visible(getattr(tool, "name", str(tool)))
        ]
    except ImportError:
        return tools  # Show all if dynamic tools not available


__all__ = [
    "ToolFilterMiddleware",
    "create_tool_filter_middleware",
    "filter_tools_by_visibility",
]

