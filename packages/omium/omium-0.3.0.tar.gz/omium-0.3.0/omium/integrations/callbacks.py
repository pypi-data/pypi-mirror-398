"""
Omium Callback Handler - LangChain/LangGraph compatible callbacks

This module provides a callback handler that integrates with LangChain's
callback system, allowing Omium tracing to work with any LangChain-based
application including LangGraph.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence, Union, TYPE_CHECKING
from uuid import UUID
import uuid as uuid_module
import time

logger = logging.getLogger("omium.callbacks")

# Type checking imports (never executed at runtime)
if TYPE_CHECKING:
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult, ChatGenerationChunk, GenerationChunk
    from langchain_core.agents import AgentAction, AgentFinish
    from langchain_core.documents import Document

# Check if LangChain is available at runtime
try:
    from langchain_core.callbacks.base import BaseCallbackHandler as _BaseCallbackHandler
    from langchain_core.outputs import LLMResult
    LANGCHAIN_AVAILABLE = True
    _CallbackBase = _BaseCallbackHandler
except ImportError:
    LANGCHAIN_AVAILABLE = False
    _CallbackBase = object
    LLMResult = None


class OmiumCallbackHandler(_CallbackBase):
    """
    LangChain/LangGraph callback handler for Omium.
    
    Captures traces from LangChain executions and sends them to Omium
    for visualization and analysis.
    
    Usage:
        ```python
        from omium import OmiumCallbackHandler
        
        # Create handler
        handler = OmiumCallbackHandler(api_key="om_xxx")
        
        # Use with any LangChain runnable
        chain.invoke(input, config={"callbacks": [handler]})
        
        # Or with LangGraph
        graph.invoke(state, config={"callbacks": [handler]})
        ```
    """
    
    # Required by LangChain
    raise_error: bool = False
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        project: Optional[str] = None,
        auto_checkpoint: bool = True,
        flush_on_chain_end: bool = True,
    ):
        """
        Initialize the Omium callback handler.
        
        Args:
            api_key: Omium API key. Uses OMIUM_API_KEY env var if not provided.
            project: Project name for organizing traces.
            auto_checkpoint: Whether to create checkpoints at significant points.
            flush_on_chain_end: Whether to flush traces when chain ends.
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain is not installed. Install with: pip install langchain-core"
            )
        
        super().__init__()
        
        from omium.integrations.core import init, get_current_config, is_initialized
        
        # Initialize Omium if not already done
        if not is_initialized():
            init(api_key=api_key, project=project)
        
        self.config = get_current_config()
        self.project = project or (self.config.project if self.config else "default")
        self.auto_checkpoint = auto_checkpoint
        self.flush_on_chain_end = flush_on_chain_end
        
        # Execution tracking
        self.execution_id = str(uuid_module.uuid4())
        
        # Run tracking (maps run_id to span info)
        self._run_map: Dict[str, Dict[str, Any]] = {}
        
        # Create tracer
        from omium.integrations.tracer import OmiumTracer
        self.tracer = OmiumTracer(
            execution_id=self.execution_id,
            project=self.project
        )
        
        # Statistics
        self._stats = {
            "chains": 0,
            "llm_calls": 0,
            "tool_calls": 0,
            "total_tokens": 0,
            "errors": 0,
        }
    
    @property
    def stats(self) -> Dict[str, int]:
        """Get execution statistics."""
        return self._stats.copy()
    
    # ==================== Chain Callbacks ====================
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chain starts running."""
        chain_name = serialized.get("name", serialized.get("id", ["chain"])[-1])
        
        self._run_map[str(run_id)] = {
            "type": "chain",
            "name": chain_name,
            "start_time": time.time(),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
        }
        
        self._stats["chains"] += 1
        
        self.tracer.add_event("chain_start", {
            "chain_name": chain_name,
            "run_id": str(run_id),
            "input_keys": list(inputs.keys()) if isinstance(inputs, dict) else None,
            "tags": tags,
        })
        
        logger.debug(f"Chain started: {chain_name} (run_id={run_id})")
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chain finishes running."""
        run_info = self._run_map.pop(str(run_id), {})
        
        self.tracer.add_event("chain_end", {
            "chain_name": run_info.get("name", "chain"),
            "run_id": str(run_id),
            "output_keys": list(outputs.keys()) if isinstance(outputs, dict) else None,
            "duration_ms": (time.time() - run_info.get("start_time", time.time())) * 1000,
        })
        
        # Flush if this is a root chain
        if parent_run_id is None and self.flush_on_chain_end:
            self.tracer.flush()
        
        logger.debug(f"Chain ended: {run_info.get('name', 'chain')}")
    
    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chain errors."""
        run_info = self._run_map.pop(str(run_id), {})
        self._stats["errors"] += 1
        
        self.tracer.add_event("chain_error", {
            "chain_name": run_info.get("name", "chain"),
            "run_id": str(run_id),
            "error": str(error),
            "error_type": type(error).__name__,
        })
        
        logger.debug(f"Chain error: {error}")
    
    # ==================== LLM Callbacks ====================
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM starts running."""
        model_name = serialized.get("name", serialized.get("id", ["llm"])[-1])
        
        self._run_map[str(run_id)] = {
            "type": "llm",
            "name": model_name,
            "start_time": time.time(),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
        }
        
        self._stats["llm_calls"] += 1
        
        self.tracer.add_event("llm_start", {
            "model": model_name,
            "run_id": str(run_id),
            "prompt_count": len(prompts),
            "total_prompt_length": sum(len(p) for p in prompts),
        })
        
        logger.debug(f"LLM call started: {model_name}")
    
    def on_llm_end(
        self,
        response: "LLMResult",
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM call ends."""
        run_info = self._run_map.pop(str(run_id), {})
        
        # Extract token usage
        token_usage = {}
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
        
        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)
        total_tokens = token_usage.get("total_tokens", input_tokens + output_tokens)
        
        self._stats["total_tokens"] += total_tokens
        
        self.tracer.add_event("llm_end", {
            "model": run_info.get("name", "llm"),
            "run_id": str(run_id),
            "generation_count": sum(len(g) for g in response.generations),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "duration_ms": (time.time() - run_info.get("start_time", time.time())) * 1000,
        })
        
        logger.debug(f"LLM call ended: {total_tokens} tokens")
    
    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an LLM call errors."""
        run_info = self._run_map.pop(str(run_id), {})
        self._stats["errors"] += 1
        
        self.tracer.add_event("llm_error", {
            "model": run_info.get("name", "llm"),
            "run_id": str(run_id),
            "error": str(error),
            "error_type": type(error).__name__,
        })
    
    # ==================== Chat Model Callbacks ====================
    
    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a chat model starts running."""
        model_name = serialized.get("name", serialized.get("id", ["chat"])[-1])
        
        self._run_map[str(run_id)] = {
            "type": "chat",
            "name": model_name,
            "start_time": time.time(),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
        }
        
        self._stats["llm_calls"] += 1
        
        # Count messages
        total_messages = sum(len(msg_list) for msg_list in messages)
        
        self.tracer.add_event("chat_model_start", {
            "model": model_name,
            "run_id": str(run_id),
            "message_count": total_messages,
        })
    
    # ==================== Tool Callbacks ====================
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "tool")
        
        self._run_map[str(run_id)] = {
            "type": "tool",
            "name": tool_name,
            "start_time": time.time(),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
        }
        
        self._stats["tool_calls"] += 1
        
        self.tracer.add_event("tool_start", {
            "tool_name": tool_name,
            "run_id": str(run_id),
            "input_preview": input_str[:200] if input_str else None,
        })
        
        logger.debug(f"Tool started: {tool_name}")
    
    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes running."""
        run_info = self._run_map.pop(str(run_id), {})
        
        self.tracer.add_event("tool_end", {
            "tool_name": run_info.get("name", "tool"),
            "run_id": str(run_id),
            "output_preview": output[:500] if output else None,
            "duration_ms": (time.time() - run_info.get("start_time", time.time())) * 1000,
        })
        
        logger.debug(f"Tool ended: {run_info.get('name', 'tool')}")
    
    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool errors."""
        run_info = self._run_map.pop(str(run_id), {})
        self._stats["errors"] += 1
        
        self.tracer.add_event("tool_error", {
            "tool_name": run_info.get("name", "tool"),
            "run_id": str(run_id),
            "error": str(error),
            "error_type": type(error).__name__,
        })
    
    # ==================== Agent Callbacks ====================
    
    def on_agent_action(
        self,
        action: "AgentAction",
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an agent takes an action."""
        self.tracer.add_event("agent_action", {
            "tool": action.tool,
            "tool_input_preview": str(action.tool_input)[:200],
            "run_id": str(run_id),
        })
    
    def on_agent_finish(
        self,
        finish: "AgentFinish",
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when an agent finishes."""
        self.tracer.add_event("agent_finish", {
            "output_preview": str(finish.return_values)[:500],
            "run_id": str(run_id),
        })
    
    # ==================== Retriever Callbacks ====================
    
    def on_retriever_start(
        self,
        serialized: Dict[str, Any],
        query: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever starts retrieving."""
        retriever_name = serialized.get("name", "retriever")
        
        self._run_map[str(run_id)] = {
            "type": "retriever",
            "name": retriever_name,
            "start_time": time.time(),
        }
        
        self.tracer.add_event("retriever_start", {
            "retriever": retriever_name,
            "query_preview": query[:200] if query else None,
            "run_id": str(run_id),
        })
    
    def on_retriever_end(
        self,
        documents: Sequence["Document"],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Called when a retriever finishes retrieving."""
        run_info = self._run_map.pop(str(run_id), {})
        
        self.tracer.add_event("retriever_end", {
            "retriever": run_info.get("name", "retriever"),
            "document_count": len(documents),
            "run_id": str(run_id),
            "duration_ms": (time.time() - run_info.get("start_time", time.time())) * 1000,
        })
    
    # ==================== Lifecycle Methods ====================
    
    def flush(self):
        """Flush all pending traces to Omium."""
        self.tracer.flush()
    
    async def aflush(self):
        """Async flush."""
        await self.tracer.aflush()
    
    def get_execution_id(self) -> str:
        """Get the execution ID for this handler."""
        return self.execution_id
    
    def get_trace_url(self) -> str:
        """Get the URL to view this trace in the Omium dashboard."""
        return f"https://app.omium.ai/traces/{self.tracer.trace_id}"
