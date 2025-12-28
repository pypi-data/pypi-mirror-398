"""
Consolidated MCP Tools

Combines related tools into unified interfaces with action parameters.
Reduces tool count while maintaining all functionality.

All tools use 'action' as the dispatcher parameter for consistency.

Consolidated tools:
- analyze_alignment(action=todo2|prd) ← analyze_todo2_alignment, analyze_prd_alignment
- automation(action=daily|nightly|sprint|discover) ← run_daily_automation, run_nightly_automation, run_sprint_automation, run_discover_automation
- estimation(action=estimate|analyze|stats) ← estimate_task_duration, analyze_estimation_accuracy, get_estimation_statistics
- security(action=scan|alerts|report) ← scan_dependency_security, fetch_dependabot_alerts, generate_security_report
- generate_config(action=rules|ignore|simplify) ← generate_cursor_rules, generate_cursorignore, simplify_rules
- setup_hooks(action=git|patterns) ← setup_git_hooks, setup_pattern_triggers
- prompt_tracking(action=log|analyze) ← log_prompt_iteration, analyze_prompt_iterations
- health(action=server|git|docs|dod|cicd) ← server_status, check_working_copy_health, check_documentation_health, check_definition_of_done, validate_ci_cd_workflow
- report(action=overview|scorecard|briefing|prd) ← generate_project_overview, generate_project_scorecard, get_daily_briefing, generate_prd
- advisor_audio removed - migrated to devwisdom-go MCP server
- task_analysis(action=duplicates|tags|hierarchy|dependencies|parallelization) ← detect_duplicate_tasks, consolidate_tags, analyze_task_hierarchy, analyze_todo2_dependencies, optimize_todo2_parallelization
- testing(action=run|coverage|suggest|validate) ← run_tests, analyze_test_coverage, suggest_test_cases, validate_test_structure
- lint(action=run|analyze) ← run_linter, analyze_problems
- memory(action=save|recall|search) ← save_memory, recall_context, search_memories
- memory_maint(action=health|gc|prune|consolidate|dream) ← memory lifecycle management and advisor dreaming
- task_discovery(action=comments|markdown|orphans|all) ← NEW: find tasks from various sources
- task_workflow(action=sync|approve|clarify|clarity|cleanup, sub_action for clarify) ← sync_todo_tasks, batch_approve_tasks, clarification, improve_task_clarity, cleanup_stale_tasks
- context(action=summarize|budget|batch) ← summarize_context, estimate_context_budget, batch_summarize
- tool_catalog(action=list|help) ← list_tools, get_tool_help
- workflow_mode(action=focus|suggest|stats) ← focus_mode, suggest_mode, get_tool_usage_stats
- recommend(action=model|workflow|advisor) ← recommend_model, recommend_workflow_mode, consult_advisor
"""

import asyncio
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def analyze_alignment(
    action: str = "todo2",
    create_followup_tasks: bool = True,
    output_path: Optional[str] = None,
) -> str:
    """
    Unified alignment analysis tool.

    Args:
        action: "todo2" for task alignment, "prd" for PRD persona mapping
        create_followup_tasks: Create tasks for misaligned items (todo2 only)
        output_path: Optional file to save results

    Returns:
        JSON string with alignment analysis results (FastMCP requires strings)
    """
    if action == "todo2":
        from .todo2_alignment import analyze_todo2_alignment
        # analyze_todo2_alignment already returns a JSON string
        result = analyze_todo2_alignment(create_followup_tasks, output_path)
        # Ensure it's a string (it should already be)
        return result if isinstance(result, str) else json.dumps(result, separators=(",", ":"))
    elif action == "prd":
        from .prd_alignment import analyze_prd_alignment
        result = analyze_prd_alignment(output_path)
        # Ensure we return a JSON string
        if isinstance(result, str):
            return result
        else:
            return json.dumps(result, separators=(",", ":"))
    else:
        error_result = {
            "status": "error",
            "error": f"Unknown alignment action: {action}. Use 'todo2' or 'prd'.",
        }
        return json.dumps(error_result, separators=(",", ":"))


async def security_async(
    action: str = "report",
    repo: str = "davidl71/project-management-automation",
    languages: Optional[list[str]] = None,
    config_path: Optional[str] = None,
    state: str = "open",
    include_dismissed: bool = False,
    ctx: Optional[Any] = None,
    alert_critical: bool = False,
) -> str:
    """
    Unified security analysis tool (async with progress).

    Args:
        action: "scan" for local pip-audit, "alerts" for Dependabot, "report" for combined
        repo: GitHub repo for alerts/report (owner/repo format)
        languages: Languages to scan (scan action)
        config_path: Config file path (scan action)
        state: Alert state filter (alerts action)
        include_dismissed: Include dismissed alerts (report action)
        ctx: FastMCP Context for progress reporting (optional)

    Returns:
        JSON string with security scan/report results
    """
    if action == "scan":
        from .dependency_security import scan_dependency_security_async
        result = await scan_dependency_security_async(languages, config_path, ctx, alert_critical)
        # Result should already be a string, but ensure it is
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    elif action == "alerts":
        from .dependabot_integration import fetch_dependabot_alerts
        result = fetch_dependabot_alerts(repo, state)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "report":
        from .dependabot_integration import get_unified_security_report
        result = get_unified_security_report(repo, include_dismissed)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown security action: {action}. Use 'scan', 'alerts', or 'report'.",
        }, indent=2)


def security(
    action: str = "report",
    repo: str = "davidl71/project-management-automation",
    languages: Optional[list[str]] = None,
    config_path: Optional[str] = None,
    state: str = "open",
    include_dismissed: bool = False,
    ctx: Optional[Any] = None,
    alert_critical: bool = False,
) -> str:
    """
    Unified security analysis tool (sync wrapper).

    Args:
        action: "scan" for local pip-audit, "alerts" for Dependabot, "report" for combined
        repo: GitHub repo for alerts/report (owner/repo format)
        languages: Languages to scan (scan action)
        config_path: Config file path (scan action)
        state: Alert state filter (alerts action)
        include_dismissed: Include dismissed alerts (report action)
        ctx: FastMCP Context for progress reporting (optional)

    Returns:
        JSON string with security scan/report results
    """
    # Check if we're in an async context using try/except/else pattern
    # This ensures the intentional RuntimeError is raised in else block, not caught
    try:
        asyncio.get_running_loop()
        # If we get here, we're in an async context - raise helpful error
        raise RuntimeError(
            "security() cannot be called from an async context. "
            "Use security_async() instead and await it."
        )
    except RuntimeError as e:
        # Re-raise if it's our intentional error
        if "security_async()" in str(e) or "async context" in str(e).lower():
            raise
        # Otherwise, no running loop - safe to use asyncio.run()
        result = asyncio.run(security_async(action, repo, languages, config_path, state, include_dismissed, ctx, alert_critical))
    # Convert dict to JSON string
    return json.dumps(result, indent=2) if isinstance(result, dict) else result


