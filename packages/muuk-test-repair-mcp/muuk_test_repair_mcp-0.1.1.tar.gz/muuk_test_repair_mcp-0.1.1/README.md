# MuukTest Repair MCP

MCP server for analyzing and repairing E2E test failures (Playwright, Cypress, Selenium, etc).

## Installation

```bash
pip install muuk-test-repair-mcp
```

## Configuration

### VS Code / GitHub Copilot

Open User MCP Configuration (`Cmd+Shift+P` → "MCP: Open User Configuration"):

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "muuk_api_key",
      "description": "MuukTest API Key",
      "password": true
    }
  ],
  "servers": {
    "muuk-test-repair": {
      "command": "muuk-test-repair-mcp",
      "env": {
        "MUUK_API_KEY": "${input:muuk_api_key}"
      }
    }
  }
}
```

### Claude Desktop

Edit `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "muuk-test-repair": {
      "command": "muuk-test-repair-mcp",
      "env": {
        "MUUK_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Cursor

Similar to VS Code configuration.

## Usage

Ask your AI agent:

```
Analyze the test failure with:
- test_file_path: ./tests/login.spec.ts
- failure_info_path: ./failure-data/failure_info.json
- dom_elements_path: ./failure-data/dom_elements.json
- screenshot_path: ./failure-data/screenshot.png
```

Or more naturally:

```
Analyze the test failure in ./failure-data/
```

## Required Files

| File | Description |
|------|-------------|
| Test file (.ts/.js/.py) | The test that failed |
| failure_info.json | Error details and stack trace |
| dom_elements.json | DOM state at failure |
| screenshot.png | Screenshot of the failure |

## Available AI Presets

- `claude` (default)
- `openai`
- `gemini`
- `deepseek`
- `mistral`

## API Key

Request your `MUUK_API_KEY` from [MuukTest](https://muuktest.com).

## License

MIT