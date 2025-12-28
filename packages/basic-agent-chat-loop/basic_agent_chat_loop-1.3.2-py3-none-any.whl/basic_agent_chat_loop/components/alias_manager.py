"""
Agent alias management.

Handles saving, loading, and managing agent aliases in ~/.chat_aliases.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class AliasManager:
    """Manage agent aliases in ~/.chat_aliases."""

    def __init__(self, aliases_file: Optional[Path] = None):
        """
        Initialize alias manager.

        Args:
            aliases_file: Path to aliases file (defaults to ~/.chat_aliases)
        """
        self.aliases_file = aliases_file or Path.home() / ".chat_aliases"

    def load_aliases(self) -> dict[str, str]:
        """
        Load aliases from file.

        Returns:
            Dictionary mapping alias names to agent paths
        """
        if not self.aliases_file.exists():
            return {}

        try:
            with open(self.aliases_file, encoding="utf-8") as f:
                data = json.load(f)

            # Validate format
            if not isinstance(data, dict):
                logger.warning("Invalid aliases file format, expected dict")
                return {}

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse aliases file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load aliases: {e}")
            return {}

    def save_aliases(self, aliases: dict[str, str]) -> bool:
        """
        Save aliases to file.

        Args:
            aliases: Dictionary mapping alias names to agent paths

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if needed
            self.aliases_file.parent.mkdir(parents=True, exist_ok=True)

            # Write JSON with pretty formatting
            with open(self.aliases_file, "w", encoding="utf-8") as f:
                json.dump(aliases, f, indent=2, sort_keys=True)

            return True

        except Exception as e:
            logger.error(f"Failed to save aliases: {e}")
            return False

    def get_alias(self, alias_name: str) -> Optional[str]:
        """
        Get agent path for an alias.

        Args:
            alias_name: Name of the alias

        Returns:
            Agent path if found, None otherwise
        """
        aliases = self.load_aliases()
        return aliases.get(alias_name)

    def add_alias(
        self, alias_name: str, agent_path: str, overwrite: bool = False
    ) -> tuple[bool, str]:
        """
        Add or update an alias.

        Args:
            alias_name: Name of the alias
            agent_path: Path to the agent
            overwrite: Whether to overwrite existing alias

        Returns:
            Tuple of (success, message)
        """
        # Validate alias name
        if not alias_name:
            return False, "Alias name cannot be empty"

        if not alias_name.replace("_", "").replace("-", "").isalnum():
            msg = (
                "Alias name must contain only letters, numbers, "
                "hyphens, and underscores"
            )
            return (False, msg)

        # Convert to absolute path
        path_obj = Path(agent_path).expanduser().resolve()

        # Validate path exists
        if not path_obj.exists():
            return False, f"Agent file not found: {path_obj}"

        if not path_obj.is_file():
            return False, f"Path is not a file: {path_obj}"

        # Load existing aliases
        aliases = self.load_aliases()

        # Check if alias already exists
        if alias_name in aliases and not overwrite:
            existing_path = aliases[alias_name]
            msg = (
                f"Alias '{alias_name}' already exists "
                f"(points to: {existing_path}). Use --overwrite to update."
            )
            return (False, msg)

        # Add/update alias
        aliases[alias_name] = str(path_obj)

        # Save
        if self.save_aliases(aliases):
            if overwrite and alias_name in self.load_aliases():
                return True, f"Updated alias '{alias_name}' -> {path_obj}"
            else:
                return True, f"Saved alias '{alias_name}' -> {path_obj}"
        else:
            return False, "Failed to save aliases file"

    def remove_alias(self, alias_name: str) -> tuple[bool, str]:
        """
        Remove an alias.

        Args:
            alias_name: Name of the alias to remove

        Returns:
            Tuple of (success, message)
        """
        aliases = self.load_aliases()

        if alias_name not in aliases:
            return False, f"Alias '{alias_name}' not found"

        # Remove and save
        removed_path = aliases.pop(alias_name)

        if self.save_aliases(aliases):
            return True, f"Removed alias '{alias_name}' (was: {removed_path})"
        else:
            return False, "Failed to save aliases file"

    def list_aliases(self) -> dict[str, str]:
        """
        List all aliases.

        Returns:
            Dictionary mapping alias names to agent paths
        """
        return self.load_aliases()

    def resolve_agent_path(self, agent_input: str) -> Optional[str]:
        """
        Resolve agent input to a path.

        First checks if input is a valid file path, then checks aliases.

        Args:
            agent_input: Either a file path or an alias name

        Returns:
            Resolved path if found, None otherwise
        """
        # First, check if it's a valid path
        path = Path(agent_input).expanduser()
        if path.exists() and path.is_file():
            return str(path.resolve())

        # If not a path, check aliases
        alias_path = self.get_alias(agent_input)
        if alias_path:
            # Verify alias path still exists
            if Path(alias_path).exists():
                return alias_path
            else:
                logger.warning(
                    f"Alias '{agent_input}' points to non-existent path: {alias_path}"
                )
                return None

        return None
