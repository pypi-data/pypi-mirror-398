"""ReAlign mirror command - Mirror project files to shadow git repository."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..tracker.git_tracker import ReAlignGitTracker
from ..mirror_utils import collect_project_files
from realign import get_realign_dir

console = Console()


def mirror_project(
    project_path: Optional[Path] = None,
    verbose: bool = False
) -> bool:
    """
    Mirror all project files to the shadow git repository.

    Args:
        project_path: Path to project directory (defaults to current directory)
        verbose: Print detailed progress information

    Returns:
        True if successful, False otherwise
    """
    # Use current directory if not specified
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path).resolve()

    # Check if project exists
    if not project_path.exists():
        console.print(f"[red]Error: Project directory does not exist: {project_path}[/red]")
        return False

    # Check if ReAlign is initialized
    realign_dir = get_realign_dir(project_path)
    if not realign_dir.exists():
        console.print(f"[red]Error: ReAlign not initialized in {project_path}[/red]")
        console.print(f"[dim]Run 'realign init' first[/dim]")
        return False

    try:
        # Initialize git tracker
        tracker = ReAlignGitTracker(project_path)
        if not tracker.is_initialized():
            console.print("[yellow]Shadow git not initialized, initializing now...[/yellow]")
            if not tracker.init_repo():
                console.print("[red]Failed to initialize shadow git[/red]")
                return False

        # Collect all project files
        if verbose:
            console.print(f"[dim]Scanning project files in {project_path}...[/dim]")

        all_files = collect_project_files(project_path)

        if not all_files:
            console.print("[yellow]No files to mirror[/yellow]")
            return True

        # Mirror files with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Mirroring {len(all_files)} file(s)...",
                total=None
            )

            mirrored_files = tracker.mirror_files(all_files)
            progress.update(task, completed=True)

        # Report results
        if mirrored_files:
            console.print(f"[green]✓ Mirrored {len(mirrored_files)} file(s) to {realign_dir / 'mirror'}[/green]")
            if verbose:
                console.print("\n[bold]Mirrored files:[/bold]")
                for file_path in mirrored_files[:10]:  # Show first 10
                    rel_path = file_path.relative_to(realign_dir / "mirror")
                    console.print(f"  • {rel_path}")
                if len(mirrored_files) > 10:
                    console.print(f"  ... and {len(mirrored_files) - 10} more")
        else:
            console.print("[dim]No files needed to be copied (all up to date)[/dim]")

        return True

    except Exception as e:
        console.print(f"[red]Error mirroring project: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def mirror_command(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress"),
    path: Optional[str] = typer.Argument(None, help="Project path (defaults to current directory)"),
):
    """Mirror all project files to the shadow git repository.

    This command copies all project files (respecting .gitignore) to the
    ~/.aline/{project_name}/mirror/ directory in the shadow git repository.

    The mirror is automatically updated when watcher detects session changes,
    but this command can be used to manually sync files at any time.
    """
    project_path = Path(path) if path else None

    if verbose:
        if project_path:
            console.print(f"[bold blue]Mirroring project: {project_path}[/bold blue]\n")
        else:
            console.print(f"[bold blue]Mirroring project: {Path.cwd()}[/bold blue]\n")

    success = mirror_project(project_path=project_path, verbose=verbose)

    if not success:
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(mirror_command)
