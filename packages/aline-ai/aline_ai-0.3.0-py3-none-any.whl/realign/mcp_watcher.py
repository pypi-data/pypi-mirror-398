"""Session file watcher for MCP auto-commit per user request completion.

Supports both Claude Code and Codex session formats with unified interface.
"""

import asyncio
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Literal
from datetime import datetime

from .config import ReAlignConfig
from .hash_registry import HashRegistry
from .hooks import find_all_active_sessions
from .logging_config import setup_logger
from .tracker import ReAlignGitTracker
from .mirror_utils import collect_project_files

# Initialize logger for watcher
logger = setup_logger('realign.mcp_watcher', 'mcp_watcher.log')


# Session type detection
SessionType = Literal["claude", "codex", "unknown"]


def is_path_blacklisted(project_path: Path) -> bool:
    """
    Check if a project path is blacklisted for auto-init.

    Blacklisted paths:
    - Anything inside ~/.aline/ directories
    - User home directory itself (~)
    - ~/Desktop, ~/Documents, ~/Downloads (but allow subdirectories)

    Args:
        project_path: Absolute path to check

    Returns:
        True if blacklisted, False if allowed
    """
    try:
        # Normalize path (resolve symlinks, make absolute)
        normalized = project_path.resolve()
        home = Path.home().resolve()
        aline_dir = (home / ".aline").resolve()

        # Check if inside .aline directory
        try:
            normalized.relative_to(aline_dir)
            logger.debug(f"Blacklisted (inside .aline): {normalized}")
            return True
        except ValueError:
            pass  # Not inside .aline

        # Check if it IS the home directory itself
        if normalized == home:
            logger.debug(f"Blacklisted (home directory): {normalized}")
            return True

        # Check forbidden top-level home subdirectories
        # But allow their subdirectories (e.g., ~/Desktop/project is OK)
        forbidden_dirs = ["Desktop", "Documents", "Downloads"]
        for forbidden in forbidden_dirs:
            forbidden_path = (home / forbidden).resolve()
            if normalized == forbidden_path:
                logger.debug(f"Blacklisted (forbidden dir): {normalized}")
                return True

        return False

    except Exception as e:
        logger.error(f"Error checking blacklist for {project_path}: {e}")
        # If we can't determine, err on the side of caution
        return True


def decode_claude_project_path(project_dir_name: str) -> Optional[Path]:
    """
    Decode Claude Code project directory name to actual project path.

    Claude naming: -Users-huminhao-Projects-ReAlign
    Decoded: /Users/huminhao/Projects/ReAlign

    If naive decoding fails (e.g., paths with underscores/hyphens in directory names),
    falls back to reading the 'cwd' field from JSONL session files.

    Args:
        project_dir_name: Claude project directory name (or full path to Claude project dir)

    Returns:
        Decoded Path if valid, None otherwise
    """
    # Handle both directory name and full path
    if isinstance(project_dir_name, Path):
        project_dir = project_dir_name
        dir_name = project_dir.name
    elif '/' in project_dir_name:
        project_dir = Path(project_dir_name)
        dir_name = project_dir.name
    else:
        dir_name = project_dir_name
        project_dir = Path.home() / ".claude" / "projects" / dir_name

    if not dir_name.startswith('-'):
        return None

    # Try naive decoding first
    path_str = '/' + dir_name[1:].replace('-', '/')
    project_path = Path(path_str)

    if project_path.exists():
        return project_path

    # Naive decoding failed - try reading from JSONL files
    logger.debug(f"Naive decoding failed for {dir_name}, trying JSONL fallback")

    if not project_dir.exists() or not project_dir.is_dir():
        logger.debug(f"Claude project directory not found: {project_dir}")
        return None

    # Find any JSONL file (excluding agent files)
    try:
        jsonl_files = [
            f for f in project_dir.iterdir()
            if f.suffix == '.jsonl' and not f.name.startswith('agent-')
        ]

        if not jsonl_files:
            logger.debug(f"No JSONL session files found in {project_dir}")
            return None

        # Read lines from first JSONL file to find cwd field
        jsonl_file = jsonl_files[0]
        with jsonl_file.open('r', encoding='utf-8') as f:
            # Check up to first 20 lines for cwd field
            for i, line in enumerate(f):
                if i >= 20:
                    break

                line = line.strip()
                if not line:
                    continue

                session_data = json.loads(line)
                cwd = session_data.get('cwd')

                if cwd:
                    project_path = Path(cwd)
                    if project_path.exists():
                        logger.debug(f"Decoded path from JSONL: {dir_name} -> {project_path}")
                        return project_path
                    else:
                        logger.debug(f"Path from JSONL doesn't exist: {project_path}")
                        return None

            logger.debug(f"No 'cwd' field found in first 20 lines of {jsonl_file.name}")
            return None

    except Exception as e:
        logger.debug(f"Error reading JSONL files from {project_dir}: {e}")
        return None

    return None


def is_project_initialized(project_path: Path) -> bool:
    """
    Check if a project has been initialized with aline.

    Checks for:
    1. .aline-config marker in project root
    2. .aline directory existence
    3. .git repo inside .aline directory

    Args:
        project_path: Absolute path to project

    Returns:
        True if initialized, False otherwise
    """
    try:
        config_marker = project_path / ".aline-config"

        if not config_marker.exists():
            return False

        # Read configured .aline path
        realign_dir = Path(config_marker.read_text(encoding='utf-8').strip())

        # Check if .git exists inside
        git_config = realign_dir / ".git" / "config"
        return git_config.exists()

    except Exception as e:
        logger.debug(f"Error checking init status for {project_path}: {e}")
        return False


