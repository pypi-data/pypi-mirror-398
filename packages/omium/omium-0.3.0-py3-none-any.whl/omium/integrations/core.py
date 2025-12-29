"""
Omium Core Integration - Initialization and Configuration

This module provides the central initialization and configuration for Omium SDK.
It handles API key validation, auto-detection of frameworks, and global state management.
"""

import os
import logging
import threading
import atexit
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("omium")


class CheckpointStrategy(str, Enum):
    """Checkpoint creation strategy."""
    NODE = "node"       # Create checkpoint at each graph node (LangGraph)
    TASK = "task"       # Create checkpoint at each task (CrewAI)
    AGENT = "agent"     # Create checkpoint at each agent execution
    MANUAL = "manual"   # Only create checkpoints when explicitly called


@dataclass
class OmiumConfig:
    """
    Omium SDK configuration.
    
    Attributes:
        api_key: Omium API key (required, starts with 'om_')
        project: Project name for organizing traces
        auto_trace: Enable automatic tracing of framework calls
        auto_checkpoint: Enable automatic checkpoint creation
        checkpoint_strategy: When to create checkpoints
        api_base_url: Omium API base URL
        checkpoint_manager_url: Checkpoint Manager gRPC endpoint
        tracing_url: Trace ingestion endpoint
        batch_size: Number of spans to batch before sending
        flush_interval: Seconds between automatic flushes
        max_retries: Max retry attempts for failed requests
        timeout: Request timeout in seconds
        debug: Enable debug logging
    """
    
    # Required
    api_key: Optional[str] = None
    
    # Project settings
    project: str = "default"
    
    # Auto-instrumentation settings
    auto_trace: bool = True
    auto_checkpoint: bool = True
    checkpoint_strategy: CheckpointStrategy = CheckpointStrategy.NODE
    
    # Backend URLs
    api_base_url: str = "https://api.omium.ai/api/v1"
    checkpoint_manager_url: str = "checkpoint-manager.omium.ai:7001"
    tracing_url: str = "https://api.omium.ai/api/v1/traces"
    
    # Performance settings
    batch_size: int = 100
    flush_interval: float = 5.0
    max_retries: int = 3
    timeout: float = 30.0
    
    # Debug
    debug: bool = False
    
    # Runtime state (set after validation)
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    execution_id: Optional[str] = None
    
    # Detected frameworks
    detected_frameworks: List[str] = field(default_factory=list)
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key:
            raise ValueError(
                "API key is required. Set OMIUM_API_KEY environment variable "
                "or pass api_key to omium.init()"
            )
        
        # Accept both 'om_' and 'omium_' prefixes
        if not (self.api_key.startswith("om_") or self.api_key.startswith("omium_")):
            raise ValueError(
                f"Invalid API key format: '{self.api_key[:10]}...'. "
                "API key should start with 'om_' or 'omium_'"
            )
        
        if len(self.api_key) < 20:
            raise ValueError("API key is too short. Please check your key.")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)."""
        return {
            "project": self.project,
            "auto_trace": self.auto_trace,
            "auto_checkpoint": self.auto_checkpoint,
            "checkpoint_strategy": self.checkpoint_strategy.value,
            "api_base_url": self.api_base_url,
            "detected_frameworks": self.detected_frameworks,
        }


# Global state
_config: Optional[OmiumConfig] = None
_initialized: bool = False
_lock = threading.Lock()
_shutdown_registered: bool = False


def init(
    api_key: Optional[str] = None,
    project: Optional[str] = None,
    auto_trace: bool = True,
    auto_checkpoint: bool = True,
    checkpoint_strategy: str = "node",
    api_base_url: Optional[str] = None,
    debug: bool = False,
    **kwargs
) -> OmiumConfig:
    """
    Initialize Omium SDK.
    
    This is the primary entry point for Omium. Call this at the start of your
    application to enable automatic tracing and checkpointing.
    
    Args:
        api_key: Omium API key. If not provided, reads from OMIUM_API_KEY env var.
        project: Project name for organizing traces. Defaults to "default".
        auto_trace: Enable automatic tracing of LangGraph/CrewAI calls.
        auto_checkpoint: Enable automatic checkpoint creation.
        checkpoint_strategy: When to create checkpoints - "node", "task", "agent", or "manual".
        api_base_url: Override the default API URL (for self-hosted deployments).
        debug: Enable debug logging.
        **kwargs: Additional configuration options.
    
    Returns:
        OmiumConfig: The active configuration object.
    
    Raises:
        ValueError: If API key is missing or invalid.
    
    Example:
        ```python
        import omium
        
        # Simple initialization
        omium.init(api_key="om_xxx")
        
        # With project name
        omium.init(api_key="om_xxx", project="my-research-crew")
        
        # Disable auto-checkpointing
        omium.init(api_key="om_xxx", auto_checkpoint=False)
        ```
    """
    global _config, _initialized
    
    with _lock:
        if _initialized:
            logger.warning(
                "Omium already initialized. Use omium.configure() to update settings."
            )
            return _config
        
        # Load from environment variables first, then override with parameters
        resolved_api_key = api_key or os.environ.get("OMIUM_API_KEY")
        resolved_project = project or os.environ.get("OMIUM_PROJECT", "default")
        
        # Handle auto_trace from env
        env_tracing = os.environ.get("OMIUM_TRACING", "").lower()
        if api_key is None and env_tracing:
            auto_trace = env_tracing in ("true", "1", "yes")
        
        # Handle auto_checkpoint from env
        env_checkpoints = os.environ.get("OMIUM_CHECKPOINTS", "").lower()
        if api_key is None and env_checkpoints:
            auto_checkpoint = env_checkpoints not in ("false", "0", "no")
        
        # Parse checkpoint strategy
        try:
            strategy = CheckpointStrategy(checkpoint_strategy)
        except ValueError:
            logger.warning(f"Invalid checkpoint_strategy '{checkpoint_strategy}', using 'node'")
            strategy = CheckpointStrategy.NODE
        
        # Create config
        _config = OmiumConfig(
            api_key=resolved_api_key,
            project=resolved_project,
            auto_trace=auto_trace,
            auto_checkpoint=auto_checkpoint,
            checkpoint_strategy=strategy,
            api_base_url=api_base_url or os.environ.get("OMIUM_API_URL", "https://api.omium.ai/api/v1"),
            debug=debug or os.environ.get("OMIUM_DEBUG", "").lower() in ("true", "1"),
            **kwargs
        )
        
        # Set up debug logging if requested
        if _config.debug:
            logging.getLogger("omium").setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [OMIUM] %(levelname)s: %(message)s"
            ))
            logging.getLogger("omium").addHandler(handler)
        
        # Validate
        _config.validate()
        
        # Detect and instrument frameworks
        if _config.auto_trace:
            _detect_and_instrument_frameworks()
        
        # Register shutdown handler
        _register_shutdown()
        
        _initialized = True
        
        logger.info(
            f"Omium initialized: project={_config.project}, "
            f"auto_trace={_config.auto_trace}, "
            f"frameworks={_config.detected_frameworks}"
        )
        
        return _config


def configure(**kwargs) -> OmiumConfig:
    """
    Update configuration after initialization.
    
    If Omium hasn't been initialized yet, this will call init() with the
    provided parameters.
    
    Args:
        **kwargs: Configuration options to update.
    
    Returns:
        OmiumConfig: The updated configuration.
    """
    global _config
    
    if not _initialized:
        return init(**kwargs)
    
    with _lock:
        for key, value in kwargs.items():
            if hasattr(_config, key):
                setattr(_config, key, value)
            else:
                logger.warning(f"Unknown configuration option: {key}")
        
        return _config


def get_current_config() -> Optional[OmiumConfig]:
    """
    Get the current configuration.
    
    Returns:
        OmiumConfig or None if not initialized.
    """
    return _config


def is_initialized() -> bool:
    """
    Check if Omium has been initialized.
    
    Returns:
        bool: True if init() has been called successfully.
    """
    return _initialized


def shutdown():
    """
    Shutdown Omium SDK gracefully.
    
    This flushes any pending traces and closes connections.
    Called automatically on program exit.
    """
    global _initialized, _config
    
    if not _initialized:
        return
    
    logger.debug("Shutting down Omium SDK...")
    
    # Flush pending traces
    try:
        from omium.integrations.tracer import flush_all_tracers
        flush_all_tracers()
    except Exception as e:
        logger.warning(f"Error flushing traces on shutdown: {e}")
    
    _initialized = False
    logger.debug("Omium SDK shutdown complete")


def _detect_and_instrument_frameworks():
    """Detect installed frameworks and apply instrumentation."""
    global _config
    
    detected = []
    
    # Try LangGraph
    try:
        from omium.integrations.langgraph import instrument_langgraph
        instrument_langgraph()
        detected.append("langgraph")
        logger.info("✓ LangGraph auto-instrumentation enabled")
    except ImportError:
        logger.debug("LangGraph not installed, skipping instrumentation")
    except Exception as e:
        logger.warning(f"Failed to instrument LangGraph: {e}")
    
    # Try CrewAI
    try:
        from omium.integrations.crewai import instrument_crewai
        instrument_crewai()
        detected.append("crewai")
        logger.info("✓ CrewAI auto-instrumentation enabled")
    except ImportError:
        logger.debug("CrewAI not installed, skipping instrumentation")
    except Exception as e:
        logger.warning(f"Failed to instrument CrewAI: {e}")
    
    # Try LangChain (for general callback support)
    try:
        import langchain_core
        detected.append("langchain")
        logger.debug("LangChain detected (use OmiumCallbackHandler for tracing)")
    except ImportError:
        pass
    
    if _config:
        _config.detected_frameworks = detected
    
    if not detected:
        logger.info(
            "No supported frameworks detected. "
            "Use @omium.trace decorator for manual tracing."
        )


def _register_shutdown():
    """Register shutdown handler."""
    global _shutdown_registered
    
    if _shutdown_registered:
        return
    
    atexit.register(shutdown)
    _shutdown_registered = True


# Auto-initialization support
def _try_auto_init():
    """
    Attempt auto-initialization from environment variables.
    
    This is called lazily when frameworks are first used if
    OMIUM_TRACING=true is set.
    """
    if _initialized:
        return
    
    if os.environ.get("OMIUM_TRACING", "").lower() in ("true", "1", "yes"):
        if os.environ.get("OMIUM_API_KEY"):
            try:
                init()
            except Exception as e:
                logger.warning(f"Auto-initialization failed: {e}")
