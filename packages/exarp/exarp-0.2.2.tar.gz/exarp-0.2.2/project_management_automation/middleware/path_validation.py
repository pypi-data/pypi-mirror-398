"""
Path Validation Middleware for FastMCP.

Enforces path boundaries on all tool calls that include path arguments.
"""

import re
from pathlib import Path
from typing import Callable, Optional

try:
    from fastmcp.server.middleware import Middleware, MiddlewareContext
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False
    class Middleware:
        pass
    class MiddlewareContext:
        pass


class PathValidationMiddleware(Middleware):
    """
    Path boundary enforcement middleware.

    Validates all path-like arguments in tool calls to prevent
    directory traversal attacks.

    Usage:
        mcp.add_middleware(PathValidationMiddleware(
            allowed_roots=[project_root, Path("/tmp")],
            blocked_patterns=[r"\\.git", r"\\.env"],
        ))
    """

    # Argument names that typically contain paths
    PATH_ARG_PATTERNS = {
        "path", "file", "filepath", "file_path", "filename",
        "dir", "directory", "folder", "output", "output_path",
        "input", "input_path", "source", "target", "dest",
        "config_path", "workflow_path", "test_path", "coverage_file",
        "doc_path", "rule_files", "output_dir",
    }

    def __init__(
        self,
        allowed_roots: Optional[list[Path]] = None,
        allow_symlinks: bool = False,
        blocked_patterns: Optional[list[str]] = None,
        path_arg_patterns: Optional[set[str]] = None,
    ):
        """
        Initialize path validator.

        Args:
            allowed_roots: List of allowed root directories
            allow_symlinks: Whether to allow symlinks
            blocked_patterns: Regex patterns for blocked paths
            path_arg_patterns: Additional argument names to treat as paths
        """
        self.allowed_roots = [Path(r).resolve() for r in (allowed_roots or [Path.cwd()])]
        self.allow_symlinks = allow_symlinks
        self.blocked_patterns = blocked_patterns or [
            r"\.git(?:/|$)",
            r"\.env",
            r"\.ssh",
            r"\.aws",
            r"id_rsa",
            r"\.pem$",
            r"secrets?\.ya?ml",
        ]
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.blocked_patterns]
        self.path_arg_patterns = self.PATH_ARG_PATTERNS | (path_arg_patterns or set())

    def _is_path_argument(self, arg_name: str) -> bool:
        """Check if argument name looks like a path argument."""
        arg_lower = arg_name.lower()
        return any(pattern in arg_lower for pattern in self.path_arg_patterns)

    def _is_within_boundary(self, path: Path) -> bool:
        """Check if path is within allowed boundaries."""
        resolved = path.resolve()
        return any(
            resolved == root or root in resolved.parents
            for root in self.allowed_roots
        )

    def _is_blocked(self, path: Path) -> bool:
        """Check if path matches any blocked patterns."""
        path_str = str(path)
        return any(pattern.search(path_str) for pattern in self._compiled_patterns)

    def _validate_path(self, path_str: str) -> tuple[bool, str]:
        """
        Validate a path string.

        Returns:
            Tuple of (valid: bool, error_message: str)
        """
        if not path_str or not isinstance(path_str, str):
            return True, ""  # Empty/non-string paths are allowed (optional params)

        try:
            path = Path(path_str).expanduser()

            # Check for symlinks
            if not self.allow_symlinks and path.exists() and path.is_symlink():
                return False, f"Symlinks not allowed: {path_str}"

            resolved = path.resolve()

            # Check boundary
            if not self._is_within_boundary(resolved):
                return False, f"Path outside allowed boundaries: {path_str}"

            # Check blocked patterns
            if self._is_blocked(resolved):
                return False, f"Path matches blocked pattern: {path_str}"

            return True, ""

        except (OSError, ValueError) as e:
            return False, f"Invalid path: {path_str} - {e}"

    async def on_call_tool(self, context: MiddlewareContext, call_next: Callable):
        """Validate path arguments in tool calls."""
        if not FASTMCP_AVAILABLE:
            return await call_next(context)

        # Get arguments from context
        arguments = getattr(context, "arguments", {}) or {}

        # Validate each path-like argument
        for arg_name, arg_value in arguments.items():
            if self._is_path_argument(arg_name) and arg_value:
                valid, error = self._validate_path(str(arg_value))
                if not valid:
                    return {
                        "error": "path_validation_failed",
                        "message": error,
                        "argument": arg_name,
                    }

        return await call_next(context)

