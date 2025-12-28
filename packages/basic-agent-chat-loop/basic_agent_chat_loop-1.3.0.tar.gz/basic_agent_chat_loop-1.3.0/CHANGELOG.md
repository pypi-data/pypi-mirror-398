# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.7] - 2025-10-20

### Fixed
- **Windows Command History** - pyreadline3 now installed automatically on Windows
  - No longer requires manual installation with `[windows]` extras
  - Ensures consistent UX across all platforms
  - Added warning message if readline is unavailable on Windows
  - Resolves long-standing usability issue for Windows users

### Changed
- pyreadline3 moved from optional to core dependency (Windows only)
- Updated installation documentation to reflect automatic Windows support

## [0.3.6] - 2025-10-20

### Added
- **Named Color Palette** - User-friendly color configuration
  - 12 predefined colors: black, red, green, yellow, blue, magenta, cyan, white, bright_red, bright_green, bright_blue, bright_white
  - Color wizard now uses color names instead of ANSI escape codes
  - Backward compatibility with existing ANSI code configs
  - New `Colors._resolve_color()` method for flexible color resolution

- **Agent Tool Message Highlighting** - Better visibility for agent operations
  - Lines starting with `[` or `Tool #` now display in bright_green
  - Works in both streaming and non-streaming modes
  - Automatic detection and colorization of agent tool usage
  - New `Colors.format_agent_response()` method

- **Configuration Reset** - Easy restoration of default settings
  - New `--reset-config` flag to reset .chatrc to defaults
  - Interactive prompt with confirmation
  - Supports both global (~/.chatrc) and project (./.chatrc) configs
  - Comprehensive default values for all configuration sections

### Changed
- Config wizard now prompts for color names instead of raw ANSI codes
- Improved color configuration user experience
- Enhanced test coverage (276 tests passing, +8 new tests)

### Fixed
- Removed unused `scope` variable in reset_config_to_defaults
- Fixed line length violations in config_wizard.py and ui_components.py
- Type hints added to default_config dictionary

## [0.3.5] - 2025-10-16

### Added
- **Audio Notifications** - Play sound when agent completes a turn
  - New `audio.enabled` config option (default: true)
  - Custom WAV file support via `audio.notification_sound` config
  - Bundled notification.wav included in package
  - Cross-platform support (macOS: afplay, Linux: aplay/paplay, Windows: winsound)
  - Per-agent audio override support

- **Configuration Wizard** - Interactive setup for .chatrc files
  - New `--wizard` / `-w` flag to launch interactive configuration wizard
  - Walks through all available settings section by section
  - Loads and displays current values when editing existing configs
  - Supports both global (`~/.chatrc`) and project-level (`./.chatrc`) configs
  - Input validation for all setting types (bool, int, float, string)
  - Generates well-formatted YAML with helpful comments
  - Secure file permissions (0o600) on created configs

### Changed
- Code quality improvements with ruff formatting
- Enhanced type annotations for winsound and yaml imports

### Fixed
- Line length warnings in config wizard (addressed via formatting)
- Type checking issues with platform-specific imports

## [0.3.0] - 2025-10-15

### Added
- **Conversation Auto-Save** - Automatically save conversations on exit
  - New `--auto-save` / `-s` flag to enable automatic saving
  - Config option `features.auto_save` for persistent setting
  - Per-agent config override support
  - Conversations saved to `~/agent-conversations/` by default
  - Filenames include agent name, timestamp, and first query snippet
  - JSON format with metadata (agent, model, tokens, duration)
  - 181 tests passing (maintained from 0.2.1)

### Changed
- Minor version bump to reflect new auto-save feature

## [0.2.1] - 2025-10-13

### Fixed
- **Code Quality** - Cleanup for release standards
  - Fixed all line-length violations (E501) - 88 character limit
  - Fixed mypy type checking issues
  - Improved type hints throughout codebase
  - All 181 tests passing

## [0.2.0] - 2025-10-10

### Added
- **Automatic Dependency Installation** - New `--auto-setup` / `-a` flag to automatically install agent dependencies
  - Supports `requirements.txt`, `pyproject.toml`, and `setup.py`
  - Smart detection: Suggests using `--auto-setup` when dependency files are found
  - Helpful feedback with installation progress and errors
  - 20 new tests for dependency management (181 total tests)
- **Community Roadmap** - Created 37 feature request issues for community discussion
  - CLI enhancements (watch, budget, pipe, resume, inspect, validate, export, quiet, test-suite, benchmark, compare, context, preset, profile, dry-run, max-turns)
  - Documentation & learning (tutorial, example agents, videos)
  - Integrations (VS Code, Web UI, API server, Slack/Discord)
  - Quality of life (better errors, keyboard shortcuts, tab completion, conversation management)
  - Advanced features (multi-agent, RAG, persistent memory, marketplace)
  - Developer experience (debug mode, config wizard, scaffolding, hot reload)
  - Testing & quality (integration tests, fuzzing, performance benchmarks)
  - Community & sharing (plugin system, templates, import/export)
  - Security & safety (sandboxing, audit logging, secret detection)

### Changed
- Minor version bump to reflect new auto-setup feature

## [0.1.3] - 2025-10-09

