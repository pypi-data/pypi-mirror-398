r'''
# Azure Virtual Network Construct

This module provides a high-level TypeScript construct for managing Azure Virtual Networks using the Terraform CDK and Azure AZAPI provider.

## Features

* **Multiple API Version Support**: Automatically supports the 3 most recent stable API versions (2025-01-01, 2024-10-01, 2024-07-01)
* **Automatic Version Resolution**: Uses the latest API version by default
* **Version Pinning**: Lock to a specific API version for stability
* **Type-Safe**: Full TypeScript support with comprehensive interfaces
* **JSII Compatible**: Can be used from TypeScript, Python, Java, and C#
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

### Simple Virtual Network

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import { VirtualNetwork } from "@microsoft/terraform-cdk-constructs/azure-virtualnetwork";

const app = new App();
const stack = new TerraformStack(app, "virtual-network-stack");

// Configure the Azure provider
new AzapiProvider(stack, "azapi", {});

// Create a resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

// Create a virtual network
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "my-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
  tags: {
    environment: "production",
    project: "networking",
  },
});

app.synth();
```

## Advanced Usage

### Virtual Network with Custom DNS Servers

```python
const vnet = new VirtualNetwork(stack, "vnet-custom-dns", {
  name: "vnet-with-dns",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
  dhcpOptions: {
    dnsServers: ["10.0.0.4", "10.0.0.5"],
  },
  tags: {
    environment: "production",
  },
});
```

### Multiple Address Spaces

```python
const vnet = new VirtualNetwork(stack, "vnet-multi-address", {
  name: "vnet-multi",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16", "10.1.0.0/16"],
  },
});
```

### DDoS Protection and VM Protection

```python
const vnet = new VirtualNetwork(stack, "vnet-protected", {
  name: "vnet-protected",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
  enableDdosProtection: true,
  enableVmProtection: true,
});
```

### Flow Timeout Configuration

```python
const vnet = new VirtualNetwork(stack, "vnet-flow-timeout", {
  name: "vnet-flow",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
  flowTimeoutInMinutes: 20, // Valid range: 4-30 minutes
});
```

### Pinning to a Specific API Version

```python
const vnet = new VirtualNetwork(stack, "vnet-pinned", {
  name: "vnet-stable",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-07-01", // Pin to specific version
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
});
```

### Using Outputs

```python
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "my-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
});

// Access VNet ID for use in other resources
console.log(vnet.id); // Terraform interpolation string
console.log(vnet.resourceId); // Alias for id

// Use outputs for cross-stack references
new TerraformOutput(stack, "vnet-id", {
  value: vnet.idOutput,
});
```

### Ignore Changes Lifecycle

```python
const vnet = new VirtualNetwork(stack, "vnet-ignore-changes", {
  name: "vnet-lifecycle",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
  tags: {
    managed: "terraform",
  },
  ignoreChanges: ["tags"], // Ignore changes to tags
});
```

### Tag Management

```python
const vnet = new VirtualNetwork(stack, "vnet-tags", {
  name: "vnet-tags",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
  tags: {
    environment: "production",
  },
});

// Add a tag
vnet.addTag("cost-center", "engineering");

// Remove a tag
vnet.removeTag("environment");
```

## API Reference

### VirtualNetworkProps

Configuration properties for the Virtual Network construct.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | No* | Name of the virtual network. If not provided, uses the construct ID. |
| `location` | `string` | Yes | Azure region where the VNet will be created. |
| `resourceGroupId` | `string` | No | Resource group ID. If not provided, uses subscription scope. |
| `addressSpace` | `VirtualNetworkAddressSpace` | Yes | Address space configuration with address prefixes. |
| `dhcpOptions` | `VirtualNetworkDhcpOptions` | No | DHCP options including DNS servers. |
| `subnets` | `any[]` | No | Inline subnet configurations. |
| `enableDdosProtection` | `boolean` | No | Enable DDoS protection (default: false). |
| `enableVmProtection` | `boolean` | No | Enable VM protection (default: false). |
| `encryption` | `any` | No | Encryption settings for the VNet. |
| `flowTimeoutInMinutes` | `number` | No | Flow timeout in minutes (range: 4-30). |
| `tags` | `{ [key: string]: string }` | No | Resource tags. |
| `apiVersion` | `string` | No | Pin to a specific API version. |
| `ignoreChanges` | `string[]` | No | Properties to ignore during updates. |

### VirtualNetworkAddressSpace

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `addressPrefixes` | `string[]` | Yes | Array of address prefixes in CIDR notation (e.g., ["10.0.0.0/16"]). |

### VirtualNetworkDhcpOptions

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `dnsServers` | `string[]` | No | Array of DNS server IP addresses. |

### Public Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | The Azure resource ID of the VNet. |
| `resourceId` | `string` | Alias for `id`. |
| `tags` | `{ [key: string]: string }` | The tags assigned to the VNet. |
| `subscriptionId` | `string` | The subscription ID extracted from the VNet ID. |
| `addressSpace` | `string` | Terraform interpolation string for the address space. |

### Outputs

The construct automatically creates Terraform outputs:

* `id`: The VNet resource ID
* `name`: The VNet name
* `location`: The VNet location
* `addressSpace`: The VNet address space
* `tags`: The VNet tags

### Methods

| Method | Parameters | Description |
|--------|-----------|-------------|
| `addTag` | `key: string, value: string` | Add a tag to the VNet (requires redeployment). |
| `removeTag` | `key: string` | Remove a tag from the VNet (requires redeployment). |

## Best Practices

### 1. Use Latest API Version for New Deployments

Unless you have specific requirements, use the default (latest) API version:

```python
// ✅ Recommended - Uses latest version automatically
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "my-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.0.0.0/16"] },
});
```

### 2. Pin API Versions for Production Stability

For production workloads, consider pinning to a specific API version:

```python
// ✅ Production-ready - Pinned version
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "prod-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-10-01",
  addressSpace: { addressPrefixes: ["10.0.0.0/16"] },
});
```

### 3. Use Proper Address Space Planning

Plan your address spaces carefully to avoid conflicts:

```python
// ✅ Good - Non-overlapping address spaces
const hubVnet = new VirtualNetwork(stack, "hub", {
  name: "hub-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.0.0.0/16"] },
});

const spokeVnet = new VirtualNetwork(stack, "spoke", {
  name: "spoke-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.1.0.0/16"] },
});
```

### 4. Use Tags for Resource Management

Apply consistent tags for better organization:

```python
// ✅ Recommended - Comprehensive tagging
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "my-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.0.0.0/16"] },
  tags: {
    environment: "production",
    cost-center: "engineering",
    managed-by: "terraform",
    project: "network-infrastructure",
  },
});
```

### 5. Configure Custom DNS When Needed

Use custom DNS servers for hybrid scenarios:

```python
// ✅ Hybrid networking setup
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "hybrid-vnet",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.0.0.0/16"] },
  dhcpOptions: {
    dnsServers: ["10.0.0.4", "10.0.0.5"], // Custom DNS servers
  },
});
```

## Troubleshooting

### Common Issues

1. **Address Space Conflicts**: Ensure address spaces don't overlap with existing VNets or on-premises networks.
2. **API Version Errors**: If you encounter API version errors, verify the version is supported (2025-01-01, 2024-10-01, or 2024-07-01).
3. **Permission Issues**: Ensure your Azure service principal has `Network Contributor` role or equivalent permissions.

## Related Constructs

* [`ResourceGroup`](../azure-resourcegroup/README.md) - Azure Resource Groups
* [`Subnet`](../azure-subnet/README.md) - Virtual Network Subnets (coming soon)
* [`NetworkSecurityGroup`](../azure-networksecuritygroup/README.md) - Network Security Groups (coming soon)
* [`NetworkInterface`](../azure-networkinterface/README.md) - Network Interfaces (coming soon)

## Additional Resources

* [Azure Virtual Network Documentation](https://learn.microsoft.com/en-us/azure/virtual-network/)
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


class VirtualNetwork(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetwork.VirtualNetwork",
):
    '''Azure Virtual Network implementation.

    This class provides a single, version-aware implementation that replaces
    version-specific Virtual Network classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Example::

        // Usage with explicit version pinning:
        const vnet = new VirtualNetwork(this, "vnet", {
          name: "my-vnet",
          location: "eastus",
          apiVersion: "2024-07-01",
          addressSpace: {
            addressPrefixes: ["10.0.0.0/16"]
          }
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        address_space: typing.Union["VirtualNetworkAddressSpace", typing.Dict[builtins.str, typing.Any]],
        dhcp_options: typing.Optional[typing.Union["VirtualNetworkDhcpOptions", typing.Dict[builtins.str, typing.Any]]] = None,
        enable_ddos_protection: typing.Optional[builtins.bool] = None,
        enable_vm_protection: typing.Optional[builtins.bool] = None,
        encryption: typing.Any = None,
        flow_timeout_in_minutes: typing.Optional[jsii.Number] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        subnets: typing.Optional[typing.Sequence[typing.Any]] = None,
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
        '''Creates a new Azure Virtual Network using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Virtual Network implementations.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param address_space: Address space for the virtual network Must contain at least one address prefix.
        :param dhcp_options: DHCP options configuration Optional - configures DNS servers for the VNet.
        :param enable_ddos_protection: Enable DDoS protection for the virtual network Requires a DDoS protection plan. Default: false
        :param enable_vm_protection: Enable VM protection for the virtual network. Default: false
        :param encryption: Encryption settings for the virtual network Optional - configures encryption for the VNet.
        :param flow_timeout_in_minutes: Flow timeout in minutes for the virtual network Valid range: 4-30 minutes.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param resource_group_id: Resource group ID where the VNet will be created Optional - will use the subscription scope if not provided.
        :param subnets: Subnets to create within the virtual network Optional - subnets can also be created separately.
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
            type_hints = typing.get_type_hints(_typecheckingstub__dd4ce778dcb9182d7af5ea83093fb360bd445ef6a99597364dde504a17cc51cb)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VirtualNetworkProps(
            address_space=address_space,
            dhcp_options=dhcp_options,
            enable_ddos_protection=enable_ddos_protection,
            enable_vm_protection=enable_vm_protection,
            encryption=encryption,
            flow_timeout_in_minutes=flow_timeout_in_minutes,
            ignore_changes=ignore_changes,
            resource_group_id=resource_group_id,
            subnets=subnets,
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
        '''Add a tag to the Virtual Network Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bd1414b1ffbce9665ef29778775cd7bf12c7355f69f9427b0609345b39a77c41)
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
            type_hints = typing.get_type_hints(_typecheckingstub__8afd4d9551007f99b20f1c8fbd0d997e481ddd9470d81c5ac88a876876fe1778)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Virtual Network Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fc0d449fa548f0a120843ef85553de890c530f950de589dc3bbc65162e279ce8)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Virtual Networks.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Networks.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="addressSpace")
    def address_space(self) -> builtins.str:
        '''Get the address space output value Returns the Terraform interpolation string for the address space.'''
        return typing.cast(builtins.str, jsii.get(self, "addressSpace"))

    @builtins.property
    @jsii.member(jsii_name="addressSpaceOutput")
    def address_space_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "addressSpaceOutput"))

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
    def props(self) -> "VirtualNetworkProps":
        '''The input properties for this Virtual Network instance.'''
        return typing.cast("VirtualNetworkProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property to match original interface.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> builtins.str:
        '''Get the subscription ID from the Virtual Network ID Extracts the subscription ID from the Azure resource ID format.'''
        return typing.cast(builtins.str, jsii.get(self, "subscriptionId"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetwork.VirtualNetworkAddressSpace",
    jsii_struct_bases=[],
    name_mapping={"address_prefixes": "addressPrefixes"},
)
class VirtualNetworkAddressSpace:
    def __init__(self, *, address_prefixes: typing.Sequence[builtins.str]) -> None:
        '''Address space configuration for Virtual Network.

        :param address_prefixes: Array of address prefixes in CIDR notation.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__490702e5495d2fa4c809e4b6ba30ccf3d2ec88751f7be8c530d49f8e0836eebe)
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
        }

    @builtins.property
    def address_prefixes(self) -> typing.List[builtins.str]:
        '''Array of address prefixes in CIDR notation.

        Example::

            ["10.0.0.0/16", "10.1.0.0/16"]
        '''
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkAddressSpace(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetwork.VirtualNetworkDhcpOptions",
    jsii_struct_bases=[],
    name_mapping={"dns_servers": "dnsServers"},
)
class VirtualNetworkDhcpOptions:
    def __init__(
        self,
        *,
        dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''DHCP options configuration for Virtual Network.

        :param dns_servers: Array of DNS server IP addresses.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__186deb296f9f792fd0cdb9c36694f23af05cfe7454ef4823f66f6239a1474e1d)
            check_type(argname="argument dns_servers", value=dns_servers, expected_type=type_hints["dns_servers"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dns_servers is not None:
            self._values["dns_servers"] = dns_servers

    @builtins.property
    def dns_servers(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of DNS server IP addresses.

        Example::

            ["10.0.0.4", "10.0.0.5"]
        '''
        result = self._values.get("dns_servers")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkDhcpOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetwork.VirtualNetworkProps",
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
        "address_space": "addressSpace",
        "dhcp_options": "dhcpOptions",
        "enable_ddos_protection": "enableDdosProtection",
        "enable_vm_protection": "enableVmProtection",
        "encryption": "encryption",
        "flow_timeout_in_minutes": "flowTimeoutInMinutes",
        "ignore_changes": "ignoreChanges",
        "resource_group_id": "resourceGroupId",
        "subnets": "subnets",
    },
)
class VirtualNetworkProps(_AzapiResourceProps_141a2340):
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
        address_space: typing.Union[VirtualNetworkAddressSpace, typing.Dict[builtins.str, typing.Any]],
        dhcp_options: typing.Optional[typing.Union[VirtualNetworkDhcpOptions, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_ddos_protection: typing.Optional[builtins.bool] = None,
        enable_vm_protection: typing.Optional[builtins.bool] = None,
        encryption: typing.Any = None,
        flow_timeout_in_minutes: typing.Optional[jsii.Number] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        subnets: typing.Optional[typing.Sequence[typing.Any]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network.

        Extends AzapiResourceProps with Virtual Network specific properties

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
        :param address_space: Address space for the virtual network Must contain at least one address prefix.
        :param dhcp_options: DHCP options configuration Optional - configures DNS servers for the VNet.
        :param enable_ddos_protection: Enable DDoS protection for the virtual network Requires a DDoS protection plan. Default: false
        :param enable_vm_protection: Enable VM protection for the virtual network. Default: false
        :param encryption: Encryption settings for the virtual network Optional - configures encryption for the VNet.
        :param flow_timeout_in_minutes: Flow timeout in minutes for the virtual network Valid range: 4-30 minutes.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param resource_group_id: Resource group ID where the VNet will be created Optional - will use the subscription scope if not provided.
        :param subnets: Subnets to create within the virtual network Optional - subnets can also be created separately.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(address_space, dict):
            address_space = VirtualNetworkAddressSpace(**address_space)
        if isinstance(dhcp_options, dict):
            dhcp_options = VirtualNetworkDhcpOptions(**dhcp_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3d4361feb9291d6fb4be34646f26c38a80913364024d7e2b9179e0025119baa1)
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
            check_type(argname="argument address_space", value=address_space, expected_type=type_hints["address_space"])
            check_type(argname="argument dhcp_options", value=dhcp_options, expected_type=type_hints["dhcp_options"])
            check_type(argname="argument enable_ddos_protection", value=enable_ddos_protection, expected_type=type_hints["enable_ddos_protection"])
            check_type(argname="argument enable_vm_protection", value=enable_vm_protection, expected_type=type_hints["enable_vm_protection"])
            check_type(argname="argument encryption", value=encryption, expected_type=type_hints["encryption"])
            check_type(argname="argument flow_timeout_in_minutes", value=flow_timeout_in_minutes, expected_type=type_hints["flow_timeout_in_minutes"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument subnets", value=subnets, expected_type=type_hints["subnets"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_space": address_space,
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
        if dhcp_options is not None:
            self._values["dhcp_options"] = dhcp_options
        if enable_ddos_protection is not None:
            self._values["enable_ddos_protection"] = enable_ddos_protection
        if enable_vm_protection is not None:
            self._values["enable_vm_protection"] = enable_vm_protection
        if encryption is not None:
            self._values["encryption"] = encryption
        if flow_timeout_in_minutes is not None:
            self._values["flow_timeout_in_minutes"] = flow_timeout_in_minutes
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if subnets is not None:
            self._values["subnets"] = subnets

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
    def address_space(self) -> VirtualNetworkAddressSpace:
        '''Address space for the virtual network Must contain at least one address prefix.'''
        result = self._values.get("address_space")
        assert result is not None, "Required property 'address_space' is missing"
        return typing.cast(VirtualNetworkAddressSpace, result)

    @builtins.property
    def dhcp_options(self) -> typing.Optional[VirtualNetworkDhcpOptions]:
        '''DHCP options configuration Optional - configures DNS servers for the VNet.'''
        result = self._values.get("dhcp_options")
        return typing.cast(typing.Optional[VirtualNetworkDhcpOptions], result)

    @builtins.property
    def enable_ddos_protection(self) -> typing.Optional[builtins.bool]:
        '''Enable DDoS protection for the virtual network Requires a DDoS protection plan.

        :default: false
        '''
        result = self._values.get("enable_ddos_protection")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_vm_protection(self) -> typing.Optional[builtins.bool]:
        '''Enable VM protection for the virtual network.

        :default: false
        '''
        result = self._values.get("enable_vm_protection")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encryption(self) -> typing.Any:
        '''Encryption settings for the virtual network Optional - configures encryption for the VNet.'''
        result = self._values.get("encryption")
        return typing.cast(typing.Any, result)

    @builtins.property
    def flow_timeout_in_minutes(self) -> typing.Optional[jsii.Number]:
        '''Flow timeout in minutes for the virtual network Valid range: 4-30 minutes.'''
        result = self._values.get("flow_timeout_in_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed.

        Example::

            ["tags", "subnets"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the VNet will be created Optional - will use the subscription scope if not provided.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def subnets(self) -> typing.Optional[typing.List[typing.Any]]:
        '''Subnets to create within the virtual network Optional - subnets can also be created separately.'''
        result = self._values.get("subnets")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "VirtualNetwork",
    "VirtualNetworkAddressSpace",
    "VirtualNetworkDhcpOptions",
    "VirtualNetworkProps",
]

publication.publish()

def _typecheckingstub__dd4ce778dcb9182d7af5ea83093fb360bd445ef6a99597364dde504a17cc51cb(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    address_space: typing.Union[VirtualNetworkAddressSpace, typing.Dict[builtins.str, typing.Any]],
    dhcp_options: typing.Optional[typing.Union[VirtualNetworkDhcpOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_ddos_protection: typing.Optional[builtins.bool] = None,
    enable_vm_protection: typing.Optional[builtins.bool] = None,
    encryption: typing.Any = None,
    flow_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    subnets: typing.Optional[typing.Sequence[typing.Any]] = None,
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

def _typecheckingstub__bd1414b1ffbce9665ef29778775cd7bf12c7355f69f9427b0609345b39a77c41(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8afd4d9551007f99b20f1c8fbd0d997e481ddd9470d81c5ac88a876876fe1778(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fc0d449fa548f0a120843ef85553de890c530f950de589dc3bbc65162e279ce8(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__490702e5495d2fa4c809e4b6ba30ccf3d2ec88751f7be8c530d49f8e0836eebe(
    *,
    address_prefixes: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__186deb296f9f792fd0cdb9c36694f23af05cfe7454ef4823f66f6239a1474e1d(
    *,
    dns_servers: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3d4361feb9291d6fb4be34646f26c38a80913364024d7e2b9179e0025119baa1(
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
    address_space: typing.Union[VirtualNetworkAddressSpace, typing.Dict[builtins.str, typing.Any]],
    dhcp_options: typing.Optional[typing.Union[VirtualNetworkDhcpOptions, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_ddos_protection: typing.Optional[builtins.bool] = None,
    enable_vm_protection: typing.Optional[builtins.bool] = None,
    encryption: typing.Any = None,
    flow_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    subnets: typing.Optional[typing.Sequence[typing.Any]] = None,
) -> None:
    """Type checking stubs"""
    pass
