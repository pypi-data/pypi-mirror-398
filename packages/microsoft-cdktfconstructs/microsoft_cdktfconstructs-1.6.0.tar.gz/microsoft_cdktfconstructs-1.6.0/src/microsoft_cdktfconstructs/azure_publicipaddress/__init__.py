r'''
# Azure Public IP Address Construct

This module provides a high-level TypeScript construct for managing Azure Public IP Addresses using the Terraform CDK and Azure AZAPI provider.

## Features

* **Multiple API Version Support**: Automatically supports the 3 most recent stable API versions (2025-01-01, 2024-10-01, 2024-07-01)
* **Automatic Version Resolution**: Uses the latest API version by default
* **Version Pinning**: Lock to a specific API version for stability
* **Type-Safe**: Full TypeScript support with comprehensive interfaces
* **JSII Compatible**: Can be used from TypeScript, Python, Java, and C#
* **Terraform Outputs**: Automatic creation of outputs for easy reference
* **Tag Management**: Built-in methods for managing resource tags
* **SKU Support**: Standard and Basic SKU options
* **Zone Support**: Availability zone configuration for high availability

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

### Simple Standard Static Public IP

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import { PublicIPAddress } from "@microsoft/terraform-cdk-constructs/azure-publicipaddress";

const app = new App();
const stack = new TerraformStack(app, "public-ip-stack");

// Configure the Azure provider
new AzapiProvider(stack, "azapi", {});

// Create a resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

// Create a public IP address
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "my-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  tags: {
    environment: "production",
    purpose: "load-balancer",
  },
});

app.synth();
```

## Advanced Usage

### Standard Static Public IP for Load Balancer (Zone-Redundant)

```python
const lbPublicIp = new PublicIPAddress(stack, "lb-public-ip", {
  name: "pip-load-balancer",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
    tier: "Regional",
  },
  publicIPAllocationMethod: "Static",
  zones: ["1", "2", "3"], // Zone-redundant across all availability zones
  tags: {
    purpose: "load-balancer",
    tier: "production",
  },
});
```

### Basic Dynamic Public IP for Virtual Machine

```python
const vmPublicIp = new PublicIPAddress(stack, "vm-public-ip", {
  name: "pip-virtual-machine",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Basic",
  },
  publicIPAllocationMethod: "Dynamic",
  tags: {
    purpose: "virtual-machine",
    tier: "development",
  },
});
```

### Public IP with DNS Label

```python
const dnsPublicIp = new PublicIPAddress(stack, "dns-public-ip", {
  name: "pip-with-dns",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  dnsSettings: {
    domainNameLabel: "myapp", // Creates myapp.eastus.cloudapp.azure.com
  },
  tags: {
    purpose: "application-gateway",
  },
});
```

### Zonal Public IP for NAT Gateway

```python
const natPublicIp = new PublicIPAddress(stack, "nat-public-ip", {
  name: "pip-nat-gateway",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  zones: ["1"], // Pinned to a specific zone
  idleTimeoutInMinutes: 30, // Maximum timeout for long-lived connections
  tags: {
    purpose: "nat-gateway",
    zone: "1",
  },
});
```

### IPv6 Public IP Address

```python
const ipv6PublicIp = new PublicIPAddress(stack, "ipv6-public-ip", {
  name: "pip-ipv6",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  publicIPAddressVersion: "IPv6",
  zones: ["1", "2", "3"],
  tags: {
    purpose: "dual-stack-networking",
  },
});
```

### Global Tier Public IP for Cross-Region Load Balancer

```python
const globalPublicIp = new PublicIPAddress(stack, "global-public-ip", {
  name: "pip-global",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
    tier: "Global",
  },
  publicIPAllocationMethod: "Static",
  tags: {
    purpose: "cross-region-load-balancer",
  },
});
```

### Pinning to a Specific API Version

```python
const publicIp = new PublicIPAddress(stack, "versioned-public-ip", {
  name: "pip-stable",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-07-01", // Pin to specific version
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
});
```

### Using Outputs

```python
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "my-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
});

// Access Public IP ID for use in other resources
console.log(publicIp.id); // Terraform interpolation string
console.log(publicIp.resourceId); // Alias for id

// Access the allocated IP address
console.log(publicIp.ipAddressOutput); // The actual IP address
console.log(publicIp.fqdnOutput); // FQDN if DNS label is configured

// Use outputs for cross-stack references
new TerraformOutput(stack, "public-ip-address", {
  value: publicIp.ipAddressOutput,
});
```

### Tag Management

```python
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "my-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  tags: {
    environment: "production",
  },
});

// Add a tag
publicIp.addTag("cost-center", "engineering");

// Remove a tag
publicIp.removeTag("environment");
```

## API Reference

### PublicIPAddressProps

Configuration properties for the Public IP Address construct.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | No* | Name of the public IP address. If not provided, uses the construct ID. |
| `location` | `string` | Yes | Azure region where the Public IP will be created. |
| `resourceGroupId` | `string` | No | Resource group ID. If not provided, uses subscription scope. |
| `sku` | `PublicIPAddressSku` | No | SKU configuration (default: Standard). |
| `publicIPAllocationMethod` | `string` | No | Allocation method: "Static" or "Dynamic" (default: Dynamic). |
| `publicIPAddressVersion` | `string` | No | IP version: "IPv4" or "IPv6" (default: IPv4). |
| `dnsSettings` | `PublicIPAddressDnsSettings` | No | DNS configuration including domain name label. |
| `idleTimeoutInMinutes` | `number` | No | Idle timeout in minutes (range: 4-30). |
| `zones` | `string[]` | No | Availability zones (e.g., ["1", "2", "3"]). |
| `tags` | `{ [key: string]: string }` | No | Resource tags. |
| `apiVersion` | `string` | No | Pin to a specific API version. |
| `ignoreChanges` | `string[]` | No | Properties to ignore during updates. |

### PublicIPAddressSku

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | SKU name: "Standard" or "Basic". |
| `tier` | `string` | No | SKU tier: "Regional" or "Global" (Standard SKU only). |

### PublicIPAddressDnsSettings

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `domainNameLabel` | `string` | No | Domain name label for DNS configuration. |
| `fqdn` | `string` | No | Fully qualified domain name (read-only). |
| `reverseFqdn` | `string` | No | Reverse FQDN for reverse DNS lookup. |

### Public Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | The Azure resource ID of the Public IP. |
| `resourceId` | `string` | Alias for `id`. |
| `tags` | `{ [key: string]: string }` | The tags assigned to the Public IP. |
| `subscriptionId` | `string` | The subscription ID extracted from the Public IP ID. |

### Outputs

The construct automatically creates Terraform outputs:

* `id`: The Public IP resource ID
* `name`: The Public IP name
* `location`: The Public IP location
* `ipAddress`: The allocated IP address
* `fqdn`: The fully qualified domain name (if DNS label is configured)
* `tags`: The Public IP tags

### Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `addTag` | `key: string, value: string` | Add a tag to the Public IP (requires redeployment). |
| `removeTag` | `key: string` | Remove a tag from the Public IP (requires redeployment). |

## SKU Comparison

### Standard SKU

* **Availability Zones**: Supported (zone-redundant or zonal)
* **Allocation Method**: Requires Static allocation
* **SLA**: 99.99% uptime SLA
* **Security**: Secure by default, NSG required for inbound traffic
* **Use Cases**: Production load balancers, NAT gateways, application gateways
* **Pricing**: Higher cost

### Basic SKU

* **Availability Zones**: Not supported
* **Allocation Method**: Supports Static or Dynamic
* **SLA**: No SLA
* **Security**: Open by default
* **Use Cases**: Development/test VMs, non-production workloads
* **Pricing**: Lower cost

## Allocation Methods

### Static Allocation

* IP address is allocated immediately when the resource is created
* IP address remains constant even when resource is stopped/deallocated
* **Required** for Standard SKU
* Recommended for production workloads

### Dynamic Allocation

* IP address is allocated only when associated with a resource
* IP address may change if resource is stopped/deallocated
* Only supported with Basic SKU
* Suitable for development/test environments

## Best Practices

### 1. Use Standard SKU for Production

```python
// ✅ Recommended - Standard SKU with zone redundancy
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "prod-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
    tier: "Regional",
  },
  publicIPAllocationMethod: "Static",
  zones: ["1", "2", "3"],
});
```

### 2. Configure DNS Labels for User-Friendly Access

```python
// ✅ Good - DNS label for easy access
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "app-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  dnsSettings: {
    domainNameLabel: "myapp", // Creates myapp.eastus.cloudapp.azure.com
  },
});
```

### 3. Use Zone Redundancy for High Availability

```python
// ✅ Recommended - Zone-redundant deployment
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "ha-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  zones: ["1", "2", "3"], // Spread across all zones
});
```

### 4. Apply Consistent Tags

```python
// ✅ Recommended - Comprehensive tagging
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "my-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  tags: {
    environment: "production",
    "cost-center": "engineering",
    "managed-by": "terraform",
    purpose: "load-balancer",
  },
});
```

### 5. Configure Appropriate Idle Timeout

```python
// ✅ Good - Longer timeout for persistent connections
const publicIp = new PublicIPAddress(stack, "public-ip", {
  name: "nat-public-ip",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: {
    name: "Standard",
  },
  publicIPAllocationMethod: "Static",
  idleTimeoutInMinutes: 30, // Maximum for NAT Gateway scenarios
});
```

## Common Use Cases

### Load Balancer Public IP

```python
const lbPublicIp = new PublicIPAddress(stack, "lb-pip", {
  name: "pip-lb",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: { name: "Standard" },
  publicIPAllocationMethod: "Static",
  zones: ["1", "2", "3"],
});
```

### Application Gateway Public IP

```python
const agwPublicIp = new PublicIPAddress(stack, "agw-pip", {
  name: "pip-agw",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: { name: "Standard" },
  publicIPAllocationMethod: "Static",
  dnsSettings: { domainNameLabel: "myapp" },
  zones: ["1", "2", "3"],
});
```

### NAT Gateway Public IP

```python
const natPublicIp = new PublicIPAddress(stack, "nat-pip", {
  name: "pip-nat",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: { name: "Standard" },
  publicIPAllocationMethod: "Static",
  zones: ["1"],
  idleTimeoutInMinutes: 30,
});
```

### Virtual Machine Public IP (Dev/Test)

```python
const vmPublicIp = new PublicIPAddress(stack, "vm-pip", {
  name: "pip-vm",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  sku: { name: "Basic" },
  publicIPAllocationMethod: "Dynamic",
});
```

## Troubleshooting

### Common Issues

1. **SKU Mismatch**: Standard SKU requires Static allocation. Use `publicIPAllocationMethod: "Static"` with Standard SKU.
2. **Zone Availability**: Not all regions support availability zones. Verify zone availability in your target region.
3. **DNS Label Conflicts**: DNS labels must be unique within a region. Choose unique labels or omit the DNS configuration.
4. **API Version Errors**: If you encounter API version errors, verify the version is supported (2025-01-01, 2024-10-01, or 2024-07-01).
5. **Permission Issues**: Ensure your Azure service principal has `Network Contributor` role or equivalent permissions.

## Related Constructs

* [`ResourceGroup`](../azure-resourcegroup/README.md) - Azure Resource Groups
* [`VirtualNetwork`](../azure-virtualnetwork/README.md) - Virtual Networks
* [`NetworkSecurityGroup`](../azure-networksecuritygroup/README.md) - Network Security Groups
* [`Subnet`](../azure-subnet/README.md) - Virtual Network Subnets

## Additional Resources

* [Azure Public IP Documentation](https://learn.microsoft.com/en-us/azure/virtual-network/ip-services/public-ip-addresses)
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


class PublicIPAddress(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_publicipaddress.PublicIPAddress",
):
    '''Azure Public IP Address implementation.

    This class provides a single, version-aware implementation that replaces
    version-specific Public IP Address classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Example::

        // Zonal Public IP:
        const publicIp = new PublicIPAddress(this, "publicIp", {
          name: "my-public-ip",
          location: "eastus",
          sku: {
            name: "Standard"
          },
          publicIPAllocationMethod: "Static",
          zones: ["1"]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        dns_settings: typing.Optional[typing.Union["PublicIPAddressDnsSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        public_ip_address_version: typing.Optional[builtins.str] = None,
        public_ip_allocation_method: typing.Optional[builtins.str] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        sku: typing.Optional[typing.Union["PublicIPAddressSku", typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Creates a new Azure Public IP Address using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Public IP Address implementations.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param dns_settings: DNS settings for the public IP address Optional - configures DNS label for the public IP.
        :param idle_timeout_in_minutes: Idle timeout in minutes Valid range: 4-30 minutes. Default: 4
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param public_ip_address_version: Public IP address version. Default: "IPv4"
        :param public_ip_allocation_method: Public IP allocation method - Static: IP address is allocated immediately and doesn't change - Dynamic: IP address is allocated when associated with a resource Note: Standard SKU requires Static allocation. Default: "Dynamic"
        :param resource_group_id: Resource group ID where the Public IP will be created Optional - will use the subscription scope if not provided.
        :param sku: SKU of the public IP address Standard SKU supports zones and has SLA guarantees Basic SKU does not support zones.
        :param zones: Availability zones for the public IP address Only supported with Standard SKU.
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
            type_hints = typing.get_type_hints(_typecheckingstub__e873bfa7484cb82d7a274dfaef8713b29bea608e35998e5e539b5b95255769db)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = PublicIPAddressProps(
            dns_settings=dns_settings,
            idle_timeout_in_minutes=idle_timeout_in_minutes,
            ignore_changes=ignore_changes,
            public_ip_address_version=public_ip_address_version,
            public_ip_allocation_method=public_ip_allocation_method,
            resource_group_id=resource_group_id,
            sku=sku,
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

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Add a tag to the Public IP Address Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc57b7177e881c4f033246313887ae2d346bf85c48197ea3d0d776e5e4e31552)
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
            type_hints = typing.get_type_hints(_typecheckingstub__1d29442ff657adb5f1dc01cca790d5586c7eaa7d2e35250ec33befcedadf37b0)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Public IP Address Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fc06c232ae76a7f1cdb63b7df7913b6cc2ae839f28bb4f2bb42a0532ff4a95c0)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Public IP Addresses.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Public IP Addresses.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="ipAddress")
    def ip_address(self) -> builtins.str:
        '''Get the IP address output value Returns the Terraform interpolation string for the IP address.'''
        return typing.cast(builtins.str, jsii.get(self, "ipAddress"))

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
    def props(self) -> "PublicIPAddressProps":
        '''The input properties for this Public IP Address instance.'''
        return typing.cast("PublicIPAddressProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property to match original interface.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> builtins.str:
        '''Get the subscription ID from the Public IP Address ID Extracts the subscription ID from the Azure resource ID format.'''
        return typing.cast(builtins.str, jsii.get(self, "subscriptionId"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_publicipaddress.PublicIPAddressDnsSettings",
    jsii_struct_bases=[],
    name_mapping={
        "domain_name_label": "domainNameLabel",
        "fqdn": "fqdn",
        "reverse_fqdn": "reverseFqdn",
    },
)
class PublicIPAddressDnsSettings:
    def __init__(
        self,
        *,
        domain_name_label: typing.Optional[builtins.str] = None,
        fqdn: typing.Optional[builtins.str] = None,
        reverse_fqdn: typing.Optional[builtins.str] = None,
    ) -> None:
        '''DNS settings configuration for Public IP Address.

        :param domain_name_label: The domain name label The concatenation of the domain name label and regionalized DNS zone make up the fully qualified domain name (FQDN) associated with the public IP.
        :param fqdn: The Fully Qualified Domain Name This is the concatenation of the domainNameLabel and the regionalized DNS zone.
        :param reverse_fqdn: The reverse FQDN A user-visible, fully qualified domain name that resolves to this public IP address.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__55d73fbfd95420bc81df5c2d136dd6694feb55a52264c9dc312df010a31fa25c)
            check_type(argname="argument domain_name_label", value=domain_name_label, expected_type=type_hints["domain_name_label"])
            check_type(argname="argument fqdn", value=fqdn, expected_type=type_hints["fqdn"])
            check_type(argname="argument reverse_fqdn", value=reverse_fqdn, expected_type=type_hints["reverse_fqdn"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if domain_name_label is not None:
            self._values["domain_name_label"] = domain_name_label
        if fqdn is not None:
            self._values["fqdn"] = fqdn
        if reverse_fqdn is not None:
            self._values["reverse_fqdn"] = reverse_fqdn

    @builtins.property
    def domain_name_label(self) -> typing.Optional[builtins.str]:
        '''The domain name label The concatenation of the domain name label and regionalized DNS zone make up the fully qualified domain name (FQDN) associated with the public IP.'''
        result = self._values.get("domain_name_label")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def fqdn(self) -> typing.Optional[builtins.str]:
        '''The Fully Qualified Domain Name This is the concatenation of the domainNameLabel and the regionalized DNS zone.'''
        result = self._values.get("fqdn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def reverse_fqdn(self) -> typing.Optional[builtins.str]:
        '''The reverse FQDN A user-visible, fully qualified domain name that resolves to this public IP address.'''
        result = self._values.get("reverse_fqdn")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PublicIPAddressDnsSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_publicipaddress.PublicIPAddressProps",
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
        "dns_settings": "dnsSettings",
        "idle_timeout_in_minutes": "idleTimeoutInMinutes",
        "ignore_changes": "ignoreChanges",
        "public_ip_address_version": "publicIPAddressVersion",
        "public_ip_allocation_method": "publicIPAllocationMethod",
        "resource_group_id": "resourceGroupId",
        "sku": "sku",
        "zones": "zones",
    },
)
class PublicIPAddressProps(_AzapiResourceProps_141a2340):
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
        dns_settings: typing.Optional[typing.Union[PublicIPAddressDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
        idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        public_ip_address_version: typing.Optional[builtins.str] = None,
        public_ip_allocation_method: typing.Optional[builtins.str] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        sku: typing.Optional[typing.Union["PublicIPAddressSku", typing.Dict[builtins.str, typing.Any]]] = None,
        zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure Public IP Address.

        Extends AzapiResourceProps with Public IP Address specific properties

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
        :param dns_settings: DNS settings for the public IP address Optional - configures DNS label for the public IP.
        :param idle_timeout_in_minutes: Idle timeout in minutes Valid range: 4-30 minutes. Default: 4
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param public_ip_address_version: Public IP address version. Default: "IPv4"
        :param public_ip_allocation_method: Public IP allocation method - Static: IP address is allocated immediately and doesn't change - Dynamic: IP address is allocated when associated with a resource Note: Standard SKU requires Static allocation. Default: "Dynamic"
        :param resource_group_id: Resource group ID where the Public IP will be created Optional - will use the subscription scope if not provided.
        :param sku: SKU of the public IP address Standard SKU supports zones and has SLA guarantees Basic SKU does not support zones.
        :param zones: Availability zones for the public IP address Only supported with Standard SKU.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(dns_settings, dict):
            dns_settings = PublicIPAddressDnsSettings(**dns_settings)
        if isinstance(sku, dict):
            sku = PublicIPAddressSku(**sku)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ce3f61160b815ff638dbb042394db57c53ecc4ed09ce279a558a203eea727e8c)
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
            check_type(argname="argument dns_settings", value=dns_settings, expected_type=type_hints["dns_settings"])
            check_type(argname="argument idle_timeout_in_minutes", value=idle_timeout_in_minutes, expected_type=type_hints["idle_timeout_in_minutes"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument public_ip_address_version", value=public_ip_address_version, expected_type=type_hints["public_ip_address_version"])
            check_type(argname="argument public_ip_allocation_method", value=public_ip_allocation_method, expected_type=type_hints["public_ip_allocation_method"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument zones", value=zones, expected_type=type_hints["zones"])
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
        if dns_settings is not None:
            self._values["dns_settings"] = dns_settings
        if idle_timeout_in_minutes is not None:
            self._values["idle_timeout_in_minutes"] = idle_timeout_in_minutes
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if public_ip_address_version is not None:
            self._values["public_ip_address_version"] = public_ip_address_version
        if public_ip_allocation_method is not None:
            self._values["public_ip_allocation_method"] = public_ip_allocation_method
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if sku is not None:
            self._values["sku"] = sku
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
    def dns_settings(self) -> typing.Optional[PublicIPAddressDnsSettings]:
        '''DNS settings for the public IP address Optional - configures DNS label for the public IP.'''
        result = self._values.get("dns_settings")
        return typing.cast(typing.Optional[PublicIPAddressDnsSettings], result)

    @builtins.property
    def idle_timeout_in_minutes(self) -> typing.Optional[jsii.Number]:
        '''Idle timeout in minutes Valid range: 4-30 minutes.

        :default: 4
        '''
        result = self._values.get("idle_timeout_in_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def public_ip_address_version(self) -> typing.Optional[builtins.str]:
        '''Public IP address version.

        :default: "IPv4"
        '''
        result = self._values.get("public_ip_address_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def public_ip_allocation_method(self) -> typing.Optional[builtins.str]:
        '''Public IP allocation method - Static: IP address is allocated immediately and doesn't change - Dynamic: IP address is allocated when associated with a resource Note: Standard SKU requires Static allocation.

        :default: "Dynamic"
        '''
        result = self._values.get("public_ip_allocation_method")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the Public IP will be created Optional - will use the subscription scope if not provided.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sku(self) -> typing.Optional["PublicIPAddressSku"]:
        '''SKU of the public IP address Standard SKU supports zones and has SLA guarantees Basic SKU does not support zones.'''
        result = self._values.get("sku")
        return typing.cast(typing.Optional["PublicIPAddressSku"], result)

    @builtins.property
    def zones(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Availability zones for the public IP address Only supported with Standard SKU.

        Example::

            ["1"], ["2"], ["3"], ["1", "2", "3"]
        '''
        result = self._values.get("zones")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PublicIPAddressProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_publicipaddress.PublicIPAddressSku",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "tier": "tier"},
)
class PublicIPAddressSku:
    def __init__(
        self,
        *,
        name: builtins.str,
        tier: typing.Optional[builtins.str] = None,
    ) -> None:
        '''SKU configuration for Public IP Address.

        :param name: Name of the SKU.
        :param tier: Tier of the SKU.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__263eb94850767278fd0ad2586dd902b091ca565007dba8392a04a9ca8c5be45c)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tier", value=tier, expected_type=type_hints["tier"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }
        if tier is not None:
            self._values["tier"] = tier

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of the SKU.

        Example::

            "Basic", "Standard"
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def tier(self) -> typing.Optional[builtins.str]:
        '''Tier of the SKU.

        Example::

            "Regional", "Global"
        '''
        result = self._values.get("tier")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PublicIPAddressSku(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "PublicIPAddress",
    "PublicIPAddressDnsSettings",
    "PublicIPAddressProps",
    "PublicIPAddressSku",
]

publication.publish()

def _typecheckingstub__e873bfa7484cb82d7a274dfaef8713b29bea608e35998e5e539b5b95255769db(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    dns_settings: typing.Optional[typing.Union[PublicIPAddressDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    public_ip_address_version: typing.Optional[builtins.str] = None,
    public_ip_allocation_method: typing.Optional[builtins.str] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    sku: typing.Optional[typing.Union[PublicIPAddressSku, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__bc57b7177e881c4f033246313887ae2d346bf85c48197ea3d0d776e5e4e31552(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d29442ff657adb5f1dc01cca790d5586c7eaa7d2e35250ec33befcedadf37b0(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fc06c232ae76a7f1cdb63b7df7913b6cc2ae839f28bb4f2bb42a0532ff4a95c0(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__55d73fbfd95420bc81df5c2d136dd6694feb55a52264c9dc312df010a31fa25c(
    *,
    domain_name_label: typing.Optional[builtins.str] = None,
    fqdn: typing.Optional[builtins.str] = None,
    reverse_fqdn: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ce3f61160b815ff638dbb042394db57c53ecc4ed09ce279a558a203eea727e8c(
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
    dns_settings: typing.Optional[typing.Union[PublicIPAddressDnsSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    public_ip_address_version: typing.Optional[builtins.str] = None,
    public_ip_allocation_method: typing.Optional[builtins.str] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    sku: typing.Optional[typing.Union[PublicIPAddressSku, typing.Dict[builtins.str, typing.Any]]] = None,
    zones: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__263eb94850767278fd0ad2586dd902b091ca565007dba8392a04a9ca8c5be45c(
    *,
    name: builtins.str,
    tier: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
