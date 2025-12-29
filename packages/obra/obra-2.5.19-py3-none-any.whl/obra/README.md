# Obra

AI orchestration for autonomous software development.

## Installation

```bash
pipx install obra
```

## Quick Start

```bash
# Authenticate
obra login

# Start AI-orchestrated work
obra "Add user authentication to the application"

# Check status
obra status

# Access documentation
obra docs
```

## Commands

| Command | Description |
|---------|-------------|
| `obra login` | Authenticate with Obra |
| `obra "objective"` | Start orchestrated workflow |
| `obra status` | Check session status |
| `obra resume` | Resume interrupted session |
| `obra config` | Manage configuration (TUI + headless flags) |
| `obra docs` | Open documentation in browser |
| `obra version` | Show version info |

## For LLM Operators

If you're an LLM agent (like Claude Code) working with Obra, you can find the LLM operator guide at:

```bash
obra docs --llm
```

This displays the path to `LLM_ONBOARDING.md`, which contains:
- Autonomous operation behaviors
- Configuration guidelines
- Error handling patterns
- Best practices for AI-orchestrated development

## Troubleshooting

### Authentication Issues

**Problem**: Login fails or credentials not recognized
- **Solution**: Run `obra logout` then `obra login` to re-authenticate
- **Check**: Verify your account is active at [obra.dev](https://obra.dev)

### Missing Provider CLIs

**Problem**: Error about missing `claude-code-local` or other provider CLI
- **Solution**: Run `obra config --validate` to check which CLIs are installed
- **Check**: See [documentation](https://obra.dev/docs) for provider CLI installation guides

### Firewall/Network Issues

**Problem**: Connection timeouts or API unreachable
- **Solution**: Check firewall settings allow HTTPS traffic to `obra.dev`
- **Check**: Verify network connectivity with `ping obra.dev`

### Session Issues

**Problem**: Session appears stuck or unresponsive
- **Solution**: Use `obra status` to check session state, or `obra resume <session-id>` to continue
- **Check**: Review session logs for specific error messages

For more help, visit the [Obra documentation](https://obra.dev/docs) or check the troubleshooting guide.

## Requirements

- Python 3.12+
- Active Obra account (sign up at [obra.dev](https://obra.dev))
- Provider CLI (claude-code-local, gemini-cli, or compatible agent)

## License

Proprietary - All Rights Reserved. Copyright (c) 2024-2025 Unpossible Creations, Inc.
