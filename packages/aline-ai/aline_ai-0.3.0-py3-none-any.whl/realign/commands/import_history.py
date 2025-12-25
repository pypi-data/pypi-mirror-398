#!/usr/bin/env python3
"""
Import History command - Discover and display historical Claude Code sessions.

This command finds all unprocessed historical sessions for the current project,
parses them turn-by-turn, and displays them in chronological order. This is a
dry-run/preview mode that prepares for future auto-commit functionality.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel

from ..hooks import get_claude_project_name, clean_user_message
from ..logging_config import setup_logger
from .. import get_realign_dir

# Initialize logger and console
logger = setup_logger('realign.import_history', 'import_history.log')
console = Console()


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class HistoricalTurn:
    """Represents a single turn in a historical session."""
    turn_number: int                # 1-indexed turn number within session
    session_id: str                 # Session ID (UUID)
    session_file: Path              # Path to original session file
    timestamp: datetime             # When the user message was sent
    user_message: str              # Full user message text
    user_message_preview: str      # First 80 chars for display


@dataclass
class HistoricalSession:
    """Represents a discovered historical session."""
    session_id: str                # UUID from filename
    session_file: Path             # Full path to session file
    created_at: datetime           # Session creation time
    modified_at: datetime          # Last modification time
    turns: List[HistoricalTurn]    # All turns in chronological order
    total_turns: int               # Cached turn count


# ============================================================================
# Session Discovery Functions
# ============================================================================

def discover_historical_sessions(project_path: Path) -> List[Path]:
    """
    Find all Claude Code sessions for the current project.

    Args:
        project_path: The project directory path

    Returns:
        List of session file paths (unfiltered)
    """
    logger.info(f"Discovering Claude Code sessions for project: {project_path}")

    # Get Claude project directory
    encoded_name = get_claude_project_name(project_path)
    claude_project_dir = Path.home() / ".claude" / "projects" / encoded_name

    logger.debug(f"Claude project directory: {claude_project_dir}")

    if not claude_project_dir.exists():
        logger.info(f"Claude project directory not found: {claude_project_dir}")
        return []

    # Find all session files (exclude agent files)
    all_sessions = []
    for session_file in claude_project_dir.glob("*.jsonl"):
        # Only include files starting with "session-" or UUID pattern
        # Exclude "agent-*.jsonl" files
        if not session_file.name.startswith("agent-"):
            all_sessions.append(session_file)
            logger.debug(f"Found session: {session_file.name}")

    logger.info(f"Discovered {len(all_sessions)} total sessions")
    return all_sessions


def filter_already_processed(sessions: List[Path], realign_dir: Path) -> List[Path]:
    """
    Filter out sessions that have already been processed.

    Checks:
    1. Session files in .realign/sessions/ (by stem matching)
    2. Metadata files in .realign/.metadata/ (by session ID)

    Args:
        sessions: List of session file paths
        realign_dir: Path to .realign directory

    Returns:
        List of unprocessed session file paths
    """
    sessions_dir = realign_dir / "sessions"
    metadata_dir = realign_dir / ".metadata"

    # Build set of processed session IDs
    processed_ids = set()

    # Check sessions directory
    if sessions_dir.exists():
        for processed_file in sessions_dir.glob("*.jsonl"):
            # Extract session ID from filename (format: username_agent_sessionid.jsonl)
            # Examples: minhao_claude_6e3d8ad3.jsonl, minhao_codex_019a7374.jsonl
            parts = processed_file.stem.split('_')
            if len(parts) >= 3:
                session_id = parts[-1]  # Last part is the session hash
                processed_ids.add(session_id)
                logger.debug(f"Marking session {session_id} as processed (in sessions/)")

    # Check metadata directory
    if metadata_dir.exists():
        for meta_file in metadata_dir.glob("*.meta"):
            # Metadata files are named: username_agent_sessionid.meta
            parts = meta_file.stem.split('_')
            if len(parts) >= 3:
                session_id = parts[-1]
                processed_ids.add(session_id)
                logger.debug(f"Marking session {session_id} as processed (in .metadata/)")

    # Filter sessions
    unprocessed = []
    for session_file in sessions:
        # Extract session ID - could be UUID or hash
        # Pattern 1: session-{UUID}.jsonl (Claude format)
        # Pattern 2: {UUID}.jsonl (plain UUID)
        session_name = session_file.stem
        if session_name.startswith("session-"):
            session_id = session_name.replace("session-", "")
        else:
            session_id = session_name

        # Check if this session has been processed
        # We need to check both full UUID and potential short hash
        is_processed = False

        # Check full ID
        if session_id in processed_ids:
            is_processed = True

        # Check if any processed ID is a prefix of this session (short hash matching)
        if not is_processed:
            for proc_id in processed_ids:
                if session_id.startswith(proc_id) or proc_id.startswith(session_id[:8]):
                    is_processed = True
                    break

        if not is_processed:
            unprocessed.append(session_file)
            logger.debug(f"Session {session_id} is unprocessed")
        else:
            logger.debug(f"Session {session_id} already processed, skipping")

    logger.info(f"Filtered to {len(unprocessed)} unprocessed sessions")
    return unprocessed


# ============================================================================
# Turn Extraction Functions
# ============================================================================

def extract_text_from_content(content) -> str:
    """
    Extract plain text from Claude message content blocks.

    Args:
        content: Message content (can be string, list, or dict)

    Returns:
        Extracted text string
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        return " ".join(text_parts)

    return ""


