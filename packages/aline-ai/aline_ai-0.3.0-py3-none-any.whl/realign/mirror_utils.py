"""Shared utilities for mirroring project files to shadow git repository."""

import os
from pathlib import Path
from typing import List, Set, Optional
import fnmatch


# File size limit for mirroring (50MB)
# Files larger than this will be skipped to prevent performance issues
MAX_MIRROR_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


def get_gitignore_patterns(project_path: Path) -> Set[str]:
    """
    Load .gitignore patterns from project directory.

    Args:
        project_path: Path to the project directory

    Returns:
        Set of gitignore patterns
    """
    patterns = set()
    gitignore_path = project_path / ".gitignore"

    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    patterns.add(line)
    except Exception:
        pass  # Silently ignore errors

    return patterns


def is_file_too_large(file_path: Path, max_size: int = MAX_MIRROR_FILE_SIZE) -> bool:
    """
    Check if a file exceeds the maximum size limit for mirroring.

    Args:
        file_path: Path to the file to check
        max_size: Maximum file size in bytes (default: 50MB)

    Returns:
        True if file is too large, False otherwise
    """
    try:
        file_size = file_path.stat().st_size
        return file_size > max_size
    except (OSError, IOError):
        # If we can't get file size (permission error, file doesn't exist, etc.),
        # skip the file to be safe
        return True


def should_ignore_file(file_path: Path, project_path: Path, gitignore_patterns: Set[str]) -> bool:
    """
    Check if a file should be ignored based on .gitignore patterns.

    Args:
        file_path: Absolute path to the file
        project_path: Root path of the project
        gitignore_patterns: Set of gitignore patterns

    Returns:
        True if file should be ignored, False otherwise
    """
    try:
        rel_path = file_path.relative_to(project_path)
        rel_path_str = str(rel_path)

        # Check each pattern
        for pattern in gitignore_patterns:
            # Simple pattern matching (basic implementation)
            if pattern.endswith('/'):
                # Directory pattern
                if rel_path_str.startswith(pattern.rstrip('/')):
                    return True
            elif '*' in pattern:
                # Wildcard pattern - simple implementation
                if fnmatch.fnmatch(rel_path_str, pattern):
                    return True
            else:
                # Exact match or prefix match
                if rel_path_str == pattern or rel_path_str.startswith(pattern + '/'):
                    return True

        return False

    except Exception:
        return False


def collect_project_files(project_path: Path, logger=None) -> List[Path]:
    """
    Collect all project files that should be mirrored.

    This is the core logic shared between the mirror command and watcher.
    It walks through the project directory, respects .gitignore patterns,
    and excludes .git, .aline, and .realign directories.

    Args:
        project_path: Root path of the project
        logger: Optional logger for debug messages

    Returns:
        List of absolute paths to files that should be mirrored
    """
    all_files = []
    gitignore_patterns = get_gitignore_patterns(project_path)

    # Walk through project directory
    for root, dirs, files in os.walk(project_path):
        # Skip .git directory
        if '.git' in dirs:
            dirs.remove('.git')

        # Skip .aline and .realign directories
        if '.aline' in dirs:
            dirs.remove('.aline')
        if '.realign' in dirs:
            dirs.remove('.realign')

        for file in files:
            file_path = Path(root) / file

            # Check if file should be ignored
            if should_ignore_file(file_path, project_path, gitignore_patterns):
                continue

            # Check file size limit (50MB)
            if is_file_too_large(file_path):
                if logger:
                    try:
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        logger.warning(
                            f"Skipping large file: {file_path.relative_to(project_path)} "
                            f"({file_size_mb:.1f}MB > 50MB limit)"
                        )
                    except (OSError, IOError):
                        logger.warning(
                            f"Skipping large file: {file_path.relative_to(project_path)} "
                            f"(unable to determine size)"
                        )
                continue

            # Add all non-ignored files
            if file_path.exists():
                all_files.append(file_path)
                if logger:
                    logger.debug(f"Found project file: {file_path.relative_to(project_path)}")

    if logger:
        logger.info(f"Found {len(all_files)} project file(s) to mirror")

    return all_files


