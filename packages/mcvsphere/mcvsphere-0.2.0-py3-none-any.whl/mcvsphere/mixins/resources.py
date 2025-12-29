"""MCP Resources - datastores, networks, hosts, clusters."""

from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class ResourcesMixin(MCPMixin):
    """MCP Resources for vSphere infrastructure."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    # ─────────────────────────────────────────────────────────────────────────────
    # Datastore File Browser (templated resource)
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_resource(
        uri="datastore://{datastore_name}",
        name="datastore_files",
        description="Browse root files on a datastore (e.g., datastore://c1_ds-02)",
    )
    def browse_datastore_root(self, datastore_name: str) -> list[dict[str, Any]]:
        """Browse files and folders at the root of a datastore."""
        return self._browse_datastore_path(datastore_name, "")

    def _browse_datastore_path(
        self, datastore_name: str, path: str
    ) -> list[dict[str, Any]]:
        """Browse files and folders on a datastore at a given path."""
        ds = self.conn.find_datastore(datastore_name)
        if not ds:
            raise ValueError(f"Datastore '{datastore_name}' not found")

        browser = ds.browser

        # Build the datastore path
        if path and not path.endswith("/"):
            path = path + "/"
        ds_path = f"[{datastore_name}] {path}" if path else f"[{datastore_name}]"

        # Search spec to get file details
        search_spec = vim.host.DatastoreBrowser.SearchSpec()
        search_spec.details = vim.host.DatastoreBrowser.FileInfo.Details(
            fileType=True,
            fileSize=True,
            modification=True,
            fileOwner=False,
        )
        # Match all files
        search_spec.matchPattern = ["*"]

        # Search for files
        task = browser.SearchDatastore_Task(ds_path, search_spec)
        self.conn.wait_for_task(task)

        results = []
        if task.info.result and task.info.result.file:
            for file_info in task.info.result.file:
                file_type = type(file_info).__name__.replace("Info", "")

                entry = {
                    "name": file_info.path,
                    "type": file_type,
                    "size_bytes": file_info.fileSize if file_info.fileSize else 0,
                    "size_human": self._format_size(file_info.fileSize)
                    if file_info.fileSize
                    else "0 B",
                    "modified": file_info.modification.isoformat()
                    if file_info.modification
                    else None,
                }

                # Add type-specific info
                if isinstance(file_info, vim.host.DatastoreBrowser.VmDiskInfo):
                    entry["disk_type"] = file_info.diskType
                    entry["capacity_kb"] = file_info.capacityKb
                    entry["hardware_version"] = file_info.hardwareVersion

                results.append(entry)

        return sorted(results, key=lambda x: (x["type"] != "Folder", x["name"]))

    def _stream_from_esxi(self, datastore: str, path: str, chunk_size: int = 1024 * 1024):
        """Generator that streams file content from ESXi datastore.

        Yields raw bytes chunks as they arrive from ESXi HTTP API.
        Used internally for memory-efficient file transfers.
        """
        import ssl
        import urllib.request
        from urllib.parse import quote

        ds = self.conn.find_datastore(datastore)
        if not ds:
            raise ValueError(f"Datastore '{datastore}' not found")

        # Build download URL
        dc_name = self.conn.datacenter.name
        host = self.conn.settings.vcenter_host
        encoded_path = quote(path, safe="")

        url = (
            f"https://{host}/folder/{encoded_path}"
            f"?dcPath={quote(dc_name)}&dsName={quote(datastore)}"
        )

        # Create SSL context
        context = ssl.create_default_context()
        if self.conn.settings.vcenter_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        # Get session cookie
        stub = self.conn.si._stub
        cookie = stub.cookie

        request = urllib.request.Request(url, method="GET")
        request.add_header("Cookie", cookie)

        try:
            with urllib.request.urlopen(request, context=context) as response:
                # Yield total size first (or None if unknown)
                content_length = response.headers.get("Content-Length")
                yield int(content_length) if content_length else None

                # Then yield chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(f"File not found: [{datastore}] {path}") from e
            raise RuntimeError(f"Download failed: {e.code} {e.reason}") from e

    @mcp_tool(
        name="browse_datastore",
        description="Browse files in a datastore folder (use path='' for root)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def browse_datastore_tool(
        self, datastore: str, path: str = ""
    ) -> list[dict[str, Any]]:
        """Browse files at a specific path on a datastore.

        Args:
            datastore: Datastore name (e.g., c1_ds-02)
            path: Path within datastore (e.g., "rpm-desktop-1/" or "" for root)
        """
        return self._browse_datastore_path(datastore, path)

    @mcp_tool(
        name="download_from_datastore",
        description="Download a file from datastore. Returns content for small files, streams to disk for large files.",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def download_from_datastore(
        self,
        datastore: str,
        path: str,
        save_to: str | None = None,
        max_memory_mb: int = 50,
    ) -> dict[str, Any]:
        """Download a file from a datastore using streaming.

        Streams data from ESXi as it arrives (generator-based).
        For small files: assembles chunks and returns content.
        For large files or save_to: streams directly to disk.

        Args:
            datastore: Datastore name (e.g., c1_ds-02)
            path: Path to file on datastore (e.g., "iso/readme.txt")
            save_to: Local path to save file (recommended for large files)
            max_memory_mb: Max file size in MB to return in response (default 50MB)

        Returns:
            Dict with file content or save confirmation
        """
        import base64

        max_bytes = max_memory_mb * 1024 * 1024
        stream = self._stream_from_esxi(datastore, path)

        # First yield is total size (or None)
        total_size = next(stream)

        if save_to:
            # Stream directly to disk
            bytes_written = 0
            with open(save_to, "wb") as f:
                for chunk in stream:
                    f.write(chunk)
                    bytes_written += len(chunk)

            return {
                "datastore": datastore,
                "path": path,
                "size_bytes": bytes_written,
                "size_human": self._format_size(bytes_written),
                "saved_to": save_to,
            }

        # Check size limit before loading into memory
        if total_size and total_size > max_bytes:
            raise ValueError(
                f"File too large: {self._format_size(total_size)} exceeds {max_memory_mb}MB limit. "
                f"Use save_to parameter to stream to disk."
            )

        # Assemble chunks into memory (with streaming limit check)
        chunks = []
        bytes_read = 0
        for chunk in stream:
            bytes_read += len(chunk)
            if bytes_read > max_bytes:
                raise ValueError(
                    f"File exceeded {max_memory_mb}MB limit during streaming. "
                    f"Use save_to parameter for large files."
                )
            chunks.append(chunk)

        content = b"".join(chunks)

        # Try to decode as text, fall back to base64
        try:
            return {
                "datastore": datastore,
                "path": path,
                "size_bytes": len(content),
                "size_human": self._format_size(len(content)),
                "encoding": "utf-8",
                "content": content.decode("utf-8"),
            }
        except UnicodeDecodeError:
            return {
                "datastore": datastore,
                "path": path,
                "size_bytes": len(content),
                "size_human": self._format_size(len(content)),
                "encoding": "base64",
                "content": base64.b64encode(content).decode("ascii"),
            }

    @mcp_tool(
        name="upload_to_datastore",
        description="Upload a file to a datastore from local path or base64 content. Streams large files from disk.",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def upload_to_datastore(
        self,
        datastore: str,
        remote_path: str,
        local_path: str | None = None,
        content_base64: str | None = None,
        chunk_size: int = 8 * 1024 * 1024,  # 8MB chunks
    ) -> dict[str, Any]:
        """Upload a file to a datastore.

        For local_path: streams from disk in chunks (memory efficient for large files)
        For content_base64: decodes and uploads (use for small files only)

        Args:
            datastore: Datastore name (e.g., c1_ds-02)
            remote_path: Destination path on datastore (e.g., "iso/myfile.iso")
            local_path: Local file path to upload - streams from disk (preferred for large files)
            content_base64: Base64-encoded file content (for small files only)
            chunk_size: Chunk size for streaming uploads (default 8MB)

        Returns:
            Dict with upload details including size and whether streaming was used
        """
        import base64
        import os
        import ssl
        import urllib.request

        if not local_path and not content_base64:
            raise ValueError("Either local_path or content_base64 must be provided")
        if local_path and content_base64:
            raise ValueError("Only one of local_path or content_base64 can be provided")

        ds = self.conn.find_datastore(datastore)
        if not ds:
            raise ValueError(f"Datastore '{datastore}' not found")

        # Build upload URL
        dc_name = self.conn.datacenter.name
        host = self.conn.settings.vcenter_host

        from urllib.parse import quote
        encoded_path = quote(remote_path, safe="")

        url = (
            f"https://{host}/folder/{encoded_path}"
            f"?dcPath={quote(dc_name)}&dsName={quote(datastore)}"
        )

        # Create SSL context
        context = ssl.create_default_context()
        if self.conn.settings.vcenter_insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        # Get session cookie from existing connection
        stub = self.conn.si._stub
        cookie = stub.cookie

        if local_path:
            # Stream from disk - never load entire file into memory
            if not os.path.exists(local_path):
                raise ValueError(f"Local file not found: {local_path}")

            file_size = os.path.getsize(local_path)

            # Use a file-like wrapper that reads in chunks
            class StreamingFileReader:
                """File wrapper that streams content for HTTP upload."""

                def __init__(self, filepath: str, chunk_sz: int):
                    self.filepath = filepath
                    self.chunk_size = chunk_sz
                    self.file_size = os.path.getsize(filepath)
                    self._file = None

                def __len__(self) -> int:
                    return self.file_size

                def read(self, size: int = -1) -> bytes:
                    if self._file is None:
                        self._file = open(self.filepath, "rb")  # noqa: SIM115
                    if size == -1:
                        size = self.chunk_size
                    return self._file.read(size)

                def close(self) -> None:
                    if self._file:
                        self._file.close()

            streamer = StreamingFileReader(local_path, chunk_size)
            try:
                request = urllib.request.Request(url, data=streamer, method="PUT")
                request.add_header("Content-Type", "application/octet-stream")
                request.add_header("Content-Length", str(file_size))
                request.add_header("Cookie", cookie)

                with urllib.request.urlopen(request, context=context) as response:
                    if response.status not in (200, 201):
                        raise RuntimeError(f"Upload failed with status {response.status}")
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"Upload failed: {e.code} {e.reason}") from e
            finally:
                streamer.close()

            return {
                "datastore": datastore,
                "path": remote_path,
                "size_bytes": file_size,
                "size_human": self._format_size(file_size),
                "source": local_path,
                "streamed": True,
            }

        else:
            # Base64 content - small files only
            content = base64.b64decode(content_base64)
            file_size = len(content)

            request = urllib.request.Request(url, data=content, method="PUT")
            request.add_header("Content-Type", "application/octet-stream")
            request.add_header("Content-Length", str(file_size))
            request.add_header("Cookie", cookie)

            try:
                with urllib.request.urlopen(request, context=context) as response:
                    if response.status not in (200, 201):
                        raise RuntimeError(f"Upload failed with status {response.status}")
            except urllib.error.HTTPError as e:
                raise RuntimeError(f"Upload failed: {e.code} {e.reason}") from e

            return {
                "datastore": datastore,
                "path": remote_path,
                "size_bytes": file_size,
                "size_human": self._format_size(file_size),
                "source": "base64",
                "streamed": False,
            }

    @mcp_tool(
        name="delete_datastore_file",
        description="Delete a file or folder from a datastore",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def delete_datastore_file(self, datastore: str, path: str) -> str:
        """Delete a file or folder from a datastore.

        Args:
            datastore: Datastore name
            path: Path to file or folder to delete (e.g., "iso/old-file.iso")

        Returns:
            Success message
        """
        ds = self.conn.find_datastore(datastore)
        if not ds:
            raise ValueError(f"Datastore '{datastore}' not found")

        # Build full datastore path
        ds_path = f"[{datastore}] {path}"

        # Use FileManager to delete
        file_manager = self.conn.content.fileManager
        dc = self.conn.datacenter

        task = file_manager.DeleteDatastoreFile_Task(name=ds_path, datacenter=dc)
        self.conn.wait_for_task(task)

        return f"Deleted [{datastore}] {path}"

    @mcp_tool(
        name="create_datastore_folder",
        description="Create a folder on a datastore",
        annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
    )
    def create_datastore_folder(self, datastore: str, path: str) -> str:
        """Create a folder on a datastore.

        Args:
            datastore: Datastore name
            path: Folder path to create (e.g., "iso/new-folder")

        Returns:
            Success message
        """
        ds = self.conn.find_datastore(datastore)
        if not ds:
            raise ValueError(f"Datastore '{datastore}' not found")

        # Build full datastore path
        ds_path = f"[{datastore}] {path}"

        # Use FileManager to create directory
        file_manager = self.conn.content.fileManager
        file_manager.MakeDirectory(name=ds_path, datacenter=self.conn.datacenter)

        return f"Created folder [{datastore}] {path}"

    def _format_size(self, size_bytes: int | None) -> str:
        """Format bytes to human readable size."""
        if not size_bytes:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(size_bytes) < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    @mcp_tool(
        name="move_datastore_file",
        description="Move/rename a file or folder on a datastore",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def move_datastore_file(
        self,
        source_datastore: str,
        source_path: str,
        dest_datastore: str | None = None,
        dest_path: str | None = None,
    ) -> dict[str, Any]:
        """Move or rename a file or folder on a datastore.

        Args:
            source_datastore: Source datastore name
            source_path: Source path (e.g., "iso/old-name.iso")
            dest_datastore: Destination datastore (default: same as source)
            dest_path: Destination path (default: same as source with new name)

        Returns:
            Dict with move operation details
        """
        ds = self.conn.find_datastore(source_datastore)
        if not ds:
            raise ValueError(f"Datastore '{source_datastore}' not found")

        # Default to same datastore if not specified
        if not dest_datastore:
            dest_datastore = source_datastore
        else:
            dest_ds = self.conn.find_datastore(dest_datastore)
            if not dest_ds:
                raise ValueError(f"Destination datastore '{dest_datastore}' not found")

        if not dest_path:
            dest_path = source_path

        # Build full paths
        source_ds_path = f"[{source_datastore}] {source_path}"
        dest_ds_path = f"[{dest_datastore}] {dest_path}"

        # Use FileManager to move
        file_manager = self.conn.content.fileManager
        dc = self.conn.datacenter

        task = file_manager.MoveDatastoreFile_Task(
            sourceName=source_ds_path,
            sourceDatacenter=dc,
            destinationName=dest_ds_path,
            destinationDatacenter=dc,
            force=False,
        )
        self.conn.wait_for_task(task)

        return {
            "action": "moved",
            "source": source_ds_path,
            "destination": dest_ds_path,
        }

    @mcp_tool(
        name="copy_datastore_file",
        description="Copy a file or folder on a datastore",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def copy_datastore_file(
        self,
        source_datastore: str,
        source_path: str,
        dest_datastore: str | None = None,
        dest_path: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Copy a file or folder on a datastore.

        Args:
            source_datastore: Source datastore name
            source_path: Source path (e.g., "iso/original.iso")
            dest_datastore: Destination datastore (default: same as source)
            dest_path: Destination path (required)
            force: Overwrite destination if exists (default False)

        Returns:
            Dict with copy operation details
        """
        ds = self.conn.find_datastore(source_datastore)
        if not ds:
            raise ValueError(f"Datastore '{source_datastore}' not found")

        # Default to same datastore if not specified
        if not dest_datastore:
            dest_datastore = source_datastore
        else:
            dest_ds = self.conn.find_datastore(dest_datastore)
            if not dest_ds:
                raise ValueError(f"Destination datastore '{dest_datastore}' not found")

        if not dest_path:
            raise ValueError("dest_path is required for copy operation")

        # Build full paths
        source_ds_path = f"[{source_datastore}] {source_path}"
        dest_ds_path = f"[{dest_datastore}] {dest_path}"

        # Use FileManager to copy
        file_manager = self.conn.content.fileManager
        dc = self.conn.datacenter

        task = file_manager.CopyDatastoreFile_Task(
            sourceName=source_ds_path,
            sourceDatacenter=dc,
            destinationName=dest_ds_path,
            destinationDatacenter=dc,
            force=force,
        )
        self.conn.wait_for_task(task)

        return {
            "action": "copied",
            "source": source_ds_path,
            "destination": dest_ds_path,
            "force": force,
        }

    # ─────────────────────────────────────────────────────────────────────────────
    # MCP Resources (read-only data exposed as URIs)
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_resource(
        uri="esxi://vms",
        name="vm_list",
        description="List of all virtual machines with power state",
    )
    def resource_vm_list(self) -> list[dict[str, Any]]:
        """Get list of all VMs with basic info."""
        return [
            {
                "name": vm.name,
                "power_state": str(vm.runtime.powerState),
                "guest_os": vm.config.guestFullName if vm.config else None,
            }
            for vm in self.conn.get_all_vms()
        ]

    @mcp_resource(
        uri="esxi://datastores",
        name="datastore_list",
        description="List of all datastores with capacity information",
    )
    def resource_datastore_list(self) -> list[dict[str, Any]]:
        """Get list of datastores with capacity information."""
        datastores = [
            ds
            for ds in self.conn.datacenter.datastoreFolder.childEntity
            if isinstance(ds, vim.Datastore)
        ]
        return [
            {
                "name": ds.name,
                "capacity_gb": round(ds.summary.capacity / (1024**3), 2),
                "free_gb": round(ds.summary.freeSpace / (1024**3), 2),
                "used_percent": round(
                    (1 - ds.summary.freeSpace / ds.summary.capacity) * 100, 1
                )
                if ds.summary.capacity
                else 0,
                "type": ds.summary.type,
                "accessible": ds.summary.accessible,
            }
            for ds in datastores
        ]

    @mcp_resource(
        uri="esxi://networks",
        name="network_list",
        description="List of all available networks",
    )
    def resource_network_list(self) -> list[dict[str, Any]]:
        """Get list of available networks."""
        networks = []
        for net in self.conn.datacenter.networkFolder.childEntity:
            net_info = {"name": net.name, "type": type(net).__name__}

            if isinstance(net, vim.dvs.DistributedVirtualPortgroup):
                net_info["vlan"] = getattr(net.config.defaultPortConfig.vlan, "vlanId", None)
                net_info["switch"] = net.config.distributedVirtualSwitch.name

            networks.append(net_info)
        return networks

    @mcp_resource(
        uri="esxi://hosts",
        name="host_list",
        description="List of all ESXi hosts",
    )
    def resource_host_list(self) -> list[dict[str, Any]]:
        """Get list of ESXi hosts."""
        container = self.conn.content.viewManager.CreateContainerView(
            self.conn.content.rootFolder, [vim.HostSystem], True
        )
        try:
            return [
                {
                    "name": host.name,
                    "connection_state": str(host.summary.runtime.connectionState),
                    "power_state": str(host.summary.runtime.powerState),
                    "cpu_cores": host.summary.hardware.numCpuCores,
                    "memory_gb": round(host.summary.hardware.memorySize / (1024**3), 2),
                }
                for host in container.view
            ]
        finally:
            container.Destroy()

    @mcp_resource(
        uri="esxi://clusters",
        name="cluster_list",
        description="List of all clusters with DRS/HA status",
    )
    def resource_cluster_list(self) -> list[dict[str, Any]]:
        """Get list of clusters."""
        clusters = [
            cr
            for cr in self.conn.datacenter.hostFolder.childEntity
            if isinstance(cr, vim.ClusterComputeResource)
        ]
        return [
            {
                "name": cluster.name,
                "host_count": len(cluster.host) if cluster.host else 0,
                "total_cpu_cores": cluster.summary.numCpuCores,
                "total_memory_gb": round(
                    cluster.summary.totalMemory / (1024**3), 2
                )
                if cluster.summary.totalMemory
                else 0,
                "drs_enabled": cluster.configuration.drsConfig.enabled
                if cluster.configuration.drsConfig
                else False,
                "ha_enabled": cluster.configuration.dasConfig.enabled
                if cluster.configuration.dasConfig
                else False,
            }
            for cluster in clusters
        ]

    # ─────────────────────────────────────────────────────────────────────────────
    # Tools for detailed resource information
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_tool(
        name="get_datastore_info",
        description="Get detailed information about a specific datastore",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_datastore_info(self, name: str) -> dict[str, Any]:
        """Get detailed datastore information."""
        ds = self.conn.find_datastore(name)
        if not ds:
            raise ValueError(f"Datastore '{name}' not found")

        summary = ds.summary

        # Get VMs on this datastore
        vm_names = [vm.name for vm in ds.vm] if ds.vm else []

        return {
            "name": ds.name,
            "type": summary.type,
            "capacity_gb": round(summary.capacity / (1024**3), 2),
            "free_gb": round(summary.freeSpace / (1024**3), 2),
            "used_gb": round((summary.capacity - summary.freeSpace) / (1024**3), 2),
            "used_percent": round(
                (1 - summary.freeSpace / summary.capacity) * 100, 1
            )
            if summary.capacity
            else 0,
            "accessible": summary.accessible,
            "maintenance_mode": summary.maintenanceMode,
            "url": summary.url,
            "vm_count": len(vm_names),
            "vms": vm_names[:20],  # Limit to first 20
        }

    @mcp_tool(
        name="get_network_info",
        description="Get detailed information about a specific network",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_network_info(self, name: str) -> dict[str, Any]:
        """Get detailed network information."""
        net = self.conn.find_network(name)
        if not net:
            raise ValueError(f"Network '{name}' not found")

        info = {
            "name": net.name,
            "type": type(net).__name__,
            "vm_count": len(net.vm) if net.vm else 0,
            "host_count": len(net.host) if hasattr(net, "host") and net.host else 0,
        }

        if isinstance(net, vim.dvs.DistributedVirtualPortgroup):
            config = net.config
            info["switch"] = config.distributedVirtualSwitch.name
            info["port_binding"] = config.type
            info["num_ports"] = config.numPorts

            if hasattr(config.defaultPortConfig, "vlan"):
                vlan = config.defaultPortConfig.vlan
                if hasattr(vlan, "vlanId"):
                    info["vlan_id"] = vlan.vlanId

        return info

    @mcp_tool(
        name="get_resource_pool_info",
        description="Get information about resource pools",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_resource_pool_info(self, name: str | None = None) -> dict[str, Any]:
        """Get resource pool information.

        If name is not provided, returns info for the default resource pool.
        """
        if name:
            container = self.conn.content.viewManager.CreateContainerView(
                self.conn.content.rootFolder, [vim.ResourcePool], True
            )
            try:
                pool = next((p for p in container.view if p.name == name), None)
            finally:
                container.Destroy()
            if not pool:
                raise ValueError(f"Resource pool '{name}' not found")
        else:
            pool = self.conn.resource_pool

        runtime = pool.summary.runtime
        config = pool.summary.config

        return {
            "name": pool.name,
            "cpu_reservation_mhz": config.cpuAllocation.reservation,
            "cpu_limit_mhz": config.cpuAllocation.limit,
            "cpu_expandable": config.cpuAllocation.expandableReservation,
            "cpu_usage_mhz": runtime.cpu.overallUsage if runtime.cpu else 0,
            "memory_reservation_mb": config.memoryAllocation.reservation,
            "memory_limit_mb": config.memoryAllocation.limit,
            "memory_expandable": config.memoryAllocation.expandableReservation,
            "memory_usage_mb": runtime.memory.overallUsage if runtime.memory else 0,
            "vm_count": len(pool.vm) if pool.vm else 0,
        }

    @mcp_tool(
        name="list_templates",
        description="List all VM templates in the inventory",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_templates(self) -> list[dict[str, Any]]:
        """List all VM templates."""
        templates = []
        for vm in self.conn.get_all_vms():
            if vm.config and vm.config.template:
                templates.append(
                    {
                        "name": vm.name,
                        "guest_os": vm.config.guestFullName,
                        "cpu": vm.config.hardware.numCPU,
                        "memory_mb": vm.config.hardware.memoryMB,
                    }
                )
        return templates

    @mcp_tool(
        name="get_vcenter_info",
        description="Get vCenter/ESXi server information",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_vcenter_info(self) -> dict[str, Any]:
        """Get vCenter/ESXi server information."""
        about = self.conn.content.about
        return {
            "name": about.name,
            "full_name": about.fullName,
            "vendor": about.vendor,
            "version": about.version,
            "build": about.build,
            "os_type": about.osType,
            "api_type": about.apiType,
            "api_version": about.apiVersion,
            "instance_uuid": about.instanceUuid,
        }
