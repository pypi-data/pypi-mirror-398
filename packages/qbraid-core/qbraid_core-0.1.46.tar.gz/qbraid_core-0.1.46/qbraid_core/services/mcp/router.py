# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
MCP message router for aggregating multiple backend servers.

"""
import asyncio
import logging
from typing import Any, Callable, Optional

from .client import MCPWebSocketClient

logger = logging.getLogger(__name__)


class MCPRouter:
    """
    Router for aggregating multiple qBraid MCP backend servers.

    Routes tool calls to appropriate backends based on tool name prefixes.

    Architecture:
        Claude Desktop ↔ stdio ↔ THIS ROUTER ↔ Multiple MCPWebSocketClients ↔ MCP Servers

    Tool Naming Convention:
        qbraid_lab_environment_install    → routes to "lab" backend
        qbraid_lab_job_submit             → routes to "lab" backend
        qbraid_devices_list               → routes to "devices" backend (future)
        qbraid_jobs_submit                → routes to "jobs" backend (future)

    The second component of the tool name (after "qbraid_") determines the routing.
    """

    def __init__(self, on_message: Optional[Callable[[dict[str, Any]], None]] = None):
        """
        Initialize MCP router.

        Args:
            on_message: Callback function for messages from any backend
        """
        self.on_message = on_message
        self._backends: dict[str, MCPWebSocketClient] = {}
        self._is_shutting_down = False

    def add_backend(self, name: str, client: MCPWebSocketClient) -> None:
        """
        Add a backend MCP client to the router.

        Args:
            name: Backend name (e.g., "lab", "devices", "jobs")
            client: MCPWebSocketClient instance for this backend
        """
        self._backends[name] = client
        logger.info("Added backend: %s", name)

    async def connect_all(self) -> None:
        """
        Connect to all registered backend servers in parallel.
        """
        if not self._backends:
            logger.warning("No backends registered")
            return

        logger.info("Connecting to %s backend(s)...", len(self._backends))

        # Create connection tasks for all backends
        connection_tasks = [
            asyncio.create_task(client.connect()) for client in self._backends.values()
        ]

        # Wait for all connections (doesn't fail if some fail - they'll retry)
        await asyncio.gather(*connection_tasks, return_exceptions=True)

        # Log connection status
        connected_count = sum(1 for client in self._backends.values() if client.is_connected)
        logger.info("Connected to %s/%s backend(s)", connected_count, len(self._backends))

    def route_tool_call(self, tool_name: str) -> Optional[str]:
        """
        Determine which backend should handle this tool call.

        Args:
            tool_name: Full tool name (e.g., "qbraid_lab_environment_install" or "ping")

        Returns:
            Backend name if found, None otherwise

        Example:
            >>> router.route_tool_call("qbraid_lab_environment_install")
            'lab'
            >>> router.route_tool_call("qbraid_devices_list")
            'devices'
            >>> router.route_tool_call("ping")  # Falls back to first backend
            'lab'
        """
        parts = tool_name.split("_")

        # Tool names should follow pattern: qbraid_{backend}_{tool}_{details}
        if len(parts) >= 3 and parts[0] == "qbraid":
            backend_name = parts[1]  # Extract backend from second component

            if backend_name not in self._backends:
                logger.warning(
                    "Unknown backend '%s' for tool '%s'. Available backends: %s",
                    backend_name,
                    tool_name,
                    list(self._backends.keys()),
                )
                return None

            return backend_name

        # Tool doesn't follow qbraid_{backend}_ pattern
        # Route to first available backend (for single-backend deployments)
        if len(self._backends) == 1:
            backend_name = list(self._backends.keys())[0]
            logger.info(
                "Tool '%s' doesn't follow naming convention, routing to only backend '%s'",
                tool_name,
                backend_name,
            )
            return backend_name

        logger.warning(
            "Tool '%s' doesn't follow qbraid_{backend}_ naming convention "
            "and multiple backends available. Cannot route. Available backends: %s",
            tool_name,
            list(self._backends.keys()),
        )
        return None

    async def send_to_backend(self, backend_name: str, message: dict[str, Any]) -> None:
        """
        Send a message to a specific backend.

        Args:
            backend_name: Name of the backend to send to
            message: Message dictionary to send

        Raises:
            ValueError: If backend not found
            ConnectionError: If backend not connected and message cannot be queued
        """
        backend = self._backends.get(backend_name)
        if not backend:
            raise ValueError(f"Backend '{backend_name}' not found")  # noqa: G004

        await backend.send(message)

    async def handle_message(self, message: dict[str, Any]) -> None:
        """
        Handle incoming message from Claude Desktop and route to appropriate backend.

        Args:
            message: Message dictionary from Claude Desktop

        The message should contain a "method" field (e.g., "tools/call")
        and potentially a "params" field with tool name and arguments.
        """
        try:
            logger.info("Router received message: %s", str(message)[:100])

            # Extract tool name from message if it's a tool call
            method = message.get("method")
            params = message.get("params", {})

            if method == "tools/call":
                tool_name = params.get("name")
                if tool_name:
                    # Route based on tool name
                    backend_name = self.route_tool_call(tool_name)
                    if backend_name:
                        logger.info("Routing '%s' to backend '%s'", tool_name, backend_name)
                        await self.send_to_backend(backend_name, message)
                    else:
                        logger.error("Cannot route tool call: %s", tool_name)
                else:
                    logger.error("Tool call message missing 'name' parameter")
            else:
                # For non-tool-call messages, send to all backends
                # (e.g., initialization, list_tools, etc.)
                logger.info(
                    "Broadcasting message with method '%s' to %s backend(s)",
                    method,
                    len(self._backends),
                )
                for backend_name in self._backends:
                    try:
                        logger.info("  Sending to backend '%s'", backend_name)
                        await self.send_to_backend(backend_name, message)
                        logger.info("  Sent to backend '%s'", backend_name)
                    except Exception as err:  # pylint: disable=broad-exception-caught
                        logger.error(
                            "Error sending to backend '%s': %s", backend_name, err, exc_info=True
                        )

        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("Error handling message: %s", err, exc_info=True)

    async def shutdown_all(self) -> None:
        """
        Gracefully shutdown all backend connections.
        """
        if self._is_shutting_down:
            return

        logger.info("Shutting down all backends...")
        self._is_shutting_down = True

        # Create shutdown tasks for all backends
        shutdown_tasks = [
            asyncio.create_task(client.shutdown()) for client in self._backends.values()
        ]

        # Wait for all shutdowns
        await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        logger.info("All backends shut down")

    def get_connected_backends(self) -> list[str]:
        """
        Get list of currently connected backend names.

        Returns:
            List of backend names that are connected
        """
        return [name for name, client in self._backends.items() if client.is_connected]

    def get_backend_status(self) -> dict[str, bool]:
        """
        Get connection status for all backends.

        Returns:
            Dictionary mapping backend names to connection status

        Example:
            >>> router.get_backend_status()
            {'lab': True, 'devices': False, 'jobs': True}
        """
        return {name: client.is_connected for name, client in self._backends.items()}
