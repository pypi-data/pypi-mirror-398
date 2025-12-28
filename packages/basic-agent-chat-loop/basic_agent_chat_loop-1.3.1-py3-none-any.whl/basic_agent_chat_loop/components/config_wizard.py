"""
Configuration wizard for Basic Agent Chat Loop.

Interactive wizard to help users configure their .chatrc settings.
"""

from pathlib import Path
from typing import Any, Optional

from ..chat_config import ChatConfig
from .ui_components import COLOR_PALETTE


def reset_config_to_defaults() -> Optional[Path]:
    """
    Reset .chatrc configuration file to default values.

    Prompts user for scope and confirmation, then writes a fresh
    configuration file with all default values.

    Returns:
        Path to the reset config file, or None if cancelled
    """
    print("\n" + "=" * 70)
    print("  Reset Configuration to Defaults")
    print("=" * 70)
    print("\nThis will reset your .chatrc file to default values.")
    print("Any customizations will be lost!")
    print("\nPress Ctrl+C at any time to cancel.\n")

    try:
        # Ask which config to reset
        print("Which configuration would you like to reset?")
        print("  1. Global (~/.chatrc)")
        print("  2. Project (./.chatrc)")

        while True:
            choice = input("\nChoice [1]: ").strip() or "1"

            if choice == "1":
                config_path = Path.home() / ".chatrc"
                break
            elif choice == "2":
                config_path = Path.cwd() / ".chatrc"
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")

        # Show what will be reset
        print(f"\nThis will reset: {config_path}")

        # Confirm
        confirm = input("\nAre you sure you want to continue? [y/N]: ").strip().lower()

        if confirm not in ["y", "yes"]:
            print("\nReset cancelled. No changes were made.")
            return None

        # Create default config
        default_config: dict[str, Any] = {
            "colors": {
                "user": "bright_white",
                "agent": "bright_blue",
                "system": "yellow",
                "error": "bright_red",
                "success": "bright_green",
            },
            "features": {
                "auto_save": False,
                "show_tokens": False,
                "show_metadata": True,
                "rich_enabled": True,
                "readline_enabled": True,
            },
            "ui": {
                "show_banner": True,
                "show_thinking_indicator": True,
                "show_duration": True,
                "show_status_bar": False,
            },
            "audio": {
                "enabled": True,
                "notification_sound": None,
            },
            "behavior": {
                "max_retries": 3,
                "retry_delay": 2.0,
                "timeout": 120.0,
                "spinner_style": "dots",
            },
            "paths": {
                "save_location": "~/agent-conversations",
                "log_location": "~/.chat_loop_logs",
            },
        }

        # Generate YAML content
        yaml_lines = [
            "# Basic Agent Chat Loop Configuration",
            "#",
            "# Reset to default values",
            "#",
            "# Format: YAML",
            "# Precedence: Project .chatrc > Global ~/.chatrc > Built-in defaults",
            "",
            "# ==================================================================",
            "# COLORS - Named color palette",
            "# ==================================================================",
            "# Available colors: black, red, green, yellow, blue, magenta, cyan,",
            "# white, bright_red, bright_green, bright_blue, bright_white",
            "colors:",
        ]

        for key, value in default_config["colors"].items():
            yaml_lines.append(f"  {key}: {value}")

        yaml_lines.extend(
            [
                "",
                "# ==================================================================",
                "# FEATURES - Toggle optional functionality",
                "# ==================================================================",
                "features:",
            ]
        )

        for key, value in default_config["features"].items():
            yaml_lines.append(f"  {key}: {str(value).lower()}")

        yaml_lines.extend(
            [
                "",
                "# ==================================================================",
                "# PATHS - File system locations",
                "# ==================================================================",
                "paths:",
            ]
        )

        for key, value in default_config["paths"].items():
            yaml_lines.append(f"  {key}: {value}")

        yaml_lines.extend(
            [
                "",
                "# ==================================================================",
                "# BEHAVIOR - Runtime behavior settings",
                "# ==================================================================",
                "behavior:",
            ]
        )

        for key, value in default_config["behavior"].items():
            yaml_lines.append(f"  {key}: {value}")

        yaml_lines.extend(
            [
                "",
                "# ==================================================================",
                "# UI - User interface preferences",
                "# ==================================================================",
                "ui:",
            ]
        )

        for key, value in default_config["ui"].items():
            yaml_lines.append(f"  {key}: {str(value).lower()}")

        yaml_lines.extend(
            [
                "",
                "# ==================================================================",
                "# AUDIO - Notification sounds",
                "# ==================================================================",
                "audio:",
                f"  enabled: {str(default_config['audio']['enabled']).lower()}",
                (
                    f"  notification_sound: "
                    f"{default_config['audio']['notification_sound'] or 'null'}"
                ),
                "",
                "# ==================================================================",
                "# PER-AGENT OVERRIDES",
                "# ==================================================================",
                "# Override settings for specific agents by name",
                "# Example:",
                "# agents:",
                "#   'My Agent':",
                "#     features:",
                "#       auto_save: true",
                "",
                "agents: {}",
            ]
        )

        yaml_content = "\n".join(yaml_lines) + "\n"

        # Write the file
        try:
            with open(config_path, "w") as f:
                f.write(yaml_content)

            # Set secure permissions
            config_path.chmod(0o600)

            print("\n" + "=" * 70)
            print(f"✓ Configuration reset to defaults: {config_path}")
            print("=" * 70)
            print("\nYou can customize it again with 'chat_loop --wizard'\n")

            return config_path

        except Exception as e:
            print(f"\nError writing configuration file: {e}")
            return None

    except KeyboardInterrupt:
        print("\n\nReset cancelled. No changes were made.")
        return None


