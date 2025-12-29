"""Virtual Disk Management - add, remove, extend disks and manage ISOs."""

from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class DiskManagementMixin(MCPMixin):
    """Virtual disk and ISO management tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _get_next_disk_unit_number(self, vm: vim.VirtualMachine) -> tuple[int, vim.vm.device.VirtualSCSIController]:
        """Find the next available SCSI unit number and controller."""
        scsi_controllers = []
        used_units = {}

        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualSCSIController):
                scsi_controllers.append(device)
                used_units[device.key] = set()

            if (
                hasattr(device, "controllerKey")
                and hasattr(device, "unitNumber")
                and device.controllerKey in used_units
            ):
                used_units[device.controllerKey].add(device.unitNumber)

        if not scsi_controllers:
            raise ValueError("No SCSI controller found on VM")

        # Find first available slot (unit 7 is reserved for controller)
        for controller in scsi_controllers:
            for unit in range(16):
                if unit == 7:  # Reserved for SCSI controller
                    continue
                if unit not in used_units.get(controller.key, set()):
                    return unit, controller

        raise ValueError("No available SCSI unit numbers (all 15 slots used)")

    def _find_disk_by_label(
        self, vm: vim.VirtualMachine, label: str
    ) -> vim.vm.device.VirtualDisk | None:
        """Find a virtual disk by its label (e.g., 'Hard disk 1')."""
        for device in vm.config.hardware.device:
            if (
                isinstance(device, vim.vm.device.VirtualDisk)
                and device.deviceInfo.label.lower() == label.lower()
            ):
                return device
        return None

    def _find_cdrom(self, vm: vim.VirtualMachine) -> vim.vm.device.VirtualCdrom | None:
        """Find the first CD-ROM drive on the VM."""
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualCdrom):
                return device
        return None

    @mcp_tool(
        name="add_disk",
        description="Add a new virtual disk to a VM",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def add_disk(
        self,
        vm_name: str,
        size_gb: int,
        thin_provisioned: bool = True,
        datastore: str | None = None,
    ) -> dict[str, Any]:
        """Add a new virtual disk to a VM.

        Args:
            vm_name: Name of the virtual machine
            size_gb: Size of the new disk in GB
            thin_provisioned: Use thin provisioning (default True)
            datastore: Datastore for the disk (default: same as VM)

        Returns:
            Dict with new disk details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        # Get next available unit number and controller
        unit_number, controller = self._get_next_disk_unit_number(vm)

        # Determine datastore
        if datastore:
            ds = self.conn.find_datastore(datastore)
            if not ds:
                raise ValueError(f"Datastore '{datastore}' not found")
            ds_name = datastore
        else:
            # Use VM's datastore
            ds_name = vm.config.files.vmPathName.split("]")[0].strip("[")

        # Calculate size in KB
        size_kb = size_gb * 1024 * 1024

        # Create disk backing
        backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        backing.diskMode = "persistent"
        backing.thinProvisioned = thin_provisioned
        backing.datastore = self.conn.find_datastore(ds_name)

        # Create the virtual disk
        disk = vim.vm.device.VirtualDisk()
        disk.backing = backing
        disk.controllerKey = controller.key
        disk.unitNumber = unit_number
        disk.capacityInKB = size_kb

        # Create device config spec
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
        disk_spec.device = disk

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [disk_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "disk_added",
            "size_gb": size_gb,
            "thin_provisioned": thin_provisioned,
            "datastore": ds_name,
            "controller": controller.deviceInfo.label,
            "unit_number": unit_number,
        }

    @mcp_tool(
        name="remove_disk",
        description="Remove a virtual disk from a VM",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def remove_disk(
        self,
        vm_name: str,
        disk_label: str,
        delete_file: bool = False,
    ) -> dict[str, Any]:
        """Remove a virtual disk from a VM.

        Args:
            vm_name: Name of the virtual machine
            disk_label: Label of disk to remove (e.g., 'Hard disk 2')
            delete_file: Also delete the VMDK file (default False - keep file)

        Returns:
            Dict with removal details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        disk = self._find_disk_by_label(vm, disk_label)
        if not disk:
            # List available disks
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualDisk)
            ]
            raise ValueError(f"Disk '{disk_label}' not found. Available: {available}")

        # Create device removal spec
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        if delete_file:
            disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.destroy
        disk_spec.device = disk

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [disk_spec]

        # Get disk info before removal
        disk_path = disk.backing.fileName if hasattr(disk.backing, "fileName") else "unknown"
        disk_size_gb = disk.capacityInKB / (1024 * 1024)

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "disk_removed",
            "disk_label": disk_label,
            "disk_path": disk_path,
            "size_gb": round(disk_size_gb, 2),
            "file_deleted": delete_file,
        }

    @mcp_tool(
        name="extend_disk",
        description="Extend/grow a virtual disk",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def extend_disk(
        self,
        vm_name: str,
        disk_label: str,
        new_size_gb: int,
    ) -> dict[str, Any]:
        """Extend a virtual disk to a larger size.

        Args:
            vm_name: Name of the virtual machine
            disk_label: Label of disk to extend (e.g., 'Hard disk 1')
            new_size_gb: New total size in GB (must be larger than current)

        Returns:
            Dict with extension details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        disk = self._find_disk_by_label(vm, disk_label)
        if not disk:
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualDisk)
            ]
            raise ValueError(f"Disk '{disk_label}' not found. Available: {available}")

        current_size_gb = disk.capacityInKB / (1024 * 1024)
        if new_size_gb <= current_size_gb:
            raise ValueError(
                f"New size ({new_size_gb}GB) must be larger than current ({current_size_gb:.2f}GB)"
            )

        # Update disk capacity
        new_size_kb = new_size_gb * 1024 * 1024
        disk.capacityInKB = new_size_kb

        # Create device edit spec
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        disk_spec.device = disk

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [disk_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "disk_extended",
            "disk_label": disk_label,
            "old_size_gb": round(current_size_gb, 2),
            "new_size_gb": new_size_gb,
        }

    @mcp_tool(
        name="list_disks",
        description="List all virtual disks attached to a VM",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_disks(self, vm_name: str) -> list[dict[str, Any]]:
        """List all virtual disks attached to a VM.

        Args:
            vm_name: Name of the virtual machine

        Returns:
            List of disk details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        disks = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk):
                backing = device.backing
                disk_info = {
                    "label": device.deviceInfo.label,
                    "size_gb": round(device.capacityInKB / (1024 * 1024), 2),
                    "unit_number": device.unitNumber,
                }

                if hasattr(backing, "fileName"):
                    disk_info["file"] = backing.fileName
                if hasattr(backing, "thinProvisioned"):
                    disk_info["thin_provisioned"] = backing.thinProvisioned
                if hasattr(backing, "diskMode"):
                    disk_info["mode"] = backing.diskMode

                disks.append(disk_info)

        return disks

    @mcp_tool(
        name="attach_iso",
        description="Attach an ISO file to a VM's CD/DVD drive",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def attach_iso(
        self,
        vm_name: str,
        iso_path: str,
        datastore: str | None = None,
    ) -> dict[str, Any]:
        """Attach an ISO file to a VM's CD/DVD drive.

        Args:
            vm_name: Name of the virtual machine
            iso_path: Path to ISO file on datastore (e.g., 'iso/ubuntu.iso')
            datastore: Datastore containing the ISO (default: first VM datastore)

        Returns:
            Dict with attachment details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        cdrom = self._find_cdrom(vm)
        if not cdrom:
            raise ValueError(f"No CD/DVD drive found on VM '{vm_name}'")

        # Determine datastore
        if not datastore:
            datastore = vm.config.files.vmPathName.split("]")[0].strip("[")

        # Build full ISO path
        full_iso_path = f"[{datastore}] {iso_path}"

        # Create ISO backing
        backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
        backing.fileName = full_iso_path

        # Configure CD-ROM
        cdrom.backing = backing
        cdrom.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        cdrom.connectable.connected = True
        cdrom.connectable.startConnected = True
        cdrom.connectable.allowGuestControl = True

        # Create device edit spec
        cdrom_spec = vim.vm.device.VirtualDeviceSpec()
        cdrom_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        cdrom_spec.device = cdrom

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [cdrom_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "iso_attached",
            "iso_path": full_iso_path,
            "cdrom": cdrom.deviceInfo.label,
            "connected": True,
        }

    @mcp_tool(
        name="detach_iso",
        description="Detach/eject ISO from a VM's CD/DVD drive",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def detach_iso(self, vm_name: str) -> dict[str, Any]:
        """Detach/eject ISO from a VM's CD/DVD drive.

        Args:
            vm_name: Name of the virtual machine

        Returns:
            Dict with detachment details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        cdrom = self._find_cdrom(vm)
        if not cdrom:
            raise ValueError(f"No CD/DVD drive found on VM '{vm_name}'")

        # Get current ISO path for reporting
        old_iso = None
        if hasattr(cdrom.backing, "fileName"):
            old_iso = cdrom.backing.fileName

        # Create empty client device backing (ejects the ISO)
        backing = vim.vm.device.VirtualCdrom.RemotePassthroughBackingInfo()
        backing.deviceName = ""

        # Configure CD-ROM
        cdrom.backing = backing
        cdrom.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        cdrom.connectable.connected = False
        cdrom.connectable.startConnected = False
        cdrom.connectable.allowGuestControl = True

        # Create device edit spec
        cdrom_spec = vim.vm.device.VirtualDeviceSpec()
        cdrom_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        cdrom_spec.device = cdrom

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [cdrom_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "iso_detached",
            "previous_iso": old_iso,
            "cdrom": cdrom.deviceInfo.label,
        }
