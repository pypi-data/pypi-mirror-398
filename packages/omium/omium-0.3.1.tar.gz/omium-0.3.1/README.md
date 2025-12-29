# Omium Python SDK

Python SDK for integrating Omium checkpoint and recovery capabilities into your agent workflows.

## Installation

### From PyPI (recommended)

```bash
python -m pip install --upgrade pip
python -m pip install omium
```

The package is signed and published via PyPI’s Trusted Publisher workflow so that no API
tokens are stored in the repository. Enable pip’s hash-checking mode or use `pipx` if you
need additional supply-chain guarantees.

### From source (development)

```bash
cd omium-platform/sdk/python
python -m pip install -e ".[dev]"
```

## Quick Start

### 1. Setup Client

```python
from omium import OmiumClient

client = OmiumClient(checkpoint_manager_url="localhost:7001")
await client.connect()
client.set_execution_context(execution_id="exec_123", agent_id="agent_1")
```

### 2. Using @checkpoint Decorator

```python
from omium import checkpoint

@checkpoint("validate_data", preconditions=["data is not None"])
async def validate_data(data: dict) -> dict:
    assert data is not None
    assert "value" in data
    return {"validated": True, "data": data}

# Use the function
result = await validate_data({"value": 42})
```

### 3. Using Checkpoint Context Manager

```python
from omium import Checkpoint

async with Checkpoint("important_state", client=client) as cp:
    # Critical code here
    result = await do_critical_thing()
    cp.update_state(step="complete")
    # Checkpoint saved automatically on exit
```

### 4. Manual Checkpoint Creation

```python
checkpoint_id = await client.create_checkpoint(
    checkpoint_name="manual_checkpoint",
    state={"data": "important"},
    preconditions=["data exists"],
    postconditions=["data is valid"],
)
```

### 5. Rollback to Checkpoint

```python
rollback_result = await client.rollback_to_checkpoint(
    checkpoint_id="cp_123",
    trigger_reason="manual rollback",
)
```

## Features

- **@checkpoint Decorator** - Automatic checkpoint creation before/after function execution
- **Checkpoint Context Manager** - Manual checkpoint control with context manager
- **Async gRPC Client** - High-performance async communication with checkpoint-manager
- **State Serialization** - Automatic serialization of function arguments and results
- **Pre/Post Conditions** - Validation support for checkpoint creation
- **Rollback Support** - Rollback execution to any checkpoint

## Examples

See `examples/basic_checkpoint.py` for complete examples.

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=omium --cov-report=html
```

## API Reference

### OmiumClient

Main client for checkpoint operations.

#### Methods

- `connect()` - Connect to checkpoint-manager service
- `close()` - Close connection
- `set_execution_context(execution_id, agent_id)` - Set execution context
- `create_checkpoint(...)` - Create a checkpoint
- `get_checkpoint(checkpoint_id)` - Get checkpoint details
- `list_checkpoints(execution_id)` - List checkpoints for execution
- `rollback_to_checkpoint(checkpoint_id)` - Rollback to checkpoint
- `verify_checkpoint(checkpoint_id)` - Verify checkpoint integrity

### @checkpoint Decorator

```python
@checkpoint(
    name: str,
    preconditions: Optional[List[str]] = None,
    postconditions: Optional[List[str]] = None,
    client: Optional[OmiumClient] = None,
    execution_id: Optional[str] = None,
    agent_id: Optional[str] = None,
)
```

### Checkpoint Context Manager

```python
Checkpoint(
    name: str,
    client: Optional[OmiumClient] = None,
    execution_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    preconditions: Optional[List[str]] = None,
    postconditions: Optional[List[str]] = None,
)
```

## Requirements

- Python >= 3.11
- grpcio >= 1.60.0
- protobuf >= 4.25.0

## Development

### Generating Proto Code

```bash
# From sdk/python directory
python -m grpc_tools.protoc \
    --python_out=omium/proto \
    --grpc_python_out=omium/proto \
    --proto_path=../../shared/proto \
    ../../shared/proto/checkpoint/checkpoint.proto
```

Or use the script:

```bash
.\scripts\generate-proto.ps1  # Windows
./scripts/generate-proto.sh   # Linux/Mac
```

## License

Proprietary - Omium Platform
