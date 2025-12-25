"""Git-based tracking system for AI work history.

This module implements Plan A: an independent Git repository in .realign/
that mirrors project file structure and tracks AI work history using standard Git.
"""

from .git_tracker import ReAlignGitTracker

__all__ = ["ReAlignGitTracker"]
