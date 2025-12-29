r'''
# Azure Metric Alert Construct

This construct provides a type-safe, version-aware implementation of Azure Metric Alerts using the AZAPI provider framework.

## Overview

Metric Alerts monitor Azure resource metrics and trigger notifications when thresholds are breached. They support both static thresholds and dynamic thresholds based on machine learning.

## Features

* **Version Management**: Automatic resolution to the latest stable API version (2018-03-01)
* **Type Safety**: Full TypeScript type definitions with JSII compliance
* **Static & Dynamic Thresholds**: Support for both threshold types
* **Multi-Resource Alerts**: Monitor metrics across multiple resources
* **Dimension Filtering**: Filter metrics by dimensions
* **Validation**: Schema-driven property validation
* **Multi-language**: Generated bindings for TypeScript, Python, Java, and C#

## Installation

This construct is part of the `@microsoft/terraform-cdk-constructs` package.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Usage

### Basic Static Threshold Alert

```python
import { MetricAlert } from "@microsoft/terraform-cdk-constructs/azure-metricalert";
import { ActionGroup } from "@microsoft/terraform-cdk-constructs/azure-actiongroup";
import { VirtualMachine } from "@microsoft/terraform-cdk-constructs/azure-virtualmachine";

const cpuAlert = new MetricAlert(this, "high-cpu", {
  name: "vm-high-cpu-alert",
  resourceGroupId: resourceGroup.id,
  severity: 2,
  scopes: [virtualMachine.id],
  criteria: {
    type: "StaticThreshold",
    metricName: "Percentage CPU",
    operator: "GreaterThan",
    threshold: 80,
    timeAggregation: "Average"
  },
  actions: [{
    actionGroupId: actionGroup.id
  }],
  tags: {
    Environment: "Production",
    AlertType: "Performance"
  }
});
```

### Dynamic Threshold Alert

```python
const dynamicAlert = new MetricAlert(this, "dynamic-cpu", {
  name: "vm-dynamic-cpu-alert",
  description: "Dynamic CPU threshold based on historical patterns",
  resourceGroupId: resourceGroup.id,
  severity: 2,
  scopes: [resourceGroup.id],
  targetResourceType: "Microsoft.Compute/virtualMachines",
  targetResourceRegion: "eastus",
  evaluationFrequency: "PT1M",
  windowSize: "PT5M",
  criteria: {
    type: "DynamicThreshold",
    metricName: "Percentage CPU",
    operator: "GreaterThan",
    alertSensitivity: "Medium",
    failingPeriods: {
      numberOfEvaluationPeriods: 4,
      minFailingPeriodsToAlert: 3
    },
    timeAggregation: "Average"
  },
  actions: [{
    actionGroupId: actionGroup.id
  }]
});
```

### Alert with Dimensions

```python
const dimensionAlert = new MetricAlert(this, "app-errors", {
  name: "app-service-errors",
  resourceGroupId: resourceGroup.id,
  severity: 1,
  scopes: [appService.id],
  criteria: {
    type: "StaticThreshold",
    metricName: "Http5xx",
    operator: "GreaterThan",
    threshold: 10,
    timeAggregation: "Total",
    dimensions: [{
      name: "Instance",
      operator: "Include",
      values: ["*"]
    }]
  },
  actions: [{
    actionGroupId: actionGroup.id,
    webHookProperties: {
      severity: "high",
      environment: "production"
    }
  }]
});
```

### Multi-Resource Alert

```python
const multiResourceAlert = new MetricAlert(this, "all-vms-cpu", {
  name: "all-vms-high-cpu",
  description: "Monitor CPU across all VMs in resource group",
  resourceGroupId: resourceGroup.id,
  severity: 3,
  scopes: [resourceGroup.id],
  targetResourceType: "Microsoft.Compute/virtualMachines",
  targetResourceRegion: "eastus",
  criteria: {
    type: "StaticThreshold",
    metricName: "Percentage CPU",
    operator: "GreaterThan",
    threshold: 90,
    timeAggregation: "Average"
  },
  actions: [{
    actionGroupId: actionGroup.id
  }]
});
```

## Properties

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | The name of the metric alert |
| `severity` | `0 \| 1 \| 2 \| 3 \| 4` | Alert severity (0=Critical, 4=Verbose) |
| `scopes` | `string[]` | Resource IDs that this alert is scoped to |
| `criteria` | `StaticThresholdCriteria \| DynamicThresholdCriteria` | Alert criteria |

### Optional Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `location` | `string` | Azure region | `"global"` |
| `description` | `string` | Description of the alert rule | - |
| `enabled` | `boolean` | Whether the alert rule is enabled | `true` |
| `evaluationFrequency` | `string` | Evaluation frequency (ISO 8601) | `"PT5M"` |
| `windowSize` | `string` | Aggregation window (ISO 8601) | `"PT15M"` |
| `targetResourceType` | `string` | Resource type for multi-resource alerts | - |
| `targetResourceRegion` | `string` | Region for multi-resource alerts | - |
| `actions` | `MetricAlertAction[]` | Action groups to notify | `[]` |
| `autoMitigate` | `boolean` | Auto-resolve when condition clears | `true` |
| `tags` | `Record<string, string>` | Resource tags | `{}` |
| `resourceGroupId` | `string` | Resource group ID | Required |
| `apiVersion` | `string` | Explicit API version | Latest |

## Criteria Types

### StaticThresholdCriteria

```python
interface StaticThresholdCriteria {
  type: "StaticThreshold";
  metricName: string;
  metricNamespace?: string;
  operator: "GreaterThan" | "LessThan" | "GreaterOrEqual" | "LessOrEqual" | "Equals";
  threshold: number;
  timeAggregation: "Average" | "Count" | "Minimum" | "Maximum" | "Total";
  dimensions?: MetricDimension[];
}
```

### DynamicThresholdCriteria

```python
interface DynamicThresholdCriteria {
  type: "DynamicThreshold";
  metricName: string;
  metricNamespace?: string;
  operator: "GreaterThan" | "LessThan" | "GreaterOrLessThan";
  alertSensitivity: "Low" | "Medium" | "High";
  failingPeriods: {
    numberOfEvaluationPeriods: number;
    minFailingPeriodsToAlert: number;
  };
  timeAggregation: "Average" | "Count" | "Minimum" | "Maximum" | "Total";
  dimensions?: MetricDimension[];
  ignoreDataBefore?: string;  // ISO 8601 date
}
```

## Severity Levels

| Level | Name | Use Case |
|-------|------|----------|
| 0 | Critical | System down, immediate action required |
| 1 | Error | Major functionality impaired |
| 2 | Warning | Potential issue, monitoring required |
| 3 | Informational | FYI, no action needed |
| 4 | Verbose | Detailed information for debugging |

## Time Windows

Common ISO 8601 duration values:

* `PT1M` - 1 minute
* `PT5M` - 5 minutes (default evaluation frequency)
* `PT15M` - 15 minutes (default window size)
* `PT30M` - 30 minutes
* `PT1H` - 1 hour
* `PT6H` - 6 hours
* `PT12H` - 12 hours
* `PT24H` - 24 hours

## Dynamic Threshold Sensitivity

| Sensitivity | Description |
|-------------|-------------|
| Low | Loose bounds, fewer alerts |
| Medium | Balanced sensitivity (recommended) |
| High | Tight bounds, more alerts |

## Metric Dimensions

Filter metrics by specific dimension values:

```python
dimensions: [{
  name: "Instance",
  operator: "Include",
  values: ["instance1", "instance2"]
}, {
  name: "StatusCode",
  operator: "Exclude",
  values: ["404", "401"]
}]
```

## Common Metrics by Resource Type

### Virtual Machines

* `Percentage CPU`
* `Available Memory Bytes`
* `Disk Read Bytes`
* `Disk Write Bytes`
* `Network In Total`
* `Network Out Total`

### App Service

* `Http5xx`
* `Http4xx`
* `ResponseTime`
* `Requests`
* `CpuPercentage`
* `MemoryPercentage`

### Storage Account

* `UsedCapacity`
* `Transactions`
* `Availability`
* `SuccessE2ELatency`

### SQL Database

* `cpu_percent`
* `dtu_consumption_percent`
* `storage_percent`
* `connection_successful`
* `connection_failed`

## Best Practices

1. **Use Appropriate Severity**: Match severity to business impact
2. **Set Realistic Thresholds**: Base on historical data and capacity planning
3. **Enable Auto-Mitigation**: Set `autoMitigate: true` to reduce noise
4. **Use Dynamic Thresholds**: For metrics with varying patterns
5. **Add Descriptions**: Document the alert purpose and response procedures
6. **Tag Alerts**: Use tags for organization and filtering
7. **Test Actions**: Verify action groups receive notifications
8. **Review Regularly**: Adjust thresholds based on false positive rates

## Outputs

The Metric Alert construct provides the following outputs:

* `id`: The resource ID of the metric alert
* `name`: The name of the metric alert

## API Versions

### Supported Versions

* **2018-03-01** (Active, Latest) - Stable API version with dynamic threshold support

## Examples

See the [examples directory](../../examples/) for complete working examples:

* Static threshold alerts
* Dynamic threshold alerts
* Multi-resource monitoring
* Dimension filtering
* Integration with action groups

## Related Constructs

* [`ActionGroup`](../azure-actiongroup/) - Notification hub
* [`ActivityLogAlert`](../azure-activitylogalert/) - Activity log alerting

## Resources

* [Azure Metric Alerts Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-metric-overview)
* [Dynamic Thresholds](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-dynamic-thresholds)
* [Supported Metrics](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/metrics-supported)
* [REST API Reference](https://learn.microsoft.com/en-us/rest/api/monitor/metricalerts)
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
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.DynamicThresholdCriteria",
    jsii_struct_bases=[],
    name_mapping={
        "alert_sensitivity": "alertSensitivity",
        "failing_periods": "failingPeriods",
        "metric_name": "metricName",
        "operator": "operator",
        "time_aggregation": "timeAggregation",
        "type": "type",
        "dimensions": "dimensions",
        "ignore_data_before": "ignoreDataBefore",
        "metric_namespace": "metricNamespace",
    },
)
class DynamicThresholdCriteria:
    def __init__(
        self,
        *,
        alert_sensitivity: builtins.str,
        failing_periods: typing.Union["MetricAlertFailingPeriods", typing.Dict[builtins.str, typing.Any]],
        metric_name: builtins.str,
        operator: builtins.str,
        time_aggregation: builtins.str,
        type: builtins.str,
        dimensions: typing.Optional[typing.Sequence[typing.Union["MetricDimension", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_data_before: typing.Optional[builtins.str] = None,
        metric_namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Dynamic threshold criteria configuration.

        :param alert_sensitivity: The alert sensitivity (Low, Medium, High).
        :param failing_periods: Failing periods configuration.
        :param metric_name: The metric name.
        :param operator: The comparison operator.
        :param time_aggregation: The time aggregation method.
        :param type: The criteria type.
        :param dimensions: Metric dimensions for filtering (optional).
        :param ignore_data_before: Ignore data before this date (ISO 8601 format).
        :param metric_namespace: The metric namespace (optional).
        '''
        if isinstance(failing_periods, dict):
            failing_periods = MetricAlertFailingPeriods(**failing_periods)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__30c9b64719ac2d95b79fe194d09c972c132e3fc9ef357cf8a185eb391c1d1cdc)
            check_type(argname="argument alert_sensitivity", value=alert_sensitivity, expected_type=type_hints["alert_sensitivity"])
            check_type(argname="argument failing_periods", value=failing_periods, expected_type=type_hints["failing_periods"])
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument operator", value=operator, expected_type=type_hints["operator"])
            check_type(argname="argument time_aggregation", value=time_aggregation, expected_type=type_hints["time_aggregation"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
            check_type(argname="argument ignore_data_before", value=ignore_data_before, expected_type=type_hints["ignore_data_before"])
            check_type(argname="argument metric_namespace", value=metric_namespace, expected_type=type_hints["metric_namespace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "alert_sensitivity": alert_sensitivity,
            "failing_periods": failing_periods,
            "metric_name": metric_name,
            "operator": operator,
            "time_aggregation": time_aggregation,
            "type": type,
        }
        if dimensions is not None:
            self._values["dimensions"] = dimensions
        if ignore_data_before is not None:
            self._values["ignore_data_before"] = ignore_data_before
        if metric_namespace is not None:
            self._values["metric_namespace"] = metric_namespace

    @builtins.property
    def alert_sensitivity(self) -> builtins.str:
        '''The alert sensitivity (Low, Medium, High).'''
        result = self._values.get("alert_sensitivity")
        assert result is not None, "Required property 'alert_sensitivity' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def failing_periods(self) -> "MetricAlertFailingPeriods":
        '''Failing periods configuration.'''
        result = self._values.get("failing_periods")
        assert result is not None, "Required property 'failing_periods' is missing"
        return typing.cast("MetricAlertFailingPeriods", result)

    @builtins.property
    def metric_name(self) -> builtins.str:
        '''The metric name.'''
        result = self._values.get("metric_name")
        assert result is not None, "Required property 'metric_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def operator(self) -> builtins.str:
        '''The comparison operator.'''
        result = self._values.get("operator")
        assert result is not None, "Required property 'operator' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def time_aggregation(self) -> builtins.str:
        '''The time aggregation method.'''
        result = self._values.get("time_aggregation")
        assert result is not None, "Required property 'time_aggregation' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''The criteria type.'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def dimensions(self) -> typing.Optional[typing.List["MetricDimension"]]:
        '''Metric dimensions for filtering (optional).'''
        result = self._values.get("dimensions")
        return typing.cast(typing.Optional[typing.List["MetricDimension"]], result)

    @builtins.property
    def ignore_data_before(self) -> typing.Optional[builtins.str]:
        '''Ignore data before this date (ISO 8601 format).'''
        result = self._values.get("ignore_data_before")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metric_namespace(self) -> typing.Optional[builtins.str]:
        '''The metric namespace (optional).'''
        result = self._values.get("metric_namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DynamicThresholdCriteria(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class MetricAlert(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricAlert",
):
    '''Unified Azure Metric Alert implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    Metric Alerts monitor Azure resource metrics and trigger notifications when thresholds are breached.
    They support both static thresholds and dynamic thresholds based on machine learning.

    Example::

        // Dynamic threshold alert with machine learning:
        const dynamicAlert = new MetricAlert(this, "dynamic-cpu", {
          name: "vm-dynamic-cpu-alert",
          resourceGroupId: resourceGroup.id,
          severity: 2,
          scopes: [resourceGroup.id],
          targetResourceType: "Microsoft.Compute/virtualMachines",
          targetResourceRegion: "eastus",
          criteria: {
            type: "DynamicThreshold",
            metricName: "Percentage CPU",
            operator: "GreaterThan",
            alertSensitivity: "Medium",
            failingPeriods: {
              numberOfEvaluationPeriods: 4,
              minFailingPeriodsToAlert: 3
            },
            timeAggregation: "Average"
          },
          actions: [{
            actionGroupId: actionGroup.id
          }]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        criteria: typing.Union[typing.Union["StaticThresholdCriteria", typing.Dict[builtins.str, typing.Any]], typing.Union[DynamicThresholdCriteria, typing.Dict[builtins.str, typing.Any]]],
        scopes: typing.Sequence[builtins.str],
        severity: jsii.Number,
        actions: typing.Optional[typing.Sequence[typing.Union["MetricAlertAction", typing.Dict[builtins.str, typing.Any]]]] = None,
        auto_mitigate: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        enabled: typing.Optional[builtins.bool] = None,
        evaluation_frequency: typing.Optional[builtins.str] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        target_resource_region: typing.Optional[builtins.str] = None,
        target_resource_type: typing.Optional[builtins.str] = None,
        window_size: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Metric Alert using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param criteria: Alert criteria (static or dynamic threshold).
        :param scopes: Resource IDs that this alert is scoped to.
        :param severity: Alert severity (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose).
        :param actions: Action groups to notify.
        :param auto_mitigate: Auto-resolve alerts when condition is no longer met. Default: true
        :param description: Description of the alert rule.
        :param enabled: Whether the alert rule is enabled. Default: true
        :param evaluation_frequency: How often the alert is evaluated (ISO 8601 duration). Default: "PT5M"
        :param resource_group_id: Resource group ID where the metric alert will be created.
        :param target_resource_region: Region of the target resource (for multi-resource alerts).
        :param target_resource_type: Resource type of the target (for multi-resource alerts).
        :param window_size: Time window for aggregation (ISO 8601 duration). Default: "PT15M"
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
            type_hints = typing.get_type_hints(_typecheckingstub__89a31dd72d07a3fb3ea9f11c966fd677dff2f202fa495d954aa9d15a60a7539b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = MetricAlertProps(
            criteria=criteria,
            scopes=scopes,
            severity=severity,
            actions=actions,
            auto_mitigate=auto_mitigate,
            description=description,
            enabled=enabled,
            evaluation_frequency=evaluation_frequency,
            resource_group_id=resource_group_id,
            target_resource_region=target_resource_region,
            target_resource_type=target_resource_type,
            window_size=window_size,
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
        '''Add a tag to the Metric Alert Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4baa13a919d19f71908b259fb94eaa627541f705b3ec24d3afc64c4abd754030)
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
            type_hints = typing.get_type_hints(_typecheckingstub__06c23d9b423dd95ffb894b1d938b0be07ed40b984cb475bb26abacc3bf9b9b0b)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Metric Alert Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6bb42d384bcf97a52d4d7b85554be48ecee8e311da25098c86d67f130d04b06e)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Metric Alerts.'''
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
    def props(self) -> "MetricAlertProps":
        '''The input properties for this Metric Alert instance.'''
        return typing.cast("MetricAlertProps", jsii.get(self, "props"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricAlertAction",
    jsii_struct_bases=[],
    name_mapping={
        "action_group_id": "actionGroupId",
        "web_hook_properties": "webHookProperties",
    },
)
class MetricAlertAction:
    def __init__(
        self,
        *,
        action_group_id: builtins.str,
        web_hook_properties: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Metric alert action configuration.

        :param action_group_id: The action group resource ID.
        :param web_hook_properties: Webhook properties (optional).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f794defb3fa18238c8281a6371d0b04fb34ea4698521d9392bb1028ecad95c73)
            check_type(argname="argument action_group_id", value=action_group_id, expected_type=type_hints["action_group_id"])
            check_type(argname="argument web_hook_properties", value=web_hook_properties, expected_type=type_hints["web_hook_properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "action_group_id": action_group_id,
        }
        if web_hook_properties is not None:
            self._values["web_hook_properties"] = web_hook_properties

    @builtins.property
    def action_group_id(self) -> builtins.str:
        '''The action group resource ID.'''
        result = self._values.get("action_group_id")
        assert result is not None, "Required property 'action_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def web_hook_properties(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Webhook properties (optional).'''
        result = self._values.get("web_hook_properties")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetricAlertAction(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricAlertBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class MetricAlertBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["MetricAlertBodyProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Metric Alert API calls.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = MetricAlertBodyProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d9515a8b1fb707e45676cc528853e81d6fae82099aa3d55bc09c1f674ea889a3)
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
    def properties(self) -> "MetricAlertBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("MetricAlertBodyProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetricAlertBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricAlertBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "auto_mitigate": "autoMitigate",
        "criteria": "criteria",
        "enabled": "enabled",
        "evaluation_frequency": "evaluationFrequency",
        "scopes": "scopes",
        "severity": "severity",
        "window_size": "windowSize",
        "actions": "actions",
        "description": "description",
        "target_resource_region": "targetResourceRegion",
        "target_resource_type": "targetResourceType",
    },
)
class MetricAlertBodyProperties:
    def __init__(
        self,
        *,
        auto_mitigate: builtins.bool,
        criteria: typing.Any,
        enabled: builtins.bool,
        evaluation_frequency: builtins.str,
        scopes: typing.Sequence[builtins.str],
        severity: jsii.Number,
        window_size: builtins.str,
        actions: typing.Optional[typing.Sequence[typing.Union[MetricAlertAction, typing.Dict[builtins.str, typing.Any]]]] = None,
        description: typing.Optional[builtins.str] = None,
        target_resource_region: typing.Optional[builtins.str] = None,
        target_resource_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Metric Alert properties for the request body.

        :param auto_mitigate: 
        :param criteria: 
        :param enabled: 
        :param evaluation_frequency: 
        :param scopes: 
        :param severity: 
        :param window_size: 
        :param actions: 
        :param description: 
        :param target_resource_region: 
        :param target_resource_type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be39a78330e696f6adf61ec70611b58553c03d6690069f493935bb3eefbb69b6)
            check_type(argname="argument auto_mitigate", value=auto_mitigate, expected_type=type_hints["auto_mitigate"])
            check_type(argname="argument criteria", value=criteria, expected_type=type_hints["criteria"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument evaluation_frequency", value=evaluation_frequency, expected_type=type_hints["evaluation_frequency"])
            check_type(argname="argument scopes", value=scopes, expected_type=type_hints["scopes"])
            check_type(argname="argument severity", value=severity, expected_type=type_hints["severity"])
            check_type(argname="argument window_size", value=window_size, expected_type=type_hints["window_size"])
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument target_resource_region", value=target_resource_region, expected_type=type_hints["target_resource_region"])
            check_type(argname="argument target_resource_type", value=target_resource_type, expected_type=type_hints["target_resource_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "auto_mitigate": auto_mitigate,
            "criteria": criteria,
            "enabled": enabled,
            "evaluation_frequency": evaluation_frequency,
            "scopes": scopes,
            "severity": severity,
            "window_size": window_size,
        }
        if actions is not None:
            self._values["actions"] = actions
        if description is not None:
            self._values["description"] = description
        if target_resource_region is not None:
            self._values["target_resource_region"] = target_resource_region
        if target_resource_type is not None:
            self._values["target_resource_type"] = target_resource_type

    @builtins.property
    def auto_mitigate(self) -> builtins.bool:
        result = self._values.get("auto_mitigate")
        assert result is not None, "Required property 'auto_mitigate' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def criteria(self) -> typing.Any:
        result = self._values.get("criteria")
        assert result is not None, "Required property 'criteria' is missing"
        return typing.cast(typing.Any, result)

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def evaluation_frequency(self) -> builtins.str:
        result = self._values.get("evaluation_frequency")
        assert result is not None, "Required property 'evaluation_frequency' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scopes(self) -> typing.List[builtins.str]:
        result = self._values.get("scopes")
        assert result is not None, "Required property 'scopes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def severity(self) -> jsii.Number:
        result = self._values.get("severity")
        assert result is not None, "Required property 'severity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def window_size(self) -> builtins.str:
        result = self._values.get("window_size")
        assert result is not None, "Required property 'window_size' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def actions(self) -> typing.Optional[typing.List[MetricAlertAction]]:
        result = self._values.get("actions")
        return typing.cast(typing.Optional[typing.List[MetricAlertAction]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_resource_region(self) -> typing.Optional[builtins.str]:
        result = self._values.get("target_resource_region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_resource_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("target_resource_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetricAlertBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricAlertFailingPeriods",
    jsii_struct_bases=[],
    name_mapping={
        "min_failing_periods_to_alert": "minFailingPeriodsToAlert",
        "number_of_evaluation_periods": "numberOfEvaluationPeriods",
    },
)
class MetricAlertFailingPeriods:
    def __init__(
        self,
        *,
        min_failing_periods_to_alert: jsii.Number,
        number_of_evaluation_periods: jsii.Number,
    ) -> None:
        '''Metric alert failing periods configuration.

        :param min_failing_periods_to_alert: Minimum failing periods to trigger alert.
        :param number_of_evaluation_periods: Number of evaluation periods.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__94152fb09ac928d03362359231e76ac6f72db0edb842fe73cc778e7b5af3b4df)
            check_type(argname="argument min_failing_periods_to_alert", value=min_failing_periods_to_alert, expected_type=type_hints["min_failing_periods_to_alert"])
            check_type(argname="argument number_of_evaluation_periods", value=number_of_evaluation_periods, expected_type=type_hints["number_of_evaluation_periods"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "min_failing_periods_to_alert": min_failing_periods_to_alert,
            "number_of_evaluation_periods": number_of_evaluation_periods,
        }

    @builtins.property
    def min_failing_periods_to_alert(self) -> jsii.Number:
        '''Minimum failing periods to trigger alert.'''
        result = self._values.get("min_failing_periods_to_alert")
        assert result is not None, "Required property 'min_failing_periods_to_alert' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def number_of_evaluation_periods(self) -> jsii.Number:
        '''Number of evaluation periods.'''
        result = self._values.get("number_of_evaluation_periods")
        assert result is not None, "Required property 'number_of_evaluation_periods' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetricAlertFailingPeriods(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricAlertProps",
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
        "criteria": "criteria",
        "scopes": "scopes",
        "severity": "severity",
        "actions": "actions",
        "auto_mitigate": "autoMitigate",
        "description": "description",
        "enabled": "enabled",
        "evaluation_frequency": "evaluationFrequency",
        "resource_group_id": "resourceGroupId",
        "target_resource_region": "targetResourceRegion",
        "target_resource_type": "targetResourceType",
        "window_size": "windowSize",
    },
)
class MetricAlertProps(_AzapiResourceProps_141a2340):
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
        criteria: typing.Union[typing.Union["StaticThresholdCriteria", typing.Dict[builtins.str, typing.Any]], typing.Union[DynamicThresholdCriteria, typing.Dict[builtins.str, typing.Any]]],
        scopes: typing.Sequence[builtins.str],
        severity: jsii.Number,
        actions: typing.Optional[typing.Sequence[typing.Union[MetricAlertAction, typing.Dict[builtins.str, typing.Any]]]] = None,
        auto_mitigate: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        enabled: typing.Optional[builtins.bool] = None,
        evaluation_frequency: typing.Optional[builtins.str] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        target_resource_region: typing.Optional[builtins.str] = None,
        target_resource_type: typing.Optional[builtins.str] = None,
        window_size: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Metric Alert.

        Extends AzapiResourceProps with Metric Alert specific properties

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
        :param criteria: Alert criteria (static or dynamic threshold).
        :param scopes: Resource IDs that this alert is scoped to.
        :param severity: Alert severity (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose).
        :param actions: Action groups to notify.
        :param auto_mitigate: Auto-resolve alerts when condition is no longer met. Default: true
        :param description: Description of the alert rule.
        :param enabled: Whether the alert rule is enabled. Default: true
        :param evaluation_frequency: How often the alert is evaluated (ISO 8601 duration). Default: "PT5M"
        :param resource_group_id: Resource group ID where the metric alert will be created.
        :param target_resource_region: Region of the target resource (for multi-resource alerts).
        :param target_resource_type: Resource type of the target (for multi-resource alerts).
        :param window_size: Time window for aggregation (ISO 8601 duration). Default: "PT15M"
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40a00d331e2d75aa18a1d2ab404a55fad3004abfd33dad2f6a5d2428c188754c)
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
            check_type(argname="argument criteria", value=criteria, expected_type=type_hints["criteria"])
            check_type(argname="argument scopes", value=scopes, expected_type=type_hints["scopes"])
            check_type(argname="argument severity", value=severity, expected_type=type_hints["severity"])
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument auto_mitigate", value=auto_mitigate, expected_type=type_hints["auto_mitigate"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument evaluation_frequency", value=evaluation_frequency, expected_type=type_hints["evaluation_frequency"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument target_resource_region", value=target_resource_region, expected_type=type_hints["target_resource_region"])
            check_type(argname="argument target_resource_type", value=target_resource_type, expected_type=type_hints["target_resource_type"])
            check_type(argname="argument window_size", value=window_size, expected_type=type_hints["window_size"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "criteria": criteria,
            "scopes": scopes,
            "severity": severity,
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
        if actions is not None:
            self._values["actions"] = actions
        if auto_mitigate is not None:
            self._values["auto_mitigate"] = auto_mitigate
        if description is not None:
            self._values["description"] = description
        if enabled is not None:
            self._values["enabled"] = enabled
        if evaluation_frequency is not None:
            self._values["evaluation_frequency"] = evaluation_frequency
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if target_resource_region is not None:
            self._values["target_resource_region"] = target_resource_region
        if target_resource_type is not None:
            self._values["target_resource_type"] = target_resource_type
        if window_size is not None:
            self._values["window_size"] = window_size

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
    def criteria(
        self,
    ) -> typing.Union["StaticThresholdCriteria", DynamicThresholdCriteria]:
        '''Alert criteria (static or dynamic threshold).'''
        result = self._values.get("criteria")
        assert result is not None, "Required property 'criteria' is missing"
        return typing.cast(typing.Union["StaticThresholdCriteria", DynamicThresholdCriteria], result)

    @builtins.property
    def scopes(self) -> typing.List[builtins.str]:
        '''Resource IDs that this alert is scoped to.

        Example::

            ["/subscriptions/.../resourceGroups/.../providers/Microsoft.Compute/virtualMachines/myVM"]
        '''
        result = self._values.get("scopes")
        assert result is not None, "Required property 'scopes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def severity(self) -> jsii.Number:
        '''Alert severity (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose).

        Example::

            2
        '''
        result = self._values.get("severity")
        assert result is not None, "Required property 'severity' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def actions(self) -> typing.Optional[typing.List[MetricAlertAction]]:
        '''Action groups to notify.'''
        result = self._values.get("actions")
        return typing.cast(typing.Optional[typing.List[MetricAlertAction]], result)

    @builtins.property
    def auto_mitigate(self) -> typing.Optional[builtins.bool]:
        '''Auto-resolve alerts when condition is no longer met.

        :default: true
        '''
        result = self._values.get("auto_mitigate")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Description of the alert rule.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''Whether the alert rule is enabled.

        :default: true
        '''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def evaluation_frequency(self) -> typing.Optional[builtins.str]:
        '''How often the alert is evaluated (ISO 8601 duration).

        :default: "PT5M"

        Example::

            "PT1M", "PT5M", "PT15M"
        '''
        result = self._values.get("evaluation_frequency")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the metric alert will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_resource_region(self) -> typing.Optional[builtins.str]:
        '''Region of the target resource (for multi-resource alerts).

        Example::

            "eastus"
        '''
        result = self._values.get("target_resource_region")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def target_resource_type(self) -> typing.Optional[builtins.str]:
        '''Resource type of the target (for multi-resource alerts).

        Example::

            "Microsoft.Compute/virtualMachines"
        '''
        result = self._values.get("target_resource_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def window_size(self) -> typing.Optional[builtins.str]:
        '''Time window for aggregation (ISO 8601 duration).

        :default: "PT15M"

        Example::

            "PT5M", "PT15M", "PT30M", "PT1H"
        '''
        result = self._values.get("window_size")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetricAlertProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.MetricDimension",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "operator": "operator", "values": "values"},
)
class MetricDimension:
    def __init__(
        self,
        *,
        name: builtins.str,
        operator: builtins.str,
        values: typing.Sequence[builtins.str],
    ) -> None:
        '''Metric dimension for filtering.

        :param name: The dimension name.
        :param operator: The operator (Include or Exclude).
        :param values: The dimension values.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6b9653b46c13a829df2baec313d89558e8e2577584588c3c0abe250678e323cf)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument operator", value=operator, expected_type=type_hints["operator"])
            check_type(argname="argument values", value=values, expected_type=type_hints["values"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "operator": operator,
            "values": values,
        }

    @builtins.property
    def name(self) -> builtins.str:
        '''The dimension name.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def operator(self) -> builtins.str:
        '''The operator (Include or Exclude).'''
        result = self._values.get("operator")
        assert result is not None, "Required property 'operator' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def values(self) -> typing.List[builtins.str]:
        '''The dimension values.'''
        result = self._values.get("values")
        assert result is not None, "Required property 'values' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MetricDimension(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_metricalert.StaticThresholdCriteria",
    jsii_struct_bases=[],
    name_mapping={
        "metric_name": "metricName",
        "operator": "operator",
        "threshold": "threshold",
        "time_aggregation": "timeAggregation",
        "type": "type",
        "dimensions": "dimensions",
        "metric_namespace": "metricNamespace",
    },
)
class StaticThresholdCriteria:
    def __init__(
        self,
        *,
        metric_name: builtins.str,
        operator: builtins.str,
        threshold: jsii.Number,
        time_aggregation: builtins.str,
        type: builtins.str,
        dimensions: typing.Optional[typing.Sequence[typing.Union[MetricDimension, typing.Dict[builtins.str, typing.Any]]]] = None,
        metric_namespace: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Static threshold criteria configuration.

        :param metric_name: The metric name.
        :param operator: The comparison operator.
        :param threshold: The threshold value.
        :param time_aggregation: The time aggregation method.
        :param type: The criteria type.
        :param dimensions: Metric dimensions for filtering (optional).
        :param metric_namespace: The metric namespace (optional).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__497ccf89fdbc8a98dd79ec1c3ff4429822a0c179e74100253eb8d767972c641e)
            check_type(argname="argument metric_name", value=metric_name, expected_type=type_hints["metric_name"])
            check_type(argname="argument operator", value=operator, expected_type=type_hints["operator"])
            check_type(argname="argument threshold", value=threshold, expected_type=type_hints["threshold"])
            check_type(argname="argument time_aggregation", value=time_aggregation, expected_type=type_hints["time_aggregation"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument dimensions", value=dimensions, expected_type=type_hints["dimensions"])
            check_type(argname="argument metric_namespace", value=metric_namespace, expected_type=type_hints["metric_namespace"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "metric_name": metric_name,
            "operator": operator,
            "threshold": threshold,
            "time_aggregation": time_aggregation,
            "type": type,
        }
        if dimensions is not None:
            self._values["dimensions"] = dimensions
        if metric_namespace is not None:
            self._values["metric_namespace"] = metric_namespace

    @builtins.property
    def metric_name(self) -> builtins.str:
        '''The metric name.'''
        result = self._values.get("metric_name")
        assert result is not None, "Required property 'metric_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def operator(self) -> builtins.str:
        '''The comparison operator.'''
        result = self._values.get("operator")
        assert result is not None, "Required property 'operator' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def threshold(self) -> jsii.Number:
        '''The threshold value.'''
        result = self._values.get("threshold")
        assert result is not None, "Required property 'threshold' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def time_aggregation(self) -> builtins.str:
        '''The time aggregation method.'''
        result = self._values.get("time_aggregation")
        assert result is not None, "Required property 'time_aggregation' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''The criteria type.'''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def dimensions(self) -> typing.Optional[typing.List[MetricDimension]]:
        '''Metric dimensions for filtering (optional).'''
        result = self._values.get("dimensions")
        return typing.cast(typing.Optional[typing.List[MetricDimension]], result)

    @builtins.property
    def metric_namespace(self) -> typing.Optional[builtins.str]:
        '''The metric namespace (optional).'''
        result = self._values.get("metric_namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "StaticThresholdCriteria(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "DynamicThresholdCriteria",
    "MetricAlert",
    "MetricAlertAction",
    "MetricAlertBody",
    "MetricAlertBodyProperties",
    "MetricAlertFailingPeriods",
    "MetricAlertProps",
    "MetricDimension",
    "StaticThresholdCriteria",
]

publication.publish()

def _typecheckingstub__30c9b64719ac2d95b79fe194d09c972c132e3fc9ef357cf8a185eb391c1d1cdc(
    *,
    alert_sensitivity: builtins.str,
    failing_periods: typing.Union[MetricAlertFailingPeriods, typing.Dict[builtins.str, typing.Any]],
    metric_name: builtins.str,
    operator: builtins.str,
    time_aggregation: builtins.str,
    type: builtins.str,
    dimensions: typing.Optional[typing.Sequence[typing.Union[MetricDimension, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_data_before: typing.Optional[builtins.str] = None,
    metric_namespace: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__89a31dd72d07a3fb3ea9f11c966fd677dff2f202fa495d954aa9d15a60a7539b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    criteria: typing.Union[typing.Union[StaticThresholdCriteria, typing.Dict[builtins.str, typing.Any]], typing.Union[DynamicThresholdCriteria, typing.Dict[builtins.str, typing.Any]]],
    scopes: typing.Sequence[builtins.str],
    severity: jsii.Number,
    actions: typing.Optional[typing.Sequence[typing.Union[MetricAlertAction, typing.Dict[builtins.str, typing.Any]]]] = None,
    auto_mitigate: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    enabled: typing.Optional[builtins.bool] = None,
    evaluation_frequency: typing.Optional[builtins.str] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    target_resource_region: typing.Optional[builtins.str] = None,
    target_resource_type: typing.Optional[builtins.str] = None,
    window_size: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__4baa13a919d19f71908b259fb94eaa627541f705b3ec24d3afc64c4abd754030(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__06c23d9b423dd95ffb894b1d938b0be07ed40b984cb475bb26abacc3bf9b9b0b(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6bb42d384bcf97a52d4d7b85554be48ecee8e311da25098c86d67f130d04b06e(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f794defb3fa18238c8281a6371d0b04fb34ea4698521d9392bb1028ecad95c73(
    *,
    action_group_id: builtins.str,
    web_hook_properties: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d9515a8b1fb707e45676cc528853e81d6fae82099aa3d55bc09c1f674ea889a3(
    *,
    location: builtins.str,
    properties: typing.Union[MetricAlertBodyProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be39a78330e696f6adf61ec70611b58553c03d6690069f493935bb3eefbb69b6(
    *,
    auto_mitigate: builtins.bool,
    criteria: typing.Any,
    enabled: builtins.bool,
    evaluation_frequency: builtins.str,
    scopes: typing.Sequence[builtins.str],
    severity: jsii.Number,
    window_size: builtins.str,
    actions: typing.Optional[typing.Sequence[typing.Union[MetricAlertAction, typing.Dict[builtins.str, typing.Any]]]] = None,
    description: typing.Optional[builtins.str] = None,
    target_resource_region: typing.Optional[builtins.str] = None,
    target_resource_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94152fb09ac928d03362359231e76ac6f72db0edb842fe73cc778e7b5af3b4df(
    *,
    min_failing_periods_to_alert: jsii.Number,
    number_of_evaluation_periods: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40a00d331e2d75aa18a1d2ab404a55fad3004abfd33dad2f6a5d2428c188754c(
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
    criteria: typing.Union[typing.Union[StaticThresholdCriteria, typing.Dict[builtins.str, typing.Any]], typing.Union[DynamicThresholdCriteria, typing.Dict[builtins.str, typing.Any]]],
    scopes: typing.Sequence[builtins.str],
    severity: jsii.Number,
    actions: typing.Optional[typing.Sequence[typing.Union[MetricAlertAction, typing.Dict[builtins.str, typing.Any]]]] = None,
    auto_mitigate: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    enabled: typing.Optional[builtins.bool] = None,
    evaluation_frequency: typing.Optional[builtins.str] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    target_resource_region: typing.Optional[builtins.str] = None,
    target_resource_type: typing.Optional[builtins.str] = None,
    window_size: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6b9653b46c13a829df2baec313d89558e8e2577584588c3c0abe250678e323cf(
    *,
    name: builtins.str,
    operator: builtins.str,
    values: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__497ccf89fdbc8a98dd79ec1c3ff4429822a0c179e74100253eb8d767972c641e(
    *,
    metric_name: builtins.str,
    operator: builtins.str,
    threshold: jsii.Number,
    time_aggregation: builtins.str,
    type: builtins.str,
    dimensions: typing.Optional[typing.Sequence[typing.Union[MetricDimension, typing.Dict[builtins.str, typing.Any]]]] = None,
    metric_namespace: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
