"""
Nia Rule Transformer
Handles transformation of rule files for different IDE profiles
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .profiles import get_profile_config, TEMPLATE_CONFIGS

logger = logging.getLogger(__name__)


def transform_rules_for_profile(
    profile: str,
    source_dir: Path,
    target_dir: Path,
    project_root: Path
) -> List[str]:
    """
    Transform rule files for a specific profile
    
    Args:
        profile: Profile name (cursor, vscode, etc.)
        source_dir: Directory containing source rule files
        target_dir: Directory to write transformed rules
        project_root: Project root directory for context
        
    Returns:
        List of created file paths
    """
    profile_config = get_profile_config(profile)
    if not profile_config:
        raise ValueError(f"Unknown profile: {profile}")
    
    created_files = []
    file_map = profile_config.get("file_map", {})
    
    # Process each file in the file map
    for source_file, target_file in file_map.items():
        source_path = source_dir / source_file
        
        if not source_path.exists():
            logger.warning(f"Source file not found: {source_path}")
            continue
        
        # Read source content
        content = source_path.read_text()
        
        # Apply transformations
        transformed_content = apply_transformations(
            content,
            profile_config,
            project_root
        )
        
        # Write to target
        target_path = target_dir / target_file
        os.makedirs(target_path.parent, exist_ok=True)
        target_path.write_text(transformed_content)
        created_files.append(str(target_path))
        
        logger.info(f"Created rule file: {target_path}")
    
    # Handle additional files (like VSCode tasks.json)
    additional_files = profile_config.get("additional_files", {})
    for filename, template_key in additional_files.items():
        if template_key in TEMPLATE_CONFIGS:
            template_config = TEMPLATE_CONFIGS[template_key]
            target_path = target_dir / filename
            
            # Apply any necessary transformations to template
            content = template_config["content"]
            content = apply_template_variables(content, project_root)
            
            target_path.write_text(content)
            created_files.append(str(target_path))
            logger.info(f"Created additional file: {target_path}")
    
    return created_files


def apply_transformations(
    content: str,
    profile_config: Dict[str, Any],
    project_root: Path
) -> str:
    """
    Apply profile-specific transformations to content
    
    Args:
        content: Original content
        profile_config: Profile configuration
        project_root: Project root for context
        
    Returns:
        Transformed content
    """
    # Apply global replacements
    global_replacements = profile_config.get("global_replacements", {})
    for pattern, replacement in global_replacements.items():
        content = content.replace(pattern, replacement)
    
    # Apply project-specific variables
    content = apply_template_variables(content, project_root)
    
    # Apply format-specific transformations
    if profile_config.get("format") == "markdown":
        content = transform_markdown_format(content, profile_config)
    elif profile_config.get("format") == "mdc":
        content = transform_to_mdc_format(content, profile_config)
    
    # Apply feature-specific enhancements
    features = profile_config.get("features", [])
    content = enhance_for_features(content, features, profile_config)
    
    return content


def apply_template_variables(content: str, project_root: Path) -> str:
    """
    Replace template variables with actual values
    
    Args:
        content: Content with template variables
        project_root: Project root directory
        
    Returns:
        Content with variables replaced
    """
    variables = {
        "{{PROJECT_ROOT}}": str(project_root),
        "{{PROJECT_NAME}}": project_root.name,
        "{{WORKSPACE_FOLDER}}": "${workspaceFolder}",
        "{{USER_HOME}}": str(Path.home()),
    }
    
    for var, value in variables.items():
        content = content.replace(var, value)
    
    return content


def transform_markdown_format(content: str, profile_config: Dict[str, Any]) -> str:
    """
    Apply markdown-specific transformations
    
    Args:
        content: Markdown content
        profile_config: Profile configuration
        
    Returns:
        Transformed markdown
    """
    # Add profile-specific header if not present
    profile_name = profile_config.get("name", "Unknown")
    if not content.startswith(f"# Nia Integration for {profile_name}"):
        # Check if it starts with a generic Nia header
        if content.startswith("# Nia"):
            # Replace the first line
            lines = content.split('\n')
            lines[0] = f"# Nia Integration for {profile_name}"
            content = '\n'.join(lines)
    
    # Enhance code blocks with profile-specific annotations
    if "mcp" in profile_config.get("features", []):
        content = enhance_mcp_code_blocks(content)
    
    return content


def transform_to_mdc_format(content: str, profile_config: Dict[str, Any]) -> str:
    """
    Transform markdown content to MDC format for Cursor
    
    Args:
        content: Original markdown content
        profile_config: Profile configuration
        
    Returns:
        MDC formatted content
    """
    # Extract the first line as description
    lines = content.split('\n')
    description = ""
    content_start = 0
    
    if lines and lines[0].startswith('#'):
        # Use the first header as description
        description = lines[0].replace('#', '').strip()
        content_start = 1
    else:
        description = "Nia Knowledge Agent Integration Rules"
    
    # Build MDC header
    # For Nia rules, we want them always applied since they guide AI assistant behavior
    mdc_header = f"""---
