"""
MCP Tool Wrapper for Auto Update Task Status

Automatically infers and updates task status based on codebase analysis.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

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
        def format_success_response(data, message=None):
            return {"success": True, "data": data, "timestamp": time.time()}
        def format_error_response(error, error_code, include_traceback=False):
            return {"success": False, "error": {"code": str(error_code), "message": str(error)}}
        def log_automation_execution(name, duration, success, error=None):
            logger.info(f"{name}: {duration:.2f}s, success={success}")
        class ErrorCode:
            AUTOMATION_ERROR = "AUTOMATION_ERROR"


def auto_update_task_status(
    project_id: Optional[str] = None,
    scan_depth: int = 3,
    file_extensions: Optional[list[str]] = None,
    auto_update_tasks: bool = False,
    confidence_threshold: float = 0.7,
    dry_run: bool = True,
    output_path: Optional[str] = None
) -> str:
    """
    Automatically infer and update task status based on codebase analysis.
    
    Uses agentic-tools `infer_task_progress` to analyze codebase and detect
    completed tasks based on code changes, file creation, and implementation evidence.
    
    Args:
        project_id: Filter to specific project (optional)
        scan_depth: Directory depth to scan (1-5, default: 3)
        file_extensions: File types to analyze (default: [.js, .ts, .jsx, .tsx, .py, .java, .cs, .go, .rs])
        auto_update_tasks: Whether to automatically update task status (default: False)
        confidence_threshold: Minimum confidence for auto-updating (0-1, default: 0.7)
        dry_run: Preview changes without applying (default: True)
        output_path: Path for report output (default: docs/AUTO_UPDATE_TASK_STATUS_REPORT.md)
    
    Returns:
        JSON string with inference results and update recommendations
    """
    start_time = time.time()
    
    try:
        from project_management_automation.utils import find_project_root
        from project_management_automation.utils.agentic_tools_client import infer_task_progress_mcp
        from project_management_automation.utils.todo2_mcp_client import list_todos_mcp, update_todos_mcp
        
        project_root = find_project_root()
        
        # Default file extensions if not provided
        if file_extensions is None:
            file_extensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cs', '.go', '.rs']
        
        # Call agentic-tools to infer task progress
        logger.info("Analyzing codebase to infer task progress...")
        inference_result = infer_task_progress_mcp(
            project_id=project_id,
            scan_depth=scan_depth,
            file_extensions=file_extensions,
            auto_update_tasks=False,  # We'll handle updates ourselves
            confidence_threshold=confidence_threshold,
            project_root=project_root
        )
        
        if not inference_result:
            return json.dumps(format_error_response(
                "Failed to infer task progress from codebase",
                ErrorCode.AUTOMATION_ERROR
            ), indent=2)
        
        # Get current tasks from Todo2
        current_tasks = list_todos_mcp(project_root=project_root)
        task_map = {t.get('id'): t for t in current_tasks}
        
        # Analyze inferred completions
        inferred_completions = inference_result.get('inferred_completions', [])
        discrepancies = []
        updates_needed = []
        
        for inferred in inferred_completions:
            task_id = inferred.get('task_id')
            inferred_status = inferred.get('status', 'Done')
            confidence = inferred.get('confidence', 0.0)
            evidence = inferred.get('evidence', [])
            
            if task_id not in task_map:
                continue
            
            current_task = task_map[task_id]
            current_status = current_task.get('status', 'Todo')
            
            # Check for discrepancies
            if inferred_status == 'Done' and current_status not in ['Done', 'Review']:
                if confidence >= confidence_threshold:
                    discrepancies.append({
                        'task_id': task_id,
                        'task_name': current_task.get('name', ''),
                        'current_status': current_status,
                        'inferred_status': inferred_status,
                        'confidence': confidence,
                        'evidence': evidence
                    })
                    
                    if not dry_run and auto_update_tasks:
                        updates_needed.append({
                            'id': task_id,
                            'status': 'Review'  # Move to Review, not directly to Done
                        })
        
        # Apply updates if not dry run
        updated_count = 0
        if updates_needed and not dry_run and auto_update_tasks:
            try:
                update_result = update_todos_mcp(updates_needed, project_root=project_root)
                if update_result:
                    updated_count = len(updates_needed)
                    logger.info(f"Updated {updated_count} task statuses")
            except Exception as e:
                logger.error(f"Failed to update tasks: {e}")
        
        # Generate report
        report_path = output_path or 'docs/AUTO_UPDATE_TASK_STATUS_REPORT.md'
        if report_path:
            report = _generate_report(
                inference_result,
                discrepancies,
                updates_needed,
                updated_count,
                dry_run,
                confidence_threshold
            )
            report_file = project_root / report_path
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w') as f:
                f.write(report)
        
        # Format response
        response_data = {
            'total_tasks_analyzed': len(current_tasks),
            'inferred_completions': len(inferred_completions),
            'discrepancies_found': len(discrepancies),
            'updates_applied': updated_count,
            'updates_pending': len(updates_needed) - updated_count,
            'dry_run': dry_run,
            'confidence_threshold': confidence_threshold,
            'report_path': str(Path(report_path).absolute()),
            'discrepancies': discrepancies[:10]  # Limit to first 10 for response
        }
        
        duration = time.time() - start_time
        log_automation_execution('auto_update_task_status', duration, True)
        
        return json.dumps(format_success_response(response_data), indent=2)
        
    except Exception as e:
        duration = time.time() - start_time
        log_automation_execution('auto_update_task_status', duration, False, e)
        error_response = format_error_response(e, ErrorCode.AUTOMATION_ERROR)
        return json.dumps(error_response, indent=2)


def _generate_report(
    inference_result: Dict[str, Any],
    discrepancies: list[Dict[str, Any]],
    updates_needed: list[Dict[str, Any]],
    updated_count: int,
    dry_run: bool,
    confidence_threshold: float
) -> str:
    """Generate markdown report."""
    report = f"""# Auto Update Task Status Report

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'Dry Run' if dry_run else 'Live'}
**Confidence Threshold**: {confidence_threshold}

## Summary

- **Total Tasks Analyzed**: {inference_result.get('total_tasks', 0)}
- **Inferred Completions**: {len(inference_result.get('inferred_completions', []))}
- **Discrepancies Found**: {len(discrepancies)}
- **Updates {'Pending' if dry_run else 'Applied'}**: {len(updates_needed) if dry_run else updated_count}

## Discrepancies

Tasks where codebase suggests completion but status is not Done/Review:

"""
    
    if not discrepancies:
        report += "✅ No discrepancies found - all tasks are properly tracked.\n"
    else:
        for disc in discrepancies:
            report += f"""### {disc['task_name']} ({disc['task_id']})

- **Current Status**: {disc['current_status']}
- **Inferred Status**: {disc['inferred_status']}
- **Confidence**: {disc['confidence']:.0%}
- **Evidence**: {len(disc.get('evidence', []))} items

"""
    
    if updates_needed and not dry_run:
        report += f"\n## Updates Applied\n\n{updated_count} tasks moved to Review status.\n"
    elif updates_needed and dry_run:
        report += f"\n## Updates Pending (Dry Run)\n\n{len(updates_needed)} tasks would be updated.\n"
    
    return report