def extract_turns_from_session(session_file: Path) -> List[HistoricalTurn]:
    """
    Parse JSONL session file and extract all turns with user messages.

    Algorithm:
    1. Read line-by-line (JSONL format)
    2. For each line with type="user":
       - Skip if it's a tool_result (check content blocks)
       - Skip if it's continuation message ("This session is being continued")
       - Extract timestamp and message text
       - Use timestamp for deduplication (Claude 2.0 splits messages)
    3. Build list of unique turns ordered by timestamp

    Args:
        session_file: Path to session JSONL file

    Returns:
        List of HistoricalTurn objects
    """
    turns = []
    user_messages_by_timestamp = {}  # timestamp -> message text

    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON on line {line_num} in {session_file.name}: {e}")
                    continue

                # Only process user messages
                if data.get("type") != "user":
                    continue

                message = data.get("message", {})
                content = message.get("content", [])

                # Filter out tool results
                is_tool_result = False
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            is_tool_result = True
                            break

                if is_tool_result:
                    continue

                # Extract text from content
                message_text = extract_text_from_content(content)

                # Clean the message text (remove IDE tags, etc.)
                message_text = clean_user_message(message_text)

                # Skip empty messages
                if not message_text.strip():
                    continue

                # Skip continuation messages
                if "This session is being continued" in message_text:
                    continue

                # Extract timestamp
                timestamp_str = data.get("timestamp")
                if timestamp_str:
                    try:
                        # Handle ISO format with timezone
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        user_messages_by_timestamp[timestamp] = message_text
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
                        continue

    except FileNotFoundError:
        logger.error(f"Session file not found: {session_file}")
        return []
    except Exception as e:
        logger.error(f"Error reading session file {session_file}: {e}", exc_info=True)
        return []

    # Extract session ID from filename
    session_id = session_file.stem.replace("session-", "") if session_file.name.startswith("session-") else session_file.stem

    # Sort by timestamp and create Turn objects
    for idx, (timestamp, text) in enumerate(sorted(user_messages_by_timestamp.items()), 1):
        preview = text[:80] + "..." if len(text) > 80 else text
        turns.append(HistoricalTurn(
            turn_number=idx,
            session_id=session_id,
            session_file=session_file,
            timestamp=timestamp,
            user_message=text,
            user_message_preview=preview
        ))

    logger.debug(f"Extracted {len(turns)} turns from {session_file.name}")
    return turns


# ============================================================================
# Display Functions
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


