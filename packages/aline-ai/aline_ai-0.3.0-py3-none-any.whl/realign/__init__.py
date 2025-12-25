"""Aline - AI Agent Chat Session Tracker."""

from pathlib import Path

__version__ = "0.3.0"


def get_realign_dir(project_root: Path) -> Path:
    """
    Get the ReAlign directory path for a project.

    The directory is located at ~/.aline/{project_name}/ instead of
    in the project directory itself.

    First checks for .realign-config file in project root,
    otherwise uses default location.

    Args:
        project_root: Root directory of the project

    Returns:
        Path to the ReAlign directory for this project
    """
    project_root = Path(project_root).resolve()
    config_marker = project_root / ".realign-config"

    if config_marker.exists():
        # Read the configured path
        configured_path = config_marker.read_text(encoding="utf-8").strip()
        return Path(configured_path)
    else:
        # Use default location
        project_name = project_root.name
        return Path.home() / ".aline" / project_name
