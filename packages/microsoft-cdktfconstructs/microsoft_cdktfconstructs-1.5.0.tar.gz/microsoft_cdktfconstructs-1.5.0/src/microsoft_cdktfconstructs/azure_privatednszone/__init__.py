r'''
# Azure Private DNS Zone Construct (AZAPI)

This Construct represents a Private DNS Zone in Azure using the AZAPI provider for direct Azure REST API access.

## What is Azure Private DNS Zone?

Azure Private DNS provides a reliable and secure DNS service for your virtual networks. By using private DNS zones, you can use your own custom domain names rather than the Azure-provided names available today. Private DNS zones enable name resolution for virtual machines (VMs) within a virtual network and across virtual networks without needing to configure custom DNS servers.

**Key Features:**

* **Internal Name Resolution**: Resolve hostnames within and across Azure virtual networks
* **Custom Domain Names**: Use your own domain names for internal resources
* **No Custom DNS Required**: No need to manage custom DNS server infrastructure
* **Automatic Hostname Registration**: Optionally auto-register VM hostnames
* **Cross-VNet Resolution**: Enable DNS resolution across peered virtual networks
* **Secure and Private**: DNS records only accessible from linked virtual networks
* **High Availability**: Built on Azure's reliable DNS infrastructure

**Differences from Public DNS Zones:**

* Private DNS zones are **not** accessible from the Internet
* They provide name resolution **only** for linked virtual networks
* No need to configure name servers at a domain registrar
* Virtual network links are required for functionality
* Support for automatic VM hostname registration

You can learn more about Azure Private DNS in the [official Azure documentation](https://docs.microsoft.com/azure/dns/private-dns-overview).

## AZAPI Provider Benefits

This Private DNS Zone construct uses the AZAPI provider, which provides:

* **Direct Azure REST API Access**: No dependency on AzureRM provider limitations
* **Immediate Feature Access**: Get new Azure features as soon as they're available
* **Version-Specific Implementations**: Support for multiple API versions
* **Enhanced Type Safety**: Better IDE support and compile-time validation

## Best Practices

### Private DNS Zone Naming

* **Use internal domains**: Choose domain names that clearly indicate internal use (e.g., `internal.contoso.com`, `corp.contoso.local`)
* **Avoid public TLDs**: Don't use the same domain as your public DNS to prevent confusion
* **Plan for splits**: Consider split-brain DNS if you need both public and private zones

### Virtual Network Links

* **Link strategically**: Link private DNS zones to virtual networks that need name resolution
* **Enable auto-registration carefully**: Only enable hostname registration where appropriate
* **Consider hub-spoke**: In hub-spoke topologies, link to the hub and enable resolution via peering
* **Minimize links**: Each private DNS zone has a limit on virtual network links

### Security and Isolation

* **Use separate zones**: Create separate private DNS zones for different environments or tiers
* **Implement RBAC**: Control who can create and manage DNS records
* **Monitor changes**: Enable diagnostic logging to track DNS changes
* **Plan network topology**: Design DNS resolution strategy for complex network architectures

## Properties

This Construct supports the following properties:

### Required Properties

* **`name`**: (Required) The name of the Private DNS Zone (without a terminating dot). Must be a valid domain name.
* **`location`**: (Required) The Azure region (typically "global" for Private DNS zones as they are global resources)

### Optional Properties

* **`resourceGroupId`**: (Optional) The resource ID of the resource group where the Private DNS zone will be created
* **`tags`**: (Optional) Key-value pairs for resource tagging and organization
* **`ignoreChanges`**: (Optional) Lifecycle rules to ignore changes for specific properties
* **`apiVersion`**: (Optional) Explicit API version to use (defaults to latest: "2024-06-01")

### Read-Only Properties (Available as Outputs)

* **`maxNumberOfRecordSets`**: Maximum number of record sets that can be created
* **`numberOfRecordSets`**: Current number of record sets in the zone
* **`maxNumberOfVirtualNetworkLinks`**: Maximum number of virtual network links allowed
* **`numberOfVirtualNetworkLinks`**: Current number of virtual network links
* **`maxNumberOfVirtualNetworkLinksWithRegistration`**: Maximum VNet links with auto-registration
* **`numberOfVirtualNetworkLinksWithRegistration`**: Current VNet links with auto-registration
* **`provisioningState`**: Current provisioning state of the zone
* **`internalId`**: Internal identifier for the Private DNS zone

## Supported API Versions

| API Version | Status  | Features                                          |
|-------------|---------|---------------------------------------------------|
| 2024-06-01  | ✅ Latest | Full support for private DNS zones and VNet links |

## Basic Usage

### Simple Private DNS Zone

```python
import { PrivateDnsZone } from "@microsoft/terraform-cdk-constructs/azure-privatednszone";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";

// Create a resource group
const resourceGroup = new ResourceGroup(this, 'rg', {
  name: 'dns-rg',
  location: 'eastus',
});

// Create a private DNS zone
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  tags: {
    environment: 'production',
    service: 'dns',
  },
});
```

### Private DNS Zone with Virtual Network Link

**Note**: Virtual network links are managed as separate child resources (to be implemented). This example shows the Private DNS Zone creation, which is the prerequisite for adding virtual network links.

```python
import { PrivateDnsZone } from "@microsoft/terraform-cdk-constructs/azure-privatednszone";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import { VirtualNetwork } from "@microsoft/terraform-cdk-constructs/azure-virtualnetwork";

const resourceGroup = new ResourceGroup(this, 'rg', {
  name: 'dns-rg',
  location: 'eastus',
});

const vnet = new VirtualNetwork(this, 'vnet', {
  name: 'my-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: ['10.0.0.0/16'],
});

// Create the private DNS zone
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  tags: {
    environment: 'production',
    type: 'private',
  },
});

// Virtual network links will be added using a separate construct
// (PrivateDnsZoneVirtualNetworkLink - to be implemented)
```

## Advanced Features

### Version Pinning

Pin to a specific API version for stability:

```python
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  apiVersion: '2024-06-01', // Pin to specific version
});
```

### Ignore Changes

Prevent Terraform from detecting changes to specific properties:

```python
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  ignoreChanges: ['tags'], // Ignore tag changes
});
```

### Tag Management

Add and remove tags programmatically:

```python
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  tags: {
    environment: 'production',
  },
});

// Add a tag
privateDnsZone.addTag('owner', 'platform-team');

// Remove a tag
privateDnsZone.removeTag('environment');
```

## Outputs

The Private DNS Zone construct provides several outputs for use in other resources:

```python
// Resource ID
console.log(privateDnsZone.id);

// Private DNS Zone name
console.log(privateDnsZone.name);

// Location
console.log(privateDnsZone.location);

// Read-only properties
console.log(privateDnsZone.maxNumberOfRecordSets);
console.log(privateDnsZone.numberOfRecordSets);
console.log(privateDnsZone.maxNumberOfVirtualNetworkLinks);
console.log(privateDnsZone.numberOfVirtualNetworkLinks);
console.log(privateDnsZone.maxNumberOfVirtualNetworkLinksWithRegistration);
console.log(privateDnsZone.numberOfVirtualNetworkLinksWithRegistration);
console.log(privateDnsZone.provisioningState);
console.log(privateDnsZone.internalId);

// Terraform outputs
privateDnsZone.idOutput;
privateDnsZone.nameOutput;
privateDnsZone.maxNumberOfRecordSetsOutput;
privateDnsZone.numberOfRecordSetsOutput;
privateDnsZone.maxNumberOfVirtualNetworkLinksOutput;
privateDnsZone.numberOfVirtualNetworkLinksOutput;
privateDnsZone.maxNumberOfVirtualNetworkLinksWithRegistrationOutput;
privateDnsZone.numberOfVirtualNetworkLinksWithRegistrationOutput;
privateDnsZone.provisioningStateOutput;
privateDnsZone.internalIdOutput;
```

## Common Patterns

### Hub-Spoke Topology with Private DNS

```python
// Create hub virtual network
const hubVnet = new VirtualNetwork(this, 'hub', {
  name: 'hub-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: ['10.0.0.0/16'],
});

// Create spoke virtual networks
const spoke1Vnet = new VirtualNetwork(this, 'spoke1', {
  name: 'spoke1-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: ['10.1.0.0/16'],
});

const spoke2Vnet = new VirtualNetwork(this, 'spoke2', {
  name: 'spoke2-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: ['10.2.0.0/16'],
});

// Create private DNS zone
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
});

// Link to hub (with auto-registration) and spokes (resolution only)
// Virtual network links are created separately using PrivateDnsZoneVirtualNetworkLink
```

### Multi-Environment Private DNS Strategy

```python
// Production
const prodPrivateDnsZone = new PrivateDnsZone(this, 'prodPrivateDns', {
  name: 'prod.internal.contoso.com',
  location: 'global',
  resourceGroupId: prodResourceGroup.id,
  tags: { environment: 'production' },
});

// Staging
const stagingPrivateDnsZone = new PrivateDnsZone(this, 'stagingPrivateDns', {
  name: 'staging.internal.contoso.com',
  location: 'global',
  resourceGroupId: stagingResourceGroup.id,
  tags: { environment: 'staging' },
});

// Development
const devPrivateDnsZone = new PrivateDnsZone(this, 'devPrivateDns', {
  name: 'dev.internal.contoso.com',
  location: 'global',
  resourceGroupId: devResourceGroup.id,
  tags: { environment: 'development' },
});
```

### Shared Services Private DNS

```python
// Create a shared private DNS zone for common services
const sharedServicesDns = new PrivateDnsZone(this, 'sharedDns', {
  name: 'services.internal.contoso.com',
  location: 'global',
  resourceGroupId: sharedResourceGroup.id,
  tags: {
    purpose: 'shared-services',
    managed: 'platform-team',
  },
});

// Link to multiple virtual networks across subscriptions and regions
// (using PrivateDnsZoneVirtualNetworkLink constructs)
```

## Error Handling

The construct includes built-in validation:

```python
// Invalid domain name (will fail validation)
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com.', // ❌ No terminating dot allowed
  location: 'global',
  resourceGroupId: resourceGroup.id,
});

// Valid domain name
const privateDnsZone = new PrivateDnsZone(this, 'privateDns', {
  name: 'internal.contoso.com', // ✅ Correct format
  location: 'global',
  resourceGroupId: resourceGroup.id,
});
```

## Troubleshooting

### Private DNS Resolution Not Working

If private DNS isn't resolving:

1. Verify virtual network links are created and associated with the zone
2. Check that VMs are using Azure DNS (168.63.129.16) - this is default
3. Ensure virtual network peering is properly set up if using hub-spoke
4. Verify NSG rules aren't blocking DNS traffic (port 53)
5. Check that the private DNS zone is linked to the correct virtual networks

### Auto-Registration Issues

If VM hostnames aren't auto-registering:

1. Verify the virtual network link has auto-registration enabled
2. Ensure VMs are in a subnet of the linked virtual network
3. Check that VMs are using DHCP for their IP configuration
4. Restart the VM if necessary to trigger registration

### Resource Limits

If you hit limits:

1. Check the maximum number of record sets for your subscription
2. Review the maximum number of virtual network links allowed
3. Consider creating multiple private DNS zones if you hit limits
4. Contact Azure support if you need increased limits

### API Version Issues

If you encounter version-related errors:

1. Check supported API versions in this README
2. Consider pinning to a specific version
3. Review Azure Private DNS API documentation for breaking changes

## Related Constructs

* **Private DNS Zone Virtual Network Link**: (To be implemented) Link private DNS zones to virtual networks
* **DNS Record Sets**: (To be implemented) Create A, AAAA, CNAME, and other DNS records
* **Virtual Network**: Required for private DNS zone functionality
* **Resource Group**: Container for private DNS zone resources

## Comparison with Public DNS Zones

| Feature | Private DNS Zone | Public DNS Zone |
|---------|------------------|-----------------|
| **Accessibility** | Only from linked VNets | Internet-accessible |
| **Name Servers** | Azure-managed (automatic) | Must configure at registrar |
| **Use Case** | Internal applications | Public-facing services |
| **VNet Links** | Required for functionality | Not applicable |
| **Auto-Registration** | Supported | Not supported |
| **Record Types** | A, AAAA, CNAME, MX, PTR, SOA, SRV, TXT | All standard DNS record types |

## References

* [Azure Private DNS Documentation](https://docs.microsoft.com/azure/dns/private-dns-overview)
* [Private DNS REST API Reference](https://docs.microsoft.com/rest/api/dns/privatedns)
* [Private DNS Best Practices](https://docs.microsoft.com/azure/dns/private-dns-scenarios)
* [Azure DNS Private Resolver](https://docs.microsoft.com/azure/dns/dns-private-resolver-overview)
* [Virtual Network DNS Settings](https://docs.microsoft.com/azure/virtual-network/virtual-networks-name-resolution-for-vms-and-role-instances)
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


class PrivateDnsZone(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_privatednszone.PrivateDnsZone",
):
    '''Unified Azure Private DNS Zone implementation.

    This class provides a single, version-aware implementation that replaces all
    version-specific Private DNS Zone classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Azure Private DNS Zones are used to provide internal DNS resolution within
    Azure virtual networks. They enable name resolution for resources within a
    virtual network without requiring custom DNS servers.

    Example::

        // Private DNS zone with explicit version pinning:
        const privateDnsZone = new PrivateDnsZone(this, "privateDns", {
          name: "internal.contoso.com",
          location: "global",
          resourceGroupId: resourceGroup.id,
          apiVersion: "2024-06-01",
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
        '''Creates a new Azure Private DNS Zone using the VersionedAzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param resource_group_id: Resource group ID where the Private DNS Zone will be created.
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
            type_hints = typing.get_type_hints(_typecheckingstub__a33322a4540e130927932b239b2f69ffe4c8d2764185c487e6ce7b329fd6b8b0)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = PrivateDnsZoneProps(
            ignore_changes=ignore_changes,
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
        '''Add a tag to the Private DNS Zone.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__52038be3ed4336755627549f21019a71b7d1154cb8abef5a6aea1d337a194673)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "addTag", [key, value]))

    @jsii.member(jsii_name="apiSchema")
    def _api_schema(self) -> _ApiSchema_5ce0490e:
        '''Gets the API schema for the resolved version.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, _props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call.

        :param _props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f1a9f42188fe25ae2c4ea7136182c012ef92c3439856928f7d7a900e86265523)
            check_type(argname="argument _props", value=_props, expected_type=type_hints["_props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [_props]))

    @jsii.member(jsii_name="defaultLocation")
    def _default_location(self) -> builtins.str:
        '''Provides default location for Private DNS Zones (global resource).'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultLocation", []))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Private DNS Zone.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7469f2d59c06a35e3520ba55a80bb874cf0c48f815311d2e3f683e8d8e250a7e)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Private DNS Zones.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="internalId")
    def internal_id(self) -> builtins.str:
        '''Get the internal identifier for the Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "internalId"))

    @builtins.property
    @jsii.member(jsii_name="internalIdOutput")
    def internal_id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "internalIdOutput"))

    @builtins.property
    @jsii.member(jsii_name="locationOutput")
    def location_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "locationOutput"))

    @builtins.property
    @jsii.member(jsii_name="maxNumberOfRecordSets")
    def max_number_of_record_sets(self) -> builtins.str:
        '''Get the maximum number of record sets that can be created in this Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "maxNumberOfRecordSets"))

    @builtins.property
    @jsii.member(jsii_name="maxNumberOfRecordSetsOutput")
    def max_number_of_record_sets_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "maxNumberOfRecordSetsOutput"))

    @builtins.property
    @jsii.member(jsii_name="maxNumberOfVirtualNetworkLinks")
    def max_number_of_virtual_network_links(self) -> builtins.str:
        '''Get the maximum number of virtual network links that can be created in this Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "maxNumberOfVirtualNetworkLinks"))

    @builtins.property
    @jsii.member(jsii_name="maxNumberOfVirtualNetworkLinksOutput")
    def max_number_of_virtual_network_links_output(
        self,
    ) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "maxNumberOfVirtualNetworkLinksOutput"))

    @builtins.property
    @jsii.member(jsii_name="maxNumberOfVirtualNetworkLinksWithRegistration")
    def max_number_of_virtual_network_links_with_registration(self) -> builtins.str:
        '''Get the maximum number of virtual network links with auto-registration that can be created in this Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "maxNumberOfVirtualNetworkLinksWithRegistration"))

    @builtins.property
    @jsii.member(jsii_name="maxNumberOfVirtualNetworkLinksWithRegistrationOutput")
    def max_number_of_virtual_network_links_with_registration_output(
        self,
    ) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "maxNumberOfVirtualNetworkLinksWithRegistrationOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="numberOfRecordSets")
    def number_of_record_sets(self) -> builtins.str:
        '''Get the current number of record sets in this Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "numberOfRecordSets"))

    @builtins.property
    @jsii.member(jsii_name="numberOfRecordSetsOutput")
    def number_of_record_sets_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "numberOfRecordSetsOutput"))

    @builtins.property
    @jsii.member(jsii_name="numberOfVirtualNetworkLinksWithRegistration")
    def number_of_virtual_network_links_with_registration(self) -> builtins.str:
        '''Get the current number of virtual network links with auto-registration in this Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "numberOfVirtualNetworkLinksWithRegistration"))

    @builtins.property
    @jsii.member(jsii_name="numberOfVirtualNetworkLinksWithRegistrationOutput")
    def number_of_virtual_network_links_with_registration_output(
        self,
    ) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "numberOfVirtualNetworkLinksWithRegistrationOutput"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "PrivateDnsZoneProps":
        return typing.cast("PrivateDnsZoneProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Private DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="provisioningStateOutput")
    def provisioning_state_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "provisioningStateOutput"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_privatednszone.PrivateDnsZoneBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class PrivateDnsZoneBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Private DNS Zone API calls This matches the Azure REST API schema.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82474e42972ae6325b6e2bda187431af80d0289a7b4cf87bd94b5262eb31f1e9)
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "location": location,
        }
        if properties is not None:
            self._values["properties"] = properties
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def location(self) -> builtins.str:
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PrivateDnsZoneBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_privatednszone.PrivateDnsZoneProps",
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
        "ignore_changes": "ignoreChanges",
        "resource_group_id": "resourceGroupId",
    },
)
class PrivateDnsZoneProps(_AzapiResourceProps_141a2340):
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
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Private DNS Zone.

        Extends AzapiResourceProps with Private DNS Zone specific properties

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
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param resource_group_id: Resource group ID where the Private DNS Zone will be created.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e0ffc37a6bab0926aab13cedd20ed5a99aee97e14321707fba04cab2de074290)
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
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
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
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
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
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the Private DNS Zone will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PrivateDnsZoneProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "PrivateDnsZone",
    "PrivateDnsZoneBody",
    "PrivateDnsZoneProps",
]

publication.publish()

def _typecheckingstub__a33322a4540e130927932b239b2f69ffe4c8d2764185c487e6ce7b329fd6b8b0(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__52038be3ed4336755627549f21019a71b7d1154cb8abef5a6aea1d337a194673(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1a9f42188fe25ae2c4ea7136182c012ef92c3439856928f7d7a900e86265523(
    _props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7469f2d59c06a35e3520ba55a80bb874cf0c48f815311d2e3f683e8d8e250a7e(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82474e42972ae6325b6e2bda187431af80d0289a7b4cf87bd94b5262eb31f1e9(
    *,
    location: builtins.str,
    properties: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e0ffc37a6bab0926aab13cedd20ed5a99aee97e14321707fba04cab2de074290(
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
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
