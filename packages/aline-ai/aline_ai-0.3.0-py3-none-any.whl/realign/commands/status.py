#!/usr/bin/env python3
"""ReAlign status command - Display system status and activity."""

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel

from ..config import ReAlignConfig
from ..hooks import find_all_active_sessions
from ..logging_config import setup_logger
from .review import get_unpushed_commits

# Initialize logger
logger = setup_logger('realign.status', 'status.log')
console = Console()


# ============================================================================
# Data Collection Functions
# ============================================================================

def check_initialization_status() -> Dict:
    """
    Check if ReAlign is initialized in current directory.

    Returns:
        dict: Initialization status with paths and commit count
    """
    try:
        realign_path = Path.cwd() / '.realign'
        if not realign_path.exists():
            return {
                "initialized": False,
                "realign_path": None,
                "project_path": None,
                "total_commits": 0,
                "has_git_mirror": False
            }

        # Check for git mirror
        git_path = realign_path / '.git'
        has_git_mirror = git_path.exists()

        # Try to count commits
        total_commits = 0
        if has_git_mirror:
            try:
                result = subprocess.run(
                    ['git', '-C', str(git_path), 'rev-list', '--count', 'HEAD'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    total_commits = int(result.stdout.strip())
            except (subprocess.TimeoutExpired, ValueError, Exception) as e:
                logger.warning(f"Failed to count commits: {e}")

        return {
            "initialized": True,
            "realign_path": realign_path,
            "project_path": Path.cwd(),
            "total_commits": total_commits,
            "has_git_mirror": has_git_mirror
        }

    except Exception as e:
        logger.error(f"Error checking initialization: {e}", exc_info=True)
        return {
            "initialized": False,
            "realign_path": None,
            "project_path": None,
            "total_commits": 0,
            "has_git_mirror": False
        }


def detect_watcher_status() -> Dict:
    """
    Detect if MCP watcher is running.

    Uses multi-method detection:
    1. Check for aline-mcp process (ps aux)
    2. Check log freshness (< 5 mins = active)

    Returns:
        dict: Watcher status and configuration
    """
    try:
        # Load configuration
        config = ReAlignConfig.load()

        # Step 1: Check for process
        is_process_running = False
        pid = None
        try:
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if ps_output.returncode == 0:
                for line in ps_output.stdout.split('\n'):
                    if 'aline-mcp' in line:
                        is_process_running = True
                        # Try to extract PID (second column)
                        parts = line.split()
                        if len(parts) > 1:
                            try:
                                pid = int(parts[1])
                            except ValueError:
                                pass
                        break
        except subprocess.TimeoutExpired:
            logger.warning("Process check timed out")

        # Step 2: Check log freshness
        log_path = Path.home() / '.aline/.logs/mcp_watcher.log'
        is_log_active = False
        last_activity = None

        if log_path.exists():
            try:
                last_modified = datetime.fromtimestamp(log_path.stat().st_mtime)
                seconds_since_modified = (datetime.now() - last_modified).total_seconds()
                is_log_active = seconds_since_modified < 300  # 5 mins
                last_activity = last_modified
            except Exception as e:
                logger.warning(f"Failed to check log timestamp: {e}")

        # Step 3: Determine status
        if is_process_running and is_log_active:
            status = "Running"
        elif not is_process_running:
            status = "Stopped"
        else:
            status = "Inactive"  # Process exists but log is stale

        return {
            "status": status,
            "pid": pid,
            "auto_commit_enabled": config.mcp_auto_commit,
            "debounce_delay": 2.0,  # Hardcoded from mcp_watcher.py
            "cooldown": 5.0,  # Hardcoded from mcp_watcher.py
            "last_activity": last_activity
        }

    except Exception as e:
        logger.error(f"Error detecting watcher status: {e}", exc_info=True)
        return {
            "status": "Unknown",
            "pid": None,
            "auto_commit_enabled": False,
            "debounce_delay": 2.0,
            "cooldown": 5.0,
            "last_activity": None
        }


def get_session_information() -> Dict:
    """
    Detect active sessions from Claude Code and Codex.

    Returns:
        dict: Session paths and latest session info
    """
    try:
        config = ReAlignConfig.load()
        project_path = Path.cwd()

        # Find all active sessions
        all_sessions = find_all_active_sessions(config, project_path)

        # Separate by type (Claude vs Codex)
        claude_sessions = []
        codex_sessions = []

        for session in all_sessions:
            session_str = str(session)
            if '.claude/projects/' in session_str:
                claude_sessions.append(session)
            elif '.codex/sessions/' in session_str:
                codex_sessions.append(session)
            else:
                # Default to Claude if unclear
                claude_sessions.append(session)

        # Get latest session
        latest_session = None
        latest_session_time = None

        if all_sessions:
            try:
                latest_session = max(all_sessions, key=lambda f: f.stat().st_mtime)
                latest_session_time = datetime.fromtimestamp(latest_session.stat().st_mtime)
            except Exception as e:
                logger.warning(f"Failed to determine latest session: {e}")

        return {
            "claude_sessions": claude_sessions,
            "codex_sessions": codex_sessions,
            "latest_session": latest_session,
            "latest_session_time": latest_session_time
        }

    except Exception as e:
        logger.error(f"Error getting session information: {e}", exc_info=True)
        return {
            "claude_sessions": [],
            "codex_sessions": [],
            "latest_session": None,
            "latest_session_time": None
        }


def get_configuration_summary() -> Dict:
    """
    Extract key configuration values.

    Returns:
        dict: Configuration summary
    """
    try:
        config = ReAlignConfig.load()
        return {
            "llm_provider": config.llm_provider,
            "use_llm": config.use_LLM,
            "redact_on_match": config.redact_on_match,
            "hooks_installation": config.hooks_installation,
            "auto_detect_claude": config.auto_detect_claude,
            "auto_detect_codex": config.auto_detect_codex
        }
    except Exception as e:
        logger.error(f"Error getting configuration: {e}", exc_info=True)
        return {
            "llm_provider": "unknown",
            "use_llm": False,
            "redact_on_match": False,
            "hooks_installation": "unknown",
            "auto_detect_claude": False,
            "auto_detect_codex": False
        }


def get_recent_activity() -> Dict:
    """
    Get recent commit and session statistics.

    Returns:
        dict: Recent activity information
    """
    try:
        realign_path = Path.cwd() / '.realign'

        # Latest commit from .realign/.git
        latest_commit_hash = None
        latest_commit_message = None
        latest_commit_time = None

        git_path = realign_path / '.git'
        if git_path.exists():
            try:
                result = subprocess.run(
                    ['git', '-C', str(git_path), 'log', '-1', '--format=%h|%s|%ct'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    parts = result.stdout.strip().split('|')
                    if len(parts) >= 3:
                        latest_commit_hash = parts[0]
                        latest_commit_message = parts[1]
                        latest_commit_time = datetime.fromtimestamp(int(parts[2]))
            except (subprocess.TimeoutExpired, ValueError, Exception) as e:
                logger.warning(f"Failed to get latest commit: {e}")

        # Unpushed commits count
        unpushed_count = 0
        try:
            unpushed_commits = get_unpushed_commits()
            unpushed_count = len(unpushed_commits)
        except Exception as e:
            logger.warning(f"Failed to get unpushed commits: {e}")

        # Total sessions tracked
        total_sessions = 0
        sessions_path = realign_path / 'sessions'
        if sessions_path.exists():
            try:
                total_sessions = len(list(sessions_path.glob('*.jsonl')))
            except Exception as e:
                logger.warning(f"Failed to count sessions: {e}")

        return {
            "latest_commit_hash": latest_commit_hash,
            "latest_commit_message": latest_commit_message,
            "latest_commit_time": latest_commit_time,
            "unpushed_count": unpushed_count,
            "total_sessions": total_sessions
        }

    except Exception as e:
        logger.error(f"Error getting recent activity: {e}", exc_info=True)
        return {
            "latest_commit_hash": None,
            "latest_commit_message": None,
            "latest_commit_time": None,
            "unpushed_count": 0,
            "total_sessions": 0
        }


def collect_all_status_data() -> Dict:
    """
    Collect all status information from all data functions.

    Returns:
        dict: Complete status data
    """
    return {
        "init": check_initialization_status(),
        "watcher": detect_watcher_status(),
        "sessions": get_session_information(),
        "config": get_configuration_summary(),
        "activity": get_recent_activity()
    }


# ============================================================================
# Helper Functions
# ============================================================================

def format_time_with_relative(dt: datetime) -> str:
    """
    Format datetime with both absolute and relative time.

    Args:
        dt: Datetime to format

    Returns:
        str: Formatted time string (e.g., "2025-11-29 14:23:45 (2 mins ago)")
    """
    absolute = dt.strftime('%Y-%m-%d %H:%M:%S')

    # Calculate relative time
    now = datetime.now()
    diff = now - dt
    total_seconds = diff.total_seconds()

    if total_seconds < 60:
        relative = "just now"
    elif total_seconds < 3600:
        mins = int(total_seconds // 60)
        relative = f"{mins} min{'s' if mins != 1 else ''} ago"
    elif diff.days == 0:
        hours = int(total_seconds // 3600)
        relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days < 7:
        relative = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    else:
        weeks = diff.days // 7
        relative = f"{weeks} week{'s' if weeks != 1 else ''} ago"

    return f"{absolute} ({relative})"


def abbreviate_path(path: Path) -> str:
    """
    Abbreviate home directory with ~.

    Args:
        path: Path to abbreviate

    Returns:
        str: Abbreviated path
    """
    home = Path.home()
    try:
        relative = path.relative_to(home)
        return f"~/{relative}"
    except ValueError:
        # Path is not under home directory
        return str(path)


# ============================================================================
# Display Function
# ============================================================================

def display_status(data: Dict, is_watch: bool = False) -> None:
    """
    Display status using Rich library.

    Args:
        data: Status data from collect_all_status_data()
        is_watch: Whether in watch mode
    """
    # Title panel
    console.print(Panel("ReAlign System Status", style="bold cyan"))

    # Section 1: Initialization
    console.print("\n[bold cyan][1] Initialization[/bold cyan]")
    if data['init']['initialized']:
        console.print(f"    Status: Initialized [green]✓[/green]")
        console.print(f"    Path: {data['init']['project_path']}")
        console.print(f"    Shadow Repository: .realign/.git ({data['init']['total_commits']} commits)")
    else:
        console.print(f"    Status: Not initialized [red]✗[/red]")
        console.print(f"\n    [dim]ReAlign is not initialized in this directory.[/dim]")
        console.print(f"    [dim]Run 'aline init' to set up session tracking.[/dim]")
        return  # Stop here, don't show other sections

    # Section 2: Watcher
    console.print("\n[bold cyan][2] Watcher[/bold cyan]")
    status = data['watcher']['status']
    if status == "Running":
        console.print(f"    Status: Running [green]✓[/green]")
    elif status == "Stopped":
        console.print(f"    Status: Stopped [red]✗[/red]")
    else:
        console.print(f"    Status: Inactive [yellow]✗[/yellow]")
        console.print(f"    [dim]Suggestion: Restart MCP server[/dim]")

    # Auto-commit status
    if data['watcher']['auto_commit_enabled']:
        console.print(f"    Auto-commit: [green]Enabled[/green]")
    else:
        console.print(f"    Auto-commit: [red]Disabled[/red]")

    # Timing info
    console.print(f"    Timing: Debounce {data['watcher']['debounce_delay']}s | Cooldown {data['watcher']['cooldown']}s")

    # Last activity (if available)
    if data['watcher']['last_activity']:
        time_str = format_time_with_relative(data['watcher']['last_activity'])
        console.print(f"    Last Activity: {time_str}")

    # Section 3: Sessions
    console.print("\n[bold cyan][3] Active Sessions[/bold cyan]")
    claude_count = len(data['sessions']['claude_sessions'])
    codex_count = len(data['sessions']['codex_sessions'])

    if claude_count > 0:
        console.print(f"    Claude Code: {claude_count} session(s)")
        for session in data['sessions']['claude_sessions'][:3]:  # Show max 3
            abbreviated_path = abbreviate_path(session)
            console.print(f"      {abbreviated_path}")
        if claude_count > 3:
            console.print(f"      [dim]... and {claude_count - 3} more[/dim]")
    else:
        console.print(f"    Claude Code: [dim]No sessions found[/dim]")

    if codex_count > 0:
        console.print(f"    Codex: {codex_count} session(s)")
        for session in data['sessions']['codex_sessions'][:3]:
            abbreviated_path = abbreviate_path(session)
            console.print(f"      {abbreviated_path}")
        if codex_count > 3:
            console.print(f"      [dim]... and {codex_count - 3} more[/dim]")
    else:
        console.print(f"    Codex: [dim]No sessions found[/dim]")

    # Section 4: Configuration
    console.print("\n[bold cyan][4] Configuration[/bold cyan]")

    # LLM Provider
    llm_status = "[green]Enabled[/green]" if data['config']['use_llm'] else "[red]Disabled[/red]"
    console.print(f"    LLM Provider: {data['config']['llm_provider']} ({llm_status})")

    # Redaction
    redaction_status = "[green]Enabled[/green]" if data['config']['redact_on_match'] else "[red]Disabled[/red]"
    console.print(f"    Redaction: {redaction_status}")

    # Hook Mode
    console.print(f"    Hook Mode: {data['config']['hooks_installation']}")

    # Section 5: Recent Activity
    console.print("\n[bold cyan][5] Recent Activity[/bold cyan]")

    # Latest commit
    if data['activity']['latest_commit_hash']:
        commit_msg = data['activity']['latest_commit_message']
        # Extract turn number if present
        if 'Turn' in commit_msg:
            # Format: "Session xxx, Turn N: message"
            parts = commit_msg.split(': ', 1)
            if len(parts) == 2:
                commit_msg = parts[1][:50]  # Truncate message
        else:
            commit_msg = commit_msg[:50]

        time_str = format_time_with_relative(data['activity']['latest_commit_time'])
        console.print(f"    Latest Commit: {data['activity']['latest_commit_hash']} - {commit_msg}")
        console.print(f"                   {time_str}")
    else:
        console.print(f"    Latest Commit: [dim]No commits yet[/dim]")

    # Unpushed commits
    unpushed = data['activity']['unpushed_count']
    if unpushed > 0:
        console.print(f"    Unpushed: {unpushed} commit{'s' if unpushed != 1 else ''}")
    else:
        console.print(f"    Unpushed: [dim]None[/dim]")

    # Sessions tracked
    total_sessions = data['activity']['total_sessions']
    console.print(f"    Sessions Tracked: {total_sessions}")


# ============================================================================
# Main Command Function
# ============================================================================

def status_command(watch: bool = False) -> int:
    """
    Main entry point for status command.

    Args:
        watch: Enable watch mode (continuous refresh)

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    try:
        if watch:
            # Watch mode: continuous refresh
            while True:
                console.clear()
                console.print(f"[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")

                # Collect all data
                data = collect_all_status_data()

                # Display
                display_status(data, is_watch=True)

                # Wait 2 seconds
                time.sleep(2)
        else:
            # Single display
            data = collect_all_status_data()
            display_status(data, is_watch=False)

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Status monitoring stopped[/yellow]")
        return 0
    except Exception as e:
        logger.error(f"Error in status command: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return 1
