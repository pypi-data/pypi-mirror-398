"""ESXi MCP Server - VMware vSphere management via Model Context Protocol.

This package provides an MCP server for managing VMware ESXi/vCenter
virtual machines through AI assistants like Claude.
"""

import argparse
from pathlib import Path

from mcvsphere.config import Settings, get_settings
from mcvsphere.connection import VMwareConnection
from mcvsphere.server import create_server, run_server

__all__ = [
    "Settings",
    "get_settings",
    "VMwareConnection",
    "create_server",
    "run_server",
    "main",
]


def main() -> None:
    """Entry point for the mcvsphere CLI."""
    parser = argparse.ArgumentParser(
        description="ESXi MCP Server - VMware vSphere management via MCP"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        help="Path to configuration file (YAML or JSON)",
        default=None,
    )
    parser.add_argument(
        "--transport",
        "-t",
        choices=["stdio", "sse"],
        help="MCP transport type (default: stdio)",
        default=None,
    )
    parser.add_argument(
        "--host",
        help="Host to bind SSE server (default: 0.0.0.0)",
        default=None,
    )
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        help="Port for SSE server (default: 8080)",
        default=None,
    )

    args = parser.parse_args()

    # Load base settings
    settings = Settings.from_yaml(args.config) if args.config else get_settings()

    # Override with CLI args
    if args.transport:
        settings = settings.model_copy(update={"mcp_transport": args.transport})
    if args.host:
        settings = settings.model_copy(update={"mcp_host": args.host})
    if args.port:
        settings = settings.model_copy(update={"mcp_port": args.port})

    run_server(args.config)


if __name__ == "__main__":
    main()
