"""Push command - Push session commits to remote repository."""

import os
from pathlib import Path
from typing import Optional

from ..tracker.git_tracker import ReAlignGitTracker
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.push', 'push.log')


def push_command(
    force: bool = False,
    repo_root: Optional[Path] = None
) -> int:
    """
    Push session commits to remote repository.

    This command pushes your local session commits to the configured
    remote repository, making them available to your team.

    Args:
        force: If True, force push (use with caution)
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
        print("\nTo set up sharing:")
        print("  aline init --share          (browser-based setup)")
        print("  aline share configure       (manual configuration)")
        return 1

    # Get unpushed commits
    unpushed = tracker.get_unpushed_commits()

    if not unpushed:
        print("✓ All commits are already pushed")
        print(f"\nRemote: {tracker.get_remote_url()}")
        return 0

    # Show review of unpushed commits
    print(f"Found {len(unpushed)} unpushed commit(s)\n")

    # Display commits summary
    try:
        display_commits_summary(tracker, unpushed)
    except Exception as e:
        logger.warning(f"Failed to display commit details: {e}")
        # Just show hashes
        for commit_hash in unpushed:
            print(f"  {commit_hash[:8]}")

    print()

    # For non-interactive mode, just push
    if force:
        print("Force pushing...")
        success = tracker.safe_push(force=True)
        if success:
            print(f"✓ Successfully force-pushed {len(unpushed)} commit(s)")
            print(f"\nRemote: {tracker.get_remote_url()}")
            return 0
        else:
            print("❌ Push failed")
            return 1

    # Interactive mode - prompt user
    print("Push these commit(s)?")
    print("  [Y] Push all")
    print("  [n] Cancel")
    print("  [h] Hide specific commits")
    print()

    choice = input("Select [Y/n/h]: ").strip().lower()

    if choice == 'n':
        print("Cancelled")
        return 0

    if choice == 'h':
        # Interactive hide mode
        print("\nEnter commit indices to hide (comma-separated, e.g., 1,3):")
        print("Commits are numbered from the list above")

        indices_str = input("Indices: ").strip()

        if indices_str:
            try:
                # Parse indices
                indices = [int(i.strip()) for i in indices_str.split(',')]

                # Validate indices
                valid_indices = [i for i in indices if 1 <= i <= len(unpushed)]

                if not valid_indices:
                    print("No valid indices provided, cancelling")
                    return 0

                # Hide commits using the hide command
                from .hide import hide_command

                # Convert indices back to string format for hide command
                indices_for_hide = ','.join(map(str, valid_indices))

                if hide_command(indices=indices_for_hide, repo_root=repo_root, force=True) == 0:
                    print(f"\n✓ Hidden {len(valid_indices)} commit(s)")

                    # Re-check unpushed commits
                    unpushed = tracker.get_unpushed_commits()

                    if not unpushed:
                        print("All commits have been hidden")
                        return 0

                    print(f"\nRemaining {len(unpushed)} commit(s) to push")

                    confirm = input("Proceed with push? [Y/n]: ").strip().lower()
                    if confirm == 'n':
                        print("Cancelled")
                        return 0
                else:
                    print("❌ Failed to hide commits")
                    return 1

            except ValueError:
                print("Invalid input format")
                return 1

    # Perform push
    print("\nPushing to remote...")

    success = tracker.safe_push(force=force)

    if success:
        print(f"✓ Successfully pushed {len(unpushed)} commit(s)")
        print(f"\nRemote: {tracker.get_remote_url()}")
        return 0
    else:
        print("❌ Push failed")
        print("\nTroubleshooting:")
        print("  - Check network connection")
        print("  - Verify remote repository access")
        print("  - Check logs: .realign/logs/push.log")
        return 1


def display_commits_summary(tracker: ReAlignGitTracker, commit_hashes: list):
    """
    Display a summary of commits to be pushed.

    Args:
        tracker: ReAlignGitTracker instance
        commit_hashes: List of commit hashes
    """
    import subprocess

    for i, commit_hash in enumerate(commit_hashes, 1):
        # Get commit message
        result = subprocess.run(
            ["git", "log", "-1", "--format=%s", commit_hash],
            cwd=tracker.realign_dir,
            capture_output=True,
            text=True,
            check=False
        )

        message = result.stdout.strip() if result.returncode == 0 else "Unknown"

        # Get timestamp
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ar", commit_hash],
            cwd=tracker.realign_dir,
            capture_output=True,
            text=True,
            check=False
        )

        timestamp = result.stdout.strip() if result.returncode == 0 else ""

        print(f"[{i}] {commit_hash[:8]} - {message}")
        if timestamp:
            print(f"     {timestamp}")
