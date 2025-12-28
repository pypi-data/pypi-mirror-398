"""
Centralized Hint Registry with Dynamic Loading

Provides a unified registry for all tool hints that can be:
- Loaded from JSON files (hot-reloadable)
- Extended programmatically
- Filtered by category, mode, or agent type
- Watched for changes (dynamic reload)

This replaces scattered [HINT: ...] markers in docstrings with a
centralized, manageable, and dynamically loadable system.

Usage:
    from project_management_automation.resources.hint_registry import (
        HintRegistry,
        get_hint_registry,
        reload_hints,
    )
    
    # Get singleton registry
    registry = get_hint_registry()
    
    # Get hints for a tool
    hint = registry.get_hint("project_scorecard")
    
    # Get all hints for a category
    hints = registry.get_hints_by_category("security")
    
    # Reload hints from disk (hot-reload)
    reload_hints()
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# Optional watchdog import for file watching (hot-reload)
try:
    from watchdog.events import FileModifiedEvent, FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None  # type: ignore
    FileSystemEventHandler = object  # type: ignore
    FileModifiedEvent = object  # type: ignore

logger = logging.getLogger("exarp.hint_registry")


@dataclass
class ToolHint:
    """A single tool hint with metadata."""

    tool_name: str
    hint: str
    category: str
    outputs: List[str] = field(default_factory=list)
    inputs: Dict[str, str] = field(default_factory=dict)
    side_effects: str = "None"
    runtime: str = "< 1s"
    examples: List[str] = field(default_factory=list)
    related_tools: List[str] = field(default_factory=list)
    recommended_model: str = "claude-haiku"
    persona: str = "developer"
    modes: List[str] = field(default_factory=list)  # Workflow modes this tool is visible in

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tool_name": self.tool_name,
            "hint": self.hint,
            "category": self.category,
            "outputs": self.outputs,
            "inputs": self.inputs,
            "side_effects": self.side_effects,
            "runtime": self.runtime,
            "examples": self.examples,
            "related_tools": self.related_tools,
            "recommended_model": self.recommended_model,
            "persona": self.persona,
            "modes": self.modes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolHint":
        """Create from dictionary."""
        return cls(
            tool_name=data.get("tool_name", "unknown"),
            hint=data.get("hint", ""),
            category=data.get("category", "other"),
            outputs=data.get("outputs", []),
            inputs=data.get("inputs", {}),
            side_effects=data.get("side_effects", "None"),
            runtime=data.get("runtime", "< 1s"),
            examples=data.get("examples", []),
            related_tools=data.get("related_tools", []),
            recommended_model=data.get("recommended_model", "claude-haiku"),
            persona=data.get("persona", "developer"),
            modes=data.get("modes", []),
        )


class HintFileHandler(FileSystemEventHandler):
    """Watches hint files for changes and triggers reload."""

    def __init__(self, callback: Callable[[], None]):
        self.callback = callback
        self._last_reload = 0
        self._debounce_seconds = 1.0  # Debounce rapid changes

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent) and event.src_path.endswith(".json"):
            now = time.time()
            if now - self._last_reload > self._debounce_seconds:
                self._last_reload = now
                logger.info(f"Hint file changed: {event.src_path}, reloading...")
                self.callback()


class HintRegistry:
    """
    Centralized registry for tool hints with dynamic loading.
    
    Features:
    - Load hints from JSON files
    - Programmatic hint registration
    - Category and mode filtering
    - File watching for hot-reload
    - Thread-safe operations
    """

    def __init__(self, hints_dir: Optional[Path] = None, watch: bool = False):
        """
        Initialize the hint registry.
        
        Args:
            hints_dir: Directory containing hint JSON files
            watch: Whether to watch for file changes (hot-reload)
        """
        self._hints: Dict[str, ToolHint] = {}
        self._lock = threading.RLock()
        self._last_loaded: Optional[datetime] = None
        self._observer: Optional[Observer] = None
        self._callbacks: List[Callable[[], None]] = []

        # Find hints directory
        if hints_dir:
            self._hints_dir = hints_dir
        else:
            self._hints_dir = self._find_hints_dir()

        # Load initial hints
        self._load_builtin_hints()
        self._load_file_hints()

        # Start file watcher if requested
        if watch and self._hints_dir.exists():
            self._start_watcher()

    def _find_hints_dir(self) -> Path:
        """Find the hints directory."""
        # Check for .exarp/hints or config/hints
        env_root = os.getenv("PROJECT_ROOT") or os.getenv("WORKSPACE_PATH")
        if env_root:
            base = Path(env_root)
        else:
            base = Path.cwd()

        # Try common locations
        for subdir in [".exarp/hints", "config/hints", ".cursor/hints"]:
            hints_path = base / subdir
            if hints_path.exists():
                return hints_path

        # Default to .exarp/hints (will be created if needed)
        return base / ".exarp" / "hints"

    def _load_builtin_hints(self) -> None:
        """Load built-in hints from context_primer module."""
        try:
            from .context_primer import TOOL_HINTS_REGISTRY

            with self._lock:
                for name, data in TOOL_HINTS_REGISTRY.items():
                    hint = ToolHint(
                        tool_name=name,
                        hint=data.get("hint", ""),
                        category=data.get("category", "other"),
                        outputs=data.get("outputs", []),
                    )
                    self._hints[name] = hint

            logger.debug(f"Loaded {len(TOOL_HINTS_REGISTRY)} built-in hints")
        except ImportError as e:
            logger.warning(f"Could not load built-in hints: {e}")

    def _load_file_hints(self) -> None:
        """Load hints from JSON files in hints directory."""
        if not self._hints_dir.exists():
            logger.debug(f"Hints directory not found: {self._hints_dir}")
            return

        loaded = 0
        for hint_file in self._hints_dir.glob("*.json"):
            try:
                data = json.loads(hint_file.read_text())

                # Support both single hint and array of hints
                hints = data if isinstance(data, list) else [data]

                with self._lock:
                    for hint_data in hints:
                        if "tool_name" in hint_data:
                            hint = ToolHint.from_dict(hint_data)
                            self._hints[hint.tool_name] = hint
                            loaded += 1

            except Exception as e:
                logger.warning(f"Error loading hint file {hint_file}: {e}")

        self._last_loaded = datetime.now()
        if loaded > 0:
            logger.info(f"Loaded {loaded} hints from files")

    def _start_watcher(self) -> None:
        """Start file watcher for hot-reload."""
        if not WATCHDOG_AVAILABLE:
            logger.debug("Watchdog not available, file watching disabled")
            return

        try:
            self._observer = Observer()
            handler = HintFileHandler(self.reload)
            self._observer.schedule(handler, str(self._hints_dir), recursive=False)
            self._observer.start()
            logger.info(f"Started hint file watcher on {self._hints_dir}")
        except Exception as e:
            logger.warning(f"Could not start file watcher: {e}")

    def stop_watcher(self) -> None:
        """Stop file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def reload(self) -> None:
        """Reload hints from files (hot-reload)."""
        logger.info("Reloading hints...")
        self._load_file_hints()

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"Callback error on reload: {e}")

    def on_reload(self, callback: Callable[[], None]) -> None:
        """Register callback for reload events."""
        self._callbacks.append(callback)

    def register(self, hint: ToolHint) -> None:
        """Register a tool hint programmatically."""
        with self._lock:
            self._hints[hint.tool_name] = hint

    def register_from_dict(self, data: Dict[str, Any]) -> None:
        """Register a hint from dictionary."""
        hint = ToolHint.from_dict(data)
        self.register(hint)

    def get_hint(self, tool_name: str) -> Optional[ToolHint]:
        """Get hint for a specific tool."""
        with self._lock:
            return self._hints.get(tool_name)

    def get_hint_text(self, tool_name: str) -> str:
        """Get just the hint text for a tool."""
        hint = self.get_hint(tool_name)
        return hint.hint if hint else ""

    def get_all_hints(self) -> Dict[str, ToolHint]:
        """Get all registered hints."""
        with self._lock:
            return dict(self._hints)

    def get_hints_by_category(self, category: str) -> Dict[str, ToolHint]:
        """Get hints filtered by category."""
        with self._lock:
            return {
                name: hint for name, hint in self._hints.items()
                if hint.category == category
            }

    def get_hints_by_mode(self, mode: str) -> Dict[str, ToolHint]:
        """Get hints filtered by workflow mode."""
        with self._lock:
            return {
                name: hint for name, hint in self._hints.items()
                if not hint.modes or mode in hint.modes
            }

    def get_hints_by_persona(self, persona: str) -> Dict[str, ToolHint]:
        """Get hints filtered by target persona."""
        with self._lock:
            return {
                name: hint for name, hint in self._hints.items()
                if hint.persona == persona
            }

    def get_categories(self) -> Set[str]:
        """Get all unique categories."""
        with self._lock:
            return {hint.category for hint in self._hints.values()}

    def get_compact_hints(self) -> Dict[str, str]:
        """Get hints in compact format (tool_name -> hint_text)."""
        with self._lock:
            return {name: hint.hint for name, hint in self._hints.items()}

    def export_to_json(self, path: Optional[Path] = None) -> str:
        """Export all hints to JSON."""
        with self._lock:
            hints_list = [hint.to_dict() for hint in self._hints.values()]

        json_str = json.dumps(hints_list, indent=2)

        if path:
            path.write_text(json_str)
            logger.info(f"Exported {len(hints_list)} hints to {path}")

        return json_str

    def status(self) -> Dict[str, Any]:
        """Get registry status."""
        with self._lock:
            return {
                "total_hints": len(self._hints),
                "categories": list(self.get_categories()),
                "hints_dir": str(self._hints_dir),
                "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
                "watcher_active": self._observer is not None and self._observer.is_alive(),
            }


