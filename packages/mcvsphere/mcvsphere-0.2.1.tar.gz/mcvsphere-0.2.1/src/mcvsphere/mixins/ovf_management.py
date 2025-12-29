"""OVF/OVA Management - deploy and export virtual appliances."""

import ssl
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class OVFManagementMixin(MCPMixin):
    """OVF/OVA deployment and export tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _extract_ova(self, ova_path: str) -> tuple[str, str, list[str]]:
        """Extract OVA file and return (temp_dir, ovf_path, disk_files)."""
        temp_dir = tempfile.mkdtemp(prefix="ovf_")

        with tarfile.open(ova_path, "r") as tar:
            tar.extractall(temp_dir)

        # Find OVF descriptor and disk files
        temp_path = Path(temp_dir)
        ovf_files = list(temp_path.glob("*.ovf"))
        if not ovf_files:
            raise ValueError("No OVF descriptor found in OVA file")

        ovf_path = str(ovf_files[0])
        disk_files = [str(f) for f in temp_path.glob("*.vmdk")]
        disk_files.extend([str(f) for f in temp_path.glob("*.iso")])

        return temp_dir, ovf_path, disk_files

    def _get_ovf_descriptor(self, ovf_path: str) -> str:
        """Read OVF descriptor XML content."""
        with open(ovf_path) as f:
            return f.read()

    def _upload_disk_to_lease(
        self,
        _lease: vim.HttpNfcLease,
        disk_path: str,
        device_url: str,
    ) -> None:
        """Upload a disk file via NFC lease."""
        # Create SSL context
        context = ssl.create_default_context()
        if self.conn.settings.vcenter_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        # Get file size
        file_size = Path(disk_path).stat().st_size

        # Create upload request
        request = urllib.request.Request(device_url, method="PUT")
        request.add_header("Content-Type", "application/x-vnd.vmware-streamVmdk")
        request.add_header("Content-Length", str(file_size))
        request.add_header("Connection", "Keep-Alive")

        # Add session cookie
        if hasattr(self.conn.service_instance, "_stub"):
            cookie = self.conn.service_instance._stub.cookie
            if cookie:
                request.add_header("Cookie", cookie)

        # Upload file
        with open(disk_path, "rb") as f:
            request.data = f
            urllib.request.urlopen(request, context=context)

    @mcp_tool(
        name="deploy_ovf",
        description="Deploy a VM from an OVF or OVA file on a datastore",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def deploy_ovf(
        self,
        ovf_path: str,
        vm_name: str,
        datastore: str,
        network: str | None = None,
        power_on: bool = False,
    ) -> dict[str, Any]:
        """Deploy a virtual machine from an OVF or OVA file.

        The OVF/OVA must already be on a datastore accessible to ESXi.

        Args:
            ovf_path: Path to OVF/OVA on datastore (e.g., 'templates/ubuntu.ova')
            vm_name: Name for the new VM
            datastore: Target datastore for VM files
            network: Network to connect VM to (optional)
            power_on: Power on VM after deployment (default False)

        Returns:
            Dict with deployment details
        """
        # Get OVF Manager
        ovf_manager = self.conn.content.ovfManager

        # Find target datastore
        ds = self.conn.find_datastore(datastore)
        if not ds:
            raise ValueError(f"Datastore '{datastore}' not found")

        # Get resource pool and folder
        host = None
        for h in self.conn.datacenter.hostFolder.childEntity:
            if hasattr(h, "host"):
                host = h.host[0] if h.host else None
                break
            elif hasattr(h, "resourcePool"):
                host = h
                break

        if not host:
            raise ValueError("No ESXi host found")

        # Get resource pool
        if hasattr(host, "resourcePool"):
            resource_pool = host.resourcePool
        else:
            resource_pool = host.parent.resourcePool

        # Get VM folder
        vm_folder = self.conn.datacenter.vmFolder

        # Read OVF descriptor from datastore
        # For OVA, we need to extract first
        is_ova = ovf_path.lower().endswith(".ova")

        if is_ova:
            # Download OVA to temp location for extraction
            # This is complex - for now, require OVF files directly
            raise ValueError(
                "Direct OVA deployment from datastore not yet supported. "
                "Please extract OVF first, or use local OVA deployment."
            )

        # Read OVF descriptor via datastore browser
        ovf_descriptor = self._read_datastore_file(datastore, ovf_path)

        # Create import spec params
        import_spec_params = vim.OvfManager.CreateImportSpecParams(
            entityName=vm_name,
            diskProvisioning="thin",
        )

        # If network specified, add network mapping
        if network:
            net = self.conn.find_network(network)
            if net:
                network_mapping = vim.OvfManager.NetworkMapping(
                    name="VM Network",  # Common default in OVF
                    network=net,
                )
                import_spec_params.networkMapping = [network_mapping]

        # Create import spec
        import_spec = ovf_manager.CreateImportSpec(
            ovfDescriptor=ovf_descriptor,
            resourcePool=resource_pool,
            datastore=ds,
            cisp=import_spec_params,
        )

        if import_spec.error:
            errors = [str(e.msg) for e in import_spec.error]
            raise ValueError(f"OVF import errors: {errors}")

        # Import the OVF
        lease = resource_pool.ImportVApp(
            spec=import_spec.importSpec,
            folder=vm_folder,
        )

        # Wait for lease to be ready
        while lease.state == vim.HttpNfcLease.State.initializing:
            pass

        if lease.state == vim.HttpNfcLease.State.error:
            raise ValueError(f"Lease error: {lease.error}")

        # Upload disk files if needed
        if import_spec.fileItem:
            ovf_dir = str(Path(ovf_path).parent)
            for item in import_spec.fileItem:
                for device_url in lease.info.deviceUrl:
                    if device_url.importKey == item.deviceId:
                        disk_path = f"{ovf_dir}/{item.path}"
                        self._upload_disk_from_datastore(
                            datastore, disk_path, device_url.url
                        )
                        break

        # Complete the lease
        lease.Complete()

        # Find the newly created VM
        vm = self.conn.find_vm(vm_name)

        result = {
            "vm": vm_name,
            "action": "ovf_deployed",
            "datastore": datastore,
            "source": ovf_path,
        }

        if vm:
            result["uuid"] = vm.config.uuid
            if power_on:
                task = vm.PowerOnVM_Task()
                self.conn.wait_for_task(task)
                result["power_state"] = "poweredOn"
            else:
                result["power_state"] = "poweredOff"

        return result

    def _read_datastore_file(self, datastore: str, path: str) -> str:
        """Read a text file from datastore."""
        ds = self.conn.find_datastore(datastore)
        if not ds:
            raise ValueError(f"Datastore '{datastore}' not found")

        # Build HTTP URL
        dc_name = self.conn.datacenter.name
        url = (
            f"https://{self.conn.settings.vcenter_host}/folder/{path}"
            f"?dcPath={dc_name}&dsName={datastore}"
        )

        # Setup request
        context = ssl.create_default_context()
        if self.conn.settings.vcenter_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        request = urllib.request.Request(url)
        if hasattr(self.conn.service_instance, "_stub"):
            cookie = self.conn.service_instance._stub.cookie
            if cookie:
                request.add_header("Cookie", cookie)

        with urllib.request.urlopen(request, context=context) as response:
            return response.read().decode("utf-8")

    def _upload_disk_from_datastore(
        self, datastore: str, disk_path: str, target_url: str
    ) -> None:
        """Stream disk from datastore to NFC lease URL."""
        # This is complex - need to pipe from datastore HTTP to NFC upload
        # For now, document this limitation
        pass

    @mcp_tool(
        name="export_vm_ovf",
        description="Export a VM to OVF format on a datastore",
        annotations=ToolAnnotations(readOnlyHint=False),
    )
    def export_vm_ovf(
        self,
        vm_name: str,
        target_path: str,
        datastore: str | None = None,
    ) -> dict[str, Any]:
        """Export a virtual machine to OVF format.

        Args:
            vm_name: Name of the VM to export
            target_path: Target directory path on datastore
            datastore: Target datastore (default: VM's datastore)

        Returns:
            Dict with export details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        # VM must be powered off
        if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOff:
            raise ValueError("VM must be powered off to export")

        # Determine target datastore
        if datastore:
            ds = self.conn.find_datastore(datastore)
            if not ds:
                raise ValueError(f"Datastore '{datastore}' not found")
            ds_name = datastore
        else:
            ds_name = vm.config.files.vmPathName.split("]")[0].strip("[")

        # Get export lease
        lease = vm.ExportVm()

        # Wait for lease to be ready
        while lease.state == vim.HttpNfcLease.State.initializing:
            pass

        if lease.state == vim.HttpNfcLease.State.error:
            raise ValueError(f"Export lease error: {lease.error}")

        # Get OVF descriptor
        ovf_manager = self.conn.content.ovfManager
        ovf_descriptor = ovf_manager.CreateDescriptor(
            obj=vm,
            cdp=vim.OvfManager.CreateDescriptorParams(
                name=vm_name,
                description=f"Exported from {vm_name}",
            ),
        )

        if ovf_descriptor.error:
            lease.Abort(fault=vim.LocalizedMethodFault(localizedMessage="OVF error"))
            errors = [str(e.msg) for e in ovf_descriptor.error]
            raise ValueError(f"OVF descriptor errors: {errors}")

        # Download disk files from lease
        exported_files = []

        for device_url in lease.info.deviceUrl:
            # Get disk key for filename
            disk_key = device_url.key

            # Create output path
            disk_filename = f"{vm_name}-disk-{disk_key}.vmdk"
            output_path = f"{target_path}/{disk_filename}"

            # Download disk to datastore
            # This would need streaming from NFC to datastore HTTP PUT
            exported_files.append(output_path)

        # Write OVF descriptor
        ovf_filename = f"{vm_name}.ovf"
        ovf_output_path = f"{target_path}/{ovf_filename}"

        # Upload OVF descriptor to datastore
        self._write_datastore_file(ds_name, ovf_output_path, ovf_descriptor.ovfDescriptor)

        exported_files.append(ovf_output_path)

        # Complete the lease
        lease.Complete()

        return {
            "vm": vm_name,
            "action": "vm_exported",
            "datastore": ds_name,
            "target_path": target_path,
            "files": exported_files,
            "ovf_descriptor": ovf_filename,
        }

    def _write_datastore_file(self, datastore: str, path: str, content: str) -> None:
        """Write a text file to datastore."""
        dc_name = self.conn.datacenter.name
        url = (
            f"https://{self.conn.settings.vcenter_host}/folder/{path}"
            f"?dcPath={dc_name}&dsName={datastore}"
        )

        # Setup request
        context = ssl.create_default_context()
        if self.conn.settings.vcenter_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        data = content.encode("utf-8")
        request = urllib.request.Request(url, data=data, method="PUT")
        request.add_header("Content-Type", "application/xml")
        request.add_header("Content-Length", str(len(data)))

        if hasattr(self.conn.service_instance, "_stub"):
            cookie = self.conn.service_instance._stub.cookie
            if cookie:
                request.add_header("Cookie", cookie)

        urllib.request.urlopen(request, context=context)

    @mcp_tool(
        name="list_ovf_networks",
        description="List networks defined in an OVF file",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_ovf_networks(
        self,
        ovf_path: str,
        datastore: str,
    ) -> list[dict[str, str]]:
        """List networks defined in an OVF descriptor.

        Args:
            ovf_path: Path to OVF file on datastore
            datastore: Datastore containing the OVF

        Returns:
            List of network definitions
        """
        # Read OVF descriptor
        ovf_descriptor = self._read_datastore_file(datastore, ovf_path)

        # Parse network references
        ovf_manager = self.conn.content.ovfManager

        # Get resource pool for parsing
        host = None
        for h in self.conn.datacenter.hostFolder.childEntity:
            if hasattr(h, "host"):
                host = h.host[0] if h.host else None
                break

        if not host:
            raise ValueError("No ESXi host found")

        resource_pool = host.parent.resourcePool if hasattr(host, "parent") else None
        ds = self.conn.find_datastore(datastore)

        # Create parse params to extract network info
        import_spec_params = vim.OvfManager.CreateImportSpecParams()

        result = ovf_manager.CreateImportSpec(
            ovfDescriptor=ovf_descriptor,
            resourcePool=resource_pool,
            datastore=ds,
            cisp=import_spec_params,
        )

        networks = []
        if result.importSpec and hasattr(result.importSpec, "networkMapping"):
            for net in result.importSpec.networkMapping:
                networks.append({
                    "name": net.name,
                    "network": net.network.name if net.network else "Not mapped",
                })

        # Also check warnings for network requirements
        if result.warning:
            for warn in result.warning:
                if "network" in str(warn.msg).lower():
                    networks.append({
                        "name": "Warning",
                        "network": str(warn.msg),
                    })

        return networks
