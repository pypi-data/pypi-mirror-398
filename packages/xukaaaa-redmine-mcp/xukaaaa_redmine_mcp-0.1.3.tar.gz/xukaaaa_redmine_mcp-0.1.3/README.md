# Redmine MCP Server

MCP (Model Context Protocol) Server for Redmine - Manage tasks, log time, update status via Claude/AI assistants.

## Features

- **List Tasks** - View tasks assigned to you with status filtering
- **Task Details** - Get detailed information about specific issues
- **Log Time** - Record time entries with comments
- **Update Status** - Change issue status (in progress, resolved, etc.)
- **Update Progress** - Set completion percentage (0-100%)
- **Add Notes** - Add comments to issues
- **Daily Summary** - Check today's logged hours
- **Time Logs Range** - View logged hours within a date range

## Installation

```bash
pip install xukaaaa-redmine-mcp
```

Or install from source:

```bash
git clone https://github.com/xukaaaa/redmine-mcp-server.git
cd redmine-mcp-server
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
export REDMINE_URL="https://your-redmine-instance.com"
export REDMINE_API_KEY="your-api-key"
```

### Getting your Redmine API Key

1. Log in to your Redmine instance
2. Go to **My Account** (top right)
3. Find **API access key** on the right sidebar
4. Click **Show** or **Reset** to get your key

## Usage with Claude Desktop

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json` on Linux/Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "redmine": {
      "command": "redmine-mcp-server",
      "env": {
        "REDMINE_URL": "https://your-redmine-instance.com",
        "REDMINE_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_my_tasks` | List tasks assigned to you (filter: open/closed/status name) |
| `get_issue_details` | Get detailed info about a specific issue |
| `log_time` | Log time entry with hours and comment |
| `update_issue_status` | Change issue status |
| `update_progress` | Update completion percentage |
| `add_note` | Add a comment to an issue |
| `get_today_logs` | View today's time entries and total hours |
| `get_time_logs_range` | View time logs within a date range (from_date, to_date) |
| `clear_cache` | Clear cached metadata |

## Examples

Ask Claude:

- "Show me my open tasks"
- "What's the status of issue #123?"
- "Log 2 hours on task #456 for code review"
- "Mark issue #789 as resolved"
- "Update task #101 to 80% complete"
- "How many hours have I logged today?"
- "Show me my time logs from 2025-12-23 to 2025-12-27"

## Development

```bash
# Clone the repo
git clone https://github.com/xukaaaa/redmine-mcp-server.git
cd redmine-mcp-server

# Install in development mode
pip install -e .

# Run the server
redmine-mcp-server
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**xukaaaa** - [GitHub](https://github.com/xukaaaa)