description: {description}
alwaysApply: true
---
"""
    
    # Get the rest of the content
    remaining_content = '\n'.join(lines[content_start:]).strip()
    
    # Apply markdown transformations first
    remaining_content = transform_markdown_format(remaining_content, profile_config)
    
    return mdc_header + '\n' + remaining_content


def enhance_for_features(
    content: str,
    features: List[str],
    profile_config: Dict[str, Any]
) -> str:
    """
    Enhance content based on profile features
    
    Args:
        content: Original content
        features: List of features supported by profile
        profile_config: Profile configuration
        
    Returns:
        Enhanced content
    """
    # Add feature-specific sections if not present
    enhancements = []
    
    if "mcp" in features and "## MCP Integration" not in content:
        enhancements.append(generate_mcp_section(profile_config))
    
    if "composer" in features and "## Composer Usage" not in content:
        enhancements.append(generate_composer_section())
    
    if "tasks" in features and "## Task Automation" not in content:
        enhancements.append(generate_tasks_section())
    
    if "terminal_integration" in features and "## Terminal Commands" not in content:
        enhancements.append(generate_terminal_section())
    
    # Append enhancements to content
    if enhancements:
        content += "\n\n" + "\n\n".join(enhancements)
    
    return content


def enhance_mcp_code_blocks(content: str) -> str:
    """
    Enhance code blocks for MCP-enabled profiles
    
    Args:
        content: Markdown content
        
    Returns:
        Enhanced content
    """
    # Pattern to find code blocks with Nia commands
    pattern = r'```(\w*)\n(.*?nia.*?)\n```'
    
    def replacer(match):
        lang = match.group(1) or "bash"
        code = match.group(2)
        
        # If it's a NIA command, add annotation
        if any(re.search(rf'\b{re.escape(cmd)}\b', code, re.IGNORECASE) for cmd in ["index_repository", "search", "list_repositories"]):
            return f'```{lang}\n# MCP Command - Run this in your AI assistant\n{code}\n```'
        return match.group(0)
    
    return re.sub(pattern, replacer, content, flags=re.DOTALL)


def generate_mcp_section(profile_config: Dict[str, Any]) -> str:
    """Generate MCP integration section"""
    profile_name = profile_config.get("name", "IDE")
    return f"""## MCP Integration

{profile_name} supports Nia through the Model Context Protocol (MCP). After initialization:

1. **Restart {profile_name}** to load the Nia MCP server
2. **Verify connection** by running: `list_repositories`
3. **Set API key** in your environment or {profile_name} settings

The MCP server provides direct access to all Nia commands within your AI assistant."""


def generate_composer_section() -> str:
    """Generate Composer-specific section"""
    return """## Composer Usage

When using Cursor's Composer:

1. **Start with context**: Always check indexed repositories first
2. **Natural language**: Use complete questions, not keywords
3. **Inline results**: Nia results appear directly in your code
4. **Multi-file**: Reference multiple files from search results

Example:
```
Composer: "How does authentication work in this Next.js app?"
[Nia searches indexed codebase and shows relevant files]
```"""


def generate_tasks_section() -> str:
    """Generate tasks automation section"""
    return """## Task Automation

Quick tasks are configured in `.vscode/tasks.json`:

- **Ctrl+Shift+P** → "Tasks: Run Task"
- Select "Nia: Index Repository" or other Nia tasks
- Follow prompts for input

Custom keyboard shortcuts can be added in keybindings.json."""


def generate_terminal_section() -> str:
    """Generate terminal integration section"""
    return """## Terminal Commands

Quick aliases for your terminal:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
alias nia-index='echo "index_repository"'
alias nia-search='echo "search"'
alias nia-list='echo "list_repositories"'
```

Use these in the integrated terminal for quick access."""


def create_profile_specific_file(
    profile: str,
    filename: str,
    content: str,
    target_dir: Path
) -> Optional[str]:
    """
    Create a profile-specific file
    
    Args:
        profile: Profile name
        filename: Target filename
        content: File content
        target_dir: Target directory
        
    Returns:
        Created file path or None
    """
    try:
        file_path = target_dir / filename
        os.makedirs(file_path.parent, exist_ok=True)
        file_path.write_text(content)
        logger.info(f"Created {profile} file: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"Failed to create {filename} for {profile}: {e}")
        return None