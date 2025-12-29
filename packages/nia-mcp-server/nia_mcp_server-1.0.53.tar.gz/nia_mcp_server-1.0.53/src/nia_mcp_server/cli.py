"""
CLI interface for NIA MCP Server
"""
import sys
import argparse
from typing import Optional
from .setup import setup_mcp_config, SUPPORTED_IDES, REMOTE_SUPPORTED_IDES


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    # Check if it starts with the expected prefix
    if not api_key.startswith("nk_"):
        return False
    # Check minimum length (prefix + reasonable key length)
    if len(api_key) < 10:
        return False
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NIA MCP Server - AI-powered code search",
        prog="nia-mcp-server"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Set up NIA MCP Server for your IDE"
    )
    setup_parser.add_argument(
        "api_key",
        help="Your NIA API key (get it from https://app.trynia.ai/api-keys)"
    )
    setup_parser.add_argument(
        "--ide",
        choices=SUPPORTED_IDES,
        default="cursor",
        help="IDE to configure (default: cursor)"
    )
    setup_parser.add_argument(
        "--remote",
        action="store_true",
        help="Use remote MCP server (no local installation, connects via HTTP)"
    )
    
    # List command
    list_parser = subparsers.add_parser(
        "list-ides",
        help="List all supported IDEs and their capabilities"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "setup":
        # Validate API key
        if not validate_api_key(args.api_key):
            print("❌ Invalid API key format. API key should start with 'nk_'")
            print("   Get your API key from: https://app.trynia.ai/api-keys")
            sys.exit(1)
        
        # Run setup
        success = setup_mcp_config(args.api_key, args.ide, args.remote)
        sys.exit(0 if success else 1)
    
    elif args.command == "list-ides":
        print("\n🖥️  Supported IDEs:\n")
        print("Remote + Local (both modes supported):")
        for ide in sorted(SUPPORTED_IDES):
            if ide in REMOTE_SUPPORTED_IDES:
                print(f"  ✅ {ide}")
        
        print("\nLocal only:")
        for ide in sorted(SUPPORTED_IDES):
            if ide not in REMOTE_SUPPORTED_IDES:
                print(f"  📦 {ide}")
        
        print("\n💡 Use --remote for cloud-hosted MCP (no local deps)")
        print("   Use default (local) for self-hosted MCP via pipx\n")
        sys.exit(0)
    
    # If no command specified, show help
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
