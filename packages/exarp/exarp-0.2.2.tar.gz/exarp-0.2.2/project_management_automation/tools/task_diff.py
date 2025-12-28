"""
Task diff tool - Compare task versions across commits.

Provides Git-inspired diff functionality for tasks.

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
from ..utils.branch_utils import get_task_branch
from ..utils.commit_tracking import CommitTracker, TaskCommit, get_commit_tracker

logger = logging.getLogger(__name__)


def diff_task_states(old_state: dict[str, Any], new_state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate diff between two task states.
    
    Args:
        old_state: Previous task state
        new_state: Current task state
        
    Returns:
        Dictionary with:
        - changed: Fields that changed
        - added: Fields added in new state
        - removed: Fields removed in old state
        - unchanged: Fields that didn't change
    """
    old_keys = set(old_state.keys())
    new_keys = set(new_state.keys())
    
    added = new_keys - old_keys
    removed = old_keys - new_keys
    common = old_keys & new_keys
    
    changed = {}
    unchanged = {}
    
    for key in common:
        old_val = old_state[key]
        new_val = new_state[key]
        
        # Compare values (handling nested dicts/lists)
        if old_val != new_val:
            changed[key] = {"old": old_val, "new": new_val}
        else:
            unchanged[key] = old_val
    
    return {
        "changed": changed,
        "added": {k: new_state[k] for k in added},
        "removed": {k: old_state[k] for k in removed},
        "unchanged": unchanged,
    }


def format_diff_output(diff: dict[str, Any], task_name: Optional[str] = None) -> str:
    """
    Format diff output in human-readable format.
    
    Args:
        diff: Diff dictionary from diff_task_states
        task_name: Optional task name for header
        
    Returns:
        Formatted diff string
    """
    lines = []
    
    if task_name:
        lines.append(f"Task: {task_name}")
        lines.append("=" * 60)
        lines.append("")
    
    changed = diff.get("changed", {})
    added = diff.get("added", {})
    removed = diff.get("removed", {})
    
    if changed:
        lines.append("Changed Fields:")
        lines.append("-" * 60)
        for key, values in changed.items():
            lines.append(f"  {key}:")
            lines.append(f"    - {json.dumps(values['old'], default=str)}")
            lines.append(f"    + {json.dumps(values['new'], default=str)}")
        lines.append("")
    
    if added:
        lines.append("Added Fields:")
        lines.append("-" * 60)
        for key, value in added.items():
            lines.append(f"  + {key}: {json.dumps(value, default=str)}")
        lines.append("")
    
    if removed:
        lines.append("Removed Fields:")
        lines.append("-" * 60)
        for key, value in removed.items():
            lines.append(f"  - {key}: {json.dumps(value, default=str)}")
        lines.append("")
    
    if not (changed or added or removed):
        lines.append("No changes detected.")
    
    return "\n".join(lines)


def compare_task_commits(task_id: str, commit1_id: str, commit2_id: str) -> dict[str, Any]:
    """
    Compare task state between two commits.
    
    Args:
        task_id: Task ID
        commit1_id: First commit ID
        commit2_id: Second commit ID
        
    Returns:
        Dictionary with diff results and commit information
    """
    tracker = get_commit_tracker()
    
    # Get commits
    commit1 = None
    commit2 = None
    
    for commit in tracker.get_commits_for_task(task_id):
        if commit.id == commit1_id:
            commit1 = commit
        if commit.id == commit2_id:
            commit2 = commit
    
    if not commit1:
        raise ValueError(f"Commit {commit1_id} not found for task {task_id}")
    if not commit2:
        raise ValueError(f"Commit {commit2_id} not found for task {task_id}")
    
    # Ensure chronological order
    if commit1.timestamp > commit2.timestamp:
        commit1, commit2 = commit2, commit1
    
    old_state = commit1.new_state
    new_state = commit2.new_state
    
    diff = diff_task_states(old_state, new_state)
    
    return {
        "task_id": task_id,
        "commit1": {
            "id": commit1.id,
            "message": commit1.message,
            "timestamp": commit1.timestamp.isoformat(),
            "author": commit1.author,
        },
        "commit2": {
            "id": commit2.id,
            "message": commit2.message,
            "timestamp": commit2.timestamp.isoformat(),
            "author": commit2.author,
        },
        "diff": diff,
        "formatted": format_diff_output(diff, new_state.get("name")),
    }


