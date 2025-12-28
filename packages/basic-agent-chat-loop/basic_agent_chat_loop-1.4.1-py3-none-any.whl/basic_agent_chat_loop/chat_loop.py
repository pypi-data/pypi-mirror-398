#!/usr/bin/env python3
"""
Basic Agent Chat Loop - Interactive CLI for AI Agents

A feature-rich, unified chat interface for any AI agent with token tracking,
prompt templates, configuration management, and extensive UX enhancements.

Features:
- Async streaming support with real-time response display
- Command history with readline (↑↓ to navigate, saved to ~/.chat_history)
- Agent logs with rotation and secure permissions (0600) in ~/.chat_loop_logs/
- Multi-line input support (type \\\\ to enter multi-line mode)
  - Ctrl+D to cancel, ↑ arrow to edit previous line
  - Saves full block to history for later recall
- Token tracking and cost estimation per query and session
- Prompt templates from ~/.prompts/ with variable substitution
- Configuration file support (~/.chatrc or .chatrc in project root)
- Status bar with real-time metrics (queries, tokens, duration)
- Session summary on exit with full statistics
- Automatic error recovery with retry logic
- Rich markdown rendering with syntax highlighting
- Agent metadata display (model, tools, capabilities)

Privacy Note:
- Logs may contain user queries (truncated) and should be treated as sensitive
- See SECURITY.md for details on what gets logged and privacy considerations

Usage:
    chat_loop path/to/agent.py
    chat_loop my_agent_alias
    chat_loop <agent_path> --config ~/.chatrc-custom
"""

import argparse
import asyncio
import json
import logging
import logging.handlers
import os
import stat
import sys
import time
from pathlib import Path
from typing import Any, Optional

import pyperclip  # type: ignore[import-untyped]

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

# Platform-specific imports for ESC key detection
# Note: imports are done inside functions to avoid unused import warnings
try:
    if sys.platform != "win32":
        TERMIOS_AVAILABLE = True
    else:
        TERMIOS_AVAILABLE = False
    ESC_KEY_SUPPORT = True
except Exception:
    ESC_KEY_SUPPORT = False
    TERMIOS_AVAILABLE = False


# Components
# Configuration management
from .chat_config import ChatConfig, get_config
from .components import (
    AliasManager,
    AudioNotifier,
    Colors,
    ConfigWizard,
    DependencyManager,
    DisplayManager,
    HarmonyProcessor,
    SessionManager,
    StatusBar,
    TemplateManager,
    TokenTracker,
    extract_agent_metadata,
    load_agent_module,
)

# Rich library for better formatting
try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.spinner import Spinner

    RICH_AVAILABLE = True
    ConsoleType = Console
    MarkdownType = Markdown
except ImportError:
    RICH_AVAILABLE = False
    ConsoleType = None  # type: ignore
    MarkdownType = None  # type: ignore

# Setup logging directory in home directory for easy access
# Default: ~/.chat_loop_logs/
log_dir = Path.home() / ".chat_loop_logs"

# Command history configuration
READLINE_HISTORY_LENGTH = 1000

# Use a single consistent logger throughout the module
logger = logging.getLogger("basic_agent_chat_loop")


def _serialize_for_logging(obj: Any) -> str:
    """
    Serialize an object to JSON string for logging, with repr() fallback.

    Args:
        obj: The object to serialize

    Returns:
        JSON string if serializable, otherwise repr() string
    """
    try:
        return json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        # Fallback to repr() for non-serializable objects
        return repr(obj)


def setup_logging(agent_name: str) -> bool:
    """
    Setup logging with agent-specific filename, rotation, and secure permissions.

    Log files are stored in ~/.chat_loop_logs/ with:
    - Rotating file handler (max 10MB per file, 5 backup files)
    - Restrictive permissions (0600 - owner read/write only)
    - UTF-8 encoding

    Args:
        agent_name: Name of the agent for the log file

    Returns:
        True if logging was successfully configured, False otherwise
    """
    try:
        # Ensure log directory exists with secure permissions
        log_dir.mkdir(exist_ok=True, mode=0o700)

        # Create log file path with sanitized agent name
        safe_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        log_file = log_dir / f"{safe_name}_chat.log"

        # Configure our logger
        logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        logger.handlers = []

        # Add rotating file handler with formatting
        # maxBytes=10MB, backupCount=5 keeps last ~50MB of logs
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)

        # Set restrictive permissions on log file (owner read/write only)
        if log_file.exists():
            os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)  # 0600

        # Also add console handler for errors (stderr only)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)

        logger.info(f"Logging initialized for agent: {agent_name}")
        logger.info(f"Log file: {log_file}")
        return True

    except Exception as e:
        # Fallback: print to stderr if logging setup fails
        print(f"Warning: Could not setup logging: {e}", file=sys.stderr)
        # Set up minimal console-only logging as fallback
        logger.setLevel(logging.WARNING)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console_handler)
        return False


def set_terminal_title(title: str) -> None:
    """
    Set the terminal window/tab title.

    Uses ANSI escape sequences to update the terminal title.
    Works on macOS Terminal, iTerm2, Linux terminals, Windows Terminal, etc.

    Args:
        title: The title to set
    """
    try:
        # \033]0; sets both icon and window title
        # \033\\ is ST (String Terminator) - more compatible than BEL (\007)
        # ST works better with Mac Terminal and VSCode's integrated terminal
        print(f"\033]0;{title}\033\\", end="", flush=True)
    except Exception:
        # Silently fail if terminal doesn't support it
        pass


def setup_readline_history() -> Optional[Path]:
    """
    Setup readline command history with persistence.

    Returns:
        Path to history file if successful, None otherwise
    """
    if not READLINE_AVAILABLE:
        logger.debug("Readline not available, history will not be saved")
        # Show warning on Windows if readline is not available
        if sys.platform == "win32":
            print(
                Colors.system(
                    "⚠️  Command history not available. "
                    "This should not happen on Windows.\n"
                    "   Try reinstalling: "
                    "pip install --force-reinstall basic-agent-chat-loop"
                )
            )
        return None

    try:
        # History file in user's home directory
        history_file = Path.home() / ".chat_history"

        # Set history length
        readline.set_history_length(READLINE_HISTORY_LENGTH)

        # Enable tab completion and better editing
        try:
            # Suppress CPR warning by redirecting stderr temporarily
            old_stderr = sys.stderr
            sys.stderr = open(os.devnull, "w")

            try:
                # Parse readline init file if it exists
                readline.parse_and_bind("tab: complete")

                # Enable vi or emacs mode (emacs is default)
                readline.parse_and_bind("set editing-mode emacs")

                # Disable horizontal scroll to prevent CPR check
                readline.parse_and_bind("set horizontal-scroll-mode off")

                # Enable better line editing
                readline.parse_and_bind("set show-all-if-ambiguous on")
                readline.parse_and_bind("set completion-ignore-case on")
            finally:
                # Restore stderr
                sys.stderr.close()
                sys.stderr = old_stderr
        except Exception as e:
            logger.debug(f"Could not configure readline bindings: {e}")
            # Continue anyway, basic history will still work

        # Load existing history
        if history_file.exists():
            try:
                readline.read_history_file(str(history_file))
                count = readline.get_current_history_length()
                logger.debug(f"Loaded {count} history entries")
            except Exception as e:
                logger.warning(f"Could not load history from {history_file}: {e}")
                # Continue anyway, we'll create new history

        logger.debug(f"Command history will be saved to: {history_file}")
        return history_file

    except Exception as e:
        logger.warning(f"Could not setup command history: {e}")
        return None


def save_readline_history(history_file: Optional[Path]) -> bool:
    """
    Save readline command history.

    Args:
        history_file: Path to history file

    Returns:
        True if history was successfully saved, False otherwise
    """
    if not history_file:
        return False

    if not READLINE_AVAILABLE:
        return False

    try:
        # Ensure parent directory exists
        history_file.parent.mkdir(parents=True, exist_ok=True)

        # Save history
        readline.write_history_file(str(history_file))

        # Set secure permissions (readable/writable by owner only)
        history_file.chmod(0o600)

        count = readline.get_current_history_length()
        logger.debug(f"Saved {count} history entries to {history_file}")
        return True

    except Exception as e:
        logger.warning(f"Could not save command history to {history_file}: {e}")
        return False


