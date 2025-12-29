r'''
# Azure Action Group Construct

This construct provides a type-safe, version-aware implementation of Azure Action Groups using the AZAPI provider framework.

## Overview

Action Groups serve as the central notification hub for Azure Monitor alerts. They support multiple receiver types including email, SMS, webhook, Azure Functions, Logic Apps, and voice calls.

## Features

* **Version Management**: Automatic resolution to the latest stable API version (2021-09-01)
* **Type Safety**: Full TypeScript type definitions with JSII compliance
* **Multiple Receivers**: Support for email, SMS, webhook, Azure Function, Logic App, and voice receivers
* **Validation**: Schema-driven property validation
* **Multi-language**: Generated bindings for TypeScript, Python, Java, and C#

## Installation

This construct is part of the `@microsoft/terraform-cdk-constructs` package.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Usage

### Basic Action Group with Email

```python
import { ActionGroup } from "@microsoft/terraform-cdk-constructs/azure-actiongroup";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";

const resourceGroup = new ResourceGroup(this, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

const actionGroup = new ActionGroup(this, "ops-team", {
  name: "ops-action-group",
  groupShortName: "OpsTeam",
  resourceGroupId: resourceGroup.id,
  emailReceivers: [{
    name: "ops-email",
    emailAddress: "ops@company.com",
    useCommonAlertSchema: true
  }],
});
```

### Action Group with Multiple Receiver Types

```python
const actionGroup = new ActionGroup(this, "critical-alerts", {
  name: "critical-action-group",
  groupShortName: "Critical",
  resourceGroupId: resourceGroup.id,
  emailReceivers: [{
    name: "oncall-email",
    emailAddress: "oncall@company.com",
    useCommonAlertSchema: true
  }],
  smsReceivers: [{
    name: "oncall-sms",
    countryCode: "1",
    phoneNumber: "5551234567"
  }],
  webhookReceivers: [{
    name: "pagerduty-webhook",
    serviceUri: "https://events.pagerduty.com/integration/...",
    useCommonAlertSchema: true
  }],
  tags: {
    Environment: "Production",
    Team: "Operations"
  }
});
```

### Action Group with Azure Function Receiver

```python
const actionGroup = new ActionGroup(this, "automation-alerts", {
  name: "automation-action-group",
  groupShortName: "Automation",
  resourceGroupId: resourceGroup.id,
  azureFunctionReceivers: [{
    name: "alert-processor",
    functionAppResourceId: "/subscriptions/.../resourceGroups/.../providers/Microsoft.Web/sites/my-function-app",
    functionName: "ProcessAlert",
    httpTriggerUrl: "https://my-function-app.azurewebsites.net/api/ProcessAlert",
    useCommonAlertSchema: true
  }],
});
```

### Action Group with Logic App Receiver

```python
const actionGroup = new ActionGroup(this, "workflow-alerts", {
  name: "workflow-action-group",
  groupShortName: "Workflow",
  resourceGroupId: resourceGroup.id,
  logicAppReceivers: [{
    name: "ticket-creation",
    resourceId: "/subscriptions/.../resourceGroups/.../providers/Microsoft.Logic/workflows/create-ticket",
    callbackUrl: "https://prod-00.eastus.logic.azure.com:443/workflows/.../triggers/manual/paths/invoke",
    useCommonAlertSchema: true
  }],
});
```

## Properties

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `string` | The name of the action group |
| `groupShortName` | `string` | Short name for SMS notifications (1-12 alphanumeric characters) |

### Optional Properties

| Property | Type | Description | Default |
|----------|------|-------------|---------|
| `location` | `string` | Azure region | `"global"` |
| `enabled` | `boolean` | Whether the action group is enabled | `true` |
| `emailReceivers` | `EmailReceiver[]` | Email notification receivers | `[]` |
| `smsReceivers` | `SmsReceiver[]` | SMS notification receivers | `[]` |
| `webhookReceivers` | `WebhookReceiver[]` | Webhook notification receivers | `[]` |
| `azureFunctionReceivers` | `AzureFunctionReceiver[]` | Azure Function receivers | `[]` |
| `logicAppReceivers` | `LogicAppReceiver[]` | Logic App receivers | `[]` |
| `voiceReceivers` | `VoiceReceiver[]` | Voice call receivers | `[]` |
| `tags` | `Record<string, string>` | Resource tags | `{}` |
| `resourceGroupId` | `string` | Resource group ID | Required for resource creation |
| `apiVersion` | `string` | Explicit API version | Latest version |

## Receiver Types

### EmailReceiver

```python
interface EmailReceiver {
  name: string;                    // Receiver name
  emailAddress: string;            // Email address
  useCommonAlertSchema?: boolean;  // Use common alert schema (default: false)
}
```

### SmsReceiver

```python
interface SmsReceiver {
  name: string;         // Receiver name
  countryCode: string;  // Country code (e.g., "1" for US)
  phoneNumber: string;  // Phone number
}
```

### WebhookReceiver

```python
interface WebhookReceiver {
  name: string;                    // Receiver name
  serviceUri: string;              // Webhook URL
  useCommonAlertSchema?: boolean;  // Use common alert schema (default: false)
}
```

### AzureFunctionReceiver

```python
interface AzureFunctionReceiver {
  name: string;                    // Receiver name
  functionAppResourceId: string;   // Function app resource ID
  functionName: string;            // Function name
  httpTriggerUrl: string;          // HTTP trigger URL
  useCommonAlertSchema?: boolean;  // Use common alert schema (default: false)
}
```

### LogicAppReceiver

```python
interface LogicAppReceiver {
  name: string;                    // Receiver name
  resourceId: string;              // Logic App resource ID
  callbackUrl: string;             // Callback URL
  useCommonAlertSchema?: boolean;  // Use common alert schema (default: false)
}
```

### VoiceReceiver

```python
interface VoiceReceiver {
  name: string;         // Receiver name
  countryCode: string;  // Country code (e.g., "1" for US)
  phoneNumber: string;  // Phone number
}
```

## Outputs

The Action Group construct provides the following outputs:

* `id`: The resource ID of the action group
* `name`: The name of the action group

You can reference these in other constructs:

```python
const alert = new MetricAlert(this, "cpu-alert", {
  // ... other properties
  actions: [{
    actionGroupId: actionGroup.id
  }]
});
```

## API Versions

### Supported Versions

* **2021-09-01** (Active, Latest) - Stable API version with full feature support

The construct automatically uses the latest stable version unless explicitly pinned:

```python
const actionGroup = new ActionGroup(this, "my-group", {
  name: "my-action-group",
  groupShortName: "MyGroup",
  apiVersion: "2021-09-01",  // Optional: pin to specific version
  // ... other properties
});
```

## Common Alert Schema

Microsoft recommends using the Common Alert Schema for better integration and consistency. Enable it per receiver:

```python
emailReceivers: [{
  name: "ops-email",
  emailAddress: "ops@company.com",
  useCommonAlertSchema: true  // Enable common alert schema
}]
```

Benefits of Common Alert Schema:

* Unified payload format across all alert types
* Easier to build integrations
* Better parsing and processing
* Consistent field names and structure

## Best Practices

1. **Use Short Names Wisely**: The `groupShortName` appears in SMS messages (max 12 characters)
2. **Enable Common Alert Schema**: Set `useCommonAlertSchema: true` for better integration
3. **Tag Your Resources**: Add meaningful tags for organization and cost tracking
4. **Multiple Receivers**: Configure multiple receiver types for redundancy
5. **Test Receivers**: Use the Azure Portal's "Test action group" feature after deployment

## Examples

See the [examples directory](../../examples/) for complete working examples:

* Basic action group setup
* Multi-receiver configurations
* Integration with metric alerts
* Integration with activity log alerts

## Related Constructs

* [`MetricAlert`](../azure-metricalert/) - Metric-based alerting
* [`ActivityLogAlert`](../azure-activitylogalert/) - Activity log alerting

## Resources

* [Azure Action Groups Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/action-groups)
* [Common Alert Schema](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-common-schema)
* [REST API Reference](https://learn.microsoft.com/en-us/rest/api/monitor/action-groups)
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


class ActionGroup(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.ActionGroup",
):
    '''Unified Azure Action Group implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    Action Groups serve as the central notification hub for Azure Monitor alerts, supporting
    multiple receiver types including email, SMS, webhook, Azure Functions, Logic Apps, and voice calls.

    Example::

        // Action group with multiple receiver types:
        const actionGroup = new ActionGroup(this, "critical-alerts", {
          name: "critical-action-group",
          groupShortName: "Critical",
          resourceGroupId: resourceGroup.id,
          emailReceivers: [{
            name: "oncall-email",
            emailAddress: "oncall@company.com",
            useCommonAlertSchema: true
          }],
          smsReceivers: [{
            name: "oncall-sms",
            countryCode: "1",
            phoneNumber: "5551234567"
          }],
          webhookReceivers: [{
            name: "pagerduty-webhook",
            serviceUri: "https://events.pagerduty.com/...",
            useCommonAlertSchema: true
          }]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        group_short_name: builtins.str,
        azure_function_receivers: typing.Optional[typing.Sequence[typing.Union["AzureFunctionReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        email_receivers: typing.Optional[typing.Sequence[typing.Union["EmailReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        enabled: typing.Optional[builtins.bool] = None,
        logic_app_receivers: typing.Optional[typing.Sequence[typing.Union["LogicAppReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        sms_receivers: typing.Optional[typing.Sequence[typing.Union["SmsReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        voice_receivers: typing.Optional[typing.Sequence[typing.Union["VoiceReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        webhook_receivers: typing.Optional[typing.Sequence[typing.Union["WebhookReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
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
        '''Creates a new Azure Action Group using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param group_short_name: Short name for SMS notifications (max 12 chars).
        :param azure_function_receivers: Azure Function receivers.
        :param email_receivers: Email notification receivers.
        :param enabled: Whether the action group is enabled. Default: true
        :param logic_app_receivers: Logic App receivers.
        :param resource_group_id: Resource group ID where the action group will be created.
        :param sms_receivers: SMS notification receivers.
        :param voice_receivers: Voice call receivers.
        :param webhook_receivers: Webhook notification receivers.
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
            type_hints = typing.get_type_hints(_typecheckingstub__77e0be16fb4436d24a807dbea7e95be557b3841313e781361bc103ff4d6bb7f1)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ActionGroupProps(
            group_short_name=group_short_name,
            azure_function_receivers=azure_function_receivers,
            email_receivers=email_receivers,
            enabled=enabled,
            logic_app_receivers=logic_app_receivers,
            resource_group_id=resource_group_id,
            sms_receivers=sms_receivers,
            voice_receivers=voice_receivers,
            webhook_receivers=webhook_receivers,
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
        '''Add a tag to the Action Group Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9d52220d812d3bcba5f644a1dd032eec5bb55cd56b36c715741288540d84e24a)
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
            type_hints = typing.get_type_hints(_typecheckingstub__56a260e49d7166e3d33a2b7c91c0356397651d4a4f33c5d69ed824acdef2ab68)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Action Group Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ba74edbe9c752c0fdf4145262393c096eced6991ea1467e68d6f4b1cd1e9607e)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Action Groups.'''
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
    def props(self) -> "ActionGroupProps":
        '''The input properties for this Action Group instance.'''
        return typing.cast("ActionGroupProps", jsii.get(self, "props"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.ActionGroupBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class ActionGroupBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["ActionGroupBodyProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Action Group API calls.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = ActionGroupBodyProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__03326d27efcbc0f8fd9e49674e9bdfc6aad76a380f35d50da8948481a7ce5a1c)
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
    def properties(self) -> "ActionGroupBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("ActionGroupBodyProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActionGroupBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.ActionGroupBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "enabled": "enabled",
        "group_short_name": "groupShortName",
        "azure_function_receivers": "azureFunctionReceivers",
        "email_receivers": "emailReceivers",
        "logic_app_receivers": "logicAppReceivers",
        "sms_receivers": "smsReceivers",
        "voice_receivers": "voiceReceivers",
        "webhook_receivers": "webhookReceivers",
    },
)
class ActionGroupBodyProperties:
    def __init__(
        self,
        *,
        enabled: builtins.bool,
        group_short_name: builtins.str,
        azure_function_receivers: typing.Optional[typing.Sequence[typing.Union["AzureFunctionReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        email_receivers: typing.Optional[typing.Sequence[typing.Union["EmailReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        logic_app_receivers: typing.Optional[typing.Sequence[typing.Union["LogicAppReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        sms_receivers: typing.Optional[typing.Sequence[typing.Union["SmsReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        voice_receivers: typing.Optional[typing.Sequence[typing.Union["VoiceReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        webhook_receivers: typing.Optional[typing.Sequence[typing.Union["WebhookReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Action Group properties for the request body.

        :param enabled: 
        :param group_short_name: 
        :param azure_function_receivers: 
        :param email_receivers: 
        :param logic_app_receivers: 
        :param sms_receivers: 
        :param voice_receivers: 
        :param webhook_receivers: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e79d4dfceb7a78007a3441cf692df43c0db4047830d66e87b0a1292ec531fecc)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument group_short_name", value=group_short_name, expected_type=type_hints["group_short_name"])
            check_type(argname="argument azure_function_receivers", value=azure_function_receivers, expected_type=type_hints["azure_function_receivers"])
            check_type(argname="argument email_receivers", value=email_receivers, expected_type=type_hints["email_receivers"])
            check_type(argname="argument logic_app_receivers", value=logic_app_receivers, expected_type=type_hints["logic_app_receivers"])
            check_type(argname="argument sms_receivers", value=sms_receivers, expected_type=type_hints["sms_receivers"])
            check_type(argname="argument voice_receivers", value=voice_receivers, expected_type=type_hints["voice_receivers"])
            check_type(argname="argument webhook_receivers", value=webhook_receivers, expected_type=type_hints["webhook_receivers"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "enabled": enabled,
            "group_short_name": group_short_name,
        }
        if azure_function_receivers is not None:
            self._values["azure_function_receivers"] = azure_function_receivers
        if email_receivers is not None:
            self._values["email_receivers"] = email_receivers
        if logic_app_receivers is not None:
            self._values["logic_app_receivers"] = logic_app_receivers
        if sms_receivers is not None:
            self._values["sms_receivers"] = sms_receivers
        if voice_receivers is not None:
            self._values["voice_receivers"] = voice_receivers
        if webhook_receivers is not None:
            self._values["webhook_receivers"] = webhook_receivers

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def group_short_name(self) -> builtins.str:
        result = self._values.get("group_short_name")
        assert result is not None, "Required property 'group_short_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def azure_function_receivers(
        self,
    ) -> typing.Optional[typing.List["AzureFunctionReceiver"]]:
        result = self._values.get("azure_function_receivers")
        return typing.cast(typing.Optional[typing.List["AzureFunctionReceiver"]], result)

    @builtins.property
    def email_receivers(self) -> typing.Optional[typing.List["EmailReceiver"]]:
        result = self._values.get("email_receivers")
        return typing.cast(typing.Optional[typing.List["EmailReceiver"]], result)

    @builtins.property
    def logic_app_receivers(self) -> typing.Optional[typing.List["LogicAppReceiver"]]:
        result = self._values.get("logic_app_receivers")
        return typing.cast(typing.Optional[typing.List["LogicAppReceiver"]], result)

    @builtins.property
    def sms_receivers(self) -> typing.Optional[typing.List["SmsReceiver"]]:
        result = self._values.get("sms_receivers")
        return typing.cast(typing.Optional[typing.List["SmsReceiver"]], result)

    @builtins.property
    def voice_receivers(self) -> typing.Optional[typing.List["VoiceReceiver"]]:
        result = self._values.get("voice_receivers")
        return typing.cast(typing.Optional[typing.List["VoiceReceiver"]], result)

    @builtins.property
    def webhook_receivers(self) -> typing.Optional[typing.List["WebhookReceiver"]]:
        result = self._values.get("webhook_receivers")
        return typing.cast(typing.Optional[typing.List["WebhookReceiver"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActionGroupBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.ActionGroupProps",
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
        "group_short_name": "groupShortName",
        "azure_function_receivers": "azureFunctionReceivers",
        "email_receivers": "emailReceivers",
        "enabled": "enabled",
        "logic_app_receivers": "logicAppReceivers",
        "resource_group_id": "resourceGroupId",
        "sms_receivers": "smsReceivers",
        "voice_receivers": "voiceReceivers",
        "webhook_receivers": "webhookReceivers",
    },
)
class ActionGroupProps(_AzapiResourceProps_141a2340):
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
        group_short_name: builtins.str,
        azure_function_receivers: typing.Optional[typing.Sequence[typing.Union["AzureFunctionReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        email_receivers: typing.Optional[typing.Sequence[typing.Union["EmailReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        enabled: typing.Optional[builtins.bool] = None,
        logic_app_receivers: typing.Optional[typing.Sequence[typing.Union["LogicAppReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        sms_receivers: typing.Optional[typing.Sequence[typing.Union["SmsReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        voice_receivers: typing.Optional[typing.Sequence[typing.Union["VoiceReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
        webhook_receivers: typing.Optional[typing.Sequence[typing.Union["WebhookReceiver", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Properties for the unified Azure Action Group.

        Extends AzapiResourceProps with Action Group specific properties

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
        :param group_short_name: Short name for SMS notifications (max 12 chars).
        :param azure_function_receivers: Azure Function receivers.
        :param email_receivers: Email notification receivers.
        :param enabled: Whether the action group is enabled. Default: true
        :param logic_app_receivers: Logic App receivers.
        :param resource_group_id: Resource group ID where the action group will be created.
        :param sms_receivers: SMS notification receivers.
        :param voice_receivers: Voice call receivers.
        :param webhook_receivers: Webhook notification receivers.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0467174df5ade5e1552d6c59375e8720b8d1046a8ebb8bf72c1f11538d48cad5)
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
            check_type(argname="argument group_short_name", value=group_short_name, expected_type=type_hints["group_short_name"])
            check_type(argname="argument azure_function_receivers", value=azure_function_receivers, expected_type=type_hints["azure_function_receivers"])
            check_type(argname="argument email_receivers", value=email_receivers, expected_type=type_hints["email_receivers"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument logic_app_receivers", value=logic_app_receivers, expected_type=type_hints["logic_app_receivers"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument sms_receivers", value=sms_receivers, expected_type=type_hints["sms_receivers"])
            check_type(argname="argument voice_receivers", value=voice_receivers, expected_type=type_hints["voice_receivers"])
            check_type(argname="argument webhook_receivers", value=webhook_receivers, expected_type=type_hints["webhook_receivers"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "group_short_name": group_short_name,
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
        if azure_function_receivers is not None:
            self._values["azure_function_receivers"] = azure_function_receivers
        if email_receivers is not None:
            self._values["email_receivers"] = email_receivers
        if enabled is not None:
            self._values["enabled"] = enabled
        if logic_app_receivers is not None:
            self._values["logic_app_receivers"] = logic_app_receivers
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if sms_receivers is not None:
            self._values["sms_receivers"] = sms_receivers
        if voice_receivers is not None:
            self._values["voice_receivers"] = voice_receivers
        if webhook_receivers is not None:
            self._values["webhook_receivers"] = webhook_receivers

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
    def group_short_name(self) -> builtins.str:
        '''Short name for SMS notifications (max 12 chars).

        Example::

            "OpsTeam"
        '''
        result = self._values.get("group_short_name")
        assert result is not None, "Required property 'group_short_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def azure_function_receivers(
        self,
    ) -> typing.Optional[typing.List["AzureFunctionReceiver"]]:
        '''Azure Function receivers.'''
        result = self._values.get("azure_function_receivers")
        return typing.cast(typing.Optional[typing.List["AzureFunctionReceiver"]], result)

    @builtins.property
    def email_receivers(self) -> typing.Optional[typing.List["EmailReceiver"]]:
        '''Email notification receivers.'''
        result = self._values.get("email_receivers")
        return typing.cast(typing.Optional[typing.List["EmailReceiver"]], result)

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''Whether the action group is enabled.

        :default: true
        '''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def logic_app_receivers(self) -> typing.Optional[typing.List["LogicAppReceiver"]]:
        '''Logic App receivers.'''
        result = self._values.get("logic_app_receivers")
        return typing.cast(typing.Optional[typing.List["LogicAppReceiver"]], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the action group will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sms_receivers(self) -> typing.Optional[typing.List["SmsReceiver"]]:
        '''SMS notification receivers.'''
        result = self._values.get("sms_receivers")
        return typing.cast(typing.Optional[typing.List["SmsReceiver"]], result)

    @builtins.property
    def voice_receivers(self) -> typing.Optional[typing.List["VoiceReceiver"]]:
        '''Voice call receivers.'''
        result = self._values.get("voice_receivers")
        return typing.cast(typing.Optional[typing.List["VoiceReceiver"]], result)

    @builtins.property
    def webhook_receivers(self) -> typing.Optional[typing.List["WebhookReceiver"]]:
        '''Webhook notification receivers.'''
        result = self._values.get("webhook_receivers")
        return typing.cast(typing.Optional[typing.List["WebhookReceiver"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ActionGroupProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.AzureFunctionReceiver",
    jsii_struct_bases=[],
    name_mapping={
        "function_app_resource_id": "functionAppResourceId",
        "function_name": "functionName",
        "http_trigger_url": "httpTriggerUrl",
        "name": "name",
        "use_common_alert_schema": "useCommonAlertSchema",
    },
)
class AzureFunctionReceiver:
    def __init__(
        self,
        *,
        function_app_resource_id: builtins.str,
        function_name: builtins.str,
        http_trigger_url: builtins.str,
        name: builtins.str,
        use_common_alert_schema: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Azure Function receiver configuration.

        :param function_app_resource_id: The function app resource ID.
        :param function_name: The function name.
        :param http_trigger_url: The HTTP trigger URL.
        :param name: The name of the Azure Function receiver.
        :param use_common_alert_schema: Whether to use common alert schema. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5718c3b9086c91438dcf7f0e9f28cf284cbec386d1727c2a77890f019b8f75e1)
            check_type(argname="argument function_app_resource_id", value=function_app_resource_id, expected_type=type_hints["function_app_resource_id"])
            check_type(argname="argument function_name", value=function_name, expected_type=type_hints["function_name"])
            check_type(argname="argument http_trigger_url", value=http_trigger_url, expected_type=type_hints["http_trigger_url"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument use_common_alert_schema", value=use_common_alert_schema, expected_type=type_hints["use_common_alert_schema"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "function_app_resource_id": function_app_resource_id,
            "function_name": function_name,
            "http_trigger_url": http_trigger_url,
            "name": name,
        }
        if use_common_alert_schema is not None:
            self._values["use_common_alert_schema"] = use_common_alert_schema

    @builtins.property
    def function_app_resource_id(self) -> builtins.str:
        '''The function app resource ID.'''
        result = self._values.get("function_app_resource_id")
        assert result is not None, "Required property 'function_app_resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def function_name(self) -> builtins.str:
        '''The function name.'''
        result = self._values.get("function_name")
        assert result is not None, "Required property 'function_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def http_trigger_url(self) -> builtins.str:
        '''The HTTP trigger URL.'''
        result = self._values.get("http_trigger_url")
        assert result is not None, "Required property 'http_trigger_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the Azure Function receiver.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def use_common_alert_schema(self) -> typing.Optional[builtins.bool]:
        '''Whether to use common alert schema.

        :default: false
        '''
        result = self._values.get("use_common_alert_schema")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AzureFunctionReceiver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.EmailReceiver",
    jsii_struct_bases=[],
    name_mapping={
        "email_address": "emailAddress",
        "name": "name",
        "use_common_alert_schema": "useCommonAlertSchema",
    },
)
class EmailReceiver:
    def __init__(
        self,
        *,
        email_address: builtins.str,
        name: builtins.str,
        use_common_alert_schema: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Email receiver configuration.

        :param email_address: The email address to send notifications to.
        :param name: The name of the email receiver.
        :param use_common_alert_schema: Whether to use common alert schema. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a83a2e1e28589dc50509a1e840effc93d5f659df0d90b1e3916884797e5ad8ee)
            check_type(argname="argument email_address", value=email_address, expected_type=type_hints["email_address"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument use_common_alert_schema", value=use_common_alert_schema, expected_type=type_hints["use_common_alert_schema"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "email_address": email_address,
            "name": name,
        }
        if use_common_alert_schema is not None:
            self._values["use_common_alert_schema"] = use_common_alert_schema

    @builtins.property
    def email_address(self) -> builtins.str:
        '''The email address to send notifications to.'''
        result = self._values.get("email_address")
        assert result is not None, "Required property 'email_address' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the email receiver.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def use_common_alert_schema(self) -> typing.Optional[builtins.bool]:
        '''Whether to use common alert schema.

        :default: false
        '''
        result = self._values.get("use_common_alert_schema")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EmailReceiver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.LogicAppReceiver",
    jsii_struct_bases=[],
    name_mapping={
        "callback_url": "callbackUrl",
        "name": "name",
        "resource_id": "resourceId",
        "use_common_alert_schema": "useCommonAlertSchema",
    },
)
class LogicAppReceiver:
    def __init__(
        self,
        *,
        callback_url: builtins.str,
        name: builtins.str,
        resource_id: builtins.str,
        use_common_alert_schema: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Logic App receiver configuration.

        :param callback_url: The callback URL.
        :param name: The name of the Logic App receiver.
        :param resource_id: The Logic App resource ID.
        :param use_common_alert_schema: Whether to use common alert schema. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f058926a135d11439a34a6657be70d37ffecc68928ff2a521ba2c71b4d74336)
            check_type(argname="argument callback_url", value=callback_url, expected_type=type_hints["callback_url"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument use_common_alert_schema", value=use_common_alert_schema, expected_type=type_hints["use_common_alert_schema"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "callback_url": callback_url,
            "name": name,
            "resource_id": resource_id,
        }
        if use_common_alert_schema is not None:
            self._values["use_common_alert_schema"] = use_common_alert_schema

    @builtins.property
    def callback_url(self) -> builtins.str:
        '''The callback URL.'''
        result = self._values.get("callback_url")
        assert result is not None, "Required property 'callback_url' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the Logic App receiver.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''The Logic App resource ID.'''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def use_common_alert_schema(self) -> typing.Optional[builtins.bool]:
        '''Whether to use common alert schema.

        :default: false
        '''
        result = self._values.get("use_common_alert_schema")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LogicAppReceiver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.SmsReceiver",
    jsii_struct_bases=[],
    name_mapping={
        "country_code": "countryCode",
        "name": "name",
        "phone_number": "phoneNumber",
    },
)
class SmsReceiver:
    def __init__(
        self,
        *,
        country_code: builtins.str,
        name: builtins.str,
        phone_number: builtins.str,
    ) -> None:
        '''SMS receiver configuration.

        :param country_code: The country code (e.g., "1" for US).
        :param name: The name of the SMS receiver.
        :param phone_number: The phone number to send SMS to.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad253453a305e7e5342f4ecb57198c2a5d88f06046b6b1e0ce11eaf642b40503)
            check_type(argname="argument country_code", value=country_code, expected_type=type_hints["country_code"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument phone_number", value=phone_number, expected_type=type_hints["phone_number"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "country_code": country_code,
            "name": name,
            "phone_number": phone_number,
        }

    @builtins.property
    def country_code(self) -> builtins.str:
        '''The country code (e.g., "1" for US).'''
        result = self._values.get("country_code")
        assert result is not None, "Required property 'country_code' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the SMS receiver.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def phone_number(self) -> builtins.str:
        '''The phone number to send SMS to.'''
        result = self._values.get("phone_number")
        assert result is not None, "Required property 'phone_number' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SmsReceiver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.VoiceReceiver",
    jsii_struct_bases=[],
    name_mapping={
        "country_code": "countryCode",
        "name": "name",
        "phone_number": "phoneNumber",
    },
)
class VoiceReceiver:
    def __init__(
        self,
        *,
        country_code: builtins.str,
        name: builtins.str,
        phone_number: builtins.str,
    ) -> None:
        '''Voice receiver configuration.

        :param country_code: The country code (e.g., "1" for US).
        :param name: The name of the voice receiver.
        :param phone_number: The phone number to call.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d2c513d1203f49b53ed7b54b11c22a12d11e9209884872ecebdb95d0271a76ec)
            check_type(argname="argument country_code", value=country_code, expected_type=type_hints["country_code"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument phone_number", value=phone_number, expected_type=type_hints["phone_number"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "country_code": country_code,
            "name": name,
            "phone_number": phone_number,
        }

    @builtins.property
    def country_code(self) -> builtins.str:
        '''The country code (e.g., "1" for US).'''
        result = self._values.get("country_code")
        assert result is not None, "Required property 'country_code' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the voice receiver.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def phone_number(self) -> builtins.str:
        '''The phone number to call.'''
        result = self._values.get("phone_number")
        assert result is not None, "Required property 'phone_number' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VoiceReceiver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_actiongroup.WebhookReceiver",
    jsii_struct_bases=[],
    name_mapping={
        "name": "name",
        "service_uri": "serviceUri",
        "use_common_alert_schema": "useCommonAlertSchema",
    },
)
class WebhookReceiver:
    def __init__(
        self,
        *,
        name: builtins.str,
        service_uri: builtins.str,
        use_common_alert_schema: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Webhook receiver configuration.

        :param name: The name of the webhook receiver.
        :param service_uri: The service URI to send webhooks to.
        :param use_common_alert_schema: Whether to use common alert schema. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__33b8e07750a30d4620204607eb08493d7a595c4ca865f62b77b7fb3b2ba8521f)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument service_uri", value=service_uri, expected_type=type_hints["service_uri"])
            check_type(argname="argument use_common_alert_schema", value=use_common_alert_schema, expected_type=type_hints["use_common_alert_schema"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "service_uri": service_uri,
        }
        if use_common_alert_schema is not None:
            self._values["use_common_alert_schema"] = use_common_alert_schema

    @builtins.property
    def name(self) -> builtins.str:
        '''The name of the webhook receiver.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def service_uri(self) -> builtins.str:
        '''The service URI to send webhooks to.'''
        result = self._values.get("service_uri")
        assert result is not None, "Required property 'service_uri' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def use_common_alert_schema(self) -> typing.Optional[builtins.bool]:
        '''Whether to use common alert schema.

        :default: false
        '''
        result = self._values.get("use_common_alert_schema")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "WebhookReceiver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ActionGroup",
    "ActionGroupBody",
    "ActionGroupBodyProperties",
    "ActionGroupProps",
    "AzureFunctionReceiver",
    "EmailReceiver",
    "LogicAppReceiver",
    "SmsReceiver",
    "VoiceReceiver",
    "WebhookReceiver",
]

publication.publish()

def _typecheckingstub__77e0be16fb4436d24a807dbea7e95be557b3841313e781361bc103ff4d6bb7f1(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    group_short_name: builtins.str,
    azure_function_receivers: typing.Optional[typing.Sequence[typing.Union[AzureFunctionReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    email_receivers: typing.Optional[typing.Sequence[typing.Union[EmailReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    enabled: typing.Optional[builtins.bool] = None,
    logic_app_receivers: typing.Optional[typing.Sequence[typing.Union[LogicAppReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    sms_receivers: typing.Optional[typing.Sequence[typing.Union[SmsReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    voice_receivers: typing.Optional[typing.Sequence[typing.Union[VoiceReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    webhook_receivers: typing.Optional[typing.Sequence[typing.Union[WebhookReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
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

def _typecheckingstub__9d52220d812d3bcba5f644a1dd032eec5bb55cd56b36c715741288540d84e24a(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56a260e49d7166e3d33a2b7c91c0356397651d4a4f33c5d69ed824acdef2ab68(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ba74edbe9c752c0fdf4145262393c096eced6991ea1467e68d6f4b1cd1e9607e(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__03326d27efcbc0f8fd9e49674e9bdfc6aad76a380f35d50da8948481a7ce5a1c(
    *,
    location: builtins.str,
    properties: typing.Union[ActionGroupBodyProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e79d4dfceb7a78007a3441cf692df43c0db4047830d66e87b0a1292ec531fecc(
    *,
    enabled: builtins.bool,
    group_short_name: builtins.str,
    azure_function_receivers: typing.Optional[typing.Sequence[typing.Union[AzureFunctionReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    email_receivers: typing.Optional[typing.Sequence[typing.Union[EmailReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    logic_app_receivers: typing.Optional[typing.Sequence[typing.Union[LogicAppReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    sms_receivers: typing.Optional[typing.Sequence[typing.Union[SmsReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    voice_receivers: typing.Optional[typing.Sequence[typing.Union[VoiceReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    webhook_receivers: typing.Optional[typing.Sequence[typing.Union[WebhookReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0467174df5ade5e1552d6c59375e8720b8d1046a8ebb8bf72c1f11538d48cad5(
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
    group_short_name: builtins.str,
    azure_function_receivers: typing.Optional[typing.Sequence[typing.Union[AzureFunctionReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    email_receivers: typing.Optional[typing.Sequence[typing.Union[EmailReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    enabled: typing.Optional[builtins.bool] = None,
    logic_app_receivers: typing.Optional[typing.Sequence[typing.Union[LogicAppReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    sms_receivers: typing.Optional[typing.Sequence[typing.Union[SmsReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    voice_receivers: typing.Optional[typing.Sequence[typing.Union[VoiceReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
    webhook_receivers: typing.Optional[typing.Sequence[typing.Union[WebhookReceiver, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5718c3b9086c91438dcf7f0e9f28cf284cbec386d1727c2a77890f019b8f75e1(
    *,
    function_app_resource_id: builtins.str,
    function_name: builtins.str,
    http_trigger_url: builtins.str,
    name: builtins.str,
    use_common_alert_schema: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a83a2e1e28589dc50509a1e840effc93d5f659df0d90b1e3916884797e5ad8ee(
    *,
    email_address: builtins.str,
    name: builtins.str,
    use_common_alert_schema: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f058926a135d11439a34a6657be70d37ffecc68928ff2a521ba2c71b4d74336(
    *,
    callback_url: builtins.str,
    name: builtins.str,
    resource_id: builtins.str,
    use_common_alert_schema: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad253453a305e7e5342f4ecb57198c2a5d88f06046b6b1e0ce11eaf642b40503(
    *,
    country_code: builtins.str,
    name: builtins.str,
    phone_number: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d2c513d1203f49b53ed7b54b11c22a12d11e9209884872ecebdb95d0271a76ec(
    *,
    country_code: builtins.str,
    name: builtins.str,
    phone_number: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__33b8e07750a30d4620204607eb08493d7a595c4ca865f62b77b7fb3b2ba8521f(
    *,
    name: builtins.str,
    service_uri: builtins.str,
    use_common_alert_schema: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass
