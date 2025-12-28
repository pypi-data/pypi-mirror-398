"""
Display and output formatting.

Handles all display methods including banner, help, info, and session summary.
"""

import time
from pathlib import Path
from typing import Any, Optional

from .token_tracker import TokenTracker
from .ui_components import Colors

# Check for readline availability
try:
    import readline  # noqa: F401

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False


class DisplayManager:
    """Manage all display and output formatting."""

    def __init__(
        self,
        agent_name: str,
        agent_description: str,
        agent_metadata: Optional[dict[str, Any]] = None,
        show_banner: bool = True,
        show_metadata: bool = False,
        use_rich: bool = False,
        auto_save: bool = False,
        config: Any = None,
        status_bar: Any = None,
    ):
        """
        Initialize display manager.

        Args:
            agent_name: Name of the agent
            agent_description: Agent description
            agent_metadata: Agent metadata dict
            show_banner: Whether to show banner
            show_metadata: Whether to show metadata in banner
            use_rich: Whether rich formatting is enabled
            auto_save: Whether auto-save is enabled
            config: Configuration object
            status_bar: StatusBar instance
        """
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_metadata = agent_metadata or {}
        self.show_banner = show_banner
        self.show_metadata = show_metadata
        self.use_rich = use_rich
        self.auto_save = auto_save
        self.config = config
        self.status_bar = status_bar

    def display_banner(self):
        """Display agent banner and help."""
        if not self.show_banner:
            return

        # Show status bar if enabled
        if self.status_bar:
            print(f"\n{self.status_bar.render()}")

        print(f"\n{self.agent_name.upper()} - Interactive Chat")
        print("=" * 60)
        print(f"Welcome to {self.agent_name}!")
        print(f"{self.agent_description}")

        # Display agent metadata if enabled and available
        if self.show_metadata and self.agent_metadata:
            print()
            print(Colors.DIM + "Agent Configuration:" + Colors.RESET)

            # Use status bar model if available (it has overrides applied)
            if self.status_bar and self.status_bar.model_info:
                print(f"  Model: {self.status_bar.model_info}")
            elif "model_id" in self.agent_metadata:
                print(f"  Model: {self.agent_metadata['model_id']}")

            if (
                "max_tokens" in self.agent_metadata
                and self.agent_metadata["max_tokens"] != "Unknown"
            ):
                print(f"  Max Tokens: {self.agent_metadata['max_tokens']}")

            if (
                "tool_count" in self.agent_metadata
                and self.agent_metadata["tool_count"] > 0
            ):
                tool_count = self.agent_metadata["tool_count"]
                print(f"  Tools: {tool_count} available")

        print()
        print("Commands:")
        print("  help      - Show this help message")
        print("  info      - Show detailed agent information")
        print("  templates - List available prompt templates")
        print("  sessions  - List saved conversation sessions")
        print("  /name     - Use prompt template from ~/.prompts/name.md")
        print("  resume <#>- Resume a previous session by number or ID")
        print("  copy      - Copy last response to clipboard")
        print("  clear     - Clear screen and reset agent session")
        print("  quit      - Exit the chat")
        print("  exit      - Exit the chat")
        print()
        print("Features:")
        if READLINE_AVAILABLE:
            print("  ↑↓        - Navigate command history")
        print("  Enter     - Submit single line")
        print("  \\\\        - Start multi-line input")
        print(
            "              (empty line submits, Ctrl+D cancels, ↑ edits previous line)"
        )
        if self.use_rich:
            print("  Rich      - Enhanced markdown rendering with syntax highlighting")

        # Show config info if config loaded
        if self.config:
            print()
            print(Colors.DIM + "Configuration loaded" + Colors.RESET)
            if self.auto_save:
                save_loc = self.config.get(
                    "paths.save_location",
                    "~/agent-conversations",
                    agent_name=self.agent_name,
                )
                print(f"  Auto-save: enabled → {save_loc}")

        print("=" * 60)

    def display_help(self):
        """Display help information."""
        print(f"\n{self.agent_name.upper()} - Help")
        print("=" * 50)
        print(f"Agent: {self.agent_name}")
        print(f"Description: {self.agent_description}")
        print()
        print("Commands:")
        print("  help      - Show this help message")
        print("  info      - Show detailed agent information")
        print("  templates - List available prompt templates")
        print("  sessions  - List saved conversation sessions")
        print("  /name     - Use prompt template from ~/.prompts/name.md")
        print("  resume <#>- Resume a previous session by number or ID")
        print("  copy      - Copy last response to clipboard")
        print("  clear     - Clear screen and reset agent session")
        print("  quit      - Exit the chat")
        print("  exit      - Exit the chat")
        print()
        print("Session Management:")
        print("  sessions  - See all saved conversations")
        print("  resume 1  - Resume session by number from list")
        print("  resume ID - Resume session by full ID")
        print("  Auto-save - Enabled with --auto-save or in config")
        print()
        print("Copy Commands:")
        print("  copy       - Copy last response to clipboard")
        print("  copy query - Copy your last query")
        print("  copy all   - Copy entire conversation as markdown")
        print("  copy code  - Copy code blocks from last response")
        print()
        print("Prompt Templates:")
        print("  Create: Save markdown files to ~/.prompts/name.md")
        print("  Use: Type /name <optional context>")
        print("  Variables: Use {input} in template for substitution")
        print("  Example: /review {input} → replaces {input} with context")
        print()
        print("Multi-line Input:")
        print("  Type \\\\ to start multi-line mode")
        print("  Press Enter on empty line to submit")
        print("  Press Ctrl+D to cancel (or type .cancel)")
        print("  Press ↑ at start of line to edit previous line (or type .back)")
        print("  Full block saved to history - use ↑ at main prompt to recall")
        print("  Great for code blocks and long prompts")
        if READLINE_AVAILABLE:
            print()
            print("History:")
            print("  Use ↑↓ arrows to navigate previous queries")
            print("  History saved to ~/.chat_history")
        print("=" * 50)

    def display_info(self):
        """Display detailed agent information."""
        print(f"\n{self.agent_name.upper()} - Information")
        print("=" * 60)
        print(f"Name: {self.agent_name}")
        print(f"Description: {self.agent_description}")
        print()

        if self.agent_metadata:
            print("Configuration:")
            if "model_id" in self.agent_metadata:
                print(f"  Model ID: {self.agent_metadata['model_id']}")
            if "max_tokens" in self.agent_metadata:
                print(f"  Max Tokens: {self.agent_metadata['max_tokens']}")
            if "temperature" in self.agent_metadata:
                print(f"  Temperature: {self.agent_metadata['temperature']}")
            print()

            if "tools" in self.agent_metadata and self.agent_metadata["tools"]:
                print(f"Available Tools ({self.agent_metadata['tool_count']}):")
                for i, tool in enumerate(self.agent_metadata["tools"], 1):
                    print(f"  {i}. {tool}")
                if self.agent_metadata["tool_count"] > len(
                    self.agent_metadata["tools"]
                ):
                    remaining = self.agent_metadata["tool_count"] - len(
                        self.agent_metadata["tools"]
                    )
                    print(f"  ... and {remaining} more")
            elif self.agent_metadata["tool_count"] > 0:
                print(f"Tools: {self.agent_metadata['tool_count']} available")
            else:
                print("Tools: None")

        print()
        print("Features:")
        if self.use_rich:
            print("  ✓ Rich markdown rendering with syntax highlighting")
        if READLINE_AVAILABLE:
            print("  ✓ Command history with full readline editing")
        print("  ✓ Multi-line input support")
        print("  ✓ Automatic error recovery and retry logic")
        print("  ✓ Session reset with 'clear' command")
        if self.config:
            print("  ✓ Configuration file support (~/.chatrc or .chatrc)")
        if self.auto_save:
            print("  ✓ Auto-save conversations on exit")
        print("=" * 60)

    def display_session_summary(
        self, session_start_time: float, query_count: int, token_tracker: TokenTracker
    ):
        """
        Display session summary on exit.

        Args:
            session_start_time: Session start timestamp
            query_count: Number of queries in session
            token_tracker: TokenTracker instance
        """
        session_duration = time.time() - session_start_time

        # Format duration
        if session_duration < 60:
            duration_str = f"{session_duration:.0f}s"
        elif session_duration < 3600:
            minutes = int(session_duration / 60)
            seconds = int(session_duration % 60)
            duration_str = f"{minutes}m {seconds}s"
        else:
            hours = int(session_duration / 3600)
            minutes = int((session_duration % 3600) / 60)
            duration_str = f"{hours}h {minutes}m"

        print(f"\n{Colors.DIM}{'=' * 60}{Colors.RESET}")
        print(Colors.system("Session Summary"))
        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")

        summary_parts = []
        summary_parts.append(f"Duration: {duration_str}")
        summary_parts.append(f"Queries: {query_count}")

        # Token and cost info
        total_tokens = token_tracker.get_total_tokens()
        if total_tokens > 0:
            input_tok = token_tracker.total_input_tokens
            output_tok = token_tracker.total_output_tokens

            token_str = f"Tokens: {token_tracker.format_tokens(total_tokens)}"
            token_str += f" (in: {token_tracker.format_tokens(input_tok)}, "
            token_str += f"out: {token_tracker.format_tokens(output_tok)})"
            summary_parts.append(token_str)

            cost = token_tracker.get_cost()
            if cost > 0:
                summary_parts.append(f"Total Cost: {token_tracker.format_cost()}")

        for part in summary_parts:
            print(Colors.system(f"  {part}"))

        print(f"{Colors.DIM}{'=' * 60}{Colors.RESET}")

    def display_templates(self, templates: list, prompts_dir: Path):
        """
        Display available templates.

        Args:
            templates: List of (name, description) tuples or list of names
            prompts_dir: Path to prompts directory
        """
        if templates:
            print(
                f"\n{Colors.system('Available Prompt Templates')} ({len(templates)}):"
            )
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            for item in templates:
                if isinstance(item, tuple):
                    name, desc = item
                    print(f"  {Colors.success('/' + name)} - {desc}")
                else:
                    print(f"  {Colors.success('/' + item)}")
            print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
            print(Colors.system("Usage: /template_name <optional context>"))
            print(Colors.system(f"Location: {prompts_dir}"))
        else:
            print(f"\n{Colors.system('No prompt templates found')}")
            print(f"Create templates in: {prompts_dir}")
            print(f"Example: {prompts_dir}/review.md")

    def display_sessions(self, sessions: list, agent_name: Optional[str] = None):
        """
        Display list of available sessions.

        Args:
            sessions: List of SessionInfo objects
            agent_name: Optional current agent name for highlighting
        """

        if not sessions:
            print(f"\n{Colors.system('No saved sessions found')}")
            if agent_name:
                print(f"Start chatting to create your first session with {agent_name}")
            return

        print(f"\n{Colors.system('Available Sessions')} ({len(sessions)}):")
        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")

        for i, session in enumerate(sessions, 1):
            # Format date
            created_str = session.created.strftime("%b %d, %H:%M")

            # Build session line
            session_line = f"  {i}. {session.agent_name} - {created_str}"
            session_line += f" - {session.query_count} "
            session_line += "query" if session.query_count == 1 else "queries"

            # Add cost if available
            if session.total_cost > 0:
                session_line += f" - ${session.total_cost:.2f}"

            # Highlight if same agent
            if agent_name and session.agent_name == agent_name:
                print(Colors.success(session_line))
            else:
                print(session_line)

            # Show preview
            preview_text = f'     "{session.preview}"'
            print(f"{Colors.DIM}{preview_text}{Colors.RESET}")

        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
        print(Colors.system("Use: resume <number> or resume <session_id>"))

    def display_session_loaded(self, session_info, query_count: int):
        """
        Display confirmation that a session was loaded.

        Args:
            session_info: SessionInfo object
            query_count: Number of queries in the session
        """
        print(f"\n{Colors.success('✓ Session Restored!')}")
        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
        print(f"  Agent: {session_info.agent_name}")
        print(f"  Created: {session_info.created.strftime('%b %d, %Y at %H:%M')}")
        print(f"  Previous queries: {query_count}")
        if session_info.total_tokens > 0:
            print(f"  Tokens used: {session_info.total_tokens:,}")
        if session_info.total_cost > 0:
            print(f"  Cost so far: ${session_info.total_cost:.3f}")
        print(f"{Colors.DIM}{'-' * 60}{Colors.RESET}")
        print(Colors.system("Continuing from where you left off...\n"))
