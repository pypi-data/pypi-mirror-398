"""
Setup utilities for NIA MCP Server configuration
"""
import os
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any, List

# Remote MCP endpoint
REMOTE_MCP_URL = "https://apigcp.trynia.ai/mcp"
NIA_API_URL = "https://apigcp.trynia.ai/"

# All supported IDEs
SUPPORTED_IDES = [
    "cursor", "claude-code", "claude-desktop", "vscode", "windsurf", "continue", 
    "cline", "codex", "antigravity", "trae", "amp", "zed", "augment", "roo-code", 
    "kilo-code", "gemini-cli", "opencode", "jetbrains", "kiro", "lm-studio", 
    "visual-studio", "crush", "bolt-ai", "rovo-dev", "zencoder", "qodo-gen", 
    "qwen-coder", "perplexity", "warp", "copilot-agent", "copilot-cli", 
    "amazon-q", "factory"
]

# IDEs that support remote mode
REMOTE_SUPPORTED_IDES = [
    "cursor", "vscode", "windsurf", "cline", "antigravity", "trae", "continue",
    "roo-code", "kilo-code", "gemini-cli", "opencode", "qodo-gen", "qwen-coder",
    "visual-studio", "crush", "copilot-agent", "copilot-cli", "factory", 
    "rovo-dev", "claude-code", "amp"
]

# IDEs that require CLI-based setup
CLI_BASED_IDES = ["claude-code", "codex", "amp", "factory"]


