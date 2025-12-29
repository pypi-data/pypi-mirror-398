"""
Consensus client for multi-agent coordination.
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
    from omium.proto.consensus import consensus_pb2, consensus_pb2_grpc
except ImportError:
    try:
        from omium.proto import consensus_pb2, consensus_pb2_grpc
    except ImportError:
        consensus_pb2 = None
        consensus_pb2_grpc = None

logger = logging.getLogger(__name__)


class ConsensusError(Exception):
    """Base exception for consensus operations."""
    pass


class ConsensusClient:
    """
    Async gRPC client for Consensus Coordinator service.
    
    Provides multi-agent consensus and handoff capabilities.
    """
    
    def __init__(
        self,
        consensus_coordinator_url: str = "localhost:7002",
        timeout: float = 30.0,
    ):
        """
        Initialize consensus client.
        
        Args:
            consensus_coordinator_url: Consensus Coordinator gRPC endpoint
            timeout: Request timeout in seconds
        """
        self.consensus_coordinator_url = consensus_coordinator_url
        self.timeout = timeout
        self._channel: Optional[grpc.aio.Channel] = None
        self._consensus_stub: Optional[Any] = None
        self._consensus_pb2 = None
        self._consensus_pb2_grpc = None
    
    async def connect(self):
        """Create gRPC channel and stubs."""
        # Try multiple import paths
        try:
            from omium.proto.consensus import consensus_pb2, consensus_pb2_grpc
            self._consensus_pb2 = consensus_pb2
            self._consensus_pb2_grpc = consensus_pb2_grpc
        except ImportError as e1:
            try:
                from omium.proto import consensus_pb2, consensus_pb2_grpc
                self._consensus_pb2 = consensus_pb2
                self._consensus_pb2_grpc = consensus_pb2_grpc
            except ImportError as e2:
                raise ImportError(
                    f"Consensus proto code not found. Tried: omium.proto.consensus (error: {e1}), "
                    f"omium.proto (error: {e2}). "
                    "Ensure proto files are generated and included in package."
                )
        
        self._channel = grpc.aio.insecure_channel(self.consensus_coordinator_url)
        self._consensus_stub = self._consensus_pb2_grpc.ConsensusServiceStub(self._channel)
        
        # Test connection
        try:
            await asyncio.wait_for(self._channel.channel_ready(), timeout=5.0)
            logger.info(f"Connected to consensus-coordinator at {self.consensus_coordinator_url}")
        except asyncio.TimeoutError:
            raise ConnectionError(f"Failed to connect to {self.consensus_coordinator_url}")
    
    async def close(self):
        """Close gRPC channel."""
        if self._channel:
            await self._channel.close()
            logger.info("Closed consensus client connection")
    
    def _dict_to_struct(self, data: Dict[str, Any]) -> struct_pb2.Struct:
        """Convert Python dict to protobuf Struct."""
        return json_format.ParseDict(data, struct_pb2.Struct())
    
    def _struct_to_dict(self, struct: struct_pb2.Struct) -> Dict[str, Any]:
        """Convert protobuf Struct to Python dict."""
        if struct is None:
            return {}
        return json_format.MessageToDict(struct)
    
    async def broadcast_message(
        self,
        execution_id: str,
        sender_agent_id: str,
        receiver_agent_ids: List[str],
        message_type: int,
        payload: Dict[str, Any],
        acks_required: Optional[int] = None,
        timeout_seconds: int = 5,
    ) -> Dict[str, Any]:
        """
        Broadcast message to agents with consensus guarantees.
        
        Args:
            execution_id: Execution ID
            sender_agent_id: Sender agent ID
            receiver_agent_ids: List of receiver agent IDs
            message_type: Message type (1=HANDOFF, 2=STATE_UPDATE, etc.)
            payload: Message payload
            acks_required: Number of acknowledgments required (default: majority)
            timeout_seconds: Timeout for consensus
        
        Returns:
            Dictionary with consensus result
        """
        if self._consensus_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        if acks_required is None:
            # Default to majority
            acks_required = (len(receiver_agent_ids) // 2) + 1
        
        request = self._consensus_pb2.BroadcastMessageRequest(
            execution_id=execution_id,
            sender_agent_id=sender_agent_id,
            receiver_agent_ids=receiver_agent_ids,
            message_type=message_type,
            payload=self._dict_to_struct(payload),
            acks_required=acks_required,
            timeout_seconds=timeout_seconds,
        )
        
        try:
            response = await asyncio.wait_for(
                self._consensus_stub.BroadcastMessage(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise ConsensusError(response.error_message or "Failed to broadcast message")
            
            result = {
                "message_id": response.message.id if response.message else None,
                "consensus_reached": response.consensus_reached,
                "acks_received": response.acks_received,
                "acks_required": response.acks_required,
                "acknowledged_by": list(response.acknowledged_by),
            }
            
            if response.message and response.message.payload:
                result["payload"] = self._struct_to_dict(response.message.payload)
            
            return result
            
        except grpc.RpcError as e:
            raise ConsensusError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise ConsensusError(f"Request timeout after {self.timeout}s")
    
    async def acknowledge_message(
        self,
        message_id: str,
        agent_id: str,
        valid: bool = True,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Acknowledge receipt of a consensus message.
        
        Args:
            message_id: Message ID to acknowledge
            agent_id: Agent ID acknowledging
            valid: Whether message is valid
            error_message: Error message if invalid
        
        Returns:
            Dictionary with acknowledgment result
        """
        if self._consensus_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._consensus_pb2.AcknowledgeMessageRequest(
            message_id=message_id,
            agent_id=agent_id,
            valid=valid,
            error_message=error_message or "",
        )
        
        try:
            response = await asyncio.wait_for(
                self._consensus_stub.AcknowledgeMessage(request),
                timeout=self.timeout
            )
            
            return {
                "success": response.success,
                "consensus_reached": response.consensus_reached,
            }
            
        except grpc.RpcError as e:
            raise ConsensusError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise ConsensusError(f"Request timeout after {self.timeout}s")
    
    async def propose_handoff(
        self,
        execution_id: str,
        from_agent_id: str,
        to_agent_id: str,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Propose handoff from one agent to another.
        
        Args:
            execution_id: Execution ID
            from_agent_id: Source agent ID
            to_agent_id: Target agent ID
            state: State to hand off
            context: Optional context
        
        Returns:
            Dictionary with handoff proposal details
        """
        if self._consensus_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._consensus_pb2.ProposeHandoffRequest(
            execution_id=execution_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            state=self._dict_to_struct(state),
            context=self._dict_to_struct(context) if context else None,
        )
        
        try:
            response = await asyncio.wait_for(
                self._consensus_stub.ProposeHandoff(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise ConsensusError(response.error_message or "Failed to propose handoff")
            
            proposal = response.proposal
            result = {
                "proposal_id": proposal.id if proposal else None,
                "execution_id": proposal.execution_id if proposal else None,
                "from_agent_id": proposal.from_agent_id if proposal else None,
                "to_agent_id": proposal.to_agent_id if proposal else None,
                "success": response.success,
            }
            
            if proposal and proposal.state:
                result["state"] = self._struct_to_dict(proposal.state)
            if proposal and proposal.context:
                result["context"] = self._struct_to_dict(proposal.context)
            
            return result
            
        except grpc.RpcError as e:
            raise ConsensusError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise ConsensusError(f"Request timeout after {self.timeout}s")
    
    async def vote_on_handoff(
        self,
        proposal_id: str,
        agent_id: str,
        vote: bool,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Vote on a handoff proposal.
        
        Args:
            proposal_id: Handoff proposal ID
            agent_id: Agent ID voting
            vote: True to accept, False to reject
            reason: Reason for vote
        
        Returns:
            Dictionary with voting result
        """
        if self._consensus_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._consensus_pb2.VoteOnHandoffRequest(
            proposal_id=proposal_id,
            agent_id=agent_id,
            vote=vote,
            reason=reason or "",
        )
        
        try:
            response = await asyncio.wait_for(
                self._consensus_stub.VoteOnHandoff(request),
                timeout=self.timeout
            )
            
            if not response.success:
                raise ConsensusError(response.error_message or "Failed to vote")
            
            return {
                "success": response.success,
                "proposal_accepted": response.proposal_accepted,
                "votes_for": response.votes_for,
                "votes_against": response.votes_against,
                "votes_required": response.votes_required,
            }
            
        except grpc.RpcError as e:
            raise ConsensusError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise ConsensusError(f"Request timeout after {self.timeout}s")
    
    async def get_consensus_status(
        self,
        execution_id: str,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get consensus status for a message or execution.
        
        Args:
            execution_id: Execution ID
            message_id: Optional message ID
        
        Returns:
            Dictionary with consensus status
        """
        if self._consensus_stub is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        request = self._consensus_pb2.GetConsensusStatusRequest(
            execution_id=execution_id,
            message_id=message_id or "",
        )
        
        try:
            response = await asyncio.wait_for(
                self._consensus_stub.GetConsensusStatus(request),
                timeout=self.timeout
            )
            
            return {
                "consensus_reached": response.consensus_reached,
                "acks_received": response.acks_received,
                "acks_required": response.acks_required,
                "acknowledged_by": list(response.acknowledged_by),
                "pending_agents": list(response.pending_agents),
            }
            
        except grpc.RpcError as e:
            raise ConsensusError(f"gRPC error: {e.details()}")
        except asyncio.TimeoutError:
            raise ConsensusError(f"Request timeout after {self.timeout}s")