def display_historical_sessions(
    sessions: List[HistoricalSession],
    verbose: bool = False,
    limit: Optional[int] = None
) -> None:
    """
    Display discovered sessions in formatted output.

    Args:
        sessions: List of HistoricalSession objects
        verbose: Show full messages instead of previews
        limit: Maximum number of sessions to display
    """
    if not sessions:
        console.print("\n[yellow]No historical sessions found to import.[/yellow]")
        console.print("[dim]All sessions have already been processed, or no Claude Code sessions exist for this project.[/dim]\n")
        return

    # Calculate statistics
    total_turns = sum(s.total_turns for s in sessions)
    date_range = f"{sessions[0].created_at.date()} to {sessions[-1].created_at.date()}" if len(sessions) > 1 else str(sessions[0].created_at.date())

    # Header
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]ReAlign Historical Session Import[/bold cyan]\n\n"
        f"Project: [green]{Path.cwd()}[/green]\n"
        f"Discovered: [yellow]{len(sessions)}[/yellow] session{'s' if len(sessions) != 1 else ''} | "
        f"[yellow]{total_turns}[/yellow] turn{'s' if total_turns != 1 else ''} | {date_range}",
        border_style="cyan"
    ))

    # Display sessions
    displayed = 0
    for idx, session in enumerate(sessions, 1):
        if limit and displayed >= limit:
            remaining = len(sessions) - displayed
            console.print(f"\n[dim]... and {remaining} more session{'s' if remaining != 1 else ''} (use --limit to see more)[/dim]\n")
            break

        # Session header
        console.print(f"\n{'─' * 70}")
        console.print(f"[bold cyan]Session #{idx}:[/bold cyan] [yellow]{session.session_id}[/yellow]")
        time_str = format_time_with_relative(session.created_at)
        console.print(f"[dim]Created: {time_str} | {session.total_turns} turn{'s' if session.total_turns != 1 else ''}[/dim]")
        console.print(f"{'─' * 70}")

        # Display turns
        for turn in session.turns:
            time_str = turn.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            message = turn.user_message if verbose else turn.user_message_preview
            console.print(f"  [cyan]Turn {turn.turn_number:2d}[/cyan]  [{time_str}]")
            console.print(f"          [dim]User:[/dim] \"{message}\"")
            console.print()  # Blank line between turns

        displayed += 1

    console.print()


# ============================================================================
# Commit Functions
# ============================================================================

def is_turn_processed(realign_dir: Path, session_id: str, turn_number: int) -> bool:
    """
    Check if a turn has already been processed and committed.

    Args:
        realign_dir: Path to .realign directory
        session_id: Session ID (UUID)
        turn_number: Turn number within session

    Returns:
        True if turn has been processed, False otherwise
    """
    metadata_dir = realign_dir / ".metadata"
    metadata_file = metadata_dir / f"{session_id}_turn_{turn_number}.meta"
    return metadata_file.exists()


def save_turn_metadata(
    realign_dir: Path,
    session_id: str,
    turn_number: int,
    commit_hash: str
):
    """
    Save metadata for a processed turn to enable resume functionality.

    Args:
        realign_dir: Path to .realign directory
        session_id: Session ID (UUID)
        turn_number: Turn number within session
        commit_hash: Git commit hash
    """
    import time

    metadata_dir = realign_dir / ".metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    metadata_file = metadata_dir / f"{session_id}_turn_{turn_number}.meta"
    metadata = {
        "processed_at": time.time(),
        "commit_hash": commit_hash,
        "turn_number": turn_number,
        "session_id": session_id
    }

    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger.debug(f"Saved metadata for turn {turn_number} of session {session_id}")


