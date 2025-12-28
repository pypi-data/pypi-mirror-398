#!/usr/bin/env python3
"""
Project Management Automation MCP Server

Model Context Protocol server exposing project management automation tools
built on IntelligentAutomationBase.

Provides AI assistants with access to:
- Documentation health checks
- Todo2 alignment analysis
- Duplicate task detection
- Dependency security scanning
- Automation opportunity discovery
- Todo synchronization

Complementary MCP Servers:
- tractatus_thinking: Use BEFORE Exarp tools for structural analysis (WHAT)
- sequential_thinking: Use AFTER Exarp analysis for implementation workflows (HOW)

Recommended workflow:
1. tractatus_thinking → Understand problem structure
2. exarp → Analyze and automate project management tasks
3. sequential_thinking → Convert results into implementation steps
"""

import os
import sys

# Set MCP mode flag BEFORE any logging imports
# This tells our logging utilities to suppress console output
os.environ["EXARP_MCP_MODE"] = "1"

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

# Import our MCP-aware logging utilities
from .utils.logging_config import configure_logging, suppress_noisy_loggers

# Dynamic version from version.py
from .version import __version__

# Configure logging (quiet in MCP mode, verbose in CLI)
# Enable file logging for debugging MCP errors
log_file = Path(__file__).parent.parent / "mcp_server_debug.log"
logger = configure_logging("exarp", level=logging.DEBUG, log_file=log_file)
suppress_noisy_loggers()
# Re-enable our logger at DEBUG level to capture errors
logger.setLevel(logging.DEBUG)
# Also enable FastMCP error logging to file
fastmcp_logger = logging.getLogger("fastmcp")
fastmcp_logger.setLevel(logging.DEBUG)
if log_file:
    fastmcp_handler = logging.FileHandler(log_file)
    fastmcp_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    fastmcp_logger.addHandler(fastmcp_handler)

# Import security utilities
from .utils.security import (
    AccessController,
    PathValidator,
    set_access_controller,
    set_default_path_validator,
)


# Robust project root detection
def _find_project_root(start_path: Path) -> Path:
    """
    Find project root by looking for .git directory or other markers.
    Falls back to relative path detection if markers not found.
    """
    # Try environment variable first
    env_root = os.getenv("PROJECT_ROOT") or os.getenv("WORKSPACE_PATH")
    if env_root:
        root_path = Path(env_root)
        if root_path.exists():
            return root_path.resolve()

    # Try relative path detection (assumes standard structure)
    current = start_path
    for _ in range(5):  # Go up max 5 levels
        # Check for project markers
        if (current / ".git").exists() or (current / ".todo2").exists() or (current / "CMakeLists.txt").exists() or (current / "go.mod").exists():
            return current.resolve()
        if current.parent == current:  # Reached filesystem root
            break
        current = current.parent

    # Fallback to relative path (assumes project-management-automation/project_management_automation/server.py)
    return start_path.parent.parent.parent.parent.resolve()


# Add project root to path for script imports
project_root = _find_project_root(Path(__file__))
sys.path.insert(0, str(project_root))

# Initialize security controls
# Path boundary: only allow access within project root and common temp dirs
import tempfile
_temp_dir = Path(tempfile.gettempdir())  # Cross-platform temp directory
_path_validator = PathValidator(
    allowed_roots=[project_root, _temp_dir],
    allow_symlinks=False,
    blocked_patterns=[
        r"\.git(?:/|$)",  # .git directory
        r"\.env",  # Environment files
        r"\.ssh",  # SSH keys
        r"\.aws",  # AWS credentials
        r"id_rsa",  # SSH private keys
        r"\.pem$",  # Certificate files
        r"secrets?\.ya?ml",  # Secrets files
    ],
)
set_default_path_validator(_path_validator)

# Access control: default write access, customizable per deployment
_access_controller = AccessController(default_level="write")
set_access_controller(_access_controller)

logger.debug(f"Security initialized: path_boundaries={len(_path_validator.allowed_roots)} roots, access_control=write")

# Validate project ownership (compare PROJECT_ROOT with Todo2 project.path)
try:
    from .utils.todo2_utils import validate_project_ownership, get_current_project_id
    is_valid, error_msg = validate_project_ownership(project_root, warn_only=True)
    if error_msg:
        logger.warning(f"⚠️  {error_msg}")
    else:
        project_id = get_current_project_id(project_root)
        if project_id:
            logger.info(f"✅ Project ownership validated: {project_id}")
except Exception as e:
    logger.debug(f"Project ownership validation skipped: {e}")

# Add server directory to path for absolute imports when run as script
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

# Import error handling (handle both relative and absolute imports)
try:
    # Try relative imports first (when run as module)
    try:
        from .error_handler import (
            AutomationError,
            ErrorCode,
            format_error_response,
            format_success_response,
            handle_automation_error,
            log_automation_execution,
        )
    except ImportError:
        # Fallback to absolute imports (when run as script)
        from error_handler import (
            AutomationError,
            ErrorCode,
            format_error_response,
            format_success_response,
            handle_automation_error,
            log_automation_execution,
        )

    ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    ERROR_HANDLING_AVAILABLE = False
    logger.warning(f"Error handling module not available - using basic error handling: {e}")

# Import tool wrapper utility (ensures all tools return JSON strings per FastMCP requirements)
try:
    from .utils.tool_wrapper import ensure_json_string, wrap_tool_result
    TOOL_WRAPPER_AVAILABLE = True
except ImportError:
    try:
        from utils.tool_wrapper import ensure_json_string, wrap_tool_result
        TOOL_WRAPPER_AVAILABLE = True
    except ImportError:
        TOOL_WRAPPER_AVAILABLE = False
        logger.warning("Tool wrapper utility not available - tools may have return type issues")
        # Fallback implementation
        def wrap_tool_result(result):
            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2) if isinstance(result, (dict, list)) else json.dumps({"result": str(result)}, indent=2)
        
        def ensure_json_string(func):
            """Decorator to ensure function returns JSON string."""
            import functools
            import asyncio
            import inspect
            
            if inspect.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    try:
                        result = await func(*args, **kwargs)
                        return wrap_tool_result(result)
                    except Exception as e:
                        return json.dumps({"error": str(e)}, indent=2)
                return async_wrapper
            else:
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    try:
                        result = func(*args, **kwargs)
                        return wrap_tool_result(result)
                    except Exception as e:
                        return json.dumps({"error": str(e)}, indent=2)
                return wrapper

# Try to import MCP - Phase 2 tools complete, MCP installation needed for runtime
# Check for environment variable to force stdio mode (bypass FastMCP)
FORCE_STDIO = os.environ.get("EXARP_FORCE_STDIO", "").lower() in ("1", "true", "yes")

# Try FastMCP first, fall back to stdio if FastMCP is not available or forced
MCP_AVAILABLE = False
USE_STDIO = False
FastMCP = None

if FORCE_STDIO:
    # Force stdio mode - skip FastMCP entirely
    logger.info("EXARP_FORCE_STDIO=1 - forcing stdio server mode (bypassing FastMCP)")
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool, Prompt, PromptArgument

        MCP_AVAILABLE = True
        USE_STDIO = True
        FastMCP = None
        Server = Server
        stdio_server = stdio_server
        logger.info("MCP stdio server initialized (forced mode)")
    except ImportError:
        logger.warning("MCP not installed - server structure ready, install with: uv sync (or uv pip install mcp>=1.0.0)")
        MCP_AVAILABLE = False
        Server = None
        stdio_server = None
        Tool = None
        TextContent = None
else:
    # Normal mode: Try FastMCP first, fall back to stdio
    try:
        # Try FastMCP from mcp package (may be available in newer versions)
        from mcp import FastMCP
        from mcp.types import TextContent, Tool

        MCP_AVAILABLE = True
        USE_STDIO = False
        Server = None
        stdio_server = None
    except ImportError:
        try:
            # Try FastMCP from separate fastmcp package
            from fastmcp import FastMCP
            from mcp.types import TextContent, Tool

            MCP_AVAILABLE = True
            USE_STDIO = False
            Server = None
            stdio_server = None
        except ImportError:
            try:
                from mcp.server import Server
                from mcp.server.stdio import stdio_server

                # For stdio server, we'll construct Tool objects manually
                from mcp.types import TextContent, Tool, Prompt, PromptArgument

                MCP_AVAILABLE = True
                USE_STDIO = True
                FastMCP = None
                logger.info("MCP stdio server available - using stdio server (FastMCP not available)")
            except ImportError:
                logger.warning("MCP not installed - server structure ready, install with: uv sync (or uv pip install mcp>=1.0.0)")
                MCP_AVAILABLE = False
                Server = None
                stdio_server = None
                Tool = None
                TextContent = None

# Logging already configured above

# Initialize availability flags
TOOLS_AVAILABLE = False
RESOURCES_AVAILABLE = False

