# Basic Agent Chat Loop

[![PyPI version](https://img.shields.io/pypi/v/basic-agent-chat-loop.svg)](https://pypi.org/project/basic-agent-chat-loop/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/actions/workflows/ci.yml/badge.svg)](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Open-Agent-Tools/Basic-Agent-Chat-Loop/branch/main/graph/badge.svg)](https://codecov.io/gh/Open-Agent-Tools/Basic-Agent-Chat-Loop)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A feature-rich, interactive CLI for AI agents with token tracking, prompt templates, agent aliases, and extensive configuration options.

## Features

- 🏷️ **Agent Aliases** - Save agents as short names (`chat_loop pete` instead of full paths)
- 📦 **Auto-Setup** - Automatically install agent dependencies from `requirements.txt` or `pyproject.toml`
- 🔔 **Audio Notifications** - Play sound when agent completes a turn (cross-platform support)
- 🎵 **Harmony Support** - Specialized processing for OpenAI Harmony format (gpt-oss models)
- 📜 **Command History** - Navigate previous queries with ↑↓ arrows (persisted to `~/.chat_history`)
- ✍️ **Multi-line Input** - Type `\\` to enter multi-line mode with Ctrl+D to cancel and ↑ to edit previous lines
- 💾 **Session Management** - Save, resume, and search previous conversations with full context restoration
- 📋 **Copy Commands** - Copy responses, queries, code blocks, or entire conversations to clipboard
- 💰 **Token Tracking** - Track tokens and costs per query and session
- 📝 **Prompt Templates** - Reusable prompts from `~/.prompts/`
- ⚙️ **Configuration** - YAML-based config with per-agent overrides
- 📊 **Status Bar** - Real-time metrics (queries, tokens, duration)
- 📈 **Session Summary** - Full statistics displayed on exit
- 🎨 **Rich Formatting** - Enhanced markdown rendering with syntax highlighting
- 🔄 **Error Recovery** - Automatic retry logic with exponential backoff
- 🔍 **Agent Metadata** - Display model, tools, and capabilities

## Installation

### Quick Install (Recommended)

```bash
pip install basic-agent-chat-loop
```

That's it! The package will automatically create:
- `~/.chatrc` - Configuration file with recommended defaults
- `~/.prompts/` - Sample prompt templates (on first use)

### Platform-Specific Options

**Windows:**
Command history support (pyreadline3) is now **installed automatically** on Windows - no extra steps needed!

**AWS Bedrock integration:**
```bash
pip install basic-agent-chat-loop[bedrock]
```

### From Source

For development or the latest features:

```bash
git clone https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop.git
cd Basic-Agent-Chat-Loop
pip install -e ".[dev]"
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed installation instructions and troubleshooting.

## Quick Start

### Basic Usage

```bash
# Run with agent path
chat_loop path/to/your/agent.py

# Or use an alias (after saving)
chat_loop myagent
```

### Agent Aliases

Save frequently used agents for quick access:

```bash
# Save an agent as an alias
chat_loop --save-alias myagent path/to/agent.py

# Use the alias from anywhere
chat_loop myagent

# List all saved aliases
chat_loop --list-aliases

# Remove an alias
chat_loop --remove-alias myagent
```

**Example with real agents:**
```bash
# Save your agents
chat_loop --save-alias pete ~/agents/product_manager/agent.py
chat_loop --save-alias dev ~/agents/senior_developer/agent.py

# Use them from anywhere
cd ~/projects/my-app
chat_loop dev  # Get coding help
chat_loop pete  # Get product feedback
```

Aliases are stored in `~/.chat_aliases` and work from any directory.

### Auto-Setup Dependencies

Automatically install agent dependencies with the `--auto-setup` flag (or `-a` for short):

```bash
# Auto-install dependencies when running an agent
chat_loop myagent --auto-setup
chat_loop path/to/agent.py -a

# Works with any of these dependency files:
# - requirements.txt (most common)
# - pyproject.toml (modern Python projects)
# - setup.py (legacy projects)
```

**Smart detection**: If you run an agent without `--auto-setup` and dependency files are detected, you'll see a helpful suggestion:

```bash
chat_loop myagent
💡 Found requirements.txt in agent directory. Run with --auto-setup (or -a) to install dependencies automatically
```

**What gets installed:**
- `requirements.txt` → `pip install -r requirements.txt`
- `pyproject.toml` → `pip install -e <agent_directory>`
- `setup.py` → `pip install -e <agent_directory>`

This makes sharing agents easier—just include a `requirements.txt` with your agent and users can install everything with one command.

### Prompt Templates

The package automatically creates sample templates in `~/.prompts/` on first use:
- `explain.md` - Explain code in detail
- `review.md` - Code review with best practices
- `debug.md` - Help debugging issues
- `optimize.md` - Performance optimization suggestions
- `test.md` - Generate test cases
- `document.md` - Add documentation

**Use templates in chat:**
```bash
chat_loop myagent
You: /review src/app.py
You: /explain utils.py
You: /test my_function
```

**Create custom templates:**
```bash
# Create your own template
cat > ~/.prompts/security.md <<'EOF'
# Security Review

Please review this code for security vulnerabilities:

{input}

Focus on:
- Input validation
- Authentication/authorization
- Data sanitization
- Common security patterns
EOF

# Use it in chat
You: /security auth.py
```

## Configuration

A configuration file (`~/.chatrc`) is automatically created on first use with recommended defaults. You can customize it to your preferences:

```yaml
features:
  auto_save: true             # Automatically save conversations on exit
  show_tokens: true           # Display token counts
  show_metadata: true         # Show agent model/tools info
  rich_enabled: true          # Enhanced formatting

ui:
  show_status_bar: true       # Top status bar
  show_duration: true         # Query duration

audio:
  enabled: true               # Play sound when agent completes
  notification_sound: null    # Custom WAV file (null = bundled sound)

harmony:
  enabled: auto               # Harmony processing (auto/yes/no)
  show_detailed_thinking: true  # Show reasoning with labeled prefixes

behavior:
  max_retries: 3              # Retry attempts on failure
  timeout: 120.0              # Request timeout (seconds)

# Per-agent overrides
agents:
  'Product Pete':
    features:
      show_tokens: false
    audio:
      enabled: false          # Disable audio for this agent
```

### Audio Notifications

Audio notifications alert you when the agent completes a response. Enabled by default with a bundled notification sound.

**Platforms supported:**
- macOS (using `afplay`)
- Linux (using `aplay` or `paplay`)
- Windows (using `winsound`)

**Configure audio in ~/.chatrc:**
```yaml
audio:
  enabled: true
  notification_sound: null    # Use bundled sound

  # Or specify a custom WAV file:
  # notification_sound: /path/to/custom.wav
```

**Per-agent overrides:**
```yaml
agents:
  'Silent Agent':
    audio:
      enabled: false  # Disable audio for this agent
```

See [CONFIG.md](CONFIG.md) for full configuration options.

## Commands

| Command | Description |
|---------|-------------|
| `help` | Show help message |
| `info` | Show agent details (model, tools) |
| `templates` | List available prompt templates |
| `sessions` | List all saved conversation sessions |
| `/name` | Use prompt template from `~/.prompts/name.md` |
| `resume <#>` | Resume a previous session by number or ID |
| `copy` | Copy last response to clipboard (see variants below) |
| `clear` | Clear screen and reset agent session |
| `exit`, `quit` | Exit chat (shows session summary) |

### Session Management

**Save conversations automatically:**

```bash
# Enable auto-save in config
features:
  auto_save: true
```

**Resume a previous conversation:**

```bash
# In chat - list sessions
You: sessions

Available Sessions (3):
  1. MyAgent - Jan 26, 14:30 - 15 queries - $0.48
     "Can you help me build a REST API..."

  2. MyAgent - Jan 25, 09:15 - 7 queries - $0.23
     "Explain async/await in Python..."

# Resume by number
You: resume 1

# Or resume on startup
chat_loop myagent --resume
chat_loop myagent --resume 1
chat_loop myagent --resume myagent_20250126_143022
```

**List all saved sessions:**

```bash
chat_loop --list-sessions
```

Sessions are saved to `~/agent-conversations/` by default (configurable).

### Copy Commands

Quickly copy content to clipboard:

**Available copy commands:**

```bash
# Copy last agent response (default)
You: copy

# Copy your last query
You: copy query

# Copy entire conversation as markdown
You: copy all

# Copy only code blocks from last response
You: copy code
```

**Example workflow:**

```
You: Write a Python function to reverse a string

Agent: Here's a function to reverse a string:

    def reverse_string(s):
        return s[::-1]

You: copy code
✓ Copied code blocks from last response to clipboard

# Now paste into your editor with Cmd+V (Mac) or Ctrl+V (Windows/Linux)
```

### Multi-line Input

Press `\\` to enter multi-line mode:

```
You: \\
... def factorial(n):
...     if n <= 1:
...         return 1
...     return n * factorial(n - 1)
...
[Press Enter on empty line to submit]
```

## Token Tracking

### During Chat

When `show_tokens: true` in config:

```
------------------------------------------------------------
Time: 6.3s │ 1 cycle │ Tokens: 4.6K (in: 4.4K, out: 237) │ Cost: $0.017
```

### Session Summary

Always shown on exit:

```
============================================================
Session Summary
------------------------------------------------------------
  Duration: 12m 34s
  Queries: 15
  Tokens: 67.8K (in: 45.2K, out: 22.6K)
  Total Cost: $0.475
============================================================
```

## Programmatic Usage

```python
from basic_agent_chat_loop import ChatLoop

# Create chat interface
chat = ChatLoop(
    agent=your_agent,
    name="My Agent",
    description="Agent description",
    config_path=Path("~/.chatrc")  # Optional
)

# Run interactive loop
chat.run()
```

## Harmony Format Support

The chat loop includes built-in support for the [OpenAI Harmony](https://pypi.org/project/openai-harmony/) response format (designed for gpt-oss open-weight models). Harmony support is **included by default** in all installations.

### What is Harmony?

Harmony is OpenAI's response formatting standard for their open-weight model series (gpt-oss). It provides:
- Structured conversation handling with multiple output channels
- Reasoning output generation (internal analysis separate from final response)
- Function call management with namespaces
- Tool usage tracking and structured outputs

### Automatic Detection

The chat loop automatically detects Harmony agents by checking for:
- Explicit `uses_harmony` attribute on the agent
- Model names containing "gpt-oss" or "harmony"
- Harmony-specific methods or attributes
- Agent class names containing "harmony"

### Enhanced Display

When a Harmony agent is detected, responses are automatically processed to:
- Extract and display multiple output channels (analysis, commentary, final)
- Highlight internal reasoning separately from the final response
- Detect and format tool calls appropriately
- Parse structured Harmony response formats

### Configuration

Control Harmony processing behavior:

```yaml
# In ~/.chatrc or .chatrc
harmony:
  enabled: auto                 # auto (default) / yes / no
  show_detailed_thinking: true  # Default - show all channels with labels
```

**`harmony.enabled` options:**
- `auto` (default) - Automatically detect harmony agents
- `yes` - Force enable harmony processing for all agents
- `no` - Disable harmony processing completely

### Detailed Thinking Mode

**By default, detailed thinking is enabled** - showing all channels with labeled prefixes:

**With detailed thinking enabled (`true`, default):**
```
💭 [REASONING]
I need to analyze this query for potential bottlenecks...

📊 [ANALYSIS]
Looking at the query structure:
- Multiple table joins without proper indexes
- WHERE clause filtering happens after the joins

📝 [COMMENTARY]
This is a common pattern I see in legacy codebases...

💬 [RESPONSE]
Here are three optimizations for your database query...
```

**To disable detailed thinking (set to `false`):**
```yaml
harmony:
  show_detailed_thinking: false  # Only show final response
```

**Output with detailed thinking disabled:**
```
Here are three optimizations for your database query...
```

### Example

```python
# Your agent using Harmony
class MyHarmonyAgent:
    uses_harmony = True  # Explicit marker

    def __call__(self, query):
        # Agent returns Harmony-formatted response
        return harmony_response

# Chat loop will automatically detect and handle Harmony format
chat_loop my_harmony_agent
```

## Requirements

### Core Dependencies

- **Python 3.9+** (required by openai-harmony dependency)
- `pyyaml>=6.0.1` - Configuration file parsing
- `rich>=13.7.0` - Enhanced terminal rendering
- `pyperclip>=1.8.0` - Clipboard support for copy commands
- `openai-harmony>=0.0.8` - OpenAI Harmony format support (built-in)
- `pyreadline3>=3.4.1` - Command history on Windows (auto-installed on Windows)

### Optional Dependencies

- `anthropic-bedrock>=0.8.0` - AWS Bedrock integration (install with `[bedrock]`)

### Built-in Features

- `readline` (built-in on Unix) - Command history on macOS/Linux

## Platform Support

- ✅ **macOS** - Full support with native readline
- ✅ **Linux** - Full support with native readline
- ✅ **Windows** - Full support with automatic pyreadline3 installation

## Architecture

```
src/basic_agent_chat_loop/
├── chat_loop.py          # Main orchestration
├── chat_config.py        # Configuration management
├── cli.py                # CLI entry point
├── components/           # Modular components
│   ├── ui_components.py      # Colors, StatusBar
│   ├── token_tracker.py      # Token/cost tracking
│   ├── template_manager.py   # Prompt templates
│   ├── display_manager.py    # Display formatting
│   ├── agent_loader.py       # Agent loading
│   └── alias_manager.py      # Alias management
docs/
├── ALIASES.md            # Alias system guide
├── CONFIG.md             # Configuration reference
├── INSTALL.md            # Installation instructions
└── Chat_TODO.md          # Roadmap and future features
```

## Documentation

- [docs/ALIASES.md](docs/ALIASES.md) - Agent alias system guide
- [docs/CONFIG.md](docs/CONFIG.md) - Configuration reference
- [docs/INSTALL.md](docs/INSTALL.md) - Installation instructions
- [docs/Chat_TODO.md](docs/Chat_TODO.md) - Roadmap and future features

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Latest Release: v1.3.3 (2024-12-24)

Hotfix release with default features enabled and harmony improvements:
- ✨ **Default Features Enabled** - All features now enabled by default for better UX
  - `auto_save: true` - Save conversations automatically
  - `show_tokens: true` - Display token counts and costs
  - `show_status_bar: true` - Status bar with agent, model, queries, time
  - `show_detailed_thinking: true` - Show harmony reasoning channels
- 🔧 **Status Bar Fix** - Status bar now displays correctly between messages
- 📊 **Harmony Improvements** - Enhanced detection logging and documentation
- 🎨 **Better Defaults** - Optimized out-of-the-box experience for new users

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

**Quick fixes:**
- **Package not found**: Run `pip install --upgrade basic-agent-chat-loop`
- **Command not found**: Ensure pip's bin directory is in your PATH
- **Import errors**: Try reinstalling with `pip install --force-reinstall basic-agent-chat-loop`

## Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/issues)
- 📖 **Documentation**: [docs/](docs/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Open-Agent-Tools/Basic-Agent-Chat-Loop/discussions)
