"""
Nia Project Initialization Module
Handles creation of Nia-enabled project structures and configurations
"""
import os
import json
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from .profiles import PROFILE_CONFIGS, get_profile_config
from .rule_transformer import transform_rules_for_profile

logger = logging.getLogger(__name__)

class NIAProjectInitializer:
    """Handles Nia project initialization with support for multiple IDE profiles"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.assets_dir = Path(__file__).parent / "assets"
        self.templates_dir = self.assets_dir / "templates"
        self.rules_dir = self.assets_dir / "rules"
        
        # Validate that required directories exist
        if not self.assets_dir.exists():
            raise RuntimeError(f"Assets directory not found at {self.assets_dir}. Nia MCP server may not be installed correctly.")
        if not self.rules_dir.exists():
            raise RuntimeError(f"Rules directory not found at {self.rules_dir}. Nia MCP server may not be installed correctly.")
        
    def initialize_project(
        self,
        profiles: List[str] = ["cursor"]
    ) -> Dict[str, Any]:
        """
        Initialize a Nia project with specified profiles
        
        Args:
            profiles: List of IDE profiles to set up (cursor, vscode, claude, etc.)
            
        Returns:
            Dictionary with initialization results and status
        """
        try:
            results = {
                "success": True,
                "project_root": str(self.project_root),
                "profiles_initialized": [],
                "files_created": [],
                "warnings": [],
                "next_steps": []
            }
            
            # Validate project root
            if not self.project_root.exists():
                os.makedirs(self.project_root, exist_ok=True)
                
            # No longer creating .nia directory or config files
            
            # Process each profile
            for profile in profiles:
                if profile not in PROFILE_CONFIGS:
                    results["warnings"].append(f"Unknown profile: {profile}")
                    continue
                    
                profile_results = self._initialize_profile(profile)
                if profile_results["success"]:
                    results["profiles_initialized"].append(profile)
                    results["files_created"].extend(profile_results["files_created"])
                else:
                    results["warnings"].append(f"Failed to initialize {profile}: {profile_results.get('error')}")
            
            # Generate next steps
            results["next_steps"].extend(self._generate_next_steps(profiles))
            
            logger.info(f"Successfully initialized Nia project at {self.project_root}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to initialize project: {e}")
            return {
                "success": False,
                "error": str(e),
                "project_root": str(self.project_root)
            }
    
    def _create_nia_directories(self):
        """Create the .nia directory structure"""
        # Simplified - no unnecessary directories or files
        pass
    
    
    
    
    def _initialize_profile(self, profile: str) -> Dict[str, Any]:
        """Initialize a specific IDE profile"""
        try:
            profile_config = get_profile_config(profile)
            if not profile_config:
                return {"success": False, "error": "Profile configuration not found"}
            
            files_created = []
            
            # Create profile directory
            profile_dir = self.project_root / profile_config["target_dir"]
            os.makedirs(profile_dir, exist_ok=True)
            
            # Transform and copy rules
            rule_files = transform_rules_for_profile(
                profile,
                self.rules_dir,
                profile_dir,
                self.project_root
            )
            
            for rule_file in rule_files:
                files_created.append(str(Path(rule_file).relative_to(self.project_root)))
            
            # Handle profile-specific setup
            if profile == "vscode" and profile_config.get("additional_files"):
                # VSCode gets tasks.json and snippets from additional_files
                pass  # Handled by transform_rules_for_profile
            # No need to setup MCP config - user is already running through MCP!
            
            return {
                "success": True,
                "files_created": files_created
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize profile {profile}: {e}")
            return {"success": False, "error": str(e)}
    
    
    
    def _generate_next_steps(self, profiles: List[str]) -> List[str]:
        """Generate helpful next steps for the user"""
        steps = []
        
        # Check for current git repository
        if (self.project_root / ".git").exists():
            try:
                # Use subprocess for safer command execution
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False  # Don't raise exception if git command fails
                )
                git_remote = result.stdout.strip()
                if git_remote and "github.com" in git_remote:
                    steps.append(f"Index this repository: index_repository {git_remote}")
            except (subprocess.SubprocessError, FileNotFoundError):
                # Git might not be installed or available
                logger.debug("Could not get git remote URL")
        
        # Profile-specific steps
        if "cursor" in profiles:
            steps.append("Restart Cursor to load Nia MCP server")
        if "vscode" in profiles:
            steps.append("Reload VSCode window to apply settings")
        
        # General steps
        steps.extend([
            "Explore available commands with list_repositories",
            "Search across code and docs with search",
            "Find new libraries with nia_web_search"
        ])
        
        return steps


def initialize_nia_project(
    project_root: str,
    profiles: List[str] = ["cursor"]
) -> Dict[str, Any]:
    """
    Convenience function to initialize a Nia project
    
    Args:
        project_root: Root directory of the project
        profiles: List of IDE profiles to set up
        
    Returns:
        Dictionary with initialization results
    """
    initializer = NIAProjectInitializer(project_root)
    return initializer.initialize_project(
        profiles=profiles
    )