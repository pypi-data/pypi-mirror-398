"""Utility functions for detecting and integrating with Codex."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List


def find_codex_sessions_for_project(
    project_path: Path,
    days_back: int = 7
) -> List[Path]:
    """
    Find Codex sessions for a given project path.

    Codex stores sessions in ~/.codex/sessions/{YYYY}/{MM}/{DD}/
    with all projects mixed together. We need to search by date
    and filter by the 'cwd' field in session metadata.

    Args:
        project_path: The absolute path to the project
        days_back: Number of days to look back (default: 7)

    Returns:
        List of session file paths that match the project, sorted by timestamp (newest first)
    """
    codex_sessions_base = Path.home() / ".codex" / "sessions"

    if not codex_sessions_base.exists():
        return []

    # Normalize project path for comparison
    abs_project_path = str(project_path.resolve())

    matching_sessions = []

    # Search through recent days
    for days_ago in range(days_back + 1):
        target_date = datetime.now() - timedelta(days=days_ago)
        date_path = codex_sessions_base / str(target_date.year) / f"{target_date.month:02d}" / f"{target_date.day:02d}"

        if not date_path.exists():
            continue

        # Check all session files in this date directory
        for session_file in date_path.glob("rollout-*.jsonl"):
            try:
                # Read first line to get session metadata
                with open(session_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if first_line:
                        data = json.loads(first_line)
                        if data.get('type') == 'session_meta':
                            session_cwd = data.get('payload', {}).get('cwd', '')
                            # Match the project path
                            if session_cwd == abs_project_path:
                                matching_sessions.append(session_file)
            except (json.JSONDecodeError, IOError):
                # Skip malformed or unreadable files
                continue

    # Sort by modification time, newest first
    matching_sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    return matching_sessions


def get_latest_codex_session(project_path: Path, days_back: int = 7) -> Optional[Path]:
    """
    Get the most recent Codex session for a given project.

    Args:
        project_path: The absolute path to the project
        days_back: Number of days to look back (default: 7)

    Returns:
        Path to the most recent session file, or None if not found
    """
    sessions = find_codex_sessions_for_project(project_path, days_back)
    return sessions[0] if sessions else None


def get_codex_sessions_dir() -> Optional[Path]:
    """
    Get the Codex sessions base directory if it exists.

    Returns:
        Path to ~/.codex/sessions if it exists, None otherwise
    """
    codex_sessions = Path.home() / ".codex" / "sessions"
    return codex_sessions if codex_sessions.exists() else None


def auto_detect_codex_sessions(
    project_path: Path,
    fallback_path: Optional[str] = None,
    days_back: int = 7
) -> Optional[Path]:
    """
    Auto-detect the most recent Codex session for a project.

    Priority:
    1. REALIGN_LOCAL_HISTORY_PATH environment variable (disables auto-detection)
    2. Most recent Codex session matching project path
    3. fallback_path parameter (if provided)
    4. Default: None (let caller decide fallback)

    Args:
        project_path: The absolute path to the project
        fallback_path: Optional fallback path if auto-detection fails
        days_back: Number of days to look back for sessions (default: 7)

    Returns:
        Path to use for session history, or None if not found
    """
    # Check environment variable first (highest priority, disables auto-detection)
    env_path = os.getenv("REALIGN_LOCAL_HISTORY_PATH")
    if env_path:
        return Path(os.path.expanduser(env_path))

    # Try to find the latest Codex session for this project
    latest_session = get_latest_codex_session(project_path, days_back)
    if latest_session:
        return latest_session

    # Use fallback if provided
    if fallback_path:
        return Path(os.path.expanduser(fallback_path))

    return None
