r'''
# Azure Network Interface Construct

This module provides a unified TypeScript implementation for Azure Network Interfaces using the AzapiResource framework. It automatically handles version management, schema validation, and property transformation across all supported API versions.

## Supported API Versions

* **2024-07-01** (Active)
* **2024-10-01** (Active)
* **2025-01-01** (Active, Latest - Default)

The construct automatically uses the latest version when no explicit version is specified, while maintaining full backward compatibility with all supported versions.

## Features

* ✅ **Automatic Version Resolution** - Uses the latest API version by default
* ✅ **Explicit Version Pinning** - Lock to specific API versions for stability
* ✅ **Schema-Driven Validation** - Validates properties against Azure REST API specifications
* ✅ **Type Safety** - Full TypeScript support with comprehensive type definitions
* ✅ **IP Configuration Management** - Support for single or multiple IP configurations
* ✅ **Network Security Group Integration** - Optional NSG association
* ✅ **Public IP Support** - Attach public IPs to NICs
* ✅ **Accelerated Networking** - Enable SR-IOV for high-performance scenarios
* ✅ **IP Forwarding** - Support for Network Virtual Appliances (NVAs)
* ✅ **Custom DNS Settings** - Configure DNS servers and internal DNS labels
* ✅ **JSII Compliance** - Multi-language support (TypeScript, Python, Java, .NET)

## Installation

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Basic Usage

### Simple Network Interface with Dynamic IP

```python
import { NetworkInterface } from "@microsoft/terraform-cdk-constructs";

const nic = new NetworkInterface(this, "basic-nic", {
  name: "my-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
});
```

### Network Interface with Static Private IP

```python
const nic = new NetworkInterface(this, "static-nic", {
  name: "my-static-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Static",
    privateIPAddress: "10.0.1.4",
    primary: true,
  }],
});
```

### Network Interface with Public IP

```python
const nic = new NetworkInterface(this, "public-nic", {
  name: "my-public-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    publicIPAddress: { id: publicIp.id },
    primary: true,
  }],
});
```

### Network Interface with Network Security Group

```python
const nic = new NetworkInterface(this, "secured-nic", {
  name: "my-secured-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
  networkSecurityGroup: { id: nsg.id },
});
```

### Network Interface with Accelerated Networking

```python
const nic = new NetworkInterface(this, "accelerated-nic", {
  name: "my-accelerated-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
  enableAcceleratedNetworking: true, // Requires supported VM size
});
```

### Network Virtual Appliance NIC with IP Forwarding

```python
const nvaNic = new NetworkInterface(this, "nva-nic", {
  name: "my-nva-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Static",
    privateIPAddress: "10.0.1.10",
    primary: true,
  }],
  enableIPForwarding: true, // Allow forwarding traffic
  enableAcceleratedNetworking: true,
  tags: {
    role: "network-virtual-appliance",
  },
});
```

### Network Interface with Multiple IP Configurations

```python
const multiIpNic = new NetworkInterface(this, "multi-ip-nic", {
  name: "my-multi-ip-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [
    {
      name: "ipconfig1",
      subnet: { id: subnet.id },
      privateIPAllocationMethod: "Dynamic",
      primary: true, // Must have exactly one primary
    },
    {
      name: "ipconfig2",
      subnet: { id: subnet.id },
      privateIPAllocationMethod: "Static",
      privateIPAddress: "10.0.1.5",
      primary: false,
    },
    {
      name: "ipconfig3",
      subnet: { id: subnet.id },
      privateIPAllocationMethod: "Static",
      privateIPAddress: "10.0.1.6",
      primary: false,
    },
  ],
});
```

### Network Interface with Custom DNS Settings

```python
const dnsNic = new NetworkInterface(this, "dns-nic", {
  name: "my-dns-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
  dnsSettings: {
    dnsServers: ["10.0.0.4", "10.0.0.5"],
    internalDnsNameLabel: "myvm",
  },
});
```

## Version Pinning

### Explicit API Version

```python
const nic = new NetworkInterface(this, "versioned-nic", {
  name: "my-versioned-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-07-01", // Pin to specific version
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
});
```

## Complete Networking Stack Example

```python
import { App, TerraformStack } from "cdktf";
import {
  ResourceGroup,
  VirtualNetwork,
  Subnet,
  PublicIPAddress,
  NetworkSecurityGroup,
  NetworkInterface,
} from "@microsoft/terraform-cdk-constructs";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/lib/azapi";

class NetworkingStack extends TerraformStack {
  constructor(scope: App, id: string) {
    super(scope, id);

    // Configure provider
    new AzapiProvider(this, "azapi", {});

    // Create resource group
    const rg = new ResourceGroup(this, "rg", {
      name: "my-networking-rg",
      location: "eastus",
    });

    // Create virtual network
    const vnet = new VirtualNetwork(this, "vnet", {
      name: "my-vnet",
      location: rg.props.location!,
      resourceGroupId: rg.id,
      addressSpace: {
        addressPrefixes: ["10.0.0.0/16"],
      },
    });

    // Create subnet
    const subnet = new Subnet(this, "subnet", {
      name: "my-subnet",
      resourceGroupName: rg.props.name!,
      virtualNetworkName: vnet.props.name!,
      addressPrefix: "10.0.1.0/24",
    });

    // Create public IP
    const publicIp = new PublicIPAddress(this, "pip", {
      name: "my-public-ip",
      location: rg.props.location!,
      resourceGroupId: rg.id,
      sku: { name: "Standard" },
      publicIPAllocationMethod: "Static",
    });

    // Create network security group
    const nsg = new NetworkSecurityGroup(this, "nsg", {
      name: "my-nsg",
      location: rg.props.location!,
      resourceGroupId: rg.id,
      securityRules: [
        {
          name: "allow-ssh",
          properties: {
            protocol: "Tcp",
            sourcePortRange: "*",
            destinationPortRange: "22",
            sourceAddressPrefix: "*",
            destinationAddressPrefix: "*",
            access: "Allow",
            priority: 100,
            direction: "Inbound",
          },
        },
      ],
    });

    // Create network interface tying everything together
    const nic = new NetworkInterface(this, "nic", {
      name: "my-vm-nic",
      location: rg.props.location!,
      resourceGroupId: rg.id,
      ipConfigurations: [{
        name: "ipconfig1",
        subnet: { id: subnet.id },
        privateIPAllocationMethod: "Static",
        privateIPAddress: "10.0.1.4",
        publicIPAddress: { id: publicIp.id },
        primary: true,
      }],
      networkSecurityGroup: { id: nsg.id },
      enableAcceleratedNetworking: true,
      tags: {
        environment: "production",
        role: "web-server",
      },
    });

    // Access NIC properties
    console.log(`NIC ID: ${nic.id}`);
    console.log(`Private IP: ${nic.privateIPAddress}`);
  }
}

const app = new App();
new NetworkingStack(app, "networking-stack");
app.synth();
```

## Properties

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `location` | `string` | Azure region where the NIC will be created |
| `ipConfigurations` | `NetworkInterfaceIPConfiguration[]` | IP configuration(s) for the NIC (at least one required) |

### Optional Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | `string` | Construct ID | Name of the network interface |
| `apiVersion` | `string` | `"2025-01-01"` | Azure API version to use |
| `networkSecurityGroup` | `{ id: string }` | - | NSG to associate with the NIC |
| `enableAcceleratedNetworking` | `boolean` | `false` | Enable SR-IOV for high performance |
| `enableIPForwarding` | `boolean` | `false` | Enable IP forwarding (for NVAs) |
| `dnsSettings` | `NetworkInterfaceDnsSettings` | - | Custom DNS configuration |
| `tags` | `{ [key: string]: string }` | `{}` | Resource tags |
| `resourceGroupId` | `string` | - | Resource group ID |
| `ignoreChanges` | `string[]` | - | Properties to ignore during updates |

### IP Configuration Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | ✅ | Name of the IP configuration |
| `subnet` | `{ id: string }` | ✅ | Subnet reference |
| `privateIPAllocationMethod` | `"Dynamic" \| "Static"` | - | Private IP allocation method (default: Dynamic) |
| `privateIPAddress` | `string` | - | Static private IP address (required if method is Static) |
| `publicIPAddress` | `{ id: string }` | - | Public IP reference |
| `primary` | `boolean` | - | Whether this is the primary IP configuration |

### DNS Settings Properties

| Property | Type | Description |
|----------|------|-------------|
| `dnsServers` | `string[]` | Custom DNS server IP addresses |
| `internalDnsNameLabel` | `string` | Internal DNS name label |

## Output Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | The resource ID of the network interface |
| `privateIPAddress` | `string` | The primary private IP address |
| `idOutput` | `TerraformOutput` | Terraform output for the NIC ID |
| `nameOutput` | `TerraformOutput` | Terraform output for the NIC name |
| `locationOutput` | `TerraformOutput` | Terraform output for the NIC location |
| `privateIPAddressOutput` | `TerraformOutput` | Terraform output for the private IP |
| `tagsOutput` | `TerraformOutput` | Terraform output for tags |

## Methods

### `addTag(key: string, value: string): void`

Add a tag to the network interface.

```python
nic.addTag("environment", "production");
```

### `removeTag(key: string): void`

Remove a tag from the network interface.

```python
nic.removeTag("temporary");
```

## Dependencies

Network Interfaces depend on:

* **Subnet** (required) - The subnet to attach the NIC to
* **Public IP Address** (optional) - For public connectivity
* **Network Security Group** (optional) - For traffic filtering

## Important Notes

1. **IP Configuration Requirements**:

   * At least one IP configuration is required
   * Exactly one IP configuration must be marked as `primary: true`
2. **Accelerated Networking**:

   * Requires a supported VM size
   * Cannot be enabled on all VM SKUs
   * Check Azure documentation for compatible VM sizes
3. **IP Forwarding**:

   * Required for Network Virtual Appliances (NVAs)
   * Allows the NIC to forward traffic not destined for its IP address
4. **Static IP Addresses**:

   * Must be within the subnet's address range
   * Should not conflict with other allocated IPs
5. **Public IP Association**:

   * Public IP must use Standard SKU if NIC uses accelerated networking
   * Public IP must be in the same location as the NIC

## Testing

### Unit Tests

```bash
npm test -- network-interface.spec.ts
```

### Integration Tests

```bash
npm run integration:nostream -- network-interface.integ.ts
```

## Migration from Version-Specific Classes

If you were using version-specific Network Interface classes, migration is straightforward:

```python
// Old approach (version-specific)
import { NetworkInterface20240701 } from "...";
const nic = new NetworkInterface20240701(this, "nic", { ... });

// New approach (unified)
import { NetworkInterface } from "...";
const nic = new NetworkInterface(this, "nic", {
  apiVersion: "2024-07-01", // Optional: pin to specific version
  ...
});
```

## Integration with Other Services

### Using with Virtual Machines

Network Interfaces created with this module can be referenced by Virtual Machines:

```python
import { NetworkInterface } from "@microsoft/terraform-cdk-constructs";
import { VirtualMachine } from "@microsoft/terraform-cdk-constructs";

// Create the network interface
const nic = new NetworkInterface(this, "vm-nic", {
  name: "my-vm-nic",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  ipConfigurations: [{
    name: "ipconfig1",
    subnet: { id: subnet.id },
    privateIPAllocationMethod: "Dynamic",
    primary: true,
  }],
});

// Reference the NIC in the VM
const vm = new VirtualMachine(this, "vm", {
  name: "my-vm",
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
    computerName: "myvm",
    adminUsername: "azureuser",
    linuxConfiguration: {
      disablePasswordAuthentication: true,
      ssh: {
        publicKeys: [{
          path: "/home/azureuser/.ssh/authorized_keys",
          keyData: "ssh-rsa AAAA...",
        }],
      },
    },
  },
  networkProfile: {
    networkInterfaces: [{
      id: nic.id, // Reference the NIC by ID
    }],
  },
});
```

### Using with Virtual Machine Scale Sets

For VMSS, network interfaces are defined as **templates** that are applied to each VM instance:

```python
import { VirtualMachineScaleSet } from "@microsoft/terraform-cdk-constructs";
import type { NetworkInterfaceDnsSettings } from "@microsoft/terraform-cdk-constructs";

const vmss = new VirtualMachineScaleSet(this, "vmss", {
  name: "my-vmss",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard_D2s_v3",
    capacity: 3,
  },
  orchestrationMode: "Uniform",
  virtualMachineProfile: {
    storageProfile: {
      // ... storage configuration
    },
    osProfile: {
      // ... OS configuration
    },
    networkProfile: {
      // Network interface configuration template
      networkInterfaceConfigurations: [{
        name: "nic-config",
        properties: {
          primary: true,
          enableAcceleratedNetworking: true,
          ipConfigurations: [{
            name: "ipconfig1",
            properties: {
              subnet: { id: subnet.id },
            },
          }],
          // Shared DNS settings type from NetworkInterface module
          dnsSettings: {
            dnsServers: ["10.0.0.4", "10.0.0.5"],
          } as NetworkInterfaceDnsSettings,
        },
      }],
    },
  },
});
```

**Key Differences**:

* **VMs**: Reference pre-created NICs by ID
* **VMSS**: Use NIC templates that create NICs for each VM instance
* **Shared Types**: VMSS imports `NetworkInterfaceDnsSettings` from this module for consistency

## Related Constructs

* [`VirtualNetwork`](../azure-virtualnetwork/README.md) - Azure Virtual Network
* [`Subnet`](../azure-subnet/README.md) - Virtual Network Subnet
* [`PublicIPAddress`](../azure-publicipaddress/README.md) - Public IP Address
* [`NetworkSecurityGroup`](../azure-networksecuritygroup/README.md) - Network Security Group
* [`ResourceGroup`](../azure-resourcegroup/README.md) - Azure Resource Group
* [`VirtualMachine`](../azure-virtualmachine/README.md) - Azure Virtual Machine (references NICs)
* [`VirtualMachineScaleSet`](../azure-vmss/README.md) - Azure VMSS (uses NIC templates)

## Additional Resources

* [Azure Network Interface Documentation](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-network-interface)
* [Azure REST API - Network Interfaces](https://learn.microsoft.com/en-us/rest/api/virtualnetwork/network-interfaces)
* [Accelerated Networking](https://learn.microsoft.com/en-us/azure/virtual-network/accelerated-networking-overview)
* [IP Forwarding](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-networks-udr-overview#ip-forwarding)

## License

This project is licensed under the MIT License.
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


class NetworkInterface(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterface",
):
    '''Unified Azure Network Interface implementation.

    This class provides a single, version-aware implementation that replaces all
    version-specific Network Interface classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Example::

        // Usage with explicit version pinning:
        const nic = new NetworkInterface(this, "nic", {
          name: "mynic",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          ipConfigurations: [{
            name: "ipconfig1",
            subnet: { id: subnet.id },
            privateIPAllocationMethod: "Dynamic",
            primary: true
          }],
          apiVersion: "2024-07-01",
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        ip_configurations: typing.Sequence[typing.Union["NetworkInterfaceIPConfiguration", typing.Dict[builtins.str, typing.Any]]],
        dns_settings: typing.Optional[typing.Union["NetworkInterfaceDnsSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        enable_accelerated_networking: typing.Optional[builtins.bool] = None,
        enable_ip_forwarding: typing.Optional[builtins.bool] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        network_security_group: typing.Optional[typing.Union["NetworkInterfaceNSGReference", typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Network Interface using the VersionedAzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param ip_configurations: IP configurations for the network interface At least one IP configuration is required One IP configuration must be marked as primary.
        :param dns_settings: DNS settings configuration Optional - configures DNS servers for the NIC.
        :param enable_accelerated_networking: Enable accelerated networking for high-performance scenarios Requires supported VM size. Default: false
        :param enable_ip_forwarding: Enable IP forwarding for network virtual appliances Allows NIC to forward traffic not destined for its IP. Default: false
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param network_security_group: Network Security Group reference with id property Optional - associates an NSG with this NIC.
        :param resource_group_id: Resource group ID where the network interface will be created.
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
            type_hints = typing.get_type_hints(_typecheckingstub__3b8db2e4b7e8bf51b1dceda2a4347eed8051b369bf1312f334f8355127d11dd7)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = NetworkInterfaceProps(
            ip_configurations=ip_configurations,
            dns_settings=dns_settings,
            enable_accelerated_networking=enable_accelerated_networking,
            enable_ip_forwarding=enable_ip_forwarding,
            ignore_changes=ignore_changes,
            network_security_group=network_security_group,
            resource_group_id=resource_group_id,
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

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Add a tag to the Network Interface.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a249985b536f02f45fff53454fbd7aedbe96f8cc37b238fe4b1749d01b6b40e8)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "addTag", [key, value]))

    @jsii.member(jsii_name="apiSchema")
    def _api_schema(self) -> _ApiSchema_5ce0490e:
        '''Gets the API schema for the resolved version.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0543d03565d766c24d70f7b22e4858a625930528ed7577592f650efc7b9705f4)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Network Interface.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e30e15da9919f000205fe1766e521cbc479bcdcdc720bb324611b6972499e1e3)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Network Interfaces.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Network Interfaces.'''
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
    @jsii.member(jsii_name="privateIPAddress")
    def private_ip_address(self) -> builtins.str:
        '''Get the private IP address of the primary IP configuration Note: This may not be available until after the resource is created The actual IP address location in Azure API response varies by API version.'''
        return typing.cast(builtins.str, jsii.get(self, "privateIPAddress"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "NetworkInterfaceProps":
        return typing.cast("NetworkInterfaceProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class NetworkInterfaceBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["NetworkInterfaceBodyProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Network Interface API calls.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = NetworkInterfaceBodyProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3dec53505a76fcad334043345e7158ce42cd19d15e8e127704c142a85d4f4dd0)
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "location": location,
            "properties": properties,
        }
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def location(self) -> builtins.str:
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> "NetworkInterfaceBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("NetworkInterfaceBodyProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "ip_configurations": "ipConfigurations",
        "dns_settings": "dnsSettings",
        "enable_accelerated_networking": "enableAcceleratedNetworking",
        "enable_ip_forwarding": "enableIPForwarding",
        "network_security_group": "networkSecurityGroup",
    },
)
class NetworkInterfaceBodyProperties:
    def __init__(
        self,
        *,
        ip_configurations: typing.Sequence[typing.Union["NetworkInterfaceIPConfiguration", typing.Dict[builtins.str, typing.Any]]],
        dns_settings: typing.Optional[typing.Union["NetworkInterfaceDnsSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        enable_accelerated_networking: typing.Optional[builtins.bool] = None,
        enable_ip_forwarding: typing.Optional[builtins.bool] = None,
        network_security_group: typing.Optional[typing.Union["NetworkInterfaceNSGReference", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Network Interface properties for the request body.

        :param ip_configurations: 
        :param dns_settings: 
        :param enable_accelerated_networking: 
        :param enable_ip_forwarding: 
        :param network_security_group: 
        '''
        if isinstance(dns_settings, dict):
            dns_settings = NetworkInterfaceDnsSettings(**dns_settings)
        if isinstance(network_security_group, dict):
            network_security_group = NetworkInterfaceNSGReference(**network_security_group)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b14b418c98a6e7f5e87613b2b98f36d475ce1ea2a7916ab302d893bd941d6ebb)
            check_type(argname="argument ip_configurations", value=ip_configurations, expected_type=type_hints["ip_configurations"])
            check_type(argname="argument dns_settings", value=dns_settings, expected_type=type_hints["dns_settings"])
            check_type(argname="argument enable_accelerated_networking", value=enable_accelerated_networking, expected_type=type_hints["enable_accelerated_networking"])
            check_type(argname="argument enable_ip_forwarding", value=enable_ip_forwarding, expected_type=type_hints["enable_ip_forwarding"])
            check_type(argname="argument network_security_group", value=network_security_group, expected_type=type_hints["network_security_group"])
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

    @builtins.property
    def ip_configurations(self) -> typing.List["NetworkInterfaceIPConfiguration"]:
        result = self._values.get("ip_configurations")
        assert result is not None, "Required property 'ip_configurations' is missing"
        return typing.cast(typing.List["NetworkInterfaceIPConfiguration"], result)

    @builtins.property
    def dns_settings(self) -> typing.Optional["NetworkInterfaceDnsSettings"]:
        result = self._values.get("dns_settings")
        return typing.cast(typing.Optional["NetworkInterfaceDnsSettings"], result)

    @builtins.property
    def enable_accelerated_networking(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_accelerated_networking")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_ip_forwarding(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_ip_forwarding")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def network_security_group(self) -> typing.Optional["NetworkInterfaceNSGReference"]:
        result = self._values.get("network_security_group")
        return typing.cast(typing.Optional["NetworkInterfaceNSGReference"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceDnsSettings",
    jsii_struct_bases=[],
    name_mapping={
        "dns_servers": "dnsServers",
        "internal_dns_name_label": "internalDnsNameLabel",
    },
)
class NetworkInterfaceDnsSettings:
    def __init__(
        self,
        *,
        dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
        internal_dns_name_label: typing.Optional[builtins.str] = None,
    ) -> None:
        '''DNS settings configuration for Network Interface.

        :param dns_servers: Array of DNS server IP addresses.
        :param internal_dns_name_label: Internal DNS name label for the NIC.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b16b2104f6bb2f4176c9ba089263ed25bbb904befb5ff3c0ae69e8b75d5cbce)
            check_type(argname="argument dns_servers", value=dns_servers, expected_type=type_hints["dns_servers"])
            check_type(argname="argument internal_dns_name_label", value=internal_dns_name_label, expected_type=type_hints["internal_dns_name_label"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dns_servers is not None:
            self._values["dns_servers"] = dns_servers
        if internal_dns_name_label is not None:
            self._values["internal_dns_name_label"] = internal_dns_name_label

    @builtins.property
    def dns_servers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of DNS server IP addresses.

        Example::

            ["10.0.0.4", "10.0.0.5"]
        '''
        result = self._values.get("dns_servers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def internal_dns_name_label(self) -> typing.Optional[builtins.str]:
        '''Internal DNS name label for the NIC.

        Example::

            "myvm"
        '''
        result = self._values.get("internal_dns_name_label")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceDnsSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceIPConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "name": "name",
        "subnet": "subnet",
        "primary": "primary",
        "private_ip_address": "privateIPAddress",
        "private_ip_allocation_method": "privateIPAllocationMethod",
        "public_ip_address": "publicIPAddress",
    },
)
class NetworkInterfaceIPConfiguration:
    def __init__(
        self,
        *,
        name: builtins.str,
        subnet: typing.Union["NetworkInterfaceSubnetReference", typing.Dict[builtins.str, typing.Any]],
        primary: typing.Optional[builtins.bool] = None,
        private_ip_address: typing.Optional[builtins.str] = None,
        private_ip_allocation_method: typing.Optional[builtins.str] = None,
        public_ip_address: typing.Optional[typing.Union["NetworkInterfacePublicIPReference", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''IP Configuration for Network Interface.

        :param name: Name of the IP configuration.
        :param subnet: Subnet reference with id property.
        :param primary: Whether this is the primary IP configuration At least one IP configuration must be primary. Default: false
        :param private_ip_address: Private IP address (required if privateIPAllocationMethod is Static).
        :param private_ip_allocation_method: Private IP allocation method. Default: "Dynamic"
        :param public_ip_address: Public IP address reference with id property Optional - for NICs that need public IPs.
        '''
        if isinstance(subnet, dict):
            subnet = NetworkInterfaceSubnetReference(**subnet)
        if isinstance(public_ip_address, dict):
            public_ip_address = NetworkInterfacePublicIPReference(**public_ip_address)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e174ec41099a9676fb6c67ca9d5b5e431c461dfd3ec0672942af14c486e1a529)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument subnet", value=subnet, expected_type=type_hints["subnet"])
            check_type(argname="argument primary", value=primary, expected_type=type_hints["primary"])
            check_type(argname="argument private_ip_address", value=private_ip_address, expected_type=type_hints["private_ip_address"])
            check_type(argname="argument private_ip_allocation_method", value=private_ip_allocation_method, expected_type=type_hints["private_ip_allocation_method"])
            check_type(argname="argument public_ip_address", value=public_ip_address, expected_type=type_hints["public_ip_address"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "subnet": subnet,
        }
        if primary is not None:
            self._values["primary"] = primary
        if private_ip_address is not None:
            self._values["private_ip_address"] = private_ip_address
        if private_ip_allocation_method is not None:
            self._values["private_ip_allocation_method"] = private_ip_allocation_method
        if public_ip_address is not None:
            self._values["public_ip_address"] = public_ip_address

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of the IP configuration.

        Example::

            "ipconfig1"
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def subnet(self) -> "NetworkInterfaceSubnetReference":
        '''Subnet reference with id property.

        Example::

            { id: "/subscriptions/.../subnets/mySubnet" }
        '''
        result = self._values.get("subnet")
        assert result is not None, "Required property 'subnet' is missing"
        return typing.cast("NetworkInterfaceSubnetReference", result)

    @builtins.property
    def primary(self) -> typing.Optional[builtins.bool]:
        '''Whether this is the primary IP configuration At least one IP configuration must be primary.

        :default: false
        '''
        result = self._values.get("primary")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def private_ip_address(self) -> typing.Optional[builtins.str]:
        '''Private IP address (required if privateIPAllocationMethod is Static).

        Example::

            "10.0.1.4"
        '''
        result = self._values.get("private_ip_address")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def private_ip_allocation_method(self) -> typing.Optional[builtins.str]:
        '''Private IP allocation method.

        :default: "Dynamic"

        Example::

            "Dynamic" or "Static"
        '''
        result = self._values.get("private_ip_allocation_method")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def public_ip_address(self) -> typing.Optional["NetworkInterfacePublicIPReference"]:
        '''Public IP address reference with id property Optional - for NICs that need public IPs.

        Example::

            { id: "/subscriptions/.../publicIPAddresses/myPublicIP" }
        '''
        result = self._values.get("public_ip_address")
        return typing.cast(typing.Optional["NetworkInterfacePublicIPReference"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceIPConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceNSGReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class NetworkInterfaceNSGReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Network Security Group reference for Network Interface.

        :param id: Network Security Group resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__27d97cf3ee9b10c49ac6160ab6a3a0f668bd8de42e590417dd1315599f22fc19)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Network Security Group resource ID.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceNSGReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceProps",
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
        "ip_configurations": "ipConfigurations",
        "dns_settings": "dnsSettings",
        "enable_accelerated_networking": "enableAcceleratedNetworking",
        "enable_ip_forwarding": "enableIPForwarding",
        "ignore_changes": "ignoreChanges",
        "network_security_group": "networkSecurityGroup",
        "resource_group_id": "resourceGroupId",
    },
)
class NetworkInterfaceProps(_AzapiResourceProps_141a2340):
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
        ip_configurations: typing.Sequence[typing.Union[NetworkInterfaceIPConfiguration, typing.Dict[builtins.str, typing.Any]]],
        dns_settings: typing.Optional[typing.Union[NetworkInterfaceDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_accelerated_networking: typing.Optional[builtins.bool] = None,
        enable_ip_forwarding: typing.Optional[builtins.bool] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        network_security_group: typing.Optional[typing.Union[NetworkInterfaceNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Network Interface.

        Extends VersionedAzapiResourceProps with Network Interface specific properties

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
        :param ip_configurations: IP configurations for the network interface At least one IP configuration is required One IP configuration must be marked as primary.
        :param dns_settings: DNS settings configuration Optional - configures DNS servers for the NIC.
        :param enable_accelerated_networking: Enable accelerated networking for high-performance scenarios Requires supported VM size. Default: false
        :param enable_ip_forwarding: Enable IP forwarding for network virtual appliances Allows NIC to forward traffic not destined for its IP. Default: false
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param network_security_group: Network Security Group reference with id property Optional - associates an NSG with this NIC.
        :param resource_group_id: Resource group ID where the network interface will be created.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(dns_settings, dict):
            dns_settings = NetworkInterfaceDnsSettings(**dns_settings)
        if isinstance(network_security_group, dict):
            network_security_group = NetworkInterfaceNSGReference(**network_security_group)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70105f9f3a3e89c2f7bf8a70591be498ecead30276e9ded664bad6face4671dc)
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
            check_type(argname="argument ip_configurations", value=ip_configurations, expected_type=type_hints["ip_configurations"])
            check_type(argname="argument dns_settings", value=dns_settings, expected_type=type_hints["dns_settings"])
            check_type(argname="argument enable_accelerated_networking", value=enable_accelerated_networking, expected_type=type_hints["enable_accelerated_networking"])
            check_type(argname="argument enable_ip_forwarding", value=enable_ip_forwarding, expected_type=type_hints["enable_ip_forwarding"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument network_security_group", value=network_security_group, expected_type=type_hints["network_security_group"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "ip_configurations": ip_configurations,
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
        if dns_settings is not None:
            self._values["dns_settings"] = dns_settings
        if enable_accelerated_networking is not None:
            self._values["enable_accelerated_networking"] = enable_accelerated_networking
        if enable_ip_forwarding is not None:
            self._values["enable_ip_forwarding"] = enable_ip_forwarding
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if network_security_group is not None:
            self._values["network_security_group"] = network_security_group
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id

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
    def ip_configurations(self) -> typing.List[NetworkInterfaceIPConfiguration]:
        '''IP configurations for the network interface At least one IP configuration is required One IP configuration must be marked as primary.'''
        result = self._values.get("ip_configurations")
        assert result is not None, "Required property 'ip_configurations' is missing"
        return typing.cast(typing.List[NetworkInterfaceIPConfiguration], result)

    @builtins.property
    def dns_settings(self) -> typing.Optional[NetworkInterfaceDnsSettings]:
        '''DNS settings configuration Optional - configures DNS servers for the NIC.'''
        result = self._values.get("dns_settings")
        return typing.cast(typing.Optional[NetworkInterfaceDnsSettings], result)

    @builtins.property
    def enable_accelerated_networking(self) -> typing.Optional[builtins.bool]:
        '''Enable accelerated networking for high-performance scenarios Requires supported VM size.

        :default: false
        '''
        result = self._values.get("enable_accelerated_networking")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_ip_forwarding(self) -> typing.Optional[builtins.bool]:
        '''Enable IP forwarding for network virtual appliances Allows NIC to forward traffic not destined for its IP.

        :default: false
        '''
        result = self._values.get("enable_ip_forwarding")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def network_security_group(self) -> typing.Optional[NetworkInterfaceNSGReference]:
        '''Network Security Group reference with id property Optional - associates an NSG with this NIC.

        Example::

            { id: "/subscriptions/.../networkSecurityGroups/myNSG" }
        '''
        result = self._values.get("network_security_group")
        return typing.cast(typing.Optional[NetworkInterfaceNSGReference], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the network interface will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfacePublicIPReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class NetworkInterfacePublicIPReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Public IP address reference for Network Interface.

        :param id: Public IP address resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dbb80ea2bc84cf4b34d4b62cca00571fa0f3f602bef1550e17fdec3cdb259a8d)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Public IP address resource ID.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfacePublicIPReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networkinterface.NetworkInterfaceSubnetReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class NetworkInterfaceSubnetReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Subnet reference for Network Interface.

        :param id: Subnet resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__36e3a5db2c044e22ad51b5fb01c27a7a234a02502e305b736fea289dd0d2b444)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Subnet resource ID.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkInterfaceSubnetReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "NetworkInterface",
    "NetworkInterfaceBody",
    "NetworkInterfaceBodyProperties",
    "NetworkInterfaceDnsSettings",
    "NetworkInterfaceIPConfiguration",
    "NetworkInterfaceNSGReference",
    "NetworkInterfaceProps",
    "NetworkInterfacePublicIPReference",
    "NetworkInterfaceSubnetReference",
]

publication.publish()

def _typecheckingstub__3b8db2e4b7e8bf51b1dceda2a4347eed8051b369bf1312f334f8355127d11dd7(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    ip_configurations: typing.Sequence[typing.Union[NetworkInterfaceIPConfiguration, typing.Dict[builtins.str, typing.Any]]],
    dns_settings: typing.Optional[typing.Union[NetworkInterfaceDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_accelerated_networking: typing.Optional[builtins.bool] = None,
    enable_ip_forwarding: typing.Optional[builtins.bool] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    network_security_group: typing.Optional[typing.Union[NetworkInterfaceNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__a249985b536f02f45fff53454fbd7aedbe96f8cc37b238fe4b1749d01b6b40e8(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0543d03565d766c24d70f7b22e4858a625930528ed7577592f650efc7b9705f4(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e30e15da9919f000205fe1766e521cbc479bcdcdc720bb324611b6972499e1e3(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3dec53505a76fcad334043345e7158ce42cd19d15e8e127704c142a85d4f4dd0(
    *,
    location: builtins.str,
    properties: typing.Union[NetworkInterfaceBodyProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b14b418c98a6e7f5e87613b2b98f36d475ce1ea2a7916ab302d893bd941d6ebb(
    *,
    ip_configurations: typing.Sequence[typing.Union[NetworkInterfaceIPConfiguration, typing.Dict[builtins.str, typing.Any]]],
    dns_settings: typing.Optional[typing.Union[NetworkInterfaceDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_accelerated_networking: typing.Optional[builtins.bool] = None,
    enable_ip_forwarding: typing.Optional[builtins.bool] = None,
    network_security_group: typing.Optional[typing.Union[NetworkInterfaceNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b16b2104f6bb2f4176c9ba089263ed25bbb904befb5ff3c0ae69e8b75d5cbce(
    *,
    dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
    internal_dns_name_label: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e174ec41099a9676fb6c67ca9d5b5e431c461dfd3ec0672942af14c486e1a529(
    *,
    name: builtins.str,
    subnet: typing.Union[NetworkInterfaceSubnetReference, typing.Dict[builtins.str, typing.Any]],
    primary: typing.Optional[builtins.bool] = None,
    private_ip_address: typing.Optional[builtins.str] = None,
    private_ip_allocation_method: typing.Optional[builtins.str] = None,
    public_ip_address: typing.Optional[typing.Union[NetworkInterfacePublicIPReference, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__27d97cf3ee9b10c49ac6160ab6a3a0f668bd8de42e590417dd1315599f22fc19(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70105f9f3a3e89c2f7bf8a70591be498ecead30276e9ded664bad6face4671dc(
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
    ip_configurations: typing.Sequence[typing.Union[NetworkInterfaceIPConfiguration, typing.Dict[builtins.str, typing.Any]]],
    dns_settings: typing.Optional[typing.Union[NetworkInterfaceDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_accelerated_networking: typing.Optional[builtins.bool] = None,
    enable_ip_forwarding: typing.Optional[builtins.bool] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    network_security_group: typing.Optional[typing.Union[NetworkInterfaceNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dbb80ea2bc84cf4b34d4b62cca00571fa0f3f602bef1550e17fdec3cdb259a8d(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__36e3a5db2c044e22ad51b5fb01c27a7a234a02502e305b736fea289dd0d2b444(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass
