# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Auto-discovery of available qBraid MCP servers.

"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPServerEndpoint:
    """
    Configuration for an MCP server endpoint.

    Attributes:
        name: Human-readable name (e.g., "lab", "devices", "jobs")
        base_url: Base URL for the server (e.g., "https://lab.qbraid.com")
        path_template: URL path template with placeholders
            (e.g., "/user/{username}/mcp/mcp")
        requires_token: Whether this endpoint requires authentication token
        description: Human-readable description
    """

    name: str
    base_url: str
    path_template: str
    requires_token: bool = True
    description: Optional[str] = None

    def build_url(self, username: str, token: Optional[str] = None) -> str:
        """
        Build the full WebSocket URL for this endpoint.

        Args:
            username: qBraid username (email)
            token: API or session token (if requires_token=True)

        Returns:
            Full WebSocket URL with protocol, path, and query params

        Example:
            >>> endpoint = MCPServerEndpoint(
            ...     name="lab",
            ...     base_url="https://lab.qbraid.com",
            ...     path_template="/user/{username}/mcp/mcp"
            ... )
            >>> endpoint.build_url("user@example.com", "abc123")
            'wss://lab.qbraid.com/user/user@example.com/mcp/mcp?token=abc123'
        """
        # Convert https:// to wss:// and http:// to ws://
        if self.base_url.startswith("https://"):
            ws_base = "wss://" + self.base_url[8:]
        elif self.base_url.startswith("http://"):
            ws_base = "ws://" + self.base_url[7:]
        else:
            ws_base = self.base_url

        # Format path with username
        path = self.path_template.format(username=username)

        # Build full URL
        full_url = ws_base.rstrip("/") + "/" + path.lstrip("/")

        # Add token query parameter if required
        if self.requires_token and token:
            full_url += f"?token={token}"

        return full_url


# Known qBraid MCP server endpoints
KNOWN_MCP_ENDPOINTS: list[MCPServerEndpoint] = [
    MCPServerEndpoint(
        name="lab",
        base_url="https://lab.qbraid.com",
        path_template="/user/{username}/mcp/mcp",
        description="qBraid Lab MCP server (pod_mcp) - manage environments, jobs, files",
    ),
    MCPServerEndpoint(
        name="lab-staging",
        base_url="https://lab-staging.qbraid.com",
        path_template="/user/{username}/mcp/mcp",
        description="qBraid Lab Staging MCP server (for testing)",
    ),
    # Future endpoints (not yet deployed):
    # MCPServerEndpoint(
    #     name="devices",
    #     base_url="https://api.qbraid.com",
    #     path_template="/mcp/devices",
    #     description="Quantum device catalog and management"
    # ),
    # MCPServerEndpoint(
    #     name="jobs",
    #     base_url="https://api.qbraid.com",
    #     path_template="/mcp/jobs",
    #     description="Quantum job submission and monitoring"
    # ),
]


def discover_mcp_servers(
    workspace: str = "lab",
    include_staging: bool = False,
) -> list[MCPServerEndpoint]:
    """
    Discover available qBraid MCP servers based on workspace.

    Args:
        workspace: Workspace name ("lab", "qbook", etc.)
        include_staging: Whether to use staging endpoints (replaces production)

    Returns:
        List of available MCP server endpoints

    Example:
        >>> endpoints = discover_mcp_servers(workspace="lab")
        >>> for endpoint in endpoints:
        ...     print(f"{endpoint.name}: {endpoint.description}")
        lab: qBraid Lab MCP server (pod_mcp) - manage environments, jobs, files

        >>> endpoints = discover_mcp_servers(workspace="lab", include_staging=True)
        >>> for endpoint in endpoints:
        ...     print(f"{endpoint.name}: {endpoint.description}")
        lab-staging: qBraid Lab Staging MCP server (for testing)
    """
    available = []

    for endpoint in KNOWN_MCP_ENDPOINTS:
        # Filter by workspace
        if workspace and not endpoint.name.startswith(workspace):
            continue

        # If include_staging=True, ONLY return staging endpoints
        # If include_staging=False, ONLY return production endpoints
        is_staging = "staging" in endpoint.name
        if is_staging != include_staging:
            continue

        available.append(endpoint)
        logger.debug("Discovered MCP endpoint: %s (%s)", endpoint.name, endpoint.base_url)

    if not available:
        logger.warning("No MCP endpoints found for workspace '%s'", workspace)

    return available


def get_mcp_endpoint(name: str) -> Optional[MCPServerEndpoint]:
    """
    Get a specific MCP endpoint by name.

    Args:
        name: Endpoint name (e.g., "lab", "lab-staging", "devices")

    Returns:
        MCPServerEndpoint if found, None otherwise

    Example:
        >>> endpoint = get_mcp_endpoint("lab")
        >>> print(endpoint.base_url)
        https://lab.qbraid.com
    """
    for endpoint in KNOWN_MCP_ENDPOINTS:
        if endpoint.name == name:
            return endpoint

    logger.warning("MCP endpoint '%s' not found", name)
    return None
