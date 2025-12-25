#!/usr/bin/env python3
"""Aline watcher commands - Manage MCP watcher process."""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table

from ..config import ReAlignConfig
from ..hooks import find_all_active_sessions
from ..logging_config import setup_logger

# Initialize logger
logger = setup_logger('realign.watcher', 'watcher.log')
console = Console()


def get_watcher_pid_file() -> Path:
    """Get path to the watcher PID file."""
    return Path.home() / '.aline/.logs/watcher.pid'


def detect_watcher_process() -> tuple[bool, int | None, str]:
    """
    Detect if watcher is running (either MCP or standalone).

    Returns:
        tuple: (is_running, pid, mode)
        mode can be: 'mcp', 'standalone', or 'unknown'
    """
    # First check for standalone daemon via PID file
    pid_file = get_watcher_pid_file()
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            # Verify process is still running
            try:
                import os
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True, pid, 'standalone'
            except (OSError, ProcessLookupError):
                # PID file exists but process is dead - clean it up
                pid_file.unlink(missing_ok=True)
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to read PID file: {e}")

    # Then check for MCP watcher process
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
                    # Extract PID (second column)
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            return True, pid, 'mcp'
                        except ValueError:
                            return True, None, 'mcp'
            return False, None, 'unknown'
    except subprocess.TimeoutExpired:
        logger.warning("Process check timed out")
        return False, None, 'unknown'


def detect_all_watcher_processes() -> list[tuple[int, str]]:
    """
    Detect ALL running watcher processes (both standalone and MCP).

    Returns:
        list of tuples: [(pid, mode), ...]
        mode can be: 'standalone' or 'mcp'
    """
    processes = []

    try:
        # Use ps to find all watcher_daemon.py processes
        ps_output = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=2
        )

        if ps_output.returncode == 0:
            for line in ps_output.stdout.split('\n'):
                # Look for watcher_daemon.py processes
                if 'watcher_daemon.py' in line and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pid = int(parts[1])
                            # Determine mode based on command line
                            if 'aline-mcp' in line:
                                processes.append((pid, 'mcp'))
                            else:
                                processes.append((pid, 'standalone'))
                        except ValueError:
                            continue

    except subprocess.TimeoutExpired:
        logger.warning("Process check timed out")
    except Exception as e:
        logger.warning(f"Failed to detect watcher processes: {e}")

    return processes


def check_watcher_log_activity() -> tuple[bool, datetime | None]:
    """
    Check if watcher log has recent activity.

    Returns:
        tuple: (is_active, last_modified)
    """
    log_path = Path.home() / '.aline/.logs/mcp_watcher.log'
    if log_path.exists():
        try:
            last_modified = datetime.fromtimestamp(log_path.stat().st_mtime)
            seconds_since_modified = (datetime.now() - last_modified).total_seconds()
            is_active = seconds_since_modified < 300  # 5 mins
            return is_active, last_modified
        except Exception as e:
            logger.warning(f"Failed to check log timestamp: {e}")
            return False, None
    return False, None


def get_watched_projects() -> list[Path]:
    """
    Get list of projects being watched by checking ~/.aline directory.

    Returns:
        List of project paths that have Aline initialized
    """
    aline_dir = Path.home() / '.aline'
    if not aline_dir.exists():
        return []

    watched = []
    try:
        for project_dir in aline_dir.iterdir():
            if project_dir.is_dir() and project_dir.name not in ['.logs', '.cache']:
                # Skip test/temporary directories
                if project_dir.name.startswith(('tmp', 'test_')):
                    continue
                # Check if it has .git (shadow git repo)
                if (project_dir / '.git').exists():
                    watched.append(project_dir)
    except Exception as e:
        logger.warning(f"Failed to scan watched projects: {e}")

    return watched


