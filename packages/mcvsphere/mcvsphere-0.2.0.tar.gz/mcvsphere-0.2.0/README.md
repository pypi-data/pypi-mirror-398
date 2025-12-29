# mcvsphere

A comprehensive VMware vSphere management server implementing the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), enabling AI assistants like Claude to manage virtual infrastructure through natural language.

## Why mcvsphere?

Traditional VMware management requires navigating complex UIs or writing scripts. With mcvsphere, you can simply ask:

> "Create a new VM with 4 CPUs and 8GB RAM, then take a snapshot before installing the OS"

And watch it happen. The server exposes **94 tools** covering every aspect of vSphere management.

## Features

- **94 MCP Tools** - Complete vSphere management capabilities
- **6 MCP Resources** - Real-time access to VMs, hosts, datastores, networks, and clusters
- **Modular Architecture** - 13 specialized mixins organized by function
- **Full vCenter & ESXi Support** - Works with standalone hosts or vCenter Server
- **Guest Operations** - Execute commands, transfer files inside VMs via VMware Tools
- **Serial Console Access** - Network serial ports for headless VMs and network appliances
- **VM Screenshots** - Capture console screenshots for monitoring or documentation

## Quick Start

### Installation

```bash
# Install with uv (recommended)
uvx mcvsphere

# Or install with pip
pip install mcvsphere
```

### Configuration

Create a `.env` file or set environment variables:

```bash
VCENTER_HOST=vcenter.example.com
VCENTER_USER=administrator@vsphere.local
VCENTER_PASSWORD=your-password
VCENTER_INSECURE=true  # Skip SSL verification (dev only)
```

### Run the Server

```bash
# Using uvx
uvx mcvsphere

# Or if installed
mcvsphere
```

### Add to Claude Code

```bash
claude mcp add esxi "uvx mcvsphere"
```

## Available Tools (94 Total)

### VM Lifecycle (6 tools)
| Tool | Description |
|------|-------------|
| `list_vms` | List all virtual machines |
| `get_vm_info` | Get detailed VM information |
| `create_vm` | Create a new virtual machine |
| `clone_vm` | Clone from template or existing VM |
| `delete_vm` | Delete a virtual machine |
| `reconfigure_vm` | Modify CPU, memory, annotation |
| `rename_vm` | Rename a virtual machine |

### Power Operations (6 tools)
| Tool | Description |
|------|-------------|
| `power_on_vm` | Power on a VM |
| `power_off_vm` | Power off a VM (hard) |
| `shutdown_guest` | Graceful guest OS shutdown |
| `reboot_guest` | Graceful guest OS reboot |
| `suspend_vm` | Suspend a VM |
| `reset_vm` | Hard reset a VM |

### Snapshots (5 tools)
| Tool | Description |
|------|-------------|
| `list_snapshots` | List all snapshots |
| `create_snapshot` | Create a new snapshot |
| `revert_to_snapshot` | Revert to a snapshot |
| `delete_snapshot` | Delete a snapshot |
| `delete_all_snapshots` | Remove all snapshots |

### Guest Operations (7 tools)
*Requires VMware Tools running in the guest*

| Tool | Description |
|------|-------------|
| `list_guest_processes` | List processes in guest OS |
| `run_command_in_guest` | Execute command in guest |
| `read_guest_file` | Read file from guest OS |
| `write_guest_file` | Write file to guest OS |
| `list_guest_directory` | List directory contents |
| `create_guest_directory` | Create directory in guest |
| `delete_guest_file` | Delete file or directory |

### Console & Monitoring (5 tools)
| Tool | Description |
|------|-------------|
| `vm_screenshot` | Capture VM console screenshot |
| `wait_for_vm_tools` | Wait for VMware Tools to be ready |
| `get_vm_tools_status` | Get VMware Tools status |
| `get_vm_stats` | Get VM performance statistics |
| `get_host_stats` | Get host performance statistics |

### Serial Port Management (5 tools)
*For network appliances and headless VMs*

| Tool | Description |
|------|-------------|
| `get_serial_port` | Get serial port configuration |
| `setup_serial_port` | Configure network serial port |
| `connect_serial_port` | Connect/disconnect serial port |
| `clear_serial_port` | Reset serial port connection |
| `remove_serial_port` | Remove serial port from VM |

### Disk Management (5 tools)
| Tool | Description |
|------|-------------|
| `list_disks` | List VM disks |
| `add_disk` | Add a new disk |
| `remove_disk` | Remove a disk |
| `resize_disk` | Expand disk size |
| `get_disk_info` | Get disk details |

### NIC Management (6 tools)
| Tool | Description |
|------|-------------|
| `list_nics` | List VM network adapters |
| `add_nic` | Add a network adapter |
| `remove_nic` | Remove a network adapter |
| `connect_nic` | Connect/disconnect NIC |
| `change_nic_network` | Change NIC network |
| `get_nic_info` | Get NIC details |

### OVF/OVA Management (5 tools)
| Tool | Description |
|------|-------------|
| `deploy_ovf` | Deploy VM from OVF template |
| `export_ovf` | Export VM to OVF |
| `list_ovf_networks` | List OVF network mappings |
| `upload_to_datastore` | Upload file to datastore |
| `download_from_datastore` | Download file from datastore |

