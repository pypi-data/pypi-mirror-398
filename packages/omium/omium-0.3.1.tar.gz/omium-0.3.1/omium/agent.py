"""
Agent decorator and base classes for Omium SDK.
"""

from typing import Callable, Any
from functools import wraps


def agent(cls_or_func: Any = None):
    """
    Decorator to mark a class or function as an Omium agent.
    
    Usage:
        @agent
        class MyAgent:
            ...
        
        @agent
        async def my_agent_function():
            ...
    """
    def decorator(obj: Any) -> Any:
        if isinstance(obj, type):
            # Class decorator
            obj._omium_agent = True
            return obj
        else:
            # Function decorator
            @wraps(obj)
            async def wrapper(*args, **kwargs):
                return await obj(*args, **kwargs)
            wrapper._omium_agent = True
            return wrapper
    
    if cls_or_func is None:
        return decorator
    return decorator(cls_or_func)

