# puremcp-google-workspace

MCP server for Google Workspace (Gmail, Drive, Calendar, Docs, Sheets, and more).

## Installation

```bash
pip install puremcp-google-workspace
```

## Client Setup (Claude Desktop)

Add to your Claude Desktop config:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "uvx",
      "args": ["puremcp-google-workspace"]
    }
  }
}
```

For local development:
```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "uv",
      "args": ["--directory", "/path/to/google-workspace", "run", "gworkspace"]
    }
  }
}
```

## Development

```bash
uv sync --all-groups
uv run pre-commit install
```

## Commands

```bash
uv run pytest           # test
uv run ruff check .     # lint
uv run ruff format .    # format
uv run gworkspace       # run
uv build                # build
uv publish              # publish to PyPI
```

## License

Apache-2.0