def generate_commit_message_for_turn(
    partial_session_file: Path,
    user_message: str,
    turn_number: int,
    use_llm: bool = False
) -> tuple[str, str, str]:
    """
    Generate commit message for a turn, optionally using LLM.

    Args:
        partial_session_file: Path to partial session file (JSONL format)
        user_message: User's message text (for fallback only)
        turn_number: Turn number
        use_llm: Whether to use LLM for summary generation

    Returns:
        Tuple of (title, description, model_name)
    """
    if not use_llm:
        # Simple commit message without LLM
        title_preview = user_message[:50]
        if len(user_message) > 50:
            title_preview += "..."
        title = f"Turn #{turn_number}: {title_preview}"
        description = "Historical session import - no summary"
        model_name = "historical-import"
        return title, description, model_name

    # Use LLM to generate summary by passing the partial session file content
    # to the existing generate_summary_with_llm function from hooks.py
    from ..hooks import generate_summary_with_llm

    try:
        # Read the partial session file content (JSONL format)
        with open(partial_session_file, 'r', encoding='utf-8') as f:
            session_content = f.read()

        # Call the existing LLM summary function
        llm_title, model_name, llm_description = generate_summary_with_llm(
            content=session_content,
            provider="auto"
        )

        # If LLM failed, fall back to simple message
        if not llm_title or not model_name:
            title_preview = user_message[:50]
            if len(user_message) > 50:
                title_preview += "..."
            title = f"Turn #{turn_number}: {title_preview}"
            description = "Historical session import - LLM unavailable"
            model_name = "historical-import"
            return title, description, model_name

        return llm_title, llm_description or "", model_name

    except Exception as e:
        logger.error(f"Error generating LLM summary: {e}", exc_info=True)
        # Fallback to simple message on error
        title_preview = user_message[:50]
        if len(user_message) > 50:
            title_preview += "..."
        title = f"Turn #{turn_number}: {title_preview}"
        description = f"Historical session import - LLM error: {str(e)}"
        model_name = "historical-import"
        return title, description, model_name


