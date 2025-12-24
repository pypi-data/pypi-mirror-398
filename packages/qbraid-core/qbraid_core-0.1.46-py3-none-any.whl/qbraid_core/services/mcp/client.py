# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
WebSocket client for connecting to qBraid MCP servers.

"""
import asyncio
import json
import logging
from typing import Any, Callable, Optional

try:
    import websockets  # type: ignore[import-not-found]
    from websockets.exceptions import (  # type: ignore[import-not-found]
        ConnectionClosed,
        WebSocketException,
    )

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None  # type: ignore[assignment]
    ConnectionClosed = Exception  # type: ignore[misc,assignment]
    WebSocketException = Exception  # type: ignore[misc,assignment]
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPWebSocketClient:  # pylint: disable=too-many-instance-attributes
    """
    WebSocket client for qBraid MCP servers.

    Handles connection, reconnection, heartbeat, and message routing
    for a single MCP backend server.

    Architecture:
        stdio ↔ MCPRouter ↔ THIS CLIENT ↔ WebSocket ↔ qBraid MCP Server

    Based on the Node.js bridge pattern from ~/.qbraid-mcp/bridges/websocket_bridge.js
    """

    RECONNECT_DELAY = 1.0  # seconds
    HEARTBEAT_INTERVAL = 30.0  # seconds
    CONNECTION_TIMEOUT = 10.0  # seconds

    def __init__(
        self,
        websocket_url: str,
        on_message: Optional[Callable[[dict[str, Any]], None]] = None,
        name: str = "unnamed",
    ):
        """
        Initialize MCP WebSocket client.

        Args:
            websocket_url: Full WebSocket URL (wss://lab.qbraid.com/user/{user}/mcp/mcp?token=xxx)
            on_message: Callback function for received messages
            name: Human-readable name for this backend (e.g., "lab", "devices")
        """
        self.websocket_url = websocket_url
        self.on_message = on_message
        self.name = name

        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._is_connected = False
        self._is_shutting_down = False
        self._message_queue: list[str] = []
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

    @property
    def is_connected(self) -> bool:
        """Return whether the WebSocket is currently connected."""
        return self._is_connected and self._ws is not None

    async def connect(self) -> None:
        """
        Establish WebSocket connection to the MCP server.

        Handles reconnection logic and queued messages.
        """
        if self._is_shutting_down:
            return

        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "MCP WebSocket client requires the 'websockets' package. "
                "Install it with: pip install qbraid-core[mcp]"
            )

        try:
            logger.info("[%s] Connecting to %s", self.name, self.websocket_url)

            # Connect with timeout
            self._ws = await asyncio.wait_for(
                websockets.connect(
                    self.websocket_url,
                    ping_interval=None,  # We'll handle heartbeat manually
                    ping_timeout=None,
                    close_timeout=5,
                ),
                timeout=self.CONNECTION_TIMEOUT,
            )

            self._is_connected = True
            logger.info("[%s] Connected to MCP server", self.name)

            # Send queued messages
            while self._message_queue:
                queued_message = self._message_queue.pop(0)
                logger.debug("[%s] Sending queued message", self.name)
                assert self._ws is not None
                await self._ws.send(queued_message)

            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Start receive loop as background task (non-blocking)
            self._receive_task = asyncio.create_task(self._receive_loop())

        except asyncio.TimeoutError:
            logger.error("[%s] Connection timeout", self.name)
            await self._schedule_reconnect()
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("[%s] Connection error: %s", self.name, err)
            await self._schedule_reconnect()

    async def _receive_loop(self) -> None:
        """
        Receive and process messages from the WebSocket.

        This loop continues until the connection is closed or an error occurs.
        """
        try:
            assert self._ws is not None
            async for message in self._ws:
                try:
                    logger.info("[%s] Received message from WebSocket", self.name)

                    # Parse JSON message
                    data = json.loads(message) if isinstance(message, str) else message
                    logger.info("[%s] Parsed message: %s", self.name, str(data)[:100])

                    # Call message handler if provided
                    if self.on_message:
                        logger.info("[%s] Calling on_message callback", self.name)
                        self.on_message(data)
                        logger.info("[%s] on_message callback completed", self.name)
                    else:
                        logger.warning("[%s] No on_message callback registered!", self.name)

                except json.JSONDecodeError as err:
                    logger.error("[%s] Invalid JSON message: %s", self.name, err)
                except Exception as err:  # pylint: disable=broad-exception-caught
                    logger.error("[%s] Error processing message: %s", self.name, err, exc_info=True)

        except ConnectionClosed as err:  # pylint: disable=broad-exception-caught
            logger.warning("[%s] WebSocket connection closed: %s", self.name, err)
        except WebSocketException as err:  # pylint: disable=broad-exception-caught,duplicate-except
            logger.error("[%s] WebSocket error: %s", self.name, err)
        except Exception as err:  # pylint: disable=broad-exception-caught,duplicate-except
            logger.error("[%s] Unexpected error in receive loop: %s", self.name, err)
        finally:
            self._is_connected = False
            await self._cleanup_connection()

            if not self._is_shutting_down:
                await self._schedule_reconnect()

    async def _heartbeat_loop(self) -> None:
        """
        Send periodic ping frames to keep the connection alive.
        """
        try:
            while self.is_connected and not self._is_shutting_down:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

                if self._ws and self.is_connected:
                    try:
                        pong = await self._ws.ping()
                        await asyncio.wait_for(pong, timeout=5.0)
                        logger.debug("[%s] Heartbeat pong received", self.name)
                    except asyncio.TimeoutError:
                        logger.warning("[%s] Heartbeat timeout", self.name)
                        break
                    except Exception as err:  # pylint: disable=broad-exception-caught
                        logger.error("[%s] Heartbeat error: %s", self.name, err)
                        break
        except asyncio.CancelledError:
            logger.debug("[%s] Heartbeat task cancelled", self.name)
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("[%s] Error in heartbeat loop: %s", self.name, err)

    async def send(self, message: dict[str, Any]) -> None:
        """
        Send a message to the MCP server.

        Args:
            message: Dictionary to send as JSON

        Raises:
            ConnectionError: If not connected and message cannot be queued
        """
        message_str = json.dumps(message)

        if self.is_connected and self._ws:
            try:
                logger.debug("[%s] Sending message", self.name)
                await self._ws.send(message_str)
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.error("[%s] Error sending message: %s", self.name, err)
                # Queue the message and attempt reconnection
                self._message_queue.append(message_str)
                error_msg = f"Failed to send message to {self.name}"  # noqa: G004
                raise ConnectionError(error_msg) from err
        else:
            logger.warning("[%s] Not connected, message queued", self.name)
            self._message_queue.append(message_str)

    async def _schedule_reconnect(self) -> None:
        """
        Schedule a reconnection attempt after a delay.
        """
        if self._is_shutting_down or self._reconnect_task:
            return

        logger.info("[%s] Reconnecting in %ss...", self.name, self.RECONNECT_DELAY)

        async def _reconnect():
            await asyncio.sleep(self.RECONNECT_DELAY)
            self._reconnect_task = None
            await self.connect()

        self._reconnect_task = asyncio.create_task(_reconnect())

    async def _cleanup_connection(self) -> None:
        """
        Clean up connection resources.
        """
        # Cancel receive task
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        # Cancel heartbeat
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None

        # Close WebSocket
        if self._ws:
            try:
                await self._ws.close()
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.debug("[%s] Error closing WebSocket: %s", self.name, err)
            self._ws = None

        self._is_connected = False

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the WebSocket client.
        """
        if self._is_shutting_down:
            return

        logger.info("[%s] Shutting down...", self.name)
        self._is_shutting_down = True

        # Cancel reconnect task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        # Cleanup connection
        await self._cleanup_connection()

        logger.info("[%s] Shutdown complete", self.name)
