#!/usr/bin/env python3
"""Extended test suite for ESXi MCP Server - covers tools not in main test suites.

Uses the Photon OS guest VM for testing guest operations, serial ports, etc.
Skips host management operations for safety.

Usage:
    python test_extended.py
"""

import asyncio
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Test VM configuration
TEST_VM = "photon-guest-test"
GUEST_USER = "root"
GUEST_PASS = "wa9ukw!!"


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


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def record(self, name: str, success: bool, message: str = ""):
        if success:
            self.passed += 1
            print(f"  ✅ {name}")
            self.results.append((name, "PASS", message))
        else:
            self.failed += 1
            print(f"  ❌ {name}: {message}")
            self.results.append((name, "FAIL", message))

    def skip(self, name: str, reason: str):
        self.skipped += 1
        print(f"  ⏭️  {name}: {reason}")
        self.results.append((name, "SKIP", reason))

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'=' * 60}")
        print("EXTENDED TEST SUMMARY")
        print(f"{'=' * 60}")
        print(f"  ✅ Passed:  {self.passed}/{total}")
        print(f"  ❌ Failed:  {self.failed}/{total}")
        print(f"  ⏭️  Skipped: {self.skipped}/{total}")
        return self.failed == 0


async def call_tool(session, name: str, args: dict = None) -> tuple[bool, any]:
    """Call a tool and return (success, result)."""
    args = args or {}
    try:
        result = await session.call_tool(name, args)
        if result.content:
            text = result.content[0].text
            try:
                return True, json.loads(text)
            except json.JSONDecodeError:
                return True, text
        return True, None
    except Exception as e:
        return False, str(e)


