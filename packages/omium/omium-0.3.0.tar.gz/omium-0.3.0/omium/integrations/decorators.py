"""
Omium Decorators - Manual tracing and checkpointing

This module provides decorators for explicit tracing and checkpointing
when auto-instrumentation is not sufficient or desired.
"""

import functools
import asyncio
import logging
import inspect
from typing import Callable, Optional, Any, TypeVar, Union
import uuid

logger = logging.getLogger("omium.decorators")

F = TypeVar('F', bound=Callable[..., Any])


def trace(
    name: Optional[str] = None,
    span_type: str = "function",
    capture_input: bool = True,
    capture_output: bool = True,
    capture_errors: bool = True,
    **default_attributes
) -> Callable[[F], F]:
    """
    Decorator to trace a function.
    
    Automatically creates a span for the decorated function, capturing
    input arguments, output, errors, and timing.
    
    Args:
        name: Span name. Defaults to function name.
        span_type: Type of span (function, tool, llm, etc.)
        capture_input: Whether to capture function arguments
        capture_output: Whether to capture return value
        capture_errors: Whether to capture exceptions
        **default_attributes: Additional attributes to add to every span
    
    Returns:
        Decorated function
    
    Example:
        ```python
        import omium
        
        @omium.trace("research_step")
        def research(topic: str) -> str:
            # ... research logic ...
            return results
        
        @omium.trace(capture_input=False)  # Don't log sensitive inputs
        def process_secret(secret: str) -> bool:
            return validate(secret)
        ```
    """
    def decorator(func: F) -> F:
        span_name = name or func.__name__
        
        # Check if async
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            from omium.integrations.core import get_current_config, is_initialized
            from omium.integrations.tracer import OmiumTracer, get_current_tracer
            
            # Skip if not initialized or tracing disabled
            config = get_current_config()
            if not is_initialized() or not config or not config.auto_trace:
                return func(*args, **kwargs)
            
            # Get or create tracer
            tracer = get_current_tracer()
            should_flush = False
            
            if not tracer:
                tracer = OmiumTracer()
                should_flush = True
            
            # Prepare input data
            input_data = None
            if capture_input:
                input_data = _capture_args(func, args, kwargs)
            
            # Create span
            with tracer.span(
                span_name,
                input=input_data,
                span_type=span_type,
                **default_attributes
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    
                    if capture_output:
                        span.set_output(_safe_repr(result))
                    
                    return result
                    
                except Exception as e:
                    if capture_errors:
                        span.set_error(e)
                    raise
                
                finally:
                    if should_flush:
                        tracer.flush()
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            from omium.integrations.core import get_current_config, is_initialized
            from omium.integrations.tracer import OmiumTracer, get_current_tracer
            
            config = get_current_config()
            if not is_initialized() or not config or not config.auto_trace:
                return await func(*args, **kwargs)
            
            tracer = get_current_tracer()
            should_flush = False
            
            if not tracer:
                tracer = OmiumTracer()
                should_flush = True
            
            input_data = None
            if capture_input:
                input_data = _capture_args(func, args, kwargs)
            
            with tracer.span(
                span_name,
                input=input_data,
                span_type=span_type,
                **default_attributes
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    
                    if capture_output:
                        span.set_output(_safe_repr(result))
                    
                    return result
                    
                except Exception as e:
                    if capture_errors:
                        span.set_error(e)
                    raise
                
                finally:
                    if should_flush:
                        await tracer.aflush()
        
        if is_async:
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def checkpoint(
    name: str,
    capture_state: bool = True,
    on_error: str = "skip",  # "skip", "raise", "log"
) -> Callable[[F], F]:
    """
    Decorator to create a checkpoint before executing a function.
    
    Checkpoints capture the current state and can be used to replay
    execution from that point.
    
    Args:
        name: Checkpoint name (descriptive, e.g., "after_research", "before_summarize")
        capture_state: Whether to capture function arguments in checkpoint
        on_error: What to do if checkpoint creation fails:
                  - "skip": Continue execution without checkpoint
                  - "raise": Raise the error
                  - "log": Log warning and continue
    
    Returns:
        Decorated function
    
    Example:
        ```python
        import omium
        
        @omium.checkpoint("before_research")
        def research_step(topic: str) -> Dict:
            # ... expensive research ...
            return results
        
        @omium.checkpoint("after_analysis", capture_state=False)
        def analyze(data: Dict) -> str:
            return analysis
        ```
    """
    def decorator(func: F) -> F:
        is_async = asyncio.iscoroutinefunction(func)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            from omium.integrations.core import get_current_config, is_initialized
            
            config = get_current_config()
            
            # Create checkpoint if enabled
            if is_initialized() and config and config.auto_checkpoint:
                try:
                    _create_checkpoint_sync(
                        name=name,
                        state=_capture_args(func, args, kwargs) if capture_state else None,
                        config=config
                    )
                except Exception as e:
                    if on_error == "raise":
                        raise
                    elif on_error == "log":
                        logger.warning(f"Failed to create checkpoint '{name}': {e}")
                    # "skip" - do nothing
            
            return func(*args, **kwargs)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            from omium.integrations.core import get_current_config, is_initialized
            
            config = get_current_config()
            
            if is_initialized() and config and config.auto_checkpoint:
                try:
                    await _create_checkpoint_async(
                        name=name,
                        state=_capture_args(func, args, kwargs) if capture_state else None,
                        config=config
                    )
                except Exception as e:
                    if on_error == "raise":
                        raise
                    elif on_error == "log":
                        logger.warning(f"Failed to create checkpoint '{name}': {e}")
            
            return await func(*args, **kwargs)
        
        if is_async:
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore
    
    return decorator


def _capture_args(func: Callable, args: tuple, kwargs: dict) -> dict:
    """
    Capture function arguments as a dictionary.
    
    Tries to map positional args to their parameter names.
    """
    result = {}
    
    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        # Map positional args
        for i, arg in enumerate(args):
            if i < len(params):
                param_name = params[i]
                # Skip 'self' and 'cls'
                if param_name not in ('self', 'cls'):
                    result[param_name] = _safe_repr(arg)
        
        # Add keyword args
        for key, value in kwargs.items():
            result[key] = _safe_repr(value)
            
    except Exception:
        # Fallback: just use indices
        for i, arg in enumerate(args):
            result[f"arg_{i}"] = _safe_repr(arg)
        result.update({k: _safe_repr(v) for k, v in kwargs.items()})
    
    return result


def _safe_repr(obj: Any, max_length: int = 500) -> Any:
    """
    Safely represent an object, truncating if necessary.
    """
    try:
        if obj is None:
            return None
        
        if isinstance(obj, (str, int, float, bool)):
            if isinstance(obj, str) and len(obj) > max_length:
                return obj[:max_length] + f"... ({len(obj)} total)"
            return obj
        
        if isinstance(obj, dict):
            return {k: _safe_repr(v, max_length // 2) for k, v in list(obj.items())[:20]}
        
        if isinstance(obj, (list, tuple)):
            items = [_safe_repr(item, max_length // 2) for item in obj[:20]]
            if len(obj) > 20:
                items.append(f"... ({len(obj)} total items)")
            return items
        
        # Try string representation
        s = str(obj)
        if len(s) > max_length:
            return s[:max_length] + f"... ({len(s)} total)"
        return s
        
    except Exception:
        return f"<{type(obj).__name__}>"


def _create_checkpoint_sync(
    name: str,
    state: Optional[dict],
    config: Any
) -> Optional[str]:
    """Create a checkpoint synchronously."""
    from omium.integrations.tracer import get_current_tracer
    
    tracer = get_current_tracer()
    execution_id = tracer.execution_id if tracer else str(uuid.uuid4())
    
    logger.info(f"📍 Checkpoint: {name}")
    
    # For now, add as an event in the current span
    # Full checkpoint implementation would use the gRPC client
    if tracer and tracer.current_span:
        tracer.current_span.add_event(f"checkpoint:{name}", {
            "checkpoint_name": name,
            "has_state": state is not None,
        })
    
    # TODO: Full checkpoint implementation
    # try:
    #     from omium.client import OmiumClient
    #     async with OmiumClient(checkpoint_manager_url=config.checkpoint_manager_url) as client:
    #         await client.create_checkpoint(
    #             checkpoint_name=name,
    #             state=state or {},
    #             execution_id=execution_id,
    #         )
    # except Exception as e:
    #     logger.warning(f"Checkpoint creation failed: {e}")
    
    return None


async def _create_checkpoint_async(
    name: str,
    state: Optional[dict],
    config: Any
) -> Optional[str]:
    """Create a checkpoint asynchronously."""
    from omium.integrations.tracer import get_current_tracer
    
    tracer = get_current_tracer()
    execution_id = tracer.execution_id if tracer else str(uuid.uuid4())
    
    logger.info(f"📍 Checkpoint: {name}")
    
    if tracer and tracer.current_span:
        tracer.current_span.add_event(f"checkpoint:{name}", {
            "checkpoint_name": name,
            "has_state": state is not None,
        })
    
    # TODO: Full async checkpoint implementation
    
    return None
