"""
Tracing Service client for Python services.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4

import grpc
from google.protobuf import struct_pb2, timestamp_pb2
from google.protobuf import json_format

# Import generated proto code
try:
    from omium.proto.tracing import tracing_pb2, tracing_pb2_grpc
except ImportError:
    try:
        from omium.proto import tracing_pb2, tracing_pb2_grpc
    except ImportError:
        tracing_pb2 = None
        tracing_pb2_grpc = None

logger = logging.getLogger(__name__)


class TracingError(Exception):
    """Base exception for tracing operations."""
    pass


class TracingClient:
    """
    Async gRPC client for Tracing Service.
    
    Provides distributed tracing and replay capabilities.
    """
    
    def __init__(
        self,
        tracing_service_url: str = "localhost:7003",
        timeout: float = 30.0,
    ):
        """
        Initialize tracing client.
        
        Args:
            tracing_service_url: Tracing Service gRPC endpoint
            timeout: Request timeout in seconds
        """
        self.tracing_service_url = tracing_service_url
        self.timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._tracing_stub: Optional[Any] = None
        self._tracing_pb2 = None
        self._tracing_pb2_grpc = None
    
    async def connect(self):
        """Create gRPC channel and stubs."""
        # Try multiple import paths
        try:
            from omium.proto.tracing import tracing_pb2, tracing_pb2_grpc
            self._tracing_pb2 = tracing_pb2
            self._tracing_pb2_grpc = tracing_pb2_grpc
        except ImportError as e1:
            try:
                from omium.proto import tracing_pb2, tracing_pb2_grpc
                self._tracing_pb2 = tracing_pb2
                self._tracing_pb2_grpc = tracing_pb2_grpc
            except ImportError as e2:
                raise ImportError(
                    f"Tracing proto code not found. Tried: omium.proto.tracing (error: {e1}), "
                    f"omium.proto (error: {e2}). "
                    "Ensure proto files are generated and included in package."
                )
        
        self._channel = grpc.aio.insecure_channel(self.tracing_service_url)
        self._tracing_stub = self._tracing_pb2_grpc.TracingServiceStub(self._channel)
        
        # Test connection
        try:
            await asyncio.wait_for(self._channel.channel_ready(), timeout=5.0)
            logger.info(f"Connected to tracing-service at {self.tracing_service_url}")
        except asyncio.TimeoutError:
            raise ConnectionError(f"Failed to connect to {self.tracing_service_url}")
    
    async def close(self):
        """Close gRPC channel."""
        if self._channel:
            await self._channel.close()
            logger.info("Closed tracing client connection")
    
    def _dict_to_struct(self, data: Dict[str, Any]) -> struct_pb2.Struct:
        """Convert Python dict to protobuf Struct."""
        return json_format.ParseDict(data, struct_pb2.Struct())
    
    def _datetime_to_timestamp(self, dt: datetime) -> timestamp_pb2.Timestamp:
        """Convert datetime to protobuf Timestamp."""
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(dt)
        return ts
    
    async def save_span(
        self,
        span_id: str,
        trace_id: str,
        name: str,
        service_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        status: str = "ok",
        status_message: Optional[str] = None,
    ) -> bool:
        """
        Save a trace span.
        
        Args:
            span_id: Span ID
            trace_id: Trace ID (usually execution_id)
            name: Span name
            service_name: Service name
            start_time: Start time
            end_time: End time (optional)
            duration_ms: Duration in milliseconds (optional)
            parent_span_id: Parent span ID (optional)
            attributes: Span attributes (optional)
            events: Span events (optional)
            status: Status ("ok", "error", "unset")
            status_message: Status message (optional)
        
        Returns:
            True if successful
        """
        if self._tracing_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        # Convert events
        pb_events = []
        if events:
            for event in events:
                pb_event = self._tracing_pb2.TraceEvent(
                    name=event.get("name", ""),
                    timestamp=self._datetime_to_timestamp(
                        event.get("timestamp", datetime.utcnow())
                    ),
                    attributes=self._dict_to_struct(event.get("attributes", {})) if event.get("attributes") else None,
                )
                pb_events.append(pb_event)
        
        request = self._tracing_pb2.SaveSpanRequest(
            id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id or "",
            name=name,
            service_name=service_name,
            start_time=self._datetime_to_timestamp(start_time),
            end_time=self._datetime_to_timestamp(end_time) if end_time else None,
            duration_ms=duration_ms or 0,
            attributes=self._dict_to_struct(attributes) if attributes else None,
            events=pb_events,
            status=status,
            status_message=status_message or "",
        )
        
        try:
            response = await asyncio.wait_for(
                self._tracing_stub.SaveSpan(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise TracingError(response.error_message or "Failed to save span")
            
            return True
            
        except grpc.RpcError as e:
            raise TracingError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise TracingError(f"Request timeout after {self.timeout}s")
    
    async def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """Get a complete trace."""
        if self._tracing_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._tracing_pb2.GetTraceRequest(trace_id=trace_id)
        
        try:
            response = await asyncio.wait_for(
                self._tracing_stub.GetTrace(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise TracingError(response.error_message or "Failed to get trace")
            
            trace = response.trace
            spans = []
            for span in trace.spans:
                spans.append({
                    "id": span.id,
                    "trace_id": span.trace_id,
                    "parent_span_id": span.parent_span_id or None,
                    "name": span.name,
                    "service_name": span.service_name,
                    "duration_ms": span.duration_ms,
                    "status": span.status,
                    "status_message": span.status_message or None,
                })
            
            return {
                "id": trace.id,
                "execution_id": trace.execution_id,
                "trace_id": trace.trace_id,
                "spans": spans,
                "duration_ms": trace.duration_ms,
            }
            
        except grpc.RpcError as e:
            raise TracingError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise TracingError(f"Request timeout after {self.timeout}s")
    
    async def list_traces(
        self,
        execution_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List traces for an execution."""
        if self._tracing_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._tracing_pb2.ListTracesRequest(
            execution_id=execution_id,
            limit=limit,
            offset=offset,
        )
        
        try:
            response = await asyncio.wait_for(
                self._tracing_stub.ListTraces(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise TracingError(response.error_message or "Failed to list traces")
            
            traces = []
            for trace in response.traces:
                traces.append({
                    "id": trace.id,
                    "execution_id": trace.execution_id,
                    "trace_id": trace.trace_id,
                    "duration_ms": trace.duration_ms,
                    "span_count": len(trace.spans),
                })
            
            return traces
            
        except grpc.RpcError as e:
            raise TracingError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise TracingError(f"Request timeout after {self.timeout}s")

