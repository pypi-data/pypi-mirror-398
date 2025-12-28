"""
MCP Resource Handler for Task Assignees

Provides resource access to task assignments for cross-host visibility.
Different machines can query these resources to see what other agents/hosts are working on.

Resources:
    automation://assignees                     - List of all assignees with task counts
    automation://assignees/workload            - Workload distribution summary
    automation://tasks/assignee/{name}         - Tasks for a specific assignee
    automation://tasks/unassigned              - All unassigned tasks
    automation://tasks/host/{hostname}         - Tasks assigned to a specific host
"""

import json
import logging
from datetime import datetime

from ..tools.task_assignee import (
    KNOWN_AGENTS,
    KNOWN_HUMANS,
    _detect_agents_from_project,
    _get_current_hostname,
    _get_known_hosts,
    _load_todo2_state,
    get_workload_summary,
    list_tasks_by_assignee,
)

logger = logging.getLogger(__name__)


def get_all_assignees_resource() -> str:
    """
    Resource: automation://assignees
    
    Returns list of all assignees with their task counts and status.
    Useful for seeing who is working on what across the system.
    """
    try:
        state = _load_todo2_state()
        todos = state.get("todos", [])

        # Collect unique assignees
        assignees: dict[str, dict] = {}

        for task in todos:
            assignee = task.get("assignee")
            if not assignee:
                continue

            atype = assignee.get("type", "unknown")
            aname = assignee.get("name", "unknown")
            key = f"{atype}:{aname}"

            if key not in assignees:
                assignees[key] = {
                    "type": atype,
                    "name": aname,
                    "hostname": assignee.get("hostname"),
                    "task_count": 0,
                    "in_progress_count": 0,
                    "tasks": [],
                }

            assignees[key]["task_count"] += 1
            if task.get("status") == "In Progress":
                assignees[key]["in_progress_count"] += 1
            assignees[key]["tasks"].append({
                "id": task.get("id"),
                "name": task.get("name", "")[:50],
                "status": task.get("status"),
            })

        # Get available agents/hosts
        available_agents = _detect_agents_from_project()
        known_hosts = _get_known_hosts()

        result = {
            "assignees": list(assignees.values()),
            "available": {
                "agents": available_agents or KNOWN_AGENTS,
                "hosts": list(known_hosts.keys()),
                "humans": KNOWN_HUMANS,
            },
            "summary": {
                "total_assignees": len(assignees),
                "total_tasks": len(todos),
                "assigned_tasks": sum(a["task_count"] for a in assignees.values()),
                "unassigned_tasks": sum(1 for t in todos if not t.get("assignee")),
            },
            "current_host": _get_current_hostname(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        return json.dumps(result, separators=(',', ':'))

    except Exception as e:
        logger.error(f"Error getting assignees resource: {e}")
        return json.dumps({
            "assignees": [],
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }, indent=2)


def get_workload_resource() -> str:
    """
    Resource: automation://assignees/workload
    
    Returns workload distribution across all assignees.
    Shows task counts per agent/human/host for coordination.
    """
    return get_workload_summary()


def get_tasks_for_assignee_resource(assignee_name: str) -> str:
    """
    Resource: automation://tasks/assignee/{assignee_name}
    
    Returns all tasks assigned to a specific assignee.
    
    Args:
        assignee_name: Name of the assignee (e.g., "backend-agent", "david")
    """
    return list_tasks_by_assignee(assignee_name=assignee_name)


def get_unassigned_tasks_resource() -> str:
    """
    Resource: automation://tasks/unassigned
    
    Returns all unassigned tasks.
    Useful for finding work to pick up.
    """
    try:
        state = _load_todo2_state()
        todos = state.get("todos", [])

        unassigned = []
        for task in todos:
            if not task.get("assignee"):
                unassigned.append({
                    "id": task.get("id"),
                    "name": task.get("name", ""),
                    "status": task.get("status"),
                    "priority": task.get("priority"),
                    "tags": task.get("tags", []),
                })

        # Group by status
        by_status: dict[str, list] = {}
        for task in unassigned:
            status = task.get("status", "Unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(task)

        return json.dumps({
            "unassigned_tasks": unassigned,
            "by_status": by_status,
            "total": len(unassigned),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting unassigned tasks: {e}")
        return json.dumps({
            "unassigned_tasks": [],
            "error": str(e),
        }, indent=2)


def get_tasks_for_host_resource(hostname: str) -> str:
    """
    Resource: automation://tasks/host/{hostname}
    
    Returns all tasks assigned to agents running on a specific host.
    Useful for seeing what a remote machine is working on.
    
    Args:
        hostname: Hostname or IP of the machine
    """
    try:
        state = _load_todo2_state()
        todos = state.get("todos", [])

        # Find tasks where assignee hostname matches
        host_tasks = []
        for task in todos:
            assignee = task.get("assignee")
            if assignee and assignee.get("hostname") == hostname:
                host_tasks.append({
                    "id": task.get("id"),
                    "name": task.get("name", ""),
                    "status": task.get("status"),
                    "priority": task.get("priority"),
                    "assignee_name": assignee.get("name"),
                    "assignee_type": assignee.get("type"),
                    "assigned_at": assignee.get("assigned_at"),
                })

        return json.dumps({
            "hostname": hostname,
            "tasks": host_tasks,
            "task_count": len(host_tasks),
            "current_host": _get_current_hostname(),
            "is_current_host": hostname == _get_current_hostname(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting tasks for host: {e}")
        return json.dumps({
            "hostname": hostname,
            "tasks": [],
            "error": str(e),
        }, indent=2)


def get_my_tasks_resource() -> str:
    """
    Resource: automation://tasks/mine
    
    Returns tasks assigned to the current host.
    Useful for agents to see their own workload.
    """
    current_host = _get_current_hostname()
    return get_tasks_for_host_resource(current_host)


def get_latest_handoff_resource() -> str:
    """
    Resource: automation://handoff/latest
    
    Get the most recent session handoff note.
    """
    try:
        from ..tools.session_handoff import get_latest_handoff
        return get_latest_handoff()
    except Exception as e:
        return json.dumps({"error": str(e)}, separators=(',', ':'))


def register_assignee_resources(mcp) -> None:
    """
    Register assignee resources with the MCP server.
    """
    try:
        @mcp.resource("automation://assignees")
        def assignees_resource() -> str:
            """Get list of all assignees with task counts."""
            return get_all_assignees_resource()

        @mcp.resource("automation://assignees/workload")
        def workload_resource() -> str:
            """Get workload distribution across assignees."""
            return get_workload_resource()

        @mcp.resource("automation://tasks/assignee/{assignee_name}")
        def tasks_by_assignee_resource(assignee_name: str) -> str:
            """Get tasks for a specific assignee."""
            return get_tasks_for_assignee_resource(assignee_name)

        @mcp.resource("automation://tasks/unassigned")
        def unassigned_tasks_resource() -> str:
            """Get all unassigned tasks."""
            return get_unassigned_tasks_resource()

        @mcp.resource("automation://tasks/host/{hostname}")
        def tasks_by_host_resource(hostname: str) -> str:
            """Get tasks assigned to a specific host."""
            return get_tasks_for_host_resource(hostname)

        @mcp.resource("automation://tasks/mine")
        def my_tasks_resource() -> str:
            """Get tasks assigned to the current host."""
            return get_my_tasks_resource()

        @mcp.resource("automation://handoff/latest")
        def handoff_latest_resource() -> str:
            """Get the most recent session handoff note."""
            return get_latest_handoff_resource()

        logger.info("✅ Registered 7 assignee/handoff resources")

    except Exception as e:
        logger.warning(f"Could not register assignee resources: {e}")


__all__ = [
    "get_all_assignees_resource",
    "get_workload_resource",
    "get_tasks_for_assignee_resource",
    "get_unassigned_tasks_resource",
    "get_tasks_for_host_resource",
    "get_my_tasks_resource",
    "get_latest_handoff_resource",
    "register_assignee_resources",
]