def generate_config(
    action: str = "rules",
    # rules params
    rules: Optional[str] = None,
    overwrite: bool = False,
    analyze_only: bool = False,
    # ignore params
    include_indexing: bool = True,
    analyze_project: bool = True,
    # simplify params
    rule_files: Optional[str] = None,
    output_dir: Optional[str] = None,
    # common
    dry_run: bool = False,
) -> str:
    """
    Unified config generation tool.

    Args:
        action: "rules" for .mdc files, "ignore" for .cursorignore, "simplify" for rule simplification
        rules: Specific rules to generate (rules action)
        overwrite: Overwrite existing rules (rules action)
        analyze_only: Only analyze, don't generate (rules action)
        include_indexing: Include indexing ignore (ignore action)
        analyze_project: Analyze project structure (ignore action)
        rule_files: Rule files to simplify (simplify action)
        output_dir: Output directory (simplify action)
        dry_run: Preview changes without writing

    Returns:
        JSON string with config generation results
    """
    if action == "rules":
        from .cursor_rules_generator import generate_cursor_rules
        result = generate_cursor_rules(rules, overwrite, analyze_only)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "ignore":
        from .cursorignore_generator import generate_cursorignore
        result = generate_cursorignore(include_indexing, analyze_project, dry_run)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "simplify":
        from .simplify_rules import simplify_rules
        parsed_files = None
        if rule_files:
            try:
                parsed_files = json.loads(rule_files)
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid JSON in rule_files parameter"}, indent=2)
        result = simplify_rules(parsed_files, dry_run, output_dir)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown config action: {action}. Use 'rules', 'ignore', or 'simplify'.",
        }, indent=2)


def setup_hooks(
    action: str = "git",
    # git hooks params
    hooks: Optional[list[str]] = None,
    # pattern params
    patterns: Optional[str] = None,
    config_path: Optional[str] = None,
    # common
    install: bool = True,
    dry_run: bool = False,
) -> str:
    """
    Unified hooks setup tool.

    Args:
        action: "git" for git hooks, "patterns" for pattern triggers
        hooks: Specific git hooks to install (git action)
        patterns: Pattern trigger definitions as JSON (patterns action)
        config_path: Config file path (patterns action)
        install: Install hooks (vs uninstall)
        dry_run: Preview changes without writing

    Returns:
        JSON string with hook setup results
    """
    if action == "git":
        from .git_hooks import setup_git_hooks
        result = setup_git_hooks(hooks, install, dry_run)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "patterns":
        from .pattern_triggers import setup_pattern_triggers
        parsed_patterns = None
        if patterns:
            try:
                parsed_patterns = json.loads(patterns)
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid JSON in patterns parameter"}, indent=2)
        result = setup_pattern_triggers(parsed_patterns, config_path, install, dry_run)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown hooks action: {action}. Use 'git' or 'patterns'.",
        }, indent=2)


def prompt_tracking(
    action: str = "analyze",
    # log params
    prompt: Optional[str] = None,
    task_id: Optional[str] = None,
    mode: Optional[str] = None,
    outcome: Optional[str] = None,
    iteration: int = 1,
    # analyze params
    days: int = 7,
) -> str:
    """
    Unified prompt tracking tool.

    Args:
        action: "log" to record a prompt, "analyze" to view patterns
        prompt: Prompt text to log (log action, required)
        task_id: Associated task ID (log action)
        mode: Workflow mode used (log action)
        outcome: Result of prompt (log action)
        iteration: Iteration number (log action)
        days: Days of history to analyze (analyze action)

    Returns:
        JSON string with log confirmation or analysis results
    """
    if action == "log":
        if not prompt:
            return json.dumps({"status": "error", "error": "prompt parameter required for log action"}, indent=2)
        from .prompt_iteration_tracker import log_prompt_iteration
        result = log_prompt_iteration(prompt, task_id, mode, outcome, iteration)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "analyze":
        from .prompt_iteration_tracker import analyze_prompt_iterations
        result = analyze_prompt_iterations(days)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown prompt tracking action: {action}. Use 'log' or 'analyze'.",
        }, indent=2)


def health(
    action: str = "server",
    # git params
    agent_name: Optional[str] = None,
    check_remote: bool = True,
    # docs params
    output_path: Optional[str] = None,
    create_tasks: bool = True,
    # dod params
    task_id: Optional[str] = None,
    changed_files: Optional[str] = None,
    auto_check: bool = True,
    # cicd params
    workflow_path: Optional[str] = None,
    check_runners: bool = True,
) -> str:
    """
    Unified health check tool.

    Args:
        action: "server" for server status, "git" for working copy, "docs" for documentation, "dod" for definition of done, "cicd" for CI/CD validation
        agent_name: Agent name filter (git action)
        check_remote: Check remote sync status (git action)
        output_path: Save results to file (docs, cicd actions)
        create_tasks: Create tasks for issues (docs action)
        task_id: Task to check completion for (dod action)
        changed_files: Files changed as JSON (dod action)
        auto_check: Auto-run checks (dod action)
        workflow_path: Path to workflow file (cicd action)
        check_runners: Validate runner configs (cicd action)

    Returns:
        JSON string with health check results
    """
    if action == "server":
        import time

        from ..utils import find_project_root

        project_root = find_project_root()
        version = "unknown"
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            import re
            content = pyproject.read_text()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                version = match.group(1)

        result = {
            "status": "operational",
            "version": version,
            "project_root": str(project_root),
            "timestamp": time.time(),
        }
        return json.dumps(result, indent=2)
    elif action == "git":
        from .working_copy_health import check_working_copy_health
        result = check_working_copy_health(agent_name=agent_name, check_remote=check_remote)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "docs":
        from .docs_health import check_documentation_health
        result = check_documentation_health(output_path, create_tasks)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "dod":
        from .definition_of_done import check_definition_of_done
        result = check_definition_of_done(task_id, changed_files, auto_check, output_path)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "cicd":
        from .ci_cd_validation import validate_ci_cd_workflow
        result = validate_ci_cd_workflow(workflow_path, check_runners, output_path)
        # Result might already be a string, or might be a dict
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown health action: {action}. Use 'server', 'git', 'docs', 'dod', or 'cicd'.",
        }, indent=2)