def get_files_at_commit(tracker, commit_hash: str) -> List[Path]:
    """
    Get list of files that existed in the mirror at a specific commit.

    Args:
        tracker: ReAlignGitTracker instance
        commit_hash: Commit hash to query

    Returns:
        List of relative paths (from project root) that existed at that commit
    """
    try:
        import subprocess
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit_hash, "mirror/"],
            cwd=tracker.realign_dir,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return []

        files = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("mirror/"):
                # Strip "mirror/" prefix to get relative path from project root
                rel_path = line[7:]  # len("mirror/") == 7
                files.append(Path(rel_path))

        return files

    except Exception:
        return []


def reverse_mirror_file(source_content: bytes, dest_path: Path, project_root: Path) -> bool:
    """
    Write content to a destination file, creating parent directories as needed.

    Args:
        source_content: File content as bytes
        dest_path: Absolute destination path
        project_root: Project root directory (for logging)

    Returns:
        True on success, False on failure
    """
    try:
        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        dest_path.write_bytes(source_content)

        return True

    except Exception:
        return False


def reverse_mirror_from_commit(
    tracker,
    commit_hash: str,
    project_root: Path,
    gitignore_patterns: Set[str],
    logger=None
):
    """
    Restore files from mirror at a specific commit to the user's project directory.

    Args:
        tracker: ReAlignGitTracker instance
        commit_hash: Commit hash to restore from
        project_root: Root directory of the user's project
        gitignore_patterns: Set of .gitignore patterns
        logger: Optional logger for messages

    Returns:
        Dictionary with keys: 'restored', 'skipped', 'failed' (lists of file paths)
    """
    import subprocess

    result = {
        'restored': [],
        'skipped': [],
        'failed': []
    }

    # Get list of files at target commit
    files_at_commit = get_files_at_commit(tracker, commit_hash)

    if logger:
        logger.info(f"Found {len(files_at_commit)} file(s) in mirror at commit {commit_hash}")

    for rel_path in files_at_commit:
        dest_path = project_root / rel_path

        # Check if should be ignored
        if should_ignore_file(dest_path, project_root, gitignore_patterns):
            if logger:
                logger.debug(f"Skipping ignored file: {rel_path}")
            result['skipped'].append(str(rel_path))
            continue

        # Extract content from git
        try:
            git_path = f"mirror/{rel_path}"
            extract_result = subprocess.run(
                ["git", "show", f"{commit_hash}:{git_path}"],
                cwd=tracker.realign_dir,
                capture_output=True,
                check=False
            )

            if extract_result.returncode != 0:
                if logger:
                    logger.warning(f"Failed to extract {rel_path} from commit")
                result['failed'].append(str(rel_path))
                continue

            content = extract_result.stdout

            # Check size limit
            if len(content) > MAX_MIRROR_FILE_SIZE:
                if logger:
                    size_mb = len(content) / (1024 * 1024)
                    logger.warning(
                        f"Skipping large file: {rel_path} ({size_mb:.1f}MB > 50MB limit)"
                    )
                result['skipped'].append(str(rel_path))
                continue

            # Write to destination
            if reverse_mirror_file(content, dest_path, project_root):
                result['restored'].append(str(rel_path))
                if logger:
                    logger.debug(f"Restored: {rel_path}")
            else:
                result['failed'].append(str(rel_path))
                if logger:
                    logger.warning(f"Failed to write: {rel_path}")

        except Exception as e:
            if logger:
                logger.warning(f"Error restoring {rel_path}: {e}")
            result['failed'].append(str(rel_path))

    if logger:
        logger.info(
            f"Reverse mirror complete: {len(result['restored'])} restored, "
            f"{len(result['skipped'])} skipped, {len(result['failed'])} failed"
        )

    return result