def get_char_with_esc_detection() -> Optional[str]:
    """
    Get a single character from stdin with ESC and arrow key detection.

    Returns:
        The character typed, None if ESC was pressed,
        "UP_ARROW" if up arrow was pressed, or "" if detection failed
    """
    if not ESC_KEY_SUPPORT:
        return ""  # Fall back to regular input

    try:
        if sys.platform == "win32":
            # Windows implementation
            import msvcrt

            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\xe0":  # Extended key prefix on Windows
                    if msvcrt.kbhit():
                        extended = msvcrt.getch()
                        if extended == b"H":  # Up arrow
                            return "UP_ARROW"
                    return ""
                elif char == b"\x1b":  # ESC key
                    return None
                return char.decode("utf-8", errors="ignore")
            return ""
        else:
            # Unix/Linux/Mac implementation
            import select
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
                if char == "\x1b":  # ESC or arrow key sequence
                    # Check if more characters follow (within 100ms)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        seq = sys.stdin.read(2)
                        if seq == "[A":  # Up arrow
                            return "UP_ARROW"
                        # Other arrow keys would be [B, [C, [D
                    # Just ESC pressed
                    return None
                return char
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception as e:
        logger.debug(f"Key detection failed: {e}")
        return ""  # Fall back to regular input


def input_with_esc(prompt: str) -> Optional[str]:
    """
    Enhanced input() that detects ESC and arrow key presses.

    Args:
        prompt: The prompt to display

    Returns:
        The user's input string, None if ESC was pressed,
        or "UP_ARROW" if up arrow was pressed
    """
    if not ESC_KEY_SUPPORT:
        # Fall back to regular input
        return input(prompt)

    # Print the prompt
    print(prompt, end="", flush=True)

    # Try to detect ESC/arrows on first character
    first_char = get_char_with_esc_detection()

    if first_char is None:
        # ESC was pressed
        print()  # New line after ESC
        return None
    elif first_char == "UP_ARROW":
        # Up arrow was pressed
        print()  # New line
        return "UP_ARROW"
    elif first_char == "":
        # Detection not available or failed, use regular input
        # But we already printed the prompt, so use empty prompt
        return input("")
    else:
        # Got a character, print it and continue with regular input
        print(first_char, end="", flush=True)
        rest_of_line = input("")
        return first_char + rest_of_line


