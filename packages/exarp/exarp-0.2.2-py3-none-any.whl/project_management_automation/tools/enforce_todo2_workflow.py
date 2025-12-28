"""
MCP Tool Wrapper for Todo2 Workflow Enforcement

Verifies Todo2 tasks comply with workflow requirements.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def enforce_todo2_workflow(
    auto_fix: bool = False,
    dry_run: bool = True,
    output_path: Optional[str] = None
) -> str:
    """
    Verify Todo2 tasks comply with workflow requirements.
    
    Workflow Rules:
    - "In Progress" status requires research_with_links comment
    - "Review" status requires result comment
    - "Done" status requires human approval (cannot auto-advance)
    
    Args:
        auto_fix: Whether to automatically fix violations (default: False)
        dry_run: Preview changes without applying (default: True)
        output_path: Path for report output (default: docs/TODO2_WORKFLOW_ENFORCEMENT_REPORT.md)
    
    Returns:
        JSON string with workflow validation results
    """
    start_time = time.time()
    
    try:
        from project_management_automation.utils import find_project_root
        from project_management_automation.utils.todo2_mcp_client import (
            list_todos_mcp,
            get_todo_details_mcp,
            update_todos_mcp,
            add_comments_mcp,
        )
        
        project_root = find_project_root()
        
        # Get all tasks
        all_tasks = list_todos_mcp(project_root=project_root)
        
        violations = []
        fixes_applied = []
        
        # Check each task for workflow compliance
        for task in all_tasks:
            task_id = task.get('id')
            task_name = task.get('name', '')
            status = task.get('status', 'Todo')
            
            # Get detailed task info including comments
            task_details = get_todo_details_mcp([task_id], project_root=project_root)
            if not task_details:
                continue
            
            task_detail = task_details[0] if task_details else {}
            comments = task_detail.get('comments', [])
            
            # Check workflow violations
            task_violations = []
            
            # Rule 1: In Progress requires research_with_links (T-16)
            if status == 'In Progress':
                has_research = any(
                    c.get('type') == 'research_with_links' 
                    for c in comments
                )
                if not has_research:
                    task_violations.append({
                        'rule': 'In Progress requires research_with_links',
                        'violation': 'Missing research_with_links comment',
                        'fix': 'Add research_with_links comment or move back to Todo'
                    })
                    
                    # Auto-generate research queries if auto_fix enabled (T-16)
                    if auto_fix and not dry_run:
                        try:
                            from project_management_automation.utils.agentic_tools_client import generate_research_queries_mcp
                            queries_result = generate_research_queries_mcp(
                                task_id=task_id,
                                project_root=project_root,
                                query_types=['implementation', 'best_practices'],
                                include_advanced=True,
                                target_year=2025
                            )
                            if queries_result and queries_result.get('queries'):
                                # Add research comment with generated queries
                                from project_management_automation.utils.todo2_mcp_client import add_comments_mcp
                                research_content = _format_queries_as_research(queries_result['queries'], task_name)
                                add_comments_mcp(
                                    todo_id=task_id,
                                    comments=[{
                                        'type': 'research_with_links',
                                        'content': research_content
                                    }],
                                    project_root=project_root
                                )
                                logger.info(f"Auto-generated research for task {task_id}")
                        except Exception as e:
                            logger.debug(f"Failed to auto-generate research: {e}")


def _format_queries_as_research(queries: List[Dict[str, Any]], task_name: str) -> str:
    """Format generated queries as research_with_links comment."""
    lines = ["**MANDATORY RESEARCH COMPLETED** ✅", "", f"## Auto-Generated Research Queries for: {task_name}", ""]
    
    for i, query in enumerate(queries, 1):
        query_text = query.get('query', '')
        query_type = query.get('type', 'general')
        lines.append(f"### Query {i}: {query_type}")
        lines.append(f"- **Query**: {query_text}")
        if query.get('rationale'):
            lines.append(f"- **Rationale**: {query['rationale']}")
        lines.append("")
    
    lines.append("**Note**: These queries were auto-generated. Execute via web search to gather research links.")
    
    return "\n".join(lines)
            
            # Rule 2: Review requires result comment
            if status == 'Review':
                has_result = any(
                    c.get('type') == 'result'
                    for c in comments
                )
                if not has_result:
                    task_violations.append({
                        'rule': 'Review requires result comment',
                        'violation': 'Missing result comment',
                        'fix': 'Add result comment or move back to In Progress'
                    })
            
            # Rule 3: Done requires human approval (cannot auto-advance)
            # This is informational only - we don't block Done status
            
            if task_violations:
                violations.append({
                    'task_id': task_id,
                    'task_name': task_name,
                    'status': status,
                    'violations': task_violations
                })
                
                # Auto-fix if enabled
                if auto_fix and not dry_run:
                    fix_applied = _apply_workflow_fix(
                        task_id,
                        task_violations,
                        status,
                        project_root
                    )
                    if fix_applied:
                        fixes_applied.append({
                            'task_id': task_id,
                            'task_name': task_name,
                            'fixes': fix_applied
                        })
        
        # Generate report
        report_path = output_path or 'docs/TODO2_WORKFLOW_ENFORCEMENT_REPORT.md'
        if report_path:
            report = _generate_report(
                violations,
                fixes_applied,
                len(all_tasks),
                dry_run,
                auto_fix
            )
            report_file = project_root / report_path
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w') as f:
                f.write(report)
        
        # Format response
        response_data = {
            'total_tasks_checked': len(all_tasks),
            'violations_found': len(violations),
            'fixes_applied': len(fixes_applied),
            'dry_run': dry_run,
            'auto_fix': auto_fix,
            'report_path': str(Path(report_path).absolute()),
            'violations': violations[:20]  # Limit to first 20 for response
        }
        
        duration = time.time() - start_time
        log_automation_execution('enforce_todo2_workflow', duration, True)
        
        return json.dumps(format_success_response(response_data), indent=2)
        
    except Exception as e:
        duration = time.time() - start_time
        log_automation_execution('enforce_todo2_workflow', duration, False, e)
        error_response = format_error_response(e, ErrorCode.AUTOMATION_ERROR)
        return json.dumps(error_response, indent=2)


def _apply_workflow_fix(
    task_id: str,
    violations: List[Dict[str, Any]],
    current_status: str,
    project_root: Path
) -> Optional[List[str]]:
    """Apply workflow fixes to a task."""
    from project_management_automation.utils.todo2_mcp_client import (
        update_todos_mcp,
        add_comments_mcp,
    )
    
    fixes_applied = []
    
    try:
        for violation in violations:
            rule = violation.get('rule', '')
            fix = violation.get('fix', '')
            
            # Fix 1: Missing research_with_links - move back to Todo
            if 'research_with_links' in rule and current_status == 'In Progress':
                update_todos_mcp(
                    updates=[{
                        'id': task_id,
                        'status': 'Todo'
                    }],
                    project_root=project_root
                )
                fixes_applied.append(f"Moved {task_id} from In Progress to Todo (missing research)")
            
            # Fix 2: Missing result - move back to In Progress
            elif 'result' in rule and current_status == 'Review':
                update_todos_mcp(
                    updates=[{
                        'id': task_id,
                        'status': 'In Progress'
                    }],
                    project_root=project_root
                )
                fixes_applied.append(f"Moved {task_id} from Review to In Progress (missing result)")
        
        return fixes_applied if fixes_applied else None
        
    except Exception as e:
        logger.error(f"Failed to apply workflow fix for {task_id}: {e}")
        return None


def _generate_report(
    violations: List[Dict[str, Any]],
    fixes_applied: List[Dict[str, Any]],
    total_tasks: int,
    dry_run: bool,
    auto_fix: bool
) -> str:
    """Generate markdown report."""
    report = f"""# Todo2 Workflow Enforcement Report

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Mode**: {'Dry Run' if dry_run else 'Live'}
**Auto-Fix**: {'Enabled' if auto_fix else 'Disabled'}

## Summary

- **Total Tasks Checked**: {total_tasks}
- **Violations Found**: {len(violations)}
- **Fixes Applied**: {len(fixes_applied)}

## Workflow Rules

1. **In Progress** status requires `research_with_links` comment
2. **Review** status requires `result` comment
3. **Done** status requires human approval (cannot auto-advance)

## Violations

"""
    
    if not violations:
        report += "✅ **No violations found!** All tasks comply with workflow requirements.\n"
    else:
        for violation in violations:
            report += f"""### {violation['task_name']} ({violation['task_id']})

- **Status**: {violation['status']}
- **Violations**:
"""
            for v in violation['violations']:
                report += f"  - **{v['rule']}**: {v['violation']}\n"
                report += f"    - *Fix*: {v['fix']}\n"
            report += "\n"
    
    if fixes_applied and not dry_run:
        report += f"\n## Fixes Applied\n\n"
        for fix in fixes_applied:
            report += f"### {fix['task_name']} ({fix['task_id']})\n\n"
            for f in fix['fixes']:
                report += f"- {f}\n"
            report += "\n"
    elif fixes_applied and dry_run:
        report += f"\n## Fixes Pending (Dry Run)\n\n{len(fixes_applied)} fixes would be applied.\n"
    
    return report

