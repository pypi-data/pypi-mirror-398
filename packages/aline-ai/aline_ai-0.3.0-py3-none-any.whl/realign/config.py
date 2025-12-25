"""Configuration management for ReAlign."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ReAlignConfig:
    """ReAlign configuration."""

    local_history_path: str = "~/.local/share/realign/histories"
    summary_max_chars: int = 500
    redact_on_match: bool = False    # Default: disable redaction (can be enabled in config)
    hooks_installation: str = "repo"
    use_LLM: bool = True
    llm_provider: str = "auto"       # LLM provider: "auto", "claude", or "openai"
    auto_detect_claude: bool = True  # Enable Claude Code session auto-detection
    auto_detect_codex: bool = True   # Enable Codex session auto-detection
    mcp_auto_commit: bool = True     # Enable MCP watcher auto-commit after each user request completes
    use_mcp_sampling: bool = True    # Use MCP Sampling API for LLM summaries (requires MCP mode)
    share_backend_url: str = "https://realign-server.vercel.app"  # Backend URL for interactive share export

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "ReAlignConfig":
        """Load configuration from file with environment variable overrides."""
        if config_path is None:
            config_path = Path.home() / ".config" / "aline" / "config.yaml"

        config_dict = {}

        # Load from file if exists
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f) or {}

        # Apply environment variable overrides
        env_overrides = {
            "local_history_path": os.getenv("REALIGN_LOCAL_HISTORY_PATH"),
            "summary_max_chars": os.getenv("REALIGN_SUMMARY_MAX_CHARS"),
            "redact_on_match": os.getenv("REALIGN_REDACT_ON_MATCH"),
            "hooks_installation": os.getenv("REALIGN_HOOKS_INSTALLATION"),
            "use_LLM": os.getenv("REALIGN_USE_LLM"),
            "llm_provider": os.getenv("REALIGN_LLM_PROVIDER"),
            "auto_detect_claude": os.getenv("REALIGN_AUTO_DETECT_CLAUDE"),
            "auto_detect_codex": os.getenv("REALIGN_AUTO_DETECT_CODEX"),
            "mcp_auto_commit": os.getenv("REALIGN_MCP_AUTO_COMMIT"),
            "use_mcp_sampling": os.getenv("REALIGN_USE_MCP_SAMPLING"),
            "share_backend_url": os.getenv("REALIGN_SHARE_BACKEND_URL"),
        }

        for key, value in env_overrides.items():
            if value is not None:
                if key == "summary_max_chars":
                    config_dict[key] = int(value)
                elif key in ["redact_on_match", "use_LLM", "auto_detect_claude", "auto_detect_codex", "mcp_auto_commit", "use_mcp_sampling"]:
                    config_dict[key] = value.lower() in ("true", "1", "yes")
                else:
                    config_dict[key] = value

        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})

    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.home() / ".config" / "aline" / "config.yaml"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = {
            "local_history_path": self.local_history_path,
            "summary_max_chars": self.summary_max_chars,
            "redact_on_match": self.redact_on_match,
            "hooks_installation": self.hooks_installation,
            "use_LLM": self.use_LLM,
            "llm_provider": self.llm_provider,
            "auto_detect_claude": self.auto_detect_claude,
            "auto_detect_codex": self.auto_detect_codex,
            "mcp_auto_commit": self.mcp_auto_commit,
            "use_mcp_sampling": self.use_mcp_sampling,
            "share_backend_url": self.share_backend_url,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

    @property
    def expanded_local_history_path(self) -> Path:
        """Get the expanded local history path."""
        return Path(os.path.expanduser(self.local_history_path))

    def get_effective_history_path(self, project_path: Optional[Path] = None) -> Path:
        """
        Get the effective history path with Codex and Claude Code auto-detection.

        DEPRECATED: This method returns only ONE path for backward compatibility.
        For multi-agent support, use find_all_active_sessions() instead.

        Priority:
        1. REALIGN_LOCAL_HISTORY_PATH environment variable (disables auto-detection)
        2. Codex session file (if auto_detect_codex is True and exists)
        3. Claude Code sessions directory (if auto_detect_claude is True and exists)
        4. Configured local_history_path

        Args:
            project_path: Optional path to the current project (git repo root)

        Returns:
            The effective path to use for session history
        """
        # Environment variable has highest priority (disables auto-detection)
        if os.getenv("REALIGN_LOCAL_HISTORY_PATH"):
            return Path(os.path.expanduser(self.local_history_path))

        # Try Codex auto-detection first if enabled
        if self.auto_detect_codex and project_path:
            from realign.codex_detector import get_latest_codex_session
            codex_session = get_latest_codex_session(project_path)
            if codex_session:
                return codex_session

        # Try Claude auto-detection if enabled
        if self.auto_detect_claude and project_path:
            from realign.claude_detector import auto_detect_sessions_path
            claude_path = auto_detect_sessions_path(project_path, self.local_history_path)
            if claude_path != self.expanded_local_history_path:
                return claude_path

        return self.expanded_local_history_path


def get_default_config_content() -> str:
    """Get default configuration file content."""
    return """# ReAlign Global Configuration (User Home Directory)
local_history_path: "~/.local/share/realign/histories"   # Directory for local agent session files
summary_max_chars: 500           # Maximum length of commit message summaries
redact_on_match: false           # Automatically redact sensitive information (disabled by default)
                                 # Original sessions are backed up to .realign/sessions-original/
                                 # Set to true to enable if you plan to share sessions publicly
hooks_installation: "repo"       # Repo mode: sets core.hooksPath=.realign/hooks
use_LLM: true                    # Whether to use a cloud LLM to generate summaries
llm_provider: "auto"             # LLM provider: "auto" (try Claude then OpenAI), "claude", or "openai"
auto_detect_claude: true         # Automatically detect Claude Code session directory (~/.claude/projects/)
auto_detect_codex: true          # Automatically detect Codex session files (~/.codex/sessions/)
mcp_auto_commit: true            # Enable MCP watcher to auto-commit after each user request completes
use_mcp_sampling: true           # Use MCP Sampling API when available (Claude Code)
                                 # Falls back to direct API if unavailable or denied
share_backend_url: "https://realign-server.vercel.app"  # Backend URL for interactive share export
                                 # For local development, use: "http://localhost:3000"

# LLM API Keys (environment variable configuration):
# export ANTHROPIC_API_KEY="your-anthropic-api-key"  # For Claude (Anthropic)
# export OPENAI_API_KEY="your-openai-api-key"        # For OpenAI (GPT)
# When use_mcp_sampling=true: tries MCP Sampling first (no API key needed)
# Falls back to direct API when not in Claude Code or user denies approval

# Secret Detection & Redaction:
# ReAlign can use detect-secrets to automatically scan for and redact:
# - API keys, tokens, passwords
# - Private keys, certificates
# - AWS credentials, database URLs
# Note: High-entropy strings (like Base64) are filtered out to reduce false positives
# To enable redaction: realign config set redact_on_match true
"""
