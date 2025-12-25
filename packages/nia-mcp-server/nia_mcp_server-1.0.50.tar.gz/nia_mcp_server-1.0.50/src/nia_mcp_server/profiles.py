"""
Nia Profile Configurations
Defines IDE/Editor profile configurations for rule transformation
"""
from typing import Dict, Any, Optional, List

# Profile configurations define how rules are transformed and where they're placed
PROFILE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "cursor": {
        "name": "Cursor",
        "target_dir": ".cursor/rules",
        "file_extension": ".mdc",
        "file_map": {
            "cursor_rules.md": "nia.mdc"
        },
        "mcp_config": True,
        "format": "mdc",
        "features": ["mcp", "composer", "inline_edits"],
        "global_replacements": {
            "# Nia": "# Nia for Cursor",
            "{{IDE}}": "Cursor"
        }
    },
    
    "vscode": {
        "name": "Visual Studio Code",
        "target_dir": ".vscode",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia-guide.md",
            "vscode_rules.md": "nia-vscode-integration.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["tasks", "snippets", "terminal_integration"],
        "global_replacements": {
            "# Nia": "# Nia for VSCode",
            "{{IDE}}": "VSCode"
        },
        "additional_files": {
            "tasks.json": "vscode_tasks_template",
            "nia.code-snippets": "vscode_snippets_template"
        }
    },
    
    "claude": {
        "name": "Claude Desktop",
        "target_dir": ".claude",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_rules.md",
            "claude_rules.md": "nia_claude_integration.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["conversational", "context_aware", "multi_step"],
        "global_replacements": {
            "# Nia": "# Nia for Claude Desktop",
            "{{IDE}}": "Claude"
        }
    },
    
    "windsurf": {
        "name": "Windsurf",
        "target_dir": ".windsurfrules",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_rules.md",
            "windsurf_rules.md": "windsurf_nia_guide.md"
        },
        "mcp_config": True,
        "format": "markdown",
        "features": ["cascade", "memories", "flows"],
        "global_replacements": {
            "# Nia": "# Nia for Windsurf Cascade",
            "{{IDE}}": "Windsurf"
        }
    },
    
    "cline": {
        "name": "Cline",
        "target_dir": ".cline",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_rules.md"
        },
        "mcp_config": True,
        "format": "markdown",
        "features": ["autonomous", "task_planning"],
        "global_replacements": {
            "# Nia": "# Nia for Cline",
            "{{IDE}}": "Cline"
        }
    },
    
    "codex": {
        "name": "OpenAI Codex",
        "target_dir": ".codex",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_codex_guide.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["completion", "generation"],
        "global_replacements": {
            "# Nia": "# Nia for Codex",
            "{{IDE}}": "Codex"
        }
    },
    
    "antigravity": {
        "name": "Google Antigravity",
        "target_dir": ".gemini/antigravity",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_antigravity_guide.md"
        },
        "mcp_config": True,
        "format": "markdown",
        "features": ["ai_assistant", "code_generation", "multi_modal"],
        "global_replacements": {
            "# Nia": "# Nia for Google Antigravity",
            "{{IDE}}": "Google Antigravity"
        }
    },
    
    "zed": {
        "name": "Zed",
        "target_dir": ".zed",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_assistant.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["assistant", "collaboration"],
        "global_replacements": {
            "# Nia": "# Nia for Zed",
            "{{IDE}}": "Zed"
        }
    },
    
    "jetbrains": {
        "name": "JetBrains IDEs",
        "target_dir": ".idea/nia",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_guide.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["ai_assistant", "code_completion"],
        "global_replacements": {
            "# Nia": "# Nia for JetBrains",
            "{{IDE}}": "JetBrains IDE"
        }
    },
    
    "neovim": {
        "name": "Neovim",
        "target_dir": ".config/nvim/nia",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_guide.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["copilot", "cmp"],
        "global_replacements": {
            "# Nia": "# Nia for Neovim",
            "{{IDE}}": "Neovim"
        }
    },
    
    "sublime": {
        "name": "Sublime Text",
        "target_dir": ".sublime",
        "file_extension": ".md",
        "file_map": {
            "nia_rules.md": "nia_guide.md"
        },
        "mcp_config": False,
        "format": "markdown",
        "features": ["copilot"],
        "global_replacements": {
            "# Nia": "# Nia for Sublime Text",
            "{{IDE}}": "Sublime Text"
        }
    }
}

# Additional template configurations for specific file types
TEMPLATE_CONFIGS = {
    "vscode_tasks_template": {
        "content": """{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Nia: Index Repository",
      "type": "shell",
      "command": "echo 'Run: index_repository ${input:repoUrl}'",
      "problemMatcher": []
    },
    {
      "label": "Nia: Search",
      "type": "shell",
      "command": "echo 'Run: search \\"${input:searchQuery}\\"'",
      "problemMatcher": []
    },
    {
      "label": "Nia: List Repositories",
      "type": "shell",
      "command": "echo 'Run: list_repositories'",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "repoUrl",
      "type": "promptString",
      "description": "GitHub repository URL"
    },
    {
      "id": "searchQuery",
      "type": "promptString",
      "description": "Search query"
    }
  ]
}"""
    },
    
    "vscode_snippets_template": {
        "content": """{
  "Nia Index": {
    "prefix": "nia-index",
    "body": ["index_repository ${1:repo_url}"],
    "description": "Index a repository with Nia"
  },
  "Nia Search": {
    "prefix": "nia-search",
    "body": ["search \\"${1:query}\\""],
    "description": "Search indexed repositories and docs"
  },
  "Nia Web Search": {
    "prefix": "nia-web",
    "body": ["nia_web_search \\"${1:query}\\""],
    "description": "Search the web with Nia"
  },
  "Nia Research": {
    "prefix": "nia-research",
    "body": ["nia_deep_research_agent \\"${1:query}\\""],
    "description": "Perform deep research with Nia"
  }
}"""
    }
}


def get_profile_config(profile: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a specific profile"""
    return PROFILE_CONFIGS.get(profile)


def get_supported_profiles() -> List[str]:
    """Get list of all supported profiles"""
    return list(PROFILE_CONFIGS.keys())


def get_profile_features(profile: str) -> List[str]:
    """Get features supported by a profile"""
    config = get_profile_config(profile)
    return config.get("features", []) if config else []


def is_mcp_enabled(profile: str) -> bool:
    """Check if a profile supports MCP"""
    config = get_profile_config(profile)
    return config.get("mcp_config", False) if config else False