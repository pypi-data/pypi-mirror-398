"""VMware vSphere connection management."""

import logging
import ssl
from typing import TYPE_CHECKING

from pyVim import connect
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.config import Settings

logger = logging.getLogger(__name__)


class VMwareConnection:
    """Shared VMware vSphere connection for all MCP mixins.

    This class manages the connection to vCenter/ESXi and provides
    common helper methods used across all operation categories.
    """

    def __init__(self, settings: "Settings"):
        self.settings = settings
        self.si: vim.ServiceInstance | None = None
        self.content: vim.ServiceContent | None = None
        self.datacenter: vim.Datacenter | None = None
        self.resource_pool: vim.ResourcePool | None = None
        self.datastore: vim.Datastore | None = None
        self.network: vim.Network | None = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to vCenter/ESXi."""
        try:
            if self.settings.vcenter_insecure:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.si = connect.SmartConnect(
                    host=self.settings.vcenter_host,
                    user=self.settings.vcenter_user,
                    pwd=self.settings.vcenter_password.get_secret_value(),
                    sslContext=context,
                )
            else:
                self.si = connect.SmartConnect(
                    host=self.settings.vcenter_host,
                    user=self.settings.vcenter_user,
                    pwd=self.settings.vcenter_password.get_secret_value(),
                )
        except Exception as e:
            logger.exception("Failed to connect to vCenter/ESXi")
            raise ConnectionError(f"Failed to connect to vCenter/ESXi: {e}") from e

        self.content = self.si.RetrieveContent()
        logger.info("Connected to VMware vCenter/ESXi at %s", self.settings.vcenter_host)

        self._setup_datacenter()
        self._setup_compute_resource()
        self._setup_datastore()
        self._setup_network()

    def _setup_datacenter(self) -> None:
        """Find and configure the target datacenter."""
        datacenters = [
            dc for dc in self.content.rootFolder.childEntity if isinstance(dc, vim.Datacenter)
        ]

        if self.settings.vcenter_datacenter:
            self.datacenter = next(
                (dc for dc in datacenters if dc.name == self.settings.vcenter_datacenter),
                None,
            )
            if not self.datacenter:
                raise ValueError(f"Datacenter '{self.settings.vcenter_datacenter}' not found")
        else:
            self.datacenter = datacenters[0] if datacenters else None

        if not self.datacenter:
            raise ValueError("No datacenter found in vSphere inventory")

        logger.info("Using datacenter: %s", self.datacenter.name)

    def _setup_compute_resource(self) -> None:
        """Find and configure compute resource (cluster or host)."""
        compute_resources = [
            cr
            for cr in self.datacenter.hostFolder.childEntity
            if isinstance(cr, vim.ComputeResource)
        ]

        if self.settings.vcenter_cluster:
            compute_resource = next(
                (
                    cr
                    for cr in compute_resources
                    if isinstance(cr, vim.ClusterComputeResource)
                    and cr.name == self.settings.vcenter_cluster
                ),
                None,
            )
            if not compute_resource:
                raise ValueError(f"Cluster '{self.settings.vcenter_cluster}' not found")
        else:
            compute_resource = compute_resources[0] if compute_resources else None

        if not compute_resource:
            raise ValueError("No compute resource (cluster or host) found")

        self.resource_pool = compute_resource.resourcePool
        logger.info("Using resource pool: %s", self.resource_pool.name)

    def _setup_datastore(self) -> None:
        """Find and configure the target datastore."""
        datastores = [
            ds
            for ds in self.datacenter.datastoreFolder.childEntity
            if isinstance(ds, vim.Datastore)
        ]

        if not datastores:
            raise ValueError("No datastore found in datacenter")

        if self.settings.vcenter_datastore:
            self.datastore = next(
                (ds for ds in datastores if ds.name == self.settings.vcenter_datastore),
                None,
            )
            if not self.datastore:
                raise ValueError(f"Datastore '{self.settings.vcenter_datastore}' not found")
        else:
            self.datastore = max(datastores, key=lambda ds: ds.summary.freeSpace)

        logger.info("Using datastore: %s", self.datastore.name)

    def _setup_network(self) -> None:
        """Find and configure the target network."""
        if not self.settings.vcenter_network:
            self.network = None
            return

        networks = self.datacenter.networkFolder.childEntity
        self.network = next(
            (net for net in networks if net.name == self.settings.vcenter_network),
            None,
        )

        if self.network:
            logger.info("Using network: %s", self.network.name)
        else:
            logger.warning("Network '%s' not found", self.settings.vcenter_network)

    # ─────────────────────────────────────────────────────────────────────────────
    # Helper Methods (shared across mixins)
    # ─────────────────────────────────────────────────────────────────────────────

    def find_vm(self, name: str) -> vim.VirtualMachine | None:
        """Find a virtual machine by name."""
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.VirtualMachine], True
        )
        try:
            return next((vm for vm in container.view if vm.name == name), None)
        finally:
            container.Destroy()

    def get_all_vms(self) -> list[vim.VirtualMachine]:
        """Get all virtual machines."""
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.VirtualMachine], True
        )
        try:
            return list(container.view)
        finally:
            container.Destroy()

    def find_datastore(self, name: str) -> vim.Datastore | None:
        """Find a datastore by name."""
        return next(
            (
                ds
                for ds in self.datacenter.datastoreFolder.childEntity
                if isinstance(ds, vim.Datastore) and ds.name == name
            ),
            None,
        )

    def find_network(self, name: str) -> vim.Network | None:
        """Find a network by name."""
        return next(
            (net for net in self.datacenter.networkFolder.childEntity if net.name == name),
            None,
        )

    def find_host(self, name: str) -> vim.HostSystem | None:
        """Find an ESXi host by name."""
        container = self.content.viewManager.CreateContainerView(
            self.content.rootFolder, [vim.HostSystem], True
        )
        try:
            return next((host for host in container.view if host.name == name), None)
        finally:
            container.Destroy()

    def wait_for_task(self, task: vim.Task) -> None:
        """Wait for a vSphere task to complete."""
        while task.info.state not in (vim.TaskInfo.State.success, vim.TaskInfo.State.error):
            pass
        if task.info.state == vim.TaskInfo.State.error:
            raise RuntimeError(f"Task failed: {task.info.error}")

    def disconnect(self) -> None:
        """Disconnect from vCenter/ESXi."""
        if self.si:
            connect.Disconnect(self.si)
            logger.info("Disconnected from VMware vCenter/ESXi")
