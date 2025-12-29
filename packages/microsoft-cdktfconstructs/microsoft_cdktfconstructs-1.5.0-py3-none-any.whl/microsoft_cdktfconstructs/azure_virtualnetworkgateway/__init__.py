r'''
# Azure Virtual Network Gateway Construct

This construct provides a CDK for Terraform (CDKTF) implementation of Azure Virtual Network Gateway using the AzapiResource framework.

## Overview

Azure Virtual Network Gateway is used to send encrypted traffic between Azure virtual networks and on-premises locations over the public Internet (VPN Gateway) or through Azure ExpressRoute circuits (ExpressRoute Gateway).

This construct supports:

* **VPN Gateways**: Site-to-Site, Point-to-Site, and VNet-to-VNet connections
* **ExpressRoute Gateways**: Private connections to Azure through ExpressRoute circuits
* **BGP Support**: Border Gateway Protocol for dynamic routing
* **Active-Active Mode**: High availability with dual gateway instances
* **Multiple SKUs**: From Basic to high-performance VpnGw5/ErGw3AZ

## Features

* ✅ Automatic latest API version resolution
* ✅ Explicit version pinning for stability
* ✅ Schema-driven validation and transformation
* ✅ Full backward compatibility
* ✅ JSII compliance for multi-language support
* ✅ Comprehensive TypeScript type definitions

## Supported API Versions

* `2024-01-01` (Active)
* `2024-05-01` (Active, Latest - Default)

## Installation

```bash
npm install @cdktf-constructs/azure-virtualnetworkgateway
```

## Basic Usage

### Simple VPN Gateway

```python
import { VirtualNetworkGateway } from '@cdktf-constructs/azure-virtualnetworkgateway';
import { ResourceGroup } from '@cdktf-constructs/azure-resourcegroup';
import { VirtualNetwork } from '@cdktf-constructs/azure-virtualnetwork';
import { Subnet } from '@cdktf-constructs/azure-subnet';
import { PublicIPAddress } from '@cdktf-constructs/azure-publicipaddress';

// Create resource group
const resourceGroup = new ResourceGroup(this, 'rg', {
  name: 'rg-network',
  location: 'eastus',
});

// Create virtual network
const vnet = new VirtualNetwork(this, 'vnet', {
  name: 'vnet-main',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ['10.0.0.0/16']
  },
});

// Create GatewaySubnet (must be named "GatewaySubnet")
const gatewaySubnet = new Subnet(this, 'gateway-subnet', {
  name: 'GatewaySubnet',
  virtualNetworkId: vnet.id,
  addressPrefix: '10.0.1.0/24',
});

// Create public IP for gateway
const publicIp = new PublicIPAddress(this, 'pip', {
  name: 'pip-gateway',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: {
    name: 'Standard',
    tier: 'Regional'
  },
  publicIPAllocationMethod: 'Static',
});

// Create VPN Gateway
const vpnGateway = new VirtualNetworkGateway(this, 'vpn-gateway', {
  name: 'vng-main',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  gatewayType: 'Vpn',
  vpnType: 'RouteBased',
  sku: {
    name: 'VpnGw1',
    tier: 'VpnGw1'
  },
  ipConfigurations: [{
    name: 'default',
    subnetId: gatewaySubnet.id,
    publicIPAddressId: publicIp.id
  }]
});
```

### VPN Gateway with BGP

```python
const vpnGateway = new VirtualNetworkGateway(this, 'vpn-gateway-bgp', {
  name: 'vng-bgp',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  gatewayType: 'Vpn',
  vpnType: 'RouteBased',
  sku: {
    name: 'VpnGw1',
    tier: 'VpnGw1'
  },
  enableBgp: true,
  bgpSettings: {
    asn: 65515,
    peerWeight: 0
  },
  ipConfigurations: [{
    name: 'default',
    subnetId: gatewaySubnet.id,
    publicIPAddressId: publicIp.id
  }],
  tags: {
    environment: 'production',
    purpose: 'site-to-site-vpn'
  }
});
```

### Active-Active VPN Gateway

```python
// Create second public IP for active-active
const publicIp2 = new PublicIPAddress(this, 'pip2', {
  name: 'pip-gateway-2',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: {
    name: 'Standard',
    tier: 'Regional'
  },
  publicIPAllocationMethod: 'Static',
});

const vpnGateway = new VirtualNetworkGateway(this, 'vpn-gateway-aa', {
  name: 'vng-active-active',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  gatewayType: 'Vpn',
  vpnType: 'RouteBased',
  sku: {
    name: 'VpnGw1',
    tier: 'VpnGw1'
  },
  activeActive: true,
  ipConfigurations: [
    {
      name: 'config1',
      subnetId: gatewaySubnet.id,
      publicIPAddressId: publicIp.id
    },
    {
      name: 'config2',
      subnetId: gatewaySubnet.id,
      publicIPAddressId: publicIp2.id
    }
  ]
});
```

### Point-to-Site VPN Gateway

```python
const vpnGateway = new VirtualNetworkGateway(this, 'vpn-gateway-p2s', {
  name: 'vng-point-to-site',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  gatewayType: 'Vpn',
  vpnType: 'RouteBased',
  sku: {
    name: 'VpnGw1',
    tier: 'VpnGw1'
  },
  ipConfigurations: [{
    name: 'default',
    subnetId: gatewaySubnet.id,
    publicIPAddressId: publicIp.id
  }],
  vpnClientConfiguration: {
    vpnClientAddressPool: {
      addressPrefixes: ['172.16.0.0/24']
    },
    vpnClientProtocols: ['IkeV2', 'OpenVPN'],
    vpnClientRootCertificates: [
      {
        name: 'RootCert',
        publicCertData: 'MIIC5zCCAc+gAwIBAgI...' // Your certificate data
      }
    ]
  }
});
```

### ExpressRoute Gateway

```python
const erGateway = new VirtualNetworkGateway(this, 'er-gateway', {
  name: 'vng-expressroute',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  gatewayType: 'ExpressRoute',
  sku: {
    name: 'ErGw1AZ',
    tier: 'ErGw1AZ'
  },
  ipConfigurations: [{
    name: 'default',
    subnetId: gatewaySubnet.id,
    publicIPAddressId: publicIp.id
  }],
  tags: {
    environment: 'production',
    purpose: 'expressroute'
  }
});
```

### Generation 2 VPN Gateway

```python
const vpnGateway = new VirtualNetworkGateway(this, 'vpn-gateway-gen2', {
  name: 'vng-generation2',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  gatewayType: 'Vpn',
  vpnType: 'RouteBased',
  sku: {
    name: 'VpnGw2',
    tier: 'VpnGw2'
  },
  vpnGatewayGeneration: 'Generation2',
  ipConfigurations: [{
    name: 'default',
    subnetId: gatewaySubnet.id,
    publicIPAddressId: publicIp.id
  }]
});
```

## Configuration Options

### VirtualNetworkGatewayProps

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | No | CDK ID | Name of the virtual network gateway |
| `location` | string | Yes | - | Azure region |
| `gatewayType` | "Vpn" | "ExpressRoute" | Yes | - | Type of gateway |
| `vpnType` | "RouteBased" | "PolicyBased" | No | "RouteBased" | VPN routing type |
| `sku` | VirtualNetworkGatewaySku | Yes | - | Gateway SKU configuration |
| `ipConfigurations` | VirtualNetworkGatewayIpConfiguration[] | Yes | - | IP configurations (1 or 2) |
| `enableBgp` | boolean | No | false | Enable BGP |
| `activeActive` | boolean | No | false | Enable active-active mode |
| `bgpSettings` | VirtualNetworkGatewayBgpSettings | No | - | BGP configuration |
| `vpnGatewayGeneration` | string | No | - | Gateway generation (Gen1/Gen2) |
| `vpnClientConfiguration` | VirtualNetworkGatewayVpnClientConfiguration | No | - | Point-to-site config |
| `customRoutes` | VirtualNetworkGatewayCustomRoutes | No | - | Custom routing |
| `enablePrivateIpAddress` | boolean | No | false | Enable private IP |
| `gatewayDefaultSite` | VirtualNetworkGatewayDefaultSite | No | - | Default site for tunneling |
| `resourceGroupId` | string | No | - | Resource group ID |
| `tags` | Record<string, string> | No | {} | Resource tags |
| `apiVersion` | string | No | "2024-05-01" | API version to use |
| `ignoreChanges` | string[] | No | [] | Properties to ignore |

### SKU Options

#### VPN Gateway SKUs

* `Basic`: Legacy SKU (limited features)
* `VpnGw1`, `VpnGw2`, `VpnGw3`: Generation 1
* `VpnGw1AZ`, `VpnGw2AZ`, `VpnGw3AZ`: Zone-redundant Generation 1
* `VpnGw4`, `VpnGw5`: Generation 2 high-performance
* `VpnGw4AZ`, `VpnGw5AZ`: Zone-redundant Generation 2

#### ExpressRoute Gateway SKUs

* `Standard`, `HighPerformance`, `UltraPerformance`: Classic SKUs
* `ErGw1AZ`, `ErGw2AZ`, `ErGw3AZ`: Zone-redundant SKUs

## Important Notes

### Provisioning Time

* **Provisioning Time**: VPN and ExpressRoute gateways typically take 30-45 minutes to provision. The construct is configured with 60-minute timeouts to accommodate this.

### GatewaySubnet Requirements

1. **Name**: The subnet MUST be named exactly "GatewaySubnet"
2. **Size**: Minimum /29, recommended /27 or larger
3. **Delegation**: Must not be delegated to any service
4. **NSG**: Network Security Groups are not recommended on GatewaySubnet

### Deployment Time

* **VPN Gateways**: 30-45 minutes to deploy
* **ExpressRoute Gateways**: 30-45 minutes to deploy
* Plan accordingly in CI/CD pipelines

### Active-Active Mode

* Requires 2 IP configurations
* Requires 2 public IP addresses
* Both configurations must reference the same GatewaySubnet
* Only supported with VpnGw1 or higher SKUs

### BGP Configuration

* Required for ExpressRoute
* Recommended for Site-to-Site VPN with dynamic routing
* Not supported with Basic SKU
* ASN must be valid (not 65515 for on-premises)

## Outputs

The construct provides the following outputs:

```python
vpnGateway.id              // Gateway resource ID
vpnGateway.name            // Gateway name
vpnGateway.location        // Gateway location
vpnGateway.resourceId      // Alias for id
vpnGateway.subscriptionId  // Extracted subscription ID
```

## API Version Support

To use a specific API version:

```python
const vpnGateway = new VirtualNetworkGateway(this, 'vpn-gateway', {
  apiVersion: '2024-01-01',
  // ... other properties
});
```

## Related Resources

* [Azure Resource Group](../azure-resourcegroup)
* [Azure Virtual Network](../azure-virtualnetwork)
* [Azure Subnet](../azure-subnet)
* [Azure Public IP Address](../azure-publicipaddress)

## Azure Documentation

* [Virtual Network Gateway Overview](https://learn.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-about-vpngateways)
* [VPN Gateway SKUs](https://learn.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-about-vpn-gateway-settings#gwsku)
* [ExpressRoute Gateways](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-about-virtual-network-gateways)
* [BGP Configuration](https://learn.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-bgp-overview)
* [Point-to-Site VPN](https://learn.microsoft.com/en-us/azure/vpn-gateway/point-to-site-about)

## License

This construct is part of the CDKTF Azure Constructs library.
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


class VirtualNetworkGateway(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGateway",
):
    '''Azure Virtual Network Gateway implementation.

    This class provides a single, version-aware implementation that replaces
    version-specific Virtual Network Gateway classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Virtual Network Gateways are used to send encrypted traffic between Azure virtual
    networks and on-premises locations over the public Internet (VPN) or through
    Azure ExpressRoute circuits (ExpressRoute).

    Example::

        // Active-Active VPN Gateway:
        const vpnGateway = new VirtualNetworkGateway(this, "vpnGateway", {
          name: "my-vpn-gateway-aa",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          gatewayType: "Vpn",
          vpnType: "RouteBased",
          sku: {
            name: "VpnGw1",
            tier: "VpnGw1"
          },
          activeActive: true,
          ipConfigurations: [
            {
              name: "config1",
              subnetId: gatewaySubnet.id,
              publicIPAddressId: publicIp1.id
            },
            {
              name: "config2",
              subnetId: gatewaySubnet.id,
              publicIPAddressId: publicIp2.id
            }
          ]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        gateway_type: builtins.str,
        ip_configurations: typing.Sequence[typing.Union["VirtualNetworkGatewayIpConfiguration", typing.Dict[builtins.str, typing.Any]]],
        sku: typing.Union["VirtualNetworkGatewaySku", typing.Dict[builtins.str, typing.Any]],
        active_active: typing.Optional[builtins.bool] = None,
        bgp_settings: typing.Optional[typing.Union["VirtualNetworkGatewayBgpSettings", typing.Dict[builtins.str, typing.Any]]] = None,
        custom_routes: typing.Optional[typing.Union["VirtualNetworkGatewayCustomRoutes", typing.Dict[builtins.str, typing.Any]]] = None,
        enable_bgp: typing.Optional[builtins.bool] = None,
        enable_private_ip_address: typing.Optional[builtins.bool] = None,
        gateway_default_site: typing.Optional[typing.Union["VirtualNetworkGatewayDefaultSite", typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        vpn_client_configuration: typing.Optional[typing.Union["VirtualNetworkGatewayVpnClientConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        vpn_gateway_generation: typing.Optional[builtins.str] = None,
        vpn_type: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Virtual Network Gateway using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Virtual Network Gateway implementations.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param gateway_type: Gateway type Must be either "Vpn" or "ExpressRoute".
        :param ip_configurations: IP configurations for the gateway At least one IP configuration is required Two IP configurations are required for active-active mode.
        :param sku: SKU configuration for the gateway.
        :param active_active: Enable active-active mode for the gateway Requires two IP configurations. Default: false
        :param bgp_settings: BGP settings for the gateway Required if enableBgp is true.
        :param custom_routes: Custom routes for the gateway.
        :param enable_bgp: Enable BGP for the gateway. Default: false
        :param enable_private_ip_address: Enable private IP address for the gateway. Default: false
        :param gateway_default_site: Default site for force tunneling.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param resource_group_id: Resource group ID where the Gateway will be created Optional - will use the subscription scope if not provided.
        :param vpn_client_configuration: VPN client configuration for point-to-site connections.
        :param vpn_gateway_generation: VPN gateway generation.
        :param vpn_type: VPN type for VPN gateways. Default: "RouteBased"
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
            type_hints = typing.get_type_hints(_typecheckingstub__f1b2bbccd26a32280967875530d8991dc124465acd35f776e522e52cb07a160b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VirtualNetworkGatewayProps(
            gateway_type=gateway_type,
            ip_configurations=ip_configurations,
            sku=sku,
            active_active=active_active,
            bgp_settings=bgp_settings,
            custom_routes=custom_routes,
            enable_bgp=enable_bgp,
            enable_private_ip_address=enable_private_ip_address,
            gateway_default_site=gateway_default_site,
            ignore_changes=ignore_changes,
            resource_group_id=resource_group_id,
            vpn_client_configuration=vpn_client_configuration,
            vpn_gateway_generation=vpn_gateway_generation,
            vpn_type=vpn_type,
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
        '''Add a tag to the Virtual Network Gateway Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__61db15ff5702cb0392f1c8b13fa5bf023b9d5f8c5302799e43469fca20c17159)
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
            type_hints = typing.get_type_hints(_typecheckingstub__b7200d420e00320d25d9438de4eb7ce05c77ea62b3f519612221a00bb6e3aa38)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Virtual Network Gateway Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26342d14bf1ec0cf3f04e99ca1479b49fd6d31f14b37c300152da564f3ce73d7)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Virtual Network Gateways.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Network Gateways.'''
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
    def props(self) -> "VirtualNetworkGatewayProps":
        '''The input properties for this Virtual Network Gateway instance.'''
        return typing.cast("VirtualNetworkGatewayProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property to match original interface.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> builtins.str:
        '''Get the subscription ID from the Virtual Network Gateway ID Extracts the subscription ID from the Azure resource ID format.'''
        return typing.cast(builtins.str, jsii.get(self, "subscriptionId"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayBgpSettings",
    jsii_struct_bases=[],
    name_mapping={
        "asn": "asn",
        "bgp_peering_address": "bgpPeeringAddress",
        "bgp_peering_addresses": "bgpPeeringAddresses",
        "peer_weight": "peerWeight",
    },
)
class VirtualNetworkGatewayBgpSettings:
    def __init__(
        self,
        *,
        asn: typing.Optional[jsii.Number] = None,
        bgp_peering_address: typing.Optional[builtins.str] = None,
        bgp_peering_addresses: typing.Optional[typing.Sequence[typing.Any]] = None,
        peer_weight: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''BGP settings for Virtual Network Gateway.

        :param asn: BGP ASN (Autonomous System Number).
        :param bgp_peering_address: BGP peering address.
        :param bgp_peering_addresses: BGP peering addresses for active-active configuration.
        :param peer_weight: Weight added to routes learned from this BGP speaker.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8ea3f6166ad07f87ec570ff7cc0ed9d8aa229d2877b4b20aa731f2a7fa651f92)
            check_type(argname="argument asn", value=asn, expected_type=type_hints["asn"])
            check_type(argname="argument bgp_peering_address", value=bgp_peering_address, expected_type=type_hints["bgp_peering_address"])
            check_type(argname="argument bgp_peering_addresses", value=bgp_peering_addresses, expected_type=type_hints["bgp_peering_addresses"])
            check_type(argname="argument peer_weight", value=peer_weight, expected_type=type_hints["peer_weight"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if asn is not None:
            self._values["asn"] = asn
        if bgp_peering_address is not None:
            self._values["bgp_peering_address"] = bgp_peering_address
        if bgp_peering_addresses is not None:
            self._values["bgp_peering_addresses"] = bgp_peering_addresses
        if peer_weight is not None:
            self._values["peer_weight"] = peer_weight

    @builtins.property
    def asn(self) -> typing.Optional[jsii.Number]:
        '''BGP ASN (Autonomous System Number).

        Example::

            65515
        '''
        result = self._values.get("asn")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def bgp_peering_address(self) -> typing.Optional[builtins.str]:
        '''BGP peering address.'''
        result = self._values.get("bgp_peering_address")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def bgp_peering_addresses(self) -> typing.Optional[typing.List[typing.Any]]:
        '''BGP peering addresses for active-active configuration.'''
        result = self._values.get("bgp_peering_addresses")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    @builtins.property
    def peer_weight(self) -> typing.Optional[jsii.Number]:
        '''Weight added to routes learned from this BGP speaker.'''
        result = self._values.get("peer_weight")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayBgpSettings(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayCustomRoutes",
    jsii_struct_bases=[],
    name_mapping={"address_prefixes": "addressPrefixes"},
)
class VirtualNetworkGatewayCustomRoutes:
    def __init__(
        self,
        *,
        address_prefixes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Custom routes configuration.

        :param address_prefixes: List of address prefixes.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3ebd2b6ce5d9dc44872044222122fec46657cc5ebe19c037a702ed789084b9bb)
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if address_prefixes is not None:
            self._values["address_prefixes"] = address_prefixes

    @builtins.property
    def address_prefixes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''List of address prefixes.'''
        result = self._values.get("address_prefixes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayCustomRoutes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayDefaultSite",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualNetworkGatewayDefaultSite:
    def __init__(self, *, id: builtins.str) -> None:
        '''Gateway default site reference.

        :param id: Resource ID of the local network gateway to use as default site.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__32c58f1cd50b4b890f8842296b4635b19ca5474bfc162909daff33ca05a85a40)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Resource ID of the local network gateway to use as default site.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayDefaultSite(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayIpConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "name": "name",
        "public_ip_address_id": "publicIPAddressId",
        "subnet_id": "subnetId",
        "private_ip_allocation_method": "privateIPAllocationMethod",
    },
)
class VirtualNetworkGatewayIpConfiguration:
    def __init__(
        self,
        *,
        name: builtins.str,
        public_ip_address_id: builtins.str,
        subnet_id: builtins.str,
        private_ip_allocation_method: typing.Optional[builtins.str] = None,
    ) -> None:
        '''IP configuration for Virtual Network Gateway.

        :param name: Name of the IP configuration.
        :param public_ip_address_id: ID of the public IP address to use.
        :param subnet_id: ID of the subnet to use (must be GatewaySubnet).
        :param private_ip_allocation_method: Private IP allocation method. Default: "Dynamic"
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ca4e5b564e4aa6f3c8152f63b855de08ce5420893411b4e9c2d8bb38c795b4fb)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument public_ip_address_id", value=public_ip_address_id, expected_type=type_hints["public_ip_address_id"])
            check_type(argname="argument subnet_id", value=subnet_id, expected_type=type_hints["subnet_id"])
            check_type(argname="argument private_ip_allocation_method", value=private_ip_allocation_method, expected_type=type_hints["private_ip_allocation_method"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "public_ip_address_id": public_ip_address_id,
            "subnet_id": subnet_id,
        }
        if private_ip_allocation_method is not None:
            self._values["private_ip_allocation_method"] = private_ip_allocation_method

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of the IP configuration.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def public_ip_address_id(self) -> builtins.str:
        '''ID of the public IP address to use.'''
        result = self._values.get("public_ip_address_id")
        assert result is not None, "Required property 'public_ip_address_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def subnet_id(self) -> builtins.str:
        '''ID of the subnet to use (must be GatewaySubnet).'''
        result = self._values.get("subnet_id")
        assert result is not None, "Required property 'subnet_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def private_ip_allocation_method(self) -> typing.Optional[builtins.str]:
        '''Private IP allocation method.

        :default: "Dynamic"
        '''
        result = self._values.get("private_ip_allocation_method")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayIpConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayProps",
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
        "gateway_type": "gatewayType",
        "ip_configurations": "ipConfigurations",
        "sku": "sku",
        "active_active": "activeActive",
        "bgp_settings": "bgpSettings",
        "custom_routes": "customRoutes",
        "enable_bgp": "enableBgp",
        "enable_private_ip_address": "enablePrivateIpAddress",
        "gateway_default_site": "gatewayDefaultSite",
        "ignore_changes": "ignoreChanges",
        "resource_group_id": "resourceGroupId",
        "vpn_client_configuration": "vpnClientConfiguration",
        "vpn_gateway_generation": "vpnGatewayGeneration",
        "vpn_type": "vpnType",
    },
)
class VirtualNetworkGatewayProps(_AzapiResourceProps_141a2340):
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
        gateway_type: builtins.str,
        ip_configurations: typing.Sequence[typing.Union[VirtualNetworkGatewayIpConfiguration, typing.Dict[builtins.str, typing.Any]]],
        sku: typing.Union["VirtualNetworkGatewaySku", typing.Dict[builtins.str, typing.Any]],
        active_active: typing.Optional[builtins.bool] = None,
        bgp_settings: typing.Optional[typing.Union[VirtualNetworkGatewayBgpSettings, typing.Dict[builtins.str, typing.Any]]] = None,
        custom_routes: typing.Optional[typing.Union[VirtualNetworkGatewayCustomRoutes, typing.Dict[builtins.str, typing.Any]]] = None,
        enable_bgp: typing.Optional[builtins.bool] = None,
        enable_private_ip_address: typing.Optional[builtins.bool] = None,
        gateway_default_site: typing.Optional[typing.Union[VirtualNetworkGatewayDefaultSite, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        vpn_client_configuration: typing.Optional[typing.Union["VirtualNetworkGatewayVpnClientConfiguration", typing.Dict[builtins.str, typing.Any]]] = None,
        vpn_gateway_generation: typing.Optional[builtins.str] = None,
        vpn_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Gateway.

        Extends AzapiResourceProps with Virtual Network Gateway specific properties

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
        :param gateway_type: Gateway type Must be either "Vpn" or "ExpressRoute".
        :param ip_configurations: IP configurations for the gateway At least one IP configuration is required Two IP configurations are required for active-active mode.
        :param sku: SKU configuration for the gateway.
        :param active_active: Enable active-active mode for the gateway Requires two IP configurations. Default: false
        :param bgp_settings: BGP settings for the gateway Required if enableBgp is true.
        :param custom_routes: Custom routes for the gateway.
        :param enable_bgp: Enable BGP for the gateway. Default: false
        :param enable_private_ip_address: Enable private IP address for the gateway. Default: false
        :param gateway_default_site: Default site for force tunneling.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param resource_group_id: Resource group ID where the Gateway will be created Optional - will use the subscription scope if not provided.
        :param vpn_client_configuration: VPN client configuration for point-to-site connections.
        :param vpn_gateway_generation: VPN gateway generation.
        :param vpn_type: VPN type for VPN gateways. Default: "RouteBased"
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(sku, dict):
            sku = VirtualNetworkGatewaySku(**sku)
        if isinstance(bgp_settings, dict):
            bgp_settings = VirtualNetworkGatewayBgpSettings(**bgp_settings)
        if isinstance(custom_routes, dict):
            custom_routes = VirtualNetworkGatewayCustomRoutes(**custom_routes)
        if isinstance(gateway_default_site, dict):
            gateway_default_site = VirtualNetworkGatewayDefaultSite(**gateway_default_site)
        if isinstance(vpn_client_configuration, dict):
            vpn_client_configuration = VirtualNetworkGatewayVpnClientConfiguration(**vpn_client_configuration)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__31804a308a19297e2343c8e2e9a11aa104036cbe33e614f00871aaadbb27a481)
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
            check_type(argname="argument gateway_type", value=gateway_type, expected_type=type_hints["gateway_type"])
            check_type(argname="argument ip_configurations", value=ip_configurations, expected_type=type_hints["ip_configurations"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument active_active", value=active_active, expected_type=type_hints["active_active"])
            check_type(argname="argument bgp_settings", value=bgp_settings, expected_type=type_hints["bgp_settings"])
            check_type(argname="argument custom_routes", value=custom_routes, expected_type=type_hints["custom_routes"])
            check_type(argname="argument enable_bgp", value=enable_bgp, expected_type=type_hints["enable_bgp"])
            check_type(argname="argument enable_private_ip_address", value=enable_private_ip_address, expected_type=type_hints["enable_private_ip_address"])
            check_type(argname="argument gateway_default_site", value=gateway_default_site, expected_type=type_hints["gateway_default_site"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument vpn_client_configuration", value=vpn_client_configuration, expected_type=type_hints["vpn_client_configuration"])
            check_type(argname="argument vpn_gateway_generation", value=vpn_gateway_generation, expected_type=type_hints["vpn_gateway_generation"])
            check_type(argname="argument vpn_type", value=vpn_type, expected_type=type_hints["vpn_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "gateway_type": gateway_type,
            "ip_configurations": ip_configurations,
            "sku": sku,
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
        if active_active is not None:
            self._values["active_active"] = active_active
        if bgp_settings is not None:
            self._values["bgp_settings"] = bgp_settings
        if custom_routes is not None:
            self._values["custom_routes"] = custom_routes
        if enable_bgp is not None:
            self._values["enable_bgp"] = enable_bgp
        if enable_private_ip_address is not None:
            self._values["enable_private_ip_address"] = enable_private_ip_address
        if gateway_default_site is not None:
            self._values["gateway_default_site"] = gateway_default_site
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if vpn_client_configuration is not None:
            self._values["vpn_client_configuration"] = vpn_client_configuration
        if vpn_gateway_generation is not None:
            self._values["vpn_gateway_generation"] = vpn_gateway_generation
        if vpn_type is not None:
            self._values["vpn_type"] = vpn_type

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
    def gateway_type(self) -> builtins.str:
        '''Gateway type Must be either "Vpn" or "ExpressRoute".'''
        result = self._values.get("gateway_type")
        assert result is not None, "Required property 'gateway_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ip_configurations(self) -> typing.List[VirtualNetworkGatewayIpConfiguration]:
        '''IP configurations for the gateway At least one IP configuration is required Two IP configurations are required for active-active mode.'''
        result = self._values.get("ip_configurations")
        assert result is not None, "Required property 'ip_configurations' is missing"
        return typing.cast(typing.List[VirtualNetworkGatewayIpConfiguration], result)

    @builtins.property
    def sku(self) -> "VirtualNetworkGatewaySku":
        '''SKU configuration for the gateway.'''
        result = self._values.get("sku")
        assert result is not None, "Required property 'sku' is missing"
        return typing.cast("VirtualNetworkGatewaySku", result)

    @builtins.property
    def active_active(self) -> typing.Optional[builtins.bool]:
        '''Enable active-active mode for the gateway Requires two IP configurations.

        :default: false
        '''
        result = self._values.get("active_active")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def bgp_settings(self) -> typing.Optional[VirtualNetworkGatewayBgpSettings]:
        '''BGP settings for the gateway Required if enableBgp is true.'''
        result = self._values.get("bgp_settings")
        return typing.cast(typing.Optional[VirtualNetworkGatewayBgpSettings], result)

    @builtins.property
    def custom_routes(self) -> typing.Optional[VirtualNetworkGatewayCustomRoutes]:
        '''Custom routes for the gateway.'''
        result = self._values.get("custom_routes")
        return typing.cast(typing.Optional[VirtualNetworkGatewayCustomRoutes], result)

    @builtins.property
    def enable_bgp(self) -> typing.Optional[builtins.bool]:
        '''Enable BGP for the gateway.

        :default: false
        '''
        result = self._values.get("enable_bgp")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_private_ip_address(self) -> typing.Optional[builtins.bool]:
        '''Enable private IP address for the gateway.

        :default: false
        '''
        result = self._values.get("enable_private_ip_address")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def gateway_default_site(self) -> typing.Optional[VirtualNetworkGatewayDefaultSite]:
        '''Default site for force tunneling.'''
        result = self._values.get("gateway_default_site")
        return typing.cast(typing.Optional[VirtualNetworkGatewayDefaultSite], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the Gateway will be created Optional - will use the subscription scope if not provided.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vpn_client_configuration(
        self,
    ) -> typing.Optional["VirtualNetworkGatewayVpnClientConfiguration"]:
        '''VPN client configuration for point-to-site connections.'''
        result = self._values.get("vpn_client_configuration")
        return typing.cast(typing.Optional["VirtualNetworkGatewayVpnClientConfiguration"], result)

    @builtins.property
    def vpn_gateway_generation(self) -> typing.Optional[builtins.str]:
        '''VPN gateway generation.

        Example::

            "Generation1", "Generation2"
        '''
        result = self._values.get("vpn_gateway_generation")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vpn_type(self) -> typing.Optional[builtins.str]:
        '''VPN type for VPN gateways.

        :default: "RouteBased"
        '''
        result = self._values.get("vpn_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewaySku",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "tier": "tier"},
)
class VirtualNetworkGatewaySku:
    def __init__(self, *, name: builtins.str, tier: builtins.str) -> None:
        '''SKU configuration for Virtual Network Gateway.

        :param name: Name of the SKU.
        :param tier: Tier of the SKU.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c5a7aa43f4d45b5fbd14051dd7df533b45155a68bb3ec1275b8e30435026dcdc)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tier", value=tier, expected_type=type_hints["tier"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "tier": tier,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of the SKU.

        Example::

            "Basic", "VpnGw1", "VpnGw2", "VpnGw3", "VpnGw4", "VpnGw5", "ErGw1AZ", "ErGw2AZ", "ErGw3AZ"
        '''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def tier(self) -> builtins.str:
        '''Tier of the SKU.

        Example::

            "Basic", "VpnGw1", "VpnGw2", "VpnGw3", "VpnGw4", "VpnGw5", "ErGw1AZ", "ErGw2AZ", "ErGw3AZ"
        '''
        result = self._values.get("tier")
        assert result is not None, "Required property 'tier' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewaySku(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayVpnClientAddressPool",
    jsii_struct_bases=[],
    name_mapping={"address_prefixes": "addressPrefixes"},
)
class VirtualNetworkGatewayVpnClientAddressPool:
    def __init__(self, *, address_prefixes: typing.Sequence[builtins.str]) -> None:
        '''VPN client address pool configuration.

        :param address_prefixes: List of address prefixes for VPN client connections.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7684da3ab7a55202b4d2803723b219c04cbe5530e746c0b37fd9cb90034bff9e)
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
        }

    @builtins.property
    def address_prefixes(self) -> typing.List[builtins.str]:
        '''List of address prefixes for VPN client connections.'''
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayVpnClientAddressPool(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgateway.VirtualNetworkGatewayVpnClientConfiguration",
    jsii_struct_bases=[],
    name_mapping={
        "radius_server_address": "radiusServerAddress",
        "radius_server_secret": "radiusServerSecret",
        "vpn_client_address_pool": "vpnClientAddressPool",
        "vpn_client_protocols": "vpnClientProtocols",
        "vpn_client_revoked_certificates": "vpnClientRevokedCertificates",
        "vpn_client_root_certificates": "vpnClientRootCertificates",
    },
)
class VirtualNetworkGatewayVpnClientConfiguration:
    def __init__(
        self,
        *,
        radius_server_address: typing.Optional[builtins.str] = None,
        radius_server_secret: typing.Optional[builtins.str] = None,
        vpn_client_address_pool: typing.Optional[typing.Union[VirtualNetworkGatewayVpnClientAddressPool, typing.Dict[builtins.str, typing.Any]]] = None,
        vpn_client_protocols: typing.Optional[typing.Sequence[builtins.str]] = None,
        vpn_client_revoked_certificates: typing.Optional[typing.Sequence[typing.Any]] = None,
        vpn_client_root_certificates: typing.Optional[typing.Sequence[typing.Any]] = None,
    ) -> None:
        '''VPN client configuration for point-to-site connections.

        :param radius_server_address: Radius server address.
        :param radius_server_secret: Radius server secret.
        :param vpn_client_address_pool: VPN client address pool.
        :param vpn_client_protocols: VPN client protocols.
        :param vpn_client_revoked_certificates: VPN client revoked certificates.
        :param vpn_client_root_certificates: VPN client root certificates.
        '''
        if isinstance(vpn_client_address_pool, dict):
            vpn_client_address_pool = VirtualNetworkGatewayVpnClientAddressPool(**vpn_client_address_pool)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0fea2d70c347d3f152aff0f4e78c56d297e9af79b0427f0207ac0240f65a1fba)
            check_type(argname="argument radius_server_address", value=radius_server_address, expected_type=type_hints["radius_server_address"])
            check_type(argname="argument radius_server_secret", value=radius_server_secret, expected_type=type_hints["radius_server_secret"])
            check_type(argname="argument vpn_client_address_pool", value=vpn_client_address_pool, expected_type=type_hints["vpn_client_address_pool"])
            check_type(argname="argument vpn_client_protocols", value=vpn_client_protocols, expected_type=type_hints["vpn_client_protocols"])
            check_type(argname="argument vpn_client_revoked_certificates", value=vpn_client_revoked_certificates, expected_type=type_hints["vpn_client_revoked_certificates"])
            check_type(argname="argument vpn_client_root_certificates", value=vpn_client_root_certificates, expected_type=type_hints["vpn_client_root_certificates"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if radius_server_address is not None:
            self._values["radius_server_address"] = radius_server_address
        if radius_server_secret is not None:
            self._values["radius_server_secret"] = radius_server_secret
        if vpn_client_address_pool is not None:
            self._values["vpn_client_address_pool"] = vpn_client_address_pool
        if vpn_client_protocols is not None:
            self._values["vpn_client_protocols"] = vpn_client_protocols
        if vpn_client_revoked_certificates is not None:
            self._values["vpn_client_revoked_certificates"] = vpn_client_revoked_certificates
        if vpn_client_root_certificates is not None:
            self._values["vpn_client_root_certificates"] = vpn_client_root_certificates

    @builtins.property
    def radius_server_address(self) -> typing.Optional[builtins.str]:
        '''Radius server address.'''
        result = self._values.get("radius_server_address")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def radius_server_secret(self) -> typing.Optional[builtins.str]:
        '''Radius server secret.'''
        result = self._values.get("radius_server_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vpn_client_address_pool(
        self,
    ) -> typing.Optional[VirtualNetworkGatewayVpnClientAddressPool]:
        '''VPN client address pool.'''
        result = self._values.get("vpn_client_address_pool")
        return typing.cast(typing.Optional[VirtualNetworkGatewayVpnClientAddressPool], result)

    @builtins.property
    def vpn_client_protocols(self) -> typing.Optional[typing.List[builtins.str]]:
        '''VPN client protocols.

        Example::

            ["IkeV2", "SSTP", "OpenVPN"]
        '''
        result = self._values.get("vpn_client_protocols")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def vpn_client_revoked_certificates(
        self,
    ) -> typing.Optional[typing.List[typing.Any]]:
        '''VPN client revoked certificates.'''
        result = self._values.get("vpn_client_revoked_certificates")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    @builtins.property
    def vpn_client_root_certificates(self) -> typing.Optional[typing.List[typing.Any]]:
        '''VPN client root certificates.'''
        result = self._values.get("vpn_client_root_certificates")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayVpnClientConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "VirtualNetworkGateway",
    "VirtualNetworkGatewayBgpSettings",
    "VirtualNetworkGatewayCustomRoutes",
    "VirtualNetworkGatewayDefaultSite",
    "VirtualNetworkGatewayIpConfiguration",
    "VirtualNetworkGatewayProps",
    "VirtualNetworkGatewaySku",
    "VirtualNetworkGatewayVpnClientAddressPool",
    "VirtualNetworkGatewayVpnClientConfiguration",
]

publication.publish()

def _typecheckingstub__f1b2bbccd26a32280967875530d8991dc124465acd35f776e522e52cb07a160b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    gateway_type: builtins.str,
    ip_configurations: typing.Sequence[typing.Union[VirtualNetworkGatewayIpConfiguration, typing.Dict[builtins.str, typing.Any]]],
    sku: typing.Union[VirtualNetworkGatewaySku, typing.Dict[builtins.str, typing.Any]],
    active_active: typing.Optional[builtins.bool] = None,
    bgp_settings: typing.Optional[typing.Union[VirtualNetworkGatewayBgpSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    custom_routes: typing.Optional[typing.Union[VirtualNetworkGatewayCustomRoutes, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_bgp: typing.Optional[builtins.bool] = None,
    enable_private_ip_address: typing.Optional[builtins.bool] = None,
    gateway_default_site: typing.Optional[typing.Union[VirtualNetworkGatewayDefaultSite, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    vpn_client_configuration: typing.Optional[typing.Union[VirtualNetworkGatewayVpnClientConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    vpn_gateway_generation: typing.Optional[builtins.str] = None,
    vpn_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__61db15ff5702cb0392f1c8b13fa5bf023b9d5f8c5302799e43469fca20c17159(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b7200d420e00320d25d9438de4eb7ce05c77ea62b3f519612221a00bb6e3aa38(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26342d14bf1ec0cf3f04e99ca1479b49fd6d31f14b37c300152da564f3ce73d7(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8ea3f6166ad07f87ec570ff7cc0ed9d8aa229d2877b4b20aa731f2a7fa651f92(
    *,
    asn: typing.Optional[jsii.Number] = None,
    bgp_peering_address: typing.Optional[builtins.str] = None,
    bgp_peering_addresses: typing.Optional[typing.Sequence[typing.Any]] = None,
    peer_weight: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ebd2b6ce5d9dc44872044222122fec46657cc5ebe19c037a702ed789084b9bb(
    *,
    address_prefixes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__32c58f1cd50b4b890f8842296b4635b19ca5474bfc162909daff33ca05a85a40(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ca4e5b564e4aa6f3c8152f63b855de08ce5420893411b4e9c2d8bb38c795b4fb(
    *,
    name: builtins.str,
    public_ip_address_id: builtins.str,
    subnet_id: builtins.str,
    private_ip_allocation_method: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31804a308a19297e2343c8e2e9a11aa104036cbe33e614f00871aaadbb27a481(
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
    gateway_type: builtins.str,
    ip_configurations: typing.Sequence[typing.Union[VirtualNetworkGatewayIpConfiguration, typing.Dict[builtins.str, typing.Any]]],
    sku: typing.Union[VirtualNetworkGatewaySku, typing.Dict[builtins.str, typing.Any]],
    active_active: typing.Optional[builtins.bool] = None,
    bgp_settings: typing.Optional[typing.Union[VirtualNetworkGatewayBgpSettings, typing.Dict[builtins.str, typing.Any]]] = None,
    custom_routes: typing.Optional[typing.Union[VirtualNetworkGatewayCustomRoutes, typing.Dict[builtins.str, typing.Any]]] = None,
    enable_bgp: typing.Optional[builtins.bool] = None,
    enable_private_ip_address: typing.Optional[builtins.bool] = None,
    gateway_default_site: typing.Optional[typing.Union[VirtualNetworkGatewayDefaultSite, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    vpn_client_configuration: typing.Optional[typing.Union[VirtualNetworkGatewayVpnClientConfiguration, typing.Dict[builtins.str, typing.Any]]] = None,
    vpn_gateway_generation: typing.Optional[builtins.str] = None,
    vpn_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c5a7aa43f4d45b5fbd14051dd7df533b45155a68bb3ec1275b8e30435026dcdc(
    *,
    name: builtins.str,
    tier: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7684da3ab7a55202b4d2803723b219c04cbe5530e746c0b37fd9cb90034bff9e(
    *,
    address_prefixes: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0fea2d70c347d3f152aff0f4e78c56d297e9af79b0427f0207ac0240f65a1fba(
    *,
    radius_server_address: typing.Optional[builtins.str] = None,
    radius_server_secret: typing.Optional[builtins.str] = None,
    vpn_client_address_pool: typing.Optional[typing.Union[VirtualNetworkGatewayVpnClientAddressPool, typing.Dict[builtins.str, typing.Any]]] = None,
    vpn_client_protocols: typing.Optional[typing.Sequence[builtins.str]] = None,
    vpn_client_revoked_certificates: typing.Optional[typing.Sequence[typing.Any]] = None,
    vpn_client_root_certificates: typing.Optional[typing.Sequence[typing.Any]] = None,
) -> None:
    """Type checking stubs"""
    pass