def find_mcp_config_path(ide: str = "cursor") -> Optional[Path]:
    """
    Find the MCP configuration file path based on OS and IDE.

    Args:
        ide: IDE to configure

    Returns:
        Path to the MCP configuration file, or None for CLI-based IDEs
    """
    system = platform.system()
    home = Path.home()

    # CLI-based IDEs don't have a config file path
    if ide in CLI_BASED_IDES:
        return None

    config_paths = {
        # Standard MCP config IDEs
        "cursor": {
            "Darwin": home / ".cursor" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Cursor" / "mcp.json",
            "Linux": home / ".config" / "cursor" / "mcp.json",
        },
        "vscode": {
            "Darwin": home / ".vscode" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Code" / "User" / "mcp.json",
            "Linux": home / ".config" / "Code" / "User" / "mcp.json",
        },
        "windsurf": {
            "Darwin": home / ".codeium" / "windsurf" / "mcp_config.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Windsurf" / "mcp_config.json",
            "Linux": home / ".codeium" / "windsurf" / "mcp_config.json",
        },
        "continue": {
            "Darwin": home / ".continue" / "config.json",
            "Windows": home / ".continue" / "config.json",
            "Linux": home / ".continue" / "config.json",
        },
        "cline": {
            "Darwin": home / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            "Linux": home / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        },
        "antigravity": {
            "Darwin": home / ".gemini" / "antigravity" / "mcp_config.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Gemini" / "Antigravity" / "mcp_config.json",
            "Linux": home / ".config" / "gemini" / "antigravity" / "mcp_config.json",
        },
        "trae": {
            "Darwin": home / "Library" / "Application Support" / "Trae" / "User" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Trae" / "User" / "mcp.json",
            "Linux": home / ".config" / "trae" / "mcp.json",
        },
        "gemini-cli": {
            "Darwin": home / ".gemini" / "settings.json",
            "Windows": home / ".gemini" / "settings.json",
            "Linux": home / ".gemini" / "settings.json",
        },
        "qwen-coder": {
            "Darwin": home / ".qwen" / "settings.json",
            "Windows": home / ".qwen" / "settings.json",
            "Linux": home / ".qwen" / "settings.json",
        },
        "claude-desktop": {
            "Darwin": home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Claude" / "claude_desktop_config.json",
            "Linux": home / ".config" / "claude" / "claude_desktop_config.json",
        },
        "zed": {
            "Darwin": home / ".config" / "zed" / "settings.json",
            "Windows": home / ".config" / "zed" / "settings.json",
            "Linux": home / ".config" / "zed" / "settings.json",
        },
        "roo-code": {
            "Darwin": home / ".roo-code" / "mcp.json",
            "Windows": home / ".roo-code" / "mcp.json",
            "Linux": home / ".roo-code" / "mcp.json",
        },
        "kilo-code": {
            "Darwin": home / ".kilocode" / "mcp.json",
            "Windows": home / ".kilocode" / "mcp.json",
            "Linux": home / ".kilocode" / "mcp.json",
        },
        "opencode": {
            "Darwin": home / ".opencode" / "config.json",
            "Windows": home / ".opencode" / "config.json",
            "Linux": home / ".opencode" / "config.json",
        },
        "jetbrains": {
            "Darwin": home / ".jetbrains" / "mcp.json",
            "Windows": home / ".jetbrains" / "mcp.json",
            "Linux": home / ".jetbrains" / "mcp.json",
        },
        "kiro": {
            "Darwin": home / ".kiro" / "mcp.json",
            "Windows": home / ".kiro" / "mcp.json",
            "Linux": home / ".kiro" / "mcp.json",
        },
        "lm-studio": {
            "Darwin": home / ".lmstudio" / "mcp.json",
            "Windows": home / ".lmstudio" / "mcp.json",
            "Linux": home / ".lmstudio" / "mcp.json",
        },
        "visual-studio": {
            "Darwin": home / ".vs" / "mcp.json",
            "Windows": home / ".vs" / "mcp.json",
            "Linux": home / ".vs" / "mcp.json",
        },
        "crush": {
            "Darwin": home / ".crush" / "config.json",
            "Windows": home / ".crush" / "config.json",
            "Linux": home / ".crush" / "config.json",
        },
        "bolt-ai": {
            "Darwin": home / "Library" / "Application Support" / "BoltAI" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "BoltAI" / "mcp.json",
            "Linux": home / ".config" / "bolt-ai" / "mcp.json",
        },
        "augment": {
            "Darwin": home / ".augment" / "settings.json",
            "Windows": home / ".augment" / "settings.json",
            "Linux": home / ".augment" / "settings.json",
        },
        "qodo-gen": {
            "Darwin": home / ".qodo" / "mcp.json",
            "Windows": home / ".qodo" / "mcp.json",
            "Linux": home / ".qodo" / "mcp.json",
        },
        "perplexity": {
            "Darwin": home / "Library" / "Application Support" / "Perplexity" / "mcp.json",
            "Windows": Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / "Perplexity" / "mcp.json",
            "Linux": home / ".config" / "perplexity" / "mcp.json",
        },
        "warp": {
            "Darwin": home / ".warp" / "mcp.json",
            "Windows": home / ".warp" / "mcp.json",
            "Linux": home / ".warp" / "mcp.json",
        },
        "copilot-cli": {
            "Darwin": home / ".copilot" / "mcp-config.json",
            "Windows": home / ".copilot" / "mcp-config.json",
            "Linux": home / ".copilot" / "mcp-config.json",
        },
        "copilot-agent": {
            # This is typically in the repo, not home
            "Darwin": Path(".github") / "copilot-mcp.json",
            "Windows": Path(".github") / "copilot-mcp.json",
            "Linux": Path(".github") / "copilot-mcp.json",
        },
        "amazon-q": {
            "Darwin": home / ".aws" / "amazonq" / "mcp.json",
            "Windows": home / ".aws" / "amazonq" / "mcp.json",
            "Linux": home / ".aws" / "amazonq" / "mcp.json",
        },
        "rovo-dev": {
            "Darwin": home / ".rovo" / "mcp.json",
            "Windows": home / ".rovo" / "mcp.json",
            "Linux": home / ".rovo" / "mcp.json",
        },
        "zencoder": {
            # Zencoder uses UI-based setup
            "Darwin": None,
            "Windows": None,
            "Linux": None,
        },
    }

    if ide not in config_paths:
        raise ValueError(f"Unsupported IDE: {ide}")

    ide_paths = config_paths[ide]
    return ide_paths.get(system, ide_paths.get("Linux"))


def backup_config(config_path: Path) -> Optional[Path]:
    """
    Create a backup of existing configuration file.
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        Path to the backup file if created, None otherwise
    """
    if config_path and config_path.exists():
        backup_path = config_path.with_suffix(".json.backup")
        # If backup already exists, add timestamp
        if backup_path.exists():
            import time
            timestamp = int(time.time())
            backup_path = config_path.with_suffix(f".json.backup.{timestamp}")
        
        shutil.copy2(config_path, backup_path)
        return backup_path
    return None


