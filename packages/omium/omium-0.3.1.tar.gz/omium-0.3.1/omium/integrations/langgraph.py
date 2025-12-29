"""
LangGraph Integration - Auto-instrumentation for LangGraph workflows

This module provides automatic instrumentation for LangGraph, capturing
traces and checkpoints for every graph execution without requiring
code changes.

Instrumentation is applied by monkey-patching key LangGraph methods:
- CompiledStateGraph.invoke() - synchronous execution
- CompiledStateGraph.ainvoke() - async execution
- CompiledStateGraph.stream() - streaming execution

All state transitions and node executions are automatically traced.
"""

import logging
import functools
import asyncio
from typing import Any, Dict, Iterator, Optional, Callable, AsyncIterator
from datetime import datetime
import uuid

logger = logging.getLogger("omium.langgraph")

# Store original methods for restoration
_original_invoke = None
_original_ainvoke = None
_original_stream = None
_original_astream = None
_instrumented = False


def instrument_langgraph():
    """
    Instrument LangGraph for automatic tracing and checkpointing.
    
    This patches the following methods on CompiledStateGraph:
    - invoke() - synchronous execution
    - ainvoke() - async execution
    - stream() - synchronous streaming
    - astream() - async streaming
    
    Call this function once at application startup, or use omium.init()
    which calls this automatically when LangGraph is detected.
    
    Example:
        ```python
        from omium.integrations import instrument_langgraph
        instrument_langgraph()
        
        # Now all LangGraph executions are automatically traced
        graph = workflow.compile()
        result = graph.invoke({"input": "hello"})
        ```
    """
    global _original_invoke, _original_ainvoke, _original_stream, _original_astream
    global _instrumented
    
    if _instrumented:
        logger.debug("LangGraph already instrumented")
        return
    
    try:
        from langgraph.graph.state import CompiledStateGraph
    except ImportError:
        raise ImportError(
            "LangGraph is not installed. Install with: pip install langgraph"
        )
    
    # Store original methods
    _original_invoke = CompiledStateGraph.invoke
    _original_ainvoke = CompiledStateGraph.ainvoke
    
    # Check for streaming methods (may not exist in all versions)
    if hasattr(CompiledStateGraph, 'stream'):
        _original_stream = CompiledStateGraph.stream
    if hasattr(CompiledStateGraph, 'astream'):
        _original_astream = CompiledStateGraph.astream
    
    # Apply patches
    CompiledStateGraph.invoke = _patched_invoke
    CompiledStateGraph.ainvoke = _patched_ainvoke
    
    if _original_stream:
        CompiledStateGraph.stream = _patched_stream
    if _original_astream:
        CompiledStateGraph.astream = _patched_astream
    
    _instrumented = True
    logger.info("LangGraph instrumentation applied successfully")


def uninstrument_langgraph():
    """
    Remove LangGraph instrumentation.
    
    Restores the original methods on CompiledStateGraph.
    """
    global _original_invoke, _original_ainvoke, _original_stream, _original_astream
    global _instrumented
    
    if not _instrumented:
        return
    
    try:
        from langgraph.graph.state import CompiledStateGraph
    except ImportError:
        return
    
    # Restore original methods
    if _original_invoke:
        CompiledStateGraph.invoke = _original_invoke
    if _original_ainvoke:
        CompiledStateGraph.ainvoke = _original_ainvoke
    if _original_stream:
        CompiledStateGraph.stream = _original_stream
    if _original_astream:
        CompiledStateGraph.astream = _original_astream
    
    _instrumented = False
    logger.info("LangGraph instrumentation removed")


def _get_graph_name(graph) -> str:
    """Extract a meaningful name from the graph."""
    # Try different attributes that might contain the name
    if hasattr(graph, 'name') and graph.name:
        return graph.name
    if hasattr(graph, '_name') and graph._name:
        return graph._name
    if hasattr(graph, 'builder') and hasattr(graph.builder, 'name'):
        return graph.builder.name
    return "langgraph"


def _get_node_names(graph) -> list:
    """Extract node names from the graph."""
    try:
        if hasattr(graph, 'nodes'):
            return list(graph.nodes.keys())
    except Exception:
        pass
    return []


def _safe_serialize(obj, max_depth: int = 3, current_depth: int = 0) -> Any:
    """
    Safely serialize an object for JSON, handling LangChain message types.
    
    Converts HumanMessage, AIMessage, SystemMessage etc. to dictionaries.
    """
    if current_depth > max_depth:
        return str(obj)[:200] + "..." if len(str(obj)) > 200 else str(obj)
    
    # Handle None
    if obj is None:
        return None
    
    # Handle basic types
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Handle LangChain message types
    if hasattr(obj, 'content') and hasattr(obj, 'type'):
        # This is likely a LangChain message (HumanMessage, AIMessage, etc.)
        return {
            "type": getattr(obj, 'type', type(obj).__name__),
            "content": str(obj.content)[:500] if len(str(obj.content)) > 500 else str(obj.content),
        }
    
    # Handle lists
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(item, max_depth, current_depth + 1) for item in obj[:20]]  # Limit to 20 items
    
    # Handle dicts
    if isinstance(obj, dict):
        result = {}
        for k, v in list(obj.items())[:30]:  # Limit to 30 keys
            try:
                result[str(k)] = _safe_serialize(v, max_depth, current_depth + 1)
            except Exception:
                result[str(k)] = str(v)[:200]
        return result
    
    # Handle objects with to_dict method
    if hasattr(obj, 'to_dict'):
        try:
            return _safe_serialize(obj.to_dict(), max_depth, current_depth + 1)
        except Exception:
            pass
    
    # Handle objects with dict() method
    if hasattr(obj, '__dict__'):
        try:
            return {
                "_type": type(obj).__name__,
                "_repr": str(obj)[:300]
            }
        except Exception:
            pass
    
    # Fallback to string representation
    return str(obj)[:500] if len(str(obj)) > 500 else str(obj)