# Initialize MCP server
mcp = None
stdio_server_instance = None
if MCP_AVAILABLE:
    # Suppress FastMCP/stdio server initialization logging
    # FastMCP logs "Starting MCP server" messages to stderr during initialization
    # We temporarily redirect stderr to suppress these during initialization
    import contextlib
    import io

    @contextlib.contextmanager
    def suppress_fastmcp_output():
        """Temporarily suppress stdout and stderr during FastMCP initialization"""
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        try:
            # Redirect both stdout and stderr to suppress FastMCP banner and startup messages
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            yield
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

    # Import lifespan for FastMCP
    try:
        from .lifespan import exarp_lifespan
        LIFESPAN_AVAILABLE = True
    except ImportError:
        exarp_lifespan = None
        LIFESPAN_AVAILABLE = False

    # Suppress FastMCP output during initialization (banner, startup messages)
    with suppress_fastmcp_output():
        if not USE_STDIO and FastMCP:
            # Initialize with lifespan if available
            if LIFESPAN_AVAILABLE and exarp_lifespan:
                mcp = FastMCP("exarp", lifespan=exarp_lifespan)
            else:
                mcp = FastMCP("exarp")
        elif USE_STDIO and Server:
            # Initialize stdio server
            stdio_server_instance = Server("exarp")
            # Note: Tools will be registered below using stdio server API

    # Log initialization after suppressing FastMCP output
    if not USE_STDIO and FastMCP and mcp:
        pass  # Version info logged after banner in main()
    elif USE_STDIO and Server and stdio_server_instance:
        pass  # Version info logged after banner

    # Re-apply logger suppression after initialization (in case FastMCP added new loggers)
    suppress_noisy_loggers()

    # ═══════════════════════════════════════════════════════════════════════
    # MIDDLEWARE REGISTRATION (FastMCP 2 feature)
    # ═══════════════════════════════════════════════════════════════════════
    if not USE_STDIO and FastMCP and mcp:
        try:
            from .middleware import LoggingMiddleware, SecurityMiddleware, ToolFilterMiddleware

            # Add security middleware (rate limiting + path validation + access control)
            mcp.add_middleware(SecurityMiddleware(
                allowed_roots=[project_root, _temp_dir],
                calls_per_minute=120,  # 2 calls/sec sustained
                burst_size=20,         # Allow bursts
            ))

            # Add logging middleware (request timing)
            mcp.add_middleware(LoggingMiddleware(
                log_arguments=False,   # Don't log args (may contain sensitive data)
                log_results=False,     # Don't log results (too verbose)
                slow_threshold_ms=5000,  # Warn on slow tools
            ))

            # Add tool filter middleware (dynamic tool loading)
            # Reduces context pollution by showing only relevant tools per workflow mode
            # See: https://www.jlowin.dev/blog/stop-converting-rest-apis-to-mcp
            mcp.add_middleware(ToolFilterMiddleware(enabled=True))

            logger.debug("✅ Middleware registered: SecurityMiddleware, LoggingMiddleware, ToolFilterMiddleware")
        except ImportError as e:
            logger.debug(f"Middleware not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register middleware: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # RESOURCE TEMPLATES (FastMCP 2 feature)
    # ═══════════════════════════════════════════════════════════════════════
    if not USE_STDIO and FastMCP and mcp:
        try:
            from .resources.templates import register_resource_templates
            register_resource_templates(mcp)
            logger.debug("✅ Resource templates registered")
        except ImportError as e:
            logger.debug(f"Resource templates not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register resource templates: {e}")

        # Context primer resources for AI priming
        try:
            from .resources.context_primer import register_context_primer_resources
            register_context_primer_resources(mcp)
            logger.debug("✅ Context primer resources registered")
        except ImportError as e:
            logger.debug(f"Context primer resources not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register context primer resources: {e}")

        # Hint registry resources for dynamic hint loading
        try:
            from .resources.hint_registry import register_hint_registry_resources
            register_hint_registry_resources(mcp)
            logger.debug("✅ Hint registry resources registered")
        except ImportError as e:
            logger.debug(f"Hint registry resources not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register hint registry resources: {e}")

        # Auto-primer tools for session start
        try:
            from .tools.auto_primer import register_auto_primer_tools
            register_auto_primer_tools(mcp)
            logger.debug("✅ Auto-primer tools registered")
        except ImportError as e:
            logger.debug(f"Auto-primer tools not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register auto-primer tools: {e}")
        
        # Session mode resources (MODE-002)
        try:
            from .resources.session import register_session_resources
            register_session_resources(mcp)
            logger.debug("✅ Session mode resources registered")
        except ImportError as e:
            logger.debug(f"Session mode resources not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register session mode resources: {e}")
        
        # Prompt discovery resources and tools
        try:
            from .resources.prompt_discovery import (
                register_prompt_discovery_resources,
                register_prompt_discovery_tools,
            )
            register_prompt_discovery_resources(mcp)
            register_prompt_discovery_tools(mcp)
            logger.debug("✅ Prompt discovery resources and tools registered")
        except ImportError as e:
            logger.debug(f"Prompt discovery not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register prompt discovery: {e}")

        # Assignee management resources and tools
        try:
            from .resources.assignees import register_assignee_resources
            from .tools.task_assignee import register_assignee_tools
            register_assignee_resources(mcp)
            register_assignee_tools(mcp)
            logger.debug("✅ Assignee management resources and tools registered")
        except ImportError as e:
            logger.debug(f"Assignee management not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register assignee management: {e}")

        # Capabilities resource for agent priming
        try:
            from .resources.capabilities import register_capabilities_resources
            register_capabilities_resources(mcp)
            logger.debug("✅ Capabilities resources registered")
        except ImportError as e:
            logger.debug(f"Capabilities resources not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register capabilities resources: {e}")

        # Session handoff tool for multi-dev coordination
        try:
            from .tools.session_handoff import register_handoff_tools
            register_handoff_tools(mcp)
            logger.debug("✅ Session handoff tool registered")
        except ImportError as e:
            logger.debug(f"Session handoff not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register session handoff: {e}")

        # Ollama integration tools
        try:
            from .tools.ollama_integration import register_ollama_tools
            register_ollama_tools(mcp)
            logger.debug("✅ Ollama tools registered")
        except ImportError as e:
            logger.debug(f"Ollama tools not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register Ollama tools: {e}")

        # Ollama-enhanced tools (code documentation, quality analysis, etc.)
        try:
            from .tools.ollama_enhanced_tools import register_ollama_enhanced_tools
            register_ollama_enhanced_tools(mcp)
            logger.debug("✅ Ollama-enhanced tools registered")
        except ImportError as e:
            logger.debug(f"Ollama-enhanced tools not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register Ollama-enhanced tools: {e}")

        # MLX integration tools (Apple Silicon only)
        try:
            from .tools.mlx_integration import register_mlx_tools
            register_mlx_tools(mcp)
            logger.debug("✅ MLX tools registered")
        except ImportError as e:
            logger.debug(f"MLX tools not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register MLX tools: {e}")

# Import automation tools (handle both relative and absolute imports)
try:
    # Try relative imports first (when run as module)
    try:
        from .tools.automation_opportunities import find_automation_opportunities as _find_automation_opportunities
        from .tools.batch_task_approval import batch_approve_tasks as _batch_approve_tasks
        from .tools.ci_cd_validation import validate_ci_cd_workflow as _validate_ci_cd_workflow
        from .tools.context_summarizer import (
            batch_summarize as _batch_summarize,
        )
        from .tools.context_summarizer import (
            estimate_context_budget as _estimate_context_budget,
        )
        from .tools.context_summarizer import (
            summarize_context as _summarize_context,
        )
        from .tools.cursor_rules_generator import generate_cursor_rules as _generate_cursor_rules
        from .tools.cursorignore_generator import generate_cursorignore as _generate_cursorignore
        from .tools.daily_automation import run_daily_automation as _run_daily_automation
        from .tools.definition_of_done import check_definition_of_done as _check_definition_of_done
        from .tools.dependency_security import scan_dependency_security as _scan_dependency_security
        from .tools.attribution_check import check_attribution_compliance as _check_attribution_compliance
        from .tools.docs_health import check_documentation_health as _check_documentation_health
        from .tools.duplicate_detection import detect_duplicate_tasks as _detect_duplicate_tasks
        from .tools.dynamic_tools import (
            focus_mode as _focus_mode,
        )
        from .tools.dynamic_tools import (
            get_tool_manager,
        )
        from .tools.dynamic_tools import (
            get_tool_usage_stats as _get_tool_usage_stats,
        )
        from .tools.dynamic_tools import (
            suggest_mode as _suggest_mode,
        )
        from .tools.external_tool_hints import add_external_tool_hints as _add_external_tool_hints
        from .tools.git_hooks import setup_git_hooks as _setup_git_hooks
        from .tools.hint_catalog import (
            get_tool_help as _get_tool_help,
        )
        from .tools.hint_catalog import (
            list_tools as _list_tools,
        )
        from .tools.linter import get_linter_status as _get_linter_status
        from .tools.linter import run_linter as _run_linter
        from .tools.model_recommender import (
            list_available_models as _list_available_models,
        )
        from .tools.model_recommender import (
            recommend_model as _recommend_model,
        )
        from .tools.nightly_task_automation import run_nightly_task_automation as _run_nightly_task_automation
        from .tools.pattern_triggers import setup_pattern_triggers as _setup_pattern_triggers
        from .tools.prd_alignment import analyze_prd_alignment as _analyze_prd_alignment
        from .tools.prd_generator import generate_prd as _generate_prd
        from .tools.problems_advisor import analyze_problems_tool as _analyze_problems
        from .tools.problems_advisor import list_problem_categories as _list_problem_categories
        from .tools.project_overview import generate_project_overview as _generate_project_overview
        from .tools.project_scorecard import generate_project_scorecard as _generate_project_scorecard
        from .tools.prompt_iteration_tracker import (
            analyze_prompt_iterations as _analyze_prompt_iterations,
        )
        from .tools.prompt_iteration_tracker import (
            log_prompt_iteration as _log_prompt_iteration,
        )
        from .tools.run_tests import run_tests as _run_tests
        from .tools.simplify_rules import simplify_rules as _simplify_rules
        from .tools.sprint_automation import sprint_automation as _sprint_automation
        from .tools.tag_consolidation import tag_consolidation_tool as _tag_consolidation
        from .tools.task_assignee import (
            assign_task as _assign_task,
        )
        from .tools.task_assignee import (
            auto_assign_background_tasks as _auto_assign_background_tasks,
        )
        from .tools.task_assignee import (
            bulk_assign_tasks as _bulk_assign_tasks,
        )
        from .tools.task_assignee import (
            get_workload_summary as _get_workload_summary,
        )
        from .tools.task_assignee import (
            list_tasks_by_assignee as _list_tasks_by_assignee,
        )
        from .tools.task_assignee import (
            unassign_task as _unassign_task,
        )
        from .tools.task_clarification_resolution import (
            list_tasks_awaiting_clarification as _list_tasks_awaiting_clarification,
        )
        from .tools.task_clarification_resolution import (
            resolve_multiple_clarifications as _resolve_multiple_clarifications,
        )
        from .tools.task_clarification_resolution import resolve_task_clarification as _resolve_task_clarification
        from .tools.task_hierarchy_analyzer import analyze_task_hierarchy as _analyze_task_hierarchy
        from .tools.task_clarity_improver import (
            analyze_task_clarity as _analyze_task_clarity,
            improve_task_clarity as _improve_task_clarity,
        )
        from .tools.test_coverage import analyze_test_coverage as _analyze_test_coverage
        from .tools.todo2_alignment import analyze_todo2_alignment as _analyze_todo2_alignment
        from .tools.todo_sync import sync_todo_tasks as _sync_todo_tasks
        from .tools.stale_task_cleanup import cleanup_stale_tasks as _cleanup_stale_tasks
        from .tools.workflow_recommender import recommend_workflow_mode as _recommend_workflow_mode
        from .tools.working_copy_health import check_working_copy_health as _check_working_copy_health

        TOOLS_AVAILABLE = True
    except ImportError:
        # Fallback to absolute imports (when run as script)
        from tools.automation_opportunities import find_automation_opportunities as _find_automation_opportunities
        from tools.batch_task_approval import batch_approve_tasks as _batch_approve_tasks
        from tools.ci_cd_validation import validate_ci_cd_workflow as _validate_ci_cd_workflow
        from tools.context_summarizer import (
            batch_summarize as _batch_summarize,
        )
        from tools.context_summarizer import (
            estimate_context_budget as _estimate_context_budget,
        )
        from tools.context_summarizer import (
            summarize_context as _summarize_context,
        )
        from tools.cursor_rules_generator import generate_cursor_rules as _generate_cursor_rules
        from tools.cursorignore_generator import generate_cursorignore as _generate_cursorignore
        from tools.daily_automation import run_daily_automation as _run_daily_automation
        from tools.definition_of_done import check_definition_of_done as _check_definition_of_done
        from tools.dependency_security import scan_dependency_security as _scan_dependency_security
        from tools.attribution_check import check_attribution_compliance as _check_attribution_compliance
        from tools.docs_health import check_documentation_health as _check_documentation_health
        from tools.duplicate_detection import detect_duplicate_tasks as _detect_duplicate_tasks
        from tools.dynamic_tools import (
            focus_mode as _focus_mode,
        )
        from tools.dynamic_tools import (
            get_tool_manager,
        )
        from tools.dynamic_tools import (
            get_tool_usage_stats as _get_tool_usage_stats,
        )
        from tools.dynamic_tools import (
            suggest_mode as _suggest_mode,
        )
        from tools.external_tool_hints import add_external_tool_hints as _add_external_tool_hints
        from tools.git_hooks import setup_git_hooks as _setup_git_hooks
        from tools.hint_catalog import (
            get_tool_help as _get_tool_help,
        )
        from tools.hint_catalog import (
            list_tools as _list_tools,
        )
        from tools.linter import get_linter_status as _get_linter_status
        from tools.linter import run_linter as _run_linter
        from tools.model_recommender import (
            list_available_models as _list_available_models,
        )
        from tools.model_recommender import (
            recommend_model as _recommend_model,
        )
        from tools.nightly_task_automation import run_nightly_task_automation as _run_nightly_task_automation
        from tools.pattern_triggers import setup_pattern_triggers as _setup_pattern_triggers
        from tools.prd_alignment import analyze_prd_alignment as _analyze_prd_alignment
        from tools.prd_generator import generate_prd as _generate_prd
        from tools.problems_advisor import analyze_problems_tool as _analyze_problems
        from tools.problems_advisor import list_problem_categories as _list_problem_categories
        from tools.project_overview import generate_project_overview as _generate_project_overview
        from tools.project_scorecard import generate_project_scorecard as _generate_project_scorecard
        from tools.prompt_iteration_tracker import (
            analyze_prompt_iterations as _analyze_prompt_iterations,
        )
        from tools.prompt_iteration_tracker import (
            log_prompt_iteration as _log_prompt_iteration,
        )
        from tools.run_tests import run_tests as _run_tests
        from tools.simplify_rules import simplify_rules as _simplify_rules
        from tools.sprint_automation import sprint_automation as _sprint_automation
        from tools.tag_consolidation import tag_consolidation_tool as _tag_consolidation
        from tools.task_assignee import (
            assign_task as _assign_task,
        )
        from tools.task_assignee import (
            auto_assign_background_tasks as _auto_assign_background_tasks,
        )
        from tools.task_assignee import (
            bulk_assign_tasks as _bulk_assign_tasks,
        )
        from tools.task_assignee import (
            get_workload_summary as _get_workload_summary,
        )
        from tools.task_assignee import (
            list_tasks_by_assignee as _list_tasks_by_assignee,
        )
        from tools.task_assignee import (
            unassign_task as _unassign_task,
        )
        from tools.task_clarification_resolution import (
            list_tasks_awaiting_clarification as _list_tasks_awaiting_clarification,
        )
        from tools.task_clarification_resolution import (
            resolve_multiple_clarifications as _resolve_multiple_clarifications,
        )
        from tools.task_clarification_resolution import resolve_task_clarification as _resolve_task_clarification
        from tools.task_hierarchy_analyzer import analyze_task_hierarchy as _analyze_task_hierarchy
        from tools.test_coverage import analyze_test_coverage as _analyze_test_coverage
        from tools.todo2_alignment import analyze_todo2_alignment as _analyze_todo2_alignment
        from tools.todo_sync import sync_todo_tasks as _sync_todo_tasks
        from tools.stale_task_cleanup import cleanup_stale_tasks as _cleanup_stale_tasks
        from tools.workflow_recommender import recommend_workflow_mode as _recommend_workflow_mode
        from tools.working_copy_health import check_working_copy_health as _check_working_copy_health

        TOOLS_AVAILABLE = True
    logger.info("All tools loaded successfully")
except ImportError as e:
    TOOLS_AVAILABLE = False
    logger.warning(f"Some tools not available: {e}")

# Module-level variable for consolidated tools availability (needed for stdio server)
CONSOLIDATED_AVAILABLE = False

# Tool registration - support both FastMCP and stdio Server
def register_tools():
    """Register tools with the appropriate MCP server instance."""
    # Import consolidated tools early (needed for stdio server)
    global CONSOLIDATED_AVAILABLE
    try:
        from .tools.consolidated import (
            analyze_alignment as _analyze_alignment,
            automation as _automation,
            estimation as _estimation,
            generate_config as _generate_config,
            health as _health,
            lint as _lint,
            memory as _memory,
            memory_maint as _memory_maint,
            prompt_tracking as _prompt_tracking,
            report as _report,
            security as _security,
            setup_hooks as _setup_hooks,
            task_analysis as _task_analysis,
            task_discovery as _task_discovery,
            task_workflow as _task_workflow,
            testing as _testing,
            context as _context,
            tool_catalog as _tool_catalog,
            workflow_mode as _workflow_mode,
            recommend as _recommend,
        )
        CONSOLIDATED_AVAILABLE = True
    except ImportError:
        CONSOLIDATED_AVAILABLE = False
        # Set dummy functions to avoid NameError
        _generate_config = None
        _health = None
        _lint = None
        _memory = None
        _memory_maint = None
        _prompt_tracking = None
        _report = None
        _security = None
        _setup_hooks = None
        _task_analysis = None
        _task_discovery = None
        _analyze_alignment = None
        _automation = None
        _estimation = None
        _task_workflow = None
        _testing = None
        _context = None
        _tool_catalog = None
        _workflow_mode = None
        _recommend = None
    
    if mcp:
        # FastMCP registration (decorator-based)
        # NOTE: server_status removed - use health(type="server")
        # NOTE: dev_reload removed - use watchdog script for automatic reloads on file changes
        pass  # Tool registrations continue below with @mcp.tool() decorators

    elif stdio_server_instance:
        # Stdio Server registration (handler-based)
        # Use FastMCP's tool registry if available, otherwise fall back to manual list
        @stdio_server_instance.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools."""
            tools = []
            
            # Add server_status tool (stdio-only utility)
            tools.append(
                Tool(
                    name="server_status",
                    description="Get the current status of the project management automation server.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
            )
            
            # NOTE: dev_reload removed - use watchdog script for automatic reloads on file changes
            
            # Note: FastMCP and stdio server are mutually exclusive (mcp is None when stdio is used)
            # So we maintain a manual list here that should match FastMCP's @mcp.tool() registrations
            # This ensures both interfaces expose the same tools
            
            # Manual tool list (must be kept in sync with FastMCP @mcp.tool() registrations above)
            if TOOLS_AVAILABLE:
                # Add tool definitions for all automation tools
                tools.extend(
                    [
                        # NOTE: check_documentation_health removed - use health(action="docs") instead
                        # NOTE: Individual tools removed - use consolidated tools instead:
                        # - analyze_alignment (action=todo2|prd) replaces analyze_todo2_alignment + analyze_prd_alignment
                        # - task_analysis (action=duplicates) replaces detect_duplicate_tasks
                        # - security (action=scan) replaces scan_dependency_security
                        # - automation (action=discover) replaces run_discover_automation
                        # - task_workflow (action=sync) replaces sync_todo_tasks
                        Tool(
                            name="add_external_tool_hints",
                            description="Automatically detect and add Context7/external tool hints to documentation.",
                            inputSchema={
                                "type": "object",
                                "properties": {
                                    "dry_run": {
                                        "type": "boolean",
                                        "description": "Preview changes without applying",
                                        "default": False,
                                    },
                                    "output_path": {"type": "string", "description": "Path for report output"},
                                    "min_file_size": {
                                        "type": "integer",
                                        "description": "Minimum file size in lines to process",
                                        "default": 50,
                                    },
                                },
                            },
                        ),
                        # NOTE: run_daily_automation moved to consolidated tools section below
                    ]
                )
            
            # Add consolidated tools if available
            if CONSOLIDATED_AVAILABLE:
                tools.extend([
                    Tool(
                        name="security",
                        description="[HINT: Security. action=scan|alerts|report. Vulnerabilities, remediation.] Unified security analysis.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["scan", "alerts", "report"], "default": "report"},
                                "repo": {"type": "string", "default": "davidl71/project-management-automation"},
                                "languages": {"type": "array", "items": {"type": "string"}},
                                "config_path": {"type": "string"},
                                "state": {"type": "string", "default": "open"},
                                "include_dismissed": {"type": "boolean", "default": False},
                                "alert_critical": {"type": "boolean", "default": False},
                            },
                        },
                    ),
                    Tool(
                        name="generate_config",
                        description="[HINT: Config generation. action=rules|ignore|simplify. Creates IDE config files.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["rules", "ignore", "simplify"], "default": "rules"},
                                "rules": {"type": "string"},
                                "overwrite": {"type": "boolean", "default": False},
                                "analyze_only": {"type": "boolean", "default": False},
                                "include_indexing": {"type": "boolean", "default": True},
                                "analyze_project": {"type": "boolean", "default": True},
                                "rule_files": {"type": "string"},
                                "output_dir": {"type": "string"},
                                "dry_run": {"type": "boolean", "default": False},
                            },
                        },
                    ),
                    Tool(
                        name="setup_hooks",
                        description="[HINT: Hooks setup. action=git|patterns. Install automation hooks.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["git", "patterns"], "default": "git"},
                                "hooks": {"type": "array", "items": {"type": "string"}},
                                "patterns": {"type": "string"},
                                "config_path": {"type": "string"},
                                "install": {"type": "boolean", "default": True},
                                "dry_run": {"type": "boolean", "default": False},
                            },
                        },
                    ),
                    Tool(
                        name="prompt_tracking",
                        description="[HINT: Prompt tracking. action=log|analyze. Track and analyze prompts.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["log", "analyze"], "default": "analyze"},
                                "prompt": {"type": "string"},
                                "task_id": {"type": "string"},
                                "mode": {"type": "string"},
                                "outcome": {"type": "string"},
                                "iteration": {"type": "integer", "default": 1},
                                "days": {"type": "integer", "default": 7},
                            },
                        },
                    ),
                    Tool(
                        name="health",
                        description="[HINT: Health check. action=server|git|docs|dod|cicd. Status and health metrics.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["server", "git", "docs", "dod", "cicd"], "default": "server"},
                                "agent_name": {"type": "string"},
                                "check_remote": {"type": "boolean", "default": True},
                                "output_path": {"type": "string"},
                                "create_tasks": {"type": "boolean", "default": True},
                                "task_id": {"type": "string"},
                                "changed_files": {"type": "string"},
                                "auto_check": {"type": "boolean", "default": True},
                                "workflow_path": {"type": "string"},
                                "check_runners": {"type": "boolean", "default": True},
                            },
                        },
                    ),
                    Tool(
                        name="check_attribution",
                        description="Check attribution compliance for AI-generated code.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "output_path": {"type": "string"},
                                "create_tasks": {"type": "boolean", "default": True},
                            },
                        },
                    ),
                    Tool(
                        name="report",
                        description="[HINT: Report generation. action=overview|scorecard|briefing|prd. Project reports.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["overview", "scorecard", "briefing", "prd"], "default": "overview"},
                                "output_format": {"type": "string", "default": "text"},
                                "output_path": {"type": "string"},
                                "include_recommendations": {"type": "boolean", "default": True},
                                "overall_score": {"type": "number", "default": 50.0},
                                "security_score": {"type": "number", "default": 50.0},
                                "testing_score": {"type": "number", "default": 50.0},
                                "documentation_score": {"type": "number", "default": 50.0},
                                "completion_score": {"type": "number", "default": 50.0},
                                "alignment_score": {"type": "number", "default": 50.0},
                                "project_name": {"type": "string"},
                                "include_architecture": {"type": "boolean", "default": True},
                                "include_metrics": {"type": "boolean", "default": True},
                                "include_tasks": {"type": "boolean", "default": True},
                            },
                        },
                    ),
                    Tool(
                        name="task_analysis",
                        description="[HINT: Task analysis. action=duplicates|tags|hierarchy|dependencies|parallelization. Task quality and structure.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["duplicates", "tags", "hierarchy", "dependencies", "parallelization"], "default": "duplicates"},
                                "similarity_threshold": {"type": "number", "default": 0.85},
                                "auto_fix": {"type": "boolean", "default": False},
                                "dry_run": {"type": "boolean", "default": True},
                                "custom_rules": {"type": "string"},
                                "remove_tags": {"type": "string"},
                                "output_format": {"type": "string", "default": "text"},
                                "include_recommendations": {"type": "boolean", "default": True},
                                "output_path": {"type": "string"},
                            },
                        },
                    ),
                    Tool(
                        name="testing",
                        description="[HINT: Testing tool. action=run|coverage|suggest|validate. Execute tests, analyze coverage, suggest test cases, or validate test structure.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["run", "coverage", "suggest", "validate"], "default": "run"},
                                "test_path": {"type": "string"},
                                "test_framework": {"type": "string", "default": "auto"},
                                "verbose": {"type": "boolean", "default": True},
                                "coverage": {"type": "boolean", "default": False},
                                "coverage_file": {"type": "string"},
                                "min_coverage": {"type": "integer", "default": 80},
                                "format": {"type": "string", "default": "html"},
                                "target_file": {"type": "string"},
                                "min_confidence": {"type": "number", "default": 0.7},
                                "framework": {"type": "string"},
                                "output_path": {"type": "string"},
                            },
                        },
                    ),
                    Tool(
                        name="lint",
                        description="[HINT: Linting tool. action=run|analyze. Run linter or analyze problems.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["run", "analyze"], "default": "run"},
                                "path": {"type": "string"},
                                "linter": {"type": "string", "default": "ruff"},
                                "fix": {"type": "boolean", "default": False},
                                "analyze": {"type": "boolean", "default": True},
                                "select": {"type": "string"},
                                "ignore": {"type": "string"},
                                "problems_json": {"type": "string"},
                                "include_hints": {"type": "boolean", "default": True},
                                "output_path": {"type": "string"},
                            },
                        },
                    ),
                    Tool(
                        name="memory",
                        description="[HINT: Memory tool. action=save|recall|search. Persist and retrieve AI discoveries.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["save", "recall", "search"], "default": "search"},
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "category": {"type": "string", "default": "insight"},
                                "task_id": {"type": "string"},
                                "metadata": {"type": "string"},
                                "include_related": {"type": "boolean", "default": True},
                                "query": {"type": "string"},
                                "limit": {"type": "integer", "default": 10},
                            },
                        },
                    ),
                    Tool(
                        name="task_discovery",
                        description="[HINT: Task discovery. action=comments|markdown|orphans|all. Find tasks from various sources.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["comments", "markdown", "orphans", "all"], "default": "all"},
                                "file_patterns": {"type": "string"},
                                "include_fixme": {"type": "boolean", "default": True},
                                "doc_path": {"type": "string"},
                                "output_path": {"type": "string"},
                                "create_tasks": {"type": "boolean", "default": False},
                            },
                        },
                    ),
                    Tool(
                        name="task_workflow",
                        description="[HINT: Task workflow. action=sync|approve|clarify|clarity|cleanup. Manage task lifecycle.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["sync", "approve", "clarify", "clarity", "cleanup"], "default": "sync"},
                                "dry_run": {"type": "boolean", "default": False},
                                "status": {"type": "string", "default": "Review"},
                                "new_status": {"type": "string", "default": "Todo"},
                                "clarification_none": {"type": "boolean", "default": True},
                                "filter_tag": {"type": "string"},
                                "task_ids": {"type": "string"},
                                "sub_action": {"type": "string", "default": "list"},
                                "task_id": {"type": "string"},
                                "clarification_text": {"type": "string"},
                                "decision": {"type": "string"},
                                "decisions_json": {"type": "string"},
                                "move_to_todo": {"type": "boolean", "default": True},
                                "auto_apply": {"type": "boolean", "default": False},
                                "output_format": {"type": "string", "default": "text"},
                                "stale_threshold_hours": {"type": "number", "default": 2.0},
                                "output_path": {"type": "string"},
                            },
                        },
                    ),
                    Tool(
                        name="memory_maint",
                        description="[HINT: Memory maintenance. action=health|gc|prune|consolidate|dream. Lifecycle management.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["health", "gc", "prune", "consolidate", "dream"], "default": "health"},
                                "max_age_days": {"type": "integer", "default": 90},
                                "delete_orphaned": {"type": "boolean", "default": True},
                                "delete_duplicates": {"type": "boolean", "default": True},
                                "scorecard_max_age_days": {"type": "integer", "default": 7},
                                "value_threshold": {"type": "number", "default": 0.3},
                                "keep_minimum": {"type": "integer", "default": 50},
                                "similarity_threshold": {"type": "number", "default": 0.85},
                                "merge_strategy": {"type": "string", "default": "newest"},
                                "scope": {"type": "string", "default": "week"},
                                "advisors": {"type": "string"},
                                "generate_insights": {"type": "boolean", "default": True},
                                "save_dream": {"type": "boolean", "default": True},
                                "dry_run": {"type": "boolean", "default": True},
                                "interactive": {"type": "boolean", "default": True},
                            },
                        },
                    ),
                    Tool(
                        name="automation",
                        description="[HINT: Automation. action=daily|nightly|sprint|discover. Unified automation tool.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["daily", "nightly", "sprint", "discover"], "default": "daily"},
                                "tasks": {"type": "array", "items": {"type": "string"}},
                                "include_slow": {"type": "boolean", "default": False},
                                "max_tasks_per_host": {"type": "integer", "default": 5},
                                "max_parallel_tasks": {"type": "integer", "default": 10},
                                "priority_filter": {"type": "string"},
                                "tag_filter": {"type": "array", "items": {"type": "string"}},
                                "max_iterations": {"type": "integer", "default": 10},
                                "auto_approve": {"type": "boolean", "default": True},
                                "extract_subtasks": {"type": "boolean", "default": True},
                                "run_analysis_tools": {"type": "boolean", "default": True},
                                "run_testing_tools": {"type": "boolean", "default": True},
                                "min_value_score": {"type": "number", "default": 0.7},
                                "dry_run": {"type": "boolean", "default": False},
                                "output_path": {"type": "string"},
                                "notify": {"type": "boolean", "default": False},
                            },
                        },
                    ),
                    Tool(
                        name="estimation",
                        description="[HINT: Estimation. action=estimate|analyze|stats. Unified task duration estimation tool.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["estimate", "analyze", "stats"], "default": "estimate"},
                                "name": {"type": "string"},
                                "details": {"type": "string", "default": ""},
                                "tags": {"type": "string"},
                                "priority": {"type": "string", "default": "medium"},
                                "use_historical": {"type": "boolean", "default": True},
                                "detailed": {"type": "boolean", "default": False},
                                "use_mlx": {"type": "boolean", "default": True},
                                "mlx_weight": {"type": "number", "default": 0.3},
                            },
                        },
                    ),
                    Tool(
                        name="analyze_alignment",
                        description="[HINT: Alignment analysis. action=todo2|prd. Unified alignment analysis tool.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["todo2", "prd"], "default": "todo2"},
                                "create_followup_tasks": {"type": "boolean", "default": True},
                                "output_path": {"type": "string"},
                            },
                        },
                    ),
                    Tool(
                        name="tool_catalog",
                        description="[HINT: Tool catalog. action=list|help. Unified tool catalog and help.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["list", "help"], "default": "list"},
                                "category": {"type": "string"},
                                "persona": {"type": "string"},
                                "include_examples": {"type": "boolean", "default": True},
                                "tool_name": {"type": "string"},
                            },
                        },
                    ),
                    Tool(
                        name="workflow_mode",
                        description="[HINT: Workflow mode management. action=focus|suggest|stats. Unified workflow operations.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["focus", "suggest", "stats"], "default": "focus"},
                                "mode": {"type": "string"},
                                "enable_group": {"type": "string"},
                                "disable_group": {"type": "string"},
                                "status": {"type": "boolean", "default": False},
                                "text": {"type": "string"},
                                "auto_switch": {"type": "boolean", "default": False},
                            },
                        },
                    ),
                    Tool(
                        name="context",
                        description="[HINT: Context management. action=summarize|budget|batch. Unified context operations.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["summarize", "budget", "batch"], "default": "summarize"},
                                "data": {"type": "string"},
                                "level": {"type": "string", "default": "brief"},
                                "tool_type": {"type": "string"},
                                "max_tokens": {"type": "integer"},
                                "include_raw": {"type": "boolean", "default": False},
                                "items": {"type": "string"},
                                "budget_tokens": {"type": "integer", "default": 4000},
                                "combine": {"type": "boolean", "default": True},
                            },
                        },
                    ),
                    Tool(
                        name="recommend",
                        description="[HINT: Recommendations. action=model|workflow|advisor. Unified recommendation system.]",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "action": {"type": "string", "enum": ["model", "workflow", "advisor"], "default": "model"},
                                "task_description": {"type": "string"},
                                "task_type": {"type": "string"},
                                "optimize_for": {"type": "string", "default": "quality"},
                                "include_alternatives": {"type": "boolean", "default": True},
                                "task_id": {"type": "string"},
                                "include_rationale": {"type": "boolean", "default": True},
                                "metric": {"type": "string"},
                                "tool": {"type": "string"},
                                "stage": {"type": "string"},
                                "score": {"type": "number", "default": 50.0},
                                "context": {"type": "string", "default": ""},
                                "log": {"type": "boolean", "default": True},
                            },
                        },
                    ),
                ])
            
            # Add git-inspired tools if available (must match FastMCP conditional registration)
            try:
                from .tools.git_inspired_tools import (
                    compare_task_diff,
                    generate_graph,
                    get_branch_commits,
                    get_branch_tasks,
                    get_task_commits,
                    list_branches,
                    merge_branch_tools,
                    set_task_branch_tool,
                )
                GIT_INSPIRED_TOOLS_AVAILABLE = True
            except ImportError:
                GIT_INSPIRED_TOOLS_AVAILABLE = False
                logger.warning("Git-inspired tools not available for stdio server")
            
            if GIT_INSPIRED_TOOLS_AVAILABLE:
                tools.extend([
                    Tool(
                        name="get_task_commits_tool",
                        description="[HINT: Git-inspired tools. Get commit history for a task.] Get commit history for a task showing all changes over time.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "string"},
                                "branch": {"type": "string"},
                                "limit": {"type": "integer", "default": 50},
                            },
                            "required": ["task_id"],
                        },
                    ),
                    Tool(
                        name="get_branch_commits_tool",
                        description="[HINT: Git-inspired tools. Get all commits for a branch.] Get all commits across all tasks in a branch.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "branch": {"type": "string"},
                                "limit": {"type": "integer", "default": 100},
                            },
                            "required": ["branch"],
                        },
                    ),
                    Tool(
                        name="list_branches_tool",
                        description="[HINT: Git-inspired tools. List all branches with statistics.] List all branches (work streams) from tasks and their statistics.",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                        },
                    ),
                    Tool(
                        name="get_branch_tasks_tool",
                        description="[HINT: Git-inspired tools. Get all tasks in a branch.] Get all tasks belonging to a specific branch.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "branch": {"type": "string"},
                            },
                            "required": ["branch"],
                        },
                    ),
                    Tool(
                        name="compare_task_diff_tool",
                        description="[HINT: Git-inspired tools. Compare two versions of a task.] Compare task versions across commits or timestamps to see what changed.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "string"},
                                "commit1": {"type": "string"},
                                "commit2": {"type": "string"},
                                "time1": {"type": "string"},
                                "time2": {"type": "string"},
                            },
                            "required": ["task_id"],
                        },
                    ),
                    Tool(
                        name="generate_graph_tool",
                        description="[HINT: Git-inspired tools. Generate commit graph visualization.] Generate visual timeline of commits (text ASCII or Graphviz DOT format).",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "branch": {"type": "string"},
                                "task_id": {"type": "string"},
                                "format": {"type": "string", "default": "text"},
                                "output_path": {"type": "string"},
                                "max_commits": {"type": "integer", "default": 50},
                            },
                        },
                    ),
                    Tool(
                        name="merge_branch_tools_tool",
                        description="[HINT: Git-inspired tools. Merge tasks from one branch to another.] Merge tasks from source branch to target branch with conflict detection.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "source_branch": {"type": "string"},
                                "target_branch": {"type": "string"},
                                "conflict_strategy": {"type": "string", "default": "newer"},
                                "author": {"type": "string", "default": "system"},
                                "dry_run": {"type": "boolean", "default": False},
                            },
                            "required": ["source_branch", "target_branch"],
                        },
                    ),
                    Tool(
                        name="set_task_branch",
                        description="[HINT: Git-inspired tools. Set branch for a task.] Assign a task to a branch (work stream) by adding branch: tag.",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "task_id": {"type": "string"},
                                "branch": {"type": "string"},
                            },
                            "required": ["task_id", "branch"],
                        },
                    ),
                ])
            
            return tools

        @stdio_server_instance.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            if name == "server_status":
                result = json.dumps(
                    {
                        "status": "operational",
                        "version": __version__,
                        "tools_available": TOOLS_AVAILABLE,
                        "project_root": str(project_root),
                    },
                    separators=(",", ":"),
                )
            elif TOOLS_AVAILABLE:
                # Route to appropriate tool function
                if name == "check_documentation_health":
                    result = _check_documentation_health(
                        arguments.get("output_path"), arguments.get("create_tasks", True)
                    )
                elif name == "analyze_alignment":
                    if _analyze_alignment is None:
                        result = json.dumps({"success": False, "error": "analyze_alignment tool not available"}, indent=2)
                    else:
                        result = _analyze_alignment(
                            action=arguments.get("action", "todo2"),
                            create_followup_tasks=arguments.get("create_followup_tasks", True),
                            output_path=arguments.get("output_path"),
                        )
                elif name == "analyze_todo2_alignment" or name == "analyze_prd_alignment":
                    # Redirect to analyze_alignment
                    if _analyze_alignment is None:
                        result = json.dumps({"success": False, "error": "analyze_alignment tool not available"}, indent=2)
                    else:
                        action = "todo2" if name == "analyze_todo2_alignment" else "prd"
                        result = _analyze_alignment(
                            action=action,
                            create_followup_tasks=arguments.get("create_followup_tasks", True),
                            output_path=arguments.get("output_path"),
                        )
                    
                    # Ensure JSON string (stdio server expects strings)
                    if not isinstance(result, str):
                        result = json.dumps(result, indent=2)
                elif name == "detect_duplicate_tasks":
                    result = _detect_duplicate_tasks(
                        arguments.get("similarity_threshold", 0.85),
                        arguments.get("auto_fix", False),
                        arguments.get("output_path"),
                    )
                elif name == "scan_dependency_security":
                    result = _scan_dependency_security(arguments.get("languages"), arguments.get("config_path"))
                elif name == "find_automation_opportunities":
                    result = _find_automation_opportunities(
                        arguments.get("min_value_score", 0.7), arguments.get("output_path")
                    )
                elif name == "sync_todo_tasks":
                    result = _sync_todo_tasks(arguments.get("dry_run", False), arguments.get("output_path"))
                # NOTE: cleanup_stale_tasks removed - use task_workflow(action="cleanup")
                elif name == "add_external_tool_hints":
                    result = _add_external_tool_hints(
                        arguments.get("dry_run", False),
                        arguments.get("output_path"),
                        arguments.get("min_file_size", 50),
                    )
                elif name == "automation":
                    if _automation is None:
                        result = json.dumps({"success": False, "error": "automation tool not available"}, indent=2)
                    else:
                        result = _automation(
                            action=arguments.get("action", "daily"),
                            tasks=arguments.get("tasks"),
                            include_slow=arguments.get("include_slow", False),
                            max_tasks_per_host=arguments.get("max_tasks_per_host", 5),
                            max_parallel_tasks=arguments.get("max_parallel_tasks", 10),
                            priority_filter=arguments.get("priority_filter"),
                            tag_filter=arguments.get("tag_filter"),
                            max_iterations=arguments.get("max_iterations", 10),
                            auto_approve=arguments.get("auto_approve", True),
                            extract_subtasks=arguments.get("extract_subtasks", True),
                            run_analysis_tools=arguments.get("run_analysis_tools", True),
                            run_testing_tools=arguments.get("run_testing_tools", True),
                            min_value_score=arguments.get("min_value_score", 0.7),
                            dry_run=arguments.get("dry_run", False),
                            output_path=arguments.get("output_path"),
                            notify=arguments.get("notify", False),
                        )
                elif CONSOLIDATED_AVAILABLE:
                    # Consolidated tools
                    if name == "security":
                        # Stdio server is async, so call async version directly
                        from .tools.consolidated import security_async
                        result = await security_async(
                            arguments.get("action", "report"),
                            arguments.get("repo", "davidl71/project-management-automation"),
                            arguments.get("languages"),
                            arguments.get("config_path"),
                            arguments.get("state", "open"),
                            arguments.get("include_dismissed", False),
                            ctx=None,  # No progress context in stdio mode
                            alert_critical=arguments.get("alert_critical", False),
                        )
                        # Ensure it's a string
                        if not isinstance(result, str):
                            result = json.dumps(result, indent=2)
                    elif name == "generate_config":
                        result = _generate_config(
                            arguments.get("action", "rules"),
                            arguments.get("rules"),
                            arguments.get("overwrite", False),
                            arguments.get("analyze_only", False),
                            arguments.get("include_indexing", True),
                            arguments.get("analyze_project", True),
                            arguments.get("rule_files"),
                            arguments.get("output_dir"),
                            arguments.get("dry_run", False),
                        )
                    elif name == "setup_hooks":
                        result = _setup_hooks(
                            arguments.get("action", "git"),
                            arguments.get("hooks"),
                            arguments.get("patterns"),
                            arguments.get("config_path"),
                            arguments.get("install", True),
                            arguments.get("dry_run", False),
                        )
                    elif name == "prompt_tracking":
                        result = _prompt_tracking(
                            arguments.get("action", "analyze"),
                            arguments.get("prompt"),
                            arguments.get("task_id"),
                            arguments.get("mode"),
                            arguments.get("outcome"),
                            arguments.get("iteration", 1),
                            arguments.get("days", 7),
                        )
                    elif name == "health":
                        result = _health(
                            arguments.get("action", "server"),
                            arguments.get("agent_name"),
                            arguments.get("check_remote", True),
                            arguments.get("output_path"),
                            arguments.get("create_tasks", True),
                            arguments.get("task_id"),
                            arguments.get("changed_files"),
                            arguments.get("auto_check", True),
                            arguments.get("workflow_path"),
                            arguments.get("check_runners", True),
                        )
                    elif name == "check_attribution":
                        result = _check_attribution_compliance(
                            arguments.get("output_path"),
                            arguments.get("create_tasks", True),
                        )
                    elif name == "report":
                        result = _report(
                            arguments.get("action", "overview"),
                            arguments.get("output_format", "text"),
                            arguments.get("output_path"),
                            arguments.get("include_recommendations", True),
                            arguments.get("overall_score", 50.0),
                            arguments.get("security_score", 50.0),
                            arguments.get("testing_score", 50.0),
                            arguments.get("documentation_score", 50.0),
                            arguments.get("completion_score", 50.0),
                            arguments.get("alignment_score", 50.0),
                            arguments.get("project_name"),
                            arguments.get("include_architecture", True),
                            arguments.get("include_metrics", True),
                            arguments.get("include_tasks", True),
                        )
                    # advisor_audio tool removed - migrated to devwisdom-go MCP server
                    elif name == "task_analysis":
                        result = _task_analysis(
                            arguments.get("action", "duplicates"),
                            arguments.get("similarity_threshold", 0.85),
                            arguments.get("auto_fix", False),
                            arguments.get("dry_run", True),
                            arguments.get("custom_rules"),
                            arguments.get("remove_tags"),
                            arguments.get("output_format", "text"),
                            arguments.get("include_recommendations", True),
                            arguments.get("output_path"),
                        )
                    elif name == "testing":
                        # Stdio server is async, so call async version directly
                        from .tools.consolidated import testing_async
                        result = await testing_async(
                            arguments.get("action", "run"),
                            arguments.get("test_path"),
                            arguments.get("test_framework", "auto"),
                            arguments.get("verbose", True),
                            arguments.get("coverage", False),
                            arguments.get("coverage_file"),
                            arguments.get("min_coverage", 80),
                            arguments.get("format", "html"),
                            arguments.get("target_file"),
                            arguments.get("min_confidence", 0.7),
                            arguments.get("framework"),
                            arguments.get("output_path"),
                        )
                    elif name == "lint":
                        result = _lint(
                            arguments.get("action", "run"),
                            arguments.get("path"),
                            arguments.get("linter", "ruff"),
                            arguments.get("fix", False),
                            arguments.get("analyze", True),
                            arguments.get("select"),
                            arguments.get("ignore"),
                            arguments.get("problems_json"),
                            arguments.get("include_hints", True),
                            arguments.get("output_path"),
                        )
                    elif name == "memory":
                        result = _memory(
                            arguments.get("action", "search"),
                            arguments.get("title"),
                            arguments.get("content"),
                            arguments.get("category", "insight"),
                            arguments.get("task_id"),
                            arguments.get("metadata"),
                            arguments.get("include_related", True),
                            arguments.get("query"),
                            arguments.get("limit", 10),
                        )
                    elif name == "task_discovery":
                        result = _task_discovery(
                            arguments.get("action", "all"),
                            arguments.get("file_patterns"),
                            arguments.get("include_fixme", True),
                            arguments.get("doc_path"),
                            arguments.get("output_path"),
                            arguments.get("create_tasks", False),
                        )
                    elif name == "task_workflow":
                        result = _task_workflow(
                            arguments.get("action", "sync"),
                            arguments.get("dry_run", False),
                            arguments.get("status", "Review"),
                            arguments.get("new_status", "Todo"),
                            arguments.get("clarification_none", True),
                            arguments.get("filter_tag"),
                            arguments.get("task_ids"),
                            arguments.get("sub_action", "list"),
                            arguments.get("task_id"),
                            arguments.get("clarification_text"),
                            arguments.get("decision"),
                            arguments.get("decisions_json"),
                            arguments.get("move_to_todo", True),
                            arguments.get("output_path"),
                        )
                    # NOTE: improve_task_clarity removed - use task_workflow(action="clarity")
                    elif name == "estimation":
                        if _estimation is None:
                            result = json.dumps({"success": False, "error": "estimation tool not available"}, indent=2)
                        else:
                            result = _estimation(
                                action=arguments.get("action", "estimate"),
                                name=arguments.get("name"),
                                details=arguments.get("details", ""),
                                tags=arguments.get("tags"),
                                priority=arguments.get("priority", "medium"),
                                use_historical=arguments.get("use_historical", True),
                                detailed=arguments.get("detailed", False),
                                use_mlx=arguments.get("use_mlx", True),
                                mlx_weight=arguments.get("mlx_weight", 0.3),
                            )
                    # NOTE: estimate_task_duration, analyze_estimation_accuracy, get_estimation_statistics removed
                    # Use estimation(action=estimate|analyze|stats) instead
                    elif name == "improve_task_clarity":
                        # Redirect to task_workflow(action="clarity")
                        if _task_workflow is None:
                            result = json.dumps({"success": False, "error": "task_workflow tool not available"}, indent=2)
                        else:
                            result = _task_workflow(
                                action="clarity",
                                auto_apply=arguments.get("auto_apply", False),
                                output_format=arguments.get("output_format", "text"),
                                output_path=arguments.get("output_path"),
                            )
                    elif name == "cleanup_stale_tasks":
                        # Redirect to task_workflow(action="cleanup")
                        if _task_workflow is None:
                            result = json.dumps({"success": False, "error": "task_workflow tool not available"}, indent=2)
                        else:
                            result = _task_workflow(
                                action="cleanup",
                                stale_threshold_hours=arguments.get("stale_threshold_hours", 2.0),
                                dry_run=arguments.get("dry_run", False),
                                output_path=arguments.get("output_path"),
                            )
                    elif name == "analyze_todo2_alignment" or name == "analyze_prd_alignment":
                        # Redirect to analyze_alignment
                        if _analyze_alignment is None:
                            result = json.dumps({"success": False, "error": "analyze_alignment tool not available"}, indent=2)
                        else:
                            action = "todo2" if name == "analyze_todo2_alignment" else "prd"
                            result = _analyze_alignment(
                                action=action,
                                create_followup_tasks=arguments.get("create_followup_tasks", True),
                                output_path=arguments.get("output_path"),
                            )
                    elif name == "memory_maint":
                        result = _memory_maint(
                            arguments.get("action", "health"),
                            arguments.get("max_age_days", 90),
                            arguments.get("delete_orphaned", True),
                            arguments.get("delete_duplicates", True),
                            arguments.get("scorecard_max_age_days", 7),
                            arguments.get("value_threshold", 0.3),
                            arguments.get("keep_minimum", 50),
                            arguments.get("similarity_threshold", 0.85),
                            arguments.get("merge_strategy", "newest"),
                            arguments.get("scope", "week"),
                            arguments.get("advisors"),
                            arguments.get("generate_insights", True),
                            arguments.get("save_dream", True),
                            arguments.get("dry_run", True),
                            arguments.get("interactive", True),
                        )
                    elif name == "automation":
                        if _automation is None:
                            result = json.dumps({"success": False, "error": "automation tool not available"}, indent=2)
                        else:
                            result = _automation(
                                action=arguments.get("action", "daily"),
                                tasks=arguments.get("tasks"),
                                include_slow=arguments.get("include_slow", False),
                                max_tasks_per_host=arguments.get("max_tasks_per_host", 5),
                                max_parallel_tasks=arguments.get("max_parallel_tasks", 10),
                                priority_filter=arguments.get("priority_filter"),
                                tag_filter=arguments.get("tag_filter"),
                                max_iterations=arguments.get("max_iterations", 10),
                                auto_approve=arguments.get("auto_approve", True),
                                extract_subtasks=arguments.get("extract_subtasks", True),
                                run_analysis_tools=arguments.get("run_analysis_tools", True),
                                run_testing_tools=arguments.get("run_testing_tools", True),
                                min_value_score=arguments.get("min_value_score", 0.7),
                                dry_run=arguments.get("dry_run", False),
                                output_path=arguments.get("output_path"),
                                notify=arguments.get("notify", False),
                            )
                    elif name == "analyze_alignment":
                        if _analyze_alignment is None:
                            result = json.dumps({"success": False, "error": "analyze_alignment tool not available"}, indent=2)
                        else:
                            result = _analyze_alignment(
                                action=arguments.get("action", "todo2"),
                                create_followup_tasks=arguments.get("create_followup_tasks", True),
                                output_path=arguments.get("output_path"),
                            )
                    # NOTE: run_daily_automation, run_nightly_automation, run_sprint_automation, run_discover_automation removed
                    # Use automation(action=daily|nightly|sprint|discover) instead
                    # NOTE: analyze_todo2_alignment, analyze_prd_alignment removed
                    # Use analyze_alignment(action=todo2|prd) instead
                    elif name == "tool_catalog":
                        result = _tool_catalog(
                            arguments.get("action", "list"),
                            arguments.get("category"),
                            arguments.get("persona"),
                            arguments.get("include_examples", True),
                            arguments.get("tool_name"),
                        )
                    elif name == "workflow_mode":
                        result = _workflow_mode(
                            arguments.get("action", "focus"),
                            arguments.get("mode"),
                            arguments.get("enable_group"),
                            arguments.get("disable_group"),
                            arguments.get("status", False),
                            arguments.get("text"),
                            arguments.get("auto_switch", False),
                        )
                    elif name == "context":
                        result = _context(
                            arguments.get("action", "summarize"),
                            arguments.get("data"),
                            arguments.get("level", "brief"),
                            arguments.get("tool_type"),
                            arguments.get("max_tokens"),
                            arguments.get("include_raw", False),
                            arguments.get("items"),
                            arguments.get("budget_tokens", 4000),
                            arguments.get("combine", True),
                        )
                    elif name == "recommend":
                        result = _recommend(
                            action=arguments.get("action", "model"),
                            task_description=arguments.get("task_description"),
                            task_type=arguments.get("task_type"),
                            optimize_for=arguments.get("optimize_for", "quality"),
                            include_alternatives=arguments.get("include_alternatives", True),
                            task_id=arguments.get("task_id"),
                            include_rationale=arguments.get("include_rationale", True),
                            metric=arguments.get("metric"),
                            tool=arguments.get("tool"),
                            stage=arguments.get("stage"),
                            score=arguments.get("score", 50.0),
                            context=arguments.get("context", ""),
                            log=arguments.get("log", True),
                            session_mode=None,
                        )
                    # Git-inspired tools (conditionally available)
                    elif name == "get_task_commits_tool":
                        try:
                            from .tools.git_inspired_tools import get_task_commits
                            result = get_task_commits(
                                arguments.get("task_id"),
                                arguments.get("branch"),
                                arguments.get("limit", 50),
                            )
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "get_branch_commits_tool":
                        try:
                            from .tools.git_inspired_tools import get_branch_commits
                            result = get_branch_commits(
                                arguments.get("branch"),
                                arguments.get("limit", 100),
                            )
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "list_branches_tool":
                        try:
                            from .tools.git_inspired_tools import list_branches
                            result = list_branches()
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "get_branch_tasks_tool":
                        try:
                            from .tools.git_inspired_tools import get_branch_tasks
                            result = get_branch_tasks(arguments.get("branch"))
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "compare_task_diff_tool":
                        try:
                            from .tools.git_inspired_tools import compare_task_diff
                            result = compare_task_diff(
                                arguments.get("task_id"),
                                arguments.get("commit1"),
                                arguments.get("commit2"),
                                arguments.get("time1"),
                                arguments.get("time2"),
                            )
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "generate_graph_tool":
                        try:
                            from .tools.git_inspired_tools import generate_graph
                            result = generate_graph(
                                arguments.get("branch"),
                                arguments.get("task_id"),
                                arguments.get("format", "text"),
                                arguments.get("output_path"),
                                arguments.get("max_commits", 50),
                            )
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "merge_branch_tools_tool":
                        try:
                            from .tools.git_inspired_tools import merge_branch_tools
                            result = merge_branch_tools(
                                arguments.get("source_branch"),
                                arguments.get("target_branch"),
                                arguments.get("conflict_strategy", "newer"),
                                arguments.get("author", "system"),
                                arguments.get("dry_run", False),
                            )
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    elif name == "set_task_branch":
                        try:
                            from .tools.git_inspired_tools import set_task_branch_tool
                            result = set_task_branch_tool(
                                arguments.get("task_id"),
                                arguments.get("branch"),
                            )
                            if not isinstance(result, str):
                                result = json.dumps(result, indent=2)
                        except ImportError:
                            result = json.dumps({"success": False, "error": "Git-inspired tools not available"}, indent=2)
                    else:
                        result = json.dumps({"error": f"Unknown tool: {name}"})
                else:
                    result = json.dumps({"error": f"Unknown tool: {name}"})
            else:
                result = json.dumps({"error": "Tools not available"})
            
            # Ensure result is always a JSON string
            if not isinstance(result, str):
                result = json.dumps(result, indent=2)

            return [TextContent(type="text", text=result)]

        return None


# Register tools
register_tools()

if mcp:
    # Register high-priority tools
    if TOOLS_AVAILABLE:

        # NOTE: check_documentation_health removed - use health(type="docs")
        # NOTE: analyze_todo2_alignment removed - use analyze_alignment(type="todo2")

        # NOTE: detect_duplicate_tasks removed - use task_analysis(action="duplicates")
        # NOTE: scan_dependency_security removed - use security(action="scan")
        # NOTE: find_automation_opportunities removed - use run_automation(mode="discover")
        # NOTE: sync_todo_tasks removed - use task_workflow(action="sync")

        # NOTE: cleanup_stale_tasks removed - use task_workflow(action="cleanup")

        @ensure_json_string
        @mcp.tool()
        def add_external_tool_hints(
            dry_run: bool = False, output_path: Optional[str] = None, min_file_size: int = 50
        ) -> str:
            """[HINT: Tool hints. Files scanned, modified, hints added.]"""
            return _add_external_tool_hints(dry_run, output_path, min_file_size)

        # NOTE: analyze_problems, run_linter removed - use lint(action=analyze|run)
        # NOTE: list_problem_categories removed - use resource automation://problem-categories
        # NOTE: get_linter_status removed - use resource automation://linters

        # NOTE: run_daily_automation, run_nightly_automation, run_sprint_automation, run_discover_automation removed
        # Use automation(action=daily|nightly|sprint|discover) instead

        @ensure_json_string
        @mcp.tool()
        def automation(
            action: str = "daily",
            tasks: Optional[list[str]] = None,
            include_slow: bool = False,
            max_tasks_per_host: int = 5,
            max_parallel_tasks: int = 10,
            priority_filter: Optional[str] = None,
            tag_filter: Optional[list[str]] = None,
            max_iterations: int = 10,
            auto_approve: bool = True,
            extract_subtasks: bool = True,
            run_analysis_tools: bool = True,
            run_testing_tools: bool = True,
            min_value_score: float = 0.7,
            dry_run: bool = False,
            output_path: Optional[str] = None,
            notify: bool = False,
        ) -> str:
            """
            [HINT: Automation. action=daily|nightly|sprint|discover. Unified automation tool.]

            Unified automation tool consolidating daily, nightly, sprint, and discovery automation.

            Actions:
            - action="daily": Run daily maintenance tasks (docs_health, alignment, duplicates, security)
            - action="nightly": Process background-capable tasks automatically with host limits
            - action="sprint": Full sprint automation with subtask extraction and auto-approval
            - action="discover": Find automation opportunities in codebase

            📊 Output: Automation results based on action
            🔧 Side Effects: Creates tasks, processes tasks, generates reports
            ⏱️ Typical Runtime: Varies by action (daily: <30s, nightly: minutes, sprint: minutes, discover: <10s)

            Args:
                action: "daily", "nightly", "sprint", or "discover"
                tasks: List of task IDs to run (daily action)
                include_slow: Include slow tasks (daily action)
                max_tasks_per_host: Max tasks per host (nightly action)
                max_parallel_tasks: Max parallel tasks (nightly action)
                priority_filter: Filter by priority (nightly/sprint actions)
                tag_filter: Filter by tags (nightly/sprint actions)
                max_iterations: Max sprint iterations (sprint action)
                auto_approve: Auto-approve tasks (sprint action)
                extract_subtasks: Extract subtasks (sprint action)
                run_analysis_tools: Run analysis tools (sprint action)
                run_testing_tools: Run testing tools (sprint action)
                min_value_score: Min value score threshold (discover action)
                dry_run: Preview without applying
                output_path: Save results to file
                notify: Send notifications (nightly/sprint actions)

            Examples:
                automation(action="daily")
                → Run daily maintenance checks

                automation(action="nightly", max_tasks_per_host=10)
                → Process tasks with higher host limit

                automation(action="sprint", max_iterations=5)
                → Run sprint with fewer iterations
            """
            if _automation is None:
                return json.dumps({
                    "success": False,
                    "error": "automation tool not available - import failed"
                }, indent=2)
            return _automation(
                action=action,
                tasks=tasks,
                include_slow=include_slow,
                max_tasks_per_host=max_tasks_per_host,
                max_parallel_tasks=max_parallel_tasks,
                priority_filter=priority_filter,
                tag_filter=tag_filter,
                max_iterations=max_iterations,
                auto_approve=auto_approve,
                extract_subtasks=extract_subtasks,
                run_analysis_tools=run_analysis_tools,
                run_testing_tools=run_testing_tools,
                min_value_score=min_value_score,
                dry_run=dry_run,
                output_path=output_path,
                notify=notify,
            )

        # NOTE: validate_ci_cd_workflow removed - use health(action="cicd")
        # NOTE: batch_approve_tasks removed - use task_workflow(action="approve")
        # NOTE: run_nightly_task_automation removed - use run_nightly_automation()
        # NOTE: check_working_copy_health removed - use health(action="git")
        # NOTE: clarification removed - use task_workflow(action="clarify")
        # NOTE: setup_git_hooks removed - use setup_hooks(type="git")
        # NOTE: setup_pattern_triggers removed - use setup_hooks(type="patterns")
        # NOTE: run_tests, analyze_test_coverage removed - use testing(action=run|coverage|suggest|validate)
        # NOTE: run_automation removed - use run_daily_automation, run_nightly_automation, run_sprint_automation, or run_discover_automation

        # NOTE: simplify_rules removed - use generate_config(action="simplify")

        # Helper for scorecard (shared implementation)
        def _scorecard_impl(output_format: str, include_recommendations: bool, output_path: Optional[str]) -> str:
            result = _generate_project_scorecard(output_format, include_recommendations, output_path)
            return json.dumps(
                {
                    "overall_score": result["overall_score"],
                    "production_ready": result["production_ready"],
                    "blockers": result.get("blockers", []),
                    "scores": result["scores"],
                    "recommendations": result.get("recommendations", []),
                    "formatted_output": result["formatted_output"],
                },
                separators=(",", ":"),
            )

        # NOTE: generate_project_scorecard removed - use report(type="scorecard")

        # Helper for overview (shared implementation)
        def _overview_impl(output_format: str, output_path: Optional[str]) -> str:
            result = _generate_project_overview(output_format, output_path)
            return json.dumps(
                {
                    "output_format": result["output_format"],
                    "generated_at": result["generated_at"],
                    "output_file": result.get("output_file"),
                    "formatted_output": result["formatted_output"],
                },
                separators=(",", ":"),
            )

        # NOTE: generate_project_overview removed - use report(type="overview")
        # NOTE: generate_prd removed - use report(type="prd")
        # NOTE: analyze_prd_alignment removed - use analyze_alignment(type="prd")

        # NOTE: recommend_workflow_mode removed - LLM can determine from task complexity
        # NOTE: generate_cursorignore removed - use generate_config(action="ignore")

        # NOTE: check_definition_of_done removed - use health(type="dod")
        # NOTE: generate_cursor_rules removed - use generate_config(type="rules")

        # NOTE: log_prompt_iteration removed - use prompt_tracking(action="log")
        # NOTE: analyze_prompt_iterations removed - use prompt_tracking(action="analyze")

        # NOTE: recommend_model, recommend_workflow_mode, consult_advisor removed - use recommend(action=model|workflow|advisor)
        # NOTE: list_available_models removed - use resource automation://models

        # ═══════════════════════════════════════════════════════════════════
        # DISCOVERY TOOL (CONSOLIDATED)
        # ═══════════════════════════════════════════════════════════════════

        @ensure_json_string
        @mcp.tool()
        def tool_catalog(
            action: str = "list",
            category: Optional[str] = None,
            persona: Optional[str] = None,
            include_examples: bool = True,
            tool_name: Optional[str] = None,
        ) -> str:
            """
            [HINT: Tool catalog. action=list|help. Unified tool catalog and help.]

            Unified tool catalog tool consolidating tool browsing and help operations.

            📊 Output: Tool catalog or detailed tool documentation
            🔧 Side Effects: None
            ⏱️ Typical Runtime: <1 second

            Args:
                action: "list" for tool catalog, "help" for specific tool documentation
                category: Filter by category (list action)
                persona: Filter by persona (list action)
                include_examples: Include example prompts (list action)
                tool_name: Name of tool to get help for (help action)

            Examples:
                tool_catalog(action="list", category="security")
                → Filtered tool catalog

                tool_catalog(action="help", tool_name="project_scorecard")
                → Detailed tool documentation
            """
            return _tool_catalog(action, category, persona, include_examples, tool_name)

        # NOTE: focus_mode, suggest_mode, tool_usage_stats removed - use workflow_mode(action=focus|suggest|stats)

        @mcp.tool()
        async def workflow_mode(
            action: str = "focus",
            mode: Optional[str] = None,
            enable_group: Optional[str] = None,
            disable_group: Optional[str] = None,
            status: bool = False,
            text: Optional[str] = None,
            auto_switch: bool = False,
            ctx: Any = None,
        ) -> str:
            """
            [HINT: Workflow mode management. action=focus|suggest|stats. Unified workflow operations.]

            Unified workflow mode management tool consolidating focus, suggestions, and usage statistics.

            Actions:
            - action="focus": Manage workflow modes and tool groups
            - action="suggest": Get mode suggestions based on context/usage
            - action="stats": View tool usage analytics and patterns

            📊 Output: Mode status, suggestions, or usage statistics
            🔧 Side Effects: May update tool visibility and send notifications
            ⏱️ Typical Runtime: <100ms

            Modes (focus action):
            - daily_checkin: Health + overview (9 tools, 82% reduction)
            - security_review: Security-focused (12 tools, 77% reduction)
            - task_management: Task tools only (10 tools, 81% reduction)
            - sprint_planning: Tasks + automation + PRD (15 tools, 71% reduction)
            - code_review: Testing + linting (10 tools, 81% reduction)
            - development: Balanced set (25 tools, 52% reduction) [default]
            - debugging: Memory + testing (17 tools, 67% reduction)
            - all: Full tool access (52 tools)

            Args:
                action: "focus" to manage modes/groups, "suggest" for suggestions, "stats" for analytics
                mode: Workflow mode to switch to (focus action)
                enable_group: Specific group to enable (focus action)
                disable_group: Specific group to disable (focus action)
                status: If True, return current status without changes (focus action)
                text: Optional text to analyze for mode suggestion (suggest action)
                auto_switch: If True, automatically switch to suggested mode (suggest action)

            Examples:
                workflow_mode(action="focus", mode="security_review")
                → Switch to security review mode

                workflow_mode(action="suggest", text="vulnerability scanning")
                → Get mode suggestion for security work

                workflow_mode(action="stats")
                → View usage analytics
            """
            result = _workflow_mode(action, mode, enable_group, disable_group, status, text, auto_switch)

            # Send notification if mode changed (for focus or auto-switched suggest)
            if ctx:
                should_notify = False
                if action == "focus" and (mode or enable_group or disable_group):
                    should_notify = True
                elif action == "suggest" and auto_switch:
                    try:
                        import json
                        parsed = json.loads(result)
                        if parsed.get("auto_switched"):
                            should_notify = True
                    except Exception:
                        pass

                if should_notify:
                    try:
                        from .context_helpers import notify_tools_changed
                        await notify_tools_changed(ctx)
                    except Exception as e:
                        logger.debug(f"Could not notify tools changed: {e}")

            return result

        # ═══════════════════════════════════════════════════════════════════
        # CONTEXT MANAGEMENT TOOL (CONSOLIDATED)
        # ═══════════════════════════════════════════════════════════════════

        @ensure_json_string
        @mcp.tool()
        def context(
            action: str = "summarize",
            data: Optional[str] = None,
            level: str = "brief",
            tool_type: Optional[str] = None,
            max_tokens: Optional[int] = None,
            include_raw: bool = False,
            items: Optional[str] = None,
            budget_tokens: int = 4000,
            combine: bool = True,
        ) -> str:
            """
            [HINT: Context management. action=summarize|budget|batch. Unified context operations.]

            Unified context management tool consolidating summarization, budgeting, and batch operations.

            📊 Output: Context operation results (summary, budget analysis, or batch summaries)
            🔧 Side Effects: None
            ⏱️ Typical Runtime: <10ms

            Args:
                action: "summarize" for single item, "budget" for token analysis, "batch" for multiple items
                data: JSON string to summarize (summarize action)
                level: Summarization level - "brief", "detailed", "key_metrics", "actionable" (summarize/batch actions)
                tool_type: Tool type hint for smarter summarization (summarize action)
                max_tokens: Maximum tokens for output (summarize action)
                include_raw: Include original data in response (summarize action)
                items: JSON array of items to analyze (budget/batch actions)
                budget_tokens: Target token budget (budget action)
                combine: Merge summaries into combined view (batch action)

            Examples:
                context(action="summarize", data=health_result, level="brief")
                → "Health: 85/100, 3 issues, 2 actions"

                context(action="budget", items=json_array, budget_tokens=4000)
                → Token analysis with reduction strategy

                context(action="batch", items=json_array, level="brief")
                → Combined summaries of multiple items
            """
            return _context(action, data, level, tool_type, max_tokens, include_raw, items, budget_tokens, combine)

        # NOTE: get_tool_help removed - use resource automation://tools for tool info
        # NOTE: project_overview removed - use generate_project_overview

        # NOTE: consolidate_tags removed - use task_analysis(action="tags")
        # NOTE: analyze_task_hierarchy removed - use task_analysis(action="hierarchy")

        # ═══════════════════════════════════════════════════════════════════
        # RECOMMENDATION TOOL (CONSOLIDATED)
        # ═══════════════════════════════════════════════════════════════════

        @ensure_json_string
        @mcp.tool()
        def recommend(
            action: str = "model",
            task_description: Optional[str] = None,
            task_type: Optional[str] = None,
            optimize_for: str = "quality",
            include_alternatives: bool = True,
            task_id: Optional[str] = None,
            include_rationale: bool = True,
            metric: Optional[str] = None,
            tool: Optional[str] = None,
            stage: Optional[str] = None,
            score: float = 50.0,
            context: str = "",
            log: bool = True,
        ) -> str:
            """
            [HINT: Recommendations. action=model|workflow|advisor. Unified recommendation system.]

            Unified recommendation tool consolidating model selection, workflow mode suggestions, and advisor consultations.

            Actions:
            - action="model": Recommend optimal AI model based on task
            - action="workflow": Suggest AGENT vs ASK mode based on task complexity
            - action="advisor": Get wisdom from trusted advisors

            📊 Output: Model recommendations, mode suggestions, or advisor wisdom
            🔧 Side Effects: May log consultations (advisor action)
            ⏱️ Typical Runtime: <1 second

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

            Examples:
                recommend(action="model", task_description="implement authentication")
                → AI model recommendation

                recommend(action="workflow", task_description="refactor database layer")
                → AGENT/ASK mode suggestion

                recommend(action="advisor", metric="security", score=75.0)
                → Advisor wisdom for security metric
            """
            return _recommend(
                action=action,
                task_description=task_description,
                task_type=task_type,
                optimize_for=optimize_for,
                include_alternatives=include_alternatives,
                task_id=task_id,
                include_rationale=include_rationale,
                metric=metric,
                tool=tool,
                stage=stage,
                score=score,
                context=context,
                log=log,
                session_mode=None  # Will be auto-detected in consolidated function
            )

        # NOTE: get_advisor_briefing removed - use report(type="briefing")

        # ═══════════════════════════════════════════════════════════════════
        # DEPENDABOT INTEGRATION TOOLS
        # ═══════════════════════════════════════════════════════════════════

        # NOTE: fetch_dependabot_alerts removed - use security(action="alerts")
        # NOTE: generate_security_report removed - use security(action="report")

    # ═══════════════════════════════════════════════════════════════════════════════
    # CONSOLIDATED TOOLS (Phase 3 consolidation)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Note: CONSOLIDATED_AVAILABLE is now defined in register_tools() to be available
    # to stdio server's list_tools() function. This section is for FastMCP only.
    # The imports are duplicated in register_tools() for stdio server access.

    if CONSOLIDATED_AVAILABLE:
        # NOTE: analyze_todo2_alignment, analyze_prd_alignment removed
        # Use analyze_alignment(action=todo2|prd) instead

        @ensure_json_string
        @mcp.tool()
        def analyze_alignment(
            action: str = "todo2",
            create_followup_tasks: bool = True,
            output_path: Optional[str] = None,
        ) -> str:
            """
            [HINT: Alignment analysis. action=todo2|prd. Unified alignment analysis tool.]

            Unified alignment analysis tool consolidating Todo2 and PRD alignment.

            Actions:
            - action="todo2": Analyze task alignment with project goals, find misaligned tasks
            - action="prd": Analyze PRD alignment with persona mapping and advisor assignments

            📊 Output: Alignment scores, misaligned items, recommendations
            🔧 Side Effects: Creates tasks/reports based on action
            ⏱️ Typical Runtime: <5 seconds

            Args:
                action: "todo2" for task alignment, "prd" for PRD persona mapping
                create_followup_tasks: Create tasks for misaligned items (todo2 action)
                output_path: Optional file to save results

            Examples:
                analyze_alignment(action="todo2")
                → Analyze task-to-goals alignment

                analyze_alignment(action="prd", output_path="prd_alignment.json")
                → Analyze PRD alignment and save results
            """
            if _analyze_alignment is None:
                return json.dumps({
                    "success": False,
                    "error": "analyze_alignment tool not available - import failed"
                }, indent=2)
            return _analyze_alignment(action, create_followup_tasks, output_path)

        @ensure_json_string
        @mcp.tool()
        def security(
            action: str = "report",
            repo: str = "davidl71/project-management-automation",
            languages: Optional[list[str]] = None,
            config_path: Optional[str] = None,
            state: str = "open",
            include_dismissed: bool = False,
            alert_critical: bool = False,
        ) -> str:
            """
            [HINT: Security. action=scan|alerts|report. Vulnerabilities, remediation.]

            Unified security analysis:
            - action="scan": Local pip-audit dependency scan
            - action="alerts": Fetch GitHub Dependabot alerts
            - action="report": Combined security report (Dependabot + pip-audit)

            📊 Output: Vulnerabilities by severity, remediation recommendations
            🔧 Side Effects: None (read-only)
            """
            return _security(action, repo, languages, config_path, state, include_dismissed, alert_critical=alert_critical)

        @ensure_json_string
        @mcp.tool()
        def generate_config(
            action: str = "rules",
            rules: Optional[str] = None,
            overwrite: bool = False,
            analyze_only: bool = False,
            include_indexing: bool = True,
            analyze_project: bool = True,
            rule_files: Optional[str] = None,
            output_dir: Optional[str] = None,
            dry_run: bool = False,
        ) -> str:
            """
            [HINT: Config generation. action=rules|ignore|simplify. Creates IDE config files.]

            Unified config generation:
            - action="rules": Generate .cursor/rules/*.mdc files
            - action="ignore": Generate .cursorignore/.cursorindexingignore
            - action="simplify": Simplify existing rule files

            📊 Output: Generated files, changes made
            🔧 Side Effects: Creates/updates config files (unless dry_run=True)
            """
            return _generate_config(
                action, rules, overwrite, analyze_only,
                include_indexing, analyze_project,
                rule_files, output_dir, dry_run
            )

        @ensure_json_string
        @mcp.tool()
        def setup_hooks(
            action: str = "git",
            hooks: Optional[list[str]] = None,
            patterns: Optional[str] = None,
            config_path: Optional[str] = None,
            install: bool = True,
            dry_run: bool = False,
        ) -> str:
            """
            [HINT: Hooks setup. action=git|patterns. Install automation hooks.]

            Unified hooks setup:
            - action="git": Install git hooks (pre-commit, pre-push, etc.)
            - action="patterns": Install pattern triggers for file/task automation

            📊 Output: Installation status, hooks configured
            🔧 Side Effects: Installs hooks (unless dry_run=True)
            """
            return _setup_hooks(action, hooks, patterns, config_path, install, dry_run)

        @ensure_json_string
        @mcp.tool()
        def prompt_tracking(
            action: str = "analyze",
            prompt: Optional[str] = None,
            task_id: Optional[str] = None,
            mode: Optional[str] = None,
            outcome: Optional[str] = None,
            iteration: int = 1,
            days: int = 7,
        ) -> str:
            """
            [HINT: Prompt tracking. action=log|analyze. Track and analyze prompts.]

            Unified prompt tracking:
            - action="log": Log a prompt iteration (requires prompt parameter)
            - action="analyze": Analyze prompt patterns over time

            📊 Output: Log confirmation or iteration statistics
            🔧 Side Effects: Writes to .cursor/prompt_history/ (log action)
            """
            return _prompt_tracking(action, prompt, task_id, mode, outcome, iteration, days)

        @ensure_json_string
        @mcp.tool()
        def health(
            action: str = "server",
            agent_name: Optional[str] = None,
            check_remote: bool = True,
            output_path: Optional[str] = None,
            create_tasks: bool = True,
            task_id: Optional[str] = None,
            changed_files: Optional[str] = None,
            auto_check: bool = True,
            workflow_path: Optional[str] = None,
            check_runners: bool = True,
        ) -> str:
            """
            [HINT: Health check. action=server|git|docs|dod|cicd. Status and health metrics.]

            Unified health check:
            - action="server": Server operational status, version
            - action="git": Working copy health, uncommitted changes, sync status
            - action="docs": Documentation health score, broken links
            - action="dod": Definition of done validation for task completion
            - action="cicd": CI/CD workflow validation, runner config

            📊 Output: Health status and metrics
            🔧 Side Effects: Creates tasks (docs action with create_tasks=True)
            """
            return _health(
                action, agent_name, check_remote, output_path, create_tasks,
                task_id, changed_files, auto_check, workflow_path, check_runners
            )

        @ensure_json_string
        @mcp.tool()
        def check_attribution(
            output_path: Optional[str] = None,
            create_tasks: bool = True,
        ) -> str:
            """
            [HINT: Attribution compliance check. Verify proper attribution for all third-party components.]

            Checks attribution compliance across the codebase:
            - Missing attribution in file headers
            - Missing entries in ATTRIBUTIONS.md
            - Uncredited third-party references
            - Dependency license compliance

            📊 Output: Attribution score (0-100), compliance status, issues found
            🔧 Side Effects: Creates compliance report and optional Todo2 tasks
            ⏱️ Typical Runtime: 1-3 seconds

            Args:
                output_path: Path for report output (default: docs/ATTRIBUTION_COMPLIANCE_REPORT.md)
                create_tasks: Whether to create Todo2 tasks for issues found (default: true)

            Returns:
                JSON with attribution_score, status, compliant_files count, issues_found, warnings, report_path

            Examples:
                check_attribution()
                → Full compliance check with default settings

                check_attribution(create_tasks=False)
                → Check without creating tasks

                check_attribution(output_path="custom_report.md")
                → Custom report location
            """
            result = _check_attribution_compliance(output_path, create_tasks)
            # Result is already JSON string from tool wrapper
            return result

        @mcp.tool()
        @ensure_json_string
        def report(
            action: str = "overview",
            output_format: str = "text",
            output_path: Optional[str] = None,
            include_recommendations: bool = True,
            overall_score: float = 50.0,
            security_score: float = 50.0,
            testing_score: float = 50.0,
            documentation_score: float = 50.0,
            completion_score: float = 50.0,
            alignment_score: float = 50.0,
            project_name: Optional[str] = None,
            include_architecture: bool = True,
            include_metrics: bool = True,
            include_tasks: bool = True,
        ) -> str:
            """
            [HINT: Report generation. action=overview|scorecard|briefing|prd. Project reports.]

            Unified report generation:
            - action="overview": One-page project overview for stakeholders
            - action="scorecard": Health metrics scorecard with component scores
            - action="briefing": Advisor wisdom summary for lowest-scoring areas
            - action="prd": Product requirements document from codebase

            📊 Output: Generated report in specified format
            🔧 Side Effects: Creates file (if output_path specified)
            """
            # Explicitly ensure string return to avoid FastMCP async issues
            # Call the underlying function and ensure it's a string
            result = _report(
                action, output_format, output_path, include_recommendations,
                overall_score, security_score, testing_score,
                documentation_score, completion_score, alignment_score,
                project_name, include_architecture, include_metrics, include_tasks
            )
            # Force string conversion at this level - FastMCP requires strings
            import json
            if isinstance(result, str):
                return result
            elif isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            else:
                return json.dumps({"result": str(result)}, indent=2)

        @ensure_json_string
        @mcp.tool()
        def task_analysis(
            action: str = "duplicates",
            similarity_threshold: float = 0.85,
            auto_fix: bool = False,
            dry_run: bool = True,
            custom_rules: Optional[str] = None,
            remove_tags: Optional[str] = None,
            output_format: str = "text",
            include_recommendations: bool = True,
            output_path: Optional[str] = None,
        ) -> str:
            """
            [HINT: Task analysis. action=duplicates|tags|hierarchy|dependencies|parallelization. Task quality and structure.]

            Unified task analysis:
            - action="duplicates": Find duplicate tasks by similarity
            - action="tags": Consolidate/cleanup task tags
            - action="hierarchy": Analyze task structure and groupings
            - action="dependencies": Analyze dependency chains, detect cycles, find critical paths
            - action="parallelization": Identify tasks that can run in parallel

            📊 Output: Analysis results with recommendations
            🔧 Side Effects: Modifies tasks (duplicates with auto_fix, tags without dry_run)
            """
            return _task_analysis(
                action, similarity_threshold, auto_fix, dry_run,
                custom_rules, remove_tags, output_format,
                include_recommendations, output_path
            )

        @ensure_json_string
        @mcp.tool()
        def testing(
            action: str = "run",
            test_path: Optional[str] = None,
            test_framework: str = "auto",
            verbose: bool = True,
            coverage: bool = False,
            coverage_file: Optional[str] = None,
            min_coverage: int = 80,
            format: str = "html",
            target_file: Optional[str] = None,
            min_confidence: float = 0.7,
            framework: Optional[str] = None,
            output_path: Optional[str] = None,
        ) -> str:
            """
            [HINT: Testing tool. action=run|coverage|suggest|validate. Execute tests, analyze coverage, suggest test cases, or validate test structure.]

            Unified testing:
            - action="run": Execute test suite (pytest/unittest/ctest)
            - action="coverage": Analyze test coverage with threshold
            - action="suggest": Suggest test cases based on code analysis
            - action="validate": Validate test organization and patterns

            📊 Output: Test results, coverage analysis, test suggestions, or validation report
            🔧 Side Effects: May generate coverage reports, suggestion files, or validation reports
            """
            return _testing(
                action, test_path, test_framework, verbose, coverage,
                coverage_file, min_coverage, format, target_file, min_confidence,
                framework, output_path
            )

        @ensure_json_string
        @mcp.tool()
        def lint(
            action: str = "run",
            path: Optional[str] = None,
            linter: str = "ruff",
            fix: bool = False,
            analyze: bool = True,
            select: Optional[str] = None,
            ignore: Optional[str] = None,
            problems_json: Optional[str] = None,
            include_hints: bool = True,
            output_path: Optional[str] = None,
        ) -> str:
            """
            [HINT: Linting tool. action=run|analyze. Run linter or analyze problems.]

            Unified linting:
            - action="run": Execute linter (ruff/flake8), optionally analyze results
            - action="analyze": Analyze problems JSON with resolution hints

            📊 Output: Linter results or problem analysis
            🔧 Side Effects: May auto-fix issues (with fix=true)
            """
            return _lint(
                action, path, linter, fix, analyze, select, ignore,
                problems_json, include_hints, output_path
            )

        @ensure_json_string
        @mcp.tool()
        def memory(
            action: str = "search",
            title: Optional[str] = None,
            content: Optional[str] = None,
            category: str = "insight",
            task_id: Optional[str] = None,
            metadata: Optional[str] = None,
            include_related: bool = True,
            query: Optional[str] = None,
            limit: int = 10,
        ) -> str:
            """
            [HINT: Memory tool. action=save|recall|search. Persist and retrieve AI discoveries.]

            Unified memory management:
            - action="save": Store insight with title, content, category
            - action="recall": Get memories for a task_id
            - action="search": Find memories by query text

            Categories: debug, research, architecture, preference, insight

            📊 Output: Memory operation results
            🔧 Side Effects: Creates/retrieves memory files
            """
            return _memory(
                action, title, content, category, task_id, metadata,
                include_related, query, limit
            )

        @ensure_json_string
        @mcp.tool()
        def task_discovery(
            action: str = "all",
            file_patterns: Optional[str] = None,
            include_fixme: bool = True,
            doc_path: Optional[str] = None,
            output_path: Optional[str] = None,
            create_tasks: bool = False,
        ) -> str:
            """
            [HINT: Task discovery. action=comments|markdown|orphans|all. Find tasks from various sources.]

            Discovers tasks from:
            - action="comments": TODO/FIXME in code files
            - action="markdown": Task lists in *.md files
            - action="orphans": Orphaned Todo2 tasks (no dependencies)
            - action="all": All sources combined

            📊 Output: Discovered tasks with locations
            🔧 Side Effects: Can create Todo2 tasks (create_tasks=true)
            """
            return _task_discovery(
                action, file_patterns, include_fixme, doc_path, output_path, create_tasks
            )

        # NOTE: improve_task_clarity removed - use task_workflow(action="clarity")
        # NOTE: cleanup_stale_tasks removed - use task_workflow(action="cleanup")

        @ensure_json_string
        @mcp.tool()
        def task_workflow(
            action: str = "sync",
            dry_run: bool = False,
            status: str = "Review",
            new_status: str = "Todo",
            clarification_none: bool = True,
            filter_tag: Optional[str] = None,
            task_ids: Optional[str] = None,
            sub_action: str = "list",
            task_id: Optional[str] = None,
            clarification_text: Optional[str] = None,
            decision: Optional[str] = None,
            decisions_json: Optional[str] = None,
            move_to_todo: bool = True,
            auto_apply: bool = False,
            output_format: str = "text",
            stale_threshold_hours: float = 2.0,
            output_path: Optional[str] = None,
        ) -> str:
            """
            [HINT: Task workflow. action=sync|approve|clarify|clarity|cleanup. Manage task lifecycle.]

            Unified task workflow tool consolidating sync, approval, clarification, clarity improvement, and stale cleanup.

            Actions:
            - action="sync": Sync TODO markdown tables ↔ Todo2
            - action="approve": Bulk approve/move tasks by status
            - action="clarify": Manage task clarifications (sub_action: list|resolve|batch)
            - action="clarity": Improve task clarity (adds estimates, renames, removes dependencies)
            - action="cleanup": Move stale In Progress tasks back to Todo

            📊 Output: Workflow operation results
            🔧 Side Effects: Modifies task states
            ⏱️ Typical Runtime: <1 second (most actions)

            Args:
                action: "sync", "approve", "clarify", "clarity", or "cleanup"
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

            Examples:
                task_workflow(action="sync")
                → Sync TODO tables

                task_workflow(action="clarity", auto_apply=True)
                → Improve task clarity automatically

                task_workflow(action="cleanup", stale_threshold_hours=4.0)
                → Clean up tasks stale for 4+ hours
            """
            if _task_workflow is None:
                return json.dumps({
                    "success": False,
                    "error": "task_workflow tool not available - import failed"
                }, indent=2)
            return _task_workflow(
                action=action,
                dry_run=dry_run,
                status=status,
                new_status=new_status,
                clarification_none=clarification_none,
                filter_tag=filter_tag,
                task_ids=task_ids,
                sub_action=sub_action,
                task_id=task_id,
                clarification_text=clarification_text,
                decision=decision,
                decisions_json=decisions_json,
                move_to_todo=move_to_todo,
                auto_apply=auto_apply,
                output_format=output_format,
                stale_threshold_hours=stale_threshold_hours,
                output_path=output_path,
            )

        # NOTE: estimate_task_duration, analyze_estimation_accuracy, get_estimation_statistics removed
        # Use estimation(action=estimate|analyze|stats) instead

        @ensure_json_string
        @mcp.tool()
        def estimation(
            action: str = "estimate",
            name: Optional[str] = None,
            details: str = "",
            tags: Optional[str] = None,
            priority: str = "medium",
            use_historical: bool = True,
            detailed: bool = False,
            use_mlx: bool = True,
            mlx_weight: float = 0.3,
        ) -> str:
            """
            [HINT: Estimation. action=estimate|analyze|stats. Unified task duration estimation tool.]

            Unified task duration estimation tool consolidating estimation, accuracy analysis, and statistics.

            Actions:
            - action="estimate": Generate MLX-enhanced time estimate for a task
            - action="analyze": Analyze estimation accuracy from historical data
            - action="stats": Get statistical summary of historical task durations

            📊 Output: Estimation results based on action
            🔧 MLX Enhancement: When use_mlx=True, combines statistical methods with MLX semantic analysis for 30-40% better accuracy
            ⏱️ Typical Runtime: <1 second (estimate), <2 seconds (analyze), <1 second (stats)

            Args:
                action: "estimate", "analyze", or "stats"
                name: Task name (required for estimate action)
                details: Task details (estimate action)
                tags: Comma-separated tags (estimate action)
                priority: Task priority (estimate action)
                use_historical: Use historical data (estimate action)
                detailed: Return detailed breakdown (estimate action)
                use_mlx: Use MLX enhancement (estimate action)
                mlx_weight: MLX weight in hybrid estimate (estimate action)

            Examples:
                estimation(action="estimate", name="Implement feature X", details="...")
                → Generate time estimate

                estimation(action="analyze")
                → Analyze estimation accuracy

                estimation(action="stats")
                → Get statistical summary
            """
            if _estimation is None:
                return json.dumps({
                    "success": False,
                    "error": "estimation tool not available - import failed"
                }, indent=2)
            return _estimation(
                action=action,
                name=name,
                details=details,
                tags=tags,
                priority=priority,
                use_historical=use_historical,
                detailed=detailed,
                use_mlx=use_mlx,
                mlx_weight=mlx_weight,
            )

        @ensure_json_string
        @mcp.tool()
        def memory_maint(
            action: str = "health",
            max_age_days: int = 90,
            delete_orphaned: bool = True,
            delete_duplicates: bool = True,
            scorecard_max_age_days: int = 7,
            value_threshold: float = 0.3,
            keep_minimum: int = 50,
            similarity_threshold: float = 0.85,
            merge_strategy: str = "newest",
            scope: str = "week",
            advisors: Optional[str] = None,
            generate_insights: bool = True,
            save_dream: bool = True,
            dry_run: bool = True,
            interactive: bool = True,
        ) -> str:
            """
            [HINT: Memory maintenance. action=health|gc|prune|consolidate|dream. Lifecycle management.]

            Unified memory maintenance:
            - action="health": Memory system health metrics and recommendations
            - action="gc": Garbage collect stale/orphaned memories
            - action="prune": Remove low-value memories based on scoring
            - action="consolidate": Merge similar/duplicate memories
            - action="dream": Reflect on memories with wisdom advisors

            📊 Output: Maintenance results with recommendations
            🔧 Side Effects: Modifies memories (gc/prune/consolidate with dry_run=False)
            """
            return _memory_maint(
                action, max_age_days, delete_orphaned, delete_duplicates,
                scorecard_max_age_days, value_threshold, keep_minimum,
                similarity_threshold, merge_strategy, scope, advisors,
                generate_insights, save_dream, dry_run, interactive
            )

        # ═══════════════════════════════════════════════════════════════════════════════
        # GIT-INSPIRED TASK MANAGEMENT TOOLS
        # ═══════════════════════════════════════════════════════════════════════════════
        try:
            from .tools.git_inspired_tools import (
                compare_task_diff,
                generate_graph,
                get_branch_commits,
                get_branch_tasks,
                get_task_commits,
                list_branches,
                merge_branch_tools,
                set_task_branch_tool,
            )

            GIT_INSPIRED_TOOLS_AVAILABLE = True
        except ImportError:
            GIT_INSPIRED_TOOLS_AVAILABLE = False
            logger.warning("Git-inspired tools not available")

        if GIT_INSPIRED_TOOLS_AVAILABLE:
            @ensure_json_string
            @mcp.tool()
            def get_task_commits_tool(
                task_id: str,
                branch: Optional[str] = None,
                limit: int = 50,
            ) -> str:
                """
                [HINT: Git-inspired tools. Get commit history for a task.]

                Get commit history for a task showing all changes over time.

                📊 Output: JSON with commit list, timestamps, authors, and messages
                """
                return get_task_commits(task_id, branch, limit)

            @ensure_json_string
            @mcp.tool()
            def get_branch_commits_tool(
                branch: str,
                limit: int = 100,
            ) -> str:
                """
                [HINT: Git-inspired tools. Get all commits for a branch.]

                Get all commits across all tasks in a branch.

                📊 Output: JSON with commit list for the branch
                """
                return get_branch_commits(branch, limit)

            @ensure_json_string
            @mcp.tool()
            def list_branches_tool() -> str:
                """
                [HINT: Git-inspired tools. List all branches with statistics.]

                List all branches (work streams) from tasks and their statistics.

                📊 Output: JSON with branch list and task counts per branch
                """
                return list_branches()

            @ensure_json_string
            @mcp.tool()
            def get_branch_tasks_tool(branch: str) -> str:
                """
                [HINT: Git-inspired tools. Get all tasks in a branch.]

                Get all tasks belonging to a specific branch.

                📊 Output: JSON with task list for the branch
                """
                return get_branch_tasks(branch)

            @ensure_json_string
            @mcp.tool()
            def compare_task_diff_tool(
                task_id: str,
                commit1: Optional[str] = None,
                commit2: Optional[str] = None,
                time1: Optional[str] = None,
                time2: Optional[str] = None,
            ) -> str:
                """
                [HINT: Git-inspired tools. Compare two versions of a task.]

                Compare task versions across commits or timestamps to see what changed.

                📊 Output: JSON with field-by-field differences
                """
                return compare_task_diff(task_id, commit1, commit2, time1, time2)

            @ensure_json_string
            @mcp.tool()
            def generate_graph_tool(
                branch: Optional[str] = None,
                task_id: Optional[str] = None,
                format: str = "text",
                output_path: Optional[str] = None,
                max_commits: int = 50,
            ) -> str:
                """
                [HINT: Git-inspired tools. Generate commit graph visualization.]

                Generate visual timeline of commits (text ASCII or Graphviz DOT format).

                📊 Output: Graph visualization in text or DOT format
                """
                return generate_graph(branch, task_id, format, output_path, max_commits)

            @ensure_json_string
            @mcp.tool()
            def merge_branch_tools_tool(
                source_branch: str,
                target_branch: str,
                conflict_strategy: str = "newer",
                author: str = "system",
                dry_run: bool = False,
            ) -> str:
                """
                [HINT: Git-inspired tools. Merge tasks from one branch to another.]

                Merge tasks from source branch to target branch with conflict detection.

                📊 Output: JSON with merge results, conflicts, and resolution
                🔧 Side Effects: Modifies tasks if dry_run=False
                """
                return merge_branch_tools(source_branch, target_branch, conflict_strategy, author, dry_run)

            @ensure_json_string
            @mcp.tool()
            def set_task_branch(task_id: str, branch: str) -> str:
                """
                [HINT: Git-inspired tools. Set branch for a task.]

                Assign a task to a branch (work stream) by adding branch: tag.

                📊 Output: JSON with result (old_branch, new_branch, success)
                🔧 Side Effects: Modifies task tags
                """
                return set_task_branch_tool(task_id, branch)

            logger.info("Git-inspired tools registered successfully")

    # ═══════════════════════════════════════════════════════════════════════════════
    # AI SESSION MEMORY TOOLS
    # ═══════════════════════════════════════════════════════════════════════════════

    try:
        from .tools.session_memory import (
            generate_session_summary,
            get_memories_for_sprint,
            link_memory_to_task,
            recall_task_context,
            save_session_insight,
            search_session_memories,
        )

        MEMORY_TOOLS_AVAILABLE = True
    except ImportError:
        MEMORY_TOOLS_AVAILABLE = False
        logger.warning("Memory tools not available")

    if MEMORY_TOOLS_AVAILABLE:
        # NOTE: save_memory, recall_context, search_memories removed - use memory(action=save|recall|search)
        # NOTE: get_session_summary removed - use memory(action=search) with date filter
        # NOTE: get_sprint_memories removed - use memory(action=search) with category filter
        logger.info("Memory tools loaded successfully")

    # Register prompts - support both FastMCP and stdio Server
    PROMPTS_AVAILABLE = False  # Initialize before try block
    try:
        # Try relative imports first (when run as module)
        try:
            from .prompts import (
                ADVISOR_BRIEFING,
                # Wisdom
                ADVISOR_CONSULT,
                # Automation
                AUTOMATION_DISCOVERY,
                AUTOMATION_HIGH_VALUE,
                AUTOMATION_SETUP,
                CONFIG_GENERATION,
                # Context Management
                CONTEXT_MANAGEMENT,
                DAILY_CHECKIN,
                # Session Handoff
                END_OF_DAY,
                RESUME_SESSION,
                VIEW_HANDOFFS,
                # Documentation
                DOCUMENTATION_HEALTH_CHECK,
                DOCUMENTATION_QUICK_CHECK,
                DUPLICATE_TASK_CLEANUP,
                # Memory
                MEMORY_SYSTEM,
                # Mode Suggestion
                MODE_SUGGESTION,
                PERSONA_ARCHITECT,
                PERSONA_CODE_REVIEWER,
                # Personas
                PERSONA_DEVELOPER,
                PERSONA_EXECUTIVE,
                PERSONA_PROJECT_MANAGER,
                PERSONA_QA_ENGINEER,
                PERSONA_SECURITY_ENGINEER,
                PERSONA_TECH_WRITER,
                POST_IMPLEMENTATION_REVIEW,
                # Workflows
                PRE_SPRINT_CLEANUP,
                PROJECT_HEALTH,
                # Reports
                PROJECT_OVERVIEW,
                PROJECT_SCORECARD,
                # Security
                SECURITY_SCAN_ALL,
                SECURITY_SCAN_PYTHON,
                SECURITY_SCAN_RUST,
                SPRINT_END,
                SPRINT_START,
                # Tasks
                TASK_ALIGNMENT_ANALYSIS,
                TASK_DISCOVERY,
                TASK_REVIEW,
                TASK_SYNC,
                WEEKLY_MAINTENANCE,
            )
        except ImportError:
            # Fallback to absolute imports (when run as script)
            from prompts import (
                ADVISOR_BRIEFING,
                # Wisdom
                ADVISOR_CONSULT,
                # Automation
                AUTOMATION_DISCOVERY,
                AUTOMATION_HIGH_VALUE,
                AUTOMATION_SETUP,
                CONFIG_GENERATION,
                # Context Management
                CONTEXT_MANAGEMENT,
                DAILY_CHECKIN,
                # Session Handoff
                END_OF_DAY,
                RESUME_SESSION,
                VIEW_HANDOFFS,
                # Documentation
                DOCUMENTATION_HEALTH_CHECK,
                DOCUMENTATION_QUICK_CHECK,
                DUPLICATE_TASK_CLEANUP,
                # Memory
                MEMORY_SYSTEM,
                # Mode Suggestion
                MODE_SUGGESTION,
                PERSONA_ARCHITECT,
                PERSONA_CODE_REVIEWER,
                # Personas
                PERSONA_DEVELOPER,
                PERSONA_EXECUTIVE,
                PERSONA_PROJECT_MANAGER,
                PERSONA_QA_ENGINEER,
                PERSONA_SECURITY_ENGINEER,
                PERSONA_TECH_WRITER,
                POST_IMPLEMENTATION_REVIEW,
                # Workflows
                PRE_SPRINT_CLEANUP,
                PROJECT_HEALTH,
                # Reports
                PROJECT_OVERVIEW,
                PROJECT_SCORECARD,
                # Security
                SECURITY_SCAN_ALL,
                SECURITY_SCAN_PYTHON,
                SECURITY_SCAN_RUST,
                SPRINT_END,
                SPRINT_START,
                # Tasks
                TASK_ALIGNMENT_ANALYSIS,
                TASK_DISCOVERY,
                TASK_REVIEW,
                TASK_SYNC,
                WEEKLY_MAINTENANCE,
            )

        # Register prompts for FastMCP
        if mcp:
            @mcp.prompt()
            def doc_check() -> str:
                """Analyze documentation health and create tasks for issues."""
                return DOCUMENTATION_HEALTH_CHECK

            @mcp.prompt()
            def doc_quick() -> str:
                """Quick documentation health check without creating tasks."""
                return DOCUMENTATION_QUICK_CHECK

            @mcp.prompt()
            def align() -> str:
                """Analyze Todo2 task alignment with project goals."""
                return TASK_ALIGNMENT_ANALYSIS

            @mcp.prompt()
            def dups() -> str:
                """Find and consolidate duplicate Todo2 tasks."""
                return DUPLICATE_TASK_CLEANUP

            @mcp.prompt()
            def sync() -> str:
                """Synchronize tasks between shared TODO table and Todo2."""
                return TASK_SYNC

            @mcp.prompt()
            def scan() -> str:
                """Scan all project dependencies for security vulnerabilities."""
                return SECURITY_SCAN_ALL

            @mcp.prompt()
            def scan_py() -> str:
                """Scan Python dependencies for security vulnerabilities."""
                return SECURITY_SCAN_PYTHON

            @mcp.prompt()
            def scan_rs() -> str:
                """Scan Rust dependencies for security vulnerabilities."""
                return SECURITY_SCAN_RUST

            @mcp.prompt()
            def auto() -> str:
                """Discover new automation opportunities in the codebase."""
                return AUTOMATION_DISCOVERY

            @mcp.prompt()
            def auto_high() -> str:
                """Find only high-value automation opportunities."""
                return AUTOMATION_HIGH_VALUE

            @mcp.prompt()
            def pre_sprint() -> str:
                """Pre-sprint cleanup workflow: duplicates, alignment, documentation."""
                return PRE_SPRINT_CLEANUP

            @mcp.prompt()
            def post_impl() -> str:
                """Post-implementation review workflow: docs, security, automation."""
                return POST_IMPLEMENTATION_REVIEW

            @mcp.prompt()
            def weekly() -> str:
                """Weekly maintenance workflow: docs, duplicates, security, sync."""
                return WEEKLY_MAINTENANCE

            # New workflow prompts
            @mcp.prompt()
            def daily_checkin() -> str:
                """Daily check-in workflow: server status, blockers, git health."""
                return DAILY_CHECKIN

            @mcp.prompt()
            def sprint_start() -> str:
                """Sprint start workflow: clean backlog, align tasks, queue work."""
                return SPRINT_START

            @mcp.prompt()
            def sprint_end() -> str:
                """Sprint end workflow: test coverage, docs, security check."""
                return SPRINT_END

            @mcp.prompt()
            def task_review() -> str:
                """Comprehensive task review: duplicates, alignment, staleness."""
                return TASK_REVIEW

            @mcp.prompt()
            def project_health() -> str:
                """Full project health assessment: code, docs, security, CI/CD."""
                return PROJECT_HEALTH

            @mcp.prompt()
            def automation_setup() -> str:
                """One-time automation setup: git hooks, triggers, cron."""
                return AUTOMATION_SETUP

            @mcp.prompt()
            def scorecard() -> str:
                """Generate comprehensive project health scorecard with all metrics."""
                return PROJECT_SCORECARD

            @mcp.prompt()
            def overview() -> str:
                """Generate one-page project overview for stakeholders."""
                return PROJECT_OVERVIEW

            # ═══════════════════════════════════════════════════════════════════════
            # ADDITIONAL PROMPTS
            # ═══════════════════════════════════════════════════════════════════════

            @mcp.prompt()
            def discover() -> str:
                """Discover tasks from TODO comments, markdown, and orphaned tasks."""
                return TASK_DISCOVERY

            @mcp.prompt()
            def config() -> str:
                """Generate IDE configuration files."""
                return CONFIG_GENERATION

            @mcp.prompt()
            def mode() -> str:
                """Suggest optimal Cursor IDE mode (Agent vs Ask) for a task."""
                return MODE_SUGGESTION

            @mcp.prompt()
            def context() -> str:
                """Manage LLM context with summarization and budget tools."""
                return CONTEXT_MANAGEMENT

            @mcp.prompt()
            def remember() -> str:
                """Use AI session memory to persist insights."""
                return MEMORY_SYSTEM

            # ═══════════════════════════════════════════════════════════════════════
            # SESSION HANDOFF PROMPTS
            # ═══════════════════════════════════════════════════════════════════════

            @mcp.prompt()
            def end_of_day() -> str:
                """End your work session and create a handoff for other developers."""
                return END_OF_DAY

            @mcp.prompt()
            def resume_session() -> str:
                """Resume work by reviewing the latest handoff from another developer."""
                return RESUME_SESSION

            @mcp.prompt()
            def view_handoffs() -> str:
                """View recent handoff notes from all developers."""
                return VIEW_HANDOFFS

            # ═══════════════════════════════════════════════════════════════════════
            # PERSONA WORKFLOW PROMPTS
            # ═══════════════════════════════════════════════════════════════════════

            @mcp.prompt()
            def dev() -> str:
                """Developer daily workflow for writing quality code."""
                return PERSONA_DEVELOPER

            @mcp.prompt()
            def pm() -> str:
                """Project Manager workflow for delivery tracking."""
                return PERSONA_PROJECT_MANAGER

            @mcp.prompt()
            def reviewer() -> str:
                """Code Reviewer workflow for quality gates."""
                return PERSONA_CODE_REVIEWER

            @mcp.prompt()
            def exec() -> str:
                """Executive/Stakeholder workflow for strategic view."""
                return PERSONA_EXECUTIVE

            @mcp.prompt()
            def seceng() -> str:
                """Security Engineer workflow for risk management."""
                return PERSONA_SECURITY_ENGINEER

            @mcp.prompt()
            def arch() -> str:
                """Architect workflow for system design."""
                return PERSONA_ARCHITECT

            @mcp.prompt()
            def qa() -> str:
                """QA Engineer workflow for quality assurance."""
                return PERSONA_QA_ENGINEER

            @mcp.prompt()
            def writer() -> str:
                """Technical Writer workflow for documentation."""
                return PERSONA_TECH_WRITER

            PROMPTS_AVAILABLE = True
            logger.info("Registered 41 prompts successfully (FastMCP)")
        else:
            PROMPTS_AVAILABLE = True
            logger.info("Prompts imported (will register for stdio server below)")
    except ImportError as e:
        PROMPTS_AVAILABLE = False
        logger.warning(f"Prompts not available: {e}")

    # Register prompts for stdio server
    import sys
    print(f"DEBUG PROMPT REG: stdio_server_instance={stdio_server_instance is not None}, PROMPTS_AVAILABLE={PROMPTS_AVAILABLE}", file=sys.stderr)
    logger.info(f"DEBUG: Checking prompt registration conditions - stdio_server_instance={stdio_server_instance is not None}, PROMPTS_AVAILABLE={PROMPTS_AVAILABLE}")
    if stdio_server_instance and PROMPTS_AVAILABLE:
        print("DEBUG PROMPT REG: Entering prompt registration block", file=sys.stderr)
        logger.info(f"Attempting to register prompts for stdio server (stdio_server_instance={stdio_server_instance is not None}, PROMPTS_AVAILABLE={PROMPTS_AVAILABLE})")
        logger.info(f"DEBUG: stdio_server_instance type: {type(stdio_server_instance)}")
        logger.info(f"DEBUG: hasattr list_prompts: {hasattr(stdio_server_instance, 'list_prompts')}")
        logger.info(f"DEBUG: hasattr get_prompt: {hasattr(stdio_server_instance, 'get_prompt')}")
        try:
            from mcp.types import Prompt, PromptArgument
            logger.info("DEBUG: Successfully imported Prompt types")
            
            logger.info("DEBUG: About to apply @stdio_server_instance.list_prompts() decorator")
            @stdio_server_instance.list_prompts()
            async def list_prompts() -> list[Prompt]:
                """List all available prompts."""
                return [
                    Prompt(name="doc_check", description="Analyze documentation health and create tasks for issues.", arguments=[]),
                    Prompt(name="doc_quick", description="Quick documentation health check without creating tasks.", arguments=[]),
                    Prompt(name="align", description="Analyze Todo2 task alignment with project goals.", arguments=[]),
                    Prompt(name="dups", description="Find and consolidate duplicate Todo2 tasks.", arguments=[]),
                    Prompt(name="sync", description="Synchronize tasks between shared TODO table and Todo2.", arguments=[]),
                    Prompt(name="scan", description="Scan all project dependencies for security vulnerabilities.", arguments=[]),
                    Prompt(name="scan_py", description="Scan Python dependencies for security vulnerabilities.", arguments=[]),
                    Prompt(name="scan_rs", description="Scan Rust dependencies for security vulnerabilities.", arguments=[]),
                    Prompt(name="auto", description="Discover new automation opportunities in the codebase.", arguments=[]),
                    Prompt(name="auto_high", description="Find only high-value automation opportunities.", arguments=[]),
                    Prompt(name="pre_sprint", description="Pre-sprint cleanup workflow: duplicates, alignment, documentation.", arguments=[]),
                    Prompt(name="post_impl", description="Post-implementation review workflow: docs, security, automation.", arguments=[]),
                    Prompt(name="weekly", description="Weekly maintenance workflow: docs, duplicates, security, sync.", arguments=[]),
                    Prompt(name="daily_checkin", description="Daily check-in workflow: server status, blockers, git health.", arguments=[]),
                    Prompt(name="sprint_start", description="Sprint start workflow: clean backlog, align tasks, queue work.", arguments=[]),
                    Prompt(name="sprint_end", description="Sprint end workflow: test coverage, docs, security check.", arguments=[]),
                    Prompt(name="task_review", description="Comprehensive task review: duplicates, alignment, staleness.", arguments=[]),
                    Prompt(name="project_health", description="Full project health assessment: code, docs, security, CI/CD.", arguments=[]),
                    Prompt(name="automation_setup", description="One-time automation setup: git hooks, triggers, cron.", arguments=[]),
                    Prompt(name="scorecard", description="Generate comprehensive project health scorecard with all metrics.", arguments=[]),
                    Prompt(name="overview", description="Generate one-page project overview for stakeholders.", arguments=[]),
                    Prompt(name="discover", description="Discover tasks from TODO comments, markdown, and orphaned tasks.", arguments=[]),
                    Prompt(name="config", description="Generate IDE configuration files.", arguments=[]),
                    Prompt(name="mode", description="Suggest optimal Cursor IDE mode (Agent vs Ask) for a task.", arguments=[]),
                    Prompt(name="context", description="Manage LLM context with summarization and budget tools.", arguments=[]),
                    Prompt(name="remember", description="Use AI session memory to persist insights.", arguments=[]),
                    Prompt(name="end_of_day", description="End your work session and create a handoff for other developers.", arguments=[]),
                    Prompt(name="resume_session", description="Resume work by reviewing the latest handoff from another developer.", arguments=[]),
                    Prompt(name="view_handoffs", description="View recent handoff notes from all developers.", arguments=[]),
                    Prompt(name="dev", description="Developer daily workflow for writing quality code.", arguments=[]),
                    Prompt(name="pm", description="Project Manager workflow for delivery tracking.", arguments=[]),
                    Prompt(name="reviewer", description="Code Reviewer workflow for quality gates.", arguments=[]),
                    Prompt(name="exec", description="Executive/Stakeholder workflow for strategic view.", arguments=[]),
                    Prompt(name="seceng", description="Security Engineer workflow for risk management.", arguments=[]),
                    Prompt(name="arch", description="Architect workflow for system design.", arguments=[]),
                    Prompt(name="qa", description="QA Engineer workflow for quality assurance.", arguments=[]),
                    Prompt(name="writer", description="Technical Writer workflow for documentation.", arguments=[]),
                ]
            
            logger.info("DEBUG: list_prompts decorator applied, about to apply get_prompt decorator")
            @stdio_server_instance.get_prompt()
            async def get_prompt(name: str, arguments: dict[str, Any] | None = None) -> "GetPromptResult":
                """Get prompt template by name."""
                from mcp.types import GetPromptResult, PromptMessage, TextContent
                
                prompt_map = {
                    "doc_check": DOCUMENTATION_HEALTH_CHECK,
                    "doc_quick": DOCUMENTATION_QUICK_CHECK,
                    "align": TASK_ALIGNMENT_ANALYSIS,
                    "dups": DUPLICATE_TASK_CLEANUP,
                    "sync": TASK_SYNC,
                    "scan": SECURITY_SCAN_ALL,
                    "scan_py": SECURITY_SCAN_PYTHON,
                    "scan_rs": SECURITY_SCAN_RUST,
                    "auto": AUTOMATION_DISCOVERY,
                    "auto_high": AUTOMATION_HIGH_VALUE,
                    "pre_sprint": PRE_SPRINT_CLEANUP,
                    "post_impl": POST_IMPLEMENTATION_REVIEW,
                    "weekly": WEEKLY_MAINTENANCE,
                    "daily_checkin": DAILY_CHECKIN,
                    "sprint_start": SPRINT_START,
                    "sprint_end": SPRINT_END,
                    "task_review": TASK_REVIEW,
                    "project_health": PROJECT_HEALTH,
                    "automation_setup": AUTOMATION_SETUP,
                    "scorecard": PROJECT_SCORECARD,
                    "overview": PROJECT_OVERVIEW,
                    "discover": TASK_DISCOVERY,
                    "config": CONFIG_GENERATION,
                    "mode": MODE_SUGGESTION,
                    "context": CONTEXT_MANAGEMENT,
                    "remember": MEMORY_SYSTEM,
                    "end_of_day": END_OF_DAY,
                    "resume_session": RESUME_SESSION,
                    "view_handoffs": VIEW_HANDOFFS,
                    "dev": PERSONA_DEVELOPER,
                    "pm": PERSONA_PROJECT_MANAGER,
                    "reviewer": PERSONA_CODE_REVIEWER,
                    "exec": PERSONA_EXECUTIVE,
                    "seceng": PERSONA_SECURITY_ENGINEER,
                    "arch": PERSONA_ARCHITECT,
                    "qa": PERSONA_QA_ENGINEER,
                    "writer": PERSONA_TECH_WRITER,
                }
                if name in prompt_map:
                    # Return GetPromptResult with the prompt content
                    return GetPromptResult(
                        description=f"Prompt: {name}",
                        messages=[
                            PromptMessage(
                                role="user",
                                content=TextContent(
                                    type="text",
                                    text=prompt_map[name]
                                )
                            )
                        ]
                    )
                else:
                    raise ValueError(f"Unknown prompt: {name}")
            
            logger.info("DEBUG: Both prompt decorators applied successfully")
            print("DEBUG PROMPT REG: Both decorators applied, registration complete", file=sys.stderr)
            logger.info("Registered 41 prompts for stdio server successfully")
        except Exception as e:
            print(f"DEBUG PROMPT REG ERROR: {e}", file=sys.stderr)
            import traceback
            print(f"DEBUG PROMPT REG TRACEBACK:\n{traceback.format_exc()}", file=sys.stderr)
            logger.error(f"Failed to register prompts for stdio server: {e}", exc_info=True)
            logger.debug(f"Full traceback for prompt registration:\n{traceback.format_exc()}")
    else:
        print(f"DEBUG PROMPT REG SKIPPED: stdio_server_instance={stdio_server_instance is not None}, PROMPTS_AVAILABLE={PROMPTS_AVAILABLE}", file=sys.stderr)
        logger.warning(f"Prompt registration skipped: stdio_server_instance={stdio_server_instance is not None}, PROMPTS_AVAILABLE={PROMPTS_AVAILABLE}")

    # Resource handlers (Phase 3)
    try:
        # Try relative imports first (when run as module)
        try:
            from .resources.cache import get_cache_status_resource
            from .resources.catalog import (
                get_linters_resource,
                get_models_resource,
                get_problem_categories_resource,
                get_tts_backends_resource,
            )
            from .resources.history import get_history_resource
            from .resources.list import get_tools_list_resource
            from .resources.memories import (
                get_memories_by_category_resource,
                get_memories_by_task_resource,
                get_memories_health_resource,
                get_memories_resource,
                get_recent_memories_resource,
                get_session_memories_resource,
                get_wisdom_resource,
            )
            from .resources.status import get_status_resource
            from .resources.tasks import get_agent_tasks_resource, get_agents_resource, get_tasks_resource

            MEMORIES_AVAILABLE = True
        except ImportError:
            # Fallback to absolute imports (when run as script)
            from resources.cache import get_cache_status_resource
            from resources.catalog import (
                get_linters_resource,
                get_models_resource,
                get_problem_categories_resource,
                get_tts_backends_resource,
            )
            from resources.history import get_history_resource
            from resources.list import get_tools_list_resource
            from resources.status import get_status_resource
            from resources.tasks import get_agent_tasks_resource, get_agents_resource, get_tasks_resource

            try:
                from resources.memories import (
                    get_memories_by_category_resource,
                    get_memories_by_task_resource,
                    get_memories_health_resource,
                    get_memories_resource,
                    get_recent_memories_resource,
                    get_session_memories_resource,
                )

                MEMORIES_AVAILABLE = True
            except ImportError:
                MEMORIES_AVAILABLE = False

        @mcp.resource("automation://status")
        def get_automation_status() -> str:
            """Get automation server status and health information."""
            return get_status_resource()

        @mcp.resource("automation://history")
        def get_automation_history() -> str:
            """Get automation tool execution history."""
            return get_history_resource(limit=50)

        @mcp.resource("automation://tools")
        def get_automation_tools() -> str:
            """Get list of available automation tools with descriptions."""
            return get_tools_list_resource()

        @mcp.resource("automation://tasks")
        def get_automation_tasks() -> str:
            """Get Todo2 tasks list."""
            return get_tasks_resource()

        @mcp.resource("automation://tasks/agent/{agent_name}")
        def get_automation_tasks_by_agent(agent_name: str) -> str:
            """Get Todo2 tasks for a specific agent."""
            return get_agent_tasks_resource(agent_name)

        @mcp.resource("automation://tasks/status/{status}")
        def get_automation_tasks_by_status(status: str) -> str:
            """Get Todo2 tasks filtered by status."""
            return get_tasks_resource(status=status)

        @mcp.resource("automation://agents")
        def get_automation_agents() -> str:
            """Get list of available agents with configurations and task counts."""
            return get_agents_resource()

        @mcp.resource("automation://cache")
        def get_automation_cache() -> str:
            """Get cache status - what data is cached and when it was last updated."""
            return get_cache_status_resource()

        # ═══════════════════════════════════════════════════════════════════════════════
        # CATALOG RESOURCES (converted from list_* tools)
        # ═══════════════════════════════════════════════════════════════════════════════

        @mcp.resource("automation://models")
        def get_models_catalog() -> str:
            """Get available AI models with recommendations for task types."""
            return get_models_resource()

        @mcp.resource("automation://problem-categories")
        def get_problem_categories_catalog() -> str:
            """Get problem categories with resolution hints."""
            return get_problem_categories_resource()

        @mcp.resource("automation://linters")
        def get_linters_catalog() -> str:
            """Get available linters and their installation status."""
            return get_linters_resource()

        @mcp.resource("automation://tts-backends")
        def get_tts_backends_catalog() -> str:
            """Get available text-to-speech backends."""
            return get_tts_backends_resource()

        @mcp.resource("automation://scorecard")
        def get_project_scorecard() -> str:
            """Get current project scorecard with all health metrics."""
            result = _generate_project_scorecard("json", True, None)
            # Ensure we always return a JSON string
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                return json.dumps(result, separators=(",", ":"))
            else:
                return json.dumps({"result": str(result)}, separators=(",", ":"))

        # Memory resources (AI Session Memory System)
        if MEMORIES_AVAILABLE:

            @mcp.resource("automation://memories")
            def get_all_memories() -> str:
                """Get all AI session memories - browsable context for session continuity."""
                return get_memories_resource()

            @mcp.resource("automation://memories/category/{category}")
            def get_memories_by_category(category: str) -> str:
                """Get memories filtered by category (debug, research, architecture, preference, insight)."""
                return get_memories_by_category_resource(category)

            @mcp.resource("automation://memories/task/{task_id}")
            def get_memories_for_task(task_id: str) -> str:
                """Get memories linked to a specific task."""
                return get_memories_by_task_resource(task_id)

            @mcp.resource("automation://memories/recent")
            def get_recent_memories() -> str:
                """Get memories from the last 24 hours."""
                return get_recent_memories_resource()

            @mcp.resource("automation://memories/session/{date}")
            def get_session_memories(date: str) -> str:
                """Get memories from a specific session date (YYYY-MM-DD format)."""
                return get_session_memories_resource(date)
            #     return get_wisdom_resource()

            @mcp.resource("automation://memories/health")
            def get_memory_health() -> str:
                """Get memory system health metrics and maintenance recommendations."""
                return get_memories_health_resource()

            logger.info("Memory resources loaded successfully")

        RESOURCES_AVAILABLE = True
        logger.info("Resource handlers loaded successfully")
    except ImportError as e:
        RESOURCES_AVAILABLE = False
        logger.warning(f"Resource handlers not available: {e}")

        # Fallback resource handler (only if resources failed to load)
        # Note: This is a minimal fallback - full status available via server_status tool
        @mcp.resource("automation://status")
        def get_automation_status_fallback() -> str:
            """Get automation server status (fallback when resource handlers unavailable)."""
            return json.dumps(
                {
                    "status": "operational",
                    "tools_available": TOOLS_AVAILABLE,
                    "note": "Using fallback status - resource handlers unavailable",
                }
            )

    # Main entry point for FastMCP


def _is_mcp_mode() -> bool:
    """Detect if running in MCP mode (stdin is not a TTY or MCP env vars set)."""
    import sys

    # Check for explicit MCP mode
    if os.environ.get("EXARP_MCP_MODE") == "1":
        return True
    # Check for Cursor/AI environment
    if os.environ.get("CURSOR_TRACE_ID"):
        return True
    # Check if stdin is not a TTY (piped input = likely MCP)
    if not sys.stdin.isatty():
        return True
    return False


def _print_shell_setup(shell: str = "zsh") -> None:
    """Print shell configuration that can be eval'd or sourced."""
    setup = f"""# Exarp Shell Setup (generated by: exarp --shell-setup)
# Add to your ~/.{shell}rc or eval: eval "$(exarp --shell-setup)"

# ═══════════════════════════════════════════════════════════════
# EXARP CONFIGURATION
# ═══════════════════════════════════════════════════════════════

export EXARP_CACHE_DIR="${{EXARP_CACHE_DIR:-${{XDG_CACHE_HOME:-$HOME/.cache}}/exarp}}"
mkdir -p "$EXARP_CACHE_DIR" 2>/dev/null

# Optional features (uncomment to enable)
# export EXARP_PROMPT=1              # Show score in prompt
# export EXARP_MOTD=lite             # MOTD on shell start (lite|context|score|wisdom)
# export EXARP_WISDOM_SOURCE=random  # Wisdom source

# ═══════════════════════════════════════════════════════════════
# ALIASES
# ═══════════════════════════════════════════════════════════════

alias exarp="uvx exarp"
alias pma="uvx exarp"

# ═══════════════════════════════════════════════════════════════
# FULL TOOLS WITH CACHING AND FALLBACK
# ═══════════════════════════════════════════════════════════════

# Helper: Get project-specific cache dir
_exarp_project_cache() {{
    local proj_hash=$(pwd | shasum | cut -c1-8)
    echo "$EXARP_CACHE_DIR/projects/$proj_hash"
}}

# NOTE: xs() is defined below in CAPTURED OUTPUT section with score caching

# Overview with caching and offline fallback
xo() {{
    local cache_dir=$(_exarp_project_cache)
    local cache_file="$cache_dir/overview.txt"
    mkdir -p "$cache_dir" 2>/dev/null

    local result
    result=$(uvx --from exarp python3 -c "
from project_management_automation.tools.project_overview import generate_project_overview
r = generate_project_overview()
print(r.get('formatted_output', ''))
" 2>/dev/null)

    if [[ -n "$result" ]]; then
        echo "$result"
        echo "$result" > "$cache_file"
        date +%s > "$cache_file.ts"
    elif [[ -f "$cache_file" ]]; then
        local age=999999
        [[ -f "$cache_file.ts" ]] && age=$(($(date +%s) - $(cat "$cache_file.ts")))
        echo "⚠️  Using cached overview (uvx unavailable, cached $((age/60))m ago)"
        echo ""
        cat "$cache_file"
    else
        echo "❌ Overview unavailable (no uvx, no cache)"
        echo "   Try: xl (lite context) or check network"
    fi
}}

# Wisdom with caching and offline fallback
xw() {{
    local cache_dir="$EXARP_CACHE_DIR/wisdom"
    local today=$(date +%Y%m%d)
    local cache_file="$cache_dir/$today.txt"
    mkdir -p "$cache_dir" 2>/dev/null

    local result
    result=$(uvx --from exarp python3 -c "
from project_management_automation.utils.wisdom_client import get_wisdom, format_text
print(format_text(get_wisdom(50)))
" 2>/dev/null)

    if [[ -n "$result" ]]; then
        echo "$result"
        echo "$result" > "$cache_file"
    elif [[ -f "$cache_file" ]]; then
        echo "⚠️  Using cached wisdom (uvx unavailable)"
        echo ""
        cat "$cache_file"
    else
        # Try yesterday
        local yesterday=$(date -v-1d +%Y%m%d 2>/dev/null || date -d "yesterday" +%Y%m%d 2>/dev/null)
        if [[ -f "$cache_dir/$yesterday.txt" ]]; then
            echo "⚠️  Using yesterday wisdom (uvx unavailable)"
            echo ""
            cat "$cache_dir/$yesterday.txt"
        else
            echo "❌ Wisdom unavailable (no uvx, no cache)"
            echo "   Offline wisdom: The obstacle is the way. - Marcus Aurelius"
        fi
    fi
}}

# Clear cache
exarp_clear_cache() {{
    rm -rf "$EXARP_CACHE_DIR/projects" "$EXARP_CACHE_DIR/wisdom"
    mkdir -p "$EXARP_CACHE_DIR"
    echo "✅ Exarp cache cleared"
}}

# ═══════════════════════════════════════════════════════════════
# SHELL-ONLY FUNCTIONS (instant, no Python startup)
# ═══════════════════════════════════════════════════════════════

# Fast project detection
_exarp_detect() {{
    local dir="${{1:-.}}"
    [[ -d "$dir/.todo2" ]] || [[ -d "$dir/.git" ]] || \\
    [[ -f "$dir/pyproject.toml" ]] || [[ -f "$dir/package.json" ]] || \\
    [[ -f "$dir/Cargo.toml" ]] || [[ -f "$dir/go.mod" ]]
}}

# Fast project name
_exarp_name() {{
    local dir="${{1:-.}}"
    if [[ -f "$dir/pyproject.toml" ]]; then
        grep -m1 'name.*=' "$dir/pyproject.toml" 2>/dev/null | sed 's/.*"\\([^"]*\\)".*/\\1/' | head -1
    elif [[ -f "$dir/package.json" ]]; then
        grep -m1 '"name"' "$dir/package.json" 2>/dev/null | sed 's/.*": *"\\([^"]*\\)".*/\\1/'
    else
        basename "$(cd "$dir" 2>/dev/null && pwd || echo "$dir")"
    fi
}}

