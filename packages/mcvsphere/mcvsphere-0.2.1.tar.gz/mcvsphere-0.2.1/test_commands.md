# ESXi MCP Server Test Commands

Try these in a new Claude Code session:

## 1. Basic Discovery
```
List all VMs on the ESXi host
```

```
Show me the datastores and their free space
```

```
What networks are available?
```

## 2. Host Management (NEW!)
```
Get detailed info about the ESXi host
```

```
List all services on the ESXi host
```

```
Show the NTP configuration
```

```
Show me the host networking config (vswitches, portgroups)
```

## 3. VM Hardware (NEW!)
```
List the disks on VM "your-vm-name"
```

```
List the NICs on VM "your-vm-name"
```

## 4. Datastore Operations
```
Browse the datastore "your-datastore" in the iso folder
```

```
Show me what's in the root of datastore "your-datastore"
```

## 5. Advanced Operations (be careful!)
```
# Add a 10GB disk to a VM
Add a 10GB thin-provisioned disk to VM "test-vm"

# Add a NIC
Add a vmxnet3 NIC to VM "test-vm" on network "VM Network"

# Configure NTP
Configure NTP servers 0.pool.ntp.org and 1.pool.ntp.org on the ESXi host
```

---
Start a new session with: `claude`
