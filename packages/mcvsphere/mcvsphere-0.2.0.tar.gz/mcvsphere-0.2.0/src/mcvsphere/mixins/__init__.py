"""MCP Mixins for ESXi operations organized by category."""

from mcvsphere.mixins.console import ConsoleMixin
from mcvsphere.mixins.disk_management import DiskManagementMixin
from mcvsphere.mixins.guest_ops import GuestOpsMixin
from mcvsphere.mixins.host_management import HostManagementMixin
from mcvsphere.mixins.monitoring import MonitoringMixin
from mcvsphere.mixins.nic_management import NICManagementMixin
from mcvsphere.mixins.ovf_management import OVFManagementMixin
from mcvsphere.mixins.power_ops import PowerOpsMixin
from mcvsphere.mixins.resources import ResourcesMixin
from mcvsphere.mixins.serial_port import SerialPortMixin
from mcvsphere.mixins.snapshots import SnapshotsMixin
from mcvsphere.mixins.vcenter_ops import VCenterOpsMixin
from mcvsphere.mixins.vm_lifecycle import VMLifecycleMixin

__all__ = [
    "ConsoleMixin",
    "DiskManagementMixin",
    "GuestOpsMixin",
    "HostManagementMixin",
    "MonitoringMixin",
    "NICManagementMixin",
    "OVFManagementMixin",
    "PowerOpsMixin",
    "ResourcesMixin",
    "SerialPortMixin",
    "SnapshotsMixin",
    "VCenterOpsMixin",
    "VMLifecycleMixin",
]
