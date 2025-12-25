"""Sync command - Bidirectional synchronization (pull + push)."""

import os
from pathlib import Path
from typing import Optional

from ..tracker.git_tracker import ReAlignGitTracker
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.sync', 'sync.log')


def sync_command(repo_root: Optional[Path] = None) -> int:
    """
    Synchronize with remote repository (pull then push).

    This command performs a bidirectional sync:
    1. Pulls updates from remote
    2. Pushes local commits to remote

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

    remote_url = tracker.get_remote_url()
    print(f"Synchronizing with: {remote_url}")
    print()

    # Step 1: Pull from remote
    print("[1/2] Pulling from remote...")

    pull_success = tracker.safe_pull()

    if not pull_success:
        print("❌ Pull failed")
        print("\nSync aborted. Fix pull issues before syncing.")
        print("Check logs: .realign/logs/sync.log")
        return 1

    print("✓ Pull completed")
    print()

    # Step 2: Push to remote
    print("[2/2] Pushing to remote...")

    # Get unpushed commits
    unpushed = tracker.get_unpushed_commits()

    if not unpushed:
        print("✓ No commits to push")
        print("\n✓ Synchronization complete")
        return 0

    print(f"Found {len(unpushed)} unpushed commit(s)")

    push_success = tracker.safe_push()

    if push_success:
        print(f"✓ Pushed {len(unpushed)} commit(s)")
        print("\n✓ Synchronization complete")
        return 0
    else:
        print("❌ Push failed")
        print("\nPull succeeded, but push failed.")
        print("You can try 'aline push' separately")
        print("Check logs: .realign/logs/sync.log")
        return 1
