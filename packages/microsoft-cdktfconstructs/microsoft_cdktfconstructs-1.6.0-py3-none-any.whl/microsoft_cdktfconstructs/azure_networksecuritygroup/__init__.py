r'''
# Azure Network Security Group Construct

This module provides a high-level TypeScript construct for managing Azure Network Security Groups (NSGs) using the Terraform CDK and Azure AZAPI provider.

## Features

* **Multiple API Version Support**: Automatically supports the 3 most recent stable API versions (2025-01-01, 2024-10-01, 2024-07-01)
* **Automatic Version Resolution**: Uses the latest API version by default
* **Version Pinning**: Lock to a specific API version for stability
* **Type-Safe**: Full TypeScript support with comprehensive interfaces
* **JSII Compatible**: Can be used from TypeScript, Python, Java, and C#
* **Security Rule Management**: Comprehensive support for inbound and outbound rules
* **Terraform Outputs**: Automatic creation of outputs for easy reference
* **Tag Management**: Built-in methods for managing resource tags

## Supported API Versions

| Version | Status | Release Date | Notes |
|---------|--------|--------------|-------|
| 2025-01-01 | Active (Latest) | 2025-01-01 | Recommended for new deployments |
| 2024-10-01 | Active | 2024-10-01 | Enhanced performance and reliability |
| 2024-07-01 | Active | 2024-07-01 | Stable release with core features |

## Installation

This module is part of the `@microsoft/terraform-cdk-constructs` package.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Basic Usage

### Simple Network Security Group

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import { NetworkSecurityGroup } from "@microsoft/terraform-cdk-constructs/azure-networksecuritygroup";

const app = new App();
const stack = new TerraformStack(app, "nsg-stack");

// Configure the Azure provider
new AzapiProvider(stack, "azapi", {});

// Create a resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

// Create a network security group with basic rules
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "my-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowSSH",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "22",
        sourceAddressPrefix: "10.0.0.0/24",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
  ],
  tags: {
    environment: "production",
    project: "networking",
  },
});

app.synth();
```

## Security Rule Examples

### Allow SSH from Specific IP Range

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-ssh", {
  name: "nsg-ssh-access",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowSSHFromOffice",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "22",
        sourceAddressPrefix: "203.0.113.0/24", // Office IP range
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
  ],
});
```

### Allow HTTP/HTTPS from Internet

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-web", {
  name: "nsg-web-access",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowHTTP",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "80",
        sourceAddressPrefix: "Internet",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
    {
      name: "AllowHTTPS",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "443",
        sourceAddressPrefix: "Internet",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 110,
        direction: "Inbound",
      },
    },
  ],
});
```

### Allow RDP from Management Subnet

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-rdp", {
  name: "nsg-rdp-access",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowRDPFromManagement",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "3389",
        sourceAddressPrefix: "10.0.1.0/24", // Management subnet
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
  ],
});
```

### Deny All Inbound Traffic (Default Deny)

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-deny", {
  name: "nsg-deny-all",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "DenyAllInbound",
      properties: {
        protocol: "*",
        sourcePortRange: "*",
        destinationPortRange: "*",
        sourceAddressPrefix: "*",
        destinationAddressPrefix: "*",
        access: "Deny",
        priority: 4096, // Lowest priority (evaluated last)
        direction: "Inbound",
      },
    },
  ],
});
```

### Allow Specific Outbound Traffic

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-outbound", {
  name: "nsg-outbound-restricted",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowHTTPSOutbound",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "443",
        sourceAddressPrefix: "*",
        destinationAddressPrefix: "Internet",
        access: "Allow",
        priority: 100,
        direction: "Outbound",
      },
    },
    {
      name: "AllowDNSOutbound",
      properties: {
        protocol: "Udp",
        sourcePortRange: "*",
        destinationPortRange: "53",
        sourceAddressPrefix: "*",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 110,
        direction: "Outbound",
      },
    },
  ],
});
```

## Advanced Usage

### Multiple Rules with Different Protocols

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-multi-protocol", {
  name: "nsg-complex",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowSQL",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "1433",
        sourceAddressPrefix: "10.0.2.0/24",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
    {
      name: "AllowICMPPing",
      properties: {
        protocol: "Icmp",
        sourcePortRange: "*",
        destinationPortRange: "*",
        sourceAddressPrefix: "VirtualNetwork",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 200,
        direction: "Inbound",
      },
    },
  ],
});
```

### Using Port Ranges

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-port-range", {
  name: "nsg-port-range",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowWebPorts",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "8080-8090", // Port range
        sourceAddressPrefix: "Internet",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
  ],
});
```

### Pinning to a Specific API Version

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-pinned", {
  name: "nsg-stable",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-07-01", // Pin to specific version
  securityRules: [
    {
      name: "AllowSSH",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "22",
        sourceAddressPrefix: "10.0.0.0/16",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
  ],
});
```

### Using Outputs

```python
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "my-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [],
});

// Access NSG ID for use in other resources (e.g., subnet association)
console.log(nsg.id); // Terraform interpolation string
console.log(nsg.resourceId); // Alias for id

// Use outputs for cross-stack references
new TerraformOutput(stack, "nsg-id", {
  value: nsg.idOutput,
});
```

### Tag Management

```python
const nsg = new NetworkSecurityGroup(stack, "nsg-tags", {
  name: "nsg-tags",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [],
  tags: {
    environment: "production",
  },
});

// Add a tag
nsg.addTag("cost-center", "engineering");

// Remove a tag
nsg.removeTag("environment");
```

## Understanding Security Rules

### Priority System

* Priority range: **100-4096** (lower number = higher priority)
* Rules are evaluated in priority order (100 is evaluated first)
* Once a matching rule is found, evaluation stops
* Azure has default rules with priority 65000+ that allow VNet traffic and deny all other inbound traffic

### Rule Evaluation Order

1. Rules are processed by priority (ascending order)
2. First matching rule is applied
3. No further rules are evaluated after a match

Example:

```python
securityRules: [
  {
    name: "AllowHTTP",
    properties: {
      priority: 100, // Evaluated first
      access: "Allow",
      // ...
    },
  },
  {
    name: "DenyAll",
    properties: {
      priority: 200, // Evaluated second (if no match above)
      access: "Deny",
      // ...
    },
  },
]
```

### Protocol Types

* `Tcp` - TCP protocol
* `Udp` - UDP protocol
* `Icmp` - ICMP protocol (for ping)
* `Esp` - Encapsulating Security Payload
* `Ah` - Authentication Header
* `*` - Any protocol

### Service Tags

Instead of IP addresses, you can use Azure service tags:

* `Internet` - All Internet addresses
* `VirtualNetwork` - All addresses in the VNet and connected VNets
* `AzureLoadBalancer` - Azure Load Balancer
* `AzureCloud` - All Azure datacenter IP addresses
* And many more...

```python
{
  name: "AllowAzureServices",
  properties: {
    protocol: "Tcp",
    sourcePortRange: "*",
    destinationPortRange: "443",
    sourceAddressPrefix: "AzureCloud",
    destinationAddressPrefix: "*",
    access: "Allow",
    priority: 100,
    direction: "Inbound",
  },
}
```

## API Reference

### NetworkSecurityGroupProps

Configuration properties for the Network Security Group construct.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | No* | Name of the NSG. If not provided, uses the construct ID. |
| `location` | `string` | Yes | Azure region where the NSG will be created. |
| `resourceGroupId` | `string` | No | Resource group ID. If not provided, uses subscription scope. |
| `securityRules` | `SecurityRule[]` | No | Array of security rule configurations. |
| `flushConnection` | `boolean` | No | When enabled, flows created from NSG will be re-evaluated when rules are updated. |
| `tags` | `{ [key: string]: string }` | No | Resource tags. |
| `apiVersion` | `string` | No | Pin to a specific API version. |
| `ignoreChanges` | `string[]` | No | Properties to ignore during updates. |

### SecurityRule

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the security rule. |
| `properties` | `SecurityRuleProperties` | Yes | Security rule properties. |

### SecurityRuleProperties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `protocol` | `string` | Yes | Protocol: `Tcp`, `Udp`, `Icmp`, `Esp`, `Ah`, or `*` |
| `sourcePortRange` | `string` | No | Source port or range (e.g., `80` or `80-90` or `*`) |
| `destinationPortRange` | `string` | No | Destination port or range |
| `sourceAddressPrefix` | `string` | No | Source address prefix (CIDR or service tag) |
| `destinationAddressPrefix` | `string` | No | Destination address prefix |
| `access` | `string` | Yes | `Allow` or `Deny` |
| `priority` | `number` | Yes | Priority (100-4096, lower = higher priority) |
| `direction` | `string` | Yes | `Inbound` or `Outbound` |
| `description` | `string` | No | Description of the rule |

### Public Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | The Azure resource ID of the NSG. |
| `resourceId` | `string` | Alias for `id`. |
| `tags` | `{ [key: string]: string }` | The tags assigned to the NSG. |
| `subscriptionId` | `string` | The subscription ID extracted from the NSG ID. |
| `securityRules` | `string` | Terraform interpolation string for the security rules. |

### Outputs

The construct automatically creates Terraform outputs:

* `id`: The NSG resource ID
* `name`: The NSG name
* `location`: The NSG location
* `securityRules`: The NSG security rules
* `tags`: The NSG tags

### Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `addTag` | `key: string, value: string` | Add a tag to the NSG (requires redeployment). |
| `removeTag` | `key: string` | Remove a tag from the NSG (requires redeployment). |

## Best Practices

### 1. Use Latest API Version for New Deployments

Unless you have specific requirements, use the default (latest) API version:

```python
// ✅ Recommended - Uses latest version automatically
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "my-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [],
});
```

### 2. Pin API Versions for Production Stability

For production workloads, consider pinning to a specific API version:

```python
// ✅ Production-ready - Pinned version
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "prod-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-10-01",
  securityRules: [],
});
```

### 3. Follow Principle of Least Privilege

Only allow necessary traffic and deny everything else:

```python
// ✅ Good - Specific allow rules with default deny
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "secure-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowHTTPSOnly",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "443",
        sourceAddressPrefix: "Internet",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
    {
      name: "DenyAllElse",
      properties: {
        protocol: "*",
        sourcePortRange: "*",
        destinationPortRange: "*",
        sourceAddressPrefix: "*",
        destinationAddressPrefix: "*",
        access: "Deny",
        priority: 4096,
        direction: "Inbound",
      },
    },
  ],
});
```

### 4. Use Service Tags Instead of IP Ranges When Possible

Service tags are maintained by Microsoft and automatically updated:

```python
// ✅ Recommended - Using service tags
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "my-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowFromVNet",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "443",
        sourceAddressPrefix: "VirtualNetwork", // Service tag
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
      },
    },
  ],
});
```

### 5. Document Your Security Rules

Add descriptions to security rules for maintainability:

```python
// ✅ Good - Well documented rules
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "documented-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    {
      name: "AllowWebTraffic",
      properties: {
        protocol: "Tcp",
        sourcePortRange: "*",
        destinationPortRange: "443",
        sourceAddressPrefix: "Internet",
        destinationAddressPrefix: "*",
        access: "Allow",
        priority: 100,
        direction: "Inbound",
        description: "Allow HTTPS from Internet for public web application",
      },
    },
  ],
});
```

### 6. Use Appropriate Priority Spacing

Leave gaps between priorities for future rule insertion:

```python
// ✅ Good - Priority spacing allows for future rules
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "my-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [
    { name: "Rule1", properties: { priority: 100, /* ... */ } },
    { name: "Rule2", properties: { priority: 200, /* ... */ } }, // Gap of 100
    { name: "Rule3", properties: { priority: 300, /* ... */ } },
  ],
});
```

### 7. Tag Resources Consistently

Apply consistent tags for better organization and cost tracking:

```python
// ✅ Recommended - Comprehensive tagging
const nsg = new NetworkSecurityGroup(stack, "nsg", {
  name: "my-nsg",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  securityRules: [],
  tags: {
    environment: "production",
    "cost-center": "engineering",
    "managed-by": "terraform",
    purpose: "web-tier-security",
  },
});
```

## Troubleshooting

### Common Issues

1. **Priority Conflicts**: Ensure each rule has a unique priority between 100-4096.
2. **Port Range Errors**: Verify port ranges are valid (e.g., `80`, `80-90`, `*`).
3. **Protocol Errors**: Use valid protocol values: `Tcp`, `Udp`, `Icmp`, `Esp`, `Ah`, or `*`.
4. **API Version Errors**: If you encounter API version errors, verify the version is supported (2025-01-01, 2024-10-01, or 2024-07-01).
5. **Permission Issues**: Ensure your Azure service principal has `Network Contributor` role or equivalent permissions.

## Related Constructs

* [`ResourceGroup`](../azure-resourcegroup/README.md) - Azure Resource Groups
* [`VirtualNetwork`](../azure-virtualnetwork/README.md) - Virtual Networks
* [`Subnet`](../azure-subnet/README.md) - Virtual Network Subnets
* [`NetworkInterface`](../azure-networkinterface/README.md) - Network Interfaces (coming soon)

## Additional Resources

* [Azure Network Security Groups Documentation](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview)
* [Azure Security Best Practices](https://learn.microsoft.com/en-us/azure/security/fundamentals/network-best-practices)
* [Azure Service Tags](https://learn.microsoft.com/en-us/azure/virtual-network/service-tags-overview)
* [Azure REST API Reference](https://learn.microsoft.com/en-us/rest/api/azure/)
* [Terraform CDK Documentation](https://developer.hashicorp.com/terraform/cdktf)

## Contributing

Contributions are welcome! Please see the [Contributing Guide](../../CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
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


class NetworkSecurityGroup(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networksecuritygroup.NetworkSecurityGroup",
):
    '''Azure Network Security Group implementation.

    This class provides a single, version-aware implementation that replaces
    version-specific Network Security Group classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Example::

        // Usage with explicit version pinning:
        const nsg = new NetworkSecurityGroup(this, "nsg", {
          name: "my-nsg",
          location: "eastus",
          apiVersion: "2024-07-01",
          securityRules: [...]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        flush_connection: typing.Optional[builtins.bool] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        security_rules: typing.Optional[typing.Sequence[typing.Union["SecurityRule", typing.Dict[builtins.str, typing.Any]]]] = None,
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
        '''Creates a new Azure Network Security Group using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Network Security Group implementations.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param flush_connection: When enabled, flows created from NSG connections will be re-evaluated when rules are updated. Default: false
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param resource_group_id: Resource group ID where the NSG will be created Optional - will use the subscription scope if not provided.
        :param security_rules: Security rules for the network security group Optional - rules can also be added after creation.
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
            type_hints = typing.get_type_hints(_typecheckingstub__9423eb819220f386cfbd5e50b130a75687c57d93bcab5cc39d48fd9db78f722d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = NetworkSecurityGroupProps(
            flush_connection=flush_connection,
            ignore_changes=ignore_changes,
            resource_group_id=resource_group_id,
            security_rules=security_rules,
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
        '''Add a tag to the Network Security Group Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7404791a0770273572201e3440a0531338d14307dd44f2837f0948a2c7383ff6)
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
            type_hints = typing.get_type_hints(_typecheckingstub__0112fa6d59c9f200d4736bae3c479147008a746136db5d27416d412dd4f59d3f)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Network Security Group Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f1d30e2655da483ec5684a9d61aa1ac5cf17495ce70ecb971d8a836d28340341)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Network Security Groups.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Network Security Groups.'''
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
    def props(self) -> "NetworkSecurityGroupProps":
        '''The input properties for this Network Security Group instance.'''
        return typing.cast("NetworkSecurityGroupProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property to match original interface.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="securityRules")
    def security_rules(self) -> builtins.str:
        '''Get the security rules output value Returns the Terraform interpolation string for the security rules.'''
        return typing.cast(builtins.str, jsii.get(self, "securityRules"))

    @builtins.property
    @jsii.member(jsii_name="securityRulesOutput")
    def security_rules_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "securityRulesOutput"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> builtins.str:
        '''Get the subscription ID from the Network Security Group ID Extracts the subscription ID from the Azure resource ID format.'''
        return typing.cast(builtins.str, jsii.get(self, "subscriptionId"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networksecuritygroup.NetworkSecurityGroupProps",
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
        "flush_connection": "flushConnection",
        "ignore_changes": "ignoreChanges",
        "resource_group_id": "resourceGroupId",
        "security_rules": "securityRules",
    },
)
class NetworkSecurityGroupProps(_AzapiResourceProps_141a2340):
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
        flush_connection: typing.Optional[builtins.bool] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        security_rules: typing.Optional[typing.Sequence[typing.Union["SecurityRule", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Properties for the Azure Network Security Group.

        Extends AzapiResourceProps with Network Security Group specific properties

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
        :param flush_connection: When enabled, flows created from NSG connections will be re-evaluated when rules are updated. Default: false
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param resource_group_id: Resource group ID where the NSG will be created Optional - will use the subscription scope if not provided.
        :param security_rules: Security rules for the network security group Optional - rules can also be added after creation.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c8dcced8a5a51b51e7aaa7c53e6dde044a87cd5e47f2beb00b876839341554a1)
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
            check_type(argname="argument flush_connection", value=flush_connection, expected_type=type_hints["flush_connection"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument security_rules", value=security_rules, expected_type=type_hints["security_rules"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
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
        if flush_connection is not None:
            self._values["flush_connection"] = flush_connection
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if security_rules is not None:
            self._values["security_rules"] = security_rules

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
    def flush_connection(self) -> typing.Optional[builtins.bool]:
        '''When enabled, flows created from NSG connections will be re-evaluated when rules are updated.

        :default: false
        '''
        result = self._values.get("flush_connection")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed.

        Example::

            ["tags", "securityRules"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the NSG will be created Optional - will use the subscription scope if not provided.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_rules(self) -> typing.Optional[typing.List["SecurityRule"]]:
        '''Security rules for the network security group Optional - rules can also be added after creation.'''
        result = self._values.get("security_rules")
        return typing.cast(typing.Optional[typing.List["SecurityRule"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkSecurityGroupProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networksecuritygroup.SecurityRule",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "properties": "properties"},
)
class SecurityRule:
    def __init__(
        self,
        *,
        name: builtins.str,
        properties: typing.Union["SecurityRuleProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''Security rule configuration for Network Security Group.

        :param name: The name of the security rule Must be unique within the NSG.
        :param properties: Properties of the security rule.
        '''
        if isinstance(properties, dict):
            properties = SecurityRuleProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc006efd70826fc3b23aa730e668fc93dc180d2426d4edad51161f50e602b1da)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "properties": properties,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the security rule Must be unique within the NSG.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> "SecurityRuleProperties":
        '''Properties of the security rule.'''
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("SecurityRuleProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityRule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_networksecuritygroup.SecurityRuleProperties",
    jsii_struct_bases=[],
    name_mapping={
        "access": "access",
        "direction": "direction",
        "priority": "priority",
        "protocol": "protocol",
        "description": "description",
        "destination_address_prefix": "destinationAddressPrefix",
        "destination_address_prefixes": "destinationAddressPrefixes",
        "destination_application_security_groups": "destinationApplicationSecurityGroups",
        "destination_port_range": "destinationPortRange",
        "destination_port_ranges": "destinationPortRanges",
        "source_address_prefix": "sourceAddressPrefix",
        "source_address_prefixes": "sourceAddressPrefixes",
        "source_application_security_groups": "sourceApplicationSecurityGroups",
        "source_port_range": "sourcePortRange",
        "source_port_ranges": "sourcePortRanges",
    },
)
class SecurityRuleProperties:
    def __init__(
        self,
        *,
        access: builtins.str,
        direction: builtins.str,
        priority: jsii.Number,
        protocol: builtins.str,
        description: typing.Optional[builtins.str] = None,
        destination_address_prefix: typing.Optional[builtins.str] = None,
        destination_address_prefixes: typing.Optional[typing.Sequence[builtins.str]] = None,
        destination_application_security_groups: typing.Optional[typing.Sequence[typing.Any]] = None,
        destination_port_range: typing.Optional[builtins.str] = None,
        destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        source_address_prefix: typing.Optional[builtins.str] = None,
        source_address_prefixes: typing.Optional[typing.Sequence[builtins.str]] = None,
        source_application_security_groups: typing.Optional[typing.Sequence[typing.Any]] = None,
        source_port_range: typing.Optional[builtins.str] = None,
        source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for a security rule.

        :param access: The network traffic is allowed or denied Must be "Allow" or "Deny".
        :param direction: The direction of the rule Must be "Inbound" or "Outbound".
        :param priority: The priority of the rule Value must be between 100 and 4096 Lower values have higher priority.
        :param protocol: Network protocol this rule applies to.
        :param description: A description for this rule Restricted to 140 characters.
        :param destination_address_prefix: The destination address prefix.
        :param destination_address_prefixes: The destination address prefixes (for multiple destinations).
        :param destination_application_security_groups: Destination application security groups.
        :param destination_port_range: The destination port or range.
        :param destination_port_ranges: The destination port ranges (for multiple ranges).
        :param source_address_prefix: The source address prefix.
        :param source_address_prefixes: The source address prefixes (for multiple sources).
        :param source_application_security_groups: Source application security groups.
        :param source_port_range: The source port or range.
        :param source_port_ranges: The source port ranges (for multiple ranges).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e86cffa409d9e567c88ba73d578b1575e1a6f30db8feca2d23ba182f64850cca)
            check_type(argname="argument access", value=access, expected_type=type_hints["access"])
            check_type(argname="argument direction", value=direction, expected_type=type_hints["direction"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument protocol", value=protocol, expected_type=type_hints["protocol"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument destination_address_prefix", value=destination_address_prefix, expected_type=type_hints["destination_address_prefix"])
            check_type(argname="argument destination_address_prefixes", value=destination_address_prefixes, expected_type=type_hints["destination_address_prefixes"])
            check_type(argname="argument destination_application_security_groups", value=destination_application_security_groups, expected_type=type_hints["destination_application_security_groups"])
            check_type(argname="argument destination_port_range", value=destination_port_range, expected_type=type_hints["destination_port_range"])
            check_type(argname="argument destination_port_ranges", value=destination_port_ranges, expected_type=type_hints["destination_port_ranges"])
            check_type(argname="argument source_address_prefix", value=source_address_prefix, expected_type=type_hints["source_address_prefix"])
            check_type(argname="argument source_address_prefixes", value=source_address_prefixes, expected_type=type_hints["source_address_prefixes"])
            check_type(argname="argument source_application_security_groups", value=source_application_security_groups, expected_type=type_hints["source_application_security_groups"])
            check_type(argname="argument source_port_range", value=source_port_range, expected_type=type_hints["source_port_range"])
            check_type(argname="argument source_port_ranges", value=source_port_ranges, expected_type=type_hints["source_port_ranges"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "access": access,
            "direction": direction,
            "priority": priority,
            "protocol": protocol,
        }
        if description is not None:
            self._values["description"] = description
        if destination_address_prefix is not None:
            self._values["destination_address_prefix"] = destination_address_prefix
        if destination_address_prefixes is not None:
            self._values["destination_address_prefixes"] = destination_address_prefixes
        if destination_application_security_groups is not None:
            self._values["destination_application_security_groups"] = destination_application_security_groups
        if destination_port_range is not None:
            self._values["destination_port_range"] = destination_port_range
        if destination_port_ranges is not None:
            self._values["destination_port_ranges"] = destination_port_ranges
        if source_address_prefix is not None:
            self._values["source_address_prefix"] = source_address_prefix
        if source_address_prefixes is not None:
            self._values["source_address_prefixes"] = source_address_prefixes
        if source_application_security_groups is not None:
            self._values["source_application_security_groups"] = source_application_security_groups
        if source_port_range is not None:
            self._values["source_port_range"] = source_port_range
        if source_port_ranges is not None:
            self._values["source_port_ranges"] = source_port_ranges

    @builtins.property
    def access(self) -> builtins.str:
        '''The network traffic is allowed or denied Must be "Allow" or "Deny".'''
        result = self._values.get("access")
        assert result is not None, "Required property 'access' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def direction(self) -> builtins.str:
        '''The direction of the rule Must be "Inbound" or "Outbound".'''
        result = self._values.get("direction")
        assert result is not None, "Required property 'direction' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def priority(self) -> jsii.Number:
        '''The priority of the rule Value must be between 100 and 4096 Lower values have higher priority.'''
        result = self._values.get("priority")
        assert result is not None, "Required property 'priority' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def protocol(self) -> builtins.str:
        '''Network protocol this rule applies to.

        Example::

            "Tcp", "Udp", "Icmp", "Esp", "Ah", "*"
        '''
        result = self._values.get("protocol")
        assert result is not None, "Required property 'protocol' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''A description for this rule Restricted to 140 characters.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_address_prefix(self) -> typing.Optional[builtins.str]:
        '''The destination address prefix.

        Example::

            "10.0.1.0/24", "VirtualNetwork", "*"
        '''
        result = self._values.get("destination_address_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_address_prefixes(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        '''The destination address prefixes (for multiple destinations).

        Example::

            ["10.0.1.0/24", "10.0.2.0/24"]
        '''
        result = self._values.get("destination_address_prefixes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def destination_application_security_groups(
        self,
    ) -> typing.Optional[typing.List[typing.Any]]:
        '''Destination application security groups.'''
        result = self._values.get("destination_application_security_groups")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    @builtins.property
    def destination_port_range(self) -> typing.Optional[builtins.str]:
        '''The destination port or range.

        Example::

            "443", "3389", "*"
        '''
        result = self._values.get("destination_port_range")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_port_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The destination port ranges (for multiple ranges).

        Example::

            ["80", "443"]
        '''
        result = self._values.get("destination_port_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def source_address_prefix(self) -> typing.Optional[builtins.str]:
        '''The source address prefix.

        Example::

            "10.0.0.0/16", "VirtualNetwork", "Internet", "*"
        '''
        result = self._values.get("source_address_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_address_prefixes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The source address prefixes (for multiple sources).

        Example::

            ["10.0.0.0/16", "10.1.0.0/16"]
        '''
        result = self._values.get("source_address_prefixes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def source_application_security_groups(
        self,
    ) -> typing.Optional[typing.List[typing.Any]]:
        '''Source application security groups.'''
        result = self._values.get("source_application_security_groups")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    @builtins.property
    def source_port_range(self) -> typing.Optional[builtins.str]:
        '''The source port or range.

        Example::

            "80", "8000-8999", "*"
        '''
        result = self._values.get("source_port_range")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def source_port_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The source port ranges (for multiple ranges).

        Example::

            ["80", "443", "8080-8090"]
        '''
        result = self._values.get("source_port_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityRuleProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "NetworkSecurityGroup",
    "NetworkSecurityGroupProps",
    "SecurityRule",
    "SecurityRuleProperties",
]

publication.publish()

def _typecheckingstub__9423eb819220f386cfbd5e50b130a75687c57d93bcab5cc39d48fd9db78f722d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    flush_connection: typing.Optional[builtins.bool] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    security_rules: typing.Optional[typing.Sequence[typing.Union[SecurityRule, typing.Dict[builtins.str, typing.Any]]]] = None,
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

def _typecheckingstub__7404791a0770273572201e3440a0531338d14307dd44f2837f0948a2c7383ff6(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0112fa6d59c9f200d4736bae3c479147008a746136db5d27416d412dd4f59d3f(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1d30e2655da483ec5684a9d61aa1ac5cf17495ce70ecb971d8a836d28340341(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c8dcced8a5a51b51e7aaa7c53e6dde044a87cd5e47f2beb00b876839341554a1(
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
    flush_connection: typing.Optional[builtins.bool] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    security_rules: typing.Optional[typing.Sequence[typing.Union[SecurityRule, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc006efd70826fc3b23aa730e668fc93dc180d2426d4edad51161f50e602b1da(
    *,
    name: builtins.str,
    properties: typing.Union[SecurityRuleProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e86cffa409d9e567c88ba73d578b1575e1a6f30db8feca2d23ba182f64850cca(
    *,
    access: builtins.str,
    direction: builtins.str,
    priority: jsii.Number,
    protocol: builtins.str,
    description: typing.Optional[builtins.str] = None,
    destination_address_prefix: typing.Optional[builtins.str] = None,
    destination_address_prefixes: typing.Optional[typing.Sequence[builtins.str]] = None,
    destination_application_security_groups: typing.Optional[typing.Sequence[typing.Any]] = None,
    destination_port_range: typing.Optional[builtins.str] = None,
    destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    source_address_prefix: typing.Optional[builtins.str] = None,
    source_address_prefixes: typing.Optional[typing.Sequence[builtins.str]] = None,
    source_application_security_groups: typing.Optional[typing.Sequence[typing.Any]] = None,
    source_port_range: typing.Optional[builtins.str] = None,
    source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass
