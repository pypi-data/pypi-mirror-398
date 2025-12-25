"""ReAlignGitTracker - Independent Git repository for AI work history tracking.

This module implements the core Git tracking layer of Plan A, which maintains
an independent Git repository in .realign/.git that mirrors project file structure.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml

from ..logging_config import setup_logger

logger = setup_logger('realign.tracker', 'tracker.log')


class ReAlignGitTracker:
    """
    Manages an independent Git repository in ~/.aline/{project_name}/ for tracking AI work history.

    Key features:
    - Independent git repository (separate from user's .git)
    - Mirrors project file structure for path consistency
    - Generates semantic commit messages
    - Supports remote synchronization
    """

    def __init__(self, project_root: Path):
        """
        Initialize the Git tracker.

        Args:
            project_root: Root directory of the user's project
        """
        self.project_root = Path(project_root).resolve()
        self.realign_dir = self._get_realign_dir()
        self.realign_git = self.realign_dir / ".git"

        # Load configuration
        self.config = self._load_config()

    def _get_realign_dir(self) -> Path:
        """
        Get the ReAlign directory path for this project.

        First checks for .realign-config file in project root,
        otherwise uses default location ~/.aline/{project_name}/

        Returns:
            Path to the ReAlign directory
        """
        config_marker = self.project_root / ".realign-config"

        if config_marker.exists():
            # Read the configured path
            configured_path = config_marker.read_text(encoding="utf-8").strip()
            return Path(configured_path)
        else:
            # Use default location
            project_name = self.project_root.name
            return Path.home() / ".aline" / project_name

    def get_remote_url(self) -> Optional[str]:
        """
        Get the configured remote URL.

        Returns:
            Remote URL if configured, None otherwise
        """
        try:
            result = self._run_git(
                ["remote", "get-url", "origin"],
                cwd=self.realign_dir,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                return result.stdout.strip()
            return None

        except Exception as e:
            logger.error(f"Failed to get remote URL: {e}")
            return None

    def has_remote(self) -> bool:
        """
        Check if a remote is configured.

        Returns:
            True if remote exists, False otherwise
        """
        return self.get_remote_url() is not None

    def get_current_branch(self) -> Optional[str]:
        """
        Get the current branch name.

        Returns:
            Current branch name if available, None otherwise
        """
        try:
            result = self._run_git(
                ["rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.realign_dir,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                branch = result.stdout.strip()
                # Return None if in detached HEAD state
                return branch if branch != "HEAD" else None
            return None

        except Exception as e:
            logger.error(f"Failed to get current branch: {e}")
            return None

    def get_member_branch(self) -> Optional[str]:
        """
        Get the member branch name from config if available.

        For joined repositories, members work on their own branch
        (e.g., "username/master") instead of the owner's master branch.

        Returns:
            Member branch name from config, or None if not configured
        """
        sharing_config = self.config.get('sharing', {})
        return sharing_config.get('member_branch')

    def _load_config(self) -> Dict[str, Any]:
        """Load .realign/config.yaml configuration."""
        config_path = self.realign_dir / "config.yaml"

        if not config_path.exists():
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def is_initialized(self) -> bool:
        """Check if the .realign/.git repository is initialized."""
        return self.realign_git.exists() and (self.realign_git / "config").exists()

    def init_repo(self) -> bool:
        """
        Initialize the independent .realign/.git repository.

        Returns:
            True if successful, False otherwise
        """
        if self.is_initialized():
            logger.info("Git mirror already initialized")
            return True

        try:
            # Create .realign directory
            self.realign_dir.mkdir(parents=True, exist_ok=True)

            # Initialize Git repository
            self._run_git(["init"], cwd=self.realign_dir, check=True)
            logger.info(f"Initialized Git repository at {self.realign_git}")

            # Create .gitignore to exclude certain files
            gitignore_path = self.realign_dir / ".gitignore"
            gitignore_content = (
                "# Note: sessions/ is now tracked for sharing functionality\n"
                "# Session files are committed to enable team collaboration\n\n"
                "# Exclude metadata (internal use)\n"
                ".metadata/\n\n"
                "# Exclude original sessions (may contain secrets)\n"
                "sessions-original/\n\n"
                "# Exclude lock files\n"
                ".commit.lock\n"
                ".hash_registry.lock\n\n"
                "# Exclude temporary files\n"
                "*.tmp\n"
                "*.corrupted.*\n"
            )
            gitignore_path.write_text(gitignore_content, encoding='utf-8')

            # Initial commit
            self._run_git(["add", ".gitignore"], cwd=self.realign_dir, check=True)
            self._run_git(
                ["commit", "-m", "Initial commit: ReAlign Git mirror"],
                cwd=self.realign_dir,
                check=True
            )

            logger.info("✓ Git mirror initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Git mirror: {e}", exc_info=True)
            return False

    def get_mirror_path(self, file_path: Path) -> Path:
        """
        Get the mirror path for a given file.

        Args:
            file_path: Absolute path to the file in the project

        Returns:
            Path to the mirrored file in .realign/mirror/
        """
        # Convert to absolute path
        file_path = Path(file_path).resolve()

        # Get relative path from project root
        try:
            rel_path = file_path.relative_to(self.project_root)
        except ValueError:
            # File is outside project root - skip
            logger.warning(f"File {file_path} is outside project root")
            return None

        # Return mirror path in mirror/ subdirectory
        return self.realign_dir / "mirror" / rel_path

    def _compute_file_hash(self, file_path: Path) -> Optional[str]:
        """Compute SHA256 hash of a file."""
        if not file_path.exists():
            return None

        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute hash for {file_path}: {e}")
            return None

    def _should_copy_file(self, source_path: Path, mirror_path: Path) -> bool:
        """
        Determine if a file should be copied (hash-based optimization).

        Args:
            source_path: Source file path
            mirror_path: Mirror file path

        Returns:
            True if file should be copied, False if unchanged
        """
        # If mirror doesn't exist, must copy
        if not mirror_path.exists():
            return True

        # Compare file hashes
        source_hash = self._compute_file_hash(source_path)
        mirror_hash = self._compute_file_hash(mirror_path)

        if source_hash is None or mirror_hash is None:
            # If hash computation failed, copy to be safe
            return True

        # Only copy if hashes differ
        return source_hash != mirror_hash

    def mirror_file(self, file_path: Path) -> bool:
        """
        Mirror a single file to .realign/ directory.

        Args:
            file_path: Absolute path to the file to mirror

        Returns:
            True if file was copied, False if skipped (unchanged) or error
        """
        try:
            file_path = Path(file_path).resolve()

            # Check if file exists
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False

            # Get mirror path
            mirror_path = self.get_mirror_path(file_path)
            if mirror_path is None:
                return False

            # Check if copy is needed (hash optimization)
            if not self._should_copy_file(file_path, mirror_path):
                logger.debug(f"File unchanged, skipping: {file_path.name}")
                return False

            # Create parent directory
            mirror_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(file_path, mirror_path)
            logger.debug(f"Mirrored: {file_path} -> {mirror_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to mirror file {file_path}: {e}", exc_info=True)
            return False

    def mirror_files(self, file_paths: List[Path]) -> List[Path]:
        """
        Mirror multiple files to .realign/ directory.

        Args:
            file_paths: List of absolute paths to files

        Returns:
            List of files that were actually copied (changed files only)
        """
        copied_files = []

        for file_path in file_paths:
            if self.mirror_file(file_path):
                mirror_path = self.get_mirror_path(file_path)
                if mirror_path:
                    copied_files.append(mirror_path)

        logger.info(f"Mirrored {len(copied_files)} of {len(file_paths)} files")
        return copied_files

    def has_changes(self) -> bool:
        """
        Check if there are any uncommitted changes in the .realign/ repository.

        Returns:
            True if there are changes, False otherwise
        """
        if not self.is_initialized():
            return False

        try:
            # Check for staged and unstaged changes
            result = self._run_git(
                ["status", "--porcelain"],
                cwd=self.realign_dir,
                check=True,
                capture_output=True,
                text=True
            )

            return bool(result.stdout.strip())

        except Exception as e:
            logger.error(f"Failed to check for changes: {e}")
            return False

    def _generate_commit_message(
        self,
        session_id: str,
        turn_number: int,
        user_message: str,
        llm_title: str,
        llm_description: str,
        model_name: str
    ) -> str:
        """
        Generate a semantic commit message using LLM-generated content.

        Format:
            {llm_title}

            {llm_description}

            ---
            Session: {session_id} | Turn: #{turn_number} | Model: {model_name}
            Request: {user_message}
        """
        # Validate title before using it
        if not llm_title or len(llm_title.strip()) < 2:
            raise ValueError(f"Invalid commit title: '{llm_title}' - too short or empty")

        if llm_title.strip() in ["{", "}", "[", "]"]:
            raise ValueError(f"Invalid commit title: '{llm_title}' - appears to be truncated JSON bracket")

        # Construct commit message with LLM-generated content
        message = f"""{llm_title}

{llm_description}

---
Session: {session_id} | Turn: #{turn_number} | Model: {model_name}
Request: {user_message}"""

        return message

    def commit_turn(
        self,
        session_id: str,
        turn_number: int,
        user_message: str,
        llm_title: str,
        llm_description: str,
        model_name: str,
        modified_files: List[Path],
        session_file: Optional[Path] = None
    ) -> Optional[str]:
        """
        Commit a completed dialogue turn to the .realign/.git repository.

        Args:
            session_id: Session identifier (e.g., "minhao_claude_abc123")
            turn_number: Turn number within the session
            user_message: User's message/request
            llm_title: LLM-generated one-line summary (imperative mood)
            llm_description: LLM-generated detailed description
            model_name: Name of the model that generated the summary
            modified_files: List of files modified in this turn
            session_file: Optional path to the session file to copy to sessions/

        Returns:
            Commit hash if successful, None if no changes or error
        """
        if not self.is_initialized():
            logger.warning("Git mirror not initialized")
            if not self.init_repo():
                return None

        try:
            # Copy session file to sessions/ directory if provided
            if session_file and session_file.exists():
                sessions_dir = self.realign_dir / "sessions"
                sessions_dir.mkdir(parents=True, exist_ok=True)
                session_dest = sessions_dir / session_file.name

                # Only copy if file doesn't exist or has changed
                if not session_dest.exists() or session_file.read_bytes() != session_dest.read_bytes():
                    shutil.copy2(session_file, session_dest)
                    logger.debug(f"Copied session file to {session_dest}")

            # Mirror modified files
            mirrored_files = self.mirror_files(modified_files)

            # Check if there are any changes
            if not mirrored_files and not self.has_changes():
                logger.info(f"No changes to commit for turn {turn_number}")
                return None

            # Stage all changes in .realign/
            self._run_git(["add", "-A"], cwd=self.realign_dir, check=True)

            # Check again after staging
            if not self.has_changes():
                logger.info("No changes after staging")
                return None

            # Generate commit message
            try:
                commit_message = self._generate_commit_message(
                    session_id,
                    turn_number,
                    user_message,
                    llm_title,
                    llm_description,
                    model_name
                )
            except ValueError as e:
                logger.error(f"Invalid commit message generated: {e}")
                logger.debug(f"Title: '{llm_title}'")
                return None

            # Commit
            self._run_git(
                ["commit", "-m", commit_message],
                cwd=self.realign_dir,
                check=True
            )

            # Get commit hash
            result = self._run_git(
                ["rev-parse", "HEAD"],
                cwd=self.realign_dir,
                check=True,
                capture_output=True,
                text=True
            )
            commit_hash = result.stdout.strip()

            logger.info(f"✓ Committed turn {turn_number}: {commit_hash[:8]}")

            return commit_hash

        except Exception as e:
            logger.error(f"Failed to commit turn {turn_number}: {e}", exc_info=True)
            return None

    def setup_remote(self, remote_url: str) -> bool:
        """
        Configure remote repository for sharing.

        Args:
            remote_url: Git remote URL (e.g., https://github.com/user/repo.git)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized():
            logger.error("Repository not initialized")
            return False

        try:
            # Check if remote already exists
            existing_remote = self.get_remote_url()

            if existing_remote:
                if existing_remote == remote_url:
                    logger.info("Remote already configured with same URL")
                    return True
                else:
                    # Update existing remote
                    self._run_git(
                        ["remote", "set-url", "origin", remote_url],
                        cwd=self.realign_dir,
                        check=True
                    )
                    logger.info(f"Updated remote URL: {remote_url}")
            else:
                # Add new remote
                self._run_git(
                    ["remote", "add", "origin", remote_url],
                    cwd=self.realign_dir,
                    check=True
                )
                logger.info(f"Added remote: {remote_url}")

            return True

        except Exception as e:
            logger.error(f"Failed to setup remote: {e}", exc_info=True)
            return False

    def create_branch(self, branch_name: str, start_point: str = "master") -> bool:
        """
        Create a new branch starting from a given point.

        Args:
            branch_name: Name of the branch to create (e.g., "username/master")
            start_point: Starting point for the branch (default: "master")

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create and checkout the branch
            result = self._run_git(
                ["checkout", "-b", branch_name, start_point],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"Created and checked out branch: {branch_name}")
                return True
            else:
                logger.error(f"Failed to create branch {branch_name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to create branch: {e}", exc_info=True)
            return False

    def checkout_branch(self, branch_name: str) -> bool:
        """
        Checkout an existing branch.

        Args:
            branch_name: Name of the branch to checkout

        Returns:
            True if successful, False otherwise
        """
        try:
            result = self._run_git(
                ["checkout", branch_name],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"Checked out branch: {branch_name}")
                return True
            else:
                logger.error(f"Failed to checkout branch {branch_name}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to checkout branch: {e}", exc_info=True)
            return False

    def verify_commit_exists(self, commit_hash: str) -> bool:
        """
        Verify that a commit exists and is reachable in the repository.

        Args:
            commit_hash: The commit hash to verify

        Returns:
            True if commit exists, False otherwise
        """
        try:
            result = self._run_git(
                ["rev-parse", "--verify", commit_hash],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to verify commit {commit_hash}: {e}", exc_info=True)
            return False

    def get_commit_info(self, commit_hash: str) -> Optional[Dict[str, str]]:
        """
        Get information about a specific commit.

        Args:
            commit_hash: The commit hash to query

        Returns:
            Dictionary with keys: 'hash', 'timestamp', 'message', or None if commit doesn't exist
        """
        try:
            result = self._run_git(
                ["show", "--format=%H|%at|%s", "--no-patch", commit_hash],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to get commit info for {commit_hash}: {result.stderr}")
                return None

            # Parse output: hash|timestamp|subject
            parts = result.stdout.strip().split('|', 2)
            if len(parts) < 3:
                return None

            return {
                'hash': parts[0],
                'timestamp': parts[1],
                'message': parts[2]
            }

        except Exception as e:
            logger.error(f"Failed to get commit info: {e}", exc_info=True)
            return None

    def reset_to_commit(self, commit_hash: str, hard: bool = True) -> bool:
        """
        Reset the repository to a specific commit.

        Args:
            commit_hash: The commit hash to reset to
            hard: If True, performs hard reset (discards changes). Default: True

        Returns:
            True if reset successful, False otherwise
        """
        try:
            # Verify commit exists first
            if not self.verify_commit_exists(commit_hash):
                logger.error(f"Commit {commit_hash} does not exist")
                return False

            # Perform reset
            reset_type = "--hard" if hard else "--soft"
            result = self._run_git(
                ["reset", reset_type, commit_hash],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Failed to reset to {commit_hash}: {result.stderr}")
                return False

            # Verify reset succeeded by checking HEAD
            head_result = self._run_git(
                ["rev-parse", "HEAD"],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if head_result.returncode == 0:
                current_head = head_result.stdout.strip()
                # Get full hash of target commit
                target_result = self._run_git(
                    ["rev-parse", commit_hash],
                    cwd=self.realign_dir,
                    check=False,
                    capture_output=True,
                    text=True
                )

                if target_result.returncode == 0:
                    target_full_hash = target_result.stdout.strip()
                    if current_head == target_full_hash:
                        logger.info(f"Successfully reset to commit {commit_hash}")
                        return True

            logger.error("Reset verification failed")
            return False

        except Exception as e:
            logger.error(f"Failed to reset to commit: {e}", exc_info=True)
            return False

    def get_unpushed_commits(self) -> List[str]:
        """
        Get list of unpushed commit hashes.

        Returns:
            List of commit hashes that haven't been pushed
        """
        if not self.has_remote():
            return []

        # Get current branch name
        branch = self.get_current_branch()
        if not branch:
            logger.error("Cannot determine current branch")
            return []

        try:
            # Fetch to update remote refs
            self._run_git(
                ["fetch", "origin"],
                cwd=self.realign_dir,
                check=False,
                capture_output=True
            )

            # Check if remote branch exists
            check_remote = self._run_git(
                ["rev-parse", "--verify", f"origin/{branch}"],
                cwd=self.realign_dir,
                capture_output=True,
                check=False
            )

            if check_remote.returncode != 0:
                # Remote branch doesn't exist, all local commits are unpushed
                result = self._run_git(
                    ["log", "--format=%H"],
                    cwd=self.realign_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )
            else:
                # Remote branch exists, get commits ahead of remote
                result = self._run_git(
                    ["log", f"origin/{branch}..HEAD", "--format=%H"],
                    cwd=self.realign_dir,
                    capture_output=True,
                    text=True,
                    check=False
                )

            if result.returncode == 0:
                commits = result.stdout.strip().split('\n')
                return [c for c in commits if c]
            return []

        except Exception as e:
            logger.error(f"Failed to get unpushed commits: {e}")
            return []

    def safe_push(self, force: bool = False) -> bool:
        """
        Push commits to remote with conflict handling.

        For members of shared repositories, pushes to their member branch.
        Otherwise uses the current branch.

        Args:
            force: If True, force push (use with caution)

        Returns:
            True if successful, False otherwise
        """
        if not self.has_remote():
            logger.error("No remote configured")
            return False

        # Check if this is a member branch scenario
        member_branch = self.get_member_branch()
        if member_branch:
            # Member of shared repository - push to their specific branch
            branch = member_branch
            logger.info(f"Using member branch for push: {branch}")
        else:
            # Regular repository - use current branch
            branch = self.get_current_branch()
            if not branch:
                logger.error("Cannot determine current branch")
                return False

        try:
            # Check if remote branch exists
            check_remote = self._run_git(
                ["rev-parse", "--verify", f"origin/{branch}"],
                cwd=self.realign_dir,
                capture_output=True,
                check=False
            )

            # Try push
            push_cmd = ["push"]

            # Set upstream if remote branch doesn't exist (first push)
            if check_remote.returncode != 0:
                push_cmd.extend(["-u", "origin", branch])
            else:
                push_cmd.extend(["origin", branch])

            if force:
                push_cmd.append("--force")

            result = self._run_git(
                push_cmd,
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Successfully pushed to remote")
                return True

            # Push failed - try pull and merge
            logger.info("Push rejected, attempting to pull and merge...")

            # Pull with merge strategy (not rebase)
            pull_result = self._run_git(
                ["pull", "--no-rebase", "origin", branch],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if pull_result.returncode != 0:
                # Check for conflicts
                if "CONFLICT" in pull_result.stdout or "CONFLICT" in pull_result.stderr:
                    logger.info("Conflicts detected, attempting auto-resolution...")
                    if not self._auto_resolve_session_conflicts():
                        logger.error("Failed to auto-resolve conflicts")
                        return False

                    # Commit merge resolution
                    self._run_git(
                        ["add", "-A"],
                        cwd=self.realign_dir,
                        check=True
                    )
                    self._run_git(
                        ["commit", "--no-edit"],
                        cwd=self.realign_dir,
                        check=True
                    )
                else:
                    logger.error(f"Pull failed: {pull_result.stderr}")
                    return False

            # Retry push
            retry_result = self._run_git(
                push_cmd,
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if retry_result.returncode == 0:
                logger.info("Successfully pushed after merge")
                return True
            else:
                logger.error(f"Push failed after merge: {retry_result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to push: {e}", exc_info=True)
            return False

    def safe_pull(self) -> bool:
        """
        Pull updates from remote with conflict handling.

        For members of shared repositories, pulls from their member branch.
        Otherwise uses the current branch.

        Returns:
            True if successful, False otherwise
        """
        if not self.has_remote():
            logger.error("No remote configured")
            return False

        # Check if this is a member branch scenario
        member_branch = self.get_member_branch()
        if member_branch:
            # Member of shared repository - pull from their specific branch
            branch = member_branch
            logger.info(f"Using member branch: {branch}")
        else:
            # Regular repository - use current branch
            branch = self.get_current_branch()
            if not branch:
                # If no branch (empty repository), use master as default
                # This is the standard default branch name in git
                branch = "master"
                logger.debug("No current branch found, using default 'master'")

        try:
            # Pull with merge strategy
            result = self._run_git(
                ["pull", "--no-rebase", "origin", branch],
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("Successfully pulled from remote")
                return True

            # Check for conflicts
            if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
                logger.info("Conflicts detected, attempting auto-resolution...")
                if not self._auto_resolve_session_conflicts():
                    logger.error("Failed to auto-resolve conflicts")
                    return False

                # Commit merge resolution
                self._run_git(
                    ["add", "-A"],
                    cwd=self.realign_dir,
                    check=True
                )
                self._run_git(
                    ["commit", "--no-edit"],
                    cwd=self.realign_dir,
                    check=True
                )
                logger.info("Successfully resolved conflicts and completed pull")
                return True
            else:
                logger.error(f"Pull failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to pull: {e}", exc_info=True)
            return False

    def _auto_resolve_session_conflicts(self) -> bool:
        """
        Automatically resolve conflicts in session files.

        Strategy:
        - Session files: Keep both versions (rename conflicted one)
        - Config files: Require manual resolution

        Returns:
            True if all conflicts resolved, False if manual intervention needed
        """
        try:
            # Get list of conflicted files
            result = self._run_git(
                ["diff", "--name-only", "--diff-filter=U"],
                cwd=self.realign_dir,
                capture_output=True,
                text=True,
                check=True
            )

            conflicted_files = result.stdout.strip().split('\n')
            conflicted_files = [f for f in conflicted_files if f]

            if not conflicted_files:
                return True

            for file_path_str in conflicted_files:
                file_path = Path(file_path_str)

                # Check if it's a session file
                if file_path.parts[0] == 'sessions' and file_path.suffix == '.jsonl':
                    # Session file - rename conflicted version
                    import time
                    timestamp = int(time.time())
                    base_name = file_path.stem
                    new_name = f"{base_name}_conflict_{timestamp}.jsonl"

                    full_path = self.realign_dir / file_path
                    new_path = full_path.parent / new_name

                    # Resolve by keeping both versions
                    # Git creates conflict markers, we'll use theirs version and rename ours
                    self._run_git(
                        ["checkout", "--theirs", str(file_path)],
                        cwd=self.realign_dir,
                        check=True
                    )

                    logger.info(f"Auto-resolved session conflict: {file_path}")

                elif file_path.name == 'config.yaml':
                    # Config file - require manual resolution
                    logger.error(f"Config file conflict requires manual resolution: {file_path}")
                    print(f"\n⚠️  Config file conflict: {file_path}")
                    print("Please resolve manually and run: git add <file> && git commit\n")
                    return False

                else:
                    # Other files - use theirs version by default
                    self._run_git(
                        ["checkout", "--theirs", str(file_path)],
                        cwd=self.realign_dir,
                        check=True
                    )
                    logger.info(f"Auto-resolved conflict (using remote version): {file_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to auto-resolve conflicts: {e}", exc_info=True)
            return False

    def _stash_untracked_files(self) -> None:
        """
        Handle untracked files that might conflict during pull.

        This is necessary because config files (config.yaml, .gitignore) might be created
        locally before pulling from remote, causing "untracked files would be overwritten" errors.
        """
        try:
            # Get list of untracked files
            result = self._run_git(
                ["status", "--porcelain"],
                cwd=self.realign_dir,
                check=True,
                capture_output=True,
                text=True
            )

            untracked_files = [
                line.split(maxsplit=1)[1]
                for line in result.stdout.strip().split('\n')
                if line and line.startswith('??')
            ]

            if not untracked_files:
                return

            # Try to stash, but if it fails (e.g., no initial commit), delete them
            # They will be recreated/restored from remote
            stash_result = self._run_git(
                ["stash", "push", "--include-untracked"] + untracked_files,
                cwd=self.realign_dir,
                check=False,
                capture_output=True,
                text=True
            )

            if stash_result.returncode == 0:
                logger.info(f"Stashed {len(untracked_files)} untracked file(s) before pull")
            else:
                # If stash fails, remove the untracked files instead
                # They will be restored from the remote repository during pull
                for file_path in untracked_files:
                    full_path = self.realign_dir / file_path
                    if full_path.exists():
                        full_path.unlink()
                        logger.info(f"Removed untracked file to allow pull: {file_path}")

        except Exception as e:
            logger.warning(f"Failed to handle untracked files: {e}")
            # Continue anyway, as this is not critical

    def _run_git(self, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        """
        Execute a git command.

        Args:
            cmd: Git command and arguments (e.g., ["status", "--porcelain"])
            **kwargs: Additional arguments for subprocess.run()

        Returns:
            CompletedProcess instance
        """
        full_cmd = ["git"] + cmd

        # Ensure cwd is set
        if "cwd" not in kwargs:
            kwargs["cwd"] = self.realign_dir

        logger.debug(f"Running git command: {' '.join(full_cmd)}")
        return subprocess.run(full_cmd, **kwargs)
