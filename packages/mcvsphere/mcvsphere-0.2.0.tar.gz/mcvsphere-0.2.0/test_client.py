#!/usr/bin/env python3
"""Comprehensive MCP client to test all read-only ESXi MCP server tools."""

import asyncio
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def load_env_file(path: str = ".env") -> dict[str, str]:
    """Load environment variables from a .env file."""
    env = {}
    env_path = Path(path)
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()
    return env


def print_result(data, indent=2, max_items=5):
    """Pretty print result data with truncation."""
    if isinstance(data, list):
        # Check for empty-result message
        if data and isinstance(data[0], dict) and "message" in data[0] and "count" in data[0]:
            print(f"  {data[0]['message']}")
            return
        print(f"  Found {len(data)} items:")
        for item in data[:max_items]:
            if isinstance(item, dict):
                summary = ", ".join(f"{k}={v}" for k, v in list(item.items())[:4])
                print(f"    - {summary[:100]}...")
            else:
                print(f"    - {item}")
        if len(data) > max_items:
            print(f"    ... and {len(data) - max_items} more")
    elif isinstance(data, dict):
        for k, v in list(data.items())[:8]:
            val_str = str(v)[:60] + "..." if len(str(v)) > 60 else str(v)
            print(f"    {k}: {val_str}")
    else:
        print(f"  {data}")


async def test_tool(session, name: str, args: dict = None, description: str = ""):
    """Test a single tool and print results."""
    args = args or {}
    print(f"\n{'─' * 60}")
    print(f"Testing: {name} {description}")
    print(f"{'─' * 60}")
    try:
        result = await session.call_tool(name, args)
        if result.content:
            data = json.loads(result.content[0].text)
            print_result(data)
            return data
        else:
            print("  No content returned")
            return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


async def test_resource(session, uri: str):
    """Test reading an MCP resource."""
    print(f"\n{'─' * 60}")
    print(f"Resource: {uri}")
    print(f"{'─' * 60}")
    try:
        result = await session.read_resource(uri)
        if result.contents:
            data = json.loads(result.contents[0].text)
            print_result(data)
            return data
        else:
            print("  No content returned")
            return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