def compare_task_versions(
    task_id: str,
    version1_commit_id: Optional[str] = None,
    version2_commit_id: Optional[str] = None,
    version1_time: Optional[datetime] = None,
    version2_time: Optional[datetime] = None,
) -> dict[str, Any]:
    """
    Compare two versions of a task.
    
    Can use commit IDs or timestamps to identify versions.
    
    Args:
        task_id: Task ID
        version1_commit_id: First version commit ID (optional)
        version2_commit_id: Second version commit ID (optional)
        version1_time: First version timestamp (optional)
        version2_time: Second version timestamp (optional)
        
    Returns:
        Dictionary with diff results
    """
    tracker = get_commit_tracker()
    
    # Get states for each version
    if version1_commit_id:
        state1 = tracker.get_task_state_at_commit(task_id, version1_commit_id)
        commit1_info = {"commit_id": version1_commit_id}
    elif version1_time:
        state1 = tracker.get_task_state_at_time(task_id, version1_time)
        commit1_info = {"timestamp": version1_time.isoformat()}
    else:
        # Default to first commit
        commits = tracker.get_commits_for_task(task_id)
        if not commits:
            raise ValueError(f"No commits found for task {task_id}")
        first_commit = commits[0]
        state1 = first_commit.old_state
        commit1_info = {"commit_id": first_commit.id, "message": first_commit.message}
    
    if version2_commit_id:
        state2 = tracker.get_task_state_at_commit(task_id, version2_commit_id)
        commit2_info = {"commit_id": version2_commit_id}
    elif version2_time:
        state2 = tracker.get_task_state_at_time(task_id, version2_time)
        commit2_info = {"timestamp": version2_time.isoformat()}
    else:
        # Default to current state (latest commit)
        latest_commit = tracker.get_latest_commit_for_task(task_id)
        if not latest_commit:
            raise ValueError(f"No commits found for task {task_id}")
        state2 = latest_commit.new_state
        commit2_info = {"commit_id": latest_commit.id, "message": latest_commit.message}
    
    if not state1:
        state1 = {}
    if not state2:
        state2 = {}
    
    diff = diff_task_states(state1, state2)
    
    return {
        "task_id": task_id,
        "version1": commit1_info,
        "version2": commit2_info,
        "diff": diff,
        "formatted": format_diff_output(diff, state2.get("name") or task_id[:8]),
    }


def get_task_history(task_id: str, branch: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Get complete commit history for a task.
    
    Args:
        task_id: Task ID
        branch: Optional branch filter
        
    Returns:
        List of commit dictionaries with diff information
    """
    tracker = get_commit_tracker()
    commits = tracker.get_commits_for_task(task_id, branch)
    
    history = []
    previous_state = {}
    
    for commit in commits:
        diff = diff_task_states(previous_state, commit.new_state)
        
        history.append({
            "commit_id": commit.id,
            "message": commit.message,
            "timestamp": commit.timestamp.isoformat(),
            "author": commit.author,
            "branch": commit.branch,
            "diff": diff,
        })
        
        previous_state = commit.new_state
    
    return history


def task_diff(
    task_id: str,
    commit1: Optional[str] = None,
    commit2: Optional[str] = None,
    time1: Optional[str] = None,
    time2: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> str:
    """
    Compare task versions and return/formatted diff.
    
    Args:
        task_id: Task ID
        commit1: First commit ID (optional)
        commit2: Second commit ID (optional)
        time1: First timestamp ISO string (optional)
        time2: Second timestamp ISO string (optional)
        output_path: Optional path to save formatted output
        
    Returns:
        Formatted diff string
    """
    version1_time = datetime.fromisoformat(time1) if time1 else None
    version2_time = datetime.fromisoformat(time2) if time2 else None
    
    result = compare_task_versions(
        task_id=task_id,
        version1_commit_id=commit1,
        version2_commit_id=commit2,
        version1_time=version1_time,
        version2_time=version2_time,
    )
    
    formatted = result["formatted"]
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formatted)
        logger.info(f"Diff saved to {output_path}")
    
    return formatted


__all__ = [
    "diff_task_states",
    "format_diff_output",
    "compare_task_commits",
    "compare_task_versions",
    "get_task_history",
    "task_diff",
]