@functools.wraps(_original_invoke if _original_invoke else lambda *a, **k: None)
def _patched_invoke(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs):
    """Instrumented invoke with tracing and checkpointing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    # Skip instrumentation if not initialized or disabled
    if not is_initialized():
        return _original_invoke(self, input, config, **kwargs)
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        return _original_invoke(self, input, config, **kwargs)
    
    # Create tracer for this execution
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    graph_name = _get_graph_name(self)
    node_names = _get_node_names(self)
    
    # Prepare input data (safely serialized for JSON)
    input_preview = _safe_serialize(input or {})
    
    with tracer.span(
        f"langgraph.invoke:{graph_name}",
        span_type="graph",
        input=input_preview,
        graph_name=graph_name,
        node_count=len(node_names),
        nodes=node_names[:10],  # First 10 nodes
    ) as root_span:
        try:
            logger.debug(f"Starting LangGraph execution: {graph_name}")
            
            # Execute the graph
            result = _original_invoke(self, input, config, **kwargs)
            
            # Capture output (safely serialized for JSON)
            output_preview = _safe_serialize(result)
            root_span.set_output(output_preview)
            
            logger.debug(f"LangGraph execution completed: {graph_name}")
            return result
            
        except Exception as e:
            root_span.set_error(e)
            logger.debug(f"LangGraph execution failed: {graph_name} - {e}")
            raise
            
        finally:
            tracer.flush()


@functools.wraps(_original_ainvoke if _original_ainvoke else lambda *a, **k: None)
async def _patched_ainvoke(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs):
    """Instrumented ainvoke with tracing and checkpointing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    if not is_initialized():
        return await _original_ainvoke(self, input, config, **kwargs)
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        return await _original_ainvoke(self, input, config, **kwargs)
    
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    graph_name = _get_graph_name(self)
    node_names = _get_node_names(self)
    
    input_preview = _safe_serialize(input or {})
    
    with tracer.span(
        f"langgraph.ainvoke:{graph_name}",
        span_type="graph",
        input=input_preview,
        graph_name=graph_name,
        node_count=len(node_names),
        nodes=node_names[:10],
    ) as root_span:
        try:
            logger.debug(f"Starting async LangGraph execution: {graph_name}")
            
            result = await _original_ainvoke(self, input, config, **kwargs)
            
            output_preview = _safe_serialize(result)
            root_span.set_output(output_preview)
            
            logger.debug(f"Async LangGraph execution completed: {graph_name}")
            return result
            
        except Exception as e:
            root_span.set_error(e)
            logger.debug(f"Async LangGraph execution failed: {graph_name} - {e}")
            raise
            
        finally:
            await tracer.aflush()


def _patched_stream(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs) -> Iterator:
    """Instrumented stream with tracing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    if not is_initialized():
        yield from _original_stream(self, input, config, **kwargs)
        return
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        yield from _original_stream(self, input, config, **kwargs)
        return
    
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    graph_name = _get_graph_name(self)
    chunks_count = 0
    
    with tracer.span(
        f"langgraph.stream:{graph_name}",
        span_type="graph_stream",
        graph_name=graph_name,
    ) as root_span:
        try:
            for chunk in _original_stream(self, input, config, **kwargs):
                chunks_count += 1
                
                # Add event for significant chunks (every 10th or state updates)
                if chunks_count % 10 == 0:
                    tracer.add_event("stream_chunk", {
                        "chunk_number": chunks_count,
                    })
                
                yield chunk
            
            root_span.set_attribute("total_chunks", chunks_count)
            root_span.set_output(f"Streamed {chunks_count} chunks")
            
        except Exception as e:
            root_span.set_error(e)
            raise
            
        finally:
            tracer.flush()


async def _patched_astream(self, input: Dict[str, Any], config: Optional[Dict] = None, **kwargs) -> AsyncIterator:
    """Instrumented astream with tracing."""
    from omium.integrations.core import get_current_config, is_initialized
    from omium.integrations.tracer import OmiumTracer
    
    if not is_initialized():
        async for chunk in _original_astream(self, input, config, **kwargs):
            yield chunk
        return
    
    omium_config = get_current_config()
    if not omium_config or not omium_config.auto_trace:
        async for chunk in _original_astream(self, input, config, **kwargs):
            yield chunk
        return
    
    execution_id = str(uuid.uuid4())
    tracer = OmiumTracer(
        execution_id=execution_id,
        project=omium_config.project
    )
    
    graph_name = _get_graph_name(self)
    chunks_count = 0
    
    with tracer.span(
        f"langgraph.astream:{graph_name}",
        span_type="graph_stream",
        graph_name=graph_name,
    ) as root_span:
        try:
            async for chunk in _original_astream(self, input, config, **kwargs):
                chunks_count += 1
                
                if chunks_count % 10 == 0:
                    tracer.add_event("stream_chunk", {
                        "chunk_number": chunks_count,
                    })
                
                yield chunk
            
            root_span.set_attribute("total_chunks", chunks_count)
            root_span.set_output(f"Streamed {chunks_count} chunks")
            
        except Exception as e:
            root_span.set_error(e)
            raise
            
        finally:
            await tracer.aflush()


def is_instrumented() -> bool:
    """Check if LangGraph is currently instrumented."""
    return _instrumented
