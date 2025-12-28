"""
Concise Capabilities Resource for Exarp MCP Server.

Provides a minimal, token-efficient overview of what exarp can do,
organized by domain. Designed for agent priming at session start.

Usage:
    Resource URI: automation://capabilities
    
    Returns ~500 tokens covering all major capabilities.
"""

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("exarp.resources.capabilities")

# ═══════════════════════════════════════════════════════════════════════════════
# CONCISE CAPABILITIES OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════

CAPABILITIES: Dict[str, Dict[str, Any]] = {
    "tasks": {
        "description": "Task management and alignment",
        "can_do": [
            "Detect duplicate tasks and auto-merge",
            "Check task alignment with PROJECT_GOALS.md",
            "Sync TODO table ↔ Todo2 state",
            "Batch approve tasks without clarification",
            "Analyze task hierarchy and dependencies",
            "Assign tasks to agents/hosts",
        ],
        "tools": ["analyze_todo2_alignment", "detect_duplicate_tasks", "sync_todo_tasks", "batch_approve_tasks"],
        "resources": ["tasks://{status}", "tasks://priority/{level}"],
    },
    "health": {
        "description": "Project health monitoring",
        "can_do": [
            "Generate project scorecard (0-100)",
            "Create executive overview (text/markdown/slides)",
            "Check documentation health and broken links",
            "Monitor git working copy across agents",
        ],
        "tools": ["project_scorecard", "project_overview", "check_documentation_health", "check_working_copy_health"],
        "resources": ["automation://status"],
    },
    "security": {
        "description": "Security scanning and alerts",
        "can_do": [
            "Scan Python/Rust/npm for CVEs",
            "Fetch GitHub Dependabot alerts",
            "Generate combined security reports",
        ],
        "tools": ["scan_dependency_security", "fetch_dependabot_alerts", "generate_security_report"],
        "resources": [],
    },
    "automation": {
        "description": "Automated maintenance and CI/CD",
        "can_do": [
            "Run daily health checks (docs, alignment, security)",
            "Execute nightly background tasks across hosts",
            "Find automation opportunities in workflow",
            "Setup git hooks (pre-commit, pre-push)",
            "Configure file/git/task pattern triggers",
        ],
        "tools": ["run_daily_automation", "run_nightly_task_automation", "setup_git_hooks", "setup_pattern_triggers"],
        "resources": [],
    },
    "testing": {
        "description": "Test execution and coverage",
        "can_do": [
            "Run pytest/unittest/ctest",
            "Analyze test coverage and gaps",
            "Check Definition of Done checklist",
        ],
        "tools": ["run_tests", "analyze_test_coverage", "check_definition_of_done"],
        "resources": [],
    },
    "planning": {
        "description": "PRD and roadmap management",
        "can_do": [
            "Generate PRD from codebase analysis",
            "Map tasks to personas and user stories",
            "Sprint automation with subtask extraction",
        ],
        "tools": ["generate_prd", "analyze_prd_alignment", "sprint_automation"],
        "resources": [],
    },
    "workflow": {
        "description": "AI workflow optimization",
        "can_do": [
            "Recommend AGENT vs ASK mode",
            "Suggest optimal AI model for task",
            "Focus mode to reduce visible tools 50-80%",
        ],
        "tools": ["recommend_workflow_mode", "recommend_model", "focus_mode"],
        "resources": ["automation://context-primer", "automation://hints"],
    },
    "memory": {
        "description": "Session memory and context",
        "can_do": [
            "Save insights to session memory",
            "Recall context for tasks",
            "Search past memories by query",
        ],
        "tools": ["save_memory", "recall_memory", "search_memories"],
        "resources": ["memory://{id}", "memories://category/{cat}"],
    },
    "advisors": {
        "description": "Trusted advisor wisdom",
        "can_do": [
            "Consult advisors by metric/stage",
            "Get morning briefing with guidance",
            "Score-based wisdom selection",
        ],
        "tools": ["consult_advisor", "get_morning_briefing", "list_advisors"],
        "resources": ["advisor://{name}", "automation://advisors"],
    },
}


def get_capabilities(domain: Optional[str] = None, compact: bool = True) -> str:
    """
    Resource: automation://capabilities
    
    Returns concise overview of exarp capabilities for agent priming.
    
    Args:
        domain: Filter to specific domain (tasks, health, security, etc.)
        compact: If True, returns minimal format for token efficiency
    
    Returns:
        JSON with capabilities organized by domain
    """
    if domain:
        if domain not in CAPABILITIES:
            return json.dumps({
                "error": f"Unknown domain: {domain}",
                "available": list(CAPABILITIES.keys()),
            })
        data = {domain: CAPABILITIES[domain]}
    else:
        data = CAPABILITIES

    if compact:
        # Ultra-compact format for priming
        compact_data = {}
        for dom, info in data.items():
            compact_data[dom] = {
                "can": info["can_do"],
                "tools": info["tools"],
            }
        return json.dumps({
            "exarp_capabilities": compact_data,
            "total_domains": len(data),
            "usage": "Call tools by name or access resources by URI",
        }, indent=2)
    else:
        return json.dumps({
            "exarp_capabilities": data,
            "total_domains": len(data),
        }, indent=2)


def get_capabilities_summary() -> str:
    """
    Resource: automation://capabilities/summary
    
    Returns one-liner per domain for ultra-fast priming.
    """
    summary = {}
    for domain, info in CAPABILITIES.items():
        summary[domain] = info["description"]

    return json.dumps({
        "exarp": summary,
        "hint": "Use automation://capabilities/{domain} for details",
    }, indent=2)


def get_domain_capabilities(domain: str) -> str:
    """
    Resource: automation://capabilities/{domain}
    
    Returns capabilities for a specific domain.
    """
    return get_capabilities(domain=domain, compact=False)


def register_capabilities_resources(mcp) -> None:
    """
    Register capabilities resources with the MCP server.
    """
    try:
        @mcp.resource("automation://capabilities")
        def capabilities_resource() -> str:
            """Get concise exarp capabilities for agent priming."""
            return get_capabilities()

        @mcp.resource("automation://capabilities/summary")
        def capabilities_summary_resource() -> str:
            """Get one-liner summary of exarp capabilities."""
            return get_capabilities_summary()

        @mcp.resource("automation://capabilities/{domain}")
        def domain_capabilities_resource(domain: str) -> str:
            """Get capabilities for a specific domain."""
            return get_domain_capabilities(domain)

        logger.info("✅ Registered 3 capabilities resources")

    except Exception as e:
        logger.warning(f"Could not register capabilities resources: {e}")


__all__ = [
    "CAPABILITIES",
    "get_capabilities",
    "get_capabilities_summary",
    "get_domain_capabilities",
    "register_capabilities_resources",
]

