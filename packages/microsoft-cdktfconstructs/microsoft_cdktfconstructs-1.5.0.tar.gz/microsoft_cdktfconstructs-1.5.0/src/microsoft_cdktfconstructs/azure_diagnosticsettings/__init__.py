r'''
# Azure Diagnostic Settings Construct

This module provides a version-aware implementation of Azure Diagnostic Settings using the AzapiResource framework.

## Overview

Azure Diagnostic Settings enable monitoring and observability by exporting platform logs and metrics to one or more destinations:

* **Log Analytics workspaces** - For querying and analysis
* **Storage accounts** - For long-term archival
* **Event Hubs** - For streaming to external systems

## Features

* ✅ **Version-aware** - Automatic API version management
* ✅ **Schema validation** - Input validation against Azure API schemas
* ✅ **Type-safe** - Full TypeScript type definitions
* ✅ **JSII-compliant** - Multi-language support (TypeScript, Python, Java, .NET)
* ✅ **Multiple destinations** - Support for workspace, storage, and event hub
* ✅ **Flexible configuration** - Category-based log and metric filtering

## Supported API Versions

* **2016-09-01** (Stable, Default) - Latest stable non-preview version
* **2021-05-01-preview** (Preview) - Latest preview version with additional features

## Installation

This module is part of the `@microsoft/terraform-cdk-constructs` package.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Usage

### Basic Example with Log Analytics

```python
import { DiagnosticSettings } from "@microsoft/terraform-cdk-constructs/azure-diagnosticsettings";
import { VirtualMachine } from "@microsoft/terraform-cdk-constructs/azure-virtualmachine";

// Create a virtual machine
const vm = new VirtualMachine(this, "my-vm", {
  name: "my-vm",
  resourceGroupId: resourceGroup.id,
  location: "eastus",
  // ... other VM configuration
});

// Add diagnostic settings
const diagnostics = new DiagnosticSettings(this, "vm-diagnostics", {
  name: "vm-diagnostics",
  targetResourceId: vm.id,
  workspaceId: logAnalyticsWorkspace.id,
  logs: [{
    categoryGroup: "allLogs",
    enabled: true
  }],
  metrics: [{
    category: "AllMetrics",
    enabled: true
  }]
});
```

### Multiple Destinations

```python
const diagnostics = new DiagnosticSettings(this, "storage-diagnostics", {
  name: "storage-diagnostics",
  targetResourceId: storageAccount.id,

  // Log Analytics for querying
  workspaceId: logAnalyticsWorkspace.id,

  // Storage for archival
  storageAccountId: archiveStorageAccount.id,

  // Event Hub for streaming
  eventHubAuthorizationRuleId: eventHub.authRuleId,
  eventHubName: "monitoring-hub",

  logs: [{
    category: "StorageRead",
    enabled: true,
    retentionPolicy: {
      enabled: true,
      days: 90
    }
  }, {
    category: "StorageWrite",
    enabled: true,
    retentionPolicy: {
      enabled: true,
      days: 90
    }
  }],

  metrics: [{
    category: "Transaction",
    enabled: true,
    retentionPolicy: {
      enabled: true,
      days: 30
    }
  }]
});
```

### Integrated Monitoring (via AzapiResource)

Resources extending `AzapiResource` can use the integrated monitoring configuration:

```python
const vm = new VirtualMachine(this, "my-vm", {
  name: "my-vm",
  resourceGroupId: resourceGroup.id,
  location: "eastus",

  monitoring: {
    enabled: true,
    diagnosticSettings: {
      workspaceId: logAnalyticsWorkspace.id,
      logs: [{
        categoryGroup: "allLogs",
        enabled: true
      }],
      metrics: [{
        category: "AllMetrics",
        enabled: true
      }]
    },
    metricAlerts: [{
      name: "high-cpu-alert",
      severity: 2,
      criteria: {
        // metric alert criteria
      }
    }]
  }
});
```

## Configuration

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | Name of the diagnostic setting |
| `targetResourceId` | `string` | Resource ID to attach diagnostic settings to |

**Note**: At least one destination (`workspaceId`, `storageAccountId`, or `eventHubAuthorizationRuleId`) must be specified.

### Destination Properties

| Property | Type | Description |
|----------|------|-------------|
| `workspaceId` | `string` | Log Analytics workspace resource ID |
| `storageAccountId` | `string` | Storage account resource ID for archival |
| `eventHubAuthorizationRuleId` | `string` | Event Hub authorization rule ID |
| `eventHubName` | `string` | Event Hub name (required if `eventHubAuthorizationRuleId` is set) |
| `logAnalyticsDestinationType` | `string` | Destination type: `Dedicated` or `AzureDiagnostics` |

### Log Configuration

```python
interface DiagnosticLogConfig {
  category?: string;           // Specific log category
  categoryGroup?: string;      // Log category group (e.g., "allLogs")
  enabled: boolean;           // Enable this log category
  retentionPolicy?: {
    enabled: boolean;
    days: number;             // Retention period in days
  };
}
```

### Metric Configuration

```python
interface DiagnosticMetricConfig {
  category: string;           // Metric category (e.g., "AllMetrics")
  enabled: boolean;           // Enable this metric category
  retentionPolicy?: {
    enabled: boolean;
    days: number;             // Retention period in days
  };
}
```

## Common Patterns

### All Logs and Metrics

```python
const diagnostics = new DiagnosticSettings(this, "complete-monitoring", {
  name: "complete-diagnostics",
  targetResourceId: resource.id,
  workspaceId: workspace.id,
  logs: [{
    categoryGroup: "allLogs",
    enabled: true
  }],
  metrics: [{
    category: "AllMetrics",
    enabled: true
  }]
});
```

### Selective Logging with Retention

```python
const diagnostics = new DiagnosticSettings(this, "selective-logging", {
  name: "audit-only",
  targetResourceId: resource.id,
  storageAccountId: archiveStorage.id,
  logs: [{
    category: "AuditEvent",
    enabled: true,
    retentionPolicy: {
      enabled: true,
      days: 365
    }
  }, {
    category: "SecurityEvent",
    enabled: true,
    retentionPolicy: {
      enabled: true,
      days: 365
    }
  }],
  metrics: [{
    category: "AllMetrics",
    enabled: false
  }]
});
```

### Streaming to Event Hub

```python
const diagnostics = new DiagnosticSettings(this, "stream-to-siem", {
  name: "siem-streaming",
  targetResourceId: resource.id,
  eventHubAuthorizationRuleId: eventHub.authRuleId,
  eventHubName: "security-events",
  logs: [{
    category: "SecurityEvent",
    enabled: true
  }]
});
```

## API Version Management

### Using Default Stable Version (Recommended)

```python
// Automatically uses the stable version (2016-09-01)
const diagnostics = new DiagnosticSettings(this, "diagnostics", {
  name: "my-diagnostics",
  targetResourceId: resource.id,
  workspaceId: workspace.id
});
```

### Using Preview Version for Latest Features

```python
// Use preview version for category groups and other new features
const diagnostics = new DiagnosticSettings(this, "diagnostics", {
  name: "my-diagnostics",
  targetResourceId: resource.id,
  workspaceId: workspace.id,
  apiVersion: "2021-05-01-preview"  // Preview version
});
```

### Explicit Version Pinning

```python
// Explicitly specify version for full control
const diagnostics = new DiagnosticSettings(this, "diagnostics", {
  name: "my-diagnostics",
  targetResourceId: resource.id,
  workspaceId: workspace.id,
  apiVersion: "2016-09-01"  // Stable version
});
```

## Validation

The construct automatically validates:

* ✅ At least one destination is specified
* ✅ `eventHubName` is provided when `eventHubAuthorizationRuleId` is set
* ✅ Required properties are present
* ✅ Property types match schema definitions

## Best Practices

1. **Use Log Analytics for Querying**: Send logs to Log Analytics for powerful query capabilities
2. **Use Storage for Archival**: Configure long-term retention in storage accounts
3. **Use Event Hub for Integration**: Stream to external SIEM or monitoring systems
4. **Enable All Logs Initially**: Start with `categoryGroup: "allLogs"` and refine based on needs
5. **Set Appropriate Retention**: Balance between compliance requirements and storage costs
6. **Monitor Ingestion Costs**: Track Log Analytics ingestion and storage costs

## Troubleshooting

### Error: "At least one destination must be specified"

**Cause**: No destination (workspace, storage, or event hub) was provided.

**Solution**: Specify at least one of:

* `workspaceId`
* `storageAccountId`
* `eventHubAuthorizationRuleId`

### Error: "eventHubName is required when eventHubAuthorizationRuleId is specified"

**Cause**: `eventHubAuthorizationRuleId` was provided without `eventHubName`.

**Solution**: Add the `eventHubName` property:

```python
{
  eventHubAuthorizationRuleId: eventHub.authRuleId,
  eventHubName: "my-event-hub"  // Add this
}
```

## Related Constructs

* [`ActionGroup`](../azure-actiongroup/README.md) - Alert notification groups
* [`MetricAlert`](../azure-metricalert/README.md) - Metric-based alerting
* [`ActivityLogAlert`](../azure-activitylogalert/README.md) - Activity log alerting

## Migration from Old Pattern

If you were using the old `AzapiDiagnosticSettings` helper class, migrate to the new construct:

### Before (Old Pattern)

```python
// This pattern is no longer supported
resource.addDiagnosticSettings({
  workspaceId: workspace.id,
  metrics: ["AllMetrics"]
});
```

### After (New Pattern)

```python
// Use the full construct
import { DiagnosticSettings } from "@microsoft/terraform-cdk-constructs/azure-diagnosticsettings";

new DiagnosticSettings(this, "diagnostics", {
  name: "diagnostics",
  targetResourceId: resource.id,
  workspaceId: workspace.id,
  metrics: [{
    category: "AllMetrics",
    enabled: true
  }]
});
```

Or use integrated monitoring:

```python
// Via monitoring configuration
const resource = new SomeResource(this, "resource", {
  // ... resource props
  monitoring: {
    diagnosticSettings: {
      workspaceId: workspace.id,
      metrics: [{
        category: "AllMetrics",
        enabled: true
      }]
    }
  }
});
```

## References

* [Azure Diagnostic Settings Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/diagnostic-settings)
* [Azure Monitor Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/)
* [Log Analytics Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-overview)
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
    DiagnosticLogConfig as _DiagnosticLogConfig_990fcbff,
    DiagnosticMetricConfig as _DiagnosticMetricConfig_29c0add1,
    MonitoringConfig as _MonitoringConfig_7c28df74,
)


class DiagnosticSettings(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_diagnosticsettings.DiagnosticSettings",
):
    '''Unified Azure Diagnostic Settings implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    Diagnostic Settings enable monitoring and observability by exporting platform logs and metrics
    to one or more destinations including Log Analytics workspaces, Storage accounts, and Event Hubs.

    Example::

        // Diagnostic settings with multiple destinations:
        const diagnostics = new DiagnosticSettings(this, "storage-diagnostics", {
          name: "storage-diagnostics",
          targetResourceId: storageAccount.id,
          workspaceId: logAnalyticsWorkspace.id,
          storageAccountId: archiveStorageAccount.id,
          eventHubAuthorizationRuleId: eventHub.authRuleId,
          eventHubName: "monitoring-hub",
          logs: [{
            category: "StorageRead",
            enabled: true,
            retentionPolicy: {
              enabled: true,
              days: 90
            }
          }],
          metrics: [{
            category: "Transaction",
            enabled: true
          }]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        target_resource_id: builtins.str,
        event_hub_authorization_rule_id: typing.Optional[builtins.str] = None,
        event_hub_name: typing.Optional[builtins.str] = None,
        log_analytics_destination_type: typing.Optional[builtins.str] = None,
        logs: typing.Optional[typing.Sequence[typing.Union[_DiagnosticLogConfig_990fcbff, typing.Dict[builtins.str, typing.Any]]]] = None,
        metrics: typing.Optional[typing.Sequence[typing.Union[_DiagnosticMetricConfig_29c0add1, typing.Dict[builtins.str, typing.Any]]]] = None,
        storage_account_id: typing.Optional[builtins.str] = None,
        workspace_id: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Diagnostic Settings using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param target_resource_id: Target resource ID to attach diagnostic settings to This is the resource being monitored.
        :param event_hub_authorization_rule_id: Event Hub authorization rule ID for streaming Requires eventHubName to be specified as well.
        :param event_hub_name: Event Hub name for streaming Required when eventHubAuthorizationRuleId is specified.
        :param log_analytics_destination_type: Log Analytics destination type Determines the table structure in Log Analytics. Default: undefined (uses default behavior)
        :param logs: Log categories to enable Defines which log categories should be exported.
        :param metrics: Metric categories to enable Defines which metric categories should be exported.
        :param storage_account_id: Storage account ID for log/metric destination At least one destination (workspace, storage, or event hub) must be specified.
        :param workspace_id: Log Analytics workspace ID for log/metric destination At least one destination (workspace, storage, or event hub) must be specified.
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
            type_hints = typing.get_type_hints(_typecheckingstub__b54ac402d62cc6106cec44db8c4438a155b2f3c8801f2fa96359fbbf08daa6dd)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DiagnosticSettingsProps(
            target_resource_id=target_resource_id,
            event_hub_authorization_rule_id=event_hub_authorization_rule_id,
            event_hub_name=event_hub_name,
            log_analytics_destination_type=log_analytics_destination_type,
            logs=logs,
            metrics=metrics,
            storage_account_id=storage_account_id,
            workspace_id=workspace_id,
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
            type_hints = typing.get_type_hints(_typecheckingstub__453f49f1fa67463a23d4e6e74b94c3a90998d2955997c8ab376e77795b3b33af)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the latest stable (non-preview) version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for Diagnostic Settings Diagnostic Settings are child resources attached to the monitored resource.

        :param props: - The resource properties.

        :return: The parent resource ID (the target resource being monitored)
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e95760e8fe42c806ebc49f0c7b3486baa7ce988893536f14022ea426c231a985)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Diagnostic Settings.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

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
    def props(self) -> "DiagnosticSettingsProps":
        '''The input properties for this Diagnostic Settings instance.'''
        return typing.cast("DiagnosticSettingsProps", jsii.get(self, "props"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_diagnosticsettings.DiagnosticSettingsBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class DiagnosticSettingsBody:
    def __init__(
        self,
        *,
        properties: typing.Union["DiagnosticSettingsBodyProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Diagnostic Settings API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = DiagnosticSettingsBodyProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__31fbdbb03e0f6f1c703e0a0211ad6dcece578a8f1b75270fedd46d7d6e94fb7a)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "DiagnosticSettingsBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("DiagnosticSettingsBodyProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DiagnosticSettingsBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_diagnosticsettings.DiagnosticSettingsBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "event_hub_authorization_rule_id": "eventHubAuthorizationRuleId",
        "event_hub_name": "eventHubName",
        "log_analytics_destination_type": "logAnalyticsDestinationType",
        "logs": "logs",
        "metrics": "metrics",
        "storage_account_id": "storageAccountId",
        "workspace_id": "workspaceId",
    },
)
class DiagnosticSettingsBodyProperties:
    def __init__(
        self,
        *,
        event_hub_authorization_rule_id: typing.Optional[builtins.str] = None,
        event_hub_name: typing.Optional[builtins.str] = None,
        log_analytics_destination_type: typing.Optional[builtins.str] = None,
        logs: typing.Optional[typing.Sequence[typing.Union[_DiagnosticLogConfig_990fcbff, typing.Dict[builtins.str, typing.Any]]]] = None,
        metrics: typing.Optional[typing.Sequence[typing.Union[_DiagnosticMetricConfig_29c0add1, typing.Dict[builtins.str, typing.Any]]]] = None,
        storage_account_id: typing.Optional[builtins.str] = None,
        workspace_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Diagnostic Settings properties for the request body.

        :param event_hub_authorization_rule_id: 
        :param event_hub_name: 
        :param log_analytics_destination_type: 
        :param logs: 
        :param metrics: 
        :param storage_account_id: 
        :param workspace_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e7c8782c636f745e788ac6b2ed05e1bce5c1cc45e292df7c0241b78e696e1d55)
            check_type(argname="argument event_hub_authorization_rule_id", value=event_hub_authorization_rule_id, expected_type=type_hints["event_hub_authorization_rule_id"])
            check_type(argname="argument event_hub_name", value=event_hub_name, expected_type=type_hints["event_hub_name"])
            check_type(argname="argument log_analytics_destination_type", value=log_analytics_destination_type, expected_type=type_hints["log_analytics_destination_type"])
            check_type(argname="argument logs", value=logs, expected_type=type_hints["logs"])
            check_type(argname="argument metrics", value=metrics, expected_type=type_hints["metrics"])
            check_type(argname="argument storage_account_id", value=storage_account_id, expected_type=type_hints["storage_account_id"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if event_hub_authorization_rule_id is not None:
            self._values["event_hub_authorization_rule_id"] = event_hub_authorization_rule_id
        if event_hub_name is not None:
            self._values["event_hub_name"] = event_hub_name
        if log_analytics_destination_type is not None:
            self._values["log_analytics_destination_type"] = log_analytics_destination_type
        if logs is not None:
            self._values["logs"] = logs
        if metrics is not None:
            self._values["metrics"] = metrics
        if storage_account_id is not None:
            self._values["storage_account_id"] = storage_account_id
        if workspace_id is not None:
            self._values["workspace_id"] = workspace_id

    @builtins.property
    def event_hub_authorization_rule_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("event_hub_authorization_rule_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def event_hub_name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("event_hub_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def log_analytics_destination_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("log_analytics_destination_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def logs(self) -> typing.Optional[typing.List[_DiagnosticLogConfig_990fcbff]]:
        result = self._values.get("logs")
        return typing.cast(typing.Optional[typing.List[_DiagnosticLogConfig_990fcbff]], result)

    @builtins.property
    def metrics(self) -> typing.Optional[typing.List[_DiagnosticMetricConfig_29c0add1]]:
        result = self._values.get("metrics")
        return typing.cast(typing.Optional[typing.List[_DiagnosticMetricConfig_29c0add1]], result)

    @builtins.property
    def storage_account_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("storage_account_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def workspace_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("workspace_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DiagnosticSettingsBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_diagnosticsettings.DiagnosticSettingsProps",
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
        "target_resource_id": "targetResourceId",
        "event_hub_authorization_rule_id": "eventHubAuthorizationRuleId",
        "event_hub_name": "eventHubName",
        "log_analytics_destination_type": "logAnalyticsDestinationType",
        "logs": "logs",
        "metrics": "metrics",
        "storage_account_id": "storageAccountId",
        "workspace_id": "workspaceId",
    },
)
class DiagnosticSettingsProps(_AzapiResourceProps_141a2340):
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
        target_resource_id: builtins.str,
        event_hub_authorization_rule_id: typing.Optional[builtins.str] = None,
        event_hub_name: typing.Optional[builtins.str] = None,
        log_analytics_destination_type: typing.Optional[builtins.str] = None,
        logs: typing.Optional[typing.Sequence[typing.Union[_DiagnosticLogConfig_990fcbff, typing.Dict[builtins.str, typing.Any]]]] = None,
        metrics: typing.Optional[typing.Sequence[typing.Union[_DiagnosticMetricConfig_29c0add1, typing.Dict[builtins.str, typing.Any]]]] = None,
        storage_account_id: typing.Optional[builtins.str] = None,
        workspace_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Diagnostic Settings.

        Extends AzapiResourceProps with Diagnostic Settings specific properties

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
        :param target_resource_id: Target resource ID to attach diagnostic settings to This is the resource being monitored.
        :param event_hub_authorization_rule_id: Event Hub authorization rule ID for streaming Requires eventHubName to be specified as well.
        :param event_hub_name: Event Hub name for streaming Required when eventHubAuthorizationRuleId is specified.
        :param log_analytics_destination_type: Log Analytics destination type Determines the table structure in Log Analytics. Default: undefined (uses default behavior)
        :param logs: Log categories to enable Defines which log categories should be exported.
        :param metrics: Metric categories to enable Defines which metric categories should be exported.
        :param storage_account_id: Storage account ID for log/metric destination At least one destination (workspace, storage, or event hub) must be specified.
        :param workspace_id: Log Analytics workspace ID for log/metric destination At least one destination (workspace, storage, or event hub) must be specified.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6ef17aa06c685ec43cb818a79769cd72f3d69e3f7e3914ef44b16fb2e1766801)
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
            check_type(argname="argument target_resource_id", value=target_resource_id, expected_type=type_hints["target_resource_id"])
            check_type(argname="argument event_hub_authorization_rule_id", value=event_hub_authorization_rule_id, expected_type=type_hints["event_hub_authorization_rule_id"])
            check_type(argname="argument event_hub_name", value=event_hub_name, expected_type=type_hints["event_hub_name"])
            check_type(argname="argument log_analytics_destination_type", value=log_analytics_destination_type, expected_type=type_hints["log_analytics_destination_type"])
            check_type(argname="argument logs", value=logs, expected_type=type_hints["logs"])
            check_type(argname="argument metrics", value=metrics, expected_type=type_hints["metrics"])
            check_type(argname="argument storage_account_id", value=storage_account_id, expected_type=type_hints["storage_account_id"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "target_resource_id": target_resource_id,
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
        if event_hub_authorization_rule_id is not None:
            self._values["event_hub_authorization_rule_id"] = event_hub_authorization_rule_id
        if event_hub_name is not None:
            self._values["event_hub_name"] = event_hub_name
        if log_analytics_destination_type is not None:
            self._values["log_analytics_destination_type"] = log_analytics_destination_type
        if logs is not None:
            self._values["logs"] = logs
        if metrics is not None:
            self._values["metrics"] = metrics
        if storage_account_id is not None:
            self._values["storage_account_id"] = storage_account_id
        if workspace_id is not None:
            self._values["workspace_id"] = workspace_id

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
    def target_resource_id(self) -> builtins.str:
        '''Target resource ID to attach diagnostic settings to This is the resource being monitored.'''
        result = self._values.get("target_resource_id")
        assert result is not None, "Required property 'target_resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def event_hub_authorization_rule_id(self) -> typing.Optional[builtins.str]:
        '''Event Hub authorization rule ID for streaming Requires eventHubName to be specified as well.'''
        result = self._values.get("event_hub_authorization_rule_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def event_hub_name(self) -> typing.Optional[builtins.str]:
        '''Event Hub name for streaming Required when eventHubAuthorizationRuleId is specified.'''
        result = self._values.get("event_hub_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def log_analytics_destination_type(self) -> typing.Optional[builtins.str]:
        '''Log Analytics destination type Determines the table structure in Log Analytics.

        :default: undefined (uses default behavior)
        '''
        result = self._values.get("log_analytics_destination_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def logs(self) -> typing.Optional[typing.List[_DiagnosticLogConfig_990fcbff]]:
        '''Log categories to enable Defines which log categories should be exported.'''
        result = self._values.get("logs")
        return typing.cast(typing.Optional[typing.List[_DiagnosticLogConfig_990fcbff]], result)

    @builtins.property
    def metrics(self) -> typing.Optional[typing.List[_DiagnosticMetricConfig_29c0add1]]:
        '''Metric categories to enable Defines which metric categories should be exported.'''
        result = self._values.get("metrics")
        return typing.cast(typing.Optional[typing.List[_DiagnosticMetricConfig_29c0add1]], result)

    @builtins.property
    def storage_account_id(self) -> typing.Optional[builtins.str]:
        '''Storage account ID for log/metric destination At least one destination (workspace, storage, or event hub) must be specified.'''
        result = self._values.get("storage_account_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def workspace_id(self) -> typing.Optional[builtins.str]:
        '''Log Analytics workspace ID for log/metric destination At least one destination (workspace, storage, or event hub) must be specified.'''
        result = self._values.get("workspace_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DiagnosticSettingsProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DiagnosticSettings",
    "DiagnosticSettingsBody",
    "DiagnosticSettingsBodyProperties",
    "DiagnosticSettingsProps",
]

publication.publish()

def _typecheckingstub__b54ac402d62cc6106cec44db8c4438a155b2f3c8801f2fa96359fbbf08daa6dd(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    target_resource_id: builtins.str,
    event_hub_authorization_rule_id: typing.Optional[builtins.str] = None,
    event_hub_name: typing.Optional[builtins.str] = None,
    log_analytics_destination_type: typing.Optional[builtins.str] = None,
    logs: typing.Optional[typing.Sequence[typing.Union[_DiagnosticLogConfig_990fcbff, typing.Dict[builtins.str, typing.Any]]]] = None,
    metrics: typing.Optional[typing.Sequence[typing.Union[_DiagnosticMetricConfig_29c0add1, typing.Dict[builtins.str, typing.Any]]]] = None,
    storage_account_id: typing.Optional[builtins.str] = None,
    workspace_id: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__453f49f1fa67463a23d4e6e74b94c3a90998d2955997c8ab376e77795b3b33af(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e95760e8fe42c806ebc49f0c7b3486baa7ce988893536f14022ea426c231a985(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31fbdbb03e0f6f1c703e0a0211ad6dcece578a8f1b75270fedd46d7d6e94fb7a(
    *,
    properties: typing.Union[DiagnosticSettingsBodyProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e7c8782c636f745e788ac6b2ed05e1bce5c1cc45e292df7c0241b78e696e1d55(
    *,
    event_hub_authorization_rule_id: typing.Optional[builtins.str] = None,
    event_hub_name: typing.Optional[builtins.str] = None,
    log_analytics_destination_type: typing.Optional[builtins.str] = None,
    logs: typing.Optional[typing.Sequence[typing.Union[_DiagnosticLogConfig_990fcbff, typing.Dict[builtins.str, typing.Any]]]] = None,
    metrics: typing.Optional[typing.Sequence[typing.Union[_DiagnosticMetricConfig_29c0add1, typing.Dict[builtins.str, typing.Any]]]] = None,
    storage_account_id: typing.Optional[builtins.str] = None,
    workspace_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6ef17aa06c685ec43cb818a79769cd72f3d69e3f7e3914ef44b16fb2e1766801(
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
    target_resource_id: builtins.str,
    event_hub_authorization_rule_id: typing.Optional[builtins.str] = None,
    event_hub_name: typing.Optional[builtins.str] = None,
    log_analytics_destination_type: typing.Optional[builtins.str] = None,
    logs: typing.Optional[typing.Sequence[typing.Union[_DiagnosticLogConfig_990fcbff, typing.Dict[builtins.str, typing.Any]]]] = None,
    metrics: typing.Optional[typing.Sequence[typing.Union[_DiagnosticMetricConfig_29c0add1, typing.Dict[builtins.str, typing.Any]]]] = None,
    storage_account_id: typing.Optional[builtins.str] = None,
    workspace_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
