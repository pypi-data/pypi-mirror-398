"""
Omium gRPC client for SDK - Async implementation.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

import grpc
from google.protobuf import struct_pb2
from google.protobuf import json_format
from google.protobuf.timestamp_pb2 import Timestamp

# Import generated proto code
try:
    from omium.proto.checkpoint import checkpoint_pb2, checkpoint_pb2_grpc
except ImportError:
    try:
        # Try alternative import path
        from omium.proto import checkpoint_pb2, checkpoint_pb2_grpc
    except ImportError:
        # Fallback if proto code not generated yet
        checkpoint_pb2 = None
        checkpoint_pb2_grpc = None

logger = logging.getLogger(__name__)


class CheckpointError(Exception):
    """Base exception for checkpoint operations."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class CheckpointNotFoundError(CheckpointError):
    """Checkpoint not found."""
    pass


class CheckpointValidationError(CheckpointError):
    """Checkpoint validation failed."""
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None):
        super().__init__(message, {"validation_errors": validation_errors or []})
        self.validation_errors = validation_errors or []


class ConnectionError(CheckpointError):
    """Connection to checkpoint manager failed."""
    pass


class OmiumClient:
    """
    Async gRPC client for communicating with Omium services.
    
    Usage:
        client = OmiumClient(checkpoint_manager_url="localhost:7001")
        await client.connect()
        checkpoint_id = await client.create_checkpoint(...)
        await client.close()
    """
    
    def __init__(
        self,
        checkpoint_manager_url: str = "localhost:7001",
        timeout: float = 30.0,
    ):
        """
        Initialize Omium client.
        
        Args:
            checkpoint_manager_url: Checkpoint Manager gRPC endpoint
            timeout: Request timeout in seconds
        """
        self.checkpoint_manager_url = checkpoint_manager_url
        self.timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._checkpoint_stub: Optional[checkpoint_pb2_grpc.CheckpointServiceStub] = None
        self._execution_id: Optional[str] = None
        self._agent_id: Optional[str] = None
    
    async def connect(self, retries: int = 3, retry_delay: float = 1.0):
        """
        Create gRPC channel and stubs.
        
        Args:
            retries: Number of connection retry attempts
            retry_delay: Delay between retries in seconds
        """
        last_error = None
        for attempt in range(retries):
            try:
                await self._connect_once()
                logger.info(f"Connected to checkpoint manager at {self.checkpoint_manager_url}")
                return
            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect after {retries} attempts")
        
        raise ConnectionError(
            f"Failed to connect to checkpoint manager at {self.checkpoint_manager_url} after {retries} attempts",
            {"last_error": str(last_error), "url": self.checkpoint_manager_url}
        )
    
    async def _connect_once(self):
        """Single connection attempt."""
        # Try multiple import paths
        checkpoint_pb2_module = None
        checkpoint_pb2_grpc_module = None
        
        # Try direct import from checkpoint submodule
        try:
            from omium.proto.checkpoint import checkpoint_pb2, checkpoint_pb2_grpc
            checkpoint_pb2_module = checkpoint_pb2
            checkpoint_pb2_grpc_module = checkpoint_pb2_grpc
        except ImportError as e1:
            # Try importing from proto package directly
            try:
                import omium.proto.checkpoint.checkpoint_pb2 as checkpoint_pb2_module
                import omium.proto.checkpoint.checkpoint_pb2_grpc as checkpoint_pb2_grpc_module
            except ImportError as e2:
                # Try module-level fallback
                import sys
                current_module = sys.modules[__name__]
                if hasattr(current_module, 'checkpoint_pb2') and current_module.checkpoint_pb2 is not None:
                    checkpoint_pb2_module = current_module.checkpoint_pb2
                    checkpoint_pb2_grpc_module = current_module.checkpoint_pb2_grpc
                else:
                    raise ImportError(
                        f"Proto code not found. Tried: omium.proto.checkpoint (error: {e1}), "
                        f"omium.proto.checkpoint.checkpoint_pb2 (error: {e2}). "
                        "Ensure proto files are generated and included in package."
                    )
        
        self._checkpoint_pb2 = checkpoint_pb2_module
        self._checkpoint_pb2_grpc = checkpoint_pb2_grpc_module
        
        self._channel = grpc.aio.insecure_channel(self.checkpoint_manager_url)
        self._checkpoint_stub = self._checkpoint_pb2_grpc.CheckpointServiceStub(self._channel)
        
        # Test connection
        try:
            await asyncio.wait_for(self._channel.channel_ready(), timeout=5.0)
            logger.info(f"Connected to checkpoint-manager at {self.checkpoint_manager_url}")
        except asyncio.TimeoutError:
            raise ConnectionError(f"Failed to connect to {self.checkpoint_manager_url}")
    
    async def close(self):
        """Close gRPC channel."""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._checkpoint_stub = None
            logger.info("Disconnected from checkpoint-manager")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False
    
    def set_execution_context(self, execution_id: str, agent_id: Optional[str] = None):
        """
        Set execution context for checkpoint operations.
        
        Args:
            execution_id: Current execution ID
            agent_id: Optional agent ID
        """
        self._execution_id = execution_id
        self._agent_id = agent_id
    
    def _dict_to_struct(self, data: Dict[str, Any]) -> struct_pb2.Struct:
        """Convert Python dict to protobuf Struct."""
        struct = struct_pb2.Struct()
        struct.update(data)
        return struct
    
    def _struct_to_dict(self, struct: struct_pb2.Struct) -> Dict[str, Any]:
        """Convert protobuf Struct to Python dict."""
        if struct is None:
            return {}
        return json_format.MessageToDict(struct)
    
    async def create_checkpoint(
        self,
        checkpoint_name: str,
        state: Dict[str, Any],
        execution_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        preconditions: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compression_type: str = "none",
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """
        Create a checkpoint.
        
        Args:
            checkpoint_name: Name for the checkpoint
            state: State dictionary to checkpoint
            execution_id: Execution ID (uses context if not provided)
            agent_id: Agent ID (uses context if not provided)
            preconditions: List of precondition strings
            postconditions: List of postcondition strings
            metadata: Optional metadata dictionary
            compression_type: Compression type ("none", "gzip", "zstd")
            ttl_seconds: Optional TTL in seconds
        
        Returns:
            Checkpoint ID
        
        Raises:
            CheckpointError: If checkpoint creation fails
            CheckpointValidationError: If validation fails
        """
        if self._checkpoint_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        execution_id = execution_id or self._execution_id
        agent_id = agent_id or self._agent_id
        
        if execution_id is None:
            raise ValueError("execution_id must be provided or set via set_execution_context()")
        
        # Convert state to protobuf Struct
        state_struct = self._dict_to_struct(state)
        
        # Convert metadata to protobuf Struct
        metadata_struct = self._dict_to_struct(metadata or {})
        
        # Build request
        request = self._checkpoint_pb2.CreateCheckpointRequest(
            execution_id=execution_id,
            agent_id=agent_id or "",
            checkpoint_name=checkpoint_name,
            state=state_struct,
            preconditions=preconditions or [],
            postconditions=postconditions or [],
            metadata=metadata_struct,
            compression_type=compression_type,
            ttl_seconds=ttl_seconds or 0,
        )
        
        try:
            response = await asyncio.wait_for(
                self._checkpoint_stub.CreateCheckpoint(request),
                timeout=self.timeout
            )
            
            if not response.success:
                error_msg = response.error_message or "Unknown error"
                if "validation" in error_msg.lower():
                    raise CheckpointValidationError(error_msg)
                raise CheckpointError(error_msg)
            
            checkpoint_id = response.checkpoint.id
            logger.info(f"Created checkpoint: {checkpoint_id} ({checkpoint_name})")
            return checkpoint_id
            
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise CheckpointNotFoundError(f"Checkpoint not found: {e.details()}")
            error_msg = e.details() or str(e)
            if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                raise CheckpointNotFoundError(f"Checkpoint not found: {error_msg}")
            raise CheckpointError(f"gRPC error: {error_msg}")
        except asyncio.TimeoutError:
            raise CheckpointError(f"Request timeout after {self.timeout}s")
    
    async def get_checkpoint(
        self,
        checkpoint_id: str,
        include_state: bool = True,
    ) -> Dict[str, Any]:
        """
        Get checkpoint details.
        
        Args:
            checkpoint_id: Checkpoint ID
            include_state: Whether to include state blob
        
        Returns:
            Dictionary with checkpoint data
        """
        if self._checkpoint_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._checkpoint_pb2.GetCheckpointRequest(
            checkpoint_id=checkpoint_id,
            include_state=include_state,
        )
        
        try:
            response = await asyncio.wait_for(
                self._checkpoint_stub.GetCheckpoint(request),
                timeout=self.timeout
            )
            
            if not response.success:
                error_msg = response.error_message or "Failed to get checkpoint"
                if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    raise CheckpointNotFoundError(error_msg)
                raise CheckpointError(error_msg)
            
            checkpoint = response.checkpoint
            result = {
                "id": checkpoint.id,
                "execution_id": checkpoint.execution_id,
                "agent_id": checkpoint.agent_id,
                "checkpoint_name": checkpoint.checkpoint_name,
                "checkpoint_index": checkpoint.checkpoint_index,
                "state_size_bytes": checkpoint.state_size_bytes,
                "state_blob_uri": checkpoint.state_blob_uri,
                "checksum": checkpoint.checksum,
                "preconditions": list(checkpoint.preconditions),
                "postconditions": list(checkpoint.postconditions),
                "validation_passed": checkpoint.validation_passed,
                "compression_type": checkpoint.compression_type,
                "created_at": checkpoint.created_at.ToDatetime().isoformat() if checkpoint.created_at else None,
            }
            
            if include_state and response.state:
                result["state"] = self._struct_to_dict(response.state)
            
            return result
            
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise CheckpointNotFoundError(f"Checkpoint not found: {checkpoint_id}")
            raise CheckpointError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise CheckpointError(f"Request timeout after {self.timeout}s")
    
    async def list_checkpoints(
        self,
        execution_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List checkpoints for an execution.
        
        Args:
            execution_id: Execution ID (uses context if not provided)
            limit: Maximum number of checkpoints to return
            offset: Offset for pagination
        
        Returns:
            List of checkpoint dictionaries
        """
        if self._checkpoint_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        execution_id = execution_id or self._execution_id
        if execution_id is None:
            raise ValueError("execution_id must be provided or set via set_execution_context()")
        
        request = self._checkpoint_pb2.ListCheckpointsRequest(
            execution_id=execution_id,
            limit=limit,
            offset=offset,
        )
        
        try:
            response = await asyncio.wait_for(
                self._checkpoint_stub.ListCheckpoints(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise CheckpointError(response.error_message or "Failed to list checkpoints")
            
            checkpoints = []
            for cp in response.checkpoints:
                checkpoints.append({
                    "id": cp.id,
                    "execution_id": cp.execution_id,
                    "agent_id": cp.agent_id,
                    "checkpoint_name": cp.checkpoint_name,
                    "checkpoint_index": cp.checkpoint_index,
                    "created_at": cp.created_at.ToDatetime().isoformat() if cp.created_at else None,
                })
            
            return checkpoints
            
        except grpc.RpcError as e:
            raise CheckpointError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise CheckpointError(f"Request timeout after {self.timeout}s")
    
    async def rollback_to_checkpoint(
        self,
        checkpoint_id: str,
        execution_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        trigger_reason: str = "manual",
        trigger_type: str = "manual",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Rollback execution to a checkpoint.
        
        Args:
            checkpoint_id: Checkpoint ID to rollback to
            execution_id: Execution ID (uses context if not provided)
            triggered_by: User ID who triggered rollback
            trigger_reason: Reason for rollback
            trigger_type: Type of trigger ("manual", "automatic", "policy")
            options: Optional rollback options
        
        Returns:
            Dictionary with rollback details
        """
        if self._checkpoint_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        execution_id = execution_id or self._execution_id
        if execution_id is None:
            raise ValueError("execution_id must be provided or set via set_execution_context()")
        
        options_struct = self._dict_to_struct(options or {})
        
        request = self._checkpoint_pb2.RollbackToCheckpointRequest(
            execution_id=execution_id,
            checkpoint_id=checkpoint_id,
            triggered_by=triggered_by or "",
            trigger_reason=trigger_reason,
            trigger_type=trigger_type,
            options=options_struct,
        )
        
        try:
            response = await asyncio.wait_for(
                self._checkpoint_stub.RollbackToCheckpoint(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise CheckpointError(response.error_message or "Failed to rollback")
            
            return {
                "rollback_id": response.rollback_id,
                "target_checkpoint": {
                    "id": response.target_checkpoint.id,
                    "checkpoint_name": response.target_checkpoint.checkpoint_name,
                },
                "success": response.success,
            }
            
        except grpc.RpcError as e:
            raise CheckpointError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise CheckpointError(f"Request timeout after {self.timeout}s")
    
    async def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Verify checkpoint integrity.
        
        Args:
            checkpoint_id: Checkpoint ID to verify
        
        Returns:
            True if checkpoint is valid
        """
        if self._checkpoint_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._checkpoint_pb2.VerifyCheckpointRequest(checkpoint_id=checkpoint_id)
        
        try:
            response = await asyncio.wait_for(
                self._checkpoint_stub.VerifyCheckpoint(request),
                timeout=self.timeout
            )
            
            return response.valid
            
        except grpc.RpcError as e:
            raise CheckpointError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise CheckpointError(f"Request timeout after {self.timeout}s")
    
    @asynccontextmanager
    async def connection(self):
        """Context manager for client connection."""
        await self.connect()
        try:
            yield self
        finally:
            await self.close()


# Global client instance (lazy initialization)
_global_client: Optional[OmiumClient] = None


def get_client() -> OmiumClient:
    """Get or create global client instance."""
    global _global_client
    if _global_client is None:
        _global_client = OmiumClient()
    return _global_client


def set_client(client: OmiumClient):
    """Set global client instance."""
    global _global_client
    _global_client = client
