"""
Interactive MCP Integration Module

Provides optional integration with interactive-mcp for human-in-the-loop workflows.
Gracefully falls back when interactive-mcp is not available.

Usage:
    from project_management_automation.interactive import (
        request_user_input,
        message_complete_notification,
        start_intensive_chat,
        ask_intensive_chat,
        stop_intensive_chat,
        is_available,
    )
    
    # Check availability
    if is_available():
        response = request_user_input("Proceed?", options=["yes", "no"])
        message_complete_notification("Task completed!")
"""

import logging
from typing import Any, Optional

logger = logging.getLogger("exarp.interactive")

# Try to import interactive-mcp tools
_available = False
_request_user_input = None
_message_complete_notification = None
_start_intensive_chat = None
_ask_intensive_chat = None
_stop_intensive_chat = None

try:
    from mcp_interactive_request_user_input import mcp_interactive_request_user_input
    from mcp_interactive_message_complete_notification import mcp_interactive_message_complete_notification
    from mcp_interactive_start_intensive_chat import mcp_interactive_start_intensive_chat
    from mcp_interactive_ask_intensive_chat import mcp_interactive_ask_intensive_chat
    from mcp_interactive_stop_intensive_chat import mcp_interactive_stop_intensive_chat
    
    _available = True
    _request_user_input = mcp_interactive_request_user_input
    _message_complete_notification = mcp_interactive_message_complete_notification
    _start_intensive_chat = mcp_interactive_start_intensive_chat
    _ask_intensive_chat = mcp_interactive_ask_intensive_chat
    _stop_intensive_chat = mcp_interactive_stop_intensive_chat
    
    logger.debug("✅ interactive-mcp integration available")
    
except ImportError:
    logger.debug("⚠️ interactive-mcp not available - using fallback mode")
    _available = False


def is_available() -> bool:
    """
    Check if interactive-mcp is available.
    
    Returns:
        True if interactive-mcp tools are available, False otherwise
    """
    return _available


def request_user_input(
    project_name: str,
    message: str,
    predefined_options: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Request user input via interactive-mcp.
    
    Args:
        project_name: Project context identifier
        message: Question or prompt for the user
        predefined_options: Optional list of choices for quick selection
        
    Returns:
        User's response string, or None if unavailable or cancelled
        
    Example:
        response = request_user_input(
            "MyProject",
            "Approve 10 tasks?",
            options=["yes", "no", "review"]
        )
    """
    if not _available:
        logger.debug(f"Interactive input requested but unavailable: {message}")
        return None
    
    try:
        result = _request_user_input(
            project_name=project_name,
            message=message,
            predefined_options=predefined_options or [],
        )
        return result
    except Exception as e:
        logger.warning(f"Failed to request user input: {e}")
        return None


def message_complete_notification(project_name: str, message: str) -> None:
    """
    Send OS notification via interactive-mcp.
    
    Args:
        project_name: Project context identifier
        message: Notification message text
        
    Example:
        message_complete_notification("MyProject", "Automation completed: 5 tasks moved")
    """
    if not _available:
        logger.debug(f"Notification requested but unavailable: {message}")
        return
    
    try:
        _message_complete_notification(project_name=project_name, message=message)
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")


def start_intensive_chat(session_title: str) -> Optional[str]:
    """
    Start an intensive chat session for multiple questions.
    
    Args:
        session_title: Title for the chat session
        
    Returns:
        Session ID if successful, None otherwise
        
    Example:
        session_id = start_intensive_chat("Project Configuration")
    """
    if not _available:
        logger.debug(f"Intensive chat requested but unavailable: {session_title}")
        return None
    
    try:
        result = _start_intensive_chat(session_title=session_title)
        return result.get("sessionId") if isinstance(result, dict) else None
    except Exception as e:
        logger.warning(f"Failed to start intensive chat: {e}")
        return None


def ask_intensive_chat(
    session_id: str,
    question: str,
    predefined_options: Optional[list[str]] = None,
) -> Optional[str]:
    """
    Ask a question in an active intensive chat session.
    
    Args:
        session_id: Session ID from start_intensive_chat
        question: Question text
        predefined_options: Optional list of choices
        
    Returns:
        User's response, or None if unavailable
    """
    if not _available:
        logger.debug(f"Intensive chat question requested but unavailable")
        return None
    
    try:
        result = _ask_intensive_chat(
            sessionId=session_id,
            question=question,
            predefinedOptions=predefined_options or [],
        )
        return result
    except Exception as e:
        logger.warning(f"Failed to ask intensive chat question: {e}")
        return None


def stop_intensive_chat(session_id: str) -> None:
    """
    Stop and close an intensive chat session.
    
    Args:
        session_id: Session ID to close
    """
    if not _available:
        logger.debug(f"Intensive chat stop requested but unavailable")
        return
    
    try:
        _stop_intensive_chat(sessionId=session_id)
    except Exception as e:
        logger.warning(f"Failed to stop intensive chat: {e}")


__all__ = [
    "is_available",
    "request_user_input",
    "message_complete_notification",
    "start_intensive_chat",
    "ask_intensive_chat",
    "stop_intensive_chat",
]
