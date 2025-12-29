"""
LangGraph workflow export adapter.

Exports LangGraph StateGraph objects to Omium workflow format.
"""

import logging
from typing import Dict, Any, Optional, List
import inspect

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END, START
    from langgraph.graph.state import CompiledStateGraph
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    CompiledStateGraph = None
    END = None
    START = None


def export_langgraph_workflow(
    graph: CompiledStateGraph,
    workflow_name: Optional[str] = None,
    workflow_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export a LangGraph CompiledStateGraph to Omium workflow format.
    
    This function inspects a LangGraph graph and extracts:
    - Nodes (name, function reference)
    - Edges (from, to relationships)
    - State schema information
    
    Args:
        graph: Compiled LangGraph StateGraph instance to export
        workflow_name: Optional name for the workflow (defaults to "langgraph-workflow")
        workflow_id: Optional workflow ID (defaults to workflow_name)
        
    Returns:
        Dictionary in Omium workflow format
        
    Raises:
        ImportError: If LangGraph is not installed
        ValueError: If graph is not a valid CompiledStateGraph instance
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(
            "LangGraph is not installed. Install it with: pip install langgraph"
        )
    
    if not isinstance(graph, CompiledStateGraph):
        # Try to get the underlying graph if it's wrapped
        if hasattr(graph, 'graph'):
            graph = graph.graph
        else:
            raise ValueError(
                f"Expected CompiledStateGraph instance, got {type(graph)}. "
                "Note: You may need to compile the graph first with graph.compile()"
            )
    
    # Extract workflow name
    if not workflow_name:
        workflow_name = getattr(graph, 'name', None) or "langgraph-workflow"
    
    if not workflow_id:
        workflow_id = workflow_name
    
    # Extract nodes
    nodes = []
    edges = []
    
    # Try to get graph structure
    # LangGraph stores nodes and edges internally
    graph_nodes = getattr(graph, 'nodes', {})
    graph_edges = getattr(graph, 'edges', {})
    
    # If nodes/edges are not directly accessible, try alternative methods
    if not graph_nodes:
        # Try to get from _nodes attribute (internal)
        graph_nodes = getattr(graph, '_nodes', {})
    
    if not graph_edges:
        # Try to get from _edges attribute (internal)
        graph_edges = getattr(graph, '_edges', {})
    
    # Extract nodes
    if graph_nodes:
        for node_name, node_func in graph_nodes.items():
            # Skip special nodes
            if node_name in [START, END, "__start__", "__end__"]:
                continue
            
            node_dict = {
                "name": str(node_name),
                "function": _get_function_name(node_func),
            }
            
            # Try to extract function metadata
            if inspect.isfunction(node_func) or inspect.ismethod(node_func):
                if hasattr(node_func, '__name__'):
                    node_dict["function_name"] = node_func.__name__
                if hasattr(node_func, '__doc__') and node_func.__doc__:
                    node_dict["description"] = node_func.__doc__.strip().split('\n')[0]
            
            nodes.append(node_dict)
    else:
        # Fallback: try to inspect the graph structure differently
        logger.warning("Could not directly access graph nodes. Using fallback method.")
        nodes = _extract_nodes_fallback(graph)
    
    # Extract edges
    if graph_edges:
        for from_node, to_nodes in graph_edges.items():
            if not isinstance(to_nodes, list):
                to_nodes = [to_nodes]
            
            for to_node in to_nodes:
                # Handle START and END constants
                from_name = str(from_node) if from_node not in [START, "__start__"] else "START"
                to_name = str(to_node) if to_node not in [END, "__end__"] else "END"
                
                edge_dict = {
                    "from": from_name,
                    "to": to_name,
                }
                
                edges.append(edge_dict)
    else:
        # Fallback: try to reconstruct edges from graph structure
        logger.warning("Could not directly access graph edges. Using fallback method.")
        edges = _extract_edges_fallback(graph, nodes)
    
    # If we still don't have nodes/edges, create a minimal structure
    if not nodes:
        logger.warning("Could not extract nodes from graph. Creating minimal structure.")
        nodes = [{"name": "process", "function": "default_process"}]
        edges = [
            {"from": "START", "to": "process"},
            {"from": "process", "to": "END"}
        ]
    
    # Build Omium workflow definition
    workflow_definition = {
        "name": workflow_name,
        "nodes": nodes,
        "edges": edges,
    }
    
    # Build full Omium workflow format
    omium_workflow = {
        "type": "langgraph",
        "workflow_id": workflow_id,
        "agent_id": f"{workflow_id}-agent",
        "inputs": {
            "messages": [],
            "data": {
                "input": "Your input here"
            }
        },
        "definition": workflow_definition
    }
    
    logger.info(f"Exported LangGraph workflow '{workflow_name}' with {len(nodes)} nodes and {len(edges)} edges")
    
    return omium_workflow


def _get_function_name(func) -> str:
    """
    Get a string representation of a function name.
    
    Args:
        func: Function object
        
    Returns:
        Function name as string
    """
    if inspect.isfunction(func) or inspect.ismethod(func):
        return func.__name__
    elif hasattr(func, '__name__'):
        return func.__name__
    elif hasattr(func, '__class__'):
        return func.__class__.__name__
    else:
        return "unknown_function"


def _extract_nodes_fallback(graph) -> List[Dict[str, Any]]:
    """
    Fallback method to extract nodes from graph when direct access fails.
    
    Args:
        graph: LangGraph StateGraph instance
        
    Returns:
        List of node dictionaries
    """
    nodes = []
    
    # Try to use graph introspection
    if hasattr(graph, '__dict__'):
        graph_dict = graph.__dict__
        
        # Look for node-related attributes
        for key, value in graph_dict.items():
            if 'node' in key.lower() and isinstance(value, dict):
                for node_name, node_func in value.items():
                    if node_name in [START, END, "__start__", "__end__"]:
                        continue
                    
                    nodes.append({
                        "name": str(node_name),
                        "function": _get_function_name(node_func),
                    })
    
    return nodes


def _extract_edges_fallback(graph, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fallback method to extract edges from graph when direct access fails.
    
    Args:
        graph: LangGraph StateGraph instance
        nodes: List of extracted nodes
        
    Returns:
        List of edge dictionaries
    """
    edges = []
    
    # If we have nodes, create a simple linear flow
    if nodes:
        node_names = [node["name"] for node in nodes]
        
        # Create edges: START -> first_node -> ... -> last_node -> END
        if node_names:
            # START to first node
            edges.append({
                "from": "START",
                "to": node_names[0]
            })
            
            # Between nodes
            for i in range(len(node_names) - 1):
                edges.append({
                    "from": node_names[i],
                    "to": node_names[i + 1]
                })
            
            # Last node to END
            edges.append({
                "from": node_names[-1],
                "to": "END"
            })
    else:
        # Minimal fallback
        edges = [
            {"from": "START", "to": "process"},
            {"from": "process", "to": "END"}
        ]
    
    return edges