def create_partial_session_file(
    original_session_file: Path,
    realign_dir: Path,
    session_id: str,
    up_to_turn: int
) -> Path:
    """
    Create a partial session file containing only the first N turns.

    This ensures each turn's commit has meaningful session file changes.

    Args:
        original_session_file: Path to the full original session file
        realign_dir: Path to .realign directory
        session_id: Session ID (UUID)
        up_to_turn: Number of turns to include (1-indexed)

    Returns:
        Path to the created partial session file
    """
    import json

    sessions_dir = realign_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    # Read the original session file and extract lines up to the target turn
    session_lines = []
    turn_count = 0

    with open(original_session_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue

            data = json.loads(line)

            # Count user messages (excluding tool results and continuations)
            if data.get("type") == "user":
                message = data.get("message", {})
                content = message.get("content", [])

                # Check if this is a tool result
                is_tool_result = False
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            is_tool_result = True
                            break

                if not is_tool_result:
                    # Extract text to check for continuation messages
                    message_text = extract_text_from_content(content)
                    message_text = clean_user_message(message_text)

                    if message_text.strip() and "This session is being continued" not in message_text:
                        turn_count += 1

            # Add this line to the partial session
            session_lines.append(line)

            # Stop when we've collected enough turns
            if turn_count >= up_to_turn:
                break

    # Write partial session to a temporary file in sessions directory
    partial_file = sessions_dir / f"{session_id}.jsonl"
    with open(partial_file, 'w', encoding='utf-8') as f:
        f.writelines(session_lines)

    logger.debug(f"Created partial session file with {up_to_turn} turns: {partial_file}")
    return partial_file


def commit_historical_turns(
    sessions: List[HistoricalSession],
    realign_dir: Path,
    limit: Optional[int],
    no_llm: bool
) -> int:
    """
    Commit historical turns to git.

    Args:
        sessions: List of historical sessions
        realign_dir: Path to .realign directory
        limit: Maximum number of turns to process
        no_llm: Skip LLM summary generation (currently always True)

    Returns:
        Exit code (0 = success, 1 = error)
    """
    import os
    import getpass
    from ..tracker.git_tracker import ReAlignGitTracker

    # Step 1: Flatten sessions into list of turns
    all_turns = []
    for session in sessions:
        all_turns.extend(session.turns)

    # Step 2: Sort by timestamp globally
    all_turns.sort(key=lambda t: t.timestamp)

    # Step 3: Apply limit if specified
    if limit:
        all_turns = all_turns[:limit]
        total_turns = limit
    else:
        total_turns = len(all_turns)

    if total_turns == 0:
        console.print("\n[yellow]No turns to process.[/yellow]\n")
        return 0

    # Display header
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]ReAlign Historical Session Import (Commit Mode)[/bold cyan]\n\n"
        f"Project: [green]{Path.cwd()}[/green]\n"
        f"Discovered: [yellow]{len(sessions)}[/yellow] session{'s' if len(sessions) != 1 else ''} | "
        f"[yellow]{sum(len(s.turns) for s in sessions)}[/yellow] total turn{'s' if sum(len(s.turns) for s in sessions) != 1 else ''}\n"
        f"Processing: [yellow]{total_turns}[/yellow] turn{'s' if total_turns != 1 else ''}" +
        (f" (limited)" if limit else ""),
        border_style="cyan"
    ))
    console.print()

    # Step 4: Initialize git tracker
    try:
        git_tracker = ReAlignGitTracker(realign_dir)
    except Exception as e:
        logger.error(f"Failed to initialize git tracker: {e}", exc_info=True)
        console.print(f"[red]Error:[/red] Failed to initialize git tracker: {e}")
        return 1

    # Get username for session file naming
    try:
        username = os.getenv('USER') or getpass.getuser()
    except Exception:
        username = "unknown"

    # Step 5: Process each turn
    committed_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, turn in enumerate(all_turns, 1):
        # Check if already processed
        if is_turn_processed(realign_dir, turn.session_id, turn.turn_number):
            console.print(f"[{idx}/{total_turns}] Turn {turn.turn_number} of session {turn.session_id[:8]}...")
            console.print(f"       [yellow]Skipped:[/yellow] Already processed")
            console.print()
            skipped_count += 1
            continue

        # Display progress
        console.print(f"[{idx}/{total_turns}] Turn {turn.turn_number} of session {turn.session_id[:8]}...")

        try:
            # Create a partial session file containing only turns up to this point
            # This ensures each commit has meaningful session file changes
            partial_session_file = create_partial_session_file(
                original_session_file=turn.session_file,
                realign_dir=realign_dir,
                session_id=turn.session_id,
                up_to_turn=turn.turn_number
            )

            # Generate commit message (with or without LLM)
            # Pass the partial session file so LLM can analyze the full session context
            use_llm = not no_llm
            title, description, model_name = generate_commit_message_for_turn(
                partial_session_file=partial_session_file,
                user_message=turn.user_message,
                turn_number=turn.turn_number,
                use_llm=use_llm
            )

            # Prepare session ID for commit
            formatted_session_id = f"{username}_claude_{turn.session_id[:8]}"

            # Commit the turn with the partial session file
            commit_hash = git_tracker.commit_turn(
                session_id=formatted_session_id,
                turn_number=turn.turn_number,
                user_message=turn.user_message,
                llm_title=title,
                llm_description=description,
                model_name=model_name,
                modified_files=[],  # No modified files for historical imports
                session_file=partial_session_file
            )

            if commit_hash:
                console.print(f"       [green]Committed:[/green] {commit_hash[:7]}")
                committed_count += 1

                # Save metadata
                save_turn_metadata(realign_dir, turn.session_id, turn.turn_number, commit_hash)
            else:
                console.print(f"       [red]Failed:[/red] No commit hash returned")
                failed_count += 1

        except Exception as e:
            logger.error(f"Failed to commit turn {turn.turn_number}: {e}", exc_info=True)
            console.print(f"       [red]Failed:[/red] {str(e)}")
            failed_count += 1

        console.print()

    # Step 6: Display summary
    console.print(Panel.fit(
        f"[bold cyan]Summary[/bold cyan]\n\n"
        f"Total processed: [yellow]{total_turns}[/yellow] turn{'s' if total_turns != 1 else ''}\n"
        f"Committed: [green]{committed_count}[/green] turn{'s' if committed_count != 1 else ''}\n"
        f"Skipped: [yellow]{skipped_count}[/yellow] turn{'s' if skipped_count != 1 else ''} (already processed)\n"
        f"Failed: [red]{failed_count}[/red] turn{'s' if failed_count != 1 else ''}\n\n"
        f"[dim]Next steps:[/dim]\n"
        f"- Run [cyan]'aline review'[/cyan] to see commits\n" +
        (f"- Run [cyan]'aline import-history --commit'[/cyan] again to continue" if limit else ""),
        border_style="cyan"
    ))
    console.print()

    return 0 if failed_count == 0 else 1