# Fast task count
_exarp_tasks() {{
    local todo_file="${{1:-.}}/.todo2/state.todo2.json"
    if [[ ! -f "$todo_file" ]]; then echo "0/0"; return; fi
    local total=$(grep -c '"id"' "$todo_file" 2>/dev/null || echo 0)
    local done=$(grep -c '"status".*[Dd]one' "$todo_file" 2>/dev/null || echo 0)
    echo "$((total - done))/$total"
}}

# Lite context (instant)
xl() {{
    local dir="${{1:-.}}"
    if ! _exarp_detect "$dir"; then echo "📁 Not a project"; return 1; fi
    local name=$(_exarp_name "$dir")
    local tasks=$(_exarp_tasks "$dir")
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  ⚡ EXARP LITE                                      │"
    echo "├─────────────────────────────────────────────────────┤"
    printf "│  Project: %-40s│\\n" "${{name:0:40}}"
    printf "│  Tasks:   %-40s│\\n" "$tasks (pending/total)"
    echo "└─────────────────────────────────────────────────────┘"
}}

# Lite task list
xt() {{
    local todo_file="${{1:-.}}/.todo2/state.todo2.json"
    local limit="${{2:-10}}"
    if [[ ! -f "$todo_file" ]]; then echo "No .todo2 found"; return 1; fi
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    printf "│  📋 PENDING TASKS (top %-2s)                        │\\n" "$limit"
    echo "├─────────────────────────────────────────────────────┤"
    python3 -c "
import json
with open('$todo_file') as f:
    data = json.load(f)
count = 0
for t in data.get('todos', []):
    if t.get('status', '').lower() in ['pending', 'in_progress', 'todo', 'in progress']:
        # Support both 'content' (exarp) and 'name' (todo2) formats
        task_text = t.get('content') or t.get('name') or t.get('title') or ''
        print('│  • ' + task_text[:47].ljust(47) + '│')
        count += 1
        if count >= $limit: break
if count == 0: print('│  ✅ No pending tasks!                             │')
" 2>/dev/null
    echo "└─────────────────────────────────────────────────────┘"
}}

