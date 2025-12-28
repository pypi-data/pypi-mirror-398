"""
Lifespan management for Exarp MCP Server.

Provides startup/shutdown hooks for:
- Todo2 database initialization
- Security controls setup
- Cache warming
- Resource cleanup

Usage:
    from project_management_automation.lifespan import exarp_lifespan

    mcp = FastMCP("exarp", lifespan=exarp_lifespan)
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    FastMCP = Any  # Type stub

logger = logging.getLogger("exarp.lifespan")


class ExarpState:
    """
    Application state managed during lifespan.

    Accessible in tools via context.
    """

    def __init__(self):
        self.project_root: Optional[Path] = None
        self.todo2_path: Optional[Path] = None
        self.advisor_log_path: Optional[Path] = None
        self.memory_path: Optional[Path] = None
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized


# Global state instance
_app_state: Optional[ExarpState] = None


def get_app_state() -> ExarpState:
    """Get the application state (initialized during lifespan)."""
    global _app_state
    if _app_state is None:
        _app_state = ExarpState()
    return _app_state


async def _init_project_root() -> Path:
    """Find and validate project root."""
    import os
    from .utils.project_root import find_project_root

    # Use centralized project root detection
    # This checks environment variables, markers, and provides fallbacks
    return find_project_root()


async def _init_todo2(project_root: Path) -> Path:
    """Initialize Todo2 database directory."""
    todo2_path = project_root / ".todo2"

    # Create directory if needed
    todo2_path.mkdir(parents=True, exist_ok=True)

    # Ensure state file exists
    state_file = todo2_path / "state.todo2.json"
    if not state_file.exists():
        import json
        state_file.write_text(json.dumps({"todos": []}, indent=2))
        logger.info(f"Created Todo2 state file: {state_file}")

    return todo2_path


async def _init_advisor_logs(project_root: Path) -> Path:
    """Initialize advisor consultation log directory."""
    log_path = project_root / ".exarp" / "advisor_logs"
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


async def _init_memory(project_root: Path) -> Path:
    """Initialize session memory directory."""
    memory_path = project_root / ".exarp" / "memories"
    memory_path.mkdir(parents=True, exist_ok=True)
    return memory_path


async def _cleanup_old_logs(advisor_log_path: Path, max_age_days: int = 30) -> int:
    """Clean up old advisor log files."""
    import time

    now = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    cleaned = 0

    try:
        for log_file in advisor_log_path.glob("*.jsonl"):
            age = now - log_file.stat().st_mtime
            if age > max_age_seconds:
                log_file.unlink()
                cleaned += 1
    except Exception as e:
        logger.warning(f"Error cleaning old logs: {e}")

    return cleaned


@asynccontextmanager
async def exarp_lifespan(server: "FastMCP") -> AsyncIterator[dict[str, Any]]:
    """
    Exarp application lifespan manager.

    Initializes:
    - Project root detection
    - Todo2 database
    - Advisor log directory
    - Session memory storage

    Cleans up:
    - Old log files
    - Temporary caches

    Yields:
        Dict with initialized state accessible via ctx.get_state()
    """
    state = get_app_state()

    # ═══════════════════════════════════════════════════════════════════════
    # STARTUP
    # ═══════════════════════════════════════════════════════════════════════

    logger.info("🚀 Exarp MCP Server starting up...")

    try:
        # 1. Initialize project root
        try:
            state.project_root = await _init_project_root()
            logger.info(f"📁 Project root: {state.project_root}")
        except Exception as e:
            logger.error(f"Failed to initialize project root: {e}", exc_info=True)
            # Fallback to current directory
            state.project_root = Path.cwd().resolve()
            logger.warning(f"Using fallback project root: {state.project_root}")

        # 2. Initialize Todo2 database
        try:
            state.todo2_path = await _init_todo2(state.project_root)
            logger.info(f"📋 Todo2 database: {state.todo2_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Todo2 database: {e}", exc_info=True)
            state.todo2_path = None

        # 3. Initialize advisor logs
        try:
            state.advisor_log_path = await _init_advisor_logs(state.project_root)
            logger.info(f"📝 Advisor logs: {state.advisor_log_path}")
        except Exception as e:
            logger.error(f"Failed to initialize advisor logs: {e}", exc_info=True)
            state.advisor_log_path = None

        # 4. Initialize memory storage
        try:
            state.memory_path = await _init_memory(state.project_root)
            logger.info(f"🧠 Memory storage: {state.memory_path}")
        except Exception as e:
            logger.error(f"Failed to initialize memory storage: {e}", exc_info=True)
            state.memory_path = None

        # 5. Clean up old logs (non-critical, continue even if it fails)
        if state.advisor_log_path:
            try:
                cleaned = await _cleanup_old_logs(state.advisor_log_path)
                if cleaned:
                    logger.info(f"🧹 Cleaned {cleaned} old log files")
            except Exception as e:
                logger.warning(f"Failed to clean old logs: {e}")

        state._initialized = True
        logger.info("✅ Exarp MCP Server ready")

        # Yield state for tools to access
        yield {
            "project_root": state.project_root,
            "todo2_path": state.todo2_path,
            "advisor_log_path": state.advisor_log_path,
            "memory_path": state.memory_path,
        }

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        # Don't raise - let the server start with partial initialization
        # Tools can check state.is_initialized to see if they can run
        state._initialized = False
        yield {
            "project_root": state.project_root or Path.cwd().resolve(),
            "todo2_path": None,
            "advisor_log_path": None,
            "memory_path": None,
        }

    finally:
        # ═══════════════════════════════════════════════════════════════════
        # SHUTDOWN
        # ═══════════════════════════════════════════════════════════════════

        logger.info("🛑 Exarp MCP Server shutting down...")

        # Cleanup tasks
        state._initialized = False

        logger.info("👋 Exarp MCP Server stopped")


# Simpler version for when FastMCP lifespan isn't needed
@asynccontextmanager
async def basic_lifespan():
    """Basic lifespan for non-FastMCP usage."""
    state = get_app_state()

    state.project_root = await _init_project_root()
    state.todo2_path = await _init_todo2(state.project_root)
    state.advisor_log_path = await _init_advisor_logs(state.project_root)
    state.memory_path = await _init_memory(state.project_root)
    state._initialized = True

    try:
        yield state
    finally:
        state._initialized = False


__all__ = [
    "exarp_lifespan",
    "basic_lifespan",
    "ExarpState",
    "get_app_state",
]

