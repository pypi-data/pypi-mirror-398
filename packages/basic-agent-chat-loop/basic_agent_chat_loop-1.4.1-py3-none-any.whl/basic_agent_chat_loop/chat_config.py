#!/usr/bin/env python3
"""
Configuration management for Basic Agent Chat Loop.

Supports hierarchical configuration with the following precedence (highest to lowest):
1. Project-level .chatrc in current directory
2. Global ~/.chatrc
3. Built-in defaults

Configuration file format: YAML
"""

import os
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-untyped]

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ChatConfig:
    """Configuration manager for chat loop."""

    # Default configuration
    DEFAULTS = {
        "colors": {
            "user": "bright_white",
            "agent": "bright_blue",
            "system": "yellow",
            "error": "bright_red",
            "success": "bright_green",
            "dim": "\033[2m",  # Dim (no named equivalent)
            "reset": "\033[0m",  # Reset (no named equivalent)
        },
        "features": {
            "auto_save": True,
            "rich_enabled": True,
            "show_tokens": True,
            "show_metadata": True,
            "readline_enabled": True,
        },
        "paths": {
            "save_location": "~/agent-conversations",
            "log_location": "~/.chat_loop_logs",
        },
        "behavior": {
            "max_retries": 3,
            "retry_delay": 2.0,
            "timeout": 120.0,
            "spinner_style": "dots",
        },
        "ui": {
            "show_banner": True,
            "show_thinking_indicator": True,
            "show_duration": True,
            "show_status_bar": True,
            "update_terminal_title": True,
        },
        "audio": {
            "enabled": True,
            "notification_sound": None,  # Uses bundled notification.wav if None
        },
        "harmony": {
            # Enable harmony processing (auto-detects by default, set to True to force)
            "enabled": None,  # None = auto-detect, True = force enable, False = disable
            # Show reasoning/analysis/commentary channels
            "show_detailed_thinking": True,
        },
        # Per-agent overrides (example structure)
        "agents": {
            # 'Complex Coding Clara': {
            #     'features': {'auto_save': True}
            # }
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional explicit config file path
        """
        self.config = self._load_config(config_path)

    def _load_config(self, explicit_path: Optional[Path] = None) -> dict[str, Any]:
        """
        Load configuration with hierarchical precedence.

        Args:
            explicit_path: Explicit config file path (highest priority)

        Returns:
            Merged configuration dictionary
        """
        # Start with defaults
        config = self._deep_copy(self.DEFAULTS)

        if not YAML_AVAILABLE:
            return config

        config_files = []

        # Build list in order of precedence (lowest to highest)
        # Lower priority configs are loaded first, higher priority override them

        # Global config (lowest priority when explicit or project configs exist)
        global_config = Path.home() / ".chatrc"
        if global_config.exists():
            config_files.append(global_config)

        # Project config (higher priority than global)
        for i in range(4):
            if i == 0:
                project_config = Path.cwd() / ".chatrc"
            else:
                try:
                    project_config = Path.cwd().parents[i - 1] / ".chatrc"
                except IndexError:
                    break

            if project_config.exists():
                config_files.append(project_config)
                break  # Use first found, don't search higher

        # Explicit path (highest priority - loaded last to override others)
        if explicit_path and explicit_path.exists():
            config_files.append(explicit_path)

        # Load and merge configs (each subsequent config overrides previous)
        for config_file in config_files:
            try:
                with open(config_file) as f:
                    user_config = yaml.safe_load(f) or {}
                    config = self._merge_config(config, user_config)
            except Exception:
                # Silently skip invalid configs, use defaults
                pass

        return config

    def _deep_copy(self, d: dict) -> dict:
        """Deep copy a dictionary."""
        import copy

        return copy.deepcopy(d)

    def _merge_config(self, base: dict, override: dict) -> dict:
        """
        Recursively merge override config into base config.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = self._deep_copy(base)

        for key, value in override.items():
            # Skip None values (treat as "not set" rather than explicit None)
            if value is None:
                continue

            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursive merge for nested dicts
                result[key] = self._merge_config(result[key], value)
            else:
                # Direct override
                result[key] = value

        return result

    def get(
        self, key: str, default: Any = None, agent_name: Optional[str] = None
    ) -> Any:
        """
        Get configuration value with optional agent-specific override.

        Args:
            key: Dot-notation config key (e.g., 'features.auto_save')
            default: Default value if key not found
            agent_name: Optional agent name for per-agent overrides

        Returns:
            Configuration value
        """
        # Check agent-specific override first
        agents = self.config.get("agents") or {}
        if agent_name and agent_name in agents:
            agent_config = agents[agent_name]
            agent_value = self._get_nested(agent_config, key)
            if agent_value is not None:
                return agent_value

        # Fall back to global config
        value = self._get_nested(self.config, key)
        return value if value is not None else default

    def _get_nested(self, d: dict, key: str) -> Any:
        """
        Get nested dictionary value using dot notation.

        Args:
            d: Dictionary to search
            key: Dot-notation key (e.g., 'features.auto_save')

        Returns:
            Value or None if not found
        """
        keys = key.split(".")
        current = d

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def get_section(
        self, section: str, agent_name: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get entire configuration section with agent overrides applied.

        Args:
            section: Section name (e.g., 'colors', 'features')
            agent_name: Optional agent name for overrides

        Returns:
            Configuration section dictionary
        """
        base_section = self.config.get(section, {})

        # Apply agent overrides if specified
        agents = self.config.get("agents") or {}
        if agent_name and agent_name in agents:
            agent_config = agents[agent_name]
            if section in agent_config:
                base_section = self._merge_config(base_section, agent_config[section])

        # Special handling for colors section - decode escape sequences
        if section == "colors":
            decoded_colors = {}
            for key, value in base_section.items():
                if isinstance(value, str) and "\\" in value:
                    # Decode YAML-escaped strings (\\033 -> \033)
                    try:
                        decoded_colors[key] = value.encode().decode("unicode_escape")
                    except Exception:
                        decoded_colors[key] = value
                else:
                    decoded_colors[key] = value
            return decoded_colors

        return base_section

    def set(self, key: str, value: Any, agent_name: Optional[str] = None):
        """
        Set configuration value (runtime only, not persisted).

        Args:
            key: Dot-notation config key
            value: Value to set
            agent_name: Optional agent name for per-agent setting
        """
        keys = key.split(".")

        # Determine target dict
        if agent_name:
            agents = self.config.get("agents") or {}
            if "agents" not in self.config:
                self.config["agents"] = {}
            if agent_name not in agents:
                self.config["agents"][agent_name] = {}
            target = self.config["agents"][agent_name]
        else:
            target = self.config

        # Navigate to parent and set value
        for k in keys[:-1]:
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def expand_path(self, path: str) -> Path:
        """
        Expand path with ~ and environment variables.

        Args:
            path: Path string potentially with ~ or $VAR

        Returns:
            Expanded Path object
        """
        return Path(os.path.expanduser(os.path.expandvars(path)))


# Global config instance (lazy loaded)
_global_config: Optional[ChatConfig] = None


def initialize_default_config() -> Path:
    """
    Create default ~/.chatrc configuration file if it doesn't exist.

    Returns:
        Path to the config file
    """
    config_file = Path.home() / ".chatrc"

    if config_file.exists():
        return config_file

    default_config = """# Basic Agent Chat Loop Configuration
#
# This file was automatically created with recommended defaults.
# Edit to customize your experience!
#
# Format: YAML
# Precedence: Project .chatrc > Global ~/.chatrc > Built-in defaults

# ============================================================================
# COLORS - ANSI escape codes for terminal output
# ============================================================================
colors:
  user: '\\033[97m'      # Bright white - maximum contrast
  agent: '\\033[94m'     # Bright blue
  system: '\\033[33m'    # Yellow
  error: '\\033[91m'     # Bright red
  success: '\\033[92m'   # Bright green
  dim: '\\033[2m'        # Dim
  reset: '\\033[0m'      # Reset

# ============================================================================
# FEATURES - Toggle optional functionality
# ============================================================================
features:
  auto_save: true               # Automatically save conversations on exit
  rich_enabled: true            # Use rich library for formatting (if available)
  show_tokens: true             # Display token counts and cost estimates
  show_metadata: true           # Show agent metadata on startup
  readline_enabled: true        # Enable command history with readline

# ============================================================================
# PATHS - File system locations
# ============================================================================
paths:
  save_location: ~/agent-conversations    # Where to save conversations
  log_location: ~/.chat_loop_logs          # Where to write logs (in home directory)

# ============================================================================
# BEHAVIOR - Runtime behavior settings
# ============================================================================
behavior:
  max_retries: 3               # Maximum retry attempts on failure
  retry_delay: 2.0             # Seconds to wait between retries
  timeout: 120.0               # Request timeout in seconds
  spinner_style: dots          # Thinking indicator style (dots, line, arc, etc.)

# ============================================================================
# UI - User interface preferences
# ============================================================================
ui:
  show_banner: true            # Show welcome banner on startup
  show_thinking_indicator: true  # Show "Thinking..." spinner
  show_duration: true          # Show query duration
  show_status_bar: true        # Show status bar at top (agent, model, queries, time)

# ============================================================================
# AUDIO - Notification sounds
# ============================================================================
audio:
  enabled: true                # Play sound when agent completes a turn
  notification_sound: null     # Path to custom WAV file (uses bundled sound if null)

# ============================================================================
# HARMONY - OpenAI Harmony format settings (for gpt-oss models)
# ============================================================================
# IMPORTANT: Your agent must request logprobs=True in API calls for harmony
# token parsing to work. Without logprobs, only text-based fallback is used.
harmony:
  enabled: auto                 # Enable harmony processing
                                # auto (default) = Auto-detect harmony agents
                                # yes/true/force/on = Force enable for all agents
                                # no/false/off = Disable harmony processing
  show_detailed_thinking: true  # Show reasoning/analysis/commentary with prefixes
                                # When true (default), displays internal reasoning,
                                # analysis, and commentary channels with labeled
                                # prefixes. When false, only shows final response

# ============================================================================
# PER-AGENT OVERRIDES
# ============================================================================
# Override settings for specific agents by name
# Example:
# agents:
#   'My Agent':
#     features:
#       auto_save: true
#       show_tokens: true
#     paths:
#       save_location: ~/my-agent-conversations

agents: {}
"""

    try:
        with open(config_file, "w") as f:
            f.write(default_config)
        return config_file
    except Exception:
        # If we can't write the file, that's okay - will use built-in defaults
        pass

    return config_file


def get_config(config_path: Optional[Path] = None, reload: bool = False) -> ChatConfig:
    """
    Get global configuration instance.

    Args:
        config_path: Optional explicit config file path
        reload: Force reload configuration

    Returns:
        ChatConfig instance
    """
    global _global_config

    if _global_config is None or reload:
        # Initialize default config on first run if it doesn't exist
        if config_path is None:
            initialize_default_config()

        _global_config = ChatConfig(config_path)

    return _global_config
