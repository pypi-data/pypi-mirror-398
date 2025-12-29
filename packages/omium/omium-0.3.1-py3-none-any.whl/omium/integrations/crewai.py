"""
CrewAI Integration - Auto-instrumentation for CrewAI workflows

This module provides automatic instrumentation for CrewAI, capturing
traces and checkpoints for every crew execution without requiring
code changes.

Instrumentation is applied by monkey-patching key CrewAI methods:
- Crew.kickoff() - main execution method
- Crew.kickoff_async() - async execution (if available)

All agent executions and task completions are automatically traced.
"""

import logging
import functools
import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
import uuid

logger = logging.getLogger("omium.crewai")

# Store original methods for restoration
_original_kickoff = None
_original_kickoff_async = None
_original_kickoff_for_each = None
_instrumented = False


def instrument_crewai():
    """
    Instrument CrewAI for automatic tracing and checkpointing.
    
    This patches the following methods on Crew:
    - kickoff() - main synchronous execution
    - kickoff_async() - async execution (if available)
    - kickoff_for_each() - batch execution (if available)
    
    Call this function once at application startup, or use omium.init()
    which calls this automatically when CrewAI is detected.
    
    Example:
        ```python
        from omium.integrations import instrument_crewai
        instrument_crewai()
        
        # Now all CrewAI executions are automatically traced
        crew = Crew(agents=[...], tasks=[...])
        result = crew.kickoff()
        ```
    """
    global _original_kickoff, _original_kickoff_async, _original_kickoff_for_each
    global _instrumented
    
    if _instrumented:
        logger.debug("CrewAI already instrumented")
        return
    
    try:
        from crewai import Crew
    except ImportError:
        raise ImportError(
            "CrewAI is not installed. Install with: pip install crewai"
        )
    
    # Store original methods
    _original_kickoff = Crew.kickoff
    
    if hasattr(Crew, 'kickoff_async'):
        _original_kickoff_async = Crew.kickoff_async
    
    if hasattr(Crew, 'kickoff_for_each'):
        _original_kickoff_for_each = Crew.kickoff_for_each
    
    # Apply patches
    Crew.kickoff = _patched_kickoff
    
    if _original_kickoff_async:
        Crew.kickoff_async = _patched_kickoff_async
    
    if _original_kickoff_for_each:
        Crew.kickoff_for_each = _patched_kickoff_for_each
    
    _instrumented = True
    logger.info("CrewAI instrumentation applied successfully")


def uninstrument_crewai():
    """
    Remove CrewAI instrumentation.
    
    Restores the original methods on Crew.
    """
    global _original_kickoff, _original_kickoff_async, _original_kickoff_for_each
    global _instrumented
    
    if not _instrumented:
        return
    
    try:
        from crewai import Crew
    except ImportError:
        return
    
    # Restore original methods
    if _original_kickoff:
        Crew.kickoff = _original_kickoff
    if _original_kickoff_async:
        Crew.kickoff_async = _original_kickoff_async
    if _original_kickoff_for_each:
        Crew.kickoff_for_each = _original_kickoff_for_each
    
    _instrumented = False
    logger.info("CrewAI instrumentation removed")


def _get_crew_info(crew) -> Dict[str, Any]:
    """Extract information about the crew for logging."""
    info = {
        "crew_name": getattr(crew, 'name', None) or "crew",
        "agent_count": 0,
        "task_count": 0,
        "agents": [],
        "tasks": [],
    }
    
    # Get agents
    try:
        if hasattr(crew, 'agents') and crew.agents:
            info["agent_count"] = len(crew.agents)
            for agent in crew.agents[:5]:  # First 5 agents
                agent_info = {
                    "role": getattr(agent, 'role', 'unknown'),
                    "goal": str(getattr(agent, 'goal', ''))[:100],
                }
                info["agents"].append(agent_info)
    except Exception as e:
        logger.debug(f"Error extracting agent info: {e}")
    
    # Get tasks
    try:
        if hasattr(crew, 'tasks') and crew.tasks:
            info["task_count"] = len(crew.tasks)
            for task in crew.tasks[:5]:  # First 5 tasks
                task_info = {
                    "description": str(getattr(task, 'description', ''))[:100],
                }
                if hasattr(task, 'agent') and task.agent:
                    task_info["agent_role"] = getattr(task.agent, 'role', 'unknown')
                info["tasks"].append(task_info)
    except Exception as e:
        logger.debug(f"Error extracting task info: {e}")
    
    return info


def _truncate_inputs(inputs: Optional[Dict]) -> Optional[Dict]:
    """Truncate input values for logging."""
    if not inputs:
        return None
    
    result = {}
    for k, v in inputs.items():
        if isinstance(v, str) and len(v) > 200:
            result[k] = v[:200] + "..."
        elif isinstance(v, dict):
            result[k] = _truncate_inputs(v)
        else:
            result[k] = v
    return result


