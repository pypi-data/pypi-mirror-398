# Claude Desktop Configuration for GTM Wizard

This guide walks you through setting up GTM Wizard with Claude Desktop.

## Prerequisites

- Claude Desktop installed ([download](https://claude.ai/download))
- Python 3.10 or higher
- GTM Wizard installed (see below)

## Step 1: Install GTM Wizard

### Option A: From Source (Recommended for Development)

```bash
git clone https://github.com/MathewJoseph1993/gtm-wizard.git
cd gtm-wizard
pip install -e .
```

### Option B: From PyPI (When Available)

```bash
pip install gtm-wizard
```

## Step 2: Locate Config File

Claude Desktop's configuration file location:

| Platform | Path |
|----------|------|
| **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
| **Linux** | `~/.config/Claude/claude_desktop_config.json` |

### Create the File if Missing

```bash
# macOS
mkdir -p ~/Library/Application\ Support/Claude
touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## Step 3: Add GTM Wizard Configuration

Open the config file and add:

```json
{
  "mcpServers": {
    "gtm-wizard": {
      "command": "python",
      "args": ["-m", "gtm_wizard.server"]
    }
  }
}
```

### If You Have Other MCP Servers

Add GTM Wizard alongside existing servers:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
    "gtm-wizard": {
      "command": "python",
      "args": ["-m", "gtm_wizard.server"]
    }
  }
}
```

## Step 4: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. GTM Wizard tools should now be available

## Step 5: Verify Installation

Ask Claude:

> "What GTM engineering tools do you have access to?"

You should see `diagnose_rate_limiting` listed.

## Example Usage

Try these prompts:

### Rate Limiting Diagnosis

```
I'm getting 429 errors from HubSpot when syncing contacts.
Can you help diagnose the rate limiting issue?
```

### General GTM Questions

```
How should I structure a queue-based lead processing pipeline?
```

## Troubleshooting

### "Server not found" Error

1. Verify Python is in your PATH:
   ```bash
   which python
   ```

2. Try using the full Python path:
   ```json
   {
     "mcpServers": {
       "gtm-wizard": {
         "command": "/usr/local/bin/python3",
         "args": ["-m", "gtm_wizard.server"]
       }
     }
   }
   ```

### "Module not found" Error

1. Verify GTM Wizard is installed:
   ```bash
   python -c "import gtm_wizard; print('OK')"
   ```

2. If using a virtual environment, use the full path:
   ```json
   {
     "mcpServers": {
       "gtm-wizard": {
         "command": "/path/to/venv/bin/python",
         "args": ["-m", "gtm_wizard.server"]
       }
     }
   }
   ```

### Server Crashes on Startup

Check the logs:
```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log
```

### Testing Manually

Run the server directly to see errors:
```bash
python -m gtm_wizard.server
```

## Using MCP Inspector

For debugging, use MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python -m gtm_wizard.server
```

This opens a web UI where you can:
- List available tools
- Test tool inputs/outputs
- View protocol messages

## Full Configuration Example

Complete `claude_desktop_config.json` with multiple servers:

```json
{
  "mcpServers": {
    "gtm-wizard": {
      "command": "python",
      "args": ["-m", "gtm_wizard.server"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    }
  }
}
```

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/MathewJoseph1993/gtm-wizard/issues)
- **Discussions:** [GitHub Discussions](https://github.com/MathewJoseph1993/gtm-wizard/discussions)
