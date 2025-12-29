r'''
# Azure DNS Zone Construct (AZAPI)

This Construct represents a DNS Zone in Azure using the AZAPI provider for direct Azure REST API access.

## What is Azure DNS Zone?

Azure DNS is a hosting service for DNS domains that provides name resolution using Microsoft Azure infrastructure. DNS zones are containers for DNS records for a particular domain. Azure DNS supports both public DNS zones (accessible from the Internet) and private DNS zones (accessible only from specified virtual networks).

**Key Features:**

* Host your DNS domain on Azure's global anycast network
* Manage DNS records using Azure tools and APIs
* Support for both public and private DNS zones
* Integration with Azure virtual networks for private DNS
* High availability and fast DNS responses
* Support for DNSSEC (coming soon)
* Built-in DDoS protection

You can learn more about Azure DNS in the [official Azure documentation](https://docs.microsoft.com/azure/dns/dns-overview).

## AZAPI Provider Benefits

This DNS Zone construct uses the AZAPI provider, which provides:

* **Direct Azure REST API Access**: No dependency on AzureRM provider limitations
* **Immediate Feature Access**: Get new Azure features as soon as they're available
* **Version-Specific Implementations**: Support for multiple API versions
* **Enhanced Type Safety**: Better IDE support and compile-time validation

## Best Practices

### Public DNS Zones

* **Use descriptive names**: DNS zone names should match your domain (e.g., `contoso.com`)
* **Configure at registrar**: Update your domain registrar with Azure DNS name servers
* **Monitor DNS queries**: Use diagnostic settings to track DNS usage and issues
* **Implement tags**: Tag DNS zones for cost management and organization
* **Plan for TTL**: Consider Time To Live (TTL) values for your DNS records

### Private DNS Zones

* **Link to virtual networks**: Associate private DNS zones with your Azure virtual networks
* **Use for internal services**: Ideal for internal application communication
* **Consider auto-registration**: Enable VM hostname auto-registration when appropriate
* **Plan network topology**: Design DNS resolution strategy for hub-spoke or complex networks

## Properties

This Construct supports the following properties:

### Required Properties

* **`name`**: (Required) The name of the DNS Zone (without a terminating dot). Must be a valid domain name.
* **`location`**: (Required) The Azure region (typically "global" for DNS zones as they are global resources)

### Optional Properties

* **`resourceGroupId`**: (Optional) The resource ID of the resource group where the DNS zone will be created
* **`zoneType`**: (Optional) The type of DNS zone: "Public" (default) or "Private"
* **`registrationVirtualNetworks`**: (Optional) Array of virtual network references that register hostnames (Private zones only)
* **`resolutionVirtualNetworks`**: (Optional) Array of virtual network references that resolve DNS records (Private zones only)
* **`tags`**: (Optional) Key-value pairs for resource tagging and organization
* **`ignoreChanges`**: (Optional) Lifecycle rules to ignore changes for specific properties
* **`apiVersion`**: (Optional) Explicit API version to use (defaults to latest: "2018-05-01")

## Supported API Versions

| API Version | Status  | Features                                          |
|-------------|---------|---------------------------------------------------|
| 2018-05-01  | ✅ Latest | Full support for public and private DNS zones    |

## Basic Usage

### Public DNS Zone

```python
import { DnsZone } from "@microsoft/terraform-cdk-constructs/azure-dnszone";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";

// Create a resource group
const resourceGroup = new ResourceGroup(this, 'rg', {
  name: 'dns-rg',
  location: 'eastus',
});

// Create a public DNS zone
const dnsZone = new DnsZone(this, 'publicDns', {
  name: 'contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  tags: {
    environment: 'production',
    service: 'dns',
  },
});

// Access name servers for domain registrar configuration
console.log('Configure these name servers at your domain registrar:');
console.log(dnsZone.nameServers);
```

### Private DNS Zone

```python
import { DnsZone } from "@microsoft/terraform-cdk-constructs/azure-dnszone";
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

// Create a private DNS zone linked to virtual network
const privateDnsZone = new DnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  zoneType: 'Private',
  registrationVirtualNetworks: [
    { id: vnet.id }
  ],
  tags: {
    environment: 'production',
    type: 'private',
  },
});
```

## Advanced Features

### Version Pinning

Pin to a specific API version for stability:

```python
const dnsZone = new DnsZone(this, 'dns', {
  name: 'contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  apiVersion: '2018-05-01', // Pin to specific version
});
```

### Ignore Changes

Prevent Terraform from detecting changes to specific properties:

```python
const dnsZone = new DnsZone(this, 'dns', {
  name: 'contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  ignoreChanges: ['tags'], // Ignore tag changes
});
```

### Multiple Virtual Network Links (Private DNS)

Link a private DNS zone to multiple virtual networks:

```python
const privateDnsZone = new DnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  zoneType: 'Private',
  registrationVirtualNetworks: [
    { id: hubVnet.id },
  ],
  resolutionVirtualNetworks: [
    { id: spoke1Vnet.id },
    { id: spoke2Vnet.id },
  ],
});
```

### Tag Management

Add and remove tags programmatically:

```python
const dnsZone = new DnsZone(this, 'dns', {
  name: 'contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  tags: {
    environment: 'production',
  },
});

// Add a tag
dnsZone.addTag('owner', 'platform-team');

// Remove a tag
dnsZone.removeTag('environment');
```

## Outputs

The DNS Zone construct provides several outputs for use in other resources:

```python
// Resource ID
console.log(dnsZone.id);

// DNS Zone name
console.log(dnsZone.name);

// Location
console.log(dnsZone.location);

// Name servers (for domain registrar configuration)
console.log(dnsZone.nameServers);

// Maximum number of record sets
console.log(dnsZone.maxNumberOfRecordSets);

// Current number of record sets
console.log(dnsZone.numberOfRecordSets);

// Zone type
console.log(dnsZone.zoneType); // "Public" or "Private"

// Terraform outputs
dnsZone.idOutput;           // Terraform output for ID
dnsZone.nameOutput;         // Terraform output for name
dnsZone.nameServersOutput;  // Terraform output for name servers
```

## Configuring Your Domain

After creating a public DNS zone, you need to configure your domain registrar to use Azure DNS name servers:

1. Get the name servers from your DNS zone:

   ```python
   console.log(dnsZone.nameServers);
   ```
2. Update your domain's name server records at your registrar with the Azure DNS name servers (typically 4 name servers like `ns1-01.azure-dns.com`)
3. Wait for DNS propagation (can take up to 48 hours, but usually much faster)
4. Verify the delegation using DNS tools:

   ```bash
   nslookup -type=NS contoso.com
   ```

## Common Patterns

### Hub-Spoke Topology with Private DNS

```python
// Create hub virtual network and private DNS zone
const hubVnet = new VirtualNetwork(this, 'hub', {
  name: 'hub-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: ['10.0.0.0/16'],
});

const privateDnsZone = new DnsZone(this, 'privateDns', {
  name: 'internal.contoso.com',
  location: 'global',
  resourceGroupId: resourceGroup.id,
  zoneType: 'Private',
  registrationVirtualNetworks: [
    { id: hubVnet.id }
  ],
});

// Spoke networks can resolve DNS through peering
const spoke1Vnet = new VirtualNetwork(this, 'spoke1', {
  name: 'spoke1-vnet',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  addressSpace: ['10.1.0.0/16'],
});
```

### Multi-Environment DNS Strategy

```python
// Production
const prodDnsZone = new DnsZone(this, 'prodDns', {
  name: 'contoso.com',
  location: 'global',
  resourceGroupId: prodResourceGroup.id,
  tags: { environment: 'production' },
});

// Staging
const stagingDnsZone = new DnsZone(this, 'stagingDns', {
  name: 'staging.contoso.com',
  location: 'global',
  resourceGroupId: stagingResourceGroup.id,
  tags: { environment: 'staging' },
});

// Development
const devDnsZone = new DnsZone(this, 'devDns', {
  name: 'dev.contoso.com',
  location: 'global',
  resourceGroupId: devResourceGroup.id,
  tags: { environment: 'development' },
});
```

## Error Handling

The construct includes built-in validation:

```python
// Invalid domain name (will fail validation)
const dnsZone = new DnsZone(this, 'dns', {
  name: 'contoso.com.', // ❌ No terminating dot allowed
  location: 'global',
  resourceGroupId: resourceGroup.id,
});

// Valid domain name
const dnsZone = new DnsZone(this, 'dns', {
  name: 'contoso.com', // ✅ Correct format
  location: 'global',
  resourceGroupId: resourceGroup.id,
});
```

## Troubleshooting

### Name Server Propagation

If DNS queries aren't working:

1. Verify name servers are correctly configured at your registrar
2. Check DNS propagation: `dig NS contoso.com` or use online tools
3. Ensure sufficient time has passed for propagation (up to 48 hours)

### Private DNS Resolution

If private DNS isn't resolving:

1. Verify virtual network links are correctly configured
2. Check that VMs are using Azure DNS (168.63.129.16)
3. Ensure virtual network peering is properly set up
4. Verify NSG rules aren't blocking DNS traffic

### API Version Issues

If you encounter version-related errors:

1. Check supported API versions in this README
2. Consider pinning to a specific version
3. Review Azure DNS API documentation for breaking changes

## Related Constructs

* **DNS Record Sets**: Use separate constructs for A, AAAA, CNAME, MX, TXT, and other DNS records
* **Virtual Network**: Required for private DNS zones
* **Resource Group**: Container for DNS zone resources

## References

* [Azure DNS Documentation](https://docs.microsoft.com/azure/dns/)
* [Azure DNS REST API Reference](https://docs.microsoft.com/rest/api/dns/)
* [DNS Zone Best Practices](https://docs.microsoft.com/azure/dns/dns-best-practices)
* [Private DNS Documentation](https://docs.microsoft.com/azure/dns/private-dns-overview)
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


class DnsZone(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnszone.DnsZone",
):
    '''Unified Azure DNS Zone implementation.

    This class provides a single, version-aware implementation that replaces all
    version-specific DNS Zone classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Azure DNS Zones are global resources used to host DNS records for a domain.
    They can be either Public (Internet-accessible) or Private (accessible only
    from specified virtual networks).

    Example::

        // DNS zone with explicit version pinning:
        const dnsZone = new DnsZone(this, "dns", {
          name: "contoso.com",
          location: "global",
          resourceGroupId: resourceGroup.id,
          apiVersion: "2018-05-01",
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        registration_virtual_networks: typing.Optional[typing.Sequence[typing.Union["VirtualNetworkReference", typing.Dict[builtins.str, typing.Any]]]] = None,
        resolution_virtual_networks: typing.Optional[typing.Sequence[typing.Union["VirtualNetworkReference", typing.Dict[builtins.str, typing.Any]]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        zone_type: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure DNS Zone using the VersionedAzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param registration_virtual_networks: A list of references to virtual networks that register hostnames in this DNS zone Only valid when zoneType is Private.
        :param resolution_virtual_networks: A list of references to virtual networks that resolve records in this DNS zone Only valid when zoneType is Private.
        :param resource_group_id: Resource group ID where the DNS Zone will be created.
        :param zone_type: The type of this DNS zone (Public or Private). Default: "Public"
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
            type_hints = typing.get_type_hints(_typecheckingstub__aee912c8e3e07a0b51b4711d2da81f67fa4442b423f7fd330937c643aaa15b6b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DnsZoneProps(
            ignore_changes=ignore_changes,
            registration_virtual_networks=registration_virtual_networks,
            resolution_virtual_networks=resolution_virtual_networks,
            resource_group_id=resource_group_id,
            zone_type=zone_type,
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
        '''Add a tag to the DNS Zone.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77e00bcb3c7f63b6db78ef385d519763624fa0638483ae95d4acad2278e1a73a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__0d5b3d955f84bf7e070a23100471e1fb6b3e5c64e2eeb630e4af1ff22e8e3a64)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultLocation")
    def _default_location(self) -> builtins.str:
        '''Provides default location for DNS Zones (global resource).'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultLocation", []))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the DNS Zone.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__999cd220e27d042b17a258f2c8120a7835ab7b1d0d6b4c54ae1ee70173975bae)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for DNS Zones.'''
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
    @jsii.member(jsii_name="maxNumberOfRecordSets")
    def max_number_of_record_sets(self) -> builtins.str:
        '''Get the maximum number of record sets that can be created in this DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "maxNumberOfRecordSets"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameServers")
    def name_servers(self) -> builtins.str:
        '''Get the name servers for the DNS Zone These are the Azure DNS name servers that should be configured at your domain registrar.'''
        return typing.cast(builtins.str, jsii.get(self, "nameServers"))

    @builtins.property
    @jsii.member(jsii_name="nameServersOutput")
    def name_servers_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameServersOutput"))

    @builtins.property
    @jsii.member(jsii_name="numberOfRecordSets")
    def number_of_record_sets(self) -> builtins.str:
        '''Get the current number of record sets in this DNS zone.'''
        return typing.cast(builtins.str, jsii.get(self, "numberOfRecordSets"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "DnsZoneProps":
        return typing.cast("DnsZoneProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))

    @builtins.property
    @jsii.member(jsii_name="zoneType")
    def zone_type(self) -> builtins.str:
        '''Get the zone type (Public or Private).'''
        return typing.cast(builtins.str, jsii.get(self, "zoneType"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnszone.DnsZoneBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class DnsZoneBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure DNS Zone API calls This matches the Azure REST API schema.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e8c7d0cb3047ab5191de4fe254097e405b30c7b01bfd94e44e5ea51281e48fc2)
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
        return "DnsZoneBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnszone.DnsZoneProps",
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
        "registration_virtual_networks": "registrationVirtualNetworks",
        "resolution_virtual_networks": "resolutionVirtualNetworks",
        "resource_group_id": "resourceGroupId",
        "zone_type": "zoneType",
    },
)
class DnsZoneProps(_AzapiResourceProps_141a2340):
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
        registration_virtual_networks: typing.Optional[typing.Sequence[typing.Union["VirtualNetworkReference", typing.Dict[builtins.str, typing.Any]]]] = None,
        resolution_virtual_networks: typing.Optional[typing.Sequence[typing.Union["VirtualNetworkReference", typing.Dict[builtins.str, typing.Any]]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        zone_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure DNS Zone.

        Extends AzapiResourceProps with DNS Zone specific properties

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
        :param registration_virtual_networks: A list of references to virtual networks that register hostnames in this DNS zone Only valid when zoneType is Private.
        :param resolution_virtual_networks: A list of references to virtual networks that resolve records in this DNS zone Only valid when zoneType is Private.
        :param resource_group_id: Resource group ID where the DNS Zone will be created.
        :param zone_type: The type of this DNS zone (Public or Private). Default: "Public"
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__572d018393e48c6c8661dd34e1ff7792e7d915187e1bb730f30cea9041334487)
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
            check_type(argname="argument registration_virtual_networks", value=registration_virtual_networks, expected_type=type_hints["registration_virtual_networks"])
            check_type(argname="argument resolution_virtual_networks", value=resolution_virtual_networks, expected_type=type_hints["resolution_virtual_networks"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument zone_type", value=zone_type, expected_type=type_hints["zone_type"])
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
        if registration_virtual_networks is not None:
            self._values["registration_virtual_networks"] = registration_virtual_networks
        if resolution_virtual_networks is not None:
            self._values["resolution_virtual_networks"] = resolution_virtual_networks
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if zone_type is not None:
            self._values["zone_type"] = zone_type

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
    def registration_virtual_networks(
        self,
    ) -> typing.Optional[typing.List["VirtualNetworkReference"]]:
        '''A list of references to virtual networks that register hostnames in this DNS zone Only valid when zoneType is Private.'''
        result = self._values.get("registration_virtual_networks")
        return typing.cast(typing.Optional[typing.List["VirtualNetworkReference"]], result)

    @builtins.property
    def resolution_virtual_networks(
        self,
    ) -> typing.Optional[typing.List["VirtualNetworkReference"]]:
        '''A list of references to virtual networks that resolve records in this DNS zone Only valid when zoneType is Private.'''
        result = self._values.get("resolution_virtual_networks")
        return typing.cast(typing.Optional[typing.List["VirtualNetworkReference"]], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the DNS Zone will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def zone_type(self) -> typing.Optional[builtins.str]:
        '''The type of this DNS zone (Public or Private).

        :default: "Public"
        '''
        result = self._values.get("zone_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsZoneProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnszone.VirtualNetworkReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class VirtualNetworkReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Virtual network reference for private DNS zones.

        :param id: The resource ID of the virtual network.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__84105e85dba305bf4f10fea1bdb25d1e26a51d8e4c5e9724adb1a68347ecbd28)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''The resource ID of the virtual network.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DnsZone",
    "DnsZoneBody",
    "DnsZoneProps",
    "VirtualNetworkReference",
]

publication.publish()

def _typecheckingstub__aee912c8e3e07a0b51b4711d2da81f67fa4442b423f7fd330937c643aaa15b6b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    registration_virtual_networks: typing.Optional[typing.Sequence[typing.Union[VirtualNetworkReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    resolution_virtual_networks: typing.Optional[typing.Sequence[typing.Union[VirtualNetworkReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    zone_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__77e00bcb3c7f63b6db78ef385d519763624fa0638483ae95d4acad2278e1a73a(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d5b3d955f84bf7e070a23100471e1fb6b3e5c64e2eeb630e4af1ff22e8e3a64(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__999cd220e27d042b17a258f2c8120a7835ab7b1d0d6b4c54ae1ee70173975bae(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e8c7d0cb3047ab5191de4fe254097e405b30c7b01bfd94e44e5ea51281e48fc2(
    *,
    location: builtins.str,
    properties: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__572d018393e48c6c8661dd34e1ff7792e7d915187e1bb730f30cea9041334487(
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
    registration_virtual_networks: typing.Optional[typing.Sequence[typing.Union[VirtualNetworkReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    resolution_virtual_networks: typing.Optional[typing.Sequence[typing.Union[VirtualNetworkReference, typing.Dict[builtins.str, typing.Any]]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    zone_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__84105e85dba305bf4f10fea1bdb25d1e26a51d8e4c5e9724adb1a68347ecbd28(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass
