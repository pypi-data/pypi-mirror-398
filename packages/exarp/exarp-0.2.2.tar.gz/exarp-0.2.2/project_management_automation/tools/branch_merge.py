"""
Branch merge workflow - Merge tasks from one branch to another.

Implements Git-inspired branch merging with conflict detection and resolution.

Inspired by concepts from GitTask (https://github.com/Bengerthelorf/gittask)
Licensed under GPL-3.0. This implementation is original Python code.
See ATTRIBUTIONS.md for details.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..utils import find_project_root
from ..utils.branch_utils import (
    filter_tasks_by_branch,
    get_all_branches,
    get_task_branch,
    set_task_branch,
)
from ..utils.commit_tracking import (
    CommitTracker,
    get_commit_tracker,
    track_task_update,
)

logger = logging.getLogger(__name__)


class MergeConflict:
    """Represents a merge conflict between branches."""

    def __init__(
        self,
        task_id: str,
        source_state: dict[str, Any],
        target_state: dict[str, Any],
        conflict_fields: list[str],
    ):
        self.task_id = task_id
        self.source_state = source_state
        self.target_state = target_state
        self.conflict_fields = conflict_fields

    def to_dict(self) -> dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            "task_id": self.task_id,
            "source_state": self.source_state,
            "target_state": self.target_state,
            "conflict_fields": self.conflict_fields,
        }


def detect_merge_conflicts(
    source_tasks: list[dict[str, Any]], target_tasks: list[dict[str, Any]]
) -> list[MergeConflict]:
    """
    Detect merge conflicts between source and target branch tasks.
    
    A conflict occurs when:
    - Same task ID exists in both branches
    - Task fields differ (name, description, status, etc.)
    
    Args:
        source_tasks: Tasks from source branch
        target_tasks: Tasks from target branch
        
    Returns:
        List of MergeConflict objects
    """
    conflicts = []
    
    # Create task lookup by ID
    target_by_id = {task.get("id"): task for task in target_tasks}
    
    for source_task in source_tasks:
        task_id = source_task.get("id")
        if not task_id:
            continue
        
        target_task = target_by_id.get(task_id)
        if not target_task:
            continue
        
        # Compare task fields
        conflict_fields = []
        fields_to_check = ["name", "long_description", "status", "priority", "tags"]
        
        for field in fields_to_check:
            source_val = source_task.get(field)
            target_val = target_task.get(field)
            
            if source_val != target_val:
                conflict_fields.append(field)
        
        if conflict_fields:
            conflicts.append(
                MergeConflict(
                    task_id=task_id,
                    source_state=source_task,
                    target_state=target_task,
                    conflict_fields=conflict_fields,
                )
            )
    
    return conflicts


def resolve_conflict(
    conflict: MergeConflict,
    strategy: str = "newer",
    preferred_branch: Optional[str] = None,
) -> dict[str, Any]:
    """
    Resolve a merge conflict using a strategy.
    
    Strategies:
    - 'newer': Use task with later updatedAt timestamp
    - 'source': Always use source branch version
    - 'target': Always use target branch version
    - 'preferred': Use preferred_branch version if specified, else newer
    
    Args:
        conflict: MergeConflict object
        strategy: Resolution strategy
        preferred_branch: Preferred branch for 'preferred' strategy
        
    Returns:
        Resolved task dictionary
    """
    source = conflict.source_state
    target = conflict.target_state
    
    if strategy == "source":
        return source.copy()
    elif strategy == "target":
        return target.copy()
    elif strategy == "newer":
        source_time = source.get("lastModified") or source.get("createdAt")
        target_time = target.get("lastModified") or target.get("createdAt")
        
        if source_time and target_time:
            if source_time > target_time:
                return source.copy()
            else:
                return target.copy()
        elif source_time:
            return source.copy()
        else:
            return target.copy()
    elif strategy == "preferred":
        if preferred_branch == "source":
            return source.copy()
        elif preferred_branch == "target":
            return target.copy()
        else:
            # Fallback to newer
            return resolve_conflict(conflict, strategy="newer")
    else:
        # Default to newer
        return resolve_conflict(conflict, strategy="newer")


def merge_branches(
    source_branch: str,
    target_branch: str,
    conflict_strategy: str = "newer",
    author: str = "system",
    create_merge_commit: bool = True,
) -> dict[str, Any]:
    """
    Merge tasks from source branch into target branch.
    
    Args:
        source_branch: Source branch name
        target_branch: Target branch name
        conflict_strategy: Conflict resolution strategy
        author: Author for merge commit
        create_merge_commit: Whether to create a merge commit
        
    Returns:
        Dictionary with merge results:
        - merged_tasks: Number of tasks merged
        - conflicts: List of conflicts found
        - resolved: Number of conflicts resolved
        - merge_commit_id: ID of merge commit (if created)
    """
    project_root = find_project_root()
    todo2_file = project_root / ".todo2" / "state.todo2.json"
    
    if not todo2_file.exists():
        raise FileNotFoundError(f"Todo2 state file not found: {todo2_file}")
    
    # Load tasks
    with open(todo2_file) as f:
        data = json.load(f)
    
    all_tasks = data.get("todos", [])
    source_tasks = filter_tasks_by_branch(all_tasks, source_branch)
    target_tasks = filter_tasks_by_branch(all_tasks, target_branch)
    
    # Detect conflicts
    conflicts = detect_merge_conflicts(source_tasks, target_tasks)
    
    # Create task lookup
    task_by_id = {task.get("id"): task for task in all_tasks}
    updated_tasks = []
    merged_count = 0
    
    # Merge tasks
    for source_task in source_tasks:
        task_id = source_task.get("id")
        if not task_id:
            continue
        
        target_task = task_by_id.get(task_id)
        
        if target_task:
            # Task exists in target - check for conflicts
            conflict = next((c for c in conflicts if c.task_id == task_id), None)
            
            if conflict:
                # Resolve conflict
                resolved_task = resolve_conflict(conflict, strategy=conflict_strategy, preferred_branch=source_branch)
                resolved_task = set_task_branch(resolved_task, target_branch)
                
                # Update task
                task_index = next((i for i, t in enumerate(all_tasks) if t.get("id") == task_id), None)
                if task_index is not None:
                    old_task = all_tasks[task_index]
                    all_tasks[task_index] = resolved_task
                    updated_tasks.append((old_task, resolved_task))
                    merged_count += 1
            else:
                # No conflict - task already in target
                pass
        else:
            # New task - add to target
            new_task = source_task.copy()
            new_task = set_task_branch(new_task, target_branch)
            
            all_tasks.append(new_task)
            merged_count += 1
    
    # Save updated tasks
    data["todos"] = all_tasks
    with open(todo2_file, "w") as f:
        json.dump(data, f, indent=2)
    
    # Create merge commits for updated tasks
    tracker = get_commit_tracker()
    merge_commit_ids = []
    
    for old_task, new_task in updated_tasks:
        commit = track_task_update(
            task_id=new_task.get("id"),
            old_state=old_task,
            new_state=new_task,
            author=author,
            branch=target_branch,
        )
        merge_commit_ids.append(commit.id)
    
    # Create merge commit record
    if create_merge_commit and merged_count > 0:
        merge_commit = tracker.create_commit(
            task_id="merge",
            message=f"Merge branch: {source_branch} -> {target_branch}",
            old_state={"source_branch": source_branch, "merged_count": 0},
            new_state={"source_branch": source_branch, "target_branch": target_branch, "merged_count": merged_count},
            author=author,
            branch=target_branch,
        )
        merge_commit_ids.append(merge_commit.id)
    
    resolved_count = len(conflicts) if conflict_strategy else 0
    
    return {
        "source_branch": source_branch,
        "target_branch": target_branch,
        "merged_tasks": merged_count,
        "conflicts": [c.to_dict() for c in conflicts],
        "resolved": resolved_count,
        "merge_commit_ids": merge_commit_ids,
        "timestamp": datetime.now().isoformat(),
    }


def preview_merge(source_branch: str, target_branch: str) -> dict[str, Any]:
    """
    Preview merge without actually merging (dry run).
    
    Args:
        source_branch: Source branch name
        target_branch: Target branch name
        
    Returns:
        Dictionary with merge preview information
    """
    project_root = find_project_root()
    todo2_file = project_root / ".todo2" / "state.todo2.json"
    
    if not todo2_file.exists():
        raise FileNotFoundError(f"Todo2 state file not found: {todo2_file}")
    
    # Load tasks
    with open(todo2_file) as f:
        data = json.load(f)
    
    all_tasks = data.get("todos", [])
    source_tasks = filter_tasks_by_branch(all_tasks, source_branch)
    target_tasks = filter_tasks_by_branch(all_tasks, target_branch)
    
    # Detect conflicts
    conflicts = detect_merge_conflicts(source_tasks, target_tasks)
    
    # Count tasks to merge
    target_task_ids = {task.get("id") for task in target_tasks}
    new_tasks = [task for task in source_tasks if task.get("id") not in target_task_ids]
    
    return {
        "source_branch": source_branch,
        "target_branch": target_branch,
        "source_task_count": len(source_tasks),
        "target_task_count": len(target_tasks),
        "new_tasks": len(new_tasks),
        "conflicts": [c.to_dict() for c in conflicts],
        "would_merge": len(new_tasks) + len([c for c in conflicts]),
    }


__all__ = [
    "MergeConflict",
    "detect_merge_conflicts",
    "resolve_conflict",
    "merge_branches",
    "preview_merge",
]
