r'''
# Azure Virtual Machine Scale Sets (VMSS) Construct

This module provides a CDK construct for creating and managing Azure Virtual Machine Scale Sets using the AzapiResource framework with automatic version management.

## Features

* **Automatic Version Management**: Uses the latest stable API version (2025-04-01) by default
* **Version Pinning**: Support for explicit API version specification
* **Code Reuse**: Leverages VM interfaces for storage, OS, and identity profiles
* **Orchestration Modes**: Support for both Uniform and Flexible orchestration
* **Scaling Features**: Overprovision, zone balance, and automatic repairs
* **Upgrade Policies**: Automatic, Manual, and Rolling upgrade modes
* **Full JSII Compliance**: Multi-language support (TypeScript, Python, Java, C#, Go)

## Installation

```bash
npm install @cdktf/provider-azapi
```

## API Versions

This construct supports the following Azure API versions:

* **2025-01-02**: Initial release with comprehensive VMSS features
* **2025-02-01**: Enhanced orchestration and scaling features
* **2025-04-01**: Latest version with newest features (default)

## Basic Usage

### Understanding VMSS Network Interface Templates

Unlike Virtual Machines that **reference** pre-existing NICs by ID, Virtual Machine Scale Sets use **NIC templates** that define how network interfaces should be created for each VM instance.

**Key Concept**: VMSS creates new NICs automatically for each VM instance based on the template you provide.

```python
import { VirtualMachineScaleSet } from "./azure-vmss";
import { ResourceGroup } from "./azure-resourcegroup";
import type { NetworkInterfaceDnsSettings } from "./azure-networkinterface";

const resourceGroup = new ResourceGroup(this, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

const vmss = new VirtualMachineScaleSet(this, "vmss", {
  name: "my-vmss",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 3,
  },
  orchestrationMode: "Uniform",
  upgradePolicy: {
    mode: "Automatic",
  },
  virtualMachineProfile: {
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
      computerName: "vmss-vm",
      adminUsername: "azureuser",
      linuxConfiguration: {
        disablePasswordAuthentication: true,
        ssh: {
          publicKeys: [
            {
              path: "/home/azureuser/.ssh/authorized_keys",
              keyData: "ssh-rsa AAAAB3NzaC1yc2E...",
            },
          ],
        },
      },
    },
    networkProfile: {
      networkInterfaceConfigurations: [
        {
          name: "nic-config",
          properties: {
            primary: true,
            ipConfigurations: [
              {
                name: "ip-config",
                properties: {
                  subnet: {
                    id: subnet.id,
                  },
                },
              },
            ],
          },
        },
      ],
    },
  },
});
```

### VMSS with Load Balancer Integration

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-lb", {
  name: "my-vmss-with-lb",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 5,
  },
  orchestrationMode: "Uniform",
  upgradePolicy: {
    mode: "Automatic",
  },
  virtualMachineProfile: {
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
      computerName: "vmss-vm",
      adminUsername: "azureuser",
      linuxConfiguration: {
        disablePasswordAuthentication: true,
        ssh: {
          publicKeys: [
            {
              path: "/home/azureuser/.ssh/authorized_keys",
              keyData: "ssh-rsa AAAAB3NzaC1yc2E...",
            },
          ],
        },
      },
    },
    networkProfile: {
      networkInterfaceConfigurations: [
        {
          name: "nic-config",
          properties: {
            primary: true,
            ipConfigurations: [
              {
                name: "ip-config",
                properties: {
                  subnet: {
                    id: subnet.id,
                  },
                  loadBalancerBackendAddressPools: [
                    {
                      id: loadBalancer.backendPoolId,
                    },
                  ],
                },
              },
            ],
          },
        },
      ],
    },
  },
});
```

## Flexible Orchestration Mode

Flexible orchestration mode provides more control over VM placement and management:

```python
const flexibleVmss = new VirtualMachineScaleSet(this, "flexible-vmss", {
  name: "my-flexible-vmss",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 5,
  },
  orchestrationMode: "Flexible",
  platformFaultDomainCount: 1,
  singlePlacementGroup: false,
  virtualMachineProfile: {
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
      computerName: "vmss-vm",
      adminUsername: "azureuser",
      adminPassword: "P@ssw0rd1234!",
    },
    networkProfile: {
      networkInterfaceConfigurations: [
        {
          name: "nic-config",
          properties: {
            primary: true,
            ipConfigurations: [
              {
                name: "ip-config",
                properties: {
                  subnet: {
                    id: subnet.id,
                  },
                },
              },
            ],
          },
        },
      ],
    },
  },
});
```

## Rolling Upgrade Policy

Configure rolling upgrades for controlled deployment of updates:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-rolling", {
  name: "my-vmss-rolling",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 10,
  },
  upgradePolicy: {
    mode: "Rolling",
    rollingUpgradePolicy: {
      maxBatchInstancePercent: 20,
      maxUnhealthyInstancePercent: 20,
      maxUnhealthyUpgradedInstancePercent: 20,
      pauseTimeBetweenBatches: "PT5S",
      enableCrossZoneUpgrade: true,
      prioritizeUnhealthyInstances: true,
    },
    automaticOSUpgradePolicy: {
      enableAutomaticOSUpgrade: true,
      disableAutomaticRollback: false,
      useRollingUpgradePolicy: true,
    },
  },
  virtualMachineProfile: {
    // ... VM profile configuration
  },
});
```

## Automatic Repairs

Enable automatic instance repairs for improved availability:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-repairs", {
  name: "my-vmss-repairs",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 5,
  },
  automaticRepairsPolicy: {
    enabled: true,
    gracePeriod: "PT30M",
    repairAction: "Replace",
  },
  virtualMachineProfile: {
    // ... VM profile configuration
  },
});
```

## Zone-Balanced Deployment

Deploy VMs across availability zones for high availability:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-zones", {
  name: "my-vmss-zones",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  zones: ["1", "2", "3"],
  sku: {
    name: "Standard_D2s_v3",
    capacity: 9,
  },
  zoneBalance: true,
  singlePlacementGroup: false,
  virtualMachineProfile: {
    // ... VM profile configuration
  },
});
```

## Managed Identity

Enable system-assigned or user-assigned managed identity:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-identity", {
  name: "my-vmss-identity",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 3,
  },
  identity: {
    type: "SystemAssigned",
  },
  virtualMachineProfile: {
    // ... VM profile configuration
  },
});
```

## API Version Pinning

Pin to a specific API version for stability:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-pinned", {
  name: "my-vmss-pinned",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2025-02-01", // Pin to specific version
  sku: {
    name: "Standard_D2s_v3",
    capacity: 3,
  },
  virtualMachineProfile: {
    // ... VM profile configuration
  },
});
```

## Properties

### Required Properties

* **name**: The name of the Virtual Machine Scale Set
* **location**: The Azure region where the VMSS will be created
* **sku**: SKU configuration including VM size and capacity

### Optional Properties

* **resourceGroupId**: Resource group ID (defaults to subscription scope)
* **tags**: Dictionary of tags to apply
* **apiVersion**: Explicit API version (defaults to latest)
* **identity**: Managed identity configuration
* **zones**: Availability zones for the VMSS
* **plan**: Plan information for marketplace images
* **orchestrationMode**: "Uniform" or "Flexible"
* **upgradePolicy**: Upgrade policy configuration
* **virtualMachineProfile**: VM configuration profile
* **overprovision**: Whether to overprovision VMs
* **doNotRunExtensionsOnOverprovisionedVMs**: Skip extensions on overprovisioned VMs
* **singlePlacementGroup**: Use single placement group
* **zoneBalance**: Balance VMs across zones
* **platformFaultDomainCount**: Number of fault domains
* **automaticRepairsPolicy**: Automatic repairs configuration
* **scaleInPolicy**: Scale-in policy configuration
* **proximityPlacementGroup**: Proximity placement group reference
* **hostGroup**: Dedicated host group reference
* **additionalCapabilities**: Additional capabilities like Ultra SSD
* **ignoreChanges**: Properties to ignore during updates

## Outputs

The construct provides the following outputs:

* **id**: The resource ID of the VMSS
* **location**: The location of the VMSS
* **name**: The name of the VMSS
* **tags**: The tags assigned to the VMSS
* **uniqueId**: The unique identifier assigned by Azure

## Methods

### addTag(key: string, value: string)

Add a tag to the VMSS (requires redeployment).

### removeTag(key: string)

Remove a tag from the VMSS (requires redeployment).

## Advanced Features

### Scale-In Policy

Control which VMs are removed during scale-in operations:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-scalein", {
  name: "my-vmss-scalein",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 5,
  },
  scaleInPolicy: {
    rules: ["Default", "OldestVM"],
    forceDeletion: false,
  },
  virtualMachineProfile: {
    // ... VM profile configuration
  },
});
```

### Extensions

Add VM extensions to the scale set:

```python
const vmss = new VirtualMachineScaleSet(this, "vmss-ext", {
  name: "my-vmss-extensions",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 3,
  },
  virtualMachineProfile: {
    storageProfile: {
      // ... storage configuration
    },
    osProfile: {
      // ... OS configuration
    },
    networkProfile: {
      // ... network configuration
    },
    extensionProfile: {
      extensions: [
        {
          name: "customScript",
          properties: {
            publisher: "Microsoft.Azure.Extensions",
            type: "CustomScript",
            typeHandlerVersion: "2.1",
            autoUpgradeMinorVersion: true,
            settings: {
              fileUris: ["https://example.com/script.sh"],
            },
            protectedSettings: {
              commandToExecute: "bash script.sh",
            },
          },
        },
      ],
    },
  },
});
```

## Best Practices

1. **Use Managed Identity**: Enable managed identity instead of storing credentials
2. **Zone Deployment**: Deploy across availability zones for high availability
3. **Automatic Repairs**: Enable automatic repairs for improved reliability
4. **Rolling Upgrades**: Use rolling upgrades for zero-downtime updates
5. **Load Balancer Integration**: Use load balancers for distributing traffic
6. **Monitoring**: Enable boot diagnostics and configure monitoring
7. **Version Pinning**: Pin API versions in production for stability

## Troubleshooting

### Schema Validation Errors

If you encounter schema validation errors, ensure all required properties are provided and match the expected types.

### Deployment Failures

Check the Azure portal for detailed error messages and ensure your subscription has sufficient quota.

### Version Compatibility

If using an older API version, some properties may not be available. Refer to the API version documentation.

## Networking Architecture

### NIC Template Pattern vs. NIC Reference Pattern

VMSS uses a fundamentally different networking approach compared to standalone VMs:

| Aspect | Virtual Machine | Virtual Machine Scale Set |
|--------|----------------|---------------------------|
| **NIC Creation** | Pre-created separately | Created from template per instance |
| **Pattern** | Reference by ID | Define template configuration |
| **Management** | Independent lifecycle | Managed with VM instance |
| **Use Case** | Single VM with persistent NIC | Multiple VMs with ephemeral NICs |

### VMSS Network Interface Template Example

```python
import type { NetworkInterfaceDnsSettings } from "./azure-networkinterface";

const vmss = new VirtualMachineScaleSet(this, "vmss", {
  name: "my-vmss",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 3,
  },
  virtualMachineProfile: {
    // ... storage and OS configuration
    networkProfile: {
      // This is a TEMPLATE - Azure creates a NIC for each VM instance
      networkInterfaceConfigurations: [{
        name: "nic-config", // Template name (not the actual NIC name)
        properties: {
          primary: true,
          enableAcceleratedNetworking: true,
          enableIPForwarding: false,
          ipConfigurations: [{
            name: "ipconfig1",
            properties: {
              subnet: { id: subnet.id },
              // Optional: Public IP configuration template
              publicIPAddressConfiguration: {
                name: "public-ip-config",
                properties: {
                  idleTimeoutInMinutes: 15,
                },
              },
              // Optional: Load balancer integration
              loadBalancerBackendAddressPools: [{
                id: loadBalancer.backendPoolId,
              }],
            },
          }],
          // Shared type from NetworkInterface module
          dnsSettings: {
            dnsServers: ["10.0.0.4", "10.0.0.5"],
            internalDnsNameLabel: "vmss-vm",
          } as NetworkInterfaceDnsSettings,
        },
      }],
    },
  },
});
```

### Shared Types with NetworkInterface Module

VMSS imports shared types from the [`NetworkInterface`](../azure-networkinterface/README.md) module for consistency:

```python
import type { NetworkInterfaceDnsSettings } from "./azure-networkinterface";

// Use the shared DNS settings type
const dnsSettings: NetworkInterfaceDnsSettings = {
  dnsServers: ["10.0.0.4"],
  internalDnsNameLabel: "vmss",
};
```

This ensures type consistency across the codebase while maintaining the architectural difference between VM and VMSS networking patterns.

### Why Templates Instead of References?

1. **Scalability**: VMSS can create hundreds of VMs - pre-creating NICs would be impractical
2. **Dynamic Scaling**: Auto-scale operations need to create/delete NICs automatically
3. **Uniformity**: All instances get identical network configuration
4. **Lifecycle**: NICs are created and destroyed with VM instances

## Migration Guide

When upgrading between API versions, the construct will automatically analyze compatibility and provide warnings for breaking changes.

## Related Resources

* [Azure Virtual Machine](../azure-virtualmachine/README.md) - Uses NIC reference pattern
* [Azure Network Interface](../azure-networkinterface/README.md) - Centralized NIC construct
* [Azure Resource Group](../azure-resourcegroup/README.md)
* [Azure Virtual Network](../azure-virtualnetwork/README.md)

## License

This construct is part of the terraform-cdk-constructs library.

## Monitoring

The Virtual Machine Scale Set construct provides built-in monitoring capabilities through the `defaultMonitoring()` static method.

### Default Monitoring Configuration

```python
import { VirtualMachineScaleSet } from '@cdktf/azure-vmss';
import { ActionGroup } from '@cdktf/azure-actiongroup';
import { LogAnalyticsWorkspace } from '@cdktf/azure-loganalyticsworkspace';

const actionGroup = new ActionGroup(this, 'alerts', {
  // ... action group configuration
});

const workspace = new LogAnalyticsWorkspace(this, 'logs', {
  // ... workspace configuration
});

const vmss = new VirtualMachineScaleSet(this, 'vmss', {
  name: 'myvmss',
  location: 'eastus',
  resourceGroupName: resourceGroup.name,
  // ... other properties
  monitoring: VirtualMachineScaleSet.defaultMonitoring(
    actionGroup.id,
    workspace.id
  )
});
```

### Monitored Metrics

The default monitoring configuration includes:

1. **CPU Alert**

   * Metric: `Percentage CPU`
   * Threshold: 75% (default - lower than VM to allow scaling headroom)
   * Severity: Warning (2)
   * Triggers when aggregate CPU usage exceeds threshold
2. **Memory Alert**

   * Metric: `Available Memory Bytes`
   * Threshold: 1GB (default)
   * Severity: Warning (2)
   * Triggers when available memory drops below threshold
3. **Disk Queue Alert**

   * Metric: `OS Disk Queue Depth`
   * Threshold: 32 (default)
   * Severity: Warning (2)
   * Triggers when disk queue depth exceeds threshold
4. **Deletion Alert**

   * Tracks VMSS deletion via Activity Log
   * Severity: Informational

### Custom Monitoring Configuration

Customize thresholds and severities:

```python
const vmss = new VirtualMachineScaleSet(this, 'vmss', {
  name: 'myvmss',
  location: 'eastus',
  resourceGroupName: resourceGroup.name,
  monitoring: VirtualMachineScaleSet.defaultMonitoring(
    actionGroup.id,
    workspace.id,
    {
      cpuThreshold: 85,                  // Higher CPU threshold
      memoryThreshold: 536870912,        // 512MB in bytes
      diskQueueThreshold: 64,            // Higher queue depth
      cpuAlertSeverity: 1,              // Critical for CPU
      enableDiskQueueAlert: false,       // Disable disk monitoring
    }
  )
});
```

### Monitoring Options

All available options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cpuThreshold` | number | 75 | CPU usage percentage threshold |
| `memoryThreshold` | number | 1073741824 | Available memory bytes threshold (1GB) |
| `diskQueueThreshold` | number | 32 | Disk queue depth threshold |
| `enableCpuAlert` | boolean | true | Enable/disable CPU alert |
| `enableMemoryAlert` | boolean | true | Enable/disable memory alert |
| `enableDiskQueueAlert` | boolean | true | Enable/disable disk queue alert |
| `enableDeletionAlert` | boolean | true | Enable/disable deletion tracking |
| `cpuAlertSeverity` | 0|1|2|3|4 | 2 | CPU alert severity (0=Critical, 4=Verbose) |
| `memoryAlertSeverity` | 0|1|2|3|4 | 2 | Memory alert severity |
| `diskQueueAlertSeverity` | 0|1|2|3|4 | 2 | Disk queue alert severity |

### Note on CPU Threshold

The default CPU threshold for VMSS (75%) is lower than standalone VMs (80%) to provide headroom for auto-scaling. This allows the scale set to trigger scaling operations before reaching saturation.
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
from ..azure_networkinterface import (
    NetworkInterfaceDnsSettings as _NetworkInterfaceDnsSettings_c9406208
)
from ..azure_virtualmachine import (
    VirtualMachineBillingProfile as _VirtualMachineBillingProfile_b57d8936,
    VirtualMachineDiagnosticsProfile as _VirtualMachineDiagnosticsProfile_05cee027,
    VirtualMachineIdentity as _VirtualMachineIdentity_dc7decb0,
    VirtualMachineLinuxConfiguration as _VirtualMachineLinuxConfiguration_5f791d4c,
    VirtualMachinePlan as _VirtualMachinePlan_2ca6c6de,
    VirtualMachineSecurityProfile as _VirtualMachineSecurityProfile_59175751,
    VirtualMachineStorageProfile as _VirtualMachineStorageProfile_793daa4a,
    VirtualMachineWindowsConfiguration as _VirtualMachineWindowsConfiguration_31cdebe5,
)
from ..core_azure import (
    ApiSchema as _ApiSchema_5ce0490e,
    AzapiResource as _AzapiResource_7e7f5b39,
    MonitoringConfig as _MonitoringConfig_7c28df74,
)


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.AdditionalCapabilities",
    jsii_struct_bases=[],
    name_mapping={"ultra_ssd_enabled": "ultraSSDEnabled"},
)
class AdditionalCapabilities:
    def __init__(
        self,
        *,
        ultra_ssd_enabled: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Additional capabilities.

        :param ultra_ssd_enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f0088e60f6cc210be020fce08d77607368139fad3a793d3157cd2283c444476d)
            check_type(argname="argument ultra_ssd_enabled", value=ultra_ssd_enabled, expected_type=type_hints["ultra_ssd_enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if ultra_ssd_enabled is not None:
            self._values["ultra_ssd_enabled"] = ultra_ssd_enabled

    @builtins.property
    def ultra_ssd_enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("ultra_ssd_enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AdditionalCapabilities(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.AutomaticOSUpgradePolicy",
    jsii_struct_bases=[],
    name_mapping={
        "disable_automatic_rollback": "disableAutomaticRollback",
        "enable_automatic_os_upgrade": "enableAutomaticOSUpgrade",
        "use_rolling_upgrade_policy": "useRollingUpgradePolicy",
    },
)
class AutomaticOSUpgradePolicy:
    def __init__(
        self,
        *,
        disable_automatic_rollback: typing.Optional[builtins.bool] = None,
        enable_automatic_os_upgrade: typing.Optional[builtins.bool] = None,
        use_rolling_upgrade_policy: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Automatic OS upgrade policy.

        :param disable_automatic_rollback: 
        :param enable_automatic_os_upgrade: 
        :param use_rolling_upgrade_policy: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__62e07bb01afa007f00b0ecb6d0a7431aa925fac6767cc8d206361551144fcf91)
            check_type(argname="argument disable_automatic_rollback", value=disable_automatic_rollback, expected_type=type_hints["disable_automatic_rollback"])
            check_type(argname="argument enable_automatic_os_upgrade", value=enable_automatic_os_upgrade, expected_type=type_hints["enable_automatic_os_upgrade"])
            check_type(argname="argument use_rolling_upgrade_policy", value=use_rolling_upgrade_policy, expected_type=type_hints["use_rolling_upgrade_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if disable_automatic_rollback is not None:
            self._values["disable_automatic_rollback"] = disable_automatic_rollback
        if enable_automatic_os_upgrade is not None:
            self._values["enable_automatic_os_upgrade"] = enable_automatic_os_upgrade
        if use_rolling_upgrade_policy is not None:
            self._values["use_rolling_upgrade_policy"] = use_rolling_upgrade_policy

    @builtins.property
    def disable_automatic_rollback(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("disable_automatic_rollback")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_automatic_os_upgrade(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_automatic_os_upgrade")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def use_rolling_upgrade_policy(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("use_rolling_upgrade_policy")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AutomaticOSUpgradePolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.AutomaticRepairsPolicy",
    jsii_struct_bases=[],
    name_mapping={
        "enabled": "enabled",
        "grace_period": "gracePeriod",
        "repair_action": "repairAction",
    },
)
class AutomaticRepairsPolicy:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        grace_period: typing.Optional[builtins.str] = None,
        repair_action: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Automatic repairs policy.

        :param enabled: 
        :param grace_period: 
        :param repair_action: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b14d6a8fc1e86da57bf89ff582ba9ea0035ac64deac0d28ae8a59983ed9419a)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument grace_period", value=grace_period, expected_type=type_hints["grace_period"])
            check_type(argname="argument repair_action", value=repair_action, expected_type=type_hints["repair_action"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if grace_period is not None:
            self._values["grace_period"] = grace_period
        if repair_action is not None:
            self._values["repair_action"] = repair_action

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def grace_period(self) -> typing.Optional[builtins.str]:
        result = self._values.get("grace_period")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def repair_action(self) -> typing.Optional[builtins.str]:
        result = self._values.get("repair_action")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AutomaticRepairsPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.ExtensionProfile",
    jsii_struct_bases=[],
    name_mapping={"extensions": "extensions"},
)
class ExtensionProfile:
    def __init__(
        self,
        *,
        extensions: typing.Optional[typing.Sequence[typing.Union["VMExtension", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Extension profile.

        :param extensions: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__051635f4e54cae7c4ccea9f47d12a2c4680a7f61a9836fbd633dc7d7aa077e2f)
            check_type(argname="argument extensions", value=extensions, expected_type=type_hints["extensions"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if extensions is not None:
            self._values["extensions"] = extensions

    @builtins.property
    def extensions(self) -> typing.Optional[typing.List["VMExtension"]]:
        result = self._values.get("extensions")
        return typing.cast(typing.Optional[typing.List["VMExtension"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ExtensionProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.HealthProbeReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class HealthProbeReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Health probe reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d7dae2afdd0c946d6ed2877367ab322d9149ab56798dd280538ca8c263f641a2)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "HealthProbeReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.HostGroupReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class HostGroupReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Host group reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__23c76e3e8ca30c8791a2bd83f634892e97a0563ac0c394e12bacdee7ac36449c)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "HostGroupReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.interface(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.IPConfiguration"
)
class IPConfiguration(typing_extensions.Protocol):
    '''Network interface IP configuration.'''

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        ...

    @builtins.property
    @jsii.member(jsii_name="properties")
    def properties(self) -> typing.Optional["IPConfigurationProperties"]:
        ...


class _IPConfigurationProxy:
    '''Network interface IP configuration.'''

    __jsii_type__: typing.ClassVar[str] = "@microsoft/terraform-cdk-constructs.azure_vmss.IPConfiguration"

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="properties")
    def properties(self) -> typing.Optional["IPConfigurationProperties"]:
        return typing.cast(typing.Optional["IPConfigurationProperties"], jsii.get(self, "properties"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IPConfiguration).__jsii_proxy_class__ = lambda : _IPConfigurationProxy


@jsii.interface(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.IPConfigurationProperties"
)
class IPConfigurationProperties(typing_extensions.Protocol):
    '''IP configuration properties.'''

    @builtins.property
    @jsii.member(jsii_name="applicationGatewayBackendAddressPools")
    def application_gateway_backend_address_pools(
        self,
    ) -> typing.Optional[typing.List["ResourceReference"]]:
        ...

    @builtins.property
    @jsii.member(jsii_name="loadBalancerBackendAddressPools")
    def load_balancer_backend_address_pools(
        self,
    ) -> typing.Optional[typing.List["ResourceReference"]]:
        ...

    @builtins.property
    @jsii.member(jsii_name="loadBalancerInboundNatPools")
    def load_balancer_inbound_nat_pools(
        self,
    ) -> typing.Optional[typing.List["ResourceReference"]]:
        ...

    @builtins.property
    @jsii.member(jsii_name="primary")
    def primary(self) -> typing.Optional[builtins.bool]:
        ...

    @builtins.property
    @jsii.member(jsii_name="privateIPAddressVersion")
    def private_ip_address_version(self) -> typing.Optional[builtins.str]:
        ...

    @builtins.property
    @jsii.member(jsii_name="publicIPAddressConfiguration")
    def public_ip_address_configuration(
        self,
    ) -> typing.Optional["PublicIPAddressConfiguration"]:
        ...

    @builtins.property
    @jsii.member(jsii_name="subnet")
    def subnet(self) -> typing.Optional["IPConfigurationSubnet"]:
        ...


class _IPConfigurationPropertiesProxy:
    '''IP configuration properties.'''

    __jsii_type__: typing.ClassVar[str] = "@microsoft/terraform-cdk-constructs.azure_vmss.IPConfigurationProperties"

    @builtins.property
    @jsii.member(jsii_name="applicationGatewayBackendAddressPools")
    def application_gateway_backend_address_pools(
        self,
    ) -> typing.Optional[typing.List["ResourceReference"]]:
        return typing.cast(typing.Optional[typing.List["ResourceReference"]], jsii.get(self, "applicationGatewayBackendAddressPools"))

    @builtins.property
    @jsii.member(jsii_name="loadBalancerBackendAddressPools")
    def load_balancer_backend_address_pools(
        self,
    ) -> typing.Optional[typing.List["ResourceReference"]]:
        return typing.cast(typing.Optional[typing.List["ResourceReference"]], jsii.get(self, "loadBalancerBackendAddressPools"))

    @builtins.property
    @jsii.member(jsii_name="loadBalancerInboundNatPools")
    def load_balancer_inbound_nat_pools(
        self,
    ) -> typing.Optional[typing.List["ResourceReference"]]:
        return typing.cast(typing.Optional[typing.List["ResourceReference"]], jsii.get(self, "loadBalancerInboundNatPools"))

    @builtins.property
    @jsii.member(jsii_name="primary")
    def primary(self) -> typing.Optional[builtins.bool]:
        return typing.cast(typing.Optional[builtins.bool], jsii.get(self, "primary"))

    @builtins.property
    @jsii.member(jsii_name="privateIPAddressVersion")
    def private_ip_address_version(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "privateIPAddressVersion"))

    @builtins.property
    @jsii.member(jsii_name="publicIPAddressConfiguration")
    def public_ip_address_configuration(
        self,
    ) -> typing.Optional["PublicIPAddressConfiguration"]:
        return typing.cast(typing.Optional["PublicIPAddressConfiguration"], jsii.get(self, "publicIPAddressConfiguration"))

    @builtins.property
    @jsii.member(jsii_name="subnet")
    def subnet(self) -> typing.Optional["IPConfigurationSubnet"]:
        return typing.cast(typing.Optional["IPConfigurationSubnet"], jsii.get(self, "subnet"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IPConfigurationProperties).__jsii_proxy_class__ = lambda : _IPConfigurationPropertiesProxy


@jsii.interface(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.IPConfigurationSubnet"
)
class IPConfigurationSubnet(typing_extensions.Protocol):
    '''IP configuration subnet reference.'''

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        ...


class _IPConfigurationSubnetProxy:
    '''IP configuration subnet reference.'''

    __jsii_type__: typing.ClassVar[str] = "@microsoft/terraform-cdk-constructs.azure_vmss.IPConfigurationSubnet"

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the interface
typing.cast(typing.Any, IPConfigurationSubnet).__jsii_proxy_class__ = lambda : _IPConfigurationSubnetProxy


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.NetworkInterfaceConfiguration",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "properties": "properties"},
)
class NetworkInterfaceConfiguration:
    def __init__(
        self,
        *,
        name: builtins.str,
        properties: typing.Optional[typing.Union["NetworkInterfaceConfigurationProperties", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Network interface configuration for VMSS.

        :param name: 
        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = NetworkInterfaceConfigurationProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2a623aca9e086117d581dee086d19b1e81ca257e74ed9ae69dff476645bc8cc3)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }
        if properties is not None:
            self._values["properties"] = properties

    @builtins.property
    def name(self) -> builtins.str:
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> typing.Optional["NetworkInterfaceConfigurationProperties"]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional["NetworkInterfaceConfigurationProperties"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.NetworkInterfaceConfigurationProperties",
    jsii_struct_bases=[],
    name_mapping={
        "ip_configurations": "ipConfigurations",
        "dns_settings": "dnsSettings",
        "enable_accelerated_networking": "enableAcceleratedNetworking",
        "enable_ip_forwarding": "enableIPForwarding",
        "network_security_group": "networkSecurityGroup",
        "primary": "primary",
    },
)
class NetworkInterfaceConfigurationProperties:
    def __init__(
        self,
        *,
        ip_configurations: typing.Sequence[IPConfiguration],
        dns_settings: typing.Optional[typing.Union[_NetworkInterfaceDnsSettings_c9406208, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_accelerated_networking: typing.Optional[builtins.bool] = None,
        enable_ip_forwarding: typing.Optional[builtins.bool] = None,
        network_security_group: typing.Optional[typing.Union["NetworkSecurityGroupReference", typing.Dict[builtins.str, typing.Any]]] = None,
        primary: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Network interface configuration properties Uses NetworkInterfaceDnsSettings from azure-networkinterface for consistency.

        :param ip_configurations: 
        :param dns_settings: 
        :param enable_accelerated_networking: 
        :param enable_ip_forwarding: 
        :param network_security_group: 
        :param primary: 
        '''
        if isinstance(dns_settings, dict):
            dns_settings = _NetworkInterfaceDnsSettings_c9406208(**dns_settings)
        if isinstance(network_security_group, dict):
            network_security_group = NetworkSecurityGroupReference(**network_security_group)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6c8728bc5e1e2d6411f5fe2492fa5a0e3fd8684f1afd3c181ae0a74e3ca0b504)
            check_type(argname="argument ip_configurations", value=ip_configurations, expected_type=type_hints["ip_configurations"])
            check_type(argname="argument dns_settings", value=dns_settings, expected_type=type_hints["dns_settings"])
            check_type(argname="argument enable_accelerated_networking", value=enable_accelerated_networking, expected_type=type_hints["enable_accelerated_networking"])
            check_type(argname="argument enable_ip_forwarding", value=enable_ip_forwarding, expected_type=type_hints["enable_ip_forwarding"])
            check_type(argname="argument network_security_group", value=network_security_group, expected_type=type_hints["network_security_group"])
            check_type(argname="argument primary", value=primary, expected_type=type_hints["primary"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "ip_configurations": ip_configurations,
        }
        if dns_settings is not None:
            self._values["dns_settings"] = dns_settings
        if enable_accelerated_networking is not None:
            self._values["enable_accelerated_networking"] = enable_accelerated_networking
        if enable_ip_forwarding is not None:
            self._values["enable_ip_forwarding"] = enable_ip_forwarding
        if network_security_group is not None:
            self._values["network_security_group"] = network_security_group
        if primary is not None:
            self._values["primary"] = primary

    @builtins.property
    def ip_configurations(self) -> typing.List[IPConfiguration]:
        result = self._values.get("ip_configurations")
        assert result is not None, "Required property 'ip_configurations' is missing"
        return typing.cast(typing.List[IPConfiguration], result)

    @builtins.property
    def dns_settings(self) -> typing.Optional[_NetworkInterfaceDnsSettings_c9406208]:
        result = self._values.get("dns_settings")
        return typing.cast(typing.Optional[_NetworkInterfaceDnsSettings_c9406208], result)

    @builtins.property
    def enable_accelerated_networking(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_accelerated_networking")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_ip_forwarding(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_ip_forwarding")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def network_security_group(
        self,
    ) -> typing.Optional["NetworkSecurityGroupReference"]:
        result = self._values.get("network_security_group")
        return typing.cast(typing.Optional["NetworkSecurityGroupReference"], result)

    @builtins.property
    def primary(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("primary")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceConfigurationProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.NetworkSecurityGroupReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class NetworkSecurityGroupReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Network security group reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dd0a23e57cee8a498aa81813906b4f4b1ea7c684648d5bd872ce8ef71c9d6574)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkSecurityGroupReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.ProximityPlacementGroupReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class ProximityPlacementGroupReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Proximity placement group reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9eaf8a7eb0c95d5841934337d1e2b31a09c8795b9ac74fafc7fc0b14de3bbb0d)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ProximityPlacementGroupReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.PublicIPAddressConfiguration",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "properties": "properties"},
)
class PublicIPAddressConfiguration:
    def __init__(
        self,
        *,
        name: builtins.str,
        properties: typing.Optional[typing.Union["PublicIPAddressConfigurationProperties", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Public IP address configuration.

        :param name: 
        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = PublicIPAddressConfigurationProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__11077ef88da161c6f6321c07480b6570cdb9fd7010244c6a56c71adfcab1deb8)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }
        if properties is not None:
            self._values["properties"] = properties

    @builtins.property
    def name(self) -> builtins.str:
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> typing.Optional["PublicIPAddressConfigurationProperties"]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional["PublicIPAddressConfigurationProperties"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PublicIPAddressConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.PublicIPAddressConfigurationProperties",
    jsii_struct_bases=[],
    name_mapping={
        "dns_settings": "dnsSettings",
        "idle_timeout_in_minutes": "idleTimeoutInMinutes",
    },
)
class PublicIPAddressConfigurationProperties:
    def __init__(
        self,
        *,
        dns_settings: typing.Optional[typing.Union["PublicIPDnsSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Public IP address configuration properties.

        :param dns_settings: 
        :param idle_timeout_in_minutes: 
        '''
        if isinstance(dns_settings, dict):
            dns_settings = PublicIPDnsSettings(**dns_settings)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__05760d45e9db0243881b99a335fcb383ef3bad2524d1012483f7d8192cb20576)
            check_type(argname="argument dns_settings", value=dns_settings, expected_type=type_hints["dns_settings"])
            check_type(argname="argument idle_timeout_in_minutes", value=idle_timeout_in_minutes, expected_type=type_hints["idle_timeout_in_minutes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dns_settings is not None:
            self._values["dns_settings"] = dns_settings
        if idle_timeout_in_minutes is not None:
            self._values["idle_timeout_in_minutes"] = idle_timeout_in_minutes

    @builtins.property
    def dns_settings(self) -> typing.Optional["PublicIPDnsSettings"]:
        result = self._values.get("dns_settings")
        return typing.cast(typing.Optional["PublicIPDnsSettings"], result)

    @builtins.property
    def idle_timeout_in_minutes(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("idle_timeout_in_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PublicIPAddressConfigurationProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.PublicIPDnsSettings",
    jsii_struct_bases=[],
    name_mapping={"domain_name_label": "domainNameLabel"},
)
class PublicIPDnsSettings:
    def __init__(self, *, domain_name_label: builtins.str) -> None:
        '''DNS settings for public IP.

        :param domain_name_label: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13fbcf768d77cc18efed3fec7825d97d3af3997acf5ac011fa18b9d4f27b7a35)
            check_type(argname="argument domain_name_label", value=domain_name_label, expected_type=type_hints["domain_name_label"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "domain_name_label": domain_name_label,
        }

    @builtins.property
    def domain_name_label(self) -> builtins.str:
        result = self._values.get("domain_name_label")
        assert result is not None, "Required property 'domain_name_label' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PublicIPDnsSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.ResourceReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class ResourceReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Resource reference with ID.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5784636f85d4a41eaa83f9bd150a53874161ae1b2ae8df94c4fc468d11df2c12)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.RollingUpgradePolicy",
    jsii_struct_bases=[],
    name_mapping={
        "enable_cross_zone_upgrade": "enableCrossZoneUpgrade",
        "max_batch_instance_percent": "maxBatchInstancePercent",
        "max_unhealthy_instance_percent": "maxUnhealthyInstancePercent",
        "max_unhealthy_upgraded_instance_percent": "maxUnhealthyUpgradedInstancePercent",
        "pause_time_between_batches": "pauseTimeBetweenBatches",
        "prioritize_unhealthy_instances": "prioritizeUnhealthyInstances",
    },
)
class RollingUpgradePolicy:
    def __init__(
        self,
        *,
        enable_cross_zone_upgrade: typing.Optional[builtins.bool] = None,
        max_batch_instance_percent: typing.Optional[jsii.Number] = None,
        max_unhealthy_instance_percent: typing.Optional[jsii.Number] = None,
        max_unhealthy_upgraded_instance_percent: typing.Optional[jsii.Number] = None,
        pause_time_between_batches: typing.Optional[builtins.str] = None,
        prioritize_unhealthy_instances: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Rolling upgrade policy.

        :param enable_cross_zone_upgrade: 
        :param max_batch_instance_percent: 
        :param max_unhealthy_instance_percent: 
        :param max_unhealthy_upgraded_instance_percent: 
        :param pause_time_between_batches: 
        :param prioritize_unhealthy_instances: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__71b43cade14359f34e3069ca8c745262fb8f856c96ec51f74b13172a3a316b92)
            check_type(argname="argument enable_cross_zone_upgrade", value=enable_cross_zone_upgrade, expected_type=type_hints["enable_cross_zone_upgrade"])
            check_type(argname="argument max_batch_instance_percent", value=max_batch_instance_percent, expected_type=type_hints["max_batch_instance_percent"])
            check_type(argname="argument max_unhealthy_instance_percent", value=max_unhealthy_instance_percent, expected_type=type_hints["max_unhealthy_instance_percent"])
            check_type(argname="argument max_unhealthy_upgraded_instance_percent", value=max_unhealthy_upgraded_instance_percent, expected_type=type_hints["max_unhealthy_upgraded_instance_percent"])
            check_type(argname="argument pause_time_between_batches", value=pause_time_between_batches, expected_type=type_hints["pause_time_between_batches"])
            check_type(argname="argument prioritize_unhealthy_instances", value=prioritize_unhealthy_instances, expected_type=type_hints["prioritize_unhealthy_instances"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enable_cross_zone_upgrade is not None:
            self._values["enable_cross_zone_upgrade"] = enable_cross_zone_upgrade
        if max_batch_instance_percent is not None:
            self._values["max_batch_instance_percent"] = max_batch_instance_percent
        if max_unhealthy_instance_percent is not None:
            self._values["max_unhealthy_instance_percent"] = max_unhealthy_instance_percent
        if max_unhealthy_upgraded_instance_percent is not None:
            self._values["max_unhealthy_upgraded_instance_percent"] = max_unhealthy_upgraded_instance_percent
        if pause_time_between_batches is not None:
            self._values["pause_time_between_batches"] = pause_time_between_batches
        if prioritize_unhealthy_instances is not None:
            self._values["prioritize_unhealthy_instances"] = prioritize_unhealthy_instances

    @builtins.property
    def enable_cross_zone_upgrade(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_cross_zone_upgrade")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def max_batch_instance_percent(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("max_batch_instance_percent")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_unhealthy_instance_percent(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("max_unhealthy_instance_percent")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_unhealthy_upgraded_instance_percent(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("max_unhealthy_upgraded_instance_percent")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def pause_time_between_batches(self) -> typing.Optional[builtins.str]:
        result = self._values.get("pause_time_between_batches")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def prioritize_unhealthy_instances(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("prioritize_unhealthy_instances")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RollingUpgradePolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.ScheduledEventsProfile",
    jsii_struct_bases=[],
    name_mapping={"terminate_notification_profile": "terminateNotificationProfile"},
)
class ScheduledEventsProfile:
    def __init__(
        self,
        *,
        terminate_notification_profile: typing.Optional[typing.Union["TerminateNotificationProfile", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Scheduled events profile.

        :param terminate_notification_profile: 
        '''
        if isinstance(terminate_notification_profile, dict):
            terminate_notification_profile = TerminateNotificationProfile(**terminate_notification_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__959dd21066c22148be0155dd74d2c85d1b44501e92218a482393c3f4fd442b3f)
            check_type(argname="argument terminate_notification_profile", value=terminate_notification_profile, expected_type=type_hints["terminate_notification_profile"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if terminate_notification_profile is not None:
            self._values["terminate_notification_profile"] = terminate_notification_profile

    @builtins.property
    def terminate_notification_profile(
        self,
    ) -> typing.Optional["TerminateNotificationProfile"]:
        result = self._values.get("terminate_notification_profile")
        return typing.cast(typing.Optional["TerminateNotificationProfile"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ScheduledEventsProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.TerminateNotificationProfile",
    jsii_struct_bases=[],
    name_mapping={"enable": "enable", "not_before_timeout": "notBeforeTimeout"},
)
class TerminateNotificationProfile:
    def __init__(
        self,
        *,
        enable: typing.Optional[builtins.bool] = None,
        not_before_timeout: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Terminate notification profile.

        :param enable: 
        :param not_before_timeout: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6efba26ec34394ce7b3cea1473ba77010839e891ad4d7e712b3b3389c8033098)
            check_type(argname="argument enable", value=enable, expected_type=type_hints["enable"])
            check_type(argname="argument not_before_timeout", value=not_before_timeout, expected_type=type_hints["not_before_timeout"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enable is not None:
            self._values["enable"] = enable
        if not_before_timeout is not None:
            self._values["not_before_timeout"] = not_before_timeout

    @builtins.property
    def enable(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def not_before_timeout(self) -> typing.Optional[builtins.str]:
        result = self._values.get("not_before_timeout")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TerminateNotificationProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VMExtension",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "properties": "properties"},
)
class VMExtension:
    def __init__(
        self,
        *,
        name: builtins.str,
        properties: typing.Optional[typing.Union["VMExtensionProperties", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''VM extension.

        :param name: 
        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = VMExtensionProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4a8a8ef54ba5745c8f4492cdf6496b727e4d03049c2e9192e380d0a9e9c81417)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }
        if properties is not None:
            self._values["properties"] = properties

    @builtins.property
    def name(self) -> builtins.str:
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> typing.Optional["VMExtensionProperties"]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional["VMExtensionProperties"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VMExtension(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VMExtensionProperties",
    jsii_struct_bases=[],
    name_mapping={
        "publisher": "publisher",
        "type": "type",
        "type_handler_version": "typeHandlerVersion",
        "auto_upgrade_minor_version": "autoUpgradeMinorVersion",
        "protected_settings": "protectedSettings",
        "settings": "settings",
    },
)
class VMExtensionProperties:
    def __init__(
        self,
        *,
        publisher: builtins.str,
        type: builtins.str,
        type_handler_version: builtins.str,
        auto_upgrade_minor_version: typing.Optional[builtins.bool] = None,
        protected_settings: typing.Any = None,
        settings: typing.Any = None,
    ) -> None:
        '''Extension properties.

        :param publisher: 
        :param type: 
        :param type_handler_version: 
        :param auto_upgrade_minor_version: 
        :param protected_settings: 
        :param settings: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e39d70b519d8b37ddffbec6c492e6a63e3c01e54b161c44a46db2cb85815b75f)
            check_type(argname="argument publisher", value=publisher, expected_type=type_hints["publisher"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument type_handler_version", value=type_handler_version, expected_type=type_hints["type_handler_version"])
            check_type(argname="argument auto_upgrade_minor_version", value=auto_upgrade_minor_version, expected_type=type_hints["auto_upgrade_minor_version"])
            check_type(argname="argument protected_settings", value=protected_settings, expected_type=type_hints["protected_settings"])
            check_type(argname="argument settings", value=settings, expected_type=type_hints["settings"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "publisher": publisher,
            "type": type,
            "type_handler_version": type_handler_version,
        }
        if auto_upgrade_minor_version is not None:
            self._values["auto_upgrade_minor_version"] = auto_upgrade_minor_version
        if protected_settings is not None:
            self._values["protected_settings"] = protected_settings
        if settings is not None:
            self._values["settings"] = settings

    @builtins.property
    def publisher(self) -> builtins.str:
        result = self._values.get("publisher")
        assert result is not None, "Required property 'publisher' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type_handler_version(self) -> builtins.str:
        result = self._values.get("type_handler_version")
        assert result is not None, "Required property 'type_handler_version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def auto_upgrade_minor_version(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("auto_upgrade_minor_version")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def protected_settings(self) -> typing.Any:
        result = self._values.get("protected_settings")
        return typing.cast(typing.Any, result)

    @builtins.property
    def settings(self) -> typing.Any:
        result = self._values.get("settings")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VMExtensionProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class VirtualMachineScaleSet(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSet",
):
    '''Unified Azure Virtual Machine Scale Set implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    The class uses the AzapiResource framework to provide:

    - Automatic latest version resolution (2025-04-01 as of this implementation)
    - Support for explicit version pinning when stability is required
    - Schema-driven property validation and transformation
    - Migration analysis and deprecation warnings
    - Full JSII compliance for multi-language support

    Example::

        // Flexible orchestration mode with rolling upgrades:
        const flexibleVmss = new VirtualMachineScaleSet(this, "flexible-vmss", {
          name: "my-flexible-vmss",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          sku: {
            name: "Standard_D2s_v3",
            capacity: 5
          },
          orchestrationMode: "Flexible",
          upgradePolicy: {
            mode: "Rolling",
            rollingUpgradePolicy: {
              maxBatchInstancePercent: 20,
              maxUnhealthyInstancePercent: 20,
              maxUnhealthyUpgradedInstancePercent: 20,
              pauseTimeBetweenBatches: "PT5S"
            }
          },
          automaticRepairsPolicy: {
            enabled: true,
            gracePeriod: "PT30M"
          }
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        location: builtins.str,
        name: builtins.str,
        sku: typing.Union["VirtualMachineScaleSetSku", typing.Dict[builtins.str, typing.Any]],
        additional_capabilities: typing.Optional[typing.Union[AdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
        api_version: typing.Optional[builtins.str] = None,
        automatic_repairs_policy: typing.Optional[typing.Union[AutomaticRepairsPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
        do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        host_group: typing.Optional[typing.Union[HostGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union[_VirtualMachineIdentity_dc7decb0, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        monitoring: typing.Any = None,
        orchestration_mode: typing.Optional[builtins.str] = None,
        overprovision: typing.Optional[builtins.bool] = None,
        plan: typing.Optional[typing.Union[_VirtualMachinePlan_2ca6c6de, typing.Dict[builtins.str, typing.Any]]] = None,
        platform_fault_domain_count: typing.Optional[jsii.Number] = None,
        proximity_placement_group: typing.Optional[typing.Union[ProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        scale_in_policy: typing.Optional[typing.Union["VirtualMachineScaleSetScaleInPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        single_placement_group: typing.Optional[builtins.bool] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        upgrade_policy: typing.Optional[typing.Union["VirtualMachineScaleSetUpgradePolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        virtual_machine_profile: typing.Optional[typing.Union["VirtualMachineScaleSetVMProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        zone_balance: typing.Optional[builtins.bool] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Creates a new Azure Virtual Machine Scale Set using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param location: 
        :param name: 
        :param sku: 
        :param additional_capabilities: 
        :param api_version: 
        :param automatic_repairs_policy: 
        :param do_not_run_extensions_on_overprovisioned_v_ms: 
        :param enable_migration_analysis: 
        :param enable_transformation: 
        :param enable_validation: 
        :param host_group: 
        :param identity: 
        :param ignore_changes: 
        :param monitoring: 
        :param orchestration_mode: 
        :param overprovision: 
        :param plan: 
        :param platform_fault_domain_count: 
        :param proximity_placement_group: 
        :param resource_group_id: 
        :param scale_in_policy: 
        :param single_placement_group: 
        :param tags: 
        :param upgrade_policy: 
        :param virtual_machine_profile: 
        :param zone_balance: 
        :param zones: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b6a3b588a8afae9a429644692a96c1a609f151d1c1e26aa9a1d49dc087da02d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VirtualMachineScaleSetProps(
            location=location,
            name=name,
            sku=sku,
            additional_capabilities=additional_capabilities,
            api_version=api_version,
            automatic_repairs_policy=automatic_repairs_policy,
            do_not_run_extensions_on_overprovisioned_v_ms=do_not_run_extensions_on_overprovisioned_v_ms,
            enable_migration_analysis=enable_migration_analysis,
            enable_transformation=enable_transformation,
            enable_validation=enable_validation,
            host_group=host_group,
            identity=identity,
            ignore_changes=ignore_changes,
            monitoring=monitoring,
            orchestration_mode=orchestration_mode,
            overprovision=overprovision,
            plan=plan,
            platform_fault_domain_count=platform_fault_domain_count,
            proximity_placement_group=proximity_placement_group,
            resource_group_id=resource_group_id,
            scale_in_policy=scale_in_policy,
            single_placement_group=single_placement_group,
            tags=tags,
            upgrade_policy=upgrade_policy,
            virtual_machine_profile=virtual_machine_profile,
            zone_balance=zone_balance,
            zones=zones,
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
        '''Returns a production-ready monitoring configuration for Virtual Machine Scale Sets.

        This static factory method provides a complete MonitoringConfig with sensible defaults
        for VMSS monitoring including CPU, memory, disk queue alerts, and deletion tracking.

        VMSS uses a lower CPU threshold (75%) compared to single VMs (80%) to allow headroom
        for scaling operations before reaching saturation.

        :param action_group_id: - The resource ID of the action group for alert notifications.
        :param workspace_id: - Optional Log Analytics workspace ID for diagnostic settings.
        :param cpu_alert_severity: Severity level for CPU usage alerts. - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2
        :param cpu_threshold: CPU usage threshold percentage for triggering alerts. VMSS uses a lower default threshold (75%) compared to single VMs (80%) to allow headroom for scaling operations before reaching saturation. Default: 75
        :param disk_queue_alert_severity: Severity level for disk queue depth alerts. - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2
        :param disk_queue_threshold: Disk queue depth threshold for triggering alerts. High disk queue depth can indicate disk performance bottlenecks. Default: 32
        :param enable_cpu_alert: Enable or disable CPU usage alert. Default: true
        :param enable_deletion_alert: Enable or disable VMSS deletion activity log alert. Default: true
        :param enable_disk_queue_alert: Enable or disable disk queue depth alert. Default: true
        :param enable_memory_alert: Enable or disable memory usage alert. Default: true
        :param memory_alert_severity: Severity level for memory usage alerts. - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2
        :param memory_threshold: Available memory threshold in bytes for triggering alerts. When available memory drops below this threshold, an alert will be triggered. Default is 1GB (1073741824 bytes). Default: 1073741824

        :return: A complete MonitoringConfig object ready to use in VirtualMachineScaleSet props

        Example::

            // Custom thresholds and severities
            const vmss = new VirtualMachineScaleSet(this, "vmss", {
              // ... other properties ...
              monitoring: VirtualMachineScaleSet.defaultMonitoring(
                actionGroup.id,
                workspace.id,
                {
                  cpuThreshold: 85,
                  memoryThreshold: 536870912, // 512MB
                  enableDiskQueueAlert: false,
                  cpuAlertSeverity: 1 // Error level
                }
              )
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6917380daf4e70524dba89082ea35abaab15ac19a6730218756860a5d62c434c)
            check_type(argname="argument action_group_id", value=action_group_id, expected_type=type_hints["action_group_id"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
        options = VmssMonitoringOptions(
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
        '''Add a tag to the Virtual Machine Scale Set Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__541c4a270054d2680122cb241f756d617a76fcbb9f41ec30413915ccab305805)
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
            type_hints = typing.get_type_hints(_typecheckingstub__794b97049be03a2ecb5f43ec19edfb849a336ebc8bdf5e742ea44302de0ead2c)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Virtual Machine Scale Set Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__999477397029103b191c80f86441576ec2628003f8d8caf1e462455857bf1fe6)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Virtual Machine Scale Sets.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Machine Scale Sets.'''
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
    def props(self) -> "VirtualMachineScaleSetProps":
        '''The input properties for this VMSS instance.'''
        return typing.cast("VirtualMachineScaleSetProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Virtual Machine Scale Set.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="sku")
    def sku(self) -> "VirtualMachineScaleSetSku":
        '''Get the SKU configuration.'''
        return typing.cast("VirtualMachineScaleSetSku", jsii.get(self, "sku"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))

    @builtins.property
    @jsii.member(jsii_name="uniqueId")
    def unique_id(self) -> builtins.str:
        '''Get the unique ID (unique identifier assigned by Azure).'''
        return typing.cast(builtins.str, jsii.get(self, "uniqueId"))

    @builtins.property
    @jsii.member(jsii_name="uniqueIdOutput")
    def unique_id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "uniqueIdOutput"))

    @builtins.property
    @jsii.member(jsii_name="capacity")
    def capacity(self) -> typing.Optional[jsii.Number]:
        '''Get the capacity (number of VMs).'''
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "capacity"))

    @builtins.property
    @jsii.member(jsii_name="orchestrationMode")
    def orchestration_mode(self) -> typing.Optional[builtins.str]:
        '''Get the orchestration mode.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "orchestrationMode"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetBody",
    jsii_struct_bases=[],
    name_mapping={
        "location": "location",
        "properties": "properties",
        "sku": "sku",
        "identity": "identity",
        "plan": "plan",
        "tags": "tags",
        "zones": "zones",
    },
)
class VirtualMachineScaleSetBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["VirtualMachineScaleSetBodyProperties", typing.Dict[builtins.str, typing.Any]],
        sku: typing.Union["VirtualMachineScaleSetSku", typing.Dict[builtins.str, typing.Any]],
        identity: typing.Optional[typing.Union[_VirtualMachineIdentity_dc7decb0, typing.Dict[builtins.str, typing.Any]]] = None,
        plan: typing.Optional[typing.Union[_VirtualMachinePlan_2ca6c6de, typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure VMSS API calls.

        :param location: 
        :param properties: 
        :param sku: 
        :param identity: 
        :param plan: 
        :param tags: 
        :param zones: 
        '''
        if isinstance(properties, dict):
            properties = VirtualMachineScaleSetBodyProperties(**properties)
        if isinstance(sku, dict):
            sku = VirtualMachineScaleSetSku(**sku)
        if isinstance(identity, dict):
            identity = _VirtualMachineIdentity_dc7decb0(**identity)
        if isinstance(plan, dict):
            plan = _VirtualMachinePlan_2ca6c6de(**plan)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a3596048fbeb8cda8933485ec91ec615ecdb18605b1335e9d1ddfb883876ccb)
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument plan", value=plan, expected_type=type_hints["plan"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument zones", value=zones, expected_type=type_hints["zones"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "location": location,
            "properties": properties,
            "sku": sku,
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
    def properties(self) -> "VirtualMachineScaleSetBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("VirtualMachineScaleSetBodyProperties", result)

    @builtins.property
    def sku(self) -> "VirtualMachineScaleSetSku":
        result = self._values.get("sku")
        assert result is not None, "Required property 'sku' is missing"
        return typing.cast("VirtualMachineScaleSetSku", result)

    @builtins.property
    def identity(self) -> typing.Optional[_VirtualMachineIdentity_dc7decb0]:
        result = self._values.get("identity")
        return typing.cast(typing.Optional[_VirtualMachineIdentity_dc7decb0], result)

    @builtins.property
    def plan(self) -> typing.Optional[_VirtualMachinePlan_2ca6c6de]:
        result = self._values.get("plan")
        return typing.cast(typing.Optional[_VirtualMachinePlan_2ca6c6de], result)

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
        return "VirtualMachineScaleSetBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "additional_capabilities": "additionalCapabilities",
        "automatic_repairs_policy": "automaticRepairsPolicy",
        "do_not_run_extensions_on_overprovisioned_v_ms": "doNotRunExtensionsOnOverprovisionedVMs",
        "host_group": "hostGroup",
        "orchestration_mode": "orchestrationMode",
        "overprovision": "overprovision",
        "platform_fault_domain_count": "platformFaultDomainCount",
        "proximity_placement_group": "proximityPlacementGroup",
        "scale_in_policy": "scaleInPolicy",
        "single_placement_group": "singlePlacementGroup",
        "upgrade_policy": "upgradePolicy",
        "virtual_machine_profile": "virtualMachineProfile",
        "zone_balance": "zoneBalance",
    },
)
class VirtualMachineScaleSetBodyProperties:
    def __init__(
        self,
        *,
        additional_capabilities: typing.Optional[typing.Union[AdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
        automatic_repairs_policy: typing.Optional[typing.Union[AutomaticRepairsPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
        do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
        host_group: typing.Optional[typing.Union[HostGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
        orchestration_mode: typing.Optional[builtins.str] = None,
        overprovision: typing.Optional[builtins.bool] = None,
        platform_fault_domain_count: typing.Optional[jsii.Number] = None,
        proximity_placement_group: typing.Optional[typing.Union[ProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
        scale_in_policy: typing.Optional[typing.Union["VirtualMachineScaleSetScaleInPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        single_placement_group: typing.Optional[builtins.bool] = None,
        upgrade_policy: typing.Optional[typing.Union["VirtualMachineScaleSetUpgradePolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        virtual_machine_profile: typing.Optional[typing.Union["VirtualMachineScaleSetVMProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        zone_balance: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Body properties for VMSS.

        :param additional_capabilities: 
        :param automatic_repairs_policy: 
        :param do_not_run_extensions_on_overprovisioned_v_ms: 
        :param host_group: 
        :param orchestration_mode: 
        :param overprovision: 
        :param platform_fault_domain_count: 
        :param proximity_placement_group: 
        :param scale_in_policy: 
        :param single_placement_group: 
        :param upgrade_policy: 
        :param virtual_machine_profile: 
        :param zone_balance: 
        '''
        if isinstance(additional_capabilities, dict):
            additional_capabilities = AdditionalCapabilities(**additional_capabilities)
        if isinstance(automatic_repairs_policy, dict):
            automatic_repairs_policy = AutomaticRepairsPolicy(**automatic_repairs_policy)
        if isinstance(host_group, dict):
            host_group = HostGroupReference(**host_group)
        if isinstance(proximity_placement_group, dict):
            proximity_placement_group = ProximityPlacementGroupReference(**proximity_placement_group)
        if isinstance(scale_in_policy, dict):
            scale_in_policy = VirtualMachineScaleSetScaleInPolicy(**scale_in_policy)
        if isinstance(upgrade_policy, dict):
            upgrade_policy = VirtualMachineScaleSetUpgradePolicy(**upgrade_policy)
        if isinstance(virtual_machine_profile, dict):
            virtual_machine_profile = VirtualMachineScaleSetVMProfile(**virtual_machine_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c26b336583be370dbecde9d33e4a634c3d8e3209a23b1a6e437c676adfacc377)
            check_type(argname="argument additional_capabilities", value=additional_capabilities, expected_type=type_hints["additional_capabilities"])
            check_type(argname="argument automatic_repairs_policy", value=automatic_repairs_policy, expected_type=type_hints["automatic_repairs_policy"])
            check_type(argname="argument do_not_run_extensions_on_overprovisioned_v_ms", value=do_not_run_extensions_on_overprovisioned_v_ms, expected_type=type_hints["do_not_run_extensions_on_overprovisioned_v_ms"])
            check_type(argname="argument host_group", value=host_group, expected_type=type_hints["host_group"])
            check_type(argname="argument orchestration_mode", value=orchestration_mode, expected_type=type_hints["orchestration_mode"])
            check_type(argname="argument overprovision", value=overprovision, expected_type=type_hints["overprovision"])
            check_type(argname="argument platform_fault_domain_count", value=platform_fault_domain_count, expected_type=type_hints["platform_fault_domain_count"])
            check_type(argname="argument proximity_placement_group", value=proximity_placement_group, expected_type=type_hints["proximity_placement_group"])
            check_type(argname="argument scale_in_policy", value=scale_in_policy, expected_type=type_hints["scale_in_policy"])
            check_type(argname="argument single_placement_group", value=single_placement_group, expected_type=type_hints["single_placement_group"])
            check_type(argname="argument upgrade_policy", value=upgrade_policy, expected_type=type_hints["upgrade_policy"])
            check_type(argname="argument virtual_machine_profile", value=virtual_machine_profile, expected_type=type_hints["virtual_machine_profile"])
            check_type(argname="argument zone_balance", value=zone_balance, expected_type=type_hints["zone_balance"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if additional_capabilities is not None:
            self._values["additional_capabilities"] = additional_capabilities
        if automatic_repairs_policy is not None:
            self._values["automatic_repairs_policy"] = automatic_repairs_policy
        if do_not_run_extensions_on_overprovisioned_v_ms is not None:
            self._values["do_not_run_extensions_on_overprovisioned_v_ms"] = do_not_run_extensions_on_overprovisioned_v_ms
        if host_group is not None:
            self._values["host_group"] = host_group
        if orchestration_mode is not None:
            self._values["orchestration_mode"] = orchestration_mode
        if overprovision is not None:
            self._values["overprovision"] = overprovision
        if platform_fault_domain_count is not None:
            self._values["platform_fault_domain_count"] = platform_fault_domain_count
        if proximity_placement_group is not None:
            self._values["proximity_placement_group"] = proximity_placement_group
        if scale_in_policy is not None:
            self._values["scale_in_policy"] = scale_in_policy
        if single_placement_group is not None:
            self._values["single_placement_group"] = single_placement_group
        if upgrade_policy is not None:
            self._values["upgrade_policy"] = upgrade_policy
        if virtual_machine_profile is not None:
            self._values["virtual_machine_profile"] = virtual_machine_profile
        if zone_balance is not None:
            self._values["zone_balance"] = zone_balance

    @builtins.property
    def additional_capabilities(self) -> typing.Optional[AdditionalCapabilities]:
        result = self._values.get("additional_capabilities")
        return typing.cast(typing.Optional[AdditionalCapabilities], result)

    @builtins.property
    def automatic_repairs_policy(self) -> typing.Optional[AutomaticRepairsPolicy]:
        result = self._values.get("automatic_repairs_policy")
        return typing.cast(typing.Optional[AutomaticRepairsPolicy], result)

    @builtins.property
    def do_not_run_extensions_on_overprovisioned_v_ms(
        self,
    ) -> typing.Optional[builtins.bool]:
        result = self._values.get("do_not_run_extensions_on_overprovisioned_v_ms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def host_group(self) -> typing.Optional[HostGroupReference]:
        result = self._values.get("host_group")
        return typing.cast(typing.Optional[HostGroupReference], result)

    @builtins.property
    def orchestration_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("orchestration_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def overprovision(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("overprovision")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def platform_fault_domain_count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("platform_fault_domain_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def proximity_placement_group(
        self,
    ) -> typing.Optional[ProximityPlacementGroupReference]:
        result = self._values.get("proximity_placement_group")
        return typing.cast(typing.Optional[ProximityPlacementGroupReference], result)

    @builtins.property
    def scale_in_policy(self) -> typing.Optional["VirtualMachineScaleSetScaleInPolicy"]:
        result = self._values.get("scale_in_policy")
        return typing.cast(typing.Optional["VirtualMachineScaleSetScaleInPolicy"], result)

    @builtins.property
    def single_placement_group(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("single_placement_group")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def upgrade_policy(self) -> typing.Optional["VirtualMachineScaleSetUpgradePolicy"]:
        result = self._values.get("upgrade_policy")
        return typing.cast(typing.Optional["VirtualMachineScaleSetUpgradePolicy"], result)

    @builtins.property
    def virtual_machine_profile(
        self,
    ) -> typing.Optional["VirtualMachineScaleSetVMProfile"]:
        result = self._values.get("virtual_machine_profile")
        return typing.cast(typing.Optional["VirtualMachineScaleSetVMProfile"], result)

    @builtins.property
    def zone_balance(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("zone_balance")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetNetworkProfile",
    jsii_struct_bases=[],
    name_mapping={
        "health_probe": "healthProbe",
        "network_api_version": "networkApiVersion",
        "network_interface_configurations": "networkInterfaceConfigurations",
    },
)
class VirtualMachineScaleSetNetworkProfile:
    def __init__(
        self,
        *,
        health_probe: typing.Optional[typing.Union[HealthProbeReference, typing.Dict[builtins.str, typing.Any]]] = None,
        network_api_version: typing.Optional[builtins.str] = None,
        network_interface_configurations: typing.Optional[typing.Sequence[typing.Union[NetworkInterfaceConfiguration, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Network profile for VMSS (different from VM).

        :param health_probe: 
        :param network_api_version: The API version to use for network interface configurations. This property is automatically set to the latest Network Interface API version when orchestrationMode is "Flexible" and networkInterfaceConfigurations are specified. You can explicitly provide a version if you need to pin to a specific API version. Default: Latest Network Interface API version (auto-resolved)
        :param network_interface_configurations: 
        '''
        if isinstance(health_probe, dict):
            health_probe = HealthProbeReference(**health_probe)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__35a65513e5ed657b7b4a5b1ac3d133c61bcba8bb4deeb7629dfd3781b019044b)
            check_type(argname="argument health_probe", value=health_probe, expected_type=type_hints["health_probe"])
            check_type(argname="argument network_api_version", value=network_api_version, expected_type=type_hints["network_api_version"])
            check_type(argname="argument network_interface_configurations", value=network_interface_configurations, expected_type=type_hints["network_interface_configurations"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if health_probe is not None:
            self._values["health_probe"] = health_probe
        if network_api_version is not None:
            self._values["network_api_version"] = network_api_version
        if network_interface_configurations is not None:
            self._values["network_interface_configurations"] = network_interface_configurations

    @builtins.property
    def health_probe(self) -> typing.Optional[HealthProbeReference]:
        result = self._values.get("health_probe")
        return typing.cast(typing.Optional[HealthProbeReference], result)

    @builtins.property
    def network_api_version(self) -> typing.Optional[builtins.str]:
        '''The API version to use for network interface configurations.

        This property is automatically set to the latest Network Interface API version
        when orchestrationMode is "Flexible" and networkInterfaceConfigurations are specified.

        You can explicitly provide a version if you need to pin to a specific API version.

        :default: Latest Network Interface API version (auto-resolved)

        Example::

            "2024-10-01"
        '''
        result = self._values.get("network_api_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def network_interface_configurations(
        self,
    ) -> typing.Optional[typing.List[NetworkInterfaceConfiguration]]:
        result = self._values.get("network_interface_configurations")
        return typing.cast(typing.Optional[typing.List[NetworkInterfaceConfiguration]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetNetworkProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetOSProfile",
    jsii_struct_bases=[],
    name_mapping={
        "admin_password": "adminPassword",
        "admin_username": "adminUsername",
        "allow_extension_operations": "allowExtensionOperations",
        "computer_name_prefix": "computerNamePrefix",
        "custom_data": "customData",
        "linux_configuration": "linuxConfiguration",
        "require_guest_provision_signal": "requireGuestProvisionSignal",
        "secrets": "secrets",
        "windows_configuration": "windowsConfiguration",
    },
)
class VirtualMachineScaleSetOSProfile:
    def __init__(
        self,
        *,
        admin_password: typing.Optional[builtins.str] = None,
        admin_username: typing.Optional[builtins.str] = None,
        allow_extension_operations: typing.Optional[builtins.bool] = None,
        computer_name_prefix: typing.Optional[builtins.str] = None,
        custom_data: typing.Optional[builtins.str] = None,
        linux_configuration: typing.Optional[typing.Union[_VirtualMachineLinuxConfiguration_5f791d4c, typing.Dict[builtins.str, typing.Any]]] = None,
        require_guest_provision_signal: typing.Optional[builtins.bool] = None,
        secrets: typing.Optional[typing.Sequence[typing.Any]] = None,
        windows_configuration: typing.Optional[typing.Union[_VirtualMachineWindowsConfiguration_31cdebe5, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''OS Profile for Virtual Machine Scale Set VMSS uses computerNamePrefix instead of computerName.

        :param admin_password: 
        :param admin_username: 
        :param allow_extension_operations: 
        :param computer_name_prefix: 
        :param custom_data: 
        :param linux_configuration: 
        :param require_guest_provision_signal: 
        :param secrets: 
        :param windows_configuration: 
        '''
        if isinstance(linux_configuration, dict):
            linux_configuration = _VirtualMachineLinuxConfiguration_5f791d4c(**linux_configuration)
        if isinstance(windows_configuration, dict):
            windows_configuration = _VirtualMachineWindowsConfiguration_31cdebe5(**windows_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4b1f7ad42a6f2ffcdacaa6eddad93e2b66975dfdd0e2811b11ceb48b6f145cf)
            check_type(argname="argument admin_password", value=admin_password, expected_type=type_hints["admin_password"])
            check_type(argname="argument admin_username", value=admin_username, expected_type=type_hints["admin_username"])
            check_type(argname="argument allow_extension_operations", value=allow_extension_operations, expected_type=type_hints["allow_extension_operations"])
            check_type(argname="argument computer_name_prefix", value=computer_name_prefix, expected_type=type_hints["computer_name_prefix"])
            check_type(argname="argument custom_data", value=custom_data, expected_type=type_hints["custom_data"])
            check_type(argname="argument linux_configuration", value=linux_configuration, expected_type=type_hints["linux_configuration"])
            check_type(argname="argument require_guest_provision_signal", value=require_guest_provision_signal, expected_type=type_hints["require_guest_provision_signal"])
            check_type(argname="argument secrets", value=secrets, expected_type=type_hints["secrets"])
            check_type(argname="argument windows_configuration", value=windows_configuration, expected_type=type_hints["windows_configuration"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if admin_password is not None:
            self._values["admin_password"] = admin_password
        if admin_username is not None:
            self._values["admin_username"] = admin_username
        if allow_extension_operations is not None:
            self._values["allow_extension_operations"] = allow_extension_operations
        if computer_name_prefix is not None:
            self._values["computer_name_prefix"] = computer_name_prefix
        if custom_data is not None:
            self._values["custom_data"] = custom_data
        if linux_configuration is not None:
            self._values["linux_configuration"] = linux_configuration
        if require_guest_provision_signal is not None:
            self._values["require_guest_provision_signal"] = require_guest_provision_signal
        if secrets is not None:
            self._values["secrets"] = secrets
        if windows_configuration is not None:
            self._values["windows_configuration"] = windows_configuration

    @builtins.property
    def admin_password(self) -> typing.Optional[builtins.str]:
        result = self._values.get("admin_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def admin_username(self) -> typing.Optional[builtins.str]:
        result = self._values.get("admin_username")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def allow_extension_operations(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("allow_extension_operations")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def computer_name_prefix(self) -> typing.Optional[builtins.str]:
        result = self._values.get("computer_name_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_data(self) -> typing.Optional[builtins.str]:
        result = self._values.get("custom_data")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def linux_configuration(
        self,
    ) -> typing.Optional[_VirtualMachineLinuxConfiguration_5f791d4c]:
        result = self._values.get("linux_configuration")
        return typing.cast(typing.Optional[_VirtualMachineLinuxConfiguration_5f791d4c], result)

    @builtins.property
    def require_guest_provision_signal(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("require_guest_provision_signal")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def secrets(self) -> typing.Optional[typing.List[typing.Any]]:
        result = self._values.get("secrets")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    @builtins.property
    def windows_configuration(
        self,
    ) -> typing.Optional[_VirtualMachineWindowsConfiguration_31cdebe5]:
        result = self._values.get("windows_configuration")
        return typing.cast(typing.Optional[_VirtualMachineWindowsConfiguration_31cdebe5], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetOSProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetProps",
    jsii_struct_bases=[],
    name_mapping={
        "location": "location",
        "name": "name",
        "sku": "sku",
        "additional_capabilities": "additionalCapabilities",
        "api_version": "apiVersion",
        "automatic_repairs_policy": "automaticRepairsPolicy",
        "do_not_run_extensions_on_overprovisioned_v_ms": "doNotRunExtensionsOnOverprovisionedVMs",
        "enable_migration_analysis": "enableMigrationAnalysis",
        "enable_transformation": "enableTransformation",
        "enable_validation": "enableValidation",
        "host_group": "hostGroup",
        "identity": "identity",
        "ignore_changes": "ignoreChanges",
        "monitoring": "monitoring",
        "orchestration_mode": "orchestrationMode",
        "overprovision": "overprovision",
        "plan": "plan",
        "platform_fault_domain_count": "platformFaultDomainCount",
        "proximity_placement_group": "proximityPlacementGroup",
        "resource_group_id": "resourceGroupId",
        "scale_in_policy": "scaleInPolicy",
        "single_placement_group": "singlePlacementGroup",
        "tags": "tags",
        "upgrade_policy": "upgradePolicy",
        "virtual_machine_profile": "virtualMachineProfile",
        "zone_balance": "zoneBalance",
        "zones": "zones",
    },
)
class VirtualMachineScaleSetProps:
    def __init__(
        self,
        *,
        location: builtins.str,
        name: builtins.str,
        sku: typing.Union["VirtualMachineScaleSetSku", typing.Dict[builtins.str, typing.Any]],
        additional_capabilities: typing.Optional[typing.Union[AdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
        api_version: typing.Optional[builtins.str] = None,
        automatic_repairs_policy: typing.Optional[typing.Union[AutomaticRepairsPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
        do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        host_group: typing.Optional[typing.Union[HostGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union[_VirtualMachineIdentity_dc7decb0, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        monitoring: typing.Any = None,
        orchestration_mode: typing.Optional[builtins.str] = None,
        overprovision: typing.Optional[builtins.bool] = None,
        plan: typing.Optional[typing.Union[_VirtualMachinePlan_2ca6c6de, typing.Dict[builtins.str, typing.Any]]] = None,
        platform_fault_domain_count: typing.Optional[jsii.Number] = None,
        proximity_placement_group: typing.Optional[typing.Union[ProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        scale_in_policy: typing.Optional[typing.Union["VirtualMachineScaleSetScaleInPolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        single_placement_group: typing.Optional[builtins.bool] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        upgrade_policy: typing.Optional[typing.Union["VirtualMachineScaleSetUpgradePolicy", typing.Dict[builtins.str, typing.Any]]] = None,
        virtual_machine_profile: typing.Optional[typing.Union["VirtualMachineScaleSetVMProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        zone_balance: typing.Optional[builtins.bool] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Virtual Machine Scale Set.

        :param location: 
        :param name: 
        :param sku: 
        :param additional_capabilities: 
        :param api_version: 
        :param automatic_repairs_policy: 
        :param do_not_run_extensions_on_overprovisioned_v_ms: 
        :param enable_migration_analysis: 
        :param enable_transformation: 
        :param enable_validation: 
        :param host_group: 
        :param identity: 
        :param ignore_changes: 
        :param monitoring: 
        :param orchestration_mode: 
        :param overprovision: 
        :param plan: 
        :param platform_fault_domain_count: 
        :param proximity_placement_group: 
        :param resource_group_id: 
        :param scale_in_policy: 
        :param single_placement_group: 
        :param tags: 
        :param upgrade_policy: 
        :param virtual_machine_profile: 
        :param zone_balance: 
        :param zones: 
        '''
        if isinstance(sku, dict):
            sku = VirtualMachineScaleSetSku(**sku)
        if isinstance(additional_capabilities, dict):
            additional_capabilities = AdditionalCapabilities(**additional_capabilities)
        if isinstance(automatic_repairs_policy, dict):
            automatic_repairs_policy = AutomaticRepairsPolicy(**automatic_repairs_policy)
        if isinstance(host_group, dict):
            host_group = HostGroupReference(**host_group)
        if isinstance(identity, dict):
            identity = _VirtualMachineIdentity_dc7decb0(**identity)
        if isinstance(plan, dict):
            plan = _VirtualMachinePlan_2ca6c6de(**plan)
        if isinstance(proximity_placement_group, dict):
            proximity_placement_group = ProximityPlacementGroupReference(**proximity_placement_group)
        if isinstance(scale_in_policy, dict):
            scale_in_policy = VirtualMachineScaleSetScaleInPolicy(**scale_in_policy)
        if isinstance(upgrade_policy, dict):
            upgrade_policy = VirtualMachineScaleSetUpgradePolicy(**upgrade_policy)
        if isinstance(virtual_machine_profile, dict):
            virtual_machine_profile = VirtualMachineScaleSetVMProfile(**virtual_machine_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1c470ee53055753c0e9736ac6f8c8cb7c5ac2ef5773c8ebdc75d41770733a9e2)
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument additional_capabilities", value=additional_capabilities, expected_type=type_hints["additional_capabilities"])
            check_type(argname="argument api_version", value=api_version, expected_type=type_hints["api_version"])
            check_type(argname="argument automatic_repairs_policy", value=automatic_repairs_policy, expected_type=type_hints["automatic_repairs_policy"])
            check_type(argname="argument do_not_run_extensions_on_overprovisioned_v_ms", value=do_not_run_extensions_on_overprovisioned_v_ms, expected_type=type_hints["do_not_run_extensions_on_overprovisioned_v_ms"])
            check_type(argname="argument enable_migration_analysis", value=enable_migration_analysis, expected_type=type_hints["enable_migration_analysis"])
            check_type(argname="argument enable_transformation", value=enable_transformation, expected_type=type_hints["enable_transformation"])
            check_type(argname="argument enable_validation", value=enable_validation, expected_type=type_hints["enable_validation"])
            check_type(argname="argument host_group", value=host_group, expected_type=type_hints["host_group"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument monitoring", value=monitoring, expected_type=type_hints["monitoring"])
            check_type(argname="argument orchestration_mode", value=orchestration_mode, expected_type=type_hints["orchestration_mode"])
            check_type(argname="argument overprovision", value=overprovision, expected_type=type_hints["overprovision"])
            check_type(argname="argument plan", value=plan, expected_type=type_hints["plan"])
            check_type(argname="argument platform_fault_domain_count", value=platform_fault_domain_count, expected_type=type_hints["platform_fault_domain_count"])
            check_type(argname="argument proximity_placement_group", value=proximity_placement_group, expected_type=type_hints["proximity_placement_group"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument scale_in_policy", value=scale_in_policy, expected_type=type_hints["scale_in_policy"])
            check_type(argname="argument single_placement_group", value=single_placement_group, expected_type=type_hints["single_placement_group"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument upgrade_policy", value=upgrade_policy, expected_type=type_hints["upgrade_policy"])
            check_type(argname="argument virtual_machine_profile", value=virtual_machine_profile, expected_type=type_hints["virtual_machine_profile"])
            check_type(argname="argument zone_balance", value=zone_balance, expected_type=type_hints["zone_balance"])
            check_type(argname="argument zones", value=zones, expected_type=type_hints["zones"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "location": location,
            "name": name,
            "sku": sku,
        }
        if additional_capabilities is not None:
            self._values["additional_capabilities"] = additional_capabilities
        if api_version is not None:
            self._values["api_version"] = api_version
        if automatic_repairs_policy is not None:
            self._values["automatic_repairs_policy"] = automatic_repairs_policy
        if do_not_run_extensions_on_overprovisioned_v_ms is not None:
            self._values["do_not_run_extensions_on_overprovisioned_v_ms"] = do_not_run_extensions_on_overprovisioned_v_ms
        if enable_migration_analysis is not None:
            self._values["enable_migration_analysis"] = enable_migration_analysis
        if enable_transformation is not None:
            self._values["enable_transformation"] = enable_transformation
        if enable_validation is not None:
            self._values["enable_validation"] = enable_validation
        if host_group is not None:
            self._values["host_group"] = host_group
        if identity is not None:
            self._values["identity"] = identity
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if monitoring is not None:
            self._values["monitoring"] = monitoring
        if orchestration_mode is not None:
            self._values["orchestration_mode"] = orchestration_mode
        if overprovision is not None:
            self._values["overprovision"] = overprovision
        if plan is not None:
            self._values["plan"] = plan
        if platform_fault_domain_count is not None:
            self._values["platform_fault_domain_count"] = platform_fault_domain_count
        if proximity_placement_group is not None:
            self._values["proximity_placement_group"] = proximity_placement_group
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if scale_in_policy is not None:
            self._values["scale_in_policy"] = scale_in_policy
        if single_placement_group is not None:
            self._values["single_placement_group"] = single_placement_group
        if tags is not None:
            self._values["tags"] = tags
        if upgrade_policy is not None:
            self._values["upgrade_policy"] = upgrade_policy
        if virtual_machine_profile is not None:
            self._values["virtual_machine_profile"] = virtual_machine_profile
        if zone_balance is not None:
            self._values["zone_balance"] = zone_balance
        if zones is not None:
            self._values["zones"] = zones

    @builtins.property
    def location(self) -> builtins.str:
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def sku(self) -> "VirtualMachineScaleSetSku":
        result = self._values.get("sku")
        assert result is not None, "Required property 'sku' is missing"
        return typing.cast("VirtualMachineScaleSetSku", result)

    @builtins.property
    def additional_capabilities(self) -> typing.Optional[AdditionalCapabilities]:
        result = self._values.get("additional_capabilities")
        return typing.cast(typing.Optional[AdditionalCapabilities], result)

    @builtins.property
    def api_version(self) -> typing.Optional[builtins.str]:
        result = self._values.get("api_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def automatic_repairs_policy(self) -> typing.Optional[AutomaticRepairsPolicy]:
        result = self._values.get("automatic_repairs_policy")
        return typing.cast(typing.Optional[AutomaticRepairsPolicy], result)

    @builtins.property
    def do_not_run_extensions_on_overprovisioned_v_ms(
        self,
    ) -> typing.Optional[builtins.bool]:
        result = self._values.get("do_not_run_extensions_on_overprovisioned_v_ms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_migration_analysis(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_migration_analysis")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_transformation(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_transformation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_validation(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_validation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def host_group(self) -> typing.Optional[HostGroupReference]:
        result = self._values.get("host_group")
        return typing.cast(typing.Optional[HostGroupReference], result)

    @builtins.property
    def identity(self) -> typing.Optional[_VirtualMachineIdentity_dc7decb0]:
        result = self._values.get("identity")
        return typing.cast(typing.Optional[_VirtualMachineIdentity_dc7decb0], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def monitoring(self) -> typing.Any:
        result = self._values.get("monitoring")
        return typing.cast(typing.Any, result)

    @builtins.property
    def orchestration_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("orchestration_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def overprovision(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("overprovision")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def plan(self) -> typing.Optional[_VirtualMachinePlan_2ca6c6de]:
        result = self._values.get("plan")
        return typing.cast(typing.Optional[_VirtualMachinePlan_2ca6c6de], result)

    @builtins.property
    def platform_fault_domain_count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("platform_fault_domain_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def proximity_placement_group(
        self,
    ) -> typing.Optional[ProximityPlacementGroupReference]:
        result = self._values.get("proximity_placement_group")
        return typing.cast(typing.Optional[ProximityPlacementGroupReference], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_in_policy(self) -> typing.Optional["VirtualMachineScaleSetScaleInPolicy"]:
        result = self._values.get("scale_in_policy")
        return typing.cast(typing.Optional["VirtualMachineScaleSetScaleInPolicy"], result)

    @builtins.property
    def single_placement_group(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("single_placement_group")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def upgrade_policy(self) -> typing.Optional["VirtualMachineScaleSetUpgradePolicy"]:
        result = self._values.get("upgrade_policy")
        return typing.cast(typing.Optional["VirtualMachineScaleSetUpgradePolicy"], result)

    @builtins.property
    def virtual_machine_profile(
        self,
    ) -> typing.Optional["VirtualMachineScaleSetVMProfile"]:
        result = self._values.get("virtual_machine_profile")
        return typing.cast(typing.Optional["VirtualMachineScaleSetVMProfile"], result)

    @builtins.property
    def zone_balance(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("zone_balance")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def zones(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("zones")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetScaleInPolicy",
    jsii_struct_bases=[],
    name_mapping={"force_deletion": "forceDeletion", "rules": "rules"},
)
class VirtualMachineScaleSetScaleInPolicy:
    def __init__(
        self,
        *,
        force_deletion: typing.Optional[builtins.bool] = None,
        rules: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Scale-in policy.

        :param force_deletion: 
        :param rules: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__51f7d8f843061624ef0f26bbdf836a097498cf8c00695ae8a5b7bbe320a56c69)
            check_type(argname="argument force_deletion", value=force_deletion, expected_type=type_hints["force_deletion"])
            check_type(argname="argument rules", value=rules, expected_type=type_hints["rules"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if force_deletion is not None:
            self._values["force_deletion"] = force_deletion
        if rules is not None:
            self._values["rules"] = rules

    @builtins.property
    def force_deletion(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("force_deletion")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def rules(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("rules")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetScaleInPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetScalingConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "do_not_run_extensions_on_overprovisioned_v_ms": "doNotRunExtensionsOnOverprovisionedVMs",
        "overprovision": "overprovision",
        "platform_fault_domain_count": "platformFaultDomainCount",
        "single_placement_group": "singlePlacementGroup",
        "zone_balance": "zoneBalance",
    },
)
class VirtualMachineScaleSetScalingConfiguration:
    def __init__(
        self,
        *,
        do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
        overprovision: typing.Optional[builtins.bool] = None,
        platform_fault_domain_count: typing.Optional[jsii.Number] = None,
        single_placement_group: typing.Optional[builtins.bool] = None,
        zone_balance: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Scaling configuration.

        :param do_not_run_extensions_on_overprovisioned_v_ms: 
        :param overprovision: 
        :param platform_fault_domain_count: 
        :param single_placement_group: 
        :param zone_balance: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e82e8cf9e3188859ea502f835cbc8fa08951d4e573fdf38709b883a3f57db16)
            check_type(argname="argument do_not_run_extensions_on_overprovisioned_v_ms", value=do_not_run_extensions_on_overprovisioned_v_ms, expected_type=type_hints["do_not_run_extensions_on_overprovisioned_v_ms"])
            check_type(argname="argument overprovision", value=overprovision, expected_type=type_hints["overprovision"])
            check_type(argname="argument platform_fault_domain_count", value=platform_fault_domain_count, expected_type=type_hints["platform_fault_domain_count"])
            check_type(argname="argument single_placement_group", value=single_placement_group, expected_type=type_hints["single_placement_group"])
            check_type(argname="argument zone_balance", value=zone_balance, expected_type=type_hints["zone_balance"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if do_not_run_extensions_on_overprovisioned_v_ms is not None:
            self._values["do_not_run_extensions_on_overprovisioned_v_ms"] = do_not_run_extensions_on_overprovisioned_v_ms
        if overprovision is not None:
            self._values["overprovision"] = overprovision
        if platform_fault_domain_count is not None:
            self._values["platform_fault_domain_count"] = platform_fault_domain_count
        if single_placement_group is not None:
            self._values["single_placement_group"] = single_placement_group
        if zone_balance is not None:
            self._values["zone_balance"] = zone_balance

    @builtins.property
    def do_not_run_extensions_on_overprovisioned_v_ms(
        self,
    ) -> typing.Optional[builtins.bool]:
        result = self._values.get("do_not_run_extensions_on_overprovisioned_v_ms")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def overprovision(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("overprovision")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def platform_fault_domain_count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("platform_fault_domain_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def single_placement_group(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("single_placement_group")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def zone_balance(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("zone_balance")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetScalingConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetSku",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "capacity": "capacity", "tier": "tier"},
)
class VirtualMachineScaleSetSku:
    def __init__(
        self,
        *,
        name: builtins.str,
        capacity: typing.Optional[jsii.Number] = None,
        tier: typing.Optional[builtins.str] = None,
    ) -> None:
        '''SKU for the Virtual Machine Scale Set.

        :param name: 
        :param capacity: 
        :param tier: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d3e3fa4e7def31802321b8625e603c2e28c9dbca49129900b99bef6f28440b3b)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument capacity", value=capacity, expected_type=type_hints["capacity"])
            check_type(argname="argument tier", value=tier, expected_type=type_hints["tier"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }
        if capacity is not None:
            self._values["capacity"] = capacity
        if tier is not None:
            self._values["tier"] = tier

    @builtins.property
    def name(self) -> builtins.str:
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def capacity(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("capacity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def tier(self) -> typing.Optional[builtins.str]:
        result = self._values.get("tier")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetSku(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetUpgradePolicy",
    jsii_struct_bases=[],
    name_mapping={
        "automatic_os_upgrade_policy": "automaticOSUpgradePolicy",
        "mode": "mode",
        "rolling_upgrade_policy": "rollingUpgradePolicy",
    },
)
class VirtualMachineScaleSetUpgradePolicy:
    def __init__(
        self,
        *,
        automatic_os_upgrade_policy: typing.Optional[typing.Union[AutomaticOSUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
        mode: typing.Optional[builtins.str] = None,
        rolling_upgrade_policy: typing.Optional[typing.Union[RollingUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Upgrade policy for the Virtual Machine Scale Set.

        :param automatic_os_upgrade_policy: 
        :param mode: 
        :param rolling_upgrade_policy: 
        '''
        if isinstance(automatic_os_upgrade_policy, dict):
            automatic_os_upgrade_policy = AutomaticOSUpgradePolicy(**automatic_os_upgrade_policy)
        if isinstance(rolling_upgrade_policy, dict):
            rolling_upgrade_policy = RollingUpgradePolicy(**rolling_upgrade_policy)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9ea838947a3766bffd8d64db61db1526995e577bfa2093a7dd61d92ab897e41a)
            check_type(argname="argument automatic_os_upgrade_policy", value=automatic_os_upgrade_policy, expected_type=type_hints["automatic_os_upgrade_policy"])
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument rolling_upgrade_policy", value=rolling_upgrade_policy, expected_type=type_hints["rolling_upgrade_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if automatic_os_upgrade_policy is not None:
            self._values["automatic_os_upgrade_policy"] = automatic_os_upgrade_policy
        if mode is not None:
            self._values["mode"] = mode
        if rolling_upgrade_policy is not None:
            self._values["rolling_upgrade_policy"] = rolling_upgrade_policy

    @builtins.property
    def automatic_os_upgrade_policy(self) -> typing.Optional[AutomaticOSUpgradePolicy]:
        result = self._values.get("automatic_os_upgrade_policy")
        return typing.cast(typing.Optional[AutomaticOSUpgradePolicy], result)

    @builtins.property
    def mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def rolling_upgrade_policy(self) -> typing.Optional[RollingUpgradePolicy]:
        result = self._values.get("rolling_upgrade_policy")
        return typing.cast(typing.Optional[RollingUpgradePolicy], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetUpgradePolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VirtualMachineScaleSetVMProfile",
    jsii_struct_bases=[],
    name_mapping={
        "billing_profile": "billingProfile",
        "diagnostics_profile": "diagnosticsProfile",
        "eviction_policy": "evictionPolicy",
        "extension_profile": "extensionProfile",
        "license_type": "licenseType",
        "network_profile": "networkProfile",
        "os_profile": "osProfile",
        "priority": "priority",
        "scheduled_events_profile": "scheduledEventsProfile",
        "security_profile": "securityProfile",
        "storage_profile": "storageProfile",
    },
)
class VirtualMachineScaleSetVMProfile:
    def __init__(
        self,
        *,
        billing_profile: typing.Optional[typing.Union[_VirtualMachineBillingProfile_b57d8936, typing.Dict[builtins.str, typing.Any]]] = None,
        diagnostics_profile: typing.Optional[typing.Union[_VirtualMachineDiagnosticsProfile_05cee027, typing.Dict[builtins.str, typing.Any]]] = None,
        eviction_policy: typing.Optional[builtins.str] = None,
        extension_profile: typing.Optional[typing.Union[ExtensionProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        license_type: typing.Optional[builtins.str] = None,
        network_profile: typing.Optional[typing.Union[VirtualMachineScaleSetNetworkProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        os_profile: typing.Optional[typing.Union[VirtualMachineScaleSetOSProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        priority: typing.Optional[builtins.str] = None,
        scheduled_events_profile: typing.Optional[typing.Union[ScheduledEventsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        security_profile: typing.Optional[typing.Union[_VirtualMachineSecurityProfile_59175751, typing.Dict[builtins.str, typing.Any]]] = None,
        storage_profile: typing.Optional[typing.Union[_VirtualMachineStorageProfile_793daa4a, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''VM profile for the Virtual Machine Scale Set Wraps VM configuration and reuses VM interfaces.

        :param billing_profile: 
        :param diagnostics_profile: 
        :param eviction_policy: 
        :param extension_profile: 
        :param license_type: 
        :param network_profile: 
        :param os_profile: 
        :param priority: 
        :param scheduled_events_profile: 
        :param security_profile: 
        :param storage_profile: 
        '''
        if isinstance(billing_profile, dict):
            billing_profile = _VirtualMachineBillingProfile_b57d8936(**billing_profile)
        if isinstance(diagnostics_profile, dict):
            diagnostics_profile = _VirtualMachineDiagnosticsProfile_05cee027(**diagnostics_profile)
        if isinstance(extension_profile, dict):
            extension_profile = ExtensionProfile(**extension_profile)
        if isinstance(network_profile, dict):
            network_profile = VirtualMachineScaleSetNetworkProfile(**network_profile)
        if isinstance(os_profile, dict):
            os_profile = VirtualMachineScaleSetOSProfile(**os_profile)
        if isinstance(scheduled_events_profile, dict):
            scheduled_events_profile = ScheduledEventsProfile(**scheduled_events_profile)
        if isinstance(security_profile, dict):
            security_profile = _VirtualMachineSecurityProfile_59175751(**security_profile)
        if isinstance(storage_profile, dict):
            storage_profile = _VirtualMachineStorageProfile_793daa4a(**storage_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7f893068ea77a5ca860dfb626f33250e262173c6bd6cb5f8818bc6016f3f7f1b)
            check_type(argname="argument billing_profile", value=billing_profile, expected_type=type_hints["billing_profile"])
            check_type(argname="argument diagnostics_profile", value=diagnostics_profile, expected_type=type_hints["diagnostics_profile"])
            check_type(argname="argument eviction_policy", value=eviction_policy, expected_type=type_hints["eviction_policy"])
            check_type(argname="argument extension_profile", value=extension_profile, expected_type=type_hints["extension_profile"])
            check_type(argname="argument license_type", value=license_type, expected_type=type_hints["license_type"])
            check_type(argname="argument network_profile", value=network_profile, expected_type=type_hints["network_profile"])
            check_type(argname="argument os_profile", value=os_profile, expected_type=type_hints["os_profile"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument scheduled_events_profile", value=scheduled_events_profile, expected_type=type_hints["scheduled_events_profile"])
            check_type(argname="argument security_profile", value=security_profile, expected_type=type_hints["security_profile"])
            check_type(argname="argument storage_profile", value=storage_profile, expected_type=type_hints["storage_profile"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if billing_profile is not None:
            self._values["billing_profile"] = billing_profile
        if diagnostics_profile is not None:
            self._values["diagnostics_profile"] = diagnostics_profile
        if eviction_policy is not None:
            self._values["eviction_policy"] = eviction_policy
        if extension_profile is not None:
            self._values["extension_profile"] = extension_profile
        if license_type is not None:
            self._values["license_type"] = license_type
        if network_profile is not None:
            self._values["network_profile"] = network_profile
        if os_profile is not None:
            self._values["os_profile"] = os_profile
        if priority is not None:
            self._values["priority"] = priority
        if scheduled_events_profile is not None:
            self._values["scheduled_events_profile"] = scheduled_events_profile
        if security_profile is not None:
            self._values["security_profile"] = security_profile
        if storage_profile is not None:
            self._values["storage_profile"] = storage_profile

    @builtins.property
    def billing_profile(
        self,
    ) -> typing.Optional[_VirtualMachineBillingProfile_b57d8936]:
        result = self._values.get("billing_profile")
        return typing.cast(typing.Optional[_VirtualMachineBillingProfile_b57d8936], result)

    @builtins.property
    def diagnostics_profile(
        self,
    ) -> typing.Optional[_VirtualMachineDiagnosticsProfile_05cee027]:
        result = self._values.get("diagnostics_profile")
        return typing.cast(typing.Optional[_VirtualMachineDiagnosticsProfile_05cee027], result)

    @builtins.property
    def eviction_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("eviction_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def extension_profile(self) -> typing.Optional[ExtensionProfile]:
        result = self._values.get("extension_profile")
        return typing.cast(typing.Optional[ExtensionProfile], result)

    @builtins.property
    def license_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("license_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def network_profile(self) -> typing.Optional[VirtualMachineScaleSetNetworkProfile]:
        result = self._values.get("network_profile")
        return typing.cast(typing.Optional[VirtualMachineScaleSetNetworkProfile], result)

    @builtins.property
    def os_profile(self) -> typing.Optional[VirtualMachineScaleSetOSProfile]:
        result = self._values.get("os_profile")
        return typing.cast(typing.Optional[VirtualMachineScaleSetOSProfile], result)

    @builtins.property
    def priority(self) -> typing.Optional[builtins.str]:
        result = self._values.get("priority")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scheduled_events_profile(self) -> typing.Optional[ScheduledEventsProfile]:
        result = self._values.get("scheduled_events_profile")
        return typing.cast(typing.Optional[ScheduledEventsProfile], result)

    @builtins.property
    def security_profile(
        self,
    ) -> typing.Optional[_VirtualMachineSecurityProfile_59175751]:
        result = self._values.get("security_profile")
        return typing.cast(typing.Optional[_VirtualMachineSecurityProfile_59175751], result)

    @builtins.property
    def storage_profile(
        self,
    ) -> typing.Optional[_VirtualMachineStorageProfile_793daa4a]:
        result = self._values.get("storage_profile")
        return typing.cast(typing.Optional[_VirtualMachineStorageProfile_793daa4a], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualMachineScaleSetVMProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_vmss.VmssMonitoringOptions",
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
class VmssMonitoringOptions:
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
        '''Configuration options for Virtual Machine Scale Set monitoring.

        This interface provides options for configuring monitoring alerts and diagnostic
        settings for VMSS resources. All properties are JSII-compliant for multi-language support.

        :param cpu_alert_severity: Severity level for CPU usage alerts. - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2
        :param cpu_threshold: CPU usage threshold percentage for triggering alerts. VMSS uses a lower default threshold (75%) compared to single VMs (80%) to allow headroom for scaling operations before reaching saturation. Default: 75
        :param disk_queue_alert_severity: Severity level for disk queue depth alerts. - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2
        :param disk_queue_threshold: Disk queue depth threshold for triggering alerts. High disk queue depth can indicate disk performance bottlenecks. Default: 32
        :param enable_cpu_alert: Enable or disable CPU usage alert. Default: true
        :param enable_deletion_alert: Enable or disable VMSS deletion activity log alert. Default: true
        :param enable_disk_queue_alert: Enable or disable disk queue depth alert. Default: true
        :param enable_memory_alert: Enable or disable memory usage alert. Default: true
        :param memory_alert_severity: Severity level for memory usage alerts. - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2
        :param memory_threshold: Available memory threshold in bytes for triggering alerts. When available memory drops below this threshold, an alert will be triggered. Default is 1GB (1073741824 bytes). Default: 1073741824
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d80f406ea069e39338acf5ad5428b48a674f6cc922730fc1ebd990de0e982294)
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
        '''Severity level for CPU usage alerts.

        - 0: Critical
        - 1: Error
        - 2: Warning
        - 3: Informational
        - 4: Verbose

        :default: 2
        '''
        result = self._values.get("cpu_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def cpu_threshold(self) -> typing.Optional[jsii.Number]:
        '''CPU usage threshold percentage for triggering alerts.

        VMSS uses a lower default threshold (75%) compared to single VMs (80%)
        to allow headroom for scaling operations before reaching saturation.

        :default: 75
        '''
        result = self._values.get("cpu_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def disk_queue_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for disk queue depth alerts.

        - 0: Critical
        - 1: Error
        - 2: Warning
        - 3: Informational
        - 4: Verbose

        :default: 2
        '''
        result = self._values.get("disk_queue_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def disk_queue_threshold(self) -> typing.Optional[jsii.Number]:
        '''Disk queue depth threshold for triggering alerts.

        High disk queue depth can indicate disk performance bottlenecks.

        :default: 32
        '''
        result = self._values.get("disk_queue_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def enable_cpu_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable CPU usage alert.

        :default: true
        '''
        result = self._values.get("enable_cpu_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_deletion_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable VMSS deletion activity log alert.

        :default: true
        '''
        result = self._values.get("enable_deletion_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_disk_queue_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable disk queue depth alert.

        :default: true
        '''
        result = self._values.get("enable_disk_queue_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_memory_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable memory usage alert.

        :default: true
        '''
        result = self._values.get("enable_memory_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def memory_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for memory usage alerts.

        - 0: Critical
        - 1: Error
        - 2: Warning
        - 3: Informational
        - 4: Verbose

        :default: 2
        '''
        result = self._values.get("memory_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def memory_threshold(self) -> typing.Optional[jsii.Number]:
        '''Available memory threshold in bytes for triggering alerts.

        When available memory drops below this threshold, an alert will be triggered.
        Default is 1GB (1073741824 bytes).

        :default: 1073741824
        '''
        result = self._values.get("memory_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VmssMonitoringOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AdditionalCapabilities",
    "AutomaticOSUpgradePolicy",
    "AutomaticRepairsPolicy",
    "ExtensionProfile",
    "HealthProbeReference",
    "HostGroupReference",
    "IPConfiguration",
    "IPConfigurationProperties",
    "IPConfigurationSubnet",
    "NetworkInterfaceConfiguration",
    "NetworkInterfaceConfigurationProperties",
    "NetworkSecurityGroupReference",
    "ProximityPlacementGroupReference",
    "PublicIPAddressConfiguration",
    "PublicIPAddressConfigurationProperties",
    "PublicIPDnsSettings",
    "ResourceReference",
    "RollingUpgradePolicy",
    "ScheduledEventsProfile",
    "TerminateNotificationProfile",
    "VMExtension",
    "VMExtensionProperties",
    "VirtualMachineScaleSet",
    "VirtualMachineScaleSetBody",
    "VirtualMachineScaleSetBodyProperties",
    "VirtualMachineScaleSetNetworkProfile",
    "VirtualMachineScaleSetOSProfile",
    "VirtualMachineScaleSetProps",
    "VirtualMachineScaleSetScaleInPolicy",
    "VirtualMachineScaleSetScalingConfiguration",
    "VirtualMachineScaleSetSku",
    "VirtualMachineScaleSetUpgradePolicy",
    "VirtualMachineScaleSetVMProfile",
    "VmssMonitoringOptions",
]

publication.publish()

def _typecheckingstub__f0088e60f6cc210be020fce08d77607368139fad3a793d3157cd2283c444476d(
    *,
    ultra_ssd_enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__62e07bb01afa007f00b0ecb6d0a7431aa925fac6767cc8d206361551144fcf91(
    *,
    disable_automatic_rollback: typing.Optional[builtins.bool] = None,
    enable_automatic_os_upgrade: typing.Optional[builtins.bool] = None,
    use_rolling_upgrade_policy: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b14d6a8fc1e86da57bf89ff582ba9ea0035ac64deac0d28ae8a59983ed9419a(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    grace_period: typing.Optional[builtins.str] = None,
    repair_action: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__051635f4e54cae7c4ccea9f47d12a2c4680a7f61a9836fbd633dc7d7aa077e2f(
    *,
    extensions: typing.Optional[typing.Sequence[typing.Union[VMExtension, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d7dae2afdd0c946d6ed2877367ab322d9149ab56798dd280538ca8c263f641a2(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__23c76e3e8ca30c8791a2bd83f634892e97a0563ac0c394e12bacdee7ac36449c(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2a623aca9e086117d581dee086d19b1e81ca257e74ed9ae69dff476645bc8cc3(
    *,
    name: builtins.str,
    properties: typing.Optional[typing.Union[NetworkInterfaceConfigurationProperties, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6c8728bc5e1e2d6411f5fe2492fa5a0e3fd8684f1afd3c181ae0a74e3ca0b504(
    *,
    ip_configurations: typing.Sequence[IPConfiguration],
    dns_settings: typing.Optional[typing.Union[_NetworkInterfaceDnsSettings_c9406208, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_accelerated_networking: typing.Optional[builtins.bool] = None,
    enable_ip_forwarding: typing.Optional[builtins.bool] = None,
    network_security_group: typing.Optional[typing.Union[NetworkSecurityGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    primary: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dd0a23e57cee8a498aa81813906b4f4b1ea7c684648d5bd872ce8ef71c9d6574(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9eaf8a7eb0c95d5841934337d1e2b31a09c8795b9ac74fafc7fc0b14de3bbb0d(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__11077ef88da161c6f6321c07480b6570cdb9fd7010244c6a56c71adfcab1deb8(
    *,
    name: builtins.str,
    properties: typing.Optional[typing.Union[PublicIPAddressConfigurationProperties, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__05760d45e9db0243881b99a335fcb383ef3bad2524d1012483f7d8192cb20576(
    *,
    dns_settings: typing.Optional[typing.Union[PublicIPDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13fbcf768d77cc18efed3fec7825d97d3af3997acf5ac011fa18b9d4f27b7a35(
    *,
    domain_name_label: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5784636f85d4a41eaa83f9bd150a53874161ae1b2ae8df94c4fc468d11df2c12(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__71b43cade14359f34e3069ca8c745262fb8f856c96ec51f74b13172a3a316b92(
    *,
    enable_cross_zone_upgrade: typing.Optional[builtins.bool] = None,
    max_batch_instance_percent: typing.Optional[jsii.Number] = None,
    max_unhealthy_instance_percent: typing.Optional[jsii.Number] = None,
    max_unhealthy_upgraded_instance_percent: typing.Optional[jsii.Number] = None,
    pause_time_between_batches: typing.Optional[builtins.str] = None,
    prioritize_unhealthy_instances: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__959dd21066c22148be0155dd74d2c85d1b44501e92218a482393c3f4fd442b3f(
    *,
    terminate_notification_profile: typing.Optional[typing.Union[TerminateNotificationProfile, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6efba26ec34394ce7b3cea1473ba77010839e891ad4d7e712b3b3389c8033098(
    *,
    enable: typing.Optional[builtins.bool] = None,
    not_before_timeout: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4a8a8ef54ba5745c8f4492cdf6496b727e4d03049c2e9192e380d0a9e9c81417(
    *,
    name: builtins.str,
    properties: typing.Optional[typing.Union[VMExtensionProperties, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e39d70b519d8b37ddffbec6c492e6a63e3c01e54b161c44a46db2cb85815b75f(
    *,
    publisher: builtins.str,
    type: builtins.str,
    type_handler_version: builtins.str,
    auto_upgrade_minor_version: typing.Optional[builtins.bool] = None,
    protected_settings: typing.Any = None,
    settings: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b6a3b588a8afae9a429644692a96c1a609f151d1c1e26aa9a1d49dc087da02d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    location: builtins.str,
    name: builtins.str,
    sku: typing.Union[VirtualMachineScaleSetSku, typing.Dict[builtins.str, typing.Any]],
    additional_capabilities: typing.Optional[typing.Union[AdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
    api_version: typing.Optional[builtins.str] = None,
    automatic_repairs_policy: typing.Optional[typing.Union[AutomaticRepairsPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
    enable_migration_analysis: typing.Optional[builtins.bool] = None,
    enable_transformation: typing.Optional[builtins.bool] = None,
    enable_validation: typing.Optional[builtins.bool] = None,
    host_group: typing.Optional[typing.Union[HostGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[_VirtualMachineIdentity_dc7decb0, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    monitoring: typing.Any = None,
    orchestration_mode: typing.Optional[builtins.str] = None,
    overprovision: typing.Optional[builtins.bool] = None,
    plan: typing.Optional[typing.Union[_VirtualMachinePlan_2ca6c6de, typing.Dict[builtins.str, typing.Any]]] = None,
    platform_fault_domain_count: typing.Optional[jsii.Number] = None,
    proximity_placement_group: typing.Optional[typing.Union[ProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    scale_in_policy: typing.Optional[typing.Union[VirtualMachineScaleSetScaleInPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    single_placement_group: typing.Optional[builtins.bool] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    upgrade_policy: typing.Optional[typing.Union[VirtualMachineScaleSetUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    virtual_machine_profile: typing.Optional[typing.Union[VirtualMachineScaleSetVMProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    zone_balance: typing.Optional[builtins.bool] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6917380daf4e70524dba89082ea35abaab15ac19a6730218756860a5d62c434c(
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

def _typecheckingstub__541c4a270054d2680122cb241f756d617a76fcbb9f41ec30413915ccab305805(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__794b97049be03a2ecb5f43ec19edfb849a336ebc8bdf5e742ea44302de0ead2c(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__999477397029103b191c80f86441576ec2628003f8d8caf1e462455857bf1fe6(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a3596048fbeb8cda8933485ec91ec615ecdb18605b1335e9d1ddfb883876ccb(
    *,
    location: builtins.str,
    properties: typing.Union[VirtualMachineScaleSetBodyProperties, typing.Dict[builtins.str, typing.Any]],
    sku: typing.Union[VirtualMachineScaleSetSku, typing.Dict[builtins.str, typing.Any]],
    identity: typing.Optional[typing.Union[_VirtualMachineIdentity_dc7decb0, typing.Dict[builtins.str, typing.Any]]] = None,
    plan: typing.Optional[typing.Union[_VirtualMachinePlan_2ca6c6de, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c26b336583be370dbecde9d33e4a634c3d8e3209a23b1a6e437c676adfacc377(
    *,
    additional_capabilities: typing.Optional[typing.Union[AdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
    automatic_repairs_policy: typing.Optional[typing.Union[AutomaticRepairsPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
    host_group: typing.Optional[typing.Union[HostGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    orchestration_mode: typing.Optional[builtins.str] = None,
    overprovision: typing.Optional[builtins.bool] = None,
    platform_fault_domain_count: typing.Optional[jsii.Number] = None,
    proximity_placement_group: typing.Optional[typing.Union[ProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    scale_in_policy: typing.Optional[typing.Union[VirtualMachineScaleSetScaleInPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    single_placement_group: typing.Optional[builtins.bool] = None,
    upgrade_policy: typing.Optional[typing.Union[VirtualMachineScaleSetUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    virtual_machine_profile: typing.Optional[typing.Union[VirtualMachineScaleSetVMProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    zone_balance: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__35a65513e5ed657b7b4a5b1ac3d133c61bcba8bb4deeb7629dfd3781b019044b(
    *,
    health_probe: typing.Optional[typing.Union[HealthProbeReference, typing.Dict[builtins.str, typing.Any]]] = None,
    network_api_version: typing.Optional[builtins.str] = None,
    network_interface_configurations: typing.Optional[typing.Sequence[typing.Union[NetworkInterfaceConfiguration, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e4b1f7ad42a6f2ffcdacaa6eddad93e2b66975dfdd0e2811b11ceb48b6f145cf(
    *,
    admin_password: typing.Optional[builtins.str] = None,
    admin_username: typing.Optional[builtins.str] = None,
    allow_extension_operations: typing.Optional[builtins.bool] = None,
    computer_name_prefix: typing.Optional[builtins.str] = None,
    custom_data: typing.Optional[builtins.str] = None,
    linux_configuration: typing.Optional[typing.Union[_VirtualMachineLinuxConfiguration_5f791d4c, typing.Dict[builtins.str, typing.Any]]] = None,
    require_guest_provision_signal: typing.Optional[builtins.bool] = None,
    secrets: typing.Optional[typing.Sequence[typing.Any]] = None,
    windows_configuration: typing.Optional[typing.Union[_VirtualMachineWindowsConfiguration_31cdebe5, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1c470ee53055753c0e9736ac6f8c8cb7c5ac2ef5773c8ebdc75d41770733a9e2(
    *,
    location: builtins.str,
    name: builtins.str,
    sku: typing.Union[VirtualMachineScaleSetSku, typing.Dict[builtins.str, typing.Any]],
    additional_capabilities: typing.Optional[typing.Union[AdditionalCapabilities, typing.Dict[builtins.str, typing.Any]]] = None,
    api_version: typing.Optional[builtins.str] = None,
    automatic_repairs_policy: typing.Optional[typing.Union[AutomaticRepairsPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
    enable_migration_analysis: typing.Optional[builtins.bool] = None,
    enable_transformation: typing.Optional[builtins.bool] = None,
    enable_validation: typing.Optional[builtins.bool] = None,
    host_group: typing.Optional[typing.Union[HostGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[_VirtualMachineIdentity_dc7decb0, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    monitoring: typing.Any = None,
    orchestration_mode: typing.Optional[builtins.str] = None,
    overprovision: typing.Optional[builtins.bool] = None,
    plan: typing.Optional[typing.Union[_VirtualMachinePlan_2ca6c6de, typing.Dict[builtins.str, typing.Any]]] = None,
    platform_fault_domain_count: typing.Optional[jsii.Number] = None,
    proximity_placement_group: typing.Optional[typing.Union[ProximityPlacementGroupReference, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    scale_in_policy: typing.Optional[typing.Union[VirtualMachineScaleSetScaleInPolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    single_placement_group: typing.Optional[builtins.bool] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    upgrade_policy: typing.Optional[typing.Union[VirtualMachineScaleSetUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    virtual_machine_profile: typing.Optional[typing.Union[VirtualMachineScaleSetVMProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    zone_balance: typing.Optional[builtins.bool] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__51f7d8f843061624ef0f26bbdf836a097498cf8c00695ae8a5b7bbe320a56c69(
    *,
    force_deletion: typing.Optional[builtins.bool] = None,
    rules: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8e82e8cf9e3188859ea502f835cbc8fa08951d4e573fdf38709b883a3f57db16(
    *,
    do_not_run_extensions_on_overprovisioned_v_ms: typing.Optional[builtins.bool] = None,
    overprovision: typing.Optional[builtins.bool] = None,
    platform_fault_domain_count: typing.Optional[jsii.Number] = None,
    single_placement_group: typing.Optional[builtins.bool] = None,
    zone_balance: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d3e3fa4e7def31802321b8625e603c2e28c9dbca49129900b99bef6f28440b3b(
    *,
    name: builtins.str,
    capacity: typing.Optional[jsii.Number] = None,
    tier: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9ea838947a3766bffd8d64db61db1526995e577bfa2093a7dd61d92ab897e41a(
    *,
    automatic_os_upgrade_policy: typing.Optional[typing.Union[AutomaticOSUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
    mode: typing.Optional[builtins.str] = None,
    rolling_upgrade_policy: typing.Optional[typing.Union[RollingUpgradePolicy, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7f893068ea77a5ca860dfb626f33250e262173c6bd6cb5f8818bc6016f3f7f1b(
    *,
    billing_profile: typing.Optional[typing.Union[_VirtualMachineBillingProfile_b57d8936, typing.Dict[builtins.str, typing.Any]]] = None,
    diagnostics_profile: typing.Optional[typing.Union[_VirtualMachineDiagnosticsProfile_05cee027, typing.Dict[builtins.str, typing.Any]]] = None,
    eviction_policy: typing.Optional[builtins.str] = None,
    extension_profile: typing.Optional[typing.Union[ExtensionProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    license_type: typing.Optional[builtins.str] = None,
    network_profile: typing.Optional[typing.Union[VirtualMachineScaleSetNetworkProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    os_profile: typing.Optional[typing.Union[VirtualMachineScaleSetOSProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    priority: typing.Optional[builtins.str] = None,
    scheduled_events_profile: typing.Optional[typing.Union[ScheduledEventsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    security_profile: typing.Optional[typing.Union[_VirtualMachineSecurityProfile_59175751, typing.Dict[builtins.str, typing.Any]]] = None,
    storage_profile: typing.Optional[typing.Union[_VirtualMachineStorageProfile_793daa4a, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d80f406ea069e39338acf5ad5428b48a674f6cc922730fc1ebd990de0e982294(
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

for cls in [IPConfiguration, IPConfigurationProperties, IPConfigurationSubnet]:
    typing.cast(typing.Any, cls).__protocol_attrs__ = typing.cast(typing.Any, cls).__protocol_attrs__ - set(['__jsii_proxy_class__', '__jsii_type__'])
