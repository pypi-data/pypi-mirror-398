"""
MCP Resource Handler for Automation Status

Provides resource access to automation server status and health.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from ..version import __version__

logger = logging.getLogger(__name__)


def get_status_resource() -> str:
    """
    Get automation server status as resource.

    Returns:
        JSON string with server status, tools, and health information
    """
    try:
        # Check if tools are available by checking if tool files exist
        tools_dir = Path(__file__).parent.parent / 'tools'
        tool_files = [
            'docs_health.py',
            'todo2_alignment.py',
            'duplicate_detection.py',
            'dependency_security.py',
            'automation_opportunities.py',
            'todo_sync.py',
        ]

        tools_available = all((tools_dir / tool_file).exists() for tool_file in tool_files)
        error_handler_available = (Path(__file__).parent.parent / 'error_handler.py').exists()

        status = {
            "server": "exarp",
            "version": __version__,
            "status": "operational",
            "mcp_available": True,  # Assumed if resource is being called
            "tools_available": tools_available,
            "error_handling_available": error_handler_available,
            "timestamp": datetime.now().isoformat(),
            "tools": {
                "total": 20 if tools_available else 1,
                "high_priority": 5 if tools_available else 0,
                "medium_priority": 13 if tools_available else 0,
                "low_priority": 1 if tools_available else 0,
                "available": [
                    "server_status",
                    "check_documentation_health",
                    "analyze_todo2_alignment",
                    "detect_duplicate_tasks",
                    "scan_dependency_security",
                    "find_automation_opportunities",
                    "sync_todo_tasks",
                    "add_external_tool_hints",
                    "run_daily_automation",
                    "validate_ci_cd_workflow",
                    "batch_approve_tasks",
                    "run_nightly_task_automation",
                    "check_working_copy_health",
                    "resolve_task_clarification",
                    "resolve_multiple_clarifications",
                    "list_tasks_awaiting_clarification",
                    "setup_git_hooks",
                    "setup_pattern_triggers",
                    "simplify_rules"
                ] if tools_available else ["server_status"]
            }
        }

        return json.dumps(status, separators=(',', ':'))

    except Exception as e:
        logger.error(f"Error getting status resource: {e}")
        return json.dumps({
            "server": "exarp",
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
