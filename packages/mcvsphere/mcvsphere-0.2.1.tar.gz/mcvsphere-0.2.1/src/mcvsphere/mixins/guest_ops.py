"""Guest operations - run commands, file transfers (requires VMware Tools)."""

import base64
import time
from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class GuestOpsMixin(MCPMixin):
    """Guest OS operations (requires VMware Tools running in the VM)."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _get_guest_auth(
        self, username: str, password: str
    ) -> vim.vm.guest.NamePasswordAuthentication:
        """Create guest authentication object."""
        return vim.vm.guest.NamePasswordAuthentication(
            username=username,
            password=password,
            interactiveSession=False,
        )

    def _check_tools_running(self, vm: vim.VirtualMachine) -> None:
        """Verify VMware Tools is running."""
        if vm.runtime.powerState != vim.VirtualMachine.PowerState.poweredOn:
            raise RuntimeError(f"VM '{vm.name}' is not powered on")

        if vm.guest.toolsRunningStatus != "guestToolsRunning":
            raise RuntimeError(
                f"VMware Tools not running on '{vm.name}'. "
                "Guest operations require VMware Tools to be installed and running."
            )

    @mcp_tool(
        name="run_command_in_guest",
        description="Execute a command inside a VM's guest OS (requires VMware Tools and guest credentials)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=False),
    )
    def run_command_in_guest(
        self,
        name: str,
        username: str,
        password: str,
        command: str,
        arguments: str = "",
        working_directory: str = "",
        wait_for_completion: bool = True,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        """Run a command in the guest OS.

        Args:
            name: VM name
            username: Guest OS username
            password: Guest OS password
            command: Path to executable (e.g., /bin/bash, cmd.exe)
            arguments: Command arguments (e.g., -c "echo hello")
            working_directory: Working directory for the command
            wait_for_completion: Wait for command to complete
            timeout_seconds: Timeout in seconds (only if waiting)
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        process_manager = guest_ops.processManager
        auth = self._get_guest_auth(username, password)

        # Build program spec
        program_spec = vim.vm.guest.ProcessManager.ProgramSpec(
            programPath=command,
            arguments=arguments,
            workingDirectory=working_directory if working_directory else None,
        )

        # Start the process
        pid = process_manager.StartProgramInGuest(vm, auth, program_spec)

        result = {
            "pid": pid,
            "command": command,
            "arguments": arguments,
            "started": True,
        }

        if wait_for_completion:
            # Poll for completion
            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                processes = process_manager.ListProcessesInGuest(vm, auth, [pid])
                if processes:
                    proc = processes[0]
                    if proc.endTime:
                        result["exit_code"] = proc.exitCode
                        result["completed"] = True
                        result["end_time"] = proc.endTime.isoformat()
                        break
                time.sleep(1)
            else:
                result["completed"] = False
                result["timeout"] = True

        return result

    @mcp_tool(
        name="list_guest_processes",
        description="List running processes in a VM's guest OS",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_guest_processes(
        self, name: str, username: str, password: str
    ) -> list[dict[str, Any]]:
        """List processes running in the guest OS."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        process_manager = guest_ops.processManager
        auth = self._get_guest_auth(username, password)

        processes = process_manager.ListProcessesInGuest(vm, auth, pids=[])

        return [
            {
                "pid": proc.pid,
                "name": proc.name,
                "owner": proc.owner,
                "command": proc.cmdLine,
                "start_time": proc.startTime.isoformat() if proc.startTime else None,
            }
            for proc in processes
        ]

    @mcp_tool(
        name="read_guest_file",
        description="Read a file from a VM's guest OS (returns base64 for binary files)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def read_guest_file(
        self, name: str, username: str, password: str, guest_path: str
    ) -> dict[str, Any]:
        """Read a file from the guest OS.

        Args:
            name: VM name
            username: Guest OS username
            password: Guest OS password
            guest_path: Path to file in guest (e.g., /etc/hosts, C:\\Windows\\System32\\hosts)
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        file_manager = guest_ops.fileManager
        auth = self._get_guest_auth(username, password)

        # Get file attributes first
        try:
            attrs = file_manager.ListFilesInGuest(
                vm, auth, guest_path, matchPattern=None
            )
            if not attrs.files:
                raise ValueError(f"File not found: {guest_path}")
            file_info = attrs.files[0]
        except vim.fault.FileNotFound:
            raise ValueError(f"File not found: {guest_path}") from None

        # Initiate file transfer from guest
        file_transfer = file_manager.InitiateFileTransferFromGuest(
            vm, auth, guest_path
        )

        # Download the file content via the transfer URL
        import ssl
        import urllib.request

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(file_transfer.url, context=context) as response:
            content = response.read()

        # Try to decode as text, fall back to base64
        try:
            text_content = content.decode("utf-8")
            return {
                "path": guest_path,
                "size": file_info.size,
                "content": text_content,
                "encoding": "utf-8",
            }
        except UnicodeDecodeError:
            return {
                "path": guest_path,
                "size": file_info.size,
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            }

    @mcp_tool(
        name="write_guest_file",
        description="Write a file to a VM's guest OS",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def write_guest_file(
        self,
        name: str,
        username: str,
        password: str,
        guest_path: str,
        content: str,
        overwrite: bool = True,
    ) -> str:
        """Write a file to the guest OS.

        Args:
            name: VM name
            username: Guest OS username
            password: Guest OS password
            guest_path: Destination path in guest
            content: File content (text)
            overwrite: Overwrite if exists
        """
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        file_manager = guest_ops.fileManager
        auth = self._get_guest_auth(username, password)

        content_bytes = content.encode("utf-8")

        # Initiate file transfer to guest
        file_attrs = vim.vm.guest.FileManager.FileAttributes()
        transfer_url = file_manager.InitiateFileTransferToGuest(
            vm,
            auth,
            guest_path,
            file_attrs,
            len(content_bytes),
            overwrite,
        )

        # Upload the content
        import ssl
        import urllib.request

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        request = urllib.request.Request(
            transfer_url,
            data=content_bytes,
            method="PUT",
        )
        request.add_header("Content-Type", "application/octet-stream")

        with urllib.request.urlopen(request, context=context):
            pass

        return f"File written to {guest_path} ({len(content_bytes)} bytes)"

    @mcp_tool(
        name="list_guest_directory",
        description="List files in a directory on a VM's guest OS",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_guest_directory(
        self, name: str, username: str, password: str, guest_path: str
    ) -> list[dict[str, Any]]:
        """List files in a guest directory."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        file_manager = guest_ops.fileManager
        auth = self._get_guest_auth(username, password)

        try:
            listing = file_manager.ListFilesInGuest(
                vm, auth, guest_path, matchPattern=None
            )
        except vim.fault.FileNotFound:
            raise ValueError(f"Directory not found: {guest_path}") from None

        results = []
        for f in listing.files:
            mod_time = getattr(f, "modificationTime", None)
            results.append({
                "name": f.path,
                "size": getattr(f, "size", None),
                "type": getattr(f, "type", None),
                "owner": getattr(f, "owner", None),
                "modified": mod_time.isoformat() if mod_time else None,
            })
        return results

    @mcp_tool(
        name="create_guest_directory",
        description="Create a directory in a VM's guest OS",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def create_guest_directory(
        self,
        name: str,
        username: str,
        password: str,
        guest_path: str,
        create_parents: bool = True,
    ) -> str:
        """Create a directory in the guest OS."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        file_manager = guest_ops.fileManager
        auth = self._get_guest_auth(username, password)

        file_manager.MakeDirectoryInGuest(
            vm, auth, guest_path, createParentDirectories=create_parents
        )

        return f"Directory created: {guest_path}"

    @mcp_tool(
        name="delete_guest_file",
        description="Delete a file or directory from a VM's guest OS",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def delete_guest_file(
        self, name: str, username: str, password: str, guest_path: str
    ) -> str:
        """Delete a file or directory from the guest OS."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        self._check_tools_running(vm)

        guest_ops = self.conn.content.guestOperationsManager
        file_manager = guest_ops.fileManager
        auth = self._get_guest_auth(username, password)

        try:
            file_manager.DeleteFileInGuest(vm, auth, guest_path)
            return f"Deleted: {guest_path}"
        except vim.fault.NotAFile:
            # It's a directory
            file_manager.DeleteDirectoryInGuest(vm, auth, guest_path, recursive=True)
            return f"Directory deleted: {guest_path}"
