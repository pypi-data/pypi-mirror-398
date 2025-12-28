"""
Git graph visualization - Generate visual timeline of commits.

Creates text-based and Graphviz DOT format visualizations of commit history.

Inspired by concepts from GitTask (https://github.com/Bengerthelorf/gittask)
Licensed under GPL-3.0. This implementation is original Python code.
See ATTRIBUTIONS.md for details.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..utils import find_project_root
from ..utils.commit_tracking import CommitTracker, TaskCommit, get_commit_tracker
from ..utils.branch_utils import MAIN_BRANCH

logger = logging.getLogger(__name__)


def generate_text_graph(
    commits: list[TaskCommit],
    max_commits: int = 50,
    show_branches: bool = True,
) -> str:
    """
    Generate ASCII text-based Git graph.
    
    Args:
        commits: List of commits (should be sorted by timestamp)
        max_commits: Maximum number of commits to display
        show_branches: Whether to show branch information
        
    Returns:
        Formatted text graph string
    """
    if not commits:
        return "No commits found."
    
    # Sort commits by timestamp
    sorted_commits = sorted(commits, key=lambda c: c.timestamp)
    
    # Limit to max_commits (most recent)
    if len(sorted_commits) > max_commits:
        sorted_commits = sorted_commits[-max_commits:]
        logger.warning(f"Showing only last {max_commits} commits (total: {len(commits)})")
    
    lines = []
    
    # Group by branch
    branch_commits: dict[str, list[TaskCommit]] = defaultdict(list)
    for commit in sorted_commits:
        branch_commits[commit.branch].append(commit)
    
    # Build graph
    branch_colors = {}
    color_index = 0
    colors = ["*", "+", "#", "@", "%", "&", "="]
    
    for branch in sorted(branch_commits.keys()):
        if branch not in branch_colors:
            if branch == MAIN_BRANCH:
                branch_colors[branch] = "*"
            else:
                branch_colors[branch] = colors[color_index % len(colors)]
                color_index += 1
    
    # Header
    lines.append("Commit History Graph")
    lines.append("=" * 80)
    lines.append("")
    
    if show_branches:
        lines.append("Branches:")
        for branch, symbol in sorted(branch_colors.items()):
            lines.append(f"  {symbol} {branch}")
        lines.append("")
    
    # Graph lines
    for commit in sorted_commits:
        branch_symbol = branch_colors.get(commit.branch, "*")
        timestamp = commit.timestamp.strftime("%Y-%m-%d %H:%M")
        commit_short = commit.id[:8]
        
        # Truncate message
        message = commit.message[:60]
        if len(commit.message) > 60:
            message += "..."
        
        lines.append(f"{branch_symbol} {commit_short} | {timestamp}")
        lines.append(f"  {commit.author}: {message}")
        
        # Show task ID if different from commit message
        if commit.task_id and commit.task_id not in commit.message:
            task_short = commit.task_id[:8]
            lines.append(f"  Task: {task_short}")
        
        lines.append("")
    
    return "\n".join(lines)


def generate_graphviz_dot(
    commits: list[TaskCommit],
    output_path: Optional[Path] = None,
    show_task_links: bool = True,
) -> str:
    """
    Generate Graphviz DOT format graph.
    
    Args:
        commits: List of commits (should be sorted by timestamp)
        output_path: Optional path to save DOT file
        show_task_links: Whether to show links between commits of same task
        
    Returns:
        Graphviz DOT format string
    """
    if not commits:
        return 'digraph empty { label="No commits"; }'
    
    # Sort commits by timestamp
    sorted_commits = sorted(commits, key=lambda c: c.timestamp)
    
    # Assign branch colors
    branch_colors: dict[str, str] = {}
    colors = [
        "#2196F3",  # Blue (main)
        "#4CAF50",  # Green
        "#F44336",  # Red
        "#9C27B0",  # Purple
        "#FF9800",  # Orange
        "#009688",  # Teal
        "#673AB7",  # Deep Purple
        "#3F51B5",  # Indigo
    ]
    
    branches = sorted(set(c.branch for c in sorted_commits))
    for i, branch in enumerate(branches):
        branch_colors[branch] = colors[i % len(colors)]
    
    # Build DOT graph
    lines = []
    lines.append('digraph commit_history {')
    lines.append('  rankdir=TB;')
    lines.append('  node [shape=box, style=rounded];')
    lines.append('  edge [arrowhead=vee];')
    lines.append('')
    
    # Create nodes
    commit_nodes = {}
    for commit in sorted_commits:
        node_id = f"commit_{commit.id[:8]}"
        commit_nodes[commit.id] = node_id
        
        branch_color = branch_colors.get(commit.branch, colors[0])
        
        # Escape quotes in message
        message = commit.message.replace('"', '\\"')
        
        # Node label
        label = f'"{commit.id[:8]}\\n{message[:40]}\\n{commit.timestamp.strftime("%Y-%m-%d %H:%M")}"'
        
        lines.append(f'  {node_id} [label={label}, fillcolor="{branch_color}", style="rounded,filled"];')
    
    lines.append('')
    
    # Create edges (chronological)
    if show_task_links:
        # Group by task and create edges
        task_commits: dict[str, list[TaskCommit]] = defaultdict(list)
        for commit in sorted_commits:
            if commit.task_id:
                task_commits[commit.task_id].append(commit)
        
        for task_id, task_commit_list in task_commits.items():
            task_commit_list.sort(key=lambda c: c.timestamp)
            for i in range(len(task_commit_list) - 1):
                from_commit = task_commit_list[i]
                to_commit = task_commit_list[i + 1]
                from_node = commit_nodes[from_commit.id]
                to_node = commit_nodes[to_commit.id]
                lines.append(f'  {from_node} -> {to_node} [color="{branch_colors.get(to_commit.branch, colors[0])}"];')
    else:
        # Simple chronological edges
        for i in range(len(sorted_commits) - 1):
            from_commit = sorted_commits[i]
            to_commit = sorted_commits[i + 1]
            from_node = commit_nodes[from_commit.id]
            to_node = commit_nodes[to_commit.id]
            branch_color = branch_colors.get(to_commit.branch, colors[0])
            lines.append(f'  {from_node} -> {to_node} [color="{branch_color}"];')
    
    lines.append('')
    
    # Legend
    lines.append('  subgraph cluster_legend {')
    lines.append('    label="Branches";')
    lines.append('    style=dashed;')
    for branch, color in sorted(branch_colors.items()):
        lines.append(f'    "{branch}" [fillcolor="{color}", style="rounded,filled"];')
    lines.append('  }')
    
    lines.append('}')
    
    dot_content = '\n'.join(lines)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dot_content)
        logger.info(f"Graphviz DOT saved to {output_path}")
    
    return dot_content


def generate_commit_graph(
    branch: Optional[str] = None,
    task_id: Optional[str] = None,
    format: str = "text",
    output_path: Optional[Path] = None,
    max_commits: int = 50,
) -> str:
    """
    Generate commit graph visualization.
    
    Args:
        branch: Optional branch filter
        task_id: Optional task ID filter
        format: Output format ('text' or 'dot')
        output_path: Optional path to save output
        max_commits: Maximum commits to include (for text format)
        
    Returns:
        Graph visualization string
    """
    tracker = get_commit_tracker()
    
    # Get commits
    if task_id:
        commits = tracker.get_commits_for_task(task_id, branch)
    elif branch:
        commits = tracker.get_commits_for_branch(branch)
    else:
        # Get all commits
        commits = tracker._load_commits()
    
    if format.lower() == "dot":
        return generate_graphviz_dot(commits, output_path)
    else:
        return generate_text_graph(commits, max_commits)


def get_branch_timeline(branch: str) -> list[dict[str, Any]]:
    """
    Get timeline of commits for a branch.
    
    Args:
        branch: Branch name
        
    Returns:
        List of commit dictionaries with timeline information
    """
    tracker = get_commit_tracker()
    commits = tracker.get_commits_for_branch(branch)
    
    timeline = []
    for commit in commits:
        timeline.append({
            "commit_id": commit.id,
            "task_id": commit.task_id,
            "message": commit.message,
            "timestamp": commit.timestamp.isoformat(),
            "author": commit.author,
            "type": _classify_commit_type(commit),
        })
    
    return timeline


def _classify_commit_type(commit: TaskCommit) -> str:
    """Classify commit type from message."""
    message = commit.message.lower()
    if "create" in message:
        return "create"
    elif "update" in message:
        return "update"
    elif "delete" in message:
        return "delete"
    elif "merge" in message:
        return "merge"
    elif "status" in message:
        return "status_change"
    else:
        return "other"


__all__ = [
    "generate_text_graph",
    "generate_graphviz_dot",
    "generate_commit_graph",
    "get_branch_timeline",
]
