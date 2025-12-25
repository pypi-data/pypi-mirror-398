#!/usr/bin/env python3
"""
ReAlign Git Hooks - Entry points for git hook commands.

This module provides the hook functionality as Python commands that can be
invoked directly from git hooks without copying any Python files to the target repository.
"""

import os
import re
import sys
import json
import time
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from .config import ReAlignConfig
from .claude_detector import find_claude_sessions_dir
from .logging_config import setup_logger

try:
    from .redactor import check_and_redact_session, save_original_session
    REDACTOR_AVAILABLE = True
except ImportError:
    REDACTOR_AVAILABLE = False

# Initialize logger for hooks
logger = setup_logger('realign.hooks', 'hooks.log')


# ============================================================================
# Message Cleaning Utilities
# ============================================================================

def clean_user_message(text: str) -> str:
    """
    Clean user message by removing IDE context tags and other system noise.

    This function removes IDE-generated context that's not part of the actual
    user intent, making commit messages and session logs cleaner.

    Removes:
    - <ide_opened_file>...</ide_opened_file> tags
    - <ide_selection>...</ide_selection> tags
    - System interrupt messages like "[Request interrupted by user for tool use]"
    - Other system-generated context tags

    Args:
        text: Raw user message text

    Returns:
        Cleaned message text with system tags removed, or empty string if message is purely system-generated
    """
    if not text:
        return text

    # Check for system interrupt messages first (return empty for these)
    # These are generated when user stops the AI mid-execution
    if text.strip() == "[Request interrupted by user for tool use]":
        return ""

    # Remove IDE opened file tags
    text = re.sub(r'<ide_opened_file>.*?</ide_opened_file>\s*', '', text, flags=re.DOTALL)

    # Remove IDE selection tags
    text = re.sub(r'<ide_selection>.*?</ide_selection>\s*', '', text, flags=re.DOTALL)

    # Remove other common system tags if needed
    # text = re.sub(r'<system_context>.*?</system_context>\s*', '', text, flags=re.DOTALL)

    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Replace multiple blank lines with double newline
    text = text.strip()

    return text


