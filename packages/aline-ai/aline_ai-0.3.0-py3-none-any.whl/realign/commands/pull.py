"""Pull command - Pull session updates from remote repository."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from ..tracker.git_tracker import ReAlignGitTracker
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.pull', 'pull.log')


def pull_command(repo_root: Optional[Path] = None) -> int:
    """
    Pull session updates from remote repository.

    This command fetches and merges session commits from the
    remote repository, bringing in updates from your teammates.

    Args:
        repo_root: Path to repository root (uses cwd if not provided)

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get project root
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    # Check if repository is initialized
    if not tracker.is_initialized():
        print("❌ Repository not initialized")
        print("Run 'aline init' first")
        return 1

    # Check if remote is configured
    if not tracker.has_remote():
        print("❌ No remote configured")
        print("\nTo join a shared repository:")
        print("  aline init --join <repo>")
        print("\nOr to set up sharing:")
        print("  aline init --share")
        return 1

    # Check for unpushed commits
    unpushed = tracker.get_unpushed_commits()

    if unpushed:
        print(f"⚠️  Warning: You have {len(unpushed)} unpushed commit(s)")
        print("These will be merged with remote changes")
        print()

        confirm = input("Continue with pull? [Y/n]: ").strip().lower()
        if confirm == 'n':
            print("Cancelled")
            return 0

    # Perform pull
    print("Pulling from remote...")

    remote_url = tracker.get_remote_url()
    print(f"Remote: {remote_url}")
    print()

    success = tracker.safe_pull()

    if success:
        print("✓ Successfully pulled updates from remote")

        # Try to get some stats about what was pulled
        try:
            # Get log of recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=tracker.realign_dir,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0 and result.stdout.strip():
                print("\nRecent commits:")
                for line in result.stdout.strip().split('\n'):
                    print(f"  {line}")

        except Exception as e:
            logger.debug(f"Failed to get commit stats: {e}")

        return 0
    else:
        print("❌ Pull failed")
        print("\nPossible issues:")
        print("  - Conflicts requiring manual resolution")
        print("  - Network connection problems")
        print("  - Repository access issues")
        print("\nCheck logs: .realign/logs/pull.log")
        return 1
