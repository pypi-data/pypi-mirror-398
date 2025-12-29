r'''
# Azure DNS Forwarding Ruleset

This package provides constructs for managing Azure DNS Forwarding Rulesets and their child resources, enabling conditional DNS forwarding for hybrid and multi-cloud scenarios.

## Overview

Azure DNS Forwarding Rulesets work with DNS Resolver Outbound Endpoints to enable conditional forwarding of DNS queries based on domain names. This is essential for hybrid DNS scenarios where Azure resources need to resolve names from on-premises or other external DNS servers.

### Key Components

1. **DNS Forwarding Ruleset** - The parent resource that contains forwarding rules and links to virtual networks
2. **Forwarding Rules** - Define which domains to forward and where to forward them
3. **Virtual Network Links** - Connect virtual networks to the ruleset so they can use the forwarding rules

## Architecture

```
DNS Resolver (Parent)
    └── Outbound Endpoint (Child)
            └── DNS Forwarding Ruleset (uses)
                    ├── Forwarding Rules (Child)
                    └── Virtual Network Links (Child)
```

## Installation

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Usage

### Basic Example

```python
import { DnsForwardingRuleset, ForwardingRule, DnsForwardingRulesetVirtualNetworkLink } from '@microsoft/terraform-cdk-constructs/azure-dnsforwardingruleset';
import { DnsResolver } from '@microsoft/terraform-cdk-constructs/azure-dnsresolver';
import { DnsResolverOutboundEndpoint } from '@microsoft/terraform-cdk-constructs/azure-dnsresolver';

// Create DNS Resolver and Outbound Endpoint first
const resolver = new DnsResolver(stack, 'resolver', {
  name: 'my-resolver',
  location: 'eastus',
  resourceGroupId: rg.id,
  virtualNetworkId: vnet.id,
});

const outboundEndpoint = new DnsResolverOutboundEndpoint(stack, 'outbound', {
  name: 'outbound-ep',
  location: 'eastus',
  dnsResolverId: resolver.id,
  subnetId: subnet.id,
});

// Create DNS Forwarding Ruleset
const ruleset = new DnsForwardingRuleset(stack, 'ruleset', {
  name: 'my-ruleset',
  location: 'eastus',
  resourceGroupId: rg.id,
  dnsResolverOutboundEndpointIds: [outboundEndpoint.id],
  tags: {
    environment: 'production',
  },
});

// Add Forwarding Rule
const rule = new ForwardingRule(stack, 'rule', {
  name: 'contoso-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'contoso.com.',
  targetDnsServers: [
    { ipAddress: '10.0.0.4', port: 53 },
    { ipAddress: '10.0.0.5' },  // Port defaults to 53
  ],
  forwardingRuleState: 'Enabled',
});

// Link VNet to Ruleset
const link = new DnsForwardingRulesetVirtualNetworkLink(stack, 'link', {
  name: 'vnet-link',
  dnsForwardingRulesetId: ruleset.id,
  virtualNetworkId: vnet.id,
});
```

### Multiple Forwarding Rules

```python
// Forward corporate domain
new ForwardingRule(stack, 'corp-rule', {
  name: 'corp-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'corp.contoso.com.',
  targetDnsServers: [
    { ipAddress: '10.1.0.4' },
    { ipAddress: '10.1.0.5' },
  ],
  metadata: {
    owner: 'it-team',
    purpose: 'corporate-dns',
  },
});

// Forward partner domain
new ForwardingRule(stack, 'partner-rule', {
  name: 'partner-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'partner.external.com.',
  targetDnsServers: [
    { ipAddress: '192.168.1.10', port: 5353 },
  ],
  forwardingRuleState: 'Enabled',
});
```

### Disabled Rule (for testing)

```python
new ForwardingRule(stack, 'test-rule', {
  name: 'test-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'test.local.',
  targetDnsServers: [{ ipAddress: '10.0.0.100' }],
  forwardingRuleState: 'Disabled',  // Rule exists but won't be used
});
```

### Multiple VNet Links

```python
// Link production VNet
new DnsForwardingRulesetVirtualNetworkLink(stack, 'prod-link', {
  name: 'prod-vnet-link',
  dnsForwardingRulesetId: ruleset.id,
  virtualNetworkId: prodVnet.id,
  metadata: {
    environment: 'production',
  },
});

// Link development VNet
new DnsForwardingRulesetVirtualNetworkLink(stack, 'dev-link', {
  name: 'dev-vnet-link',
  dnsForwardingRulesetId: ruleset.id,
  virtualNetworkId: devVnet.id,
  metadata: {
    environment: 'development',
  },
});
```

## How It Works

1. **DNS Query Flow**:

   * VM in linked VNet makes DNS query for `app.contoso.com`
   * Query goes to Azure DNS
   * Azure DNS checks if domain matches any forwarding rule
   * If match found, query is forwarded via Outbound Endpoint to target DNS servers
   * Response is returned to the VM
2. **Rule Matching**:

   * Rules are matched based on domain name suffix
   * Most specific match wins (e.g., `app.contoso.com.` matches `app.contoso.com.` before `contoso.com.`)
   * Domain names must end with a dot for FQDN
3. **VNet Linking**:

   * Only VMs in linked VNets can use the forwarding rules
   * Multiple VNets can be linked to the same ruleset
   * Each VNet can only be linked to one ruleset per DNS resolver

## Use Cases

### Hybrid DNS Resolution

Forward on-premises domain queries to on-premises DNS servers:

```python
new ForwardingRule(stack, 'onprem-rule', {
  name: 'onprem-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'onprem.corp.',
  targetDnsServers: [
    { ipAddress: '10.10.0.10' },  // On-premises DNS
    { ipAddress: '10.10.0.11' },  // Secondary on-premises DNS
  ],
});
```

### Split-Horizon DNS

Different resolution for internal vs. external:

```python
// Internal resolution for app.contoso.com
new ForwardingRule(stack, 'internal-rule', {
  name: 'internal-app-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'app.contoso.com.',
  targetDnsServers: [
    { ipAddress: '10.0.1.10' },  // Internal app DNS
  ],
});
```

### Multi-Cloud DNS

Forward queries to another cloud provider:

```python
new ForwardingRule(stack, 'aws-rule', {
  name: 'aws-rule',
  dnsForwardingRulesetId: ruleset.id,
  domainName: 'aws.mycompany.com.',
  targetDnsServers: [
    { ipAddress: '172.16.0.10' },  // AWS DNS endpoint via VPN
  ],
});
```

## Limits and Quotas

* **Rules per Ruleset**: Maximum 1,000
* **Target DNS Servers per Rule**: Maximum 6
* **VNet Links per Ruleset**: Maximum 500
* **Rulesets per Subscription**: Maximum 15
* **Domain Name**: Maximum 255 characters, must end with dot

## Best Practices

1. **Use Specific Domain Names**: Create specific rules for subdomains rather than broad wildcards
2. **Multiple Target Servers**: Always configure at least 2 target DNS servers for high availability
3. **Monitor Rules**: Regularly review and remove unused rules
4. **Metadata Tags**: Use metadata/tags for organization and cost tracking
5. **Testing**: Use disabled rules to test configurations before enabling
6. **Naming Convention**: Use clear, descriptive names for rules and links

## Troubleshooting

### DNS Queries Not Being Forwarded

**Check**:

1. VNet is linked to the ruleset
2. Forwarding rule state is "Enabled"
3. Domain name ends with a dot (.)
4. Outbound endpoint is in "Succeeded" state

### Timeouts or Failed Queries

**Check**:

1. Target DNS servers are reachable from the outbound endpoint subnet
2. Network security groups allow outbound UDP/53 traffic
3. Target DNS servers are responding correctly
4. Firewall rules allow traffic from Azure IP ranges

### Rule Not Matching

**Check**:

1. Domain name in rule matches exactly (including trailing dot)
2. Most specific rule takes precedence
3. Check for typos in domain names

## Properties Reference

### DnsForwardingRuleset

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the ruleset |
| `location` | string | Yes | Azure region |
| `resourceGroupId` | string | Yes | Resource group ID |
| `dnsResolverOutboundEndpointIds` | string[] | Yes | Array of outbound endpoint IDs |
| `tags` | object | No | Resource tags |
| `apiVersion` | string | No | API version (default: 2022-07-01) |

### ForwardingRule

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the rule |
| `dnsForwardingRulesetId` | string | Yes | Parent ruleset ID |
| `domainName` | string | Yes | Domain to forward (must end with .) |
| `targetDnsServers` | TargetDnsServer[] | Yes | Target DNS servers (max 6) |
| `forwardingRuleState` | string | No | "Enabled" or "Disabled" (default: "Enabled") |
| `metadata` | object | No | Key-value metadata |
| `apiVersion` | string | No | API version (default: 2022-07-01) |

#### TargetDnsServer

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `ipAddress` | string | Yes | IP address of DNS server |
| `port` | number | No | Port number (default: 53) |

### DnsForwardingRulesetVirtualNetworkLink

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | Yes | Name of the link |
| `dnsForwardingRulesetId` | string | Yes | Parent ruleset ID |
| `virtualNetworkId` | string | Yes | VNet ID to link |
| `metadata` | object | No | Key-value metadata |
| `apiVersion` | string | No | API version (default: 2022-07-01) |

## Examples

See the [integration test](./test/dns-forwarding-ruleset.integ.ts) for a complete working example.

## Related Resources

* [Azure DNS Resolver](../azure-dnsresolver/README.md)
* [Azure Private DNS Zones](../azure-privatednszone/README.md)
* [Azure Virtual Networks](../azure-virtualnetwork/README.md)

## API Documentation

* [DNS Forwarding Rulesets REST API](https://learn.microsoft.com/rest/api/dns/dnsforwardingrulesets)
* [Forwarding Rules REST API](https://learn.microsoft.com/rest/api/dns/dnsforwardingrulesets/forwardingrules)
* [Virtual Network Links REST API](https://learn.microsoft.com/rest/api/dns/dnsforwardingrulesets/virtualnetworklinks)
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


class DnsForwardingRuleset(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRuleset",
):
    '''Unified Azure DNS Forwarding Ruleset implementation.

    This class provides a unified implementation for creating DNS Forwarding Rulesets
    that enable conditional forwarding of DNS queries. Rulesets work with DNS Resolver
    Outbound Endpoints to route queries to specific target DNS servers based on domain names.

    Key Requirements:

    - Requires at least one DNS Resolver Outbound Endpoint
    - Each ruleset can contain up to 1000 forwarding rules
    - Regional resource (must match outbound endpoint location)
    - Can be linked to multiple virtual networks

    Example::

        // DNS forwarding ruleset with explicit version pinning:
        const ruleset = new DnsForwardingRuleset(this, "ruleset", {
          name: "my-ruleset",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          dnsResolverOutboundEndpointIds: [outboundEndpoint.id],
          apiVersion: "2022-07-01",
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        dns_resolver_outbound_endpoint_ids: typing.Sequence[builtins.str],
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
        '''Creates a new Azure DNS Forwarding Ruleset using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param dns_resolver_outbound_endpoint_ids: Array of resource IDs of DNS Resolver Outbound Endpoints The ruleset uses these endpoints to forward DNS queries based on the rules.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param resource_group_id: Resource group ID where the DNS Forwarding Ruleset will be created.
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
            type_hints = typing.get_type_hints(_typecheckingstub__8d15d325ac27a73f041f5be36fd1e671dfc8ec1d70a4c97974b17fd80e7194f8)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DnsForwardingRulesetProps(
            dns_resolver_outbound_endpoint_ids=dns_resolver_outbound_endpoint_ids,
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
        '''Add a tag to the DNS Forwarding Ruleset.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e6905418f9f9ad348439a6056e62eb842efc5e9dda232743f08bde5a05d8d7a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__dc27d70eb021810137744676e64fdfb226343a5c153191f2a256e9dca414485d)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the DNS Forwarding Ruleset.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2ee3d5446bb31f42500f46d46766237a2c4022aa60e365eef8cb975b77057019)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for DNS Forwarding Rulesets.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for DNS Forwarding Rulesets.'''
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
    def props(self) -> "DnsForwardingRulesetProps":
        return typing.cast("DnsForwardingRulesetProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the DNS Forwarding Ruleset.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="provisioningStateOutput")
    def provisioning_state_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "provisioningStateOutput"))

    @builtins.property
    @jsii.member(jsii_name="resourceGuid")
    def resource_guid(self) -> builtins.str:
        '''Get the unique identifier for the DNS Forwarding Ruleset resource.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceGuid"))

    @builtins.property
    @jsii.member(jsii_name="resourceGuidOutput")
    def resource_guid_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "resourceGuidOutput"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class DnsForwardingRulesetBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["DnsForwardingRulesetProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure DNS Forwarding Ruleset API calls This matches the Azure REST API schema.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = DnsForwardingRulesetProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7abf5a3fda837c6997881aa6392d792f8c713544229be655047d2d7a71bd322f)
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
    def properties(self) -> "DnsForwardingRulesetProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("DnsForwardingRulesetProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsForwardingRulesetBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetProperties",
    jsii_struct_bases=[],
    name_mapping={"dns_resolver_outbound_endpoints": "dnsResolverOutboundEndpoints"},
)
class DnsForwardingRulesetProperties:
    def __init__(
        self,
        *,
        dns_resolver_outbound_endpoints: typing.Sequence[typing.Union["DnsResolverOutboundEndpointReference", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''Properties for the DNS Forwarding Ruleset body.

        :param dns_resolver_outbound_endpoints: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__936dc2978060e67abc665e124fb38efe190d5eb1220a4627d536cc3654272c48)
            check_type(argname="argument dns_resolver_outbound_endpoints", value=dns_resolver_outbound_endpoints, expected_type=type_hints["dns_resolver_outbound_endpoints"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dns_resolver_outbound_endpoints": dns_resolver_outbound_endpoints,
        }

    @builtins.property
    def dns_resolver_outbound_endpoints(
        self,
    ) -> typing.List["DnsResolverOutboundEndpointReference"]:
        result = self._values.get("dns_resolver_outbound_endpoints")
        assert result is not None, "Required property 'dns_resolver_outbound_endpoints' is missing"
        return typing.cast(typing.List["DnsResolverOutboundEndpointReference"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsForwardingRulesetProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetProps",
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
        "dns_resolver_outbound_endpoint_ids": "dnsResolverOutboundEndpointIds",
        "ignore_changes": "ignoreChanges",
        "resource_group_id": "resourceGroupId",
    },
)
class DnsForwardingRulesetProps(_AzapiResourceProps_141a2340):
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
        dns_resolver_outbound_endpoint_ids: typing.Sequence[builtins.str],
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure DNS Forwarding Ruleset.

        Extends AzapiResourceProps with DNS Forwarding Ruleset specific properties

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
        :param dns_resolver_outbound_endpoint_ids: Array of resource IDs of DNS Resolver Outbound Endpoints The ruleset uses these endpoints to forward DNS queries based on the rules.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param resource_group_id: Resource group ID where the DNS Forwarding Ruleset will be created.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1d9f89a57d4994c047266e16c5feedf511fa683ba4a0fd579cdc8aab6fcc2d4a)
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
            check_type(argname="argument dns_resolver_outbound_endpoint_ids", value=dns_resolver_outbound_endpoint_ids, expected_type=type_hints["dns_resolver_outbound_endpoint_ids"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dns_resolver_outbound_endpoint_ids": dns_resolver_outbound_endpoint_ids,
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
    def dns_resolver_outbound_endpoint_ids(self) -> typing.List[builtins.str]:
        '''Array of resource IDs of DNS Resolver Outbound Endpoints The ruleset uses these endpoints to forward DNS queries based on the rules.

        Example::

            ["/subscriptions/.../dnsResolvers/resolver1/outboundEndpoints/endpoint1"]
        '''
        result = self._values.get("dns_resolver_outbound_endpoint_ids")
        assert result is not None, "Required property 'dns_resolver_outbound_endpoint_ids' is missing"
        return typing.cast(typing.List[builtins.str], result)

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
        '''Resource group ID where the DNS Forwarding Ruleset will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsForwardingRulesetProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DnsForwardingRulesetVirtualNetworkLink(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetVirtualNetworkLink",
):
    '''Azure DNS Forwarding Ruleset Virtual Network Link implementation.

    Virtual Network Links connect DNS Forwarding Rulesets to virtual networks,
    enabling those VNets to use the conditional forwarding rules defined in the ruleset.
    This allows VMs and other resources in the linked VNets to resolve domains according
    to the forwarding rules.

    Example::

        // Virtual network link with explicit version:
        const link = new DnsForwardingRulesetVirtualNetworkLink(this, "vnet-link", {
          name: "my-vnet-link",
          dnsForwardingRulesetId: ruleset.id,
          virtualNetworkId: vnet.id,
          apiVersion: "2022-07-01"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        dns_forwarding_ruleset_id: builtins.str,
        virtual_network_id: builtins.str,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
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
        '''Creates a new Azure DNS Forwarding Ruleset Virtual Network Link using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param dns_forwarding_ruleset_id: Resource ID of the parent DNS Forwarding Ruleset.
        :param virtual_network_id: Resource ID of the Virtual Network to link.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata attached to the virtual network link as key-value pairs.
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
            type_hints = typing.get_type_hints(_typecheckingstub__fa5a9b25305cc1e00a2e42d370bac05029f5fa88399761d861a1c6c2d3a86591)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DnsForwardingRulesetVirtualNetworkLinkProps(
            dns_forwarding_ruleset_id=dns_forwarding_ruleset_id,
            virtual_network_id=virtual_network_id,
            ignore_changes=ignore_changes,
            metadata=metadata,
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
        '''Gets the API schema for the resolved version.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__73ed7e7aa6f288ecc5bd354c21c895e19287c37c5bbe96b9765e1d8905e95ead)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Virtual Network Link Virtual Network Links are child resources of DNS Forwarding Rulesets.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__572e670c101933afc727f2b9572f93328b102ebcc2411f1b87c95d543774adde)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Network Links.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="metadata")
    def metadata(self) -> builtins.str:
        '''Get the metadata.'''
        return typing.cast(builtins.str, jsii.get(self, "metadata"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "DnsForwardingRulesetVirtualNetworkLinkProps":
        '''The input properties for this Virtual Network Link instance.'''
        return typing.cast("DnsForwardingRulesetVirtualNetworkLinkProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Virtual Network Link.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="provisioningStateOutput")
    def provisioning_state_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "provisioningStateOutput"))

    @builtins.property
    @jsii.member(jsii_name="resourceName")
    def resource_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceName"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetVirtualNetworkLinkBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class DnsForwardingRulesetVirtualNetworkLinkBody:
    def __init__(
        self,
        *,
        properties: typing.Union["DnsForwardingRulesetVirtualNetworkLinkProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Virtual Network Link API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = DnsForwardingRulesetVirtualNetworkLinkProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0c06b8564f8db22d0371485b4bf6e5aee6451856ba7bb95e9882a1610d78715)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "DnsForwardingRulesetVirtualNetworkLinkProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("DnsForwardingRulesetVirtualNetworkLinkProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsForwardingRulesetVirtualNetworkLinkBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetVirtualNetworkLinkProperties",
    jsii_struct_bases=[],
    name_mapping={"virtual_network": "virtualNetwork", "metadata": "metadata"},
)
class DnsForwardingRulesetVirtualNetworkLinkProperties:
    def __init__(
        self,
        *,
        virtual_network: typing.Union["DnsForwardingRulesetVirtualNetworkReference", typing.Dict[builtins.str, typing.Any]],
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Properties for Virtual Network Link body.

        :param virtual_network: 
        :param metadata: 
        '''
        if isinstance(virtual_network, dict):
            virtual_network = DnsForwardingRulesetVirtualNetworkReference(**virtual_network)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4c3e09a00909d7d24af89b42edbad6721a41855725eb7ecd801b4c25180dfea4)
            check_type(argname="argument virtual_network", value=virtual_network, expected_type=type_hints["virtual_network"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "virtual_network": virtual_network,
        }
        if metadata is not None:
            self._values["metadata"] = metadata

    @builtins.property
    def virtual_network(self) -> "DnsForwardingRulesetVirtualNetworkReference":
        result = self._values.get("virtual_network")
        assert result is not None, "Required property 'virtual_network' is missing"
        return typing.cast("DnsForwardingRulesetVirtualNetworkReference", result)

    @builtins.property
    def metadata(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("metadata")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsForwardingRulesetVirtualNetworkLinkProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetVirtualNetworkLinkProps",
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
        "dns_forwarding_ruleset_id": "dnsForwardingRulesetId",
        "virtual_network_id": "virtualNetworkId",
        "ignore_changes": "ignoreChanges",
        "metadata": "metadata",
    },
)
class DnsForwardingRulesetVirtualNetworkLinkProps(_AzapiResourceProps_141a2340):
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
        dns_forwarding_ruleset_id: builtins.str,
        virtual_network_id: builtins.str,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure DNS Forwarding Ruleset Virtual Network Link.

        Extends AzapiResourceProps with Virtual Network Link specific properties

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
        :param dns_forwarding_ruleset_id: Resource ID of the parent DNS Forwarding Ruleset.
        :param virtual_network_id: Resource ID of the Virtual Network to link.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata attached to the virtual network link as key-value pairs.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8d6b7cae9b9ea927a4a26343cf36a4de7a0b6b286b4b2595381c08999c8668c7)
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
            check_type(argname="argument dns_forwarding_ruleset_id", value=dns_forwarding_ruleset_id, expected_type=type_hints["dns_forwarding_ruleset_id"])
            check_type(argname="argument virtual_network_id", value=virtual_network_id, expected_type=type_hints["virtual_network_id"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dns_forwarding_ruleset_id": dns_forwarding_ruleset_id,
            "virtual_network_id": virtual_network_id,
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
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if metadata is not None:
            self._values["metadata"] = metadata

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
    def dns_forwarding_ruleset_id(self) -> builtins.str:
        '''Resource ID of the parent DNS Forwarding Ruleset.

        Example::

            "/subscriptions/.../resourceGroups/rg/providers/Microsoft.Network/dnsForwardingRulesets/ruleset1"
        '''
        result = self._values.get("dns_forwarding_ruleset_id")
        assert result is not None, "Required property 'dns_forwarding_ruleset_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def virtual_network_id(self) -> builtins.str:
        '''Resource ID of the Virtual Network to link.

        Example::

            "/subscriptions/.../resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1"
        '''
        result = self._values.get("virtual_network_id")
        assert result is not None, "Required property 'virtual_network_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["metadata"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def metadata(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Metadata attached to the virtual network link as key-value pairs.'''
        result = self._values.get("metadata")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DnsForwardingRulesetVirtualNetworkLinkProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsForwardingRulesetVirtualNetworkReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class DnsForwardingRulesetVirtualNetworkReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''Virtual Network reference for DNS Forwarding Ruleset link.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2c7d8faa424e77d0cc974950c02575dee65301abc7ac4dde399d0583468a6696)
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
        return "DnsForwardingRulesetVirtualNetworkReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.DnsResolverOutboundEndpointReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class DnsResolverOutboundEndpointReference:
    def __init__(self, *, id: builtins.str) -> None:
        '''DNS Resolver Outbound Endpoint reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0b6f564f3152c678558ba5f8ac30cc6162578f989af0c65d6806676e933ea0fb)
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
        return "DnsResolverOutboundEndpointReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ForwardingRule(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.ForwardingRule",
):
    '''Azure DNS Forwarding Rule implementation.

    Forwarding rules define conditional DNS forwarding behavior. When a DNS query
    matches the domain name pattern, it's forwarded to the specified target DNS servers.
    Up to 1000 rules can be configured per ruleset, with up to 6 target servers per rule.

    Example::

        // Disabled forwarding rule:
        const rule = new ForwardingRule(this, "rule", {
          name: "temp-rule",
          dnsForwardingRulesetId: ruleset.id,
          domainName: "temp.local.",
          targetDnsServers: [{ ipAddress: "10.0.0.4" }],
          forwardingRuleState: "Disabled"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        dns_forwarding_ruleset_id: builtins.str,
        domain_name: builtins.str,
        target_dns_servers: typing.Sequence[typing.Union["TargetDnsServer", typing.Dict[builtins.str, typing.Any]]],
        forwarding_rule_state: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
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
        '''Creates a new Azure DNS Forwarding Rule using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param dns_forwarding_ruleset_id: Resource ID of the parent DNS Forwarding Ruleset.
        :param domain_name: The domain name to forward (must end with a dot for FQDN).
        :param target_dns_servers: Array of target DNS servers to forward queries to Maximum of 6 servers per rule.
        :param forwarding_rule_state: The state of the forwarding rule. Default: "Enabled"
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata attached to the forwarding rule as key-value pairs.
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
            type_hints = typing.get_type_hints(_typecheckingstub__77c89b6d2a71359ccb7f25356f12a64037ad7a4ffc479ce6a0f2b33f58a4c9df)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ForwardingRuleProps(
            dns_forwarding_ruleset_id=dns_forwarding_ruleset_id,
            domain_name=domain_name,
            target_dns_servers=target_dns_servers,
            forwarding_rule_state=forwarding_rule_state,
            ignore_changes=ignore_changes,
            metadata=metadata,
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
        '''Gets the API schema for the resolved version.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__abefc2cde23b36b222a00c9bcbfd8592c1b1869d0022b8f2460106672cb68631)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Forwarding Rule Forwarding Rules are child resources of DNS Forwarding Rulesets.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ae896f931e124d78e046913d5e7bdebe744effedaf00979923f3bbe265f788a7)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Forwarding Rules.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="metadata")
    def metadata(self) -> builtins.str:
        '''Get the metadata.'''
        return typing.cast(builtins.str, jsii.get(self, "metadata"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "ForwardingRuleProps":
        '''The input properties for this Forwarding Rule instance.'''
        return typing.cast("ForwardingRuleProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Forwarding Rule.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="provisioningStateOutput")
    def provisioning_state_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "provisioningStateOutput"))

    @builtins.property
    @jsii.member(jsii_name="resourceName")
    def resource_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceName"))

    @builtins.property
    @jsii.member(jsii_name="targetDnsServers")
    def target_dns_servers(self) -> builtins.str:
        '''Get the target DNS servers.'''
        return typing.cast(builtins.str, jsii.get(self, "targetDnsServers"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.ForwardingRuleBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class ForwardingRuleBody:
    def __init__(
        self,
        *,
        properties: typing.Union["ForwardingRuleProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Forwarding Rule API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = ForwardingRuleProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad7f2c365b2509c61a6a758e9d9f16ab6687a7aea7947397eae3d0bdd9a362bf)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "ForwardingRuleProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("ForwardingRuleProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ForwardingRuleBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.ForwardingRuleProperties",
    jsii_struct_bases=[],
    name_mapping={
        "domain_name": "domainName",
        "target_dns_servers": "targetDnsServers",
        "forwarding_rule_state": "forwardingRuleState",
        "metadata": "metadata",
    },
)
class ForwardingRuleProperties:
    def __init__(
        self,
        *,
        domain_name: builtins.str,
        target_dns_servers: typing.Sequence[typing.Union["TargetDnsServer", typing.Dict[builtins.str, typing.Any]]],
        forwarding_rule_state: typing.Optional[builtins.str] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Properties for Forwarding Rule body.

        :param domain_name: 
        :param target_dns_servers: 
        :param forwarding_rule_state: 
        :param metadata: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e5a31891c24d66fa2b09c8380914b83f99a81adc8939d91c802aeba56d3266ac)
            check_type(argname="argument domain_name", value=domain_name, expected_type=type_hints["domain_name"])
            check_type(argname="argument target_dns_servers", value=target_dns_servers, expected_type=type_hints["target_dns_servers"])
            check_type(argname="argument forwarding_rule_state", value=forwarding_rule_state, expected_type=type_hints["forwarding_rule_state"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "domain_name": domain_name,
            "target_dns_servers": target_dns_servers,
        }
        if forwarding_rule_state is not None:
            self._values["forwarding_rule_state"] = forwarding_rule_state
        if metadata is not None:
            self._values["metadata"] = metadata

    @builtins.property
    def domain_name(self) -> builtins.str:
        result = self._values.get("domain_name")
        assert result is not None, "Required property 'domain_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def target_dns_servers(self) -> typing.List["TargetDnsServer"]:
        result = self._values.get("target_dns_servers")
        assert result is not None, "Required property 'target_dns_servers' is missing"
        return typing.cast(typing.List["TargetDnsServer"], result)

    @builtins.property
    def forwarding_rule_state(self) -> typing.Optional[builtins.str]:
        result = self._values.get("forwarding_rule_state")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metadata(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("metadata")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ForwardingRuleProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.ForwardingRuleProps",
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
        "dns_forwarding_ruleset_id": "dnsForwardingRulesetId",
        "domain_name": "domainName",
        "target_dns_servers": "targetDnsServers",
        "forwarding_rule_state": "forwardingRuleState",
        "ignore_changes": "ignoreChanges",
        "metadata": "metadata",
    },
)
class ForwardingRuleProps(_AzapiResourceProps_141a2340):
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
        dns_forwarding_ruleset_id: builtins.str,
        domain_name: builtins.str,
        target_dns_servers: typing.Sequence[typing.Union["TargetDnsServer", typing.Dict[builtins.str, typing.Any]]],
        forwarding_rule_state: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure DNS Forwarding Rule.

        Extends AzapiResourceProps with Forwarding Rule specific properties

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
        :param dns_forwarding_ruleset_id: Resource ID of the parent DNS Forwarding Ruleset.
        :param domain_name: The domain name to forward (must end with a dot for FQDN).
        :param target_dns_servers: Array of target DNS servers to forward queries to Maximum of 6 servers per rule.
        :param forwarding_rule_state: The state of the forwarding rule. Default: "Enabled"
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata attached to the forwarding rule as key-value pairs.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d7bdd781688c015c23daf23cb856369d61cbf806451eab72ea89a5d314e2cf5b)
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
            check_type(argname="argument dns_forwarding_ruleset_id", value=dns_forwarding_ruleset_id, expected_type=type_hints["dns_forwarding_ruleset_id"])
            check_type(argname="argument domain_name", value=domain_name, expected_type=type_hints["domain_name"])
            check_type(argname="argument target_dns_servers", value=target_dns_servers, expected_type=type_hints["target_dns_servers"])
            check_type(argname="argument forwarding_rule_state", value=forwarding_rule_state, expected_type=type_hints["forwarding_rule_state"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dns_forwarding_ruleset_id": dns_forwarding_ruleset_id,
            "domain_name": domain_name,
            "target_dns_servers": target_dns_servers,
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
        if forwarding_rule_state is not None:
            self._values["forwarding_rule_state"] = forwarding_rule_state
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if metadata is not None:
            self._values["metadata"] = metadata

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
    def dns_forwarding_ruleset_id(self) -> builtins.str:
        '''Resource ID of the parent DNS Forwarding Ruleset.

        Example::

            "/subscriptions/.../resourceGroups/rg/providers/Microsoft.Network/dnsForwardingRulesets/ruleset1"
        '''
        result = self._values.get("dns_forwarding_ruleset_id")
        assert result is not None, "Required property 'dns_forwarding_ruleset_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def domain_name(self) -> builtins.str:
        '''The domain name to forward (must end with a dot for FQDN).

        Example::

            "internal.corp."
        '''
        result = self._values.get("domain_name")
        assert result is not None, "Required property 'domain_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def target_dns_servers(self) -> typing.List["TargetDnsServer"]:
        '''Array of target DNS servers to forward queries to Maximum of 6 servers per rule.

        Example::

            [{ ipAddress: "10.0.0.4", port: 53 }, { ipAddress: "10.0.0.5" }]
        '''
        result = self._values.get("target_dns_servers")
        assert result is not None, "Required property 'target_dns_servers' is missing"
        return typing.cast(typing.List["TargetDnsServer"], result)

    @builtins.property
    def forwarding_rule_state(self) -> typing.Optional[builtins.str]:
        '''The state of the forwarding rule.

        :default: "Enabled"
        '''
        result = self._values.get("forwarding_rule_state")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["metadata"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def metadata(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Metadata attached to the forwarding rule as key-value pairs.'''
        result = self._values.get("metadata")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ForwardingRuleProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_dnsforwardingruleset.TargetDnsServer",
    jsii_struct_bases=[],
    name_mapping={"ip_address": "ipAddress", "port": "port"},
)
class TargetDnsServer:
    def __init__(
        self,
        *,
        ip_address: builtins.str,
        port: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Target DNS server configuration.

        :param ip_address: IP address of the target DNS server.
        :param port: Port number for the target DNS server. Default: 53
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cf20ab796e18895b575476d92eb8b428d2ef3be24eb130de9fac8d73cea0f809)
            check_type(argname="argument ip_address", value=ip_address, expected_type=type_hints["ip_address"])
            check_type(argname="argument port", value=port, expected_type=type_hints["port"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "ip_address": ip_address,
        }
        if port is not None:
            self._values["port"] = port

    @builtins.property
    def ip_address(self) -> builtins.str:
        '''IP address of the target DNS server.

        Example::

            "10.0.0.4"
        '''
        result = self._values.get("ip_address")
        assert result is not None, "Required property 'ip_address' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def port(self) -> typing.Optional[jsii.Number]:
        '''Port number for the target DNS server.

        :default: 53
        '''
        result = self._values.get("port")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TargetDnsServer(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DnsForwardingRuleset",
    "DnsForwardingRulesetBody",
    "DnsForwardingRulesetProperties",
    "DnsForwardingRulesetProps",
    "DnsForwardingRulesetVirtualNetworkLink",
    "DnsForwardingRulesetVirtualNetworkLinkBody",
    "DnsForwardingRulesetVirtualNetworkLinkProperties",
    "DnsForwardingRulesetVirtualNetworkLinkProps",
    "DnsForwardingRulesetVirtualNetworkReference",
    "DnsResolverOutboundEndpointReference",
    "ForwardingRule",
    "ForwardingRuleBody",
    "ForwardingRuleProperties",
    "ForwardingRuleProps",
    "TargetDnsServer",
]

publication.publish()

def _typecheckingstub__8d15d325ac27a73f041f5be36fd1e671dfc8ec1d70a4c97974b17fd80e7194f8(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    dns_resolver_outbound_endpoint_ids: typing.Sequence[builtins.str],
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

def _typecheckingstub__8e6905418f9f9ad348439a6056e62eb842efc5e9dda232743f08bde5a05d8d7a(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dc27d70eb021810137744676e64fdfb226343a5c153191f2a256e9dca414485d(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2ee3d5446bb31f42500f46d46766237a2c4022aa60e365eef8cb975b77057019(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7abf5a3fda837c6997881aa6392d792f8c713544229be655047d2d7a71bd322f(
    *,
    location: builtins.str,
    properties: typing.Union[DnsForwardingRulesetProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__936dc2978060e67abc665e124fb38efe190d5eb1220a4627d536cc3654272c48(
    *,
    dns_resolver_outbound_endpoints: typing.Sequence[typing.Union[DnsResolverOutboundEndpointReference, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d9f89a57d4994c047266e16c5feedf511fa683ba4a0fd579cdc8aab6fcc2d4a(
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
    dns_resolver_outbound_endpoint_ids: typing.Sequence[builtins.str],
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa5a9b25305cc1e00a2e42d370bac05029f5fa88399761d861a1c6c2d3a86591(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    dns_forwarding_ruleset_id: builtins.str,
    virtual_network_id: builtins.str,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
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

def _typecheckingstub__73ed7e7aa6f288ecc5bd354c21c895e19287c37c5bbe96b9765e1d8905e95ead(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__572e670c101933afc727f2b9572f93328b102ebcc2411f1b87c95d543774adde(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0c06b8564f8db22d0371485b4bf6e5aee6451856ba7bb95e9882a1610d78715(
    *,
    properties: typing.Union[DnsForwardingRulesetVirtualNetworkLinkProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4c3e09a00909d7d24af89b42edbad6721a41855725eb7ecd801b4c25180dfea4(
    *,
    virtual_network: typing.Union[DnsForwardingRulesetVirtualNetworkReference, typing.Dict[builtins.str, typing.Any]],
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8d6b7cae9b9ea927a4a26343cf36a4de7a0b6b286b4b2595381c08999c8668c7(
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
    dns_forwarding_ruleset_id: builtins.str,
    virtual_network_id: builtins.str,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2c7d8faa424e77d0cc974950c02575dee65301abc7ac4dde399d0583468a6696(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0b6f564f3152c678558ba5f8ac30cc6162578f989af0c65d6806676e933ea0fb(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77c89b6d2a71359ccb7f25356f12a64037ad7a4ffc479ce6a0f2b33f58a4c9df(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    dns_forwarding_ruleset_id: builtins.str,
    domain_name: builtins.str,
    target_dns_servers: typing.Sequence[typing.Union[TargetDnsServer, typing.Dict[builtins.str, typing.Any]]],
    forwarding_rule_state: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
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

def _typecheckingstub__abefc2cde23b36b222a00c9bcbfd8592c1b1869d0022b8f2460106672cb68631(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ae896f931e124d78e046913d5e7bdebe744effedaf00979923f3bbe265f788a7(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad7f2c365b2509c61a6a758e9d9f16ab6687a7aea7947397eae3d0bdd9a362bf(
    *,
    properties: typing.Union[ForwardingRuleProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e5a31891c24d66fa2b09c8380914b83f99a81adc8939d91c802aeba56d3266ac(
    *,
    domain_name: builtins.str,
    target_dns_servers: typing.Sequence[typing.Union[TargetDnsServer, typing.Dict[builtins.str, typing.Any]]],
    forwarding_rule_state: typing.Optional[builtins.str] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d7bdd781688c015c23daf23cb856369d61cbf806451eab72ea89a5d314e2cf5b(
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
    dns_forwarding_ruleset_id: builtins.str,
    domain_name: builtins.str,
    target_dns_servers: typing.Sequence[typing.Union[TargetDnsServer, typing.Dict[builtins.str, typing.Any]]],
    forwarding_rule_state: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cf20ab796e18895b575476d92eb8b428d2ef3be24eb130de9fac8d73cea0f809(
    *,
    ip_address: builtins.str,
    port: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass
