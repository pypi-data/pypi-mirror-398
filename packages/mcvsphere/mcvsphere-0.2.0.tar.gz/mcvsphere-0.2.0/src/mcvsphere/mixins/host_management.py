"""ESXi Host Management - maintenance mode, services, NTP, and host configuration."""

from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class HostManagementMixin(MCPMixin):
    """ESXi host management tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    def _get_host(self) -> vim.HostSystem:
        """Get the ESXi host system."""
        for entity in self.conn.datacenter.hostFolder.childEntity:
            if isinstance(entity, vim.ComputeResource):
                if entity.host:
                    return entity.host[0]
            elif isinstance(entity, vim.HostSystem):
                return entity
        raise ValueError("No ESXi host found")

    @mcp_tool(
        name="get_host_info",
        description="Get detailed information about the ESXi host",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_host_info(self) -> dict[str, Any]:
        """Get detailed ESXi host information.

        Returns:
            Dict with host details including hardware, software, and status
        """
        host = self._get_host()
        summary = host.summary
        hardware = summary.hardware
        config = summary.config

        return {
            "name": config.name,
            "uuid": hardware.uuid,
            "product": {
                "name": config.product.name,
                "version": config.product.version,
                "build": config.product.build,
                "full_name": config.product.fullName,
            },
            "hardware": {
                "vendor": hardware.vendor,
                "model": hardware.model,
                "cpu_model": hardware.cpuModel,
                "cpu_cores": hardware.numCpuCores,
                "cpu_threads": hardware.numCpuThreads,
                "cpu_mhz": hardware.cpuMhz,
                "memory_gb": round(hardware.memorySize / (1024**3), 2),
                "nics": hardware.numNics,
                "hbas": hardware.numHBAs,
            },
            "status": {
                "power_state": str(host.runtime.powerState),
                "connection_state": str(host.runtime.connectionState),
                "maintenance_mode": host.runtime.inMaintenanceMode,
                "uptime_seconds": host.summary.quickStats.uptime,
                "boot_time": str(host.runtime.bootTime) if host.runtime.bootTime else None,
            },
            "management_ip": getattr(config, "managementServerIp", None),
        }

    @mcp_tool(
        name="enter_maintenance_mode",
        description="Put ESXi host into maintenance mode",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def enter_maintenance_mode(
        self,
        evacuate_vms: bool = True,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        """Put ESXi host into maintenance mode.

        Args:
            evacuate_vms: Evacuate/suspend VMs before entering (default True)
            timeout_seconds: Timeout for the operation (default 300)

        Returns:
            Dict with operation result
        """
        host = self._get_host()

        if host.runtime.inMaintenanceMode:
            return {
                "host": host.name,
                "action": "already_in_maintenance_mode",
                "maintenance_mode": True,
            }

        # Enter maintenance mode
        task = host.EnterMaintenanceMode_Task(
            timeout=timeout_seconds,
            evacuatePoweredOffVms=evacuate_vms,
        )
        self.conn.wait_for_task(task)

        return {
            "host": host.name,
            "action": "entered_maintenance_mode",
            "maintenance_mode": True,
            "evacuate_vms": evacuate_vms,
        }

    @mcp_tool(
        name="exit_maintenance_mode",
        description="Exit ESXi host from maintenance mode",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def exit_maintenance_mode(
        self,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        """Exit ESXi host from maintenance mode.

        Args:
            timeout_seconds: Timeout for the operation (default 300)

        Returns:
            Dict with operation result
        """
        host = self._get_host()

        if not host.runtime.inMaintenanceMode:
            return {
                "host": host.name,
                "action": "not_in_maintenance_mode",
                "maintenance_mode": False,
            }

        task = host.ExitMaintenanceMode_Task(timeout=timeout_seconds)
        self.conn.wait_for_task(task)

        return {
            "host": host.name,
            "action": "exited_maintenance_mode",
            "maintenance_mode": False,
        }

    @mcp_tool(
        name="list_services",
        description="List all services on the ESXi host",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_services(self) -> list[dict[str, Any]]:
        """List all services on the ESXi host.

        Returns:
            List of service details
        """
        host = self._get_host()
        service_system = host.configManager.serviceSystem

        services = []
        for service in service_system.serviceInfo.service:
            services.append({
                "key": service.key,
                "label": service.label,
                "policy": service.policy,
                "running": service.running,
                "required": service.required,
                "uninstallable": service.uninstallable,
            })

        return services

    @mcp_tool(
        name="start_service",
        description="Start a service on the ESXi host",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def start_service(self, service_key: str) -> dict[str, Any]:
        """Start a service on the ESXi host.

        Args:
            service_key: Service key (e.g., 'TSM-SSH', 'ntpd', 'sfcbd')

        Returns:
            Dict with operation result
        """
        host = self._get_host()
        service_system = host.configManager.serviceSystem

        # Verify service exists
        service_found = None
        for service in service_system.serviceInfo.service:
            if service.key == service_key:
                service_found = service
                break

        if not service_found:
            available = [s.key for s in service_system.serviceInfo.service]
            raise ValueError(f"Service '{service_key}' not found. Available: {available}")

        if service_found.running:
            return {
                "host": host.name,
                "service": service_key,
                "action": "already_running",
                "running": True,
            }

        service_system.StartService(id=service_key)

        return {
            "host": host.name,
            "service": service_key,
            "action": "started",
            "running": True,
        }

    @mcp_tool(
        name="stop_service",
        description="Stop a service on the ESXi host",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def stop_service(self, service_key: str) -> dict[str, Any]:
        """Stop a service on the ESXi host.

        Args:
            service_key: Service key (e.g., 'TSM-SSH', 'ntpd')

        Returns:
            Dict with operation result
        """
        host = self._get_host()
        service_system = host.configManager.serviceSystem

        # Verify service exists
        service_found = None
        for service in service_system.serviceInfo.service:
            if service.key == service_key:
                service_found = service
                break

        if not service_found:
            available = [s.key for s in service_system.serviceInfo.service]
            raise ValueError(f"Service '{service_key}' not found. Available: {available}")

        if not service_found.running:
            return {
                "host": host.name,
                "service": service_key,
                "action": "already_stopped",
                "running": False,
            }

        service_system.StopService(id=service_key)

        return {
            "host": host.name,
            "service": service_key,
            "action": "stopped",
            "running": False,
        }

    @mcp_tool(
        name="set_service_policy",
        description="Set the startup policy for a service",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def set_service_policy(
        self,
        service_key: str,
        policy: str,
    ) -> dict[str, Any]:
        """Set the startup policy for a service.

        Args:
            service_key: Service key (e.g., 'TSM-SSH', 'ntpd')
            policy: Startup policy - 'on' (auto), 'off' (manual), 'automatic'

        Returns:
            Dict with operation result
        """
        host = self._get_host()
        service_system = host.configManager.serviceSystem

        valid_policies = ["on", "off", "automatic"]
        if policy not in valid_policies:
            raise ValueError(f"Invalid policy '{policy}'. Valid: {valid_policies}")

        # Verify service exists
        service_found = None
        for service in service_system.serviceInfo.service:
            if service.key == service_key:
                service_found = service
                break

        if not service_found:
            available = [s.key for s in service_system.serviceInfo.service]
            raise ValueError(f"Service '{service_key}' not found. Available: {available}")

        old_policy = service_found.policy
        service_system.UpdateServicePolicy(id=service_key, policy=policy)

        return {
            "host": host.name,
            "service": service_key,
            "action": "policy_updated",
            "old_policy": old_policy,
            "new_policy": policy,
        }

    @mcp_tool(
        name="get_ntp_config",
        description="Get NTP configuration for the ESXi host",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_ntp_config(self) -> dict[str, Any]:
        """Get NTP configuration for the ESXi host.

        Returns:
            Dict with NTP configuration
        """
        host = self._get_host()
        datetime_system = host.configManager.dateTimeSystem

        ntp_config = datetime_system.dateTimeInfo.ntpConfig

        # Get ntpd service status
        service_system = host.configManager.serviceSystem
        ntpd_running = False
        ntpd_policy = "unknown"
        for service in service_system.serviceInfo.service:
            if service.key == "ntpd":
                ntpd_running = service.running
                ntpd_policy = service.policy
                break

        return {
            "host": host.name,
            "ntp_servers": list(ntp_config.server) if ntp_config else [],
            "service_running": ntpd_running,
            "service_policy": ntpd_policy,
            "current_time": str(datetime_system.QueryDateTime()),
            "timezone": datetime_system.dateTimeInfo.timeZone.name,
        }

    @mcp_tool(
        name="configure_ntp",
        description="Configure NTP servers for the ESXi host",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def configure_ntp(
        self,
        ntp_servers: list[str],
        start_service: bool = True,
    ) -> dict[str, Any]:
        """Configure NTP servers for the ESXi host.

        Args:
            ntp_servers: List of NTP server addresses
            start_service: Start ntpd service after configuring (default True)

        Returns:
            Dict with configuration result
        """
        host = self._get_host()
        datetime_system = host.configManager.dateTimeSystem

        # Create NTP config
        ntp_config = vim.host.NtpConfig(server=ntp_servers)

        # Create DateTime config
        datetime_config = vim.host.DateTimeConfig(ntpConfig=ntp_config)

        # Apply configuration
        datetime_system.UpdateDateTimeConfig(config=datetime_config)

        result = {
            "host": host.name,
            "action": "ntp_configured",
            "ntp_servers": ntp_servers,
        }

        if start_service:
            # Restart ntpd to pick up new config
            service_system = host.configManager.serviceSystem
            try:
                service_system.RestartService(id="ntpd")
                result["service_restarted"] = True
            except Exception:
                # Service might not be running, try to start it
                try:
                    service_system.StartService(id="ntpd")
                    result["service_started"] = True
                except Exception as e:
                    result["service_error"] = str(e)

        return result

    @mcp_tool(
        name="reboot_host",
        description="Reboot the ESXi host (requires maintenance mode)",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def reboot_host(self, force: bool = False) -> dict[str, Any]:
        """Reboot the ESXi host.

        Args:
            force: Force reboot even if VMs are running (dangerous!)

        Returns:
            Dict with operation result
        """
        host = self._get_host()

        if not host.runtime.inMaintenanceMode and not force:
            raise ValueError(
                "Host must be in maintenance mode to reboot. "
                "Use enter_maintenance_mode first, or set force=True (dangerous!)."
            )

        host.RebootHost_Task(force=force)
        # Don't wait for task - host will reboot

        return {
            "host": host.name,
            "action": "reboot_initiated",
            "force": force,
            "warning": "Host is rebooting. Connection will be lost.",
        }

    @mcp_tool(
        name="shutdown_host",
        description="Shutdown the ESXi host (requires maintenance mode)",
        annotations=ToolAnnotations(destructiveHint=True),
    )
    def shutdown_host(self, force: bool = False) -> dict[str, Any]:
        """Shutdown the ESXi host.

        Args:
            force: Force shutdown even if VMs are running (dangerous!)

        Returns:
            Dict with operation result
        """
        host = self._get_host()

        if not host.runtime.inMaintenanceMode and not force:
            raise ValueError(
                "Host must be in maintenance mode to shutdown. "
                "Use enter_maintenance_mode first, or set force=True (dangerous!)."
            )

        host.ShutdownHost_Task(force=force)
        # Don't wait for task - host will shutdown

        return {
            "host": host.name,
            "action": "shutdown_initiated",
            "force": force,
            "warning": "Host is shutting down. Connection will be lost.",
        }

    @mcp_tool(
        name="get_host_hardware",
        description="Get detailed hardware information for the ESXi host",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_host_hardware(self) -> dict[str, Any]:
        """Get detailed hardware information.

        Returns:
            Dict with hardware details
        """
        host = self._get_host()
        hardware = host.hardware

        # CPU info
        cpu_info = {
            "packages": hardware.cpuInfo.numCpuPackages,
            "cores": hardware.cpuInfo.numCpuCores,
            "threads": hardware.cpuInfo.numCpuThreads,
            "hz": hardware.cpuInfo.hz,
        }

        # Memory info
        memory_info = {
            "total_bytes": hardware.memorySize,
            "total_gb": round(hardware.memorySize / (1024**3), 2),
        }

        # PCI devices
        pci_devices = []
        for pci in hardware.pciDevice[:10]:  # Limit to first 10
            pci_devices.append({
                "id": pci.id,
                "vendor_name": pci.vendorName,
                "device_name": pci.deviceName,
                "class_id": pci.classId,
            })

        # NICs
        nics = []
        for nic in host.config.network.pnic:
            nics.append({
                "device": nic.device,
                "driver": nic.driver,
                "mac": nic.mac,
                "link_speed": nic.linkSpeed.speedMb if nic.linkSpeed else None,
            })

        return {
            "host": host.name,
            "uuid": hardware.systemInfo.uuid,
            "bios": {
                "vendor": hardware.biosInfo.vendor,
                "version": hardware.biosInfo.biosVersion,
                "release_date": str(hardware.biosInfo.releaseDate),
            },
            "cpu": cpu_info,
            "memory": memory_info,
            "pci_devices": pci_devices,
            "network_adapters": nics,
        }

    @mcp_tool(
        name="get_host_networking",
        description="Get network configuration for the ESXi host",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_host_networking(self) -> dict[str, Any]:
        """Get network configuration for the ESXi host.

        Returns:
            Dict with networking details
        """
        host = self._get_host()
        network_config = host.config.network

        # Virtual switches
        vswitches = []
        for vswitch in network_config.vswitch:
            vswitches.append({
                "name": vswitch.name,
                "ports": vswitch.numPorts,
                "ports_available": vswitch.numPortsAvailable,
                "mtu": vswitch.mtu,
                "pnics": list(vswitch.pnic) if vswitch.pnic else [],
            })

        # Port groups
        portgroups = []
        for pg in network_config.portgroup:
            portgroups.append({
                "name": pg.spec.name,
                "vswitch": pg.spec.vswitchName,
                "vlan_id": pg.spec.vlanId,
            })

        # VMkernel adapters
        vmknics = []
        for vmk in network_config.vnic:
            vmknics.append({
                "device": vmk.device,
                "portgroup": vmk.portgroup,
                "ip": vmk.spec.ip.ipAddress,
                "netmask": vmk.spec.ip.subnetMask,
                "mac": vmk.spec.mac,
                "mtu": vmk.spec.mtu,
            })

        # DNS config
        dns = network_config.dnsConfig
        dns_info = {
            "hostname": dns.hostName,
            "domain": dns.domainName,
            "servers": list(dns.address) if dns.address else [],
            "search_domains": list(dns.searchDomain) if dns.searchDomain else [],
        }

        return {
            "host": host.name,
            "vswitches": vswitches,
            "portgroups": portgroups,
            "vmkernel_adapters": vmknics,
            "dns": dns_info,
        }
