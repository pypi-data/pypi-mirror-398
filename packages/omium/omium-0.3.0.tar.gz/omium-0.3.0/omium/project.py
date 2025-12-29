"""
Omium Project Configuration - Config-as-code support.

This module provides support for omium.toml project configuration files,
allowing workflows and settings to be defined in version-controlled config.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python < 3.11
    except ImportError:
        tomllib = None

from omium.output import console, print_success, print_error, print_warning, print_info


# Default omium.toml template
OMIUM_TOML_TEMPLATE = '''# Omium Project Configuration
# https://docs.omium.ai/configuration

[project]
name = "{project_name}"
version = "0.1.0"

[execution]
# Default execution engine URL
engine_url = "http://localhost:8000"
# Checkpoint manager URL  
checkpoint_manager = "localhost:7001"

[llm]
# LLM provider: router, auto, digitalocean, openai
provider = "router"
# Default model
model = "llama3.3-70b-instruct"

[workflows]
# Default workflow directory
directory = "./workflows"

# Define workflows inline
# [[workflows.definitions]]
# id = "my-workflow"
# type = "crewai"
# file = "workflows/my-workflow.json"

[checkpoints]
# Auto-checkpoint interval in seconds
interval = 30
# Maximum checkpoints to keep
max_count = 100

[logging]
# Log level: debug, info, warning, error
level = "info"
# Enable rich formatting
rich_output = true
'''


class OmiumProject:
    """Represents an Omium project with omium.toml configuration."""
    
    CONFIG_FILE = "omium.toml"
    
    def __init__(self, project_dir: Optional[str] = None):
        self.project_dir = Path(project_dir or os.getcwd())
        self.config_path = self.project_dir / self.CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load configuration from omium.toml if it exists."""
        if self.config_path.exists():
            if tomllib is None:
                print_warning("tomllib/tomli not available. Install with: pip install tomli")
                return
            
            try:
                with open(self.config_path, "rb") as f:
                    self.config = tomllib.load(f)
            except Exception as e:
                print_warning(f"Failed to load {self.CONFIG_FILE}: {e}")
    
    @property
    def exists(self) -> bool:
        """Check if project config exists."""
        return self.config_path.exists()
    
    @property
    def name(self) -> str:
        """Get project name."""
        return self.config.get("project", {}).get("name", self.project_dir.name)
    
    @property
    def version(self) -> str:
        """Get project version."""
        return self.config.get("project", {}).get("version", "0.0.0")
    
    @property
    def execution_engine_url(self) -> str:
        """Get execution engine URL."""
        return self.config.get("execution", {}).get("engine_url", "http://localhost:8000")
    
    @property
    def checkpoint_manager_url(self) -> str:
        """Get checkpoint manager URL."""
        return self.config.get("execution", {}).get("checkpoint_manager", "localhost:7001")
    
    @property
    def llm_provider(self) -> str:
        """Get LLM provider."""
        return self.config.get("llm", {}).get("provider", "router")
    
    @property
    def llm_model(self) -> str:
        """Get LLM model."""
        return self.config.get("llm", {}).get("model", "llama3.3-70b-instruct")
    
    @property
    def workflows_dir(self) -> Path:
        """Get workflows directory."""
        dir_path = self.config.get("workflows", {}).get("directory", "./workflows")
        return self.project_dir / dir_path
    
    @property
    def workflow_definitions(self) -> List[Dict[str, Any]]:
        """Get inline workflow definitions."""
        return self.config.get("workflows", {}).get("definitions", [])
    
    @property
    def checkpoint_interval(self) -> int:
        """Get checkpoint interval in seconds."""
        return self.config.get("checkpoints", {}).get("interval", 30)
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.config.get("logging", {}).get("level", "info")
    
    def get_workflow_file(self, workflow_id: str) -> Optional[Path]:
        """Get path to a workflow file by ID."""
        # Check inline definitions first
        for wf in self.workflow_definitions:
            if wf.get("id") == workflow_id:
                file_path = wf.get("file")
                if file_path:
                    return self.project_dir / file_path
        
        # Check workflows directory
        workflows_dir = self.workflows_dir
        if workflows_dir.exists():
            # Try common extensions
            for ext in [".json", ".yaml", ".yml"]:
                path = workflows_dir / f"{workflow_id}{ext}"
                if path.exists():
                    return path
        
        return None
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows."""
        workflows = []
        
        # Get inline definitions
        for wf in self.workflow_definitions:
            workflows.append({
                "id": wf.get("id", "unknown"),
                "type": wf.get("type", "unknown"),
                "file": wf.get("file", "inline"),
                "source": "config"
            })
        
        # Scan workflows directory
        workflows_dir = self.workflows_dir
        if workflows_dir.exists():
            for path in workflows_dir.glob("*.json"):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    workflows.append({
                        "id": data.get("workflow_id", path.stem),
                        "type": data.get("type", "unknown"),
                        "file": str(path.relative_to(self.project_dir)),
                        "source": "file"
                    })
                except:
                    pass
        
        return workflows


def init_project(project_dir: Optional[str] = None, project_name: Optional[str] = None) -> bool:
    """
    Initialize a new Omium project with omium.toml.
    
    Args:
        project_dir: Directory to create project in (default: current directory)
        project_name: Project name (default: directory name)
        
    Returns:
        True if successful, False otherwise
    """
    project_path = Path(project_dir or os.getcwd())
    config_path = project_path / "omium.toml"
    
    if config_path.exists():
        print_warning(f"omium.toml already exists in {project_path}")
        return False
    
    # Create project directory if needed
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Create workflows directory
    workflows_dir = project_path / "workflows"
    workflows_dir.mkdir(exist_ok=True)
    
    # Create omium.toml
    name = project_name or project_path.name
    content = OMIUM_TOML_TEMPLATE.format(project_name=name)
    
    try:
        with open(config_path, "w") as f:
            f.write(content)
        print_success(f"Created {config_path}")
        
        # Create .gitignore
        gitignore_path = project_path / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write("# Omium\n.omium/\n*.checkpoint\n__pycache__/\n")
            print_success("Created .gitignore")
        
        return True
    except Exception as e:
        print_error(f"Failed to create project: {e}")
        return False


def get_current_project() -> Optional[OmiumProject]:
    """Get the current project if omium.toml exists."""
    project = OmiumProject()
    if project.exists:
        return project
    return None
