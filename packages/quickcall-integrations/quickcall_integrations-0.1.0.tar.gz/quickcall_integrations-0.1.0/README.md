# QuickCall Integrations

Developer integrations for Claude Code and Cursor.

**Current integrations:**
- Git - commits, diffs, code changes

**Coming soon:**
- Calendar
- Slack
- GitHub PRs & Issues

## Quick Install

Add to Claude Code:
```bash
claude mcp add quickcall -- uvx quickcall-integrations
```

Or add to your `.mcp.json`:
```json
{
  "mcpServers": {
    "quickcall": {
      "command": "uvx",
      "args": ["quickcall-integrations"]
    }
  }
}
```

## Usage

Just ask Claude:
- "What did I work on today?"
- "Show me recent commits"
- "What's changed in the last week?"

Or use the plugin command: `/quickcall:daily-updates`

## Development

```bash
# Clone and install
git clone https://github.com/quickcall-dev/quickcall-integrations
cd quickcall-integrations
uv pip install -e .

# Run locally
quickcall-integrations

# Run with SSE (for remote deployment)
MCP_TRANSPORT=sse quickcall-integrations
```
