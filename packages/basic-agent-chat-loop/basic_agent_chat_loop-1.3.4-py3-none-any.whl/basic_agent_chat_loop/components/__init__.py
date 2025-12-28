"""
Components for Basic Agent Chat Loop.

This package contains modular components extracted from the main chat loop
for better maintainability and testability.
"""

from .agent_loader import (
    extract_agent_metadata,
    load_agent_module,
)
from .alias_manager import AliasManager
from .audio_notifier import AudioNotifier
from .config_wizard import ConfigWizard
from .dependency_manager import DependencyManager
from .display_manager import DisplayManager
from .harmony_processor import HarmonyProcessor
from .session_manager import SessionInfo, SessionManager
from .template_manager import TemplateManager
from .token_tracker import TokenTracker
from .ui_components import Colors, StatusBar

__all__ = [
    "AudioNotifier",
    "Colors",
    "ConfigWizard",
    "StatusBar",
    "TokenTracker",
    "TemplateManager",
    "DisplayManager",
    "AliasManager",
    "DependencyManager",
    "HarmonyProcessor",
    "SessionInfo",
    "SessionManager",
    "load_agent_module",
    "extract_agent_metadata",
]
