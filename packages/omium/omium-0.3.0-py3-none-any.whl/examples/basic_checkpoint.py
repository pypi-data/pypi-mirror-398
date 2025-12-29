"""
Basic checkpoint example using Omium SDK.

This example demonstrates:
1. Setting up the Omium client
2. Using the @checkpoint decorator
3. Using the Checkpoint context manager
"""

import asyncio
import logging
from omium import OmiumClient, checkpoint, Checkpoint

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Example 1: Using @checkpoint decorator
@checkpoint("validate_data", preconditions=["data is not None"])
async def validate_data(data: dict) -> dict:
    """Validate data with automatic checkpointing."""
    logger.info(f"Validating data: {data}")
    
    # Simulate validation
    assert data is not None, "Data cannot be None"
    assert "value" in data, "Data must contain 'value' key"
    assert data["value"] > 0, "Value must be positive"
    
    return {"validated": True, "data": data}


# Example 2: Using Checkpoint context manager
async def process_with_checkpoint(data: dict):
    """Process data with manual checkpoint control."""
    client = OmiumClient(checkpoint_manager_url="localhost:7001")
    
    try:
        await client.connect()
        client.set_execution_context(execution_id="exec_123", agent_id="agent_1")
        
        async with Checkpoint("important_processing", client=client) as cp:
            logger.info("Starting critical processing...")
            
            # Critical operations
            result = {"processed": True, "data": data}
            cp.update_state(step="processing_complete")
            
            logger.info("Processing complete")
            return result
            
    finally:
        await client.close()


# Example 3: Full workflow with multiple checkpoints
@checkpoint("step1_initialize")
async def initialize():
    """Initialize workflow."""
    logger.info("Initializing...")
    return {"status": "initialized"}


@checkpoint("step2_process")
async def process(initial_data: dict):
    """Process data."""
    logger.info("Processing...")
    return {"status": "processed", "data": initial_data}


@checkpoint("step3_finalize")
async def finalize(processed_data: dict):
    """Finalize workflow."""
    logger.info("Finalizing...")
    return {"status": "complete", "result": processed_data}


async def main():
    """Main example function."""
    logger.info("=== Omium SDK Checkpoint Examples ===\n")
    
    # Example 1: Decorator usage
    logger.info("Example 1: Using @checkpoint decorator")
    try:
        client = OmiumClient(checkpoint_manager_url="localhost:7001")
        await client.connect()
        client.set_execution_context(execution_id="exec_example1", agent_id="agent_1")
        
        result = await validate_data({"value": 42})
        logger.info(f"Result: {result}\n")
        
        await client.close()
    except Exception as e:
        logger.error(f"Example 1 failed: {e}\n")
    
    # Example 2: Context manager usage
    logger.info("Example 2: Using Checkpoint context manager")
    try:
        result = await process_with_checkpoint({"value": 100})
        logger.info(f"Result: {result}\n")
    except Exception as e:
        logger.error(f"Example 2 failed: {e}\n")
    
    # Example 3: Full workflow
    logger.info("Example 3: Full workflow with multiple checkpoints")
    try:
        client = OmiumClient(checkpoint_manager_url="localhost:7001")
        await client.connect()
        client.set_execution_context(execution_id="exec_example3", agent_id="agent_1")
        
        init_result = await initialize()
        process_result = await process(init_result)
        final_result = await finalize(process_result)
        
        logger.info(f"Final result: {final_result}\n")
        
        # List checkpoints
        checkpoints = await client.list_checkpoints()
        logger.info(f"Created {len(checkpoints)} checkpoints:")
        for cp in checkpoints:
            logger.info(f"  - {cp['checkpoint_name']} ({cp['id']})")
        
        await client.close()
    except Exception as e:
        logger.error(f"Example 3 failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())