# Singleton instance
_registry: Optional[HintRegistry] = None
_registry_lock = threading.Lock()


def get_hint_registry(watch: bool = False) -> HintRegistry:
    """
    Get the singleton hint registry instance.
    
    Args:
        watch: Enable file watching for hot-reload (only on first call)
    
    Returns:
        The global HintRegistry instance
    """
    global _registry

    with _registry_lock:
        if _registry is None:
            _registry = HintRegistry(watch=watch)
        return _registry


def reload_hints() -> None:
    """Reload hints from files (hot-reload)."""
    registry = get_hint_registry()
    registry.reload()


def get_hint(tool_name: str) -> str:
    """Get hint text for a tool (convenience function)."""
    registry = get_hint_registry()
    return registry.get_hint_text(tool_name)


def create_hints_directory() -> Path:
    """Create hints directory with example file."""
    env_root = os.getenv("PROJECT_ROOT") or os.getenv("WORKSPACE_PATH")
    base = Path(env_root) if env_root else Path.cwd()

    hints_dir = base / ".exarp" / "hints"
    hints_dir.mkdir(parents=True, exist_ok=True)

    # Create example hint file
    example_file = hints_dir / "example_hints.json"
    if not example_file.exists():
        example_hints = [
            {
                "tool_name": "my_custom_tool",
                "hint": "Custom tool. Does something useful. Returns result.",
                "category": "custom",
                "outputs": ["result", "status"],
                "examples": ["Use my_custom_tool to do X"],
                "modes": ["development"],
            }
        ]
        example_file.write_text(json.dumps(example_hints, indent=2))
        logger.info(f"Created example hints file: {example_file}")

    return hints_dir