### Fixed
- **Eliminated Import Error Messages During Startup**
  - Completely removed "No module named" errors when using fully qualified agent paths
  - Parent package `__init__.py` files are no longer executed during agent loading
  - Register parent packages as stub modules (sufficient for Python's import machinery)
  - Added sys.stderr suppression during agent module execution as defense-in-depth
  - Fixes issue with paths like `/agents/local/timmy/agent.py` where parent `agents/__init__.py` tries to import sibling modules

### Impact
- Clean startup experience with no confusing error messages
- Agent functionality unchanged (absolute imports still work)
- All 161 tests passing

## [0.1.2] - 2025-10-09

### Fixed
- **Configuration System Bugs** - Fixed three critical config bugs
  - Fixed config loading precedence (explicit path now has highest priority)
  - Fixed NoneType handling in config merge (skips None values from YAML)
  - Fixed default template to use `agents: {}` instead of `agents:`
  - Resolves "NoneType not iterable" errors
- **Enhanced Relative Import Support** - Improved multi-module imports
  - Added proper parent package registration in sys.modules
  - Agents can now import from multiple sibling modules
  - Fixed: `from .utils import X` followed by `from .helpers import Y`

### Testing
- All 161 tests passing (up from 160)
- Added test for multiple sibling imports
- All 24 config tests now pass (was 20/24)

## [0.1.1] - 2025-10-09

### Fixed
- **Relative Import Support** - Agents with relative imports (from .module or from ..module) now work correctly on all platforms
  - Added package root detection by walking up directory tree for __init__.py files
  - Set proper __package__ attribute for Python import system
  - Support for both same-level and parent-level relative imports
  - Added comprehensive tests for relative import scenarios

### Added
- Comprehensive documentation updates:
  - PyPI, tests, and coverage badges in README
  - Complete INSTALL.md rewrite with platform-specific instructions
  - New TROUBLESHOOTING.md with common issues and solutions
  - Auto-setup documentation for .chatrc and ~/.prompts/

### Testing
- Added 2 new tests for relative imports (156 total tests passing)
- Verified Windows installation and compatibility

## [0.1.0] - 2025-10-09

### Added
- **Agent Alias System** - Save agents as short names for quick access
- **Command History** - Navigate previous queries with ↑↓ arrows (persisted to `~/.chat_history`)
- **Multi-line Input** - Type `\\` to enter multi-line mode for code blocks
- **Token Tracking** - Track tokens and costs per query and session
- **Prompt Templates** - Reusable prompts from `~/.prompts/` with variable substitution
- **Configuration System** - YAML-based config with per-agent overrides
- **Status Bar** - Real-time metrics (queries, tokens, duration)
- **Session Summary** - Full statistics displayed on exit
- **Rich Formatting** - Enhanced markdown rendering with syntax highlighting
- **Error Recovery** - Automatic retry logic with exponential backoff
- **Agent Metadata Display** - Show model, tools, and capabilities
- **Async Streaming Support** - Real-time response display with streaming
- **Cross-Platform Installers** - Support for macOS, Linux, and Windows
- **Comprehensive Test Suite** - 158 tests with 61% code coverage
- **Type Hints** - Full type annotations throughout codebase

### Fixed
- Logging configuration no longer interferes with other libraries
- Cost display duplication removed (was showing same value twice)
- Error messages sanitized to prevent path information leakage
- Magic numbers extracted to named constants for maintainability
- All linting issues resolved (ruff, black, mypy)

### Changed
- Renamed from "AWS Strands Chat Loop" to "Basic Agent Chat Loop" (framework-agnostic)
- Made `anthropic-bedrock` an optional dependency (moved to `[bedrock]` extra)
- Added `python-dotenv` as core dependency
- Improved error handling with more informative messages

### Security
- Error messages now show only filenames, not full system paths
- Environment variable loading limited to 3 parent directories
- Log files created with secure behavior

### Documentation
- Complete README with installation and usage examples
- Configuration reference (CONFIG.md)
- Alias system guide (ALIASES.md)
- Installation instructions (INSTALL.md)
- Comprehensive QA report with all issues documented

### Testing
- 158 unit tests covering all components
- Test coverage: 61% overall
  - TokenTracker: 100%
  - UIComponents: 100%
  - DisplayManager: 98%
  - AgentLoader: 93%
  - ChatConfig: 91%
  - TemplateManager: 86%
  - AliasManager: 83%

### Infrastructure
- GitHub-ready project structure
- PyPI-ready package configuration
- Development tooling (pytest, ruff, black, mypy)
- Comprehensive .gitignore

## [Unreleased]

### Planned Features
- Integration tests with mock agents
- Platform-specific testing (Windows, Linux)
- CI/CD pipeline with GitHub Actions
- Additional agent framework support (LangChain, CrewAI)
- Plugin system for extensions
- Web interface option

---

## Release Notes

### v0.1.0 - Initial Release

This is the first public release of Basic Agent Chat Loop, a feature-rich interactive CLI for AI agents. The project provides a unified interface for any AI agent with token tracking, prompt templates, and extensive configuration options.

**Key Highlights:**
- 🏷️ Save agents as aliases for quick access
- 💰 Track token usage and costs
- 📝 Reusable prompt templates
- ⚙️ Flexible YAML configuration
- 🎨 Rich markdown rendering
- 🔄 Automatic error recovery
- 📊 Real-time status updates
- ✅ Comprehensive test coverage

**Installation:**
```bash
pip install basic-agent-chat-loop
```

**Quick Start:**
```bash
# Save an alias
chat_loop --save-alias myagent path/to/agent.py

# Run chat
chat_loop myagent
```

For detailed documentation, see [README.md](README.md) and [docs/](docs/).

---

[0.3.7]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.7
[0.3.6]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.6
[0.3.5]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.5
[0.3.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.3.0
[0.2.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.2.1
[0.2.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.2.0
[0.1.3]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.3
[0.1.2]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.2
[0.1.1]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.1
[0.1.0]: https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/releases/tag/v0.1.0
