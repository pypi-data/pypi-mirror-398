"""
Unified Context Primer Resource for Exarp MCP Server.

Provides a single resource that returns all essential context for AI priming:
- Current workflow mode and visible tools
- Project goals keywords for alignment
- Centralized tool hints (aggregated from all tools)
- Recent task summary
- Relevant prompts for current mode

This eliminates the need to read multiple files to prime AI context.

Usage:
    Resource URI: automation://context-primer
    
    Returns compact JSON with all priming data in one request.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("exarp.resources.context_primer")


def _find_project_root() -> Path:
    """Find project root by looking for markers."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# CENTRALIZED HINT REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

# All tool hints aggregated in one place for quick AI understanding
# Format: [HINT: Brief description. Key outputs.]
TOOL_HINTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Project Health
    "server_status": {
        "hint": "Server status. Version, uptime, tools count.",
        "category": "health",
        "outputs": ["version", "status", "tools_available"],
    },
    "project_scorecard": {
        "hint": "Scorecard. Overall score 0-100, component scores, production readiness.",
        "category": "health",
        "outputs": ["overall_score", "component_scores", "production_ready"],
    },
    "project_overview": {
        "hint": "Overview. One-page summary with scores, metrics, tasks, risks.",
        "category": "health",
        "outputs": ["health_score", "task_summary", "risks", "next_actions"],
    },
    "check_documentation_health": {
        "hint": "Docs health. Score 0-100, broken links count, tasks created.",
        "category": "documentation",
        "outputs": ["health_score", "broken_links", "tasks_created"],
    },
    "check_working_copy_health": {
        "hint": "Git health. Uncommitted changes, sync status across agents.",
        "category": "health",
        "outputs": ["agents_status", "uncommitted_files", "recommendations"],
    },

    # Task Management
    "analyze_todo2_alignment": {
        "hint": "Task alignment. Misaligned count, avg score, follow-up tasks.",
        "category": "tasks",
        "outputs": ["misaligned_count", "average_score", "followup_tasks"],
    },
    "detect_duplicate_tasks": {
        "hint": "Duplicate detection. Duplicate count, groups, auto_fix available.",
        "category": "tasks",
        "outputs": ["duplicate_count", "groups", "recommendations"],
    },
    "sync_todo_tasks": {
        "hint": "Task sync. Matches found, conflicts, new tasks created.",
        "category": "tasks",
        "outputs": ["matches", "conflicts", "tasks_created"],
    },
    "batch_approve_tasks": {
        "hint": "Batch approve. Tasks approved count, status transitions.",
        "category": "tasks",
        "outputs": ["approved_count", "task_ids", "dry_run"],
    },
    "resolve_task_clarification": {
        "hint": "Clarification resolver. Task updated, moved to todo status.",
        "category": "tasks",
        "outputs": ["task_id", "moved_to_todo", "status"],
    },
    "list_tasks_awaiting_clarification": {
        "hint": "Pending clarifications. Tasks in Review needing input.",
        "category": "tasks",
        "outputs": ["total_tasks", "tasks_list"],
    },

    # Security
    "scan_dependency_security": {
        "hint": "Security scan. Vuln count by severity, language breakdown, remediation.",
        "category": "security",
        "outputs": ["total_vulns", "by_severity", "remediation"],
    },
    "fetch_dependabot_alerts": {
        "hint": "Dependabot alerts. GitHub security alerts, severity breakdown.",
        "category": "security",
        "outputs": ["alerts", "by_severity", "affected_packages"],
    },
    "generate_security_report": {
        "hint": "Security report. Combined scan + alerts, recommendations.",
        "category": "security",
        "outputs": ["total_issues", "critical_count", "recommendations"],
    },

    # Automation
    "run_daily_automation": {
        "hint": "Daily automation. Docs, alignment, duplicates, security checks.",
        "category": "automation",
        "outputs": ["checks_run", "issues_found", "tasks_created"],
    },
    "run_nightly_task_automation": {
        "hint": "Nightly automation. Background tasks executed, parallel across hosts.",
        "category": "automation",
        "outputs": ["tasks_assigned", "hosts_used", "batch_approved"],
    },
    "find_automation_opportunities": {
        "hint": "Automation discovery. Opportunity count, value scores, recommendations.",
        "category": "automation",
        "outputs": ["opportunities", "high_value_count", "recommendations"],
    },
    "setup_git_hooks": {
        "hint": "Git hooks. Pre-commit, pre-push hooks configured.",
        "category": "automation",
        "outputs": ["hooks_installed", "triggers_configured"],
    },
    "setup_pattern_triggers": {
        "hint": "Pattern triggers. File/git/task pattern automation configured.",
        "category": "automation",
        "outputs": ["patterns_configured", "actions_defined"],
    },

    # Testing
    "run_tests": {
        "hint": "Test runner. pytest/unittest, pass/fail counts, coverage.",
        "category": "testing",
        "outputs": ["passed", "failed", "coverage_percent"],
    },
    "analyze_test_coverage": {
        "hint": "Coverage analysis. Coverage %, gap analysis, recommendations.",
        "category": "testing",
        "outputs": ["coverage_percent", "uncovered_files", "recommendations"],
    },
    "check_definition_of_done": {
        "hint": "DoD check. Validates task completion criteria checklist.",
        "category": "testing",
        "outputs": ["checklist_status", "pass_fail_counts", "ready_for_review"],
    },

    # Configuration
    "generate_cursor_rules": {
        "hint": "Cursor rules. Generates .mdc rules from project analysis.",
        "category": "config",
        "outputs": ["rules_generated", "languages_detected"],
    },
    "generate_cursorignore": {
        "hint": "Cursorignore. Generates ignore files for AI context optimization.",
        "category": "config",
        "outputs": ["patterns_detected", "files_created"],
    },
    "simplify_rules": {
        "hint": "Rules simplifier. Removes redundancy from rule files.",
        "category": "config",
        "outputs": ["files_simplified", "reduction_percent"],
    },
    # PRD & Planning
    "generate_prd": {
        "hint": "PRD generation. Creates Product Requirements Document from codebase.",
        "category": "planning",
        "outputs": ["prd_path", "user_stories", "features"],
    },
    "analyze_prd_alignment": {
        "hint": "PRD alignment. Task-to-persona mapping, advisor assignments.",
        "category": "planning",
        "outputs": ["persona_coverage", "unaligned_tasks", "recommendations"],
    },

    # Workflow
    "focus_mode": {
        "hint": "Focus mode. Switch workflow modes, reduce visible tools 50-80%.",
        "category": "workflow",
        "outputs": ["current_mode", "visible_tools", "reduction_percent"],
    },
    "suggest_mode": {
        "hint": "Mode suggestion. Infers optimal mode from text or usage patterns.",
        "category": "workflow",
        "outputs": ["suggested_mode", "confidence", "rationale"],
    },
    "recommend_workflow_mode": {
        "hint": "Workflow mode. AGENT vs ASK recommendation.",
        "category": "workflow",
        "outputs": ["recommended_mode", "confidence", "reason"],
    },
    "recommend_model": {
        "hint": "Model selection. Optimal AI model for task type.",
        "category": "workflow",
        "outputs": ["recommended_model", "confidence", "alternatives"],
    },

    # Advisors
    "consult_advisor": {
        "hint": "Advisor consultation. Wisdom from trusted advisors by metric/stage.",
        "category": "advisors",
        "outputs": ["advisor", "quote", "guidance"],
    },
    "get_morning_briefing": {
        "hint": "Morning briefing. Score-based wisdom from advisors.",
        "category": "advisors",
        "outputs": ["focus_metrics", "guidance", "advisor_quotes"],
    },
    "list_advisors": {
        "hint": "Advisor list. All trusted advisors with assignments.",
        "category": "advisors",
        "outputs": ["advisors", "by_metric", "by_stage"],
    },

    # Memory
    "save_memory": {
        "hint": "Save memory. Persist insight to AI session memory.",
        "category": "memory",
        "outputs": ["memory_id", "category", "timestamp"],
    },
    "recall_memory": {
        "hint": "Recall memory. Get context for a task from session memory.",
        "category": "memory",
        "outputs": ["memories", "relevance_scores"],
    },
    "search_memories": {
        "hint": "Search memories. Find past insights by query.",
        "category": "memory",
        "outputs": ["results", "match_count"],
    },

    # Session Handoff (Multi-Dev Coordination)
    "session_handoff": {
        "hint": "Session handoff. End/resume sessions for multi-dev coordination. Actions: end, resume, latest, list.",
        "category": "coordination",
        "outputs": ["handoff_id", "blockers", "next_steps", "available_work"],
    },
    "task_assignee": {
        "hint": "Task assignee. Manage task assignments across agents/humans/hosts. Actions: assign, unassign, list, workload, auto_assign.",
        "category": "coordination",
        "outputs": ["assignee", "workload_summary", "unassigned_count"],
    },

    # Context Management
    "summarize_context": {
        "hint": "Context summarizer. Compresses verbose outputs to key metrics.",
        "category": "context",
        "outputs": ["summary", "token_reduction_percent"],
    },
    "estimate_context_budget": {
        "hint": "Context budget. Estimates tokens and suggests what to keep/summarize.",
        "category": "context",
        "outputs": ["total_tokens", "over_budget", "strategy"],
    },
    "list_tools": {
        "hint": "Tool catalog. Lists all tools with rich descriptions and examples.",
        "category": "tool_catalog",
        "outputs": ["tools", "categories", "count"],
    },
    "get_tool_help": {
        "hint": "Tool help. Detailed help for a specific tool with examples.",
        "category": "tool_catalog",
        "outputs": ["tool_info", "examples", "related_tools"],
    },
}