def get_new_content_from_git_diff(repo_root: Path, session_relpath: str) -> str:
    """
    Extract new content added in this commit by using git diff.
    Returns the raw text of all added lines, without parsing.

    Args:
        repo_root: Path to git repository root
        session_relpath: Relative path to session file in repo (e.g. ".realign/sessions/xxx.jsonl")

    Returns:
        String containing all new content added in this commit
    """
    logger.debug(f"Extracting new content from git diff for: {session_relpath}")

    try:
        # Use --cached to check staged changes (what will be committed)
        # This compares the staging area with HEAD
        result = subprocess.run(
            ["git", "diff", "--cached", "--", session_relpath],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            logger.warning(f"Git diff command failed with return code {result.returncode}")
            return ""

        # If no diff output, this file has no staged changes in this commit
        if not result.stdout.strip():
            logger.debug(f"No staged changes found for: {session_relpath}")
            return ""

        # Parse diff output to extract added lines
        new_lines = []
        for line in result.stdout.split("\n"):
            # Lines starting with '+' (but not '+++') are additions
            if line.startswith("+") and not line.startswith("+++"):
                # Remove the '+' prefix
                new_lines.append(line[1:])

        content = "\n".join(new_lines)
        logger.info(f"Extracted {len(new_lines)} new lines ({len(content)} bytes) from {session_relpath}")
        return content

    except subprocess.TimeoutExpired:
        logger.error(f"Git diff command timed out for: {session_relpath}")
        print("Warning: git diff command timed out", file=sys.stderr)
        return ""
    except Exception as e:
        logger.error(f"Failed to extract new content from git diff: {e}", exc_info=True)
        print(f"Warning: Could not extract new content from git diff: {e}", file=sys.stderr)
        return ""


def get_claude_project_name(project_path: Path) -> str:
    """
    Convert a project path to Claude Code's project directory name format.

    Claude Code transforms project paths by replacing '/' with '-' (excluding root '/').
    For example: /Users/alice/Projects/MyApp -> -Users-alice-Projects-MyApp
    """
    abs_path = project_path.resolve()
    path_str = str(abs_path)
    if path_str.startswith('/'):
        path_str = path_str[1:]
    return '-' + path_str.replace('/', '-')


def find_codex_latest_session(project_path: Path, days_back: int = 7) -> Optional[Path]:
    """
    Find the most recent Codex session for a given project path.

    Codex stores sessions in ~/.codex/sessions/{YYYY}/{MM}/{DD}/
    with all projects mixed together. We need to search by date
    and filter by the 'cwd' field in session metadata.

    Args:
        project_path: The absolute path to the project
        days_back: Number of days to look back (default: 7)

    Returns:
        Path to the most recent session file, or None if not found
    """
    from datetime import datetime, timedelta

    logger.debug(f"Searching for Codex sessions for project: {project_path}")

    codex_sessions_base = Path.home() / ".codex" / "sessions"

    if not codex_sessions_base.exists():
        logger.debug(f"Codex sessions directory not found: {codex_sessions_base}")
        return None

    # Normalize project path for comparison
    abs_project_path = str(project_path.resolve())

    matching_sessions = []

    # Search through recent days
    for days_ago in range(days_back + 1):
        target_date = datetime.now() - timedelta(days=days_ago)
        date_path = codex_sessions_base / str(target_date.year) / f"{target_date.month:02d}" / f"{target_date.day:02d}"

        if not date_path.exists():
            continue

        # Check all session files in this date directory
        for session_file in date_path.glob("rollout-*.jsonl"):
            try:
                # Read first line to get session metadata
                with open(session_file, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if first_line:
                        data = json.loads(first_line)
                        if data.get('type') == 'session_meta':
                            session_cwd = data.get('payload', {}).get('cwd', '')
                            # Match the project path
                            if session_cwd == abs_project_path:
                                matching_sessions.append(session_file)
                                logger.debug(f"Found matching Codex session: {session_file}")
            except (json.JSONDecodeError, IOError) as e:
                logger.debug(f"Skipping malformed session file {session_file}: {e}")
                continue

    # Sort by modification time, newest first
    matching_sessions.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    if matching_sessions:
        logger.info(f"Found {len(matching_sessions)} Codex session(s), using latest: {matching_sessions[0]}")
    else:
        logger.debug("No matching Codex sessions found")

    return matching_sessions[0] if matching_sessions else None


def find_all_claude_sessions() -> List[Path]:
    """
    Find all active Claude Code sessions from ALL projects.

    Scans ~/.claude/projects/ and returns the latest session from each project.

    Returns:
        List of session file paths from all Claude projects
    """
    sessions = []
    claude_base = Path.home() / ".claude" / "projects"

    if not claude_base.exists():
        logger.debug(f"Claude projects directory not found: {claude_base}")
        return sessions

    # Iterate through all project directories
    for project_dir in claude_base.iterdir():
        if not project_dir.is_dir():
            continue

        # Skip system directories
        if project_dir.name.startswith('.'):
            continue

        # Find the latest session in this project directory
        session = find_latest_session(project_dir)
        if session:
            sessions.append(session)
            logger.debug(f"Found Claude session in {project_dir.name}: {session.name}")

    logger.info(f"Found {len(sessions)} Claude session(s) across all projects")
    return sessions


def find_all_active_sessions(
    config: ReAlignConfig,
    project_path: Optional[Path] = None
) -> List[Path]:
    """
    Find all active session files based on enabled auto-detection options.

    Returns a list of session file paths from all enabled sources:
    - Codex session (if auto_detect_codex is True)
    - Claude Code latest session (if auto_detect_claude is True)
    - Sessions from local_history_path (if no auto-detection or as fallback)

    Args:
        config: Configuration object
        project_path: Optional path to the current project (git repo root).
                     If None, will find sessions from ALL projects (multi-project mode).

    Returns:
        List of session file paths (may be empty if no sessions found)
    """
    logger.info("Searching for active AI sessions")
    logger.debug(f"Config: auto_detect_codex={config.auto_detect_codex}, auto_detect_claude={config.auto_detect_claude}")
    logger.debug(f"Project path: {project_path}")

    sessions = []

    # If REALIGN_LOCAL_HISTORY_PATH is set, only use that path (disables auto-detection)
    if os.getenv("REALIGN_LOCAL_HISTORY_PATH"):
        history_path = config.expanded_local_history_path
        logger.info(f"Using explicit history path from environment: {history_path}")
        session = find_latest_session(history_path)
        if session:
            sessions.append(session)
            logger.info(f"Found session at explicit path: {session}")
        else:
            logger.warning(f"No session found at explicit path: {history_path}")
        return sessions

    # Multi-project mode: find sessions from ALL projects
    if project_path is None:
        logger.info("Multi-project mode: scanning all projects")

        # Find all Claude sessions if enabled
        if config.auto_detect_claude:
            logger.debug("Scanning all Claude projects")
            claude_sessions = find_all_claude_sessions()
            sessions.extend(claude_sessions)

        # TODO: Add Codex multi-project support if needed
        # For now, Codex sessions are only found when project_path is specified

        if sessions:
            logger.info(f"Multi-project scan complete: found {len(sessions)} session(s)")
            return sessions

        # Fallback: try local history path
        logger.debug("No sessions found in multi-project scan, trying fallback path")
        history_path = config.expanded_local_history_path
        session = find_latest_session(history_path)
        if session:
            sessions.append(session)
            logger.info(f"Found session at fallback path: {session}")
        else:
            logger.warning(f"No session found at fallback path: {history_path}")

        return sessions

    # Single-project mode: find sessions for specific project
    logger.info(f"Single-project mode for: {project_path}")

    # Try Codex auto-detection if enabled
    if config.auto_detect_codex:
        logger.debug("Attempting Codex auto-detection")
        codex_session = find_codex_latest_session(project_path)
        if codex_session:
            sessions.append(codex_session)

    # Try Claude auto-detection if enabled
    if config.auto_detect_claude:
        logger.debug("Attempting Claude auto-detection")
        claude_dir = find_claude_sessions_dir(project_path)
        if claude_dir:
            logger.debug(f"Found Claude sessions directory: {claude_dir}")
            claude_session = find_latest_session(claude_dir)
            if claude_session:
                sessions.append(claude_session)
                logger.info(f"Found Claude session: {claude_session}")
        else:
            logger.debug("No Claude sessions directory found")

    # If no sessions found from auto-detection, try fallback path
    if not sessions:
        history_path = config.expanded_local_history_path
        logger.debug(f"No sessions from auto-detection, trying fallback path: {history_path}")
        session = find_latest_session(history_path)
        if session:
            sessions.append(session)
            logger.info(f"Found session at fallback path: {session}")
        else:
            logger.warning(f"No session found at fallback path: {history_path}")

    logger.info(f"Session discovery complete: found {len(sessions)} session(s)")
    return sessions


def find_latest_session(history_path: Path, explicit_path: Optional[str] = None) -> Optional[Path]:
    """
    Find the most recent session file.

    Filters out Claude Code agent sessions (agent-*.jsonl) since they are
    sub-tasks of main sessions and their results are already incorporated
    into the main session files.

    Args:
        history_path: Path to history directory or a specific session file (for Codex)
        explicit_path: Explicit path to a session file (overrides history_path)

    Returns:
        Path to the session file, or None if not found
    """
    if explicit_path:
        session_file = Path(explicit_path)
        if session_file.exists():
            return session_file
        return None

    # Expand user path
    history_path = Path(os.path.expanduser(history_path)) if isinstance(history_path, str) else history_path

    if not history_path.exists():
        return None

    # If history_path is already a file (e.g., Codex session), return it directly
    if history_path.is_file():
        return history_path

    # Otherwise, search directory for session files
    session_files = []
    for pattern in ["*.json", "*.jsonl"]:
        for file in history_path.glob(pattern):
            # Filter out Claude Code agent sessions (agent-*.jsonl)
            # These are sub-tasks whose results are already in main sessions
            if file.name.startswith("agent-"):
                logger.debug(f"Skipping agent session: {file.name}")
                continue
            session_files.append(file)

    if not session_files:
        return None

    # Return most recently modified
    return max(session_files, key=lambda p: p.stat().st_mtime)


def filter_session_content(content: str) -> Tuple[str, str, str]:
    """
    Filter session content to extract meaningful information for LLM summarization.

    Filters out exploratory operations (Read, Grep, Glob) and technical details,
    keeping only user requests, AI responses, and code changes.

    Args:
        content: Raw text content of new session additions

    Returns:
        Tuple of (user_messages, assistant_replies, code_changes)
    """
    if not content or not content.strip():
        return "", "", ""

    user_messages = []
    assistant_replies = []
    code_changes = []

    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        try:
            obj = json.loads(line)

            # Extract user messages and tool results
            if obj.get("type") == "user":
                msg = obj.get("message", {})
                if isinstance(msg, dict):
                    content_data = msg.get("content", "")
                    if isinstance(content_data, str) and content_data.strip():
                        user_messages.append(content_data.strip())
                    elif isinstance(content_data, list):
                        # Extract text from content list
                        for item in content_data:
                            if isinstance(item, dict):
                                if item.get("type") == "text":
                                    text = item.get("text", "").strip()
                                    if text:
                                        user_messages.append(text)
                                # Extract code changes from tool results
                                elif item.get("type") == "tool_result":
                                    tool_use_result = obj.get("toolUseResult", {})
                                    if "oldString" in tool_use_result and "newString" in tool_use_result:
                                        # This is an Edit operation
                                        new_string = tool_use_result.get("newString", "")
                                        if new_string:
                                            code_changes.append(f"Edit: {new_string[:300]}")
                                    elif "content" in tool_use_result and "filePath" in tool_use_result:
                                        # This is a Write operation
                                        new_content = tool_use_result.get("content", "")
                                        if new_content:
                                            code_changes.append(f"Write: {new_content[:300]}")

            # Extract assistant text replies (not tool use)
            elif obj.get("type") == "assistant":
                msg = obj.get("message", {})
                if isinstance(msg, dict):
                    content_data = msg.get("content", [])
                    if isinstance(content_data, list):
                        for item in content_data:
                            if isinstance(item, dict):
                                # Only extract text blocks, skip tool_use blocks
                                if item.get("type") == "text":
                                    text = item.get("text", "").strip()
                                    if text:
                                        assistant_replies.append(text)
                                # Extract code changes from Edit/Write tool uses
                                elif item.get("type") == "tool_use":
                                    tool_name = item.get("name", "")
                                    if tool_name in ("Edit", "Write"):
                                        params = item.get("input", {})
                                        if tool_name == "Edit":
                                            new_string = params.get("new_string", "")
                                            if new_string:
                                                code_changes.append(f"Edit: {new_string[:200]}")
                                        elif tool_name == "Write":
                                            new_content = params.get("content", "")
                                            if new_content:
                                                code_changes.append(f"Write: {new_content[:200]}")

            # Also handle simple role/content format (for compatibility)
            elif obj.get("role") == "user":
                content_text = obj.get("content", "")
                if isinstance(content_text, str) and content_text.strip():
                    user_messages.append(content_text.strip())

            elif obj.get("role") == "assistant":
                content_text = obj.get("content", "")
                if isinstance(content_text, str) and content_text.strip():
                    assistant_replies.append(content_text.strip())

        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON or doesn't have expected structure, skip
            continue

    # Join with newlines for better readability
    user_str = "\n".join(user_messages) if user_messages else ""
    assistant_str = "\n".join(assistant_replies) if assistant_replies else ""
    code_str = "\n".join(code_changes) if code_changes else ""

    return user_str, assistant_str, code_str


def simple_summarize(content: str, max_chars: int = 500) -> str:
    """
    Generate a simple summary from new session content.
    Extracts key information without LLM.

    Args:
        content: Raw text content of new session additions
        max_chars: Maximum characters in summary
    """
    if not content or not content.strip():
        return "No new content in this session"

    lines = content.strip().split("\n")

    # Try to extract meaningful content from JSONL format
    summaries = []
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            # Extract summary from special summary lines
            if obj.get("type") == "summary" and obj.get("summary"):
                summaries.append(f"Summary: {obj.get('summary')}")
            # Extract message content from user/assistant messages (complex format)
            elif obj.get("type") in ("user", "assistant") and obj.get("message"):
                msg = obj.get("message")
                if isinstance(msg, dict) and msg.get("content"):
                    content_text = msg.get("content")
                    if isinstance(content_text, str):
                        summaries.append(content_text[:100])
                    elif isinstance(content_text, list):
                        for item in content_text:
                            if isinstance(item, dict) and item.get("type") == "text":
                                summaries.append(item.get("text", "")[:100])
                                break
            # Also handle simple role/content format (for compatibility)
            elif obj.get("role") in ("user", "assistant") and obj.get("content"):
                content_text = obj.get("content")
                if isinstance(content_text, str):
                    summaries.append(content_text[:100])
        except (json.JSONDecodeError, KeyError, TypeError):
            # Not JSON or doesn't have expected structure, try raw text
            if len(line) > 20:
                summaries.append(line[:100])

    if summaries:
        summary = " | ".join(summaries[:3])
        return summary[:max_chars]

    # Fallback: surface the first few non-empty raw lines to give context
    fallback_lines = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        # Skip noisy JSON braces-only lines
        if stripped in ("{", "}", "[", "]"):
            continue
        fallback_lines.append(stripped[:120])
        if len(fallback_lines) == 3:
            break

    if fallback_lines:
        summary = " | ".join(fallback_lines)
        return summary[:max_chars]

    return f"Session updated with {len(lines)} new lines"


def detect_agent_from_session_path(session_relpath: str) -> str:
    """Infer agent type based on session filename."""
    lower_path = session_relpath.lower()

    if "codex" in lower_path or "rollout-" in lower_path:
        return "Codex"
    if "claude" in lower_path or "agent-" in lower_path:
        return "Claude"
    if lower_path.endswith(".jsonl"):
        # Default to Unknown to avoid mislabeling generic files
        return "Unknown"
    return "Unknown"


def generate_summary_with_llm(
    content: str,
    max_chars: int = 500,
    provider: str = "auto"
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Generate summary using LLM (Anthropic Claude or OpenAI) for NEW content only.
    Returns (title, model_name, description) tuple, or (None, None, None) if LLM is unavailable.

    Args:
        content: Raw text content of new session additions
        max_chars: Maximum characters in summary (not used, kept for compatibility)
        provider: LLM provider to use - "auto" (try Claude then OpenAI), "claude", or "openai"

    Returns:
        Tuple of (title, model_name, description) where:
        - title: One-line summary (max 150 chars)
        - model_name: Name of the model used
        - description: Detailed description of what happened (200-400 chars)
    """
    logger.info(f"Attempting to generate LLM summary (provider: {provider})")

    if not content or not content.strip():
        logger.debug("No content provided for summarization")
        return "No new content in this session", None, ""

    # Filter content to extract meaningful information
    user_messages, assistant_replies, code_changes = filter_session_content(content)

    # If no meaningful content after filtering, return early
    if not user_messages and not assistant_replies and not code_changes:
        logger.debug("No meaningful content after filtering")
        return "Session update with no significant changes", None, "No significant changes detected in this session"

    # System prompt for structured summarization
    system_prompt = """You are a git commit message generator for AI chat sessions.
Analyze the conversation and code changes, then generate a summary in JSON format:
{
  "title": "One-line summary (imperative mood, like 'Add feature X' or 'Fix bug in Y'. Aim for 80-120 chars, up to 150 max. Use complete words only - never truncate words. Omit articles like 'the', 'a' when possible to save space)",
  "description": "Detailed description of what happened in this session. Aim for 300-600 words - be thorough and complete. Focus on key actions, decisions, and outcomes. Include specific details like function names, features discussed, bugs fixed, etc. NEVER truncate - write complete sentences."
}

IMPORTANT for title:
- Keep it concise (80-120 chars ideal, 150 max) but COMPLETE - no truncated words
- Use imperative mood (e.g., "Add", "Fix", "Refactor", "Implement")
- If you can't fit everything, prioritize the most important change

IMPORTANT for description:
- Be thorough and complete (300-600 words)
- Focus on WHAT was accomplished and WHY, not HOW
- Include technical details: function names, module names, specific features
- Mention key decisions or discussions
- Write in clear, complete sentences - grammar matters for readability
- NEVER truncate mid-sentence - always finish your thought
- Avoid mentioning tool names like 'Edit', 'Write', 'Read'
- For discussions without code: summarize the topics and conclusions
- For code changes: describe what was changed and the purpose
- If there were multiple related changes, group them logically

Return JSON only, no other text."""

    # Build user prompt with filtered content
    user_prompt_parts = ["Summarize this AI chat session:\n"]

    if user_messages:
        user_prompt_parts.append(f"User requests:\n{user_messages[:1500]}\n")

    if assistant_replies:
        user_prompt_parts.append(f"AI responses:\n{assistant_replies[:1500]}\n")

    if code_changes:
        user_prompt_parts.append(f"Code changes:\n{code_changes[:1500]}\n")

    user_prompt_parts.append("\nReturn JSON only, no other text.")

    user_prompt = "\n".join(user_prompt_parts)

    # Determine which providers to try based on the provider parameter
    try_claude = provider in ("auto", "claude")
    try_openai = provider in ("auto", "openai")

    # Try Anthropic (Claude) first if enabled
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if try_claude and anthropic_key:
        logger.debug("ANTHROPIC_API_KEY found, attempting Claude")
        print("   → Trying Anthropic (Claude)...", file=sys.stderr)
        try:
            import anthropic
            import time
            start_time = time.time()

            client = anthropic.Anthropic(api_key=anthropic_key)
            logger.debug("Anthropic client initialized")

            response = client.messages.create(
                model="claude-3-5-haiku-20241022",  # Fast and cost-effective
                max_tokens=1000,  # Increased to allow complete descriptions (300-600 words)
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            elapsed = time.time() - start_time
            response_text = response.content[0].text.strip()
            logger.info(f"Claude API success: {len(response_text)} chars in {elapsed:.2f}s")
            logger.debug(f"Claude response: {response_text[:200]}...")

            # Parse JSON response
            try:
                # Try to extract JSON if wrapped in markdown code blocks
                json_str = response_text
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    # Only extract if closing ``` was found
                    if json_end != -1:
                        json_str = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    # Only extract if closing ``` was found
                    if json_end != -1:
                        json_str = response_text[json_start:json_end].strip()

                summary_data = json.loads(json_str)
                title = summary_data.get("title", "")
                description = summary_data.get("description", "")

                # Validate title is not just brackets or very short
                if not title or len(title.strip()) < 2:
                    logger.warning(f"Generated title is empty or too short: '{title}'")
                    raise json.JSONDecodeError("Title validation failed", json_str, 0)

                print("   ✅ Anthropic (Claude) summary successful", file=sys.stderr)
                return title, "claude-3-5-haiku-20241022", description

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from Claude response: {e}")
                logger.debug(f"Raw response: {response_text}")
                # Fallback: use first line as title, empty description
                first_line = response_text.split("\n")[0][:150].strip()
                # Validate fallback title is reasonable
                if first_line and len(first_line) >= 2 and not first_line.startswith("{"):
                    print("   ⚠️  Claude response was not valid JSON, using fallback", file=sys.stderr)
                    return first_line, "claude-3-5-haiku-20241022", ""
                else:
                    logger.error(f"Claude fallback title validation failed: '{first_line}'")
                    return None, None, None

        except ImportError:
            logger.warning("Anthropic package not installed")
            if provider == "claude":
                print("   ❌ Anthropic package not installed", file=sys.stderr)
                return None, None, None
            else:
                print("   ❌ Anthropic package not installed, trying OpenAI...", file=sys.stderr)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Claude API error: {error_msg}", exc_info=True)
            if provider == "claude":
                # If specifically requesting Claude, don't fall back
                if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                    logger.error("Claude authentication failed")
                    print(f"   ❌ Anthropic authentication failed (check API key)", file=sys.stderr)
                elif "quota" in error_msg.lower() or "credit" in error_msg.lower():
                    logger.error("Claude quota/credit issue")
                    print(f"   ❌ Anthropic quota/credit issue", file=sys.stderr)
                else:
                    print(f"   ❌ Anthropic API error: {e}", file=sys.stderr)
                return None, None, None
            else:
                # Auto mode: try falling back to OpenAI
                if "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
                    logger.warning("Claude auth failed, falling back to OpenAI")
                    print(f"   ❌ Anthropic authentication failed (check API key), trying OpenAI...", file=sys.stderr)
                elif "quota" in error_msg.lower() or "credit" in error_msg.lower():
                    logger.warning("Claude quota issue, falling back to OpenAI")
                    print(f"   ❌ Anthropic quota/credit issue, trying OpenAI...", file=sys.stderr)
                else:
                    logger.warning(f"Claude API error, falling back to OpenAI: {error_msg}")
                    print(f"   ❌ Anthropic API error: {e}, trying OpenAI...", file=sys.stderr)
    elif try_claude:
        logger.debug("ANTHROPIC_API_KEY not set")
        if provider == "claude":
            print("   ❌ ANTHROPIC_API_KEY not set", file=sys.stderr)
            return None, None, None
        else:
            print("   ⓘ ANTHROPIC_API_KEY not set, trying OpenAI...", file=sys.stderr)

    # Fallback to OpenAI (or try OpenAI directly if provider is "openai")
    openai_key = os.getenv("OPENAI_API_KEY")
    if try_openai and openai_key:
        logger.debug("OPENAI_API_KEY found, attempting OpenAI")
        print("   → Trying OpenAI (GPT)...", file=sys.stderr)
        try:
            import openai
            import time
            start_time = time.time()

            client = openai.OpenAI(api_key=openai_key)
            logger.debug("OpenAI client initialized")

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                max_tokens=1000,  # Increased to allow complete descriptions (300-600 words)
                temperature=0.7,
            )

            elapsed = time.time() - start_time
            response_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI API success: {len(response_text)} chars in {elapsed:.2f}s")
            logger.debug(f"OpenAI response: {response_text[:200]}...")

            # Parse JSON response
            try:
                # Try to extract JSON if wrapped in markdown code blocks
                json_str = response_text
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    # Only extract if closing ``` was found
                    if json_end != -1:
                        json_str = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    # Only extract if closing ``` was found
                    if json_end != -1:
                        json_str = response_text[json_start:json_end].strip()

                summary_data = json.loads(json_str)
                title = summary_data.get("title", "")
                description = summary_data.get("description", "")

                # Validate title is not just brackets or very short
                if not title or len(title.strip()) < 2:
                    logger.warning(f"Generated title is empty or too short: '{title}'")
                    raise json.JSONDecodeError("Title validation failed", json_str, 0)

                print("   ✅ OpenAI (GPT) summary successful", file=sys.stderr)
                return title, "gpt-3.5-turbo", description

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from OpenAI response: {e}")
                logger.debug(f"Raw response: {response_text}")
                # Fallback: use first line as title, empty description
                first_line = response_text.split("\n")[0][:150].strip()
                # Validate fallback title is reasonable
                if first_line and len(first_line) >= 2 and not first_line.startswith("{"):
                    print("   ⚠️  OpenAI response was not valid JSON, using fallback", file=sys.stderr)
                    return first_line, "gpt-3.5-turbo", ""
                else:
                    logger.error(f"OpenAI fallback title validation failed: '{first_line}'")
                    return None, None, None

        except ImportError:
            logger.warning("OpenAI package not installed")
            print("   ❌ OpenAI package not installed", file=sys.stderr)
            return None, None, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"OpenAI API error: {error_msg}", exc_info=True)
            if "Incorrect API key" in error_msg or "authentication" in error_msg.lower():
                logger.error("OpenAI authentication failed")
                print(f"   ❌ OpenAI authentication failed (check API key)", file=sys.stderr)
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                logger.error("OpenAI quota/billing issue")
                print(f"   ❌ OpenAI quota/billing issue", file=sys.stderr)
            else:
                print(f"   ❌ OpenAI API error: {e}", file=sys.stderr)
            return None, None, None
    elif try_openai:
        logger.debug("OPENAI_API_KEY not set")
        print("   ❌ OPENAI_API_KEY not set", file=sys.stderr)
        return None, None, None

    # No API keys available or provider not configured
    logger.warning(f"No LLM API keys available (provider: {provider})")
    if provider == "auto":
        print("   ❌ No LLM API keys configured", file=sys.stderr)
    return None, None, None


def generate_session_filename(user: str, agent: str = "claude") -> str:
    """Generate a unique session filename."""
    timestamp = int(time.time())
    user_short = user.split()[0].lower() if user else "unknown"
    short_id = uuid.uuid4().hex[:8]
    return f"{timestamp}_{user_short}_{agent}_{short_id}.jsonl"


def extract_codex_rollout_hash(filename: str) -> Optional[str]:
    """
    Extract stable hash from Codex rollout filename.

    Primary Codex rollout format:
        rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl
        Example: rollout-2025-11-16T18-10-42-019a8ddc-b4b3-7942-9a4f-fac74d1580c9.jsonl
                 -> 019a8ddc-b4b3-7942-9a4f-fac74d1580c9

    Legacy format (still supported):
        rollout-<timestamp>-<hash>.jsonl
        Example: rollout-1763315655-abc123def.jsonl -> abc123def

    Args:
        filename: Original Codex rollout filename

    Returns:
        Hash string, or None if parsing fails
    """
    if not filename.startswith("rollout-"):
        return None

    # Normalize filename (strip extension) and remove prefix
    stem = Path(filename).stem
    if stem.startswith("rollout-"):
        stem = stem[len("rollout-"):]

    if not stem:
        return None

    def looks_like_uuid(value: str) -> bool:
        """Return True if value matches canonical UUID format."""
        parts = value.split("-")
        expected_lengths = [8, 4, 4, 4, 12]
        if len(parts) != 5:
            return False
        hex_digits = set("0123456789abcdefABCDEF")
        for part, length in zip(parts, expected_lengths):
            if len(part) != length or not set(part).issubset(hex_digits):
                return False
        return True

    # Newer Codex exports append a full UUID after the human-readable timestamp.
    uuid_candidate_parts = stem.rsplit("-", 5)
    if len(uuid_candidate_parts) == 6:
        candidate_uuid = "-".join(uuid_candidate_parts[1:])
        if looks_like_uuid(candidate_uuid):
            return candidate_uuid.lower()

    # Fallback for legacy rollout names: everything after first '-' is the hash.
    legacy_parts = stem.split("-", 1)
    if len(legacy_parts) == 2 and legacy_parts[1]:
        return legacy_parts[1]

    return None


def get_git_user() -> str:
    """Get git user name."""
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return os.getenv("USER", "unknown")


def get_username(session_relpath: str = "") -> str:
    """
    Get username for commit message.

    Tries to get from git config first, then falls back to extracting
    from session filename.

    Args:
        session_relpath: Relative path to session file (used for fallback)

    Returns:
        Username string
    """
    # Try git config first
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=True,
        )
        username = result.stdout.strip()
        if username:
            return username
    except subprocess.CalledProcessError:
        pass

    # Fallback: extract from session filename
    # Format: username_agent_hash.jsonl
    if session_relpath:
        filename = Path(session_relpath).name
        parts = filename.split("_")
        if len(parts) >= 3:
            # First part is username
            return parts[0]

    # Final fallback
    return os.getenv("USER", "unknown")


def copy_session_to_repo(
    session_file: Path,
    repo_root: Path,
    user: str,
    config: Optional[ReAlignConfig] = None
) -> Tuple[Path, str, bool, int]:
    """
    Copy session file to repository sessions/ directory (in ~/.aline/{project_name}/).
    Optionally redacts sensitive information if configured.
    If the source filename is in UUID format, renames it to include username for better identification.
    Returns (absolute_path, relative_path, was_redacted, content_size).
    """
    logger.info(f"Copying session to repo: {session_file.name}")
    logger.debug(f"Source: {session_file}, Repo root: {repo_root}, User: {user}")

    from realign import get_realign_dir
    realign_dir = get_realign_dir(repo_root)
    sessions_dir = realign_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    original_filename = session_file.name

    # Check if filename is in UUID format (no underscores, only hyphens and hex chars)
    # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jsonl
    stem = session_file.stem  # filename without extension
    is_uuid_format = (
        '-' in stem and
        '_' not in stem and
        len(stem) == 36  # UUID is 36 chars including hyphens
    )
    # Codex rollout exports always start with rollout-<timestamp>-
    is_codex_rollout = original_filename.startswith("rollout-")

    # Read session content first to detect agent type
    try:
        with open(session_file, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Session file read: {len(content)} bytes")
    except Exception as e:
        logger.error(f"Failed to read session file: {e}", exc_info=True)
        print(f"Warning: Could not read session file: {e}", file=sys.stderr)
        # Fallback to simple copy with unknown agent
        if is_uuid_format:
            short_id = stem.split('-')[0]
            user_short = user.split()[0].lower() if user else "unknown"
            new_filename = f"{user_short}_unknown_{short_id}.jsonl"
            dest_path = sessions_dir / new_filename
        elif is_codex_rollout:
            # Extract stable hash from rollout filename
            rollout_hash = extract_codex_rollout_hash(original_filename)
            user_short = user.split()[0].lower() if user else "unknown"
            if rollout_hash:
                new_filename = f"{user_short}_codex_{rollout_hash}.jsonl"
            else:
                # Fallback if hash extraction fails
                new_filename = generate_session_filename(user, "codex")
            dest_path = sessions_dir / new_filename
        else:
            dest_path = sessions_dir / original_filename
        temp_path = dest_path.with_suffix(".tmp")
        shutil.copy2(session_file, temp_path)
        temp_path.rename(dest_path)
        rel_path = dest_path.relative_to(repo_root)
        logger.warning(f"Copied session with fallback (no agent detection): {rel_path}")
        # Get file size for the fallback case
        try:
            fallback_size = dest_path.stat().st_size
        except Exception:
            fallback_size = 0
        return dest_path, str(rel_path), False, fallback_size

    # Detect agent type from session content
    agent_type = "unknown"
    try:
        import json
        for line in content.split('\n')[:10]:  # Check first 10 lines
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                # Claude Code format
                if data.get("type") in ("user", "assistant"):
                    agent_type = "claude"
                    break
                # Codex format
                elif data.get("type") == "response_item":
                    agent_type = "codex"
                    break
                elif data.get("type") == "session_meta":
                    payload = data.get("payload", {})
                    if "codex" in payload.get("originator", "").lower():
                        agent_type = "codex"
                        break
            except json.JSONDecodeError:
                continue
        logger.debug(f"Detected agent type: {agent_type}")
    except Exception as e:
        logger.warning(f"Agent type detection failed: {e}")

    # If it's UUID format, rename to include username and agent type
    if is_uuid_format:
        # Extract short ID from UUID (first 8 chars)
        short_id = stem.split('-')[0]
        user_short = user.split()[0].lower() if user else "unknown"
        # Format: username_agent_shortid.jsonl (no timestamp for consistency)
        new_filename = f"{user_short}_{agent_type}_{short_id}.jsonl"
        dest_path = sessions_dir / new_filename
    elif is_codex_rollout:
        # Extract stable hash from rollout filename
        codex_agent = agent_type if agent_type != "unknown" else "codex"
        rollout_hash = extract_codex_rollout_hash(original_filename)
        user_short = user.split()[0].lower() if user else "unknown"
        if rollout_hash:
            # Format: username_codex_hash.jsonl (stable naming)
            new_filename = f"{user_short}_{codex_agent}_{rollout_hash}.jsonl"
        else:
            # Fallback if hash extraction fails
            new_filename = generate_session_filename(user, codex_agent)
        dest_path = sessions_dir / new_filename
    else:
        # Keep original filename (could be timestamp_user_agent_id format or other)
        dest_path = sessions_dir / original_filename

    # Check if redaction is enabled
    was_redacted = False
    if config and config.redact_on_match and REDACTOR_AVAILABLE:
        logger.info("Redaction enabled, checking for secrets")
        # Backup original before redaction
        backup_path = save_original_session(dest_path, repo_root)
        if backup_path:
            logger.info(f"Original session backed up to: {backup_path}")
            print(f"   💾 Original session backed up to: {backup_path.relative_to(repo_root)}", file=sys.stderr)

        # Perform redaction
        redacted_content, has_secrets, secrets = check_and_redact_session(
            content,
            redact_mode="auto"
        )

        if has_secrets:
            logger.warning(f"Secrets detected and redacted: {len(secrets)} secret(s)")
            content = redacted_content
            was_redacted = True
        else:
            logger.info("No secrets detected")
    elif config and config.redact_on_match and not REDACTOR_AVAILABLE:
        logger.warning("Redaction enabled but detect-secrets not installed")
        print("⚠️  Redaction enabled but detect-secrets not installed", file=sys.stderr)
        print("   Install with: pip install 'realign-git[redact]'", file=sys.stderr)

    # Write content to destination (redacted or original)
    temp_path = dest_path.with_suffix(".tmp")
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        temp_path.rename(dest_path)
        logger.info(f"Session written to: {dest_path.relative_to(repo_root)}")
    except Exception as e:
        logger.error(f"Failed to write session file: {e}", exc_info=True)
        print(f"Warning: Could not write session file: {e}", file=sys.stderr)
        # Fallback to simple copy
        if temp_path.exists():
            temp_path.unlink()
        shutil.copy2(session_file, dest_path)
        logger.warning("Fallback to simple copy")

    # Return both absolute and relative paths, plus redaction status and content size
    rel_path = dest_path.relative_to(repo_root)
    content_size = len(content)
    return dest_path, str(rel_path), was_redacted, content_size


def save_session_metadata(repo_root: Path, session_relpath: str, content_size: int):
    """
    Save metadata about a processed session to avoid reprocessing.

    Args:
        repo_root: Path to repository root
        session_relpath: Relative path to session file
        content_size: Size of session content when processed
    """
    from realign import get_realign_dir
    realign_dir = get_realign_dir(repo_root)
    metadata_dir = realign_dir / ".metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Use session filename as metadata key
    session_name = Path(session_relpath).name
    metadata_file = metadata_dir / f"{session_name}.meta"

    metadata = {
        "processed_at": time.time(),
        "content_size": content_size,
        "session_relpath": session_relpath,
    }

    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)
        logger.debug(f"Saved metadata for {session_relpath}: {content_size} bytes")
    except Exception as e:
        logger.warning(f"Failed to save metadata for {session_relpath}: {e}")


def get_session_metadata(repo_root: Path, session_relpath: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata about a previously processed session.

    Args:
        repo_root: Path to repository root
        session_relpath: Relative path to session file

    Returns:
        Metadata dictionary or None if not found
    """
    from realign import get_realign_dir
    realign_dir = get_realign_dir(repo_root)
    metadata_dir = realign_dir / ".metadata"
    session_name = Path(session_relpath).name
    metadata_file = metadata_dir / f"{session_name}.meta"

    if not metadata_file.exists():
        return None

    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        logger.debug(f"Loaded metadata for {session_relpath}: {metadata.get('content_size')} bytes")
        return metadata
    except Exception as e:
        logger.warning(f"Failed to load metadata for {session_relpath}: {e}")
        return None


