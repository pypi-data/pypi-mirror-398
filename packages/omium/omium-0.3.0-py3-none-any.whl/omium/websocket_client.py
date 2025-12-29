"""
WebSocket client for receiving real-time execution updates from Omium.

Features:
- Automatic reconnection with exponential backoff
- Ping/pong heartbeat handling
- Simple async iterator interface for updates
"""

import asyncio
import json
import logging
import time
from typing import AsyncIterator, Optional, Dict, Any, Callable

import websockets


logger = logging.getLogger(__name__)


class ExecutionWebSocketClient:
    """
    High-level WebSocket client for execution progress streaming.

    Usage:
        client = ExecutionWebSocketClient(base_url, api_key)
        async for msg in client.stream(execution_id):
            ...
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        reconnect: bool = True,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        max_retries: Optional[int] = None,
    ) -> None:
        # Expect base_url like: wss://api.omium.ai/api/v1/ws
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.reconnect = reconnect
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.max_retries = max_retries

    async def stream(
        self,
        execution_id: str,
        *,
        on_connected: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Connect to the execution WebSocket and yield messages as they arrive.

        Automatically reconnects with exponential backoff if connection drops.
        """
        attempt = 0
        backoff = self.initial_backoff

        url = f"{self.base_url}/executions/{execution_id}?api_key={self.api_key}"

        while True:
            if self.max_retries is not None and attempt > self.max_retries:
                logger.error(
                    "Maximum WebSocket reconnect attempts reached (execution_id=%s)", execution_id
                )
                break

            try:
                logger.info("Connecting to execution WebSocket: %s", url)
                async with websockets.connect(url) as ws:
                    attempt = 0
                    backoff = self.initial_backoff

                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                        except Exception:
                            # Already JSON from server or invalid JSON; wrap as dict if needed
                            if isinstance(raw, dict):
                                msg = raw
                            else:
                                logger.debug("Received non-JSON WebSocket message: %r", raw)
                                continue

                        msg_type = msg.get("type")
                        if msg_type == "connected" and on_connected:
                            on_connected(msg)
                        elif msg_type in {"ping", "pong"}:
                            # Heartbeat messages; respond to ping
                            if msg_type == "ping":
                                await ws.send(
                                    json.dumps(
                                        {
                                            "type": "pong",
                                            "execution_id": execution_id,
                                            "timestamp": time.time(),
                                        }
                                    )
                                )
                            continue

                        yield msg

                    # Normal close from server - stop unless reconnect explicitly desired
                    if not self.reconnect:
                        break

            except Exception as exc:
                attempt += 1
                logger.warning(
                    "WebSocket connection error (attempt=%s, backoff=%.1fs): %s",
                    attempt,
                    backoff,
                    exc,
                )
                if not self.reconnect:
                    break

                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self.max_backoff)