def report(
    action: str = "overview",
    # common params
    output_format: str = "text",
    output_path: Optional[str] = None,
    # scorecard params
    include_recommendations: bool = True,
    # briefing params
    overall_score: float = 50.0,
    security_score: float = 50.0,
    testing_score: float = 50.0,
    documentation_score: float = 50.0,
    completion_score: float = 50.0,
    alignment_score: float = 50.0,
    # prd params
    project_name: Optional[str] = None,
    include_architecture: bool = True,
    include_metrics: bool = True,
    include_tasks: bool = True,
) -> str:
    """
    Unified report generation tool.

    Args:
        action: "overview" for project overview, "scorecard" for health metrics, "briefing" for advisor wisdom, "prd" for requirements doc
        output_format: Output format (text, json, markdown)
        output_path: Save results to file
        include_recommendations: Include recommendations (scorecard action)
        overall_score: Overall project score (briefing action)
        security_score: Security metric score (briefing action)
        testing_score: Testing metric score (briefing action)
        documentation_score: Documentation score (briefing action)
        completion_score: Completion score (briefing action)
        alignment_score: Alignment score (briefing action)
        project_name: Project name override (prd action)
        include_architecture: Include architecture section (prd action)
        include_metrics: Include metrics section (prd action)
        include_tasks: Include tasks section (prd action)

    Returns:
        Generated report
    """
    try:
        if action == "overview":
            from .project_overview import generate_project_overview
            result = generate_project_overview(output_format, output_path)
        elif action == "scorecard":
            from .project_scorecard import generate_project_scorecard
            result = generate_project_scorecard(output_format, include_recommendations, output_path)
        elif action == "briefing":
            # Use devwisdom-go MCP server instead of direct import
            from ..utils.wisdom_client import get_daily_briefing
            metric_scores = {
                "security": security_score,
                "testing": testing_score,
                "documentation": documentation_score,
                "completion": completion_score,
                "alignment": alignment_score,
            }
            result = get_daily_briefing(overall_score, metric_scores)
            # Convert dict to JSON string if needed
            if isinstance(result, dict):
                result = json.dumps(result, indent=2)
        elif action == "prd":
            from .prd_generator import generate_prd
            result = generate_prd(project_name, include_architecture, include_metrics, include_tasks, output_path)
        else:
            result = {
                "status": "error",
                "error": f"Unknown report action: {action}. Use 'overview', 'scorecard', 'briefing', or 'prd'.",
            }
        
        # Ensure we always return a JSON string
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"result": str(result)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# advisor_audio tool removed - migrated to devwisdom-go MCP server
# Use devwisdom MCP server tools directly for voice synthesis and podcast generation


def task_analysis(
    action: str = "duplicates",
    # duplicates params
    similarity_threshold: float = 0.85,
    auto_fix: bool = False,
    # tags params
    dry_run: bool = True,
    custom_rules: Optional[str] = None,
    remove_tags: Optional[str] = None,
    # hierarchy params
    output_format: str = "text",
    include_recommendations: bool = True,
    # dependencies params (uses output_format)
    # parallelization params (uses output_format)
    # common
    output_path: Optional[str] = None,
) -> str:
    """
    Unified task analysis tool.

    Args:
        action: "duplicates" to find duplicates, "tags" for tag cleanup, "hierarchy" for structure analysis,
                "dependencies" for dependency chain analysis, "parallelization" for parallel execution optimization
        similarity_threshold: Threshold for duplicate detection (duplicates action)
        auto_fix: Auto-merge duplicates (duplicates action)
        dry_run: Preview changes without applying (tags action)
        custom_rules: Custom tag rename rules as JSON (tags action)
        remove_tags: Tags to remove as JSON list (tags action)
        output_format: Output format - text, json, or markdown (hierarchy/dependencies/parallelization actions)
        include_recommendations: Include recommendations (hierarchy action)
        output_path: Save results to file

    Returns:
        JSON string with analysis results
    """
    if action == "duplicates":
        from .duplicate_detection import detect_duplicate_tasks
        result = detect_duplicate_tasks(similarity_threshold, auto_fix, output_path)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "tags":
        from .tag_consolidation import consolidate_tags
        result = consolidate_tags(dry_run, custom_rules, remove_tags, output_path)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "hierarchy":
        from .task_hierarchy_analyzer import analyze_task_hierarchy
        result = analyze_task_hierarchy(output_format, output_path, include_recommendations)
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    elif action == "dependencies":
        from .analyze_todo2_dependencies import analyze_todo2_dependencies
        result = analyze_todo2_dependencies(output_format, output_path)
        return result if isinstance(result, str) else json.dumps(result, indent=2)
    elif action == "parallelization":
        from .optimize_todo2_parallelization import optimize_todo2_parallelization
        result = optimize_todo2_parallelization(output_format, output_path)
        return result if isinstance(result, str) else json.dumps(result, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown task_analysis action: {action}. Use 'duplicates', 'tags', 'hierarchy', 'dependencies', or 'parallelization'.",
        }, indent=2)


async def testing_async(
    action: str = "run",
    # run params
    test_path: Optional[str] = None,
    test_framework: str = "auto",
    verbose: bool = True,
    coverage: bool = False,
    # coverage params
    coverage_file: Optional[str] = None,
    min_coverage: int = 80,
    format: str = "html",
    # suggest params
    target_file: Optional[str] = None,
    min_confidence: float = 0.7,
    # validate params
    framework: Optional[str] = None,
    # common
    output_path: Optional[str] = None,
    ctx: Optional[Any] = None,
) -> str:
    """
    Unified testing tool (async with progress).

    Args:
        action: "run" to execute tests, "coverage" to analyze coverage, "suggest" to suggest test cases, "validate" to validate test structure
        test_path: Path to test file/directory (run action)
        test_framework: pytest, unittest, ctest, or auto (run action)
        verbose: Show detailed output (run action)
        coverage: Generate coverage during test run (run action)
        coverage_file: Path to coverage file (coverage action)
        min_coverage: Minimum coverage threshold (coverage action)
        format: Report format - html, json, terminal (coverage action)
        target_file: File to analyze for suggestions (suggest action)
        min_confidence: Minimum confidence threshold for suggestions (suggest action, default: 0.7)
        framework: Expected framework for validation (validate action, default: auto)
        output_path: Save results to file
        ctx: FastMCP Context for progress reporting (optional)

    Returns:
        JSON string with test, coverage, suggestion, or validation results
    """
    if action == "run":
        from .run_tests import run_tests_async
        result = await run_tests_async(test_path, test_framework, verbose, coverage, output_path, ctx)
        # Result should already be a string, but ensure it is
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    elif action == "coverage":
        from .test_coverage import analyze_test_coverage
        result = analyze_test_coverage(coverage_file, min_coverage, output_path, format)
        # Result should already be a string, but ensure it is
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    elif action == "suggest":
        from .test_suggestions import suggest_test_cases
        result = suggest_test_cases(target_file, test_framework, min_confidence, output_path)
        # Result should already be a string, but ensure it is
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    elif action == "validate":
        from .test_validation import validate_test_structure
        result = validate_test_structure(test_path, framework, output_path)
        # Result should already be a string, but ensure it is
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown testing action: {action}. Use 'run', 'coverage', 'suggest', or 'validate'.",
        }, indent=2)


