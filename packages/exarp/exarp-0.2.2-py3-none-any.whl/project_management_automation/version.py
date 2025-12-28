"""
Dynamic versioning for Exarp.

Version formats (PEP 440 compliant):
- Release:  X.Y.Z                    (from git tag vX.Y.Z)
- Dev:      X.Y.Z.devEPOCH+gCOMMIT   (dev version with epoch and commit)
- Nightly:  X.Y.Z.postEPOCH          (nightly/CI builds)

Version is determined by:
1. Git tag (if on a tag): exact version from tag
2. Environment variable EXARP_VERSION_TYPE: 'release', 'dev', 'nightly'
3. Default: dev version with epoch timestamp

Usage:
    from project_management_automation.version import __version__, get_version_info
    print(__version__)  # Dynamic version string
"""

import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Base version - increment this for releases
# Format: MAJOR.MINOR.PATCH
BASE_VERSION = "0.2.2"


def get_epoch() -> int:
    """Get current Unix epoch timestamp."""
    return int(time.time())


def get_git_info() -> dict[str, Optional[str]]:
    """
    Get git information for versioning.

    Returns:
        Dict with keys: tag, commit, branch, dirty
    """
    info = {
        "tag": None,
        "commit": None,
        "branch": None,
        "dirty": False,
        "commits_since_tag": 0,
    }

    try:
        # Check if we're in a git repo
        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return info

        # Get current commit
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            info["commit"] = result.stdout.strip()

        # Get current branch
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            info["branch"] = result.stdout.strip() or "HEAD"

        # Check if dirty (uncommitted changes)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            info["dirty"] = bool(result.stdout.strip())

        # Get tag on current commit (if any)
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match", "HEAD"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            info["tag"] = result.stdout.strip()

        # Get commits since last tag
        result = subprocess.run(["git", "describe", "--tags", "--long"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Format: v0.1.14-5-g1234567
            match = re.match(r"v?(\d+\.\d+\.\d+)-(\d+)-g([a-f0-9]+)", result.stdout.strip())
            if match:
                info["commits_since_tag"] = int(match.group(2))

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return info


def parse_tag_version(tag: str) -> Optional[str]:
    """
    Parse version from git tag.

    Args:
        tag: Git tag (e.g., 'v0.1.15', '0.1.15')

    Returns:
        Version string or None if not a version tag
    """
    if not tag:
        return None

    # Strip 'v' prefix if present
    version = tag.lstrip("v")

    # Validate it's a proper version
    if re.match(r"^\d+\.\d+\.\d+$", version):
        return version

    return None


def get_version_type() -> str:
    """
    Determine version type from environment or git state.

    Returns:
        'release', 'dev', or 'nightly'
    """
    # Check environment variable first
    env_type = os.environ.get("EXARP_VERSION_TYPE", "").lower()
    if env_type in ("release", "dev", "nightly"):
        return env_type

    # Check if we're on a release tag
    git_info = get_git_info()
    if git_info["tag"] and not git_info["dirty"]:
        tag_version = parse_tag_version(git_info["tag"])
        if tag_version:
            return "release"

    # Check for CI/CD environment
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        # Nightly if scheduled, dev otherwise
        if os.environ.get("GITHUB_EVENT_NAME") == "schedule":
            return "nightly"

    # Default to dev
    return "dev"


def get_version(version_type: Optional[str] = None) -> str:
    """
    Get the full version string.

    Args:
        version_type: Override version type ('release', 'dev', 'nightly')

    Returns:
        Full version string (PEP 440 compliant)
    """
    if version_type is None:
        version_type = get_version_type()

    git_info = get_git_info()

    # Release version: use tag or base version
    if version_type == "release":
        if git_info["tag"]:
            tag_version = parse_tag_version(git_info["tag"])
            if tag_version:
                return tag_version
        return BASE_VERSION

    # Dev version: base.devEPOCH
    if version_type == "dev":
        epoch = get_epoch()
        version = f"{BASE_VERSION}.dev{epoch}"

        # Add commit hash if available
        if git_info["commit"]:
            version = f"{version}+g{git_info['commit']}"

        # Add dirty marker
        if git_info["dirty"]:
            version = f"{version}.dirty" if "+" in version else f"{version}+dirty"

        return version

    # Nightly version: base.nEPOCH (using 'n' for nightly, PEP 440 post-release)
    if version_type == "nightly":
        epoch = get_epoch()
        # Use .post for nightly to be PEP 440 compliant
        return f"{BASE_VERSION}.post{epoch}"

    return BASE_VERSION


def get_version_info() -> dict[str, any]:
    """
    Get comprehensive version information.

    Returns:
        Dict with version details
    """
    git_info = get_git_info()
    version_type = get_version_type()

    return {
        "version": get_version(version_type),
        "base_version": BASE_VERSION,
        "version_type": version_type,
        "epoch": get_epoch(),
        "timestamp": datetime.now().isoformat(),
        "git": {
            "tag": git_info["tag"],
            "commit": git_info["commit"],
            "branch": git_info["branch"],
            "dirty": git_info["dirty"],
            "commits_since_tag": git_info["commits_since_tag"],
        },
    }


def bump_version(part: str = "patch") -> str:
    """
    Bump the base version.

    Args:
        part: 'major', 'minor', or 'patch'

    Returns:
        New version string
    """
    major, minor, patch = map(int, BASE_VERSION.split("."))

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_base_version(new_version: str) -> bool:
    """
    Update BASE_VERSION in this file.

    Args:
        new_version: New version string (e.g., '0.1.16')

    Returns:
        True if successful
    """
    version_file = Path(__file__)
    content = version_file.read_text()

    # Replace BASE_VERSION with new version
    new_content = re.sub(r'BASE_VERSION = "0.2.1"]*"', f'BASE_VERSION = "0.2.1"', content)

    if new_content != content:
        version_file.write_text(new_content)
        return True

    return False


def generate_release_notes(since_tag: Optional[str] = None) -> str:
    """
    Generate release notes from git commits since the last tag.

    Args:
        since_tag: Tag to start from (default: most recent tag)

    Returns:
        Markdown-formatted release notes
    """
    notes_lines = []

    try:
        # Get the last tag if not specified
        if not since_tag:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                since_tag = result.stdout.strip()

        # Get commits since tag (or all commits if no tag)
        if since_tag:
            cmd = ["git", "log", f"{since_tag}..HEAD", "--pretty=format:%s|%h|%an"]
        else:
            cmd = ["git", "log", "--pretty=format:%s|%h|%an"]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0 or not result.stdout.strip():
            return f"## What's Changed\n\nNo changes since {since_tag or 'initial commit'}.\n"

        # Categorize commits by conventional commit type
        categories = {
            "feat": ("✨ Features", []),
            "fix": ("🐛 Bug Fixes", []),
            "docs": ("📚 Documentation", []),
            "refactor": ("♻️ Refactoring", []),
            "perf": ("⚡ Performance", []),
            "test": ("🧪 Tests", []),
            "chore": ("🔧 Maintenance", []),
            "ci": ("🔄 CI/CD", []),
            "style": ("💄 Style", []),
            "build": ("📦 Build", []),
            "other": ("📝 Other Changes", []),
        }

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 2:
                message, commit_hash = parts[0], parts[1]
                author = parts[2] if len(parts) > 2 else "Unknown"

                # Parse conventional commit format
                categorized = False
                for prefix in categories:
                    if prefix == "other":
                        continue
                    # Match: feat:, feat(scope):, etc.
                    if re.match(rf"^{prefix}(\(.+\))?:", message, re.IGNORECASE):
                        # Clean up the message
                        clean_msg = re.sub(rf"^{prefix}(\(.+\))?:\s*", "", message, flags=re.IGNORECASE)
                        categories[prefix][1].append((clean_msg, commit_hash, author))
                        categorized = True
                        break

                if not categorized:
                    categories["other"][1].append((message, commit_hash, author))

        # Build release notes
        notes_lines.append("## What's Changed\n")

        for _key, (title, commits) in categories.items():
            if commits:
                notes_lines.append(f"### {title}\n")
                for msg, hash_, author in commits:
                    notes_lines.append(f"- {msg} ({hash_}) @{author}")
                notes_lines.append("")

        # Add comparison link placeholder
        if since_tag:
            notes_lines.append(f"\n**Full Changelog**: `{since_tag}...v{BASE_VERSION}`")

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        return f"## What's Changed\n\nError generating release notes: {e}\n"

    return "\n".join(notes_lines)


def create_release(
    version: Optional[str] = None,
    bump: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, any]:
    """
    Create a release: bump version, generate notes, create tag.

    Args:
        version: Explicit version to release (default: current BASE_VERSION)
        bump: Bump type before release ('major', 'minor', 'patch')
        dry_run: If True, show what would happen without making changes

    Returns:
        Dict with release info
    """
    result = {
        "success": False,
        "version": None,
        "tag": None,
        "release_notes": None,
        "actions": [],
    }

    try:
        # Determine version
        if bump:
            new_version = bump_version(bump)
            if not dry_run:
                update_base_version(new_version)
                result["actions"].append(f"Bumped version: {BASE_VERSION} -> {new_version}")
            else:
                result["actions"].append(f"Would bump version: {BASE_VERSION} -> {new_version}")
            release_version = new_version
        else:
            release_version = version or BASE_VERSION

        result["version"] = release_version
        result["tag"] = f"v{release_version}"

        # Generate release notes
        release_notes = generate_release_notes()
        result["release_notes"] = release_notes

        # Write release notes to file
        notes_file = Path(__file__).parent.parent / "RELEASE_NOTES.md"
        if not dry_run:
            notes_file.write_text(f"# Release v{release_version}\n\n{release_notes}")
            result["actions"].append(f"Wrote release notes to {notes_file}")
        else:
            result["actions"].append(f"Would write release notes to {notes_file}")

        # Create git tag
        if not dry_run:
            # Stage and commit version changes
            subprocess.run(["git", "add", "-A"], capture_output=True, timeout=10)
            subprocess.run(
                ["git", "commit", "-m", f"chore: Release v{release_version}"],
                capture_output=True,
                timeout=10,
            )
            result["actions"].append("Committed release changes")

            # Create annotated tag
            tag_result = subprocess.run(
                ["git", "tag", "-a", f"v{release_version}", "-m", f"Release v{release_version}"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if tag_result.returncode == 0:
                result["actions"].append(f"Created tag: v{release_version}")
            else:
                result["actions"].append(f"Tag creation failed: {tag_result.stderr}")
                return result
        else:
            result["actions"].append(f"Would commit and create tag: v{release_version}")

        result["success"] = True

    except Exception as e:
        result["actions"].append(f"Error: {e}")

    return result


# Module-level version (evaluated at import time)
__version__ = get_version()


# CLI interface
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Exarp version utility")
    parser.add_argument("--type", choices=["release", "dev", "nightly"], help="Override version type")
    parser.add_argument("--info", action="store_true", help="Show detailed version info as JSON")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], help="Bump and update BASE_VERSION")
    parser.add_argument("--base", action="store_true", help="Show only base version")
    parser.add_argument("--release-notes", action="store_true", help="Generate release notes from git history")
    parser.add_argument("--release", action="store_true", help="Create a release (bump, notes, tag)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")

    args = parser.parse_args()

    if args.release:
        result = create_release(bump=args.bump, dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    elif args.release_notes:
        print(generate_release_notes())
    elif args.bump and not args.release:
        new_ver = bump_version(args.bump)
        if args.dry_run:
            print(f"Would update BASE_VERSION: {BASE_VERSION} -> {new_ver}")
        elif update_base_version(new_ver):
            print(f"Updated BASE_VERSION: {BASE_VERSION} -> {new_ver}")
        else:
            print("Failed to update BASE_VERSION")
    elif args.info:
        print(json.dumps(get_version_info(), indent=2))
    elif args.base:
        print(BASE_VERSION)
    else:
        print(get_version(args.type))
