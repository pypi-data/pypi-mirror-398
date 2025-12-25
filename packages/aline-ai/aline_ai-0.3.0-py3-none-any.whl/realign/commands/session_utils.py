"""Shared helpers for working with session files recorded in commits."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List


def find_session_paths_for_commit(repo_root: Path, commit_hash: str, git_dir: Path = None) -> List[str]:
    """
    Return relative session file paths tracked in a given commit.

    Args:
        repo_root: Root directory (used if git_dir not provided)
        commit_hash: Commit hash to query
        git_dir: Optional git directory to use (for .aline repos)

    Returns:
        List of relative session file paths
    """
    try:
        cwd = git_dir if git_dir else repo_root
        result = subprocess.run(
            ["git", "show", "--pretty=format:", "--name-only", commit_hash],
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError:
        return []

    paths = []
    for line in result.stdout.splitlines():
        candidate = line.strip()
        # Support both .realign/sessions/ and sessions/ patterns
        if (candidate.startswith(".realign/sessions/") or candidate.startswith("sessions/")) and candidate.endswith(".jsonl"):
            paths.append(candidate)
    return paths


def detect_original_session_location(session_filename: str, project_root: Path, commit_timestamp: int) -> Path:
    """
    Detect the original location where a session file should be restored.

    Args:
        session_filename: Name of session file (e.g., "huminhao_claude_637f35af.jsonl" or "uuid.jsonl")
        project_root: Root directory of the user's project
        commit_timestamp: Unix timestamp of the commit

    Returns:
        Path where session should be restored, or None if cannot detect
    """
    from datetime import datetime
    import re

    # Check if this is a UUID format (Claude Code original format)
    # UUID pattern: 8-4-4-4-12 hex digits
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$'
    if re.match(uuid_pattern, session_filename, re.IGNORECASE):
        # This is a UUID format session file, likely from Claude Code
        try:
            from ..claude_detector import find_claude_sessions_dir
            claude_dir = find_claude_sessions_dir(project_root)
            if claude_dir and claude_dir.exists():
                return claude_dir / session_filename
        except Exception:
            pass
        # Fall through to return None if Claude dir not found

    else:
        # Parse filename to extract agent type
        # Expected format: {user}_{agent}_{hash}.jsonl
        parts = session_filename.replace('.jsonl', '').split('_')

        if len(parts) >= 3:
            agent_type = parts[1].lower()  # e.g., "claude", "codex"

            if agent_type == "claude":
                # Try to find Claude sessions directory
                try:
                    from ..claude_detector import find_claude_sessions_dir
                    claude_dir = find_claude_sessions_dir(project_root)
                    if claude_dir and claude_dir.exists():
                        return claude_dir / session_filename
                except Exception:
                    pass

            elif agent_type == "codex":
                # Construct Codex path from timestamp
                try:
                    dt = datetime.fromtimestamp(int(commit_timestamp))
                    codex_dir = Path.home() / ".codex" / "sessions" / dt.strftime("%Y") / dt.strftime("%m") / dt.strftime("%d")
                    if codex_dir.exists():
                        # Codex uses rollout-* naming, but we'll use our renamed format
                        return codex_dir / session_filename
                except Exception:
                    pass

    # Fall back to None if cannot detect
    return None


def restore_session_from_commit(tracker, commit_hash: str, session_rel_path: str, dest_path: Path) -> bool:
    """
    Restore a session file from a commit to its original location.

    Args:
        tracker: ReAlignGitTracker instance
        commit_hash: Commit hash to restore from
        session_rel_path: Relative path in git (e.g., "sessions/user_claude_hash.jsonl")
        dest_path: Destination path to restore to

    Returns:
        True if successful, False otherwise
    """
    import json
    from datetime import datetime

    try:
        # Extract session content from commit
        result = subprocess.run(
            ["git", "show", f"{commit_hash}:{session_rel_path}"],
            cwd=tracker.realign_dir,
            capture_output=True,
            check=False
        )

        if result.returncode != 0:
            return False

        content = result.stdout.decode('utf-8', errors='replace')

        # Validate JSONL format (basic check)
        try:
            for line in content.splitlines():
                line = line.strip()
                if line:  # Skip empty lines
                    json.loads(line)  # Will raise if invalid JSON
        except json.JSONDecodeError:
            # Invalid JSONL, create .corrupted file
            corrupted_path = dest_path.with_suffix('.jsonl.corrupted')
            corrupted_path.write_text(content, encoding='utf-8')
            return False

        # If destination exists, create backup
        if dest_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_name = dest_path.stem + f".backup-{timestamp}" + dest_path.suffix
            backup_path = dest_path.parent / backup_name
            dest_path.rename(backup_path)

        # Create parent directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Write session content
        dest_path.write_text(content, encoding='utf-8')

        return True

    except Exception:
        return False
