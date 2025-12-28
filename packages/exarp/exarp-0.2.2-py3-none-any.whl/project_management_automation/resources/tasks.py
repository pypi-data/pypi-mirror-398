"""
MCP Resource Handler for Todo2 Tasks

Provides resource access to cached Todo2 task lists, filtered by agent, status, etc.
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from ..utils import (
    find_project_root,
    filter_tasks_by_project,
    get_current_project_id,
    task_belongs_to_project,
)
from ..utils.json_cache import JsonCacheManager

logger = logging.getLogger(__name__)

# Cache manager for Todo2 state
_cache_manager = JsonCacheManager.get_instance()


def _load_todo2_state() -> dict[str, Any]:
    """Load Todo2 state file with caching based on file modification time."""
    project_root = find_project_root()
    todo2_file = project_root / '.todo2' / 'state.todo2.json'

    # Use unified JSON cache utility
    cache = _cache_manager.get_cache(todo2_file, enable_stats=True)
    
    try:
        data = cache.get_or_load()
        # Ensure we always return a dict with 'todos' key
        if not isinstance(data, dict):
            return {"todos": []}
        if "todos" not in data:
            return {"todos": [], **data}
        return data
    except Exception as e:
        logger.error(f"Error loading Todo2 state: {e}")
        return {"todos": [], "error": str(e)}


def _get_agent_names() -> list[str]:
    """Get list of agent names from cursor-agent.json files."""
    project_root = find_project_root()
    agents_dir = project_root / 'agents'

    agent_names = []
    if agents_dir.exists():
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                cursor_agent_file = agent_dir / 'cursor-agent.json'
                if cursor_agent_file.exists():
                    try:
                        with open(cursor_agent_file) as f:
                            config = json.load(f)
                            agent_name = config.get('name', agent_dir.name)
                            agent_names.append(agent_name)
                    except Exception as e:
                        logger.warning(f"Error reading {cursor_agent_file}: {e}")

    return sorted(agent_names)


def _filter_tasks_by_agent(tasks: list[dict[str, Any]], agent_name: str) -> list[dict[str, Any]]:
    """Filter tasks by agent name (checks name, description, tags)."""
    agent_lower = agent_name.lower()
    filtered = []

    for task in tasks:
        name = task.get('name', '').lower()
        desc = task.get('long_description', '').lower()
        tags = [tag.lower() for tag in task.get('tags', [])]

        # Check if agent name appears in task name, description, or tags
        if (agent_lower in name or
            agent_lower in desc or
            agent_lower in tags or
            f"{agent_lower}-agent" in name or
            f"{agent_lower}-agent" in desc):
            filtered.append(task)

    return filtered


def get_tasks_resource(agent: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> str:
    """
    Get Todo2 tasks as resource, optionally filtered by agent or status.

    Args:
        agent: Optional agent name to filter by
        status: Optional status to filter by (Todo, In Progress, Review, Done, etc.)
        limit: Maximum number of tasks to return

    Returns:
        JSON string with filtered task list
    """
    try:
        state = _load_todo2_state()
        all_tasks = state.get('todos', [])
        
        # Get current project ID and filter tasks
        project_id = get_current_project_id()
        cross_project_tasks = []
        
        # Filter by project ownership (include unassigned tasks)
        tasks = filter_tasks_by_project(all_tasks, project_id, include_unassigned=True, logger=logger)
        
        # Identify cross-project tasks for warnings
        if project_id:
            for task in all_tasks:
                task_project = task.get('project_id')
                if task_project and task_project != project_id:
                    cross_project_tasks.append({
                        'id': task.get('id'),
                        'name': task.get('name', '')[:50],
                        'project_id': task_project
                    })

        # Apply filters
        if agent:
            tasks = _filter_tasks_by_agent(tasks, agent)

        if status:
            tasks = [t for t in tasks if t.get('status', '').lower() == status.lower()]

        # Limit results
        tasks = tasks[:limit]

        # Count by status (only current project tasks)
        status_counts = {}
        for task in tasks:
            task_status = task.get('status', 'Unknown')
            status_counts[task_status] = status_counts.get(task_status, 0) + 1

        result = {
            "tasks": tasks,
            "total_tasks": len(tasks),
            "total_in_state": len(all_tasks),
            "project_id": project_id,
            "cross_project_tasks_count": len(cross_project_tasks),
            "cross_project_tasks": cross_project_tasks[:5] if cross_project_tasks else [],  # Show first 5
            "filters": {
                "agent": agent,
                "status": status,
                "limit": limit
            },
            "status_counts": status_counts,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add warning if cross-project tasks found
        if cross_project_tasks:
            result["warnings"] = [
                f"Found {len(cross_project_tasks)} task(s) from other projects. "
                f"These are excluded from results but shown in cross_project_tasks."
            ]

        return json.dumps(result, separators=(',', ':'))

    except Exception as e:
        logger.error(f"Error getting tasks resource: {e}")
        return json.dumps({
            "tasks": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, separators=(',', ':'))


def get_agent_tasks_resource(agent_name: str, status: Optional[str] = None, limit: int = 50) -> str:
    """
    Get tasks for a specific agent.

    Args:
        agent_name: Agent name (e.g., 'backend-agent', 'web-agent')
        status: Optional status filter
        limit: Maximum number of tasks to return

    Returns:
        JSON string with agent's tasks
    """
    return get_tasks_resource(agent=agent_name, status=status, limit=limit)


def get_agents_resource() -> str:
    """
    Get list of available agents with their configurations.

    Returns:
        JSON string with agent list and metadata
    """
    try:
        project_root = find_project_root()
        agents_dir = project_root / 'agents'

        agents = []
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir():
                    cursor_agent_file = agent_dir / 'cursor-agent.json'
                    if cursor_agent_file.exists():
                        try:
                            with open(cursor_agent_file) as f:
                                config = json.load(f)
                                agent_info = {
                                    "name": config.get('name', agent_dir.name),
                                    "directory": str(agent_dir.relative_to(project_root)),
                                    "working_directory": config.get('workingDirectory', ''),
                                    "env": config.get('env', {}),
                                    "startup_commands": config.get('startupCommands', []),
                                    "runtime_commands": config.get('runtimeCommands', [])
                                }
                                agents.append(agent_info)
                        except Exception as e:
                            logger.warning(f"Error reading {cursor_agent_file}: {e}")

        # Get task counts per agent
        state = _load_todo2_state()
        all_tasks = state.get('todos', [])

        agent_task_counts = {}
        for agent_info in agents:
            agent_name = agent_info['name']
            agent_tasks = _filter_tasks_by_agent(all_tasks, agent_name)
            agent_task_counts[agent_name] = len(agent_tasks)

        result = {
            "agents": agents,
            "total_agents": len(agents),
            "task_counts": agent_task_counts,
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(result, separators=(',', ':'))

    except Exception as e:
        logger.error(f"Error getting agents resource: {e}")
        return json.dumps({
            "agents": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
