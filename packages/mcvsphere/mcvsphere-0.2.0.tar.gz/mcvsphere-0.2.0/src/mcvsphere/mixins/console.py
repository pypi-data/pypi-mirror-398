"""VM Console operations - screenshots and tools monitoring."""

import base64
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import requests
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class ConsoleMixin(MCPMixin):
    """VM console operations - screenshots and VMware Tools monitoring."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    @mcp_tool(
        name="wait_for_vm_tools",
        description="Wait for VMware Tools to become available on a VM. Useful after powering on a VM.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def wait_for_vm_tools(
        self, name: str, timeout: int = 120, poll_interval: int = 5
    ) -> dict[str, Any]:
        """Wait for VMware Tools to become available.

        Args:
            name: VM name
            timeout: Maximum seconds to wait (default: 120)
            poll_interval: Seconds between status checks (default: 5)

        Returns:
            Dict with tools status, version, and guest info when ready
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=timeout)

        while datetime.now() < end_time:
            tools_status = vm.guest.toolsStatus if vm.guest else None

            if tools_status == vim.vm.GuestInfo.ToolsStatus.toolsOk:
                return {
                    "status": "ready",
                    "tools_status": str(tools_status),
                    "tools_version": vm.guest.toolsVersion if vm.guest else None,
                    "tools_running_status": (
                        vm.guest.toolsRunningStatus if vm.guest else None
                    ),
                    "ip_address": vm.guest.ipAddress if vm.guest else None,
                    "hostname": vm.guest.hostName if vm.guest else None,
                    "guest_os": vm.guest.guestFullName if vm.guest else None,
                    "wait_time_seconds": (datetime.now() - start_time).total_seconds(),
                }

            time.sleep(poll_interval)

        # Timeout reached
        return {
            "status": "timeout",
            "tools_status": str(vm.guest.toolsStatus) if vm.guest else None,
            "message": f"VMware Tools not ready after {timeout} seconds",
            "wait_time_seconds": timeout,
        }

    @mcp_tool(
        name="get_vm_tools_status",
        description="Get current VMware Tools status for a VM",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_vm_tools_status(self, name: str) -> dict[str, Any]:
        """Get VMware Tools status without waiting.

        Args:
            name: VM name

        Returns:
            Dict with current tools status and guest info
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        return {
            "tools_status": str(vm.guest.toolsStatus) if vm.guest else None,
            "tools_version": vm.guest.toolsVersion if vm.guest else None,
            "tools_running_status": (
                vm.guest.toolsRunningStatus if vm.guest else None
            ),
            "tools_version_status": (
                str(vm.guest.toolsVersionStatus) if vm.guest else None
            ),
            "ip_address": vm.guest.ipAddress if vm.guest else None,
            "hostname": vm.guest.hostName if vm.guest else None,
            "guest_os": vm.guest.guestFullName if vm.guest else None,
            "guest_id": vm.guest.guestId if vm.guest else None,
            "guest_state": vm.guest.guestState if vm.guest else None,
        }

    @mcp_tool(
        name="vm_screenshot",
        description="Capture a screenshot of the VM console. Returns base64-encoded PNG image.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def vm_screenshot(
        self,
        name: str,
        width: int | None = None,
        height: int | None = None,
    ) -> dict[str, Any]:
        """Capture VM console screenshot via vSphere HTTP API.

        Args:
            name: VM name
            width: Optional width to scale the image
            height: Optional height to scale the image

        Returns:
            Dict with base64-encoded image data and metadata
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        # Build screenshot URL
        # Format: https://{host}/screen?id={moid}
        host = self.conn.settings.vcenter_host
        moid = vm._moId
        screenshot_url = f"https://{host}/screen?id={moid}"

        # Add optional scaling parameters
        params = []
        if width:
            params.append(f"w={width}")
        if height:
            params.append(f"h={height}")
        if params:
            screenshot_url += "&" + "&".join(params)

        # Build auth header
        username = self.conn.settings.vcenter_user
        password = self.conn.settings.vcenter_password.get_secret_value()
        auth = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")

        # Make request
        try:
            response = requests.get(
                screenshot_url,
                headers={"Authorization": f"Basic {auth}"},
                verify=not self.conn.settings.vcenter_insecure,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Failed to capture screenshot: {e}") from e

        # Encode image as base64
        image_data = base64.b64encode(response.content).decode("ascii")
        content_type = response.headers.get("Content-Type", "image/png")

        return {
            "vm_name": name,
            "moid": moid,
            "content_type": content_type,
            "size_bytes": len(response.content),
            "image_base64": image_data,
            "width": width,
            "height": height,
        }
