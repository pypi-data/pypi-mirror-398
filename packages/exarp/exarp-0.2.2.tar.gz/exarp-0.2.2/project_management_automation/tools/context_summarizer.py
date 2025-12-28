"""
Context Summarization Tool

Strategically summarizes and reduces context for LLM interactions.
Compresses verbose tool outputs into key metrics while preserving actionable information.

Features:
- Multi-level summarization (brief, detailed, key_metrics)
- Tool-aware compression using hint patterns
- Batch summarization for multiple results
- Token estimation for context budgeting
"""

import json
import logging
import time
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARIZATION PATTERNS (Tool-specific extraction rules)
# ═══════════════════════════════════════════════════════════════════════════════

TOOL_PATTERNS = {
    # Health tools
    "health": {
        "key_fields": ["health_score", "score", "overall_score"],
        "count_fields": ["broken_links", "broken_internal", "broken_external", "stale_files", "format_errors"],
        "action_fields": ["tasks_created", "followup_tasks", "recommendations"],
        "brief_template": "Health: {score}/100, {issues} issues, {actions} actions",
    },
    "scorecard": {
        "key_fields": ["overall_score", "production_ready"],
        "count_fields": ["security_score", "testing_score", "documentation_score", "completion_score"],
        "action_fields": ["recommendations", "critical_issues"],
        "brief_template": "Score: {overall_score}/100, Production Ready: {production_ready}",
    },
    # Security tools
    "security": {
        "key_fields": ["status", "total_vulnerabilities"],
        "count_fields": ["critical", "high", "medium", "low", "vulnerabilities"],
        "action_fields": ["remediation", "recommendations", "fixes_available"],
        "brief_template": "Security: {critical} critical, {high} high, {medium} medium vulns",
    },
    # Task tools
    "task": {
        "key_fields": ["status", "tasks_analyzed", "total_tasks"],
        "count_fields": ["duplicates", "misaligned", "pending", "completed", "blocked"],
        "action_fields": ["tasks_created", "recommendations", "followup_tasks"],
        "brief_template": "Tasks: {total} total, {pending} pending, {actions} actions",
    },
    "alignment": {
        "key_fields": ["average_score", "alignment_score"],
        "count_fields": ["misaligned_count", "tasks_analyzed"],
        "action_fields": ["followup_tasks", "recommendations"],
        "brief_template": "Alignment: {score}% avg, {misaligned} misaligned tasks",
    },
    "duplicates": {
        "key_fields": ["duplicate_count", "groups_found"],
        "count_fields": ["total_tasks", "unique_tasks"],
        "action_fields": ["auto_fix_available", "recommendations"],
        "brief_template": "Duplicates: {count} found in {groups} groups",
    },
    # Testing tools
    "testing": {
        "key_fields": ["status", "passed", "failed", "coverage"],
        "count_fields": ["total_tests", "skipped", "errors"],
        "action_fields": ["failures", "recommendations"],
        "brief_template": "Tests: {passed} passed, {failed} failed, {coverage}% coverage",
    },
    # Generic fallback
    "generic": {
        "key_fields": ["status", "success", "result"],
        "count_fields": ["count", "total", "found"],
        "action_fields": ["recommendations", "actions", "tasks"],
        "brief_template": "Result: {status}, {count} items",
    },
}

# Estimate tokens per character (rough approximation)
TOKENS_PER_CHAR = 0.25


# ═══════════════════════════════════════════════════════════════════════════════
# CORE SUMMARIZATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════