def create_local_nia_config(api_key: str, ide: str = "cursor") -> Dict[str, Any]:
    """
    Create local NIA MCP server configuration.

    Args:
        api_key: NIA API key
        ide: IDE to configure (affects config format)

    Returns:
        Dictionary with local NIA server configuration
    """
    base_local = {
        "command": "pipx",
        "args": ["run", "--no-cache", "nia-mcp-server"],
        "env": {
            "NIA_API_KEY": api_key,
            "NIA_API_URL": NIA_API_URL
        }
    }

    # IDE-specific variations
    if ide == "cline":
        return {
            **base_local,
            "alwaysAllow": [
                "index", "search", "manage_resource", "regex_search",
                "get_github_file_tree", "nia_web_search", "nia_deep_research_agent",
                "read_source_content", "doc_tree", "doc_ls", "doc_read", "doc_grep", "context"
            ],
            "disabled": False
        }
    elif ide in ["vscode", "visual-studio"]:
        return {
            "type": "stdio",
            **base_local
        }
    elif ide == "opencode":
        return {
            "type": "local",
            "command": ["pipx", "run", "--no-cache", "nia-mcp-server"],
            "env": {
                "NIA_API_KEY": api_key,
                "NIA_API_URL": NIA_API_URL
            },
            "enabled": True
        }
    elif ide == "crush":
        return {
            "type": "stdio",
            **base_local
        }
    elif ide in ["copilot-agent", "copilot-cli"]:
        return {
            "type": "stdio" if ide == "copilot-agent" else "local",
            **base_local,
            "tools": ["index", "search", "manage_resource", "nia_web_search", "nia_deep_research_agent"]
        }
    elif ide == "zed":
        return {
            "source": "custom",
            "command": "pipx",
            "args": ["run", "--no-cache", "nia-mcp-server"],
            "env": {
                "NIA_API_KEY": api_key,
                "NIA_API_URL": NIA_API_URL
            }
        }
    elif ide == "warp":
        return {
            **base_local,
            "working_directory": None,
            "start_on_launch": True
        }
    elif ide == "kilo-code":
        return {
            **base_local,
            "alwaysAllow": [],
            "disabled": False
        }
    
    return base_local


def create_remote_nia_config(api_key: str, ide: str = "cursor") -> Dict[str, Any]:
    """
    Create remote NIA MCP server configuration (HTTP transport).

    Args:
        api_key: NIA API key
        ide: IDE to configure (affects config format)

    Returns:
        Dictionary with remote NIA server configuration
    """
    base_remote = {
        "url": REMOTE_MCP_URL,
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }

    # IDE-specific variations
    if ide == "windsurf":
        return {
            "serverUrl": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            }
        }
    elif ide in ["vscode", "visual-studio"]:
        return {
            "type": "http",
            "url": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            }
        }
    elif ide == "cline":
        return {
            "url": REMOTE_MCP_URL,
            "type": "streamableHttp",
            "headers": {
                "Authorization": f"Bearer {api_key}"
            },
            "alwaysAllow": [
                "index", "search", "manage_resource", "regex_search",
                "get_github_file_tree", "nia_web_search", "nia_deep_research_agent",
                "read_source_content", "doc_tree", "doc_ls", "doc_read", "doc_grep", "context"
            ],
            "disabled": False
        }
    elif ide == "roo-code":
        return {
            "type": "streamable-http",
            "url": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            }
        }
    elif ide == "kilo-code":
        return {
            "type": "streamable-http",
            "url": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            },
            "alwaysAllow": [],
            "disabled": False
        }
    elif ide in ["gemini-cli", "qwen-coder"]:
        return {
            "httpUrl": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json, text/event-stream"
            }
        }
    elif ide == "opencode":
        return {
            "type": "remote",
            "url": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            },
            "enabled": True
        }
    elif ide == "crush":
        return {
            "type": "http",
            "url": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            }
        }
    elif ide in ["copilot-agent", "copilot-cli"]:
        return {
            "type": "http",
            "url": REMOTE_MCP_URL,
            "headers": {
                "Authorization": f"Bearer {api_key}"
            },
            "tools": ["index", "search", "manage_resource", "nia_web_search", "nia_deep_research_agent"]
        }
    
    # Default for cursor, antigravity, trae, qodo-gen, etc.
    return base_remote


def create_nia_config(api_key: str, ide: str = "cursor", remote: bool = False) -> Dict[str, Any]:
    """
    Create NIA MCP server configuration.

    Args:
        api_key: NIA API key
        ide: IDE to configure (affects config format)
        remote: If True, create remote HTTP config instead of local

    Returns:
        Dictionary with NIA server configuration
    """
    if remote:
        return create_remote_nia_config(api_key, ide)
    return create_local_nia_config(api_key, ide)


