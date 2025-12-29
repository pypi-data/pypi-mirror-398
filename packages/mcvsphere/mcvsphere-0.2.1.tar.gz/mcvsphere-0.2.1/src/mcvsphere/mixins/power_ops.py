"""Power operations - power on/off, shutdown, reset, suspend."""

from typing import TYPE_CHECKING

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class PowerOpsMixin(MCPMixin):
    """VM power management tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    @mcp_tool(
        name="power_on",
        description="Power on a virtual machine",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def power_on(self, name: str) -> str:
        """Power on a virtual machine."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
            return f"VM '{name}' is already powered on"

        task = vm.PowerOnVM_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' powered on"

    @mcp_tool(
        name="power_off",
        description="Power off a virtual machine (hard shutdown, like pulling the power cord)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def power_off(self, name: str) -> str:
        """Power off a virtual machine (hard shutdown)."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
            return f"VM '{name}' is already powered off"

        task = vm.PowerOffVM_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' powered off"

    @mcp_tool(
        name="shutdown_guest",
        description="Gracefully shutdown the guest OS (requires VMware Tools installed and running)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def shutdown_guest(self, name: str) -> str:
        """Gracefully shutdown the guest OS."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
            return f"VM '{name}' is already powered off"

        if vm.guest.toolsRunningStatus != "guestToolsRunning":
            raise RuntimeError(
                f"VMware Tools not running on '{name}'. "
                "Use power_off for hard shutdown instead."
            )

        vm.ShutdownGuest()
        return f"Guest shutdown initiated for VM '{name}'"

    @mcp_tool(
        name="reboot_guest",
        description="Gracefully reboot the guest OS (requires VMware Tools)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False),
    )
    def reboot_guest(self, name: str) -> str:
        """Gracefully reboot the guest OS."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOn:
            raise RuntimeError(f"VM '{name}' is not powered on")

        if vm.guest.toolsRunningStatus != "guestToolsRunning":
            raise RuntimeError(
                f"VMware Tools not running on '{name}'. "
                "Use reset_vm for hard reset instead."
            )

        vm.RebootGuest()
        return f"Guest reboot initiated for VM '{name}'"

    @mcp_tool(
        name="reset_vm",
        description="Reset (hard reboot) a virtual machine - like pressing the reset button",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False),
    )
    def reset_vm(self, name: str) -> str:
        """Reset (hard reboot) a virtual machine."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        task = vm.ResetVM_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' reset"

    @mcp_tool(
        name="suspend_vm",
        description="Suspend a virtual machine (save state to disk)",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def suspend_vm(self, name: str) -> str:
        """Suspend a virtual machine."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if vm.runtime.powerState == vim.VirtualMachine.PowerState.suspended:
            return f"VM '{name}' is already suspended"

        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
            return f"VM '{name}' is powered off, cannot suspend"

        task = vm.SuspendVM_Task()
        self.conn.wait_for_task(task)

        return f"VM '{name}' suspended"

    @mcp_tool(
        name="standby_guest",
        description="Put guest OS into standby mode (requires VMware Tools)",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def standby_guest(self, name: str) -> str:
        """Put guest OS into standby mode."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOn:
            raise RuntimeError(f"VM '{name}' is not powered on")

        if vm.guest.toolsRunningStatus != "guestToolsRunning":
            raise RuntimeError(f"VMware Tools not running on '{name}'")

        vm.StandbyGuest()
        return f"Standby initiated for VM '{name}'"
