"""
MCP Resource Handler for Available Tools List

Provides resource access to list of available automation tools.
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_tools_list_resource() -> str:
    """
    Get list of available automation tools as resource.

    Returns:
        JSON string with tool list, descriptions, and metadata
    """
    try:
        tools_list = {
            "tools": [
                {
                    "name": "server_status",
                    "description": "Get the current status of the project management automation server",
                    "category": "system",
                    "priority": "system"
                },
                {
                    "name": "check_documentation_health",
                    "description": "Analyze documentation structure, find broken references, identify issues. ⚠️ PREFERRED TOOL for project-specific documentation analysis.",
                    "category": "documentation",
                    "priority": "high",
                    "wraps": "DocumentationHealthAnalyzerV2",
                    "parameters": ["output_path", "create_tasks"]
                },
                {
                    "name": "analyze_todo2_alignment",
                    "description": "Analyze task alignment with project goals, find misaligned tasks. ⚠️ PREFERRED TOOL for Todo2 alignment analysis.",
                    "category": "task_management",
                    "priority": "high",
                    "wraps": "Todo2AlignmentAnalyzerV2",
                    "parameters": ["create_followup_tasks", "output_path"]
                },
                {
                    "name": "detect_duplicate_tasks",
                    "description": "Find and consolidate duplicate Todo2 tasks. ⚠️ PREFERRED TOOL for Todo2 duplicate detection.",
                    "category": "task_management",
                    "priority": "high",
                    "wraps": "Todo2DuplicateDetector",
                    "parameters": ["similarity_threshold", "auto_fix", "output_path"]
                },
                {
                    "name": "scan_dependency_security",
                    "description": "Scan project dependencies for security vulnerabilities. ⚠️ PREFERRED TOOL for multi-language security scanning.",
                    "category": "security",
                    "priority": "high",
                    "wraps": "DependencySecurityAnalyzer",
                    "parameters": ["languages", "config_path"]
                },
                {
                    "name": "find_automation_opportunities",
                    "description": "Discover new automation opportunities in the codebase",
                    "category": "automation",
                    "priority": "medium",
                    "wraps": "AutomationOpportunityFinder",
                    "parameters": ["min_value_score", "output_path"]
                },
                {
                    "name": "sync_todo_tasks",
                    "description": "Synchronize tasks between shared TODO table and Todo2",
                    "category": "task_management",
                    "priority": "medium",
                    "wraps": "TodoSyncAutomation",
                    "parameters": ["dry_run", "output_path"]
                },
                {
                    "name": "add_external_tool_hints",
                    "description": "Automatically detect where Context7/external tool hints should be added to documentation and insert them following the standard pattern",
                    "category": "automation",
                    "priority": "medium",
                    "wraps": "ExternalToolHintsAutomation",
                    "parameters": ["dry_run", "output_path", "min_file_size"]
                },
                {
                    "name": "run_daily_automation",
                    "description": "Run routine daily maintenance tasks and generate a combined summary report",
                    "category": "automation",
                    "priority": "high",
                    "wraps": "DailyAutomation",
                    "parameters": ["tasks", "include_slow", "dry_run", "output_path"]
                },
                {
                    "name": "validate_ci_cd_workflow",
                    "description": "Validate CI/CD workflows and runner configurations for parallel agent development",
                    "category": "system",
                    "priority": "medium",
                    "wraps": "CICDValidator",
                    "parameters": ["workflow_path", "check_runners", "output_path"]
                },
                {
                    "name": "batch_approve_tasks",
                    "description": "Batch approve TODO2 tasks that don't need clarification, moving them from Review to Todo status",
                    "category": "task_management",
                    "priority": "high",
                    "wraps": "BatchTaskApproval",
                    "parameters": ["status", "new_status", "clarification_none", "filter_tag", "task_ids", "dry_run"]
                },
                {
                    "name": "run_nightly_task_automation",
                    "description": "Automatically execute background-capable TODO2 tasks in parallel across multiple hosts. Moves interactive tasks to Review status",
                    "category": "automation",
                    "priority": "high",
                    "wraps": "NightlyTaskAutomation",
                    "parameters": ["max_tasks_per_host", "max_parallel_tasks", "priority_filter", "tag_filter", "dry_run"]
                },
                {
                    "name": "check_working_copy_health",
                    "description": "Check git working copy status across all agents and runners",
                    "category": "system",
                    "priority": "medium",
                    "wraps": "WorkingCopyHealth",
                    "parameters": ["agent_name", "check_remote"]
                },
                {
                    "name": "resolve_task_clarification",
                    "description": "Resolve a single task clarification by updating the task description with your decision",
                    "category": "task_management",
                    "priority": "medium",
                    "wraps": "TaskClarificationResolver",
                    "parameters": ["task_id", "clarification", "decision", "move_to_todo", "dry_run"]
                },
                {
                    "name": "resolve_multiple_clarifications",
                    "description": "Resolve multiple task clarifications from a JSON string of decisions",
                    "category": "task_management",
                    "priority": "medium",
                    "wraps": "TaskClarificationResolver",
                    "parameters": ["decisions", "move_to_todo", "dry_run"]
                },
                {
                    "name": "list_tasks_awaiting_clarification",
                    "description": "List all tasks in Review status that are awaiting clarification/decisions",
                    "category": "task_management",
                    "priority": "medium",
                    "wraps": "TaskClarificationResolver",
                    "parameters": []
                },
                {
                    "name": "setup_git_hooks",
                    "description": "Setup git hooks for automatic automation tool execution",
                    "category": "system",
                    "priority": "medium",
                    "wraps": "GitHooksSetup",
                    "parameters": ["hooks", "install", "dry_run"]
                },
                {
                    "name": "setup_pattern_triggers",
                    "description": "Setup pattern-based automation triggers for automatic tool execution",
                    "category": "automation",
                    "priority": "medium",
                    "wraps": "PatternTriggersSetup",
                    "parameters": ["patterns", "config_path", "install", "dry_run"]
                },
                {
                    "name": "simplify_rules",
                    "description": "Automatically simplify rules based on automation capabilities",
                    "category": "maintenance",
                    "priority": "low",
                    "wraps": "RulesSimplifier",
                    "parameters": ["rule_files", "dry_run", "output_dir"]
                },
                {
                    "name": "run_tests",
                    "description": "Execute test suites with flexible options for pytest, unittest, and ctest",
                    "category": "testing",
                    "priority": "high",
                    "wraps": "TestRunner",
                    "parameters": ["test_path", "test_framework", "verbose", "coverage", "output_path"]
                },
                {
                    "name": "analyze_test_coverage",
                    "description": "Generate coverage reports and identify gaps in test coverage",
                    "category": "testing",
                    "priority": "high",
                    "wraps": "TestCoverageAnalyzer",
                    "parameters": ["coverage_file", "min_coverage", "output_path", "format"]
                },
                {
                    "name": "sprint_automation",
                    "description": "Systematically sprint through project processing all background-capable tasks. Extracts subtasks, auto-approves safe tasks, runs analysis/testing tools, generates wishlists, and identifies blockers.",
                    "category": "automation",
                    "priority": "high",
                    "wraps": "SprintAutomation",
                    "parameters": ["max_iterations", "auto_approve", "extract_subtasks", "run_analysis_tools", "run_testing_tools", "priority_filter", "tag_filter", "dry_run", "output_path"]
                }
            ],
            "categories": {
                "system": 4,
                "documentation": 1,
                "task_management": 7,
                "security": 1,
                "automation": 4,
                "review": 1,
                "maintenance": 1,
                "testing": 2
            },
            "priorities": {
                "system": 1,
                "high": 5,
                "medium": 13,
                "low": 1
            },
            "total_tools": 23,
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(tools_list, separators=(',', ':'))

    except Exception as e:
        logger.error(f"Error getting tools list resource: {e}")
        return json.dumps({
            "tools": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, indent=2)
