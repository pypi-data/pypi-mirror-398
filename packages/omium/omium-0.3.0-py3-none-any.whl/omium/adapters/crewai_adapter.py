"""
CrewAI workflow export adapter.

Exports CrewAI Crew objects to Omium workflow format.
"""

import logging
from typing import Dict, Any, Optional, List
import json

logger = logging.getLogger(__name__)

try:
    from crewai import Agent, Task, Crew
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Task = None
    Crew = None


def export_crewai_workflow(
    crew: Crew,
    workflow_name: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export a CrewAI Crew object to Omium workflow format.
    
    This function inspects a CrewAI Crew object and extracts:
    - Agents (role, goal, backstory, verbose, allow_delegation, LLM config)
    - Tasks (description, agent assignment, expected_output)
    - LLM configuration
    - Crew settings (verbose, etc.)
    
    Args:
        crew: CrewAI Crew instance to export
        workflow_name: Optional name for the workflow (defaults to crew name or "crewai-workflow")
        workflow_id: Optional workflow ID (defaults to workflow_name)
        
    Returns:
        Dictionary in Omium workflow format
        
    Raises:
        ImportError: If CrewAI is not installed
        ValueError: If crew is not a valid Crew instance
    """
    if not CREWAI_AVAILABLE:
        raise ImportError(
            "CrewAI is not installed. Install it with: pip install crewai"
        )
    
    if not isinstance(crew, Crew):
        raise ValueError(f"Expected CrewAI Crew instance, got {type(crew)}")
    
    # Extract workflow name
    if not workflow_name:
        workflow_name = getattr(crew, 'name', None) or getattr(crew, 'crew_name', None) or "crewai-workflow"
    
    if not workflow_id:
        workflow_id = workflow_name
    
    # Extract agents
    agents = []
    crew_agents = getattr(crew, 'agents', [])
    
    for i, agent in enumerate(crew_agents):
        if not isinstance(agent, Agent):
            logger.warning(f"Agent {i} is not a CrewAI Agent instance, skipping")
            continue
        
        # Extract agent properties
        agent_dict = {
            "role": getattr(agent, 'role', f"agent_{i}"),
            "goal": getattr(agent, 'goal', ""),
            "backstory": getattr(agent, 'backstory', ""),
            "verbose": getattr(agent, 'verbose', True),
            "allow_delegation": getattr(agent, 'allow_delegation', False),
        }
        
        # Extract LLM configuration if available
        llm = getattr(agent, 'llm', None)
        if llm:
            llm_info = _extract_llm_config(llm)
            if llm_info:
                agent_dict["llm"] = llm_info
        
        # Extract tools if available
        tools = getattr(agent, 'tools', None)
        if tools:
            agent_dict["tools"] = _extract_tools(tools)
        
        agents.append(agent_dict)
    
    # Extract tasks
    tasks = []
    crew_tasks = getattr(crew, 'tasks', [])
    
    for i, task in enumerate(crew_tasks):
        if not isinstance(task, Task):
            logger.warning(f"Task {i} is not a CrewAI Task instance, skipping")
            continue
        
        # Find which agent this task is assigned to
        task_agent = getattr(task, 'agent', None)
        agent_index = None
        
        if task_agent:
            # Find agent index in crew.agents
            try:
                agent_index = crew_agents.index(task_agent)
            except ValueError:
                # Agent not found in crew, try to match by role
                if hasattr(task_agent, 'role'):
                    for idx, agent in enumerate(crew_agents):
                        if hasattr(agent, 'role') and agent.role == task_agent.role:
                            agent_index = idx
                            break
        
        task_dict = {
            "description": getattr(task, 'description', ""),
            "agent_index": agent_index if agent_index is not None else 0,
            "expected_output": getattr(task, 'expected_output', ""),
        }
        
        # Extract task context/dependencies if available
        if hasattr(task, 'context'):
            context = getattr(task, 'context', None)
            if context:
                task_dict["context"] = context if isinstance(context, list) else [context]
        
        # Extract additional task properties if available
        if hasattr(task, 'async_execution'):
            task_dict["async_execution"] = getattr(task, 'async_execution', False)
        
        tasks.append(task_dict)
    
    # Extract LLM configuration from crew or first agent
    llm_config = None
    if agents and agents[0].get("llm"):
        llm_config = agents[0]["llm"]
    else:
        # Try to get LLM from crew itself
        crew_llm = getattr(crew, 'llm', None)
        if crew_llm:
            llm_config = _extract_llm_config(crew_llm)
    
    # Default LLM config if none found
    if not llm_config:
        llm_config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
    
    # Extract crew-level settings
    verbose = getattr(crew, 'verbose', True)
    
    # Build Omium workflow definition
    workflow_definition = {
        "name": workflow_name,
        "verbose": verbose,
        "llm": llm_config,
        "agents": agents,
        "tasks": tasks,
    }
    
    # Extract input variables from task descriptions
    input_variables = _extract_input_variables(tasks)
    
    # Build default inputs dict from extracted variables
    default_inputs = {}
    for var in input_variables:
        default_inputs[var] = f"Your {var.replace('_', ' ')} here"
    
    # If no variables found, use default
    if not default_inputs:
        default_inputs = {
            "topic": "Your input here"
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


def _extract_llm_config(llm) -> Optional[Dict[str, Any]]:
    """
    Extract LLM configuration from a CrewAI or LangChain LLM object.
    
    Handles CrewAI's LLM class which uses format like "openai/gpt-4o-mini"
    
    Args:
        llm: LLM instance (CrewAI or LangChain)
        
    Returns:
        Dictionary with LLM configuration or None
    """
    if llm is None:
        return None
    
    config = {}
    
    # Try to get model name - CrewAI LLM class may store it differently
    model_name = None
    
    # CrewAI LLM class may have model attribute as string like "openai/gpt-4o-mini"
    if hasattr(llm, 'model'):
        model_attr = llm.model
        if isinstance(model_attr, str):
            model_name = model_attr
        else:
            model_name = str(model_attr)
    elif hasattr(llm, 'model_name'):
        model_name = llm.model_name
    elif hasattr(llm, '_model'):
        model_name = getattr(llm, '_model', None)
    
    # Parse model string if it's in "provider/model" format (e.g., "openai/gpt-4o-mini")
    provider = "openai"  # default
    parsed_model = None
    
    if model_name:
        # Check if model_name is in "provider/model" format
        if '/' in model_name:
            parts = model_name.split('/', 1)
            provider = parts[0].lower()
            parsed_model = parts[1]
        else:
            parsed_model = model_name
        
        config["model"] = parsed_model
    
    # Try to get temperature
    if hasattr(llm, 'temperature'):
        config["temperature"] = llm.temperature
    elif hasattr(llm, 'model_kwargs') and isinstance(llm.model_kwargs, dict):
        config["temperature"] = llm.model_kwargs.get("temperature", 0.7)
    elif hasattr(llm, '_temperature'):
        config["temperature"] = getattr(llm, '_temperature', 0.7)
    else:
        config["temperature"] = 0.7  # default
    
    # Determine provider from class name if not already set
    if provider == "openai":  # Only override if we didn't parse from model string
        llm_class_name = type(llm).__name__.lower()
        
        if "anthropic" in llm_class_name or "claude" in llm_class_name:
            provider = "anthropic"
        elif "openai" in llm_class_name or "gpt" in llm_class_name:
            provider = "openai"
        elif "megallm" in llm_class_name:
            provider = "megallm"
        elif "digitalocean" in llm_class_name or "do" in llm_class_name:
            provider = "digitalocean"
    
    config["provider"] = provider
    
    # Try to get API key and base URL (if accessible)
    if hasattr(llm, 'api_key'):
        config["api_key"] = llm.api_key
    if hasattr(llm, 'base_url'):
        config["base_url"] = llm.base_url
    elif hasattr(llm, 'openai_api_base'):
        config["base_url"] = llm.openai_api_base
    elif hasattr(llm, '_base_url'):
        config["base_url"] = getattr(llm, '_base_url', None)
    
    return config if config else None


def _extract_tools(tools) -> List[Dict[str, Any]]:
    """
    Extract tool information from a list of tools.
    
    Handles CrewAI tools like ScrapeWebsiteTool, BraveSearchTool, etc.
    
    Args:
        tools: List of tool objects
        
    Returns:
        List of tool dictionaries
    """
    if not tools:
        return []
    
    tool_list = []
    for tool in tools:
        tool_dict = {
            "name": getattr(tool, 'name', type(tool).__name__),
            "type": type(tool).__name__,
        }
        
        # Try to extract description
        if hasattr(tool, 'description'):
            tool_dict["description"] = tool.description
        
        # Extract tool class/module info for better identification
        tool_class = type(tool)
        tool_dict["class_name"] = tool_class.__name__
        if hasattr(tool_class, '__module__'):
            tool_dict["module"] = tool_class.__module__
        
        # For crewai_tools, try to get more info
        if hasattr(tool, 'args_schema'):
            tool_dict["has_args_schema"] = True
        
        tool_list.append(tool_dict)
    
    return tool_list


def _extract_input_variables(tasks: List[Dict[str, Any]]) -> List[str]:
    """
    Extract input variables from task descriptions.
    
    Looks for patterns like {variable_name} in task descriptions.
    
    Args:
        tasks: List of task dictionaries with descriptions
        
    Returns:
        List of unique variable names found
    """
    import re
    
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

