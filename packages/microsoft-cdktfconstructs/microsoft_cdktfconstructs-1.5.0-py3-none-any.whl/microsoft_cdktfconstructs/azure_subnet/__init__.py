r'''
# Azure Subnet Construct

This construct provides a type-safe, version-aware interface for managing Azure Subnets using the Azure API (azapi) provider in Terraform CDK.

## Features

* **Multi-Version Support**: Supports the three most recent stable API versions (2025-01-01, 2024-10-01, 2024-07-01)
* **Type Safety**: Full TypeScript support with comprehensive type definitions
* **Parent-Child Relationship**: Properly models the relationship between Virtual Networks and Subnets
* **Flexible Configuration**: Support for advanced networking features including NSGs, route tables, service endpoints, and delegations
* **Property Validation**: Schema-based validation for all subnet properties
* **Version Auto-Resolution**: Automatically resolves to the latest stable API version unless explicitly specified

## Supported API Versions

* `2025-01-01` (default)
* `2024-10-01`
* `2024-07-01`

All versions are sourced from the [Azure REST API specifications](https://github.com/Azure/azure-rest-api-specs/tree/main/specification/network/resource-manager/Microsoft.Network/stable).

## Installation

This construct is part of the `@cdktf/terraform-cdk-constructs` package.

```bash
npm install @cdktf/terraform-cdk-constructs
```

## Usage

### Basic Subnet

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@cdktf/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@cdktf/terraform-cdk-constructs/azure-resourcegroup";
import { VirtualNetwork } from "@cdktf/terraform-cdk-constructs/azure-virtualnetwork";
import { Subnet } from "@cdktf/terraform-cdk-constructs/azure-subnet";

const app = new App();
const stack = new TerraformStack(app, "subnet-stack");

// Configure the Azure provider
new AzapiProvider(stack, "azapi", {});

// Create a resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "rg-network",
  location: "eastus",
});

// Create a virtual network
const vnet = new VirtualNetwork(stack, "vnet", {
  name: "vnet-main",
  location: "eastus",
  resourceGroupId: resourceGroup.id,
  addressSpace: {
    addressPrefixes: ["10.0.0.0/16"],
  },
});

// Create a subnet within the virtual network
const subnet = new Subnet(stack, "subnet", {
  name: "subnet-app",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.1.0/24",
});

app.synth();
```

### Subnet with Service Endpoints

```python
const subnet = new Subnet(stack, "subnet-storage", {
  name: "subnet-storage",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.2.0/24",
  serviceEndpoints: [
    {
      service: "Microsoft.Storage",
      locations: ["eastus"],
    },
    {
      service: "Microsoft.Sql",
      locations: ["eastus"],
    },
  ],
});
```

### Subnet with Network Security Group

```python
const subnet = new Subnet(stack, "subnet-secure", {
  name: "subnet-secure",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.3.0/24",
  networkSecurityGroup: {
    id: "/subscriptions/{subscription-id}/resourceGroups/rg-network/providers/Microsoft.Network/networkSecurityGroups/nsg-app",
  },
});
```

### Subnet with Delegation

```python
const subnet = new Subnet(stack, "subnet-sql", {
  name: "subnet-sql",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.4.0/24",
  delegations: [
    {
      name: "sql-delegation",
      serviceName: "Microsoft.Sql/managedInstances",
    },
  ],
});
```

### Multiple Subnets in the Same VNet

```python
// Frontend subnet
const frontendSubnet = new Subnet(stack, "subnet-frontend", {
  name: "subnet-frontend",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.10.0/24",
});

// Backend subnet with service endpoints
const backendSubnet = new Subnet(stack, "subnet-backend", {
  name: "subnet-backend",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.20.0/24",
  serviceEndpoints: [
    {
      service: "Microsoft.Storage",
      locations: ["eastus"],
    },
  ],
});

// Database subnet with delegation
const dbSubnet = new Subnet(stack, "subnet-database", {
  name: "subnet-database",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.30.0/24",
  delegations: [
    {
      name: "db-delegation",
      serviceName: "Microsoft.DBforPostgreSQL/flexibleServers",
    },
  ],
});
```

### Subnet with Private Endpoint Policies

```python
const subnet = new Subnet(stack, "subnet-private", {
  name: "subnet-private",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  addressPrefix: "10.0.5.0/24",
  privateEndpointNetworkPolicies: "Disabled",
  privateLinkServiceNetworkPolicies: "Enabled",
});
```

### Using a Specific API Version

```python
const subnet = new Subnet(stack, "subnet-versioned", {
  name: "subnet-versioned",
  virtualNetworkName: "vnet-main",
  resourceGroupId: resourceGroup.id,
  apiVersion: "2024-10-01",
  addressPrefix: "10.0.6.0/24",
});
```

## Properties

### Required Properties

* **name** (string): The name of the subnet
* **virtualNetworkName** (string): The name of the parent virtual network
* **resourceGroupId** (string): The resource ID of the resource group containing the virtual network
* **addressPrefix** (string): The address prefix for the subnet in CIDR notation (e.g., "10.0.1.0/24")

### Optional Properties

* **apiVersion** (string): The Azure API version to use (defaults to 2025-01-01)
* **location** (string): The Azure region (inherited from parent VNet if not specified)
* **networkSecurityGroup** (object): Reference to a Network Security Group

  * **id** (string): The resource ID of the NSG
* **routeTable** (object): Reference to a Route Table

  * **id** (string): The resource ID of the route table
* **natGateway** (object): Reference to a NAT Gateway

  * **id** (string): The resource ID of the NAT gateway
* **serviceEndpoints** (array): List of service endpoints to enable

  * **service** (string): The service type (e.g., "Microsoft.Storage", "Microsoft.Sql")
  * **locations** (array): List of locations where the service endpoint is available
* **serviceEndpointPolicies** (array): List of service endpoint policies

  * **id** (string): The resource ID of the service endpoint policy
* **delegations** (array): List of subnet delegations

  * **name** (string): Name of the delegation
  * **serviceName** (string): The service to delegate to (e.g., "Microsoft.Sql/managedInstances")
  * **actions** (array, optional): List of actions allowed by the delegation
* **privateEndpointNetworkPolicies** (string): Enable or disable network policies for private endpoints ("Enabled" or "Disabled")
* **privateLinkServiceNetworkPolicies** (string): Enable or disable network policies for private link services ("Enabled" or "Disabled")
* **applicationGatewayIPConfigurations** (array): IP configurations for application gateway
* **ipAllocations** (array): IP allocation references
* **defaultOutboundAccess** (boolean): Enable or disable default outbound access
* **tags** (object): Resource tags as key-value pairs

## Parent-Child Relationship

Subnets are child resources of Virtual Networks. This relationship is implemented through:

1. **virtualNetworkName**: The name of the parent VNet must be provided
2. **resourceGroupId**: The resource group ID is used to construct the parent VNet's full resource ID
3. **Parent ID Construction**: The construct automatically builds the correct parent resource ID in the format:

   ```
   ${resourceGroupId}/providers/Microsoft.Network/virtualNetworks/${virtualNetworkName}
   ```

This ensures that the subnet is properly created as a child of the specified virtual network.

## Outputs

The construct provides the following outputs:

* **id**: The fully qualified resource ID of the subnet
* **name**: The name of the subnet
* **virtualNetworkId**: The resource ID of the parent virtual network
* **addressPrefix**: The address prefix of the subnet
* **resolvedApiVersion**: The API version being used for this resource

## Best Practices

1. **Address Planning**: Carefully plan your subnet address spaces to avoid overlapping ranges
2. **Service Endpoints**: Enable service endpoints only for the services you need to reduce complexity
3. **Delegations**: Use delegations when hosting specific Azure services that require dedicated subnets
4. **NSG Association**: Consider associating NSGs at the subnet level for centralized security management
5. **Multiple Subnets**: Create separate subnets for different tiers (frontend, backend, database) for better network isolation
6. **Private Endpoints**: Disable network policies when using private endpoints in a subnet
7. **API Version**: Use the latest stable API version unless you have specific compatibility requirements

## Common Delegation Services

* `Microsoft.Sql/managedInstances` - SQL Managed Instances
* `Microsoft.DBforPostgreSQL/flexibleServers` - PostgreSQL Flexible Servers
* `Microsoft.DBforMySQL/flexibleServers` - MySQL Flexible Servers
* `Microsoft.Web/serverFarms` - App Service Plans
* `Microsoft.ContainerInstance/containerGroups` - Container Instances
* `Microsoft.Netapp/volumes` - NetApp Volumes
* `Microsoft.Logic/integrationServiceEnvironments` - Logic Apps ISE

## Resource Type

This construct manages resources of type:

```
Microsoft.Network/virtualNetworks/subnets@{apiVersion}
```

## Related Constructs

* **VirtualNetwork**: Parent resource for subnets
* **NetworkSecurityGroup**: Can be associated with subnets for security rules
* **RouteTable**: Can be associated with subnets for custom routing

## License

This construct is part of the Terraform CDK Constructs project and is licensed under the Mozilla Public License 2.0.

## Contributing

Contributions are welcome! Please see the main project repository for contribution guidelines.
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


class Subnet(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.Subnet",
):
    '''Azure Subnet implementation.

    This class provides a single, version-aware implementation that replaces
    version-specific Subnet classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    **Child Resource Pattern**: Subnets are child resources of Virtual Networks.
    This implementation overrides the ``resolveParentId()`` method to properly
    construct the Virtual Network ID as the parent, following the enhanced base
    class pattern for child resources.

    Example::

        // Usage with network security group:
        const subnet = new Subnet(this, "subnet", {
          name: "my-subnet",
          virtualNetworkName: "my-vnet",
          resourceGroupId: resourceGroup.id,
          addressPrefix: "10.0.1.0/24",
          networkSecurityGroup: { id: nsg.id }
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        address_prefix: builtins.str,
        resource_group_id: builtins.str,
        virtual_network_name: builtins.str,
        delegations: typing.Optional[typing.Sequence[typing.Union["SubnetDelegation", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        ip_allocations: typing.Optional[typing.Sequence[typing.Any]] = None,
        nat_gateway: typing.Optional[typing.Union["SubnetNATGatewayReference", typing.Dict[builtins.str, typing.Any]]] = None,
        network_security_group: typing.Optional[typing.Union["SubnetNSGReference", typing.Dict[builtins.str, typing.Any]]] = None,
        private_endpoint_network_policies: typing.Optional[builtins.str] = None,
        private_link_service_network_policies: typing.Optional[builtins.str] = None,
        route_table: typing.Optional[typing.Union["SubnetRouteTableReference", typing.Dict[builtins.str, typing.Any]]] = None,
        service_endpoints: typing.Optional[typing.Sequence[typing.Union["SubnetServiceEndpoint", typing.Dict[builtins.str, typing.Any]]]] = None,
        virtual_network_id: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Subnet using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Subnet implementations.

        **Parent ID Resolution**: Subnets are child resources of Virtual Networks.
        The resolveParentId() method is overridden to return the Virtual Network ID
        instead of the Resource Group ID, establishing the proper parent-child hierarchy.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param address_prefix: Address prefix for the subnet in CIDR notation Must be within the parent VNet's address space.
        :param resource_group_id: Resource group ID where the parent VNet exists Required for constructing the parent ID.
        :param virtual_network_name: Name of the parent virtual network Required for constructing the parent ID.
        :param delegations: Subnet delegations Delegates subnet to specific Azure services.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param ip_allocations: IP allocations for the subnet Optional - for custom IP allocation.
        :param nat_gateway: NAT gateway reference Optional - for outbound internet connectivity.
        :param network_security_group: Network security group reference Optional - can be attached later.
        :param private_endpoint_network_policies: Private endpoint network policies Controls whether network policies apply to private endpoints. Default: "Disabled"
        :param private_link_service_network_policies: Private link service network policies Controls whether network policies apply to private link services. Default: "Enabled"
        :param route_table: Route table reference Optional - can be attached later.
        :param service_endpoints: Service endpoints for the subnet Enables private access to Azure services.
        :param virtual_network_id: Optional: Full resource ID of the parent Virtual Network When provided, creates a proper Terraform dependency on the VNet If not provided, the parent ID will be constructed from resourceGroupId and virtualNetworkName.
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
            type_hints = typing.get_type_hints(_typecheckingstub__9db44f8f653bfc6c19c8f1781ba6df56d93b3f3898d92cdad97d2ed774167f93)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SubnetProps(
            address_prefix=address_prefix,
            resource_group_id=resource_group_id,
            virtual_network_name=virtual_network_name,
            delegations=delegations,
            ignore_changes=ignore_changes,
            ip_allocations=ip_allocations,
            nat_gateway=nat_gateway,
            network_security_group=network_security_group,
            private_endpoint_network_policies=private_endpoint_network_policies,
            private_link_service_network_policies=private_link_service_network_policies,
            route_table=route_table,
            service_endpoints=service_endpoints,
            virtual_network_id=virtual_network_id,
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
            type_hints = typing.get_type_hints(_typecheckingstub__840ef9c7cf99db284a6f49870c9b303a12ff26362a0181491a71c8926a997719)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="parentResourceForLocation")
    def _parent_resource_for_location(self) -> typing.Optional[_AzapiResource_7e7f5b39]:
        '''Subnets inherit location from their parent VNet, so no parent resource reference needed The Azure API automatically handles location inheritance for child resources.'''
        return typing.cast(typing.Optional[_AzapiResource_7e7f5b39], jsii.invoke(self, "parentResourceForLocation", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent ID for the Subnet resource.

        Subnets are child resources of Virtual Networks. This method overrides
        the default parent ID resolution to return the Virtual Network ID instead
        of the Resource Group ID.

        :param props: - The resource properties.

        :return: The Virtual Network ID (parent resource ID)
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c35905cdc7f422c6d5019fa188793f5dde12359bd77c122a07d98f50342112cd)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Subnets.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="addressPrefix")
    def address_prefix(self) -> builtins.str:
        '''Get the address prefix value Returns the address prefix from the input props since Azure API doesn't return it in output.'''
        return typing.cast(builtins.str, jsii.get(self, "addressPrefix"))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "SubnetProps":
        '''The input properties for this Subnet instance.'''
        return typing.cast("SubnetProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property to match original interface.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="virtualNetworkId")
    def virtual_network_id(self) -> builtins.str:
        '''Get the parent Virtual Network ID Constructs the VNet resource ID from the subnet's parent reference.'''
        return typing.cast(builtins.str, jsii.get(self, "virtualNetworkId"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.SubnetDelegation",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "service_name": "serviceName", "actions": "actions"},
)
class SubnetDelegation:
    def __init__(
        self,
        *,
        name: builtins.str,
        service_name: builtins.str,
        actions: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Delegation configuration for Subnet.

        :param name: Name of the delegation.
        :param service_name: The service name to delegate to.
        :param actions: Optional actions allowed for the delegation.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bed6f7f98bb8179d7f8269eb18f8b80e0680bbd376ffa8180d40d60c59a6c014)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument service_name", value=service_name, expected_type=type_hints["service_name"])
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "service_name": service_name,
        }
        if actions is not None:
            self._values["actions"] = actions

    @builtins.property
    def name(self) -> builtins.str:
        '''Name of the delegation.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def service_name(self) -> builtins.str:
        '''The service name to delegate to.

        Example::

            "Microsoft.Sql/managedInstances"
        '''
        result = self._values.get("service_name")
        assert result is not None, "Required property 'service_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def actions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Optional actions allowed for the delegation.'''
        result = self._values.get("actions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SubnetDelegation(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.SubnetNATGatewayReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class SubnetNATGatewayReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''NAT Gateway reference for Subnet.

        :param id: NAT Gateway resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9f736dc29242ea2c3058a3acdffff2a74a63391a1843f9f6fc805ef92f13888d)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''NAT Gateway resource ID.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SubnetNATGatewayReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.SubnetNSGReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class SubnetNSGReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Network Security Group reference for Subnet.

        :param id: Network Security Group resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ea84418e6fdb5ecfa45925ceffee41a65be485bb7b0e6dce8d0efe73bae1c081)
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
        return "SubnetNSGReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.SubnetProps",
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
        "address_prefix": "addressPrefix",
        "resource_group_id": "resourceGroupId",
        "virtual_network_name": "virtualNetworkName",
        "delegations": "delegations",
        "ignore_changes": "ignoreChanges",
        "ip_allocations": "ipAllocations",
        "nat_gateway": "natGateway",
        "network_security_group": "networkSecurityGroup",
        "private_endpoint_network_policies": "privateEndpointNetworkPolicies",
        "private_link_service_network_policies": "privateLinkServiceNetworkPolicies",
        "route_table": "routeTable",
        "service_endpoints": "serviceEndpoints",
        "virtual_network_id": "virtualNetworkId",
    },
)
class SubnetProps(_AzapiResourceProps_141a2340):
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
        address_prefix: builtins.str,
        resource_group_id: builtins.str,
        virtual_network_name: builtins.str,
        delegations: typing.Optional[typing.Sequence[typing.Union[SubnetDelegation, typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        ip_allocations: typing.Optional[typing.Sequence[typing.Any]] = None,
        nat_gateway: typing.Optional[typing.Union[SubnetNATGatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
        network_security_group: typing.Optional[typing.Union[SubnetNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
        private_endpoint_network_policies: typing.Optional[builtins.str] = None,
        private_link_service_network_policies: typing.Optional[builtins.str] = None,
        route_table: typing.Optional[typing.Union["SubnetRouteTableReference", typing.Dict[builtins.str, typing.Any]]] = None,
        service_endpoints: typing.Optional[typing.Sequence[typing.Union["SubnetServiceEndpoint", typing.Dict[builtins.str, typing.Any]]]] = None,
        virtual_network_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the Azure Subnet.

        Extends AzapiResourceProps with Subnet specific properties

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
        :param address_prefix: Address prefix for the subnet in CIDR notation Must be within the parent VNet's address space.
        :param resource_group_id: Resource group ID where the parent VNet exists Required for constructing the parent ID.
        :param virtual_network_name: Name of the parent virtual network Required for constructing the parent ID.
        :param delegations: Subnet delegations Delegates subnet to specific Azure services.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        :param ip_allocations: IP allocations for the subnet Optional - for custom IP allocation.
        :param nat_gateway: NAT gateway reference Optional - for outbound internet connectivity.
        :param network_security_group: Network security group reference Optional - can be attached later.
        :param private_endpoint_network_policies: Private endpoint network policies Controls whether network policies apply to private endpoints. Default: "Disabled"
        :param private_link_service_network_policies: Private link service network policies Controls whether network policies apply to private link services. Default: "Enabled"
        :param route_table: Route table reference Optional - can be attached later.
        :param service_endpoints: Service endpoints for the subnet Enables private access to Azure services.
        :param virtual_network_id: Optional: Full resource ID of the parent Virtual Network When provided, creates a proper Terraform dependency on the VNet If not provided, the parent ID will be constructed from resourceGroupId and virtualNetworkName.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(nat_gateway, dict):
            nat_gateway = SubnetNATGatewayReference(**nat_gateway)
        if isinstance(network_security_group, dict):
            network_security_group = SubnetNSGReference(**network_security_group)
        if isinstance(route_table, dict):
            route_table = SubnetRouteTableReference(**route_table)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__37b98de7a15657113de263093efd0d005bffcee674fc805d622b872ad715cb84)
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
            check_type(argname="argument address_prefix", value=address_prefix, expected_type=type_hints["address_prefix"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument virtual_network_name", value=virtual_network_name, expected_type=type_hints["virtual_network_name"])
            check_type(argname="argument delegations", value=delegations, expected_type=type_hints["delegations"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument ip_allocations", value=ip_allocations, expected_type=type_hints["ip_allocations"])
            check_type(argname="argument nat_gateway", value=nat_gateway, expected_type=type_hints["nat_gateway"])
            check_type(argname="argument network_security_group", value=network_security_group, expected_type=type_hints["network_security_group"])
            check_type(argname="argument private_endpoint_network_policies", value=private_endpoint_network_policies, expected_type=type_hints["private_endpoint_network_policies"])
            check_type(argname="argument private_link_service_network_policies", value=private_link_service_network_policies, expected_type=type_hints["private_link_service_network_policies"])
            check_type(argname="argument route_table", value=route_table, expected_type=type_hints["route_table"])
            check_type(argname="argument service_endpoints", value=service_endpoints, expected_type=type_hints["service_endpoints"])
            check_type(argname="argument virtual_network_id", value=virtual_network_id, expected_type=type_hints["virtual_network_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefix": address_prefix,
            "resource_group_id": resource_group_id,
            "virtual_network_name": virtual_network_name,
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
        if delegations is not None:
            self._values["delegations"] = delegations
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if ip_allocations is not None:
            self._values["ip_allocations"] = ip_allocations
        if nat_gateway is not None:
            self._values["nat_gateway"] = nat_gateway
        if network_security_group is not None:
            self._values["network_security_group"] = network_security_group
        if private_endpoint_network_policies is not None:
            self._values["private_endpoint_network_policies"] = private_endpoint_network_policies
        if private_link_service_network_policies is not None:
            self._values["private_link_service_network_policies"] = private_link_service_network_policies
        if route_table is not None:
            self._values["route_table"] = route_table
        if service_endpoints is not None:
            self._values["service_endpoints"] = service_endpoints
        if virtual_network_id is not None:
            self._values["virtual_network_id"] = virtual_network_id

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
    def address_prefix(self) -> builtins.str:
        '''Address prefix for the subnet in CIDR notation Must be within the parent VNet's address space.

        Example::

            "10.0.1.0/24"
        '''
        result = self._values.get("address_prefix")
        assert result is not None, "Required property 'address_prefix' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_group_id(self) -> builtins.str:
        '''Resource group ID where the parent VNet exists Required for constructing the parent ID.'''
        result = self._values.get("resource_group_id")
        assert result is not None, "Required property 'resource_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def virtual_network_name(self) -> builtins.str:
        '''Name of the parent virtual network Required for constructing the parent ID.'''
        result = self._values.get("virtual_network_name")
        assert result is not None, "Required property 'virtual_network_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def delegations(self) -> typing.Optional[typing.List[SubnetDelegation]]:
        '''Subnet delegations Delegates subnet to specific Azure services.'''
        result = self._values.get("delegations")
        return typing.cast(typing.Optional[typing.List[SubnetDelegation]], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed.

        Example::

            ["networkSecurityGroup", "routeTable"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def ip_allocations(self) -> typing.Optional[typing.List[typing.Any]]:
        '''IP allocations for the subnet Optional - for custom IP allocation.'''
        result = self._values.get("ip_allocations")
        return typing.cast(typing.Optional[typing.List[typing.Any]], result)

    @builtins.property
    def nat_gateway(self) -> typing.Optional[SubnetNATGatewayReference]:
        '''NAT gateway reference Optional - for outbound internet connectivity.'''
        result = self._values.get("nat_gateway")
        return typing.cast(typing.Optional[SubnetNATGatewayReference], result)

    @builtins.property
    def network_security_group(self) -> typing.Optional[SubnetNSGReference]:
        '''Network security group reference Optional - can be attached later.'''
        result = self._values.get("network_security_group")
        return typing.cast(typing.Optional[SubnetNSGReference], result)

    @builtins.property
    def private_endpoint_network_policies(self) -> typing.Optional[builtins.str]:
        '''Private endpoint network policies Controls whether network policies apply to private endpoints.

        :default: "Disabled"
        '''
        result = self._values.get("private_endpoint_network_policies")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def private_link_service_network_policies(self) -> typing.Optional[builtins.str]:
        '''Private link service network policies Controls whether network policies apply to private link services.

        :default: "Enabled"
        '''
        result = self._values.get("private_link_service_network_policies")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def route_table(self) -> typing.Optional["SubnetRouteTableReference"]:
        '''Route table reference Optional - can be attached later.'''
        result = self._values.get("route_table")
        return typing.cast(typing.Optional["SubnetRouteTableReference"], result)

    @builtins.property
    def service_endpoints(
        self,
    ) -> typing.Optional[typing.List["SubnetServiceEndpoint"]]:
        '''Service endpoints for the subnet Enables private access to Azure services.'''
        result = self._values.get("service_endpoints")
        return typing.cast(typing.Optional[typing.List["SubnetServiceEndpoint"]], result)

    @builtins.property
    def virtual_network_id(self) -> typing.Optional[builtins.str]:
        '''Optional: Full resource ID of the parent Virtual Network When provided, creates a proper Terraform dependency on the VNet If not provided, the parent ID will be constructed from resourceGroupId and virtualNetworkName.'''
        result = self._values.get("virtual_network_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SubnetProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.SubnetRouteTableReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class SubnetRouteTableReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Route Table reference for Subnet.

        :param id: Route Table resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d3a8b15873148faec66f1f9cd30692e61b94eb09772dba92ab774eebccbe080)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Route Table resource ID.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SubnetRouteTableReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_subnet.SubnetServiceEndpoint",
    jsii_struct_bases=[],
    name_mapping={"service": "service", "locations": "locations"},
)
class SubnetServiceEndpoint:
    def __init__(
        self,
        *,
        service: builtins.str,
        locations: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Service endpoint configuration for Subnet.

        :param service: The service endpoint identifier.
        :param locations: Optional locations where the service endpoint is available.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c79ea465a630ad678f0cc57f225703f6f3441a09b986134543944923ceb70648)
            check_type(argname="argument service", value=service, expected_type=type_hints["service"])
            check_type(argname="argument locations", value=locations, expected_type=type_hints["locations"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "service": service,
        }
        if locations is not None:
            self._values["locations"] = locations

    @builtins.property
    def service(self) -> builtins.str:
        '''The service endpoint identifier.

        Example::

            "Microsoft.Storage"
        '''
        result = self._values.get("service")
        assert result is not None, "Required property 'service' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def locations(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Optional locations where the service endpoint is available.

        Example::

            ["eastus", "westus"]
        '''
        result = self._values.get("locations")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SubnetServiceEndpoint(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Subnet",
    "SubnetDelegation",
    "SubnetNATGatewayReference",
    "SubnetNSGReference",
    "SubnetProps",
    "SubnetRouteTableReference",
    "SubnetServiceEndpoint",
]

publication.publish()

def _typecheckingstub__9db44f8f653bfc6c19c8f1781ba6df56d93b3f3898d92cdad97d2ed774167f93(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    address_prefix: builtins.str,
    resource_group_id: builtins.str,
    virtual_network_name: builtins.str,
    delegations: typing.Optional[typing.Sequence[typing.Union[SubnetDelegation, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ip_allocations: typing.Optional[typing.Sequence[typing.Any]] = None,
    nat_gateway: typing.Optional[typing.Union[SubnetNATGatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
    network_security_group: typing.Optional[typing.Union[SubnetNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
    private_endpoint_network_policies: typing.Optional[builtins.str] = None,
    private_link_service_network_policies: typing.Optional[builtins.str] = None,
    route_table: typing.Optional[typing.Union[SubnetRouteTableReference, typing.Dict[builtins.str, typing.Any]]] = None,
    service_endpoints: typing.Optional[typing.Sequence[typing.Union[SubnetServiceEndpoint, typing.Dict[builtins.str, typing.Any]]]] = None,
    virtual_network_id: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__840ef9c7cf99db284a6f49870c9b303a12ff26362a0181491a71c8926a997719(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c35905cdc7f422c6d5019fa188793f5dde12359bd77c122a07d98f50342112cd(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bed6f7f98bb8179d7f8269eb18f8b80e0680bbd376ffa8180d40d60c59a6c014(
    *,
    name: builtins.str,
    service_name: builtins.str,
    actions: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9f736dc29242ea2c3058a3acdffff2a74a63391a1843f9f6fc805ef92f13888d(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ea84418e6fdb5ecfa45925ceffee41a65be485bb7b0e6dce8d0efe73bae1c081(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__37b98de7a15657113de263093efd0d005bffcee674fc805d622b872ad715cb84(
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
    address_prefix: builtins.str,
    resource_group_id: builtins.str,
    virtual_network_name: builtins.str,
    delegations: typing.Optional[typing.Sequence[typing.Union[SubnetDelegation, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ip_allocations: typing.Optional[typing.Sequence[typing.Any]] = None,
    nat_gateway: typing.Optional[typing.Union[SubnetNATGatewayReference, typing.Dict[builtins.str, typing.Any]]] = None,
    network_security_group: typing.Optional[typing.Union[SubnetNSGReference, typing.Dict[builtins.str, typing.Any]]] = None,
    private_endpoint_network_policies: typing.Optional[builtins.str] = None,
    private_link_service_network_policies: typing.Optional[builtins.str] = None,
    route_table: typing.Optional[typing.Union[SubnetRouteTableReference, typing.Dict[builtins.str, typing.Any]]] = None,
    service_endpoints: typing.Optional[typing.Sequence[typing.Union[SubnetServiceEndpoint, typing.Dict[builtins.str, typing.Any]]]] = None,
    virtual_network_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d3a8b15873148faec66f1f9cd30692e61b94eb09772dba92ab774eebccbe080(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c79ea465a630ad678f0cc57f225703f6f3441a09b986134543944923ceb70648(
    *,
    service: builtins.str,
    locations: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass
