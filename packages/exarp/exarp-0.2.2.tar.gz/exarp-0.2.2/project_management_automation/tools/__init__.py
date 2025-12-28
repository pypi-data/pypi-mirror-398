"""
MCP Tool Wrappers for Project Management Automation

These modules wrap IntelligentAutomationBase classes to expose them
as MCP tools for AI assistant access.
"""

# Import error handling utilities for use in tools
import sys
from pathlib import Path

# Handle both relative and absolute imports
try:
    # Try relative import first (when run as module)
    from ..error_handler import (
        AutomationError,
        ErrorCode,
        format_error_response,
        format_success_response,
        handle_automation_error,
        log_automation_execution,
    )
except ImportError:
    # Fallback to absolute import (when run as script)
    server_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(server_dir))
    from error_handler import (
        AutomationError,
        ErrorCode,
        format_error_response,
        format_success_response,
        handle_automation_error,
        log_automation_execution,
    )

__all__ = [
    'handle_automation_error',
    'format_error_response',
    'format_success_response',
    'log_automation_execution',
    'AutomationError',
    'ErrorCode'
]
