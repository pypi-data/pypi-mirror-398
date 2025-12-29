"""Monitoring and performance - stats, metrics, events."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from mcp.types import ToolAnnotations
from pyVmomi import vim

if TYPE_CHECKING:
    from mcvsphere.connection import VMwareConnection


class MonitoringMixin(MCPMixin):
    """VM and host monitoring tools."""

    def __init__(self, conn: "VMwareConnection"):
        self.conn = conn

    @mcp_tool(
        name="get_vm_stats",
        description="Get current performance statistics for a virtual machine",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_vm_stats(self, name: str) -> dict[str, Any]:
        """Get VM performance statistics."""
        vm = self.conn.find_vm(name)
        if not vm:
            raise ValueError(f"VM '{name}' not found")

        qs = vm.summary.quickStats
        storage = vm.summary.storage

        stats = {
            "name": name,
            "power_state": str(vm.runtime.powerState),
            "cpu_usage_mhz": qs.overallCpuUsage,
            "cpu_demand_mhz": qs.overallCpuDemand,
            "memory_usage_mb": qs.guestMemoryUsage,
            "memory_active_mb": qs.activeMemory,
            "memory_ballooned_mb": qs.balloonedMemory,
            "memory_swapped_mb": qs.swappedMemory,
            "storage_committed_gb": round(storage.committed / (1024**3), 2)
            if storage
            else 0,
            "storage_uncommitted_gb": round(storage.uncommitted / (1024**3), 2)
            if storage
            else 0,
            "uptime_seconds": qs.uptimeSeconds,
            "uptime_human": self._format_uptime(qs.uptimeSeconds)
            if qs.uptimeSeconds
            else None,
        }

        return stats

    @mcp_tool(
        name="get_host_stats",
        description="Get performance statistics for an ESXi host",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_host_stats(self, host_name: str | None = None) -> dict[str, Any]:
        """Get ESXi host performance statistics.

        If host_name is not provided, returns stats for the first host.
        """
        if host_name:
            host = self.conn.find_host(host_name)
            if not host:
                raise ValueError(f"Host '{host_name}' not found")
        else:
            # Get first host
            container = self.conn.content.viewManager.CreateContainerView(
                self.conn.content.rootFolder, [vim.HostSystem], True
            )
            try:
                hosts = list(container.view)
                if not hosts:
                    raise ValueError("No ESXi hosts found")
                host = hosts[0]
            finally:
                container.Destroy()

        summary = host.summary
        hardware = summary.hardware
        qs = summary.quickStats

        return {
            "name": host.name,
            "connection_state": str(summary.runtime.connectionState),
            "power_state": str(summary.runtime.powerState),
            "model": hardware.model,
            "vendor": hardware.vendor,
            "cpu_model": hardware.cpuModel,
            "cpu_cores": hardware.numCpuCores,
            "cpu_threads": hardware.numCpuThreads,
            "cpu_mhz": hardware.cpuMhz,
            "cpu_usage_mhz": qs.overallCpuUsage,
            "cpu_usage_percent": round(
                (qs.overallCpuUsage / (hardware.numCpuCores * hardware.cpuMhz)) * 100, 1
            )
            if qs.overallCpuUsage
            else 0,
            "memory_total_gb": round(hardware.memorySize / (1024**3), 2),
            "memory_usage_mb": qs.overallMemoryUsage,
            "memory_usage_percent": round(
                (qs.overallMemoryUsage * 1024 * 1024 / hardware.memorySize) * 100, 1
            )
            if qs.overallMemoryUsage
            else 0,
            "uptime_seconds": qs.uptime,
            "uptime_human": self._format_uptime(qs.uptime) if qs.uptime else None,
            "vm_count": len(host.vm) if host.vm else 0,
        }

    @mcp_tool(
        name="list_hosts",
        description="List all ESXi hosts in the datacenter",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def list_hosts(self) -> list[dict[str, Any]]:
        """List all ESXi hosts with basic info."""
        container = self.conn.content.viewManager.CreateContainerView(
            self.conn.content.rootFolder, [vim.HostSystem], True
        )
        try:
            hosts = []
            for host in container.view:
                summary = host.summary
                hardware = summary.hardware
                hosts.append(
                    {
                        "name": host.name,
                        "connection_state": str(summary.runtime.connectionState),
                        "power_state": str(summary.runtime.powerState),
                        "model": hardware.model,
                        "cpu_cores": hardware.numCpuCores,
                        "memory_gb": round(hardware.memorySize / (1024**3), 2),
                        "vm_count": len(host.vm) if host.vm else 0,
                    }
                )
            return hosts
        finally:
            container.Destroy()

    @mcp_tool(
        name="get_recent_tasks",
        description="Get recent vSphere tasks (VM operations, etc.)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_recent_tasks(self, count: int = 20) -> list[dict[str, Any]]:
        """Get recent vSphere tasks."""
        task_manager = self.conn.content.taskManager
        recent_tasks = task_manager.recentTask[:count] if task_manager.recentTask else []

        tasks = []
        for task in recent_tasks:
            try:
                info = task.info
                tasks.append(
                    {
                        "name": info.name,
                        "state": str(info.state),
                        "progress": info.progress,
                        "entity": info.entityName,
                        "queued_time": info.queueTime.isoformat()
                        if info.queueTime
                        else None,
                        "start_time": info.startTime.isoformat()
                        if info.startTime
                        else None,
                        "complete_time": info.completeTime.isoformat()
                        if info.completeTime
                        else None,
                        "description": str(info.description) if info.description else None,
                        "error": str(info.error) if info.error else None,
                    }
                )
            except Exception:
                # Task may have been cleaned up
                continue

        return tasks

    @mcp_tool(
        name="get_recent_events",
        description="Get recent vSphere events (alarms, changes, etc.)",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_recent_events(
        self, count: int = 50, hours: int = 24
    ) -> list[dict[str, Any]]:
        """Get recent vSphere events."""
        event_manager = self.conn.content.eventManager

        # Create time filter
        time_filter = vim.event.EventFilterSpec.ByTime()
        time_filter.beginTime = datetime.now(UTC) - timedelta(hours=hours)

        filter_spec = vim.event.EventFilterSpec(time=time_filter)

        events = []
        try:
            collector = event_manager.CreateCollectorForEvents(filter_spec)
            try:
                collector.SetCollectorPageSize(count)
                latest_events = collector.latestPage

                for event in latest_events:
                    events.append(
                        {
                            "key": event.key,
                            "type": type(event).__name__,
                            "created_time": event.createdTime.isoformat()
                            if event.createdTime
                            else None,
                            "message": event.fullFormattedMessage,
                            "username": event.userName,
                            "datacenter": event.datacenter.name
                            if event.datacenter
                            else None,
                            "host": event.host.name if event.host else None,
                            "vm": event.vm.name if event.vm else None,
                        }
                    )
            finally:
                collector.DestroyCollector()
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve events: {e}") from e

        return events

    @mcp_tool(
        name="get_alarms",
        description="Get triggered alarms in the datacenter",
        annotations=ToolAnnotations(readOnlyHint=True),
    )
    def get_alarms(self) -> list[dict[str, Any]]:
        """Get all triggered alarms."""
        alarms = []

        # Check datacenter alarms
        if self.conn.datacenter.triggeredAlarmState:
            for alarm_state in self.conn.datacenter.triggeredAlarmState:
                alarms.append(self._format_alarm(alarm_state))

        # Check VM alarms
        for vm in self.conn.get_all_vms():
            if vm.triggeredAlarmState:
                for alarm_state in vm.triggeredAlarmState:
                    alarms.append(self._format_alarm(alarm_state, vm.name))

        return alarms

    def _format_alarm(
        self, alarm_state: vim.alarm.AlarmState, entity_name: str | None = None
    ) -> dict[str, Any]:
        """Format alarm state for output."""
        return {
            "alarm": alarm_state.alarm.info.name if alarm_state.alarm else "Unknown",
            "entity": entity_name or str(alarm_state.entity),
            "status": str(alarm_state.overallStatus),
            "time": alarm_state.time.isoformat() if alarm_state.time else None,
            "acknowledged": alarm_state.acknowledged,
            "acknowledged_by": alarm_state.acknowledgedByUser,
        }

    def _format_uptime(self, seconds: int | None) -> str:
        """Format uptime seconds to human readable string."""
        if not seconds:
            return "N/A"
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
