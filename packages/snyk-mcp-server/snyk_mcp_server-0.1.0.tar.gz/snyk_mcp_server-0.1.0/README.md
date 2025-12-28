# Snyk MCP Server

Custom MCP server for fetching vulnerability data from Snyk REST API.

## Installation via uvx

```bash
uvx snyk-mcp-server@latest
```

## MCP Configuration

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "snyk": {
      "command": "uvx",
      "args": ["snyk-mcp-server@latest"],
      "env": {
        "SNYK_API_TOKEN": "your_snyk_api_token_here",
        "SNYK_API_VERSION": "2024-06-21"
      }
    }
  }
}
```

## Development

```bash
# Clone and install
git clone <repo>
cd snyk-mcp
uv sync

# Run locally
uv run python -m snyk_mcp_server.main

# Build package
uv build
```

## MCP Tools

- `fetch_org_vulnerabilities(org_id: str)` - Get all vulnerabilities for an organization
- `fetch_package_vulnerabilities(org_id: str, purl: str)` - Get vulnerabilities for a specific package

## Environment Variables

- `SNYK_API_TOKEN` - Required Snyk API token
- `SNYK_API_VERSION` - API version (default: 2024-06-21)
