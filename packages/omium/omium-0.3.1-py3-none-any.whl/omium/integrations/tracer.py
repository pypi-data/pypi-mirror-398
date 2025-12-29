"""
Omium Tracer - Lightweight tracing for agent workflows

This module provides the core tracing functionality for Omium SDK.
It captures spans (individual operations) and traces (complete execution paths)
and sends them to the Omium backend for visualization and analysis.
"""

import time
import json
import logging
import threading
import asyncio
import queue
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
from contextlib import contextmanager
from contextvars import ContextVar
import uuid
import weakref

logger = logging.getLogger("omium.tracer")

# Context variable for current tracer
_current_tracer: ContextVar[Optional["OmiumTracer"]] = ContextVar("current_tracer", default=None)

# Global registry of active tracers for shutdown
_active_tracers: Set[weakref.ref] = set()
_tracers_lock = threading.Lock()


@dataclass
class SpanEvent:
    """An event within a span."""
    
    name: str
    timestamp: float = field(default_factory=time.time)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "attributes": self.attributes,
        }


@dataclass
class Span:
    """
    A single span in a trace.
    
    A span represents a single unit of work, such as:
    - An LLM call
    - A tool invocation
    - A graph node execution
    - An agent task
    
    Spans can be nested to form a trace tree.
    """
    
    span_id: str
    name: str
    trace_id: str
    parent_span_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Data
    input: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    span_type: str = "default"  # llm, tool, agent, node, task, chain
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[SpanEvent] = field(default_factory=list)
    
    # Metrics
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    token_count_total: Optional[int] = None
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    
    # State
    _ended: bool = field(default=False, repr=False)
    
    def set_input(self, input_data: Any):
        """Set span input, truncating if necessary."""
        if isinstance(input_data, dict):
            self.input = self._truncate_dict(input_data)
        else:
            self.input = {"value": self._truncate_str(str(input_data))}
    
    def set_output(self, output: Any):
        """Set span output and end the span."""
        if isinstance(output, dict):
            self.output = self._truncate_dict(output)
        else:
            self.output = self._truncate_str(str(output))
        self._end()
    
    def set_error(self, error: Exception):
        """Set span error and end the span."""
        self.error = str(error)
        self.error_type = type(error).__name__
        self._end()
    
    def set_attribute(self, key: str, value: Any):
        """Set a span attribute."""
        self.attributes[key] = value
    
    def set_token_counts(
        self,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ):
        """Set token usage metrics."""
        if input_tokens is not None:
            self.token_count_input = input_tokens
        if output_tokens is not None:
            self.token_count_output = output_tokens
        if total_tokens is not None:
            self.token_count_total = total_tokens
        elif input_tokens is not None and output_tokens is not None:
            self.token_count_total = input_tokens + output_tokens
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Add an event to the span."""
        self.events.append(SpanEvent(
            name=name,
            attributes=attributes or {}
        ))
    
    def end(self):
        """Explicitly end the span."""
        self._end()
    
    def _end(self):
        """Internal method to end the span."""
        if self._ended:
            return
        
        self.end_time = time.time()
        self.latency_ms = (self.end_time - self.start_time) * 1000
        self._ended = True
    
    def _truncate_str(self, s: str, max_len: int = 2000) -> str:
        """Truncate string to max length."""
        if len(s) > max_len:
            return s[:max_len] + f"... (truncated, {len(s)} total chars)"
        return s
    
    def _truncate_dict(self, d: Dict, max_len: int = 2000) -> Dict:
        """Truncate dict values to max length."""
        result = {}
        for k, v in d.items():
            if isinstance(v, str) and len(v) > max_len:
                result[k] = self._truncate_str(v, max_len)
            elif isinstance(v, dict):
                result[k] = self._truncate_dict(v, max_len)
            else:
                result[k] = v
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for API submission."""
        return {
            "span_id": self.span_id,
            "name": self.name,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "span_type": self.span_type,
            "start_time": datetime.fromtimestamp(self.start_time, tz=timezone.utc).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time, tz=timezone.utc).isoformat() if self.end_time else None,
            "input": self.input,
            "output": self.output,
            "error": self.error,
            "error_type": self.error_type,
            "attributes": self.attributes,
            "events": [e.to_dict() for e in self.events],
            "token_count_input": self.token_count_input,
            "token_count_output": self.token_count_output,
            "token_count_total": self.token_count_total,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
        }