def update_mcp_config(config_path: Path, api_key: str, ide: str = "cursor", remote: bool = False) -> bool:
    """
    Update or create MCP configuration file with NIA server.

    Args:
        config_path: Path to the MCP configuration file
        api_key: NIA API key
        ide: IDE to configure
        remote: If True, use remote HTTP config

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config or create new one
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    content = f.read().strip()
                    config = json.loads(content) if content else {}
            except (json.JSONDecodeError, ValueError):
                config = {}
        else:
            config = {}

        nia_config = create_nia_config(api_key, ide, remote)

        # Handle different config structures based on IDE
        if ide == "continue":
            if "experimental" not in config:
                config["experimental"] = {}
            if "modelContextProtocolServer" not in config["experimental"]:
                config["experimental"]["modelContextProtocolServer"] = {}
            
            if remote:
                config["experimental"]["modelContextProtocolServer"]["transport"] = {
                    "type": "http",
                    "url": REMOTE_MCP_URL,
                    "headers": {
                        "Authorization": f"Bearer {api_key}"
                    }
                }
            else:
                config["experimental"]["modelContextProtocolServer"]["transport"] = {
                    "type": "stdio",
                    "command": "pipx",
                    "args": ["run", "--no-cache", "nia-mcp-server"],
                    "env": {
                        "NIA_API_KEY": api_key,
                        "NIA_API_URL": NIA_API_URL
                    }
                }
        elif ide in ["vscode", "visual-studio"]:
            if "servers" not in config:
                config["servers"] = {}
            config["servers"]["nia"] = nia_config
        elif ide == "zed":
            if "context_servers" not in config:
                config["context_servers"] = {}
            config["context_servers"]["Nia"] = nia_config
        elif ide == "augment":
            if "augment.advanced" not in config:
                config["augment.advanced"] = {}
            if "mcpServers" not in config["augment.advanced"]:
                config["augment.advanced"]["mcpServers"] = []
            # Remove existing nia config if present
            config["augment.advanced"]["mcpServers"] = [
                s for s in config["augment.advanced"]["mcpServers"] 
                if s.get("name") != "nia"
            ]
            config["augment.advanced"]["mcpServers"].append({
                "name": "nia",
                **nia_config
            })
        elif ide == "opencode":
            if "mcp" not in config:
                config["mcp"] = {}
            config["mcp"]["nia"] = nia_config
        elif ide == "crush":
            if "$schema" not in config:
                config["$schema"] = "https://charm.land/crush.json"
            if "mcp" not in config:
                config["mcp"] = {}
            config["mcp"]["nia"] = nia_config
        else:
            # Standard mcpServers structure for cursor, windsurf, cline, etc.
            if "mcpServers" not in config:
                config["mcpServers"] = {}
            config["mcpServers"]["nia"] = nia_config

        # Write updated configuration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return True

    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
        print(f"   Try running with elevated permissions or check file ownership.")
        return False
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False


def check_cli_available(cli_name: str) -> bool:
    """
    Check if a CLI tool is available in PATH.
    
    Args:
        cli_name: Name of the CLI to check
        
    Returns:
        True if available, False otherwise
    """
    return shutil.which(cli_name) is not None


def setup_command_based_ide(api_key: str, ide: str, remote: bool = False) -> bool:
    """
    Setup NIA MCP Server for command-based IDEs (claude-code, codex, amp, factory).

    Args:
        api_key: NIA API key
        ide: IDE to configure
        remote: If True, use remote config

    Returns:
        True if successful, False otherwise
    """
    # Map IDE to CLI command
    cli_map = {
        "claude-code": ("claude", "Claude Code", "https://www.claude.ai/download"),
        "codex": ("codex", "Codex", "https://github.com/openai/codex"),
        "amp": ("amp", "Amp", "https://ampcode.com"),
        "factory": ("droid", "Factory", "https://factory.dev"),
    }
    
    if ide in cli_map:
        cli_cmd, ide_name, install_url = cli_map[ide]
        if not check_cli_available(cli_cmd):
            print(f"❌ {ide_name} CLI ('{cli_cmd}') not found in PATH.")
            print(f"   Please install {ide_name} from: {install_url}")
            return False
    
    if ide == "claude-code":
        if remote:
            cmd = [
                "claude", "mcp", "add", "--transport", "http", "nia",
                REMOTE_MCP_URL,
                "--header", f"Authorization: Bearer {api_key}"
            ]
        else:
            cmd = [
                "claude", "mcp", "add", "nia", "--scope", "user",
                "-e", f"NIA_API_KEY={api_key}",
                "-e", f"NIA_API_URL={NIA_API_URL}",
                "--", "pipx", "run", "--no-cache", "nia-mcp-server"
            ]
        ide_name = "Claude Code"
    elif ide == "codex":
        if remote:
            print("❌ Codex does not support remote MCP. Please use local mode.")
            return False
        cmd = [
            "codex", "mcp", "add", "nia",
            "--env", f"NIA_API_KEY={api_key}",
            "--env", f"NIA_API_URL={NIA_API_URL}",
            "--", "pipx", "run", "--no-cache", "nia-mcp-server"
        ]
        ide_name = "Codex"
    elif ide == "amp":
        if remote:
            cmd = [
                "amp", "mcp", "add", "nia",
                "--header", f"Authorization=Bearer {api_key}",
                REMOTE_MCP_URL
            ]
        else:
            print("❌ Amp only supports remote MCP. Please use --remote flag.")
            return False
        ide_name = "Amp"
    elif ide == "factory":
        if remote:
            cmd = [
                "droid", "mcp", "add", "nia",
                REMOTE_MCP_URL,
                "--type", "http",
                "--header", f"Authorization: Bearer {api_key}"
            ]
        else:
            cmd = [
                "droid", "mcp", "add", "nia",
                "pipx run --no-cache nia-mcp-server",
                "--env", f"NIA_API_KEY={api_key}",
                "--env", f"NIA_API_URL={NIA_API_URL}"
            ]
        ide_name = "Factory"
    else:
        print(f"❌ Unsupported command-based IDE: {ide}")
        return False

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"\n✅ Setup complete!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Setup failed with error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False
    except FileNotFoundError as e:
        # This shouldn't happen since we check upfront, but keep as safety net
        print(f"\n❌ CLI command not found: {e}")
        return False


def setup_mcp_config(api_key: str, ide: str = "cursor", remote: bool = False) -> bool:
    """
    Main setup function to configure NIA MCP Server.

    Args:
        api_key: NIA API key
        ide: IDE to configure
        remote: If True, use remote HTTP config (no local installation needed)

    Returns:
        True if successful, False otherwise
    """
    # Check remote support
    if remote and ide not in REMOTE_SUPPORTED_IDES:
        print(f"⚠️  {ide} does not support remote MCP mode.")
        print(f"   Falling back to local installation...")
        remote = False

    # Handle command-based IDEs differently
    if ide in CLI_BASED_IDES:
        return setup_command_based_ide(api_key, ide, remote)

    # Handle IDEs that require manual UI setup
    if ide == "zencoder":
        print(f"\n📋 Zencoder requires manual setup via UI:")
        print("   1. Go to: Zencoder menu (…) → Agent tools → Add custom MCP")
        print("   2. Add this configuration:")
        print(json.dumps({
            "command": "pipx",
            "args": ["run", "--no-cache", "nia-mcp-server"],
            "env": {
                "NIA_API_KEY": api_key,
                "NIA_API_URL": NIA_API_URL
            }
        }, indent=2))
        return True

    # For file-based configuration IDEs
    config_path = find_mcp_config_path(ide)
    
    if config_path is None:
        print(f"❌ Could not determine config path for {ide}")
        return False

    # Backup existing config
    backup_path = backup_config(config_path)
    if backup_path:
        print(f"📦 Backed up existing config to: {backup_path}")

    # Update configuration
    if update_mcp_config(config_path, api_key, ide, remote):
        mode_str = "Remote MCP" if remote else "Local MCP"
        print(f"\n✅ {mode_str} setup complete!")
        print(f"📝 Configuration written to: {config_path}")
        if remote:
            print(f"🌐 Connected to: {REMOTE_MCP_URL}")
            print(f"\n💡 No local installation required - your IDE connects directly to NIA's servers.")
        return True
    else:
        print(f"\n❌ Setup failed. Please check the error messages above.")
        if backup_path:
            print(f"   Your original config is safe at: {backup_path}")
        return False
