"""Aline init command - Initialize Aline tracking system."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any
import typer
from rich.console import Console

from ..config import ReAlignConfig, get_default_config_content
from realign import get_realign_dir

console = Console()


def init_repository(
    repo_path: str = ".",
    force: bool = False,
) -> Dict[str, Any]:
    """
    Core initialization logic (non-interactive).

    Args:
        repo_path: Path to the repository to initialize
        force: Force re-initialization even if .aline already exists

    Returns:
        Dictionary with initialization results and metadata
    """
    result = {
        "success": False,
        "repo_path": None,
        "repo_root": None,
        "realign_dir": None,
        "config_path": None,
        "history_dir": None,
        "realign_git_initialized": False,
        "message": "",
        "errors": [],
    }

    # Change to target directory
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)
        result["repo_path"] = os.getcwd()
    except Exception as e:
        result["errors"].append(f"Failed to change to directory {repo_path}: {e}")
        result["message"] = "Failed to access target directory"
        return result

    try:
        # Use current directory as repo_root (no git dependency)
        repo_root = Path(os.getcwd()).resolve()
        result["repo_root"] = str(repo_root)

        # Create directory structure in ~/.aline/{project_name}/
        realign_dir = get_realign_dir(repo_root)
        sessions_dir = realign_dir / "sessions"
        result["realign_dir"] = str(realign_dir)

        # Check if already initialized (unless --force)
        if realign_dir.exists() and not force:
            result["errors"].append("Aline already initialized in this project")
            result["message"] = "Already initialized. Use --force to reinitialize."
            return result

        # If force and exists, remove existing directory
        if force and realign_dir.exists():
            import shutil
            console.print(f"[yellow]Removing existing Aline directory: {realign_dir}[/yellow]")
            shutil.rmtree(realign_dir)
            result["message"] = "Re-initialized existing Aline directory"

        # Create directories (no hooks needed)
        for directory in [realign_dir, sessions_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Create .gitignore for sessions and metadata
        gitignore_path = realign_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_content = (
                "# Ignore metadata files (used internally to prevent duplicate processing)\n"
                ".metadata/\n\n"
                "# Ignore original sessions (contains potential secrets before redaction)\n"
                "sessions-original/\n"
            )
            gitignore_path.write_text(gitignore_content, encoding="utf-8")

        # Initialize .aline/.git if it doesn't exist
        # NOTE: We only create the git repo here, the initial commit happens after mirroring
        realign_git = realign_dir / ".git"
        if not realign_git.exists():
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=realign_dir,
                    check=True,
                    capture_output=True
                )
                result["realign_git_initialized"] = True
            except subprocess.CalledProcessError as e:
                result["errors"].append(f"Failed to initialize .aline/.git: {e}")
                # Continue anyway, this is not critical for basic functionality

        # Initialize global config if not exists
        global_config_path = Path.home() / ".config" / "aline" / "config.yaml"
        if not global_config_path.exists():
            global_config_path.parent.mkdir(parents=True, exist_ok=True)
            global_config_path.write_text(get_default_config_content(), encoding="utf-8")
        result["config_path"] = str(global_config_path)

        # Create local history directory
        config = ReAlignConfig.load()
        history_dir = config.expanded_local_history_path
        history_dir.mkdir(parents=True, exist_ok=True)
        result["history_dir"] = str(history_dir)

        # Create a .aline-config file in project root to store realign_dir location
        config_marker = repo_root / ".aline-config"
        config_marker.write_text(str(realign_dir), encoding="utf-8")

        # Update project .gitignore to ignore .aline-config
        project_gitignore = repo_root / ".gitignore"
        if project_gitignore.exists():
            gitignore_content = project_gitignore.read_text(encoding="utf-8")
            if ".aline-config" not in gitignore_content:
                # Add .aline-config to .gitignore
                if not gitignore_content.endswith('\n'):
                    gitignore_content += '\n'
                gitignore_content += '\n# Aline config file\n.aline-config\n'
                project_gitignore.write_text(gitignore_content, encoding="utf-8")
        else:
            # Create new .gitignore with .aline-config
            project_gitignore.write_text('# Aline config file\n.aline-config\n', encoding="utf-8")

        result["success"] = True
        result["message"] = "Aline initialized successfully"

    except Exception as e:
        result["errors"].append(f"Initialization failed: {e}")
        result["message"] = f"Failed to initialize: {e}"
    finally:
        # Restore original directory
        os.chdir(original_dir)

    return result


def init_command(
    force: bool = typer.Option(False, "--force", "-f", help="Force re-initialization even if .aline exists"),
):
    """Initialize Aline tracking system in the current directory.

    Creates .aline directory structure and initializes the shadow git repository.
    Works with or without an existing git repository in the project.
    """
    # Standard initialization
    # Call the core function
    result = init_repository(
        repo_path=".",
        force=force,
    )

    # Print detailed results
    console.print("\n[bold blue]═══ Aline Initialization ═══[/bold blue]\n")

    if result["success"]:
        console.print("[bold green]✓ Status: SUCCESS[/bold green]\n")
    else:
        console.print("[bold red]✗ Status: FAILED[/bold red]\n")

    # Print all parameters and results
    console.print("[bold]Configuration:[/bold]")
    console.print(f"  Project Root: [cyan]{result.get('repo_root', 'N/A')}[/cyan]")
    console.print(f"  Aline Directory: [cyan]{result.get('realign_dir', 'N/A')}[/cyan]")
    console.print(f"  Global Config: [cyan]{result.get('config_path', 'N/A')}[/cyan]")
    console.print(f"  History Directory: [cyan]{result.get('history_dir', 'N/A')}[/cyan]")
    console.print(f"  Shadow Git Initialized: [cyan]{result.get('realign_git_initialized', False)}[/cyan]")

    if result.get("errors"):
        console.print("\n[bold red]Errors:[/bold red]")
        for error in result["errors"]:
            console.print(f"  • {error}", style="red")

    console.print(f"\n[bold]Result:[/bold] {result['message']}\n")

    if result["success"]:
        # Mirror project files after successful initialization
        console.print("[bold]Mirroring project files...[/bold]")
        from .mirror import mirror_project
        mirror_success = mirror_project(project_path=Path(result["repo_root"]), verbose=False)

        if mirror_success:
            console.print("[green]✓ Project files mirrored successfully[/green]\n")

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
                console.print("[green]✓ Created initial commit in shadow git[/green]\n")
            except subprocess.CalledProcessError as e:
                console.print(f"[yellow]⚠ Warning: Failed to create initial commit: {e}[/yellow]\n")
        else:
            console.print("[yellow]⚠ Warning: Failed to mirror project files[/yellow]")
            console.print("[dim]You can manually run 'aline mirror' later[/dim]\n")

        console.print("[bold]Next steps:[/bold]")
        console.print("  1. Start Claude Code or Codex - the MCP server will auto-start", style="dim")
        console.print("  2. Sessions are automatically tracked to .aline/.git", style="dim")
        console.print("  3. Review commits with: [cyan]aline review[/cyan]", style="dim")
        console.print("  4. Hide sensitive commits with: [cyan]aline hide <indices>[/cyan]", style="dim")
    else:
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(init_command)