class ConfigWizard:
    """Interactive configuration wizard."""

    def __init__(self):
        """Initialize the wizard."""
        self.config: dict[str, Any] = {}
        self.current_config: Optional[ChatConfig] = None

    def run(self) -> Optional[Path]:
        """
        Run the interactive configuration wizard.

        Returns:
            Path to the created config file, or None if cancelled
        """
        print("\n" + "=" * 70)
        print("  Basic Agent Chat Loop - Configuration Wizard")
        print("=" * 70)
        print("\nThis wizard will help you create a .chatrc configuration file.")
        print("Press Ctrl+C at any time to cancel.\n")

        try:
            # Choose scope
            scope = self._prompt_scope()
            if scope is None:
                return None

            # Load existing config if it exists
            self._load_existing_config(scope)

            # Configure each section
            print("\n" + "-" * 70)
            print("Let's configure your settings section by section.")
            if self.current_config:
                print(
                    "Current values are shown in [brackets]. Press Enter to keep them."
                )
            else:
                print(
                    "Default values are shown in [brackets]. Press Enter to use them."
                )
            print("-" * 70 + "\n")

            self._configure_features()
            self._configure_ui()
            self._configure_audio()
            self._configure_harmony()
            self._configure_behavior()
            self._configure_paths()
            self._configure_colors()

            # Write config file
            config_path = self._write_config(scope)

            if config_path:
                print("\n" + "=" * 70)
                print(f"✓ Configuration saved to: {config_path}")
                print("=" * 70)
                print("\nYou can edit this file directly at any time.")
                print("Run 'chat_loop --wizard' again to reconfigure.\n")

            return config_path

        except KeyboardInterrupt:
            print("\n\nWizard cancelled. No configuration file was created.")
            return None

    def _prompt_scope(self) -> Optional[str]:
        """
        Prompt user to choose configuration scope.

        Returns:
            'global' or 'project', or None if cancelled
        """
        print("Where would you like to save your configuration?")
        print("  1. Global (~/.chatrc) - applies to all agents")
        print("  2. Project (./.chatrc) - applies only to this directory")

        while True:
            choice = input("\nChoice [1]: ").strip() or "1"

            if choice == "1":
                return "global"
            elif choice == "2":
                return "project"
            else:
                print("Invalid choice. Please enter 1 or 2.")

    def _load_existing_config(self, scope: str):
        """
        Load existing configuration file if it exists.

        Args:
            scope: 'global' or 'project'
        """
        # Determine config path
        if scope == "global":
            config_path = Path.home() / ".chatrc"
        else:
            config_path = Path.cwd() / ".chatrc"

        # Load config if it exists
        if config_path.exists():
            print(f"\nFound existing config at: {config_path}")
            print("Loading current settings...\n")
            try:
                self.current_config = ChatConfig(config_path)
            except Exception as e:
                print(f"Warning: Could not load existing config: {e}")
                print("Using default values instead.\n")
                self.current_config = None
        else:
            print(f"\nNo existing config found at: {config_path}")
            print("Creating new configuration...\n")
            self.current_config = None

    def _configure_features(self):
        """Configure features section."""
        print("\n" + "=" * 70)
        print("FEATURES - Toggle optional functionality")
        print("=" * 70 + "\n")

        self.config["features"] = {}

        # auto_save
        current_auto_save = (
            self.current_config.get("features.auto_save", False)
            if self.current_config
            else False
        )
        self.config["features"]["auto_save"] = self._prompt_bool(
            "Automatically save conversations on exit?",
            default=current_auto_save,
            help_text="Saves each conversation to ~/agent-conversations as markdown",
        )

        # show_tokens
        current_show_tokens = (
            self.current_config.get("features.show_tokens", False)
            if self.current_config
            else False
        )
        self.config["features"]["show_tokens"] = self._prompt_bool(
            "Display token counts and cost estimates?",
            default=current_show_tokens,
            help_text="Shows input/output tokens and estimated costs per query",
        )

        # show_metadata
        current_show_metadata = (
            self.current_config.get("features.show_metadata", True)
            if self.current_config
            else True
        )
        self.config["features"]["show_metadata"] = self._prompt_bool(
            "Show agent metadata on startup?",
            default=current_show_metadata,
            help_text="Displays agent model, tools, and capabilities",
        )

        # rich_enabled
        current_rich_enabled = (
            self.current_config.get("features.rich_enabled", True)
            if self.current_config
            else True
        )
        self.config["features"]["rich_enabled"] = self._prompt_bool(
            "Use rich library for enhanced formatting?",
            default=current_rich_enabled,
            help_text="Enables markdown rendering and syntax highlighting",
        )

        # readline_enabled
        current_readline_enabled = (
            self.current_config.get("features.readline_enabled", True)
            if self.current_config
            else True
        )
        self.config["features"]["readline_enabled"] = self._prompt_bool(
            "Enable command history with readline?",
            default=current_readline_enabled,
            help_text="Allows using arrow keys to navigate command history",
        )

    def _configure_ui(self):
        """Configure UI section."""
        print("\n" + "=" * 70)
        print("UI - User interface preferences")
        print("=" * 70 + "\n")

        self.config["ui"] = {}

        # show_banner
        current_show_banner = (
            self.current_config.get("ui.show_banner", True)
            if self.current_config
            else True
        )
        self.config["ui"]["show_banner"] = self._prompt_bool(
            "Show welcome banner on startup?",
            default=current_show_banner,
            help_text="Displays agent name and description",
        )

        # show_thinking_indicator
        current_show_thinking = (
            self.current_config.get("ui.show_thinking_indicator", True)
            if self.current_config
            else True
        )
        self.config["ui"]["show_thinking_indicator"] = self._prompt_bool(
            "Show 'Thinking...' spinner while waiting?",
            default=current_show_thinking,
            help_text="Visual indicator while agent processes your query",
        )

        # show_duration
        current_show_duration = (
            self.current_config.get("ui.show_duration", True)
            if self.current_config
            else True
        )
        self.config["ui"]["show_duration"] = self._prompt_bool(
            "Show query duration?",
            default=current_show_duration,
            help_text="Displays how long each query took to complete",
        )

        # show_status_bar
        current_show_status_bar = (
            self.current_config.get("ui.show_status_bar", False)
            if self.current_config
            else False
        )
        self.config["ui"]["show_status_bar"] = self._prompt_bool(
            "Show status bar at top of screen?",
            default=current_show_status_bar,
            help_text="Displays agent, model, query count, and session time",
        )

        # update_terminal_title
        current_update_terminal_title = (
            self.current_config.get("ui.update_terminal_title", True)
            if self.current_config
            else True
        )
        self.config["ui"]["update_terminal_title"] = self._prompt_bool(
            "Update terminal title with agent status?",
            default=current_update_terminal_title,
            help_text="Shows 'Agent Name - Idle' or 'Agent Name - Processing...'",
        )

    def _configure_audio(self):
        """Configure audio section."""
        print("\n" + "=" * 70)
        print("AUDIO - Notification sounds")
        print("=" * 70 + "\n")

        self.config["audio"] = {}

        # enabled
        current_audio_enabled = (
            self.current_config.get("audio.enabled", True)
            if self.current_config
            else True
        )
        self.config["audio"]["enabled"] = self._prompt_bool(
            "Play sound when agent completes a turn?",
            default=current_audio_enabled,
            help_text="Uses bundled notification.wav by default",
        )

        # notification_sound
        if self.config["audio"]["enabled"]:
            current_sound = (
                self.current_config.get("audio.notification_sound", None)
                if self.current_config
                else None
            )
            default_text = current_sound if current_sound else "default"
            custom_sound = input(
                f"Custom WAV file path (leave blank for {default_text}): "
            ).strip()
            # If user presses enter, keep current value or None
            if not custom_sound:
                self.config["audio"]["notification_sound"] = current_sound
            else:
                self.config["audio"]["notification_sound"] = custom_sound
        else:
            self.config["audio"]["notification_sound"] = None

    def _configure_harmony(self):
        """Configure harmony section."""
        print("\n" + "=" * 70)
        print("HARMONY - OpenAI Harmony format settings (for gpt-oss models)")
        print("=" * 70 + "\n")

        self.config["harmony"] = {}

        # show_detailed_thinking
        current_show_detailed = (
            self.current_config.get("harmony.show_detailed_thinking", False)
            if self.current_config
            else False
        )
        self.config["harmony"]["show_detailed_thinking"] = self._prompt_bool(
            "Show detailed thinking with prefixes (reasoning, analysis, commentary)?",
            default=current_show_detailed,
            help_text="When enabled, Harmony agents will display internal reasoning, "
            "analysis, and commentary channels with labeled prefixes. "
            "When disabled (default), only shows final response.",
        )

    def _configure_behavior(self):
        """Configure behavior section."""
        print("\n" + "=" * 70)
        print("BEHAVIOR - Runtime behavior settings")
        print("=" * 70 + "\n")

        self.config["behavior"] = {}

        # max_retries
        current_max_retries = (
            self.current_config.get("behavior.max_retries", 3)
            if self.current_config
            else 3
        )
        self.config["behavior"]["max_retries"] = self._prompt_int(
            "Maximum retry attempts on failure",
            default=int(current_max_retries),
            min_val=0,
            max_val=10,
            help_text="Number of times to retry failed requests",
        )

        # retry_delay
        current_retry_delay = (
            self.current_config.get("behavior.retry_delay", 2.0)
            if self.current_config
            else 2.0
        )
        self.config["behavior"]["retry_delay"] = self._prompt_float(
            "Seconds to wait between retries",
            default=float(current_retry_delay),
            min_val=0.5,
            max_val=30.0,
            help_text="Delay before retrying after an error",
        )

        # timeout
        current_timeout = (
            self.current_config.get("behavior.timeout", 120.0)
            if self.current_config
            else 120.0
        )
        self.config["behavior"]["timeout"] = self._prompt_float(
            "Request timeout in seconds",
            default=float(current_timeout),
            min_val=10.0,
            max_val=600.0,
            help_text="Maximum time to wait for agent response",
        )

        # spinner_style
        current_spinner_style = (
            self.current_config.get("behavior.spinner_style", "dots")
            if self.current_config
            else "dots"
        )
        styles = ["dots", "line", "arc", "arrow", "bounce", "circle"]
        print(f"\nThinking indicator style (options: {', '.join(styles)})")
        print(f"   [{current_spinner_style}] Current style")
        style = (
            input(f"Style [{current_spinner_style}]: ").strip() or current_spinner_style
        )
        self.config["behavior"]["spinner_style"] = (
            style if style in styles else current_spinner_style
        )

    def _configure_paths(self):
        """Configure paths section."""
        print("\n" + "=" * 70)
        print("PATHS - File system locations")
        print("=" * 70 + "\n")

        self.config["paths"] = {}

        # save_location
        current_save_location = (
            self.current_config.get("paths.save_location", "~/agent-conversations")
            if self.current_config
            else "~/agent-conversations"
        )
        print("Where to save conversations (supports ~ for home directory)")
        save_loc = input(f"Save location [{current_save_location}]: ").strip()
        self.config["paths"]["save_location"] = save_loc or current_save_location

        # log_location
        current_log_location = (
            self.current_config.get("paths.log_location", "~/.chat_loop_logs")
            if self.current_config
            else "~/.chat_loop_logs"
        )
        print("\nWhere to write logs (supports ~ for home directory)")
        log_loc = input(f"Log location [{current_log_location}]: ").strip()
        self.config["paths"]["log_location"] = log_loc or current_log_location

    def _configure_colors(self):
        """Configure colors section."""
        print("\n" + "=" * 70)
        print("COLORS - Terminal color customization")
        print("=" * 70 + "\n")

        # Default color names (not ANSI codes)
        default_colors = {
            "user": "bright_white",
            "agent": "bright_blue",
            "system": "yellow",
            "error": "bright_red",
            "success": "bright_green",
        }

        # Get current colors from config
        if self.current_config:
            current_colors = self.current_config.get_section("colors")
            # Convert ANSI codes to color names if needed (backward compatibility)
            for key in default_colors:
                if key in current_colors:
                    val = current_colors[key]
                    # Check if it's already a color name
                    if val not in COLOR_PALETTE:
                        # It's an ANSI code, use default color name
                        current_colors[key] = default_colors[key]
        else:
            current_colors = default_colors.copy()

        print("Would you like to customize terminal colors?")
        if self.current_config:
            print("  (Current colors will be preserved if you skip customization)")
        else:
            print("  (Default colors work well for most terminals)")

        if not self._prompt_bool("Customize colors?", default=False):
            # Keep current/default colors
            self.config["colors"] = current_colors
            return

        print("\nSelect colors from the named palette:")
        print("(12 colors available: black, red, green, yellow, blue, magenta,")
        print(" cyan, white, bright_red, bright_green, bright_blue, bright_white)\n")

        self.config["colors"] = {
            "user": self._prompt_color(
                "User input color", current_colors.get("user", "bright_white")
            ),
            "agent": self._prompt_color(
                "Agent response color", current_colors.get("agent", "bright_blue")
            ),
            "system": self._prompt_color(
                "System message color", current_colors.get("system", "yellow")
            ),
            "error": self._prompt_color(
                "Error message color", current_colors.get("error", "bright_red")
            ),
            "success": self._prompt_color(
                "Success message color", current_colors.get("success", "bright_green")
            ),
        }

    def _write_config(self, scope: str) -> Optional[Path]:
        """
        Write configuration to YAML file.

        Args:
            scope: 'global' or 'project'

        Returns:
            Path to created config file, or None on failure
        """
        # Determine config path
        if scope == "global":
            config_path = Path.home() / ".chatrc"
        else:
            config_path = Path.cwd() / ".chatrc"

        # Check if file exists
        if config_path.exists():
            if self.current_config:
                # We loaded this config, so it's an update
                print(f"\nReady to save changes to: {config_path}")
                overwrite = self._prompt_bool(
                    "Save changes to existing file?", default=True
                )
            else:
                # File exists but couldn't be loaded
                print(f"\nWarning: {config_path} already exists.")
                overwrite = self._prompt_bool("Overwrite existing file?", default=False)

            if not overwrite:
                print("Configuration not saved.")
                return None

        # Add agents placeholder
        self.config["agents"] = {}

        # Generate YAML with comments
        yaml_content = self._generate_yaml_with_comments()

        try:
            with open(config_path, "w") as f:
                f.write(yaml_content)

            # Set secure permissions
            config_path.chmod(0o600)

            return config_path

        except Exception as e:
            print(f"\nError writing configuration file: {e}")
            return None

    def _generate_yaml_with_comments(self) -> str:
        """
        Generate YAML content with helpful comments.

        Returns:
            Formatted YAML string
        """
        lines = [
            "# Basic Agent Chat Loop Configuration",
            "#",
            "# Generated by configuration wizard",
            "#",
            "# Format: YAML",
            "# Precedence: Project .chatrc > Global ~/.chatrc > Built-in defaults",
            "",
            "# ==================================================================",
            "# COLORS - Named color palette",
            "# ==================================================================",
            "# Available colors: black, red, green, yellow, blue, magenta, cyan,",
            "# white, bright_red, bright_green, bright_blue, bright_white",
            "colors:",
        ]

        for key, value in self.config["colors"].items():
            lines.append(f"  {key}: {value}")

        lines.extend(
            [
                "",
                "# ==================================================================",
                "# FEATURES - Toggle optional functionality",
                "# ==================================================================",
                "features:",
            ]
        )

        for key, value in self.config["features"].items():
            lines.append(f"  {key}: {str(value).lower()}")

        lines.extend(
            [
                "",
                "# ==================================================================",
                "# PATHS - File system locations",
                "# ==================================================================",
                "paths:",
            ]
        )

        for key, value in self.config["paths"].items():
            lines.append(f"  {key}: {value}")

        lines.extend(
            [
                "",
                "# ==================================================================",
                "# BEHAVIOR - Runtime behavior settings",
                "# ==================================================================",
                "behavior:",
            ]
        )

        for key, value in self.config["behavior"].items():
            lines.append(f"  {key}: {value}")

        lines.extend(
            [
                "",
                "# ==================================================================",
                "# UI - User interface preferences",
                "# ==================================================================",
                "ui:",
            ]
        )

        for key, value in self.config["ui"].items():
            lines.append(f"  {key}: {str(value).lower()}")

        lines.extend(
            [
                "",
                "# ==================================================================",
                "# AUDIO - Notification sounds",
                "# ==================================================================",
                "audio:",
                f"  enabled: {str(self.config['audio']['enabled']).lower()}",
                f"  notification_sound: "
                f"{self.config['audio']['notification_sound'] or 'null'}",
                "",
                "# ==================================================================",
                "# PER-AGENT OVERRIDES",
                "# ==================================================================",
                "# Override settings for specific agents by name",
                "# Example:",
                "# agents:",
                "#   'My Agent':",
                "#     features:",
                "#       auto_save: true",
                "",
                "agents: {}",
            ]
        )

        return "\n".join(lines) + "\n"

    def _prompt_bool(
        self, prompt: str, default: bool, help_text: Optional[str] = None
    ) -> bool:
        """
        Prompt user for a boolean value.

        Args:
            prompt: Question to ask
            default: Default value
            help_text: Optional help text

        Returns:
            Boolean value
        """
        default_str = "Y/n" if default else "y/N"

        if help_text:
            print(f"   {help_text}")

        while True:
            response = input(f"{prompt} [{default_str}]: ").strip().lower()

            if not response:
                return default

            if response in ["y", "yes", "true", "1"]:
                return True
            elif response in ["n", "no", "false", "0"]:
                return False
            else:
                print("Please enter y or n")

    def _prompt_int(
        self,
        prompt: str,
        default: int,
        min_val: Optional[int] = None,
        max_val: Optional[int] = None,
        help_text: Optional[str] = None,
    ) -> int:
        """
        Prompt user for an integer value.

        Args:
            prompt: Question to ask
            default: Default value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            help_text: Optional help text

        Returns:
            Integer value
        """
        if help_text:
            print(f"   {help_text}")

        while True:
            response = input(f"{prompt} [{default}]: ").strip()

            if not response:
                return default

            try:
                value = int(response)

                if min_val is not None and value < min_val:
                    print(f"Value must be at least {min_val}")
                    continue

                if max_val is not None and value > max_val:
                    print(f"Value must be at most {max_val}")
                    continue

                return value

            except ValueError:
                print("Please enter a valid integer")

    def _prompt_float(
        self,
        prompt: str,
        default: float,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        help_text: Optional[str] = None,
    ) -> float:
        """
        Prompt user for a float value.

        Args:
            prompt: Question to ask
            default: Default value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            help_text: Optional help text

        Returns:
            Float value
        """
        if help_text:
            print(f"   {help_text}")

        while True:
            response = input(f"{prompt} [{default}]: ").strip()

            if not response:
                return default

            try:
                value = float(response)

                if min_val is not None and value < min_val:
                    print(f"Value must be at least {min_val}")
                    continue

                if max_val is not None and value > max_val:
                    print(f"Value must be at most {max_val}")
                    continue

                return value

            except ValueError:
                print("Please enter a valid number")

    def _prompt_string(self, prompt: str, default: str) -> str:
        """
        Prompt user for a string value.

        Args:
            prompt: Question to ask
            default: Default value

        Returns:
            String value
        """
        response = input(f"{prompt} [{default}]: ").strip()
        return response or default

    def _prompt_color(self, prompt: str, default: str) -> str:
        """
        Prompt user for a color selection from the named palette.

        Args:
            prompt: Question to ask
            default: Default color name

        Returns:
            Color name from palette
        """
        # Get list of available colors
        colors = sorted(COLOR_PALETTE.keys())

        print(f"\n{prompt}")
        print(f"Available colors: {', '.join(colors)}")

        while True:
            response = input(f"Color [{default}]: ").strip().lower()

            if not response:
                return default

            if response in COLOR_PALETTE:
                return response
            else:
                print(f"Invalid color. Choose from: {', '.join(colors)}")