def testing(
    action: str = "run",
    # run params
    test_path: Optional[str] = None,
    test_framework: str = "auto",
    verbose: bool = True,
    coverage: bool = False,
    # coverage params
    coverage_file: Optional[str] = None,
    min_coverage: int = 80,
    format: str = "html",
    # suggest params
    target_file: Optional[str] = None,
    min_confidence: float = 0.7,
    # validate params
    framework: Optional[str] = None,
    # common
    output_path: Optional[str] = None,
    ctx: Optional[Any] = None,
) -> str:
    """
    Unified testing tool (sync wrapper).

    Args:
        action: "run" to execute tests, "coverage" to analyze coverage, "suggest" to suggest test cases, "validate" to validate test structure
        test_path: Path to test file/directory (run/validate action)
        test_framework: pytest, unittest, ctest, or auto (run/suggest action)
        verbose: Show detailed output (run action)
        coverage: Generate coverage during test run (run action)
        coverage_file: Path to coverage file (coverage action)
        min_coverage: Minimum coverage threshold (coverage action)
        format: Report format - html, json, terminal (coverage action)
        target_file: File to analyze for suggestions (suggest action)
        min_confidence: Minimum confidence threshold for suggestions (suggest action, default: 0.7)
        framework: Expected framework for validation (validate action, default: auto)
        output_path: Save results to file
        ctx: FastMCP Context for progress reporting (optional)

    Returns:
        JSON string with test, coverage, suggestion, or validation results
    """
    # Check if we're in an async context using try/except/else pattern
    # This ensures the intentional RuntimeError is raised in else block, not caught
    try:
        asyncio.get_running_loop()
        # If we get here, we're in an async context - raise helpful error
        raise RuntimeError(
            "testing() cannot be called from an async context. "
            "Use testing_async() instead and await it."
        )
    except RuntimeError as e:
        # Re-raise if it's our intentional error
        if "testing_async()" in str(e) or "async context" in str(e).lower():
            raise
        # Otherwise, no running loop - safe to use asyncio.run()
        result = asyncio.run(testing_async(action, test_path, test_framework, verbose, coverage, coverage_file, min_coverage, format, target_file, min_confidence, framework, output_path, ctx))
    # Convert dict to JSON string
    return json.dumps(result, indent=2) if isinstance(result, dict) else result


def lint(
    action: str = "run",
    # run params
    path: Optional[str] = None,
    linter: str = "ruff",
    fix: bool = False,
    analyze: bool = True,
    select: Optional[str] = None,
    ignore: Optional[str] = None,
    # analyze params
    problems_json: Optional[str] = None,
    include_hints: bool = True,
    # common
    output_path: Optional[str] = None,
) -> str:
    """
    Unified linting tool.

    Args:
        action: "run" to execute linter, "analyze" to analyze problems
        path: File or directory to lint (run action)
        linter: "ruff" or "flake8" (run action)
        fix: Auto-fix issues (run action)
        analyze: Run analyze_problems on results (run action)
        select: Rule codes to enable (run action)
        ignore: Rule codes to ignore (run action)
        problems_json: JSON string of problems to analyze (analyze action)
        include_hints: Include resolution hints (analyze action)
        output_path: Save results to file

    Returns:
        JSON string with linting or analysis results
    """
    if action == "run":
        from .linter import run_linter
        result = run_linter(path, linter, fix, analyze, select, ignore)
        # Result might already be a string, or might be a dict
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    elif action == "analyze":
        if not problems_json:
            return json.dumps({
                "status": "error",
                "error": "problems_json is required for analyze action",
            }, indent=2)
        from .problems_advisor import analyze_problems_tool
        result = analyze_problems_tool(problems_json, include_hints, output_path)
        # Result should already be a string, but ensure it is
        if isinstance(result, str):
            return result
        return json.dumps(result, indent=2)
    else:
        return {
            "status": "error",
            "error": f"Unknown lint action: {action}. Use 'run' or 'analyze'.",
        }


def memory(
    action: str = "search",
    # save params
    title: Optional[str] = None,
    content: Optional[str] = None,
    category: str = "insight",
    task_id: Optional[str] = None,
    metadata: Optional[str] = None,  # JSON string
    # recall params
    include_related: bool = True,
    # search params
    query: Optional[str] = None,
    limit: int = 10,
) -> str:
    """
    Unified memory management tool.

    Args:
        action: "save" to store insight, "recall" to get task context, "search" to find memories
        title: Memory title (save action, required)
        content: Memory content (save action, required)
        category: One of: debug, research, architecture, preference, insight (save action)
        task_id: Task ID to link memory to (save action) or recall context for (recall action)
        metadata: Additional metadata as JSON string (save action)
        include_related: Include related task memories (recall action)
        query: Search query text (search action)
        limit: Maximum results (search action)

    Returns:
        JSON string with memory operation results
    """
    if action == "save":
        if not title or not content:
            return json.dumps({
                "success": False,
                "error": "title and content are required for save action",
            }, indent=2)
        from .session_memory import save_session_insight
        meta = None
        if metadata:
            try:
                meta = json.loads(metadata)
            except json.JSONDecodeError:
                return json.dumps({"success": False, "error": "Invalid metadata JSON"}, indent=2)
        result = save_session_insight(title, content, category, task_id, meta)
        # Ensure we always return a JSON string
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"result": str(result)}, indent=2)
    elif action == "recall":
        if not task_id:
            return json.dumps({
                "success": False,
                "error": "task_id is required for recall action",
            }, indent=2)
        from .session_memory import recall_task_context
        result = recall_task_context(task_id, include_related)
        # Ensure we always return a JSON string
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"result": str(result)}, indent=2)
    elif action == "search":
        if not query:
            return json.dumps({
                "success": False,
                "error": "query is required for search action",
            }, indent=2)
        from .session_memory import search_session_memories
        result = search_session_memories(query, category if category != "insight" else None, limit)
        # Ensure we always return a JSON string
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"result": str(result)}, indent=2)
    else:
        return json.dumps({
            "success": False,
            "error": f"Unknown memory action: {action}. Use 'save', 'recall', or 'search'.",
        }, indent=2)


