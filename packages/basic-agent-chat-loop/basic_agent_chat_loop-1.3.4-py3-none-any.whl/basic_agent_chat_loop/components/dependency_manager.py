"""
Dependency detection and installation for agents.

Handles automatic detection and installation of agent dependencies from
requirements.txt, pyproject.toml, or other dependency files.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DependencyManager:
    """Manages agent dependency detection and installation."""

    def __init__(self, agent_path: str):
        """
        Initialize dependency manager for an agent.

        Args:
            agent_path: Path to agent file
        """
        self.agent_path = Path(agent_path).resolve()
        self.agent_dir = self.agent_path.parent

    def detect_dependency_file(self) -> Optional[tuple[str, Path]]:
        """
        Detect dependency files in agent directory.

        Returns:
            Tuple of (file_type, file_path) if found, None otherwise
            file_type is one of: 'requirements', 'pyproject', 'setup'
        """
        # Check for requirements.txt (most common)
        requirements_txt = self.agent_dir / "requirements.txt"
        if requirements_txt.exists():
            return ("requirements", requirements_txt)

        # Check for pyproject.toml
        pyproject_toml = self.agent_dir / "pyproject.toml"
        if pyproject_toml.exists():
            # Verify it has dependencies section
            try:
                content = pyproject_toml.read_text()
                if "[project.dependencies]" in content or "dependencies = [" in content:
                    return ("pyproject", pyproject_toml)
            except Exception as e:
                logger.debug(f"Could not read pyproject.toml: {e}")

        # Check for setup.py (legacy)
        setup_py = self.agent_dir / "setup.py"
        if setup_py.exists():
            return ("setup", setup_py)

        return None

    def install_dependencies(self, file_type: str, file_path: Path) -> tuple[bool, str]:
        """
        Install dependencies from detected file.

        Args:
            file_type: Type of dependency file ('requirements', 'pyproject', 'setup')
            file_path: Path to dependency file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if file_type == "requirements":
                return self._install_from_requirements(file_path)
            elif file_type == "pyproject":
                return self._install_from_pyproject(file_path)
            elif file_type == "setup":
                return self._install_from_setup(file_path)
            else:
                return (False, f"Unknown dependency file type: {file_type}")
        except Exception as e:
            logger.error(f"Failed to install dependencies: {e}", exc_info=True)
            return (False, f"Installation failed: {e}")

    def _install_from_requirements(self, requirements_file: Path) -> tuple[bool, str]:
        """Install dependencies from requirements.txt."""
        try:
            # Use subprocess to call pip
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                filename = requirements_file.name
                msg = f"✓ Successfully installed dependencies from {filename}"
                return (True, msg)
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"pip install failed: {error_msg}")
                return (False, f"Failed to install dependencies: {error_msg}")

        except subprocess.TimeoutExpired:
            return (False, "Installation timed out after 5 minutes")
        except Exception as e:
            return (False, f"Installation error: {e}")

    def _install_from_pyproject(self, pyproject_file: Path) -> tuple[bool, str]:
        """Install dependencies from pyproject.toml."""
        try:
            # Install in editable mode from directory containing pyproject.toml
            project_dir = pyproject_file.parent
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", str(project_dir)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                msg = f"✓ Successfully installed project from {pyproject_file.name}"
                return (True, msg)
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"pip install failed: {error_msg}")
                return (False, f"Failed to install project: {error_msg}")

        except subprocess.TimeoutExpired:
            return (False, "Installation timed out after 5 minutes")
        except Exception as e:
            return (False, f"Installation error: {e}")

    def _install_from_setup(self, setup_file: Path) -> tuple[bool, str]:
        """Install dependencies from setup.py."""
        try:
            # Install in editable mode from directory containing setup.py
            project_dir = setup_file.parent
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", str(project_dir)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                msg = f"✓ Successfully installed project from {setup_file.name}"
                return (True, msg)
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"pip install failed: {error_msg}")
                return (False, f"Failed to install project: {error_msg}")

        except subprocess.TimeoutExpired:
            return (False, "Installation timed out after 5 minutes")
        except Exception as e:
            return (False, f"Installation error: {e}")

    def suggest_auto_setup(self) -> Optional[str]:
        """
        Check if dependencies exist and suggest using --auto-setup.

        Returns:
            Suggestion message if dependencies found, None otherwise
        """
        dep_info = self.detect_dependency_file()
        if dep_info:
            file_type, file_path = dep_info
            return (
                f"💡 Found {file_path.name} in agent directory. "
                f"Run with --auto-setup (or -a) to install dependencies automatically"
            )
        return None
