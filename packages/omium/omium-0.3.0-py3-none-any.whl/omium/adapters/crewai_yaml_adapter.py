"""
Alternative CrewAI workflow export adapter that parses YAML configs and Python code directly.

This avoids the need to instantiate the crew, which requires API keys and proper config setup.
"""

import logging
import os
import re
import ast
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None


def export_crewai_workflow_from_yaml(
    crew_file_path: str,
    workflow_name: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export a CrewAI workflow by parsing YAML configs and Python code directly.
    
    This method doesn't require instantiating the crew, making it more robust
    for export scenarios where API keys or full setup isn't available.
    
    Args:
        crew_file_path: Path to the crew.py file
        workflow_name: Optional name for the workflow
        workflow_id: Optional workflow ID
        
    Returns:
        Dictionary in Omium workflow format
    """
    crew_file_path = os.path.abspath(crew_file_path)
    crew_dir = os.path.dirname(crew_file_path)
    project_root = _find_project_root(crew_dir)
    
    # Determine config directory
    # CrewAI projects typically have config in src/<project>/config/
    config_dir = os.path.join(crew_dir, "config")
    if not os.path.exists(config_dir):
        # Try project root config
        config_dir = os.path.join(project_root, "config")
    
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML is required for YAML-based export. Install with: pip install pyyaml")
    
    # Load agent configs
    agents_config_path = os.path.join(config_dir, "agents.yaml")
    agents_config = {}
    if os.path.exists(agents_config_path):
        with open(agents_config_path, "r") as f:
            agents_config = yaml.safe_load(f) or {}
    else:
        logger.warning(f"Agents config not found at {agents_config_path}")
    
    # Load task configs
    tasks_config_path = os.path.join(config_dir, "tasks.yaml")
    tasks_config = {}
    if os.path.exists(tasks_config_path):
        with open(tasks_config_path, "r") as f:
            tasks_config = yaml.safe_load(f) or {}
    else:
        logger.warning(f"Tasks config not found at {tasks_config_path}")
    
    # Parse Python file for LLM configs and tools
    python_config = _parse_crew_python_file(crew_file_path)
    
    # Extract agents from YAML and Python
    agents = []
    agent_names = list(agents_config.keys())
    
    for i, agent_name in enumerate(agent_names):
        agent_yaml = agents_config[agent_name]
        agent_python = python_config.get("agents", {}).get(agent_name, {})
        
        agent_dict = {
            "role": agent_yaml.get("role", agent_name),
            "goal": agent_yaml.get("goal", ""),
            "backstory": agent_yaml.get("backstory", ""),
            "verbose": agent_python.get("verbose", True),
            "allow_delegation": agent_python.get("allow_delegation", False),
        }
        
        # Add LLM config from Python
        if "llm" in agent_python:
            agent_dict["llm"] = agent_python["llm"]
        
        # Add tools from Python
        if "tools" in agent_python:
            agent_dict["tools"] = agent_python["tools"]
        
        agents.append(agent_dict)
    
    # Extract tasks from YAML
    tasks = []
    task_names = list(tasks_config.keys())
    task_to_agent_map = {}
    
    for task_name in task_names:
        task_yaml = tasks_config[task_name]
        agent_name = task_yaml.get("agent")
        
        # Find agent index
        agent_index = 0
        if agent_name and agent_name in agent_names:
            agent_index = agent_names.index(agent_name)
        
        task_dict = {
            "description": task_yaml.get("description", ""),
            "agent_index": agent_index,
            "expected_output": task_yaml.get("expected_output", ""),
        }
        
        # Add context if available
        if "context" in task_yaml:
            task_dict["context"] = task_yaml["context"] if isinstance(task_yaml["context"], list) else [task_yaml["context"]]
        
        tasks.append(task_dict)
        task_to_agent_map[task_name] = agent_name
    
    # Extract input variables from task descriptions
    input_variables = _extract_input_variables_from_tasks(tasks)
    
    # Determine workflow name
    if not workflow_name:
        workflow_name = os.path.basename(crew_dir) or "crewai-workflow"
    
    if not workflow_id:
        workflow_id = workflow_name
    
    # Get LLM config (from first agent or default)
    llm_config = None
    if agents and agents[0].get("llm"):
        llm_config = agents[0]["llm"]
    else:
        llm_config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
    
    # Build default inputs
    default_inputs = {}
    for var in input_variables:
        default_inputs[var] = f"Your {var.replace('_', ' ')} here"
    
    if not default_inputs:
        default_inputs = {"topic": "Your input here"}
    
    # Build workflow definition
    workflow_definition = {
        "name": workflow_name,
        "verbose": True,
        "llm": llm_config,
        "agents": agents,
        "tasks": tasks,
    }
    
    # Build full Omium workflow format
    omium_workflow = {
        "type": "crewai",
        "workflow_id": workflow_id,
        "agent_id": f"{workflow_id}-agent",
        "inputs": default_inputs,
        "definition": workflow_definition
    }
    
    logger.info(f"Exported CrewAI workflow '{workflow_name}' with {len(agents)} agents and {len(tasks)} tasks")
    if input_variables:
        logger.info(f"Extracted input variables: {', '.join(input_variables)}")
    
    return omium_workflow


def _find_project_root(start_dir: str) -> str:
    """Find project root by looking for pyproject.toml or setup.py."""
    current = os.path.abspath(start_dir)
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "pyproject.toml")):
            return current
        if os.path.exists(os.path.join(current, "setup.py")):
            return current
        current = os.path.dirname(current)
    return start_dir


def _parse_crew_python_file(file_path: str) -> Dict[str, Any]:
    """Parse Python crew file to extract LLM configs and tools."""
    result = {"agents": {}, "tasks": {}}
    
    try:
        with open(file_path, "r") as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        # Find the Crew class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for @agent methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Check if it's an agent method (has @agent decorator)
                        is_agent = any(
                            isinstance(d, ast.Name) and d.id == "agent"
                            or (isinstance(d, ast.Attribute) and d.attr == "agent")
                            for d in item.decorator_list
                        )
                        
                        if is_agent:
                            agent_name = item.name
                            agent_config = _extract_agent_config_from_ast(item)
                            result["agents"][agent_name] = agent_config
    except Exception as e:
        logger.warning(f"Could not parse Python file for advanced config: {e}")
    
    return result


def _extract_agent_config_from_ast(func_node: ast.FunctionDef) -> Dict[str, Any]:
    """Extract agent configuration from AST node."""
    config = {}
    
    # Look for Agent() call in return statement
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Agent":
            # Extract keyword arguments
            for keyword in node.keywords:
                key = keyword.arg
                if key == "llm":
                    # Extract LLM config
                    if isinstance(keyword.value, ast.Call) and isinstance(keyword.value.func, ast.Name) and keyword.value.func.id == "LLM":
                        llm_config = _extract_llm_config_from_ast(keyword.value)
                        if llm_config:
                            config["llm"] = llm_config
                elif key == "tools":
                    # Extract tools
                    if isinstance(keyword.value, ast.List):
                        tools = []
                        for elt in keyword.value.elts:
                            tool_name = _extract_tool_name_from_ast(elt)
                            if tool_name:
                                tools.append({"name": tool_name, "type": tool_name})
                        if tools:
                            config["tools"] = tools
                elif key in ["verbose", "allow_delegation"]:
                    # Extract boolean values
                    if isinstance(keyword.value, ast.Constant):
                        config[key] = keyword.value.value
                    elif isinstance(keyword.value, ast.NameConstant):  # Python < 3.8
                        config[key] = keyword.value.value
    
    return config


def _extract_llm_config_from_ast(llm_node: ast.Call) -> Optional[Dict[str, Any]]:
    """Extract LLM configuration from AST node."""
    config = {}
    
    for keyword in llm_node.keywords:
        if keyword.arg == "model":
            if isinstance(keyword.value, ast.Constant):
                model_str = keyword.value.value
            elif isinstance(keyword.value, ast.Str):  # Python < 3.8
                model_str = keyword.value.s
            else:
                continue
            
            # Parse "openai/gpt-4o-mini" format
            if '/' in model_str:
                parts = model_str.split('/', 1)
                config["provider"] = parts[0].lower()
                config["model"] = parts[1]
            else:
                config["model"] = model_str
                config["provider"] = "openai"
        elif keyword.arg == "temperature":
            if isinstance(keyword.value, ast.Constant):
                config["temperature"] = keyword.value.value
            elif isinstance(keyword.value, ast.Num):  # Python < 3.8
                config["temperature"] = keyword.value.n
    
    if not config:
        return None
    
    # Set defaults
    if "provider" not in config:
        config["provider"] = "openai"
    if "temperature" not in config:
        config["temperature"] = 0.7
    
    return config


def _extract_tool_name_from_ast(elt: ast.AST) -> Optional[str]:
    """Extract tool name from AST element."""
    if isinstance(elt, ast.Call):
        if isinstance(elt.func, ast.Name):
            return elt.func.id
        elif isinstance(elt.func, ast.Attribute):
            return elt.func.attr
    elif isinstance(elt, ast.Name):
        return elt.id
    return None


def _extract_input_variables_from_tasks(tasks: List[Dict[str, Any]]) -> List[str]:
    """Extract input variables from task descriptions."""
    variables = set()
    
    for task in tasks:
        description = task.get("description", "")
        if not description:
            continue
        
        # Find all {variable} patterns
        matches = re.findall(r'\{(\w+)\}', description)
        for match in matches:
            # Skip common CrewAI internal variables
            if match not in ['agent', 'task', 'crew', 'context']:
                variables.add(match)
    
    return sorted(list(variables))

