"""
Exarp Naming Conventions

This module documents and enforces consistent naming across tools, prompts, and resources.

## Naming Convention

### Tools: verb_object pattern
- `generate_*` - Create/produce output (scorecards, reports, audio)
- `check_*` - Validate/verify status (health, backends)
- `analyze_*` - Examine and report on data (alignment, coverage, hierarchy)
- `detect_*` - Find issues (duplicates)
- `scan_*` - Search for problems (security vulnerabilities)
- `find_*` - Discover opportunities (automation)
- `run_*` - Execute processes (automation, tests)
- `get_*` - Retrieve data (briefing, summary, memories)
- `list_*` - Enumerate items (advisors, tasks)
- `sync_*` - Synchronize data (tasks)
- `setup_*` - Configure systems (hooks, triggers)
- `validate_*` - Check configuration (CI/CD)
- `batch_*` - Process multiple items (approve)
- `resolve_*` - Handle issues (clarifications)
- `consult_*` - Get advice (advisor)
- `save_*` - Persist data (memory)
- `recall_*` - Retrieve stored data (context)
- `search_*` - Query data (memories)
- `export_*` - Output data (podcast)
- `fetch_*` - Get external data (alerts)
- `consolidate_*` - Merge/cleanup (tags)
- `simplify_*` - Reduce complexity (rules)
- `synthesize_*` - Create from parts (audio)

### Prompts: action_target pattern (short but readable)
- `check_docs` instead of `doc_check`
- `find_duplicates` instead of `dups`
- `scan_security` instead of `scan`

### Resources: automation://noun pattern
- `automation://status`
- `automation://tasks`
- `automation://memories`
"""


# Tool name mapping: new_name -> old_name (for backward compatibility)
TOOL_RENAMES: dict[str, str] = {
    # New verb_object names -> old names (aliases)
    "generate_project_scorecard": "project_scorecard",
    "generate_project_overview": "project_overview",
    "generate_security_report": "unified_security_report",
    "run_sprint_automation": "sprint_automation",
    "get_session_summary": "session_summary",
    "get_sprint_memories": "sprint_memories",
}

# Reverse mapping for lookup
TOOL_ALIASES: dict[str, str] = {v: k for k, v in TOOL_RENAMES.items()}

# Prompt name mapping: new_name -> old_name
PROMPT_RENAMES: dict[str, str] = {
    "check_docs": "doc_check",
    "check_docs_quick": "doc_quick",
    "find_duplicates": "dups",
    "sync_tasks": "sync",
    "scan_security": "scan",
    "scan_security_python": "scan_py",
    "scan_security_rust": "scan_rs",
    "find_automation": "auto",
    "find_automation_high_value": "auto_high",
    "analyze_alignment": "align",
    "run_weekly": "weekly",
    "run_pre_sprint": "pre_sprint",
    "run_post_impl": "post_impl",
    "run_daily": "daily_checkin",
    "start_sprint": "sprint_start",
    "end_sprint": "sprint_end",
    "review_tasks": "task_review",
    "check_project_health": "project_health",
    "setup_automation": "automation_setup",
    "generate_scorecard": "scorecard",
    "generate_overview": "overview",
}

# Reverse mapping for lookup
PROMPT_ALIASES: dict[str, str] = {v: k for k, v in PROMPT_RENAMES.items()}


def get_canonical_tool_name(name: str) -> str:
    """Get the canonical (new) name for a tool."""
    return TOOL_ALIASES.get(name, name)


def get_tool_alias(name: str) -> str:
    """Get the alias (old) name for a tool if it exists."""
    return TOOL_RENAMES.get(name, name)


def get_canonical_prompt_name(name: str) -> str:
    """Get the canonical (new) name for a prompt."""
    return PROMPT_ALIASES.get(name, name)


def get_prompt_alias(name: str) -> str:
    """Get the alias (old) name for a prompt if it exists."""
    return PROMPT_RENAMES.get(name, name)


def validate_tool_name(name: str) -> tuple[bool, str]:
    """
    Validate a tool name follows verb_object convention.

    Returns:
        (is_valid, suggestion) - If invalid, suggestion contains recommended name
    """
    valid_prefixes = (
        "generate_",
        "check_",
        "analyze_",
        "detect_",
        "scan_",
        "find_",
        "run_",
        "get_",
        "list_",
        "sync_",
        "setup_",
        "validate_",
        "batch_",
        "resolve_",
        "consult_",
        "save_",
        "recall_",
        "search_",
        "export_",
        "fetch_",
        "consolidate_",
        "simplify_",
        "synthesize_",
        "add_",
        "server_",  # Exception for server_status
    )

    if name.startswith(valid_prefixes):
        return True, name

    # Suggest a fix
    if "scorecard" in name:
        return False, f"generate_{name}"
    elif "overview" in name:
        return False, f"generate_{name}"
    elif "report" in name:
        return False, f"generate_{name}"
    elif "automation" in name:
        return False, f"run_{name}"
    elif "summary" in name or "memories" in name:
        return False, f"get_{name}"
    else:
        return False, f"run_{name}"  # Default suggestion


def list_all_conventions() -> dict[str, list[str]]:
    """List all naming conventions for documentation."""
    return {
        "tool_renames": list(TOOL_RENAMES.items()),
        "prompt_renames": list(PROMPT_RENAMES.items()),
        "valid_tool_prefixes": [
            "generate_",
            "check_",
            "analyze_",
            "detect_",
            "scan_",
            "find_",
            "run_",
            "get_",
            "list_",
            "sync_",
            "setup_",
            "validate_",
            "batch_",
            "resolve_",
            "consult_",
            "save_",
            "recall_",
            "search_",
            "export_",
            "fetch_",
            "consolidate_",
            "simplify_",
            "synthesize_",
            "add_",
        ],
    }