# Workflow modes with their tool groups and relevant prompts
WORKFLOW_MODE_CONTEXT: Dict[str, Dict[str, Any]] = {
    "daily_checkin": {
        "description": "Quick health check for start of day - includes handoff review",
        "tool_groups": ["core", "tool_catalog", "health", "coordination"],
        "prompts": ["daily_checkin", "project_scorecard", "advisor_consult", "resume_session"],
        "keywords": ["daily", "morning", "status", "health", "overview", "handoff"],
    },
    "security_review": {
        "description": "Security audits and dependency scanning",
        "tool_groups": ["core", "tool_catalog", "security", "health"],
        "prompts": ["security_scan_all", "security_scan_python", "security_scan_rust"],
        "keywords": ["security", "vulnerability", "cve", "scan", "audit"],
    },
    "task_management": {
        "description": "Sprint backlog grooming and task management",
        "tool_groups": ["core", "tool_catalog", "tasks", "coordination"],
        "prompts": ["task_alignment", "duplicate_cleanup", "task_sync", "task_discovery", "end_of_day"],
        "keywords": ["task", "backlog", "sprint", "duplicate", "alignment", "assign"],
    },
    "code_review": {
        "description": "PR reviews and code quality checks",
        "tool_groups": ["core", "tool_catalog", "testing", "health"],
        "prompts": ["project_health", "persona_code_reviewer"],
        "keywords": ["review", "pr", "test", "coverage", "quality"],
    },
    "sprint_planning": {
        "description": "Sprint planning and roadmap work",
        "tool_groups": ["core", "tool_catalog", "tasks", "automation", "prd", "coordination"],
        "prompts": ["sprint_start", "sprint_end", "pre_sprint_cleanup", "automation_setup", "end_of_day"],
        "keywords": ["sprint", "planning", "roadmap", "prd", "automation", "handoff"],
    },
    "debugging": {
        "description": "Bug fixing and investigation",
        "tool_groups": ["core", "tool_catalog", "memory", "testing", "health"],
        "prompts": ["memory_system", "persona_developer"],
        "keywords": ["debug", "bug", "fix", "error", "investigate"],
    },
    "development": {
        "description": "General development work (default) - includes coordination tools",
        "tool_groups": ["core", "tool_catalog", "health", "tasks", "testing", "memory", "coordination"],
        "prompts": ["persona_developer", "mode_suggestion", "context_management", "end_of_day", "resume_session"],
        "keywords": ["develop", "implement", "build", "feature", "code", "handoff"],
    },
}


