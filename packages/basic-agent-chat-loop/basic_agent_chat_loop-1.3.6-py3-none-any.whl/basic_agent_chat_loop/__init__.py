"""Basic Agent Chat Loop - Feature-rich interactive CLI for AI agents.

A powerful chat interface for AI agents with token tracking, prompt templates,
agent aliases, and extensive configuration options.
"""

__version__ = "1.3.6"

from .chat_config import ChatConfig
from .chat_loop import ChatLoop
from .components.alias_manager import AliasManager
from .components.token_tracker import TokenTracker

__all__ = [
    "ChatLoop",
    "ChatConfig",
    "AliasManager",
    "TokenTracker",
    "__version__",
]
