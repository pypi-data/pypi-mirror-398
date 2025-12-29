"""Snapshot management - create, revert, delete, list snapshots."""

from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class SnapshotsMixin(MCPMixin):
    """VM snapshot management tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _get_snapshot_tree(
        self, snapshots: list, parent_path: str = ""
    ) -> list[dict[str, Any]]:
        """Recursively build snapshot tree."""
        result = []
        for snapshot in snapshots:
            path = f"{parent_path}/{snapshot.name}" if parent_path else snapshot.name
            result.append(
                {
                    "name": snapshot.name,
                    "path": path,
                    "description": snapshot.description,
                    "created": snapshot.createTime.isoformat() if snapshot.createTime else None,
                    "state": str(snapshot.state),
                    "quiesced": snapshot.quiesced,
                    "id": snapshot.id,
                }
            )
            if snapshot.childSnapshotList:
                result.extend(self._get_snapshot_tree(snapshot.childSnapshotList, path))
        return result

    def _find_snapshot_by_name(
        self, snapshots: list, name: str
    ) -> vim.vm.Snapshot | None:
        """Find a snapshot by name in the tree."""
        for snapshot in snapshots:
            if snapshot.name == name:
                return snapshot.snapshot
            if snapshot.childSnapshotList:
                found = self._find_snapshot_by_name(snapshot.childSnapshotList, name)
                if found:
                    return found
        return None

    @mcp_tool(
        name="list_snapshots",
        description="List all snapshots for a virtual machine",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_snapshots(self, name: str) -> list[dict[str, Any]]:
        """List all snapshots for a VM."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if not vm.snapshot or not vm.snapshot.rootSnapshotList:
            return []

        snapshots = self._get_snapshot_tree(vm.snapshot.rootSnapshotList)

        # Mark current snapshot
        current_snapshot = vm.snapshot.currentSnapshot
        for snap in snapshots:
            snap["is_current"] = False

        if current_snapshot:
            for snap in snapshots:
                # Compare by checking if this is the current one
                found = self._find_snapshot_by_name(
                    vm.snapshot.rootSnapshotList, snap["name"]
                )
                if found and found == current_snapshot:
                    snap["is_current"] = True
                    break

        return snapshots

    @mcp_tool(
        name="create_snapshot",
        description="Create a snapshot of a virtual machine",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False),
    )
    def create_snapshot(
        self,
        name: str,
        snapshot_name: str,
        description: str = "",
        memory: bool = True,
        quiesce: bool = False,
    ) -> str:
        """Create a VM snapshot.

        Args:
            name: VM name
            snapshot_name: Name for the new snapshot
            description: Optional description
            memory: Include memory state (allows instant restore to running state)
            quiesce: Quiesce guest filesystem (requires VMware Tools, ensures consistent state)
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        # Can only quiesce if VM is powered on and has tools
        if (
            quiesce
            and vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn
            and vm.guest.toolsRunningStatus != "guestToolsRunning"
        ):
            raise RuntimeError(
                "Cannot quiesce: VMware Tools not running. "
                "Set quiesce=False or install/start VMware Tools."
            )

        task = vm.CreateSnapshot_Task(
            name=snapshot_name,
            description=description,
            memory=memory,
            quiesce=quiesce,
        )
        self.conn.wait_for_task(task)

        return f"Snapshot '{snapshot_name}' created for VM '{name}'"

    @mcp_tool(
        name="revert_to_snapshot",
        description="Revert a VM to a specific snapshot",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False),
    )
    def revert_to_snapshot(self, name: str, snapshot_name: str) -> str:
        """Revert VM to a specific snapshot."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if not vm.snapshot or not vm.snapshot.rootSnapshotList:
            raise ValueError(f"VM '{name}' has no snapshots")

        snapshot = self._find_snapshot_by_name(
            vm.snapshot.rootSnapshotList, snapshot_name
        )
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_name}' not found on VM '{name}'")

        task = snapshot.RevertToSnapshot_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' reverted to snapshot '{snapshot_name}'"

    @mcp_tool(
        name="revert_to_current_snapshot",
        description="Revert a VM to its current (most recent) snapshot",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False),
    )
    def revert_to_current_snapshot(self, name: str) -> str:
        """Revert VM to its current snapshot."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if not vm.snapshot or not vm.snapshot.currentSnapshot:
            raise ValueError(f"VM '{name}' has no current snapshot")

        task = vm.RevertToCurrentSnapshot_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' reverted to current snapshot"

    @mcp_tool(
        name="delete_snapshot",
        description="Delete a specific snapshot from a VM",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def delete_snapshot(
        self, name: str, snapshot_name: str, remove_children: bool = False
    ) -> str:
        """Delete a VM snapshot.

        Args:
            name: VM name
            snapshot_name: Name of snapshot to delete
            remove_children: If True, also delete child snapshots
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if not vm.snapshot or not vm.snapshot.rootSnapshotList:
            raise ValueError(f"VM '{name}' has no snapshots")

        snapshot = self._find_snapshot_by_name(
            vm.snapshot.rootSnapshotList, snapshot_name
        )
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_name}' not found on VM '{name}'")

        task = snapshot.RemoveSnapshot_Task(removeChildren=remove_children)
        self.conn.wait_for_task(task)

        msg = f"Snapshot '{snapshot_name}' deleted from VM '{name}'"
        if remove_children:
            msg += " (including children)"
        return msg

    @mcp_tool(
        name="delete_all_snapshots",
        description="Delete ALL snapshots from a VM (consolidates disk)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def delete_all_snapshots(self, name: str) -> str:
        """Delete all snapshots from a VM."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if not vm.snapshot or not vm.snapshot.rootSnapshotList:
            return f"VM '{name}' has no snapshots to delete"

        task = vm.RemoveAllSnapshots_Task()
        self.conn.wait_for_task(task)

        return f"All snapshots deleted from VM '{name}'"

    @mcp_tool(
        name="rename_snapshot",
        description="Rename a snapshot and/or update its description",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def rename_snapshot(
        self,
        name: str,
        snapshot_name: str,
        new_name: str | None = None,
        new_description: str | None = None,
    ) -> str:
        """Rename a snapshot or update its description."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if not vm.snapshot or not vm.snapshot.rootSnapshotList:
            raise ValueError(f"VM '{name}' has no snapshots")

        snapshot = self._find_snapshot_by_name(
            vm.snapshot.rootSnapshotList, snapshot_name
        )
        if not snapshot:
            raise ValueError(f"Snapshot '{snapshot_name}' not found on VM '{name}'")

        snapshot.RenameSnapshot(
            name=new_name if new_name else snapshot_name,
            description=new_description if new_description else None,
        )

        changes = []
        if new_name:
            changes.append(f"renamed to '{new_name}'")
        if new_description:
            changes.append("description updated")

        return f"Snapshot '{snapshot_name}': {', '.join(changes)}"
