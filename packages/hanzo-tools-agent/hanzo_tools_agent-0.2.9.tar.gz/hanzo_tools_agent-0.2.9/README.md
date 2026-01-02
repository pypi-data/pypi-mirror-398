# hanzo-tools-agent

Agent orchestration tools for Hanzo MCP.

## Installation

```bash
pip install hanzo-tools-agent

# Optional: API mode
pip install hanzo-tools-agent[api]

# Optional: High-performance
pip install hanzo-tools-agent[perf]

# Optional: Full features
pip install hanzo-tools-agent[full]
```

## Tools

### agent - Unified Agent Runner
Run various AI CLI agents with YOLO mode and auto-backgrounding.

```python
# Run with default agent (claude when in Claude Code)
agent(action="run", prompt="Explain this code")

# Run specific agent
agent(action="run", name="gemini", prompt="Review this PR")

# Run with system prompt (claude only)
agent(action="run", name="claude", prompt="Fix bug", system_prompt="Be concise")

# List available agents
agent(action="list")

# Check agent status
agent(action="status", name="claude")
```

**Available Agents:**

| Agent | Command | Auth | YOLO Flags |
|-------|---------|------|------------|
| `claude` (or `cc`) | `claude` | OAuth | `--dangerously-skip-permissions -p` |
| `codex` | `codex` | OAuth | `--full-auto` |
| `gemini` | `gemini` | `GOOGLE_API_KEY` | - |
| `grok` | `grok` | `XAI_API_KEY` | - |
| `qwen` | `qwen` | `DASHSCOPE_API_KEY` | - |
| `vibe` | `vibe` | - | - |
| `code` | `hanzo-code` | - | - |
| `dev` | `hanzo-dev` | - | - |

**Features:**
- **YOLO Mode**: Agents run with full auto-approval flags
- **OAuth Support**: Claude and Codex use browser OAuth (no API keys needed)
- **System Prompts**: Inject system prompts via `--append-system-prompt` (claude)
- **Auto-backgrounding**: Long-running agents auto-background after timeout
- **Config Sharing**: MCP config passed to spawned agents

### Direct API Mode
Configure agents for direct API calls without CLI:

```json
// ~/.hanzo/agents/custom.json
{
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "api_type": "openai",
    "model": "gpt-4",
    "env_key": "OPENAI_API_KEY"
}
```

### iching - I Ching Wisdom
```python
iching(challenge="How should I approach this refactoring?")
```

### review - Code Review
```python
review(
    focus="FUNCTIONALITY",
    work_description="Implemented auto-import feature",
    file_paths=["/path/to/file.py"]
)
```

## MCP Config Sharing

When spawning agents, these environment variables are passed:
- `HANZO_MCP_MODE` - Current MCP mode
- `HANZO_MCP_ALLOWED_PATHS` - Allowed paths
- `HANZO_MCP_ENABLED_TOOLS` - Enabled tools
- `HANZO_MCP_PERSONA` - Active persona
- `HANZO_AGENT_PARENT=true` - Indicates spawned agent
- `HANZO_AGENT_NAME=<agent>` - Name of agent

## License

MIT