def _load_project_goals() -> Dict[str, Any]:
    """Load project goals keywords for alignment context."""
    project_root = _find_project_root()
    goals_file = project_root / "PROJECT_GOALS.md"

    if not goals_file.exists():
        return {"phases": [], "keywords": [], "error": "PROJECT_GOALS.md not found"}

    try:
        content = goals_file.read_text()

        # Extract phases and keywords
        phases = []
        all_keywords = []

        import re
        phase_pattern = r"### Phase \d+: (.+?)\n.*?\*\*Keywords\*\*: (.+?)(?:\n|$)"
        matches = re.findall(phase_pattern, content, re.DOTALL)

        for name, keywords in matches:
            phase_keywords = [k.strip() for k in keywords.split(",")]
            phases.append({
                "name": name.strip(),
                "keywords": phase_keywords[:10],  # Limit for context efficiency
            })
            all_keywords.extend(phase_keywords)

        return {
            "phases": phases,
            "keywords": list(set(all_keywords))[:30],  # Deduplicated, limited
        }
    except Exception as e:
        logger.error(f"Error loading project goals: {e}")
        return {"phases": [], "keywords": [], "error": str(e)}


def _load_recent_tasks(limit: int = 10) -> Dict[str, Any]:
    """Load recent task summary for context."""
    project_root = _find_project_root()
    todo2_file = project_root / ".todo2" / "state.todo2.json"

    if not todo2_file.exists():
        return {"summary": {}, "recent": [], "error": "Todo2 state not found"}

    try:
        state = json.loads(todo2_file.read_text())
        todos = state.get("todos", [])

        # Count by status
        status_counts = {}
        for todo in todos:
            status = todo.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Get recent (by modified date, limited)
        sorted_todos = sorted(
            todos,
            key=lambda t: t.get("lastModified", ""),
            reverse=True
        )[:limit]

        recent = [
            {
                "id": t.get("id"),
                "name": t.get("name", "")[:50],  # Truncate for context
                "status": t.get("status"),
                "priority": t.get("priority"),
            }
            for t in sorted_todos
        ]

        return {
            "summary": status_counts,
            "total": len(todos),
            "recent": recent,
        }
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return {"summary": {}, "recent": [], "error": str(e)}


