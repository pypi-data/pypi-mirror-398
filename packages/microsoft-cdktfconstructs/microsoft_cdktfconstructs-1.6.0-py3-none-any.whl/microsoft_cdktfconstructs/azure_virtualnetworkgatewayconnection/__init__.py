r'''
# Azure Virtual Network Gateway Connection Construct

This construct provides a CDK for Terraform (CDKTF) implementation of Azure Virtual Network Gateway Connection using the AzapiResource framework.

## Overview

Azure Virtual Network Gateway Connection establishes connectivity between Virtual Network Gateways and other networking endpoints. It supports three connection types:

* **IPsec (Site-to-Site)**: Connect VPN Gateway to on-premises networks via Local Network Gateway
* **VNet-to-VNet**: Connect two Azure virtual networks via their VPN Gateways
* **ExpressRoute**: Connect ExpressRoute Gateway to ExpressRoute circuits for private connectivity

## Features

* ✅ Automatic latest API version resolution
* ✅ Explicit version pinning for stability
* ✅ Schema-driven validation and transformation
* ✅ Type-safe discriminated unions for connection types
* ✅ Full backward compatibility
* ✅ JSII compliance for multi-language support
* ✅ Comprehensive TypeScript type definitions

## Supported API Versions

* `2024-01-01` (Active)
* `2024-05-01` (Active, Latest - Default)

## Installation

```bash
npm install @cdktf-constructs/azure-virtualnetworkgatewayconnection
```

## Basic Usage

### Site-to-Site (IPsec) Connection

```python
import { VirtualNetworkGatewayConnection } from '@cdktf-constructs/azure-virtualnetworkgatewayconnection';
import { ResourceGroup } from '@cdktf-constructs/azure-resourcegroup';

// Create resource group
const resourceGroup = new ResourceGroup(this, 'rg', {
  name: 'rg-network',
  location: 'eastus',
});

// Create Site-to-Site VPN connection
const s2sConnection = new VirtualNetworkGatewayConnection(this, 's2s-connection', {
  name: 'conn-onprem',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  connectionType: 'IPsec',
  virtualNetworkGateway1: {
    id: vpnGateway.id  // Your VPN Gateway
  },
  localNetworkGateway2: {
    id: localGateway.id  // Your Local Network Gateway
  },
  sharedKey: 'YourSecureSharedKey123!',
  tags: {
    environment: 'production'
  }
});
```

### VNet-to-VNet Connection

```python
const vnetConnection = new VirtualNetworkGatewayConnection(this, 'vnet-connection', {
  name: 'conn-vnet-to-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  connectionType: 'Vnet2Vnet',
  virtualNetworkGateway1: {
    id: vpnGateway1.id
  },
  virtualNetworkGateway2: {
    id: vpnGateway2.id
  },
  sharedKey: 'YourSecureSharedKey123!',
  enableBgp: true,
  tags: {
    environment: 'production',
    purpose: 'vnet-peering'
  }
});
```

### ExpressRoute Connection

```python
const erConnection = new VirtualNetworkGatewayConnection(this, 'er-connection', {
  name: 'conn-expressroute',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  connectionType: 'ExpressRoute',
  virtualNetworkGateway1: {
    id: erGateway.id
  },
  peer: {
    id: expressRouteCircuit.id
  },
  authorizationKey: 'optional-if-cross-subscription',
  tags: {
    environment: 'production',
    purpose: 'expressroute'
  }
});
```

## Advanced Configuration

### IPsec Connection with Custom Policies

```python
const customConnection = new VirtualNetworkGatewayConnection(this, 'custom-ipsec', {
  name: 'conn-custom-ipsec',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  connectionType: 'IPsec',
  virtualNetworkGateway1: {
    id: vpnGateway.id
  },
  localNetworkGateway2: {
    id: localGateway.id
  },
  sharedKey: 'YourSecureSharedKey123!',
  connectionProtocol: 'IKEv2',
  ipsecPolicies: [{
    dhGroup: 'DHGroup14',
    ikeEncryption: 'AES256',
    ikeIntegrity: 'SHA256',
    ipsecEncryption: 'AES256',
    ipsecIntegrity: 'SHA256',
    pfsGroup: 'PFS2048',
    saLifeTimeSeconds: 3600,
    saDataSizeKilobytes: 102400000
  }],
  usePolicyBasedTrafficSelectors: true,
  dpdTimeoutSeconds: 45
});
```

### Connection with BGP and Routing Configuration

```python
const bgpConnection = new VirtualNetworkGatewayConnection(this, 'bgp-connection', {
  name: 'conn-bgp',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  connectionType: 'Vnet2Vnet',
  virtualNetworkGateway1: {
    id: vpnGateway1.id
  },
  virtualNetworkGateway2: {
    id: vpnGateway2.id
  },
  sharedKey: 'YourSecureSharedKey123!',
  enableBgp: true,
  routingWeight: 10,
  connectionMode: 'Default'
});
```

### Connection with NAT Rules

```python
const natConnection = new VirtualNetworkGatewayConnection(this, 'nat-connection', {
  name: 'conn-nat',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  connectionType: 'IPsec',
  virtualNetworkGateway1: {
    id: vpnGateway.id
  },
  localNetworkGateway2: {
    id: localGateway.id
  },
  sharedKey: 'YourSecureSharedKey123!',
  egressNatRules: [{
    id: `${vpnGateway.id}/natRules/egress-rule`
  }],
  ingressNatRules: [{
    id: `${vpnGateway.id}/natRules/ingress-rule`
  }]
});
```

## Configuration Options

### VirtualNetworkGatewayConnectionProps

#### Base Properties (All Connection Types)

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name of the connection |
| `location` | string | Yes | - | Azure region |
| `resourceGroupId` | string | Yes | - | Resource group ID |
| `connectionType` | "IPsec" | "Vnet2Vnet" | "ExpressRoute" | Yes | - | Type of connection |
| `virtualNetworkGateway1` | GatewayReference | Yes | - | First virtual network gateway |
| `connectionProtocol` | "IKEv2" | "IKEv1" | No | "IKEv2" | Connection protocol |
| `enableBgp` | boolean | No | false | Enable BGP |
| `routingWeight` | number | No | - | Routing weight |
| `dpdTimeoutSeconds` | number | No | - | DPD timeout in seconds |
| `ipsecPolicies` | IpsecPolicy[] | No | - | Custom IPsec policies |
| `usePolicyBasedTrafficSelectors` | boolean | No | false | Use policy-based traffic selectors |
| `connectionMode` | "Default" | "ResponderOnly" | "InitiatorOnly" | No | "Default" | Connection mode |
| `egressNatRules` | NatRuleReference[] | No | - | Egress NAT rules |
| `ingressNatRules` | NatRuleReference[] | No | - | Ingress NAT rules |
| `tags` | Record<string, string> | No | {} | Resource tags |
| `apiVersion` | string | No | "2024-05-01" | API version to use |
| `ignoreChanges` | string[] | No | [] | Properties to ignore |

#### IPsec Connection (Site-to-Site) Specific

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `localNetworkGateway2` | GatewayReference | Yes | Local network gateway reference |
| `sharedKey` | string | Yes | Shared key for the connection |

#### Vnet2Vnet Connection Specific

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `virtualNetworkGateway2` | GatewayReference | Yes | Second virtual network gateway |
| `sharedKey` | string | Yes | Shared key for the connection |

#### ExpressRoute Connection Specific

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `peer` | PeerReference | Yes | ExpressRoute circuit reference |
| `authorizationKey` | string | No | Authorization key (for cross-subscription) |

### IPsec Policy Configuration

```python
interface IpsecPolicy {
  dhGroup: string;              // DHGroup14, DHGroup2048, ECP256, ECP384
  ikeEncryption: string;        // AES128, AES192, AES256, GCMAES128, GCMAES256
  ikeIntegrity: string;         // SHA256, SHA384, GCMAES128, GCMAES256
  ipsecEncryption: string;      // AES128, AES192, AES256, GCMAES128, GCMAES192, GCMAES256
  ipsecIntegrity: string;       // SHA256, GCMAES128, GCMAES192, GCMAES256
  pfsGroup: string;             // None, PFS1, PFS2, PFS2048, ECP256, ECP384, PFS24, PFS14, PFSMM
  saLifeTimeSeconds: number;    // e.g., 3600
  saDataSizeKilobytes: number;  // e.g., 102400000
}
```

## Important Notes

### Connection Type Requirements

#### IPsec (Site-to-Site)

* Requires a VPN Gateway (`gatewayType: "Vpn"`)
* Requires a Local Network Gateway representing on-premises network
* Requires a shared key
* Typically uses IKEv2 protocol
* Can use custom IPsec policies

#### VNet-to-VNet

* Requires two VPN Gateways in different virtual networks
* Both gateways must be route-based VPN gateways
* Requires a shared key (must match on both sides)
* Can enable BGP for dynamic routing
* Faster than VNet peering for encrypted traffic

#### ExpressRoute

* Requires an ExpressRoute Gateway (`gatewayType: "ExpressRoute"`)
* Requires a provisioned ExpressRoute circuit
* Optional authorization key for cross-subscription scenarios
* Does not use shared keys or IPsec
* Provides private, dedicated connectivity

### Deployment Time

* **Connection Provisioning**: Typically 5-10 minutes
* **Gateway Provisioning** (prerequisite): 30-45 minutes per gateway
* Plan accordingly in CI/CD pipelines

### Shared Keys

* Must be strong and unique
* Must match on both ends for IPsec and VNet-to-VNet
* Store securely (use Azure Key Vault in production)
* Can be rotated without recreating the connection

### BGP Configuration

* Available for IPsec and VNet-to-VNet connections
* Required for ExpressRoute connections
* Enables dynamic routing and automatic failover
* ASN must be coordinated between endpoints

### Connection Modes

* **Default**: Standard bidirectional connection
* **ResponderOnly**: Connection only accepts incoming requests
* **InitiatorOnly**: Connection only initiates outgoing requests
* Useful for specific security requirements

## Outputs

The construct provides the following outputs:

```python
connection.id              // Connection resource ID
connection.name            // Connection name
connection.location        // Connection location
connection.resourceId      // Alias for id
connection.subscriptionId  // Extracted subscription ID
```

## API Version Support

To use a specific API version:

```python
const connection = new VirtualNetworkGatewayConnection(this, 'connection', {
  apiVersion: '2024-01-01',
  // ... other properties
});
```

## Related Resources

* [Azure Virtual Network Gateway](../azure-virtualnetworkgateway)
* [Azure Resource Group](../azure-resourcegroup)
* [Azure Virtual Network](../azure-virtualnetwork)

## Azure Documentation

* [VPN Gateway Connections Overview](https://learn.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-about-vpn-gateway-settings#connection)
* [Site-to-Site Connections](https://learn.microsoft.com/en-us/azure/vpn-gateway/tutorial-site-to-site-portal)
* [VNet-to-VNet Connections](https://learn.microsoft.com/en-us/azure/vpn-gateway/vpn-gateway-howto-vnet-vnet-resource-manager-portal)
* [ExpressRoute Connections](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-howto-linkvnet-portal-resource-manager)
* [IPsec/IKE Policy](https://learn.microsoft.com/en-us/azure/vpn-gateway/ipsec-ike-policy-howto)

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


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgatewayconnection.GatewayReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class GatewayReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Reference to a Virtual Network Gateway.

        :param id: Resource ID of the virtual network gateway.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b3e42a46a89f704f9bf7d4d07d3e57211a7f3c5ea0a549c2742cfbcb1b76c3eb)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Resource ID of the virtual network gateway.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "GatewayReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgatewayconnection.IpsecPolicy",
    jsii_struct_bases=[],
    name_mapping={
        "dh_group": "dhGroup",
        "ike_encryption": "ikeEncryption",
        "ike_integrity": "ikeIntegrity",
        "ipsec_encryption": "ipsecEncryption",
        "ipsec_integrity": "ipsecIntegrity",
        "pfs_group": "pfsGroup",
        "sa_data_size_kilobytes": "saDataSizeKilobytes",
        "sa_life_time_seconds": "saLifeTimeSeconds",
    },
)
class IpsecPolicy:
    def __init__(
        self,
        *,
        dh_group: builtins.str,
        ike_encryption: builtins.str,
        ike_integrity: builtins.str,
        ipsec_encryption: builtins.str,
        ipsec_integrity: builtins.str,
        pfs_group: builtins.str,
        sa_data_size_kilobytes: jsii.Number,
        sa_life_time_seconds: jsii.Number,
    ) -> None:
        '''IPsec policy configuration.

        :param dh_group: DH Group for IKE Phase 1.
        :param ike_encryption: IKE encryption algorithm.
        :param ike_integrity: IKE integrity algorithm.
        :param ipsec_encryption: IPsec encryption algorithm.
        :param ipsec_integrity: IPsec integrity algorithm.
        :param pfs_group: PFS Group for IKE Phase 2.
        :param sa_data_size_kilobytes: SA data size in kilobytes.
        :param sa_life_time_seconds: SA lifetime in seconds.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48a1a9023babbe0ff91a428bcdf27881b956ea99d3d4faf5abc4d7fecb005574)
            check_type(argname="argument dh_group", value=dh_group, expected_type=type_hints["dh_group"])
            check_type(argname="argument ike_encryption", value=ike_encryption, expected_type=type_hints["ike_encryption"])
            check_type(argname="argument ike_integrity", value=ike_integrity, expected_type=type_hints["ike_integrity"])
            check_type(argname="argument ipsec_encryption", value=ipsec_encryption, expected_type=type_hints["ipsec_encryption"])
            check_type(argname="argument ipsec_integrity", value=ipsec_integrity, expected_type=type_hints["ipsec_integrity"])
            check_type(argname="argument pfs_group", value=pfs_group, expected_type=type_hints["pfs_group"])
            check_type(argname="argument sa_data_size_kilobytes", value=sa_data_size_kilobytes, expected_type=type_hints["sa_data_size_kilobytes"])
            check_type(argname="argument sa_life_time_seconds", value=sa_life_time_seconds, expected_type=type_hints["sa_life_time_seconds"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dh_group": dh_group,
            "ike_encryption": ike_encryption,
            "ike_integrity": ike_integrity,
            "ipsec_encryption": ipsec_encryption,
            "ipsec_integrity": ipsec_integrity,
            "pfs_group": pfs_group,
            "sa_data_size_kilobytes": sa_data_size_kilobytes,
            "sa_life_time_seconds": sa_life_time_seconds,
        }

    @builtins.property
    def dh_group(self) -> builtins.str:
        '''DH Group for IKE Phase 1.

        Example::

            "DHGroup14", "DHGroup2048", "ECP256", "ECP384"
        '''
        result = self._values.get("dh_group")
        assert result is not None, "Required property 'dh_group' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ike_encryption(self) -> builtins.str:
        '''IKE encryption algorithm.

        Example::

            "AES128", "AES192", "AES256", "GCMAES128", "GCMAES256"
        '''
        result = self._values.get("ike_encryption")
        assert result is not None, "Required property 'ike_encryption' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ike_integrity(self) -> builtins.str:
        '''IKE integrity algorithm.

        Example::

            "SHA256", "SHA384", "GCMAES128", "GCMAES256"
        '''
        result = self._values.get("ike_integrity")
        assert result is not None, "Required property 'ike_integrity' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ipsec_encryption(self) -> builtins.str:
        '''IPsec encryption algorithm.

        Example::

            "AES128", "AES192", "AES256", "GCMAES128", "GCMAES192", "GCMAES256"
        '''
        result = self._values.get("ipsec_encryption")
        assert result is not None, "Required property 'ipsec_encryption' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ipsec_integrity(self) -> builtins.str:
        '''IPsec integrity algorithm.

        Example::

            "SHA256", "GCMAES128", "GCMAES192", "GCMAES256"
        '''
        result = self._values.get("ipsec_integrity")
        assert result is not None, "Required property 'ipsec_integrity' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def pfs_group(self) -> builtins.str:
        '''PFS Group for IKE Phase 2.

        Example::

            "None", "PFS1", "PFS2", "PFS2048", "ECP256", "ECP384", "PFS24", "PFS14", "PFSMM"
        '''
        result = self._values.get("pfs_group")
        assert result is not None, "Required property 'pfs_group' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def sa_data_size_kilobytes(self) -> jsii.Number:
        '''SA data size in kilobytes.

        Example::

            102400000
        '''
        result = self._values.get("sa_data_size_kilobytes")
        assert result is not None, "Required property 'sa_data_size_kilobytes' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def sa_life_time_seconds(self) -> jsii.Number:
        '''SA lifetime in seconds.

        Example::

            3600
        '''
        result = self._values.get("sa_life_time_seconds")
        assert result is not None, "Required property 'sa_life_time_seconds' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpsecPolicy(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgatewayconnection.NatRuleReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class NatRuleReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''NAT rule reference.

        :param id: Resource ID of the NAT rule.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e987169fed4c3a61696b68e6fa91b60d6ddb0c54019838f65ed5d0b78bdb6e53)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Resource ID of the NAT rule.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NatRuleReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgatewayconnection.PeerReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class PeerReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Reference to an ExpressRoute circuit peer.

        :param id: Resource ID of the ExpressRoute circuit.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f951db7790af9fda3ccd18eaae249af1bbcf573140d9f0e1823afb6e97620485)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Resource ID of the ExpressRoute circuit.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PeerReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class VirtualNetworkGatewayConnection(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgatewayconnection.VirtualNetworkGatewayConnection",
):
    '''Azure Virtual Network Gateway Connection implementation.

    This class provides a single, version-aware implementation that replaces
    version-specific Virtual Network Gateway Connection classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Virtual Network Gateway Connections establish connectivity between Virtual Network Gateways
    and other networking endpoints:

    - IPsec: Site-to-Site VPN connections to on-premises networks
    - Vnet2Vnet: VNet-to-VNet connections between Azure virtual networks
    - ExpressRoute: Private connections to Azure via ExpressRoute circuits

    Example::

        // IPsec Connection with Custom IPsec Policies:
        const customConnection = new VirtualNetworkGatewayConnection(this, "customConnection", {
          name: "my-custom-connection",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          connectionType: "IPsec",
          virtualNetworkGateway1: { id: vpnGateway.id },
          localNetworkGateway2: { id: localGateway.id },
          sharedKey: "mySecureSharedKey123!",
          connectionProtocol: "IKEv2",
          ipsecPolicies: [{
            dhGroup: "DHGroup14",
            ikeEncryption: "AES256",
            ikeIntegrity: "SHA256",
            ipsecEncryption: "AES256",
            ipsecIntegrity: "SHA256",
            pfsGroup: "PFS2048",
            saLifeTimeSeconds: 3600,
            saDataSizeKilobytes: 102400000
          }],
          usePolicyBasedTrafficSelectors: true
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        connection_type: builtins.str,
        resource_group_id: builtins.str,
        virtual_network_gateway1: typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]],
        authorization_key: typing.Optional[builtins.str] = None,
        connection_mode: typing.Optional[builtins.str] = None,
        connection_protocol: typing.Optional[builtins.str] = None,
        dpd_timeout_seconds: typing.Optional[jsii.Number] = None,
        egress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
        enable_bgp: typing.Optional[builtins.bool] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        ingress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
        ipsec_policies: typing.Optional[typing.Sequence[typing.Union[IpsecPolicy, typing.Dict[builtins.str, typing.Any]]]] = None,
        local_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
        peer: typing.Optional[typing.Union[PeerReference, typing.Dict[builtins.str, typing.Any]]] = None,
        routing_weight: typing.Optional[jsii.Number] = None,
        shared_key: typing.Optional[builtins.str] = None,
        use_policy_based_traffic_selectors: typing.Optional[builtins.bool] = None,
        virtual_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Creates a new Azure Virtual Network Gateway Connection using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Virtual Network Gateway Connection implementations.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param connection_type: Connection type Must be "IPsec", "Vnet2Vnet", or "ExpressRoute".
        :param resource_group_id: Resource group ID where the connection will be created.
        :param virtual_network_gateway1: Reference to the first virtual network gateway Required for all connection types.
        :param authorization_key: Authorization key for the ExpressRoute circuit Optional - for cross-subscription ExpressRoute connections.
        :param connection_mode: Connection mode. Default: "Default"
        :param connection_protocol: Connection protocol to use. Default: "IKEv2"
        :param dpd_timeout_seconds: DPD timeout in seconds.
        :param egress_nat_rules: Egress NAT rules.
        :param enable_bgp: Enable BGP for the connection. Default: false
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param ingress_nat_rules: Ingress NAT rules.
        :param ipsec_policies: Custom IPsec policies.
        :param local_network_gateway2: Reference to the local network gateway Required for IPsec connections only.
        :param peer: Reference to the ExpressRoute circuit Required for ExpressRoute connections only.
        :param routing_weight: Routing weight for the connection.
        :param shared_key: Shared key for the connection Required for IPsec and Vnet2Vnet connections.
        :param use_policy_based_traffic_selectors: Enable policy-based traffic selectors. Default: false
        :param virtual_network_gateway2: Reference to the second virtual network gateway Required for Vnet2Vnet connections only.
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
            type_hints = typing.get_type_hints(_typecheckingstub__4ec8b67425ce1a07c13ad80ba0ba64b66156d199acdef2b96000710e0e70cfb2)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VirtualNetworkGatewayConnectionProps(
            connection_type=connection_type,
            resource_group_id=resource_group_id,
            virtual_network_gateway1=virtual_network_gateway1,
            authorization_key=authorization_key,
            connection_mode=connection_mode,
            connection_protocol=connection_protocol,
            dpd_timeout_seconds=dpd_timeout_seconds,
            egress_nat_rules=egress_nat_rules,
            enable_bgp=enable_bgp,
            ignore_changes=ignore_changes,
            ingress_nat_rules=ingress_nat_rules,
            ipsec_policies=ipsec_policies,
            local_network_gateway2=local_network_gateway2,
            peer=peer,
            routing_weight=routing_weight,
            shared_key=shared_key,
            use_policy_based_traffic_selectors=use_policy_based_traffic_selectors,
            virtual_network_gateway2=virtual_network_gateway2,
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
        '''Add a tag to the Virtual Network Gateway Connection Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8023058abef2eee43191d9491a9ee407770f2d0120af347b43bdfd7f3704840b)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "addTag", [key, value]))

    @jsii.member(jsii_name="apiSchema")
    def _api_schema(self) -> _ApiSchema_5ce0490e:
        '''Gets the API schema for the resolved version Uses the framework's schema resolution to get the appropriate schema.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call Transforms the input properties into the JSON format expected by Azure REST API Handles type-specific properties based on connectionType.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3823f93c07bbe2b869b530760ef7a1f94e3c24dac16c8415180ec28df1da3c96)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Virtual Network Gateway Connection Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cd01f37589cbca66cf40488d0d59a94de2e9f9dc3afa4f99e12590b64e2e0252)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Virtual Network Gateway Connections.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Network Gateway Connections.'''
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
    def props(self) -> "VirtualNetworkGatewayConnectionProps":
        '''The input properties for this Virtual Network Gateway Connection instance.'''
        return typing.cast("VirtualNetworkGatewayConnectionProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property to match original interface.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> builtins.str:
        '''Get the subscription ID from the Virtual Network Gateway Connection ID Extracts the subscription ID from the Azure resource ID format.'''
        return typing.cast(builtins.str, jsii.get(self, "subscriptionId"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkgatewayconnection.VirtualNetworkGatewayConnectionProps",
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
        "connection_type": "connectionType",
        "resource_group_id": "resourceGroupId",
        "virtual_network_gateway1": "virtualNetworkGateway1",
        "authorization_key": "authorizationKey",
        "connection_mode": "connectionMode",
        "connection_protocol": "connectionProtocol",
        "dpd_timeout_seconds": "dpdTimeoutSeconds",
        "egress_nat_rules": "egressNatRules",
        "enable_bgp": "enableBgp",
        "ignore_changes": "ignoreChanges",
        "ingress_nat_rules": "ingressNatRules",
        "ipsec_policies": "ipsecPolicies",
        "local_network_gateway2": "localNetworkGateway2",
        "peer": "peer",
        "routing_weight": "routingWeight",
        "shared_key": "sharedKey",
        "use_policy_based_traffic_selectors": "usePolicyBasedTrafficSelectors",
        "virtual_network_gateway2": "virtualNetworkGateway2",
    },
)
class VirtualNetworkGatewayConnectionProps(_AzapiResourceProps_141a2340):
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
        connection_type: builtins.str,
        resource_group_id: builtins.str,
        virtual_network_gateway1: typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]],
        authorization_key: typing.Optional[builtins.str] = None,
        connection_mode: typing.Optional[builtins.str] = None,
        connection_protocol: typing.Optional[builtins.str] = None,
        dpd_timeout_seconds: typing.Optional[jsii.Number] = None,
        egress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
        enable_bgp: typing.Optional[builtins.bool] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        ingress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
        ipsec_policies: typing.Optional[typing.Sequence[typing.Union[IpsecPolicy, typing.Dict[builtins.str, typing.Any]]]] = None,
        local_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
        peer: typing.Optional[typing.Union[PeerReference, typing.Dict[builtins.str, typing.Any]]] = None,
        routing_weight: typing.Optional[jsii.Number] = None,
        shared_key: typing.Optional[builtins.str] = None,
        use_policy_based_traffic_selectors: typing.Optional[builtins.bool] = None,
        virtual_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Gateway Connection.

        Supports three connection types: IPsec (Site-to-Site), VNet-to-VNet, and ExpressRoute

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
        :param connection_type: Connection type Must be "IPsec", "Vnet2Vnet", or "ExpressRoute".
        :param resource_group_id: Resource group ID where the connection will be created.
        :param virtual_network_gateway1: Reference to the first virtual network gateway Required for all connection types.
        :param authorization_key: Authorization key for the ExpressRoute circuit Optional - for cross-subscription ExpressRoute connections.
        :param connection_mode: Connection mode. Default: "Default"
        :param connection_protocol: Connection protocol to use. Default: "IKEv2"
        :param dpd_timeout_seconds: DPD timeout in seconds.
        :param egress_nat_rules: Egress NAT rules.
        :param enable_bgp: Enable BGP for the connection. Default: false
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param ingress_nat_rules: Ingress NAT rules.
        :param ipsec_policies: Custom IPsec policies.
        :param local_network_gateway2: Reference to the local network gateway Required for IPsec connections only.
        :param peer: Reference to the ExpressRoute circuit Required for ExpressRoute connections only.
        :param routing_weight: Routing weight for the connection.
        :param shared_key: Shared key for the connection Required for IPsec and Vnet2Vnet connections.
        :param use_policy_based_traffic_selectors: Enable policy-based traffic selectors. Default: false
        :param virtual_network_gateway2: Reference to the second virtual network gateway Required for Vnet2Vnet connections only.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(virtual_network_gateway1, dict):
            virtual_network_gateway1 = GatewayReference(**virtual_network_gateway1)
        if isinstance(local_network_gateway2, dict):
            local_network_gateway2 = GatewayReference(**local_network_gateway2)
        if isinstance(peer, dict):
            peer = PeerReference(**peer)
        if isinstance(virtual_network_gateway2, dict):
            virtual_network_gateway2 = GatewayReference(**virtual_network_gateway2)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5faabf10103c78fb68094359eba693b531cba47bbbb8002f03e5f2809da73e0a)
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
            check_type(argname="argument connection_type", value=connection_type, expected_type=type_hints["connection_type"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument virtual_network_gateway1", value=virtual_network_gateway1, expected_type=type_hints["virtual_network_gateway1"])
            check_type(argname="argument authorization_key", value=authorization_key, expected_type=type_hints["authorization_key"])
            check_type(argname="argument connection_mode", value=connection_mode, expected_type=type_hints["connection_mode"])
            check_type(argname="argument connection_protocol", value=connection_protocol, expected_type=type_hints["connection_protocol"])
            check_type(argname="argument dpd_timeout_seconds", value=dpd_timeout_seconds, expected_type=type_hints["dpd_timeout_seconds"])
            check_type(argname="argument egress_nat_rules", value=egress_nat_rules, expected_type=type_hints["egress_nat_rules"])
            check_type(argname="argument enable_bgp", value=enable_bgp, expected_type=type_hints["enable_bgp"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument ingress_nat_rules", value=ingress_nat_rules, expected_type=type_hints["ingress_nat_rules"])
            check_type(argname="argument ipsec_policies", value=ipsec_policies, expected_type=type_hints["ipsec_policies"])
            check_type(argname="argument local_network_gateway2", value=local_network_gateway2, expected_type=type_hints["local_network_gateway2"])
            check_type(argname="argument peer", value=peer, expected_type=type_hints["peer"])
            check_type(argname="argument routing_weight", value=routing_weight, expected_type=type_hints["routing_weight"])
            check_type(argname="argument shared_key", value=shared_key, expected_type=type_hints["shared_key"])
            check_type(argname="argument use_policy_based_traffic_selectors", value=use_policy_based_traffic_selectors, expected_type=type_hints["use_policy_based_traffic_selectors"])
            check_type(argname="argument virtual_network_gateway2", value=virtual_network_gateway2, expected_type=type_hints["virtual_network_gateway2"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "connection_type": connection_type,
            "resource_group_id": resource_group_id,
            "virtual_network_gateway1": virtual_network_gateway1,
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
        if authorization_key is not None:
            self._values["authorization_key"] = authorization_key
        if connection_mode is not None:
            self._values["connection_mode"] = connection_mode
        if connection_protocol is not None:
            self._values["connection_protocol"] = connection_protocol
        if dpd_timeout_seconds is not None:
            self._values["dpd_timeout_seconds"] = dpd_timeout_seconds
        if egress_nat_rules is not None:
            self._values["egress_nat_rules"] = egress_nat_rules
        if enable_bgp is not None:
            self._values["enable_bgp"] = enable_bgp
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if ingress_nat_rules is not None:
            self._values["ingress_nat_rules"] = ingress_nat_rules
        if ipsec_policies is not None:
            self._values["ipsec_policies"] = ipsec_policies
        if local_network_gateway2 is not None:
            self._values["local_network_gateway2"] = local_network_gateway2
        if peer is not None:
            self._values["peer"] = peer
        if routing_weight is not None:
            self._values["routing_weight"] = routing_weight
        if shared_key is not None:
            self._values["shared_key"] = shared_key
        if use_policy_based_traffic_selectors is not None:
            self._values["use_policy_based_traffic_selectors"] = use_policy_based_traffic_selectors
        if virtual_network_gateway2 is not None:
            self._values["virtual_network_gateway2"] = virtual_network_gateway2

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
    def connection_type(self) -> builtins.str:
        '''Connection type Must be "IPsec", "Vnet2Vnet", or "ExpressRoute".'''
        result = self._values.get("connection_type")
        assert result is not None, "Required property 'connection_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_group_id(self) -> builtins.str:
        '''Resource group ID where the connection will be created.'''
        result = self._values.get("resource_group_id")
        assert result is not None, "Required property 'resource_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def virtual_network_gateway1(self) -> GatewayReference:
        '''Reference to the first virtual network gateway Required for all connection types.'''
        result = self._values.get("virtual_network_gateway1")
        assert result is not None, "Required property 'virtual_network_gateway1' is missing"
        return typing.cast(GatewayReference, result)

    @builtins.property
    def authorization_key(self) -> typing.Optional[builtins.str]:
        '''Authorization key for the ExpressRoute circuit Optional - for cross-subscription ExpressRoute connections.'''
        result = self._values.get("authorization_key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def connection_mode(self) -> typing.Optional[builtins.str]:
        '''Connection mode.

        :default: "Default"
        '''
        result = self._values.get("connection_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def connection_protocol(self) -> typing.Optional[builtins.str]:
        '''Connection protocol to use.

        :default: "IKEv2"
        '''
        result = self._values.get("connection_protocol")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def dpd_timeout_seconds(self) -> typing.Optional[jsii.Number]:
        '''DPD timeout in seconds.'''
        result = self._values.get("dpd_timeout_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def egress_nat_rules(self) -> typing.Optional[typing.List[NatRuleReference]]:
        '''Egress NAT rules.'''
        result = self._values.get("egress_nat_rules")
        return typing.cast(typing.Optional[typing.List[NatRuleReference]], result)

    @builtins.property
    def enable_bgp(self) -> typing.Optional[builtins.bool]:
        '''Enable BGP for the connection.

        :default: false
        '''
        result = self._values.get("enable_bgp")
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
    def ingress_nat_rules(self) -> typing.Optional[typing.List[NatRuleReference]]:
        '''Ingress NAT rules.'''
        result = self._values.get("ingress_nat_rules")
        return typing.cast(typing.Optional[typing.List[NatRuleReference]], result)

    @builtins.property
    def ipsec_policies(self) -> typing.Optional[typing.List[IpsecPolicy]]:
        '''Custom IPsec policies.'''
        result = self._values.get("ipsec_policies")
        return typing.cast(typing.Optional[typing.List[IpsecPolicy]], result)

    @builtins.property
    def local_network_gateway2(self) -> typing.Optional[GatewayReference]:
        '''Reference to the local network gateway Required for IPsec connections only.'''
        result = self._values.get("local_network_gateway2")
        return typing.cast(typing.Optional[GatewayReference], result)

    @builtins.property
    def peer(self) -> typing.Optional[PeerReference]:
        '''Reference to the ExpressRoute circuit Required for ExpressRoute connections only.'''
        result = self._values.get("peer")
        return typing.cast(typing.Optional[PeerReference], result)

    @builtins.property
    def routing_weight(self) -> typing.Optional[jsii.Number]:
        '''Routing weight for the connection.'''
        result = self._values.get("routing_weight")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def shared_key(self) -> typing.Optional[builtins.str]:
        '''Shared key for the connection Required for IPsec and Vnet2Vnet connections.'''
        result = self._values.get("shared_key")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def use_policy_based_traffic_selectors(self) -> typing.Optional[builtins.bool]:
        '''Enable policy-based traffic selectors.

        :default: false
        '''
        result = self._values.get("use_policy_based_traffic_selectors")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def virtual_network_gateway2(self) -> typing.Optional[GatewayReference]:
        '''Reference to the second virtual network gateway Required for Vnet2Vnet connections only.'''
        result = self._values.get("virtual_network_gateway2")
        return typing.cast(typing.Optional[GatewayReference], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkGatewayConnectionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "GatewayReference",
    "IpsecPolicy",
    "NatRuleReference",
    "PeerReference",
    "VirtualNetworkGatewayConnection",
    "VirtualNetworkGatewayConnectionProps",
]

publication.publish()

def _typecheckingstub__b3e42a46a89f704f9bf7d4d07d3e57211a7f3c5ea0a549c2742cfbcb1b76c3eb(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48a1a9023babbe0ff91a428bcdf27881b956ea99d3d4faf5abc4d7fecb005574(
    *,
    dh_group: builtins.str,
    ike_encryption: builtins.str,
    ike_integrity: builtins.str,
    ipsec_encryption: builtins.str,
    ipsec_integrity: builtins.str,
    pfs_group: builtins.str,
    sa_data_size_kilobytes: jsii.Number,
    sa_life_time_seconds: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e987169fed4c3a61696b68e6fa91b60d6ddb0c54019838f65ed5d0b78bdb6e53(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f951db7790af9fda3ccd18eaae249af1bbcf573140d9f0e1823afb6e97620485(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4ec8b67425ce1a07c13ad80ba0ba64b66156d199acdef2b96000710e0e70cfb2(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    connection_type: builtins.str,
    resource_group_id: builtins.str,
    virtual_network_gateway1: typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]],
    authorization_key: typing.Optional[builtins.str] = None,
    connection_mode: typing.Optional[builtins.str] = None,
    connection_protocol: typing.Optional[builtins.str] = None,
    dpd_timeout_seconds: typing.Optional[jsii.Number] = None,
    egress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    enable_bgp: typing.Optional[builtins.bool] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ingress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    ipsec_policies: typing.Optional[typing.Sequence[typing.Union[IpsecPolicy, typing.Dict[builtins.str, typing.Any]]]] = None,
    local_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
    peer: typing.Optional[typing.Union[PeerReference, typing.Dict[builtins.str, typing.Any]]] = None,
    routing_weight: typing.Optional[jsii.Number] = None,
    shared_key: typing.Optional[builtins.str] = None,
    use_policy_based_traffic_selectors: typing.Optional[builtins.bool] = None,
    virtual_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__8023058abef2eee43191d9491a9ee407770f2d0120af347b43bdfd7f3704840b(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3823f93c07bbe2b869b530760ef7a1f94e3c24dac16c8415180ec28df1da3c96(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd01f37589cbca66cf40488d0d59a94de2e9f9dc3afa4f99e12590b64e2e0252(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5faabf10103c78fb68094359eba693b531cba47bbbb8002f03e5f2809da73e0a(
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
    connection_type: builtins.str,
    resource_group_id: builtins.str,
    virtual_network_gateway1: typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]],
    authorization_key: typing.Optional[builtins.str] = None,
    connection_mode: typing.Optional[builtins.str] = None,
    connection_protocol: typing.Optional[builtins.str] = None,
    dpd_timeout_seconds: typing.Optional[jsii.Number] = None,
    egress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    enable_bgp: typing.Optional[builtins.bool] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ingress_nat_rules: typing.Optional[typing.Sequence[typing.Union[NatRuleReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    ipsec_policies: typing.Optional[typing.Sequence[typing.Union[IpsecPolicy, typing.Dict[builtins.str, typing.Any]]]] = None,
    local_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
    peer: typing.Optional[typing.Union[PeerReference, typing.Dict[builtins.str, typing.Any]]] = None,
    routing_weight: typing.Optional[jsii.Number] = None,
    shared_key: typing.Optional[builtins.str] = None,
    use_policy_based_traffic_selectors: typing.Optional[builtins.bool] = None,
    virtual_network_gateway2: typing.Optional[typing.Union[GatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass
