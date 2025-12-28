"""
Direct Access Wrapper for Session Handoff Tools

Bypasses MCP interface to provide direct Python access to session handoff functionality.
Use this when the MCP framework has issues, as all underlying functions work perfectly.

Usage:
    from project_management_automation.tools.session_handoff_wrapper import SessionHandoffWrapper
    
    wrapper = SessionHandoffWrapper()
    result = wrapper.resume()
    # Returns dict instead of JSON string for easier use
"""

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from .session_handoff import (
        session_handoff as _session_handoff,
        resume_session as _resume_session,
        get_latest_handoff as _get_latest_handoff,
        list_handoffs as _list_handoffs,
        end_session as _end_session,
        sync_todo2_state as _sync_todo2_state,
    )
    FUNCTIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Session handoff functions not available: {e}")
    FUNCTIONS_AVAILABLE = False


class SessionHandoffWrapper:
    """
    Direct access wrapper for session handoff functionality.
    
    Bypasses MCP interface to provide direct Python access.
    All methods return Python dictionaries for easier use.
    """
    
    def __init__(self):
        """Initialize wrapper."""
        if not FUNCTIONS_AVAILABLE:
            raise RuntimeError("Session handoff functions not available")
    
    def resume(self) -> dict[str, Any]:
        """
        Resume a session by reviewing the latest handoff.
        
        Returns:
            Dict with session resumption context, latest handoff, and available tasks
        """
        result_str = _resume_session()
        return json.loads(result_str)
    
    def latest(self) -> dict[str, Any]:
        """
        Get the latest handoff note.
        
        Returns:
            Dict with latest handoff information
        """
        result_str = _get_latest_handoff()
        return json.loads(result_str)
    
    def list(self, limit: int = 5) -> dict[str, Any]:
        """
        List recent handoff notes.
        
        Args:
            limit: Maximum number of handoffs to return (default: 5)
            
        Returns:
            Dict with list of handoff notes
        """
        result_str = _list_handoffs(limit=limit)
        return json.loads(result_str)
    
    def end(
        self,
        summary: Optional[str] = None,
        blockers: Optional[list[str]] = None,
        next_steps: Optional[list[str]] = None,
        unassign_my_tasks: bool = True,
        include_git_status: bool = True,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """
        End current session and create handoff note.
        
        Args:
            summary: Summary of work completed
            blockers: List of blockers encountered
            next_steps: Suggested next steps
            unassign_my_tasks: Unassign tasks on end (default: True)
            include_git_status: Include git status (default: True)
            dry_run: Preview without changes (default: False)
            
        Returns:
            Dict with handoff creation result
        """
        result_str = _end_session(
            summary=summary,
            blockers=blockers,
            next_steps=next_steps,
            unassign_my_tasks=unassign_my_tasks,
            include_git_status=include_git_status,
            dry_run=dry_run
        )
        return json.loads(result_str)
    
    def sync(
        self,
        direction: str = "both",
        prefer_agentic_tools: bool = True,
        auto_commit: bool = True,
        dry_run: bool = False
    ) -> dict[str, Any]:
        """
        Sync Todo2 state across agents/machines.
        
        Args:
            direction: Sync direction - "pull", "push", or "both" (default: "both")
            prefer_agentic_tools: Try agentic-tools MCP first (default: True)
            auto_commit: Auto-commit state changes (default: True)
            dry_run: Preview without changes (default: False)
            
        Returns:
            Dict with sync results
        """
        result_str = _sync_todo2_state(
            direction=direction,
            prefer_agentic_tools=prefer_agentic_tools,
            auto_commit=auto_commit,
            dry_run=dry_run
        )
        return json.loads(result_str)
    
    def handoff(
        self,
        action: str,
        **kwargs
    ) -> dict[str, Any]:
        """
        Unified entry point for all session handoff actions.
        
        Args:
            action: One of "end", "resume", "latest", "list", "sync"
            **kwargs: Additional arguments for specific actions
            
        Returns:
            Dict with action results
            
        Examples:
            wrapper.handoff("resume")
            wrapper.handoff("latest")
            wrapper.handoff("list", limit=10)
            wrapper.handoff("end", summary="Completed feature X")
            wrapper.handoff("sync", direction="pull")
        """
        result_str = _session_handoff(action=action, **kwargs)
        return json.loads(result_str)


# Convenience instance for quick access
_wrapper_instance = None

def get_wrapper() -> SessionHandoffWrapper:
    """Get or create wrapper instance."""
    global _wrapper_instance
    if _wrapper_instance is None:
        _wrapper_instance = SessionHandoffWrapper()
    return _wrapper_instance


# Convenience functions for direct access
def resume() -> dict[str, Any]:
    """Resume session - convenience function."""
    return get_wrapper().resume()

def latest() -> dict[str, Any]:
    """Get latest handoff - convenience function."""
    return get_wrapper().latest()

def list_handoffs(limit: int = 5) -> dict[str, Any]:
    """List handoffs - convenience function."""
    return get_wrapper().list(limit=limit)

def end_session(
    summary: Optional[str] = None,
    blockers: Optional[list[str]] = None,
    next_steps: Optional[list[str]] = None,
    **kwargs
) -> dict[str, Any]:
    """End session - convenience function."""
    return get_wrapper().end(
        summary=summary,
        blockers=blockers,
        next_steps=next_steps,
        **kwargs
    )

def sync_state(**kwargs) -> dict[str, Any]:
    """Sync state - convenience function."""
    return get_wrapper().sync(**kwargs)


__all__ = [
    "SessionHandoffWrapper",
    "get_wrapper",
    "resume",
    "latest",
    "list_handoffs",
    "end_session",
    "sync_state",
]
