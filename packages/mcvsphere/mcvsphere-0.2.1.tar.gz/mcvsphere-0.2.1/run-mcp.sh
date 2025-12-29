#!/bin/bash
# ESXi MCP Server wrapper for Claude Code
cd "$(dirname "$0")"
exec uv run esxi-mcp-server "$@"