### Host Management (10 tools)
| Tool | Description |
|------|-------------|
| `list_hosts` | List ESXi hosts |
| `get_host_info` | Get host details |
| `get_host_hardware` | Get hardware information |
| `get_host_networking` | Get network configuration |
| `list_services` | List host services |
| `get_service_status` | Get service status |
| `start_service` | Start a host service |
| `stop_service` | Stop a host service |
| `restart_service` | Restart a host service |
| `get_ntp_config` | Get NTP configuration |

### Datastore & Resources (8 tools)
| Tool | Description |
|------|-------------|
| `get_datastore_info` | Get datastore details |
| `browse_datastore` | Browse datastore files |
| `get_vcenter_info` | Get vCenter information |
| `get_resource_pool_info` | Get resource pool details |
| `get_network_info` | Get network details |
| `list_templates` | List VM templates |
| `get_alarms` | Get active alarms |
| `get_recent_events` | Get recent events |

### vCenter Operations (18 tools)
*Available when connected to vCenter Server*

| Tool | Description |
|------|-------------|
| `list_folders` | List VM folders |
| `create_folder` | Create a folder |
| `delete_folder` | Delete a folder |
| `move_vm_to_folder` | Move VM to folder |
| `list_clusters` | List clusters |
| `get_cluster_info` | Get cluster details |
| `list_resource_pools` | List resource pools |
| `create_resource_pool` | Create resource pool |
| `delete_resource_pool` | Delete resource pool |
| `move_vm_to_resource_pool` | Move VM to resource pool |
| `list_tags` | List tags |
| `get_vm_tags` | Get tags on a VM |
| `apply_tag_to_vm` | Apply tag to VM |
| `remove_tag_from_vm` | Remove tag from VM |
| `migrate_vm` | Migrate VM to another host |
| `list_recent_tasks` | List recent tasks |
| `list_recent_events` | List recent events |
| `cancel_task` | Cancel a running task |

## MCP Resources

Access real-time data through MCP resources:

| Resource URI | Description |
|--------------|-------------|
| `esxi://vms` | All virtual machines |
| `esxi://hosts` | All ESXi hosts |
| `esxi://datastores` | All datastores |
| `esxi://networks` | All networks |
| `esxi://clusters` | All clusters |
| `esxi://resource-pools` | All resource pools |

## Architecture

The server uses a modular mixin architecture:

```
mcvsphere/
├── server.py           # FastMCP server setup
├── connection.py       # VMware connection management
├── config.py           # Settings and configuration
└── mixins/
    ├── vm_lifecycle.py    # VM CRUD operations
    ├── power_ops.py       # Power management
    ├── snapshots.py       # Snapshot management
    ├── guest_ops.py       # Guest OS operations
    ├── console.py         # Screenshots & Tools monitoring
    ├── serial_port.py     # Serial console access
    ├── disk_management.py # Disk operations
    ├── nic_management.py  # Network adapter operations
    ├── ovf_management.py  # OVF/OVA handling
    ├── host_management.py # Host operations
    ├── monitoring.py      # Performance monitoring
    ├── resources.py       # MCP resources
    └── vcenter_ops.py     # vCenter-specific operations
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `VCENTER_HOST` | vCenter/ESXi hostname or IP | *required* |
| `VCENTER_USER` | Username | *required* |
| `VCENTER_PASSWORD` | Password | *required* |
| `VCENTER_INSECURE` | Skip SSL verification | `false` |
| `VCENTER_DATACENTER` | Target datacenter | *auto-detect* |
| `VCENTER_CLUSTER` | Target cluster | *auto-detect* |
| `VCENTER_DATASTORE` | Default datastore | *auto-detect* |
| `VCENTER_NETWORK` | Default network | *auto-detect* |
| `MCP_TRANSPORT` | Transport mode (`stdio` or `sse`) | `stdio` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Docker Support

```bash
# Build
docker build -t mcvsphere .

# Run
docker run -d \
  -e VCENTER_HOST=vcenter.example.com \
  -e VCENTER_USER=admin@vsphere.local \
  -e VCENTER_PASSWORD=secret \
  mcvsphere
```

## Examples

### Create a VM and Install an OS

```
User: Create a new VM called "web-server" with 4 CPUs, 8GB RAM, and a 100GB disk

Claude: I'll create that VM for you.
[Calls create_vm with name="web-server", cpu=4, memory_mb=8192, disk_gb=100]

VM 'web-server' created successfully.

User: Power it on and take a screenshot

Claude: [Calls power_on_vm, then vm_screenshot]

The VM is now running. Here's the console screenshot showing the BIOS boot screen.
```

### Guest Operations

```
User: Run "uname -a" on the linux-server VM

Claude: [Calls run_command_in_guest with command="/usr/bin/uname", arguments="-a"]

The command returned:
Linux linux-server 5.15.0-generic #1 SMP x86_64 GNU/Linux
```

### Serial Console for Network Appliances

```
User: Set up a serial console on my Cisco router VM

Claude: [Calls setup_serial_port with name="cisco-router", protocol="telnet"]

Serial port configured. You can connect via:
telnet://10.20.0.22:4521
```

## Requirements

- Python 3.11+
- VMware vSphere 7.0+ (ESXi or vCenter)
- VMware Tools (for guest operations)

## Development

```bash
# Clone the repo
git clone https://github.com/yourusername/mcvsphere.git
cd mcvsphere

# Install dependencies
uv sync

# Run tests
uv run python test_client.py
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read the contributing guidelines and submit a PR.

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Uses [pyVmomi](https://github.com/vmware/pyvmomi) for vSphere API
- Inspired by the Model Context Protocol specification