def extract_project_name_from_session(session_file: Path) -> str:
    """
    Extract project name from session file path.

    Supports:
        - Claude Code format: ~/.claude/projects/-Users-foo-Projects-MyApp/abc.jsonl → MyApp
        - .aline format: ~/.aline/MyProject/sessions/abc.jsonl → MyProject

    Args:
        session_file: Path to session file

    Returns:
        Project name, or "unknown" if cannot determine
    """
    try:
        # Method 1: Claude Code format
        if '.claude/projects/' in str(session_file):
            project_dir = session_file.parent.name
            if project_dir.startswith('-'):
                # Decode: -Users-foo-Projects-MyApp → MyApp
                parts = project_dir[1:].split('-')
                return parts[-1] if parts else "unknown"

        # Method 2: .aline format
        if '.aline/' in str(session_file):
            # Find the project directory (parent of 'sessions')
            path_parts = session_file.parts
            try:
                aline_idx = path_parts.index('.aline')
                if aline_idx + 1 < len(path_parts):
                    return path_parts[aline_idx + 1]
            except ValueError:
                pass

        return "unknown"
    except Exception as e:
        logger.debug(f"Error extracting project name from {session_file}: {e}")
        return "unknown"


def _detect_session_type(session_file: Path) -> str:
    """
    Detect the type of session file.

    Returns:
        "claude" for Claude Code sessions
        "codex" for Codex/GPT sessions
        "unknown" if cannot determine
    """
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") in ("assistant", "user") and "message" in data:
                        return "claude"
                    if data.get("type") == "session_meta":
                        payload = data.get("payload", {})
                        if "codex" in payload.get("originator", "").lower():
                            return "codex"
                    if data.get("type") == "response_item":
                        payload = data.get("payload", {})
                        if "message" not in data and "role" in payload:
                            return "codex"
                except json.JSONDecodeError:
                    continue
        return "unknown"
    except Exception as e:
        logger.debug(f"Error detecting session type: {e}")
        return "unknown"


def _count_complete_turns(session_file: Path) -> int:
    """
    Count complete dialogue turns in a session file.

    Returns:
        Number of complete turns
    """
    session_type = _detect_session_type(session_file)

    if session_type == "claude":
        return _count_claude_turns(session_file)
    elif session_type == "codex":
        return _count_codex_turns(session_file)
    else:
        return 0


def _count_claude_turns(session_file: Path) -> int:
    """Count complete dialogue turns for Claude Code sessions."""
    user_message_ids = set()
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    msg_type = data.get("type")

                    if msg_type == "user":
                        message = data.get("message", {})
                        content = message.get("content", [])

                        is_tool_result = False
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict) and item.get("type") == "tool_result":
                                    is_tool_result = True
                                    break

                        if not is_tool_result:
                            uuid = data.get("uuid")
                            if uuid:
                                user_message_ids.add(uuid)
                except json.JSONDecodeError:
                    continue
        return len(user_message_ids)
    except Exception as e:
        logger.debug(f"Error counting Claude turns: {e}")
        return 0


def _count_codex_turns(session_file: Path) -> int:
    """Count complete dialogue turns for Codex sessions."""
    count = 0
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "event_msg":
                        payload = data.get("payload", {})
                        if payload.get("type") == "token_count":
                            count += 1
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.debug(f"Error counting Codex turns: {e}")
    return count


def get_session_details(session_file: Path, idle_timeout: float = 300.0) -> Dict:
    """
    Get detailed information about a session file.

    Args:
        session_file: Path to session file
        idle_timeout: Idle timeout threshold in seconds

    Returns:
        dict with session details including:
        - name: session filename
        - path: session file path
        - project_name: project name extracted from path
        - type: claude/codex/unknown
        - turns: number of complete turns
        - mtime: last modified time
        - idle_seconds: seconds since last modification
        - is_idle: whether session exceeds idle timeout
        - size_kb: file size in KB
    """
    try:
        stat = session_file.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        current_time = time.time()
        idle_seconds = current_time - stat.st_mtime

        return {
            "name": session_file.name,
            "path": session_file,
            "project_name": extract_project_name_from_session(session_file),
            "type": _detect_session_type(session_file),
            "turns": _count_complete_turns(session_file),
            "mtime": mtime,
            "idle_seconds": idle_seconds,
            "is_idle": idle_seconds >= idle_timeout,
            "size_kb": stat.st_size / 1024
        }
    except Exception as e:
        logger.debug(f"Error getting session details for {session_file}: {e}")
        return {
            "name": session_file.name,
            "path": session_file,
            "project_name": "unknown",
            "type": "error",
            "turns": 0,
            "mtime": None,
            "idle_seconds": 0,
            "is_idle": False,
            "size_kb": 0
        }


