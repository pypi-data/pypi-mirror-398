#!/usr/bin/env python3
"""
Review command - Display unpushed commits with session summaries.

This allows users to review what will be pushed before making it public.
"""

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from ..logging_config import setup_logger

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

logger = setup_logger('realign.commands.review', 'review.log')


@dataclass
class UnpushedCommit:
    """Represents an unpushed commit with session information."""
    index: int                                      # User-visible index (1-based)
    hash: str                                        # Short commit hash
    full_hash: str                                   # Full commit hash
    message: str                                     # First line of commit message
    timestamp: datetime                              # Commit timestamp
    llm_summary: str                                 # Extracted LLM summary
    user_request: Optional[str]                      # User's request text
    session_files: List[str]                         # Session files modified
    session_additions: Dict[str, List[Tuple[int, int]]]  # {file: [(start, end), ...]}
    has_sensitive: bool = False                      # Whether sensitive content detected


def get_unpushed_commits(repo_root: Path) -> List[UnpushedCommit]:
    """
    Get all unpushed commits from the current branch.

    Strategy (Updated):
    1. Get current branch name
    2. If on main/master branch:
       - Use upstream (@{u}) if exists, otherwise origin/main
    3. If on feature branch:
       - Always compare against origin/main or origin/master
       - This shows all commits that will be in the PR
    4. If no remote exists, show all commits on current branch

    Args:
        repo_root: Path to repository root

    Returns:
        List of UnpushedCommit objects, ordered from newest to oldest
    """
    logger.info("Getting unpushed commits")

    # Get current branch name
    current_branch_result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if current_branch_result.returncode != 0:
        logger.error("Failed to get current branch name")
        return []

    current_branch = current_branch_result.stdout.strip()
    logger.debug(f"Current branch: {current_branch}")

    # Detect main branch name
    main_branch = detect_main_branch(repo_root)

    # Determine base branch based on current branch
    if current_branch in ['main', 'master']:
        # On main branch: show commits not pushed to upstream
        upstream_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "@{u}"],
            cwd=repo_root,
            capture_output=True,
            text=True
        )

        if upstream_result.returncode == 0:
            base = "@{u}"
            logger.debug(f"On main branch, using upstream: {upstream_result.stdout.strip()}")
        else:
            base = f"origin/{main_branch}"
            logger.debug(f"On main branch but no upstream, using: {base}")
    else:
        # On feature branch: show all commits relative to main
        # This shows what would be in a PR
        base = f"origin/{main_branch}"
        logger.debug(f"On feature branch '{current_branch}', comparing against: {base}")

    # Verify that the base branch exists
    verify_result = subprocess.run(
        ["git", "rev-parse", "--verify", base],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if verify_result.returncode != 0:
        # Remote branch doesn't exist, show all commits on current branch
        base = None
        logger.info(f"Base branch '{base}' not found, will show all commits on current branch")

    # Get commit list
    # Format: full_hash|short_hash|subject|timestamp
    if base:
        log_cmd = ["git", "log", f"{base}..HEAD", "--format=%H|%h|%s|%at"]
    else:
        # No remote, show all commits
        log_cmd = ["git", "log", "HEAD", "--format=%H|%h|%s|%at"]

    log_result = subprocess.run(
        log_cmd,
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if log_result.returncode != 0:
        logger.error(f"Failed to get commit list: {log_result.stderr}")
        return []

    commit_lines = [line for line in log_result.stdout.strip().split('\n') if line]

    if not commit_lines:
        logger.info("No unpushed commits found")
        return []

    logger.info(f"Found {len(commit_lines)} unpushed commit(s)")

    # Parse commits
    commits = []
    for idx, line in enumerate(commit_lines, 1):
        parts = line.split('|')
        if len(parts) != 4:
            logger.warning(f"Skipping malformed commit line: {line}")
            continue

        full_hash, short_hash, subject, timestamp_str = parts
        timestamp = datetime.fromtimestamp(int(timestamp_str))

        # Get full commit message
        full_message = subprocess.run(
            ["git", "log", "-1", "--format=%B", full_hash],
            cwd=repo_root,
            capture_output=True,
            text=True
        ).stdout

        # Extract LLM summary and user request
        llm_summary = extract_llm_summary(full_message)
        user_request = extract_user_request(full_message)

        # Get session file additions
        session_files, session_additions = get_session_additions(full_hash, repo_root)

        commit = UnpushedCommit(
            index=idx,
            hash=short_hash,
            full_hash=full_hash,
            message=subject,
            timestamp=timestamp,
            llm_summary=llm_summary,
            user_request=user_request,
            session_files=session_files,
            session_additions=session_additions,
            has_sensitive=False  # Will be set by --detect-secrets flag
        )

        commits.append(commit)
        logger.debug(f"Parsed commit [{idx}] {short_hash}: {subject}")

    return commits


def detect_main_branch(repo_root: Path) -> str:
    """
    Detect the main branch name (main or master).

    Args:
        repo_root: Path to repository root

    Returns:
        "main" or "master"
    """
    # Check if origin/main exists
    main_check = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if main_check.returncode == 0:
        return "main"

    # Check if origin/master exists
    master_check = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/master"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if master_check.returncode == 0:
        return "master"

    # If no remote branches exist, check current local branch name
    current_branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if current_branch.returncode == 0:
        branch_name = current_branch.stdout.strip()
        logger.info(f"No remote found, using current branch: {branch_name}")
        return branch_name

    # Default to main
    logger.warning("Could not detect main branch, defaulting to 'main'")
    return "main"


def extract_user_request(commit_message: str) -> Optional[str]:
    """
    Extract user request from commit message.

    New format (v0.3+):
        ---
        Session: ... | Turn: ... | Model: ...
        Request: {user_message}

    Args:
        commit_message: Full commit message

    Returns:
        User request text, or None if not found
    """
    lines = commit_message.split('\n')

    # Look for "Request:" line
    for i, line in enumerate(lines):
        if line.strip().startswith('Request:'):
            # Extract text after "Request:"
            request = line.strip()[8:].strip()  # Remove "Request:" prefix
            # Filter out placeholder messages
            if request and request != "No user message found":
                return request

    return None


def extract_llm_summary(commit_message: str) -> str:
    """
    Extract LLM summary from commit message.

    Supports two formats:

    New format (v0.3+):
        {llm_title}

        {llm_description}

        ---
        Turn: #{turn_number} | Model: {model_name}
        Request: {user_message}

    Legacy format:
        chore: Auto-commit MCP session (2025-11-22 19:24:29)

        --- LLM-Summary (claude-3-5-haiku) ---
        * [Claude] Discussed implementing JWT authentication

    Args:
        commit_message: Full commit message

    Returns:
        Extracted summary text, or "(No summary)"
    """
    lines = commit_message.split('\n')

    # Try new format first: title is first line, description is in the middle
    if lines and not lines[0].startswith('chore:') and '---' in commit_message:
        # New format: {title}\n\n{description}\n\n---
        title = lines[0].strip()

        # Find description (between title and ---)
        description_lines = []
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == '---':
                break
            if line.strip():  # Skip empty lines
                description_lines.append(line.strip())

        if title:
            summary = title
            if description_lines:
                # Use first line of description if available
                summary += f": {description_lines[0]}"
            return summary

    # Try legacy format
    in_summary = False
    summary_lines = []

    for line in lines:
        # Start of summary section
        if '--- LLM-Summary' in line:
            in_summary = True
            continue

        if in_summary:
            # End of summary section
            if line.strip().startswith('---') or line.strip().startswith('Agent-'):
                break

            # Extract summary content
            if line.strip().startswith('*'):
                # Remove leading "* "
                content = line.strip()[1:].strip()

                # Remove [Agent] prefix if present
                if ']' in content:
                    # "* [Claude] Text here" -> "Text here"
                    content = content.split(']', 1)[1].strip()

                summary_lines.append(content)

    if summary_lines:
        return ' | '.join(summary_lines)
    else:
        return "(No summary)"


def get_session_additions(commit_hash: str, repo_root: Path) -> Tuple[List[str], Dict[str, List[Tuple[int, int]]]]:
    """
    Get session files modified in this commit and their line additions.

    Args:
        commit_hash: Commit hash
        repo_root: Path to repository root

    Returns:
        Tuple of:
        - List of session file paths (relative to repo root)
        - Dict mapping file paths to line ranges: {file: [(start, end), ...]}
    """
    logger.debug(f"Getting session additions for commit {commit_hash}")

    # Get files modified in this commit
    files_result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    if files_result.returncode != 0:
        logger.warning(f"Failed to get files for commit {commit_hash}")
        return [], {}

    all_files = files_result.stdout.strip().split('\n')

    # Filter session files
    # Note: In shadow git, session files are in 'sessions/' directory
    # In user project, they would be in '.realign/sessions/' directory
    session_files = [
        f for f in all_files
        if (f.startswith('sessions/') or f.startswith('.realign/sessions/')) and f.endswith('.jsonl')
    ]

    if not session_files:
        logger.debug(f"No session files in commit {commit_hash}")
        return [], {}

    logger.debug(f"Found {len(session_files)} session file(s) in commit {commit_hash}")

    # Get line additions for each session file
    additions = {}

    for session_file in session_files:
        # Get diff for this file
        diff_result = subprocess.run(
            ["git", "show", commit_hash, "--", session_file],
            cwd=repo_root,
            capture_output=True,
            text=True
        )

        if diff_result.returncode != 0:
            logger.warning(f"Failed to get diff for {session_file}")
            continue

        # Parse diff to extract line ranges
        line_ranges = parse_diff_additions(diff_result.stdout)

        if line_ranges:
            additions[session_file] = line_ranges
            total_lines = sum(end - start + 1 for start, end in line_ranges)
            logger.debug(f"  {session_file}: +{total_lines} lines in {len(line_ranges)} range(s)")

    return session_files, additions


def parse_diff_additions(diff_output: str) -> List[Tuple[int, int]]:
    """
    Parse git diff output to extract line ranges of additions.

    Diff format:
        @@ -10,5 +10,8 @@
         existing line
        +new line 1
        +new line 2
        +new line 3
         existing line

    Args:
        diff_output: Output from git show or git diff

    Returns:
        List of (start_line, end_line) tuples (1-based, inclusive)
        Line numbers are based on the NEW file (after commit)
    """
    ranges = []
    current_line = 0
    range_start = None

    for line in diff_output.split('\n'):
        # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith('@@'):
            match = re.search(r'\+(\d+),?(\d+)?', line)
            if match:
                current_line = int(match.group(1))
                range_start = None
                logger.debug(f"    Hunk starts at line {current_line}")

        # Added line
        elif line.startswith('+') and not line.startswith('+++'):
            if range_start is None:
                range_start = current_line
            current_line += 1

        # Context line (unchanged)
        elif line.startswith(' '):
            if range_start is not None:
                # End current range
                ranges.append((range_start, current_line - 1))
                logger.debug(f"    Range: {range_start}-{current_line - 1}")
                range_start = None
            current_line += 1

        # Deleted line (doesn't affect new file line numbers)
        elif line.startswith('-') and not line.startswith('---'):
            pass

    # Handle last range if still open
    if range_start is not None:
        ranges.append((range_start, current_line - 1))
        logger.debug(f"    Range: {range_start}-{current_line - 1}")

    return ranges


def display_unpushed_commits(commits: List[UnpushedCommit], verbose: bool = False):
    """
    Display list of unpushed commits in a user-friendly format.

    Args:
        commits: List of UnpushedCommit objects
        verbose: Whether to show detailed information
    """
    if not commits:
        print(f"\n{Colors.GREEN}✓ No unpushed commits found.{Colors.RESET}\n")
        return

    # Header
    print(f"\n{Colors.BOLD}{Colors.CYAN}📋 Unpushed commits ({len(commits)}){Colors.RESET}\n")

    for commit in commits:
        # Index and hash in gray
        index_str = f"{Colors.GRAY}[{commit.index}]{Colors.RESET}"
        hash_str = f"{Colors.YELLOW}{commit.hash}{Colors.RESET}"

        # Commit message (first line only) in bold white
        message_str = f"{Colors.BOLD}{commit.message}{Colors.RESET}"

        print(f"{index_str} {hash_str} {message_str}")

        # User request (first 50 characters) in cyan
        if commit.user_request:
            # Truncate to 50 characters
            request_display = commit.user_request[:50]
            if len(commit.user_request) > 50:
                request_display += "..."
            print(f"    {Colors.CYAN}└─ {request_display}{Colors.RESET}")

        # Verbose mode: show additional details
        if verbose:
            # Timestamp in dim gray
            time_str = commit.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(f"    {Colors.DIM}Time: {time_str}{Colors.RESET}")

            # LLM Summary
            if commit.llm_summary and commit.llm_summary != "(No summary)":
                print(f"    {Colors.DIM}Summary: {commit.llm_summary}{Colors.RESET}")

            # Session files (only show files with additions)
            if commit.session_files:
                files_with_additions = [
                    (f, commit.session_additions.get(f, []))
                    for f in commit.session_files
                ]
                # Filter to only files with actual additions
                files_with_additions = [
                    (f, ranges) for f, ranges in files_with_additions
                    if ranges  # Only show files with non-empty additions
                ]

                for session_file, additions in files_with_additions:
                    total_lines = sum(end - start + 1 for start, end in additions)
                    print(f"    {Colors.DIM}Session: {session_file} (+{total_lines} lines){Colors.RESET}")

            # Sensitive content warning
            if commit.has_sensitive:
                print(f"    {Colors.RED}⚠️  WARNING: Potential sensitive content detected{Colors.RESET}")

            print()  # Blank line separator in verbose mode


def review_command(
    repo_root: Optional[Path] = None,
    verbose: bool = False,
    detect_secrets: bool = False
) -> int:
    """
    Main entry point for review command.

    Reviews commits in the shadow git repository (~/.aline/{project}/.git)
    rather than the user's project repository.

    Args:
        repo_root: Path to user's project root (auto-detected if None)
        verbose: Show detailed information
        detect_secrets: Run sensitive content detection

    Returns:
        0 on success, 1 on error
    """
    logger.info("======== Review command started ========")

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
    from .. import get_realign_dir
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

    # Get unpushed commits
    try:
        commits = get_unpushed_commits(repo_root)
    except Exception as e:
        print(f"Error: Failed to get unpushed commits: {e}", file=sys.stderr)
        logger.error(f"Failed to get unpushed commits: {e}", exc_info=True)
        return 1

    # Detect sensitive content if requested
    if detect_secrets:
        try:
            from ..redactor import check_and_redact_session

            for commit in commits:
                for session_file in commit.session_files:
                    file_path = repo_root / session_file
                    if not file_path.exists():
                        continue

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    _, has_secrets, _ = check_and_redact_session(
                        content,
                        redact_mode="auto"
                    )

                    if has_secrets:
                        commit.has_sensitive = True
                        logger.warning(f"Detected sensitive content in commit {commit.hash}")
                        break
        except ImportError:
            print("Warning: detect-secrets not available, skipping sensitive content detection", file=sys.stderr)
            logger.warning("detect-secrets not available")

    # Display commits
    display_unpushed_commits(commits, verbose=verbose)

    logger.info("======== Review command completed ========")
    return 0