class OmiumTracer:
    """
    Lightweight tracer for Omium.
    
    Manages trace and span lifecycle, buffering, and submission to the backend.
    
    Usage:
        tracer = OmiumTracer(execution_id="xxx")
        
        with tracer.span("my_operation", input={"x": 1}) as span:
            result = do_something()
            span.set_output(result)
        
        tracer.flush()
    """
    
    def __init__(
        self,
        execution_id: Optional[str] = None,
        project: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        """
        Initialize a tracer.
        
        Args:
            execution_id: Unique ID for this execution
            project: Project name
            trace_id: Trace ID (auto-generated if not provided)
        """
        from omium.integrations.core import get_current_config
        
        self.config = get_current_config()
        self.execution_id = execution_id or str(uuid.uuid4())
        self.trace_id = trace_id or str(uuid.uuid4())
        self.project = project or (self.config.project if self.config else "default")
        
        self._spans: List[Span] = []
        self._span_stack: List[Span] = []
        self._lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None
        
        # Register for shutdown
        self._register()
        
        # Start auto-flush timer
        if self.config and self.config.flush_interval > 0:
            self._schedule_flush()
    
    def _register(self):
        """Register tracer for shutdown handling."""
        with _tracers_lock:
            _active_tracers.add(weakref.ref(self, self._on_finalize))
    
    @staticmethod
    def _on_finalize(ref):
        """Called when tracer is garbage collected."""
        with _tracers_lock:
            _active_tracers.discard(ref)
    
    def _schedule_flush(self):
        """Schedule automatic flush."""
        if self.config and self.config.flush_interval > 0:
            self._flush_timer = threading.Timer(
                self.config.flush_interval,
                self._auto_flush
            )
            self._flush_timer.daemon = True
            self._flush_timer.start()
    
    def _auto_flush(self):
        """Auto-flush callback."""
        try:
            self.flush()
        finally:
            self._schedule_flush()
    
    @property
    def current_span(self) -> Optional[Span]:
        """Get the current active span."""
        if self._span_stack:
            return self._span_stack[-1]
        return None
    
    @contextmanager
    def span(
        self,
        name: str,
        input: Optional[Dict] = None,
        span_type: str = "default",
        **attributes
    ):
        """
        Create a span context manager.
        
        Args:
            name: Span name (e.g., "llm_call", "tool_invoke")
            input: Input data for the span
            span_type: Type of span (llm, tool, agent, node, etc.)
            **attributes: Additional attributes
        
        Yields:
            Span: The created span
        
        Example:
            with tracer.span("my_operation", input={"x": 1}) as span:
                result = do_something()
                span.set_output(result)
        """
        span = Span(
            span_id=str(uuid.uuid4()),
            name=name,
            trace_id=self.trace_id,
            parent_span_id=self.current_span.span_id if self.current_span else None,
            span_type=span_type,
            attributes=attributes,
        )
        
        if input is not None:
            span.set_input(input)
        
        # Push to stack
        self._span_stack.append(span)
        
        # Set as context tracer
        token = _current_tracer.set(self)
        
        try:
            yield span
        except Exception as e:
            if not span._ended:
                span.set_error(e)
            raise
        finally:
            # End span if not already ended
            if not span._ended:
                span.end()
            
            # Pop from stack
            if self._span_stack and self._span_stack[-1] is span:
                self._span_stack.pop()
            
            # Add to completed spans
            with self._lock:
                self._spans.append(span)
            
            # Reset context
            _current_tracer.reset(token)
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Add event to current span."""
        if self.current_span:
            self.current_span.add_event(name, attributes)
        else:
            logger.debug(f"No active span for event: {name}")
    
    def flush(self):
        """Send all pending spans to Omium backend."""
        with self._lock:
            if not self._spans:
                return
            
            spans_to_send = self._spans.copy()
            self._spans.clear()
        
        if not self.config:
            logger.warning("Omium not configured, spans not sent")
            return
        
        self._send_spans(spans_to_send)
    
    async def aflush(self):
        """Async version of flush."""
        with self._lock:
            if not self._spans:
                return
            
            spans_to_send = self._spans.copy()
            self._spans.clear()
        
        if not self.config:
            return
        
        await self._asend_spans(spans_to_send)
    
    def _send_spans(self, spans: List[Span]):
        """Send spans synchronously."""
        try:
            import httpx
            
            payload = {
                "trace_id": self.trace_id,
                "execution_id": self.execution_id,
                "project": self.project,
                "spans": [s.to_dict() for s in spans],
            }
            
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.post(
                    f"{self.config.api_base_url}/traces/ingest",
                    json=payload,
                    headers={"X-API-Key": self.config.api_key}
                )
                
                if response.status_code >= 400:
                    logger.warning(
                        f"Failed to send spans: {response.status_code} - {response.text}"
                    )
                else:
                    logger.debug(f"Sent {len(spans)} spans to Omium")
                    
        except ImportError:
            logger.warning("httpx not installed. Install with: pip install httpx")
        except Exception as e:
            logger.error(f"Failed to send spans: {e}")
            # Re-add spans for retry
            with self._lock:
                self._spans.extend(spans)
    
    async def _asend_spans(self, spans: List[Span]):
        """Send spans asynchronously."""
        try:
            import httpx
            
            payload = {
                "trace_id": self.trace_id,
                "execution_id": self.execution_id,
                "project": self.project,
                "spans": [s.to_dict() for s in spans],
            }
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_base_url}/traces/ingest",
                    json=payload,
                    headers={"X-API-Key": self.config.api_key}
                )
                
                if response.status_code >= 400:
                    logger.warning(
                        f"Failed to send spans: {response.status_code} - {response.text}"
                    )
                else:
                    logger.debug(f"Sent {len(spans)} spans to Omium")
                    
        except ImportError:
            logger.warning("httpx not installed. Install with: pip install httpx")
        except Exception as e:
            logger.error(f"Failed to send spans: {e}")
    
    def close(self):
        """Close the tracer and flush remaining spans."""
        if self._flush_timer:
            self._flush_timer.cancel()
        
        self.flush()
        
        with _tracers_lock:
            # Remove from active tracers
            for ref in list(_active_tracers):
                if ref() is self:
                    _active_tracers.discard(ref)
                    break


def get_current_tracer() -> Optional[OmiumTracer]:
    """Get the current active tracer from context."""
    return _current_tracer.get()


def flush_all_tracers():
    """Flush all active tracers. Called on shutdown."""
    with _tracers_lock:
        for ref in list(_active_tracers):
            tracer = ref()
            if tracer:
                try:
                    tracer.flush()
                except Exception as e:
                    logger.warning(f"Error flushing tracer: {e}")


# Convenience function for one-off tracing
@contextmanager
def trace_operation(
    name: str,
    input: Optional[Dict] = None,
    span_type: str = "default",
    **attributes
):
    """
    Convenience context manager for tracing a single operation.
    
    Uses the current tracer if available, or creates a temporary one.
    
    Example:
        with trace_operation("my_function", input={"x": 1}) as span:
            result = my_function()
            span.set_output(result)
    """
    tracer = get_current_tracer()
    
    if tracer:
        with tracer.span(name, input=input, span_type=span_type, **attributes) as span:
            yield span
    else:
        # Create temporary tracer
        tracer = OmiumTracer()
        with tracer.span(name, input=input, span_type=span_type, **attributes) as span:
            try:
                yield span
            finally:
                tracer.flush()
