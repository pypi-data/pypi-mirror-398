"""
Omium CLI Streaming - Live log streaming and real-time monitoring.

This module provides utilities for streaming logs and monitoring executions in real-time.
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, Callable, AsyncIterator

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

from omium.output import (
    console, print_success, print_error, print_warning, print_info,
    print_header, print_divider, OmiumSpinner
)


async def stream_execution_logs(
    execution_id: str,
    execution_engine_url: str = "http://localhost:8000",
    websocket_url: Optional[str] = None,
    follow: bool = True,
    tail: int = 50,
    on_log: Optional[Callable[[dict], None]] = None
) -> AsyncIterator[dict]:
    """
    Stream logs from an execution in real-time.
    
    Args:
        execution_id: The execution ID to stream logs from
        execution_engine_url: Base URL of the execution engine
        websocket_url: Optional WebSocket URL for real-time streaming
        follow: If True, continue streaming new logs as they arrive
        tail: Number of recent logs to fetch initially
        on_log: Optional callback for each log entry
        
    Yields:
        Log entry dictionaries
    """
    # First, fetch existing logs via HTTP
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{execution_engine_url}/api/v1/executions/{execution_id}/logs",
                params={"tail": tail}
            )
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                
                for log in logs:
                    if on_log:
                        on_log(log)
                    yield log
                    
            elif response.status_code == 404:
                print_error(f"Execution not found: {execution_id}")
                return
            else:
                print_warning(f"Could not fetch logs: {response.status_code}")
                
        except httpx.RequestError as e:
            print_warning(f"Could not connect to fetch logs: {e}")
    
    # If follow mode, try WebSocket streaming
    if follow:
        ws_url = websocket_url or execution_engine_url.replace("http", "ws")
        ws_endpoint = f"{ws_url}/ws/executions/{execution_id}/logs"
        
        try:
            async with websockets.connect(ws_endpoint) as ws:
                console.print("[dim]Connected to live log stream...[/dim]")
                while True:
                    try:
                        message = await ws.recv()
                        log = json.loads(message)
                        if on_log:
                            on_log(log)
                        yield log
                    except ConnectionClosed:
                        console.print("[dim]Log stream disconnected[/dim]")
                        break
        except Exception as e:
            # WebSocket not available, fall back to polling
            console.print(f"[dim]WebSocket not available, using polling mode...[/dim]")
            await _poll_logs(execution_id, execution_engine_url, on_log)


async def _poll_logs(
    execution_id: str,
    execution_engine_url: str,
    on_log: Optional[Callable[[dict], None]] = None,
    poll_interval: float = 2.0
):
    """Poll for new logs when WebSocket is not available."""
    seen_log_ids = set()
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(
                    f"{execution_engine_url}/api/v1/executions/{execution_id}/logs"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logs = data.get("logs", [])
                    
                    for log in logs:
                        log_id = log.get("id") or log.get("timestamp")
                        if log_id and log_id not in seen_log_ids:
                            seen_log_ids.add(log_id)
                            if on_log:
                                on_log(log)
                    
                    # Check if execution is complete
                    exec_response = await client.get(
                        f"{execution_engine_url}/api/v1/executions/{execution_id}"
                    )
                    if exec_response.status_code == 200:
                        execution = exec_response.json()
                        status = execution.get("status", "")
                        if status in ("completed", "failed", "cancelled"):
                            console.print(f"[dim]Execution {status}. Stopping log stream.[/dim]")
                            break
                            
            except httpx.RequestError:
                pass  # Ignore connection errors during polling
                
            await asyncio.sleep(poll_interval)


def format_log_entry(log: dict) -> str:
    """Format a log entry for display."""
    timestamp = log.get("timestamp", "")
    level = log.get("level", "INFO").upper()
    message = log.get("message", "")
    agent_id = log.get("agent_id", "")
    
    # Format timestamp
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            timestamp = dt.strftime("%H:%M:%S.%f")[:-3]
        except:
            timestamp = timestamp[:12]
    
    # Color based on level
    level_colors = {
        "DEBUG": "dim",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold red"
    }
    level_color = level_colors.get(level, "white")
    
    # Format the line
    parts = []
    if timestamp:
        parts.append(f"[dim]{timestamp}[/dim]")
    parts.append(f"[{level_color}]{level:7}[/{level_color}]")
    if agent_id:
        parts.append(f"[cyan][{agent_id}][/cyan]")
    parts.append(message)
    
    return " ".join(parts)


def print_log_entry(log: dict) -> None:
    """Print a formatted log entry to the console."""
    formatted = format_log_entry(log)
    console.print(formatted)


async def get_execution_status(
    execution_id: str,
    execution_engine_url: str = "http://localhost:8000"
) -> Optional[dict]:
    """Get current execution status."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{execution_engine_url}/api/v1/executions/{execution_id}"
            )
            if response.status_code == 200:
                return response.json()
        except httpx.RequestError:
            pass
    return None


async def watch_execution(
    execution_id: str,
    execution_engine_url: str = "http://localhost:8000",
    update_callback: Optional[Callable[[dict], None]] = None,
    poll_interval: float = 1.0
) -> None:
    """
    Watch an execution for status changes.
    
    Args:
        execution_id: The execution ID to watch
        execution_engine_url: Base URL of the execution engine
        update_callback: Called when status changes
        poll_interval: Seconds between status checks
    """
    last_status = None
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                response = await client.get(
                    f"{execution_engine_url}/api/v1/executions/{execution_id}"
                )
                
                if response.status_code == 200:
                    execution = response.json()
                    current_status = execution.get("status")
                    
                    if current_status != last_status:
                        last_status = current_status
                        if update_callback:
                            update_callback(execution)
                    
                    # Stop watching if execution is done
                    if current_status in ("completed", "failed", "cancelled"):
                        break
                        
            except httpx.RequestError:
                pass
                
            await asyncio.sleep(poll_interval)
