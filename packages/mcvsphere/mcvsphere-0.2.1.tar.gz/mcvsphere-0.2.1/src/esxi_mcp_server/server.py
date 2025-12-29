"""FastMCP server setup for ESXi MCP Server."""

import logging
import sys
from pathlib import Path

from fastmcp import FastMCP

from esxi_mcp_server.config import Settings, get_settings
from esxi_mcp_server.connection import VMwareConnection
from esxi_mcp_server.mixins import (
    ConsoleMixin,
    DiskManagementMixin,
    GuestOpsMixin,
    HostManagementMixin,
    MonitoringMixin,
    NICManagementMixin,
    OVFManagementMixin,
    PowerOpsMixin,
    ResourcesMixin,
    SerialPortMixin,
    SnapshotsMixin,
    VCenterOpsMixin,
    VMLifecycleMixin,
)

logger = logging.getLogger(__name__)


def create_server(settings: Settings | None = None) -> FastMCP:
    """Create and configure the FastMCP server.

    Args:
        settings: Optional settings instance. If not provided, will load from
                  environment variables and/or config file.

    Returns:
        Configured FastMCP server instance with VMware tools registered.
    """
    if settings is None:
        settings = get_settings()

    # Configure logging - MUST go to stderr for stdio transport compatibility
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # For stdio mode, suppress most logging to avoid interference
    if settings.mcp_transport == "stdio":
        log_level = logging.WARNING

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,  # Explicitly use stderr
    )

    # Create FastMCP server
    mcp = FastMCP(
        name="ESXi MCP Server",
        instructions=(
            "VMware ESXi/vCenter management server via Model Context Protocol. "
            "Provides tools for VM lifecycle management, power operations, "
            "snapshots, guest OS operations, monitoring, and infrastructure resources."
        ),
    )

    # Create shared VMware connection
    logger.info("Connecting to VMware vCenter/ESXi...")
    conn = VMwareConnection(settings)

    # Create and register all mixins
    mixins = [
        VMLifecycleMixin(conn),
        PowerOpsMixin(conn),
        SnapshotsMixin(conn),
        MonitoringMixin(conn),
        GuestOpsMixin(conn),
        ResourcesMixin(conn),
        DiskManagementMixin(conn),
        NICManagementMixin(conn),
        OVFManagementMixin(conn),
        HostManagementMixin(conn),
        VCenterOpsMixin(conn),
        ConsoleMixin(conn),
        SerialPortMixin(conn),
    ]

    tool_count = 0
    resource_count = 0

    for mixin in mixins:
        mixin.register_all(mcp)
        tool_count += len(getattr(mixin, "_mcp_tools", []))
        resource_count += len(getattr(mixin, "_mcp_resources", []))

    # Get actual counts from MCP server
    actual_tools = len(mcp._tool_manager._tools)
    actual_resources = len(mcp._resource_manager._resources)

    logger.info(
        "ESXi MCP Server ready - %d tools, %d resources registered",
        actual_tools,
        actual_resources,
    )

    return mcp


def run_server(config_path: Path | None = None) -> None:
    """Run the ESXi MCP server.

    Args:
        config_path: Optional path to YAML/JSON config file.
    """
    # Load settings
    settings = Settings.from_yaml(config_path) if config_path else get_settings()

    # Only print banner for SSE mode (stdio must stay clean for JSON-RPC)
    if settings.mcp_transport == "sse":
        try:
            from importlib.metadata import version

            package_version = version("esxi-mcp-server")
        except Exception:
            package_version = "dev"

        print(f"ESXi MCP Server v{package_version}", file=sys.stderr)
        print("─" * 40, file=sys.stderr)
        print(
            f"Starting SSE transport on {settings.mcp_host}:{settings.mcp_port}",
            file=sys.stderr,
        )

    # Create and run server
    mcp = create_server(settings)

    if settings.mcp_transport == "sse":
        mcp.run(transport="sse", host=settings.mcp_host, port=settings.mcp_port)
    else:
        # stdio mode - suppress banner to keep stdout clean for JSON-RPC
        mcp.run(show_banner=False)
