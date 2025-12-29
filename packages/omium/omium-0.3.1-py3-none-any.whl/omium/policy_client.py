"""
Policy Engine client for Python services.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List

import grpc
from google.protobuf import struct_pb2
from google.protobuf import json_format

# Import generated proto code
try:
    from omium.proto.policy import policy_pb2, policy_pb2_grpc
except ImportError:
    try:
        from omium.proto import policy_pb2, policy_pb2_grpc
    except ImportError:
        policy_pb2 = None
        policy_pb2_grpc = None

logger = logging.getLogger(__name__)


class PolicyError(Exception):
    """Base exception for policy operations."""
    pass


class PolicyClient:
    """
    Async gRPC client for Policy Engine service.
    
    Provides policy evaluation and management capabilities.
    """
    
    def __init__(
        self,
        policy_engine_url: str = "localhost:7004",
        timeout: float = 30.0,
    ):
        """
        Initialize policy client.
        
        Args:
            policy_engine_url: Policy Engine gRPC endpoint
            timeout: Request timeout in seconds
        """
        self.policy_engine_url = policy_engine_url
        self.timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._policy_stub: Optional[Any] = None
        self._policy_pb2 = None
        self._policy_pb2_grpc = None
    
    async def connect(self):
        """Create gRPC channel and stubs."""
        # Try multiple import paths
        try:
            from omium.proto.policy import policy_pb2, policy_pb2_grpc
            self._policy_pb2 = policy_pb2
            self._policy_pb2_grpc = policy_pb2_grpc
        except ImportError as e1:
            try:
                from omium.proto import policy_pb2, policy_pb2_grpc
                self._policy_pb2 = policy_pb2
                self._policy_pb2_grpc = policy_pb2_grpc
            except ImportError as e2:
                raise ImportError(
                    f"Policy proto code not found. Tried: omium.proto.policy (error: {e1}), "
                    f"omium.proto (error: {e2}). "
                    "Ensure proto files are generated and included in package."
                )
        
        self._channel = grpc.aio.insecure_channel(self.policy_engine_url)
        self._policy_stub = self._policy_pb2_grpc.PolicyServiceStub(self._channel)
        
        # Test connection
        try:
            await asyncio.wait_for(self._channel.channel_ready(), timeout=5.0)
            logger.info(f"Connected to policy-engine at {self.policy_engine_url}")
        except asyncio.TimeoutError:
            raise ConnectionError(f"Failed to connect to {self.policy_engine_url}")
    
    async def close(self):
        """Close gRPC channel."""
        if self._channel:
            await self._channel.close()
            logger.info("Closed policy client connection")
    
    def _dict_to_struct(self, data: Dict[str, Any]) -> struct_pb2.Struct:
        """Convert Python dict to protobuf Struct."""
        return json_format.ParseDict(data, struct_pb2.Struct())
    
    def _struct_to_dict(self, struct: struct_pb2.Struct) -> Dict[str, Any]:
        """Convert protobuf Struct to Python dict."""
        if struct is None:
            return {}
        return json_format.MessageToDict(struct)
    
    async def evaluate_policy(
        self,
        policy_id: str,
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate a policy against execution context.
        
        Args:
            policy_id: Policy ID to evaluate
            execution_context: Execution context (failure type, execution details, etc.)
        
        Returns:
            Dictionary with policy evaluation result
        """
        if self._policy_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._policy_pb2.EvaluatePolicyRequest(
            policy_id=policy_id,
            execution_context=self._dict_to_struct(execution_context),
        )
        
        try:
            response = await asyncio.wait_for(
                self._policy_stub.EvaluatePolicy(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise PolicyError(response.error_message or "Failed to evaluate policy")
            
            result = response.result
            evaluation_result = {
                "policy_id": result.policy_id,
                "triggered": result.triggered,
                "reason": result.reason,
                "recovery_actions": {
                    "rollback_to_last_checkpoint": result.actions.rollback_to_last_checkpoint,
                    "pause_and_notify": result.actions.pause_and_notify,
                    "await_human_review": result.actions.await_human_review,
                    "allowed_edits": list(result.actions.allowed_edits),
                    "forbidden_edits": list(result.actions.forbidden_edits),
                },
                "retry_policy": {
                    "max_retries": result.retry_policy.max_retries,
                    "backoff": result.retry_policy.backoff,
                    "condition": result.retry_policy.condition,
                },
            }
            
            return evaluation_result
            
        except grpc.RpcError as e:
            raise PolicyError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise PolicyError(f"Request timeout after {self.timeout}s")
    
    async def get_policy(self, policy_id: str) -> Dict[str, Any]:
        """Get policy details."""
        if self._policy_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._policy_pb2.GetPolicyRequest(policy_id=policy_id)
        
        try:
            response = await asyncio.wait_for(
                self._policy_stub.GetPolicy(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise PolicyError(response.error_message or "Failed to get policy")
            
            policy = response.policy
            return {
                "id": policy.id,
                "tenant_id": policy.tenant_id,
                "name": policy.name,
                "description": policy.description,
                "version": policy.version,
                "enabled": policy.enabled,
                "definition": self._struct_to_dict(policy.definition) if policy.definition else {},
            }
            
        except grpc.RpcError as e:
            raise PolicyError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise PolicyError(f"Request timeout after {self.timeout}s")
    
    async def list_policies(
        self,
        tenant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List policies for a tenant."""
        if self._policy_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._policy_pb2.ListPoliciesRequest(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
        )
        
        try:
            response = await asyncio.wait_for(
                self._policy_stub.ListPolicies(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise PolicyError(response.error_message or "Failed to list policies")
            
            policies = []
            for policy in response.policies:
                policies.append({
                    "id": policy.id,
                    "tenant_id": policy.tenant_id,
                    "name": policy.name,
                    "description": policy.description,
                    "version": policy.version,
                    "enabled": policy.enabled,
                })
            
            return policies
            
        except grpc.RpcError as e:
            raise PolicyError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise PolicyError(f"Request timeout after {self.timeout}s")