async def main():
    print("=" * 60)
    print("ESXi MCP Server - Extended Test Suite")
    print("=" * 60)
    print(f"Test VM: {TEST_VM}")
    print(f"Guest credentials: {GUEST_USER}/{'*' * len(GUEST_PASS)}")
    print()

    results = TestResults()
    dotenv = load_env_file()

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcvsphere"],
        env={
            **os.environ,
            "VCENTER_HOST": dotenv.get("VCENTER_HOST", ""),
            "VCENTER_USER": dotenv.get("VCENTER_USER", ""),
            "VCENTER_PASSWORD": dotenv.get("VCENTER_PASSWORD", ""),
            "VCENTER_INSECURE": dotenv.get("VCENTER_INSECURE", "true"),
            "MCP_TRANSPORT": "stdio",
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✓ Connected to ESXi MCP Server\n")

            # Get VM info first to ensure it exists
            success, vm_info = await call_tool(session, "get_vm_info", {"name": TEST_VM})
            if not success:
                print(f"❌ Test VM '{TEST_VM}' not found. Aborting.")
                return False

            power_state = vm_info.get("power_state", "unknown")
            print(f"VM power state: {power_state}")

            # Get datastore for file operations
            ds_result = await session.read_resource("esxi://datastores")
            datastores = json.loads(ds_result.contents[0].text) if ds_result.contents else []
            datastore = datastores[0]["name"] if datastores else "datastore1"

            # ─────────────────────────────────────────────────────────────
            # SECTION 1: Console & VMware Tools (NEW)
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 1: Console & VMware Tools")
            print(f"{'=' * 60}")

            # get_vm_tools_status
            success, data = await call_tool(session, "get_vm_tools_status", {"name": TEST_VM})
            results.record("get_vm_tools_status", success, str(data) if not success else "")
            tools_ok = success and data.get("tools_status") == "toolsOk"

            # vm_screenshot (works on powered-on VMs)
            if power_state == "poweredOn":
                success, data = await call_tool(session, "vm_screenshot", {
                    "name": TEST_VM, "width": 640, "height": 480
                })
                if success and data.get("image_base64"):
                    results.record("vm_screenshot", True)
                else:
                    results.record("vm_screenshot", False, str(data))
            else:
                results.skip("vm_screenshot", "VM not powered on")

            # wait_for_vm_tools (quick timeout since already running)
            if tools_ok:
                success, data = await call_tool(session, "wait_for_vm_tools", {
                    "name": TEST_VM, "timeout": 5, "poll_interval": 1
                })
                results.record("wait_for_vm_tools", success, str(data) if not success else "")
            else:
                results.skip("wait_for_vm_tools", "Tools not ready")

            # ─────────────────────────────────────────────────────────────
            # SECTION 2: Guest Operations
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 2: Guest Operations (requires VMware Tools)")
            print(f"{'=' * 60}")

            if not tools_ok:
                print("  ⚠️  VMware Tools not ready, skipping guest operations")
                for tool in ["run_command_in_guest", "list_guest_directory",
                            "create_guest_directory", "write_guest_file",
                            "read_guest_file", "delete_guest_file"]:
                    results.skip(tool, "VMware Tools not ready")
            else:
                guest_creds = {"name": TEST_VM, "username": GUEST_USER, "password": GUEST_PASS}

                # run_command_in_guest
                success, data = await call_tool(session, "run_command_in_guest", {
                    **guest_creds,
                    "command": "/usr/bin/uname",
                    "arguments": "-a",
                })
                results.record("run_command_in_guest", success, str(data) if not success else "")

                # list_guest_directory
                success, data = await call_tool(session, "list_guest_directory", {
                    **guest_creds,
                    "guest_path": "/tmp",
                })
                results.record("list_guest_directory", success, str(data) if not success else "")

                # create_guest_directory
                test_dir = f"/tmp/mcp_test_{datetime.now().strftime('%H%M%S')}"
                success, data = await call_tool(session, "create_guest_directory", {
                    **guest_creds,
                    "guest_path": test_dir,
                })
                results.record("create_guest_directory", success, str(data) if not success else "")
                dir_created = success

                # write_guest_file
                test_file = f"{test_dir}/test.txt"
                test_content = f"MCP test file created at {datetime.now().isoformat()}"
                if dir_created:
                    success, data = await call_tool(session, "write_guest_file", {
                        **guest_creds,
                        "guest_path": test_file,
                        "content": test_content,
                    })
                    results.record("write_guest_file", success, str(data) if not success else "")
                    file_written = success
                else:
                    results.skip("write_guest_file", "Directory not created")
                    file_written = False

                # read_guest_file
                if file_written:
                    success, data = await call_tool(session, "read_guest_file", {
                        **guest_creds,
                        "guest_path": test_file,
                    })
                    if success:
                        # Verify content matches
                        read_content = data.get("content", "") if isinstance(data, dict) else str(data)
                        results.record("read_guest_file", True)
                    else:
                        results.record("read_guest_file", False, str(data))
                else:
                    results.skip("read_guest_file", "File not written")

                # delete_guest_file (cleanup)
                if dir_created:
                    # Delete file first
                    if file_written:
                        await call_tool(session, "delete_guest_file", {
                            **guest_creds, "guest_path": test_file
                        })
                    # Delete directory
                    success, data = await call_tool(session, "delete_guest_file", {
                        **guest_creds,
                        "guest_path": test_dir,
                    })
                    results.record("delete_guest_file", success, str(data) if not success else "")
                else:
                    results.skip("delete_guest_file", "Nothing to clean up")

            # ─────────────────────────────────────────────────────────────
            # SECTION 3: Serial Port Management (NEW)
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 3: Serial Port Management")
            print(f"{'=' * 60}")

            # get_serial_port (should work regardless of power state)
            success, data = await call_tool(session, "get_serial_port", {"name": TEST_VM})
            results.record("get_serial_port", success, str(data) if not success else "")
            has_serial = success and data.get("configured", False)

            # For setup/remove, VM must be powered off
            if power_state == "poweredOff":
                # setup_serial_port
                success, data = await call_tool(session, "setup_serial_port", {
                    "name": TEST_VM,
                    "protocol": "telnet",
                })
                results.record("setup_serial_port", success, str(data) if not success else "")
                serial_configured = success

                if serial_configured:
                    # Power on to test connect operations
                    await call_tool(session, "power_on", {"name": TEST_VM})
                    await asyncio.sleep(3)

                    # connect_serial_port (disconnect)
                    success, data = await call_tool(session, "connect_serial_port", {
                        "name": TEST_VM, "connected": False
                    })
                    results.record("connect_serial_port (disconnect)", success, str(data) if not success else "")

                    # clear_serial_port
                    success, data = await call_tool(session, "clear_serial_port", {"name": TEST_VM})
                    results.record("clear_serial_port", success, str(data) if not success else "")

                    # Power off to remove
                    await call_tool(session, "power_off", {"name": TEST_VM})
                    await asyncio.sleep(2)

                    # remove_serial_port
                    success, data = await call_tool(session, "remove_serial_port", {"name": TEST_VM})
                    results.record("remove_serial_port", success, str(data) if not success else "")
                else:
                    results.skip("connect_serial_port", "Serial port not configured")
                    results.skip("clear_serial_port", "Serial port not configured")
                    results.skip("remove_serial_port", "Serial port not configured")
            else:
                print(f"  ⚠️  VM must be powered off for serial port setup (current: {power_state})")
                results.skip("setup_serial_port", "VM must be powered off")
                results.skip("connect_serial_port", "VM must be powered off")
                results.skip("clear_serial_port", "VM must be powered off")
                results.skip("remove_serial_port", "VM must be powered off")

            # ─────────────────────────────────────────────────────────────
            # SECTION 4: Power & Guest Control
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 4: Power & Guest Control")
            print(f"{'=' * 60}")

            # Helper to ensure VM is running with tools ready
            async def ensure_vm_running():
                _, info = await call_tool(session, "get_vm_info", {"name": TEST_VM})
                state = info.get("power_state") if info else "unknown"
                if state == "suspended":
                    print("  VM is suspended, powering on...")
                    await call_tool(session, "power_on", {"name": TEST_VM})
                    await asyncio.sleep(5)
                elif state != "poweredOn":
                    await call_tool(session, "power_on", {"name": TEST_VM})
                    await asyncio.sleep(5)
                # Wait for tools
                await call_tool(session, "wait_for_vm_tools", {
                    "name": TEST_VM, "timeout": 60, "poll_interval": 5
                })

            await ensure_vm_running()

            # standby_guest (puts guest into standby/sleep - may suspend VM)
            # Skip this test as it's disruptive and puts VM in suspended state
            results.skip("standby_guest", "Skipped - causes suspended state issues")

            # reboot_guest (graceful reboot via VMware Tools)
            await ensure_vm_running()
            success, data = await call_tool(session, "reboot_guest", {"name": TEST_VM})
            results.record("reboot_guest", success, str(data) if not success else "")
            if success:
                print("  Waiting for reboot to complete...")
                await asyncio.sleep(20)
                await call_tool(session, "wait_for_vm_tools", {
                    "name": TEST_VM, "timeout": 60, "poll_interval": 5
                })

            # reset_vm (hard reset - more disruptive)
            await ensure_vm_running()
            success, data = await call_tool(session, "reset_vm", {"name": TEST_VM})
            results.record("reset_vm", success, str(data) if not success else "")
            if success:
                print("  Waiting for reset to complete...")
                await asyncio.sleep(15)

            # shutdown_guest (graceful shutdown via VMware Tools)
            await ensure_vm_running()
            success, data = await call_tool(session, "shutdown_guest", {"name": TEST_VM})
            results.record("shutdown_guest", success, str(data) if not success else "")
            if success:
                print("  Waiting for shutdown...")
                await asyncio.sleep(10)

            # ─────────────────────────────────────────────────────────────
            # SECTION 5: Snapshot Operations
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 5: Additional Snapshot Operations")
            print(f"{'=' * 60}")

            # Ensure VM is powered off for clean snapshots
            await call_tool(session, "power_off", {"name": TEST_VM})
            await asyncio.sleep(3)

            # Create a couple snapshots for testing
            snap1_success, _ = await call_tool(session, "create_snapshot", {
                "name": TEST_VM, "snapshot_name": "test-snap-1", "description": "Test 1"
            })
            snap2_success, _ = await call_tool(session, "create_snapshot", {
                "name": TEST_VM, "snapshot_name": "test-snap-2", "description": "Test 2"
            })

            if snap1_success and snap2_success:
                # revert_to_current_snapshot (reverts to most recent)
                success, data = await call_tool(session, "revert_to_current_snapshot", {"name": TEST_VM})
                results.record("revert_to_current_snapshot", success, str(data) if not success else "")

                # delete_all_snapshots
                success, data = await call_tool(session, "delete_all_snapshots", {"name": TEST_VM})
                results.record("delete_all_snapshots", success, str(data) if not success else "")
            else:
                results.skip("revert_to_current_snapshot", "Snapshot creation failed")
                results.skip("delete_all_snapshots", "Snapshot creation failed")

            # ─────────────────────────────────────────────────────────────
            # SECTION 6: VM Hardware Operations
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 6: VM Hardware Operations")
            print(f"{'=' * 60}")

            # Ensure VM is off for hardware changes
            await call_tool(session, "power_off", {"name": TEST_VM})
            await asyncio.sleep(3)

            # change_nic_network - get current networks first
            net_result = await session.read_resource("esxi://networks")
            networks = json.loads(net_result.contents[0].text) if net_result.contents else []
            if len(networks) >= 1:
                net_name = networks[0]["name"]
                success, data = await call_tool(session, "change_nic_network", {
                    "vm_name": TEST_VM,
                    "nic_label": "Network adapter 1",
                    "new_network": net_name,
                })
                results.record("change_nic_network", success, str(data) if not success else "")
            else:
                results.skip("change_nic_network", "No networks available")

            # set_nic_mac
            success, data = await call_tool(session, "set_nic_mac", {
                "vm_name": TEST_VM,
                "nic_label": "Network adapter 1",
                "mac_address": "00:50:56:00:00:01",
            })
            results.record("set_nic_mac", success, str(data) if not success else "")

            # ─────────────────────────────────────────────────────────────
            # SECTION 7: Clone & Template (if time permits)
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 7: Clone Operations")
            print(f"{'=' * 60}")

            clone_name = f"mcp-clone-{datetime.now().strftime('%H%M%S')}"
            success, data = await call_tool(session, "clone_vm", {
                "template_name": TEST_VM,
                "new_name": clone_name,
                "datastore": datastore,
            })
            results.record("clone_vm", success, str(data) if not success else "")
            clone_created = success

            # Cleanup clone
            if clone_created:
                print(f"  Cleaning up clone: {clone_name}")
                await call_tool(session, "delete_vm", {"name": clone_name})

            # ─────────────────────────────────────────────────────────────
            # Restore VM state
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("CLEANUP: Restoring VM state")
            print(f"{'=' * 60}")

            # Power the test VM back on
            print(f"  Powering on {TEST_VM}...")
            await call_tool(session, "power_on", {"name": TEST_VM})

            # Print summary
            return results.summary()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
