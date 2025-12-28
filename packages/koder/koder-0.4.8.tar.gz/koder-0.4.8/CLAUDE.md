# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup

```bash
# Install dependencies
uv sync

# Run the CLI in development
uv run koder

# Run with a single prompt
uv run koder "Your prompt here"

# Run with specific session
uv run koder --session my-session "Your prompt"
```

### Code Quality

```bash
# Code formatting
uv run black .

# Linting with auto-fix
uv run ruff check --fix

# Error-only pylint check
uv run pylint koder_agent/ --disable=C,R,W --errors-only
```

### Testing

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_file_tools.py

# Run with verbose output
uv run pytest -v
```

## Architecture

Koder is a terminal-based AI coding assistant built on the `openai-agents` library with multi-provider support via LiteLLM.

### Package Structure

```
koder_agent/
├── agentic/        # Agent creation, hooks, and approval system
├── cli.py          # Main CLI entry point
├── config/         # Configuration management (YAML, env vars)
├── core/           # Scheduler, context, streaming, security, commands
├── mcp/            # Model Context Protocol server integration
├── tools/          # Tool implementations (file, search, shell, web, task, todo)
└── utils/          # Helpers (client setup, prompts, sessions, model info)
```

### Core Flow

1. **CLI Entry** (`cli.py`) → parses args, initializes session
2. **AgentScheduler** (`core/scheduler.py`) → orchestrates agent execution with streaming
3. **Agent Creation** (`agentic/agent.py`) → builds agent with tools, MCP servers, model settings
4. **Tool Engine** (`tools/engine.py`) → registers tools, validates inputs, filters sensitive output
5. **Context Manager** (`core/context.py`) → persists conversations in SQLite with token-aware compression

### Key Design Patterns

- **Provider Abstraction**: `utils/client.py` detects providers from environment and configures either native OpenAI client or LiteLLM wrapper
- **Streaming Display**: `core/streaming_display.py` manages Rich Live displays for real-time output
- **Approval Hooks**: `agentic/approval_hooks.py` wraps tool execution with permission checks
- **Security Guard**: `core/security.py` validates shell commands before execution

### Configuration Priority

CLI Arguments > Environment Variables > Config File (`~/.koder/config.yaml`) > Defaults

Key environment variables:
- `KODER_MODEL` - Model name (e.g., `gpt-4o`, `claude-opus-4-20250514`)
- Provider API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, etc.

### Database

SQLite at `~/.koder/koder.db` stores:
- Conversation history with token-aware compression (50k limit)
- Session metadata
- MCP server configurations

### Project Context

The CLI loads `AGENTS.md` from the working directory as project-specific context for the agent.