def context(
    action: str = "summarize",
    # summarize action params
    data: Optional[str] = None,
    level: str = "brief",
    tool_type: Optional[str] = None,
    max_tokens: Optional[int] = None,
    include_raw: bool = False,
    # budget action params
    items: Optional[str] = None,
    budget_tokens: int = 4000,
    # batch action params
    combine: bool = True,
) -> str:
    """
    Unified context management tool.

    Consolidates context summarization, budgeting, and batch operations.

    Args:
        action: "summarize" for single item, "budget" for token analysis, "batch" for multiple items
        data: JSON string to summarize (summarize action)
        level: Summarization level - "brief", "detailed", "key_metrics", "actionable" (summarize action)
        tool_type: Tool type hint for smarter summarization (summarize action)
        max_tokens: Maximum tokens for output (summarize action)
        include_raw: Include original data in response (summarize action)
        items: JSON array of items to analyze (budget/batch actions)
        budget_tokens: Target token budget (budget action)
        combine: Merge summaries into combined view (batch action)

    Returns:
        JSON with context operation results
    """
    if action == "summarize":
        if not data:
            return json.dumps({
                "status": "error",
                "error": "data parameter required for summarize action",
            }, indent=2)
        from .context_summarizer import summarize_context
        return summarize_context(data, level, tool_type, max_tokens, include_raw)
    
    elif action == "budget":
        if not items:
            return json.dumps({
                "status": "error",
                "error": "items parameter required for budget action",
            }, indent=2)
        import json as json_lib
        parsed_items = json_lib.loads(items) if isinstance(items, str) else items
        from .context_summarizer import estimate_context_budget
        return estimate_context_budget(parsed_items, budget_tokens)
    
    elif action == "batch":
        if not items:
            return json.dumps({
                "status": "error",
                "error": "items parameter required for batch action",
            }, indent=2)
        import json as json_lib
        parsed_items = json_lib.loads(items) if isinstance(items, str) else items
        from .context_summarizer import batch_summarize
        return batch_summarize(parsed_items, level, combine)
    
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown context action: {action}. Use 'summarize', 'budget', or 'batch'.",
        }, indent=2)


def tool_catalog(
    action: str = "list",
    # list action params
    category: Optional[str] = None,
    persona: Optional[str] = None,
    include_examples: bool = True,
    # help action params
    tool_name: Optional[str] = None,
) -> str:
    """
    Unified tool catalog tool.

    Consolidates tool catalog browsing and help operations.

    Args:
        action: "list" for tool catalog, "help" for specific tool documentation
        category: Filter by category (list action)
        persona: Filter by persona (list action)
        include_examples: Include example prompts (list action)
        tool_name: Name of tool to get help for (help action)

    Returns:
        JSON with tool catalog results
    """
    if action == "list":
        from .hint_catalog import list_tools
        return list_tools(category, persona, include_examples)
    
    elif action == "help":
        if not tool_name:
            return json.dumps({
                "status": "error",
                "error": "tool_name parameter required for help action",
            }, indent=2)
        from .hint_catalog import get_tool_help
        return get_tool_help(tool_name)
    
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool_catalog action: {action}. Use 'list' or 'help'.",
        }, indent=2)


def workflow_mode(
    action: str = "focus",
    # focus action params
    mode: Optional[str] = None,
    enable_group: Optional[str] = None,
    disable_group: Optional[str] = None,
    status: bool = False,
    # suggest action params
    text: Optional[str] = None,
    auto_switch: bool = False,
) -> str:
    """
    Unified workflow mode management tool.

    Consolidates workflow mode operations: focus, suggestions, and usage statistics.

    Args:
        action: "focus" to manage modes/groups, "suggest" to get mode suggestions, "stats" for usage analytics
        mode: Workflow mode to switch to (focus action)
        enable_group: Specific group to enable (focus action)
        disable_group: Specific group to disable (focus action)
        status: If True, return current status without changes (focus action)
        text: Optional text to analyze for mode suggestion (suggest action)
        auto_switch: If True, automatically switch to suggested mode (suggest action)

    Returns:
        JSON with workflow mode operation results
    """
    if action == "focus":
        from .dynamic_tools import focus_mode
        return focus_mode(mode, enable_group, disable_group, status)
    
    elif action == "suggest":
        from .dynamic_tools import suggest_mode
        return suggest_mode(text, auto_switch)
    
    elif action == "stats":
        from .dynamic_tools import get_tool_usage_stats
        return get_tool_usage_stats()
    
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown workflow_mode action: {action}. Use 'focus', 'suggest', or 'stats'.",
        }, indent=2)


def recommend(
    action: str = "model",
    # model action params
    task_description: Optional[str] = None,
    task_type: Optional[str] = None,
    optimize_for: str = "quality",
    include_alternatives: bool = True,
    # workflow action params
    task_id: Optional[str] = None,
    include_rationale: bool = True,
    # advisor action params
    metric: Optional[str] = None,
    tool: Optional[str] = None,
    stage: Optional[str] = None,
    score: float = 50.0,
    context: str = "",
    log: bool = True,
    session_mode: Optional[str] = None,
) -> str:
    """
    Unified recommendation tool.

    Consolidates model recommendations, workflow mode suggestions, and advisor consultations.

    Args:
        action: "model" for AI model recommendations, "workflow" for mode suggestions, "advisor" for wisdom
        task_description: Description of the task (model/workflow actions)
        task_type: Optional explicit task type (model action)
        optimize_for: "quality", "speed", or "cost" (model action)
        include_alternatives: Include alternative recommendations (model action)
        task_id: Optional Todo2 task ID to analyze (workflow action)
        include_rationale: Whether to include detailed reasoning (workflow action)
        metric: Scorecard metric to get advice for (advisor action)
        tool: Tool to get advice for (advisor action)
        stage: Workflow stage to get advice for (advisor action)
        score: Current score for wisdom tier selection (advisor action, 0-100)
        context: What you're working on (advisor action)
        log: Whether to log consultation (advisor action)
        session_mode: Inferred session mode for mode-aware guidance (advisor action)

    Returns:
        JSON with recommendation results (model/workflow) or dict (advisor)
    """
    if action == "model":
        from .model_recommender import recommend_model
        result = recommend_model(task_description, task_type, optimize_for, include_alternatives)
        # Ensure we always return a JSON string
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"result": str(result)}, indent=2)
    
    elif action == "workflow":
        from .workflow_recommender import recommend_workflow_mode
        result = recommend_workflow_mode(task_description, task_id, include_rationale)
        # Ensure we always return a JSON string
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            return json.dumps(result, indent=2)
        else:
            return json.dumps({"result": str(result)}, indent=2)
    
    elif action == "advisor":
        # Use devwisdom-go MCP server instead of direct import
        from ..utils.wisdom_client import consult_advisor
        # Get session mode if not provided
        if session_mode is None:
            try:
                from ..resources.session import get_session_mode_resource
                import json as json_lib
                mode_resource_json = get_session_mode_resource()
                mode_data = json_lib.loads(mode_resource_json)
                session_mode = mode_data.get("mode") or mode_data.get("inferred_mode")
            except Exception:
                pass  # Fallback gracefully if mode inference unavailable
        
        result = consult_advisor(
            metric=metric,
            tool=tool,
            stage=stage,
            score=score,
            context=context
        )
        # Convert dict to JSON string if needed
        if isinstance(result, dict):
            return json.dumps(result, indent=2)
        return result if result else json.dumps({"error": "Failed to consult advisor"}, indent=2)
    
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown recommend action: {action}. Use 'model', 'workflow', or 'advisor'.",
        }, indent=2)