def summarize_context(
    data: Union[str, dict, list],
    level: str = "brief",
    tool_type: Optional[str] = None,
    max_tokens: Optional[int] = None,
    include_raw: bool = False,
) -> str:
    """
    [HINT: Context summarizer. Compresses verbose outputs to key metrics. Levels: brief|detailed|key_metrics.]

    Strategically summarizes tool outputs for efficient context usage.

    📊 Output: Compressed summary with key metrics
    🔧 Side Effects: None
    ⏱️ Typical Runtime: <10ms

    Args:
        data: JSON string, dict, or list to summarize
        level: Summarization level
            - "brief": One-line summary with key metrics (default)
            - "detailed": Multi-line with categories
            - "key_metrics": Just the numbers/scores
            - "actionable": Only actionable items (recommendations, tasks)
        tool_type: Tool type hint for smarter summarization
            - "health", "security", "task", "testing", "scorecard", etc.
            - Auto-detected if not provided
        max_tokens: Maximum tokens for output (truncates if needed)
        include_raw: Include original data in response

    Returns:
        JSON with summarized content and metadata

    Example:
        summarize_context(health_result, level="brief")
        → "Health: 85/100, 3 issues, 2 actions"

        summarize_context(security_scan, level="key_metrics")
        → {"critical": 0, "high": 2, "medium": 5}
    """
    start_time = time.time()

    try:
        # Parse input
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                # Not JSON, treat as plain text
                parsed = {"text": data}
        else:
            parsed = data

        # Auto-detect tool type if not provided
        if not tool_type:
            tool_type = _detect_tool_type(parsed)

        # Get pattern for this tool type
        pattern = TOOL_PATTERNS.get(tool_type, TOOL_PATTERNS["generic"])

        # Extract based on level
        if level == "brief":
            summary = _extract_brief(parsed, pattern)
        elif level == "detailed":
            summary = _extract_detailed(parsed, pattern)
        elif level == "key_metrics":
            summary = _extract_key_metrics(parsed, pattern)
        elif level == "actionable":
            summary = _extract_actionable(parsed, pattern)
        else:
            summary = _extract_brief(parsed, pattern)

        # Calculate token estimates
        original_tokens = _estimate_tokens(json.dumps(parsed))
        summary_tokens = _estimate_tokens(json.dumps(summary) if isinstance(summary, dict) else summary)
        reduction = round((1 - summary_tokens / max(original_tokens, 1)) * 100, 1)

        # Truncate if max_tokens specified
        if max_tokens and summary_tokens > max_tokens:
            summary = _truncate_to_tokens(summary, max_tokens)
            summary_tokens = max_tokens

        result = {
            "summary": summary,
            "level": level,
            "tool_type": tool_type,
            "token_estimate": {
                "original": original_tokens,
                "summarized": summary_tokens,
                "reduction_percent": reduction,
            },
            "duration_ms": round((time.time() - start_time) * 1000, 2),
        }

        if include_raw:
            result["raw_data"] = parsed

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return json.dumps({
            "error": str(e),
            "summary": str(data)[:200] + "..." if len(str(data)) > 200 else str(data),
            "level": level,
        }, indent=2)


def batch_summarize(
    items: list[dict[str, Any]],
    level: str = "brief",
    combine: bool = True,
) -> str:
    """
    [HINT: Batch summarizer. Summarizes multiple results at once. combine=True merges into one summary.]

    Summarize multiple tool results efficiently.

    Args:
        items: List of {"data": ..., "tool_type": ...} dicts
        level: Summarization level for all items
        combine: If True, merge all summaries into combined view

    Returns:
        JSON with individual or combined summaries
    """
    summaries = []
    total_original = 0
    total_summarized = 0

    for item in items:
        data = item.get("data", item)
        tool_type = item.get("tool_type")

        result = json.loads(summarize_context(data, level=level, tool_type=tool_type))
        summaries.append(result)

        total_original += result.get("token_estimate", {}).get("original", 0)
        total_summarized += result.get("token_estimate", {}).get("summarized", 0)

    if combine:
        combined = {
            "combined_summary": [s.get("summary") for s in summaries],
            "total_items": len(summaries),
            "token_estimate": {
                "original": total_original,
                "summarized": total_summarized,
                "reduction_percent": round((1 - total_summarized / max(total_original, 1)) * 100, 1),
            },
        }
        return json.dumps(combined, indent=2)

    return json.dumps({"summaries": summaries}, indent=2)