# ============================================================================
# Main Command Function
# ============================================================================

def import_history_command(
    verbose: bool = False,
    limit: Optional[int] = None,
    commit: bool = False,
    no_llm: bool = False,
) -> int:
    """
    Discover and display historical sessions for import.

    This command finds all unprocessed Claude Code sessions for the current project,
    parses them turn-by-turn, and displays them in chronological order.

    Args:
        verbose: Show full user messages instead of previews
        limit: Maximum number of sessions to display (or turns to commit if commit=True)
        commit: Actually commit historical turns to git
        no_llm: Skip LLM summary generation (default behavior for now)

    Returns:
        int: Exit code (0 = success, 1 = error)
    """
    try:
        # Step 1: Validate initialization
        project_path = Path.cwd()
        realign_dir = get_realign_dir(project_path)

        if not realign_dir.exists():
            console.print("[red]Error:[/red] ReAlign is not initialized in this directory.")
            console.print("[dim]Run 'aline init' to set up session tracking.[/dim]")
            return 1

        logger.info(f"Starting import-history command for project: {project_path}")
        logger.debug(f"ReAlign directory: {realign_dir}")

        # Step 2: Discover sessions
        all_sessions = discover_historical_sessions(project_path)

        if not all_sessions:
            console.print("\n[yellow]No Claude Code sessions found for this project.[/yellow]")
            console.print("[dim]Make sure you have used Claude Code in this project directory.[/dim]\n")
            return 0

        # Step 3: Filter already processed sessions
        unprocessed_sessions = filter_already_processed(all_sessions, realign_dir)

        if not unprocessed_sessions:
            console.print("\n[green]✓[/green] All Claude Code sessions have already been imported!")
            console.print(f"[dim]Found {len(all_sessions)} total session(s), all processed.[/dim]\n")
            return 0

        # Step 4: Parse sessions and extract turns
        historical_sessions = []

        for session_file in unprocessed_sessions:
            # Extract session ID from filename
            session_name = session_file.stem
            if session_name.startswith("session-"):
                session_id = session_name.replace("session-", "")
            else:
                session_id = session_name

            # Get file timestamps
            try:
                stat = session_file.stat()
                created_at = datetime.fromtimestamp(stat.st_ctime)
                modified_at = datetime.fromtimestamp(stat.st_mtime)
            except Exception as e:
                logger.warning(f"Failed to get timestamps for {session_file}: {e}")
                # Use current time as fallback
                created_at = datetime.now()
                modified_at = datetime.now()

            # Extract turns
            turns = extract_turns_from_session(session_file)

            # Skip sessions with no turns
            if not turns:
                logger.debug(f"Skipping session {session_id} with no turns")
                continue

            # Create HistoricalSession object
            historical_sessions.append(HistoricalSession(
                session_id=session_id,
                session_file=session_file,
                created_at=created_at,
                modified_at=modified_at,
                turns=turns,
                total_turns=len(turns)
            ))

        # Step 5: Sort sessions chronologically (oldest first)
        historical_sessions.sort(key=lambda s: s.created_at)

        # Step 6: Display or commit based on mode
        if commit:
            # Commit mode: actually create git commits
            total_commits = commit_historical_turns(
                sessions=historical_sessions,
                realign_dir=realign_dir,
                limit=limit,
                no_llm=no_llm
            )
            logger.info(f"Successfully committed {total_commits} historical turns")
            return 0
        else:
            # Display mode: show preview only
            display_historical_sessions(historical_sessions, verbose=verbose, limit=limit)
            logger.info(f"Successfully processed {len(historical_sessions)} historical sessions")
            return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]Import cancelled by user[/yellow]")
        return 0
    except Exception as e:
        logger.error(f"Error in import-history command: {e}", exc_info=True)
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("[dim]Check logs for more details: ~/.aline/.logs/import_history.log[/dim]\n")
        return 1