def _get_current_workflow_mode() -> Dict[str, Any]:
    """Get current workflow mode from dynamic tool manager."""
    try:
        from ..tools.dynamic_tools import get_dynamic_tool_manager
        manager = get_dynamic_tool_manager()

        mode = manager.current_mode.value
        visible_tools = manager.get_visible_tool_count()
        total_tools = manager.get_total_tool_count()
        reduction = round((1 - visible_tools / max(total_tools, 1)) * 100, 1)

        return {
            "mode": mode,
            "visible_tools": visible_tools,
            "total_tools": total_tools,
            "reduction_percent": reduction,
            "mode_context": WORKFLOW_MODE_CONTEXT.get(mode, {}),
        }
    except Exception as e:
        logger.debug(f"Could not get workflow mode: {e}")
        return {
            "mode": "development",
            "visible_tools": len(TOOL_HINTS_REGISTRY),
            "total_tools": len(TOOL_HINTS_REGISTRY),
            "reduction_percent": 0,
            "mode_context": WORKFLOW_MODE_CONTEXT.get("development", {}),
        }


def get_context_primer(
    mode: Optional[str] = None,
    include_hints: bool = True,
    include_tasks: bool = True,
    include_goals: bool = True,
    include_prompts: bool = True,
) -> str:
    """
    Resource: automation://context-primer
    
    Returns unified context primer for AI in a single compact response.
    
    This is the primary resource for priming AI context efficiently.
    Instead of reading multiple files, get everything needed in one request.
    
    Args:
        mode: Workflow mode to focus on (auto-detected if not provided)
        include_hints: Include tool hints for current mode
        include_tasks: Include recent task summary
        include_goals: Include project goals keywords
        include_prompts: Include relevant prompts for mode
    
    Returns:
        JSON with all context priming data
    """
    result: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "description": "Unified context primer for AI assistance",
    }

    # 1. Current workflow mode
    workflow = _get_current_workflow_mode()
    if mode:
        workflow["mode"] = mode
        workflow["mode_context"] = WORKFLOW_MODE_CONTEXT.get(mode, {})
    result["workflow"] = workflow

    # 2. Tool hints (filtered by mode if applicable)
    if include_hints:
        mode_context = workflow.get("mode_context", {})
        tool_groups = mode_context.get("tool_groups", [])

        if tool_groups:
            # Filter hints by category
            filtered_hints = {
                name: data for name, data in TOOL_HINTS_REGISTRY.items()
                if data.get("category") in tool_groups or "core" in tool_groups
            }
        else:
            filtered_hints = TOOL_HINTS_REGISTRY

        # Return compact hint format
        result["hints"] = {
            name: data["hint"] for name, data in filtered_hints.items()
        }
        result["hints_count"] = len(filtered_hints)

    # 3. Project goals keywords
    if include_goals:
        goals = _load_project_goals()
        result["project_goals"] = {
            "phases": [p["name"] for p in goals.get("phases", [])],
            "keywords": goals.get("keywords", [])[:20],  # Top 20 keywords
        }

    # 4. Recent task summary
    if include_tasks:
        tasks = _load_recent_tasks(limit=5)
        result["tasks"] = {
            "summary": tasks.get("summary", {}),
            "total": tasks.get("total", 0),
            "recent_ids": [t["id"] for t in tasks.get("recent", [])],
        }

    # 5. Relevant prompts for mode
    if include_prompts:
        mode_context = workflow.get("mode_context", {})
        relevant_prompts = mode_context.get("prompts", [])
        result["prompts"] = {
            "recommended": relevant_prompts[:5],
            "all_modes": list(WORKFLOW_MODE_CONTEXT.keys()),
        }

    # 6. Tool count health (design constraint: ≤30 tools)
    try:
        from ..tools.tool_count_health import get_tool_count_for_context_primer
        tool_health = get_tool_count_for_context_primer()
        result["tool_health"] = tool_health

        # Add warning if over limit
        if tool_health.get("status") == "over_limit":
            result["warnings"] = result.get("warnings", [])
            result["warnings"].append(
                f"⚠️ Tool count ({tool_health['tool_count']}) exceeds limit ({tool_health['limit']}). "
                "Consider consolidating tools."
            )
    except Exception as e:
        logger.debug(f"Could not get tool count health: {e}")

    return json.dumps(result, separators=(',', ':'))