def task_discovery(
    action: str = "all",
    # comments params
    file_patterns: Optional[str] = None,  # JSON list of glob patterns
    include_fixme: bool = True,
    # markdown params
    doc_path: Optional[str] = None,
    # orphans params (uses task_analysis internally)
    # common
    output_path: Optional[str] = None,
    create_tasks: bool = False,
) -> str:
    """
    Unified task discovery tool.

    Finds tasks from various sources in the codebase.

    Args:
        action: "comments" for TODO/FIXME in code, "markdown" for task lists in docs,
                "orphans" for orphaned Todo2 tasks, "all" for everything
        file_patterns: JSON list of glob patterns for code scanning (comments action)
        include_fixme: Include FIXME comments (comments action)
        doc_path: Path to scan for markdown tasks (markdown action)
        output_path: Save results to file
        create_tasks: Auto-create Todo2 tasks from discoveries

    Returns:
        JSON string with discovery results and found tasks
    """
    import re
    from pathlib import Path

    from ..utils import find_project_root

    project_root = find_project_root()
    results = {
        "action": action,
        "discoveries": [],
        "summary": {},
    }

    def scan_comments():
        """Scan code for TODO/FIXME comments."""
        discoveries = []
        patterns = ["**/*.py", "**/*.js", "**/*.ts", "**/*.tsx", "**/*.jsx"]
        if file_patterns:
            try:
                patterns = json.loads(file_patterns)
            except json.JSONDecodeError:
                pass

        todo_pattern = re.compile(r'#\s*(TODO|FIXME)[\s:]+(.+)', re.IGNORECASE) if include_fixme else re.compile(r'#\s*TODO[\s:]+(.+)', re.IGNORECASE)

        for pattern in patterns:
            for file_path in project_root.glob(pattern):
                if any(skip in str(file_path) for skip in ['.git', 'node_modules', '__pycache__', '.venv', 'build']):
                    continue
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for line_num, line in enumerate(content.split('\n'), 1):
                        match = todo_pattern.search(line)
                        if match:
                            discoveries.append({
                                "type": match.group(1).upper() if include_fixme else "TODO",
                                "text": match.group(2).strip() if include_fixme else match.group(1).strip(),
                                "file": str(file_path.relative_to(project_root)),
                                "line": line_num,
                                "source": "comment",
                            })
                except Exception:
                    continue
        return discoveries

    def scan_markdown():
        """Scan markdown files for task lists."""
        discoveries = []
        search_path = Path(doc_path) if doc_path else project_root / "docs"
        if not search_path.exists():
            search_path = project_root

        task_pattern = re.compile(r'^[\s]*[-*]\s*\[([ xX])\]\s*(.+)', re.MULTILINE)

        for md_file in search_path.rglob("*.md"):
            if any(skip in str(md_file) for skip in ['.git', 'node_modules']):
                continue
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                for match in task_pattern.finditer(content):
                    is_done = match.group(1).lower() == 'x'
                    if not is_done:  # Only uncompleted tasks
                        discoveries.append({
                            "type": "MARKDOWN_TASK",
                            "text": match.group(2).strip(),
                            "file": str(md_file.relative_to(project_root)),
                            "completed": is_done,
                            "source": "markdown",
                        })
            except Exception:
                continue
        return discoveries

    def find_orphans():
        """Find orphaned Todo2 tasks."""
        from .task_hierarchy_analyzer import analyze_task_hierarchy
        result = analyze_task_hierarchy(output_format="json", include_recommendations=False)
        orphans = result.get("networkx_analysis", {}).get("orphans", [])
        return [{"type": "ORPHAN", "task_id": o, "source": "todo2"} for o in orphans]

    # Execute based on source
    if action in ["comments", "all"]:
        results["discoveries"].extend(scan_comments())
    if action in ["markdown", "all"]:
        results["discoveries"].extend(scan_markdown())
    if action in ["orphans", "all"]:
        results["discoveries"].extend(find_orphans())

    # Summary
    results["summary"] = {
        "total": len(results["discoveries"]),
        "by_source": {},
        "by_type": {},
    }
    for d in results["discoveries"]:
        src = d.get("source", "unknown")
        typ = d.get("type", "unknown")
        results["summary"]["by_source"][src] = results["summary"]["by_source"].get(src, 0) + 1
        results["summary"]["by_type"][typ] = results["summary"]["by_type"].get(typ, 0) + 1

    # Save if requested
    if output_path:
        Path(output_path).write_text(json.dumps(results, indent=2))

    # Always return JSON string
    return json.dumps(results, indent=2)


