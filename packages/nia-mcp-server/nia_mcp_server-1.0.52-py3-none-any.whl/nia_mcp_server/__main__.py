"""
Entry point for NIA MCP Server
"""
import sys
from .server import run
from .cli import main as cli_main


def main():
    """Main entry point."""
    # Check if running as CLI command
    if len(sys.argv) > 1 and sys.argv[1] in ["setup", "--help", "-h"]:
        # Run CLI interface
        cli_main()
    else:
        # Run MCP server
        run()


if __name__ == "__main__":
    main()