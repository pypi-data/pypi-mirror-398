# Synapse MCP Server

MCP server for AI assistants to interact with Synapse infrastructure.

## Quick Start

```bash
# Initialize config
uvx --from 'synapse-sdk[mcp]' synapse mcp init
```

### Setup via AI assistant

```
1. add_environment(name="prod", backend_url="...", access_token="...")
2. list_agents()
3. select_agent(123)  # Required for job operations
```

## Configuration

`~/.synapse/config.yaml`:

## Cursor Setup

`~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "synapse": {
      "command": "uvx",
      "args": ["--from", "synapse-sdk[mcp]", "synapse", "mcp", "serve"]
    }
  }
}
```

## Claude Code Setup

```bash
claude mcp add synapse -- uvx --from 'synapse-sdk[mcp]' synapse mcp serve

# Local development:
claude mcp add synapse -- uv run --directory <path-to-sdk> synapse mcp serve
```

## Tools

| Category | Tools |
|----------|-------|
| Environment | `switch_environment`, `list_environments`, `get_current_environment`, `add_environment` |
| Agents | `list_agents`, `select_agent`, `clear_agent` |
| Plugins | `list_plugin_releases`, `get_plugin_release`, `discover_local_plugin`, `get_action_config`, `validate_plugin_config`, `publish_plugin` |
| Execution | `run_plugin`, `run_debug_plugin`, `run_local_plugin` |
| Jobs | `list_jobs`, `get_job`, `get_job_logs`, `stop_job` |
| Deployments | `list_serve_applications`, `get_serve_application`, `delete_serve_application` |
| Models | `list_models`, `get_model` |

## Resources

- `synapse://config` - Current configuration
- `synapse://environments` - List of environments
- `synapse://plugin/{path}/config` - Plugin config.yaml
- `synapse://plugin/{path}/actions` - Plugin actions
- `synapse://plugin/{path}/action/{name}/schema` - Action schema

## Prompts

`debug_plugin`, `publish_plugin_workflow`, `diagnose_job`, `setup_environment`
