"""
Checkpoint decorator and context manager for Omium SDK.
"""

import asyncio
import functools
import inspect
import json
import logging
from typing import Callable, Any, Optional, List, Dict, Union
from contextlib import asynccontextmanager

from .client import OmiumClient, get_client, CheckpointError, CheckpointValidationError
from .remote_client import RemoteOmiumClient
from .config import get_config

logger = logging.getLogger(__name__)


def _serialize_state(obj: Any) -> Dict[str, Any]:
    """
    Serialize object to dictionary for checkpoint storage.
    
    Handles:
    - Dicts, lists, primitives
    - Objects with __dict__
    - JSON-serializable types
    """
    if isinstance(obj, dict):
        return {k: _serialize_state(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_state(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif hasattr(obj, "__dict__"):
        return _serialize_state(obj.__dict__)
    else:
        # Try JSON serialization
        try:
            return json.loads(json.dumps(obj, default=str))
        except (TypeError, ValueError):
            return {"_type": type(obj).__name__, "_repr": str(obj)}


def _capture_state(func: Callable, args: tuple, kwargs: dict, result: Any = None) -> Dict[str, Any]:
    """
    Capture function state for checkpointing.
    
    Args:
        func: Function being checkpointed
        args: Function arguments
        kwargs: Function keyword arguments
        result: Function result (if post-execution)
    
    Returns:
        State dictionary
    """
    sig = inspect.signature(func)
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()
    
    state = {
        "function": func.__name__,
        "module": func.__module__,
        "args": {},
        "kwargs": {},
    }
    
    # Capture arguments
    for param_name, param_value in bound_args.arguments.items():
        if param_name in sig.parameters:
            param = sig.parameters[param_name]
            if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                state["args"][param_name] = _serialize_state(param_value)
            elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                state["kwargs"][param_name] = _serialize_state(param_value)
    
    # Capture result if provided
    if result is not None:
        state["result"] = _serialize_state(result)
    
    return state


def checkpoint(
    name: str,
    preconditions: Optional[List[str]] = None,
    postconditions: Optional[List[str]] = None,
    client: Optional[Union[OmiumClient, RemoteOmiumClient]] = None,
    execution_id: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """
    Decorator to create a checkpoint before/after function execution.
    
    Args:
        name: Checkpoint name (must be unique per execution)
        preconditions: List of precondition strings (e.g., ["amount > 0", "user exists"])
        postconditions: List of postcondition strings
        client: Optional OmiumClient instance (uses global if not provided)
        execution_id: Optional execution ID (uses client context if not provided)
        agent_id: Optional agent ID (uses client context if not provided)
    
    Usage:
        @checkpoint("validate_data", preconditions=["data is not None"])
        async def validate(data):
            return processed_data
    
    The decorator will:
    1. Capture function arguments (pre-execution state)
    2. Execute function
    3. Capture return value (post-execution state)
    4. Create checkpoint with combined state
    5. Validate postconditions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get client (use provided or create based on config)
            if client is None:
                config = get_config()
                if config.use_remote_api:
                    # Use remote HTTP client
                    checkpoint_client = RemoteOmiumClient()
                else:
                    # Use local gRPC client
                    checkpoint_client = get_client()
                    # Ensure client is connected
                    if hasattr(checkpoint_client, '_checkpoint_stub') and checkpoint_client._checkpoint_stub is None:
                        await checkpoint_client.connect()
            else:
                checkpoint_client = client
                # Ensure gRPC client is connected if needed
                if isinstance(checkpoint_client, OmiumClient):
                    if checkpoint_client._checkpoint_stub is None:
                        await checkpoint_client.connect()
            
            # Capture pre-execution state
            pre_state = _capture_state(func, args, kwargs)
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Capture post-execution state
                post_state = _capture_state(func, args, kwargs, result)
                
                # Create checkpoint with combined state
                checkpoint_state = {
                    "pre_execution": pre_state,
                    "post_execution": post_state,
                    "function": func.__name__,
                    "module": func.__module__,
                }
                
                checkpoint_id = await checkpoint_client.create_checkpoint(
                    checkpoint_name=name,
                    state=checkpoint_state,
                    execution_id=execution_id,
                    agent_id=agent_id,
                    preconditions=preconditions,
                    postconditions=postconditions,
                    metadata={
                        "function": func.__name__,
                        "module": func.__module__,
                        "decorator": "checkpoint",
                    },
                )
                
                logger.debug(f"Checkpoint created: {checkpoint_id} for {name}")
                return result
                
            except CheckpointValidationError as e:
                logger.error(f"Checkpoint validation failed for {name}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error in checkpointed function {name}: {e}")
                # On failure, we could rollback, but for now just re-raise
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, run in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create task
                return asyncio.create_task(async_wrapper(*args, **kwargs))
            else:
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
        
        # Determine if function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class Checkpoint:
    """
    Context manager for manual checkpoint control.
    
    Usage:
        async with Checkpoint("important_state") as cp:
            # Critical code here
            result = await do_critical_thing()
            # Checkpoint saved automatically on exit
    """
    
    def __init__(
        self,
        name: str,
        client: Optional[Union[OmiumClient, RemoteOmiumClient]] = None,
        execution_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        preconditions: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
    ):
        """
        Initialize checkpoint context manager.
        
        Args:
            name: Checkpoint name
            client: Optional OmiumClient instance
            execution_id: Optional execution ID
            agent_id: Optional agent ID
            preconditions: Optional precondition list
            postconditions: Optional postcondition list
        """
        self.name = name
        # Get client based on config if not provided
        if client is None:
            config = get_config()
            if config.use_remote_api:
                self.client = RemoteOmiumClient()
            else:
                self.client = get_client()
        else:
            self.client = client
        self.execution_id = execution_id
        self.agent_id = agent_id
        self.preconditions = preconditions
        self.postconditions = postconditions
        self.checkpoint_id: Optional[str] = None
        self._state: Dict[str, Any] = {}
    
    async def __aenter__(self):
        """Enter checkpoint context."""
        # Ensure gRPC client is connected if needed
        if isinstance(self.client, OmiumClient):
            if self.client._checkpoint_stub is None:
                await self.client.connect()
        
        # Capture initial state
        self._state = {
            "checkpoint_name": self.name,
            "entered_at": asyncio.get_event_loop().time(),
        }
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit checkpoint context."""
        # Update state with exit information
        self._state.update({
            "exited_at": asyncio.get_event_loop().time(),
            "exception": str(exc_val) if exc_val else None,
            "exception_type": exc_type.__name__ if exc_type else None,
        })
        
        # Create checkpoint
        try:
            self.checkpoint_id = await self.client.create_checkpoint(
                checkpoint_name=self.name,
                state=self._state,
                execution_id=self.execution_id,
                agent_id=self.agent_id,
                preconditions=self.preconditions,
                postconditions=self.postconditions,
                metadata={
                    "context_manager": True,
                    "exception": str(exc_val) if exc_val else None,
                },
            )
            logger.debug(f"Checkpoint created: {self.checkpoint_id} for {self.name}")
        except Exception as e:
            logger.error(f"Failed to create checkpoint {self.name}: {e}")
            # Don't raise - let original exception propagate if any
        
        # If exception occurred, could rollback here
        # For now, just log it
        if exc_type is not None:
            logger.warning(f"Exception in checkpoint context {self.name}: {exc_val}")
        
        return False  # Don't suppress exceptions
    
    def update_state(self, **kwargs):
        """
        Update checkpoint state (call within context).
        
        Args:
            **kwargs: State updates
        """
        self._state.update(kwargs)
