"""Allow running the MCP server as a module: python -m synapse_sdk.mcp"""

from synapse_sdk.mcp.server import serve

if __name__ == '__main__':
    serve()