class ChatLoop:
    """Generic chat loop for any AI agent with async streaming support."""

    def __init__(
        self,
        agent,
        agent_name: str,
        agent_description: str,
        agent_factory=None,
        agent_path: Optional[str] = None,
        config: Optional["ChatConfig"] = None,
    ):
        self.agent = agent
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_factory = agent_factory  # Function to create fresh agent instance
        self.agent_path = agent_path or "unknown"  # Store for session metadata
        self.history_file = None
        self.last_response = ""  # Track last response for copy command
        self.last_query = ""  # Track last user query for copy command

        # Conversation tracking for auto-save
        self.conversation_history: list[dict[str, Any]] = []

        # Generate session ID for this chat session
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_agent_name = agent_name.lower().replace(" ", "_").replace("/", "_")
        self.session_id = f"{safe_agent_name}_{timestamp}"

        # Load or use provided config
        self.config = config if config else get_config()

        # Apply configuration values (with agent-specific overrides)
        if self.config:
            self.max_retries = int(
                self.config.get("behavior.max_retries", 3, agent_name=agent_name)
            )
            self.retry_delay = float(
                self.config.get("behavior.retry_delay", 2.0, agent_name=agent_name)
            )
            self.timeout = float(
                self.config.get("behavior.timeout", 120.0, agent_name=agent_name)
            )
            self.spinner_style = self.config.get(
                "behavior.spinner_style", "dots", agent_name=agent_name
            )

            # Feature flags
            self.auto_save = self.config.get(
                "features.auto_save", False, agent_name=agent_name
            )
            self.show_metadata = self.config.get(
                "features.show_metadata", True, agent_name=agent_name
            )
            self.show_thinking = self.config.get(
                "ui.show_thinking_indicator", True, agent_name=agent_name
            )
            self.show_duration = self.config.get(
                "ui.show_duration", True, agent_name=agent_name
            )
            self.show_banner = self.config.get(
                "ui.show_banner", True, agent_name=agent_name
            )
            self.update_terminal_title = self.config.get(
                "ui.update_terminal_title", True, agent_name=agent_name
            )

            # Rich override
            rich_enabled = self.config.get(
                "features.rich_enabled", True, agent_name=agent_name
            )
            self.use_rich = RICH_AVAILABLE and rich_enabled
        else:
            # Defaults when no config
            self.max_retries = 3
            self.retry_delay = 2.0
            self.timeout = 120.0
            self.spinner_style = "dots"
            self.auto_save = False
            self.show_metadata = True
            self.show_thinking = True
            self.show_duration = True
            self.show_banner = True
            self.update_terminal_title = True
            self.use_rich = RICH_AVAILABLE

        # Setup rich console if available and enabled
        self.console: Optional[Console] = Console() if self.use_rich else None

        # Extract agent metadata
        self.agent_metadata = extract_agent_metadata(self.agent)

        # Log model detection for debugging
        detected_model = self.agent_metadata.get("model_id", "Unknown")
        uses_harmony = self.agent_metadata.get("uses_harmony", False)
        logger.info(f"Model Detected: {detected_model}")
        logger.info(f"Harmony Detected: {uses_harmony}")

        # Setup prompt templates directory
        self.prompts_dir = Path.home() / ".prompts"

        # Create template manager
        self.template_manager = TemplateManager(self.prompts_dir)

        # Setup token tracking (always enabled for session summary)
        self.show_tokens = (
            self.config.get("features.show_tokens", False, agent_name=agent_name)
            if self.config
            else False
        )
        model_for_pricing = self.agent_metadata.get("model_id", "Unknown")

        # Check for config override
        if self.config:
            model_override = self.config.get(
                "agents." + agent_name + ".model_display_name", None
            )
            if model_override:
                model_for_pricing = model_override

        # Always create token tracker for session summary
        # (not just when show_tokens is true)
        self.token_tracker = TokenTracker(model_for_pricing)

        # Track session start time for summary
        self.session_start_time = time.time()
        self.query_count = 0

        # Setup status bar if enabled
        self.show_status_bar_enabled = (
            self.config.get("ui.show_status_bar", False, agent_name=agent_name)
            if self.config
            else False
        )
        self.status_bar = None
        if self.show_status_bar_enabled:
            model_info = self.agent_metadata.get("model_id", "Unknown Model")

            # Check for config override
            if self.config:
                model_override = self.config.get(
                    "agents." + agent_name + ".model_display_name", None
                )
                if model_override:
                    model_info = model_override

            # Shorten long model IDs (ensure it's a string first)
            model_info = str(model_info) if model_info else "Unknown Model"
            if len(model_info) > 30:
                model_info = model_info[:27] + "..."

            self.status_bar = StatusBar(
                agent_name, model_info, show_tokens=self.show_tokens
            )

            # Log for debugging
            logger.debug(
                f"Status bar initialized: agent={agent_name}, "
                f"model={model_info}, show_tokens={self.show_tokens}"
            )

        # Create display manager
        self.display_manager = DisplayManager(
            agent_name=self.agent_name,
            agent_description=self.agent_description,
            agent_metadata=self.agent_metadata,
            show_banner=self.show_banner,
            show_metadata=self.show_metadata,
            use_rich=self.use_rich,
            auto_save=self.auto_save,
            config=self.config,
            status_bar=self.status_bar,
        )

        # Setup audio notifications
        audio_enabled = (
            self.config.get("audio.enabled", True, agent_name=agent_name)
            if self.config
            else True
        )
        audio_sound_file = (
            self.config.get("audio.notification_sound", None, agent_name=agent_name)
            if self.config
            else None
        )
        self.audio_notifier = AudioNotifier(
            enabled=audio_enabled, sound_file=audio_sound_file
        )

        # Setup session manager for conversation persistence
        sessions_dir = (
            self.config.expand_path(
                self.config.get("paths.save_location", "~/agent-conversations")
            )
            if self.config
            else Path.home() / "agent-conversations"
        )
        self.session_manager = SessionManager(sessions_dir=sessions_dir)

        # Setup Harmony processor if agent uses Harmony format
        self.harmony_processor = None

        # Check if harmony should be enabled
        # Priority: config override > auto-detection
        harmony_enabled_config_raw = (
            self.config.get("harmony.enabled", None) if self.config else None
        )

        # Auto-detect harmony support
        # Detection already performed by extract_agent_metadata()
        uses_harmony = self.agent_metadata.get("uses_harmony", False)

        # Normalize config value to handle string values from YAML
        # "auto"/None → None (auto-detect)
        # "yes"/"true"/"force"/True → True (force enable)
        # "no"/"false"/False → False (force disable)
        harmony_enabled_config = self._normalize_harmony_config(
            harmony_enabled_config_raw
        )

        logger.debug(f"Harmony config value (raw): {harmony_enabled_config_raw!r}")
        logger.debug(f"Harmony config value (normalized): {harmony_enabled_config!r}")
        logger.debug(f"Auto-detected harmony: {uses_harmony}")

        # Determine if harmony should be enabled
        # None = auto-detect, True = force enable, False = force disable
        should_enable_harmony = (
            harmony_enabled_config
            if harmony_enabled_config is not None
            else uses_harmony
        )

        logger.debug(f"Should enable harmony: {should_enable_harmony}")

        if should_enable_harmony:
            # Get detailed thinking config option
            show_detailed = (
                self.config.get("harmony.show_detailed_thinking", True)
                if self.config
                else True
            )
            self.harmony_processor = HarmonyProcessor(
                show_detailed_thinking=show_detailed
            )

            # Log how harmony was enabled
            if harmony_enabled_config is True:
                logger.info(
                    f"✓ Harmony ENABLED via config override "
                    f"(detailed_thinking={show_detailed})"
                )
            elif harmony_enabled_config is False:
                logger.info("✗ Harmony DISABLED via config override")
            else:
                logger.info(
                    f"✓ Harmony AUTO-DETECTED and enabled "
                    f"(detailed_thinking={show_detailed})"
                )
        else:
            logger.info(
                "✗ Harmony NOT enabled (agent not detected as harmony, config not set)"
            )

    def _normalize_harmony_config(self, value: Any) -> Optional[bool]:
        """
        Normalize harmony config value from YAML to proper type.

        Handles various string representations from YAML config files:
        - "auto", None, "" → None (auto-detect)
        - "yes", "true", "force", "on", True → True (force enable)
        - "no", "false", "off", False → False (force disable)

        Args:
            value: Raw config value from YAML

        Returns:
            None for auto-detect, True to force enable, False to force disable
        """
        if value is None or value == "":
            return None

        # Handle boolean values
        if isinstance(value, bool):
            return value

        # Handle string values (case-insensitive)
        if isinstance(value, str):
            value_lower = value.lower().strip()

            # Auto-detect
            if value_lower in ("auto", "detect"):
                return None

            # Force enable
            if value_lower in ("yes", "true", "force", "on", "enable", "enabled"):
                return True

            # Force disable
            if value_lower in ("no", "false", "off", "disable", "disabled"):
                return False

            # Unknown string - warn and default to auto-detect
            logger.warning(
                f"Unknown harmony.enabled value: {value!r} - "
                f"using auto-detect (valid: auto/yes/no)"
            )
            return None

        # Unknown type - warn and default to auto-detect
        logger.warning(
            f"Invalid harmony.enabled type: {type(value).__name__} - "
            f"using auto-detect (expected: bool or string)"
        )
        return None

    def _extract_token_usage(self, response_obj) -> Optional[dict[str, int]]:
        """
        Extract token usage from response object.

        Args:
            response_obj: Response object from agent

        Returns:
            Dict with 'input_tokens' and 'output_tokens', or None if not available
        """
        if not response_obj:
            return None

        # Try common attribute patterns
        usage = None

        # Pattern 1: response['result'].metrics.accumulated_usage (AWS Bedrock style)
        if isinstance(response_obj, dict) and "result" in response_obj:
            result = response_obj["result"]
            if hasattr(result, "metrics") and hasattr(
                result.metrics, "accumulated_usage"
            ):
                usage = result.metrics.accumulated_usage

        # Pattern 2: response.usage (Anthropic/Claude style)
        elif hasattr(response_obj, "usage"):
            usage = response_obj.usage

        # Pattern 3: response['usage'] (dict style)
        elif isinstance(response_obj, dict) and "usage" in response_obj:
            usage = response_obj["usage"]

        # Pattern 4: response.metadata.usage
        elif hasattr(response_obj, "metadata") and hasattr(
            response_obj.metadata, "usage"
        ):
            usage = response_obj.metadata.usage

        # Pattern 5: response.data.usage (streaming event)
        elif hasattr(response_obj, "data") and hasattr(response_obj.data, "usage"):
            usage = response_obj.data.usage

        # Pattern 6: response.data['usage'] (streaming event dict)
        elif (
            hasattr(response_obj, "data")
            and isinstance(response_obj.data, dict)
            and "usage" in response_obj.data
        ):
            usage = response_obj.data["usage"]

        if not usage:
            return None

        # Extract input and output tokens
        input_tokens = 0
        output_tokens = 0

        # Try different attribute names (check dict keys first, then attributes)
        if isinstance(usage, dict):
            # AWS Bedrock camelCase
            if "inputTokens" in usage:
                input_tokens = usage["inputTokens"]
            elif "input_tokens" in usage:
                input_tokens = usage["input_tokens"]
            elif "prompt_tokens" in usage:
                input_tokens = usage["prompt_tokens"]

            if "outputTokens" in usage:
                output_tokens = usage["outputTokens"]
            elif "output_tokens" in usage:
                output_tokens = usage["output_tokens"]
            elif "completion_tokens" in usage:
                output_tokens = usage["completion_tokens"]
        else:
            # Object attributes
            if hasattr(usage, "input_tokens"):
                input_tokens = usage.input_tokens
            elif hasattr(usage, "prompt_tokens"):
                input_tokens = usage.prompt_tokens

            if hasattr(usage, "output_tokens"):
                output_tokens = usage.output_tokens
            elif hasattr(usage, "completion_tokens"):
                output_tokens = usage.completion_tokens

        if input_tokens > 0 or output_tokens > 0:
            return {"input_tokens": input_tokens, "output_tokens": output_tokens}

        return None

    def _extract_code_blocks(self, text: str) -> list:
        """
        Extract code blocks from markdown text.

        Args:
            text: Markdown text containing code blocks

        Returns:
            List of code block contents (without fence markers)
        """
        import re

        # Match code blocks with triple backticks
        pattern = r"```(?:\w+)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return [match.strip() for match in matches]

    def _format_conversation_as_markdown(self) -> str:
        """
        Format entire conversation history as markdown.

        Returns:
            Markdown-formatted conversation
        """
        from datetime import datetime

        lines = []
        lines.append(f"# {self.agent_name} - Conversation")
        lines.append(f"\nSession ID: {self.session_id}")
        lines.append(f"Agent: {self.agent_name}")

        if self.conversation_history:
            first_ts = self.conversation_history[0]["timestamp"]
            lines.append(f"Started: {datetime.fromtimestamp(first_ts)}")

        lines.append("\n---\n")

        for i, entry in enumerate(self.conversation_history, 1):
            timestamp = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
            lines.append(f"\n## Query {i} ({timestamp})\n")
            lines.append(f"**You:** {entry['query']}\n")
            lines.append(f"**{self.agent_name}:**\n\n{entry['response']}\n")

            if entry.get("duration"):
                duration = entry["duration"]
                lines.append(f"\n*Response time: {duration:.1f}s*")

            if entry.get("usage"):
                usage = entry["usage"]
                input_tok = usage.get("input_tokens", 0)
                output_tok = usage.get("output_tokens", 0)
                total = input_tok + output_tok
                lines.append(
                    f" | *Tokens: {total:,} (in: {input_tok:,}, out: {output_tok:,})*"
                )

            lines.append("\n---\n")

        return "\n".join(lines)

    async def restore_session(self, session_id: str) -> bool:
        """
        Restore a previous session by replaying conversation to agent.

        Args:
            session_id: Session ID or number from sessions list

        Returns:
            True if session was successfully restored, False otherwise
        """
        try:
            # If session_id is a number, resolve it from the list
            if session_id.isdigit():
                session_num = int(session_id)
                sessions = self.session_manager.list_sessions(
                    agent_name=self.agent_name, limit=20
                )

                if session_num < 1 or session_num > len(sessions):
                    print(Colors.error(f"Invalid session number: {session_num}"))
                    print(f"Valid range: 1-{len(sessions)}")
                    return False

                # Get actual session_id from the list (1-indexed)
                session_info = sessions[session_num - 1]
                session_id = session_info.session_id
            else:
                # Get session metadata for display
                maybe_session_info = self.session_manager.get_session_metadata(
                    session_id
                )
                if not maybe_session_info:
                    print(Colors.error(f"Session not found: {session_id}"))
                    return False
                session_info = maybe_session_info

            # Load the session data
            session_data = self.session_manager.load_session(session_id)
            if not session_data:
                print(Colors.error(f"Could not load session: {session_id}"))
                return False

            conversation = session_data.get("conversation", [])
            if not conversation:
                print(Colors.error("Session has no conversation history"))
                return False

            # Check if agent matches
            if session_data["agent_name"] != self.agent_name:
                print(
                    Colors.system(
                        f"⚠️  Warning: Session was created with "
                        f"'{session_data['agent_name']}' "
                        f"but you're using '{self.agent_name}'"
                    )
                )
                confirm = input(Colors.system("Continue anyway? (y/n): "))
                if confirm.lower() != "y":
                    print(Colors.system("Resume cancelled"))
                    return False

            # Display what we're loading
            print(f"\n🔄 Loading session: {session_id}")
            print(f"   Agent: {session_data['agent_name']}")
            print(f"   Queries: {len(conversation)}")
            print(f"   Created: {session_info.created.strftime('%b %d, %Y at %H:%M')}")
            if session_info.total_cost > 0:
                print(f"   Cost so far: ${session_info.total_cost:.3f}")
            print()

            # Ask for confirmation (if enabled in config)
            resume_confirmation = (
                self.config.get("sessions.resume_confirmation", True)
                if self.config
                else True
            )

            if resume_confirmation:
                print(
                    Colors.system(
                        "⚠️  This will restore conversation context to the agent."
                    )
                )
                confirm = input(Colors.system("Continue? (y/n): "))
                if confirm.lower() != "y":
                    print(Colors.system("Resume cancelled"))
                    return False

            # Replay strategy: Silent replay of all queries
            print(Colors.system(f"\nReplaying {len(conversation)} previous queries..."))
            print(Colors.system("(This restores the agent's context)"))

            replay_start = time.time()

            for i, entry in enumerate(conversation, 1):
                query = entry["query"]
                # Display progress every 5 queries
                if i % 5 == 0 or i == len(conversation):
                    print(
                        Colors.system(f"  Progress: {i}/{len(conversation)} queries"),
                        end="\r",
                    )

                try:
                    # Replay query silently (don't display response)
                    # Check if agent supports streaming
                    if hasattr(self.agent, "stream_async"):
                        # Consume the stream but don't display
                        async for _ in self.agent.stream_async(query):
                            pass
                    else:
                        # Non-streaming agent
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.agent, query
                        )

                except Exception as e:
                    logger.warning(f"Error replaying query {i}: {e}")
                    # Continue with next query

            replay_duration = time.time() - replay_start
            print()  # Clear progress line
            print(
                Colors.success(
                    f"✓ Replayed {len(conversation)} queries in {replay_duration:.1f}s"
                )
            )

            # Restore conversation history
            self.conversation_history = conversation.copy()

            # Update session ID to continue this session
            self.session_id = session_id

            # Restore token tracker state
            if session_info.total_tokens > 0:
                # Approximate token restoration (not exact, but close)
                # We can't perfectly restore because we don't have per-query tokens
                # But we can set the total
                self.token_tracker.total_input_tokens = int(
                    session_info.total_tokens * 0.6
                )
                self.token_tracker.total_output_tokens = int(
                    session_info.total_tokens * 0.4
                )

            # Update query count
            self.query_count = len(conversation)

            # Display confirmation
            self.display_manager.display_session_loaded(session_info, len(conversation))

            logger.info(f"Successfully restored session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore session: {e}", exc_info=True)
            print(Colors.error(f"\n⚠️  Failed to restore session: {e}"))
            return False

    def save_conversation(self) -> bool:
        """
        Save conversation history using SessionManager.

        Saves both JSON (for resume) and markdown (for humans) formats.

        Returns:
            True if save was successful, False otherwise
        """
        # Only save if there's conversation history
        if not self.conversation_history:
            logger.debug("No conversation history to save")
            return False

        try:
            # Calculate total cost for metadata
            total_cost = self.token_tracker.get_cost()
            session_duration = time.time() - self.session_start_time

            metadata = {
                "total_cost": total_cost,
                "duration": session_duration,
            }

            # Use SessionManager to save
            success, message = self.session_manager.save_session(
                session_id=self.session_id,
                agent_name=self.agent_name,
                agent_path=self.agent_path,
                agent_description=self.agent_description,
                conversation=self.conversation_history,
                metadata=metadata,
            )

            if success:
                logger.info(f"Conversation saved: {self.session_id}")
                print(Colors.success(f"\n💾 {message}"))
                return True
            else:
                logger.warning(f"Failed to save conversation: {message}")
                print(Colors.error(f"\n⚠️  {message}"))
                return False

        except Exception as e:
            logger.warning(f"Failed to save conversation: {e}", exc_info=True)
            print(Colors.error(f"\n⚠️  Could not save conversation: {e}"))
            return False

    async def get_multiline_input(self) -> str:
        """
        Get multi-line input from user.

        Features:
        - Empty line submits
        - Ctrl+D or .cancel to cancel input
        - Up arrow or .back to edit previous line
        - Saves to history as single entry
        """
        lines: list[str] = []
        print(Colors.system("Multi-line mode:"))
        print(Colors.system("  • Empty line to submit"))
        print(Colors.system("  • Ctrl+D or .cancel to cancel"))
        if ESC_KEY_SUPPORT:
            print(Colors.system("  • ↑ or .back to edit previous line"))
        else:
            print(Colors.system("  • .back to edit previous line"))

        # Variable to hold text for pre-input hook
        prefill_text = None

        def startup_hook():
            """Readline startup hook to pre-fill input buffer."""
            nonlocal prefill_text
            if prefill_text is not None:
                readline.insert_text(prefill_text)
                readline.redisplay()

        # Set the startup hook if readline is available
        if READLINE_AVAILABLE:
            readline.set_startup_hook(startup_hook)

        try:
            while True:
                try:
                    # Show line number for context
                    line_num = len(lines) + 1
                    prompt = Colors.user(f"{line_num:2d}│ ")

                    # Use input_with_esc for ESC/arrow key detection
                    line = input_with_esc(prompt)

                    # Check if ESC was pressed (returns None)
                    if line is None:
                        print(Colors.system("✗ Multi-line input cancelled (ESC)"))
                        return ""

                    # Check if up arrow was pressed - edit previous line
                    if line == "UP_ARROW":
                        if lines:
                            # Pop the last line and let user edit it
                            prev_line = lines.pop()
                            print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                            # Set prefill text for next input
                            prefill_text = prev_line
                        else:
                            print(Colors.system("⚠ No previous line to edit"))
                        continue

                    # Clear prefill text after each input
                    prefill_text = None

                    # Check for cancel command
                    if line.strip() == ".cancel":
                        print(Colors.system("✗ Multi-line input cancelled"))
                        return ""

                    # Check for back command - edit previous line
                    if line.strip() == ".back":
                        if lines:
                            # Pop the last line and let user edit it
                            prev_line = lines.pop()
                            print(Colors.system(f"↑ Editing line {len(lines) + 1}..."))
                            # Set prefill text for next input
                            prefill_text = prev_line
                        else:
                            print(Colors.system("⚠ No previous line to edit"))
                        continue

                    # Empty line submits (only if we have content)
                    if not line.strip():
                        if lines:
                            break
                        else:
                            # First line can't be empty
                            print(Colors.system("⚠ Enter some text or use .cancel"))
                            continue

                    # Add the line
                    lines.append(line)

                except EOFError:
                    # Ctrl+D cancels
                    print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+D)"))
                    return ""
                except KeyboardInterrupt:
                    # Ctrl+C cancels
                    print(Colors.system("\n✗ Multi-line input cancelled (Ctrl+C)"))
                    return ""

            result = "\n".join(lines)

            # Save to readline history as single entry for later recall
            if result and READLINE_AVAILABLE:
                readline.add_history(result)

            print(Colors.success(f"✓ {len(lines)} lines captured"))
            return result

        finally:
            # Clean up the startup hook
            if READLINE_AVAILABLE:
                readline.set_startup_hook(None)

    async def _show_thinking_indicator(self, stop_event: asyncio.Event):
        """Show thinking indicator while waiting for response."""
        if not self.show_thinking:
            # Just wait silently
            while not stop_event.is_set():
                await asyncio.sleep(0.1)
            return

        if not self.use_rich:
            # Fallback to simple dots animation
            print(Colors.system("Thinking"), end="", flush=True)
            dot_count = 0
            while not stop_event.is_set():
                print(".", end="", flush=True)
                dot_count += 1
                if dot_count >= 3:
                    print("\b\b\b   \b\b\b", end="", flush=True)  # Clear dots
                    dot_count = 0
                await asyncio.sleep(0.5)
            print("\r" + " " * 15 + "\r", end="", flush=True)  # Clear line
        else:
            # Use rich spinner with configured style
            spinner_style = (
                self.spinner_style if hasattr(self, "spinner_style") else "dots"
            )
            with Live(
                Spinner(spinner_style, text=Colors.system("Thinking...")),
                console=self.console,
                refresh_per_second=10,
            ):
                while not stop_event.is_set():
                    await asyncio.sleep(0.1)

    async def _stream_agent_response(self, query: str) -> dict[str, Any]:
        """
        Stream agent response asynchronously.

        Returns:
            Dict with 'duration' and optional 'usage' (input_tokens, output_tokens)
        """
        start_time = time.time()
        response_text = []  # Collect response for rich rendering
        response_obj = None  # Store the response object for token extraction

        # Agent name in blue
        print(f"\n{Colors.agent(self.agent_name)}: ", end="", flush=True)

        # Setup thinking indicator
        stop_thinking = asyncio.Event()
        thinking_task = None

        try:
            # Start thinking indicator if enabled
            if self.show_thinking:
                thinking_task = asyncio.create_task(
                    self._show_thinking_indicator(stop_thinking)
                )

            first_token_received = False

            # Log request payload sent to agent
            logger.debug("=" * 60)
            logger.debug("REQUEST TO AGENT:")
            logger.debug(f"Query: {_serialize_for_logging(query)}")
            logger.debug("=" * 60)

            # Check if agent supports streaming
            if hasattr(self.agent, "stream_async"):
                async for event in self.agent.stream_async(query):
                    # Store last event for token extraction
                    response_obj = event

                    # Log streaming event received from agent
                    logger.debug("STREAMING EVENT FROM AGENT:")
                    logger.debug(_serialize_for_logging(event))

                    # Stop thinking indicator on first token
                    if not first_token_received:
                        stop_thinking.set()
                        if thinking_task:
                            await thinking_task
                        first_token_received = True

                    # Handle different event types
                    if hasattr(event, "data"):
                        data = event.data
                        if isinstance(data, str):
                            response_text.append(data)
                            if self.use_rich:
                                # Don't print during streaming, render at end
                                pass
                            else:
                                # Apply colorization for tool messages during streaming
                                formatted_data = Colors.format_agent_response(data)
                                print(formatted_data, end="", flush=True)
                        elif isinstance(data, dict):
                            # Handle structured data
                            if "text" in data:
                                text = data["text"]
                                response_text.append(text)
                                if not self.use_rich:
                                    formatted_text = Colors.format_agent_response(text)
                                    print(formatted_text, end="", flush=True)
                            elif "content" in data:
                                content = data["content"]
                                if isinstance(content, list):
                                    for block in content:
                                        if isinstance(block, dict) and "text" in block:
                                            text = block["text"]
                                            response_text.append(text)
                                            if not self.use_rich:
                                                formatted_text = (
                                                    Colors.format_agent_response(text)
                                                )
                                                print(
                                                    formatted_text, end="", flush=True
                                                )
                                else:
                                    text = str(content)
                                    response_text.append(text)
                                    if not self.use_rich:
                                        formatted_text = Colors.format_agent_response(
                                            text
                                        )
                                        print(formatted_text, end="", flush=True)
            else:
                # Fallback to synchronous call if streaming not supported
                response = await asyncio.get_event_loop().run_in_executor(
                    None, self.agent, query
                )
                response_obj = response  # Store for token extraction

                # Log response received from agent
                logger.debug("RESPONSE FROM AGENT:")
                logger.debug(_serialize_for_logging(response))
                logger.debug("=" * 60)

                # Stop thinking indicator
                stop_thinking.set()
                if thinking_task:
                    await thinking_task

                # Format and display response
                if hasattr(response, "message"):
                    message = response.message
                    if isinstance(message, dict) and "content" in message:
                        content = message["content"]
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and "text" in block:
                                    response_text.append(block["text"])
                        else:
                            response_text.append(str(content))
                    else:
                        response_text.append(str(message))
                else:
                    response_text.append(str(response))

            # Log final response object (for streaming, this is the last event)
            if hasattr(self.agent, "stream_async"):
                logger.debug("FINAL RESPONSE OBJECT (last streaming event):")
                logger.debug(_serialize_for_logging(response_obj))
                logger.debug("=" * 60)

            # Render collected response
            # Use newline separator to prevent sentences from running together
            full_response = "\n".join(response_text)

            # Process through Harmony if available
            display_text = full_response
            if self.harmony_processor:
                # Debug: Log response object structure
                logger.debug(f"Response object type: {type(response_obj)}")
                logger.debug(f"Response object attrs: {dir(response_obj)[:20]}")
                if response_obj and hasattr(response_obj, "choices"):
                    logger.debug(f"Response has choices: {len(response_obj.choices)}")
                    if response_obj.choices:
                        choice = response_obj.choices[0]
                        logger.debug(f"Choice type: {type(choice)}")
                        logger.debug(f"Choice attrs: {dir(choice)[:20]}")
                        if hasattr(choice, "logprobs"):
                            logger.debug(f"Has logprobs: {choice.logprobs is not None}")
                        if hasattr(choice, "message"):
                            logger.debug(f"Message type: {type(choice.message)}")

                processed = self.harmony_processor.process_response(
                    full_response, metadata=response_obj
                )
                display_text = self.harmony_processor.format_for_display(processed)

                # Log if Harmony-specific features detected
                if processed.get("has_reasoning"):
                    logger.debug("Harmony response contains reasoning")
                if processed.get("has_tools"):
                    logger.debug("Harmony response contains tool calls")

            # Store last response for copy commands (what user sees)
            self.last_response = display_text

            if self.use_rich and display_text.strip() and self.console:
                # Use rich markdown rendering
                print()  # New line after agent name
                md = Markdown(display_text)
                self.console.print(md)
            elif not self.use_rich and response_text:
                # Already printed during streaming, just add newline
                if not first_token_received:
                    # Non-streaming case where nothing was printed yet
                    # Apply colorization for tool messages
                    formatted_response = Colors.format_agent_response(display_text)
                    print(formatted_response)

            duration = time.time() - start_time

            # Extract token usage if available
            usage_info = self._extract_token_usage(response_obj)

            # Extract additional metrics (framework-specific)
            cycle_count = None
            tool_count = None
            if isinstance(response_obj, dict) and "result" in response_obj:
                result = response_obj["result"]
                if hasattr(result, "metrics"):
                    metrics = result.metrics
                    if hasattr(metrics, "cycle_count"):
                        cycle_count = metrics.cycle_count
                    if hasattr(metrics, "tool_metrics") and metrics.tool_metrics:
                        # Count total tool calls across all tools
                        try:
                            if isinstance(metrics.tool_metrics, dict):
                                tool_count = sum(
                                    len(calls)
                                    for calls in metrics.tool_metrics.values()
                                )
                            elif hasattr(metrics.tool_metrics, "__len__"):
                                tool_count = len(metrics.tool_metrics)
                            elif hasattr(metrics.tool_metrics, "__dict__"):
                                # ToolMetrics object - count attributes
                                # that look like tool calls
                                tool_count = len(
                                    [
                                        k
                                        for k in metrics.tool_metrics.__dict__.keys()
                                        if not k.startswith("_")
                                    ]
                                )
                        except Exception as e:
                            logger.debug(f"Could not extract tool count: {e}")
                            tool_count = None

            # Track tokens (always, for session summary)
            if usage_info:
                self.token_tracker.add_usage(
                    usage_info["input_tokens"], usage_info["output_tokens"]
                )

                # Update status bar
                if self.status_bar:
                    self.status_bar.update_tokens(self.token_tracker.get_total_tokens())

            # Increment query count for session summary
            self.query_count += 1

            # Display duration and token info
            # Determine what to show
            show_info_line = (
                self.show_duration
                or (self.show_tokens and usage_info)
                or cycle_count
                or tool_count
            )

            if show_info_line:
                print(f"\n{Colors.DIM}{'-' * 60}{Colors.RESET}")

                info_parts = []
                if self.show_duration:
                    info_parts.append(f"Time: {duration:.1f}s")

                # Show agent metrics (cycles, tools) - always show if available
                if cycle_count is not None and cycle_count > 0:
                    cycle_word = "cycle" if cycle_count == 1 else "cycles"
                    info_parts.append(f"{cycle_count} {cycle_word}")

                if tool_count is not None and tool_count > 0:
                    tool_word = "tool" if tool_count == 1 else "tools"
                    info_parts.append(f"{tool_count} {tool_word}")

                # Only show tokens if show_tokens is enabled
                if self.show_tokens and usage_info:
                    input_tok = usage_info["input_tokens"]
                    output_tok = usage_info["output_tokens"]
                    total_tok = input_tok + output_tok

                    # Format tokens
                    token_str = (
                        f"Tokens: {self.token_tracker.format_tokens(total_tok)} "
                    )
                    token_str += f"(in: {self.token_tracker.format_tokens(input_tok)}, "
                    token_str += f"out: {self.token_tracker.format_tokens(output_tok)})"
                    info_parts.append(token_str)

                    # Show cost (session total)
                    cost = self.token_tracker.get_cost()
                    if cost > 0:
                        info_parts.append(f"Cost: {self.token_tracker.format_cost()}")

                if info_parts:  # Only print if we have something to show
                    print(Colors.system(" │ ".join(info_parts)))

            logger.info(f"Query completed successfully in {duration:.1f}s")

            # Track conversation for auto-save if enabled
            if self.auto_save:
                self.conversation_history.append(
                    {
                        "timestamp": time.time(),
                        "query": query,
                        # Save what user sees (includes harmony formatting)
                        "response": display_text,
                        "duration": duration,
                        "usage": usage_info,
                    }
                )

            # Play audio notification on agent turn completion
            self.audio_notifier.play()

            return {"duration": duration, "usage": usage_info}

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(Colors.error(f"{self.agent_name}: Query failed - {e}"))
            print(
                Colors.system(
                    "Try rephrasing your question or check the logs for details."
                )
            )
            logger.error(
                f"Agent query failed after {duration:.1f}s: {e}", exc_info=True
            )

            return {"duration": duration, "usage": None}

        finally:
            # Always cleanup thinking indicator, even on KeyboardInterrupt
            stop_thinking.set()
            if thinking_task and not thinking_task.done():
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling

    async def process_query(self, query: str):
        """Process query through agent with streaming and error recovery."""
        for attempt in range(1, self.max_retries + 1):
            try:
                await self._stream_agent_response(query)
                return  # Success, exit retry loop

            except asyncio.TimeoutError:
                print(
                    Colors.error(f"\n⚠️  Timeout (attempt {attempt}/{self.max_retries})")
                )
                if attempt < self.max_retries:
                    print(Colors.system(f"Retrying in {self.retry_delay}s..."))
                    await asyncio.sleep(self.retry_delay)
                    logger.warning(f"Timeout on attempt {attempt}, retrying...")
                else:
                    print(Colors.error("Max retries reached. Please try again later."))
                    logger.error("Max retries reached after timeout")

            except ConnectionError as e:
                print(Colors.error(f"\n⚠️  Connection error: {e}"))
                if attempt < self.max_retries:
                    print(Colors.system(f"Retrying in {self.retry_delay}s..."))
                    await asyncio.sleep(self.retry_delay)
                    logger.warning(
                        f"Connection error on attempt {attempt}, retrying..."
                    )
                else:
                    print(
                        Colors.error(
                            "Max retries reached. Check your network connection."
                        )
                    )
                    logger.error(f"Max retries reached after connection error: {e}")

            except Exception as e:
                # For other exceptions, don't retry - they're likely not transient
                error_msg = str(e)

                # Check for rate limit errors
                if "rate" in error_msg.lower() or "429" in error_msg:
                    print(Colors.error("\n⚠️  Rate limit reached"))
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (
                            2 ** (attempt - 1)
                        )  # Exponential backoff
                        print(
                            Colors.system(f"Waiting {wait_time:.0f}s before retry...")
                        )
                        await asyncio.sleep(wait_time)
                        logger.warning(
                            f"Rate limit on attempt {attempt}, backing off..."
                        )
                    else:
                        print(
                            Colors.error(
                                "Rate limit persists. Please wait and try again."
                            )
                        )
                        logger.error("Max retries reached due to rate limiting")
                else:
                    # Non-retryable error, log and exit
                    logger.error(f"Non-retryable error: {e}", exc_info=True)
                    raise

    async def _async_run(self):
        """Async implementation of the chat loop."""
        # Setup readline history
        self.history_file = setup_readline_history()

        # Set initial terminal title
        if self.update_terminal_title:
            set_terminal_title(f"{self.agent_name} - Idle")

        self.display_manager.display_banner()

        # Handle --resume flag if specified
        if hasattr(self, "resume_session_ref") and self.resume_session_ref:
            session_ref = self.resume_session_ref

            # If "pick" mode, show session picker
            if session_ref == "pick":
                sessions = self.session_manager.list_sessions(
                    agent_name=self.agent_name, limit=20
                )

                if not sessions:
                    print(Colors.system("\nNo saved sessions found to resume."))
                    print("Continue with fresh session...\n")
                else:
                    self.display_manager.display_sessions(
                        sessions, agent_name=self.agent_name
                    )
                    print()
                    try:
                        prompt = (
                            "Enter session number to resume (or press Enter to skip): "
                        )
                        choice = input(Colors.system(prompt)).strip()

                        if choice:
                            success = await self.restore_session(choice)
                            if success:
                                # Clear and redisplay banner after resume
                                self.display_manager.display_banner()
                    except (KeyboardInterrupt, EOFError):
                        print()
                        print(
                            Colors.system("Skipping resume, starting fresh session...")
                        )
                        print()
            else:
                # Direct resume with specific session ID/number
                success = await self.restore_session(session_ref)
                if success:
                    # Clear and redisplay banner after resume
                    self.display_manager.display_banner()
                else:
                    print(Colors.system("\nContinuing with fresh session...\n"))

        try:
            while True:
                try:
                    # Get user input directly (blocking is fine for user input)
                    # Don't use executor as it breaks readline editing
                    user_input = input(f"\n{Colors.user('You')}: ").strip()

                    # Handle commands
                    if user_input.lower() in ["exit", "quit", "bye"]:
                        print(
                            Colors.system(
                                f"\nGoodbye! Thanks for using {self.agent_name}!"
                            )
                        )
                        break
                    elif user_input.lower() == "help":
                        self.display_manager.display_help()
                        continue
                    elif user_input.lower() == "info":
                        self.display_manager.display_info()
                        continue
                    elif user_input.lower() == "templates":
                        # List available prompt templates
                        templates = (
                            self.template_manager.list_templates_with_descriptions()
                        )
                        self.display_manager.display_templates(
                            templates, self.prompts_dir
                        )
                        continue
                    elif user_input.lower() == "sessions":
                        # List saved sessions
                        sessions = self.session_manager.list_sessions(
                            agent_name=self.agent_name, limit=20
                        )
                        self.display_manager.display_sessions(
                            sessions, agent_name=self.agent_name
                        )
                        continue
                    elif user_input.lower().startswith("copy"):
                        # Copy command with variants
                        parts = user_input.lower().split(maxsplit=1)
                        copy_mode = parts[1] if len(parts) > 1 else ""

                        try:
                            content = None
                            description = ""

                            if copy_mode == "query":
                                # Copy last user query
                                if self.last_query:
                                    content = self.last_query
                                    description = "last query"
                                else:
                                    print(Colors.system("No query to copy yet"))
                                    continue
                            elif copy_mode == "all":
                                # Copy entire conversation as markdown
                                if self.conversation_history:
                                    content = self._format_conversation_as_markdown()
                                    description = "entire conversation"
                                else:
                                    print(Colors.system("No conversation to copy yet"))
                                    continue
                            elif copy_mode == "code":
                                # Copy just code blocks from last response
                                if self.last_response:
                                    code_blocks = self._extract_code_blocks(
                                        self.last_response
                                    )
                                    if code_blocks:
                                        content = "\n\n".join(code_blocks)
                                        description = "code blocks from last response"
                                    else:
                                        print(
                                            Colors.system(
                                                "No code blocks found in last response"
                                            )
                                        )
                                        continue
                                else:
                                    print(Colors.system("No response to copy yet"))
                                    continue
                            else:
                                # Default: copy last response
                                if self.last_response:
                                    content = self.last_response
                                    description = "last response"
                                else:
                                    print(Colors.system("No response to copy yet"))
                                    continue

                            # Copy to clipboard
                            pyperclip.copy(content)
                            print(
                                Colors.success(f"✓ Copied {description} to clipboard")
                            )

                        except Exception as e:
                            print(Colors.error(f"Failed to copy: {e}"))
                            logger.error(f"Copy command failed: {e}")
                        continue
                    elif user_input.lower().startswith("resume "):
                        # Resume a previous session
                        parts = user_input.split(maxsplit=1)
                        if len(parts) < 2:
                            print(Colors.error("Usage: resume <session_id or number>"))
                            print("Use 'sessions' command to see available sessions")
                            continue

                        session_ref = parts[1].strip()
                        success = await self.restore_session(session_ref)

                        if success:
                            # Show banner after resume
                            self.display_manager.display_banner()
                        continue
                    elif user_input.startswith("/") and len(user_input) > 1:
                        # Template command: /template_name <optional input>
                        parts = user_input[1:].split(maxsplit=1)
                        template_name = parts[0]
                        input_text = parts[1] if len(parts) > 1 else ""

                        # Try to load template
                        template = self.template_manager.load_template(
                            template_name, input_text
                        )
                        if template:
                            print(Colors.system(f"✓ Loaded template: {template_name}"))
                            # Use the template as the user input
                            user_input = template
                        else:
                            print(Colors.error(f"Template not found: {template_name}"))
                            templates = self.template_manager.list_templates()
                            tmpl_list = ", ".join(templates) or "none"
                            print(f"Available templates: {tmpl_list}")
                            print(f"Create at: {self.prompts_dir}/{template_name}.md")
                            continue
                    elif user_input.lower() == "clear":
                        # Clear screen (cross-platform)
                        os.system("clear" if os.name != "nt" else "cls")

                        # Reset agent session if factory available
                        if self.agent_factory:
                            try:
                                # Cleanup old agent if possible
                                if hasattr(self.agent, "cleanup"):
                                    try:
                                        if asyncio.iscoroutinefunction(
                                            self.agent.cleanup
                                        ):
                                            await self.agent.cleanup()
                                        else:
                                            self.agent.cleanup()
                                    except Exception as e:
                                        logger.debug(f"Error during agent cleanup: {e}")

                                # Create fresh agent instance
                                self.agent = self.agent_factory()
                                print(
                                    Colors.success(
                                        "✓ Screen cleared and agent session reset"
                                    )
                                )
                                logger.info("Agent session reset via clear command")
                            except Exception as e:
                                print(
                                    Colors.error(
                                        f"⚠️  Could not reset agent session: {e}"
                                    )
                                )
                                logger.error(f"Failed to reset agent session: {e}")
                                print(
                                    Colors.system(
                                        "Screen cleared but agent session maintained"
                                    )
                                )
                        else:
                            print(Colors.success("✓ Screen cleared"))

                        self.display_manager.display_banner()
                        continue
                    elif user_input == "\\\\":  # Multi-line input trigger
                        user_input = await self.get_multiline_input()
                        if not user_input.strip():
                            continue
                    elif not user_input:
                        continue

                    # Process query through agent
                    logger.info(f"Processing query: {user_input[:100]}...")

                    # Track query for copy command
                    self.last_query = user_input

                    # Update terminal title to show processing
                    if self.update_terminal_title:
                        set_terminal_title(f"{self.agent_name} - Processing...")

                    # Update status bar before query
                    if self.status_bar:
                        self.status_bar.increment_query()
                        # Clear screen and redraw status bar
                        print("\033[2J\033[H", end="")  # Clear screen, move to top
                        print(self.status_bar.render())
                        print()  # Blank line after status bar

                    await self.process_query(user_input)

                    # Update terminal title back to idle
                    if self.update_terminal_title:
                        set_terminal_title(f"{self.agent_name} - Idle")

                except KeyboardInterrupt:
                    print(
                        Colors.system(
                            f"\n\nChat interrupted. Thanks for using {self.agent_name}!"
                        )
                    )
                    break
                except EOFError:
                    print(
                        Colors.system(
                            f"\n\nChat ended. Thanks for using {self.agent_name}!"
                        )
                    )
                    break

        finally:
            # Reset terminal title
            if self.update_terminal_title:
                set_terminal_title("Terminal")

            # Save command history
            save_readline_history(self.history_file)

            # Save conversation if auto-save is enabled
            if self.auto_save:
                self.save_conversation()

            # Cleanup agent if it has cleanup method
            if hasattr(self.agent, "cleanup"):
                try:
                    if asyncio.iscoroutinefunction(self.agent.cleanup):
                        await self.agent.cleanup()
                    else:
                        self.agent.cleanup()
                except Exception as e:
                    logger.warning(f"Error during agent cleanup: {e}")

            # Display session summary
            self.display_manager.display_session_summary(
                self.session_start_time, self.query_count, self.token_tracker
            )

            print(Colors.success(f"\n{self.agent_name} session complete!"))

    def run(self):
        """Run the interactive chat loop."""
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            print(f"\n\nChat interrupted. Thanks for using {self.agent_name}!")
        except Exception as e:
            logger.error(f"Fatal error in chat loop: {e}", exc_info=True)
            print(f"\nFatal error: {e}")


