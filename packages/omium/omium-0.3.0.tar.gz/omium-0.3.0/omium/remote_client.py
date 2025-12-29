"""
Remote HTTP client for Omium SDK (for cloud API calls).
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import httpx

from .config import get_config
from .client import CheckpointError, CheckpointNotFoundError, CheckpointValidationError

logger = logging.getLogger(__name__)


class RemoteOmiumClient:
    """
    HTTP client for communicating with Omium cloud API.
    
    This client uses REST API calls instead of gRPC, suitable for remote SDK usage.
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize remote Omium client.
        
        Args:
            api_url: Omium API base URL (defaults to config)
            api_key: API key for authentication (defaults to config)
            timeout: Request timeout in seconds
        """
        config = get_config()
        self.api_url = (api_url or config.api_url).rstrip('/')
        self.api_key = api_key or config.api_key
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None
        self._execution_id: Optional[str] = None
        self._agent_id: Optional[str] = None
        
        if not self.api_key:
            raise ValueError(
                "API key required. Set OMIUM_API_KEY environment variable "
                "or run 'omium init' to configure."
            )
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
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
    
    async def create_checkpoint(
        self,
        checkpoint_name: str,
        state: Dict[str, Any],
        execution_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        preconditions: Optional[List[str]] = None,
        postconditions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compression_type: str = "gzip",
        ttl_seconds: Optional[int] = None,
    ) -> str:
        """
        Create a checkpoint via remote API.
        
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
        execution_id = execution_id or self._execution_id
        agent_id = agent_id or self._agent_id
        
        if execution_id is None:
            raise ValueError("execution_id must be provided or set via set_execution_context()")
        
        client = await self._get_client()
        
        request_data = {
            "execution_id": execution_id,
            "agent_id": agent_id,
            "checkpoint_name": checkpoint_name,
            "state": state,
            "preconditions": preconditions or [],
            "postconditions": postconditions or [],
            "metadata": metadata or {},
            "compression_type": compression_type,
            "ttl_seconds": ttl_seconds,
        }
        
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/checkpoints",
                json=request_data,
            )
            
            if response.status_code == 401:
                raise CheckpointError("Invalid API key. Check your OMIUM_API_KEY.")
            
            if response.status_code == 429:
                raise CheckpointError("Rate limit exceeded. Please try again later.")
            
            response.raise_for_status()
            
            result = response.json()
            checkpoint_id = result["id"]
            logger.info(f"Created checkpoint: {checkpoint_id} ({checkpoint_name})")
            return checkpoint_id
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                error_data = e.response.json() if e.response.content else {}
                error_msg = error_data.get("detail", "Validation failed")
                if "validation" in error_msg.lower():
                    raise CheckpointValidationError(error_msg)
                raise CheckpointError(error_msg)
            raise CheckpointError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")
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
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.api_url}/api/v1/checkpoints/{checkpoint_id}",
                params={"include_state": include_state},
            )
            
            if response.status_code == 404:
                raise CheckpointNotFoundError(f"Checkpoint not found: {checkpoint_id}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise CheckpointNotFoundError(f"Checkpoint not found: {checkpoint_id}")
            raise CheckpointError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")
    
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
        execution_id = execution_id or self._execution_id
        if execution_id is None:
            raise ValueError("execution_id must be provided or set via set_execution_context()")
        
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.api_url}/api/v1/checkpoints",
                params={
                    "execution_id": execution_id,
                    "limit": limit,
                    "offset": offset,
                },
            )
            
            response.raise_for_status()
            result = response.json()
            return result.get("checkpoints", [])
            
        except httpx.HTTPStatusError as e:
            raise CheckpointError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")
    
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
        # This would call the execution engine's rollback endpoint
        # For now, we'll implement a basic version
        execution_id = execution_id or self._execution_id
        if execution_id is None:
            raise ValueError("execution_id must be provided or set via set_execution_context()")
        
        client = await self._get_client()
        
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/executions/{execution_id}/rollback",
                json={
                    "checkpoint_id": checkpoint_id,
                },
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise CheckpointError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")
    
    async def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Verify checkpoint integrity.
        
        Args:
            checkpoint_id: Checkpoint ID to verify
        
        Returns:
            True if checkpoint is valid
        """
        try:
            await self.get_checkpoint(checkpoint_id, include_state=False)
            return True
        except CheckpointNotFoundError:
            return False
        except Exception:
            return False
    
    async def register_workflow(
        self,
        workflow_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Register a workflow with Omium backend.
        
        Args:
            workflow_data: Workflow data dictionary with:
                - name: Workflow name
                - description: Optional description
                - workflow_type: "crewai" | "langgraph" | etc.
                - definition: Workflow definition dict
                - config: Optional config dict
                - tags: Optional list of tags
        
        Returns:
            Registered workflow data with ID
        
        Raises:
            CheckpointError: If registration fails
        """
        client = await self._get_client()
        
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/workflows",
                json=workflow_data,
            )
            
            if response.status_code == 401:
                raise CheckpointError("Invalid API key. Check your OMIUM_API_KEY.")
            
            if response.status_code == 429:
                raise CheckpointError("Rate limit exceeded. Please try again later.")
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Registered workflow: {result.get('id')} ({result.get('name')})")
            return result
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            error_msg = error_data.get("detail", f"HTTP error: {e.response.status_code}")
            raise CheckpointError(error_msg)
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")
        except asyncio.TimeoutError:
            raise CheckpointError(f"Request timeout after {self.timeout}s")
    
    async def get_workflow(
        self,
        workflow_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow data or None if not found
        
        Raises:
            CheckpointError: If request fails
        """
        client = await self._get_client()
        
        try:
            response = await client.get(
                f"{self.api_url}/api/v1/workflows/{workflow_id}",
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise CheckpointError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")
    
    async def list_workflows(
        self,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List workflows.
        
        Args:
            status: Filter by status (draft, published, archived)
            workflow_type: Filter by type (crewai, langgraph, etc.)
            page: Page number
            page_size: Page size
        
        Returns:
            Dictionary with workflows list and pagination info
        
        Raises:
            CheckpointError: If request fails
        """
        client = await self._get_client()
        
        params = {
            "page": page,
            "page_size": page_size,
        }
        if status:
            params["status"] = status
        if workflow_type:
            params["workflow_type"] = workflow_type
        
        try:
            response = await client.get(
                f"{self.api_url}/api/v1/workflows",
                params=params,
            )
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise CheckpointError(f"HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise CheckpointError(f"Request failed: {str(e)}")