@functools.wraps(_original_kickoff if _original_kickoff else lambda *a, **k: None)
def _patched_kickoff(self, inputs: Optional[Dict[str, Any]] = None, **kwargs):
    """Instrumented kickoff with tracing and checkpointing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    # Skip if not initialized
    if not is_initialized():
        return _original_kickoff(self, inputs, **kwargs)
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        return _original_kickoff(self, inputs, **kwargs)
    
    # Create tracer for this execution
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    crew_info = _get_crew_info(self)
    input_preview = _truncate_inputs(inputs)
    
    with tracer.span(
        f"crewai.kickoff:{crew_info['crew_name']}",
        span_type="crew",
        input=input_preview,
        crew_name=crew_info["crew_name"],
        agent_count=crew_info["agent_count"],
        task_count=crew_info["task_count"],
        agents=[a.get("role") for a in crew_info["agents"]],
    ) as root_span:
        try:
            logger.debug(
                f"Starting CrewAI execution: {crew_info['crew_name']} "
                f"({crew_info['agent_count']} agents, {crew_info['task_count']} tasks)"
            )
            
            # Set up step callback to capture agent activities
            original_step_callback = getattr(self, 'step_callback', None)
            
            def omium_step_callback(step_output):
                """Capture each step for tracing."""
                try:
                    tracer.add_event("crew_step", {
                        "output_preview": str(step_output)[:300] if step_output else None,
                    })
                except Exception:
                    pass
                
                # Call original callback if exists
                if original_step_callback:
                    return original_step_callback(step_output)
            
            # Temporarily set our callback
            self.step_callback = omium_step_callback
            
            try:
                result = _original_kickoff(self, inputs, **kwargs)
            finally:
                # Restore original callback
                self.step_callback = original_step_callback
            
            # Capture output
            if result is not None:
                if hasattr(result, 'raw'):
                    # CrewOutput object
                    output_str = str(result.raw)[:1000]
                else:
                    output_str = str(result)[:1000]
                root_span.set_output(output_str)
            
            logger.debug(f"CrewAI execution completed: {crew_info['crew_name']}")
            return result
            
        except Exception as e:
            root_span.set_error(e)
            logger.debug(f"CrewAI execution failed: {crew_info['crew_name']} - {e}")
            raise
            
        finally:
            tracer.flush()


@functools.wraps(_original_kickoff_async if _original_kickoff_async else lambda *a, **k: None)
async def _patched_kickoff_async(self, inputs: Optional[Dict[str, Any]] = None, **kwargs):
    """Instrumented kickoff_async with tracing and checkpointing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    if not is_initialized():
        return await _original_kickoff_async(self, inputs, **kwargs)
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        return await _original_kickoff_async(self, inputs, **kwargs)
    
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    crew_info = _get_crew_info(self)
    input_preview = _truncate_inputs(inputs)
    
    with tracer.span(
        f"crewai.kickoff_async:{crew_info['crew_name']}",
        span_type="crew",
        input=input_preview,
        crew_name=crew_info["crew_name"],
        agent_count=crew_info["agent_count"],
        task_count=crew_info["task_count"],
        agents=[a.get("role") for a in crew_info["agents"]],
    ) as root_span:
        try:
            logger.debug(f"Starting async CrewAI execution: {crew_info['crew_name']}")
            
            result = await _original_kickoff_async(self, inputs, **kwargs)
            
            if result is not None:
                if hasattr(result, 'raw'):
                    output_str = str(result.raw)[:1000]
                else:
                    output_str = str(result)[:1000]
                root_span.set_output(output_str)
            
            logger.debug(f"Async CrewAI execution completed: {crew_info['crew_name']}")
            return result
            
        except Exception as e:
            root_span.set_error(e)
            logger.debug(f"Async CrewAI execution failed: {crew_info['crew_name']} - {e}")
            raise
            
        finally:
            await tracer.aflush()


def _patched_kickoff_for_each(self, inputs: List[Dict[str, Any]], **kwargs):
    """Instrumented kickoff_for_each with tracing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    if not is_initialized():
        return _original_kickoff_for_each(self, inputs, **kwargs)
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        return _original_kickoff_for_each(self, inputs, **kwargs)
    
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    crew_info = _get_crew_info(self)
    
    with tracer.span(
        f"crewai.kickoff_for_each:{crew_info['crew_name']}",
        span_type="crew_batch",
        crew_name=crew_info["crew_name"],
        batch_size=len(inputs),
        agent_count=crew_info["agent_count"],
        task_count=crew_info["task_count"],
    ) as root_span:
        try:
            logger.debug(
                f"Starting CrewAI batch execution: {crew_info['crew_name']} "
                f"({len(inputs)} inputs)"
            )
            
            results = _original_kickoff_for_each(self, inputs, **kwargs)
            
            root_span.set_output(f"Processed {len(inputs)} inputs, got {len(results)} results")
            logger.debug(f"CrewAI batch execution completed: {crew_info['crew_name']}")
            
            return results
            
        except Exception as e:
            root_span.set_error(e)
            raise
            
        finally:
            tracer.flush()


def is_instrumented() -> bool:
    """Check if CrewAI is currently instrumented."""
    return _instrumented
