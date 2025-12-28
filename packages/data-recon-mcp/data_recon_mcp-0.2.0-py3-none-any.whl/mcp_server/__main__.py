"""Allow running with: python -m mcp_server

This enables users to configure MCP clients with:
{
    "command": "python3",
    "args": ["-m", "mcp_server"]
}

This works regardless of PATH configuration, since python3 is universally available.
"""
from .server import run

if __name__ == "__main__":
    run()
