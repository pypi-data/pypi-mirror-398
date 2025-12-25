#!/usr/bin/env python3
"""ReAlign CLI - Main command-line interface."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax

from .commands import init, config, review, hide, status, watcher, push, pull, share, sync, mirror, clean, import_history, undo, export_shares

app = typer.Typer(
    name="realign",
    help="Track and version AI agent chat sessions with git commits",
    add_completion=False,
)
console = Console()

# Register commands
app.command(name="init")(init.init_command)
app.command(name="config")(config.config_command)


@app.command(name="import-history")
def import_history_cli(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full user messages instead of previews"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Maximum number of turns to process"),
    commit: bool = typer.Option(False, "--commit", help="Actually commit turns to git"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM summary generation (use simple commit messages)"),
):
    """Discover and display (or commit) historical sessions for import. By default, --commit uses LLM to generate summaries."""
    exit_code = import_history.import_history_command(
        verbose=verbose,
        limit=limit,
        commit=commit,
        no_llm=no_llm
    )
    raise typer.Exit(code=exit_code)


@app.command(name="review")
def review_cli(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
    detect_secrets: bool = typer.Option(False, "--detect-secrets", help="Detect sensitive content"),
):
    """Review unpushed commits with session summaries."""
    exit_code = review.review_command(verbose=verbose, detect_secrets=detect_secrets)
    raise typer.Exit(code=exit_code)


@app.command(name="hide")
def hide_cli(
    indices: str = typer.Argument(..., help="Commit indices to hide (e.g., '1,3,5-7' or '--all'), or 'reset' to undo last hide"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Hide (redact) specific commits before pushing, or reset to undo last hide."""
    if indices.lower() == "reset":
        exit_code = hide.hide_reset_command(force=force)
    else:
        exit_code = hide.hide_command(indices=indices, force=force)
    raise typer.Exit(code=exit_code)


@app.command(name="status")
def status_cli(
    watch: bool = typer.Option(False, "--watch", "-w", help="Continuously monitor status"),
):
    """Display ReAlign system status and activity."""
    exit_code = status.status_command(watch=watch)
    raise typer.Exit(code=exit_code)


# Create watcher subcommand group
watcher_app = typer.Typer(help="Manage MCP watcher process")
app.add_typer(watcher_app, name="watcher")


@watcher_app.command(name="status")
def watcher_status_cli(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed session tracking information"),
):
    """Display MCP watcher status."""
    exit_code = watcher.watcher_status_command(verbose=verbose)
    raise typer.Exit(code=exit_code)


@watcher_app.command(name="start")
def watcher_start_cli():
    """Start the MCP watcher process."""
    exit_code = watcher.watcher_start_command()
    raise typer.Exit(code=exit_code)


@watcher_app.command(name="stop")
def watcher_stop_cli():
    """Stop the MCP watcher process."""
    exit_code = watcher.watcher_stop_command()
    raise typer.Exit(code=exit_code)


# Push/Pull commands
@app.command(name="push")
def push_cli(
    force: bool = typer.Option(False, "--force", "-f", help="Force push (use with caution)"),
):
    """Push session commits to remote repository."""
    exit_code = push.push_command(force=force)
    raise typer.Exit(code=exit_code)


@app.command(name="pull")
def pull_cli():
    """Pull session updates from remote repository."""
    exit_code = pull.pull_command()
    raise typer.Exit(code=exit_code)


@app.command(name="sync")
def sync_cli():
    """Synchronize with remote (pull + push)."""
    exit_code = sync.sync_command()
    raise typer.Exit(code=exit_code)


# Share command group
share_app = typer.Typer(help="Manage session sharing and collaboration")
app.add_typer(share_app, name="share")


@share_app.command(name="configure")
def share_configure_cli(
    remote: str = typer.Argument(..., help="Remote repository (e.g., user/repo or full URL)"),
    token: Optional[str] = typer.Option(None, "--token", help="GitHub access token"),
):
    """Manually configure remote repository for sharing."""
    exit_code = share.share_configure_command(remote=remote, token=token)
    raise typer.Exit(code=exit_code)