async def main():
    """Test all read-only ESXi MCP server tools."""
    print("=" * 60)
    print("ESXi MCP Server - Comprehensive Read-Only Test Suite")
    print("=" * 60)

    # Load from .env file
    dotenv = load_env_file()

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcvsphere"],
        env={
            **os.environ,
            "VCENTER_HOST": dotenv.get("VCENTER_HOST", os.environ.get("VCENTER_HOST", "")),
            "VCENTER_USER": dotenv.get("VCENTER_USER", os.environ.get("VCENTER_USER", "")),
            "VCENTER_PASSWORD": dotenv.get("VCENTER_PASSWORD", os.environ.get("VCENTER_PASSWORD", "")),
            "VCENTER_INSECURE": dotenv.get("VCENTER_INSECURE", os.environ.get("VCENTER_INSECURE", "true")),
            "MCP_TRANSPORT": "stdio",
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("\n✓ Connected to ESXi MCP Server\n")

            # ─────────────────────────────────────────────────────────────
            # List available tools and resources
            # ─────────────────────────────────────────────────────────────
            tools_result = await session.list_tools()
            resources_result = await session.list_resources()
            print(f"Available: {len(tools_result.tools)} tools, {len(resources_result.resources)} resources")

            # ─────────────────────────────────────────────────────────────
            # Test MCP Resources
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 1: MCP Resources")
            print("=" * 60)

            vms = await test_resource(session, "esxi://vms")
            await test_resource(session, "esxi://hosts")
            await test_resource(session, "esxi://datastores")
            await test_resource(session, "esxi://networks")
            await test_resource(session, "esxi://clusters")

            # Get a VM name for subsequent tests
            vm_name = vms[0]["name"] if vms else None
            print(f"\n>>> Using VM '{vm_name}' for subsequent tests")

            # ─────────────────────────────────────────────────────────────
            # VM Lifecycle (read-only)
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 2: VM Lifecycle Tools")
            print("=" * 60)

            await test_tool(session, "list_vms")
            if vm_name:
                await test_tool(session, "get_vm_info", {"name": vm_name})

            # ─────────────────────────────────────────────────────────────
            # Monitoring Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 3: Monitoring Tools")
            print("=" * 60)

            await test_tool(session, "list_hosts")
            await test_tool(session, "get_host_stats")
            if vm_name:
                await test_tool(session, "get_vm_stats", {"name": vm_name})
            await test_tool(session, "get_alarms")
            await test_tool(session, "get_recent_events", {"count": 5})
            await test_tool(session, "get_recent_tasks", {"count": 5})

            # ─────────────────────────────────────────────────────────────
            # Host Management Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 4: Host Management Tools")
            print("=" * 60)

            await test_tool(session, "get_host_info")
            await test_tool(session, "get_host_hardware")
            await test_tool(session, "get_host_networking")
            await test_tool(session, "list_services")
            await test_tool(session, "get_ntp_config")

            # ─────────────────────────────────────────────────────────────
            # Datastore/Resources Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 5: Datastore & Resource Tools")
            print("=" * 60)

            # Get datastore name from resources
            ds_result = await session.read_resource("esxi://datastores")
            datastores = json.loads(ds_result.contents[0].text) if ds_result.contents else []
            ds_name = datastores[0]["name"] if datastores else None
            print(f"\n>>> Using datastore '{ds_name}' for tests")

            if ds_name:
                await test_tool(session, "get_datastore_info", {"name": ds_name})
                await test_tool(session, "browse_datastore", {"datastore": ds_name, "path": ""})

            await test_tool(session, "get_vcenter_info")
            await test_tool(session, "get_resource_pool_info")

            # Get network name
            net_result = await session.read_resource("esxi://networks")
            networks = json.loads(net_result.contents[0].text) if net_result.contents else []
            net_name = networks[0]["name"] if networks else None
            if net_name:
                await test_tool(session, "get_network_info", {"name": net_name})

            await test_tool(session, "list_templates")

            # ─────────────────────────────────────────────────────────────
            # Disk Management Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 6: Disk Management Tools")
            print("=" * 60)

            if vm_name:
                await test_tool(session, "list_disks", {"vm_name": vm_name})

            # ─────────────────────────────────────────────────────────────
            # NIC Management Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 7: NIC Management Tools")
            print("=" * 60)

            if vm_name:
                await test_tool(session, "list_nics", {"vm_name": vm_name})

            # ─────────────────────────────────────────────────────────────
            # Snapshot Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 8: Snapshot Tools")
            print("=" * 60)

            if vm_name:
                await test_tool(session, "list_snapshots", {"name": vm_name})

            # ─────────────────────────────────────────────────────────────
            # OVF Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 9: OVF Tools")
            print("=" * 60)

            await test_tool(session, "list_ovf_networks")

            # ─────────────────────────────────────────────────────────────
            # vCenter-Specific Tools
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 10: vCenter-Specific Tools")
            print("=" * 60)

            await test_tool(session, "list_folders")
            await test_tool(session, "list_clusters")
            await test_tool(session, "list_recent_tasks", {"max_count": 5})
            await test_tool(session, "list_recent_events", {"max_count": 5, "hours_back": 24})

            # ─────────────────────────────────────────────────────────────
            # Guest Operations (require VMware Tools + credentials)
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("SECTION 11: Guest Operations (may fail without VMware Tools)")
            print("=" * 60)

            # These typically need a running VM with VMware Tools
            # and guest credentials - expect failures on most VMs
            if vm_name:
                await test_tool(
                    session, "list_guest_processes",
                    {"name": vm_name, "username": "root", "password": "test"},
                    "(expected to fail without valid credentials)"
                )

            # ─────────────────────────────────────────────────────────────
            # Summary
            # ─────────────────────────────────────────────────────────────
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            print(f"✅ Read-only test suite completed")
            print(f"   Tools available: {len(tools_result.tools)}")
            print(f"   Resources available: {len(resources_result.resources)}")
            print(f"\nNote: Guest operations require VMware Tools + valid credentials")
            print("Note: Some vCenter tools return empty on standalone hosts")


if __name__ == "__main__":
    asyncio.run(main())