def estimate_context_budget(
    items: list[Any],
    budget_tokens: int = 4000,
) -> str:
    """
    [HINT: Context budget. Estimates tokens and suggests what to keep/summarize to fit budget.]

    Estimate token usage and suggest context reduction strategy.

    Args:
        items: List of data items to analyze
        budget_tokens: Target token budget

    Returns:
        JSON with budget analysis and recommendations
    """
    analysis = []
    total_tokens = 0

    for i, item in enumerate(items):
        item_str = json.dumps(item) if isinstance(item, (dict, list)) else str(item)
        tokens = _estimate_tokens(item_str)
        total_tokens += tokens

        analysis.append({
            "index": i,
            "tokens": tokens,
            "percent_of_budget": round(tokens / budget_tokens * 100, 1),
            "recommendation": _get_budget_recommendation(tokens, budget_tokens),
        })

    # Sort by size descending
    analysis.sort(key=lambda x: x["tokens"], reverse=True)

    over_budget = total_tokens > budget_tokens

    return json.dumps({
        "total_tokens": total_tokens,
        "budget_tokens": budget_tokens,
        "over_budget": over_budget,
        "reduction_needed": max(0, total_tokens - budget_tokens),
        "items": analysis,
        "strategy": _suggest_reduction_strategy(analysis, total_tokens, budget_tokens),
    }, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


def _detect_tool_type(data: dict) -> str:
    """Auto-detect tool type from data structure."""
    data_str = json.dumps(data).lower()

    if any(k in data_str for k in ["vulnerability", "cve", "security", "exploit"]):
        return "security"
    if any(k in data_str for k in ["health_score", "broken_link", "stale_file"]):
        return "health"
    if any(k in data_str for k in ["overall_score", "production_ready", "scorecard"]):
        return "scorecard"
    if any(k in data_str for k in ["alignment", "misaligned"]):
        return "alignment"
    if any(k in data_str for k in ["duplicate", "similar"]):
        return "duplicates"
    if any(k in data_str for k in ["test", "passed", "failed", "coverage"]):
        return "testing"
    if any(k in data_str for k in ["task", "todo", "pending", "completed"]):
        return "task"

    return "generic"


def _extract_brief(data: dict, pattern: dict) -> str:
    """Extract one-line brief summary."""
    values = {}

    # Extract key fields
    for field in pattern["key_fields"]:
        val = _deep_get(data, field)
        if val is not None:
            values["score"] = val
            break

    # Count issues
    issue_count = 0
    for field in pattern["count_fields"]:
        val = _deep_get(data, field)
        if isinstance(val, (int, float)):
            issue_count += val
        elif isinstance(val, list):
            issue_count += len(val)
    values["issues"] = issue_count
    values["count"] = issue_count

    # Count actions
    action_count = 0
    for field in pattern["action_fields"]:
        val = _deep_get(data, field)
        if isinstance(val, (int, float)):
            action_count += val
        elif isinstance(val, list):
            action_count += len(val)
    values["actions"] = action_count

    # Extract severity counts for security
    for sev in ["critical", "high", "medium", "low"]:
        val = _deep_get(data, sev)
        if val is not None:
            values[sev] = val

    # Extract test metrics
    for metric in ["passed", "failed", "coverage", "total"]:
        val = _deep_get(data, metric)
        if val is not None:
            values[metric] = val

    # Extract common fields
    values["status"] = _deep_get(data, "status") or _deep_get(data, "success") or "completed"
    values["overall_score"] = _deep_get(data, "overall_score") or values.get("score", "N/A")
    values["production_ready"] = _deep_get(data, "production_ready") or "unknown"
    values["misaligned"] = _deep_get(data, "misaligned_count") or 0
    values["groups"] = _deep_get(data, "groups_found") or 0
    values["pending"] = _deep_get(data, "pending") or 0
    values["total"] = _deep_get(data, "total_tasks") or _deep_get(data, "total") or 0

    # Try to format using template
    try:
        return pattern["brief_template"].format(**values)
    except KeyError:
        # Fallback to generic format
        key_items = [f"{k}: {v}" for k, v in values.items() if v and v != "N/A" and v != 0][:5]
        return ", ".join(key_items)


def _extract_detailed(data: dict, pattern: dict) -> dict:
    """Extract multi-line detailed summary."""
    result = {
        "key_metrics": {},
        "counts": {},
        "actions": [],
    }

    # Key metrics
    for field in pattern["key_fields"]:
        val = _deep_get(data, field)
        if val is not None:
            result["key_metrics"][field] = val

    # Counts
    for field in pattern["count_fields"]:
        val = _deep_get(data, field)
        if val is not None:
            if isinstance(val, list):
                result["counts"][field] = len(val)
            else:
                result["counts"][field] = val

    # Actions (first 5 only)
    for field in pattern["action_fields"]:
        val = _deep_get(data, field)
        if isinstance(val, list):
            result["actions"].extend(val[:5])
        elif val:
            result["actions"].append(str(val))

    result["actions"] = result["actions"][:5]  # Limit to 5

    return result


def _extract_key_metrics(data: dict, pattern: dict) -> dict:
    """Extract only numerical metrics."""
    metrics = {}

    all_fields = pattern["key_fields"] + pattern["count_fields"]
    for field in all_fields:
        val = _deep_get(data, field)
        if isinstance(val, (int, float)):
            metrics[field] = val
        elif isinstance(val, list):
            metrics[f"{field}_count"] = len(val)

    return metrics


def _extract_actionable(data: dict, pattern: dict) -> dict:
    """Extract only actionable items."""
    actions = {
        "recommendations": [],
        "tasks": [],
        "fixes": [],
    }

    for field in pattern["action_fields"]:
        val = _deep_get(data, field)
        if isinstance(val, list):
            if "recommend" in field.lower():
                actions["recommendations"].extend(val[:3])
            elif "task" in field.lower():
                actions["tasks"].extend(val[:3])
            else:
                actions["fixes"].extend(val[:3])

    # Clean empty lists
    return {k: v for k, v in actions.items() if v}


def _deep_get(data: dict, key: str, default=None) -> Any:
    """Get value from nested dict, searching recursively."""
    if isinstance(data, dict):
        if key in data:
            return data[key]

        # Check nested 'data' wrapper
        if "data" in data:
            result = _deep_get(data["data"], key, None)
            if result is not None:
                return result

        # Check nested 'results' wrapper
        if "results" in data:
            result = _deep_get(data["results"], key, None)
            if result is not None:
                return result

        # Search all nested dicts
        for v in data.values():
            if isinstance(v, dict):
                result = _deep_get(v, key, None)
                if result is not None:
                    return result

    return default


def _estimate_tokens(text: str) -> int:
    """Estimate token count for text."""
    return int(len(text) * TOKENS_PER_CHAR)


def _truncate_to_tokens(data: Any, max_tokens: int) -> Any:
    """Truncate data to fit within token limit."""
    data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
    max_chars = int(max_tokens / TOKENS_PER_CHAR)

    if len(data_str) <= max_chars:
        return data

    truncated = data_str[:max_chars - 20] + "... [truncated]"
    return truncated


def _get_budget_recommendation(tokens: int, budget: int) -> str:
    """Get recommendation for a single item."""
    ratio = tokens / budget

    if ratio > 0.5:
        return "summarize_brief"
    elif ratio > 0.25:
        return "summarize_key_metrics"
    elif ratio > 0.1:
        return "keep_detailed"
    else:
        return "keep_full"


def _suggest_reduction_strategy(analysis: list[dict], total: int, budget: int) -> str:
    """Suggest overall reduction strategy."""
    if total <= budget:
        return "Within budget - no reduction needed"

    reduction_needed = total - budget

    # Find items that should be summarized
    to_summarize = [a for a in analysis if a["recommendation"].startswith("summarize")]

    if not to_summarize:
        return f"Reduce largest items to fit. Need to remove ~{reduction_needed} tokens."

    return f"Summarize {len(to_summarize)} items using 'brief' level. Estimated savings: {sum(a['tokens'] * 0.7 for a in to_summarize):.0f} tokens."