def automation(
    action: str = "daily",
    # daily params
    tasks: Optional[list[str]] = None,
    include_slow: bool = False,
    # nightly params
    max_tasks_per_host: int = 5,
    max_parallel_tasks: int = 10,
    priority_filter: Optional[str] = None,
    tag_filter: Optional[list[str]] = None,
    # sprint params
    max_iterations: int = 10,
    auto_approve: bool = True,
    extract_subtasks: bool = True,
    run_analysis_tools: bool = True,
    run_testing_tools: bool = True,
    # discover params
    min_value_score: float = 0.7,
    # common params
    dry_run: bool = False,
    output_path: Optional[str] = None,
    notify: bool = False,
) -> str:
    """
    Unified automation tool.

    Args:
        action: "daily" for daily maintenance, "nightly" for task processing,
                "sprint" for sprint automation, "discover" for opportunity discovery
        tasks: List of task IDs to run (daily action)
        include_slow: Include slow tasks (daily action)
        max_tasks_per_host: Max tasks per host (nightly action)
        max_parallel_tasks: Max parallel tasks (nightly action)
        priority_filter: Filter by priority (nightly action)
        tag_filter: Filter by tags (nightly action)
        max_iterations: Max sprint iterations (sprint action)
        auto_approve: Auto-approve tasks (sprint action)
        extract_subtasks: Extract subtasks (sprint action)
        run_analysis_tools: Run analysis tools (sprint action)
        run_testing_tools: Run testing tools (sprint action)
        min_value_score: Min value score threshold (discover action)
        dry_run: Preview without applying
        output_path: Save results to file
        notify: Send notifications (nightly/sprint actions)

    Returns:
        JSON string with automation results
    """
    if action == "daily":
        from .daily_automation import run_daily_automation
        result = run_daily_automation(tasks, include_slow, dry_run, output_path)
        return result if isinstance(result, str) else json.dumps(result, indent=2)
    
    elif action == "nightly":
        from .nightly_task_automation import run_nightly_task_automation
        result = run_nightly_task_automation(
            max_tasks_per_host=max_tasks_per_host,
            max_parallel_tasks=max_parallel_tasks,
            priority_filter=priority_filter,
            tag_filter=tag_filter,
            dry_run=dry_run,
            notify=notify,  # sprint_automation uses notify parameter
        )
        return result if isinstance(result, str) else json.dumps(result, indent=2)
    
    elif action == "sprint":
        from .sprint_automation import sprint_automation
        result = sprint_automation(
            max_iterations=max_iterations,
            auto_approve=auto_approve,
            extract_subtasks=extract_subtasks,
            run_analysis_tools=run_analysis_tools,
            run_testing_tools=run_testing_tools,
            priority_filter=priority_filter,
            tag_filter=tag_filter,
            dry_run=dry_run,
            output_path=output_path,
            notify=notify,
        )
        return result if isinstance(result, str) else json.dumps(result, indent=2)
    
    elif action == "discover":
        from .automation_opportunities import find_automation_opportunities
        result = find_automation_opportunities(min_value_score, output_path)
        return result if isinstance(result, str) else json.dumps(result, indent=2)
    
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown automation action: {action}. Use 'daily', 'nightly', 'sprint', or 'discover'.",
        }, indent=2)


def estimation(
    action: str = "estimate",
    # estimate params
    name: Optional[str] = None,
    details: str = "",
    tags: Optional[str] = None,
    priority: str = "medium",
    use_historical: bool = True,
    detailed: bool = False,
    use_mlx: bool = True,
    mlx_weight: float = 0.3,
    # analyze params (no additional params needed)
    # stats params (no additional params needed)
) -> str:
    """
    Unified task duration estimation tool.

    Args:
        action: "estimate" for duration estimate, "analyze" for accuracy analysis,
                "stats" for statistical summary
        name: Task name (estimate action)
        details: Task details (estimate action)
        tags: Comma-separated tags (estimate action)
        priority: Task priority (estimate action)
        use_historical: Use historical data (estimate action)
        detailed: Return detailed breakdown (estimate action)
        use_mlx: Use MLX enhancement (estimate action)
        mlx_weight: MLX weight in hybrid estimate (estimate action)

    Returns:
        JSON string with estimation results
    """
    if action == "estimate":
        if not name:
            return json.dumps({"status": "error", "error": "name parameter required for estimate action"}, indent=2)
        
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        
        # Try MLX-enhanced estimator first (if enabled)
        if use_mlx:
            try:
                from .mlx_task_estimator import (
                    estimate_task_duration_mlx_enhanced as _estimate_mlx_simple,
                    estimate_task_duration_mlx_enhanced_detailed,
                )
                
                if detailed:
                    result = estimate_task_duration_mlx_enhanced_detailed(
                        name=name,
                        details=details,
                        tags=tag_list,
                        priority=priority,
                        use_historical=use_historical,
                        use_mlx=True,
                        mlx_weight=mlx_weight,
                    )
                    return json.dumps(result, indent=2) if isinstance(result, dict) else result
                else:
                    hours = _estimate_mlx_simple(
                        name=name,
                        details=details,
                        tags=tag_list,
                        priority=priority,
                        use_historical=use_historical,
                        use_mlx=True,
                        mlx_weight=mlx_weight,
                    )
                    return json.dumps({
                        "estimate_hours": hours,
                        "name": name,
                        "priority": priority,
                        "method": "mlx_enhanced",
                    }, indent=2)
            except ImportError:
                # MLX not available, fall through to statistical-only
                pass
        
        # Fallback to statistical-only estimator
        from .task_duration_estimator import (
            estimate_task_duration as _estimate_simple,
            estimate_task_duration_detailed,
        )
        
        if detailed:
            result = estimate_task_duration_detailed(
                name=name,
                details=details,
                tags=tag_list,
                priority=priority,
                use_historical=use_historical,
            )
            return json.dumps(result, indent=2) if isinstance(result, dict) else result
        else:
            hours = _estimate_simple(
                name=name,
                details=details,
                tags=tag_list,
                priority=priority,
                use_historical=use_historical,
            )
            return json.dumps({
                "estimate_hours": hours,
                "name": name,
                "priority": priority,
                "method": "statistical",
            }, indent=2)
    
    elif action == "analyze":
        from .estimation_learner import EstimationLearner
        learner = EstimationLearner()
        result = learner.analyze_estimation_accuracy()
        return json.dumps(result, indent=2) if isinstance(result, dict) else result
    
    elif action == "stats":
        from .task_duration_estimator import TaskDurationEstimator
        estimator = TaskDurationEstimator()
        stats = estimator.get_statistics()
        return json.dumps(stats, indent=2) if isinstance(stats, dict) else stats
    
    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown estimation action: {action}. Use 'estimate', 'analyze', or 'stats'.",
        }, indent=2)


