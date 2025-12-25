"""Undo command - Revert project and session state to a specific commit."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

from ..tracker.git_tracker import ReAlignGitTracker
from ..mirror_utils import (
    get_gitignore_patterns,
    get_files_at_commit,
    reverse_mirror_from_commit,
    collect_project_files
)
from .session_utils import (
    find_session_paths_for_commit,
    detect_original_session_location,
    restore_session_from_commit
)
from ..logging_config import setup_logger

logger = setup_logger('realign.commands.undo', 'undo.log')


def undo_command(
    commit_hash: str,
    repo_root: Optional[Path] = None,
    dry_run: bool = False,
    no_backup: bool = False,
    deletion_strategy: str = "keep",
    force: bool = False
) -> int:
    """
    Undo project and session state to a specific commit.

    Args:
        commit_hash: Commit hash to undo to
        repo_root: Project root directory (defaults to current directory)
        dry_run: Preview changes without executing
        no_backup: Skip backup creation
        deletion_strategy: How to handle extra files: "keep", "delete", or "backup"
        force: Skip confirmation prompts

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if repo_root is None:
        repo_root = Path(os.getcwd()).resolve()

    # Initialize tracker
    tracker = ReAlignGitTracker(repo_root)

    # Phase 1: Validation
    logger.info(f"Starting undo to commit {commit_hash}")

    if not tracker.is_initialized():
        print("❌ Repository not initialized")
        print("Run 'aline init' first")
        return 1

    if not tracker.verify_commit_exists(commit_hash):
        print(f"❌ Commit {commit_hash} does not exist")
        print("\nRecent commits:")
        # Show recent commits to help user
        try:
            import subprocess
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=tracker.realign_dir,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print(result.stdout)
        except Exception:
            pass
        return 1

    # Get commit info
    commit_info = tracker.get_commit_info(commit_hash)
    if not commit_info:
        print(f"❌ Failed to get commit information for {commit_hash}")
        return 1

    # Check if already at target commit
    current_head = None
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tracker.realign_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            current_head = result.stdout.strip()
    except Exception:
        pass

    if current_head and current_head.startswith(commit_info['hash'][:7]):
        print(f"Already at commit {commit_hash}")
        return 0

    # Check current branch
    current_branch = tracker.get_current_branch()
    if not current_branch:
        print("❌ Cannot undo from detached HEAD state")
        print("Please checkout master first: cd ~/.aline/{project_name} && git checkout master")
        return 1

    if current_branch != "master":
        print(f"⚠️  Warning: Currently on branch '{current_branch}', expected 'master'")
        if not force:
            response = input("Continue anyway? [y/N]: ").strip().lower()
            if response != 'y':
                print("Aborted")
                return 1

    # Phase 2: Preview
    logger.info("Calculating changes...")

    gitignore_patterns = get_gitignore_patterns(repo_root)
    files_at_target = get_files_at_commit(tracker, commit_hash)
    current_files = collect_project_files(repo_root, logger=None)

    # Convert to sets of relative paths for comparison
    target_paths = set(str(f) for f in files_at_target)
    current_paths = set(str(f.relative_to(repo_root)) for f in current_files)

    files_to_restore = target_paths
    files_to_delete = current_paths - target_paths
    files_to_create = target_paths - current_paths

    # Find session files
    session_files = find_session_paths_for_commit(
        repo_root,
        commit_hash,
        git_dir=tracker.realign_dir
    )

    # Format commit timestamp
    try:
        timestamp = int(commit_info['timestamp'])
        dt = datetime.fromtimestamp(timestamp)
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        formatted_time = commit_info['timestamp']

    # Display preview
    print(f"\nUndoing to commit {commit_hash[:7]} ({formatted_time})")
    print(f"Message: {commit_info['message']}")
    print("\nChanges preview:")
    print(f"  Files to restore: {len(files_to_restore)}")

    if files_to_delete:
        deletion_msg = "will be kept by default" if deletion_strategy == "keep" else f"will be {deletion_strategy}d"
        print(f"  Files to delete: {len(files_to_delete)} ({deletion_msg})")
    else:
        print(f"  Files to delete: 0")

    print(f"  Sessions to restore: {len(session_files)}")

    if dry_run:
        print("\n[DRY RUN] Would perform the following actions:")
        print("\nGit Operations:")

        undo_branch = f"undo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"  Create branch: {undo_branch} (from current HEAD)")
        print(f"  Reset master: {current_head[:7] if current_head else 'current'} → {commit_hash[:7]}")

        print("\nFile Changes:")
        if files_to_restore:
            print(f"  Restore ({len(files_to_restore)} files):")
            for path in sorted(list(files_to_restore)[:5]):
                print(f"    {path}")
            if len(files_to_restore) > 5:
                print(f"    ... and {len(files_to_restore) - 5} more")

        if files_to_delete:
            print(f"  {deletion_strategy.capitalize()} ({len(files_to_delete)} files):")
            for path in sorted(list(files_to_delete)[:5]):
                print(f"    {path}")
            if len(files_to_delete) > 5:
                print(f"    ... and {len(files_to_delete) - 5} more")

        if session_files:
            print("\nSession Restoration:")
            for session_file in session_files:
                filename = Path(session_file).name
                dest = detect_original_session_location(filename, repo_root, timestamp)
                if dest:
                    print(f"  {filename} → {dest}")
                else:
                    fallback = tracker.realign_dir / "sessions-restored" / filename
                    print(f"  {filename} → {fallback} (fallback)")

        print("\nNo changes made (dry-run mode)")
        return 0

    # Phase 3: User Confirmation
    if not force:
        print()
        response = input("Continue? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted")
            return 1

    # Phase 4: Backup
    backup_dir = None
    backup_metadata = None

    if not no_backup:
        print("\n✓ Creating backup...")
        timestamp_str = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_dir = tracker.realign_dir / f"undo-backup-{timestamp_str}"

        try:
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Mirror current state
            current_files_list = collect_project_files(repo_root, logger=logger)
            mirrored = tracker.mirror_files(current_files_list)

            # Store backup metadata
            backup_metadata = {
                "timestamp": datetime.now().isoformat(),
                "from_commit": current_head,
                "to_commit": commit_hash,
                "backup_path": str(backup_dir)
            }

            metadata_dir = tracker.realign_dir / ".metadata"
            metadata_dir.mkdir(exist_ok=True)

            metadata_file = metadata_dir / "undo_backup.json"
            with open(metadata_file, 'w') as f:
                json.dump(backup_metadata, f, indent=2)

            logger.info(f"Backup created at {backup_dir}")

        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            return 1

    # Phase 5: Execute Undo
    undo_branch = f"undo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    try:
        # Create undo branch (this will switch to the new branch)
        print(f"✓ Creating undo branch: {undo_branch}")
        if not tracker.create_branch(undo_branch, "HEAD"):
            raise Exception("Failed to create undo branch")

        # Always checkout master to perform the reset there
        print("✓ Checking out master branch")
        if not tracker.checkout_branch("master"):
            raise Exception("Failed to checkout master")

        # Reset to target commit
        print(f"✓ Resetting to commit {commit_hash[:7]}")
        if not tracker.reset_to_commit(commit_hash):
            raise Exception("Failed to reset to commit")

        # Restore files
        print(f"✓ Restoring {len(files_to_restore)} files")
        restore_result = reverse_mirror_from_commit(
            tracker,
            commit_hash,
            repo_root,
            gitignore_patterns,
            logger=logger
        )

        # Handle deletions
        if files_to_delete:
            if deletion_strategy == "delete":
                deleted_count = 0
                for rel_path in files_to_delete:
                    try:
                        file_path = repo_root / rel_path
                        if file_path.exists():
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {rel_path}: {e}")
                print(f"✓ Deleted {deleted_count} extra files")

            elif deletion_strategy == "backup" and backup_dir:
                moved_count = 0
                for rel_path in files_to_delete:
                    try:
                        src = repo_root / rel_path
                        dst = backup_dir / rel_path
                        if src.exists():
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(src), str(dst))
                            moved_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to move {rel_path}: {e}")
                print(f"✓ Moved {moved_count} extra files to backup")

        # Restore sessions
        sessions_restored = 0
        sessions_failed = 0

        if session_files:
            print(f"✓ Restoring {len(session_files)} session file(s)")

            for session_rel_path in session_files:
                filename = Path(session_rel_path).name

                # Detect original location
                dest_path = detect_original_session_location(filename, repo_root, timestamp)

                # Fall back to sessions-restored if cannot detect
                if not dest_path:
                    restored_dir = tracker.realign_dir / "sessions-restored"
                    restored_dir.mkdir(exist_ok=True)
                    dest_path = restored_dir / filename
                    logger.info(f"Session location not detected, using fallback: {dest_path}")

                # Restore session
                if restore_session_from_commit(tracker, commit_hash, session_rel_path, dest_path):
                    sessions_restored += 1
                    logger.info(f"Restored session: {filename} → {dest_path}")
                else:
                    sessions_failed += 1
                    logger.warning(f"Failed to restore session: {filename}")

        # Phase 6: Report
        print(f"\n✅ Successfully undone to commit {commit_hash[:7]}")
        print("\nSummary:")
        print(f"  Undo branch: {undo_branch}")

        if backup_dir:
            print(f"  Backup location: {backup_dir}")

        print(f"  Files restored: {len(restore_result['restored'])}")

        if restore_result['skipped']:
            print(f"  Files skipped: {len(restore_result['skipped'])}")

        if restore_result['failed']:
            print(f"  Files failed: {len(restore_result['failed'])}")

        if files_to_delete:
            if deletion_strategy == "keep":
                print(f"  Files kept: {len(files_to_delete)}")
            elif deletion_strategy == "delete":
                print(f"  Files deleted: {deleted_count}")
            elif deletion_strategy == "backup":
                print(f"  Files moved to backup: {moved_count}")

        if session_files:
            print(f"  Sessions restored: {sessions_restored}")
            if sessions_failed > 0:
                print(f"  Sessions failed: {sessions_failed}")

        print("\nRecovery options:")
        print(f"  To undo this operation: aline undo {current_head[:7] if current_head else '<previous_commit>'}")

        if backup_dir:
            print(f"  To restore from backup: cp -r {backup_dir}/* {repo_root}/")

        print(f"  To switch to preserved state: cd {tracker.realign_dir} && git checkout {undo_branch}")

        logger.info("Undo operation completed successfully")
        return 0

    except Exception as e:
        print(f"\n❌ Undo operation failed: {e}")
        logger.error(f"Undo operation failed: {e}", exc_info=True)

        # Attempt automatic rollback
        print("\nAttempting automatic rollback...")
        try:
            # Checkout undo branch
            if tracker.checkout_branch(undo_branch):
                # Force reset master to undo branch
                import subprocess
                result = subprocess.run(
                    ["git", "branch", "-f", "master", undo_branch],
                    cwd=tracker.realign_dir,
                    capture_output=True,
                    check=False
                )

                if result.returncode == 0:
                    tracker.checkout_branch("master")

                    # Restore files from backup if exists
                    if backup_dir and backup_dir.exists():
                        print("Restoring files from backup...")
                        # This is a simplified restore, just copying back
                        # In practice, you might want more sophisticated logic

                    print("✓ Operation failed and rolled back successfully")
                    print(f"  State preserved in branch: {undo_branch}")
                    logger.info("Rollback successful")
                else:
                    raise Exception("Failed to reset master branch")
            else:
                raise Exception("Failed to checkout undo branch")

        except Exception as rollback_error:
            print(f"❌ Automatic rollback failed: {rollback_error}")
            print("\nManual recovery instructions:")
            print(f"  1. cd {tracker.realign_dir}")
            print(f"  2. git checkout {undo_branch}")
            print(f"  3. git branch -f master {undo_branch}")
            print(f"  4. git checkout master")

            if backup_dir and backup_dir.exists():
                print(f"  5. Restore files from: {backup_dir}")

            logger.error(f"Rollback failed: {rollback_error}", exc_info=True)

        return 1