class DialogueWatcher:
    """Watch session files and auto-commit immediately after each user request completes."""

    def __init__(self):
        """Initialize watcher for multi-project monitoring - extracts project paths dynamically from sessions."""
        self.config = ReAlignConfig.load()
        self.last_commit_times: Dict[str, float] = {}  # Track last commit time per project
        self.last_session_sizes: Dict[str, int] = {}  # Track file sizes
        self.last_stop_reason_counts: Dict[str, int] = {}  # Track stop_reason counts per session
        self.last_session_mtimes: Dict[str, float] = {}  # Track last mtime of session files for idle detection
        self.last_final_commit_times: Dict[str, float] = {}  # Track when we last tried final commit per session
        self.last_committed_hashes: Dict[str, str] = {}  # Track content hash of last commit per session to prevent duplicates (DEPRECATED: use hash_registries instead)
        self.hash_registries: Dict[str, HashRegistry] = {}  # Persistent hash registries per project (lazy-loaded)
        self.min_commit_interval = 5.0  # Minimum 5 seconds between commits (cooldown)
        self.debounce_delay = 10.0  # Wait 10 seconds after file change to ensure turn is complete (increased from 2.0 to handle streaming responses)
        self.final_commit_idle_timeout = 300.0  # 5 minutes idle to trigger final commit
        self.running = False
        self.pending_commit_task: Optional[asyncio.Task] = None

        # Auto-init tracking
        self.failed_init_projects: set[str] = set()  # Projects that failed init
        self.last_auto_init_time: float = 0.0  # Last time we ran auto-init
        self.auto_init_interval: float = 5.0  # Run auto-init every 5 seconds

        # Git tracker will be initialized per-project dynamically in _do_commit_locked()
        self.git_tracker = None

    async def start(self):
        """Start watching session files."""
        if not self.config.mcp_auto_commit:
            logger.info("Auto-commit disabled in config")
            print("[MCP Watcher] Auto-commit disabled in config", file=sys.stderr)
            return

        self.running = True
        logger.info("Started watching for dialogue completion")
        logger.info(f"Mode: Multi-project monitoring (all Claude Code projects)")
        logger.info(f"Trigger: Per-request (at end of each AI response)")
        logger.info(f"Supports: Claude Code & Codex (auto-detected)")
        logger.info(f"Debounce: {self.debounce_delay}s, Cooldown: {self.min_commit_interval}s")
        print("[MCP Watcher] Started watching for dialogue completion", file=sys.stderr)
        print(f"[MCP Watcher] Mode: Multi-project monitoring (all Claude Code projects)", file=sys.stderr)
        print(f"[MCP Watcher] Trigger: Per-request (at end of each AI response)", file=sys.stderr)
        print(f"[MCP Watcher] Supports: Claude Code & Codex (auto-detected)", file=sys.stderr)
        print(f"[MCP Watcher] Debounce: {self.debounce_delay}s, Cooldown: {self.min_commit_interval}s", file=sys.stderr)

        # Initialize baseline sizes and stop_reason counts
        self.last_session_sizes = self._get_session_sizes()
        self.last_stop_reason_counts = self._get_stop_reason_counts()

        # Note: Idle timeout checking is now integrated into main loop instead of separate task

        # Run initial auto-init
        logger.info("Running initial auto-init scan")
        print("[MCP Watcher] Running initial auto-init scan", file=sys.stderr)
        await self.auto_init_projects()
        self.last_auto_init_time = time.time()

        # Start periodic auto-init task
        asyncio.create_task(self.run_periodic_auto_init())

        # Poll for file changes more frequently
        while self.running:
            try:
                await self.check_for_changes()

                # Check for idle sessions that need final commit
                await self._check_idle_sessions_for_final_commit()

                await asyncio.sleep(0.5)  # Check every 0.5 seconds for responsiveness
            except Exception as e:
                logger.error(f"Error in check loop: {e}", exc_info=True)
                print(f"[MCP Watcher] Error: {e}", file=sys.stderr)
                await asyncio.sleep(1.0)

    async def stop(self):
        """Stop watching."""
        self.running = False
        if self.pending_commit_task:
            self.pending_commit_task.cancel()
        logger.info("Watcher stopped")
        print("[MCP Watcher] Stopped", file=sys.stderr)

    def _get_session_sizes(self) -> Dict[str, int]:
        """Get current sizes of all active session files across all projects."""
        sizes = {}
        try:
            # Always use multi-project mode (project_path=None)
            session_files = find_all_active_sessions(self.config, project_path=None)
            for session_file in session_files:
                if session_file.exists():
                    sizes[str(session_file)] = session_file.stat().st_size
            logger.debug(f"Tracked {len(sizes)} session file(s) across all projects")
        except Exception as e:
            logger.error(f"Error getting session sizes: {e}", exc_info=True)
            print(f"[MCP Watcher] Error getting session sizes: {e}", file=sys.stderr)
        return sizes

    def _get_stop_reason_counts(self) -> Dict[str, int]:
        """Get current count of turn completion markers in all active session files across all projects."""
        counts = {}
        try:
            # Always use multi-project mode (project_path=None)
            session_files = find_all_active_sessions(self.config, project_path=None)
            for session_file in session_files:
                if session_file.exists():
                    counts[str(session_file)] = self._count_complete_turns(session_file)
        except Exception as e:
            print(f"[MCP Watcher] Error getting turn counts: {e}", file=sys.stderr)
        return counts

    def _get_file_hash(self, session_file: Path) -> Optional[str]:
        """Compute MD5 hash of session file for duplicate detection."""
        try:
            with open(session_file, 'rb') as f:
                md5_hash = hashlib.md5()
                while chunk := f.read(8192):
                    md5_hash.update(chunk)
                return md5_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute hash for {session_file.name}: {e}")
            return None

    async def _check_idle_sessions_for_final_commit(self):
        """Check for idle sessions and trigger final commits if needed."""
        try:
            current_time = time.time()
            # Always use multi-project mode (project_path=None)
            session_files = find_all_active_sessions(self.config, project_path=None)

            for session_file in session_files:
                if not session_file.exists():
                    continue

                session_path = str(session_file)

                try:
                    # Get current mtime
                    mtime = session_file.stat().st_mtime

                    # Initialize tracking if first time seeing this session
                    if session_path not in self.last_session_mtimes:
                        self.last_session_mtimes[session_path] = mtime
                        continue

                    last_mtime = self.last_session_mtimes[session_path]

                    # If file was modified, update mtime and skip
                    if mtime > last_mtime:
                        self.last_session_mtimes[session_path] = mtime
                        # Reset final commit attempt time when file changes
                        self.last_final_commit_times.pop(session_path, None)
                        continue

                    # Check if session has been idle long enough
                    time_since_change = current_time - last_mtime
                    if time_since_change >= self.final_commit_idle_timeout:
                        # Check if we've already tried final commit recently
                        last_attempt = self.last_final_commit_times.get(session_path, 0)
                        if current_time - last_attempt < 60:  # Don't try more than once per minute
                            continue

                        # Check if there are any new turns since last commit
                        current_count = self._count_complete_turns(session_file)
                        last_count = self.last_stop_reason_counts.get(session_path, 0)

                        if current_count <= last_count:
                            # No new content since last commit, skip
                            logger.debug(f"No new turns in {session_file.name} (count: {current_count}), skipping idle commit")
                            # Mark as attempted to avoid checking again soon
                            self.last_final_commit_times[session_path] = current_time
                            continue

                        # Try to trigger final commit
                        logger.info(f"Session {session_file.name} idle for {time_since_change:.0f}s with {current_count - last_count} new turn(s), attempting final commit")
                        print(f"[MCP Watcher] Session idle for {time_since_change:.0f}s - triggering final commit", file=sys.stderr)

                        project_path = self._extract_project_path(session_file)
                        if project_path:
                            # Check cooldown
                            project_key = str(project_path)
                            last_commit_time = self.last_commit_times.get(project_key)

                            if not last_commit_time or (current_time - last_commit_time) >= self.min_commit_interval:
                                # Trigger commit via executor to avoid blocking
                                result = await asyncio.get_event_loop().run_in_executor(
                                    None,
                                    self._run_realign_commit,
                                    project_path
                                )

                                if result:
                                    logger.info(f"✓ Final commit completed for {project_path.name}")
                                    print(f"[MCP Watcher] ✓ Final commit completed for {project_path.name}", file=sys.stderr)
                                    self.last_commit_times[project_key] = current_time

                                    # Update turn count baseline after successful commit
                                    self.last_stop_reason_counts[session_path] = current_count
                                    logger.debug(f"Updated turn count baseline for {session_file.name}: {current_count}")

                                # Record attempt time
                                self.last_final_commit_times[session_path] = current_time

                except Exception as e:
                    logger.warning(f"Error checking idle status for {session_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error in idle session check: {e}", exc_info=True)

    def _extract_project_path(self, session_file: Path) -> Optional[Path]:
        """
        Extract project path (cwd) from session file.

        Supports:
        1. Codex: Read cwd from session_meta payload
        2. Claude Code: Read cwd from message objects OR infer from project directory name

        Args:
            session_file: Path to session file

        Returns:
            Path to project directory, or None if cannot determine
        """
        try:
            # Method 1: Try to read cwd from session content
            with open(session_file, 'r', encoding='utf-8') as f:
                # Check first 10 lines for cwd field
                for i, line in enumerate(f):
                    if i >= 10:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Codex format: session_meta.payload.cwd
                        if data.get('type') == 'session_meta':
                            cwd = data.get('payload', {}).get('cwd')
                            if cwd:
                                project_path = Path(cwd)
                                if project_path.exists():
                                    return project_path

                        # Claude Code format: message object has cwd field
                        if 'cwd' in data:
                            cwd = data['cwd']
                            if cwd:
                                project_path = Path(cwd)
                                if project_path.exists():
                                    return project_path

                    except json.JSONDecodeError:
                        continue

            # Method 2: For Claude Code, infer from project directory name
            # ~/.claude/projects/-Users-huminhao-Projects-ReAlign/xxx.jsonl
            if '.claude/projects/' in str(session_file):
                project_dir_name = session_file.parent.name
                if project_dir_name.startswith('-'):
                    # Decode: -Users-huminhao-Projects-ReAlign -> /Users/huminhao/Projects/ReAlign
                    project_path_str = '/' + project_dir_name[1:].replace('-', '/')
                    project_path = Path(project_path_str)
                    if project_path.exists() and (project_path / '.git').exists():
                        return project_path

            print(f"[MCP Watcher] Could not extract project path from {session_file.name}", file=sys.stderr)
            return None

        except Exception as e:
            print(f"[MCP Watcher] Error extracting project path from {session_file}: {e}", file=sys.stderr)
            return None

    def _detect_session_type(self, session_file: Path) -> SessionType:
        """
        Detect the type of session file by examining its structure.

        Returns:
            "claude" for Claude Code sessions
            "codex" for Codex/GPT sessions
            "unknown" if cannot determine
        """
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                # Check first 20 lines for format indicators
                for i, line in enumerate(f):
                    if i >= 20:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Claude Code format: {type: "assistant", message: {...}}
                        if data.get("type") in ("assistant", "user") and "message" in data:
                            return "claude"

                        # Codex format: {type: "session_meta", payload: {originator: "codex_*"}}
                        if data.get("type") == "session_meta":
                            payload = data.get("payload", {})
                            if "codex" in payload.get("originator", "").lower():
                                return "codex"

                        # Codex format: {type: "response_item", payload: {...}}
                        if data.get("type") == "response_item":
                            payload = data.get("payload", {})
                            # Claude has "message" wrapper, Codex doesn't
                            if "message" not in data and "role" in payload:
                                return "codex"

                    except json.JSONDecodeError:
                        continue

            return "unknown"

        except Exception as e:
            print(f"[MCP Watcher] Error detecting session type for {session_file.name}: {e}", file=sys.stderr)
            return "unknown"

    def _count_complete_turns(self, session_file: Path) -> int:
        """
        Unified interface to count complete dialogue turns for any session type.

        Automatically detects session format and uses appropriate counting method.

        Returns:
            Number of complete dialogue turns (user request + assistant response)
        """
        session_type = self._detect_session_type(session_file)

        if session_type == "claude":
            return self._count_claude_turns(session_file)
        elif session_type == "codex":
            return self._count_codex_turns(session_file)
        else:
            print(f"[MCP Watcher] Unknown session type for {session_file.name}, skipping", file=sys.stderr)
            return 0

    def _count_claude_turns(self, session_file: Path) -> int:
        """
        Count complete dialogue turns for Claude Code sessions.

        Strategy:
        - Count unique user messages by timestamp (not UUID)
        - Claude Code 2.0 sometimes splits one user message into multiple entries
          with different UUIDs but the same timestamp
        - Excludes tool results (type="tool_result")
        - This represents the number of user requests that have been sent
        """
        user_message_timestamps = set()

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        msg_type = data.get("type")

                        # Count user messages (excluding tool results)
                        if msg_type == "user":
                            message = data.get("message", {})
                            content = message.get("content", [])

                            # Check if this is a tool result (has tool_use_id)
                            is_tool_result = False
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "tool_result":
                                        is_tool_result = True
                                        break

                            # Only count non-tool-result user messages
                            # Use timestamp instead of UUID to handle split messages
                            if not is_tool_result:
                                timestamp = data.get("timestamp")
                                if timestamp:
                                    user_message_timestamps.add(timestamp)

                    except json.JSONDecodeError:
                        continue

            logger.debug(f"Counted {len(user_message_timestamps)} user messages in {session_file.name}")
            return len(user_message_timestamps)

        except Exception as e:
            logger.error(f"Error counting Claude turns in {session_file}: {e}", exc_info=True)
            print(f"[MCP Watcher] Error counting Claude turns in {session_file}: {e}", file=sys.stderr)
            return 0


    def _count_codex_turns(self, session_file: Path) -> int:
        """
        Count complete dialogue turns for Codex sessions.

        Uses 'token_count' event_msg as the marker for dialogue turn completion.
        Each token_count event appears after an assistant response finishes.

        Note: Codex doesn't have the duplicate write issue that Claude Code has,
        so no deduplication is needed.
        """
        count = 0
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # Look for token_count events which mark turn completion
                        if data.get("type") == "event_msg":
                            payload = data.get("payload", {})
                            if payload.get("type") == "token_count":
                                count += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"[MCP Watcher] Error counting Codex turns in {session_file}: {e}", file=sys.stderr)
        return count

    async def check_for_changes(self):
        """Check if any session file has been modified."""
        try:
            current_sizes = self._get_session_sizes()

            # Detect changed files
            changed_files = []
            for path, size in current_sizes.items():
                old_size = self.last_session_sizes.get(path, 0)
                if size > old_size:
                    changed_files.append(Path(path))
                    logger.debug(f"Session file changed: {Path(path).name} ({old_size} -> {size} bytes)")

            if changed_files:
                logger.info(f"Detected changes in {len(changed_files)} session file(s), scheduling commit check")
                # File changed - cancel any pending commit and schedule a new one
                if self.pending_commit_task:
                    logger.debug("Cancelling pending commit task")
                    self.pending_commit_task.cancel()

                # Wait for debounce period to ensure the turn is complete
                self.pending_commit_task = asyncio.create_task(
                    self._debounced_commit(changed_files)
                )

            # Update tracked sizes
            self.last_session_sizes = current_sizes

        except Exception as e:
            logger.error(f"Error checking for changes: {e}", exc_info=True)
            print(f"[MCP Watcher] Error checking for changes: {e}", file=sys.stderr)

    async def _debounced_commit(self, changed_files: list):
        """Wait for debounce period, then check if dialogue is complete and commit."""
        try:
            # Wait for debounce period
            await asyncio.sleep(self.debounce_delay)

            # Check if any of the changed files contains a complete dialogue turn
            # And collect the session file that triggered the commit
            session_to_commit = None
            for session_file in changed_files:
                if await self._check_if_turn_complete(session_file):
                    session_to_commit = session_file
                    logger.info(f"Complete turn detected in {session_file.name}")
                    print(f"[MCP Watcher] Complete turn detected in {session_file.name}", file=sys.stderr)
                    break

            if session_to_commit:
                # Extract project path from the session file
                project_path = self._extract_project_path(session_to_commit)
                if not project_path:
                    logger.warning(f"Could not determine project path for {session_to_commit.name}, skipping commit")
                    print(f"[MCP Watcher] Could not determine project path for {session_to_commit.name}, skipping commit", file=sys.stderr)
                    return

                # Check cooldown period for this specific project
                current_time = time.time()
                project_key = str(project_path)
                last_commit_time = self.last_commit_times.get(project_key)
                if last_commit_time:
                    time_since_last = current_time - last_commit_time
                    if time_since_last < self.min_commit_interval:
                        logger.info(f"Skipping commit for {project_path.name} (cooldown: {time_since_last:.1f}s < {self.min_commit_interval}s)")
                        print(f"[MCP Watcher] Skipping commit for {project_path.name} (cooldown: {time_since_last:.1f}s < {self.min_commit_interval}s)", file=sys.stderr)
                        return

                # Perform commit for this project
                logger.info(f"Triggering commit for {project_path.name}")
                await self._do_commit(project_path, session_to_commit)

        except asyncio.CancelledError:
            # Task was cancelled because a newer change was detected
            pass
        except Exception as e:
            print(f"[MCP Watcher] Error in debounced commit: {e}", file=sys.stderr)

    async def _check_if_turn_complete(self, session_file: Path) -> bool:
        """
        Check if the session file has at least 1 new complete dialogue turn since last check.

        Supports both Claude Code and Codex formats:
        - Claude Code: Count user messages by timestamp
        - Codex: Uses token_count events (no deduplication needed)

        Each complete dialogue round consists of:
        1. User message/request
        2. Assistant response
        3. Turn completion marker (format-specific)

        Note: This method does NOT update last_stop_reason_counts.
        The count will be updated in _do_commit() after successful commit.
        """
        try:
            session_path = str(session_file)
            session_type = self._detect_session_type(session_file)

            current_count = self._count_complete_turns(session_file)
            last_count = self.last_stop_reason_counts.get(session_path, 0)

            new_turns = current_count - last_count

            # Commit after each complete assistant response (1 new turn)
            if new_turns >= 1:
                logger.info(f"Detected {new_turns} new turn(s) in {session_file.name} ({session_type})")
                print(f"[MCP Watcher] Detected {new_turns} new turn(s) in {session_file.name} ({session_type})", file=sys.stderr)
                # DO NOT update last_stop_reason_counts here!
                # It will be updated in _do_commit() after successful commit
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking turn completion: {e}", exc_info=True)
            print(f"[MCP Watcher] Error checking turn completion: {e}", file=sys.stderr)
            return False

    async def _do_commit(self, project_path: Path, session_file: Path):
        """
        Async wrapper for committing a turn to the shadow git repository.

        Args:
            project_path: Path to the project directory
            session_file: Session file that triggered the commit
        """
        try:
            # Delegate to synchronous commit method (runs in executor to avoid blocking)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_realign_commit,
                project_path
            )

            if result:
                logger.info(f"✓ Committed to {project_path.name}")
                print(f"[MCP Watcher] ✓ Auto-committed to {project_path.name}", file=sys.stderr)
                # Update last commit time for this project
                self.last_commit_times[str(project_path)] = time.time()

                # Update turn count baseline ONLY after successful commit
                # This prevents double-counting if commit fails
                session_path = str(session_file)
                current_count = self._count_complete_turns(session_file)
                self.last_stop_reason_counts[session_path] = current_count
                logger.debug(f"Updated turn count baseline for {session_file.name}: {current_count}")
            else:
                logger.warning(f"Commit failed for {project_path.name}")

        except Exception as e:
            logger.error(f"Error during commit for {project_path}: {e}", exc_info=True)
            print(f"[MCP Watcher] Error during commit for {project_path}: {e}", file=sys.stderr)

    def _run_realign_commit(self, project_path: Path) -> bool:
        """
        Execute commit with file locking to prevent race conditions.

        Args:
            project_path: Path to the project directory

        Returns:
            True if commit was created, False otherwise

        The method will:
        - Acquire a file lock to prevent concurrent commits from multiple watchers
        - Auto-initialize shadow git repository if needed
        - Generate LLM-powered commit message
        - Mirror project files to shadow repository
        - Create commit with semantic message
        """
        from .file_lock import commit_lock

        try:
            # Acquire commit lock to prevent concurrent commits from multiple MCP servers
            with commit_lock(project_path, timeout=5.0) as locked:
                if not locked:
                    print(f"[MCP Watcher] Another watcher is committing to {project_path.name}, skipping", file=sys.stderr)
                    return False

                return self._do_commit_locked(project_path)

        except TimeoutError:
            print("[MCP Watcher] Could not acquire commit lock (timeout)", file=sys.stderr)
            return False
        except Exception as e:
            print(f"[MCP Watcher] Commit error: {e}", file=sys.stderr)
            return False

    def _do_commit_locked(self, project_path: Path) -> bool:
        """
        Perform the actual commit operation using ReAlignGitTracker.

        This method:
        1. Finds the latest session file for the project
        2. Redacts sensitive information from the session
        3. Generates LLM-powered semantic commit message
        4. Mirrors project files to shadow repository
        5. Creates commit with structured metadata

        Args:
            project_path: Path to the project directory

        Returns:
            True if commit was created, False otherwise
        """
        try:
            # Initialize git tracker if not already done
            if not self.git_tracker or self.git_tracker.project_root != project_path:
                self.git_tracker = ReAlignGitTracker(project_path)
                if not self.git_tracker.is_initialized():
                    self.git_tracker.init_repo()

            # Find the latest session file for this project
            session_file = self._find_latest_session(project_path)
            if not session_file:
                logger.warning("No session file found for commit")
                return False

            # Redact sensitive information from session file before committing
            session_file = self._handle_session_redaction(session_file, project_path)

            # Extract session information
            session_id = session_file.stem  # e.g., "minhao_claude_abc123"
            turn_number = self._get_current_turn_number(session_file)
            user_message = self._extract_last_user_message(session_file)
            modified_files = self._extract_modified_files(session_file)

            # Check if we've already committed this exact turn content to avoid duplicates
            # Compute hash of current turn content (not the whole session file)
            turn_content = self._extract_current_turn_content(session_file)
            turn_hash = None
            if turn_content:
                turn_hash = hashlib.md5(turn_content.encode('utf-8')).hexdigest()

                # Get hash registry for this project
                hash_registry = self._get_hash_registry(project_path)
                last_hash = hash_registry.get_last_hash(session_file)

                if last_hash == turn_hash:
                    logger.info(f"Turn content unchanged since last commit (hash: {turn_hash[:8]}), skipping duplicate")
                    print(f"[MCP Watcher] ⓘ Turn content unchanged, skipping duplicate commit", file=sys.stderr)
                    return False

                logger.debug(f"Turn content hash: {turn_hash[:8]}")

            # Generate LLM summary (required, no fallback)
            llm_result = self._generate_llm_summary(session_file)
            if not llm_result:
                logger.error("LLM summary generation failed - cannot commit without summary")
                print("[MCP Watcher] ✗ LLM summary generation failed - cannot commit", file=sys.stderr)
                return False

            title, model_name, description = llm_result

            # Validate title - reject if it's empty, too short, or looks like truncated JSON
            if not title or len(title.strip()) < 2:
                logger.error(f"Invalid LLM title generated: '{title}' - skipping commit")
                print(f"[MCP Watcher] ✗ Invalid commit message title: '{title}'", file=sys.stderr)
                return False

            if title.strip() in ["{", "}", "[", "]"] or title.startswith("{") and not title.endswith("}"):
                logger.error(f"Title appears to be truncated JSON: '{title}' - skipping commit")
                print(f"[MCP Watcher] ✗ Truncated JSON in title: '{title}'", file=sys.stderr)
                return False

            logger.info(f"Committing turn {turn_number} for session {session_id}")
            logger.debug(f"Modified files: {[str(f) for f in modified_files]}")

            # Commit the turn to .realign/.git
            commit_hash = self.git_tracker.commit_turn(
                session_id=session_id,
                turn_number=turn_number,
                user_message=user_message,
                llm_title=title,
                llm_description=description,
                model_name=model_name,
                modified_files=modified_files,
                session_file=session_file
            )

            if commit_hash:
                logger.info(f"✓ Committed turn {turn_number} to .realign/.git: {commit_hash[:8]}")
                print(f"[MCP Watcher] ✓ Committed turn {turn_number} to .realign/.git: {commit_hash[:8]}", file=sys.stderr)

                # Store hash in persistent registry (if we computed one)
                if turn_hash:
                    hash_registry = self._get_hash_registry(project_path)
                    hash_registry.set_last_hash(
                        session_file=session_file,
                        hash_value=turn_hash,
                        commit_sha=commit_hash,
                        turn_number=turn_number
                    )

                return True
            else:
                logger.info("No changes to commit")
                return False

        except Exception as e:
            logger.error(f"Commit error for {project_path.name}: {e}", exc_info=True)
            print(f"[MCP Watcher] Commit error for {project_path.name}: {e}", file=sys.stderr)
            return False

    def _get_hash_registry(self, project_path: Path) -> HashRegistry:
        """
        Get or create hash registry for a project (lazy initialization).

        Args:
            project_path: Path to the user's project root

        Returns:
            HashRegistry instance for this project
        """
        key = str(project_path)
        if key not in self.hash_registries:
            # Get .aline directory for this project
            from realign import get_realign_dir
            realign_dir = get_realign_dir(project_path)
            self.hash_registries[key] = HashRegistry(realign_dir)
            logger.debug(f"Initialized HashRegistry for {project_path.name}")
        return self.hash_registries[key]

    def _find_latest_session(self, project_path: Path) -> Optional[Path]:
        """Find the most recently modified session file for this project."""
        try:
            session_files = find_all_active_sessions(self.config, project_path)
            if not session_files:
                return None

            # Return most recently modified session
            return max(session_files, key=lambda f: f.stat().st_mtime)
        except Exception as e:
            logger.error(f"Failed to find latest session: {e}")
            return None

    def _handle_session_redaction(self, session_file: Path, project_path: Path) -> Path:
        """Check and redact sensitive information from session file.

        Args:
            session_file: Path to the session file
            project_path: Path to the project directory

        Returns:
            Path to the (possibly modified) session file
        """
        if not self.config.redact_on_match:
            return session_file

        try:
            from .redactor import check_and_redact_session, save_original_session

            content = session_file.read_text(encoding='utf-8')
            redacted_content, has_secrets, secrets = check_and_redact_session(
                content, redact_mode="auto"
            )

            if has_secrets:
                logger.warning(f"Secrets detected: {len(secrets)} secret(s)")
                from realign import get_realign_dir
                realign_dir = get_realign_dir(project_path)
                backup_path = save_original_session(session_file, realign_dir)
                session_file.write_text(redacted_content, encoding='utf-8')
                logger.info(f"Session redacted, original saved to {backup_path}")

            return session_file

        except Exception as e:
            logger.error(f"Failed to redact session: {e}")
            # Return original session file on error
            return session_file

    def _get_current_turn_number(self, session_file: Path) -> int:
        """Get the current turn number from a session file."""
        # Count the number of complete turns in the session
        return self._count_complete_turns(session_file)

    def _extract_last_user_message(self, session_file: Path) -> str:
        """
        Extract the user message for the current turn being committed.

        This is called AFTER a new user message arrives (which triggers the commit),
        so we need to extract the SECOND-TO-LAST valid user message, not the last one.
        The last user message belongs to the next turn that hasn't been processed yet.
        """
        from .hooks import clean_user_message

        try:
            user_messages = []

            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # Check for user message
                        if data.get("type") == "user":
                            message = data.get("message", {})
                            content = message.get("content", "")

                            extracted_text = None

                            if isinstance(content, str):
                                extracted_text = content
                            elif isinstance(content, list):
                                # Extract text from content blocks
                                text_parts = []
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text_parts.append(item.get("text", ""))

                                # Only add if we found actual text content
                                # Skip entries that only contain tool_result items
                                if text_parts:
                                    extracted_text = "\n".join(text_parts)

                            if extracted_text:
                                # Clean the message (remove IDE tags, etc.)
                                cleaned_text = clean_user_message(extracted_text)

                                # Skip empty messages after cleaning
                                if not cleaned_text.strip():
                                    continue

                                # Skip continuation messages
                                if cleaned_text.startswith("This session is being continued"):
                                    continue

                                user_messages.append(cleaned_text)

                    except json.JSONDecodeError:
                        continue

            # Return second-to-last message if available, otherwise last message
            # This is because the commit is triggered by a new user message,
            # so the last message is for the NEXT turn, not the current one being committed
            if len(user_messages) >= 2:
                return user_messages[-2]
            elif len(user_messages) == 1:
                return user_messages[0]
            else:
                return "No user message found"

        except Exception as e:
            logger.error(f"Failed to extract user message: {e}")
            return "Error extracting message"

    def _extract_assistant_summary(self, session_file: Path) -> str:
        """Extract a summary of the assistant's response from session file."""
        try:
            # Extract last assistant response text
            assistant_text = ""

            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        if data.get("type") == "assistant":
                            message = data.get("message", {})
                            content = message.get("content", [])

                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        assistant_text = item.get("text", "")

                    except json.JSONDecodeError:
                        continue

            # Truncate to reasonable length
            if assistant_text:
                # Take first 300 characters as summary
                summary = assistant_text[:300]
                if len(assistant_text) > 300:
                    summary += "..."
                return summary
            else:
                return "Assistant response"

        except Exception as e:
            logger.error(f"Failed to extract assistant summary: {e}")
            return "Error extracting summary"

    def _extract_current_turn_content(self, session_file: Path) -> str:
        """
        Extract only the content for the current turn being committed.

        Since commit is triggered by a new user message (Turn N+1), we need to extract
        the content from the PREVIOUS turn (Turn N), which includes:
        - The second-to-last user message
        - All assistant responses after that user message
        - But BEFORE the last user message (which belongs to Turn N+1)

        Returns:
            JSONL content for the current turn only
        """
        try:
            lines = []
            user_message_indices = []

            # Read all lines and track user message positions
            with open(session_file, 'r', encoding='utf-8') as f:
                for idx, line in enumerate(f):
                    lines.append(line)
                    try:
                        data = json.loads(line.strip())
                        if data.get("type") == "user":
                            message = data.get("message", {})
                            content = message.get("content", "")

                            # Check if this is a real user message (not tool result, IDE notification, etc.)
                            is_real_message = False
                            if isinstance(content, str):
                                if not content.startswith("This session is being continued") and \
                                   not content.startswith("<ide_opened_file>"):
                                    is_real_message = True
                            elif isinstance(content, list):
                                text_parts = [item.get("text", "") for item in content
                                            if isinstance(item, dict) and item.get("type") == "text"]
                                if text_parts:
                                    combined_text = "\n".join(text_parts)
                                    if not combined_text.startswith("This session is being continued") and \
                                       not combined_text.startswith("<ide_opened_file>"):
                                        is_real_message = True

                            if is_real_message:
                                user_message_indices.append(idx)
                    except json.JSONDecodeError:
                        continue

            # Determine the range for current turn
            if len(user_message_indices) >= 2:
                # Extract from second-to-last user message up to (but not including) last user message
                start_idx = user_message_indices[-2]
                end_idx = user_message_indices[-1]
                turn_lines = lines[start_idx:end_idx]
            elif len(user_message_indices) == 1:
                # First turn: from first user message to end
                start_idx = user_message_indices[0]
                turn_lines = lines[start_idx:]
            else:
                # No valid user messages
                return ""

            return "".join(turn_lines)

        except Exception as e:
            logger.error(f"Failed to extract current turn content: {e}", exc_info=True)
            return ""

    def _generate_llm_summary(self, session_file: Path) -> Optional[tuple[str, str, str]]:
        """
        Generate LLM-powered summary for the CURRENT TURN only.

        Priority:
        1. MCP Sampling API (if enabled and available)
        2. Direct Claude/OpenAI API calls (existing fallback)

        Returns:
            Tuple of (title, model_name, description), or None if LLM is disabled or fails
        """
        try:
            if not self.config.use_LLM:
                logger.debug("LLM summary disabled in config")
                return None

            # Extract only the current turn's content
            turn_content = self._extract_current_turn_content(session_file)
            if not turn_content:
                logger.warning("No content found for current turn")
                return None

            # NEW: Try MCP Sampling first (if enabled)
            if self.config.use_mcp_sampling:
                logger.info("Attempting LLM summary via MCP Sampling")
                print("[MCP Watcher] → Requesting summary via MCP Sampling (user approval required)...", file=sys.stderr)

                try:
                    # Import here to avoid circular dependency
                    from .mcp_server import request_llm_summary_via_sampling

                    # Get current event loop (we're in async context via watcher)
                    import asyncio
                    loop = asyncio.get_event_loop()

                    # Run the sampling request with 30s timeout
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            request_llm_summary_via_sampling(turn_content),
                            timeout=30.0
                        )
                    )

                    if result:
                        title, model, description = result
                        logger.info(f"✓ MCP Sampling success using {model}")
                        print(f"[MCP Watcher] ✓ Generated summary via MCP Sampling ({model})", file=sys.stderr)
                        return result
                    else:
                        logger.warning("MCP Sampling returned None (not in MCP mode or user denied)")
                        print("[MCP Watcher] ⚠ MCP Sampling unavailable, falling back to direct API", file=sys.stderr)

                except asyncio.TimeoutError:
                    logger.warning("MCP Sampling timeout (30s), falling back to direct API")
                    print("[MCP Watcher] ⚠ MCP Sampling timeout, falling back to direct API", file=sys.stderr)
                except Exception as e:
                    logger.warning(f"MCP Sampling error: {e}, falling back to direct API")
                    print(f"[MCP Watcher] ⚠ MCP Sampling error: {e}", file=sys.stderr)

            # EXISTING: Fallback to direct API calls
            from .hooks import generate_summary_with_llm

            title, model_name, description = generate_summary_with_llm(
                turn_content,
                max_chars=500,
                provider=self.config.llm_provider
            )

            if title:
                if model_name:
                    logger.info(f"Generated LLM summary using {model_name}")
                    print(f"[MCP Watcher] ✓ Generated LLM summary using {model_name}", file=sys.stderr)
                return (title, model_name or "unknown", description or "")
            else:
                logger.warning("LLM summary generation returned empty result")
                return None

        except Exception as e:
            logger.error(f"Failed to generate LLM summary: {e}", exc_info=True)
            print(f"[MCP Watcher] Failed to generate LLM summary: {e}", file=sys.stderr)
            return None

    def _extract_modified_files(self, session_file: Path) -> list[Path]:
        """
        Extract all project files for mirroring.

        This method uses the shared mirror_utils.collect_project_files() logic
        to find all files that should be mirrored to the shadow git repository.
        It respects .gitignore patterns and excludes .git directory.

        Args:
            session_file: Path to the session file

        Returns:
            List of absolute paths to all project files
        """
        try:
            # Get project path
            project_path = self._extract_project_path(session_file)
            if not project_path:
                logger.warning("Could not determine project path")
                return []

            # Use shared logic to collect all project files
            all_files = collect_project_files(project_path, logger=logger)
            return all_files

        except Exception as e:
            logger.error(f"Failed to extract project files: {e}", exc_info=True)
            return []

    def _get_session_start_time(self, session_file: Path) -> Optional[float]:
        """
        Get the session start time from the first message timestamp.

        Returns:
            Unix timestamp (float) or None if not found
        """
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # Look for timestamp field in various formats
                        timestamp_str = data.get("timestamp")
                        if timestamp_str:
                            # Parse ISO 8601 timestamp
                            from datetime import datetime
                            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            return dt.timestamp()

                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue

            # Fallback: use session file's creation time
            return session_file.stat().st_ctime

        except Exception as e:
            logger.error(f"Failed to get session start time: {e}")
            return None

    async def auto_init_projects(self):
        """
        Discover and auto-initialize uninitialized projects from ~/.claude/projects/.

        This method:
        1. Scans all Claude Code project directories
        2. Decodes project paths
        3. Checks blacklist
        4. Checks if already initialized
        5. Attempts initialization for new projects
        6. Logs all operations (no user notifications)
        """
        try:
            claude_projects = Path.home() / ".claude" / "projects"

            if not claude_projects.exists():
                logger.debug("No ~/.claude/projects directory found")
                return

            logger.info("Starting auto-init scan of Claude projects")

            initialized_count = 0
            skipped_count = 0
            failed_count = 0

            for project_dir in claude_projects.iterdir():
                if not project_dir.is_dir():
                    continue

                # Skip system directories
                if project_dir.name.startswith('.'):
                    continue

                # Decode project path
                project_path = decode_claude_project_path(project_dir.name)
                if not project_path:
                    logger.debug(f"Could not decode project: {project_dir.name}")
                    skipped_count += 1
                    continue

                project_key = str(project_path)

                # Check if already initialized - if yes, skip (even if blacklisted)
                # User has explicitly initialized this project, so respect their choice
                if is_project_initialized(project_path):
                    logger.debug(f"Already initialized: {project_path}")
                    skipped_count += 1
                    continue

                # Skip if previously failed auto-init
                if project_key in self.failed_init_projects:
                    logger.debug(f"Skipping previously failed project: {project_path}")
                    skipped_count += 1
                    continue

                # Check blacklist - only for auto-init, not for already initialized projects
                if is_path_blacklisted(project_path):
                    logger.info(f"Skipping blacklisted project (auto-init): {project_path}")
                    skipped_count += 1
                    continue

                # Attempt initialization
                logger.info(f"Auto-initializing project: {project_path}")

                try:
                    from .commands.init import init_repository
                    from .commands.mirror import mirror_project

                    result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        init_repository,
                        str(project_path),
                        False  # force=False
                    )

                    if result["success"]:
                        logger.info(f"✓ Auto-initialized: {project_path.name}")

                        # Mirror project files after successful initialization
                        logger.info(f"Mirroring project files for {project_path.name}")
                        mirror_success = await asyncio.get_event_loop().run_in_executor(
                            None,
                            mirror_project,
                            project_path,
                            False  # verbose=False
                        )

                        if mirror_success:
                            logger.info(f"✓ Mirrored project files for {project_path.name}")

                            # Create initial commit with mirrored files
                            realign_dir = Path(result["realign_dir"])
                            try:
                                subprocess.run(
                                    ["git", "add", "-A"],
                                    cwd=realign_dir,
                                    check=True,
                                    capture_output=True
                                )
                                subprocess.run(
                                    ["git", "commit", "-m", "Initial commit: Mirror project files"],
                                    cwd=realign_dir,
                                    check=True,
                                    capture_output=True
                                )
                                logger.info(f"✓ Created initial commit for {project_path.name}")
                            except subprocess.CalledProcessError as e:
                                logger.warning(f"Failed to create initial commit for {project_path.name}: {e}")
                        else:
                            logger.warning(f"Failed to mirror project files for {project_path.name}")

                        initialized_count += 1
                    else:
                        logger.error(f"✗ Auto-init failed for {project_path.name}: {result.get('message')}")
                        # Mark as failed, never retry
                        self.failed_init_projects.add(project_key)
                        failed_count += 1

                except Exception as e:
                    logger.error(f"✗ Auto-init exception for {project_path.name}: {e}", exc_info=True)
                    # Mark as failed, never retry
                    self.failed_init_projects.add(project_key)
                    failed_count += 1

            logger.info(f"Auto-init complete: {initialized_count} initialized, {skipped_count} skipped, {failed_count} failed")

        except Exception as e:
            logger.error(f"Error in auto_init_projects: {e}", exc_info=True)

    async def run_periodic_auto_init(self):
        """
        Run auto-init periodically while watcher is running.

        Runs every self.auto_init_interval seconds (default 5s).
        """
        try:
            while self.running:
                current_time = time.time()

                # Check if it's time to run auto-init
                if current_time - self.last_auto_init_time >= self.auto_init_interval:
                    logger.info("Running periodic auto-init check")
                    await self.auto_init_projects()
                    self.last_auto_init_time = current_time

                # Sleep for 1 second before checking again
                await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Error in periodic auto-init: {e}", exc_info=True)

