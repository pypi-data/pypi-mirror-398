# GOV.UK Design System MCP

An MCP server that exposes GOV.UK Design System documentation to AI agents.

## Installation

```bash
pip install govuk-design-system-mcp
```

## Usage

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "govuk-design-system": {
      "command": "govuk-design-system-mcp"
    }
  }
}
```

### VS Code

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "govuk-design-system": {
      "command": "govuk-design-system-mcp"
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `list_components()` | List all GOV.UK components |
| `list_patterns()` | List all design patterns |
| `list_styles()` | List all style guides |
| `get_component_guidance(name)` | Get component documentation |
| `get_pattern(name)` | Get pattern documentation |
| `get_style(name)` | Get style documentation |

## License

MIT