# Lite projects scan
xpl() {{
    local dir="${{1:-.}}"
    echo ""
    echo "┌─────────────────────────────────────────────────────┐"
    echo "│  🗂️  PROJECTS                                       │"
    echo "├─────────────────────────────────────────────────────┤"
    local count=0
    for subdir in "$dir"/*/; do
        if _exarp_detect "$subdir"; then
            local name=$(_exarp_name "$subdir")
            local tasks=$(_exarp_tasks "$subdir")
            printf "│  %-30s %-17s│\\n" "${{name:0:30}}" "$tasks"
            count=$((count + 1))
        fi
    done
    [[ $count -eq 0 ]] && echo "│  No projects found                                │"
    echo "└─────────────────────────────────────────────────────┘"
    echo "  Found $count project(s)"
}}

# Full context (with cached score)
xc() {{
    if ! _exarp_detect "."; then echo "📁 Not a project"; return 1; fi
    xl
    echo "  Full: xs (score) | xo (overview) | xw (wisdom)"
}}

# ═══════════════════════════════════════════════════════════════
# PROMPT INTEGRATION
# ═══════════════════════════════════════════════════════════════

# Get cached score (fast, no Python)
_exarp_cached_score() {{
    local cache_file="$(_exarp_project_cache)/score.txt"
    [[ -f "$cache_file" ]] && cat "$cache_file" || echo ""
}}

# Update cached score (called after xs)
_exarp_update_score() {{
    local score="$1"
    local cache_file="$(_exarp_project_cache)/score.txt"
    mkdir -p "$(dirname "$cache_file")" 2>/dev/null
    echo "$score" > "$cache_file"
}}

# Prompt info with tasks and optional score
exarp_prompt_info() {{
    [[ "${{EXARP_PROMPT:-0}}" == "0" ]] && return
    _exarp_detect "." || return

    local tasks=$(_exarp_tasks ".")
    local pending=${{tasks%%/*}}
    local output=""

    # Task count badge
    if (( pending > 0 )); then
        if (( pending > 10 )); then
            output="%F{{red}}◇$pending%f"
        elif (( pending > 5 )); then
            output="%F{{yellow}}◇$pending%f"
        else
            output="%F{{blue}}◇$pending%f"
        fi
    fi

    # Score badge (if cached)
    local score=$(_exarp_cached_score)
    if [[ -n "$score" ]]; then
        if (( score >= 80 )); then
            output="$output %F{{green}}●$score%%%f"
        elif (( score >= 60 )); then
            output="$output %F{{yellow}}●$score%%%f"
        else
            output="$output %F{{red}}●$score%%%f"
        fi
    fi

    echo "$output"
}}

# Add to your prompt: RPROMPT='$(exarp_prompt_info) '$RPROMPT

# ═══════════════════════════════════════════════════════════════
# iTERM2 INTEGRATION
# ═══════════════════════════════════════════════════════════════

# Set iTerm2 badge (project name + score)
exarp_iterm_badge() {{
    [[ "$TERM_PROGRAM" != "iTerm.app" ]] && return
    _exarp_detect "." || return

    local name=$(_exarp_name ".")
    local tasks=$(_exarp_tasks ".")
    local score=$(_exarp_cached_score)

    local badge="$name"
    [[ -n "$tasks" ]] && badge="$badge ◇${{tasks%%/*}}"
    [[ -n "$score" ]] && badge="$badge ●$score%"

    # iTerm2 badge escape sequence
    printf "\\033]1337;SetBadgeFormat=%s\\007" "$(echo -n "$badge" | base64)"
}}

# Set iTerm2 tab title
exarp_iterm_title() {{
    [[ "$TERM_PROGRAM" != "iTerm.app" ]] && return
    _exarp_detect "." || return

    local name=$(_exarp_name ".")
    # Set tab title
    printf "\\033]0;%s\\007" "$name"
}}

# Set iTerm2 user vars (for status bar)
exarp_iterm_vars() {{
    [[ "$TERM_PROGRAM" != "iTerm.app" ]] && return
    _exarp_detect "." || return

    local name=$(_exarp_name ".")
    local tasks=$(_exarp_tasks ".")
    local score=$(_exarp_cached_score)

    # Set user variables for iTerm2 status bar
    printf "\\033]1337;SetUserVar=exarp_project=%s\\007" "$(echo -n "$name" | base64)"
    printf "\\033]1337;SetUserVar=exarp_tasks=%s\\007" "$(echo -n "$tasks" | base64)"
    [[ -n "$score" ]] && printf "\\033]1337;SetUserVar=exarp_score=%s\\007" "$(echo -n "$score" | base64)"
}}

# Update all iTerm2 integrations
exarp_iterm_update() {{
    exarp_iterm_badge
    exarp_iterm_title
    exarp_iterm_vars
}}

# Hook into cd to update iTerm2 on directory change
if [[ "$TERM_PROGRAM" == "iTerm.app" ]] && [[ "${{EXARP_ITERM:-1}}" != "0" ]]; then
    # Save original cd
    if ! type _exarp_original_cd &>/dev/null; then
        _exarp_original_cd() {{ builtin cd "$@"; }}
    fi

    cd() {{
        _exarp_original_cd "$@" && exarp_iterm_update
    }}

    # Initial update
    exarp_iterm_update
fi

# ═══════════════════════════════════════════════════════════════
# MOTD (Message of the Day)
# ═══════════════════════════════════════════════════════════════

# Enhanced MOTD with multiple modes
exarp_motd() {{
    local mode="${{EXARP_MOTD:-lite}}"

    case "$mode" in
        lite)
            # Quick summary
            echo ""
            echo "┌─────────────────────────────────────────────────────┐"
            echo "│  🌟 EXARP                                           │"
            echo "└─────────────────────────────────────────────────────┘"
            if _exarp_detect "."; then xl; else xpl; fi
            ;;
        context)
            # Project context with tasks
            echo ""
            if _exarp_detect "."; then
                xl
                echo ""
                xt | head -12
            else
                xpl
            fi
            ;;
        score)
            # Include scorecard (slower, needs uvx)
            echo ""
            if _exarp_detect "."; then
                xs 2>/dev/null | head -20
            else
                xpl
            fi
            ;;
        wisdom)
            # Wisdom only
            xw 2>/dev/null
            ;;
        full)
            # Everything
            echo ""
            if _exarp_detect "."; then
                xl
                echo ""
                xt | head -8
                echo ""
                xw 2>/dev/null | head -15
            else
                xpl
            fi
            ;;
        *)
            # Default to lite
            exarp_motd lite
            ;;
    esac
}}

# Auto-MOTD on shell start (if enabled)
if [[ "${{EXARP_MOTD:-0}}" != "0" ]]; then
    _motd_today=$(date +%Y%m%d)
    if [[ ! -f "$EXARP_CACHE_DIR/motd_${{_motd_today}}" ]]; then
        exarp_motd
        touch "$EXARP_CACHE_DIR/motd_${{_motd_today}}"
    fi
    unset _motd_today
fi

# ═══════════════════════════════════════════════════════════════
# CAPTURED OUTPUT / TRIGGERS
# ═══════════════════════════════════════════════════════════════

# Print trigger-friendly output (for iTerm2 triggers)
exarp_trigger_output() {{
    _exarp_detect "." || return
    local tasks=$(_exarp_tasks ".")
    local pending=${{tasks%%/*}}
    local total=${{tasks##*/}}
    local score=$(_exarp_cached_score)

    # Format: [EXARP] project:name tasks:N/M score:XX
    echo "[EXARP] project:$(_exarp_name .) tasks:$pending/$total score:${{score:-??}}"
}}