def task_workflow(
    action: str = "sync",
    # sync params
    dry_run: bool = False,
    # approve params
    status: str = "Review",
    new_status: str = "Todo",
    clarification_none: bool = True,
    filter_tag: Optional[str] = None,
    task_ids: Optional[str] = None,  # JSON list
    # clarify params
    sub_action: str = "list",  # list, resolve, batch (for clarify action)
    task_id: Optional[str] = None,
    clarification_text: Optional[str] = None,
    decision: Optional[str] = None,
    decisions_json: Optional[str] = None,
    move_to_todo: bool = True,
    # clarity params
    auto_apply: bool = False,
    output_format: str = "text",
    # cleanup params
    stale_threshold_hours: float = 2.0,
    # common
    output_path: Optional[str] = None,
) -> str:
    """
    Unified task workflow management tool.

    Args:
        action: "sync" for TODO↔Todo2 sync, "approve" for bulk approval, "clarify" for clarifications,
                "clarity" for task clarity improvement, "cleanup" for stale task cleanup
        dry_run: Preview changes without applying (sync, approve, cleanup)
        status: Filter tasks by status (approve)
        new_status: Target status (approve)
        clarification_none: Only tasks without clarification (approve)
        filter_tag: Filter by tag (approve)
        task_ids: JSON list of task IDs (approve)
        sub_action: "list", "resolve", or "batch" (clarify action)
        task_id: Task to resolve (clarify)
        clarification_text: Clarification response (clarify)
        decision: Decision made (clarify)
        decisions_json: Batch decisions as JSON (clarify)
        move_to_todo: Move resolved tasks to Todo (clarify)
        auto_apply: Auto-apply improvements (clarity action)
        output_format: Output format (clarity action)
        stale_threshold_hours: Hours before task is stale (cleanup action)
        output_path: Save results to file

    Returns:
        JSON string with workflow operation results
    """
    if action == "sync":
        from .todo_sync import sync_todo_tasks
        result = sync_todo_tasks(dry_run, output_path)
        return result if isinstance(result, str) else json.dumps(result, indent=2)

    elif action == "approve":
        from .batch_task_approval import batch_approve_tasks
        ids = None
        if task_ids:
            try:
                ids = json.loads(task_ids)
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid task_ids JSON"}, indent=2)
        result = batch_approve_tasks(
            status=status,
            new_status=new_status,
            clarification_none=clarification_none,
            filter_tag=filter_tag,
            task_ids=ids,
            dry_run=dry_run,
            confirm=False,
        )
        return result if isinstance(result, str) else json.dumps(result, indent=2)

    elif action == "clarify":
        from .task_clarification_resolution import (
            list_tasks_awaiting_clarification,
            resolve_multiple_clarifications,
            resolve_task_clarification,
        )

        if sub_action == "list":
            result = list_tasks_awaiting_clarification()
        elif sub_action == "resolve":
            if not task_id:
                return json.dumps({"status": "error", "error": "task_id required for resolve"}, indent=2)
            result = resolve_task_clarification(
                task_id, clarification_text, decision, move_to_todo, dry_run
            )
        elif sub_action == "batch":
            if not decisions_json:
                return json.dumps({"status": "error", "error": "decisions_json required for batch"}, indent=2)
            try:
                decisions = json.loads(decisions_json)
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid decisions_json"}, indent=2)
            result = resolve_multiple_clarifications(decisions, move_to_todo, dry_run)
        else:
            return json.dumps({"status": "error", "error": f"Unknown sub_action: {sub_action}. Use 'list', 'resolve', or 'batch'."}, indent=2)

        return result if isinstance(result, str) else json.dumps(result, indent=2)

    elif action == "clarity":
        from .task_clarity_improver import improve_task_clarity, analyze_task_clarity
        if auto_apply:
            result = improve_task_clarity(auto_apply=True, output_path=output_path)
        else:
            result = analyze_task_clarity(output_format=output_format, output_path=output_path, dry_run=True)
        
        # Handle text format output
        if output_format == "text" and isinstance(result, dict) and "formatted_output" in result:
            return result["formatted_output"]
        return result if isinstance(result, str) else json.dumps(result, indent=2)

    elif action == "cleanup":
        from .stale_task_cleanup import cleanup_stale_tasks
        result = cleanup_stale_tasks(stale_threshold_hours, dry_run, output_path)
        return result if isinstance(result, str) else json.dumps(result, indent=2)

    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown task_workflow action: {action}. Use 'sync', 'approve', 'clarify', 'clarity', or 'cleanup'.",
        }, indent=2)


def memory_maint(
    action: str = "health",
    # gc params
    max_age_days: int = 90,
    delete_orphaned: bool = True,
    delete_duplicates: bool = True,
    scorecard_max_age_days: int = 7,
    # prune params
    value_threshold: float = 0.3,
    keep_minimum: int = 50,
    # consolidate params
    similarity_threshold: float = 0.85,
    merge_strategy: str = "newest",
    # dream params
    scope: str = "week",
    advisors: Optional[str] = None,
    generate_insights: bool = True,
    save_dream: bool = True,
    # common
    dry_run: bool = True,
    interactive: bool = True,
) -> dict[str, Any]:
    """
    Unified memory maintenance tool.

    Args:
        action: "health", "gc", "prune", "consolidate", or "dream"
        max_age_days: Delete memories older than this (gc)
        delete_orphaned: Delete orphaned memories (gc)
        delete_duplicates: Delete duplicates (gc)
        scorecard_max_age_days: Max age for scorecard memories (gc)
        value_threshold: Minimum value score to keep (prune)
        keep_minimum: Always keep at least N memories (prune)
        similarity_threshold: Title similarity threshold (consolidate)
        merge_strategy: newest, oldest, or longest (consolidate)
        scope: day, week, month, or all (dream)
        advisors: JSON list of advisor keys (dream)
        generate_insights: Generate actionable insights (dream)
        save_dream: Save dream as new memory (dream)
        dry_run: Preview without executing (default True)
        interactive: Use interactive MCP for approvals (reserved for future)

    Returns:
        JSON string with maintenance operation results
    """
    if action == "health":
        from .memory_maintenance import memory_health_check
        result = memory_health_check()
        return json.dumps(result, indent=2) if isinstance(result, dict) else result

    elif action == "gc":
        from .memory_maintenance import memory_garbage_collect
        result = memory_garbage_collect(
            max_age_days=max_age_days,
            delete_orphaned=delete_orphaned,
            delete_duplicates=delete_duplicates,
            scorecard_max_age_days=scorecard_max_age_days,
            dry_run=dry_run,
        )
        return json.dumps(result, indent=2) if isinstance(result, dict) else result

    elif action == "prune":
        from .memory_maintenance import memory_prune
        result = memory_prune(
            value_threshold=value_threshold,
            keep_minimum=keep_minimum,
            dry_run=dry_run,
        )
        return json.dumps(result, indent=2) if isinstance(result, dict) else result

    elif action == "consolidate":
        from .memory_maintenance import memory_consolidate
        result = memory_consolidate(
            similarity_threshold=similarity_threshold,
            merge_strategy=merge_strategy,
            dry_run=dry_run,
        )
        return json.dumps(result, indent=2) if isinstance(result, dict) else result

    elif action == "dream":
        from .memory_dreaming import memory_dream
        advisor_list = None
        if advisors:
            try:
                advisor_list = json.loads(advisors)
            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid advisors JSON"}, indent=2)
        result = memory_dream(
            scope=scope,
            advisors=advisor_list,
            generate_insights=generate_insights,
            save_dream=save_dream,
        )
        return json.dumps(result, indent=2) if isinstance(result, dict) else result

    else:
        return json.dumps({
            "status": "error",
            "error": f"Unknown memory_maint action: {action}. Use 'health', 'gc', 'prune', 'consolidate', or 'dream'.",
        }, indent=2)

