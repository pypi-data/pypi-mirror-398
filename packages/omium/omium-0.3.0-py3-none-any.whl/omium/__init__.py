"""
Omium Python SDK

Fault-tolerant operating system for production multi-agent AI systems.

Quick Start:
    import omium
    omium.init(api_key="om_xxx")
    
    # Your LangGraph/CrewAI code runs normally
    # Traces and checkpoints are captured automatically

Manual Tracing:
    @omium.trace("my_function")
    def my_function():
        ...

Callbacks:
    from omium import OmiumCallbackHandler
    handler = OmiumCallbackHandler()
    chain.invoke(input, config={"callbacks": [handler]})
"""

from .agent import agent
from .checkpoint import checkpoint as checkpoint_decorator, Checkpoint
from .consensus import consensus, Consensus
from .client import (
    OmiumClient,
    CheckpointError,
    CheckpointNotFoundError,
    CheckpointValidationError,
    ConnectionError
)
from .remote_client import RemoteOmiumClient
from .config import get_config, ConfigManager, OmiumConfig as LegacyOmiumConfig
from .websocket_client import ExecutionWebSocketClient

# New integrations
from .integrations.core import (
    init,
    configure,
    is_initialized,
    get_current_config,
    OmiumConfig,
)
from .integrations.decorators import trace, checkpoint
from .integrations.callbacks import OmiumCallbackHandler
from .integrations.langgraph import instrument_langgraph, uninstrument_langgraph
from .integrations.crewai import instrument_crewai, uninstrument_crewai

__version__ = "0.3.0"
__all__ = [
    # New integration API (primary)
    "init",
    "configure",
    "is_initialized",
    "get_current_config",
    "OmiumConfig",
    "trace",
    "checkpoint",
    "OmiumCallbackHandler",
    "instrument_langgraph",
    "uninstrument_langgraph",
    "instrument_crewai",
    "uninstrument_crewai",
    
    # Legacy API (still supported)
    "agent",
    "checkpoint_decorator",
    "Checkpoint",
    "consensus",
    "Consensus",
    "OmiumClient",
    "RemoteOmiumClient",
    "CheckpointError",
    "CheckpointNotFoundError",
    "CheckpointValidationError",
    "ConnectionError",
    "get_config",
    "ConfigManager",
    "LegacyOmiumConfig",
    "ExecutionWebSocketClient",
]
