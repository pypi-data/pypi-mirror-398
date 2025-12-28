"""
UI Components for terminal display.

Contains terminal color codes and status bar rendering.
"""

import time

# Named color palette - maps color names to ANSI escape codes
COLOR_PALETTE = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_blue": "\033[94m",
    "bright_white": "\033[97m",
}


class Colors:
    """ANSI color codes for terminal output."""

    # Default colors (can be overridden by config)
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Text colors - these will be updated from config
    USER = "\033[97m"  # Bright white for user input (maximum contrast)
    AGENT = "\033[94m"  # Bright blue for agent
    SYSTEM = "\033[33m"  # Yellow for system messages
    ERROR = "\033[91m"  # Bright red for errors
    SUCCESS = "\033[92m"  # Bright green for success

    @classmethod
    def _resolve_color(cls, color_value: str) -> str:
        """
        Resolve a color name or ANSI code to an ANSI escape sequence.

        Args:
            color_value: Color name (e.g., 'bright_green') or ANSI code
                (e.g., '\\033[92m')

        Returns:
            ANSI escape sequence
        """
        # If it's a named color, look it up in the palette
        if color_value in COLOR_PALETTE:
            return COLOR_PALETTE[color_value]
        # Otherwise, assume it's already an ANSI code (backward compatibility)
        return color_value

    @classmethod
    def configure(cls, config: dict[str, str]):
        """
        Configure colors from config dictionary.

        Args:
            config: Dictionary of color names or ANSI codes
        """
        cls.USER = cls._resolve_color(config.get("user", cls.USER))
        cls.AGENT = cls._resolve_color(config.get("agent", cls.AGENT))
        cls.SYSTEM = cls._resolve_color(config.get("system", cls.SYSTEM))
        cls.ERROR = cls._resolve_color(config.get("error", cls.ERROR))
        cls.SUCCESS = cls._resolve_color(config.get("success", cls.SUCCESS))
        cls.DIM = cls._resolve_color(config.get("dim", cls.DIM))
        cls.RESET = cls._resolve_color(config.get("reset", cls.RESET))

    @staticmethod
    def user(text: str) -> str:
        """Format text as user input."""
        return f"{Colors.USER}{text}{Colors.RESET}"

    @staticmethod
    def agent(text: str) -> str:
        """Format text as agent response."""
        return f"{Colors.AGENT}{text}{Colors.RESET}"

    @staticmethod
    def system(text: str) -> str:
        """Format text as system message."""
        return f"{Colors.SYSTEM}{text}{Colors.RESET}"

    @staticmethod
    def error(text: str) -> str:
        """Format text as error."""
        return f"{Colors.ERROR}{text}{Colors.RESET}"

    @staticmethod
    def success(text: str) -> str:
        """Format text as success."""
        return f"{Colors.SUCCESS}{text}{Colors.RESET}"

    @staticmethod
    def format_agent_response(text: str) -> str:
        """
        Format agent response text with special colorization for tool messages.

        Lines starting with '[' or 'Tool #' are colored bright_green.
        Other lines use the standard agent color.

        Args:
            text: Agent response text (may contain multiple lines)

        Returns:
            Formatted text with color codes
        """
        lines = text.split("\n")
        formatted_lines = []

        for line in lines:
            # Check if line starts with '[' or 'Tool #'
            if line.startswith("[") or line.startswith("Tool #"):
                # Use bright_green for tool/thinking messages
                formatted_lines.append(
                    f"{COLOR_PALETTE['bright_green']}{line}{Colors.RESET}"
                )
            else:
                # Use standard agent color
                formatted_lines.append(f"{Colors.AGENT}{line}{Colors.RESET}")

        return "\n".join(formatted_lines)


class StatusBar:
    """Simple status bar for chat loop."""

    # Token display formatting thresholds
    TOKEN_THOUSANDS_THRESHOLD = 1_000
    TOKEN_MILLIONS_THRESHOLD = 1_000_000

    def __init__(self, agent_name: str, model_info: str, show_tokens: bool = False):
        """
        Initialize status bar.

        Args:
            agent_name: Name of the agent
            model_info: Model identifier string
            show_tokens: Whether to show token count
        """
        self.agent_name = agent_name
        self.model_info = model_info
        self.query_count = 0
        self.start_time = time.time()
        self.show_tokens = show_tokens
        self.total_tokens = 0

    def get_session_time(self) -> str:
        """Get formatted session time."""
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def increment_query(self):
        """Increment query counter."""
        self.query_count += 1

    def update_tokens(self, total_tokens: int):
        """Update total token count."""
        self.total_tokens = total_tokens

    def render(self) -> str:
        """
        Render status bar as string.

        Returns:
            Formatted status bar string
        """
        session_time = self.get_session_time()
        queries_text = "query" if self.query_count == 1 else "queries"

        # Build status line
        parts = [
            self.agent_name,
            self.model_info,
        ]

        # Add tokens if enabled and available
        if self.show_tokens and self.total_tokens > 0:
            if self.total_tokens >= self.TOKEN_MILLIONS_THRESHOLD:
                token_str = (
                    f"{self.total_tokens / self.TOKEN_MILLIONS_THRESHOLD:.1f}M tokens"
                )
            elif self.total_tokens >= self.TOKEN_THOUSANDS_THRESHOLD:
                token_str = (
                    f"{self.total_tokens / self.TOKEN_THOUSANDS_THRESHOLD:.1f}K tokens"
                )
            else:
                token_str = f"{self.total_tokens} tokens"
            parts.append(token_str)

        parts.extend([f"{self.query_count} {queries_text}", session_time])

        status_line = " │ ".join(parts)
        width = len(status_line) + 4  # Padding

        # Create bordered status bar
        top = "┌" + "─" * (width - 2) + "┐"
        middle = f"│ {status_line} │"
        bottom = "└" + "─" * (width - 2) + "┘"

        return f"{top}\n{middle}\n{bottom}"
