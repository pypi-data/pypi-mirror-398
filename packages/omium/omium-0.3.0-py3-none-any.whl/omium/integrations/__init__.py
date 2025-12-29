"""
Omium Integrations - Framework auto-instrumentation

Three ways to use Omium:

1. Environment Variables (Zero Code):
   ```
   export OMIUM_API_KEY=om_xxx
   export OMIUM_TRACING=true
   python main.py
   ```

2. Code Init (One Line):
   ```python
   import omium
   omium.init(api_key="om_xxx")
   # Your LangGraph/CrewAI code runs normally
   ```

3. Callbacks (Explicit):
   ```python
   from omium import OmiumCallbackHandler
   handler = OmiumCallbackHandler()
   chain.invoke(input, config={"callbacks": [handler]})
   ```
"""

from omium.integrations.core import (
    init,
    configure,
    get_current_config,
    is_initialized,
    OmiumConfig,
)
from omium.integrations.callbacks import OmiumCallbackHandler
from omium.integrations.decorators import trace, checkpoint
from omium.integrations.langgraph import instrument_langgraph, uninstrument_langgraph
from omium.integrations.crewai import instrument_crewai, uninstrument_crewai

__all__ = [
    # Core
    "init",
    "configure",
    "get_current_config",
    "is_initialized",
    "OmiumConfig",
    # Callbacks
    "OmiumCallbackHandler",
    # Decorators
    "trace",
    "checkpoint",
    # Framework instrumentation
    "instrument_langgraph",
    "uninstrument_langgraph",
    "instrument_crewai",
    "uninstrument_crewai",
]
