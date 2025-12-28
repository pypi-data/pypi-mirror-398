"""
Prompt template management.

Handles loading and listing markdown-based prompt templates.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manage prompt templates from ~/.prompts/ directory."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            prompts_dir: Directory containing templates (defaults to ~/.prompts/)
        """
        self.prompts_dir = prompts_dir or Path.home() / ".prompts"
        self._initialize_templates()

    def _initialize_templates(self):
        """Create prompts directory and sample templates if they don't exist."""
        if self.prompts_dir.exists():
            return

        try:
            self.prompts_dir.mkdir(parents=True, exist_ok=True)

            # Create sample templates
            self._create_sample_template(
                "explain",
                """# Explain this code

Please explain the following code in detail:

{input}

Focus on:
- What the code does
- How it works
- Any potential issues or improvements
- Best practices being followed or violated
""",
            )

            self._create_sample_template(
                "review",
                """# Code Review

Please review the following code:

{input}

Provide feedback on:
- Code quality and readability
- Potential bugs or issues
- Performance considerations
- Security concerns
- Suggestions for improvement
""",
            )

            self._create_sample_template(
                "debug",
                """# Debug Help

I'm having trouble with this code:

{input}

Please help me:
1. Identify the issue
2. Explain why it's happening
3. Suggest a fix
4. Provide the corrected code
""",
            )

            self._create_sample_template(
                "optimize",
                """# Optimize This Code

Please optimize the following code:

{input}

Focus on:
- Performance improvements
- Memory efficiency
- Code simplicity
- Best practices
""",
            )

            self._create_sample_template(
                "test",
                """# Write Tests

Please write comprehensive tests for the following code:

{input}

Include:
- Unit tests for all functions
- Edge cases and error handling
- Test descriptions explaining what each test validates
""",
            )

            self._create_sample_template(
                "document",
                """# Add Documentation

Please add comprehensive documentation to this code:

{input}

Include:
- Docstrings for all functions/classes
- Inline comments for complex logic
- Usage examples
- Type hints if missing
""",
            )

        except Exception as e:
            logger.debug(f"Could not initialize templates: {e}")

    def _create_sample_template(self, name: str, content: str):
        """Create a sample template file."""
        template_path = self.prompts_dir / f"{name}.md"
        if not template_path.exists():
            try:
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                logger.debug(f"Could not create template {name}: {e}")

    def load_template(self, template_name: str, input_text: str = "") -> Optional[str]:
        """
        Load a prompt template from ~/.prompts/{template_name}.md

        Args:
            template_name: Name of the template (without .md extension)
            input_text: Text to substitute for {input} placeholder

        Returns:
            Processed template text, or None if template not found
        """
        template_path = self.prompts_dir / f"{template_name}.md"

        if not template_path.exists():
            return None

        try:
            with open(template_path, encoding="utf-8") as f:
                template = f.read()

            # Replace {input} placeholder with provided text
            if "{input}" in template:
                template = template.replace("{input}", input_text)
            elif input_text:
                # If no {input} placeholder but input provided, append it
                template = f"{template}\n\n{input_text}"

            return template

        except Exception as e:
            logger.error(f"Error loading template {template_name}: {e}")
            return None

    def list_templates(self) -> list[str]:
        """
        List available prompt templates from ~/.prompts/

        Returns:
            List of template names (without .md extension)
        """
        if not self.prompts_dir.exists():
            return []

        templates = []
        for file in self.prompts_dir.glob("*.md"):
            templates.append(file.stem)

        return sorted(templates)

    def get_template_info(self, template_name: str) -> Optional[tuple[str, str]]:
        """
        Get template description from first line.

        Args:
            template_name: Name of the template

        Returns:
            Tuple of (name, description) or None if not found
        """
        template_path = self.prompts_dir / f"{template_name}.md"

        if not template_path.exists():
            return None

        try:
            with open(template_path, encoding="utf-8") as f:
                first_line = f.readline().strip()
                # Extract description from markdown heading
                if first_line.startswith("# "):
                    description = first_line[2:].strip()
                else:
                    description = template_name
                return (template_name, description)
        except Exception:
            return (template_name, template_name)

    def list_templates_with_descriptions(self) -> list[tuple[str, str]]:
        """
        List templates with their descriptions.

        Returns:
            List of (name, description) tuples
        """
        templates = []
        for template_name in self.list_templates():
            info = self.get_template_info(template_name)
            if info:
                templates.append(info)
        return templates
