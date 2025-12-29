# mcvsphere

**94 tools. Full VMware control. Natural language.**

[![PyPI version](https://img.shields.io/pypi/v/mcvsphere.svg)](https://pypi.org/project/mcvsphere/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

Stop clicking through vSphere. Start talking to it.

```bash
uvx mcvsphere
```

---

## What is this?

mcvsphere is an MCP server that gives AI assistants like Claude complete control over your VMware infrastructure. Create VMs, manage snapshots, run commands inside guests, take console screenshots, configure network appliances - all through conversation.

**94 MCP tools.** Not a toy demo. Not "just the basics." The whole thing.

```
You: "Spin up a new VM with 4 CPUs and 16GB RAM, clone it twice,
     then snapshot all three before I start testing"

Claude: Done. Three VMs running, all snapshotted. What's next?
```

---

## Install in 30 Seconds

```bash
# One command
uvx mcvsphere

# Or pip, if that's your thing
pip install mcvsphere
```

Set your credentials:

```bash
export VCENTER_HOST=vcenter.example.com
export VCENTER_USER=administrator@vsphere.local
export VCENTER_PASSWORD=your-password
```

Add to Claude Code:

```bash
claude mcp add vsphere "uvx mcvsphere"
```

That's it. You're managing vSphere with AI now.

---

## The Full Arsenal: 94 Tools

### VM Lifecycle
| Tool | What it does |
|------|--------------|
| `create_vm` | Spin up new VMs from scratch |
| `clone_vm` | Clone from templates or existing VMs |
| `delete_vm` | Clean removal |
| `reconfigure_vm` | Change CPU, memory, annotations |
| `rename_vm` | Rename VMs |
| `list_vms` / `get_vm_info` | See everything |

### Power Operations
`power_on_vm` | `power_off_vm` | `shutdown_guest` | `reboot_guest` | `suspend_vm` | `reset_vm`

### Snapshots
`create_snapshot` | `revert_to_snapshot` | `delete_snapshot` | `delete_all_snapshots` | `list_snapshots`

### Guest Operations
*Run commands inside VMs. No SSH required.*

| Tool | What it does |
|------|--------------|
| `run_command_in_guest` | Execute any command |
| `read_guest_file` | Pull files out |
| `write_guest_file` | Push files in |
| `list_guest_processes` | See what's running |
| `list_guest_directory` | Browse the filesystem |
| `create_guest_directory` | Make directories |
| `delete_guest_file` | Clean up |

### Console & Monitoring
| Tool | What it does |
|------|--------------|
| `vm_screenshot` | Capture the VM console |
| `get_vm_stats` | Performance metrics |
| `get_host_stats` | Host performance |
| `wait_for_vm_tools` | Block until Tools ready |
| `get_vm_tools_status` | Check Tools state |

### Serial Console
*For network appliances, headless boxes, and anything that talks over serial.*

`setup_serial_port` | `get_serial_port` | `connect_serial_port` | `clear_serial_port` | `remove_serial_port`

### Disk Management
`add_disk` | `remove_disk` | `resize_disk` | `list_disks` | `get_disk_info`

### Network Adapters
`add_nic` | `remove_nic` | `connect_nic` | `change_nic_network` | `list_nics` | `get_nic_info`

### OVF/OVA Operations
`deploy_ovf` | `export_ovf` | `list_ovf_networks` | `upload_to_datastore` | `download_from_datastore`

### Host Management
`list_hosts` | `get_host_info` | `get_host_hardware` | `get_host_networking` | `list_services` | `get_service_status` | `start_service` | `stop_service` | `restart_service` | `get_ntp_config`

### Datastore & Resources
`get_datastore_info` | `browse_datastore` | `get_vcenter_info` | `get_resource_pool_info` | `get_network_info` | `list_templates` | `get_alarms` | `get_recent_events`

### vCenter Operations
*Full cluster and organizational control.*

`list_folders` | `create_folder` | `delete_folder` | `move_vm_to_folder` | `list_clusters` | `get_cluster_info` | `list_resource_pools` | `create_resource_pool` | `delete_resource_pool` | `move_vm_to_resource_pool` | `list_tags` | `get_vm_tags` | `apply_tag_to_vm` | `remove_tag_from_vm` | `migrate_vm` | `list_recent_tasks` | `list_recent_events` | `cancel_task`

---

## 6 MCP Resources

Real-time data, always current:

| Resource | Data |
|----------|------|
| `esxi://vms` | All virtual machines |
| `esxi://hosts` | All ESXi hosts |
| `esxi://datastores` | All datastores |
| `esxi://networks` | All networks |
| `esxi://clusters` | All clusters |
| `esxi://resource-pools` | All resource pools |

---

## Real Examples

### Rapid VM Deployment

```
You: Create a VM called "test-web" with 4 CPUs, 8GB RAM, 100GB disk

Claude: VM 'test-web' created. Want me to power it on?

You: Yes, and take a screenshot once it's at the BIOS

Claude: [powers on, waits, captures screenshot]
        Here's the console - it's at the boot menu.
```

### Guest Operations Without SSH

```
You: What's the uptime on linux-server?

Claude: [runs "uptime" inside the guest via VMware Tools]
        linux-server has been up for 47 days, 3:22
```

### Serial Console for Network Gear

```
You: I need console access to my Cisco router VM

Claude: [configures network serial port]
        Done. Connect via: telnet://10.20.0.22:4521
```

### Disaster Recovery Practice

```
You: Snapshot all production VMs before I run the update

Claude: [snapshots 12 VMs in parallel]
        All 12 production VMs snapshotted. Ready when you are.
```

---

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VCENTER_HOST` | vCenter or ESXi hostname | *required* |
| `VCENTER_USER` | Username | *required* |
| `VCENTER_PASSWORD` | Password | *required* |
| `VCENTER_INSECURE` | Skip SSL verification | `false` |
| `VCENTER_DATACENTER` | Target datacenter | *auto-detect* |
| `VCENTER_CLUSTER` | Target cluster | *auto-detect* |
| `VCENTER_DATASTORE` | Default datastore | *auto-detect* |
| `VCENTER_NETWORK` | Default network | *auto-detect* |
| `MCP_TRANSPORT` | `stdio` or `sse` | `stdio` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Docker

```bash
docker run -d \
  -e VCENTER_HOST=vcenter.example.com \
  -e VCENTER_USER=admin@vsphere.local \
  -e VCENTER_PASSWORD=secret \
  ghcr.io/supportedsystems/mcvsphere:latest
```

---

## Requirements

- Python 3.11+
- VMware vSphere 7.0+ (ESXi or vCenter)
- VMware Tools (for guest operations)

---

## Built With

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [pyVmomi](https://github.com/vmware/pyvmomi) - VMware vSphere API

---

## License

MIT - do whatever you want with it.

---

**94 tools. Your entire VMware infrastructure. Controlled by conversation.**
