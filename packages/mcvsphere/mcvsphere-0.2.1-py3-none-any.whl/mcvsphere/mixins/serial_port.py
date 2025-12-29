"""Serial Port Management - network console access for VMs."""

import random
import socket
import time
from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class SerialPortMixin(MCPMixin):
    """Serial port management for VM network console access.

    Network serial ports allow telnet/TCP connections to VM consoles,
    useful for headless VMs, network appliances, or serial console access.

    Supported protocols:
    - telnet: Telnet over TCP (can negotiate SSL)
    - telnets: Telnet over SSL over TCP
    - tcp: Unencrypted TCP
    - tcp+ssl: Encrypted SSL over TCP
    """

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _get_serial_port(self, vm: vim.VirtualMachine) -> vim.vm.device.VirtualSerialPort | None:
        """Find existing serial port with URI backing on a VM."""
        if not vm.config:
            return None
        for device in vm.config.hardware.device:
            if (
                isinstance(device, vim.vm.device.VirtualSerialPort)
                and isinstance(device.backing, vim.vm.device.VirtualSerialPort.URIBackingInfo)
            ):
                return device
        return None

    def _find_unused_port(self, host_ip: str, start: int = 2000, end: int = 9000) -> int:
        """Find an unused TCP port on the ESXi host."""
        # Try random ports in range until we find one that's available
        attempts = 0
        max_attempts = 50
        while attempts < max_attempts:
            port = random.randint(start, end)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                result = sock.connect_ex((host_ip, port))
                if result != 0:  # Port not in use
                    return port
            except (OSError, TimeoutError):
                return port  # Likely available
            finally:
                sock.close()
            attempts += 1

        raise ValueError(f"Could not find unused port in range {start}-{end}")

    @mcp_tool(
        name="get_serial_port",
        description="Get current serial port configuration for a VM",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_serial_port(self, name: str) -> dict[str, Any]:
        """Get serial port configuration.

        Args:
            name: VM name

        Returns:
            Dict with serial port details or message if not configured
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        serial_port = self._get_serial_port(vm)
        if not serial_port:
            return {
                "configured": False,
                "message": "No network serial port configured",
            }

        backing = serial_port.backing
        return {
            "configured": True,
            "label": serial_port.deviceInfo.label,
            "connected": serial_port.connectable.connected if serial_port.connectable else None,
            "start_connected": serial_port.connectable.startConnected if serial_port.connectable else None,
            "direction": backing.direction if backing else None,
            "service_uri": backing.serviceURI if backing else None,
            "yield_on_poll": serial_port.yieldOnPoll,
        }

    @mcp_tool(
        name="setup_serial_port",
        description="Configure a network serial port on a VM for console access. VM must be powered off.",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def setup_serial_port(
        self,
        name: str,
        protocol: str = "telnet",
        port: int | None = None,
        direction: str = "server",
        yield_on_poll: bool = True,
    ) -> dict[str, Any]:
        """Setup or update network serial port.

        Args:
            name: VM name
            protocol: Protocol to use (telnet, telnets, tcp, tcp+ssl). Default: telnet
            port: TCP port number. If not specified, auto-assigns unused port.
            direction: 'server' (VM listens) or 'client' (VM connects). Default: server
            yield_on_poll: Enable CPU yield behavior. Default: True

        Returns:
            Dict with configured serial port URI and details
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        # Check VM is powered off
        if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOff:
            raise ValueError(f"VM '{name}' must be powered off to configure serial port")

        # Validate protocol
        valid_protocols = ["telnet", "telnets", "tcp", "tcp+ssl", "tcp4", "tcp6"]
        if protocol not in valid_protocols:
            raise ValueError(f"Invalid protocol '{protocol}'. Must be one of: {valid_protocols}")

        # Validate direction
        if direction not in ["server", "client"]:
            raise ValueError("Direction must be 'server' or 'client'")

        # Find or assign port
        if port is None:
            host = vm.runtime.host
            host_ip = host.name if host else self.conn.settings.vcenter_host
            port = self._find_unused_port(host_ip)

        # Build service URI
        service_uri = f"{protocol}://:{port}"

        # Build spec
        serial_spec = vim.vm.device.VirtualDeviceSpec()
        existing_port = self._get_serial_port(vm)

        if existing_port:
            # Edit existing
            serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            serial_spec.device = existing_port
        else:
            # Add new
            serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
            serial_spec.device = vim.vm.device.VirtualSerialPort()

        # Configure backing
        serial_spec.device.yieldOnPoll = yield_on_poll
        serial_spec.device.backing = vim.vm.device.VirtualSerialPort.URIBackingInfo()
        serial_spec.device.backing.direction = direction
        serial_spec.device.backing.serviceURI = service_uri

        # Configure connectable
        serial_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        serial_spec.device.connectable.startConnected = True
        serial_spec.device.connectable.allowGuestControl = True
        serial_spec.device.connectable.connected = False  # Will connect on power on

        # Apply config
        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [serial_spec]
        task = vm.ReconfigVM_Task(spec=spec)
        self.conn.wait_for_task(task)

        # Get ESXi host info for connection string
        host = vm.runtime.host
        host_ip = host.name if host else self.conn.settings.vcenter_host

        return {
            "vm_name": name,
            "service_uri": service_uri,
            "connection_string": f"{protocol}://{host_ip}:{port}",
            "protocol": protocol,
            "port": port,
            "direction": direction,
            "yield_on_poll": yield_on_poll,
            "operation": "updated" if existing_port else "created",
        }

    @mcp_tool(
        name="connect_serial_port",
        description="Connect or disconnect an existing serial port on a VM",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def connect_serial_port(self, name: str, connected: bool = True) -> dict[str, Any]:
        """Connect or disconnect serial port.

        Args:
            name: VM name
            connected: True to connect, False to disconnect. Default: True

        Returns:
            Dict with result
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        serial_port = self._get_serial_port(vm)
        if not serial_port:
            raise ValueError(f"No network serial port configured on VM '{name}'")

        # Build edit spec
        serial_spec = vim.vm.device.VirtualDeviceSpec()
        serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        serial_spec.device = serial_port
        serial_spec.device.connectable.connected = connected

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [serial_spec]
        task = vm.ReconfigVM_Task(spec=spec)
        self.conn.wait_for_task(task)

        return {
            "vm_name": name,
            "connected": connected,
            "service_uri": serial_port.backing.serviceURI if serial_port.backing else None,
        }

    @mcp_tool(
        name="clear_serial_port",
        description="Reset serial port by disconnecting and reconnecting (clears stuck connections)",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def clear_serial_port(self, name: str) -> dict[str, Any]:
        """Clear serial port by cycling connection state.

        Useful for clearing stuck or stale connections.

        Args:
            name: VM name

        Returns:
            Dict with result
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        serial_port = self._get_serial_port(vm)
        if not serial_port:
            raise ValueError(f"No network serial port configured on VM '{name}'")

        # Disconnect
        self.connect_serial_port(name, connected=False)
        time.sleep(1)

        # Reconnect
        self.connect_serial_port(name, connected=True)

        return {
            "vm_name": name,
            "status": "cleared",
            "service_uri": serial_port.backing.serviceURI if serial_port.backing else None,
            "message": "Serial port disconnected and reconnected",
        }

    @mcp_tool(
        name="remove_serial_port",
        description="Remove the network serial port from a VM. VM must be powered off.",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def remove_serial_port(self, name: str) -> str:
        """Remove serial port from VM.

        Args:
            name: VM name

        Returns:
            Success message
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        # Check VM is powered off
        if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOff:
            raise ValueError(f"VM '{name}' must be powered off to remove serial port")

        serial_port = self._get_serial_port(vm)
        if not serial_port:
            return f"No network serial port configured on VM '{name}'"

        # Build remove spec
        serial_spec = vim.vm.device.VirtualDeviceSpec()
        serial_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        serial_spec.device = serial_port

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = [serial_spec]
        task = vm.ReconfigVM_Task(spec=spec)
        self.conn.wait_for_task(task)

        return f"Serial port removed from VM '{name}'"
