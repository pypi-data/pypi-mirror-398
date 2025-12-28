"""
Test Case Suggestions Tool

Suggests test cases based on code analysis.
Analyzes function signatures, identifies edge cases, and generates test templates.
"""

import ast
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Import error handler
try:
    from ..error_handler import ErrorCode, format_error_response, format_success_response, log_automation_execution
except ImportError:
    import sys
    from pathlib import Path
    server_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(server_dir))
    try:
        from error_handler import ErrorCode, format_error_response, format_success_response, log_automation_execution
    except ImportError:
        import time
        def format_success_response(data, message=None):
            return {"success": True, "data": data, "timestamp": time.time()}
        def format_error_response(error, error_code, include_traceback=False):
            return {"success": False, "error": {"code": str(error_code), "message": str(error)}}
        def log_automation_execution(name, duration, success, error=None):
            logger.info(f"{name}: {duration:.2f}s, success={success}")
        class ErrorCode:
            AUTOMATION_ERROR = "AUTOMATION_ERROR"


def suggest_test_cases(
    target_file: Optional[str] = None,
    test_framework: str = "pytest",
    min_confidence: float = 0.7,
    output_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Suggest test cases based on code analysis.

    Args:
        target_file: File to analyze (optional - analyzes all Python files if not provided)
        test_framework: Framework for suggestions (default: pytest)
        min_confidence: Minimum confidence threshold (default: 0.7)
        output_path: Path for suggestions output (optional)

    Returns:
        Dictionary with suggested test cases
    """
    import time
    start_time = time.time()

    try:
        from ..utils import find_project_root

        project_root = find_project_root()
        suggestions = []

        if target_file:
            # Analyze specific file
            file_path = Path(target_file)
            if not file_path.is_absolute():
                file_path = project_root / file_path

            if file_path.exists() and file_path.suffix == ".py":
                suggestions.extend(_analyze_file(file_path, test_framework, min_confidence))
        else:
            # Analyze all Python files in project
            for py_file in project_root.rglob("*.py"):
                # Skip test files, venv, and hidden directories
                if "test" in str(py_file).lower() or "venv" in str(py_file) or py_file.name.startswith("."):
                    continue
                if py_file.parent.name.startswith("."):
                    continue

                file_suggestions = _analyze_file(py_file, test_framework, min_confidence)
                if file_suggestions:
                    suggestions.extend(file_suggestions)

        # Filter by confidence
        filtered_suggestions = [
            s for s in suggestions
            if s.get("confidence", 0.0) >= min_confidence
        ]

        # Sort by confidence (highest first)
        filtered_suggestions.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        result = {
            "suggestions_count": len(filtered_suggestions),
            "total_analyzed": len(suggestions),
            "min_confidence": min_confidence,
            "framework": test_framework,
            "suggestions": filtered_suggestions[:50],  # Top 50
        }

        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            if not output_file.is_absolute():
                output_file = project_root / output_file
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)

            result["output_file"] = str(output_file)

        duration = time.time() - start_time
        log_automation_execution("suggest_test_cases", duration, True)

        return format_success_response(result)

    except Exception as e:
        duration = time.time() - start_time
        log_automation_execution("suggest_test_cases", duration, False, e)
        logger.error(f"Error suggesting test cases: {e}", exc_info=True)

        error_response = format_error_response(e, ErrorCode.AUTOMATION_ERROR)
        return error_response


def _analyze_file(file_path: Path, framework: str, min_confidence: float) -> list[dict[str, Any]]:
    """Analyze a Python file and suggest test cases."""
    suggestions = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private/internal functions
                if node.name.startswith("_"):
                    continue

                # Analyze function signature
                func_suggestions = _analyze_function(node, file_path, framework)
                if func_suggestions:
                    suggestions.extend(func_suggestions)

    except SyntaxError:
        logger.debug(f"Skipping {file_path} - syntax error")
    except Exception as e:
        logger.debug(f"Error analyzing {file_path}: {e}")

    return suggestions


def _analyze_function(func_node: ast.FunctionDef, file_path: Path, framework: str) -> list[dict[str, Any]]:
    """Analyze a function and suggest test cases."""
    suggestions = []

    # Basic test case for function existence
    suggestions.append({
        "function": func_node.name,
        "file": str(file_path.relative_to(file_path.parents[len(file_path.parts) - 3])),
        "type": "basic",
        "confidence": 0.8,
        "test_name": f"test_{func_node.name}",
        "description": f"Test that {func_node.name} can be called",
        "framework": framework,
    })

    # Analyze parameters for edge cases
    args = func_node.args
    if args.args:
        # Suggest tests for None, empty, and boundary values
        for arg in args.args:
            arg_name = arg.arg
            if arg_name == "self":
                continue

            # Edge case: None
            suggestions.append({
                "function": func_node.name,
                "file": str(file_path.relative_to(file_path.parents[len(file_path.parts) - 3])),
                "type": "edge_case",
                "confidence": 0.75,
                "test_name": f"test_{func_node.name}_with_none_{arg_name}",
                "description": f"Test {func_node.name} with None for {arg_name}",
                "framework": framework,
                "parameter": arg_name,
            })

    # Check for return statements
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(func_node))
    if has_return:
        suggestions.append({
            "function": func_node.name,
            "file": str(file_path.relative_to(file_path.parents[len(file_path.parts) - 3])),
            "type": "return_value",
            "confidence": 0.85,
            "test_name": f"test_{func_node.name}_return_value",
            "description": f"Test return value of {func_node.name}",
            "framework": framework,
        })

    return suggestions