def main():
    """Main entry point for the chat loop."""
    parser = argparse.ArgumentParser(
        description=(
            "Interactive CLI for AI Agents with token tracking and rich features"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with agent path
    chat_loop path/to/agent.py

    # Run with alias
    chat_loop my_agent

    # Auto-install dependencies
    chat_loop my_agent --auto-setup
    chat_loop path/to/agent.py -a

    # Configuration
    chat_loop --wizard              # Create/customize .chatrc
    chat_loop --reset-config        # Reset .chatrc to defaults

    # Alias management
    chat_loop --save-alias my_agent path/to/agent.py
    chat_loop --list-aliases
    chat_loop --remove-alias my_agent
        """,
    )

    # Import version for --version flag
    try:
        from . import __version__

        version_string = f"%(prog)s {__version__}"
    except ImportError:
        version_string = "%(prog)s (version unknown)"

    parser.add_argument(
        "--version",
        action="version",
        version=version_string,
    )

    parser.add_argument("agent", nargs="?", help="Agent path or alias name")

    parser.add_argument(
        "--config", help="Path to configuration file (default: ~/.chatrc or .chatrc)"
    )

    # Alias management commands
    alias_group = parser.add_argument_group("alias management")

    alias_group.add_argument(
        "--save-alias",
        nargs=2,
        metavar=("ALIAS", "PATH"),
        help="Save an agent alias: --save-alias pete path/to/agent.py",
    )

    alias_group.add_argument(
        "--list-aliases", action="store_true", help="List all saved aliases"
    )

    alias_group.add_argument(
        "--remove-alias", metavar="ALIAS", help="Remove an alias: --remove-alias pete"
    )

    alias_group.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing alias when using --save-alias",
    )

    # Dependency management
    parser.add_argument(
        "--auto-setup",
        "-a",
        action="store_true",
        help=(
            "Automatically install agent dependencies "
            "(requirements.txt, pyproject.toml)"
        ),
    )

    # Session management
    session_group = parser.add_argument_group("session management")

    session_group.add_argument(
        "--resume",
        "-r",
        nargs="?",
        const="pick",
        metavar="SESSION",
        help=(
            "Resume a previous session (optionally specify session ID or number, "
            "otherwise shows picker)"
        ),
    )

    session_group.add_argument(
        "--list-sessions",
        action="store_true",
        help="List all saved sessions and exit",
    )

    # Configuration wizard
    parser.add_argument(
        "--wizard",
        "-w",
        action="store_true",
        help="Run interactive configuration wizard to create .chatrc file",
    )

    parser.add_argument(
        "--reset-config",
        action="store_true",
        help="Reset .chatrc file to default values",
    )

    args = parser.parse_args()

    # Handle configuration wizard
    if args.wizard:
        wizard = ConfigWizard()
        config_path = wizard.run()
        if config_path:
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle config reset
    if args.reset_config:
        from .components.config_wizard import reset_config_to_defaults

        config_path = reset_config_to_defaults()
        if config_path:
            sys.exit(0)
        else:
            sys.exit(1)

    # Handle alias management commands
    alias_manager = AliasManager()

    if args.save_alias:
        alias_name, agent_path = args.save_alias
        success, message = alias_manager.add_alias(
            alias_name, agent_path, overwrite=args.overwrite
        )
        if success:
            print(Colors.success(message))
            sys.exit(0)
        else:
            print(Colors.error(message))
            sys.exit(1)

    if args.list_aliases:
        aliases = alias_manager.list_aliases()
        if aliases:
            print(f"\n{Colors.system('Saved Agent Aliases')} ({len(aliases)}):")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            for alias_name, agent_path in sorted(aliases.items()):
                # Check if path still exists
                if Path(agent_path).exists():
                    print(f"  {Colors.success(alias_name):<20} → {agent_path}")
                else:
                    status = f"{Colors.YELLOW}(missing){Colors.RESET}"
                    print(f"  {Colors.error(alias_name):<20} → {agent_path} {status}")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(f"\nUsage: {Colors.system('chat_loop <alias>')}")
        else:
            print(f"\n{Colors.system('No aliases saved yet')}")
            print("\nCreate an alias with:")
            print(f"  {Colors.system('chat_loop --save-alias <name> <path>')}")
        sys.exit(0)

    if args.remove_alias:
        success, message = alias_manager.remove_alias(args.remove_alias)
        if success:
            print(Colors.success(message))
            sys.exit(0)
        else:
            print(Colors.error(message))
            sys.exit(1)

    # Handle session management commands
    if args.list_sessions:
        # List sessions and exit
        config = get_config(config_path=args.config) if args.config else get_config()
        sessions_dir = (
            config.expand_path(
                config.get("paths.save_location", "~/agent-conversations")
            )
            if config
            else Path.home() / "agent-conversations"
        )

        session_manager = SessionManager(sessions_dir=sessions_dir)
        sessions = session_manager.list_sessions(limit=50)

        if sessions:
            print(f"\n{Colors.system('Saved Sessions')} ({len(sessions)}):")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            for i, session in enumerate(sessions, 1):
                created_str = session.created.strftime("%b %d, %Y %H:%M")
                session_line = f"  {i:2}. {session.agent_name:<20} {created_str}"
                session_line += f"  {session.query_count:3} queries"
                if session.total_cost > 0:
                    session_line += f"  ${session.total_cost:.2f}"
                print(session_line)
                preview_text = f'      "{session.preview}"'
                print(f"{Colors.DIM}{preview_text}{Colors.RESET}")

            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(f"\nResume: {Colors.system('chat_loop <agent> --resume <number>')}")
            print(f"        {Colors.system('chat_loop <agent> --resume <session_id>')}")
        else:
            print(f"\n{Colors.system('No saved sessions found')}")
            print(f"Sessions will be saved to: {sessions_dir}")

        sys.exit(0)

    # Require agent argument if not doing alias management
    if not args.agent:
        print(Colors.error("Error: Agent path or alias required"))
        print()
        print("Usage:")
        print(f"  {Colors.system('chat_loop <agent_path>')}")
        print(f"  {Colors.system('chat_loop <alias>')}")
        print()
        print("Alias Management:")
        print(f"  {Colors.system('chat_loop --save-alias <name> <path>')}")
        print(f"  {Colors.system('chat_loop --list-aliases')}")
        print(f"  {Colors.system('chat_loop --remove-alias <name>')}")
        sys.exit(1)

    # Resolve agent path (try as path first, then as alias)
    agent_path = alias_manager.resolve_agent_path(args.agent)

    if not agent_path:
        print(Colors.error(f"Error: Agent not found: {args.agent}"))
        print()
        print("Not found as:")
        print(f"  • File path: {args.agent}")
        print(f"  • Alias name: {args.agent}")
        print()
        print("Available aliases:")
        aliases = alias_manager.list_aliases()
        if aliases:
            for alias_name in sorted(aliases.keys()):
                print(f"  • {alias_name}")
        else:
            print("  (none)")
        sys.exit(1)

    # Handle dependency installation if requested
    dep_manager = DependencyManager(agent_path)

    if args.auto_setup:
        # User explicitly requested dependency installation
        dep_info = dep_manager.detect_dependency_file()
        if dep_info:
            file_type, file_path = dep_info
            print(
                Colors.system(f"📦 Found {file_path.name}, installing dependencies...")
            )
            success, message = dep_manager.install_dependencies(file_type, file_path)
            if success:
                print(Colors.success(message))
            else:
                print(Colors.error(message))
                print(Colors.system("\nContinuing without dependency installation..."))
        else:
            msg = (
                "💡 No dependency files found "
                "(requirements.txt, pyproject.toml, setup.py)"
            )
            print(Colors.system(msg))
    else:
        # Check if dependencies exist and suggest using --auto-setup
        suggestion = dep_manager.suggest_auto_setup()
        if suggestion:
            print(Colors.system(suggestion))
            print()  # Extra spacing

    try:
        # Load configuration FIRST (before any print statements)
        config = None
        config_path = Path(args.config) if args.config else None
        config = get_config(config_path)

        # Apply color configuration immediately
        if config:
            color_config = config.get_section("colors")
            Colors.configure(color_config)

        # Show config info
        if config:
            if args.config:
                print(Colors.system(f"Loaded configuration from: {args.config}"))
            else:
                # Check which config file was loaded
                global_config = Path.home() / ".chatrc"
                project_config = Path.cwd() / ".chatrc"
                if project_config.exists():
                    print(Colors.system(f"Loaded configuration from: {project_config}"))
                elif global_config.exists():
                    print(Colors.system(f"Loaded configuration from: {global_config}"))

        # Load the agent
        # Show what we're loading (path or alias)
        if agent_path != args.agent:
            print(Colors.system(f"Resolved alias '{args.agent}' → {agent_path}"))
        print(Colors.system(f"Loading agent from: {agent_path}"))
        agent, agent_name, agent_description = load_agent_module(agent_path)

        # Setup logging with agent name
        setup_logging(agent_name)

        print(Colors.success(f"Agent loaded successfully: {agent_name}"))
        logger.info(f"Agent loaded successfully: {agent_name} - {agent_description}")

        # Create agent factory for session reset
        def create_fresh_agent():
            """Factory function to create a fresh agent instance."""
            new_agent, _, _ = load_agent_module(agent_path)
            return new_agent

        # Start chat loop with config
        chat_loop = ChatLoop(
            agent,
            agent_name,
            agent_description,
            agent_factory=create_fresh_agent,
            agent_path=str(agent_path),
            config=config,
        )

        # Handle --resume flag if provided
        if args.resume:
            # Store resume session for processing in _async_run
            chat_loop.resume_session_ref = args.resume
        else:
            chat_loop.resume_session_ref = None

        chat_loop.run()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
