r'''
# Azure Virtual Machine Construct

A unified, version-aware implementation for Azure Virtual Machines using the VersionedAzapiResource framework. This construct provides automatic version management, schema validation, and property transformation across all supported API versions.

## Features

* **Automatic Version Resolution**: Uses the latest stable API version by default
* **Explicit Version Pinning**: Pin to specific API versions when stability is required
* **Schema-Driven Validation**: Validates all properties against Azure API schemas
* **Multi-Language Support**: Full JSII compliance for TypeScript, Python, Java, C#, and Go
* **Comprehensive VM Support**: Linux, Windows, Spot VMs, managed identities, and more

## Supported API Versions

* `2024-07-01` (Active)
* `2024-11-01` (Active)
* `2025-04-01` (Active, Latest - Default)

## Installation

```bash
npm install @cdktf/provider-azurerm
```

## Basic Usage

### Creating Network Interface First

Virtual Machines require a network interface. Create the NIC separately using the [`NetworkInterface`](../azure-networkinterface/README.md) construct:

```python
import { VirtualMachine } from "./azure-virtualmachine";
import { NetworkInterface } from "./azure-networkinterface";
import { ResourceGroup } from "./azure-resourcegroup";

// Create a resource group
const resourceGroup = new ResourceGroup(this, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

// Create a network interface (required for VM)
const networkInterface = new NetworkInterface(this, "nic", {
  name: "my-vm-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id }, // Reference to existing subnet
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
});

// Create a Linux VM referencing the NIC by ID
const linuxVm = new VirtualMachine(this, "linux-vm", {
  name: "my-linux-vm",
  location: resourceGroup.location,
  resourceGroupId: resourceGroup.id,
  hardwareProfile: {
    vmSize: "Standard_D2s_v3",
  },
  storageProfile: {
    imageReference: {
      publisher: "Canonical",
      offer: "0001-com-ubuntu-server-jammy",
      sku: "22_04-lts-gen2",
      version: "latest",
    },
    osDisk: {
      createOption: "FromImage",
      managedDisk: {
        storageAccountType: "Premium_LRS",
      },
    },
  },
  osProfile: {
    computerName: "mylinuxvm",
    adminUsername: "azureuser",
    linuxConfiguration: {
      disablePasswordAuthentication: true,
      ssh: {
        publicKeys: [
          {
            path: "/home/azureuser/.ssh/authorized_keys",
            keyData: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...",
          },
        ],
      },
    },
  },
  networkProfile: {
    networkInterfaces: [
      {
        id: networkInterface.id,
      },
    ],
  },
  identity: {
    type: "SystemAssigned",
  },
  tags: {
    environment: "production",
  },
});

// Access VM outputs
console.log(linuxVm.id);
console.log(linuxVm.vmId);
```

### Windows VM with Password Authentication

```python
const windowsVm = new VirtualMachine(this, "windows-vm", {
  name: "my-windows-vm",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  hardwareProfile: {
    vmSize: "Standard_D2s_v3",
  },
  storageProfile: {
    imageReference: {
      publisher: "MicrosoftWindowsServer",
      offer: "WindowsServer",
      sku: "2022-datacenter-azure-edition",
      version: "latest",
    },
    osDisk: {
      createOption: "FromImage",
      managedDisk: {
        storageAccountType: "Premium_LRS",
      },
    },
  },
  osProfile: {
    computerName: "mywinvm",
    adminUsername: "azureuser",
    adminPassword: "P@ssw0rd1234!",
    windowsConfiguration: {
      provisionVMAgent: true,
      enableAutomaticUpdates: true,
    },
  },
  networkProfile: {
    networkInterfaces: [
      {
        id: networkInterface.id,
      },
    ],
  },
  licenseType: "Windows_Server",
  tags: {
    os: "windows",
    environment: "production",
  },
});
```

### VM with Managed Identity and Data Disks

```python
const vmWithIdentity = new VirtualMachine(this, "vm-identity", {
  name: "my-identity-vm",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  hardwareProfile: {
    vmSize: "Standard_D4s_v3",
  },
  storageProfile: {
    imageReference: {
      publisher: "Canonical",
      offer: "0001-com-ubuntu-server-jammy",
      sku: "22_04-lts-gen2",
      version: "latest",
    },
    osDisk: {
      createOption: "FromImage",
      managedDisk: {
        storageAccountType: "Premium_LRS",
      },
      diskSizeGB: 128,
    },
    dataDisks: [
      {
        lun: 0,
        createOption: "Empty",
        diskSizeGB: 512,
        managedDisk: {
          storageAccountType: "Premium_LRS",
        },
      },
      {
        lun: 1,
        createOption: "Empty",
        diskSizeGB: 1024,
        managedDisk: {
          storageAccountType: "Premium_LRS",
        },
      },
    ],
  },
  osProfile: {
    computerName: "myidentityvm",
    adminUsername: "azureuser",
    linuxConfiguration: {
      disablePasswordAuthentication: true,
      ssh: {
        publicKeys: [
          {
            path: "/home/azureuser/.ssh/authorized_keys",
            keyData: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...",
          },
        ],
      },
    },
  },
  networkProfile: {
    networkInterfaces: [
      {
        id: networkInterface.id,
      },
    ],
  },
  identity: {
    type: "UserAssigned",
    userAssignedIdentities: {
      [managedIdentity.id]: {},
    },
  },
});
```

### Spot VM with Eviction Policy

```python
const spotVm = new VirtualMachine(this, "spot-vm", {
  name: "my-spot-vm",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  priority: "Spot",
  evictionPolicy: "Deallocate",
  billingProfile: {
    maxPrice: -1, // Pay up to on-demand price
  },
  hardwareProfile: {
    vmSize: "Standard_D2s_v3",
  },
  storageProfile: {
    imageReference: {
      publisher: "Canonical",
      offer: "0001-com-ubuntu-server-jammy",
      sku: "22_04-lts-gen2",
      version: "latest",
    },
    osDisk: {
      createOption: "FromImage",
      managedDisk: {
        storageAccountType: "Standard_LRS",
      },
    },
  },
  osProfile: {
    computerName: "myspotvm",
    adminUsername: "azureuser",
    linuxConfiguration: {
      disablePasswordAuthentication: true,
      ssh: {
        publicKeys: [
          {
            path: "/home/azureuser/.ssh/authorized_keys",
            keyData: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...",
          },
        ],
      },
    },
  },
  networkProfile: {
    networkInterfaces: [
      {
        id: networkInterface.id,
      },
    ],
  },
  tags: {
    priority: "spot",
  },
});
```

### VM with Boot Diagnostics and Security Features

```python
const secureVm = new VirtualMachine(this, "secure-vm", {
  name: "my-secure-vm",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  hardwareProfile: {
    vmSize: "Standard_D2s_v3",
  },
  storageProfile: {
    imageReference: {
      publisher: "Canonical",
      offer: "0001-com-ubuntu-server-jammy",
      sku: "22_04-lts-gen2",
      version: "latest",
    },
    osDisk: {
      createOption: "FromImage",
      managedDisk: {
        storageAccountType: "Premium_LRS",
      },
    },
  },
  osProfile: {
    computerName: "mysecurevm",
    adminUsername: "azureuser",
    linuxConfiguration: {
      disablePasswordAuthentication: true,
      ssh: {
        publicKeys: [
          {
            path: "/home/azureuser/.ssh/authorized_keys",
            keyData: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC...",
          },
        ],
      },
    },
  },
  networkProfile: {
    networkInterfaces: [
      {
        id: networkInterface.id,
      },
    ],
  },
  diagnosticsProfile: {
    bootDiagnostics: {
      enabled: true,
      storageUri: storageAccount.primaryBlobEndpoint,
    },
  },
  securityProfile: {
    uefiSettings: {
      secureBootEnabled: true,
      vTpmEnabled: true,
    },
    securityType: "TrustedLaunch",
  },
  identity: {
    type: "SystemAssigned",
  },
});
```

## Monitoring

Virtual Machines support integrated monitoring through the `monitoring` property, which automatically creates Azure Monitor metric alerts, diagnostic settings, and activity log alerts. This provides comprehensive observability for your VMs with minimal configuration.

### Quick Start - Default Monitoring

The simplest way to enable monitoring is using the [`VirtualMachine.defaultMonitoring()`](./lib/virtual-machine.ts) static method:

```python
import { VirtualMachine } from '@microsoft/terraform-cdk-constructs/azure-virtualmachine';
import { ActionGroup } from '@microsoft/terraform-cdk-constructs/azure-actiongroup';
import { LogAnalyticsWorkspace } from '@microsoft/terraform-cdk-constructs/azure-loganalyticsworkspace';

// Create an action group for alerts
const actionGroup = new ActionGroup(this, 'alerts', {
  name: 'vm-alerts',
  resourceGroupName: resourceGroup.name,
  emailReceivers: [{
    name: 'admin',
    emailAddress: 'admin@example.com'
  }]
});

// Create or reference a Log Analytics workspace
const workspace = new LogAnalyticsWorkspace(this, 'workspace', {
  name: 'vm-monitoring-workspace',
  location: 'eastus',
  resourceGroupName: resourceGroup.name
});

// Create VM with default monitoring
const vm = new VirtualMachine(this, 'vm', {
  name: 'production-vm',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  hardwareProfile: {
    vmSize: 'Standard_D2s_v3',
  },
  // ... other VM configuration ...
  monitoring: VirtualMachine.defaultMonitoring(
    actionGroup.id,
    workspace.id
  )
});
```

### Default Monitoring Configuration

The `defaultMonitoring()` method automatically configures:

#### Metric Alerts

* **High CPU Alert**: Triggers when CPU usage exceeds 80% for 15 minutes

  * Severity: Warning (2)
  * Metric: `Percentage CPU`
  * Threshold: 80%
  * Window: 15 minutes
* **Low Memory Alert**: Triggers when available memory falls below 1GB for 15 minutes

  * Severity: Warning (2)
  * Metric: `Available Memory Bytes`
  * Threshold: 1073741824 bytes (1GB)
  * Window: 15 minutes
* **High Disk Queue Alert**: Triggers when OS disk queue depth exceeds 32 for 15 minutes

  * Severity: Warning (2)
  * Metric: `OS Disk Queue Depth`
  * Threshold: 32
  * Window: 15 minutes

#### Diagnostic Settings

When a workspace ID is provided, automatically sends all VM logs and metrics to the Log Analytics workspace for centralized analysis and long-term retention.

#### Activity Log Alerts

* **VM Deletion Alert**: Triggers when the virtual machine is deleted

  * Severity: Critical (0)
  * Monitors administrative operations on the VM resource

### Customizing Monitoring

You can customize thresholds and alert severities by providing options:

```python
monitoring: VirtualMachine.defaultMonitoring(
  actionGroup.id,
  workspace.id,
  {
    cpuThreshold: 90,              // Raise CPU threshold to 90%
    memoryThreshold: 524288000,    // Lower memory threshold to 500MB (in bytes)
    cpuAlertSeverity: 1,           // Make CPU alert critical (0=Critical, 1=Error, 2=Warning)
    enableDiskQueueAlert: false,   // Disable disk queue monitoring
    enableDeletionAlert: false     // Disable deletion alert
  }
)
```

### Customization Options

The following options are available when using `defaultMonitoring()`:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cpuThreshold` | number | 80 | CPU percentage threshold for alerts (0-100) |
| `memoryThreshold` | number | 1073741824 | Available memory threshold in bytes (default 1GB) |
| `diskQueueThreshold` | number | 32 | Disk queue depth threshold |
| `enableCpuAlert` | boolean | true | Enable/disable CPU monitoring |
| `enableMemoryAlert` | boolean | true | Enable/disable memory monitoring |
| `enableDiskQueueAlert` | boolean | true | Enable/disable disk queue monitoring |
| `enableDeletionAlert` | boolean | true | Enable/disable deletion alert |
| `cpuAlertSeverity` | 0|1|2|3|4 | 2 | Severity for CPU alerts (0=Critical, 4=Verbose) |
| `memoryAlertSeverity` | 0|1|2|3|4 | 2 | Severity for memory alerts |
| `diskQueueAlertSeverity` | 0|1|2|3|4 | 2 | Severity for disk queue alerts |

### Advanced: Fully Custom Monitoring

For complete control over monitoring configuration, provide a custom monitoring object:

```python
monitoring: {
  enabled: true,
  metricAlerts: [
    {
      name: 'custom-network-alert',
      description: 'Alert on high network traffic',
      severity: 2,
      frequency: 'PT5M',
      windowSize: 'PT15M',
      criteria: {
        singleResourceMultipleMetricCriteria: [{
          metricNamespace: 'Microsoft.Compute/virtualMachines',
          metricName: 'Network In Total',
          aggregation: 'Total',
          operator: 'GreaterThan',
          threshold: 1000000000  // 1GB
        }]
      },
      actionGroupIds: [actionGroup.id]
    },
    {
      name: 'disk-write-performance',
      description: 'Alert on high disk write latency',
      severity: 2,
      frequency: 'PT5M',
      windowSize: 'PT15M',
      criteria: {
        singleResourceMultipleMetricCriteria: [{
          metricNamespace: 'Microsoft.Compute/virtualMachines',
          metricName: 'OS Disk Write Bytes/sec',
          aggregation: 'Average',
          operator: 'LessThan',
          threshold: 1000000  // Less than 1MB/sec
        }]
      },
      actionGroupIds: [actionGroup.id]
    }
  ],
  diagnosticSettings: {
    name: 'custom-diagnostics',
    workspaceId: workspace.id,
    logs: [
      { categoryGroup: 'audit', enabled: true },
      { categoryGroup: 'allLogs', enabled: true }
    ],
    metrics: [
      { category: 'AllMetrics', enabled: true }
    ]
  },
  activityLogAlerts: [
    {
      name: 'vm-critical-operations',
      description: 'Alert on critical VM operations',
      scopes: [`/subscriptions/${subscriptionId}/resourceGroups/${resourceGroup.name}`],
      criteria: {
        category: 'Administrative',
        operationName: 'Microsoft.Compute/virtualMachines/write',
        resourceId: vm.id
      },
      actionGroupIds: [actionGroup.id]
    }
  ]
}
```

### Combining Default Monitoring with Custom Alerts

You can easily extend the default monitoring with additional custom alerts:

```python
import { VirtualMachine } from '@microsoft/terraform-cdk-constructs/azure-virtualmachine';
import { ActionGroup } from '@microsoft/terraform-cdk-constructs/azure-actiongroup';

const actionGroup = new ActionGroup(this, 'alerts', {
  name: 'vm-alerts',
  resourceGroupId: resourceGroup.id,
  emailReceivers: [{
    name: 'admin',
    emailAddress: 'admin@example.com'
  }]
});

// Start with default monitoring and add one custom alert
const monitoring = VirtualMachine.defaultMonitoring(
  actionGroup.id,
  workspace.id
);

// Add a custom network traffic alert
monitoring.metricAlerts?.push({
  name: 'high-network-traffic',
  description: 'Alert when network egress exceeds 10GB in 15 minutes',
  severity: 2,
  scopes: [], // Auto-set to this VM
  evaluationFrequency: 'PT5M',
  windowSize: 'PT15M',
  criteria: {
    type: 'StaticThreshold',
    metricName: 'Network Out Total',
    metricNamespace: 'Microsoft.Compute/virtualMachines',
    operator: 'GreaterThan',
    threshold: 10737418240, // 10GB in bytes
    timeAggregation: 'Total'
  },
  actions: [{ actionGroupId: actionGroup.id }]
});

const vm = new VirtualMachine(this, 'vm', {
  name: 'production-vm',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  hardwareProfile: { vmSize: 'Standard_D2s_v3' },
  // ... other VM configuration ...
  monitoring: monitoring
});
```

This approach gives you:

* ✅ All default alerts (CPU, Memory, Disk Queue, VM Deletion)
* ✅ Diagnostic settings sending data to Log Analytics
* ✅ Your custom network traffic alert
* ✅ All alerts using the same action group

### Available VM Metrics

Azure Virtual Machines provide numerous metrics for monitoring. Common metrics include:

* **CPU**: `Percentage CPU`
* **Memory**: `Available Memory Bytes`
* **Disk Performance**:

  * `OS Disk Queue Depth`
  * `OS Disk IOPS Consumed Percentage`
  * `OS Disk Bandwidth Consumed Percentage`
  * `Disk Read Bytes`
  * `Disk Write Bytes`
  * `Disk Read Operations/Sec`
  * `Disk Write Operations/Sec`
* **Network**:

  * `Network In Total`
  * `Network Out Total`
  * `Inbound Flows`
  * `Outbound Flows`
* **Credits** (for burstable VMs):

  * `CPU Credits Remaining`
  * `CPU Credits Consumed`

For a complete list of available metrics, see the [Azure VM Metrics Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/metrics-supported#microsoftcomputevirtualmachines).

### Disabling Monitoring

To disable monitoring entirely:

```python
monitoring: {
  enabled: false
}
```

## API Version Management

### Using Default (Latest) Version

By default, the construct uses the latest stable API version:

```python
const vm = new VirtualMachine(this, "vm", {
  // ... properties
});
// Uses 2024-07-01 automatically
```

### Pinning to Specific Version

Pin to a specific API version for stability:

```python
const vm = new VirtualMachine(this, "vm", {
  apiVersion: "2024-07-01", // Pin to specific version
  // ... other properties
});
```

### Migration Analysis

Analyze migration requirements between versions:

```python
const analysis = vm.analyzeMigrationTo("2024-07-01");
console.log(`Breaking changes: ${analysis.breakingChanges.length}`);
console.log(`Estimated effort: ${analysis.estimatedEffort}`);
```

## Properties Reference

### Required Properties

* **`hardwareProfile`**: VM size configuration

  * `vmSize`: VM size (e.g., "Standard_D2s_v3")
* **`storageProfile`**: Storage configuration

  * `imageReference`: OS image reference
  * `osDisk`: OS disk configuration
  * `dataDisks`: Optional data disks array
* **`networkProfile`**: Network configuration

  * `networkInterfaces`: Array of network interface references

### Optional Properties

* **`osProfile`**: OS configuration

  * `computerName`: Computer name
  * `adminUsername`: Admin username
  * `adminPassword`: Admin password (Windows or Linux with password auth)
  * `linuxConfiguration`: Linux-specific settings
  * `windowsConfiguration`: Windows-specific settings
* **`identity`**: Managed identity configuration
* **`zones`**: Availability zones
* **`priority`**: VM priority (Regular, Low, Spot)
* **`licenseType`**: License type for Windows VMs
* **`diagnosticsProfile`**: Boot diagnostics configuration
* **`securityProfile`**: Security settings
* **`tags`**: Resource tags

## Public Methods

### Tag Management

```python
// Add a tag
vm.addTag("environment", "production");

// Remove a tag
vm.removeTag("temporary");
```

### VM Properties

```python
// Get VM ID
const vmId = vm.vmId;

// Get provisioning state
const state = vm.provisioningState;

// Get VM size
const size = vm.vmSize;

// Get computer name
const name = vm.computerName;
```

## Migration Guide

### From Version-Specific Implementations

If migrating from version-specific VM implementations:

```python
// Old approach (version-specific class)
import { VirtualMachine_2023_07_01 } from "./old-implementation";

// New unified approach
import { VirtualMachine } from "./azure-virtualmachine";

const vm = new VirtualMachine(this, "vm", {
  apiVersion: "2024-07-01", // Explicitly pin if needed
  // ... same properties
});
```

### Upgrading API Versions

1. Test with the new version in a development environment
2. Review migration analysis for breaking changes
3. Update your code to handle any breaking changes
4. Deploy to production

```python
// Analyze migration before upgrading
const currentVm = new VirtualMachine(this, "vm", {
  apiVersion: "2024-07-01",
  // ... properties
});

const analysis = currentVm.analyzeMigrationTo("2024-07-01");
if (analysis.compatible) {
  // Safe to upgrade
  const upgradedVm = new VirtualMachine(this, "vm-upgraded", {
    apiVersion: "2024-07-01",
    // ... same properties
  });
}
```

## Common VM Sizes

### General Purpose

* **B-series**: Burstable (B1s, B2s, B2ms, B4ms)
* **D-series**: General purpose (Standard_D2s_v3, Standard_D4s_v3)

### Compute Optimized

* **F-series**: Compute optimized (Standard_F2s_v2, Standard_F4s_v2)

### Memory Optimized

* **E-series**: Memory optimized (Standard_E2s_v3, Standard_E4s_v3)

### Storage Optimized

* **L-series**: Storage optimized (Standard_L8s_v2, Standard_L16s_v2)

### GPU

* **N-series**: GPU (Standard_NC6, Standard_NV6)

## Best Practices

1. **Use Managed Identities**: Prefer managed identities over service principals
2. **Enable Boot Diagnostics**: Always enable for troubleshooting
3. **Use Premium Storage**: For production workloads
4. **Enable Encryption**: Use encryption at host when possible
5. **Tag Resources**: Use consistent tagging strategy
6. **Lifecycle Management**: Use `ignoreChanges` for properties managed externally
7. **Security**: Enable secure boot and vTPM for supported images
8. **Networking**: Use network security groups and limit public access

## Troubleshooting

### Common Issues

**Issue**: VM provisioning fails

* Check VM size availability in the region
* Verify image reference is valid
* Ensure network interface exists
* Check quota limits

**Issue**: Cannot connect to VM

* Verify network security group rules
* Check boot diagnostics output
* Verify SSH key or password configuration

**Issue**: Disk attachment fails

* Verify LUN numbers are unique
* Check storage account type compatibility
* Ensure disk doesn't already exist

## Networking Architecture

### Network Interface Reference Pattern

Virtual Machines **reference** existing network interfaces by ID rather than creating them inline. This separation provides several benefits:

1. **Reusability**: NICs can be detached and reattached to different VMs
2. **Independent Management**: NICs have their own lifecycle separate from VMs
3. **Type Safety**: Using the dedicated [`NetworkInterface`](../azure-networkinterface/README.md) construct provides proper validation

```python
// ✅ CORRECT: Create NIC separately, reference by ID
const nic = new NetworkInterface(this, "nic", {
  name: "my-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{ /* ... */ }],
});

const vm = new VirtualMachine(this, "vm", {
  // ... other properties
  networkProfile: {
    networkInterfaces: [{
      id: nic.id, // Reference by ID
    }],
  },
});

// ❌ INCORRECT: VMs don't create NICs inline
// Network interfaces must be created separately
```

### Multiple Network Interfaces

VMs can have multiple NICs for different network segments:

```python
const managementNic = new NetworkInterface(this, "mgmt-nic", {
  name: "vm-mgmt-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "mgmt-ip",
    subnet: { id: managementSubnet.id },
    primary: true,
  }],
});

const dataPlaneNic = new NetworkInterface(this, "data-nic", {
  name: "vm-data-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "data-ip",
    subnet: { id: dataSubnet.id },
    primary: false, // Not primary
  }],
});

const vm = new VirtualMachine(this, "vm", {
  // ... other properties
  networkProfile: {
    networkInterfaces: [
      { id: managementNic.id, properties: { primary: true } },
      { id: dataPlaneNic.id, properties: { primary: false } },
    ],
  },
});
```

## Links

* [Azure Virtual Machines Documentation](https://docs.microsoft.com/azure/virtual-machines/)
* [VM Sizes](https://docs.microsoft.com/azure/virtual-machines/sizes)
* [Azure REST API Reference](https://docs.microsoft.com/rest/api/compute/virtual-machines)
* [Network Interface Construct](../azure-networkinterface/README.md)

## License

This construct is part of the terraform-cdk-constructs project.
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from .._jsii import *

import cdktf as _cdktf_9a9027ec
import constructs as _constructs_77d1e7e8
from ..core_azure import (
    ApiSchema as _ApiSchema_5ce0490e,
    AzapiResource as _AzapiResource_7e7f5b39,
    AzapiResourceProps as _AzapiResourceProps_141a2340,
    MonitoringConfig as _MonitoringConfig_7c28df74,
)


class VirtualMachine(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachine",
):
    '''Unified Azure Virtual Machine implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    The class uses the VersionedAzapiResource framework to provide:

    - Automatic latest version resolution (2025-04-01 as of this implementation)
    - Support for explicit version pinning when stability is required
    - Schema-driven property validation and transformation
    - Migration analysis and deprecation warnings
    - Full JSII compliance for multi-language support

    Example::

        // Windows VM with password authentication:
        const windowsVm = new VirtualMachine(this, "windows-vm", {
          name: "my-windows-vm",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          hardwareProfile: {
            vmSize: "Standard_D2s_v3"
          },
          storageProfile: {
            imageReference: {
              publisher: "MicrosoftWindowsServer",
              offer: "WindowsServer",
              sku: "2022-datacenter-azure-edition",
              version: "latest"
            },
            osDisk: {
              createOption: "FromImage",
              managedDisk: {
                storageAccountType: "Premium_LRS"
              }
            }
          },
          osProfile: {
            computerName: "mywinvm",
            adminUsername: "azureuser",
            adminPassword: "P@ssw0rd1234!",
            windowsConfiguration: {
              provisionVMAgent: true,
              enableAutomaticUpdates: true
            }
          },
          networkProfile: {
            networkInterfaces: [{
              id: networkInterface.id
            }]
          },
          licenseType: "Windows_Server"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        hardware_profile: typing.Union["VirtualMachineHardwareProfile", typing.Dict[builtins.str, typing.Any]],
        network_profile: typing.Union["VirtualMachineNetworkProfile", typing.Dict[builtins.str, typing.Any]],
        storage_profile: typing.Union["VirtualMachineStorageProfile", typing.Dict[builtins.str, typing.Any]],
        additional_capabilities: typing.Optional[typing.Union["VirtualMachineAdditionalCapabilities", typing.Dict[builtins.str, typing.Any]]] = None,
        availability_set: typing.Optional[typing.Union["VirtualMachineAvailabilitySetReference", typing.Dict[builtins.str, typing.Any]]] = None,
        billing_profile: typing.Optional[typing.Union["VirtualMachineBillingProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        diagnostics_profile: typing.Optional[typing.Union["VirtualMachineDiagnosticsProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        eviction_policy: typing.Optional[builtins.str] = None,
        host: typing.Optional[typing.Union["VirtualMachineHostReference", typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union["VirtualMachineIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        license_type: typing.Optional[builtins.str] = None,
        os_profile: typing.Optional[typing.Union["VirtualMachineOSProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        plan: typing.Optional[typing.Union["VirtualMachinePlan", typing.Dict[builtins.str, typing.Any]]] = None,
        priority: typing.Optional[builtins.str] = None,
        proximity_placement_group: typing.Optional[typing.Union["VirtualMachineProximityPlacementGroupReference", typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        security_profile: typing.Optional[typing.Union["VirtualMachineSecurityProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        virtual_machine_scale_set: typing.Optional[typing.Union["VirtualMachineScaleSetReference", typing.Dict[builtins.str, typing.Any]]] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
        api_version: typing.Optional[builtins.str] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        location: typing.Optional[builtins.str] = None,
        monitoring: typing.Optional[typing.Union[_MonitoringConfig_7c28df74, typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Creates a new Azure Virtual Machine using the VersionedAzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param hardware_profile: The hardware profile for the Virtual Machine (VM size).
        :param network_profile: The network profile for the Virtual Machine Defines network interfaces attached to the VM.
        :param storage_profile: The storage profile for the Virtual Machine Defines the OS disk, data disks, and image reference.
        :param additional_capabilities: Additional capabilities like Ultra SSD.
        :param availability_set: Reference to an availability set.
        :param billing_profile: The billing profile for Spot VMs.
        :param diagnostics_profile: The diagnostics profile for boot diagnostics.
        :param eviction_policy: The eviction policy for Spot VMs.
        :param host: Reference to a dedicated host.
        :param identity: The identity configuration for the Virtual Machine.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed or should not trigger updates.
        :param license_type: License type for Windows VMs.
        :param os_profile: The OS profile for the Virtual Machine Defines computer name, admin credentials, and OS-specific configuration.
        :param plan: Plan information for marketplace images.
        :param priority: The priority of the Virtual Machine. Default: "Regular"
        :param proximity_placement_group: Reference to a proximity placement group.
        :param resource_group_id: Resource group ID where the Virtual Machine will be created.
        :param security_profile: Security settings for the Virtual Machine.
        :param virtual_machine_scale_set: Reference to a virtual machine scale set.
        :param zones: Availability zones for the Virtual Machine.
        :param api_version: Explicit API version to use for this resource. If not specified, the latest active version will be automatically resolved. Use this for version pinning when stability is required over latest features. Default: Latest active version from ApiVersionManager
        :param enable_migration_analysis: Whether to enable migration analysis warnings. When true, the framework will analyze the current version for deprecation status and provide migration recommendations in the deployment output. Default: true
        :param enable_transformation: Whether to apply property transformations automatically. When true, properties will be automatically transformed according to the target schema's transformation rules. This enables backward compatibility. Default: true
        :param enable_validation: Whether to validate properties against the schema. When true, all properties will be validated against the API schema before resource creation. Validation errors will cause deployment failures. Default: true
        :param location: The location where the resource should be created. Default: Varies by resource type - see specific resource documentation
        :param monitoring: Monitoring configuration for this resource. Enables integrated monitoring with diagnostic settings, metric alerts, and activity log alerts. All monitoring is optional and disabled by default.
        :param name: The name of the resource.
        :param tags: Tags to apply to the resource.
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__438bd5f5eb90ef4fe755b2ca7e07b03af0a1c21dc2ef1ee144ec35ee234b8ed9)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VirtualMachineProps(
            hardware_profile=hardware_profile,
            network_profile=network_profile,
            storage_profile=storage_profile,
            additional_capabilities=additional_capabilities,
            availability_set=availability_set,
            billing_profile=billing_profile,
            diagnostics_profile=diagnostics_profile,
            eviction_policy=eviction_policy,
            host=host,
            identity=identity,
            ignore_changes=ignore_changes,
            license_type=license_type,
            os_profile=os_profile,
            plan=plan,
            priority=priority,
            proximity_placement_group=proximity_placement_group,
            resource_group_id=resource_group_id,
            security_profile=security_profile,
            virtual_machine_scale_set=virtual_machine_scale_set,
            zones=zones,
            api_version=api_version,
            enable_migration_analysis=enable_migration_analysis,
            enable_transformation=enable_transformation,
            enable_validation=enable_validation,
            location=location,
            monitoring=monitoring,
            name=name,
            tags=tags,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="defaultMonitoring")
    @builtins.classmethod
    def default_monitoring(
        cls,
        action_group_id: builtins.str,
        workspace_id: typing.Optional[builtins.str] = None,
        *,
        cpu_alert_severity: typing.Optional[jsii.Number] = None,
        cpu_threshold: typing.Optional[jsii.Number] = None,
        disk_queue_alert_severity: typing.Optional[jsii.Number] = None,
        disk_queue_threshold: typing.Optional[jsii.Number] = None,
        enable_cpu_alert: typing.Optional[builtins.bool] = None,
        enable_deletion_alert: typing.Optional[builtins.bool] = None,
        enable_disk_queue_alert: typing.Optional[builtins.bool] = None,
        enable_memory_alert: typing.Optional[builtins.bool] = None,
        memory_alert_severity: typing.Optional[jsii.Number] = None,
        memory_threshold: typing.Optional[jsii.Number] = None,
    ) -> _MonitoringConfig_7c28df74:
        '''Returns a production-ready monitoring configuration for Virtual Machines.

        This static factory method provides a complete MonitoringConfig with sensible defaults
        for VM monitoring including CPU, memory, disk queue alerts, and deletion tracking.

        :param action_group_id: - The resource ID of the action group for alert notifications.
        :param workspace_id: - Optional Log Analytics workspace ID for diagnostic settings.
        :param cpu_alert_severity: 
        :param cpu_threshold: 
        :param disk_queue_alert_severity: 
        :param disk_queue_threshold: 
        :param enable_cpu_alert: 
        :param enable_deletion_alert: 
        :param enable_disk_queue_alert: 
        :param enable_memory_alert: 
        :param memory_alert_severity: 
        :param memory_threshold: 

        :return: A complete MonitoringConfig object ready to use in VirtualMachine props

        Example::

            // Custom thresholds
            const vm = new VirtualMachine(this, "vm", {
              // ... other properties ...
              monitoring: VirtualMachine.defaultMonitoring(
                actionGroup.id,
                workspace.id,
                {
                  cpuThreshold: 90,
                  memoryThreshold: 536870912, // 512MB
                  enableDiskQueueAlert: false
                }
              )
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__284acdb9e0713cc6f00537edbbe63820442476c7c588ddf2ba386dd409e39c09)
            check_type(argname="argument action_group_id", value=action_group_id, expected_type=type_hints["action_group_id"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
        options = VirtualMachineMonitoringOptions(
            cpu_alert_severity=cpu_alert_severity,
            cpu_threshold=cpu_threshold,
            disk_queue_alert_severity=disk_queue_alert_severity,
            disk_queue_threshold=disk_queue_threshold,
            enable_cpu_alert=enable_cpu_alert,
            enable_deletion_alert=enable_deletion_alert,
            enable_disk_queue_alert=enable_disk_queue_alert,
            enable_memory_alert=enable_memory_alert,
            memory_alert_severity=memory_alert_severity,
            memory_threshold=memory_threshold,
        )

        return typing.cast(_MonitoringConfig_7c28df74, jsii.sinvoke(cls, "defaultMonitoring", [action_group_id, workspace_id, options]))

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Add a tag to the Virtual Machine Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3bbfa912b420d66eb2516202ade284dfdfcdb8c1011dcec535bd75c0cb0d2e04)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "addTag", [key, value]))

    @jsii.member(jsii_name="apiSchema")
    def _api_schema(self) -> _ApiSchema_5ce0490e:
        '''Gets the API schema for the resolved version Uses the framework's schema resolution to get the appropriate schema.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call Transforms the input properties into the JSON format expected by Azure REST API.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ab197388e895c255303b05c028e1de2c88ff2b392d317a0a476628d4eda96fda)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Virtual Machine Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__90de9c3a12c873e91e99cb467582a2e384b35149f4dc9e91895312422a8d322b)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Virtual Machines.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Machines.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="locationOutput")
    def location_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "locationOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "VirtualMachineProps":
        '''The input properties for this Virtual Machine instance.'''
        return typing.cast("VirtualMachineProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Virtual Machine.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))

    @builtins.property
    @jsii.member(jsii_name="vmId")
    def vm_id(self) -> builtins.str:
        '''Get the VM ID (unique identifier assigned by Azure).'''
        return typing.cast(builtins.str, jsii.get(self, "vmId"))

    @builtins.property
    @jsii.member(jsii_name="vmIdOutput")
    def vm_id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "vmIdOutput"))

    @builtins.property
    @jsii.member(jsii_name="vmSize")
    def vm_size(self) -> builtins.str:
        '''Get the VM size.'''
        return typing.cast(builtins.str, jsii.get(self, "vmSize"))

    @builtins.property
    @jsii.member(jsii_name="computerName")
    def computer_name(self) -> typing.Optional[builtins.str]:
        '''Get the OS profile computer name.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "computerName"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineAdditionalCapabilities",
    jsii_struct_bases=[],
    name_mapping={
        "hibernation_enabled": "hibernationEnabled",
        "ultra_ssd_enabled": "ultraSSDEnabled",
    },
)
class VirtualMachineAdditionalCapabilities:
    def __init__(
        self,
        *,
        hibernation_enabled: typing.Optional[builtins.bool] = None,
        ultra_ssd_enabled: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Additional capabilities.

        :param hibernation_enabled: 
        :param ultra_ssd_enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0535843142573bacaa96574935d94b8ce81594ca4d27b68c39f2cae82e2d36ab)
            check_type(argname="argument hibernation_enabled", value=hibernation_enabled, expected_type=type_hints["hibernation_enabled"])
            check_type(argname="argument ultra_ssd_enabled", value=ultra_ssd_enabled, expected_type=type_hints["ultra_ssd_enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if hibernation_enabled is not None:
            self._values["hibernation_enabled"] = hibernation_enabled
        if ultra_ssd_enabled is not None:
            self._values["ultra_ssd_enabled"] = ultra_ssd_enabled

    @builtins.property
    def hibernation_enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("hibernation_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ultra_ssd_enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("ultra_ssd_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineAdditionalCapabilities(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineAvailabilitySetReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualMachineAvailabilitySetReference:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Availability set reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d95df1465def445c09ba6a0721ef6ed830a55854cf6d83ef1f84344288588f63)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineAvailabilitySetReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineBillingProfile",
    jsii_struct_bases=[],
    name_mapping={"max_price": "maxPrice"},
)
class VirtualMachineBillingProfile:
    def __init__(self, *, max_price: typing.Optional[jsii.Number] = None) -> None:
        '''Billing profile for spot VMs.

        :param max_price: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d0d4da7eef9a215e7268afbe076ec0edc86aaf9b35ed48f6ea411bfc1f60c7c)
            check_type(argname="argument max_price", value=max_price, expected_type=type_hints["max_price"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if max_price is not None:
            self._values["max_price"] = max_price

    @builtins.property
    def max_price(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("max_price")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineBillingProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineBody",
    jsii_struct_bases=[],
    name_mapping={
        "location": "location",
        "properties": "properties",
        "identity": "identity",
        "plan": "plan",
        "tags": "tags",
        "zones": "zones",
    },
)
class VirtualMachineBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["VirtualMachineBodyProperties", typing.Dict[builtins.str, typing.Any]],
        identity: typing.Optional[typing.Union["VirtualMachineIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        plan: typing.Optional[typing.Union["VirtualMachinePlan", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Virtual Machine API calls.

        :param location: 
        :param properties: 
        :param identity: 
        :param plan: 
        :param tags: 
        :param zones: 
        '''
        if isinstance(properties, dict):
            properties = VirtualMachineBodyProperties(**properties)
        if isinstance(identity, dict):
            identity = VirtualMachineIdentity(**identity)
        if isinstance(plan, dict):
            plan = VirtualMachinePlan(**plan)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__09520373190ef38630c48497a5af8d8059b1071638fa0b0d75f9a2157a2a5548)
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument plan", value=plan, expected_type=type_hints["plan"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument zones", value=zones, expected_type=type_hints["zones"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "location": location,
            "properties": properties,
        }
        if identity is not None:
            self._values["identity"] = identity
        if plan is not None:
            self._values["plan"] = plan
        if tags is not None:
            self._values["tags"] = tags
        if zones is not None:
            self._values["zones"] = zones

    @builtins.property
    def location(self) -> builtins.str:
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> "VirtualMachineBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("VirtualMachineBodyProperties", result)

    @builtins.property
    def identity(self) -> typing.Optional["VirtualMachineIdentity"]:
        result = self._values.get("identity")
        return typing.cast(typing.Optional["VirtualMachineIdentity"], result)

    @builtins.property
    def plan(self) -> typing.Optional["VirtualMachinePlan"]:
        result = self._values.get("plan")
        return typing.cast(typing.Optional["VirtualMachinePlan"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def zones(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("zones")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "hardware_profile": "hardwareProfile",
        "network_profile": "networkProfile",
        "storage_profile": "storageProfile",
        "additional_capabilities": "additionalCapabilities",
        "availability_set": "availabilitySet",
        "billing_profile": "billingProfile",
        "diagnostics_profile": "diagnosticsProfile",
        "eviction_policy": "evictionPolicy",
        "host": "host",
        "license_type": "licenseType",
        "os_profile": "osProfile",
        "priority": "priority",
        "proximity_placement_group": "proximityPlacementGroup",
        "security_profile": "securityProfile",
        "virtual_machine_scale_set": "virtualMachineScaleSet",
    },
)
class VirtualMachineBodyProperties:
    def __init__(
        self,
        *,
        hardware_profile: typing.Union["VirtualMachineHardwareProfile", typing.Dict[builtins.str, typing.Any]],
        network_profile: typing.Union["VirtualMachineNetworkProfile", typing.Dict[builtins.str, typing.Any]],
        storage_profile: typing.Union["VirtualMachineStorageProfile", typing.Dict[builtins.str, typing.Any]],
        additional_capabilities: typing.Optional[typing.Union[VirtualMachineAdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
        availability_set: typing.Optional[typing.Union[VirtualMachineAvailabilitySetReference, typing.Dict[builtins.str, typing.Any]]] = None,
        billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        diagnostics_profile: typing.Optional[typing.Union["VirtualMachineDiagnosticsProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        eviction_policy: typing.Optional[builtins.str] = None,
        host: typing.Optional[typing.Union["VirtualMachineHostReference", typing.Dict[builtins.str, typing.Any]]] = None,
        license_type: typing.Optional[builtins.str] = None,
        os_profile: typing.Optional[typing.Union["VirtualMachineOSProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        priority: typing.Optional[builtins.str] = None,
        proximity_placement_group: typing.Optional[typing.Union["VirtualMachineProximityPlacementGroupReference", typing.Dict[builtins.str, typing.Any]]] = None,
        security_profile: typing.Optional[typing.Union["VirtualMachineSecurityProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        virtual_machine_scale_set: typing.Optional[typing.Union["VirtualMachineScaleSetReference", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Virtual Machine properties for the request body.

        :param hardware_profile: 
        :param network_profile: 
        :param storage_profile: 
        :param additional_capabilities: 
        :param availability_set: 
        :param billing_profile: 
        :param diagnostics_profile: 
        :param eviction_policy: 
        :param host: 
        :param license_type: 
        :param os_profile: 
        :param priority: 
        :param proximity_placement_group: 
        :param security_profile: 
        :param virtual_machine_scale_set: 
        '''
        if isinstance(hardware_profile, dict):
            hardware_profile = VirtualMachineHardwareProfile(**hardware_profile)
        if isinstance(network_profile, dict):
            network_profile = VirtualMachineNetworkProfile(**network_profile)
        if isinstance(storage_profile, dict):
            storage_profile = VirtualMachineStorageProfile(**storage_profile)
        if isinstance(additional_capabilities, dict):
            additional_capabilities = VirtualMachineAdditionalCapabilities(**additional_capabilities)
        if isinstance(availability_set, dict):
            availability_set = VirtualMachineAvailabilitySetReference(**availability_set)
        if isinstance(billing_profile, dict):
            billing_profile = VirtualMachineBillingProfile(**billing_profile)
        if isinstance(diagnostics_profile, dict):
            diagnostics_profile = VirtualMachineDiagnosticsProfile(**diagnostics_profile)
        if isinstance(host, dict):
            host = VirtualMachineHostReference(**host)
        if isinstance(os_profile, dict):
            os_profile = VirtualMachineOSProfile(**os_profile)
        if isinstance(proximity_placement_group, dict):
            proximity_placement_group = VirtualMachineProximityPlacementGroupReference(**proximity_placement_group)
        if isinstance(security_profile, dict):
            security_profile = VirtualMachineSecurityProfile(**security_profile)
        if isinstance(virtual_machine_scale_set, dict):
            virtual_machine_scale_set = VirtualMachineScaleSetReference(**virtual_machine_scale_set)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5d45f524051568b58232171ab2104d5c535d2b911c905f45799c50b81051475)
            check_type(argname="argument hardware_profile", value=hardware_profile, expected_type=type_hints["hardware_profile"])
            check_type(argname="argument network_profile", value=network_profile, expected_type=type_hints["network_profile"])
            check_type(argname="argument storage_profile", value=storage_profile, expected_type=type_hints["storage_profile"])
            check_type(argname="argument additional_capabilities", value=additional_capabilities, expected_type=type_hints["additional_capabilities"])
            check_type(argname="argument availability_set", value=availability_set, expected_type=type_hints["availability_set"])
            check_type(argname="argument billing_profile", value=billing_profile, expected_type=type_hints["billing_profile"])
            check_type(argname="argument diagnostics_profile", value=diagnostics_profile, expected_type=type_hints["diagnostics_profile"])
            check_type(argname="argument eviction_policy", value=eviction_policy, expected_type=type_hints["eviction_policy"])
            check_type(argname="argument host", value=host, expected_type=type_hints["host"])
            check_type(argname="argument license_type", value=license_type, expected_type=type_hints["license_type"])
            check_type(argname="argument os_profile", value=os_profile, expected_type=type_hints["os_profile"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument proximity_placement_group", value=proximity_placement_group, expected_type=type_hints["proximity_placement_group"])
            check_type(argname="argument security_profile", value=security_profile, expected_type=type_hints["security_profile"])
            check_type(argname="argument virtual_machine_scale_set", value=virtual_machine_scale_set, expected_type=type_hints["virtual_machine_scale_set"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "hardware_profile": hardware_profile,
            "network_profile": network_profile,
            "storage_profile": storage_profile,
        }
        if additional_capabilities is not None:
            self._values["additional_capabilities"] = additional_capabilities
        if availability_set is not None:
            self._values["availability_set"] = availability_set
        if billing_profile is not None:
            self._values["billing_profile"] = billing_profile
        if diagnostics_profile is not None:
            self._values["diagnostics_profile"] = diagnostics_profile
        if eviction_policy is not None:
            self._values["eviction_policy"] = eviction_policy
        if host is not None:
            self._values["host"] = host
        if license_type is not None:
            self._values["license_type"] = license_type
        if os_profile is not None:
            self._values["os_profile"] = os_profile
        if priority is not None:
            self._values["priority"] = priority
        if proximity_placement_group is not None:
            self._values["proximity_placement_group"] = proximity_placement_group
        if security_profile is not None:
            self._values["security_profile"] = security_profile
        if virtual_machine_scale_set is not None:
            self._values["virtual_machine_scale_set"] = virtual_machine_scale_set

    @builtins.property
    def hardware_profile(self) -> "VirtualMachineHardwareProfile":
        result = self._values.get("hardware_profile")
        assert result is not None, "Required property 'hardware_profile' is missing"
        return typing.cast("VirtualMachineHardwareProfile", result)

    @builtins.property
    def network_profile(self) -> "VirtualMachineNetworkProfile":
        result = self._values.get("network_profile")
        assert result is not None, "Required property 'network_profile' is missing"
        return typing.cast("VirtualMachineNetworkProfile", result)

    @builtins.property
    def storage_profile(self) -> "VirtualMachineStorageProfile":
        result = self._values.get("storage_profile")
        assert result is not None, "Required property 'storage_profile' is missing"
        return typing.cast("VirtualMachineStorageProfile", result)

    @builtins.property
    def additional_capabilities(
        self,
    ) -> typing.Optional[VirtualMachineAdditionalCapabilities]:
        result = self._values.get("additional_capabilities")
        return typing.cast(typing.Optional[VirtualMachineAdditionalCapabilities], result)

    @builtins.property
    def availability_set(
        self,
    ) -> typing.Optional[VirtualMachineAvailabilitySetReference]:
        result = self._values.get("availability_set")
        return typing.cast(typing.Optional[VirtualMachineAvailabilitySetReference], result)

    @builtins.property
    def billing_profile(self) -> typing.Optional[VirtualMachineBillingProfile]:
        result = self._values.get("billing_profile")
        return typing.cast(typing.Optional[VirtualMachineBillingProfile], result)

    @builtins.property
    def diagnostics_profile(
        self,
    ) -> typing.Optional["VirtualMachineDiagnosticsProfile"]:
        result = self._values.get("diagnostics_profile")
        return typing.cast(typing.Optional["VirtualMachineDiagnosticsProfile"], result)

    @builtins.property
    def eviction_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("eviction_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def host(self) -> typing.Optional["VirtualMachineHostReference"]:
        result = self._values.get("host")
        return typing.cast(typing.Optional["VirtualMachineHostReference"], result)

    @builtins.property
    def license_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("license_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def os_profile(self) -> typing.Optional["VirtualMachineOSProfile"]:
        result = self._values.get("os_profile")
        return typing.cast(typing.Optional["VirtualMachineOSProfile"], result)

    @builtins.property
    def priority(self) -> typing.Optional[builtins.str]:
        result = self._values.get("priority")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def proximity_placement_group(
        self,
    ) -> typing.Optional["VirtualMachineProximityPlacementGroupReference"]:
        result = self._values.get("proximity_placement_group")
        return typing.cast(typing.Optional["VirtualMachineProximityPlacementGroupReference"], result)

    @builtins.property
    def security_profile(self) -> typing.Optional["VirtualMachineSecurityProfile"]:
        result = self._values.get("security_profile")
        return typing.cast(typing.Optional["VirtualMachineSecurityProfile"], result)

    @builtins.property
    def virtual_machine_scale_set(
        self,
    ) -> typing.Optional["VirtualMachineScaleSetReference"]:
        result = self._values.get("virtual_machine_scale_set")
        return typing.cast(typing.Optional["VirtualMachineScaleSetReference"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineBootDiagnostics",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled", "storage_uri": "storageUri"},
)
class VirtualMachineBootDiagnostics:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        storage_uri: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Boot diagnostics configuration.

        :param enabled: 
        :param storage_uri: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__34ecb938455456698f2ca7b671bd726c284cdb868cd9faf9f96fbb1b26768eea)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument storage_uri", value=storage_uri, expected_type=type_hints["storage_uri"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if storage_uri is not None:
            self._values["storage_uri"] = storage_uri

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def storage_uri(self) -> typing.Optional[builtins.str]:
        result = self._values.get("storage_uri")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineBootDiagnostics(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineDataDisk",
    jsii_struct_bases=[],
    name_mapping={
        "create_option": "createOption",
        "lun": "lun",
        "caching": "caching",
        "disk_size_gb": "diskSizeGB",
        "managed_disk": "managedDisk",
        "name": "name",
    },
)
class VirtualMachineDataDisk:
    def __init__(
        self,
        *,
        create_option: builtins.str,
        lun: jsii.Number,
        caching: typing.Optional[builtins.str] = None,
        disk_size_gb: typing.Optional[jsii.Number] = None,
        managed_disk: typing.Optional[typing.Union["VirtualMachineManagedDiskParameters", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Data disk configuration.

        :param create_option: 
        :param lun: 
        :param caching: 
        :param disk_size_gb: 
        :param managed_disk: 
        :param name: 
        '''
        if isinstance(managed_disk, dict):
            managed_disk = VirtualMachineManagedDiskParameters(**managed_disk)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f5a8487bb5daf5c3d2ac9e2c89f07f5e33122b0083fd86a920eb3bbdf04e43c5)
            check_type(argname="argument create_option", value=create_option, expected_type=type_hints["create_option"])
            check_type(argname="argument lun", value=lun, expected_type=type_hints["lun"])
            check_type(argname="argument caching", value=caching, expected_type=type_hints["caching"])
            check_type(argname="argument disk_size_gb", value=disk_size_gb, expected_type=type_hints["disk_size_gb"])
            check_type(argname="argument managed_disk", value=managed_disk, expected_type=type_hints["managed_disk"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "create_option": create_option,
            "lun": lun,
        }
        if caching is not None:
            self._values["caching"] = caching
        if disk_size_gb is not None:
            self._values["disk_size_gb"] = disk_size_gb
        if managed_disk is not None:
            self._values["managed_disk"] = managed_disk
        if name is not None:
            self._values["name"] = name

    @builtins.property
    def create_option(self) -> builtins.str:
        result = self._values.get("create_option")
        assert result is not None, "Required property 'create_option' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def lun(self) -> jsii.Number:
        result = self._values.get("lun")
        assert result is not None, "Required property 'lun' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def caching(self) -> typing.Optional[builtins.str]:
        result = self._values.get("caching")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def disk_size_gb(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("disk_size_gb")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def managed_disk(self) -> typing.Optional["VirtualMachineManagedDiskParameters"]:
        result = self._values.get("managed_disk")
        return typing.cast(typing.Optional["VirtualMachineManagedDiskParameters"], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineDataDisk(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineDiagnosticsProfile",
    jsii_struct_bases=[],
    name_mapping={"boot_diagnostics": "bootDiagnostics"},
)
class VirtualMachineDiagnosticsProfile:
    def __init__(
        self,
        *,
        boot_diagnostics: typing.Optional[typing.Union[VirtualMachineBootDiagnostics, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Diagnostics profile.

        :param boot_diagnostics: 
        '''
        if isinstance(boot_diagnostics, dict):
            boot_diagnostics = VirtualMachineBootDiagnostics(**boot_diagnostics)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b8a7606fb8c04f63035ed80b68b434745415882ed017ee0f81d2434ff6b00ad0)
            check_type(argname="argument boot_diagnostics", value=boot_diagnostics, expected_type=type_hints["boot_diagnostics"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if boot_diagnostics is not None:
            self._values["boot_diagnostics"] = boot_diagnostics

    @builtins.property
    def boot_diagnostics(self) -> typing.Optional[VirtualMachineBootDiagnostics]:
        result = self._values.get("boot_diagnostics")
        return typing.cast(typing.Optional[VirtualMachineBootDiagnostics], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineDiagnosticsProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineDiskEncryptionSetParameters",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualMachineDiskEncryptionSetParameters:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Disk encryption set parameters.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__46d3cac574ccab9a26813941420ae74fd8923f7e0c23d6af2fdac04650299b98)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineDiskEncryptionSetParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineHardwareProfile",
    jsii_struct_bases=[],
    name_mapping={"vm_size": "vmSize"},
)
class VirtualMachineHardwareProfile:
    def __init__(self, *, vm_size: builtins.str) -> None:
        '''Hardware profile for the virtual machine.

        :param vm_size: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3612ee16f331f4b6766c8e5763572fc70811f182437935c54af982bd7d0329c)
            check_type(argname="argument vm_size", value=vm_size, expected_type=type_hints["vm_size"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "vm_size": vm_size,
        }

    @builtins.property
    def vm_size(self) -> builtins.str:
        result = self._values.get("vm_size")
        assert result is not None, "Required property 'vm_size' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineHardwareProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineHostReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualMachineHostReference:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Host reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2976ef2f0722e68a49eda21313757206a495b5022fc913129207aed6f21ac3a0)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineHostReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineIdentity",
    jsii_struct_bases=[],
    name_mapping={
        "type": "type",
        "user_assigned_identities": "userAssignedIdentities",
    },
)
class VirtualMachineIdentity:
    def __init__(
        self,
        *,
        type: builtins.str,
        user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    ) -> None:
        '''Identity configuration for the virtual machine.

        :param type: 
        :param user_assigned_identities: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cbf3c03eea87825c0d3a5f3a45cd8db4b3c9a70f52e618b060bc44463f6a9857)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument user_assigned_identities", value=user_assigned_identities, expected_type=type_hints["user_assigned_identities"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }
        if user_assigned_identities is not None:
            self._values["user_assigned_identities"] = user_assigned_identities

    @builtins.property
    def type(self) -> builtins.str:
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def user_assigned_identities(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        result = self._values.get("user_assigned_identities")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineImageReference",
    jsii_struct_bases=[],
    name_mapping={
        "id": "id",
        "offer": "offer",
        "publisher": "publisher",
        "sku": "sku",
        "version": "version",
    },
)
class VirtualMachineImageReference:
    def __init__(
        self,
        *,
        id: typing.Optional[builtins.str] = None,
        offer: typing.Optional[builtins.str] = None,
        publisher: typing.Optional[builtins.str] = None,
        sku: typing.Optional[builtins.str] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Image reference for OS disk.

        :param id: 
        :param offer: 
        :param publisher: 
        :param sku: 
        :param version: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__16bfb28d2cc9b5102816ae149aec3a267e23c94f500a20850728c6836ee8e3ac)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument offer", value=offer, expected_type=type_hints["offer"])
            check_type(argname="argument publisher", value=publisher, expected_type=type_hints["publisher"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id
        if offer is not None:
            self._values["offer"] = offer
        if publisher is not None:
            self._values["publisher"] = publisher
        if sku is not None:
            self._values["sku"] = sku
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def offer(self) -> typing.Optional[builtins.str]:
        result = self._values.get("offer")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def publisher(self) -> typing.Optional[builtins.str]:
        result = self._values.get("publisher")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sku(self) -> typing.Optional[builtins.str]:
        result = self._values.get("sku")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineImageReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineLinuxConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "disable_password_authentication": "disablePasswordAuthentication",
        "patch_settings": "patchSettings",
        "provision_vm_agent": "provisionVMAgent",
        "ssh": "ssh",
    },
)
class VirtualMachineLinuxConfiguration:
    def __init__(
        self,
        *,
        disable_password_authentication: typing.Optional[builtins.bool] = None,
        patch_settings: typing.Optional[typing.Union["VirtualMachineLinuxPatchSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        provision_vm_agent: typing.Optional[builtins.bool] = None,
        ssh: typing.Optional[typing.Union["VirtualMachineSshConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Linux configuration.

        :param disable_password_authentication: 
        :param patch_settings: 
        :param provision_vm_agent: 
        :param ssh: 
        '''
        if isinstance(patch_settings, dict):
            patch_settings = VirtualMachineLinuxPatchSettings(**patch_settings)
        if isinstance(ssh, dict):
            ssh = VirtualMachineSshConfiguration(**ssh)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa77674d96fbe349d8be4ef95aad539c498173cc9449abc5a0556fc712504219)
            check_type(argname="argument disable_password_authentication", value=disable_password_authentication, expected_type=type_hints["disable_password_authentication"])
            check_type(argname="argument patch_settings", value=patch_settings, expected_type=type_hints["patch_settings"])
            check_type(argname="argument provision_vm_agent", value=provision_vm_agent, expected_type=type_hints["provision_vm_agent"])
            check_type(argname="argument ssh", value=ssh, expected_type=type_hints["ssh"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if disable_password_authentication is not None:
            self._values["disable_password_authentication"] = disable_password_authentication
        if patch_settings is not None:
            self._values["patch_settings"] = patch_settings
        if provision_vm_agent is not None:
            self._values["provision_vm_agent"] = provision_vm_agent
        if ssh is not None:
            self._values["ssh"] = ssh

    @builtins.property
    def disable_password_authentication(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("disable_password_authentication")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def patch_settings(self) -> typing.Optional["VirtualMachineLinuxPatchSettings"]:
        result = self._values.get("patch_settings")
        return typing.cast(typing.Optional["VirtualMachineLinuxPatchSettings"], result)

    @builtins.property
    def provision_vm_agent(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("provision_vm_agent")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ssh(self) -> typing.Optional["VirtualMachineSshConfiguration"]:
        result = self._values.get("ssh")
        return typing.cast(typing.Optional["VirtualMachineSshConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineLinuxConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineLinuxPatchSettings",
    jsii_struct_bases=[],
    name_mapping={"assessment_mode": "assessmentMode", "patch_mode": "patchMode"},
)
class VirtualMachineLinuxPatchSettings:
    def __init__(
        self,
        *,
        assessment_mode: typing.Optional[builtins.str] = None,
        patch_mode: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Linux patch settings.

        :param assessment_mode: 
        :param patch_mode: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2844b57921e0f12a21aa780645b8b02851e094a1996c3943c5db1f772f8587fc)
            check_type(argname="argument assessment_mode", value=assessment_mode, expected_type=type_hints["assessment_mode"])
            check_type(argname="argument patch_mode", value=patch_mode, expected_type=type_hints["patch_mode"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if assessment_mode is not None:
            self._values["assessment_mode"] = assessment_mode
        if patch_mode is not None:
            self._values["patch_mode"] = patch_mode

    @builtins.property
    def assessment_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("assessment_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def patch_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("patch_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineLinuxPatchSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineManagedDiskParameters",
    jsii_struct_bases=[],
    name_mapping={
        "disk_encryption_set": "diskEncryptionSet",
        "id": "id",
        "storage_account_type": "storageAccountType",
    },
)
class VirtualMachineManagedDiskParameters:
    def __init__(
        self,
        *,
        disk_encryption_set: typing.Optional[typing.Union[VirtualMachineDiskEncryptionSetParameters, typing.Dict[builtins.str, typing.Any]]] = None,
        id: typing.Optional[builtins.str] = None,
        storage_account_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Managed disk parameters.

        :param disk_encryption_set: 
        :param id: 
        :param storage_account_type: 
        '''
        if isinstance(disk_encryption_set, dict):
            disk_encryption_set = VirtualMachineDiskEncryptionSetParameters(**disk_encryption_set)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6aad03c839c11caaa212967cf358a463354dd6d8d3f6c36958ca862113c5f4f7)
            check_type(argname="argument disk_encryption_set", value=disk_encryption_set, expected_type=type_hints["disk_encryption_set"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument storage_account_type", value=storage_account_type, expected_type=type_hints["storage_account_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if disk_encryption_set is not None:
            self._values["disk_encryption_set"] = disk_encryption_set
        if id is not None:
            self._values["id"] = id
        if storage_account_type is not None:
            self._values["storage_account_type"] = storage_account_type

    @builtins.property
    def disk_encryption_set(
        self,
    ) -> typing.Optional[VirtualMachineDiskEncryptionSetParameters]:
        result = self._values.get("disk_encryption_set")
        return typing.cast(typing.Optional[VirtualMachineDiskEncryptionSetParameters], result)

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def storage_account_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("storage_account_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineManagedDiskParameters(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineMonitoringOptions",
    jsii_struct_bases=[],
    name_mapping={
        "cpu_alert_severity": "cpuAlertSeverity",
        "cpu_threshold": "cpuThreshold",
        "disk_queue_alert_severity": "diskQueueAlertSeverity",
        "disk_queue_threshold": "diskQueueThreshold",
        "enable_cpu_alert": "enableCpuAlert",
        "enable_deletion_alert": "enableDeletionAlert",
        "enable_disk_queue_alert": "enableDiskQueueAlert",
        "enable_memory_alert": "enableMemoryAlert",
        "memory_alert_severity": "memoryAlertSeverity",
        "memory_threshold": "memoryThreshold",
    },
)
class VirtualMachineMonitoringOptions:
    def __init__(
        self,
        *,
        cpu_alert_severity: typing.Optional[jsii.Number] = None,
        cpu_threshold: typing.Optional[jsii.Number] = None,
        disk_queue_alert_severity: typing.Optional[jsii.Number] = None,
        disk_queue_threshold: typing.Optional[jsii.Number] = None,
        enable_cpu_alert: typing.Optional[builtins.bool] = None,
        enable_deletion_alert: typing.Optional[builtins.bool] = None,
        enable_disk_queue_alert: typing.Optional[builtins.bool] = None,
        enable_memory_alert: typing.Optional[builtins.bool] = None,
        memory_alert_severity: typing.Optional[jsii.Number] = None,
        memory_threshold: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Configuration options for Virtual Machine monitoring.

        :param cpu_alert_severity: 
        :param cpu_threshold: 
        :param disk_queue_alert_severity: 
        :param disk_queue_threshold: 
        :param enable_cpu_alert: 
        :param enable_deletion_alert: 
        :param enable_disk_queue_alert: 
        :param enable_memory_alert: 
        :param memory_alert_severity: 
        :param memory_threshold: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cf60573bc2b5c3f7397636759fc4118e9fa12e10c04e18260e20fffbfa3fd118)
            check_type(argname="argument cpu_alert_severity", value=cpu_alert_severity, expected_type=type_hints["cpu_alert_severity"])
            check_type(argname="argument cpu_threshold", value=cpu_threshold, expected_type=type_hints["cpu_threshold"])
            check_type(argname="argument disk_queue_alert_severity", value=disk_queue_alert_severity, expected_type=type_hints["disk_queue_alert_severity"])
            check_type(argname="argument disk_queue_threshold", value=disk_queue_threshold, expected_type=type_hints["disk_queue_threshold"])
            check_type(argname="argument enable_cpu_alert", value=enable_cpu_alert, expected_type=type_hints["enable_cpu_alert"])
            check_type(argname="argument enable_deletion_alert", value=enable_deletion_alert, expected_type=type_hints["enable_deletion_alert"])
            check_type(argname="argument enable_disk_queue_alert", value=enable_disk_queue_alert, expected_type=type_hints["enable_disk_queue_alert"])
            check_type(argname="argument enable_memory_alert", value=enable_memory_alert, expected_type=type_hints["enable_memory_alert"])
            check_type(argname="argument memory_alert_severity", value=memory_alert_severity, expected_type=type_hints["memory_alert_severity"])
            check_type(argname="argument memory_threshold", value=memory_threshold, expected_type=type_hints["memory_threshold"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if cpu_alert_severity is not None:
            self._values["cpu_alert_severity"] = cpu_alert_severity
        if cpu_threshold is not None:
            self._values["cpu_threshold"] = cpu_threshold
        if disk_queue_alert_severity is not None:
            self._values["disk_queue_alert_severity"] = disk_queue_alert_severity
        if disk_queue_threshold is not None:
            self._values["disk_queue_threshold"] = disk_queue_threshold
        if enable_cpu_alert is not None:
            self._values["enable_cpu_alert"] = enable_cpu_alert
        if enable_deletion_alert is not None:
            self._values["enable_deletion_alert"] = enable_deletion_alert
        if enable_disk_queue_alert is not None:
            self._values["enable_disk_queue_alert"] = enable_disk_queue_alert
        if enable_memory_alert is not None:
            self._values["enable_memory_alert"] = enable_memory_alert
        if memory_alert_severity is not None:
            self._values["memory_alert_severity"] = memory_alert_severity
        if memory_threshold is not None:
            self._values["memory_threshold"] = memory_threshold

    @builtins.property
    def cpu_alert_severity(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("cpu_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def cpu_threshold(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("cpu_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def disk_queue_alert_severity(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("disk_queue_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def disk_queue_threshold(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("disk_queue_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def enable_cpu_alert(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_cpu_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_deletion_alert(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_deletion_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_disk_queue_alert(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_disk_queue_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_memory_alert(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_memory_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def memory_alert_severity(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("memory_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def memory_threshold(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("memory_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineMonitoringOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineNetworkInterfaceProperties",
    jsii_struct_bases=[],
    name_mapping={"primary": "primary"},
)
class VirtualMachineNetworkInterfaceProperties:
    def __init__(self, *, primary: typing.Optional[builtins.bool] = None) -> None:
        '''Network interface properties.

        :param primary: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6623f0c6fe6e5e1b3d0872cf110cf18e13543b2fd0e9753f208a4674637e7762)
            check_type(argname="argument primary", value=primary, expected_type=type_hints["primary"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if primary is not None:
            self._values["primary"] = primary

    @builtins.property
    def primary(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("primary")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineNetworkInterfaceProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineNetworkInterfaceReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id", "properties": "properties"},
)
class VirtualMachineNetworkInterfaceReference:
    def __init__(
        self,
        *,
        id: builtins.str,
        properties: typing.Optional[typing.Union[VirtualMachineNetworkInterfaceProperties, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Network interface reference.

        :param id: 
        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = VirtualMachineNetworkInterfaceProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e7ffad6ca3f3e79ed45b41dadd11288c90b6c5ec3b040006e54284a38a40074d)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }
        if properties is not None:
            self._values["properties"] = properties

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> typing.Optional[VirtualMachineNetworkInterfaceProperties]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional[VirtualMachineNetworkInterfaceProperties], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineNetworkInterfaceReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineNetworkProfile",
    jsii_struct_bases=[],
    name_mapping={"network_interfaces": "networkInterfaces"},
)
class VirtualMachineNetworkProfile:
    def __init__(
        self,
        *,
        network_interfaces: typing.Sequence[typing.Union[VirtualMachineNetworkInterfaceReference, typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''Network profile for the virtual machine.

        :param network_interfaces: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f0450bb93bc2e369b3c947237c48ae0be7f52ba28efcac1d240e752ad14d5e28)
            check_type(argname="argument network_interfaces", value=network_interfaces, expected_type=type_hints["network_interfaces"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_interfaces": network_interfaces,
        }

    @builtins.property
    def network_interfaces(
        self,
    ) -> typing.List[VirtualMachineNetworkInterfaceReference]:
        result = self._values.get("network_interfaces")
        assert result is not None, "Required property 'network_interfaces' is missing"
        return typing.cast(typing.List[VirtualMachineNetworkInterfaceReference], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineNetworkProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineOSDisk",
    jsii_struct_bases=[],
    name_mapping={
        "create_option": "createOption",
        "caching": "caching",
        "disk_size_gb": "diskSizeGB",
        "managed_disk": "managedDisk",
        "name": "name",
        "os_type": "osType",
    },
)
class VirtualMachineOSDisk:
    def __init__(
        self,
        *,
        create_option: builtins.str,
        caching: typing.Optional[builtins.str] = None,
        disk_size_gb: typing.Optional[jsii.Number] = None,
        managed_disk: typing.Optional[typing.Union[VirtualMachineManagedDiskParameters, typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        os_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''OS disk configuration.

        :param create_option: 
        :param caching: 
        :param disk_size_gb: 
        :param managed_disk: 
        :param name: 
        :param os_type: 
        '''
        if isinstance(managed_disk, dict):
            managed_disk = VirtualMachineManagedDiskParameters(**managed_disk)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0c2d5267c4ab60ab13e4a47e55737d8875e995e9b139e98e8b9216999ce41fc)
            check_type(argname="argument create_option", value=create_option, expected_type=type_hints["create_option"])
            check_type(argname="argument caching", value=caching, expected_type=type_hints["caching"])
            check_type(argname="argument disk_size_gb", value=disk_size_gb, expected_type=type_hints["disk_size_gb"])
            check_type(argname="argument managed_disk", value=managed_disk, expected_type=type_hints["managed_disk"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument os_type", value=os_type, expected_type=type_hints["os_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "create_option": create_option,
        }
        if caching is not None:
            self._values["caching"] = caching
        if disk_size_gb is not None:
            self._values["disk_size_gb"] = disk_size_gb
        if managed_disk is not None:
            self._values["managed_disk"] = managed_disk
        if name is not None:
            self._values["name"] = name
        if os_type is not None:
            self._values["os_type"] = os_type

    @builtins.property
    def create_option(self) -> builtins.str:
        result = self._values.get("create_option")
        assert result is not None, "Required property 'create_option' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def caching(self) -> typing.Optional[builtins.str]:
        result = self._values.get("caching")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def disk_size_gb(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("disk_size_gb")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def managed_disk(self) -> typing.Optional[VirtualMachineManagedDiskParameters]:
        result = self._values.get("managed_disk")
        return typing.cast(typing.Optional[VirtualMachineManagedDiskParameters], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def os_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("os_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineOSDisk(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineOSProfile",
    jsii_struct_bases=[],
    name_mapping={
        "admin_username": "adminUsername",
        "computer_name": "computerName",
        "admin_password": "adminPassword",
        "allow_extension_operations": "allowExtensionOperations",
        "custom_data": "customData",
        "linux_configuration": "linuxConfiguration",
        "secrets": "secrets",
        "windows_configuration": "windowsConfiguration",
    },
)
class VirtualMachineOSProfile:
    def __init__(
        self,
        *,
        admin_username: builtins.str,
        computer_name: builtins.str,
        admin_password: typing.Optional[builtins.str] = None,
        allow_extension_operations: typing.Optional[builtins.bool] = None,
        custom_data: typing.Optional[builtins.str] = None,
        linux_configuration: typing.Optional[typing.Union[VirtualMachineLinuxConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
        secrets: typing.Optional[typing.Sequence[typing.Union["VirtualMachineSecret", typing.Dict[builtins.str, typing.Any]]]] = None,
        windows_configuration: typing.Optional[typing.Union["VirtualMachineWindowsConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''OS profile for the virtual machine.

        :param admin_username: 
        :param computer_name: 
        :param admin_password: 
        :param allow_extension_operations: 
        :param custom_data: 
        :param linux_configuration: 
        :param secrets: 
        :param windows_configuration: 
        '''
        if isinstance(linux_configuration, dict):
            linux_configuration = VirtualMachineLinuxConfiguration(**linux_configuration)
        if isinstance(windows_configuration, dict):
            windows_configuration = VirtualMachineWindowsConfiguration(**windows_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1cab288f77bf7c6e22f1158554097af504d3fcecbc8ba9b40f174172ffd24e72)
            check_type(argname="argument admin_username", value=admin_username, expected_type=type_hints["admin_username"])
            check_type(argname="argument computer_name", value=computer_name, expected_type=type_hints["computer_name"])
            check_type(argname="argument admin_password", value=admin_password, expected_type=type_hints["admin_password"])
            check_type(argname="argument allow_extension_operations", value=allow_extension_operations, expected_type=type_hints["allow_extension_operations"])
            check_type(argname="argument custom_data", value=custom_data, expected_type=type_hints["custom_data"])
            check_type(argname="argument linux_configuration", value=linux_configuration, expected_type=type_hints["linux_configuration"])
            check_type(argname="argument secrets", value=secrets, expected_type=type_hints["secrets"])
            check_type(argname="argument windows_configuration", value=windows_configuration, expected_type=type_hints["windows_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "admin_username": admin_username,
            "computer_name": computer_name,
        }
        if admin_password is not None:
            self._values["admin_password"] = admin_password
        if allow_extension_operations is not None:
            self._values["allow_extension_operations"] = allow_extension_operations
        if custom_data is not None:
            self._values["custom_data"] = custom_data
        if linux_configuration is not None:
            self._values["linux_configuration"] = linux_configuration
        if secrets is not None:
            self._values["secrets"] = secrets
        if windows_configuration is not None:
            self._values["windows_configuration"] = windows_configuration

    @builtins.property
    def admin_username(self) -> builtins.str:
        result = self._values.get("admin_username")
        assert result is not None, "Required property 'admin_username' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def computer_name(self) -> builtins.str:
        result = self._values.get("computer_name")
        assert result is not None, "Required property 'computer_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def admin_password(self) -> typing.Optional[builtins.str]:
        result = self._values.get("admin_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def allow_extension_operations(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("allow_extension_operations")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def custom_data(self) -> typing.Optional[builtins.str]:
        result = self._values.get("custom_data")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def linux_configuration(self) -> typing.Optional[VirtualMachineLinuxConfiguration]:
        result = self._values.get("linux_configuration")
        return typing.cast(typing.Optional[VirtualMachineLinuxConfiguration], result)

    @builtins.property
    def secrets(self) -> typing.Optional[typing.List["VirtualMachineSecret"]]:
        result = self._values.get("secrets")
        return typing.cast(typing.Optional[typing.List["VirtualMachineSecret"]], result)

    @builtins.property
    def windows_configuration(
        self,
    ) -> typing.Optional["VirtualMachineWindowsConfiguration"]:
        result = self._values.get("windows_configuration")
        return typing.cast(typing.Optional["VirtualMachineWindowsConfiguration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineOSProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachinePlan",
    jsii_struct_bases=[],
    name_mapping={
        "name": "name",
        "product": "product",
        "promotion_code": "promotionCode",
        "publisher": "publisher",
    },
)
class VirtualMachinePlan:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        product: typing.Optional[builtins.str] = None,
        promotion_code: typing.Optional[builtins.str] = None,
        publisher: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Plan information for marketplace images.

        :param name: 
        :param product: 
        :param promotion_code: 
        :param publisher: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ccd2958a255f2deb47002b0697951e9de16f6c99f65f3bb72624b924448cf4b5)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument product", value=product, expected_type=type_hints["product"])
            check_type(argname="argument promotion_code", value=promotion_code, expected_type=type_hints["promotion_code"])
            check_type(argname="argument publisher", value=publisher, expected_type=type_hints["publisher"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if product is not None:
            self._values["product"] = product
        if promotion_code is not None:
            self._values["promotion_code"] = promotion_code
        if publisher is not None:
            self._values["publisher"] = publisher

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def product(self) -> typing.Optional[builtins.str]:
        result = self._values.get("product")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def promotion_code(self) -> typing.Optional[builtins.str]:
        result = self._values.get("promotion_code")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def publisher(self) -> typing.Optional[builtins.str]:
        result = self._values.get("publisher")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachinePlan(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachinePriorityProfile",
    jsii_struct_bases=[],
    name_mapping={
        "billing_profile": "billingProfile",
        "eviction_policy": "evictionPolicy",
        "priority": "priority",
    },
)
class VirtualMachinePriorityProfile:
    def __init__(
        self,
        *,
        billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        eviction_policy: typing.Optional[builtins.str] = None,
        priority: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Priority and eviction policy for spot VMs.

        :param billing_profile: 
        :param eviction_policy: 
        :param priority: 
        '''
        if isinstance(billing_profile, dict):
            billing_profile = VirtualMachineBillingProfile(**billing_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__64ba3d0560b80440f65f94ff06bf0de00b4bc37df5860fa38463a245a264bbaf)
            check_type(argname="argument billing_profile", value=billing_profile, expected_type=type_hints["billing_profile"])
            check_type(argname="argument eviction_policy", value=eviction_policy, expected_type=type_hints["eviction_policy"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if billing_profile is not None:
            self._values["billing_profile"] = billing_profile
        if eviction_policy is not None:
            self._values["eviction_policy"] = eviction_policy
        if priority is not None:
            self._values["priority"] = priority

    @builtins.property
    def billing_profile(self) -> typing.Optional[VirtualMachineBillingProfile]:
        result = self._values.get("billing_profile")
        return typing.cast(typing.Optional[VirtualMachineBillingProfile], result)

    @builtins.property
    def eviction_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("eviction_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def priority(self) -> typing.Optional[builtins.str]:
        result = self._values.get("priority")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachinePriorityProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineProps",
    jsii_struct_bases=[_AzapiResourceProps_141a2340],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "api_version": "apiVersion",
        "enable_migration_analysis": "enableMigrationAnalysis",
        "enable_transformation": "enableTransformation",
        "enable_validation": "enableValidation",
        "location": "location",
        "monitoring": "monitoring",
        "name": "name",
        "tags": "tags",
        "hardware_profile": "hardwareProfile",
        "network_profile": "networkProfile",
        "storage_profile": "storageProfile",
        "additional_capabilities": "additionalCapabilities",
        "availability_set": "availabilitySet",
        "billing_profile": "billingProfile",
        "diagnostics_profile": "diagnosticsProfile",
        "eviction_policy": "evictionPolicy",
        "host": "host",
        "identity": "identity",
        "ignore_changes": "ignoreChanges",
        "license_type": "licenseType",
        "os_profile": "osProfile",
        "plan": "plan",
        "priority": "priority",
        "proximity_placement_group": "proximityPlacementGroup",
        "resource_group_id": "resourceGroupId",
        "security_profile": "securityProfile",
        "virtual_machine_scale_set": "virtualMachineScaleSet",
        "zones": "zones",
    },
)
class VirtualMachineProps(_AzapiResourceProps_141a2340):
    def __init__(
        self,
        *,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
        api_version: typing.Optional[builtins.str] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        location: typing.Optional[builtins.str] = None,
        monitoring: typing.Optional[typing.Union[_MonitoringConfig_7c28df74, typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        hardware_profile: typing.Union[VirtualMachineHardwareProfile, typing.Dict[builtins.str, typing.Any]],
        network_profile: typing.Union[VirtualMachineNetworkProfile, typing.Dict[builtins.str, typing.Any]],
        storage_profile: typing.Union["VirtualMachineStorageProfile", typing.Dict[builtins.str, typing.Any]],
        additional_capabilities: typing.Optional[typing.Union[VirtualMachineAdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
        availability_set: typing.Optional[typing.Union[VirtualMachineAvailabilitySetReference, typing.Dict[builtins.str, typing.Any]]] = None,
        billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        diagnostics_profile: typing.Optional[typing.Union[VirtualMachineDiagnosticsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        eviction_policy: typing.Optional[builtins.str] = None,
        host: typing.Optional[typing.Union[VirtualMachineHostReference, typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union[VirtualMachineIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        license_type: typing.Optional[builtins.str] = None,
        os_profile: typing.Optional[typing.Union[VirtualMachineOSProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        plan: typing.Optional[typing.Union[VirtualMachinePlan, typing.Dict[builtins.str, typing.Any]]] = None,
        priority: typing.Optional[builtins.str] = None,
        proximity_placement_group: typing.Optional[typing.Union["VirtualMachineProximityPlacementGroupReference", typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        security_profile: typing.Optional[typing.Union["VirtualMachineSecurityProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        virtual_machine_scale_set: typing.Optional[typing.Union["VirtualMachineScaleSetReference", typing.Dict[builtins.str, typing.Any]]] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the unified Azure Virtual Machine.

        Extends AzapiResourceProps with Virtual Machine specific properties

        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param api_version: Explicit API version to use for this resource. If not specified, the latest active version will be automatically resolved. Use this for version pinning when stability is required over latest features. Default: Latest active version from ApiVersionManager
        :param enable_migration_analysis: Whether to enable migration analysis warnings. When true, the framework will analyze the current version for deprecation status and provide migration recommendations in the deployment output. Default: true
        :param enable_transformation: Whether to apply property transformations automatically. When true, properties will be automatically transformed according to the target schema's transformation rules. This enables backward compatibility. Default: true
        :param enable_validation: Whether to validate properties against the schema. When true, all properties will be validated against the API schema before resource creation. Validation errors will cause deployment failures. Default: true
        :param location: The location where the resource should be created. Default: Varies by resource type - see specific resource documentation
        :param monitoring: Monitoring configuration for this resource. Enables integrated monitoring with diagnostic settings, metric alerts, and activity log alerts. All monitoring is optional and disabled by default.
        :param name: The name of the resource.
        :param tags: Tags to apply to the resource.
        :param hardware_profile: The hardware profile for the Virtual Machine (VM size).
        :param network_profile: The network profile for the Virtual Machine Defines network interfaces attached to the VM.
        :param storage_profile: The storage profile for the Virtual Machine Defines the OS disk, data disks, and image reference.
        :param additional_capabilities: Additional capabilities like Ultra SSD.
        :param availability_set: Reference to an availability set.
        :param billing_profile: The billing profile for Spot VMs.
        :param diagnostics_profile: The diagnostics profile for boot diagnostics.
        :param eviction_policy: The eviction policy for Spot VMs.
        :param host: Reference to a dedicated host.
        :param identity: The identity configuration for the Virtual Machine.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed or should not trigger updates.
        :param license_type: License type for Windows VMs.
        :param os_profile: The OS profile for the Virtual Machine Defines computer name, admin credentials, and OS-specific configuration.
        :param plan: Plan information for marketplace images.
        :param priority: The priority of the Virtual Machine. Default: "Regular"
        :param proximity_placement_group: Reference to a proximity placement group.
        :param resource_group_id: Resource group ID where the Virtual Machine will be created.
        :param security_profile: Security settings for the Virtual Machine.
        :param virtual_machine_scale_set: Reference to a virtual machine scale set.
        :param zones: Availability zones for the Virtual Machine.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(hardware_profile, dict):
            hardware_profile = VirtualMachineHardwareProfile(**hardware_profile)
        if isinstance(network_profile, dict):
            network_profile = VirtualMachineNetworkProfile(**network_profile)
        if isinstance(storage_profile, dict):
            storage_profile = VirtualMachineStorageProfile(**storage_profile)
        if isinstance(additional_capabilities, dict):
            additional_capabilities = VirtualMachineAdditionalCapabilities(**additional_capabilities)
        if isinstance(availability_set, dict):
            availability_set = VirtualMachineAvailabilitySetReference(**availability_set)
        if isinstance(billing_profile, dict):
            billing_profile = VirtualMachineBillingProfile(**billing_profile)
        if isinstance(diagnostics_profile, dict):
            diagnostics_profile = VirtualMachineDiagnosticsProfile(**diagnostics_profile)
        if isinstance(host, dict):
            host = VirtualMachineHostReference(**host)
        if isinstance(identity, dict):
            identity = VirtualMachineIdentity(**identity)
        if isinstance(os_profile, dict):
            os_profile = VirtualMachineOSProfile(**os_profile)
        if isinstance(plan, dict):
            plan = VirtualMachinePlan(**plan)
        if isinstance(proximity_placement_group, dict):
            proximity_placement_group = VirtualMachineProximityPlacementGroupReference(**proximity_placement_group)
        if isinstance(security_profile, dict):
            security_profile = VirtualMachineSecurityProfile(**security_profile)
        if isinstance(virtual_machine_scale_set, dict):
            virtual_machine_scale_set = VirtualMachineScaleSetReference(**virtual_machine_scale_set)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e1b6631eaab4b02ac2fdf8aa26a613ea5bfbd21c7d0a8041ed5b7afc1a4b3db5)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument api_version", value=api_version, expected_type=type_hints["api_version"])
            check_type(argname="argument enable_migration_analysis", value=enable_migration_analysis, expected_type=type_hints["enable_migration_analysis"])
            check_type(argname="argument enable_transformation", value=enable_transformation, expected_type=type_hints["enable_transformation"])
            check_type(argname="argument enable_validation", value=enable_validation, expected_type=type_hints["enable_validation"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument monitoring", value=monitoring, expected_type=type_hints["monitoring"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument hardware_profile", value=hardware_profile, expected_type=type_hints["hardware_profile"])
            check_type(argname="argument network_profile", value=network_profile, expected_type=type_hints["network_profile"])
            check_type(argname="argument storage_profile", value=storage_profile, expected_type=type_hints["storage_profile"])
            check_type(argname="argument additional_capabilities", value=additional_capabilities, expected_type=type_hints["additional_capabilities"])
            check_type(argname="argument availability_set", value=availability_set, expected_type=type_hints["availability_set"])
            check_type(argname="argument billing_profile", value=billing_profile, expected_type=type_hints["billing_profile"])
            check_type(argname="argument diagnostics_profile", value=diagnostics_profile, expected_type=type_hints["diagnostics_profile"])
            check_type(argname="argument eviction_policy", value=eviction_policy, expected_type=type_hints["eviction_policy"])
            check_type(argname="argument host", value=host, expected_type=type_hints["host"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument license_type", value=license_type, expected_type=type_hints["license_type"])
            check_type(argname="argument os_profile", value=os_profile, expected_type=type_hints["os_profile"])
            check_type(argname="argument plan", value=plan, expected_type=type_hints["plan"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument proximity_placement_group", value=proximity_placement_group, expected_type=type_hints["proximity_placement_group"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument security_profile", value=security_profile, expected_type=type_hints["security_profile"])
            check_type(argname="argument virtual_machine_scale_set", value=virtual_machine_scale_set, expected_type=type_hints["virtual_machine_scale_set"])
            check_type(argname="argument zones", value=zones, expected_type=type_hints["zones"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "hardware_profile": hardware_profile,
            "network_profile": network_profile,
            "storage_profile": storage_profile,
        }
        if connection is not None:
            self._values["connection"] = connection
        if count is not None:
            self._values["count"] = count
        if depends_on is not None:
            self._values["depends_on"] = depends_on
        if for_each is not None:
            self._values["for_each"] = for_each
        if lifecycle is not None:
            self._values["lifecycle"] = lifecycle
        if provider is not None:
            self._values["provider"] = provider
        if provisioners is not None:
            self._values["provisioners"] = provisioners
        if api_version is not None:
            self._values["api_version"] = api_version
        if enable_migration_analysis is not None:
            self._values["enable_migration_analysis"] = enable_migration_analysis
        if enable_transformation is not None:
            self._values["enable_transformation"] = enable_transformation
        if enable_validation is not None:
            self._values["enable_validation"] = enable_validation
        if location is not None:
            self._values["location"] = location
        if monitoring is not None:
            self._values["monitoring"] = monitoring
        if name is not None:
            self._values["name"] = name
        if tags is not None:
            self._values["tags"] = tags
        if additional_capabilities is not None:
            self._values["additional_capabilities"] = additional_capabilities
        if availability_set is not None:
            self._values["availability_set"] = availability_set
        if billing_profile is not None:
            self._values["billing_profile"] = billing_profile
        if diagnostics_profile is not None:
            self._values["diagnostics_profile"] = diagnostics_profile
        if eviction_policy is not None:
            self._values["eviction_policy"] = eviction_policy
        if host is not None:
            self._values["host"] = host
        if identity is not None:
            self._values["identity"] = identity
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if license_type is not None:
            self._values["license_type"] = license_type
        if os_profile is not None:
            self._values["os_profile"] = os_profile
        if plan is not None:
            self._values["plan"] = plan
        if priority is not None:
            self._values["priority"] = priority
        if proximity_placement_group is not None:
            self._values["proximity_placement_group"] = proximity_placement_group
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if security_profile is not None:
            self._values["security_profile"] = security_profile
        if virtual_machine_scale_set is not None:
            self._values["virtual_machine_scale_set"] = virtual_machine_scale_set
        if zones is not None:
            self._values["zones"] = zones

    @builtins.property
    def connection(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("connection")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, _cdktf_9a9027ec.WinrmProvisionerConnection]], result)

    @builtins.property
    def count(
        self,
    ) -> typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("count")
        return typing.cast(typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]], result)

    @builtins.property
    def depends_on(
        self,
    ) -> typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("depends_on")
        return typing.cast(typing.Optional[typing.List[_cdktf_9a9027ec.ITerraformDependable]], result)

    @builtins.property
    def for_each(self) -> typing.Optional[_cdktf_9a9027ec.ITerraformIterator]:
        '''
        :stability: experimental
        '''
        result = self._values.get("for_each")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.ITerraformIterator], result)

    @builtins.property
    def lifecycle(self) -> typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle]:
        '''
        :stability: experimental
        '''
        result = self._values.get("lifecycle")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformResourceLifecycle], result)

    @builtins.property
    def provider(self) -> typing.Optional[_cdktf_9a9027ec.TerraformProvider]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provider")
        return typing.cast(typing.Optional[_cdktf_9a9027ec.TerraformProvider], result)

    @builtins.property
    def provisioners(
        self,
    ) -> typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]]:
        '''
        :stability: experimental
        '''
        result = self._values.get("provisioners")
        return typing.cast(typing.Optional[typing.List[typing.Union[_cdktf_9a9027ec.FileProvisioner, _cdktf_9a9027ec.LocalExecProvisioner, _cdktf_9a9027ec.RemoteExecProvisioner]]], result)

    @builtins.property
    def api_version(self) -> typing.Optional[builtins.str]:
        '''Explicit API version to use for this resource.

        If not specified, the latest active version will be automatically resolved.
        Use this for version pinning when stability is required over latest features.

        :default: Latest active version from ApiVersionManager

        Example::

            "2024-11-01"
        '''
        result = self._values.get("api_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_migration_analysis(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable migration analysis warnings.

        When true, the framework will analyze the current version for deprecation
        status and provide migration recommendations in the deployment output.

        :default: true
        '''
        result = self._values.get("enable_migration_analysis")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_transformation(self) -> typing.Optional[builtins.bool]:
        '''Whether to apply property transformations automatically.

        When true, properties will be automatically transformed according to the
        target schema's transformation rules. This enables backward compatibility.

        :default: true
        '''
        result = self._values.get("enable_transformation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_validation(self) -> typing.Optional[builtins.bool]:
        '''Whether to validate properties against the schema.

        When true, all properties will be validated against the API schema before
        resource creation. Validation errors will cause deployment failures.

        :default: true
        '''
        result = self._values.get("enable_validation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def location(self) -> typing.Optional[builtins.str]:
        '''The location where the resource should be created.

        :default: Varies by resource type - see specific resource documentation

        :remarks:

        Location handling varies by resource type:

        - **Top-level resources**: Most require an explicit location (e.g., "eastus", "westus")
        - **Global resources**: Some use "global" as location (e.g., Private DNS Zones)
        - **Child resources**: Inherit location from parent and should NOT set this property

        Each resource type may provide its own default through the ``resolveLocation()`` method.
        If no location is specified and no default exists, resource creation may fail.

        Example::

            // Child resource (Subnet) - do not set location
            // location: undefined (inherited from parent Virtual Network)
        '''
        result = self._values.get("location")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def monitoring(self) -> typing.Optional[_MonitoringConfig_7c28df74]:
        '''Monitoring configuration for this resource.

        Enables integrated monitoring with diagnostic settings, metric alerts,
        and activity log alerts. All monitoring is optional and disabled by default.

        Example::

            monitoring: {
              enabled: true,
              diagnosticSettings: {
                workspaceId: logAnalytics.id,
                metrics: ['AllMetrics'],
                logs: ['AuditLogs']
              },
              metricAlerts: [{
                name: 'high-cpu-alert',
                severity: 2,
                scopes: [], // Automatically set to this resource
                criteria: { ... },
                actions: [{ actionGroupId: actionGroup.id }]
              }]
            }
        '''
        result = self._values.get("monitoring")
        return typing.cast(typing.Optional[_MonitoringConfig_7c28df74], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''The name of the resource.'''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Tags to apply to the resource.'''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def hardware_profile(self) -> VirtualMachineHardwareProfile:
        '''The hardware profile for the Virtual Machine (VM size).

        Example::

            { vmSize: "Standard_D2s_v3" }
        '''
        result = self._values.get("hardware_profile")
        assert result is not None, "Required property 'hardware_profile' is missing"
        return typing.cast(VirtualMachineHardwareProfile, result)

    @builtins.property
    def network_profile(self) -> VirtualMachineNetworkProfile:
        '''The network profile for the Virtual Machine Defines network interfaces attached to the VM.'''
        result = self._values.get("network_profile")
        assert result is not None, "Required property 'network_profile' is missing"
        return typing.cast(VirtualMachineNetworkProfile, result)

    @builtins.property
    def storage_profile(self) -> "VirtualMachineStorageProfile":
        '''The storage profile for the Virtual Machine Defines the OS disk, data disks, and image reference.'''
        result = self._values.get("storage_profile")
        assert result is not None, "Required property 'storage_profile' is missing"
        return typing.cast("VirtualMachineStorageProfile", result)

    @builtins.property
    def additional_capabilities(
        self,
    ) -> typing.Optional[VirtualMachineAdditionalCapabilities]:
        '''Additional capabilities like Ultra SSD.'''
        result = self._values.get("additional_capabilities")
        return typing.cast(typing.Optional[VirtualMachineAdditionalCapabilities], result)

    @builtins.property
    def availability_set(
        self,
    ) -> typing.Optional[VirtualMachineAvailabilitySetReference]:
        '''Reference to an availability set.'''
        result = self._values.get("availability_set")
        return typing.cast(typing.Optional[VirtualMachineAvailabilitySetReference], result)

    @builtins.property
    def billing_profile(self) -> typing.Optional[VirtualMachineBillingProfile]:
        '''The billing profile for Spot VMs.'''
        result = self._values.get("billing_profile")
        return typing.cast(typing.Optional[VirtualMachineBillingProfile], result)

    @builtins.property
    def diagnostics_profile(self) -> typing.Optional[VirtualMachineDiagnosticsProfile]:
        '''The diagnostics profile for boot diagnostics.'''
        result = self._values.get("diagnostics_profile")
        return typing.cast(typing.Optional[VirtualMachineDiagnosticsProfile], result)

    @builtins.property
    def eviction_policy(self) -> typing.Optional[builtins.str]:
        '''The eviction policy for Spot VMs.

        Example::

            "Deallocate", "Delete"
        '''
        result = self._values.get("eviction_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def host(self) -> typing.Optional[VirtualMachineHostReference]:
        '''Reference to a dedicated host.'''
        result = self._values.get("host")
        return typing.cast(typing.Optional[VirtualMachineHostReference], result)

    @builtins.property
    def identity(self) -> typing.Optional[VirtualMachineIdentity]:
        '''The identity configuration for the Virtual Machine.

        Example::

            { type: "UserAssigned", userAssignedIdentities: { "/subscriptions/.../resourceGroups/.../providers/Microsoft.ManagedIdentity/userAssignedIdentities/myIdentity": {} } }
        '''
        result = self._values.get("identity")
        return typing.cast(typing.Optional[VirtualMachineIdentity], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed or should not trigger updates.

        Example::

            ["osProfile.adminPassword"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def license_type(self) -> typing.Optional[builtins.str]:
        '''License type for Windows VMs.

        Example::

            "Windows_Client"
        '''
        result = self._values.get("license_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def os_profile(self) -> typing.Optional[VirtualMachineOSProfile]:
        '''The OS profile for the Virtual Machine Defines computer name, admin credentials, and OS-specific configuration.'''
        result = self._values.get("os_profile")
        return typing.cast(typing.Optional[VirtualMachineOSProfile], result)

    @builtins.property
    def plan(self) -> typing.Optional[VirtualMachinePlan]:
        '''Plan information for marketplace images.'''
        result = self._values.get("plan")
        return typing.cast(typing.Optional[VirtualMachinePlan], result)

    @builtins.property
    def priority(self) -> typing.Optional[builtins.str]:
        '''The priority of the Virtual Machine.

        :default: "Regular"

        Example::

            "Regular", "Low", "Spot"
        '''
        result = self._values.get("priority")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def proximity_placement_group(
        self,
    ) -> typing.Optional["VirtualMachineProximityPlacementGroupReference"]:
        '''Reference to a proximity placement group.'''
        result = self._values.get("proximity_placement_group")
        return typing.cast(typing.Optional["VirtualMachineProximityPlacementGroupReference"], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the Virtual Machine will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_profile(self) -> typing.Optional["VirtualMachineSecurityProfile"]:
        '''Security settings for the Virtual Machine.'''
        result = self._values.get("security_profile")
        return typing.cast(typing.Optional["VirtualMachineSecurityProfile"], result)

    @builtins.property
    def virtual_machine_scale_set(
        self,
    ) -> typing.Optional["VirtualMachineScaleSetReference"]:
        '''Reference to a virtual machine scale set.'''
        result = self._values.get("virtual_machine_scale_set")
        return typing.cast(typing.Optional["VirtualMachineScaleSetReference"], result)

    @builtins.property
    def zones(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Availability zones for the Virtual Machine.

        Example::

            ["1", "2"]
        '''
        result = self._values.get("zones")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineProximityPlacementGroupReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualMachineProximityPlacementGroupReference:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Proximity placement group reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a4bceab44218e50edcfdec1e907f3daaaaa7c3e52f5a0d71715263cdeb492697)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineProximityPlacementGroupReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineScaleSetReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualMachineScaleSetReference:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Virtual machine scale set reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0e8e23514ea72f9cbfba41113ebd56fdbd5530a36bc6c4b4be9f34a40135192e)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineSecret",
    jsii_struct_bases=[],
    name_mapping={
        "source_vault": "sourceVault",
        "vault_certificates": "vaultCertificates",
    },
)
class VirtualMachineSecret:
    def __init__(
        self,
        *,
        source_vault: typing.Optional[typing.Union["VirtualMachineSubResource", typing.Dict[builtins.str, typing.Any]]] = None,
        vault_certificates: typing.Optional[typing.Sequence[typing.Union["VirtualMachineVaultCertificate", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Secret for OS profile.

        :param source_vault: 
        :param vault_certificates: 
        '''
        if isinstance(source_vault, dict):
            source_vault = VirtualMachineSubResource(**source_vault)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__42d8c5f3edc7b3c905ce96a1344138c14011dd8e5de2524bc85664cbb9faced1)
            check_type(argname="argument source_vault", value=source_vault, expected_type=type_hints["source_vault"])
            check_type(argname="argument vault_certificates", value=vault_certificates, expected_type=type_hints["vault_certificates"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if source_vault is not None:
            self._values["source_vault"] = source_vault
        if vault_certificates is not None:
            self._values["vault_certificates"] = vault_certificates

    @builtins.property
    def source_vault(self) -> typing.Optional["VirtualMachineSubResource"]:
        result = self._values.get("source_vault")
        return typing.cast(typing.Optional["VirtualMachineSubResource"], result)

    @builtins.property
    def vault_certificates(
        self,
    ) -> typing.Optional[typing.List["VirtualMachineVaultCertificate"]]:
        result = self._values.get("vault_certificates")
        return typing.cast(typing.Optional[typing.List["VirtualMachineVaultCertificate"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineSecret(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineSecurityProfile",
    jsii_struct_bases=[],
    name_mapping={
        "encryption_at_host": "encryptionAtHost",
        "security_type": "securityType",
        "uefi_settings": "uefiSettings",
    },
)
class VirtualMachineSecurityProfile:
    def __init__(
        self,
        *,
        encryption_at_host: typing.Optional[builtins.bool] = None,
        security_type: typing.Optional[builtins.str] = None,
        uefi_settings: typing.Optional[typing.Union["VirtualMachineUefiSettings", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Security profile.

        :param encryption_at_host: 
        :param security_type: 
        :param uefi_settings: 
        '''
        if isinstance(uefi_settings, dict):
            uefi_settings = VirtualMachineUefiSettings(**uefi_settings)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b9cc9fbec2e43cf4bd67cf36db09d18f51d6d14bc434102f3addc3f8dc392ef9)
            check_type(argname="argument encryption_at_host", value=encryption_at_host, expected_type=type_hints["encryption_at_host"])
            check_type(argname="argument security_type", value=security_type, expected_type=type_hints["security_type"])
            check_type(argname="argument uefi_settings", value=uefi_settings, expected_type=type_hints["uefi_settings"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if encryption_at_host is not None:
            self._values["encryption_at_host"] = encryption_at_host
        if security_type is not None:
            self._values["security_type"] = security_type
        if uefi_settings is not None:
            self._values["uefi_settings"] = uefi_settings

    @builtins.property
    def encryption_at_host(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("encryption_at_host")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def security_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("security_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def uefi_settings(self) -> typing.Optional["VirtualMachineUefiSettings"]:
        result = self._values.get("uefi_settings")
        return typing.cast(typing.Optional["VirtualMachineUefiSettings"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineSecurityProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineSshConfiguration",
    jsii_struct_bases=[],
    name_mapping={"public_keys": "publicKeys"},
)
class VirtualMachineSshConfiguration:
    def __init__(
        self,
        *,
        public_keys: typing.Optional[typing.Sequence[typing.Union["VirtualMachineSshPublicKey", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''SSH configuration.

        :param public_keys: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e9b675a41499311b259211cd2ac39ead52dadd002a48703cd1a0e5873f0ec5f)
            check_type(argname="argument public_keys", value=public_keys, expected_type=type_hints["public_keys"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if public_keys is not None:
            self._values["public_keys"] = public_keys

    @builtins.property
    def public_keys(self) -> typing.Optional[typing.List["VirtualMachineSshPublicKey"]]:
        result = self._values.get("public_keys")
        return typing.cast(typing.Optional[typing.List["VirtualMachineSshPublicKey"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineSshConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineSshPublicKey",
    jsii_struct_bases=[],
    name_mapping={"key_data": "keyData", "path": "path"},
)
class VirtualMachineSshPublicKey:
    def __init__(self, *, key_data: builtins.str, path: builtins.str) -> None:
        '''SSH public key.

        :param key_data: 
        :param path: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7fdb6f9f6ab9cf41b21369f914c7444f9a6a5da11087ea468620529e5d989713)
            check_type(argname="argument key_data", value=key_data, expected_type=type_hints["key_data"])
            check_type(argname="argument path", value=path, expected_type=type_hints["path"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "key_data": key_data,
            "path": path,
        }

    @builtins.property
    def key_data(self) -> builtins.str:
        result = self._values.get("key_data")
        assert result is not None, "Required property 'key_data' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def path(self) -> builtins.str:
        result = self._values.get("path")
        assert result is not None, "Required property 'path' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineSshPublicKey(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineStorageProfile",
    jsii_struct_bases=[],
    name_mapping={
        "os_disk": "osDisk",
        "data_disks": "dataDisks",
        "image_reference": "imageReference",
    },
)
class VirtualMachineStorageProfile:
    def __init__(
        self,
        *,
        os_disk: typing.Union[VirtualMachineOSDisk, typing.Dict[builtins.str, typing.Any]],
        data_disks: typing.Optional[typing.Sequence[typing.Union[VirtualMachineDataDisk, typing.Dict[builtins.str, typing.Any]]]] = None,
        image_reference: typing.Optional[typing.Union[VirtualMachineImageReference, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Storage profile for the virtual machine.

        :param os_disk: 
        :param data_disks: 
        :param image_reference: 
        '''
        if isinstance(os_disk, dict):
            os_disk = VirtualMachineOSDisk(**os_disk)
        if isinstance(image_reference, dict):
            image_reference = VirtualMachineImageReference(**image_reference)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d0ec8f811e056ff027f1d619ab2238fbe7d4ed3ba1e96c13740d849b378042b9)
            check_type(argname="argument os_disk", value=os_disk, expected_type=type_hints["os_disk"])
            check_type(argname="argument data_disks", value=data_disks, expected_type=type_hints["data_disks"])
            check_type(argname="argument image_reference", value=image_reference, expected_type=type_hints["image_reference"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "os_disk": os_disk,
        }
        if data_disks is not None:
            self._values["data_disks"] = data_disks
        if image_reference is not None:
            self._values["image_reference"] = image_reference

    @builtins.property
    def os_disk(self) -> VirtualMachineOSDisk:
        result = self._values.get("os_disk")
        assert result is not None, "Required property 'os_disk' is missing"
        return typing.cast(VirtualMachineOSDisk, result)

    @builtins.property
    def data_disks(self) -> typing.Optional[typing.List[VirtualMachineDataDisk]]:
        result = self._values.get("data_disks")
        return typing.cast(typing.Optional[typing.List[VirtualMachineDataDisk]], result)

    @builtins.property
    def image_reference(self) -> typing.Optional[VirtualMachineImageReference]:
        result = self._values.get("image_reference")
        return typing.cast(typing.Optional[VirtualMachineImageReference], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineStorageProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineSubResource",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualMachineSubResource:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Sub-resource reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8c397700b365b1c773ce8104a60ab728ee9b5c8a026a594b8c8c7a2be3eac94f)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineSubResource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineUefiSettings",
    jsii_struct_bases=[],
    name_mapping={
        "secure_boot_enabled": "secureBootEnabled",
        "v_tpm_enabled": "vTpmEnabled",
    },
)
class VirtualMachineUefiSettings:
    def __init__(
        self,
        *,
        secure_boot_enabled: typing.Optional[builtins.bool] = None,
        v_tpm_enabled: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''UEFI settings.

        :param secure_boot_enabled: 
        :param v_tpm_enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d613f5b2dded4046d80ae15926d374f1a4ae96feffb13d15af4f4bc97417af49)
            check_type(argname="argument secure_boot_enabled", value=secure_boot_enabled, expected_type=type_hints["secure_boot_enabled"])
            check_type(argname="argument v_tpm_enabled", value=v_tpm_enabled, expected_type=type_hints["v_tpm_enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if secure_boot_enabled is not None:
            self._values["secure_boot_enabled"] = secure_boot_enabled
        if v_tpm_enabled is not None:
            self._values["v_tpm_enabled"] = v_tpm_enabled

    @builtins.property
    def secure_boot_enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("secure_boot_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def v_tpm_enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("v_tpm_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineUefiSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineVaultCertificate",
    jsii_struct_bases=[],
    name_mapping={
        "certificate_store": "certificateStore",
        "certificate_url": "certificateUrl",
    },
)
class VirtualMachineVaultCertificate:
    def __init__(
        self,
        *,
        certificate_store: typing.Optional[builtins.str] = None,
        certificate_url: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Vault certificate.

        :param certificate_store: 
        :param certificate_url: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__458225e7ada8f0d312ec8d23b7372e950b0dcd22a4ea89647a7ac1ba86e089d7)
            check_type(argname="argument certificate_store", value=certificate_store, expected_type=type_hints["certificate_store"])
            check_type(argname="argument certificate_url", value=certificate_url, expected_type=type_hints["certificate_url"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if certificate_store is not None:
            self._values["certificate_store"] = certificate_store
        if certificate_url is not None:
            self._values["certificate_url"] = certificate_url

    @builtins.property
    def certificate_store(self) -> typing.Optional[builtins.str]:
        result = self._values.get("certificate_store")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def certificate_url(self) -> typing.Optional[builtins.str]:
        result = self._values.get("certificate_url")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineVaultCertificate(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineWinRMConfiguration",
    jsii_struct_bases=[],
    name_mapping={"listeners": "listeners"},
)
class VirtualMachineWinRMConfiguration:
    def __init__(
        self,
        *,
        listeners: typing.Optional[typing.Sequence[typing.Union["VirtualMachineWinRMListener", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''WinRM configuration.

        :param listeners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c372455a2a2ff7a20134c070987118108c1bae6054ddc981e6f1a0af2f56b15d)
            check_type(argname="argument listeners", value=listeners, expected_type=type_hints["listeners"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if listeners is not None:
            self._values["listeners"] = listeners

    @builtins.property
    def listeners(self) -> typing.Optional[typing.List["VirtualMachineWinRMListener"]]:
        result = self._values.get("listeners")
        return typing.cast(typing.Optional[typing.List["VirtualMachineWinRMListener"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineWinRMConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineWinRMListener",
    jsii_struct_bases=[],
    name_mapping={"protocol": "protocol", "certificate_url": "certificateUrl"},
)
class VirtualMachineWinRMListener:
    def __init__(
        self,
        *,
        protocol: builtins.str,
        certificate_url: typing.Optional[builtins.str] = None,
    ) -> None:
        '''WinRM listener.

        :param protocol: 
        :param certificate_url: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffb1e306c6c57b8a2350f629a45eac780bfbb8bb3f0e1deeb4a151a0a0422ee3)
            check_type(argname="argument protocol", value=protocol, expected_type=type_hints["protocol"])
            check_type(argname="argument certificate_url", value=certificate_url, expected_type=type_hints["certificate_url"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "protocol": protocol,
        }
        if certificate_url is not None:
            self._values["certificate_url"] = certificate_url

    @builtins.property
    def protocol(self) -> builtins.str:
        result = self._values.get("protocol")
        assert result is not None, "Required property 'protocol' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def certificate_url(self) -> typing.Optional[builtins.str]:
        result = self._values.get("certificate_url")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineWinRMListener(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineWindowsConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "enable_automatic_updates": "enableAutomaticUpdates",
        "patch_settings": "patchSettings",
        "provision_vm_agent": "provisionVMAgent",
        "time_zone": "timeZone",
        "win_rm": "winRM",
    },
)
class VirtualMachineWindowsConfiguration:
    def __init__(
        self,
        *,
        enable_automatic_updates: typing.Optional[builtins.bool] = None,
        patch_settings: typing.Optional[typing.Union["VirtualMachineWindowsPatchSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        provision_vm_agent: typing.Optional[builtins.bool] = None,
        time_zone: typing.Optional[builtins.str] = None,
        win_rm: typing.Optional[typing.Union[VirtualMachineWinRMConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Windows configuration.

        :param enable_automatic_updates: 
        :param patch_settings: 
        :param provision_vm_agent: 
        :param time_zone: 
        :param win_rm: 
        '''
        if isinstance(patch_settings, dict):
            patch_settings = VirtualMachineWindowsPatchSettings(**patch_settings)
        if isinstance(win_rm, dict):
            win_rm = VirtualMachineWinRMConfiguration(**win_rm)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e55cf022c700c4548f66e6c1db98f72ddd79bbd2961955fd11c40358e548bcba)
            check_type(argname="argument enable_automatic_updates", value=enable_automatic_updates, expected_type=type_hints["enable_automatic_updates"])
            check_type(argname="argument patch_settings", value=patch_settings, expected_type=type_hints["patch_settings"])
            check_type(argname="argument provision_vm_agent", value=provision_vm_agent, expected_type=type_hints["provision_vm_agent"])
            check_type(argname="argument time_zone", value=time_zone, expected_type=type_hints["time_zone"])
            check_type(argname="argument win_rm", value=win_rm, expected_type=type_hints["win_rm"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enable_automatic_updates is not None:
            self._values["enable_automatic_updates"] = enable_automatic_updates
        if patch_settings is not None:
            self._values["patch_settings"] = patch_settings
        if provision_vm_agent is not None:
            self._values["provision_vm_agent"] = provision_vm_agent
        if time_zone is not None:
            self._values["time_zone"] = time_zone
        if win_rm is not None:
            self._values["win_rm"] = win_rm

    @builtins.property
    def enable_automatic_updates(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_automatic_updates")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def patch_settings(self) -> typing.Optional["VirtualMachineWindowsPatchSettings"]:
        result = self._values.get("patch_settings")
        return typing.cast(typing.Optional["VirtualMachineWindowsPatchSettings"], result)

    @builtins.property
    def provision_vm_agent(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("provision_vm_agent")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def time_zone(self) -> typing.Optional[builtins.str]:
        result = self._values.get("time_zone")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def win_rm(self) -> typing.Optional[VirtualMachineWinRMConfiguration]:
        result = self._values.get("win_rm")
        return typing.cast(typing.Optional[VirtualMachineWinRMConfiguration], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineWindowsConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualmachine.VirtualMachineWindowsPatchSettings",
    jsii_struct_bases=[],
    name_mapping={
        "assessment_mode": "assessmentMode",
        "enable_hotpatching": "enableHotpatching",
        "patch_mode": "patchMode",
    },
)
class VirtualMachineWindowsPatchSettings:
    def __init__(
        self,
        *,
        assessment_mode: typing.Optional[builtins.str] = None,
        enable_hotpatching: typing.Optional[builtins.bool] = None,
        patch_mode: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Windows patch settings.

        :param assessment_mode: 
        :param enable_hotpatching: 
        :param patch_mode: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a6df7234ccb2d56eb2c84b0305b86aebc3d295fc29d87b108aa9b83d04790bab)
            check_type(argname="argument assessment_mode", value=assessment_mode, expected_type=type_hints["assessment_mode"])
            check_type(argname="argument enable_hotpatching", value=enable_hotpatching, expected_type=type_hints["enable_hotpatching"])
            check_type(argname="argument patch_mode", value=patch_mode, expected_type=type_hints["patch_mode"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if assessment_mode is not None:
            self._values["assessment_mode"] = assessment_mode
        if enable_hotpatching is not None:
            self._values["enable_hotpatching"] = enable_hotpatching
        if patch_mode is not None:
            self._values["patch_mode"] = patch_mode

    @builtins.property
    def assessment_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("assessment_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_hotpatching(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_hotpatching")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def patch_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("patch_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineWindowsPatchSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "VirtualMachine",
    "VirtualMachineAdditionalCapabilities",
    "VirtualMachineAvailabilitySetReference",
    "VirtualMachineBillingProfile",
    "VirtualMachineBody",
    "VirtualMachineBodyProperties",
    "VirtualMachineBootDiagnostics",
    "VirtualMachineDataDisk",
    "VirtualMachineDiagnosticsProfile",
    "VirtualMachineDiskEncryptionSetParameters",
    "VirtualMachineHardwareProfile",
    "VirtualMachineHostReference",
    "VirtualMachineIdentity",
    "VirtualMachineImageReference",
    "VirtualMachineLinuxConfiguration",
    "VirtualMachineLinuxPatchSettings",
    "VirtualMachineManagedDiskParameters",
    "VirtualMachineMonitoringOptions",
    "VirtualMachineNetworkInterfaceProperties",
    "VirtualMachineNetworkInterfaceReference",
    "VirtualMachineNetworkProfile",
    "VirtualMachineOSDisk",
    "VirtualMachineOSProfile",
    "VirtualMachinePlan",
    "VirtualMachinePriorityProfile",
    "VirtualMachineProps",
    "VirtualMachineProximityPlacementGroupReference",
    "VirtualMachineScaleSetReference",
    "VirtualMachineSecret",
    "VirtualMachineSecurityProfile",
    "VirtualMachineSshConfiguration",
    "VirtualMachineSshPublicKey",
    "VirtualMachineStorageProfile",
    "VirtualMachineSubResource",
    "VirtualMachineUefiSettings",
    "VirtualMachineVaultCertificate",
    "VirtualMachineWinRMConfiguration",
    "VirtualMachineWinRMListener",
    "VirtualMachineWindowsConfiguration",
    "VirtualMachineWindowsPatchSettings",
]

publication.publish()

def _typecheckingstub__438bd5f5eb90ef4fe755b2ca7e07b03af0a1c21dc2ef1ee144ec35ee234b8ed9(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    hardware_profile: typing.Union[VirtualMachineHardwareProfile, typing.Dict[builtins.str, typing.Any]],
    network_profile: typing.Union[VirtualMachineNetworkProfile, typing.Dict[builtins.str, typing.Any]],
    storage_profile: typing.Union[VirtualMachineStorageProfile, typing.Dict[builtins.str, typing.Any]],
    additional_capabilities: typing.Optional[typing.Union[VirtualMachineAdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
    availability_set: typing.Optional[typing.Union[VirtualMachineAvailabilitySetReference, typing.Dict[builtins.str, typing.Any]]] = None,
    billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    diagnostics_profile: typing.Optional[typing.Union[VirtualMachineDiagnosticsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    eviction_policy: typing.Optional[builtins.str] = None,
    host: typing.Optional[typing.Union[VirtualMachineHostReference, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[VirtualMachineIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    license_type: typing.Optional[builtins.str] = None,
    os_profile: typing.Optional[typing.Union[VirtualMachineOSProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    plan: typing.Optional[typing.Union[VirtualMachinePlan, typing.Dict[builtins.str, typing.Any]]] = None,
    priority: typing.Optional[builtins.str] = None,
    proximity_placement_group: typing.Optional[typing.Union[VirtualMachineProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    security_profile: typing.Optional[typing.Union[VirtualMachineSecurityProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    virtual_machine_scale_set: typing.Optional[typing.Union[VirtualMachineScaleSetReference, typing.Dict[builtins.str, typing.Any]]] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    api_version: typing.Optional[builtins.str] = None,
    enable_migration_analysis: typing.Optional[builtins.bool] = None,
    enable_transformation: typing.Optional[builtins.bool] = None,
    enable_validation: typing.Optional[builtins.bool] = None,
    location: typing.Optional[builtins.str] = None,
    monitoring: typing.Optional[typing.Union[_MonitoringConfig_7c28df74, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__284acdb9e0713cc6f00537edbbe63820442476c7c588ddf2ba386dd409e39c09(
    action_group_id: builtins.str,
    workspace_id: typing.Optional[builtins.str] = None,
    *,
    cpu_alert_severity: typing.Optional[jsii.Number] = None,
    cpu_threshold: typing.Optional[jsii.Number] = None,
    disk_queue_alert_severity: typing.Optional[jsii.Number] = None,
    disk_queue_threshold: typing.Optional[jsii.Number] = None,
    enable_cpu_alert: typing.Optional[builtins.bool] = None,
    enable_deletion_alert: typing.Optional[builtins.bool] = None,
    enable_disk_queue_alert: typing.Optional[builtins.bool] = None,
    enable_memory_alert: typing.Optional[builtins.bool] = None,
    memory_alert_severity: typing.Optional[jsii.Number] = None,
    memory_threshold: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3bbfa912b420d66eb2516202ade284dfdfcdb8c1011dcec535bd75c0cb0d2e04(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ab197388e895c255303b05c028e1de2c88ff2b392d317a0a476628d4eda96fda(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__90de9c3a12c873e91e99cb467582a2e384b35149f4dc9e91895312422a8d322b(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0535843142573bacaa96574935d94b8ce81594ca4d27b68c39f2cae82e2d36ab(
    *,
    hibernation_enabled: typing.Optional[builtins.bool] = None,
    ultra_ssd_enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d95df1465def445c09ba6a0721ef6ed830a55854cf6d83ef1f84344288588f63(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d0d4da7eef9a215e7268afbe076ec0edc86aaf9b35ed48f6ea411bfc1f60c7c(
    *,
    max_price: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__09520373190ef38630c48497a5af8d8059b1071638fa0b0d75f9a2157a2a5548(
    *,
    location: builtins.str,
    properties: typing.Union[VirtualMachineBodyProperties, typing.Dict[builtins.str, typing.Any]],
    identity: typing.Optional[typing.Union[VirtualMachineIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    plan: typing.Optional[typing.Union[VirtualMachinePlan, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d5d45f524051568b58232171ab2104d5c535d2b911c905f45799c50b81051475(
    *,
    hardware_profile: typing.Union[VirtualMachineHardwareProfile, typing.Dict[builtins.str, typing.Any]],
    network_profile: typing.Union[VirtualMachineNetworkProfile, typing.Dict[builtins.str, typing.Any]],
    storage_profile: typing.Union[VirtualMachineStorageProfile, typing.Dict[builtins.str, typing.Any]],
    additional_capabilities: typing.Optional[typing.Union[VirtualMachineAdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
    availability_set: typing.Optional[typing.Union[VirtualMachineAvailabilitySetReference, typing.Dict[builtins.str, typing.Any]]] = None,
    billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    diagnostics_profile: typing.Optional[typing.Union[VirtualMachineDiagnosticsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    eviction_policy: typing.Optional[builtins.str] = None,
    host: typing.Optional[typing.Union[VirtualMachineHostReference, typing.Dict[builtins.str, typing.Any]]] = None,
    license_type: typing.Optional[builtins.str] = None,
    os_profile: typing.Optional[typing.Union[VirtualMachineOSProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    priority: typing.Optional[builtins.str] = None,
    proximity_placement_group: typing.Optional[typing.Union[VirtualMachineProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    security_profile: typing.Optional[typing.Union[VirtualMachineSecurityProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    virtual_machine_scale_set: typing.Optional[typing.Union[VirtualMachineScaleSetReference, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__34ecb938455456698f2ca7b671bd726c284cdb868cd9faf9f96fbb1b26768eea(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    storage_uri: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f5a8487bb5daf5c3d2ac9e2c89f07f5e33122b0083fd86a920eb3bbdf04e43c5(
    *,
    create_option: builtins.str,
    lun: jsii.Number,
    caching: typing.Optional[builtins.str] = None,
    disk_size_gb: typing.Optional[jsii.Number] = None,
    managed_disk: typing.Optional[typing.Union[VirtualMachineManagedDiskParameters, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b8a7606fb8c04f63035ed80b68b434745415882ed017ee0f81d2434ff6b00ad0(
    *,
    boot_diagnostics: typing.Optional[typing.Union[VirtualMachineBootDiagnostics, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__46d3cac574ccab9a26813941420ae74fd8923f7e0c23d6af2fdac04650299b98(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3612ee16f331f4b6766c8e5763572fc70811f182437935c54af982bd7d0329c(
    *,
    vm_size: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2976ef2f0722e68a49eda21313757206a495b5022fc913129207aed6f21ac3a0(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cbf3c03eea87825c0d3a5f3a45cd8db4b3c9a70f52e618b060bc44463f6a9857(
    *,
    type: builtins.str,
    user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__16bfb28d2cc9b5102816ae149aec3a267e23c94f500a20850728c6836ee8e3ac(
    *,
    id: typing.Optional[builtins.str] = None,
    offer: typing.Optional[builtins.str] = None,
    publisher: typing.Optional[builtins.str] = None,
    sku: typing.Optional[builtins.str] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa77674d96fbe349d8be4ef95aad539c498173cc9449abc5a0556fc712504219(
    *,
    disable_password_authentication: typing.Optional[builtins.bool] = None,
    patch_settings: typing.Optional[typing.Union[VirtualMachineLinuxPatchSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    provision_vm_agent: typing.Optional[builtins.bool] = None,
    ssh: typing.Optional[typing.Union[VirtualMachineSshConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2844b57921e0f12a21aa780645b8b02851e094a1996c3943c5db1f772f8587fc(
    *,
    assessment_mode: typing.Optional[builtins.str] = None,
    patch_mode: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6aad03c839c11caaa212967cf358a463354dd6d8d3f6c36958ca862113c5f4f7(
    *,
    disk_encryption_set: typing.Optional[typing.Union[VirtualMachineDiskEncryptionSetParameters, typing.Dict[builtins.str, typing.Any]]] = None,
    id: typing.Optional[builtins.str] = None,
    storage_account_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cf60573bc2b5c3f7397636759fc4118e9fa12e10c04e18260e20fffbfa3fd118(
    *,
    cpu_alert_severity: typing.Optional[jsii.Number] = None,
    cpu_threshold: typing.Optional[jsii.Number] = None,
    disk_queue_alert_severity: typing.Optional[jsii.Number] = None,
    disk_queue_threshold: typing.Optional[jsii.Number] = None,
    enable_cpu_alert: typing.Optional[builtins.bool] = None,
    enable_deletion_alert: typing.Optional[builtins.bool] = None,
    enable_disk_queue_alert: typing.Optional[builtins.bool] = None,
    enable_memory_alert: typing.Optional[builtins.bool] = None,
    memory_alert_severity: typing.Optional[jsii.Number] = None,
    memory_threshold: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6623f0c6fe6e5e1b3d0872cf110cf18e13543b2fd0e9753f208a4674637e7762(
    *,
    primary: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e7ffad6ca3f3e79ed45b41dadd11288c90b6c5ec3b040006e54284a38a40074d(
    *,
    id: builtins.str,
    properties: typing.Optional[typing.Union[VirtualMachineNetworkInterfaceProperties, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f0450bb93bc2e369b3c947237c48ae0be7f52ba28efcac1d240e752ad14d5e28(
    *,
    network_interfaces: typing.Sequence[typing.Union[VirtualMachineNetworkInterfaceReference, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0c2d5267c4ab60ab13e4a47e55737d8875e995e9b139e98e8b9216999ce41fc(
    *,
    create_option: builtins.str,
    caching: typing.Optional[builtins.str] = None,
    disk_size_gb: typing.Optional[jsii.Number] = None,
    managed_disk: typing.Optional[typing.Union[VirtualMachineManagedDiskParameters, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    os_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1cab288f77bf7c6e22f1158554097af504d3fcecbc8ba9b40f174172ffd24e72(
    *,
    admin_username: builtins.str,
    computer_name: builtins.str,
    admin_password: typing.Optional[builtins.str] = None,
    allow_extension_operations: typing.Optional[builtins.bool] = None,
    custom_data: typing.Optional[builtins.str] = None,
    linux_configuration: typing.Optional[typing.Union[VirtualMachineLinuxConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    secrets: typing.Optional[typing.Sequence[typing.Union[VirtualMachineSecret, typing.Dict[builtins.str, typing.Any]]]] = None,
    windows_configuration: typing.Optional[typing.Union[VirtualMachineWindowsConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ccd2958a255f2deb47002b0697951e9de16f6c99f65f3bb72624b924448cf4b5(
    *,
    name: typing.Optional[builtins.str] = None,
    product: typing.Optional[builtins.str] = None,
    promotion_code: typing.Optional[builtins.str] = None,
    publisher: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__64ba3d0560b80440f65f94ff06bf0de00b4bc37df5860fa38463a245a264bbaf(
    *,
    billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    eviction_policy: typing.Optional[builtins.str] = None,
    priority: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e1b6631eaab4b02ac2fdf8aa26a613ea5bfbd21c7d0a8041ed5b7afc1a4b3db5(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    api_version: typing.Optional[builtins.str] = None,
    enable_migration_analysis: typing.Optional[builtins.bool] = None,
    enable_transformation: typing.Optional[builtins.bool] = None,
    enable_validation: typing.Optional[builtins.bool] = None,
    location: typing.Optional[builtins.str] = None,
    monitoring: typing.Optional[typing.Union[_MonitoringConfig_7c28df74, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    hardware_profile: typing.Union[VirtualMachineHardwareProfile, typing.Dict[builtins.str, typing.Any]],
    network_profile: typing.Union[VirtualMachineNetworkProfile, typing.Dict[builtins.str, typing.Any]],
    storage_profile: typing.Union[VirtualMachineStorageProfile, typing.Dict[builtins.str, typing.Any]],
    additional_capabilities: typing.Optional[typing.Union[VirtualMachineAdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
    availability_set: typing.Optional[typing.Union[VirtualMachineAvailabilitySetReference, typing.Dict[builtins.str, typing.Any]]] = None,
    billing_profile: typing.Optional[typing.Union[VirtualMachineBillingProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    diagnostics_profile: typing.Optional[typing.Union[VirtualMachineDiagnosticsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    eviction_policy: typing.Optional[builtins.str] = None,
    host: typing.Optional[typing.Union[VirtualMachineHostReference, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[VirtualMachineIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    license_type: typing.Optional[builtins.str] = None,
    os_profile: typing.Optional[typing.Union[VirtualMachineOSProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    plan: typing.Optional[typing.Union[VirtualMachinePlan, typing.Dict[builtins.str, typing.Any]]] = None,
    priority: typing.Optional[builtins.str] = None,
    proximity_placement_group: typing.Optional[typing.Union[VirtualMachineProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    security_profile: typing.Optional[typing.Union[VirtualMachineSecurityProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    virtual_machine_scale_set: typing.Optional[typing.Union[VirtualMachineScaleSetReference, typing.Dict[builtins.str, typing.Any]]] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a4bceab44218e50edcfdec1e907f3daaaaa7c3e52f5a0d71715263cdeb492697(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0e8e23514ea72f9cbfba41113ebd56fdbd5530a36bc6c4b4be9f34a40135192e(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__42d8c5f3edc7b3c905ce96a1344138c14011dd8e5de2524bc85664cbb9faced1(
    *,
    source_vault: typing.Optional[typing.Union[VirtualMachineSubResource, typing.Dict[builtins.str, typing.Any]]] = None,
    vault_certificates: typing.Optional[typing.Sequence[typing.Union[VirtualMachineVaultCertificate, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b9cc9fbec2e43cf4bd67cf36db09d18f51d6d14bc434102f3addc3f8dc392ef9(
    *,
    encryption_at_host: typing.Optional[builtins.bool] = None,
    security_type: typing.Optional[builtins.str] = None,
    uefi_settings: typing.Optional[typing.Union[VirtualMachineUefiSettings, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e9b675a41499311b259211cd2ac39ead52dadd002a48703cd1a0e5873f0ec5f(
    *,
    public_keys: typing.Optional[typing.Sequence[typing.Union[VirtualMachineSshPublicKey, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7fdb6f9f6ab9cf41b21369f914c7444f9a6a5da11087ea468620529e5d989713(
    *,
    key_data: builtins.str,
    path: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d0ec8f811e056ff027f1d619ab2238fbe7d4ed3ba1e96c13740d849b378042b9(
    *,
    os_disk: typing.Union[VirtualMachineOSDisk, typing.Dict[builtins.str, typing.Any]],
    data_disks: typing.Optional[typing.Sequence[typing.Union[VirtualMachineDataDisk, typing.Dict[builtins.str, typing.Any]]]] = None,
    image_reference: typing.Optional[typing.Union[VirtualMachineImageReference, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8c397700b365b1c773ce8104a60ab728ee9b5c8a026a594b8c8c7a2be3eac94f(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d613f5b2dded4046d80ae15926d374f1a4ae96feffb13d15af4f4bc97417af49(
    *,
    secure_boot_enabled: typing.Optional[builtins.bool] = None,
    v_tpm_enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__458225e7ada8f0d312ec8d23b7372e950b0dcd22a4ea89647a7ac1ba86e089d7(
    *,
    certificate_store: typing.Optional[builtins.str] = None,
    certificate_url: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c372455a2a2ff7a20134c070987118108c1bae6054ddc981e6f1a0af2f56b15d(
    *,
    listeners: typing.Optional[typing.Sequence[typing.Union[VirtualMachineWinRMListener, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffb1e306c6c57b8a2350f629a45eac780bfbb8bb3f0e1deeb4a151a0a0422ee3(
    *,
    protocol: builtins.str,
    certificate_url: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e55cf022c700c4548f66e6c1db98f72ddd79bbd2961955fd11c40358e548bcba(
    *,
    enable_automatic_updates: typing.Optional[builtins.bool] = None,
    patch_settings: typing.Optional[typing.Union[VirtualMachineWindowsPatchSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    provision_vm_agent: typing.Optional[builtins.bool] = None,
    time_zone: typing.Optional[builtins.str] = None,
    win_rm: typing.Optional[typing.Union[VirtualMachineWinRMConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a6df7234ccb2d56eb2c84b0305b86aebc3d295fc29d87b108aa9b83d04790bab(
    *,
    assessment_mode: typing.Optional[builtins.str] = None,
    enable_hotpatching: typing.Optional[builtins.bool] = None,
    patch_mode: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
