"""
Context helpers for FastMCP tools.

Provides utilities for using the FastMCP Context object:
- Progress reporting
- Client-side logging
- Resource access
- State management

Usage:
    from fastmcp import Context
    from project_management_automation.context_helpers import (
        report_progress,
        log_info,
        log_warning,
    )

    @mcp.tool()
    async def my_tool(data: str, ctx: Context) -> str:
        await log_info(ctx, "Starting processing...")
        await report_progress(ctx, 0, 100, "Initializing")
        # ... work ...
        await report_progress(ctx, 100, 100, "Complete")
        return result
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    try:
        from fastmcp import Context
    except ImportError:
        Context = Any

logger = logging.getLogger("exarp.context")


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRESS REPORTING
# ═══════════════════════════════════════════════════════════════════════════════

async def report_progress(
    ctx: "Context",
    progress: int,
    total: int,
    message: Optional[str] = None,
) -> None:
    """
    Report progress to the client.

    Args:
        ctx: FastMCP Context object
        progress: Current progress value
        total: Total progress value
        message: Optional progress message
    """
    try:
        if hasattr(ctx, "report_progress"):
            await ctx.report_progress(progress=progress, total=total, message=message)
    except Exception as e:
        logger.debug(f"Progress reporting not available: {e}")


class ProgressTracker:
    """
    Helper class for tracking progress across multiple steps.

    Usage:
        tracker = ProgressTracker(ctx, total_steps=5)
        await tracker.step("Loading data")
        await tracker.step("Processing")
        await tracker.step("Saving results")
    """

    def __init__(self, ctx: "Context", total_steps: int):
        self.ctx = ctx
        self.total_steps = total_steps
        self.current_step = 0

    async def step(self, message: Optional[str] = None) -> None:
        """Advance to next step and report progress."""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        await report_progress(self.ctx, progress, 100, message)

    async def set_progress(self, percent: int, message: Optional[str] = None) -> None:
        """Set progress to specific percentage."""
        await report_progress(self.ctx, percent, 100, message)


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT-SIDE LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

async def log_info(ctx: "Context", message: str) -> None:
    """Log info message to client."""
    try:
        if hasattr(ctx, "info"):
            await ctx.info(message)
    except Exception:
        logger.info(message)  # Fallback to server-side logging


async def log_debug(ctx: "Context", message: str) -> None:
    """Log debug message to client."""
    try:
        if hasattr(ctx, "debug"):
            await ctx.debug(message)
    except Exception:
        logger.debug(message)


async def log_warning(ctx: "Context", message: str) -> None:
    """Log warning message to client."""
    try:
        if hasattr(ctx, "warning"):
            await ctx.warning(message)
    except Exception:
        logger.warning(message)


async def log_error(ctx: "Context", message: str) -> None:
    """Log error message to client."""
    try:
        if hasattr(ctx, "error"):
            await ctx.error(message)
    except Exception:
        logger.error(message)


# ═══════════════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def get_state(ctx: "Context", key: str, default: Any = None) -> Any:
    """Get value from request-scoped state."""
    try:
        if hasattr(ctx, "get_state"):
            return ctx.get_state(key) or default
    except Exception:
        pass
    return default


def set_state(ctx: "Context", key: str, value: Any) -> None:
    """Set value in request-scoped state."""
    try:
        if hasattr(ctx, "set_state"):
            ctx.set_state(key, value)
    except Exception as e:
        logger.debug(f"State management not available: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCE ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

async def read_resource(ctx: "Context", uri: str) -> Optional[str]:
    """
    Read a resource by URI.

    Args:
        ctx: FastMCP Context object
        uri: Resource URI (e.g., "tasks://T-123")

    Returns:
        Resource content or None if not found
    """
    try:
        if hasattr(ctx, "read_resource"):
            resources = await ctx.read_resource(uri)
            if resources:
                return resources[0].content if hasattr(resources[0], "content") else str(resources[0])
    except Exception as e:
        logger.debug(f"Resource read failed for {uri}: {e}")
    return None


async def list_resources(ctx: "Context") -> list[str]:
    """List available resource URIs."""
    try:
        if hasattr(ctx, "list_resources"):
            resources = await ctx.list_resources()
            return [r.uri for r in resources]
    except Exception as e:
        logger.debug(f"Resource listing failed: {e}")
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# LLM SAMPLING (Experimental)
# ═══════════════════════════════════════════════════════════════════════════════

async def sample_llm(
    ctx: "Context",
    prompt: str,
    max_tokens: int = 500,
) -> Optional[str]:
    """
    Request the client's LLM to process a prompt.

    This allows tools to leverage the connected LLM for
    analysis, summarization, or decision-making.

    Args:
        ctx: FastMCP Context object
        prompt: Prompt to send to the LLM
        max_tokens: Maximum response tokens

    Returns:
        LLM response text or None if not available
    """
    try:
        if hasattr(ctx, "sample"):
            response = await ctx.sample(prompt, max_tokens=max_tokens)
            return response.text if hasattr(response, "text") else str(response)
    except Exception as e:
        logger.debug(f"LLM sampling not available: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST INFO
# ═══════════════════════════════════════════════════════════════════════════════

def get_request_id(ctx: "Context") -> Optional[str]:
    """Get the current request ID."""
    try:
        return getattr(ctx, "request_id", None)
    except Exception:
        return None


def get_client_id(ctx: "Context") -> Optional[str]:
    """Get the client ID."""
    try:
        return getattr(ctx, "client_id", None)
    except Exception:
        return None


def get_session_id(ctx: "Context") -> Optional[str]:
    """Get the session ID."""
    try:
        return getattr(ctx, "session_id", None)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# ELICITATION (Interactive User Input)
# ═══════════════════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class ElicitAction(str, Enum):
    """Possible user actions for elicitation."""
    ACCEPT = "accept"
    DECLINE = "decline"
    CANCEL = "cancel"


@dataclass
class ElicitResult:
    """Result of an elicitation request."""
    action: ElicitAction
    data: Any = None


async def elicit(
    ctx: "Context",
    message: str,
    response_type: type = str,
) -> ElicitResult:
    """
    Request user input through the client.

    Elicitation allows tools to interactively gather information
    from users during execution.

    Args:
        ctx: FastMCP Context object
        message: Message to display to user
        response_type: Expected response type (str, int, bool, or dataclass)

    Returns:
        ElicitResult with action and data

    Example:
        result = await elicit(ctx, "Enter your name:", str)
        if result.action == ElicitAction.ACCEPT:
            name = result.data
    """
    try:
        if hasattr(ctx, "elicit"):
            result = await ctx.elicit(message, response_type=response_type)
            return ElicitResult(
                action=ElicitAction(result.action),
                data=result.data if hasattr(result, "data") else None,
            )
    except Exception as e:
        logger.debug(f"Elicitation not available: {e}")

    # Fallback: return decline (elicitation not supported)
    return ElicitResult(action=ElicitAction.DECLINE)


async def elicit_confirmation(
    ctx: "Context",
    message: str,
) -> bool:
    """
    Request yes/no confirmation from user.

    Args:
        ctx: FastMCP Context object
        message: Confirmation message

    Returns:
        True if accepted, False otherwise
    """
    result = await elicit(ctx, message, bool)
    return result.action == ElicitAction.ACCEPT and result.data is True


async def elicit_choice(
    ctx: "Context",
    message: str,
    choices: list[str],
) -> Optional[str]:
    """
    Request user to select from choices.

    Args:
        ctx: FastMCP Context object
        message: Selection message
        choices: List of options

    Returns:
        Selected choice or None if cancelled
    """

    # Build choice type dynamically
    choice_str = f"Select one of: {', '.join(choices)}"
    result = await elicit(ctx, f"{message}\n{choice_str}", str)

    if result.action == ElicitAction.ACCEPT and result.data in choices:
        return result.data
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# ROOTS (Filesystem Access)
# ═══════════════════════════════════════════════════════════════════════════════

async def list_roots(ctx: "Context") -> list[str]:
    """
    List filesystem roots available to the server.

    Roots define which directories the client has given
    the server access to.

    Returns:
        List of root paths
    """
    try:
        if hasattr(ctx, "list_roots"):
            roots = await ctx.list_roots()
            return [str(r.uri) if hasattr(r, "uri") else str(r) for r in roots]
    except Exception as e:
        logger.debug(f"Roots listing not available: {e}")
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS (List Changes)
# ═══════════════════════════════════════════════════════════════════════════════

async def notify_tools_changed(ctx: "Context") -> None:
    """Notify client that the tool list has changed."""
    try:
        if hasattr(ctx, "send_tool_list_changed"):
            await ctx.send_tool_list_changed()
    except Exception as e:
        logger.debug(f"Tool notification not available: {e}")


async def notify_resources_changed(ctx: "Context") -> None:
    """Notify client that the resource list has changed."""
    try:
        if hasattr(ctx, "send_resource_list_changed"):
            await ctx.send_resource_list_changed()
    except Exception as e:
        logger.debug(f"Resource notification not available: {e}")


async def notify_prompts_changed(ctx: "Context") -> None:
    """Notify client that the prompt list has changed."""
    try:
        if hasattr(ctx, "send_prompt_list_changed"):
            await ctx.send_prompt_list_changed()
    except Exception as e:
        logger.debug(f"Prompt notification not available: {e}")


__all__ = [
    # Progress
    "report_progress",
    "ProgressTracker",
    # Logging
    "log_info",
    "log_debug",
    "log_warning",
    "log_error",
    # State
    "get_state",
    "set_state",
    # Resources
    "read_resource",
    "list_resources",
    # LLM Sampling
    "sample_llm",
    # Request info
    "get_request_id",
    "get_client_id",
    "get_session_id",
    # Elicitation
    "ElicitAction",
    "ElicitResult",
    "elicit",
    "elicit_confirmation",
    "elicit_choice",
    # Roots
    "list_roots",
    # Notifications
    "notify_tools_changed",
    "notify_resources_changed",
    "notify_prompts_changed",
]