@share_app.command(name="status")
def share_status_cli():
    """Show current sharing configuration."""
    exit_code = share.share_status_command()
    raise typer.Exit(code=exit_code)


@share_app.command(name="invite")
def share_invite_cli(
    email: Optional[str] = typer.Argument(None, help="Email address to invite"),
):
    """Invite collaborator to shared repository."""
    exit_code = share.share_invite_command(email=email)
    raise typer.Exit(code=exit_code)


@share_app.command(name="link")
def share_link_cli():
    """Get shareable link for teammates to join."""
    exit_code = share.share_link_command()
    raise typer.Exit(code=exit_code)


@share_app.command(name="disable")
def share_disable_cli():
    """Disable sharing (keeps history intact)."""
    exit_code = share.share_disable_command()
    raise typer.Exit(code=exit_code)


@share_app.command(name="export")
def share_export_cli(
    indices: Optional[str] = typer.Option(None, "--indices", "-i", help="Commit indices to export (e.g., '1,3,5-7' or 'all')"),
    local: bool = typer.Option(False, "--local", help="Export to local JSON only (skip interactive web upload)"),
    interactive: bool = typer.Option(False, "--interactive", help="[DEPRECATED] Interactive mode is now default"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Username for local export file"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory for local export"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password for encrypted share (auto-generated if not provided)"),
    expiry_days: int = typer.Option(7, "--expiry", help="Number of days before share expires"),
    max_views: int = typer.Option(100, "--max-views", help="Maximum number of views allowed"),
    no_preview: bool = typer.Option(False, "--no-preview", help="Skip UI preview and editing (auto-accept LLM-generated content)"),
    preset: Optional[str] = typer.Option(None, "--preset", help="Prompt preset ID (default, work-report, knowledge-agent, personality-analyzer)"),
    mcp: bool = typer.Option(True, "--mcp/--no-mcp", help="Include MCP usage instructions for agent-to-agent communication (default: enabled)"),
):
    """
    Export chat history as encrypted shareable link (default) or local JSON.

    Interactive mode (default): Creates encrypted web-accessible chatbot
    Local mode (--local): Exports to JSON file only
    """
    # Deprecation warning
    if interactive:
        print("⚠️  Warning: --interactive flag is deprecated.")
        print("   Interactive mode is now default. Use --local for JSON export.\n")

    # Determine mode (backward compatible)
    use_local_mode = local or username or output_dir

    if use_local_mode:
        # Local JSON export
        output_path = Path(output_dir) if output_dir else None
        exit_code = export_shares.export_shares_command(
            indices=indices,
            username=username,
            output_dir=output_path
        )
    else:
        # Interactive web export (DEFAULT)
        exit_code = export_shares.export_shares_interactive_command(
            indices=indices,
            password=password,
            expiry_days=expiry_days,
            max_views=max_views,
            enable_preview=not no_preview,
            preset=preset,
            enable_mcp=mcp
        )
    raise typer.Exit(code=exit_code)


@app.command(name="mirror")
def mirror_cli(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
    path: Optional[str] = typer.Argument(None, help="Project path (defaults to current directory)"),
):
    """Mirror all project files to the shadow git repository."""
    mirror.mirror_command(verbose=verbose, path=path)


@app.command(name="clean")
def clean_cli(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without deleting"),
):
    """Clean up temporary and test project directories."""
    exit_code = clean.clean_command(force=force, dry_run=dry_run)
    raise typer.Exit(code=exit_code)


@app.command(name="undo")
def undo_cli(
    commit_hash: str = typer.Argument(..., help="Commit hash to undo to"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without executing"),
    no_backup: bool = typer.Option(False, "--no-backup", help="Skip backup creation"),
    delete: str = typer.Option("keep", "--delete", help="Handle extra files: keep|delete|backup"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
):
    """Undo project and session state to a specific commit."""
    exit_code = undo.undo_command(
        commit_hash=commit_hash,
        dry_run=dry_run,
        no_backup=no_backup,
        deletion_strategy=delete,
        force=force
    )
    raise typer.Exit(code=exit_code)


@app.command()
def version():
    """Show ReAlign version."""
    from . import __version__
    console.print(f"ReAlign version {__version__}")


if __name__ == "__main__":
    app()
