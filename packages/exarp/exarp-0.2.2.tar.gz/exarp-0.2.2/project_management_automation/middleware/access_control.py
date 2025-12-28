"""
Access Control Middleware for FastMCP.

Provides tool-level access control based on tool names and access levels.
"""

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


class AccessLevel:
    """Access levels for tool operations."""
    READ = "read"           # Read files, list directories
    WRITE = "write"         # Create/modify files
    EXECUTE = "execute"     # Run commands, scripts
    ADMIN = "admin"         # Destructive operations, config changes


# Default tool access level mappings
DEFAULT_TOOL_LEVELS = {
    # Read operations
    "check_documentation_health": AccessLevel.READ,
    "analyze_todo2_alignment": AccessLevel.READ,
    "detect_duplicate_tasks": AccessLevel.READ,
    "generate_project_scorecard": AccessLevel.READ,
    "generate_project_overview": AccessLevel.READ,
    "list_tasks_awaiting_clarification": AccessLevel.READ,
    "server_status": AccessLevel.READ,
    "list_problem_categories": AccessLevel.READ,
    "list_advisors": AccessLevel.READ,
    # check_tts_backends removed - TTS functionality migrated to devwisdom-go MCP server
    "fetch_dependabot_alerts": AccessLevel.READ,
    "generate_security_report": AccessLevel.READ,

    # Write operations
    "sync_todo_tasks": AccessLevel.WRITE,
    "resolve_task_clarification": AccessLevel.WRITE,
    "batch_approve_tasks": AccessLevel.WRITE,
    "setup_git_hooks": AccessLevel.WRITE,
    "setup_pattern_triggers": AccessLevel.WRITE,
    "generate_cursor_rules": AccessLevel.WRITE,
    "generate_cursorignore": AccessLevel.WRITE,
    "save_memory": AccessLevel.WRITE,
    "log_prompt_iteration": AccessLevel.WRITE,

    # Execute operations
    "run_tests": AccessLevel.EXECUTE,
    "run_daily_automation": AccessLevel.EXECUTE,
    "scan_dependency_security": AccessLevel.EXECUTE,
    # Audio tools removed - migrated to devwisdom-go MCP server

    # Admin operations
    "run_nightly_task_automation": AccessLevel.ADMIN,
    "run_automation": AccessLevel.ADMIN,
}


class AccessControlMiddleware(Middleware):
    """
    Tool-level access control middleware.

    Enforces access levels on tool calls.

    Usage:
        mcp.add_middleware(AccessControlMiddleware(
            default_level=AccessLevel.WRITE,
            denied_tools={"dangerous_tool"},
            read_only=False,
        ))
    """

    def __init__(
        self,
        default_level: str = AccessLevel.WRITE,
        denied_tools: Optional[set[str]] = None,
        read_only: bool = False,
        tool_levels: Optional[dict[str, str]] = None,
    ):
        """
        Initialize access controller.

        Args:
            default_level: Default access level for unlisted tools
            denied_tools: Set of tool names that are always denied
            read_only: If True, deny all write/execute/admin operations
            tool_levels: Custom tool -> access level mappings
        """
        self.default_level = default_level
        self.denied_tools = denied_tools or set()
        self.read_only = read_only
        self._tool_levels = {**DEFAULT_TOOL_LEVELS, **(tool_levels or {})}

    def _get_required_level(self, tool_name: str) -> str:
        """Get required access level for a tool."""
        return self._tool_levels.get(tool_name, self.default_level)

    def _can_execute(self, tool_name: str) -> tuple[bool, str]:
        """
        Check if a tool can be executed.

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check explicit denials
        if tool_name in self.denied_tools:
            return False, f"Tool '{tool_name}' is explicitly denied"

        # Get required level
        required_level = self._get_required_level(tool_name)

        # In read-only mode, only allow read operations
        if self.read_only and required_level != AccessLevel.READ:
            return False, f"Read-only mode: '{tool_name}' requires {required_level} access"

        return True, ""

    async def on_call_tool(self, context: MiddlewareContext, call_next: Callable):
        """Check access control before tool execution."""
        if not FASTMCP_AVAILABLE:
            return await call_next(context)

        # Get tool name from context
        tool_name = getattr(context, "tool_name", None) or "unknown"

        # Check access
        allowed, reason = self._can_execute(tool_name)
        if not allowed:
            return {
                "error": "access_denied",
                "message": reason,
                "tool": tool_name,
            }

        return await call_next(context)

