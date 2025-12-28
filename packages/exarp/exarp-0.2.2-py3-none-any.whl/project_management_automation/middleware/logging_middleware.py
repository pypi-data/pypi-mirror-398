"""
Logging Middleware for FastMCP.

Provides request/response logging with timing information.
"""

import logging
import time
from typing import Callable

try:
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    class Middleware:
        pass
    class MiddlewareContext:
        pass

logger = logging.getLogger("exarp.middleware.logging")


class LoggingMiddleware(Middleware):
    """
    Request/response logging middleware.

    Logs tool calls with timing information.

    Usage:
        mcp.add_middleware(LoggingMiddleware(
            log_arguments=True,
            log_results=False,  # Don't log potentially large results
        ))
    """

    def __init__(
        self,
        log_arguments: bool = True,
        log_results: bool = False,
        log_level: int = logging.INFO,
        slow_threshold_ms: float = 1000.0,
    ):
        """
        Initialize logging middleware.

        Args:
            log_arguments: Whether to log tool arguments
            log_results: Whether to log tool results (can be verbose)
            log_level: Logging level to use
            slow_threshold_ms: Threshold for slow request warnings (ms)
        """
        self.log_arguments = log_arguments
        self.log_results = log_results
        self.log_level = log_level
        self.slow_threshold_ms = slow_threshold_ms

    async def on_call_tool(self, context: MiddlewareContext, call_next: Callable):
        """Log tool call with timing and track for mode inference (MODE-002)."""
        if not FASTMCP_AVAILABLE:
            return await call_next(context)

        tool_name = getattr(context, "tool_name", None) or "unknown"
        client_id = getattr(context.fastmcp_context, "client_id", "unknown") if hasattr(context, "fastmcp_context") else "unknown"
        request_id = getattr(context.fastmcp_context, "request_id", None) if hasattr(context, "fastmcp_context") else None
        arguments = getattr(context, "arguments", {}) or {}

        # Log request
        log_parts = [f"Tool call: {tool_name}"]
        if request_id:
            log_parts.append(f"request_id={request_id}")
        if client_id != "unknown":
            log_parts.append(f"client={client_id}")

        if self.log_arguments:
            # Truncate large arguments
            arg_str = str(arguments)
            if len(arg_str) > 200:
                arg_str = arg_str[:200] + "..."
            log_parts.append(f"args={arg_str}")

        logger.log(self.log_level, " | ".join(log_parts))

        # Track tool usage for mode inference (MODE-002)
        try:
            from ..tools.dynamic_tools import get_tool_manager
            manager = get_tool_manager()
            manager.record_tool_usage(tool_name, tool_args=arguments)
            
            # Periodically update mode inference (every 5 tool calls)
            tool_call_count = sum(manager.usage_tracker.tool_counts.values())
            if tool_call_count % 5 == 0:
                manager.update_inferred_mode()
        except Exception as e:
            logger.debug(f"Failed to track tool usage for mode inference: {e}")

        # Execute tool
        start_time = time.time()
        try:
            result = await call_next(context)
            elapsed_ms = (time.time() - start_time) * 1000

            # Log response
            log_parts = [f"Tool done: {tool_name}", f"elapsed={elapsed_ms:.1f}ms"]

            if elapsed_ms > self.slow_threshold_ms:
                logger.warning(f"Slow tool call: {tool_name} took {elapsed_ms:.1f}ms")

            if self.log_results:
                result_str = str(result)
                if len(result_str) > 200:
                    result_str = result_str[:200] + "..."
                log_parts.append(f"result={result_str}")

            logger.log(self.log_level, " | ".join(log_parts))
            return result

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            import traceback
            logger.error(f"Tool error: {tool_name} | elapsed={elapsed_ms:.1f}ms | error={e}", exc_info=True)
            logger.debug(f"Full traceback for {tool_name}:\n{traceback.format_exc()}")
            raise

    async def on_request(self, context: MiddlewareContext, call_next: Callable):
        """Log all requests (not just tool calls)."""
        if not FASTMCP_AVAILABLE:
            return await call_next(context)

        request_type = getattr(context, "request_type", "unknown")
        start_time = time.time()

        try:
            result = await call_next(context)
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"Request: {request_type} | elapsed={elapsed_ms:.1f}ms")
            return result
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Request error: {request_type} | elapsed={elapsed_ms:.1f}ms | error={e}")
            raise

