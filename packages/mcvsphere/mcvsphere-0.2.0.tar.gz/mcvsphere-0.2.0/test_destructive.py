#!/usr/bin/env python3
"""Destructive test suite for ESXi MCP server - creates/modifies/deletes resources.

WARNING: This test creates real VMs and modifies infrastructure!
Only run in a test environment.

Usage:
    python test_destructive.py [--skip-cleanup]

    --skip-cleanup: Leave test VM for inspection (default: cleanup)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Test configuration
TEST_VM_NAME = f"mcp-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
TEST_FOLDER_NAME = f"mcp-test-folder-{datetime.now().strftime('%H%M%S')}"
SKIP_CLEANUP = "--skip-cleanup" in sys.argv


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


class TestResult:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def record(self, name: str, success: bool, error: str = None):
        if success:
            self.passed += 1
            print(f"  ✅ {name}")
        else:
            self.failed += 1
            self.errors.append((name, error))
            print(f"  ❌ {name}: {error}")

    def skip(self, name: str, reason: str):
        self.skipped += 1
        print(f"  ⏭️  {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed + self.skipped
        print(f"\n{'=' * 60}")
        print("DESTRUCTIVE TEST SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Passed:  {self.passed}/{total}")
        print(f"  Failed:  {self.failed}/{total}")
        print(f"  Skipped: {self.skipped}/{total}")
        if self.errors:
            print(f"\nErrors:")
            for name, error in self.errors:
                print(f"  - {name}: {error}")
        return self.failed == 0


async def call_tool(session, name: str, args: dict = None) -> tuple[bool, any]:
    """Call a tool and return (success, result)."""
    args = args or {}
    try:
        result = await session.call_tool(name, args)
        if result.content:
            text = result.content[0].text
            # Try to parse as JSON, fall back to plain text
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = text
            return True, data
        return True, None
    except Exception as e:
        return False, str(e)


async def main():
    """Run destructive tests."""
    print("=" * 60)
    print("ESXi MCP Server - DESTRUCTIVE Test Suite")
    print("=" * 60)
    print(f"\n⚠️  WARNING: This test will CREATE and MODIFY resources!")
    print(f"    Test VM: {TEST_VM_NAME}")
    print(f"    Cleanup: {'DISABLED' if SKIP_CLEANUP else 'ENABLED'}")
    print()

    results = TestResult()
    dotenv = load_env_file()

    # Get datastore and network from env or use defaults
    default_datastore = dotenv.get("VCENTER_DATASTORE", "datastore1")
    default_network = dotenv.get("VCENTER_NETWORK", "VM Network")

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

            # Get available datastores and networks for test
            ds_result = await session.read_resource("esxi://datastores")
            datastores = json.loads(ds_result.contents[0].text) if ds_result.contents else []
            datastore = datastores[0]["name"] if datastores else default_datastore

            net_result = await session.read_resource("esxi://networks")
            networks = json.loads(net_result.contents[0].text) if net_result.contents else []
            network = networks[0]["name"] if networks else default_network

            print(f"Using datastore: {datastore}")
            print(f"Using network: {network}")

            # ─────────────────────────────────────────────────────────────
            # SECTION 1: VM Lifecycle
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 1: VM Lifecycle")
            print(f"{'=' * 60}")

            # Create VM
            print(f"\n>>> Creating test VM: {TEST_VM_NAME}")
            success, data = await call_tool(session, "create_vm", {
                "name": TEST_VM_NAME,
                "cpu": 1,
                "memory_mb": 512,
                "disk_gb": 1,
                "guest_id": "otherGuest64",
                "datastore": datastore,
                "network": network,
            })
            results.record("create_vm", success, data if not success else None)

            if not success:
                print("\n❌ Cannot continue without test VM. Aborting.")
                results.summary()
                return

            # Get VM info
            success, data = await call_tool(session, "get_vm_info", {"name": TEST_VM_NAME})
            results.record("get_vm_info (new VM)", success, data if not success else None)

            # Rename VM (and rename back)
            new_name = f"{TEST_VM_NAME}-renamed"
            success, data = await call_tool(session, "rename_vm", {
                "name": TEST_VM_NAME,
                "new_name": new_name,
            })
            results.record("rename_vm", success, data if not success else None)

            if success:
                # Rename back
                await call_tool(session, "rename_vm", {"name": new_name, "new_name": TEST_VM_NAME})

            # Reconfigure VM
            success, data = await call_tool(session, "reconfigure_vm", {
                "name": TEST_VM_NAME,
                "memory_mb": 1024,
            })
            results.record("reconfigure_vm (memory)", success, data if not success else None)

            # ─────────────────────────────────────────────────────────────
            # SECTION 2: Power Operations
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 2: Power Operations")
            print(f"{'=' * 60}")

            # Power on
            success, data = await call_tool(session, "power_on", {"name": TEST_VM_NAME})
            results.record("power_on", success, data if not success else None)

            if success:
                # Wait a moment for power state to stabilize
                await asyncio.sleep(3)

                # Suspend
                success, data = await call_tool(session, "suspend_vm", {"name": TEST_VM_NAME})
                results.record("suspend_vm", success, data if not success else None)

                if success:
                    await asyncio.sleep(2)
                    # Power on again to test power off
                    await call_tool(session, "power_on", {"name": TEST_VM_NAME})
                    await asyncio.sleep(2)

                # Power off
                success, data = await call_tool(session, "power_off", {"name": TEST_VM_NAME})
                results.record("power_off", success, data if not success else None)
            else:
                results.skip("suspend_vm", "power_on failed")
                results.skip("power_off", "power_on failed")

            # Ensure VM is off for disk operations
            await call_tool(session, "power_off", {"name": TEST_VM_NAME})
            await asyncio.sleep(2)

            # ─────────────────────────────────────────────────────────────
            # SECTION 3: Disk Management
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 3: Disk Management")
            print(f"{'=' * 60}")

            # Add disk
            success, data = await call_tool(session, "add_disk", {
                "vm_name": TEST_VM_NAME,
                "size_gb": 1,
                "thin_provisioned": True,
            })
            results.record("add_disk", success, data if not success else None)

            # List disks
            success, data = await call_tool(session, "list_disks", {"vm_name": TEST_VM_NAME})
            results.record("list_disks (after add)", success, data if not success else None)
            disk_count = len(data) if success and isinstance(data, list) else 0

            # Extend disk
            if disk_count > 0:
                success, data = await call_tool(session, "extend_disk", {
                    "vm_name": TEST_VM_NAME,
                    "disk_label": "Hard disk 1",
                    "new_size_gb": 2,
                })
                results.record("extend_disk", success, data if not success else None)

            # Remove the added disk (Hard disk 2)
            if disk_count >= 2:
                success, data = await call_tool(session, "remove_disk", {
                    "vm_name": TEST_VM_NAME,
                    "disk_label": "Hard disk 2",
                })
                results.record("remove_disk", success, data if not success else None)
            else:
                results.skip("remove_disk", "Not enough disks")

            # ─────────────────────────────────────────────────────────────
            # SECTION 4: NIC Management
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 4: NIC Management")
            print(f"{'=' * 60}")

            # Add NIC
            success, data = await call_tool(session, "add_nic", {
                "vm_name": TEST_VM_NAME,
                "network": network,
                "nic_type": "vmxnet3",
            })
            results.record("add_nic", success, data if not success else None)

            # List NICs
            success, data = await call_tool(session, "list_nics", {"vm_name": TEST_VM_NAME})
            results.record("list_nics (after add)", success, data if not success else None)
            nic_count = len(data) if success and isinstance(data, list) else 0

            # Connect/disconnect NIC
            if nic_count > 0:
                success, data = await call_tool(session, "connect_nic", {
                    "vm_name": TEST_VM_NAME,
                    "nic_label": "Network adapter 1",
                    "connected": False,
                })
                results.record("connect_nic (disconnect)", success, data if not success else None)

            # Remove added NIC (Network adapter 2)
            if nic_count >= 2:
                success, data = await call_tool(session, "remove_nic", {
                    "vm_name": TEST_VM_NAME,
                    "nic_label": "Network adapter 2",
                })
                results.record("remove_nic", success, data if not success else None)
            else:
                results.skip("remove_nic", "Not enough NICs")

            # ─────────────────────────────────────────────────────────────
            # SECTION 5: Snapshots
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 5: Snapshots")
            print(f"{'=' * 60}")

            # Create snapshot
            success, data = await call_tool(session, "create_snapshot", {
                "name": TEST_VM_NAME,
                "snapshot_name": "test-snapshot-1",
                "description": "MCP test snapshot",
            })
            results.record("create_snapshot", success, data if not success else None)

            # List snapshots
            success, data = await call_tool(session, "list_snapshots", {"name": TEST_VM_NAME})
            results.record("list_snapshots", success, data if not success else None)

            # Rename snapshot
            success, data = await call_tool(session, "rename_snapshot", {
                "name": TEST_VM_NAME,
                "snapshot_name": "test-snapshot-1",
                "new_name": "renamed-snapshot",
                "new_description": "Renamed by MCP test",
            })
            results.record("rename_snapshot", success, data if not success else None)

            # Revert to snapshot
            success, data = await call_tool(session, "revert_to_snapshot", {
                "name": TEST_VM_NAME,
                "snapshot_name": "renamed-snapshot",
            })
            results.record("revert_to_snapshot", success, data if not success else None)

            # Delete snapshot
            success, data = await call_tool(session, "delete_snapshot", {
                "name": TEST_VM_NAME,
                "snapshot_name": "renamed-snapshot",
            })
            results.record("delete_snapshot", success, data if not success else None)

            # ─────────────────────────────────────────────────────────────
            # SECTION 6: Folder Operations (vCenter)
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 6: Folder Operations (vCenter)")
            print(f"{'=' * 60}")

            # Create folder
            success, data = await call_tool(session, "create_folder", {
                "folder_name": TEST_FOLDER_NAME,
            })
            results.record("create_folder", success, data if not success else None)
            folder_created = success

            # Move VM to folder
            if folder_created:
                success, data = await call_tool(session, "move_vm_to_folder", {
                    "vm_name": TEST_VM_NAME,
                    "folder_path": f"vm/{TEST_FOLDER_NAME}",
                })
                results.record("move_vm_to_folder", success, data if not success else None)

                # Move back to root for cleanup
                if success:
                    await call_tool(session, "move_vm_to_folder", {
                        "vm_name": TEST_VM_NAME,
                        "folder_path": "vm",
                    })
            else:
                results.skip("move_vm_to_folder", "folder creation failed")

            # ─────────────────────────────────────────────────────────────
            # SECTION 7: Datastore Operations
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 7: Datastore Operations")
            print(f"{'=' * 60}")

            # Create folder in datastore
            test_ds_folder = f"mcp-test-{datetime.now().strftime('%H%M%S')}"
            success, data = await call_tool(session, "create_datastore_folder", {
                "datastore": datastore,
                "path": test_ds_folder,
            })
            results.record("create_datastore_folder", success, data if not success else None)
            ds_folder_created = success

            # Delete datastore folder
            if ds_folder_created:
                success, data = await call_tool(session, "delete_datastore_file", {
                    "datastore": datastore,
                    "path": test_ds_folder,
                })
                results.record("delete_datastore_file (folder)", success, data if not success else None)
            else:
                results.skip("delete_datastore_file", "folder creation failed")

            # ─────────────────────────────────────────────────────────────
            # SECTION 8: vCenter Advanced Operations
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("SECTION 8: vCenter Advanced Operations")
            print(f"{'=' * 60}")

            # Storage vMotion - move VM to different datastore
            # Get list of datastores to find a second one
            if len(datastores) >= 2:
                # Find a different datastore
                other_datastore = None
                for ds in datastores:
                    if ds["name"] != datastore:
                        other_datastore = ds["name"]
                        break

                if other_datastore:
                    print(f"\n>>> Storage vMotion: {datastore} → {other_datastore}")
                    success, data = await call_tool(session, "storage_vmotion", {
                        "vm_name": TEST_VM_NAME,
                        "target_datastore": other_datastore,
                    })
                    results.record("storage_vmotion", success, data if not success else None)

                    # Move back to original datastore
                    if success:
                        await call_tool(session, "storage_vmotion", {
                            "vm_name": TEST_VM_NAME,
                            "target_datastore": datastore,
                        })
                else:
                    results.skip("storage_vmotion", "No alternate datastore found")
            else:
                results.skip("storage_vmotion", "Only one datastore available")

            # Convert VM to template
            print(f"\n>>> Converting VM to template: {TEST_VM_NAME}")
            success, data = await call_tool(session, "convert_to_template", {
                "vm_name": TEST_VM_NAME,
            })
            results.record("convert_to_template", success, data if not success else None)
            is_template = success

            # Deploy from template
            deployed_vm_name = f"{TEST_VM_NAME}-deployed"
            if is_template:
                success, data = await call_tool(session, "deploy_from_template", {
                    "template_name": TEST_VM_NAME,
                    "new_vm_name": deployed_vm_name,
                    "datastore": datastore,
                })
                results.record("deploy_from_template", success, data if not success else None)
                deployed_vm_created = success

                # Clean up deployed VM
                if deployed_vm_created:
                    await call_tool(session, "delete_vm", {"name": deployed_vm_name})
            else:
                results.skip("deploy_from_template", "template conversion failed")

            # Convert template back to VM
            if is_template:
                success, data = await call_tool(session, "convert_to_vm", {
                    "template_name": TEST_VM_NAME,
                })
                results.record("convert_to_vm", success, data if not success else None)
            else:
                results.skip("convert_to_vm", "template conversion failed")

            # ─────────────────────────────────────────────────────────────
            # CLEANUP
            # ─────────────────────────────────────────────────────────────
            print(f"\n{'=' * 60}")
            print("CLEANUP")
            print(f"{'=' * 60}")

            if SKIP_CLEANUP:
                print(f"\n⚠️  Cleanup SKIPPED. Test VM '{TEST_VM_NAME}' remains.")
                if folder_created:
                    print(f"    Test folder '{TEST_FOLDER_NAME}' remains.")
            else:
                # Delete test VM
                print(f"\n>>> Deleting test VM: {TEST_VM_NAME}")
                success, data = await call_tool(session, "delete_vm", {"name": TEST_VM_NAME})
                results.record("delete_vm (cleanup)", success, data if not success else None)

                # Note: Folder deletion would require empty folder
                # In a real scenario, you'd need to handle this
                if folder_created:
                    print(f"    Note: Test folder '{TEST_FOLDER_NAME}' may need manual cleanup")

            # Print summary
            return results.summary()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
