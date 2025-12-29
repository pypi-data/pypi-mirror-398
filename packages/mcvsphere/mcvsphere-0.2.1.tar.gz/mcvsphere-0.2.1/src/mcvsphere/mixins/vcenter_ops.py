"""vCenter-specific Operations - Storage vMotion, Templates, Folders, Tasks."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class VCenterOpsMixin(MCPMixin):
    """vCenter-specific operations (require vCenter, not just ESXi)."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    # ─────────────────────────────────────────────────────────────────────────────
    # Storage vMotion (works even on single-host vCenter)
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_tool(
        name="storage_vmotion",
        description="Move a VM's disks to a different datastore (Storage vMotion). Idempotent if already on target.",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def storage_vmotion(
        self,
        vm_name: str,
        target_datastore: str,
        thin_provision: bool | None = None,
    ) -> dict[str, Any]:
        """Move a VM's storage to a different datastore.

        This moves all VM files (disks, config) to the target datastore.
        VM can be running during the migration.

        Args:
            vm_name: Name of the VM to migrate
            target_datastore: Target datastore name
            thin_provision: Convert to thin provisioning (None = keep current)

        Returns:
            Dict with migration details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        ds = self.conn.find_datastore(target_datastore)
        if not ds:
            raise ValueError(f"Datastore '{target_datastore}' not found")

        # Get current datastore
        current_ds = vm.config.files.vmPathName.split("]")[0].strip("[")

        if current_ds == target_datastore:
            return {
                "vm": vm_name,
                "action": "no_migration_needed",
                "message": f"VM is already on datastore '{target_datastore}'",
            }

        # Create relocate spec
        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.datastore = ds

        # Set disk provisioning if specified
        if thin_provision is not None:
            if thin_provision:
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.sparse
            else:
                relocate_spec.transform = vim.vm.RelocateSpec.Transformation.flat

        # Perform the relocation
        task = vm.RelocateVM_Task(spec=relocate_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "storage_vmotion_complete",
            "source_datastore": current_ds,
            "target_datastore": target_datastore,
            "thin_provision": thin_provision,
        }

    @mcp_tool(
        name="move_vm_disk",
        description="Move a specific VM disk to a different datastore",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def move_vm_disk(
        self,
        vm_name: str,
        disk_label: str,
        target_datastore: str,
    ) -> dict[str, Any]:
        """Move a specific VM disk to a different datastore.

        Args:
            vm_name: Name of the VM
            disk_label: Label of the disk (e.g., 'Hard disk 1')
            target_datastore: Target datastore name

        Returns:
            Dict with migration details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        ds = self.conn.find_datastore(target_datastore)
        if not ds:
            raise ValueError(f"Datastore '{target_datastore}' not found")

        # Find the specific disk
        target_disk = None
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualDisk) and device.deviceInfo.label.lower() == disk_label.lower():
                target_disk = device
                break

        if not target_disk:
            available = [
                d.deviceInfo.label
                for d in vm.config.hardware.device
                if isinstance(d, vim.vm.device.VirtualDisk)
            ]
            raise ValueError(f"Disk '{disk_label}' not found. Available: {available}")

        # Get current disk location
        current_path = target_disk.backing.fileName
        current_ds = current_path.split("]")[0].strip("[")

        # Create disk locator for this specific disk
        disk_locator = vim.vm.RelocateSpec.DiskLocator()
        disk_locator.diskId = target_disk.key
        disk_locator.datastore = ds

        # Create relocate spec with just this disk
        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.disk = [disk_locator]

        # Perform the relocation
        task = vm.RelocateVM_Task(spec=relocate_spec)
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "disk_moved",
            "disk": disk_label,
            "source_datastore": current_ds,
            "target_datastore": target_datastore,
        }

    # ─────────────────────────────────────────────────────────────────────────────
    # Template Management
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_tool(
        name="convert_to_template",
        description="Convert a VM to a template (idempotent - safe to call on existing template)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def convert_to_template(self, vm_name: str) -> dict[str, Any]:
        """Convert a VM to a template.

        The VM must be powered off. Once converted, it cannot be powered on
        until converted back to a VM.

        Args:
            vm_name: Name of the VM to convert

        Returns:
            Dict with conversion details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        if vm.runtime.powerState != vim.VirtualMachinePowerState.poweredOff:
            raise ValueError("VM must be powered off to convert to template")

        if vm.config.template:
            return {
                "vm": vm_name,
                "action": "already_template",
                "is_template": True,
            }

        vm.MarkAsTemplate()

        return {
            "vm": vm_name,
            "action": "converted_to_template",
            "is_template": True,
        }

    @mcp_tool(
        name="convert_to_vm",
        description="Convert a template back to a VM (idempotent - safe to call on existing VM)",
        annotations=ToolAnnotations(destructiveHint=True, idempotentHint=True),
    )
    def convert_to_vm(
        self,
        template_name: str,
        resource_pool: str | None = None,
    ) -> dict[str, Any]:
        """Convert a template back to a regular VM.

        Args:
            template_name: Name of the template
            resource_pool: Resource pool for the VM (optional)

        Returns:
            Dict with conversion details
        """
        vm = self.conn.find_vm(template_name)
        if not vm:
            raise ValueError(f"Template '{template_name}' not found")

        if not vm.config.template:
            return {
                "vm": template_name,
                "action": "already_vm",
                "is_template": False,
            }

        # Get resource pool
        if resource_pool:
            pool = self._find_resource_pool(resource_pool)
            if not pool:
                raise ValueError(f"Resource pool '{resource_pool}' not found")
        else:
            pool = self.conn.resource_pool

        # Get a host from the resource pool
        host = None
        if hasattr(pool, "owner") and hasattr(pool.owner, "host"):
            hosts = pool.owner.host
            if hosts:
                host = hosts[0]

        vm.MarkAsVirtualMachine(pool=pool, host=host)

        return {
            "vm": template_name,
            "action": "converted_to_vm",
            "is_template": False,
        }

    def _find_resource_pool(self, name: str) -> vim.ResourcePool | None:
        """Find a resource pool by name."""
        container = self.conn.content.viewManager.CreateContainerView(
            self.conn.content.rootFolder, [vim.ResourcePool], True
        )
        try:
            for pool in container.view:
                if pool.name == name:
                    return pool
        finally:
            container.Destroy()
        return None

    @mcp_tool(
        name="deploy_from_template",
        description="Deploy a new VM from a template",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def deploy_from_template(
        self,
        template_name: str,
        new_vm_name: str,
        datastore: str | None = None,
        power_on: bool = False,
    ) -> dict[str, Any]:
        """Deploy a new VM from a template.

        Args:
            template_name: Name of the template to clone
            new_vm_name: Name for the new VM
            datastore: Target datastore (default: same as template)
            power_on: Power on after deployment (default False)

        Returns:
            Dict with deployment details
        """
        template = self.conn.find_vm(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        if not template.config.template:
            raise ValueError(f"'{template_name}' is not a template")

        # Check if target VM already exists
        if self.conn.find_vm(new_vm_name):
            raise ValueError(f"VM '{new_vm_name}' already exists")

        # Build clone spec
        relocate_spec = vim.vm.RelocateSpec()
        relocate_spec.pool = self.conn.resource_pool

        if datastore:
            ds = self.conn.find_datastore(datastore)
            if not ds:
                raise ValueError(f"Datastore '{datastore}' not found")
            relocate_spec.datastore = ds

        clone_spec = vim.vm.CloneSpec()
        clone_spec.location = relocate_spec
        clone_spec.powerOn = power_on
        clone_spec.template = False  # Create VM, not another template

        # Get target folder
        folder = self.conn.datacenter.vmFolder

        # Clone the template
        task = template.Clone(folder=folder, name=new_vm_name, spec=clone_spec)
        self.conn.wait_for_task(task)

        # Get the new VM info
        new_vm = self.conn.find_vm(new_vm_name)

        return {
            "vm": new_vm_name,
            "action": "deployed_from_template",
            "template": template_name,
            "datastore": datastore or "same as template",
            "power_state": str(new_vm.runtime.powerState) if new_vm else "unknown",
        }

    # ─────────────────────────────────────────────────────────────────────────────
    # Folder Organization
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_tool(
        name="list_folders",
        description="List VM folders in the datacenter",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_folders(self) -> list[dict[str, Any]]:
        """List all VM folders in the datacenter.

        Returns:
            List of folder details
        """
        folders = []

        def _collect_folders(folder: vim.Folder, path: str = ""):
            current_path = f"{path}/{folder.name}" if path else folder.name
            folders.append({
                "name": folder.name,
                "path": current_path,
                "type": "Folder",
                "children": len(folder.childEntity) if hasattr(folder, "childEntity") else 0,
            })

            if hasattr(folder, "childEntity"):
                for child in folder.childEntity:
                    if isinstance(child, vim.Folder):
                        _collect_folders(child, current_path)

        # Start from VM folder
        vm_folder = self.conn.datacenter.vmFolder
        _collect_folders(vm_folder)

        return folders

    @mcp_tool(
        name="create_folder",
        description="Create a new VM folder",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def create_folder(
        self,
        folder_name: str,
        parent_path: str | None = None,
    ) -> dict[str, Any]:
        """Create a new VM folder.

        Args:
            folder_name: Name for the new folder
            parent_path: Path to parent folder (None = root vm folder)

        Returns:
            Dict with folder details
        """
        if parent_path:
            parent = self._find_folder_by_path(parent_path)
            if not parent:
                raise ValueError(f"Parent folder '{parent_path}' not found")
        else:
            parent = self.conn.datacenter.vmFolder

        parent.CreateFolder(name=folder_name)

        return {
            "action": "folder_created",
            "name": folder_name,
            "parent": parent_path or "vm (root)",
            "path": f"{parent_path}/{folder_name}" if parent_path else f"vm/{folder_name}",
        }

    def _find_folder_by_path(self, path: str) -> vim.Folder | None:
        """Find a folder by its path (e.g., 'vm/Production/WebServers')."""
        parts = [p for p in path.split("/") if p and p != "vm"]

        current = self.conn.datacenter.vmFolder
        for part in parts:
            found = None
            if hasattr(current, "childEntity"):
                for child in current.childEntity:
                    if isinstance(child, vim.Folder) and child.name == part:
                        found = child
                        break
            if not found:
                return None
            current = found

        return current

    @mcp_tool(
        name="move_vm_to_folder",
        description="Move a VM to a different folder",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def move_vm_to_folder(
        self,
        vm_name: str,
        folder_path: str,
    ) -> dict[str, Any]:
        """Move a VM to a different folder.

        Args:
            vm_name: Name of the VM to move
            folder_path: Path to target folder

        Returns:
            Dict with move details
        """
        vm = self.conn.find_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found")

        folder = self._find_folder_by_path(folder_path)
        if not folder:
            raise ValueError(f"Folder '{folder_path}' not found")

        # Get current folder
        current_folder = vm.parent.name if vm.parent else "unknown"

        # Move the VM
        task = folder.MoveIntoFolder_Task([vm])
        self.conn.wait_for_task(task)

        return {
            "vm": vm_name,
            "action": "moved_to_folder",
            "from_folder": current_folder,
            "to_folder": folder_path,
        }

    # ─────────────────────────────────────────────────────────────────────────────
    # vCenter Tasks and Events
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_tool(
        name="list_recent_tasks",
        description="List recent tasks from vCenter",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_recent_tasks(
        self,
        max_count: int = 20,
        entity_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """List recent tasks from vCenter.

        Args:
            max_count: Maximum number of tasks to return (default 20)
            entity_name: Filter by entity name (optional)

        Returns:
            List of task details
        """
        task_manager = self.conn.content.taskManager
        recent_tasks = task_manager.recentTask

        tasks = []
        for task in recent_tasks[:max_count]:
            task_info = {
                "key": task.info.key,
                "name": task.info.name or task.info.descriptionId,
                "state": str(task.info.state),
                "progress": task.info.progress,
                "queued_time": str(task.info.queueTime) if task.info.queueTime else None,
                "start_time": str(task.info.startTime) if task.info.startTime else None,
                "complete_time": str(task.info.completeTime) if task.info.completeTime else None,
            }

            # Add entity info if available
            if task.info.entity:
                task_info["entity"] = task.info.entity.name
                task_info["entity_type"] = type(task.info.entity).__name__

            # Add error info if failed
            if task.info.error:
                task_info["error"] = str(task.info.error.msg)

            # Filter by entity if specified
            if entity_name and task.info.entity and task.info.entity.name != entity_name:
                continue

            tasks.append(task_info)

        # Ensure we return something even if empty
        if not tasks:
            return [{"message": "No recent tasks found", "count": 0}]

        return tasks

    @mcp_tool(
        name="list_recent_events",
        description="List recent events from vCenter",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_recent_events(
        self,
        max_count: int = 50,
        event_types: list[str] | None = None,
        hours_back: int = 24,
    ) -> list[dict[str, Any]]:
        """List recent events from vCenter.

        Args:
            max_count: Maximum number of events (default 50)
            event_types: Filter by event type names (optional)
            hours_back: How many hours back to look (default 24)

        Returns:
            List of event details
        """
        event_manager = self.conn.content.eventManager

        # Create filter spec
        filter_spec = vim.event.EventFilterSpec()
        filter_spec.time = vim.event.EventFilterSpec.ByTime()
        filter_spec.time.beginTime = datetime.now() - timedelta(hours=hours_back)

        # Get events
        event_collector = event_manager.CreateCollectorForEvents(filter=filter_spec)
        try:
            events = event_collector.ReadNextEvents(max_count)

            result = []
            for event in events:
                event_info = {
                    "key": event.key,
                    "type": type(event).__name__,
                    "created_time": str(event.createdTime),
                    "message": event.fullFormattedMessage,
                    "user": event.userName if hasattr(event, "userName") else None,
                }

                # Add entity info if available
                if hasattr(event, "vm") and event.vm:
                    event_info["vm"] = event.vm.name
                if hasattr(event, "host") and event.host:
                    event_info["host"] = event.host.name

                # Filter by type if specified
                if event_types and type(event).__name__ not in event_types:
                    continue

                result.append(event_info)

            # Ensure we return something even if empty
            if not result:
                return [{"message": f"No events found in the last {hours_back} hours", "count": 0}]

            return result
        finally:
            event_collector.DestroyCollector()

    # ─────────────────────────────────────────────────────────────────────────────
    # Cluster Operations (for multi-host environments)
    # ─────────────────────────────────────────────────────────────────────────────

    @mcp_tool(
        name="list_clusters",
        description="List all clusters in the datacenter",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_clusters(self) -> list[dict[str, Any]]:
        """List all clusters in the datacenter.

        Returns:
            List of cluster details with DRS/HA status
        """
        clusters = []

        for entity in self.conn.datacenter.hostFolder.childEntity:
            if isinstance(entity, vim.ClusterComputeResource):
                drs_config = entity.configuration.drsConfig
                ha_config = entity.configuration.dasConfig

                clusters.append({
                    "name": entity.name,
                    "host_count": len(entity.host) if entity.host else 0,
                    "total_cpu_mhz": entity.summary.totalCpu,
                    "total_memory_gb": round(entity.summary.totalMemory / (1024**3), 2),
                    "effective_cpu_mhz": entity.summary.effectiveCpu,
                    "effective_memory_gb": round(entity.summary.effectiveMemory / 1024, 2),
                    "drs": {
                        "enabled": drs_config.enabled if drs_config else False,
                        "behavior": str(drs_config.defaultVmBehavior) if drs_config else None,
                    },
                    "ha": {
                        "enabled": ha_config.enabled if ha_config else False,
                        "admission_control": ha_config.admissionControlEnabled if ha_config else False,
                    },
                })

        # Return informative message if no clusters found (standalone host mode)
        if not clusters:
            return [{
                "message": "No clusters found - this appears to be a standalone host or non-clustered environment",
                "count": 0,
            }]

        return clusters

    @mcp_tool(
        name="get_drs_recommendations",
        description="Get DRS recommendations for a cluster",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_drs_recommendations(
        self,
        cluster_name: str,
    ) -> list[dict[str, Any]]:
        """Get DRS recommendations for a cluster.

        Args:
            cluster_name: Name of the cluster

        Returns:
            List of DRS recommendations
        """
        cluster = self._find_cluster(cluster_name)
        if not cluster:
            raise ValueError(f"Cluster '{cluster_name}' not found")

        if not cluster.configuration.drsConfig.enabled:
            return [{
                "message": "DRS is not enabled for this cluster",
                "cluster": cluster_name,
            }]

        recommendations = []
        if hasattr(cluster, "recommendation") and cluster.recommendation:
            for rec in cluster.recommendation:
                rec_info = {
                    "key": rec.key,
                    "reason": rec.reason,
                    "rating": rec.rating,
                    "type": rec.reasonText,
                }

                # Add action details
                if rec.action:
                    rec_info["actions"] = []
                    for action in rec.action:
                        if hasattr(action, "target"):
                            rec_info["actions"].append({
                                "type": type(action).__name__,
                                "target": action.target.name if action.target else "Unknown",
                            })

                recommendations.append(rec_info)

        if not recommendations:
            return [{
                "message": "No DRS recommendations at this time",
                "cluster": cluster_name,
            }]

        return recommendations

    def _find_cluster(self, name: str) -> vim.ClusterComputeResource | None:
        """Find a cluster by name."""
        for entity in self.conn.datacenter.hostFolder.childEntity:
            if isinstance(entity, vim.ClusterComputeResource) and entity.name == name:
                return entity
        return None
