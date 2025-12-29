r'''
# Azure Storage Account Module

This module provides unified, version-aware Azure Storage Account constructs using the VersionedAzapiResource framework.

## Features

* **Automatic Version Management**: Defaults to the latest stable API version (2024-01-01)
* **Version Pinning**: Explicitly specify API versions for stability
* **Schema Validation**: Automatic validation of properties against API schemas
* **Multi-Language Support**: Full JSII compliance for TypeScript, Python, Java, and .NET
* **Type Safety**: Complete TypeScript type definitions

## Supported API Versions

* `2023-01-01` - Stable release
* `2023-05-01` - Enhanced security features
* `2024-01-01` - Latest (default)

## Basic Usage

```python
import { StorageAccount } from '@cdktf/tf-constructs-azure/azure-storageaccount';
import { ResourceGroup } from '@cdktf/tf-constructs-azure/azure-resourcegroup';

// Create a resource group first
const resourceGroup = new ResourceGroup(this, 'rg', {
  name: 'my-resource-group',
  location: 'eastus',
});

// Create a storage account with automatic version resolution
const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: { name: 'Standard_LRS' },
  tags: {
    environment: 'production',
    project: 'myapp',
  },
});
```

## Advanced Usage

### Version Pinning

```python
const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: { name: 'Standard_LRS' },
  apiVersion: '2023-05-01', // Pin to specific version
});
```

### Security Configuration

```python
const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: { name: 'Standard_LRS' },
  enableHttpsTrafficOnly: true,
  minimumTlsVersion: 'TLS1_2',
  allowBlobPublicAccess: false,
  networkAcls: {
    defaultAction: 'Deny',
    bypass: 'AzureServices',
    ipRules: [
      { value: '1.2.3.4' },
    ],
  },
});
```

### With Managed Identity

```python
const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: { name: 'Standard_LRS' },
  identity: {
    type: 'SystemAssigned',
  },
});
```

### Premium Storage

```python
const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  sku: { name: 'Premium_LRS' },
  kind: 'BlockBlobStorage',
});
```

## Properties

### Required Properties

* `name` - Storage account name (3-24 lowercase alphanumeric characters, globally unique)
* `location` - Azure region
* `resourceGroupId` - Resource group ID where the storage account will be created
* `sku` - SKU configuration with `name` property

### Optional Properties

* `apiVersion` - API version to use (defaults to latest)
* `kind` - Storage account kind (default: 'StorageV2')
* `accessTier` - Access tier for blob storage (default: 'Hot')
* `enableHttpsTrafficOnly` - Allow only HTTPS traffic (default: true)
* `minimumTlsVersion` - Minimum TLS version (default: 'TLS1_2')
* `allowBlobPublicAccess` - Allow public blob access (default: false)
* `networkAcls` - Network ACL configuration
* `identity` - Managed identity configuration
* `encryption` - Encryption settings
* `tags` - Resource tags
* `ignoreChanges` - Properties to ignore during updates

## SKU Names

* `Standard_LRS` - Locally redundant storage
* `Standard_GRS` - Geo-redundant storage
* `Standard_RAGRS` - Read-access geo-redundant storage
* `Standard_ZRS` - Zone-redundant storage
* `Premium_LRS` - Premium locally redundant storage
* `Premium_ZRS` - Premium zone-redundant storage

## Storage Account Kinds

* `StorageV2` - General-purpose v2 (recommended)
* `Storage` - General-purpose v1
* `BlobStorage` - Blob-only storage
* `BlockBlobStorage` - Premium block blob storage
* `FileStorage` - Premium file storage

## Outputs

The StorageAccount construct provides the following outputs:

* `id` - The resource ID
* `name` - The storage account name
* `location` - The storage account location
* `tags` - The storage account tags
* `primaryBlobEndpoint` - Primary blob endpoint URL
* `primaryFileEndpoint` - Primary file endpoint URL
* `primaryQueueEndpoint` - Primary queue endpoint URL
* `primaryTableEndpoint` - Primary table endpoint URL

## Methods

* `addTag(key, value)` - Add a tag to the storage account
* `removeTag(key)` - Remove a tag from the storage account

## Architecture

This module uses the VersionedAzapiResource framework to provide:

1. **Single Implementation**: One class handles all API versions
2. **Schema-Driven**: TypeScript schemas define version-specific properties
3. **Automatic Validation**: Properties validated against API schemas
4. **Version Resolution**: Automatic latest version detection
5. **JSII Compliance**: Full multi-language support

## Migration from Version-Specific Classes

If you're migrating from version-specific storage account classes, simply:

1. Import from the unified module
2. Optionally specify `apiVersion` if you need version pinning
3. All other properties remain the same

```python
// Old approach (version-specific)
import { Group as StorageAccount } from './v2023-01-01';

// New approach (unified)
import { StorageAccount } from '@cdktf/tf-constructs-azure/azure-storageaccount';

// Optionally pin version for compatibility
const storage = new StorageAccount(this, 'storage', {
  apiVersion: '2023-01-01',
  // ... rest of props
});

## Monitoring

The Storage Account construct provides built-in monitoring capabilities through the `defaultMonitoring()` static method.

### Default Monitoring Configuration

```typescript
import { StorageAccount } from '@cdktf/azure-storageaccount';
import { ActionGroup } from '@cdktf/azure-actiongroup';
import { LogAnalyticsWorkspace } from '@cdktf/azure-loganalyticsworkspace';

const actionGroup = new ActionGroup(this, 'alerts', {
  // ... action group configuration
});

const workspace = new LogAnalyticsWorkspace(this, 'logs', {
  // ... workspace configuration
});

const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupName: resourceGroup.name,
  // ... other properties
  monitoring: StorageAccount.defaultMonitoring(
    actionGroup.id,
    workspace.id
  )
});
```

### Monitored Metrics

The default monitoring configuration includes:

1. **Availability Alert**

   * Metric: `Availability`
   * Threshold: 99.9% (default)
   * Severity: Error (1)
   * Triggers when storage account availability drops below threshold
2. **Egress Alert**

   * Metric: `Egress`
   * Threshold: 10GB per hour (default)
   * Severity: Warning (2)
   * Triggers when outbound data transfer exceeds threshold
3. **Transactions Alert**

   * Metric: `Transactions`
   * Threshold: 100,000 per 15 minutes (default)
   * Severity: Warning (2)
   * Triggers when transaction count exceeds threshold
4. **Deletion Alert**

   * Tracks storage account deletion via Activity Log
   * Severity: Informational

### Custom Monitoring Configuration

Customize thresholds and severities:

```python
const storageAccount = new StorageAccount(this, 'storage', {
  name: 'mystorageaccount',
  location: 'eastus',
  resourceGroupName: resourceGroup.name,
  monitoring: StorageAccount.defaultMonitoring(
    actionGroup.id,
    workspace.id,
    {
      availabilityThreshold: 99.5,           // Custom availability threshold
      egressThreshold: 5368709120,            // 5GB in bytes
      transactionsThreshold: 50000,           // 50k transactions
      availabilityAlertSeverity: 0,           // Critical
      enableEgressAlert: false,               // Disable egress monitoring
    }
  )
});
```

### Monitoring Options

All available options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `availabilityThreshold` | number | 99.9 | Availability percentage threshold |
| `egressThreshold` | number | 10737418240 | Egress bytes threshold (10GB) |
| `transactionsThreshold` | number | 100000 | Transaction count threshold |
| `enableAvailabilityAlert` | boolean | true | Enable/disable availability alert |
| `enableEgressAlert` | boolean | true | Enable/disable egress alert |
| `enableTransactionsAlert` | boolean | true | Enable/disable transactions alert |
| `enableDeletionAlert` | boolean | true | Enable/disable deletion tracking |
| `availabilityAlertSeverity` | 0|1|2|3|4 | 1 | Availability alert severity (0=Critical, 4=Verbose) |
| `egressAlertSeverity` | 0|1|2|3|4 | 2 | Egress alert severity |
| `transactionsAlertSeverity` | 0|1|2|3|4 | 2 | Transactions alert severity |
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


class StorageAccount(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccount",
):
    '''Unified Azure Storage Account implementation.

    This class provides a single, version-aware implementation that replaces all
    version-specific Storage Account classes. It automatically handles version
    resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Example::

        // Usage with explicit version pinning:
        const storageAccount = new StorageAccount(this, "storage", {
          name: "mystorageaccount",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          sku: { name: "Standard_LRS" },
          apiVersion: "2023-05-01",
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        sku: typing.Union["StorageAccountSku", typing.Dict[builtins.str, typing.Any]],
        access_tier: typing.Optional[builtins.str] = None,
        allow_blob_public_access: typing.Optional[builtins.bool] = None,
        enable_https_traffic_only: typing.Optional[builtins.bool] = None,
        encryption: typing.Optional[typing.Union["StorageAccountEncryption", typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union["StorageAccountIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        kind: typing.Optional[builtins.str] = None,
        minimum_tls_version: typing.Optional[builtins.str] = None,
        network_acls: typing.Optional[typing.Union["StorageAccountNetworkAcls", typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Creates a new Azure Storage Account using the VersionedAzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param sku: The SKU (pricing tier) for the Storage Account.
        :param access_tier: The access tier for blob storage. Default: "Hot"
        :param allow_blob_public_access: Whether to allow public access to blobs. Default: false
        :param enable_https_traffic_only: Whether to allow only HTTPS traffic. Default: true
        :param encryption: Encryption settings.
        :param identity: Managed identity configuration.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param kind: The kind of Storage Account. Default: "StorageV2"
        :param minimum_tls_version: The minimum TLS version required. Default: "TLS1_2"
        :param network_acls: Network ACL rules for the storage account.
        :param resource_group_id: Resource group ID where the storage account will be created.
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
            type_hints = typing.get_type_hints(_typecheckingstub__41854d4468855a70ae5f1dc34a157a49d7c0e460fcc47b8bdd4305ce4908b9d1)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = StorageAccountProps(
            sku=sku,
            access_tier=access_tier,
            allow_blob_public_access=allow_blob_public_access,
            enable_https_traffic_only=enable_https_traffic_only,
            encryption=encryption,
            identity=identity,
            ignore_changes=ignore_changes,
            kind=kind,
            minimum_tls_version=minimum_tls_version,
            network_acls=network_acls,
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

    @jsii.member(jsii_name="defaultMonitoring")
    @builtins.classmethod
    def default_monitoring(
        cls,
        action_group_id: builtins.str,
        workspace_id: typing.Optional[builtins.str] = None,
        *,
        availability_alert_severity: typing.Optional[jsii.Number] = None,
        availability_threshold: typing.Optional[jsii.Number] = None,
        egress_alert_severity: typing.Optional[jsii.Number] = None,
        egress_threshold: typing.Optional[jsii.Number] = None,
        enable_availability_alert: typing.Optional[builtins.bool] = None,
        enable_deletion_alert: typing.Optional[builtins.bool] = None,
        enable_egress_alert: typing.Optional[builtins.bool] = None,
        enable_transactions_alert: typing.Optional[builtins.bool] = None,
        transactions_alert_severity: typing.Optional[jsii.Number] = None,
        transactions_threshold: typing.Optional[jsii.Number] = None,
    ) -> _MonitoringConfig_7c28df74:
        '''Returns a production-ready monitoring configuration for Storage Accounts.

        This static factory method provides a complete MonitoringConfig with sensible defaults
        for storage account monitoring including availability, egress, transactions alerts, and deletion tracking.

        :param action_group_id: - The resource ID of the action group for alert notifications.
        :param workspace_id: - Optional Log Analytics workspace ID for diagnostic settings.
        :param availability_alert_severity: Severity level for availability alerts. Severity levels: - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 1 - Error severity for availability issues
        :param availability_threshold: Threshold for storage account availability percentage. Alert triggers when availability drops below this threshold Default: 99.9 - Triggers alert when availability is below 99.9%
        :param egress_alert_severity: Severity level for egress alerts. Severity levels: - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2 - Warning severity for high egress
        :param egress_threshold: Threshold for storage account egress in bytes. Alert triggers when egress exceeds this threshold Default: 10737418240 - Triggers alert when egress exceeds 10GB
        :param enable_availability_alert: Enable or disable availability monitoring alert. Default: true - Availability alert is enabled by default
        :param enable_deletion_alert: Enable or disable deletion activity log alert. Default: true - Deletion alert is enabled by default
        :param enable_egress_alert: Enable or disable egress monitoring alert. Default: true - Egress alert is enabled by default
        :param enable_transactions_alert: Enable or disable transactions monitoring alert. Default: true - Transactions alert is enabled by default
        :param transactions_alert_severity: Severity level for transactions alerts. Severity levels: - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2 - Warning severity for high transaction count
        :param transactions_threshold: Threshold for storage account transactions count. Alert triggers when transaction count exceeds this threshold Default: 100000 - Triggers alert when transactions exceed 100k

        :return: A complete MonitoringConfig object ready to use in StorageAccount props

        Example::

            // Custom thresholds
            const storageAccount = new StorageAccount(this, "storage", {
              // ... other properties ...
              monitoring: StorageAccount.defaultMonitoring(
                actionGroup.id,
                workspace.id,
                {
                  availabilityThreshold: 99.5,
                  egressThreshold: 21474836480, // 20GB
                  enableTransactionsAlert: false
                }
              )
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9d1c55ad8e16edcd6df0d628ae2f437eebf09c41ad898bb7f33cd2d0532eae2f)
            check_type(argname="argument action_group_id", value=action_group_id, expected_type=type_hints["action_group_id"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
        options = StorageAccountMonitoringOptions(
            availability_alert_severity=availability_alert_severity,
            availability_threshold=availability_threshold,
            egress_alert_severity=egress_alert_severity,
            egress_threshold=egress_threshold,
            enable_availability_alert=enable_availability_alert,
            enable_deletion_alert=enable_deletion_alert,
            enable_egress_alert=enable_egress_alert,
            enable_transactions_alert=enable_transactions_alert,
            transactions_alert_severity=transactions_alert_severity,
            transactions_threshold=transactions_threshold,
        )

        return typing.cast(_MonitoringConfig_7c28df74, jsii.sinvoke(cls, "defaultMonitoring", [action_group_id, workspace_id, options]))

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Add a tag to the Storage Account.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__863af4470fa4b33aa4374ddd2e4a49bd0a7e70a54b592ab1213d6bc7da80d67e)
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
            type_hints = typing.get_type_hints(_typecheckingstub__3d63355f7ee6ae8844c39b966a78b3b05766253c17bc9786d9db5178cc9c2f83)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Storage Account.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0603a5973b278a7df99efd4c495d5efb096192322f0fdc3c36890aaf078fff25)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that location is required for Storage Accounts.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Storage Accounts.'''
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
    @jsii.member(jsii_name="primaryBlobEndpoint")
    def primary_blob_endpoint(self) -> builtins.str:
        '''Get the primary blob endpoint.'''
        return typing.cast(builtins.str, jsii.get(self, "primaryBlobEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="primaryEndpointsOutput")
    def primary_endpoints_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "primaryEndpointsOutput"))

    @builtins.property
    @jsii.member(jsii_name="primaryFileEndpoint")
    def primary_file_endpoint(self) -> builtins.str:
        '''Get the primary file endpoint.'''
        return typing.cast(builtins.str, jsii.get(self, "primaryFileEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="primaryQueueEndpoint")
    def primary_queue_endpoint(self) -> builtins.str:
        '''Get the primary queue endpoint.'''
        return typing.cast(builtins.str, jsii.get(self, "primaryQueueEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="primaryTableEndpoint")
    def primary_table_endpoint(self) -> builtins.str:
        '''Get the primary table endpoint.'''
        return typing.cast(builtins.str, jsii.get(self, "primaryTableEndpoint"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "StorageAccountProps":
        return typing.cast("StorageAccountProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountBody",
    jsii_struct_bases=[],
    name_mapping={
        "kind": "kind",
        "location": "location",
        "sku": "sku",
        "identity": "identity",
        "properties": "properties",
        "tags": "tags",
    },
)
class StorageAccountBody:
    def __init__(
        self,
        *,
        kind: builtins.str,
        location: builtins.str,
        sku: typing.Union["StorageAccountSku", typing.Dict[builtins.str, typing.Any]],
        identity: typing.Optional[typing.Union["StorageAccountIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        properties: typing.Optional[typing.Union["StorageAccountBodyProperties", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Storage Account API calls.

        :param kind: 
        :param location: 
        :param sku: 
        :param identity: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(sku, dict):
            sku = StorageAccountSku(**sku)
        if isinstance(identity, dict):
            identity = StorageAccountIdentity(**identity)
        if isinstance(properties, dict):
            properties = StorageAccountBodyProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9eb371460134b4e374ffe7b776a5dd0781636550e31ff872e4ecf40db6d03706)
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "kind": kind,
            "location": location,
            "sku": sku,
        }
        if identity is not None:
            self._values["identity"] = identity
        if properties is not None:
            self._values["properties"] = properties
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def kind(self) -> builtins.str:
        result = self._values.get("kind")
        assert result is not None, "Required property 'kind' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def location(self) -> builtins.str:
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def sku(self) -> "StorageAccountSku":
        result = self._values.get("sku")
        assert result is not None, "Required property 'sku' is missing"
        return typing.cast("StorageAccountSku", result)

    @builtins.property
    def identity(self) -> typing.Optional["StorageAccountIdentity"]:
        result = self._values.get("identity")
        return typing.cast(typing.Optional["StorageAccountIdentity"], result)

    @builtins.property
    def properties(self) -> typing.Optional["StorageAccountBodyProperties"]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional["StorageAccountBodyProperties"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "access_tier": "accessTier",
        "allow_blob_public_access": "allowBlobPublicAccess",
        "encryption": "encryption",
        "minimum_tls_version": "minimumTlsVersion",
        "network_acls": "networkAcls",
        "supports_https_traffic_only": "supportsHttpsTrafficOnly",
    },
)
class StorageAccountBodyProperties:
    def __init__(
        self,
        *,
        access_tier: typing.Optional[builtins.str] = None,
        allow_blob_public_access: typing.Optional[builtins.bool] = None,
        encryption: typing.Optional[typing.Union["StorageAccountEncryption", typing.Dict[builtins.str, typing.Any]]] = None,
        minimum_tls_version: typing.Optional[builtins.str] = None,
        network_acls: typing.Optional[typing.Union["StorageAccountNetworkAcls", typing.Dict[builtins.str, typing.Any]]] = None,
        supports_https_traffic_only: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Storage Account properties for the request body.

        :param access_tier: 
        :param allow_blob_public_access: 
        :param encryption: 
        :param minimum_tls_version: 
        :param network_acls: 
        :param supports_https_traffic_only: 
        '''
        if isinstance(encryption, dict):
            encryption = StorageAccountEncryption(**encryption)
        if isinstance(network_acls, dict):
            network_acls = StorageAccountNetworkAcls(**network_acls)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a2909d304bea6ded084c6fc7f79f7589598798b89318ea780ba4d0992cbda22b)
            check_type(argname="argument access_tier", value=access_tier, expected_type=type_hints["access_tier"])
            check_type(argname="argument allow_blob_public_access", value=allow_blob_public_access, expected_type=type_hints["allow_blob_public_access"])
            check_type(argname="argument encryption", value=encryption, expected_type=type_hints["encryption"])
            check_type(argname="argument minimum_tls_version", value=minimum_tls_version, expected_type=type_hints["minimum_tls_version"])
            check_type(argname="argument network_acls", value=network_acls, expected_type=type_hints["network_acls"])
            check_type(argname="argument supports_https_traffic_only", value=supports_https_traffic_only, expected_type=type_hints["supports_https_traffic_only"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if access_tier is not None:
            self._values["access_tier"] = access_tier
        if allow_blob_public_access is not None:
            self._values["allow_blob_public_access"] = allow_blob_public_access
        if encryption is not None:
            self._values["encryption"] = encryption
        if minimum_tls_version is not None:
            self._values["minimum_tls_version"] = minimum_tls_version
        if network_acls is not None:
            self._values["network_acls"] = network_acls
        if supports_https_traffic_only is not None:
            self._values["supports_https_traffic_only"] = supports_https_traffic_only

    @builtins.property
    def access_tier(self) -> typing.Optional[builtins.str]:
        result = self._values.get("access_tier")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def allow_blob_public_access(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("allow_blob_public_access")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encryption(self) -> typing.Optional["StorageAccountEncryption"]:
        result = self._values.get("encryption")
        return typing.cast(typing.Optional["StorageAccountEncryption"], result)

    @builtins.property
    def minimum_tls_version(self) -> typing.Optional[builtins.str]:
        result = self._values.get("minimum_tls_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def network_acls(self) -> typing.Optional["StorageAccountNetworkAcls"]:
        result = self._values.get("network_acls")
        return typing.cast(typing.Optional["StorageAccountNetworkAcls"], result)

    @builtins.property
    def supports_https_traffic_only(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("supports_https_traffic_only")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountEncryption",
    jsii_struct_bases=[],
    name_mapping={"key_source": "keySource", "services": "services"},
)
class StorageAccountEncryption:
    def __init__(
        self,
        *,
        key_source: typing.Optional[builtins.str] = None,
        services: typing.Optional[typing.Union["StorageAccountEncryptionServices", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Encryption configuration for Storage Account.

        :param key_source: Key source (Microsoft.Storage or Microsoft.Keyvault).
        :param services: Encryption services (blob, file, table, queue).
        '''
        if isinstance(services, dict):
            services = StorageAccountEncryptionServices(**services)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ffface12b8c932dc7c8df23fb60d30a5d122b282c27ae791fc8b5c60a54bd0a2)
            check_type(argname="argument key_source", value=key_source, expected_type=type_hints["key_source"])
            check_type(argname="argument services", value=services, expected_type=type_hints["services"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if key_source is not None:
            self._values["key_source"] = key_source
        if services is not None:
            self._values["services"] = services

    @builtins.property
    def key_source(self) -> typing.Optional[builtins.str]:
        '''Key source (Microsoft.Storage or Microsoft.Keyvault).'''
        result = self._values.get("key_source")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def services(self) -> typing.Optional["StorageAccountEncryptionServices"]:
        '''Encryption services (blob, file, table, queue).'''
        result = self._values.get("services")
        return typing.cast(typing.Optional["StorageAccountEncryptionServices"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountEncryption(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountEncryptionService",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class StorageAccountEncryptionService:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''Encryption service configuration.

        :param enabled: Whether encryption is enabled.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__992b94e6f0ec55614c6c69292e6fb60bc36c4e5b0a27e716e8ca26944bb5d3f0)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''Whether encryption is enabled.'''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountEncryptionService(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountEncryptionServices",
    jsii_struct_bases=[],
    name_mapping={"blob": "blob", "file": "file", "queue": "queue", "table": "table"},
)
class StorageAccountEncryptionServices:
    def __init__(
        self,
        *,
        blob: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
        file: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
        queue: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
        table: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Encryption services configuration.

        :param blob: Blob service encryption.
        :param file: File service encryption.
        :param queue: Queue service encryption.
        :param table: Table service encryption.
        '''
        if isinstance(blob, dict):
            blob = StorageAccountEncryptionService(**blob)
        if isinstance(file, dict):
            file = StorageAccountEncryptionService(**file)
        if isinstance(queue, dict):
            queue = StorageAccountEncryptionService(**queue)
        if isinstance(table, dict):
            table = StorageAccountEncryptionService(**table)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__adc9d0b07c4ad108cf1c4ecf4c2b084547cd4a72f069dd85128913e2573d602b)
            check_type(argname="argument blob", value=blob, expected_type=type_hints["blob"])
            check_type(argname="argument file", value=file, expected_type=type_hints["file"])
            check_type(argname="argument queue", value=queue, expected_type=type_hints["queue"])
            check_type(argname="argument table", value=table, expected_type=type_hints["table"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if blob is not None:
            self._values["blob"] = blob
        if file is not None:
            self._values["file"] = file
        if queue is not None:
            self._values["queue"] = queue
        if table is not None:
            self._values["table"] = table

    @builtins.property
    def blob(self) -> typing.Optional[StorageAccountEncryptionService]:
        '''Blob service encryption.'''
        result = self._values.get("blob")
        return typing.cast(typing.Optional[StorageAccountEncryptionService], result)

    @builtins.property
    def file(self) -> typing.Optional[StorageAccountEncryptionService]:
        '''File service encryption.'''
        result = self._values.get("file")
        return typing.cast(typing.Optional[StorageAccountEncryptionService], result)

    @builtins.property
    def queue(self) -> typing.Optional[StorageAccountEncryptionService]:
        '''Queue service encryption.'''
        result = self._values.get("queue")
        return typing.cast(typing.Optional[StorageAccountEncryptionService], result)

    @builtins.property
    def table(self) -> typing.Optional[StorageAccountEncryptionService]:
        '''Table service encryption.'''
        result = self._values.get("table")
        return typing.cast(typing.Optional[StorageAccountEncryptionService], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountEncryptionServices(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountIdentity",
    jsii_struct_bases=[],
    name_mapping={
        "type": "type",
        "user_assigned_identities": "userAssignedIdentities",
    },
)
class StorageAccountIdentity:
    def __init__(
        self,
        *,
        type: builtins.str,
        user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    ) -> None:
        '''Identity configuration for Storage Account.

        :param type: The type of identity (SystemAssigned, UserAssigned, SystemAssigned,UserAssigned).
        :param user_assigned_identities: User assigned identity IDs.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__440277777ddc836a0314ec9b6a9d382be8b200f682ba40a4b94dd9a3c30e61d1)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument user_assigned_identities", value=user_assigned_identities, expected_type=type_hints["user_assigned_identities"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }
        if user_assigned_identities is not None:
            self._values["user_assigned_identities"] = user_assigned_identities

    @builtins.property
    def type(self) -> builtins.str:
        '''The type of identity (SystemAssigned, UserAssigned, SystemAssigned,UserAssigned).'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def user_assigned_identities(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''User assigned identity IDs.'''
        result = self._values.get("user_assigned_identities")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountIpRule",
    jsii_struct_bases=[],
    name_mapping={"value": "value"},
)
class StorageAccountIpRule:
    def __init__(self, *, value: builtins.str) -> None:
        '''IP rule for network ACLs.

        :param value: IP address or CIDR range.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8373e0a23cf3c241ccee2939b9b6d82c3738cca45a04f997c3129df58fca5537)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "value": value,
        }

    @builtins.property
    def value(self) -> builtins.str:
        '''IP address or CIDR range.'''
        result = self._values.get("value")
        assert result is not None, "Required property 'value' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountIpRule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountMonitoringOptions",
    jsii_struct_bases=[],
    name_mapping={
        "availability_alert_severity": "availabilityAlertSeverity",
        "availability_threshold": "availabilityThreshold",
        "egress_alert_severity": "egressAlertSeverity",
        "egress_threshold": "egressThreshold",
        "enable_availability_alert": "enableAvailabilityAlert",
        "enable_deletion_alert": "enableDeletionAlert",
        "enable_egress_alert": "enableEgressAlert",
        "enable_transactions_alert": "enableTransactionsAlert",
        "transactions_alert_severity": "transactionsAlertSeverity",
        "transactions_threshold": "transactionsThreshold",
    },
)
class StorageAccountMonitoringOptions:
    def __init__(
        self,
        *,
        availability_alert_severity: typing.Optional[jsii.Number] = None,
        availability_threshold: typing.Optional[jsii.Number] = None,
        egress_alert_severity: typing.Optional[jsii.Number] = None,
        egress_threshold: typing.Optional[jsii.Number] = None,
        enable_availability_alert: typing.Optional[builtins.bool] = None,
        enable_deletion_alert: typing.Optional[builtins.bool] = None,
        enable_egress_alert: typing.Optional[builtins.bool] = None,
        enable_transactions_alert: typing.Optional[builtins.bool] = None,
        transactions_alert_severity: typing.Optional[jsii.Number] = None,
        transactions_threshold: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Configuration options for Storage Account monitoring.

        This interface defines the configurable options for setting up monitoring alerts
        and diagnostic settings for Azure Storage Accounts. All properties are optional
        and have sensible defaults for production use.

        :param availability_alert_severity: Severity level for availability alerts. Severity levels: - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 1 - Error severity for availability issues
        :param availability_threshold: Threshold for storage account availability percentage. Alert triggers when availability drops below this threshold Default: 99.9 - Triggers alert when availability is below 99.9%
        :param egress_alert_severity: Severity level for egress alerts. Severity levels: - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2 - Warning severity for high egress
        :param egress_threshold: Threshold for storage account egress in bytes. Alert triggers when egress exceeds this threshold Default: 10737418240 - Triggers alert when egress exceeds 10GB
        :param enable_availability_alert: Enable or disable availability monitoring alert. Default: true - Availability alert is enabled by default
        :param enable_deletion_alert: Enable or disable deletion activity log alert. Default: true - Deletion alert is enabled by default
        :param enable_egress_alert: Enable or disable egress monitoring alert. Default: true - Egress alert is enabled by default
        :param enable_transactions_alert: Enable or disable transactions monitoring alert. Default: true - Transactions alert is enabled by default
        :param transactions_alert_severity: Severity level for transactions alerts. Severity levels: - 0: Critical - 1: Error - 2: Warning - 3: Informational - 4: Verbose Default: 2 - Warning severity for high transaction count
        :param transactions_threshold: Threshold for storage account transactions count. Alert triggers when transaction count exceeds this threshold Default: 100000 - Triggers alert when transactions exceed 100k
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8e41b957a3bc71d822b0a7f4b270460fe8063b4539b6462a7d0bc1c238f7495f)
            check_type(argname="argument availability_alert_severity", value=availability_alert_severity, expected_type=type_hints["availability_alert_severity"])
            check_type(argname="argument availability_threshold", value=availability_threshold, expected_type=type_hints["availability_threshold"])
            check_type(argname="argument egress_alert_severity", value=egress_alert_severity, expected_type=type_hints["egress_alert_severity"])
            check_type(argname="argument egress_threshold", value=egress_threshold, expected_type=type_hints["egress_threshold"])
            check_type(argname="argument enable_availability_alert", value=enable_availability_alert, expected_type=type_hints["enable_availability_alert"])
            check_type(argname="argument enable_deletion_alert", value=enable_deletion_alert, expected_type=type_hints["enable_deletion_alert"])
            check_type(argname="argument enable_egress_alert", value=enable_egress_alert, expected_type=type_hints["enable_egress_alert"])
            check_type(argname="argument enable_transactions_alert", value=enable_transactions_alert, expected_type=type_hints["enable_transactions_alert"])
            check_type(argname="argument transactions_alert_severity", value=transactions_alert_severity, expected_type=type_hints["transactions_alert_severity"])
            check_type(argname="argument transactions_threshold", value=transactions_threshold, expected_type=type_hints["transactions_threshold"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if availability_alert_severity is not None:
            self._values["availability_alert_severity"] = availability_alert_severity
        if availability_threshold is not None:
            self._values["availability_threshold"] = availability_threshold
        if egress_alert_severity is not None:
            self._values["egress_alert_severity"] = egress_alert_severity
        if egress_threshold is not None:
            self._values["egress_threshold"] = egress_threshold
        if enable_availability_alert is not None:
            self._values["enable_availability_alert"] = enable_availability_alert
        if enable_deletion_alert is not None:
            self._values["enable_deletion_alert"] = enable_deletion_alert
        if enable_egress_alert is not None:
            self._values["enable_egress_alert"] = enable_egress_alert
        if enable_transactions_alert is not None:
            self._values["enable_transactions_alert"] = enable_transactions_alert
        if transactions_alert_severity is not None:
            self._values["transactions_alert_severity"] = transactions_alert_severity
        if transactions_threshold is not None:
            self._values["transactions_threshold"] = transactions_threshold

    @builtins.property
    def availability_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for availability alerts.

        Severity levels:

        - 0: Critical
        - 1: Error
        - 2: Warning
        - 3: Informational
        - 4: Verbose

        :default: 1 - Error severity for availability issues
        '''
        result = self._values.get("availability_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def availability_threshold(self) -> typing.Optional[jsii.Number]:
        '''Threshold for storage account availability percentage.

        Alert triggers when availability drops below this threshold

        :default: 99.9 - Triggers alert when availability is below 99.9%
        '''
        result = self._values.get("availability_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def egress_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for egress alerts.

        Severity levels:

        - 0: Critical
        - 1: Error
        - 2: Warning
        - 3: Informational
        - 4: Verbose

        :default: 2 - Warning severity for high egress
        '''
        result = self._values.get("egress_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def egress_threshold(self) -> typing.Optional[jsii.Number]:
        '''Threshold for storage account egress in bytes.

        Alert triggers when egress exceeds this threshold

        :default: 10737418240 - Triggers alert when egress exceeds 10GB
        '''
        result = self._values.get("egress_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def enable_availability_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable availability monitoring alert.

        :default: true - Availability alert is enabled by default
        '''
        result = self._values.get("enable_availability_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_deletion_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable deletion activity log alert.

        :default: true - Deletion alert is enabled by default
        '''
        result = self._values.get("enable_deletion_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_egress_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable egress monitoring alert.

        :default: true - Egress alert is enabled by default
        '''
        result = self._values.get("enable_egress_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_transactions_alert(self) -> typing.Optional[builtins.bool]:
        '''Enable or disable transactions monitoring alert.

        :default: true - Transactions alert is enabled by default
        '''
        result = self._values.get("enable_transactions_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def transactions_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for transactions alerts.

        Severity levels:

        - 0: Critical
        - 1: Error
        - 2: Warning
        - 3: Informational
        - 4: Verbose

        :default: 2 - Warning severity for high transaction count
        '''
        result = self._values.get("transactions_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def transactions_threshold(self) -> typing.Optional[jsii.Number]:
        '''Threshold for storage account transactions count.

        Alert triggers when transaction count exceeds this threshold

        :default: 100000 - Triggers alert when transactions exceed 100k
        '''
        result = self._values.get("transactions_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountMonitoringOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountNetworkAcls",
    jsii_struct_bases=[],
    name_mapping={
        "bypass": "bypass",
        "default_action": "defaultAction",
        "ip_rules": "ipRules",
        "virtual_network_rules": "virtualNetworkRules",
    },
)
class StorageAccountNetworkAcls:
    def __init__(
        self,
        *,
        bypass: typing.Optional[builtins.str] = None,
        default_action: typing.Optional[builtins.str] = None,
        ip_rules: typing.Optional[typing.Sequence[typing.Union[StorageAccountIpRule, typing.Dict[builtins.str, typing.Any]]]] = None,
        virtual_network_rules: typing.Optional[typing.Sequence[typing.Union["StorageAccountVirtualNetworkRule", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Network ACL configuration for Storage Account.

        :param bypass: Whether to bypass network rules for Azure services.
        :param default_action: Default action when no rule matches (Allow or Deny).
        :param ip_rules: IP rules for the storage account.
        :param virtual_network_rules: Virtual network rules for the storage account.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2c2d233bd116db5232ae8ecb424fbd2f64f4943cd00bf24596d4535435afd26e)
            check_type(argname="argument bypass", value=bypass, expected_type=type_hints["bypass"])
            check_type(argname="argument default_action", value=default_action, expected_type=type_hints["default_action"])
            check_type(argname="argument ip_rules", value=ip_rules, expected_type=type_hints["ip_rules"])
            check_type(argname="argument virtual_network_rules", value=virtual_network_rules, expected_type=type_hints["virtual_network_rules"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if bypass is not None:
            self._values["bypass"] = bypass
        if default_action is not None:
            self._values["default_action"] = default_action
        if ip_rules is not None:
            self._values["ip_rules"] = ip_rules
        if virtual_network_rules is not None:
            self._values["virtual_network_rules"] = virtual_network_rules

    @builtins.property
    def bypass(self) -> typing.Optional[builtins.str]:
        '''Whether to bypass network rules for Azure services.'''
        result = self._values.get("bypass")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def default_action(self) -> typing.Optional[builtins.str]:
        '''Default action when no rule matches (Allow or Deny).'''
        result = self._values.get("default_action")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ip_rules(self) -> typing.Optional[typing.List[StorageAccountIpRule]]:
        '''IP rules for the storage account.'''
        result = self._values.get("ip_rules")
        return typing.cast(typing.Optional[typing.List[StorageAccountIpRule]], result)

    @builtins.property
    def virtual_network_rules(
        self,
    ) -> typing.Optional[typing.List["StorageAccountVirtualNetworkRule"]]:
        '''Virtual network rules for the storage account.'''
        result = self._values.get("virtual_network_rules")
        return typing.cast(typing.Optional[typing.List["StorageAccountVirtualNetworkRule"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountNetworkAcls(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountProps",
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
        "sku": "sku",
        "access_tier": "accessTier",
        "allow_blob_public_access": "allowBlobPublicAccess",
        "enable_https_traffic_only": "enableHttpsTrafficOnly",
        "encryption": "encryption",
        "identity": "identity",
        "ignore_changes": "ignoreChanges",
        "kind": "kind",
        "minimum_tls_version": "minimumTlsVersion",
        "network_acls": "networkAcls",
        "resource_group_id": "resourceGroupId",
    },
)
class StorageAccountProps(_AzapiResourceProps_141a2340):
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
        sku: typing.Union["StorageAccountSku", typing.Dict[builtins.str, typing.Any]],
        access_tier: typing.Optional[builtins.str] = None,
        allow_blob_public_access: typing.Optional[builtins.bool] = None,
        enable_https_traffic_only: typing.Optional[builtins.bool] = None,
        encryption: typing.Optional[typing.Union[StorageAccountEncryption, typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union[StorageAccountIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        kind: typing.Optional[builtins.str] = None,
        minimum_tls_version: typing.Optional[builtins.str] = None,
        network_acls: typing.Optional[typing.Union[StorageAccountNetworkAcls, typing.Dict[builtins.str, typing.Any]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Storage Account.

        Extends VersionedAzapiResourceProps with Storage Account specific properties

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
        :param sku: The SKU (pricing tier) for the Storage Account.
        :param access_tier: The access tier for blob storage. Default: "Hot"
        :param allow_blob_public_access: Whether to allow public access to blobs. Default: false
        :param enable_https_traffic_only: Whether to allow only HTTPS traffic. Default: true
        :param encryption: Encryption settings.
        :param identity: Managed identity configuration.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param kind: The kind of Storage Account. Default: "StorageV2"
        :param minimum_tls_version: The minimum TLS version required. Default: "TLS1_2"
        :param network_acls: Network ACL rules for the storage account.
        :param resource_group_id: Resource group ID where the storage account will be created.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(sku, dict):
            sku = StorageAccountSku(**sku)
        if isinstance(encryption, dict):
            encryption = StorageAccountEncryption(**encryption)
        if isinstance(identity, dict):
            identity = StorageAccountIdentity(**identity)
        if isinstance(network_acls, dict):
            network_acls = StorageAccountNetworkAcls(**network_acls)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56262b0499cdaccde11afb901fc29542328539b98b808b0ee9f75bdac247652d)
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
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument access_tier", value=access_tier, expected_type=type_hints["access_tier"])
            check_type(argname="argument allow_blob_public_access", value=allow_blob_public_access, expected_type=type_hints["allow_blob_public_access"])
            check_type(argname="argument enable_https_traffic_only", value=enable_https_traffic_only, expected_type=type_hints["enable_https_traffic_only"])
            check_type(argname="argument encryption", value=encryption, expected_type=type_hints["encryption"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument minimum_tls_version", value=minimum_tls_version, expected_type=type_hints["minimum_tls_version"])
            check_type(argname="argument network_acls", value=network_acls, expected_type=type_hints["network_acls"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
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
        if access_tier is not None:
            self._values["access_tier"] = access_tier
        if allow_blob_public_access is not None:
            self._values["allow_blob_public_access"] = allow_blob_public_access
        if enable_https_traffic_only is not None:
            self._values["enable_https_traffic_only"] = enable_https_traffic_only
        if encryption is not None:
            self._values["encryption"] = encryption
        if identity is not None:
            self._values["identity"] = identity
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if kind is not None:
            self._values["kind"] = kind
        if minimum_tls_version is not None:
            self._values["minimum_tls_version"] = minimum_tls_version
        if network_acls is not None:
            self._values["network_acls"] = network_acls
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
    def sku(self) -> "StorageAccountSku":
        '''The SKU (pricing tier) for the Storage Account.

        Example::

            { name: "Standard_LRS" }
        '''
        result = self._values.get("sku")
        assert result is not None, "Required property 'sku' is missing"
        return typing.cast("StorageAccountSku", result)

    @builtins.property
    def access_tier(self) -> typing.Optional[builtins.str]:
        '''The access tier for blob storage.

        :default: "Hot"

        Example::

            "Hot", "Cool"
        '''
        result = self._values.get("access_tier")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def allow_blob_public_access(self) -> typing.Optional[builtins.bool]:
        '''Whether to allow public access to blobs.

        :default: false
        '''
        result = self._values.get("allow_blob_public_access")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_https_traffic_only(self) -> typing.Optional[builtins.bool]:
        '''Whether to allow only HTTPS traffic.

        :default: true
        '''
        result = self._values.get("enable_https_traffic_only")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def encryption(self) -> typing.Optional[StorageAccountEncryption]:
        '''Encryption settings.'''
        result = self._values.get("encryption")
        return typing.cast(typing.Optional[StorageAccountEncryption], result)

    @builtins.property
    def identity(self) -> typing.Optional[StorageAccountIdentity]:
        '''Managed identity configuration.'''
        result = self._values.get("identity")
        return typing.cast(typing.Optional[StorageAccountIdentity], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def kind(self) -> typing.Optional[builtins.str]:
        '''The kind of Storage Account.

        :default: "StorageV2"

        Example::

            "StorageV2", "BlobStorage", "BlockBlobStorage", "FileStorage"
        '''
        result = self._values.get("kind")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def minimum_tls_version(self) -> typing.Optional[builtins.str]:
        '''The minimum TLS version required.

        :default: "TLS1_2"
        '''
        result = self._values.get("minimum_tls_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def network_acls(self) -> typing.Optional[StorageAccountNetworkAcls]:
        '''Network ACL rules for the storage account.'''
        result = self._values.get("network_acls")
        return typing.cast(typing.Optional[StorageAccountNetworkAcls], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the storage account will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountSku",
    jsii_struct_bases=[],
    name_mapping={"name": "name"},
)
class StorageAccountSku:
    def __init__(self, *, name: builtins.str) -> None:
        '''SKU configuration for Storage Account.

        :param name: The SKU name (Standard_LRS, Standard_GRS, Standard_RAGRS, Standard_ZRS, Premium_LRS, Premium_ZRS).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2cd6a7cf7b19b3dfce60a5f9bd53a384e04eb27e43cf000419c52b45028ce721)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''The SKU name (Standard_LRS, Standard_GRS, Standard_RAGRS, Standard_ZRS, Premium_LRS, Premium_ZRS).'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountSku(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_storageaccount.StorageAccountVirtualNetworkRule",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class StorageAccountVirtualNetworkRule:
    def __init__(self, *, id: builtins.str) -> None:
        '''Virtual network rule for network ACLs.

        :param id: Virtual network resource ID.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bae8b684687c3cd4d1bbaba0108d387574777fb8f1933d4d2ef40d51e56b999b)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "id": id,
        }

    @builtins.property
    def id(self) -> builtins.str:
        '''Virtual network resource ID.'''
        result = self._values.get("id")
        assert result is not None, "Required property 'id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StorageAccountVirtualNetworkRule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "StorageAccount",
    "StorageAccountBody",
    "StorageAccountBodyProperties",
    "StorageAccountEncryption",
    "StorageAccountEncryptionService",
    "StorageAccountEncryptionServices",
    "StorageAccountIdentity",
    "StorageAccountIpRule",
    "StorageAccountMonitoringOptions",
    "StorageAccountNetworkAcls",
    "StorageAccountProps",
    "StorageAccountSku",
    "StorageAccountVirtualNetworkRule",
]

publication.publish()

def _typecheckingstub__41854d4468855a70ae5f1dc34a157a49d7c0e460fcc47b8bdd4305ce4908b9d1(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    sku: typing.Union[StorageAccountSku, typing.Dict[builtins.str, typing.Any]],
    access_tier: typing.Optional[builtins.str] = None,
    allow_blob_public_access: typing.Optional[builtins.bool] = None,
    enable_https_traffic_only: typing.Optional[builtins.bool] = None,
    encryption: typing.Optional[typing.Union[StorageAccountEncryption, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[StorageAccountIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    kind: typing.Optional[builtins.str] = None,
    minimum_tls_version: typing.Optional[builtins.str] = None,
    network_acls: typing.Optional[typing.Union[StorageAccountNetworkAcls, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__9d1c55ad8e16edcd6df0d628ae2f437eebf09c41ad898bb7f33cd2d0532eae2f(
    action_group_id: builtins.str,
    workspace_id: typing.Optional[builtins.str] = None,
    *,
    availability_alert_severity: typing.Optional[jsii.Number] = None,
    availability_threshold: typing.Optional[jsii.Number] = None,
    egress_alert_severity: typing.Optional[jsii.Number] = None,
    egress_threshold: typing.Optional[jsii.Number] = None,
    enable_availability_alert: typing.Optional[builtins.bool] = None,
    enable_deletion_alert: typing.Optional[builtins.bool] = None,
    enable_egress_alert: typing.Optional[builtins.bool] = None,
    enable_transactions_alert: typing.Optional[builtins.bool] = None,
    transactions_alert_severity: typing.Optional[jsii.Number] = None,
    transactions_threshold: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__863af4470fa4b33aa4374ddd2e4a49bd0a7e70a54b592ab1213d6bc7da80d67e(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3d63355f7ee6ae8844c39b966a78b3b05766253c17bc9786d9db5178cc9c2f83(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0603a5973b278a7df99efd4c495d5efb096192322f0fdc3c36890aaf078fff25(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9eb371460134b4e374ffe7b776a5dd0781636550e31ff872e4ecf40db6d03706(
    *,
    kind: builtins.str,
    location: builtins.str,
    sku: typing.Union[StorageAccountSku, typing.Dict[builtins.str, typing.Any]],
    identity: typing.Optional[typing.Union[StorageAccountIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    properties: typing.Optional[typing.Union[StorageAccountBodyProperties, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a2909d304bea6ded084c6fc7f79f7589598798b89318ea780ba4d0992cbda22b(
    *,
    access_tier: typing.Optional[builtins.str] = None,
    allow_blob_public_access: typing.Optional[builtins.bool] = None,
    encryption: typing.Optional[typing.Union[StorageAccountEncryption, typing.Dict[builtins.str, typing.Any]]] = None,
    minimum_tls_version: typing.Optional[builtins.str] = None,
    network_acls: typing.Optional[typing.Union[StorageAccountNetworkAcls, typing.Dict[builtins.str, typing.Any]]] = None,
    supports_https_traffic_only: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ffface12b8c932dc7c8df23fb60d30a5d122b282c27ae791fc8b5c60a54bd0a2(
    *,
    key_source: typing.Optional[builtins.str] = None,
    services: typing.Optional[typing.Union[StorageAccountEncryptionServices, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__992b94e6f0ec55614c6c69292e6fb60bc36c4e5b0a27e716e8ca26944bb5d3f0(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__adc9d0b07c4ad108cf1c4ecf4c2b084547cd4a72f069dd85128913e2573d602b(
    *,
    blob: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
    file: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
    queue: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
    table: typing.Optional[typing.Union[StorageAccountEncryptionService, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__440277777ddc836a0314ec9b6a9d382be8b200f682ba40a4b94dd9a3c30e61d1(
    *,
    type: builtins.str,
    user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8373e0a23cf3c241ccee2939b9b6d82c3738cca45a04f997c3129df58fca5537(
    *,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8e41b957a3bc71d822b0a7f4b270460fe8063b4539b6462a7d0bc1c238f7495f(
    *,
    availability_alert_severity: typing.Optional[jsii.Number] = None,
    availability_threshold: typing.Optional[jsii.Number] = None,
    egress_alert_severity: typing.Optional[jsii.Number] = None,
    egress_threshold: typing.Optional[jsii.Number] = None,
    enable_availability_alert: typing.Optional[builtins.bool] = None,
    enable_deletion_alert: typing.Optional[builtins.bool] = None,
    enable_egress_alert: typing.Optional[builtins.bool] = None,
    enable_transactions_alert: typing.Optional[builtins.bool] = None,
    transactions_alert_severity: typing.Optional[jsii.Number] = None,
    transactions_threshold: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2c2d233bd116db5232ae8ecb424fbd2f64f4943cd00bf24596d4535435afd26e(
    *,
    bypass: typing.Optional[builtins.str] = None,
    default_action: typing.Optional[builtins.str] = None,
    ip_rules: typing.Optional[typing.Sequence[typing.Union[StorageAccountIpRule, typing.Dict[builtins.str, typing.Any]]]] = None,
    virtual_network_rules: typing.Optional[typing.Sequence[typing.Union[StorageAccountVirtualNetworkRule, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56262b0499cdaccde11afb901fc29542328539b98b808b0ee9f75bdac247652d(
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
    sku: typing.Union[StorageAccountSku, typing.Dict[builtins.str, typing.Any]],
    access_tier: typing.Optional[builtins.str] = None,
    allow_blob_public_access: typing.Optional[builtins.bool] = None,
    enable_https_traffic_only: typing.Optional[builtins.bool] = None,
    encryption: typing.Optional[typing.Union[StorageAccountEncryption, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[StorageAccountIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    kind: typing.Optional[builtins.str] = None,
    minimum_tls_version: typing.Optional[builtins.str] = None,
    network_acls: typing.Optional[typing.Union[StorageAccountNetworkAcls, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2cd6a7cf7b19b3dfce60a5f9bd53a384e04eb27e43cf000419c52b45028ce721(
    *,
    name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bae8b684687c3cd4d1bbaba0108d387574777fb8f1933d4d2ef40d51e56b999b(
    *,
    id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass
