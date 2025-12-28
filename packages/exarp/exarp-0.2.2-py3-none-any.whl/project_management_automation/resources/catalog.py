"""
MCP Resource Handlers for Static Catalog Data

Converts list_* tools to browsable MCP resources.
These are read-only, static/semi-static data that don't require tool invocation.

Resources:
- automation://advisors - List of trusted advisors
- automation://models - Available AI models
- automation://problem-categories - Problem categories with hints
- automation://tools - Available MCP tools
- automation://linters - Linter availability status
- automation://tts-backends - TTS backend status
- automation://status - Server status
"""

import json
import logging

logger = logging.getLogger(__name__)


def get_advisors_resource() -> str:
    """
    Resource: automation://advisors
    
    DEPRECATED: This resource has been migrated to devwisdom-go MCP server.
    Use devwisdom MCP server resources (wisdom://advisors) directly instead.
    
    Returns list of trusted advisors with their assignments.
    
    This function now reads from devwisdom-go MCP server via wisdom_client.
    """
    try:
        from ..utils.wisdom_client import read_wisdom_resource_sync
        from ..utils.project_root import find_project_root
        
        # Try to get advisors from devwisdom-go MCP server
        project_root = find_project_root()
        advisors_json = read_wisdom_resource_sync("wisdom://advisors", project_root)
        
        if advisors_json:
            return advisors_json
        
        # Fallback: return error message
        import json
        return json.dumps({
            "error": "devwisdom-go MCP server not available",
            "message": "Please configure devwisdom MCP server in .cursor/mcp.json",
            "migration_note": "Use wisdom://advisors resource from devwisdom-go MCP server"
        }, indent=2)
    except Exception as e:
        # Fallback to old implementation if MCP client unavailable
        try:
            from ..tools.wisdom.advisors import (
                METRIC_ADVISORS,
                STAGE_ADVISORS,
                TOOL_ADVISORS,
            )

            advisors = {
                "description": "Trusted Advisors for EXARP Project Management",
                "by_metric": {
                    metric: {
                        "advisor": info["advisor"],
                        "icon": info.get("icon", "📚"),
                        "rationale": info["rationale"],
                        "helps_with": info.get("helps_with", ""),
                    }
                    for metric, info in METRIC_ADVISORS.items()
                },
                "by_tool": {
                    tool: {
                        "advisor": info["advisor"],
                        "rationale": info["rationale"],
                    }
                    for tool, info in TOOL_ADVISORS.items()
                },
                "by_stage": {
                    stage: {
                        "advisor": info["advisor"],
                        "rationale": info["rationale"],
                    }
                    for stage, info in STAGE_ADVISORS.items()
                },
                "total_advisors": len(set(
                    [v["advisor"] for v in METRIC_ADVISORS.values()] +
                    [v["advisor"] for v in TOOL_ADVISORS.values()] +
                    [v["advisor"] for v in STAGE_ADVISORS.values()]
                )),
            }

            import json
            return json.dumps(advisors, separators=(',', ':'))

        except ImportError as e:
            logger.error(f"Failed to load advisors: {e}")
            import json
            return json.dumps({"error": "Advisors not available"})


def get_models_resource() -> str:
    """
    Resource: automation://models

    Returns available AI models with recommendations.
    """
    try:
        from ..tools.model_recommender import MODEL_RECOMMENDATIONS

        models = {
            "description": "Available AI Models for Task Execution",
            "models": {
                model_id: {
                    "name": info["name"],
                    "best_for": info["best_for"],
                    "task_types": info["task_types"],
                    "cost": info["cost"],
                    "speed": info["speed"],
                }
                for model_id, info in MODEL_RECOMMENDATIONS.items()
            },
            "total_models": len(MODEL_RECOMMENDATIONS),
            "recommended_default": "claude-sonnet",
        }

        return json.dumps(models, separators=(',', ':'))

    except ImportError as e:
        logger.error(f"Failed to load models: {e}")
        return json.dumps({"error": "Models not available"})


def get_problem_categories_resource() -> str:
    """
    Resource: automation://problem-categories

    Returns problem categories with resolution hints.
    """
    try:
        from ..tools.problems_advisor import PROBLEM_HINTS

        categories = {}
        for hint in PROBLEM_HINTS:
            cat = hint.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "pattern": hint.pattern,
                "description": hint.description,
                "resolution": hint.resolution,
                "auto_fixable": hint.auto_fixable,
                "severity_weight": hint.severity_weight,
                "tools": hint.tools,
            })

        result = {
            "description": "Problem Categories with Resolution Hints",
            "categories": categories,
            "total_categories": len(categories),
            "total_hints": len(PROBLEM_HINTS),
        }

        return json.dumps(result, separators=(',', ':'))

    except ImportError as e:
        logger.error(f"Failed to load problem categories: {e}")
        return json.dumps({"error": "Problem categories not available"})


def get_tools_resource() -> str:
    """
    Resource: automation://tools

    Returns available MCP tools with metadata.
    """
    try:
        from ..tools.hint_catalog import TOOL_HINTS

        tools = {
            "description": "Available EXARP MCP Tools",
            "tools": [
                {
                    "tool": hint["tool"],
                    "hint": hint["hint"],
                    "category": hint["category"],
                    "description": hint.get("description", ""),
                    "recommended_model": hint.get("recommended_model", "claude-haiku"),
                }
                for hint in TOOL_HINTS
            ],
            "total_tools": len(TOOL_HINTS),
            "categories": list({h["category"] for h in TOOL_HINTS}),
        }

        return json.dumps(tools, separators=(',', ':'))

    except ImportError as e:
        logger.error(f"Failed to load tools: {e}")
        return json.dumps({"error": "Tools catalog not available"})


def get_linters_resource() -> str:
    """
    Resource: automation://linters

    Returns available linter status.
    """
    import subprocess

    linters = {}

    for linter in ['ruff', 'flake8', 'pylint', 'mypy', 'black']:
        try:
            result = subprocess.run(
                [linter, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                linters[linter] = {'available': True, 'version': version}
            else:
                linters[linter] = {'available': False}
        except FileNotFoundError:
            linters[linter] = {'available': False}
        except Exception as e:
            linters[linter] = {'available': False, 'error': str(e)}

    result = {
        "description": "Available Linters",
        "linters": linters,
        "recommended": next(
            (l for l in ['ruff', 'flake8', 'pylint'] if linters.get(l, {}).get('available')),
            None
        ),
    }

    return json.dumps(result, separators=(',', ':'))


def get_tts_backends_resource() -> str:
    """
    Resource: automation://tts-backends

    DEPRECATED: TTS/voice functionality migrated to devwisdom-go MCP server.
    This resource is kept for backward compatibility but returns an error.
    """
    return json.dumps({
        "description": "TTS backends migrated to devwisdom-go MCP server",
        "error": "TTS functionality has been migrated to devwisdom-go MCP server",
        "migration_note": "Use devwisdom MCP server for TTS/voice functionality",
        "backends": {},
        "recommended": None,
    }, separators=(',', ':'))


def get_server_status_resource() -> str:
    """
    Resource: automation://status

    Returns server status and version.
    """
    import time

    try:
        from ..utils import find_project_root
        project_root = find_project_root()

        # Get version from pyproject.toml if available
        version = "unknown"
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            import re
            content = pyproject.read_text()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version = match.group(1)

        result = {
            "description": "EXARP Server Status",
            "status": "running",
            "version": version,
            "project_root": str(project_root),
            "timestamp": time.time(),
            "features": {
                "ai_memory": True,
                "trusted_advisors": True,
                "tool_consolidation": "in_progress",
            },
        }

        return json.dumps(result, separators=(',', ':'))

    except Exception as e:
        logger.error(f"Failed to get server status: {e}")
        return json.dumps({
            "status": "running",
            "error": str(e),
        })

