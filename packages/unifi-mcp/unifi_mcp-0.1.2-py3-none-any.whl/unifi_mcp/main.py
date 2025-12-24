"""Main application module for UniFi MCP server."""

from unifi_mcp.server import run_server


def main() -> None:
    """Main entry point for the UniFi MCP server."""
    run_server()


if __name__ == "__main__":
    main()
