#!/usr/bin/env python3
"""Clean up temporary and test project directories from ~/.aline."""

import shutil
from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

from ..logging_config import setup_logger

logger = setup_logger('realign.clean', 'clean.log')
console = Console()


def find_temp_projects() -> List[Path]:
    """
    Find all temporary/test project directories in ~/.aline.

    Returns:
        List of paths to temporary project directories
    """
    aline_dir = Path.home() / '.aline'
    if not aline_dir.exists():
        return []

    temp_projects = []
    try:
        for project_dir in aline_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Skip system directories
            if project_dir.name in ['.logs', '.cache']:
                continue

            # Identify temporary/test directories
            if project_dir.name.startswith(('tmp', 'test_')):
                temp_projects.append(project_dir)

    except Exception as e:
        logger.error(f"Failed to scan for temporary projects: {e}")
        console.print(f"[red]Error: {e}[/red]")

    return temp_projects


def clean_command(force: bool = False, dry_run: bool = False) -> int:
    """
    Clean up temporary and test project directories.

    Args:
        force: Skip confirmation prompt
        dry_run: Show what would be deleted without actually deleting

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        console.print("\n[bold cyan]ReAlign Cleanup[/bold cyan]")

        # Find temporary projects
        temp_projects = find_temp_projects()

        if not temp_projects:
            console.print("[green]✓ No temporary projects found[/green]")
            console.print("[dim]All clean![/dim]\n")
            return 0

        # Display what will be cleaned
        console.print(f"\n[yellow]Found {len(temp_projects)} temporary project(s):[/yellow]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Project", style="cyan")
        table.add_column("Size", justify="right", style="dim")

        total_size = 0
        for project in temp_projects:
            # Calculate directory size
            try:
                size = sum(f.stat().st_size for f in project.rglob('*') if f.is_file())
                total_size += size

                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"

                table.add_row(project.name, size_str)
            except Exception as e:
                logger.warning(f"Failed to calculate size for {project.name}: {e}")
                table.add_row(project.name, "N/A")

        console.print(table)

        # Display total size
        if total_size < 1024 * 1024:
            total_str = f"{total_size / 1024:.1f}KB"
        else:
            total_str = f"{total_size / (1024 * 1024):.1f}MB"

        console.print(f"\n[bold]Total size: {total_str}[/bold]")

        # Dry run mode - just show what would be deleted
        if dry_run:
            console.print("\n[dim]Dry run mode - no files were deleted[/dim]")
            console.print("[dim]Run without --dry-run to actually delete these directories[/dim]\n")
            return 0

        # Confirmation prompt (unless force flag is set)
        if not force:
            console.print(f"\n[yellow]⚠ This will permanently delete {len(temp_projects)} directory(ies)[/yellow]")

            from rich.prompt import Confirm
            if not Confirm.ask("Continue?", default=False):
                console.print("[dim]Cleanup cancelled[/dim]\n")
                return 0

        # Delete temporary projects
        console.print("")
        deleted_count = 0
        failed_count = 0

        for project in temp_projects:
            try:
                shutil.rmtree(project)
                console.print(f"[green]✓[/green] Deleted {project.name}")
                deleted_count += 1
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to delete {project.name}: {e}")
                logger.error(f"Failed to delete {project}: {e}")
                failed_count += 1

        # Summary
        console.print(f"\n[green]✓ Cleanup complete[/green]")
        console.print(f"  Deleted: {deleted_count}")
        if failed_count > 0:
            console.print(f"  [red]Failed: {failed_count}[/red]")
        console.print(f"  Freed: {total_str}\n")

        return 0 if failed_count == 0 else 1

    except Exception as e:
        logger.error(f"Error in clean command: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
        return 1