# Call after xs to update score cache and triggers
xs() {{
    local cache_dir=$(_exarp_project_cache)
    local cache_file="$cache_dir/scorecard.txt"
    mkdir -p "$cache_dir" 2>/dev/null

    # Try uvx first
    local result
    result=$(uvx --from exarp python3 -c "
from project_management_automation.tools.project_scorecard import generate_project_scorecard
r = generate_project_scorecard()
print(r.get('formatted_output', ''))
# Extract score for caching
import re
match = re.search(r'OVERALL SCORE: ([0-9.]+)%', r.get('formatted_output', ''))
if match:
    with open('$cache_dir/score.txt', 'w') as f:
        f.write(match.group(1).split('.')[0])
" 2>/dev/null)

    if [[ -n "$result" ]]; then
        echo "$result"
        echo "$result" > "$cache_file"
        date +%s > "$cache_file.ts"
        # Update iTerm2 after score update
        exarp_iterm_update 2>/dev/null
    elif [[ -f "$cache_file" ]]; then
        local age=999999
        [[ -f "$cache_file.ts" ]] && age=$(($(date +%s) - $(cat "$cache_file.ts")))
        echo "⚠️  Using cached scorecard (uvx unavailable, cached $((age/60))m ago)"
        echo ""
        cat "$cache_file"
    else
        echo "❌ Scorecard unavailable (no uvx, no cache)"
        echo "   Try: xl (lite context) or check network"
    fi
}}

echo "✅ Exarp loaded: xl | xt | xpl | xs/xo/xw | iTerm2: ${{TERM_PROGRAM:-n/a}}"
"""
    print(setup)


def _print_completions(shell: str = "zsh") -> None:
    """Print shell completions."""
    if shell == "zsh":
        completions = """# Exarp ZSH Completions (generated by: exarp --completions)
# Add to your ~/.zshrc or eval: eval "$(exarp --completions)"

_exarp_commands() {
    local commands=(
        "xl:Lite context (instant, shell-only)"
        "xt:Task list (instant)"
        "xpl:Projects scan (instant)"
        "xc:Full context"
        "xs:Full scorecard (via uvx)"
        "xo:Full overview (via uvx)"
        "xw:Daily wisdom (via uvx)"
    )
    _describe 'exarp commands' commands
}

_exarp() {
    local -a opts
    opts=(
        '--help[Show help]'
        '--version[Show version]'
        '--shell-setup[Print shell configuration]'
        '--completions[Print shell completions]'
        '--aliases[Print aliases only]'
        '--mcp[Run in MCP server mode]'
    )
    _arguments $opts
}

compdef _exarp exarp 2>/dev/null
compdef _exarp uvx\\ exarp 2>/dev/null
"""
    else:
        completions = f"# Completions for {shell} not yet implemented"
    print(completions)


def _print_aliases() -> None:
    """Print just the aliases (minimal setup without full functions)."""
    aliases = """# Exarp Aliases (generated by: exarp --aliases)
# eval "$(exarp --aliases)"
# Note: For caching/fallback support, use: eval "$(exarp --shell-setup)"

alias exarp="uvx exarp"
alias pma="uvx exarp"

# Simple aliases (no caching - for minimal setup)
alias xs="uvx --from exarp python3 -c 'from project_management_automation.tools.project_scorecard import generate_project_scorecard; r=generate_project_scorecard(); print(r.get(\"formatted_output\",\"\"))'"
alias xo="uvx --from exarp python3 -c 'from project_management_automation.tools.project_overview import generate_project_overview; r=generate_project_overview(); print(r.get(\"formatted_output\",\"\"))'"
alias xw="uvx --from exarp python3 -c 'from project_management_automation.utils.wisdom_client import get_wisdom, format_text; print(format_text(get_wisdom(50)))'"

# For full features with caching and offline fallback, use:
#   eval "$(exarp --shell-setup)"
"""
    print(aliases)


def _print_usage() -> None:
    """Print usage help for interactive mode."""
    version_str = __version__
    usage = f"""
╭──────────────────────────────────────────────────────────╮
│                                                          │
│    ███████╗██╗  ██╗ █████╗ ██████╗ ██████╗               │
│    ██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗              │
│    █████╗   ╚███╔╝ ███████║██████╔╝██████╔╝              │
│    ██╔══╝   ██╔██╗ ██╔══██║██╔══██╗██╔═══╝               │
│    ███████╗██╔╝ ██╗██║  ██║██║  ██║██║                   │
│    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝                   │
│                                                          │
│    Project Management Automation                         │
│    Version: {version_str:<44}│
│                                                          │
╰──────────────────────────────────────────────────────────╯

USAGE:
    exarp [OPTIONS]
    uvx exarp [OPTIONS]

OPTIONS:
    --help, -h          Show this help message
    --version, -v       Show version
    --shell-setup       Print shell configuration (eval "$(exarp --shell-setup)")
    --completions       Print shell completions
    --aliases           Print aliases only
    --mcp               Run in MCP server mode (for AI/Cursor)

SHELL SETUP (recommended):
    # Add to ~/.zshrc:
    eval "$(uvx exarp --shell-setup)"

    # Or download the full plugin:
    curl -sL https://raw.githubusercontent.com/davidl71/project-management-automation/main/shell/exarp-uvx.plugin.zsh -o ~/.exarp.zsh
    source ~/.exarp.zsh

QUICK COMMANDS (after shell setup):
    xl      Lite context (instant, shell-only)
    xt      Task list (instant)
    xpl     Projects scan (instant)
    xs      Full scorecard
    xo      Full overview
    xw      Daily wisdom

MCP MODE (for Cursor/AI):
    Cursor auto-detects MCP mode. Configure in .cursor/mcp.json:
    {{"mcpServers": {{"exarp": {{"command": "uvx", "args": ["exarp", "--mcp"]}}}}}}

DOCS:
    https://github.com/davidl71/project-management-automation
"""
    print(usage)


def _print_banner(file=None) -> None:
    """Print MCP server banner."""
    import sys

    file = file or sys.stderr

    tools_count = 25 if TOOLS_AVAILABLE else 1
    resources_ok = RESOURCES_AVAILABLE if "RESOURCES_AVAILABLE" in globals() else False

    version_str = f"{__version__}"
    tools_str = f"{tools_count}"
    resources_str = "Available" if resources_ok else "Unavailable"

    BOX_WIDTH = 56
    banner_lines = [
        "╭" + "─" * BOX_WIDTH + "╮",
        "│" + " " * BOX_WIDTH + "│",
        "│    ███████╗██╗  ██╗ █████╗ ██████╗ ██████╗             │",
        "│    ██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗            │",
        "│    █████╗   ╚███╔╝ ███████║██████╔╝██████╔╝            │",
        "│    ██╔══╝   ██╔██╗ ██╔══██║██╔══██╗██╔═══╝             │",
        "│    ███████╗██╔╝ ██╗██║  ██║██║  ██║██║                 │",
        "│    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝                 │",
        "│" + " " * BOX_WIDTH + "│",
        "│    Project Management Automation MCP Server            │",
        "│" + " " * BOX_WIDTH + "│",
        f"│    Version:    {version_str:<39}│",
        f"│    Tools:      {tools_str:<39}│",
        f"│    Resources:  {resources_str:<39}│",
        "│    Transport:  STDIO                                   │",
        "│" + " " * BOX_WIDTH + "│",
        "╰" + "─" * BOX_WIDTH + "╯",
    ]
    print("\n".join(banner_lines), file=file)


def main():
    """Entry point for exarp - detects mode and handles CLI args."""
    import sys

    args = sys.argv[1:]

    # Handle CLI arguments
    if "--help" in args or "-h" in args:
        _print_usage()
        return

    if "--version" in args or "-v" in args:
        print(f"exarp {__version__}")
        return

    if "--shell-setup" in args or "--zshrc" in args:
        _print_shell_setup("zsh")
        return

    if "--completions" in args:
        _print_completions("zsh")
        return

    if "--aliases" in args:
        _print_aliases()
        return

    # Check for explicit MCP mode or auto-detect
    if "--mcp" in args or _is_mcp_mode():
        # MCP server mode
        if not MCP_AVAILABLE:
            print("Error: MCP not available. Install with: uv sync (or uv pip install mcp>=1.0.0)", file=sys.stderr)
            sys.exit(1)
        
        if not USE_STDIO and mcp:
            # FastMCP mode
            _print_banner()
            try:
                mcp.run(show_banner=False)
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
            except Exception as e:
                logger.error(f"FastMCP server error: {e}", exc_info=True)
                # Don't exit immediately - let the connection close gracefully
                # FastMCP will handle the connection closure
                raise
        elif USE_STDIO and stdio_server_instance:
            # Stdio server mode
            _print_banner()
            import asyncio
            async def run():
                async with stdio_server() as (read_stream, write_stream):
                    init_options = stdio_server_instance.create_initialization_options()
                    await stdio_server_instance.run(read_stream, write_stream, init_options)
            try:
                asyncio.run(run())
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
            except ExceptionGroup as e:
                # Check if it's just a BrokenResourceError wrapped in ExceptionGroup
                # This happens during stdio server cleanup when client disconnects
                # anyio.BrokenResourceError is a normal connection closure, not an error
                broken_resource_found = False
                for exc in e.exceptions:
                    exc_type_name = type(exc).__name__
                    if exc_type_name == "BrokenResourceError" or "BrokenResource" in exc_type_name:
                        broken_resource_found = True
                        break
                if broken_resource_found:
                    logger.info("MCP connection closed by client (normal shutdown)")
                else:
                    # Real error - log it
                    logger.error(f"Server error: {e}", exc_info=True)
                    sys.exit(1)
            except Exception as e:
                # Check if it's a BrokenResourceError (anyio raises this on connection close)
                # This is a normal connection closure when client disconnects, not an error
                exc_type_name = type(e).__name__
                if exc_type_name == "BrokenResourceError" or "BrokenResource" in exc_type_name or "ConnectionError" in exc_type_name:
                    logger.info(f"MCP connection closed by client: {exc_type_name}")
                else:
                    logger.error(f"Server error: {e}", exc_info=True)
                    sys.exit(1)
        else:
            print("Error: MCP server not initialized properly", file=sys.stderr)
            sys.exit(1)
        return

    # Interactive terminal without args - show usage
    _print_usage()


# Register resources for stdio server (runs on import when stdio_server_instance exists)
if stdio_server_instance:
    try:
        # Try relative imports first (when run as module)
        try:
            from .resources.cache import get_cache_status_resource
            from .resources.catalog import (
                get_linters_resource,
                get_models_resource,
                get_problem_categories_resource,
                get_tts_backends_resource,
            )
            from .resources.history import get_history_resource
            from .resources.list import get_tools_list_resource
            from .resources.memories import (
                get_memories_by_category_resource,
                get_memories_by_task_resource,
                get_memories_health_resource,
                get_memories_resource,
                get_recent_memories_resource,
                get_session_memories_resource,
                get_wisdom_resource,
            )
            from .resources.status import get_status_resource
            from .resources.tasks import get_agent_tasks_resource, get_agents_resource, get_tasks_resource
            from .tools.project_scorecard import generate_project_scorecard as _generate_project_scorecard
            MEMORIES_AVAILABLE = True
        except ImportError:
            # Fallback to absolute imports (when run as script)
            from resources.cache import get_cache_status_resource
            from resources.catalog import (
                get_linters_resource,
                get_models_resource,
                get_problem_categories_resource,
                get_tts_backends_resource,
            )
            from resources.history import get_history_resource
            from resources.list import get_tools_list_resource
            from resources.status import get_status_resource
            from resources.tasks import get_agent_tasks_resource, get_agents_resource, get_tasks_resource
            from tools.project_scorecard import generate_project_scorecard as _generate_project_scorecard
            
            try:
                from resources.memories import (
                    get_memories_by_category_resource,
                    get_memories_by_task_resource,
                    get_memories_health_resource,
                    get_memories_resource,
                    get_recent_memories_resource,
                    get_session_memories_resource,
                )
                MEMORIES_AVAILABLE = True
            except ImportError:
                MEMORIES_AVAILABLE = False

        @stdio_server_instance.list_resources()
        async def list_resources():
            """List all available resources."""
            from mcp.types import Resource
            resources = [
                Resource(
                    uri="automation://status",
                    name="Server Status",
                    description="Current server status and version information",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://history",
                    name="Execution History",
                    description="Recent tool execution history",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://tools",
                    name="Tools Catalog",
                    description="Complete catalog of available tools",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://tasks",
                    name="Task List",
                    description="Current task list from Todo2",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://agents",
                    name="Agents",
                    description="Available AI agents and advisors",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://cache",
                    name="Cache",
                    description="Cached data and results",
                    mimeType="application/json",
                ),
                # Catalog resources
                Resource(
                    uri="automation://models",
                    name="Models Catalog",
                    description="Available AI models with recommendations for task types",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://problem-categories",
                    name="Problem Categories",
                    description="Problem categories with resolution hints",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://linters",
                    name="Linters Catalog",
                    description="Available linters and their installation status",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://tts-backends",
                    name="TTS Backends",
                    description="Available text-to-speech backends",
                    mimeType="application/json",
                ),
                Resource(
                    uri="automation://scorecard",
                    name="Project Scorecard",
                    description="Current project scorecard with all health metrics",
                    mimeType="application/json",
                ),
            ]
            
            # Add memory resources if available
            if MEMORIES_AVAILABLE:
                resources.extend([
                    Resource(
                        uri="automation://memories",
                        name="All Memories",
                        description="All AI session memories - browsable context for session continuity",
                        mimeType="application/json",
                    ),
                    Resource(
                        uri="automation://memories/recent",
                        name="Recent Memories",
                        description="Memories from the last 24 hours",
                        mimeType="application/json",
                    ),
                    Resource(
                        uri="automation://memories/health",
                        name="Memory Health",
                        description="Memory system health metrics and maintenance recommendations",
                        mimeType="application/json",
                    ),
                    # Note: Pattern-based resources (category/{category}, task/{task_id}, session/{date})
                    # are handled dynamically in read_resource() but not listed here as they require parameters
                ])
            
            return resources

        @stdio_server_instance.read_resource()
        async def read_resource(uri: str) -> str:
            """Handle resource reads."""
            if uri == "automation://status":
                return get_status_resource()
            elif uri == "automation://history":
                return get_history_resource(limit=50)
            elif uri == "automation://tools":
                return get_tools_list_resource()
            elif uri == "automation://tasks":
                return get_tasks_resource()
            elif uri.startswith("automation://tasks/agent/"):
                agent_name = uri.replace("automation://tasks/agent/", "")
                return get_agent_tasks_resource(agent_name)
            elif uri.startswith("automation://tasks/status/"):
                status = uri.replace("automation://tasks/status/", "")
                return get_tasks_resource(status=status)
            elif uri == "automation://agents":
                return get_agents_resource()
            elif uri == "automation://cache":
                return get_cache_status_resource()
            # Catalog resources
            elif uri == "automation://advisors":
                from ..resources.catalog import get_advisors_resource
                return get_advisors_resource()
            elif uri == "automation://models":
                return get_models_resource()
            elif uri == "automation://problem-categories":
                return get_problem_categories_resource()
            elif uri == "automation://linters":
                return get_linters_resource()
            elif uri == "automation://tts-backends":
                return get_tts_backends_resource()
            elif uri == "automation://scorecard":
                result = _generate_project_scorecard("json", True, None)
                if isinstance(result, str):
                    return result
                elif isinstance(result, dict):
                    return json.dumps(result, separators=(",", ":"))
                else:
                    return json.dumps({"result": str(result)}, separators=(",", ":"))
            # Memory resources
            elif uri == "automation://memories":
                if MEMORIES_AVAILABLE:
                    return get_memories_resource()
                else:
                    return json.dumps({"error": "Memory resources not available"})
            elif uri.startswith("automation://memories/category/"):
                if MEMORIES_AVAILABLE:
                    category = uri.replace("automation://memories/category/", "")
                    return get_memories_by_category_resource(category)
                else:
                    return json.dumps({"error": "Memory resources not available"})
            elif uri.startswith("automation://memories/task/"):
                if MEMORIES_AVAILABLE:
                    task_id = uri.replace("automation://memories/task/", "")
                    return get_memories_by_task_resource(task_id)
                else:
                    return json.dumps({"error": "Memory resources not available"})
            elif uri == "automation://memories/recent":
                if MEMORIES_AVAILABLE:
                    return get_recent_memories_resource()
                else:
                    return json.dumps({"error": "Memory resources not available"})
            elif uri.startswith("automation://memories/session/"):
                if MEMORIES_AVAILABLE:
                    date = uri.replace("automation://memories/session/", "")
                    return get_session_memories_resource(date)
                else:
                    return json.dumps({"error": "Memory resources not available"})
            elif uri == "automation://wisdom":
                if MEMORIES_AVAILABLE:
                    from ..resources.memories import get_wisdom_resource
                    return get_wisdom_resource()
                else:
                    return json.dumps({
                        "error": "automation://wisdom resource migrated to devwisdom-go MCP server",
                        "migration_note": "Use devwisdom MCP server resources directly"
                    }, separators=(",", ":"))
            elif uri == "automation://memories/health":
                if MEMORIES_AVAILABLE:
                    return get_memories_health_resource()
                else:
                    return json.dumps({"error": "Memory resources not available"})
            else:
                return json.dumps({"error": f"Unknown resource: {uri}"})

        RESOURCES_AVAILABLE = True
        logger.info("Resource handlers loaded successfully")
    except ImportError as e:
        RESOURCES_AVAILABLE = False
        logger.warning(f"Resource handlers not available: {e}")

if __name__ == "__main__":
    main()
