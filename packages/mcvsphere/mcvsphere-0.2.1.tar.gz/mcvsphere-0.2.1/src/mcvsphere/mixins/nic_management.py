"""Virtual NIC Management - add, remove, configure network adapters."""

from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class NICManagementMixin(MCPMixin):
    """Virtual network adapter management tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _find_nic_by_label(
        self, vm: vim.VirtualMachine, label: str
    ) -> vim.vm.device.VirtualEthernetCard | None:
        """Find a virtual NIC by its label (e.g., 'Network adapter 1')."""
        for device in vm.config.hardware.device:
            if (
                isinstance(device, vim.vm.device.VirtualEthernetCard)
                and device.deviceInfo.label.lower() == label.lower()
            ):
                return device
        return None

    def _get_network_backing(
        self, network_name: str
    ) -> vim.vm.device.VirtualEthernetCard.NetworkBackingInfo:
        """Get the appropriate backing info for a network."""
        network = self.conn.find_network(network_name)
        if not network:
            raise ValueError(f"Network '{network_name}' not found")

        if isinstance(network, vim.dvs.DistributedVirtualPortgroup):
            # Distributed virtual switch portgroup
            backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
            backing.port = vim.dvs.PortConnection()
            backing.port.portgroupKey = network.key
            backing.port.switchUuid = network.config.distributedVirtualSwitch.uuid
        else:
            # Standard vSwitch network
            backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            backing.network = network
            backing.deviceName = network_name

        return backing

    @mcp_tool(
        name="list_nics",
        description="List all network adapters attached to a VM",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_nics(self, vm_name: str) -> list[dict[str, Any]]:
        """List all virtual network adapters on a VM.

        Args:
            vm_name: Name of the virtual machine

        Returns:
            List of NIC details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        nics = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nic_info = {
                    "label": device.deviceInfo.label,
                    "type": type(device).__name__.replace("Virtual", ""),
                    "mac_address": device.macAddress,
                    "mac_type": device.addressType,
                    "connected": device.connectable.connected if device.connectable else False,
                    "start_connected": device.connectable.startConnected if device.connectable else False,
                }

                # Get network name from backing
                backing = device.backing
                if hasattr(backing, "deviceName"):
                    nic_info["network"] = backing.deviceName
                elif hasattr(backing, "port") and hasattr(backing.port, "portgroupKey"):
                    # For distributed switch, look up the portgroup name
                    nic_info["network"] = f"DVS:{backing.port.portgroupKey}"
                    # Try to get actual name
                    for net in self.conn.datacenter.networkFolder.childEntity:
                        if hasattr(net, "key") and net.key == backing.port.portgroupKey:
                            nic_info["network"] = net.name
                            break

                nics.append(nic_info)

        return nics

    @mcp_tool(
        name="add_nic",
        description="Add a new network adapter to a VM",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def add_nic(
        self,
        vm_name: str,
        network: str,
        nic_type: str = "vmxnet3",
        start_connected: bool = True,
    ) -> dict[str, Any]:
        """Add a new network adapter to a VM.

        Args:
            vm_name: Name of the virtual machine
            network: Network/portgroup name to connect to
            nic_type: Adapter type - vmxnet3 (default), e1000, e1000e
            start_connected: Connect adapter when VM powers on (default True)

        Returns:
            Dict with new NIC details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        # Create the appropriate NIC type
        nic_types = {
            "vmxnet3": vim.vm.device.VirtualVmxnet3,
            "vmxnet2": vim.vm.device.VirtualVmxnet2,
            "e1000": vim.vm.device.VirtualE1000,
            "e1000e": vim.vm.device.VirtualE1000e,
        }

        nic_class = nic_types.get(nic_type.lower())
        if not nic_class:
            raise ValueError(f"Unknown NIC type '{nic_type}'. Valid: {list(nic_types.keys())}")

        # Create the NIC
        nic = nic_class()
        nic.backing = self._get_network_backing(network)
        nic.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic.connectable.startConnected = start_connected
        nic.connectable.connected = False  # Can't connect until powered on
        nic.connectable.allowGuestControl = True
        nic.addressType = "generated"  # Let ESXi generate MAC address

        # Create device add spec
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        nic_spec.device = nic

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [nic_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        # Get the MAC address that was assigned
        vm.Reload()
        new_nic = None
        for device in vm.config.hardware.device:
            if (
                isinstance(device, vim.vm.device.VirtualEthernetCard)
                and device.backing
                and hasattr(device.backing, "deviceName")
                and device.backing.deviceName == network
            ):
                new_nic = device
                break

        mac_address = new_nic.macAddress if new_nic else "pending"

        return {
            "vm": vm_name,
            "action": "nic_added",
            "network": network,
            "nic_type": nic_type,
            "mac_address": mac_address,
            "start_connected": start_connected,
        }

    @mcp_tool(
        name="remove_nic",
        description="Remove a network adapter from a VM",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def remove_nic(
        self,
        vm_name: str,
        nic_label: str,
    ) -> dict[str, Any]:
        """Remove a network adapter from a VM.

        Args:
            vm_name: Name of the virtual machine
            nic_label: Label of NIC to remove (e.g., 'Network adapter 1')

        Returns:
            Dict with removal details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        nic = self._find_nic_by_label(vm, nic_label)
        if not nic:
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualEthernetCard)
            ]
            raise ValueError(f"NIC '{nic_label}' not found. Available: {available}")

        # Get info before removal
        mac_address = nic.macAddress
        network = "unknown"
        if hasattr(nic.backing, "deviceName"):
            network = nic.backing.deviceName

        # Create device removal spec
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        nic_spec.device = nic

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [nic_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "nic_removed",
            "nic_label": nic_label,
            "mac_address": mac_address,
            "network": network,
        }

    @mcp_tool(
        name="change_nic_network",
        description="Change which network a NIC is connected to",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def change_nic_network(
        self,
        vm_name: str,
        nic_label: str,
        new_network: str,
    ) -> dict[str, Any]:
        """Change which network a NIC is connected to.

        Args:
            vm_name: Name of the virtual machine
            nic_label: Label of NIC to modify (e.g., 'Network adapter 1')
            new_network: New network/portgroup name

        Returns:
            Dict with change details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        nic = self._find_nic_by_label(vm, nic_label)
        if not nic:
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualEthernetCard)
            ]
            raise ValueError(f"NIC '{nic_label}' not found. Available: {available}")

        # Get old network name
        old_network = "unknown"
        if hasattr(nic.backing, "deviceName"):
            old_network = nic.backing.deviceName

        # Update backing to new network
        nic.backing = self._get_network_backing(new_network)

        # Create device edit spec
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = nic

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [nic_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "nic_network_changed",
            "nic_label": nic_label,
            "old_network": old_network,
            "new_network": new_network,
            "mac_address": nic.macAddress,
        }

    @mcp_tool(
        name="connect_nic",
        description="Connect or disconnect a NIC on a running VM",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def connect_nic(
        self,
        vm_name: str,
        nic_label: str,
        connected: bool = True,
    ) -> dict[str, Any]:
        """Connect or disconnect a NIC on a running VM.

        Args:
            vm_name: Name of the virtual machine
            nic_label: Label of NIC (e.g., 'Network adapter 1')
            connected: True to connect, False to disconnect

        Returns:
            Dict with connection status
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        nic = self._find_nic_by_label(vm, nic_label)
        if not nic:
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualEthernetCard)
            ]
            raise ValueError(f"NIC '{nic_label}' not found. Available: {available}")

        if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOn:
            raise ValueError("VM must be powered on to change NIC connection state")

        # Update connection state
        nic.connectable.connected = connected

        # Create device edit spec
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = nic

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [nic_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "nic_connected" if connected else "nic_disconnected",
            "nic_label": nic_label,
            "connected": connected,
        }

    @mcp_tool(
        name="set_nic_mac",
        description="Set a custom MAC address for a NIC",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def set_nic_mac(
        self,
        vm_name: str,
        nic_label: str,
        mac_address: str,
    ) -> dict[str, Any]:
        """Set a custom MAC address for a NIC.

        Args:
            vm_name: Name of the virtual machine
            nic_label: Label of NIC (e.g., 'Network adapter 1')
            mac_address: MAC address in format XX:XX:XX:XX:XX:XX

        Returns:
            Dict with MAC address change details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        nic = self._find_nic_by_label(vm, nic_label)
        if not nic:
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualEthernetCard)
            ]
            raise ValueError(f"NIC '{nic_label}' not found. Available: {available}")

        # Validate MAC address format
        import re
        if not re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", mac_address):
            raise ValueError(f"Invalid MAC address format: {mac_address}")

        old_mac = nic.macAddress

        # Set manual MAC address
        nic.addressType = "manual"
        nic.macAddress = mac_address

        # Create device edit spec
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        nic_spec.device = nic

        # Create VM config spec
        config_spec = vim.vm.ConfigSpec()
        config_spec.deviceChange = [nic_spec]

        # Reconfigure VM
        task = vm.ReconfigVM_Task(spec=config_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "mac_address_changed",
            "nic_label": nic_label,
            "old_mac": old_mac,
            "new_mac": mac_address,
        }