# Resource functions for MCP
def get_hint_registry_status() -> str:
    """Resource: automation://hints/status - Get registry status."""
    registry = get_hint_registry()
    return json.dumps(registry.status(), separators=(',', ':'))


def register_hint_registry_resources(mcp) -> None:
    """Register hint registry resources with MCP server."""
    try:
        @mcp.resource("automation://hints/status")
        def hints_status_resource() -> str:
            """Get hint registry status."""
            return get_hint_registry_status()

        @mcp.resource("automation://hints/category/{category}")
        def hints_by_category_resource(category: str) -> str:
            """Get hints by category."""
            registry = get_hint_registry()
            hints = registry.get_hints_by_category(category)
            return json.dumps({
                "category": category,
                "hints": {name: hint.to_dict() for name, hint in hints.items()},
                "count": len(hints),
            }, indent=2)

        @mcp.resource("automation://hints/persona/{persona}")
        def hints_by_persona_resource(persona: str) -> str:
            """Get hints by persona."""
            registry = get_hint_registry()
            hints = registry.get_hints_by_persona(persona)
            return json.dumps({
                "persona": persona,
                "hints": {name: hint.to_dict() for name, hint in hints.items()},
                "count": len(hints),
            }, indent=2)

        logger.info("✅ Registered 3 hint registry resources")

    except Exception as e:
        logger.warning(f"Could not register hint registry resources: {e}")


__all__ = [
    "ToolHint",
    "HintRegistry",
    "get_hint_registry",
    "reload_hints",
    "get_hint",
    "create_hints_directory",
    "get_hint_registry_status",
    "register_hint_registry_resources",
]