def get_all_tracked_sessions() -> List[Dict]:
    """
    Get detailed information for all active sessions being tracked.

    Returns:
        List of session detail dictionaries
    """
    try:
        config = ReAlignConfig.load()

        # Find all active sessions across ALL projects (multi-project mode)
        all_sessions = find_all_active_sessions(config, project_path=None)

        # Get details for each session
        session_details = []
        for session_file in all_sessions:
            if session_file.exists():
                details = get_session_details(session_file)
                session_details.append(details)

        # Sort by mtime (most recent first)
        session_details.sort(key=lambda x: x["mtime"] if x["mtime"] else datetime.min, reverse=True)

        return session_details
    except Exception as e:
        logger.error(f"Error getting tracked sessions: {e}")
        return []


def watcher_status_command(verbose: bool = False) -> int:
    """
    Display watcher status.

    Args:
        verbose: Show detailed session tracking information

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    try:
        config = ReAlignConfig.load()

        # Check process
        is_running, pid, mode = detect_watcher_process()

        # Check log activity
        is_log_active, last_activity = check_watcher_log_activity()

        # Determine status
        if is_running and is_log_active:
            status = "Running"
            color = "green"
            symbol = "✓"
        elif not is_running:
            status = "Stopped"
            color = "red"
            symbol = "✗"
        else:
            status = "Inactive"
            color = "yellow"
            symbol = "✗"

        # Display status
        console.print(f"\n[bold cyan]Watcher Status[/bold cyan]")
        console.print(f"  Status: [{color}]{status} {symbol}[/{color}]")

        if pid:
            console.print(f"  PID: {pid}")

        # Show mode
        if mode == 'standalone':
            console.print(f"  Mode: [cyan]Standalone[/cyan]")
        elif mode == 'mcp':
            console.print(f"  Mode: [cyan]MCP[/cyan]")

        if last_activity:
            # Format time
            absolute = last_activity.strftime('%Y-%m-%d %H:%M:%S')
            diff = (datetime.now() - last_activity).total_seconds()

            if diff < 60:
                relative = "just now"
            elif diff < 3600:
                mins = int(diff // 60)
                relative = f"{mins} min{'s' if mins != 1 else ''} ago"
            else:
                hours = int(diff // 3600)
                relative = f"{hours} hour{'s' if hours != 1 else ''} ago"

            console.print(f"  Last Activity: {absolute} ({relative})")

        # Show tracked sessions (if verbose or if there are active sessions)
        if verbose:
            console.print(f"\n[bold cyan]Tracked Sessions (last 24h)[/bold cyan]")
            session_details = get_all_tracked_sessions()

            if session_details:
                # Filter sessions
                current_time = time.time()
                session_details = [
                    s for s in session_details
                    # Filter 1: Remove unknown/empty sessions
                    if not (s["type"] == "unknown" and s["turns"] == 0 and s["size_kb"] < 0.1)
                    # Filter 2: Only show sessions modified within last 24 hours
                    and (current_time - s["mtime"].timestamp() if s["mtime"] else 0) <= 86400
                ]

            if session_details:
                # Create a rich table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Session", style="cyan", no_wrap=False, max_width=35)
                table.add_column("Project", style="dim", width=15)
                table.add_column("Type", justify="center", style="dim", width=8)
                table.add_column("Turns", justify="center", style="yellow", width=6)
                table.add_column("Status", justify="center", width=10)
                table.add_column("Last Modified", style="dim", width=20)
                table.add_column("Size", justify="right", style="dim", width=10)

                for session in session_details:
                    # Format status (idle + commit status)
                    idle_sec = session["idle_seconds"]
                    turns = session["turns"]

                    # Determine color
                    if idle_sec < 60:
                        idle_color = "green"
                    elif idle_sec < 300:
                        idle_color = "yellow"
                    else:
                        idle_color = "red"

                    # Format idle time
                    if idle_sec < 60:
                        idle_str = f"{int(idle_sec)}s"
                    else:
                        idle_str = f"{int(idle_sec // 60)}m"

                    # Determine commit status symbol
                    if turns == 0:
                        status_symbol = "●"  # Empty
                    elif idle_sec < 10:
                        status_symbol = "⏳"  # Processing
                    else:
                        status_symbol = "✓"  # Committed

                    status_display = f"[{idle_color}]{idle_str} {status_symbol}[/{idle_color}]"

                    # Format mtime
                    if session["mtime"]:
                        mtime_str = session["mtime"].strftime("%H:%M:%S")
                    else:
                        mtime_str = "N/A"

                    # Format size
                    size_kb = session["size_kb"]
                    if size_kb < 1:
                        size_str = f"{int(size_kb * 1024)}B"
                    elif size_kb < 1024:
                        size_str = f"{size_kb:.1f}KB"
                    else:
                        size_str = f"{size_kb / 1024:.1f}MB"

                    # Truncate session name if too long
                    session_name = session["name"]
                    if len(session_name) > 32:
                        session_name = session_name[:29] + "..."

                    table.add_row(
                        session_name,
                        session["project_name"],
                        session["type"],
                        str(session["turns"]),
                        status_display,
                        mtime_str,
                        size_str
                    )

                console.print(table)
                console.print(f"\n  [dim]Total: {len(session_details)} active session(s)[/dim]")
                console.print(f"  [dim]Status: ✓=Committed ⏳=Processing ●=Empty[/dim]")
            else:
                console.print(f"  [dim]No active sessions found[/dim]")

        # Show watched projects
        watched_projects = get_watched_projects()
        if watched_projects:
            console.print(f"\n[bold cyan]Watched Projects[/bold cyan]")

            # Create table
            projects_table = Table(show_header=True, header_style="bold magenta")
            projects_table.add_column("Project", style="cyan", width=20)
            projects_table.add_column("Sessions", justify="center", style="yellow", width=10)
            projects_table.add_column("Last Commit", style="dim", width=20)

            for proj in watched_projects:
                try:
                    project_name = proj.name

                    # Count sessions
                    sessions_dir = proj / "sessions"
                    session_count = 0
                    if sessions_dir.exists():
                        session_count = len(list(sessions_dir.glob("*.jsonl")))

                    # Get last commit time
                    last_commit = ""
                    git_dir = proj / ".git"
                    if git_dir.exists():
                        try:
                            result = subprocess.run(
                                ["git", "log", "-1", "--format=%cr"],
                                cwd=proj,
                                capture_output=True,
                                text=True,
                                check=False
                            )
                            if result.returncode == 0 and result.stdout.strip():
                                last_commit = result.stdout.strip()
                        except Exception:
                            pass

                    # Add row to table
                    projects_table.add_row(
                        project_name,
                        str(session_count) if session_count > 0 else "-",
                        last_commit if last_commit else "-"
                    )

                except Exception as e:
                    logger.debug(f"Error reading project info: {e}")
                    continue

            console.print(projects_table)
            console.print(f"\n  [dim]Total: {len(watched_projects)} watched project(s)[/dim]")
        else:
            console.print(f"\n[dim]No projects being watched yet[/dim]")
            console.print(f"[dim]Run 'aline init' in a project directory to start tracking[/dim]")

        # Suggestions
        if status == "Stopped":
            console.print(f"\n  [dim]Run 'aline watcher start' to start the watcher[/dim]")
        elif status == "Inactive":
            console.print(f"\n  [dim]Suggestion: Restart watcher or check logs[/dim]")

        if not verbose:
            console.print(f"\n  [dim]Use 'aline watcher status -v' to see detailed session tracking[/dim]")

        console.print()
        return 0

    except Exception as e:
        logger.error(f"Error in watcher status: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return 1


def watcher_start_command() -> int:
    """
    Start the watcher in standalone mode.

    Launches a background daemon process that monitors session files
    and auto-commits changes.

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    try:
        # Check if already running
        is_running, pid, mode = detect_watcher_process()

        if is_running:
            console.print(f"[yellow]Watcher is already running (PID: {pid}, mode: {mode})[/yellow]")
            console.print(f"[dim]Use 'aline watcher stop' to stop it first[/dim]")
            return 0

        console.print(f"[cyan]Starting standalone watcher daemon...[/cyan]")

        # Launch the daemon as a background process
        import os
        import importlib.util

        # Get the path to the daemon script
        spec = importlib.util.find_spec("realign.watcher_daemon")
        if not spec or not spec.origin:
            console.print(f"[red]✗ Could not find watcher daemon module[/red]")
            return 1

        daemon_script = spec.origin

        # Launch daemon using python with nohup-like behavior
        # Using start_new_session=True to detach from terminal
        log_dir = Path.home() / '.aline/.logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        stdout_log = log_dir / 'watcher_stdout.log'
        stderr_log = log_dir / 'watcher_stderr.log'

        with open(stdout_log, 'a') as stdout_f, open(stderr_log, 'a') as stderr_f:
            process = subprocess.Popen(
                [sys.executable, daemon_script],
                stdout=stdout_f,
                stderr=stderr_f,
                start_new_session=True,
                cwd=Path.cwd()
            )

        # Give it a moment to start
        import time
        time.sleep(1)

        # Verify it started
        is_running, pid, mode = detect_watcher_process()

        if is_running:
            console.print(f"[green]✓ Watcher started successfully (PID: {pid})[/green]")
            console.print(f"[dim]Logs: {log_dir}/watcher_*.log[/dim]")
            return 0
        else:
            console.print(f"[red]✗ Failed to start watcher[/red]")
            console.print(f"[dim]Check logs: {stderr_log}[/dim]")
            return 1

    except Exception as e:
        logger.error(f"Error in watcher start: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return 1


def watcher_stop_command() -> int:
    """
    Stop ALL watcher processes (both standalone and MCP modes).

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    import time

    try:
        # Detect ALL running watcher processes
        all_processes = detect_all_watcher_processes()

        if not all_processes:
            console.print(f"[yellow]No watcher processes found[/yellow]")
            console.print(f"[dim]Use 'aline watcher start' to start it[/dim]")
            return 1

        # Display all processes that will be stopped
        if len(all_processes) == 1:
            pid, mode = all_processes[0]
            console.print(f"[cyan]Stopping watcher (PID: {pid}, mode: {mode})...[/cyan]")
        else:
            console.print(f"[cyan]Found {len(all_processes)} watcher processes, stopping all...[/cyan]")
            for pid, mode in all_processes:
                console.print(f"  • PID: {pid} (mode: {mode})")

        # Send SIGTERM to all processes
        failed_pids = []
        for pid, mode in all_processes:
            try:
                subprocess.run(
                    ['kill', str(pid)],
                    check=True,
                    timeout=2
                )
            except subprocess.CalledProcessError:
                failed_pids.append((pid, mode))

        # Wait a moment for graceful shutdown
        time.sleep(1)

        # Check if any processes are still running
        still_running = detect_all_watcher_processes()

        if still_running:
            # Force kill remaining processes
            console.print(f"[yellow]{len(still_running)} process(es) still running, forcing stop...[/yellow]")
            for pid, mode in still_running:
                try:
                    subprocess.run(
                        ['kill', '-9', str(pid)],
                        check=True,
                        timeout=2
                    )
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]✗ Failed to force-stop PID {pid}: {e}[/red]")
                    failed_pids.append((pid, mode))

        # Clean up PID file
        get_watcher_pid_file().unlink(missing_ok=True)

        # Final verification
        time.sleep(0.5)
        final_check = detect_all_watcher_processes()

        if not final_check:
            if len(all_processes) == 1:
                console.print(f"[green]✓ Watcher stopped successfully[/green]")
            else:
                console.print(f"[green]✓ All {len(all_processes)} watcher processes stopped successfully[/green]")
            return 0
        else:
            console.print(f"[red]✗ Failed to stop {len(final_check)} process(es)[/red]")
            for pid, mode in final_check:
                console.print(f"  • PID {pid} ({mode}) is still running")
            return 1

    except Exception as e:
        logger.error(f"Error stopping watcher: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return 1


def watcher_command(
    action: str = "status",
) -> int:
    """
    Main watcher command dispatcher.

    Args:
        action: Action to perform (status, start, stop)

    Returns:
        int: Exit code
    """
    if action == "status":
        return watcher_status_command()
    elif action == "start":
        return watcher_start_command()
    elif action == "stop":
        return watcher_stop_command()
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print(f"[dim]Available actions: status, start, stop[/dim]")
        return 1
