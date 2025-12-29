r'''
# Azure Activity Log Alert Construct

This construct provides a type-safe, version-aware implementation of Azure Activity Log Alerts using the AZAPI provider framework.

## Overview

Activity Log Alerts monitor Azure Activity Log events and trigger notifications when specific operations occur, such as resource deletions, configuration changes, or service health events.

## Features

* **Version Management**: Automatic resolution to the latest stable API version (2020-10-01)
* **Type Safety**: Full TypeScript type definitions with JSII compliance
* **Comprehensive Filtering**: Filter by category, operation, resource type, status, and more
* **Service Health Alerts**: Monitor Azure service health events
* **Resource Health Alerts**: Monitor resource-specific health events
* **Validation**: Schema-driven property validation
* **Multi-language**: Generated bindings for TypeScript, Python, Java, and C#

## Installation

This construct is part of the `@microsoft/terraform-cdk-constructs` package.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Usage

### Alert on VM Deletion

```python
import { ActivityLogAlert } from "@microsoft/terraform-cdk-constructs/azure-activitylogalert";
import { ActionGroup } from "@microsoft/terraform-cdk-constructs/azure-actiongroup";

const vmDeletionAlert = new ActivityLogAlert(this, "vm-deletion", {
  name: "vm-deletion-alert",
  description: "Alert when any VM is deleted",
  resourceGroupId: resourceGroup.id,
  scopes: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  condition: {
    allOf: [
      { field: "category", equals: "Administrative" },
      { field: "operationName", equals: "Microsoft.Compute/virtualMachines/delete" },
      { field: "status", equals: "Succeeded" }
    ]
  },
  actions: {
    actionGroups: [{
      actionGroupId: actionGroup.id
    }]
  },
  tags: {
    Environment: "Production",
    AlertType: "Security"
  }
});
```

### Service Health Alert

```python
const serviceHealthAlert = new ActivityLogAlert(this, "service-health", {
  name: "service-health-alert",
  description: "Alert on Azure service health incidents",
  resourceGroupId: resourceGroup.id,
  scopes: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  condition: {
    allOf: [
      { field: "category", equals: "ServiceHealth" },
      { field: "properties.incidentType", equals: "Incident" }
    ]
  },
  actions: {
    actionGroups: [{
      actionGroupId: actionGroup.id,
      webhookProperties: {
        severity: "critical",
        environment: "production"
      }
    }]
  }
});
```

### Resource Health Alert

```python
const resourceHealthAlert = new ActivityLogAlert(this, "resource-health", {
  name: "resource-health-alert",
  description: "Alert on resource health degradation",
  resourceGroupId: resourceGroup.id,
  scopes: [resourceGroup.id],
  condition: {
    allOf: [
      { field: "category", equals: "ResourceHealth" },
      { field: "properties.currentHealthStatus", equals: "Degraded" },
      { field: "resourceType", equals: "Microsoft.Compute/virtualMachines" }
    ]
  },
  actions: {
    actionGroups: [{
      actionGroupId: actionGroup.id
    }]
  }
});
```

### Alert on Security Center Recommendations

```python
const securityAlert = new ActivityLogAlert(this, "security-alert", {
  name: "security-center-alert",
  description: "Alert on new Security Center recommendations",
  resourceGroupId: resourceGroup.id,
  scopes: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  condition: {
    allOf: [
      { field: "category", equals: "Security" },
      { field: "operationName", equals: "Microsoft.Security/locations/alerts/activate/action" }
    ]
  },
  actions: {
    actionGroups: [{
      actionGroupId: securityActionGroup.id
    }]
  }
});
```

### Alert on Policy Violations

```python
const policyAlert = new ActivityLogAlert(this, "policy-violation", {
  name: "policy-violation-alert",
  description: "Alert on Azure Policy violations",
  resourceGroupId: resourceGroup.id,
  scopes: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  condition: {
    allOf: [
      { field: "category", equals: "Policy" },
      { field: "operationName", equals: "Microsoft.Authorization/policies/audit/action" }
    ]
  },
  actions: {
    actionGroups: [{
      actionGroupId: actionGroup.id
    }]
  }
});
```

## Properties

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | The name of the activity log alert |
| `scopes` | `string[]` | Resource IDs that this alert is scoped to |
| `condition` | `ActivityLogAlertCondition` | Alert condition with field-value pairs |

### Optional Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `location` | `string` | Azure region | `"global"` |
| `description` | `string` | Description of the alert rule | - |
| `enabled` | `boolean` | Whether the alert rule is enabled | `true` |
| `actions` | `object` | Action groups to notify | - |
| `tags` | `Record<string, string>` | Resource tags | `{}` |
| `resourceGroupId` | `string` | Resource group ID | Required |
| `apiVersion` | `string` | Explicit API version | Latest |

## Condition Structure

### ActivityLogAlertCondition

```python
interface ActivityLogAlertCondition {
  allOf: ActivityLogAlertLeafCondition[];  // All conditions are ANDed
}

interface ActivityLogAlertLeafCondition {
  field: string;   // Field name to filter on
  equals: string;  // Value to match
}
```

## Common Fields

### Standard Fields

| Field | Description | Common Values |
|-------|-------------|---------------|
| `category` | Event category | Administrative, ServiceHealth, ResourceHealth, Alert, Policy, Security |
| `operationName` | Operation performed | Microsoft.Compute/virtualMachines/delete, etc. |
| `resourceType` | Type of resource | Microsoft.Compute/virtualMachines, etc. |
| `resourceGroup` | Resource group name | Name of the resource group |
| `status` | Operation status | Succeeded, Failed, Started |
| `subStatus` | Detailed status | Detailed status information |
| `resourceId` | Full resource ID | Complete Azure resource ID |

### ServiceHealth Fields

| Field | Description | Values |
|-------|-------------|--------|
| `properties.incidentType` | Type of incident | Incident, Maintenance, Information, ActionRequired |
| `properties.impactedServices[*].ServiceName` | Affected service | Virtual Machines, App Service, etc. |
| `properties.impactedServices[*].ImpactedRegions[*].RegionName` | Affected region | eastus, westus, etc. |

### ResourceHealth Fields

| Field | Description | Values |
|-------|-------------|--------|
| `properties.currentHealthStatus` | Current status | Available, Degraded, Unavailable |
| `properties.previousHealthStatus` | Previous status | Available, Degraded, Unavailable |
| `properties.cause` | Cause of change | PlatformInitiated, UserInitiated |

## Categories

### Administrative

Tracks create, update, delete, and action operations on resources.

```python
{ field: "category", equals: "Administrative" }
```

### ServiceHealth

Tracks Azure service health events including incidents and maintenance.

```python
{ field: "category", equals: "ServiceHealth" }
```

### ResourceHealth

Tracks health status changes of individual resources.

```python
{ field: "category", equals: "ResourceHealth" }
```

### Alert

Tracks firing of Azure Monitor alerts.

```python
{ field: "category", equals: "Alert" }
```

### Policy

Tracks Azure Policy evaluation results.

```python
{ field: "category", equals: "Policy" }
```

### Security

Tracks Azure Security Center alerts and recommendations.

```python
{ field: "category", equals: "Security" }
```

## Common Operation Names

### Virtual Machines

* `Microsoft.Compute/virtualMachines/write` - Create or update
* `Microsoft.Compute/virtualMachines/delete` - Delete
* `Microsoft.Compute/virtualMachines/start/action` - Start
* `Microsoft.Compute/virtualMachines/powerOff/action` - Power off
* `Microsoft.Compute/virtualMachines/restart/action` - Restart

### Storage Accounts

* `Microsoft.Storage/storageAccounts/write` - Create or update
* `Microsoft.Storage/storageAccounts/delete` - Delete
* `Microsoft.Storage/storageAccounts/regeneratekey/action` - Regenerate key

### Network Security Groups

* `Microsoft.Network/networkSecurityGroups/write` - Create or update
* `Microsoft.Network/networkSecurityGroups/delete` - Delete
* `Microsoft.Network/networkSecurityGroups/securityRules/write` - Update rules

## Scopes

Activity Log Alerts can be scoped to:

### Subscription Level

```python
scopes: ["/subscriptions/00000000-0000-0000-0000-000000000000"]
```

### Resource Group Level

```python
scopes: ["/subscriptions/.../resourceGroups/my-resource-group"]
```

### Specific Resource

```python
scopes: ["/subscriptions/.../resourceGroups/.../providers/Microsoft.Compute/virtualMachines/myVM"]
```

### Multiple Scopes

```python
scopes: [
  "/subscriptions/.../resourceGroups/rg1",
  "/subscriptions/.../resourceGroups/rg2"
]
```

## Best Practices

1. **Use Specific Scopes**: Limit alerts to relevant resources to reduce noise
2. **Add Descriptions**: Document what the alert monitors and expected actions
3. **Filter by Status**: Include `status` field to only alert on succeeded/failed operations
4. **Service Health**: Create dedicated alerts for service health events
5. **Security Monitoring**: Alert on critical security operations (deletions, key regeneration)
6. **Tag Alerts**: Use tags to organize and categorize alerts
7. **Test Actions**: Verify action groups receive notifications
8. **Review Regularly**: Analyze activity logs to identify new operations to monitor

## Outputs

The Activity Log Alert construct provides the following outputs:

* `id`: The resource ID of the activity log alert
* `name`: The name of the activity log alert

## API Versions

### Supported Versions

* **2020-10-01** (Active, Latest) - Stable API version with full feature support

## Examples

See the [examples directory](../../examples/) for complete working examples:

* Resource operation monitoring
* Service health alerting
* Resource health monitoring
* Security event alerting
* Policy compliance monitoring

## Related Constructs

* [`ActionGroup`](../azure-actiongroup/) - Notification hub
* [`MetricAlert`](../azure-metricalert/) - Metric-based alerting

## Resources

* [Activity Log Alerts Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/activity-log-alerts)
* [Activity Log Schema](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/activity-log-schema)
* [Service Health Alerts](https://learn.microsoft.com/en-us/azure/service-health/alerts-activity-log-service-notifications-portal)
* [REST API Reference](https://learn.microsoft.com/en-us/rest/api/monitor/activitylogalerts)
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


class ActivityLogAlert(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlert",
):
    '''Unified Azure Activity Log Alert implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    Activity Log Alerts monitor Azure Activity Log events and trigger notifications when specific
    operations occur, such as resource deletions, configuration changes, or service health events.

    Example::

        // Alert on service health events:
        const serviceHealthAlert = new ActivityLogAlert(this, "service-health", {
          name: "service-health-alert",
          description: "Alert on Azure service health events",
          resourceGroupId: resourceGroup.id,
          scopes: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
          condition: {
            allOf: [
              { field: "category", equalsValue: "ServiceHealth" },
              { field: "properties.incidentType", equalsValue: "Incident" }
            ]
          },
          actions: {
            actionGroups: [{
              actionGroupId: actionGroup.id,
              webhookProperties: {
                severity: "critical"
              }
            }]
          }
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        condition: typing.Union["ActivityLogAlertCondition", typing.Dict[builtins.str, typing.Any]],
        scopes: typing.Sequence[builtins.str],
        actions: typing.Optional[typing.Union["ActivityLogAlertActions", typing.Dict[builtins.str, typing.Any]]] = None,
        description: typing.Optional[builtins.str] = None,
        enabled: typing.Optional[builtins.bool] = None,
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
        '''Creates a new Azure Activity Log Alert using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param condition: Alert condition with field-value pairs All conditions are combined with AND logic.
        :param scopes: Resource IDs that this alert is scoped to Can be subscription, resource group, or specific resource IDs.
        :param actions: Action groups to notify.
        :param description: Description of the alert rule.
        :param enabled: Whether the alert rule is enabled. Default: true
        :param resource_group_id: Resource group ID where the activity log alert will be created.
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
            type_hints = typing.get_type_hints(_typecheckingstub__7b375c73e55c6850e0175054b9aceea6ee403b58c82478375e2e47c76863844b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ActivityLogAlertProps(
            condition=condition,
            scopes=scopes,
            actions=actions,
            description=description,
            enabled=enabled,
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
        '''Add a tag to the Activity Log Alert Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d80c813c83ce5b8a76f7144cb2c510832b6e7c3b9c1d743376cab09c8a6ca2f5)
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
            type_hints = typing.get_type_hints(_typecheckingstub__b64fe1ae56f375962ba3def89c84553abf28b3ea592d1a8e6ad8432db6d26364)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Activity Log Alert Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c0c7183cc9d5b35703070718c3d70a42589af5223c62afd38b883383cd17e4c7)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Activity Log Alerts.'''
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
    def props(self) -> "ActivityLogAlertProps":
        '''The input properties for this Activity Log Alert instance.'''
        return typing.cast("ActivityLogAlertProps", jsii.get(self, "props"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertActionGroup",
    jsii_struct_bases=[],
    name_mapping={
        "action_group_id": "actionGroupId",
        "webhook_properties": "webhookProperties",
    },
)
class ActivityLogAlertActionGroup:
    def __init__(
        self,
        *,
        action_group_id: builtins.str,
        webhook_properties: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Activity log alert action group reference.

        :param action_group_id: The action group resource ID.
        :param webhook_properties: Webhook properties (optional).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f2c8829c8e731d76e35cf5122d26cc4ab574af226cb8dfc848a4a8a7d881923c)
            check_type(argname="argument action_group_id", value=action_group_id, expected_type=type_hints["action_group_id"])
            check_type(argname="argument webhook_properties", value=webhook_properties, expected_type=type_hints["webhook_properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "action_group_id": action_group_id,
        }
        if webhook_properties is not None:
            self._values["webhook_properties"] = webhook_properties

    @builtins.property
    def action_group_id(self) -> builtins.str:
        '''The action group resource ID.'''
        result = self._values.get("action_group_id")
        assert result is not None, "Required property 'action_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def webhook_properties(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Webhook properties (optional).'''
        result = self._values.get("webhook_properties")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertActionGroup(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertActions",
    jsii_struct_bases=[],
    name_mapping={"action_groups": "actionGroups"},
)
class ActivityLogAlertActions:
    def __init__(
        self,
        *,
        action_groups: typing.Optional[typing.Sequence[typing.Union[ActivityLogAlertActionGroup, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Activity log alert actions configuration.

        :param action_groups: Action groups to trigger.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d326cd2bcee696f89477bc2c74e7f2a11771ef07788cc63f4766f85e867f729)
            check_type(argname="argument action_groups", value=action_groups, expected_type=type_hints["action_groups"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if action_groups is not None:
            self._values["action_groups"] = action_groups

    @builtins.property
    def action_groups(
        self,
    ) -> typing.Optional[typing.List[ActivityLogAlertActionGroup]]:
        '''Action groups to trigger.'''
        result = self._values.get("action_groups")
        return typing.cast(typing.Optional[typing.List[ActivityLogAlertActionGroup]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertActions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class ActivityLogAlertBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["ActivityLogAlertBodyProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Activity Log Alert API calls.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = ActivityLogAlertBodyProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__abce484a753089e8ab764ef4d19969b14bad1abf0247687c0467e386ad6623cd)
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
    def properties(self) -> "ActivityLogAlertBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("ActivityLogAlertBodyProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "condition": "condition",
        "enabled": "enabled",
        "scopes": "scopes",
        "actions": "actions",
        "description": "description",
    },
)
class ActivityLogAlertBodyProperties:
    def __init__(
        self,
        *,
        condition: typing.Union["ActivityLogAlertCondition", typing.Dict[builtins.str, typing.Any]],
        enabled: builtins.bool,
        scopes: typing.Sequence[builtins.str],
        actions: typing.Optional[typing.Union[ActivityLogAlertActions, typing.Dict[builtins.str, typing.Any]]] = None,
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Activity Log Alert properties for the request body.

        :param condition: 
        :param enabled: 
        :param scopes: 
        :param actions: 
        :param description: 
        '''
        if isinstance(condition, dict):
            condition = ActivityLogAlertCondition(**condition)
        if isinstance(actions, dict):
            actions = ActivityLogAlertActions(**actions)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__edac4fe6700c239e1a1d94491ded49c90cd1a22e07b74dc0618adc229eb3c9fb)
            check_type(argname="argument condition", value=condition, expected_type=type_hints["condition"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument scopes", value=scopes, expected_type=type_hints["scopes"])
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "condition": condition,
            "enabled": enabled,
            "scopes": scopes,
        }
        if actions is not None:
            self._values["actions"] = actions
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def condition(self) -> "ActivityLogAlertCondition":
        result = self._values.get("condition")
        assert result is not None, "Required property 'condition' is missing"
        return typing.cast("ActivityLogAlertCondition", result)

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def scopes(self) -> typing.List[builtins.str]:
        result = self._values.get("scopes")
        assert result is not None, "Required property 'scopes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def actions(self) -> typing.Optional[ActivityLogAlertActions]:
        result = self._values.get("actions")
        return typing.cast(typing.Optional[ActivityLogAlertActions], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertCondition",
    jsii_struct_bases=[],
    name_mapping={"all_of": "allOf"},
)
class ActivityLogAlertCondition:
    def __init__(
        self,
        *,
        all_of: typing.Sequence[typing.Union["ActivityLogAlertLeafCondition", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''Activity log alert condition.

        :param all_of: All conditions that must be met (AND logic).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f06a19f29b13c04b7cc8550a11ca26cc339d3f250f406777193222248b30e92d)
            check_type(argname="argument all_of", value=all_of, expected_type=type_hints["all_of"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "all_of": all_of,
        }

    @builtins.property
    def all_of(self) -> typing.List["ActivityLogAlertLeafCondition"]:
        '''All conditions that must be met (AND logic).'''
        result = self._values.get("all_of")
        assert result is not None, "Required property 'all_of' is missing"
        return typing.cast(typing.List["ActivityLogAlertLeafCondition"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertCondition(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertLeafCondition",
    jsii_struct_bases=[],
    name_mapping={"equals_value": "equalsValue", "field": "field"},
)
class ActivityLogAlertLeafCondition:
    def __init__(self, *, equals_value: builtins.str, field: builtins.str) -> None:
        '''Activity log alert leaf condition.

        :param equals_value: The value to match.
        :param field: The field name to filter on Common values: category, operationName, resourceType, status, subStatus, resourceGroup.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54a116c1ed6527ad84c8cfbd29615f1af3dbe9d14a3dd886dabbe05828564891)
            check_type(argname="argument equals_value", value=equals_value, expected_type=type_hints["equals_value"])
            check_type(argname="argument field", value=field, expected_type=type_hints["field"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "equals_value": equals_value,
            "field": field,
        }

    @builtins.property
    def equals_value(self) -> builtins.str:
        '''The value to match.'''
        result = self._values.get("equals_value")
        assert result is not None, "Required property 'equals_value' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def field(self) -> builtins.str:
        '''The field name to filter on Common values: category, operationName, resourceType, status, subStatus, resourceGroup.'''
        result = self._values.get("field")
        assert result is not None, "Required property 'field' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertLeafCondition(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_activitylogalert.ActivityLogAlertProps",
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
        "condition": "condition",
        "scopes": "scopes",
        "actions": "actions",
        "description": "description",
        "enabled": "enabled",
        "resource_group_id": "resourceGroupId",
    },
)
class ActivityLogAlertProps(_AzapiResourceProps_141a2340):
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
        condition: typing.Union[ActivityLogAlertCondition, typing.Dict[builtins.str, typing.Any]],
        scopes: typing.Sequence[builtins.str],
        actions: typing.Optional[typing.Union[ActivityLogAlertActions, typing.Dict[builtins.str, typing.Any]]] = None,
        description: typing.Optional[builtins.str] = None,
        enabled: typing.Optional[builtins.bool] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Activity Log Alert.

        Extends AzapiResourceProps with Activity Log Alert specific properties

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
        :param condition: Alert condition with field-value pairs All conditions are combined with AND logic.
        :param scopes: Resource IDs that this alert is scoped to Can be subscription, resource group, or specific resource IDs.
        :param actions: Action groups to notify.
        :param description: Description of the alert rule.
        :param enabled: Whether the alert rule is enabled. Default: true
        :param resource_group_id: Resource group ID where the activity log alert will be created.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(condition, dict):
            condition = ActivityLogAlertCondition(**condition)
        if isinstance(actions, dict):
            actions = ActivityLogAlertActions(**actions)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8b022fb338a52798b582b704361ebdf1612943d910514a3c74bd972f20cd8627)
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
            check_type(argname="argument condition", value=condition, expected_type=type_hints["condition"])
            check_type(argname="argument scopes", value=scopes, expected_type=type_hints["scopes"])
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "condition": condition,
            "scopes": scopes,
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
        if description is not None:
            self._values["description"] = description
        if enabled is not None:
            self._values["enabled"] = enabled
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
    def condition(self) -> ActivityLogAlertCondition:
        '''Alert condition with field-value pairs All conditions are combined with AND logic.'''
        result = self._values.get("condition")
        assert result is not None, "Required property 'condition' is missing"
        return typing.cast(ActivityLogAlertCondition, result)

    @builtins.property
    def scopes(self) -> typing.List[builtins.str]:
        '''Resource IDs that this alert is scoped to Can be subscription, resource group, or specific resource IDs.

        Example::

            ["/subscriptions/.../resourceGroups/my-rg"]
        '''
        result = self._values.get("scopes")
        assert result is not None, "Required property 'scopes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def actions(self) -> typing.Optional[ActivityLogAlertActions]:
        '''Action groups to notify.'''
        result = self._values.get("actions")
        return typing.cast(typing.Optional[ActivityLogAlertActions], result)

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
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the activity log alert will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActivityLogAlertProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ActivityLogAlert",
    "ActivityLogAlertActionGroup",
    "ActivityLogAlertActions",
    "ActivityLogAlertBody",
    "ActivityLogAlertBodyProperties",
    "ActivityLogAlertCondition",
    "ActivityLogAlertLeafCondition",
    "ActivityLogAlertProps",
]

publication.publish()

def _typecheckingstub__7b375c73e55c6850e0175054b9aceea6ee403b58c82478375e2e47c76863844b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    condition: typing.Union[ActivityLogAlertCondition, typing.Dict[builtins.str, typing.Any]],
    scopes: typing.Sequence[builtins.str],
    actions: typing.Optional[typing.Union[ActivityLogAlertActions, typing.Dict[builtins.str, typing.Any]]] = None,
    description: typing.Optional[builtins.str] = None,
    enabled: typing.Optional[builtins.bool] = None,
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

def _typecheckingstub__d80c813c83ce5b8a76f7144cb2c510832b6e7c3b9c1d743376cab09c8a6ca2f5(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b64fe1ae56f375962ba3def89c84553abf28b3ea592d1a8e6ad8432db6d26364(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c0c7183cc9d5b35703070718c3d70a42589af5223c62afd38b883383cd17e4c7(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f2c8829c8e731d76e35cf5122d26cc4ab574af226cb8dfc848a4a8a7d881923c(
    *,
    action_group_id: builtins.str,
    webhook_properties: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d326cd2bcee696f89477bc2c74e7f2a11771ef07788cc63f4766f85e867f729(
    *,
    action_groups: typing.Optional[typing.Sequence[typing.Union[ActivityLogAlertActionGroup, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__abce484a753089e8ab764ef4d19969b14bad1abf0247687c0467e386ad6623cd(
    *,
    location: builtins.str,
    properties: typing.Union[ActivityLogAlertBodyProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__edac4fe6700c239e1a1d94491ded49c90cd1a22e07b74dc0618adc229eb3c9fb(
    *,
    condition: typing.Union[ActivityLogAlertCondition, typing.Dict[builtins.str, typing.Any]],
    enabled: builtins.bool,
    scopes: typing.Sequence[builtins.str],
    actions: typing.Optional[typing.Union[ActivityLogAlertActions, typing.Dict[builtins.str, typing.Any]]] = None,
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f06a19f29b13c04b7cc8550a11ca26cc339d3f250f406777193222248b30e92d(
    *,
    all_of: typing.Sequence[typing.Union[ActivityLogAlertLeafCondition, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54a116c1ed6527ad84c8cfbd29615f1af3dbe9d14a3dd886dabbe05828564891(
    *,
    equals_value: builtins.str,
    field: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8b022fb338a52798b582b704361ebdf1612943d910514a3c74bd972f20cd8627(
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
    condition: typing.Union[ActivityLogAlertCondition, typing.Dict[builtins.str, typing.Any]],
    scopes: typing.Sequence[builtins.str],
    actions: typing.Optional[typing.Union[ActivityLogAlertActions, typing.Dict[builtins.str, typing.Any]]] = None,
    description: typing.Optional[builtins.str] = None,
    enabled: typing.Optional[builtins.bool] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