def get_hints_for_mode(mode: str) -> str:
    """
    Resource: automation://hints/{mode}
    
    Returns tool hints filtered by workflow mode.
    
    Args:
        mode: Workflow mode (daily_checkin, security_review, task_management, etc.)
    
    Returns:
        JSON with filtered tool hints
    """
    mode_context = WORKFLOW_MODE_CONTEXT.get(mode, WORKFLOW_MODE_CONTEXT["development"])
    tool_groups = mode_context.get("tool_groups", [])

    filtered_hints = {}
    for name, data in TOOL_HINTS_REGISTRY.items():
        if data.get("category") in tool_groups or not tool_groups:
            filtered_hints[name] = {
                "hint": data["hint"],
                "category": data["category"],
                "outputs": data.get("outputs", []),
            }

    return json.dumps({
        "mode": mode,
        "description": mode_context.get("description", ""),
        "hints": filtered_hints,
        "count": len(filtered_hints),
        "keywords": mode_context.get("keywords", []),
        "prompts": mode_context.get("prompts", []),
    }, indent=2)


def get_all_hints() -> str:
    """
    Resource: automation://hints
    
    Returns the complete centralized hint registry.
    
    Returns:
        JSON with all tool hints organized by category
    """
    # Organize by category
    by_category: Dict[str, List[Dict]] = {}
    for name, data in TOOL_HINTS_REGISTRY.items():
        category = data.get("category", "other")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append({
            "tool": name,
            "hint": data["hint"],
            "outputs": data.get("outputs", []),
        })

    return json.dumps({
        "description": "Centralized tool hint registry",
        "total_tools": len(TOOL_HINTS_REGISTRY),
        "categories": list(by_category.keys()),
        "by_category": by_category,
    }, indent=2)


def register_context_primer_resources(mcp) -> None:
    """
    Register context primer resources with the MCP server.
    
    Usage:
        from project_management_automation.resources.context_primer import register_context_primer_resources
        register_context_primer_resources(mcp)
    """
    try:
        @mcp.resource("automation://context-primer")
        def context_primer_resource() -> str:
            """Get unified context primer for AI."""
            return get_context_primer()

        @mcp.resource("automation://hints")
        def all_hints_resource() -> str:
            """Get all tool hints."""
            return get_all_hints()

        @mcp.resource("automation://hints/{mode}")
        def hints_by_mode_resource(mode: str) -> str:
            """Get hints filtered by workflow mode."""
            return get_hints_for_mode(mode)

        logger.info("✅ Registered 3 context primer resources")

    except Exception as e:
        logger.warning(f"Could not register context primer resources: {e}")


__all__ = [
    "TOOL_HINTS_REGISTRY",
    "WORKFLOW_MODE_CONTEXT",
    "get_context_primer",
    "get_hints_for_mode",
    "get_all_hints",
    "register_context_primer_resources",
]

