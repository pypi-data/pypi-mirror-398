# Hanary MCP Server

[Hanary](https://hanary.org) MCP Server for Claude Code - workspace-bound task management.

## Installation

```bash
# Using uvx (recommended)
uvx hanary-mcp --workspace my-project

# Or install globally
uv tool install hanary-mcp
```

## Configuration

### Claude Code Setup

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "hanary": {
      "command": "uvx",
      "args": ["hanary-mcp", "--workspace", "your-workspace-slug"],
      "env": {
        "HANARY_API_TOKEN": "${HANARY_API_TOKEN}"
      }
    }
  }
}
```

Or add via CLI:

```bash
claude mcp add hanary --transport stdio -- uvx hanary-mcp --workspace your-workspace-slug
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HANARY_API_TOKEN` | Yes | Your Hanary API token |
| `HANARY_API_URL` | No | API URL (default: https://hanary.org) |

## Available Tools

### Task Management

- `list_tasks` - List tasks in the workspace
- `create_task` - Create a new task
- `update_task` - Update task title/description
- `complete_task` - Mark task as completed
- `uncomplete_task` - Mark task as incomplete
- `delete_task` - Soft delete a task
- `get_top_task` - Get highest priority incomplete task

### Workspace

- `get_workspace` - Get workspace details
- `list_workspace_members` - List workspace members

### Messages

- `list_messages` - List workspace messages
- `create_message` - Send a message

## Development

```bash
# Clone and install
git clone https://github.com/hanary/hanary-mcp.git
cd hanary-mcp
uv sync

# Run locally
HANARY_API_TOKEN=your_token uv run hanary-mcp --workspace test
```

## License

MIT
