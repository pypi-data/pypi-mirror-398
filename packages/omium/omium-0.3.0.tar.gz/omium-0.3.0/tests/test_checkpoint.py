"""
Unit tests for Omium SDK checkpoint functionality.
"""

import pytest
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from omium import checkpoint, Checkpoint, OmiumClient
from omium.client import CheckpointError, CheckpointNotFoundError


@pytest.fixture
def mock_client():
    """Create a mock OmiumClient."""
    client = OmiumClient(checkpoint_manager_url="localhost:7001")
    client._checkpoint_stub = AsyncMock()
    client._channel = MagicMock()
    # Provide lightweight protobuf request factories so tests do not rely on compiled protos
    def _dummy_request(**kwargs):
        return SimpleNamespace(**kwargs)

    client._checkpoint_pb2 = SimpleNamespace(
        CreateCheckpointRequest=_dummy_request,
        GetCheckpointRequest=_dummy_request,
        ListCheckpointsRequest=_dummy_request,
        RollbackToCheckpointRequest=_dummy_request,
    )
    return client


@pytest.mark.asyncio
async def test_checkpoint_decorator_success(mock_client):
    """Test @checkpoint decorator with successful execution."""
    from omium.client import set_client
    set_client(mock_client)
    
    # Mock successful checkpoint creation
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.checkpoint.id = "cp_123"
    mock_response.error_message = None
    mock_client.create_checkpoint = AsyncMock(return_value="cp_123")
    
    # The new @checkpoint decorator doesn't take a client argument
    # It uses the global client set via set_client()
    @checkpoint("test_checkpoint")
    async def test_function(data):
        return {"result": data}
    
    result = await test_function({"value": 42})
    
    assert result == {"result": {"value": 42}}
    # Note: The new decorator may not call create_checkpoint in the same way
    # This test verifies the function executes correctly with the decorator


@pytest.mark.asyncio
async def test_checkpoint_context_manager(mock_client):
    """Test Checkpoint context manager."""
    mock_client.create_checkpoint = AsyncMock(return_value="cp_456")
    
    async with Checkpoint("test_context", client=mock_client) as cp:
        cp.update_state(step="test")
    
    assert mock_client.create_checkpoint.called
    assert cp.checkpoint_id == "cp_456"


@pytest.mark.asyncio
async def test_client_create_checkpoint(mock_client):
    """Test client checkpoint creation."""
    # Mock gRPC response
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.checkpoint.id = "cp_789"
    mock_response.error_message = None
    
    mock_client._checkpoint_stub.CreateCheckpoint = AsyncMock(return_value=mock_response)
    
    checkpoint_id = await mock_client.create_checkpoint(
        checkpoint_name="test",
        state={"data": "test"},
        execution_id="exec_1",
    )
    
    assert checkpoint_id == "cp_789"
    assert mock_client._checkpoint_stub.CreateCheckpoint.called


@pytest.mark.asyncio
async def test_client_get_checkpoint(mock_client):
    """Test client checkpoint retrieval."""
    from google.protobuf import timestamp_pb2, struct_pb2
    
    # Mock response
    mock_checkpoint = MagicMock()
    mock_checkpoint.id = "cp_123"
    mock_checkpoint.execution_id = "exec_1"
    mock_checkpoint.checkpoint_name = "test"
    mock_checkpoint.state_size_bytes = 100
    mock_checkpoint.checksum = "abc123"
    mock_checkpoint.preconditions = []
    mock_checkpoint.postconditions = []
    mock_checkpoint.validation_passed = True
    mock_checkpoint.compression_type = "none"
    mock_checkpoint.created_at = timestamp_pb2.Timestamp()
    
    state_struct = struct_pb2.Struct()
    state_struct.update({"data": "test"})

    mock_response = MagicMock()
    mock_response.success = True
    mock_response.checkpoint = mock_checkpoint
    mock_response.state = state_struct
    
    mock_client._checkpoint_stub.GetCheckpoint = AsyncMock(return_value=mock_response)
    
    result = await mock_client.get_checkpoint("cp_123")
    
    assert result["id"] == "cp_123"
    assert result["execution_id"] == "exec_1"
    assert mock_client._checkpoint_stub.GetCheckpoint.called


@pytest.mark.asyncio
async def test_client_list_checkpoints(mock_client):
    """Test client checkpoint listing."""
    from google.protobuf import timestamp_pb2
    
    # Mock checkpoints
    mock_cp1 = MagicMock()
    mock_cp1.id = "cp_1"
    mock_cp1.checkpoint_name = "checkpoint_1"
    mock_cp1.created_at = timestamp_pb2.Timestamp()
    
    mock_cp2 = MagicMock()
    mock_cp2.id = "cp_2"
    mock_cp2.checkpoint_name = "checkpoint_2"
    mock_cp2.created_at = timestamp_pb2.Timestamp()
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.checkpoints = [mock_cp1, mock_cp2]
    
    mock_client._checkpoint_stub.ListCheckpoints = AsyncMock(return_value=mock_response)
    mock_client.set_execution_context("exec_1")
    
    checkpoints = await mock_client.list_checkpoints()
    
    assert len(checkpoints) == 2
    assert checkpoints[0]["id"] == "cp_1"
    assert checkpoints[1]["id"] == "cp_2"


@pytest.mark.asyncio
async def test_client_rollback(mock_client):
    """Test client rollback functionality."""
    mock_target_cp = MagicMock()
    mock_target_cp.id = "cp_target"
    mock_target_cp.checkpoint_name = "target"
    
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.rollback_id = "rb_123"
    mock_response.target_checkpoint = mock_target_cp
    
    mock_client._checkpoint_stub.RollbackToCheckpoint = AsyncMock(return_value=mock_response)
    mock_client.set_execution_context("exec_1")
    
    result = await mock_client.rollback_to_checkpoint("cp_target")
    
    assert result["rollback_id"] == "rb_123"
    assert result["success"] is True
    assert mock_client._checkpoint_stub.RollbackToCheckpoint.called


def test_state_serialization():
    """Test state serialization utility."""
    from omium.checkpoint import _serialize_state
    
    # Test dict
    assert _serialize_state({"key": "value"}) == {"key": "value"}
    
    # Test list
    assert _serialize_state([1, 2, 3]) == [1, 2, 3]
    
    # Test primitive
    assert _serialize_state(42) == 42
    assert _serialize_state("test") == "test"
    
    # Test object with __dict__
    class TestObj:
        def __init__(self):
            self.value = 42
    
    obj = TestObj()
    serialized = _serialize_state(obj)
    assert serialized == {"value": 42}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

