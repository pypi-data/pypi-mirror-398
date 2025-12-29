"""VM Lifecycle operations - create, clone, delete, reconfigure."""

from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class VMLifecycleMixin(MCPMixin):
    """VM lifecycle management tools - CRUD operations for virtual machines."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    @mcp_tool(
        name="list_vms",
        description="List all virtual machines in the vSphere inventory",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_vms(self) -> list[dict[str, Any]]:
        """List all virtual machines with basic info."""
        vms = []
        for vm in self.conn.get_all_vms():
            vms.append(
                {
                    "name": vm.name,
                    "power_state": str(vm.runtime.powerState),
                    "cpu": vm.config.hardware.numCPU if vm.config else None,
                    "memory_mb": vm.config.hardware.memoryMB if vm.config else None,
                    "guest_os": vm.config.guestFullName if vm.config else None,
                }
            )
        return vms

    @mcp_tool(
        name="get_vm_info",
        description="Get detailed information about a specific virtual machine",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_vm_info(self, name: str) -> dict[str, Any]:
        """Get detailed VM information including hardware, network, and storage."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        # Get disk info
        disks = []
        if vm.config:
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualDisk):
                    disks.append(
                        {
                            "label": device.deviceInfo.label,
                            "capacity_gb": round(device.capacityInKB / (1024 * 1024), 2),
                            "thin_provisioned": getattr(
                                device.backing, "thinProvisioned", None
                            ),
                        }
                    )

        # Get NIC info
        nics = []
        if vm.config:
            for device in vm.config.hardware.device:
                if isinstance(device, vim.vm.device.VirtualEthernetCard):
                    nics.append(
                        {
                            "label": device.deviceInfo.label,
                            "mac_address": device.macAddress,
                            "connected": device.connectable.connected
                            if device.connectable
                            else None,
                        }
                    )

        return {
            "name": vm.name,
            "power_state": str(vm.runtime.powerState),
            "cpu": vm.config.hardware.numCPU if vm.config else None,
            "memory_mb": vm.config.hardware.memoryMB if vm.config else None,
            "guest_os": vm.config.guestFullName if vm.config else None,
            "guest_id": vm.config.guestId if vm.config else None,
            "uuid": vm.config.uuid if vm.config else None,
            "instance_uuid": vm.config.instanceUuid if vm.config else None,
            "host": vm.runtime.host.name if vm.runtime.host else None,
            "datastore": [ds.name for ds in vm.datastore] if vm.datastore else [],
            "ip_address": vm.guest.ipAddress if vm.guest else None,
            "hostname": vm.guest.hostName if vm.guest else None,
            "tools_status": str(vm.guest.toolsStatus) if vm.guest else None,
            "tools_version": vm.guest.toolsVersion if vm.guest else None,
            "disks": disks,
            "nics": nics,
            "annotation": vm.config.annotation if vm.config else None,
        }

    @mcp_tool(
        name="create_vm",
        description="Create a new virtual machine with specified resources",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False),
    )
    def create_vm(
        self,
        name: str,
        cpu: int = 2,
        memory_mb: int = 4096,
        disk_gb: int = 20,
        datastore: str | None = None,
        network: str | None = None,
        guest_id: str = "otherGuest64",
    ) -> str:
        """Create a new virtual machine with specified configuration."""
        # Resolve datastore
        datastore_obj = self.conn.datastore
        if datastore:
            datastore_obj = self.conn.find_datastore(datastore)
            if not datastore_obj:
                raise ValueError(f"Datastore '{datastore}' not found")

        # Resolve network
        network_obj = self.conn.network
        if network:
            network_obj = self.conn.find_network(network)
            if not network_obj:
                raise ValueError(f"Network '{network}' not found")

        # Build VM config spec with required files property
        vm_file_info = vim.vm.FileInfo(
            vmPathName=f"[{datastore_obj.name}]"
        )
        vm_spec = vim.vm.ConfigSpec(
            name=name,
            memoryMB=memory_mb,
            numCPUs=cpu,
            guestId=guest_id,
            files=vm_file_info,
        )

        device_specs = []

        # Add SCSI controller
        controller_spec = vim.vm.device.VirtualDeviceSpec()
        controller_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        controller_spec.device = vim.vm.device.ParaVirtualSCSIController()
        controller_spec.device.busNumber = 0
        controller_spec.device.sharedBus = (
            vim.vm.device.VirtualSCSIController.Sharing.noSharing
        )
        controller_spec.device.key = -101
        device_specs.append(controller_spec)

        # Add virtual disk
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.create
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.capacityInKB = disk_gb * 1024 * 1024
        disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        disk_spec.device.backing.diskMode = "persistent"
        disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.fileName = f"[{datastore_obj.name}]"
        disk_spec.device.controllerKey = controller_spec.device.key
        disk_spec.device.unitNumber = 0
        disk_spec.device.key = -1  # Negative key for new device
        device_specs.append(disk_spec)

        # Add network adapter if network is available
        if network_obj:
            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            nic_spec.device = vim.vm.device.VirtualVmxnet3()

            if isinstance(network_obj, vim.Network):
                nic_spec.device.backing = (
                    vim.vm.device.VirtualEthernetCard.NetworkBackingInfo(
                        network=network_obj, deviceName=network_obj.name
                    )
                )
            elif isinstance(network_obj, vim.dvs.DistributedVirtualPortgroup):
                dvs_uuid = network_obj.config.distributedVirtualSwitch.uuid
                port_key = network_obj.key
                nic_spec.device.backing = (
                    vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo(
                        port=vim.dvs.PortConnection(
                            portgroupKey=port_key, switchUuid=dvs_uuid
                        )
                    )
                )

            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo(
                startConnected=True, allowGuestControl=True
            )
            device_specs.append(nic_spec)

        vm_spec.deviceChange = device_specs

        # Create VM
        task = self.conn.datacenter.vmFolder.CreateVM_Task(
            config=vm_spec, pool=self.conn.resource_pool
        )
        self.conn.wait_for_task(task)

        return f"VM '{name}' created successfully"

    @mcp_tool(
        name="clone_vm",
        description="Clone a virtual machine from an existing VM or template",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False),
    )
    def clone_vm(
        self,
        template_name: str,
        new_name: str,
        power_on: bool = False,
        datastore: str | None = None,
    ) -> str:
        """Clone a VM from a template or existing VM."""
        template_vm = self.conn.find_vm(template_name)
        if not template_vm:
            raise ValueError(f"Template VM '{template_name}' not found")

        vm_folder = template_vm.parent
        if not isinstance(vm_folder, vim.Folder):
            vm_folder = self.conn.datacenter.vmFolder

        # Resolve datastore
        datastore_obj = self.conn.datastore
        if datastore:
            datastore_obj = self.conn.find_datastore(datastore)
            if not datastore_obj:
                raise ValueError(f"Datastore '{datastore}' not found")

        resource_pool = template_vm.resourcePool or self.conn.resource_pool
        relocate_spec = vim.vm.RelocateSpec(pool=resource_pool, datastore=datastore_obj)
        clone_spec = vim.vm.CloneSpec(
            powerOn=power_on, template=False, location=relocate_spec
        )

        task = template_vm.Clone(folder=vm_folder, name=new_name, spec=clone_spec)
        self.conn.wait_for_task(task)

        return f"VM '{new_name}' cloned from '{template_name}'"

    @mcp_tool(
        name="delete_vm",
        description="Delete a virtual machine permanently (powers off if running)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def delete_vm(self, name: str) -> str:
        """Delete a virtual machine permanently."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        # Power off if running
        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
            task = vm.PowerOffVM_Task()
            self.conn.wait_for_task(task)

        task = vm.Destroy_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' deleted"

    @mcp_tool(
        name="reconfigure_vm",
        description="Reconfigure VM hardware (CPU, memory). VM should be powered off for most changes.",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def reconfigure_vm(
        self,
        name: str,
        cpu: int | None = None,
        memory_mb: int | None = None,
        annotation: str | None = None,
    ) -> str:
        """Reconfigure VM hardware settings."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        config_spec = vim.vm.ConfigSpec()
        changes = []

        if cpu is not None:
            config_spec.numCPUs = cpu
            changes.append(f"CPU: {cpu}")

        if memory_mb is not None:
            config_spec.memoryMB = memory_mb
            changes.append(f"Memory: {memory_mb}MB")

        if annotation is not None:
            config_spec.annotation = annotation
            changes.append("annotation updated")

        if not changes:
            return f"No changes specified for VM '{name}'"

        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return f"VM '{name}' reconfigured: {', '.join(changes)}"

    @mcp_tool(
        name="rename_vm",
        description="Rename a virtual machine",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def rename_vm(self, name: str, new_name: str) -> str:
        """Rename a virtual machine."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        task = vm.Rename_Task(newName=new_name)
        self.conn.wait_for_task(task)

        return f"VM renamed from '{name}' to '{new_name}'"
