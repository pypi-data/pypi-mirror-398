"""
Dynamic Resource Templates for Exarp MCP Server.

Provides parameterized resources for:
- Individual tasks by ID
- Project tasks
- Agent-specific tasks
- Advisor consultations

These use FastMCP resource templates for dynamic URIs.

Usage:
    @mcp.resource("tasks://{task_id}")
    async def get_task(task_id: str) -> dict:
        return load_task(task_id)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("exarp.resources.templates")


def _find_project_root() -> Path:
    """Find project root by looking for markers."""
    import os

    env_root = os.getenv("PROJECT_ROOT") or os.getenv("WORKSPACE_PATH")
    if env_root:
        return Path(env_root).resolve()

    current = Path.cwd()
    for _ in range(5):
        if (current / ".git").exists() or (current / ".todo2").exists() or (current / "CMakeLists.txt").exists() or (current / "go.mod").exists():
            return current.resolve()
        if current.parent == current:
            break
        current = current.parent

    return Path.cwd().resolve()


def _load_todo2_state() -> dict[str, Any]:
    """Load Todo2 state file."""
    project_root = _find_project_root()
    todo2_file = project_root / ".todo2" / "state.todo2.json"

    if not todo2_file.exists():
        return {"todos": []}

    try:
        return json.loads(todo2_file.read_text())
    except Exception as e:
        logger.error(f"Error loading Todo2 state: {e}")
        return {"todos": [], "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# TASK RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════

def get_task_by_id(task_id: str) -> dict[str, Any]:
    """
    Get a single task by ID.

    Resource URI: tasks://{task_id}

    Args:
        task_id: Task identifier (e.g., "T-SECURITY-1")

    Returns:
        Task data or error
    """
    state = _load_todo2_state()

    for task in state.get("todos", []):
        if task.get("id") == task_id:
            return {
                "task": task,
                "found": True,
                "timestamp": datetime.now().isoformat(),
            }

    return {
        "task": None,
        "found": False,
        "task_id": task_id,
        "error": f"Task not found: {task_id}",
        "timestamp": datetime.now().isoformat(),
    }


def get_tasks_by_status(status: str) -> dict[str, Any]:
    """
    Get tasks filtered by status.

    Resource URI: tasks://status/{status}

    Args:
        status: Task status (Todo, In Progress, Review, Done, etc.)

    Returns:
        Filtered task list
    """
    state = _load_todo2_state()

    status_lower = status.lower()
    tasks = [
        t for t in state.get("todos", [])
        if t.get("status", "").lower() == status_lower
    ]

    return {
        "tasks": tasks,
        "count": len(tasks),
        "status_filter": status,
        "timestamp": datetime.now().isoformat(),
    }


def get_tasks_by_tag(tag: str) -> dict[str, Any]:
    """
    Get tasks filtered by tag.

    Resource URI: tasks://tag/{tag}

    Args:
        tag: Tag to filter by

    Returns:
        Filtered task list
    """
    state = _load_todo2_state()

    tag_lower = tag.lower()
    tasks = [
        t for t in state.get("todos", [])
        if tag_lower in [tg.lower() for tg in t.get("tags", [])]
    ]

    return {
        "tasks": tasks,
        "count": len(tasks),
        "tag_filter": tag,
        "timestamp": datetime.now().isoformat(),
    }


def get_tasks_by_priority(priority: str) -> dict[str, Any]:
    """
    Get tasks filtered by priority.

    Resource URI: tasks://priority/{priority}

    Args:
        priority: Priority level (P0, P1, P2, P3, high, medium, low)

    Returns:
        Filtered task list
    """
    state = _load_todo2_state()

    priority_lower = priority.lower()
    tasks = [
        t for t in state.get("todos", [])
        if t.get("priority", "").lower() == priority_lower
    ]

    return {
        "tasks": tasks,
        "count": len(tasks),
        "priority_filter": priority,
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ADVISOR RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════

def get_advisor_consultations(days: int = 7) -> dict[str, Any]:
    """
    Get recent advisor consultations.

    Resource URI: advisor://consultations/{days}

    Args:
        days: Number of days to look back

    Returns:
        Recent consultations
    """
    from datetime import timedelta

    project_root = _find_project_root()
    log_dir = project_root / ".exarp" / "advisor_logs"

    if not log_dir.exists():
        return {
            "consultations": [],
            "count": 0,
            "days": days,
            "timestamp": datetime.now().isoformat(),
        }

    cutoff = datetime.now() - timedelta(days=days)
    consultations = []

    try:
        for log_file in sorted(log_dir.glob("*.jsonl"), reverse=True):
            # Check file date from name
            try:
                file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
                if file_date < cutoff:
                    continue
            except ValueError:
                continue

            # Read consultations
            for line in log_file.read_text().strip().split("\n"):
                if line:
                    try:
                        consultations.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"Error reading advisor logs: {e}")

    return {
        "consultations": consultations,
        "count": len(consultations),
        "days": days,
        "timestamp": datetime.now().isoformat(),
    }


def get_advisor_info(advisor_id: str) -> dict[str, Any]:
    """
    Get information about a specific advisor.

    Resource URI: advisor://{advisor_id}

    Args:
        advisor_id: Advisor identifier (bofh, stoic, zen, mystic, sage, etc.)

    Returns:
        Advisor information
    """
    try:
        # Try to use devwisdom-go MCP server first
        from ..utils.wisdom_client import read_wisdom_resource_sync
        from ..utils.project_root import find_project_root
        
        project_root = find_project_root()
        advisors_json = read_wisdom_resource_sync("wisdom://advisors", project_root)
        sources_json = read_wisdom_resource_sync("wisdom://sources", project_root)
        
        if advisors_json and sources_json:
            import json
            advisors_data = json.loads(advisors_json) if isinstance(advisors_json, str) else advisors_json
            sources_data = json.loads(sources_json) if isinstance(sources_json, str) else sources_json
            
            # Extract advisor mappings from JSON
            METRIC_ADVISORS = advisors_data.get("by_metric", {})
            TOOL_ADVISORS = advisors_data.get("by_tool", {})
            STAGE_ADVISORS = advisors_data.get("by_stage", {})
            WISDOM_SOURCES = {item.get("id", ""): item for item in sources_data} if isinstance(sources_data, list) else sources_data
        else:
            # Fallback to old implementation
            from ..tools.wisdom.advisors import METRIC_ADVISORS, STAGE_ADVISORS, TOOL_ADVISORS
            from ..tools.wisdom.sources import WISDOM_SOURCES
    except Exception:
        # Fallback to old implementation if MCP client unavailable
        from ..tools.wisdom.advisors import METRIC_ADVISORS, STAGE_ADVISORS, TOOL_ADVISORS
        from ..tools.wisdom.sources import WISDOM_SOURCES

        # Find advisor info
        advisor_info = WISDOM_SOURCES.get(advisor_id)

        if not advisor_info:
            return {
                "advisor": None,
                "found": False,
                "advisor_id": advisor_id,
                "error": f"Advisor not found: {advisor_id}",
            }

        # Find what this advisor is assigned to
        assigned_to = {
            "metrics": [k for k, v in METRIC_ADVISORS.items() if v == advisor_id],
            "tools": [k for k, v in TOOL_ADVISORS.items() if v == advisor_id],
            "stages": [k for k, v in STAGE_ADVISORS.items() if v == advisor_id],
        }

        return {
            "advisor": {
                "id": advisor_id,
                "name": advisor_info.get("name", advisor_id),
                "description": advisor_info.get("description", ""),
                "quote_count": len(advisor_info.get("quotes", [])),
            },
            "assigned_to": assigned_to,
            "found": True,
            "timestamp": datetime.now().isoformat(),
        }

    except ImportError as e:
        return {
            "advisor": None,
            "found": False,
            "error": f"Advisor system not available: {e}",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY RESOURCES
# ═══════════════════════════════════════════════════════════════════════════════

def get_memory_by_id(memory_id: str) -> dict[str, Any]:
    """
    Get a specific memory by ID.

    Resource URI: memory://{memory_id}

    Args:
        memory_id: Memory identifier

    Returns:
        Memory data or error
    """
    project_root = _find_project_root()
    memory_dir = project_root / ".exarp" / "memories"

    if not memory_dir.exists():
        return {
            "memory": None,
            "found": False,
            "error": "Memory storage not initialized",
        }

    # Search for memory file
    for memory_file in memory_dir.glob("*.json"):
        try:
            data = json.loads(memory_file.read_text())
            if data.get("id") == memory_id:
                return {
                    "memory": data,
                    "found": True,
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception:
            continue

    return {
        "memory": None,
        "found": False,
        "memory_id": memory_id,
        "error": f"Memory not found: {memory_id}",
        "timestamp": datetime.now().isoformat(),
    }


def get_memories_by_category(category: str) -> dict[str, Any]:
    """
    Get memories filtered by category.

    Resource URI: memory://category/{category}

    Args:
        category: Memory category (debug, research, architecture, preference, insight)

    Returns:
        Filtered memory list
    """
    project_root = _find_project_root()
    memory_dir = project_root / ".exarp" / "memories"

    if not memory_dir.exists():
        return {
            "memories": [],
            "count": 0,
            "category": category,
        }

    memories = []
    category_lower = category.lower()

    for memory_file in memory_dir.glob("*.json"):
        try:
            data = json.loads(memory_file.read_text())
            if data.get("category", "").lower() == category_lower:
                memories.append(data)
        except Exception:
            continue

    return {
        "memories": memories,
        "count": len(memories),
        "category": category,
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def register_resource_templates(mcp) -> None:
    """
    Register all resource templates with the MCP server.

    Usage:
        from project_management_automation.resources.templates import register_resource_templates
        register_resource_templates(mcp)
    """
    try:
        # Task resources
        @mcp.resource("tasks://{task_id}")
        def task_resource(task_id: str) -> str:
            """Get a task by ID."""
            result = get_task_by_id(task_id)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        @mcp.resource("tasks://status/{status}")
        def tasks_by_status_resource(status: str) -> str:
            """Get tasks by status."""
            result = get_tasks_by_status(status)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        @mcp.resource("tasks://tag/{tag}")
        def tasks_by_tag_resource(tag: str) -> str:
            """Get tasks by tag."""
            result = get_tasks_by_tag(tag)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        @mcp.resource("tasks://priority/{priority}")
        def tasks_by_priority_resource(priority: str) -> str:
            """Get tasks by priority."""
            result = get_tasks_by_priority(priority)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        # Advisor resources
        @mcp.resource("advisor://{advisor_id}")
        def advisor_resource(advisor_id: str) -> str:
            """Get advisor information."""
            result = get_advisor_info(advisor_id)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        @mcp.resource("advisor://consultations/{days}")
        def consultations_resource(days: str) -> str:
            """Get recent consultations."""
            result = get_advisor_consultations(int(days) if days.isdigit() else 7)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        # Memory resources
        @mcp.resource("memory://{memory_id}")
        def memory_resource(memory_id: str) -> str:
            """Get a memory by ID."""
            result = get_memory_by_id(memory_id)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        @mcp.resource("memory://category/{category}")
        def memories_by_category_resource(category: str) -> str:
            """Get memories by category."""
            result = get_memories_by_category(category)
            # Ensure we always return a JSON string
            if isinstance(result, dict):
                return json.dumps(result, separators=(',', ':'))
            return json.dumps({"result": str(result)}, separators=(',', ':'))

        logger.info("✅ Registered 8 resource templates")

    except Exception as e:
        logger.warning(f"Could not register resource templates: {e}")


__all__ = [
    # Task resources
    "get_task_by_id",
    "get_tasks_by_status",
    "get_tasks_by_tag",
    "get_tasks_by_priority",
    # Advisor resources
    "get_advisor_consultations",
    "get_advisor_info",
    # Memory resources
    "get_memory_by_id",
    "get_memories_by_category",
    # Registration
    "register_resource_templates",
]

