#!/usr/bin/env python3
"""
Hide command - Redact sensitive commits before pushing.

This allows users to hide (redact) specific commits by rewriting git history.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Set

from .review import get_unpushed_commits, UnpushedCommit
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.hide', 'hide.log')


def parse_commit_indices(indices_str: str) -> List[int]:
    """
    Parse user input of commit indices.

    Supports:
    - Single: "3" -> [3]
    - Multiple: "1,3,5" -> [1, 3, 5]
    - Range: "2-4" -> [2, 3, 4]
    - Combined: "1,3,5-7" -> [1, 3, 5, 6, 7]

    Args:
        indices_str: User input string

    Returns:
        Sorted list of unique indices

    Raises:
        ValueError: If input format is invalid
    """
    if not indices_str or not indices_str.strip():
        raise ValueError("Empty input")

    result: Set[int] = set()

    for part in indices_str.split(','):
        part = part.strip()

        if not part:
            continue

        if '-' in part:
            # Range: "2-4"
            range_parts = part.split('-', 1)
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: {part}")

            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
            except ValueError:
                raise ValueError(f"Invalid range format: {part}")

            if start > end:
                raise ValueError(f"Invalid range (start > end): {part}")

            result.update(range(start, end + 1))
        else:
            # Single number
            try:
                num = int(part)
            except ValueError:
                raise ValueError(f"Invalid number: {part}")

            if num < 1:
                raise ValueError(f"Index must be >= 1: {num}")

            result.add(num)

    return sorted(result)


def perform_safety_checks(repo_root: Path) -> Tuple[bool, str]:
    """
    Perform safety checks before rewriting git history.

    Checks:
    1. Working directory is clean
    2. Not in detached HEAD state
    3. Has unpushed commits

    Args:
        repo_root: Path to repository root

    Returns:
        Tuple of (success, message)
    """
    logger.info("Performing safety checks")

    # 1. Check working directory is clean
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if status_result.stdout.strip():
        return False, "Working directory is not clean. Please commit or stash your changes first."

    # 2. Check not in detached HEAD
    branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    branch = branch_result.stdout.strip()
    if branch == "HEAD":
        return False, "You are in detached HEAD state. Please checkout a branch first."

    logger.info(f"Current branch: {branch}")

    # 3. Check has unpushed commits (will be checked by caller)

    logger.info("Safety checks passed")
    return True, "OK"


def confirm_hide_operation(
    commits_to_hide: List[UnpushedCommit],
    all_commits: List[UnpushedCommit]
) -> bool:
    """
    Show warning and ask user for confirmation.

    Args:
        commits_to_hide: Commits to be hidden
        all_commits: All unpushed commits

    Returns:
        True if user confirms, False otherwise
    """
    print("\n⚠️  WARNING: This will rewrite git history!\n")
    print("What will happen:")
    print("  • Commit messages will be redacted")
    print("  • Session content added in these commits will be redacted")
    print("  • All later commits will be rebased\n")

    print(f"Commits to hide ({len(commits_to_hide)}):")
    for commit in commits_to_hide:
        print(f"  [{commit.index}] {commit.hash} - {commit.message}")

    print()

    # Calculate affected commits
    # Index 1 is HEAD (newest), higher index = older commits
    # We need to rewrite from HEAD (index 1) down to the oldest commit being hidden
    # For example: hide index 3 means rewrite commits 1, 2, 3 (3 commits total)
    max_hide_index = max(c.index for c in commits_to_hide)
    affected_count = max_hide_index  # All commits from 1 to max_hide_index

    print(f"⚠️  This will rewrite {affected_count} commit(s) in total.\n")

    response = input("Proceed? [y/N] ").strip().lower()

    return response == 'y'


def redact_session_lines(
    session_file: Path,
    line_ranges: List[Tuple[int, int]]
) -> None:
    """
    Redact specific line ranges in a session file.

    Strategy C: Preserve JSON structure, clear content

    Result format:
    {
        "type": "user",  // Preserved
        "message": {"content": "[REDACTED]"},  // Cleared
        "redacted": true,
        "redacted_at": "2025-11-22T19:30:00"
    }

    Args:
        session_file: Path to session file
        line_ranges: List of (start_line, end_line) tuples (1-based, inclusive)
    """
    logger.info(f"Redacting session file: {session_file}")
    logger.debug(f"Line ranges to redact: {line_ranges}")

    if not session_file.exists():
        logger.warning(f"Session file not found: {session_file}")
        return

    # Read file
    with open(session_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Collect all line indices to redact (convert to 0-based)
    lines_to_redact: Set[int] = set()
    for start, end in line_ranges:
        lines_to_redact.update(range(start - 1, end))  # Convert to 0-based

    logger.debug(f"Total lines to redact: {len(lines_to_redact)}")

    # Redact lines
    redacted_count = 0
    for i in lines_to_redact:
        if i >= len(lines):
            logger.warning(f"Line index {i} out of range (file has {len(lines)} lines)")
            continue

        # Try to preserve JSON structure
        try:
            data = json.loads(lines[i])

            # Create redacted object preserving type
            redacted = {
                "type": data.get("type", "redacted"),
                "message": {"content": "[REDACTED]"},
                "redacted": True,
                "redacted_at": datetime.now().isoformat()
            }

            lines[i] = json.dumps(redacted, ensure_ascii=False) + '\n'
            redacted_count += 1

        except json.JSONDecodeError:
            # If not valid JSON, replace entire line
            logger.debug(f"Line {i+1} is not valid JSON, replacing entire line")
            lines[i] = '{"type": "redacted", "content": "[REDACTED]"}\n'
            redacted_count += 1

    logger.info(f"Redacted {redacted_count} line(s) in {session_file}")

    # Write back
    with open(session_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def redact_commit_message(original_message: str) -> str:
    """
    Redact commit message.

    Supports both new format (with LLM-Summary) and old format (with Request:).

    New format becomes:
        [REDACTED]

        --- LLM-Summary (claude-3-5-haiku) ---
        * [Claude] [REDACTED - Content hidden by user on timestamp]

        Agent-Redacted: true

    Old format becomes:
        [REDACTED]

        ---
        Session: xxx | Turn: #2 | Model: gpt-3.5-turbo
        Request: [REDACTED - Content hidden by user on timestamp]

    Args:
        original_message: Original commit message

    Returns:
        Redacted commit message
    """
    lines = original_message.split('\n')
    redacted_lines = []
    in_summary = False
    found_session_metadata = False

    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    for line in lines:
        # First line: replace with [REDACTED]
        if not redacted_lines:
            redacted_lines.append("[REDACTED]")
            continue

        # LLM Summary section (new format)
        if '--- LLM-Summary' in line:
            in_summary = True
            # Add blank line before summary if we haven't added session metadata
            if not found_session_metadata:
                redacted_lines.append('')
            redacted_lines.append(line)
            continue

        if in_summary:
            if line.strip().startswith('*'):
                # Extract agent prefix: "* [Claude] Text" -> "* [Claude]"
                if ']' in line:
                    prefix = line.split(']')[0] + ']'
                else:
                    prefix = '*'

                redacted_lines.append(
                    f"{prefix} [REDACTED - Content hidden by user on {timestamp}]"
                )

            elif line.strip().startswith('---') or line.strip().startswith('Agent-'):
                # End of summary section
                in_summary = False
                redacted_lines.append(line)

            else:
                redacted_lines.append(line)

        else:
            # Check for session metadata line (Session: xxx | Turn: xxx | Model: xxx)
            if line.strip().startswith('Session:') or line.strip().startswith('---'):
                found_session_metadata = True
                # Add blank line before session metadata if not already present
                if redacted_lines and redacted_lines[-1].strip() != '':
                    redacted_lines.append('')
                redacted_lines.append(line)
            # Old format: Redact "Request:" line
            elif line.strip().startswith('Request:'):
                redacted_lines.append(f"Request: [REDACTED - Content hidden by user on {timestamp}]")
            # Update Agent-Redacted flag (new format)
            elif line.strip().startswith('Agent-Redacted:'):
                redacted_lines.append('Agent-Redacted: true')
            # Skip the descriptive summary paragraph in old format
            elif found_session_metadata or line.strip() == '':
                # Keep blank lines and lines after session metadata
                if line.strip() == '' or line.strip().startswith('Session:') or line.strip().startswith('Request:') or line.strip().startswith('---'):
                    continue  # Will be handled by specific conditions above
                else:
                    continue  # Skip other content between title and session metadata
            else:
                # This is likely descriptive text before session metadata - skip it
                continue

    return '\n'.join(redacted_lines)


def create_backup_ref(repo_root: Path) -> str:
    """
    Create a backup reference before rewriting history.

    This allows users to recover if something goes wrong.

    Args:
        repo_root: Path to repository root

    Returns:
        Backup reference name (e.g., "refs/realign/backup_20251122_193000")
    """
    logger.info("Creating backup reference")

    # Get current commit
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()

    # Create backup ref
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_ref = f"refs/realign/backup_{timestamp}"

    subprocess.run(
        ["git", "update-ref", backup_ref, current_commit],
        cwd=repo_root,
        check=True
    )

    logger.info(f"Created backup reference: {backup_ref}")
    print(f"✓ Created backup: {backup_ref}")
    print(f"  If something goes wrong, you can restore with:")
    print(f"  git reset --hard {backup_ref}\n")

    return backup_ref


def hide_commits_with_filter_repo(
    commits_to_hide: List[UnpushedCommit],
    all_commits: List[UnpushedCommit],
    repo_root: Path
) -> tuple[bool, dict, str]:
    """
    Hide commits using git-filter-repo.

    This rewrites git history to redact commit messages and session content.

    Args:
        commits_to_hide: Commits to hide
        all_commits: All unpushed commits
        repo_root: Path to repository root

    Returns:
        Tuple of (success: bool, content_to_redact: dict, redacted_timestamp: str)
    """
    logger.info(f"Hiding {len(commits_to_hide)} commit(s) using git-filter-repo")

    try:
        # Import git-filter-repo
        try:
            import git_filter_repo as fr
        except ImportError:
            print("\nError: git-filter-repo is not installed.", file=sys.stderr)
            print("Please install it with: pip install git-filter-repo\n", file=sys.stderr)
            logger.error("git-filter-repo not installed")
            return False, {}, ""

        # Build a map of commits to hide
        commits_to_hide_hashes = {c.full_hash for c in commits_to_hide}

        # Build a map of session files to redact for each commit
        redact_map = {}  # {commit_hash: {session_file: [(start, end), ...]}}
        for commit in commits_to_hide:
            redact_map[commit.full_hash] = commit.session_additions

        logger.debug(f"Redact map: {redact_map}")

        # Create callback to modify commits
        def commit_callback(commit, metadata):
            """Callback to modify each commit."""
            commit_hash = commit.original_id.decode('utf-8')

            if commit_hash in commits_to_hide_hashes:
                logger.debug(f"Processing commit to hide: {commit_hash[:8]}")

                # Redact commit message
                original_message = commit.message.decode('utf-8')
                redacted_message = redact_commit_message(original_message)
                commit.message = redacted_message.encode('utf-8')

                logger.debug(f"Redacted commit message for {commit_hash[:8]}")

        def blob_callback(blob, metadata):
            """Callback to modify file contents."""
            # Only process session files
            if not blob.data:
                return

            # Get current commit being processed
            # Note: git-filter-repo doesn't easily expose this,
            # so we use a different approach below

        # Actually, git-filter-repo's Python API is quite complex for this use case.
        # A simpler approach is to use git commands directly.
        logger.warning("git-filter-repo approach is complex, switching to manual git rebase")

        success, content_to_redact, redacted_timestamp = hide_commits_manual(commits_to_hide, all_commits, repo_root)
        return success, content_to_redact, redacted_timestamp

    except Exception as e:
        logger.error(f"Error hiding commits: {e}", exc_info=True)
        print(f"\nError: {e}\n", file=sys.stderr)
        return False, {}, ""


def hide_commits_manual(
    commits_to_hide: List[UnpushedCommit],
    all_commits: List[UnpushedCommit],
    repo_root: Path
) -> bool:
    """
    Hide commits using git filter-branch.

    Strategy:
    1. Collect all original content to redact from the commits being hidden
    2. In tree-filter, search and replace that content in ALL commits
    3. In msg-filter, only redact messages for commits being hidden

    This works because session files are append-only: content added in commit A
    appears at the same location in all subsequent commits.

    Args:
        commits_to_hide: Commits to hide
        all_commits: All unpushed commits
        repo_root: Path to repository root

    Returns:
        Tuple of (success: bool, content_to_redact: dict, redacted_timestamp: str)
    """
    logger.info("Hiding commits using git filter-branch")

    # Build commit hash set
    commits_to_hide_hashes = {c.full_hash for c in commits_to_hide}

    # Collect all content to redact: {session_file: [original_line_content, ...]}
    # We need to get the ORIGINAL content from the repository
    content_to_redact = {}
    for commit in commits_to_hide:
        for session_file, line_ranges in commit.session_additions.items():
            if session_file not in content_to_redact:
                content_to_redact[session_file] = []

            # Read the file at this commit to get original content
            for start_line, end_line in line_ranges:
                # Get file content at this commit
                file_content_result = subprocess.run(
                    ["git", "show", f"{commit.full_hash}:{session_file}"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True
                )

                if file_content_result.returncode == 0:
                    lines = file_content_result.stdout.split('\n')
                    # Collect the actual lines (1-based indexing)
                    for line_num in range(start_line, end_line + 1):
                        if line_num <= len(lines):
                            original_line = lines[line_num - 1]
                            if not original_line:
                                continue

                            # Skip lines that are already redacted
                            # First check the raw string for redacted content
                            if "[REDACTED:" in original_line or "[REDACTED]" in original_line:
                                continue

                            try:
                                data = json.loads(original_line)
                                # Skip if line has redacted flag
                                if data.get("redacted") == True:
                                    continue
                            except json.JSONDecodeError:
                                # If we can't parse it, skip it (likely already corrupted/redacted)
                                continue

                            # Collect unique lines
                            if original_line not in content_to_redact[session_file]:
                                content_to_redact[session_file].append(original_line)

    logger.debug(f"Commits to hide: {list(commits_to_hide_hashes)}")
    logger.debug(f"Content to redact: {content_to_redact}")

    # Find the range to rewrite
    # Index 1 is HEAD (newest), higher index = older commits
    # We need to rewrite from the oldest hidden commit's parent to HEAD
    oldest_commit = max(commits_to_hide, key=lambda c: c.index)

    # Get parent of oldest commit being hidden
    parent_result = subprocess.run(
        ["git", "rev-parse", f"{oldest_commit.full_hash}^"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if parent_result.returncode == 0:
        parent_hash = parent_result.stdout.strip()
        commit_range = f"{parent_hash}..HEAD"
    else:
        # No parent (first commit), rewrite entire history
        commit_range = "HEAD"

    logger.info(f"Rewriting commit range: {commit_range}")

    try:
        # Create a script file for the msg-filter
        msg_filter_script = repo_root / ".git" / "realign_msg_filter.py"
        # Use regular string (not f-string) to avoid escaping issues
        msg_filter_code = '''#!/usr/bin/env python3
import sys
import os

# Read commit hash from environment
commit_hash = os.getenv("GIT_COMMIT")

# Commits to redact
commits_to_redact = ''' + repr(list(commits_to_hide_hashes)) + '''

# Read original message from stdin
original_message = sys.stdin.read()

# CRITICAL FIX: Check if message is already redacted
# This prevents un-redacting previously hidden commits
first_line = original_message.split('\\n')[0] if original_message else ''
if '[REDACTED]' in first_line:
    # Already redacted, preserve as-is
    print(original_message, end='')
elif commit_hash in commits_to_redact:
    # Redact message
    from datetime import datetime
    lines = original_message.split('\\n')
    redacted_lines = []
    in_summary = False
    found_session_metadata = False

    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    for line in lines:
        if not redacted_lines:
            redacted_lines.append("[REDACTED]")
            continue

        if '--- LLM-Summary' in line:
            in_summary = True
            if not found_session_metadata:
                redacted_lines.append('')
            redacted_lines.append(line)
            continue

        if in_summary:
            if line.strip().startswith('*'):
                if ']' in line:
                    prefix = line.split(']')[0] + ']'
                else:
                    prefix = '*'
                redacted_lines.append(f"{prefix} [REDACTED - Content hidden by user on {timestamp}]")
            elif line.strip().startswith('---') or line.strip().startswith('Agent-'):
                in_summary = False
                redacted_lines.append(line)
            else:
                redacted_lines.append(line)
        else:
            if line.strip().startswith('Session:') or line.strip().startswith('---'):
                found_session_metadata = True
                if redacted_lines and redacted_lines[-1].strip() != '':
                    redacted_lines.append('')
                redacted_lines.append(line)
            elif line.strip().startswith('Request:'):
                redacted_lines.append(f"Request: [REDACTED - Content hidden by user on {timestamp}]")
            elif line.strip().startswith('Agent-Redacted:'):
                redacted_lines.append('Agent-Redacted: true')
            elif found_session_metadata or line.strip() == '':
                if line.strip() == '' or line.strip().startswith('Session:') or line.strip().startswith('Request:') or line.strip().startswith('---'):
                    continue
                else:
                    continue
            else:
                continue

    print('\\n'.join(redacted_lines))
else:
    print(original_message, end='')
'''
        msg_filter_script.write_text(msg_filter_code, encoding='utf-8')

        msg_filter_script.chmod(0o755)

        # Create a script for the tree-filter
        tree_filter_script = repo_root / ".git" / "realign_tree_filter.py"

        # Use a fixed timestamp for all redactions in this hide operation
        redacted_timestamp = datetime.now().isoformat()

        # Use regular string (not f-string) to avoid escaping issues
        tree_filter_code = '''#!/usr/bin/env python3
import sys
import os
import json
from pathlib import Path

# Fixed timestamp for this hide operation
REDACTED_TIMESTAMP = ''' + repr(redacted_timestamp) + '''

# Content to redact: {session_file: [original_line_content, ...]}
content_to_redact = ''' + json.dumps(content_to_redact, ensure_ascii=False) + '''

# Redacted replacement
def create_redacted_line(original_line):
    """Create a redacted version of a line, preserving structure if possible."""
    try:
        data = json.loads(original_line)
        return json.dumps({
            "type": data.get("type", "redacted"),
            "message": {"content": "[REDACTED]"},
            "redacted": True,
            "redacted_at": REDACTED_TIMESTAMP
        }, ensure_ascii=False)
    except json.JSONDecodeError:
        return json.dumps({
            "type": "redacted",
            "message": {"content": "[REDACTED]"},
            "redacted": True,
            "redacted_at": REDACTED_TIMESTAMP
        }, ensure_ascii=False)

# Process each session file
for session_file, original_lines in content_to_redact.items():
    file_path = Path(session_file)

    if not file_path.exists():
        continue

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace each original line with redacted version
    modified = False
    for original_line in original_lines:
        if original_line in content:
            redacted_line = create_redacted_line(original_line)
            content = content.replace(original_line, redacted_line)
            modified = True

    # Write back if modified
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
'''
        tree_filter_script.write_text(tree_filter_code, encoding='utf-8')

        tree_filter_script.chmod(0o755)

        # Run git filter-branch
        print(f"🔄 Rewriting git history...")
        print(f"   This may take a while...\n")

        filter_result = subprocess.run(
            [
                "git", "filter-branch",
                "--force",
                "--tree-filter", f"python3 {tree_filter_script}",
                "--msg-filter", f"python3 {msg_filter_script}",
                "--tag-name-filter", "cat",
                "--", commit_range
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            env={**os.environ, "FILTER_BRANCH_SQUELCH_WARNING": "1"}
        )

        # Clean up scripts
        msg_filter_script.unlink(missing_ok=True)
        tree_filter_script.unlink(missing_ok=True)

        if filter_result.returncode != 0:
            logger.error(f"git filter-branch failed: {filter_result.stderr}")
            print(f"\n❌ Error during git filter-branch: {filter_result.stderr}\n", file=sys.stderr)
            return False, {}, ""

        print("\n✅ Successfully redacted commit(s)")
        logger.info("Successfully redacted commits")

        # Clean up backup refs created by filter-branch
        print("\n🧹 Cleaning up...")
        subprocess.run(
            ["git", "for-each-ref", "--format=%(refname)", "refs/original/"],
            cwd=repo_root,
            capture_output=True
        )

        return True, content_to_redact, redacted_timestamp

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}\n", file=sys.stderr)
        return False, {}, ""


def apply_redaction_to_working_dir(
    content_to_redact: dict,
    redacted_timestamp: str,
    repo_root: Path
) -> bool:
    """
    Apply redaction to session files in the working directory.

    This ensures that future auto-commits will include the redacted content,
    not the original sensitive information.

    Args:
        content_to_redact: Dict mapping session files to lists of original lines to redact
        redacted_timestamp: ISO timestamp for the redaction
        repo_root: Path to repository root

    Returns:
        True on success, False on failure
    """
    logger.info("Applying redaction to working directory session files")

    def create_redacted_line(original_line):
        """Create a redacted version of a session line."""
        try:
            data = json.loads(original_line)
            return json.dumps({
                "type": data.get("type", "redacted"),
                "message": {"content": "[REDACTED]"},
                "redacted": True,
                "redacted_at": redacted_timestamp
            }, ensure_ascii=False)
        except json.JSONDecodeError:
            return json.dumps({
                "type": "redacted",
                "message": {"content": "[REDACTED]"},
                "redacted": True,
                "redacted_at": redacted_timestamp
            }, ensure_ascii=False)

    try:
        for session_file, original_lines in content_to_redact.items():
            file_path = repo_root / session_file

            if not file_path.exists():
                logger.warning(f"Session file not found in working directory: {session_file}")
                continue

            # Read current content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Apply redactions
            modified = False
            for original_line in original_lines:
                if original_line in content:
                    redacted_line = create_redacted_line(original_line)
                    content = content.replace(original_line, redacted_line)
                    modified = True
                    logger.debug(f"Redacted line in {session_file}")

            # Write back if modified
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Applied redaction to {session_file}")

                # Also update the backup file in sessions-original if it exists
                # This ensures pre-commit hook will use the redacted version
                from realign import get_realign_dir
                realign_dir = get_realign_dir(repo_root)
                backup_file = realign_dir / "sessions-original" / Path(session_file).name
                if backup_file.exists():
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Applied redaction to backup {backup_file.name}")

        print("✅ Applied redaction to working directory")
        return True

    except Exception as e:
        logger.error(f"Failed to apply redaction to working directory: {e}", exc_info=True)
        print(f"⚠️  Warning: Failed to apply redaction to working directory: {e}", file=sys.stderr)
        return False


def hide_command(
    indices: str,
    repo_root: Optional[Path] = None,
    force: bool = False
) -> int:
    """
    Main entry point for hide command.

    Args:
        indices: Commit indices to hide (e.g., "1,3,5-7")
        repo_root: Path to repository root (auto-detected if None)
        force: Skip confirmation prompt

    Returns:
        0 on success, 1 on error
    """
    logger.info(f"======== Hide command started: indices={indices} ========")

    # Auto-detect user project root if not provided
    if repo_root is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            repo_root = Path(result.stdout.strip())
            logger.debug(f"Detected user project root: {repo_root}")
        except subprocess.CalledProcessError:
            print("Error: Not in a git repository", file=sys.stderr)
            logger.error("Not in a git repository")
            return 1

    # Get shadow git repository path
    from realign import get_realign_dir
    shadow_dir = get_realign_dir(repo_root)
    shadow_git = shadow_dir

    # Verify shadow git exists
    if not shadow_git.exists():
        print(f"Error: Shadow git repository not found at {shadow_git}", file=sys.stderr)
        print("Run 'aline init' first to initialize the repository.", file=sys.stderr)
        logger.error(f"Shadow git not found at {shadow_git}")
        return 1

    # Check if it's a git repository
    git_dir = shadow_git / '.git'
    if not git_dir.exists():
        print(f"Error: {shadow_git} is not a git repository", file=sys.stderr)
        print("Run 'aline init' first to initialize the repository.", file=sys.stderr)
        logger.error(f"No .git found in {shadow_git}")
        return 1

    logger.info(f"Using shadow git repository: {shadow_git}")
    # Override repo_root to point to shadow git
    repo_root = shadow_git

    # Perform safety checks
    safe, message = perform_safety_checks(repo_root)
    if not safe:
        print(f"Error: {message}", file=sys.stderr)
        logger.error(f"Safety check failed: {message}")
        return 1

    # Get all unpushed commits
    try:
        all_commits = get_unpushed_commits(repo_root)
    except Exception as e:
        print(f"Error: Failed to get unpushed commits: {e}", file=sys.stderr)
        logger.error(f"Failed to get unpushed commits: {e}", exc_info=True)
        return 1

    if not all_commits:
        print("Error: No unpushed commits found", file=sys.stderr)
        logger.error("No unpushed commits found")
        return 1

    # Parse indices
    try:
        if indices == "--all":
            indices_list = [c.index for c in all_commits]
        else:
            indices_list = parse_commit_indices(indices)
    except ValueError as e:
        print(f"Error: Invalid indices format: {e}", file=sys.stderr)
        logger.error(f"Invalid indices format: {e}")
        return 1

    # Validate indices
    max_index = len(all_commits)
    invalid_indices = [i for i in indices_list if i < 1 or i > max_index]
    if invalid_indices:
        print(f"Error: Invalid indices (out of range 1-{max_index}): {invalid_indices}", file=sys.stderr)
        logger.error(f"Invalid indices: {invalid_indices}")
        return 1

    # Get commits to hide
    commits_to_hide = [c for c in all_commits if c.index in indices_list]

    logger.info(f"Commits to hide: {[c.hash for c in commits_to_hide]}")

    # Confirm operation
    if not force:
        if not confirm_hide_operation(commits_to_hide, all_commits):
            print("Operation cancelled by user")
            logger.info("Operation cancelled by user")
            return 0

    # Create backup
    try:
        create_backup_ref(repo_root)
    except Exception as e:
        print(f"Warning: Failed to create backup: {e}", file=sys.stderr)
        logger.warning(f"Failed to create backup: {e}")

    # Hide commits
    success, content_to_redact, redacted_timestamp = hide_commits_with_filter_repo(commits_to_hide, all_commits, repo_root)

    if success:
        # Apply redaction to working directory session files
        # This ensures future auto-commits will include redacted content
        apply_redaction_to_working_dir(content_to_redact, redacted_timestamp, repo_root)

        logger.info("======== Hide command completed successfully ========")
        return 0
    else:
        print("\n❌ Failed to hide commits. Check the backup reference if needed.\n", file=sys.stderr)
        logger.error("======== Hide command failed ========")
        return 1


def hide_reset_command(
    repo_root: Optional[Path] = None,
    force: bool = False
) -> int:
    """
    Reset to the last backup before hide operation.

    Args:
        repo_root: Path to repository root (auto-detected if None)
        force: Skip confirmation prompt

    Returns:
        0 on success, 1 on error
    """
    logger.info("======== Hide reset command started ========")

    # Auto-detect user project root if not provided
    if repo_root is None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True
            )
            repo_root = Path(result.stdout.strip())
            logger.debug(f"Detected user project root: {repo_root}")
        except subprocess.CalledProcessError:
            print("Error: Not in a git repository", file=sys.stderr)
            logger.error("Not in a git repository")
            return 1

    # Get shadow git repository path
    from realign import get_realign_dir
    shadow_dir = get_realign_dir(repo_root)
    shadow_git = shadow_dir

    # Verify shadow git exists
    if not shadow_git.exists():
        print(f"Error: Shadow git repository not found at {shadow_git}", file=sys.stderr)
        print("Run 'aline init' first to initialize the repository.", file=sys.stderr)
        logger.error(f"Shadow git not found at {shadow_git}")
        return 1

    # Check if it's a git repository
    git_dir = shadow_git / '.git'
    if not git_dir.exists():
        print(f"Error: {shadow_git} is not a git repository", file=sys.stderr)
        print("Run 'aline init' first to initialize the repository.", file=sys.stderr)
        logger.error(f"No .git found in {shadow_git}")
        return 1

    logger.info(f"Using shadow git repository: {shadow_git}")
    # Override repo_root to point to shadow git
    repo_root = shadow_git

    # Find all backup refs
    result = subprocess.run(
        ["git", "for-each-ref", "refs/realign/", "--format=%(refname) %(objectname) %(creatordate:unix)", "--sort=-creatordate"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("Error: Failed to list backup references", file=sys.stderr)
        logger.error("Failed to list backup references")
        return 1

    # Parse backup refs
    backup_refs = []
    for line in result.stdout.strip().split('\n'):
        if not line or not line.startswith('refs/realign/backup_'):
            continue

        parts = line.split()
        if len(parts) >= 3:
            ref_name = parts[0]
            commit_hash = parts[1]
            timestamp = int(parts[2])
            backup_refs.append((ref_name, commit_hash, timestamp))

    if not backup_refs:
        print("Error: No backup references found", file=sys.stderr)
        print("You can only reset after running 'aline hide'", file=sys.stderr)
        logger.error("No backup references found")
        return 1

    # Get the most recent backup
    latest_backup = backup_refs[0]
    backup_ref, backup_commit, _ = latest_backup

    # Get current commit
    current_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True
    )
    current_commit = current_result.stdout.strip()

    # Check if we're already at the backup
    if current_commit == backup_commit:
        print(f"Already at backup commit: {backup_commit[:8]}")
        print("Nothing to reset.")
        return 0

    # Show what will happen
    print(f"\n🔄 Reset to last hide backup\n")
    print(f"Current HEAD: {current_commit[:8]}")
    print(f"Backup ref:   {backup_ref}")
    print(f"Backup HEAD:  {backup_commit[:8]}\n")

    if not force:
        response = input("Proceed with reset? [y/N] ").strip().lower()
        if response != 'y':
            print("Reset cancelled")
            logger.info("Reset cancelled by user")
            return 0

    # Perform the reset
    try:
        reset_result = subprocess.run(
            ["git", "reset", "--hard", backup_ref],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"\n✅ Successfully reset to {backup_commit[:8]}")
        print(f"   {reset_result.stdout.strip()}")
        logger.info(f"Successfully reset to {backup_ref}")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to reset: {e.stderr}", file=sys.stderr)
        logger.error(f"Failed to reset: {e.stderr}")
        return 1
