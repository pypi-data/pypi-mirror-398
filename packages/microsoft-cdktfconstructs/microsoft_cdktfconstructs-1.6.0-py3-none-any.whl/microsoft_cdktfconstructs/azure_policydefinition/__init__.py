r'''
# Azure Policy Definition Construct

This module provides a unified, version-aware implementation for managing Azure Policy Definitions using the AZAPI provider and CDK for Terraform.

## Overview

Azure Policy Definitions are rules that enforce specific conditions and effects on Azure resources. They are deployed at subscription or management group scope and can be used to ensure compliance with organizational standards.

## Key Features

* **AZAPI Provider Integration**: Direct ARM API access for reliable deployments
* **Version-Aware**: Automatically uses the latest stable API version (2021-06-01)
* **Schema-Driven Validation**: Built-in validation based on Azure API schemas
* **Type-Safe**: Full TypeScript support with comprehensive interfaces
* **JSII Compatible**: Can be used from multiple programming languages
* **Flexible Policy Rules**: Support for simple and complex policy logic
* **Parameterized Policies**: Create reusable policies with parameters

## AZAPI Provider Benefits

This construct uses the AZAPI provider, which offers several advantages:

1. **Direct ARM API Access**: Communicates directly with Azure Resource Manager APIs
2. **Faster Updates**: New Azure features are available immediately without provider updates
3. **Consistent Behavior**: Matches Azure's native behavior exactly
4. **Better Error Messages**: Detailed error messages directly from Azure
5. **Version Flexibility**: Easily pin to specific API versions for stability

## Installation

This package is part of the `@microsoft/terraform-cdk-constructs` library.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Basic Usage

### Simple Policy Definition

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { PolicyDefinition } from "@microsoft/terraform-cdk-constructs/azure-policydefinition";

class MyStack extends TerraformStack {
  constructor(scope: App, name: string) {
    super(scope, name);

    // Configure the AZAPI provider
    new AzapiProvider(this, "azapi", {});

    // Create a simple policy definition
    const policyDefinition = new PolicyDefinition(this, "require-tags", {
      name: "require-environment-tag",
      displayName: "Require Environment Tag",
      description: "Ensures all resources have an Environment tag",
      policyType: "Custom",
      mode: "Indexed",
      policyRule: {
        if: {
          field: "tags['Environment']",
          exists: "false",
        },
        then: {
          effect: "deny",
        },
      },
      metadata: {
        category: "Tags",
        version: "1.0.0",
      },
    });

    console.log("Policy ID:", policyDefinition.id);
  }
}

const app = new App();
new MyStack(app, "my-stack");
app.synth();
```

### Policy Definition with Parameters

```python
const policyDefinition = new PolicyDefinition(this, "tag-policy", {
  name: "require-tag-with-values",
  displayName: "Require Tag with Specific Values",
  description: "Ensures resources have a tag with an allowed value",
  policyRule: {
    if: {
      allOf: [
        {
          field: "[concat('tags[', parameters('tagName'), ']')]",
          exists: "true",
        },
        {
          field: "[concat('tags[', parameters('tagName'), ']')]",
          notIn: "[parameters('allowedValues')]",
        },
      ],
    },
    then: {
      effect: "[parameters('effect')]",
    },
  },
  parameters: {
    tagName: {
      type: "String",
      metadata: {
        displayName: "Tag Name",
        description: "Name of the tag to check",
      },
      defaultValue: "CostCenter",
    },
    allowedValues: {
      type: "Array",
      metadata: {
        displayName: "Allowed Values",
        description: "List of allowed tag values",
      },
      defaultValue: ["Engineering", "Marketing", "Operations"],
    },
    effect: {
      type: "String",
      metadata: {
        displayName: "Effect",
        description: "The effect of the policy (audit or deny)",
      },
      allowedValues: ["audit", "deny"],
      defaultValue: "audit",
    },
  },
  metadata: {
    category: "Tags",
    version: "1.0.0",
  },
});
```

## Advanced Features

### Complex Policy Rules

```python
const policyDefinition = new PolicyDefinition(this, "storage-policy", {
  name: "require-https-storage",
  displayName: "Require HTTPS for Storage Accounts",
  description: "Denies storage accounts that don't enforce HTTPS",
  mode: "Indexed",
  policyRule: {
    if: {
      allOf: [
        {
          field: "type",
          equals: "Microsoft.Storage/storageAccounts",
        },
        {
          field: "Microsoft.Storage/storageAccounts/enableHttpsTrafficOnly",
          notEquals: "true",
        },
      ],
    },
    then: {
      effect: "deny",
    },
  },
  metadata: {
    category: "Storage",
    version: "1.0.0",
  },
});
```

### Explicit API Version

```python
const policyDefinition = new PolicyDefinition(this, "policy", {
  name: "my-policy",
  apiVersion: "2021-06-01", // Pin to specific version for stability
  policyRule: {
    if: {
      field: "location",
      notIn: ["eastus", "westus"],
    },
    then: {
      effect: "deny",
    },
  },
});
```

### Using Outputs

```python
const policyDefinition = new PolicyDefinition(this, "policy", {
  name: "my-policy",
  policyRule: {
    /* ... */
  },
});

// Use the policy definition ID in other resources
new TerraformOutput(this, "policy-id", {
  value: policyDefinition.id,
});

// Access policy properties
console.log("Policy Type:", policyDefinition.policyType);
console.log("Policy Mode:", policyDefinition.policyMode);
```

## Complete Properties Documentation

### PolicyDefinitionProps

| Property | Type | Required | Default | Description |
| -------- | ---- | -------- | ------- | ----------- |
| `name` | string | No* | Construct ID | Name of the policy definition |
| `policyRule` | object | **Yes** | - | The policy rule JSON object defining if/then logic |
| `displayName` | string | No | - | Display name for the policy in Azure Portal |
| `description` | string | No | - | Description of what the policy enforces |
| `policyType` | string | No | "Custom" | Type of policy: Custom, BuiltIn, Static, NotSpecified |
| `mode` | string | No | "All" | Policy mode: All, Indexed, or resource provider modes |
| `parameters` | object | No | - | Parameters that can be passed to policy assignments |
| `metadata` | object | No | - | Additional metadata (category, version, etc.) |
| `apiVersion` | string | No | "2021-06-01" | Specific API version to use |
| `ignoreChanges` | string[] | No | - | Properties to ignore during Terraform updates |
| `enableValidation` | boolean | No | true | Enable schema validation |
| `enableMigrationAnalysis` | boolean | No | false | Enable migration analysis between versions |
| `enableTransformation` | boolean | No | true | Enable property transformation |

*If `name` is not provided, the construct ID will be used as the policy definition name.

## Supported API Versions

| Version    | Support Level | Release Date | Notes                                   |
| ---------- | ------------- | ------------ | --------------------------------------- |
| 2021-06-01 | Active        | 2021-06-01   | Latest stable version (recommended)     |

## Policy Definition Concepts

### Policy Types

* **Custom**: User-defined policies (default) - Used for organization-specific requirements
* **BuiltIn**: Azure-provided policies - Pre-defined policies from Microsoft
* **Static**: Static policy definitions - Policies that don't change
* **NotSpecified**: Type not specified

### Policy Modes

* **All**: Evaluates all resource types (default) - Most common mode
* **Indexed**: Only evaluates resource types that support tags and location
* **Resource Provider Modes**: Specific modes like `Microsoft.KeyVault.Data` for data plane operations

### Policy Effects

Common effects used in the `then` clause of policy rules:

* **deny**: Blocks the resource request
* **audit**: Logs a warning but allows the request (useful for testing)
* **append**: Adds additional properties to the resource
* **modify**: Modifies the resource properties
* **deployIfNotExists**: Deploys resources if they don't exist
* **auditIfNotExists**: Audits if resources don't exist
* **disabled**: Disables the policy

### Policy Rule Structure

A policy rule consists of two main parts:

```python
{
  if: {
    // Condition(s) to evaluate
    field: "type",
    equals: "Microsoft.Storage/storageAccounts"
  },
  then: {
    // Action to take if condition is true
    effect: "deny"
  }
}
```

Conditions can use:

* `field`: Resource property to evaluate
* `equals`, `notEquals`: Exact matching
* `in`, `notIn`: Array matching
* `contains`, `notContains`: Substring matching
* `exists`: Check if property exists
* `allOf`, `anyOf`: Logical operators for multiple conditions

## Available Outputs

Policy Definition constructs expose the following outputs:

* `id`: The Azure resource ID of the policy definition
* `name`: The name of the policy definition
* `resourceId`: Alias for the ID (for consistency with other constructs)
* `policyType`: The type of policy definition (Custom, BuiltIn, etc.)
* `policyMode`: The mode of the policy definition (All, Indexed, etc.)

## Best Practices

1. **Use Descriptive Names and Display Names**

   * Make policy purpose clear from the name
   * Include version information in metadata
2. **Start with Audit Effect**

   * Test new policies with `audit` effect first
   * Monitor audit logs before switching to `deny`
3. **Add Comprehensive Metadata**

   * Include category for organization
   * Add version for tracking changes
   * Document purpose and scope
4. **Make Policies Reusable**

   * Use parameters for flexibility
   * Provide sensible default values
   * Document parameter usage
5. **Test Thoroughly**

   * Use integration tests before production
   * Test with various resource types
   * Verify parameter combinations
6. **Document Policy Logic**

   * Provide clear descriptions
   * Document any exceptions or special cases
   * Include examples in metadata
7. **Use Appropriate Policy Modes**

   * Use `Indexed` for resource-level policies
   * Use `All` when location/tags don't apply
   * Use resource provider modes for data plane policies
8. **Version Control**

   * Store policy definitions in source control
   * Use semantic versioning in metadata
   * Document breaking changes

## Examples

### Require Specific Resource Locations

```python
new PolicyDefinition(this, "allowed-locations", {
  name: "allowed-resource-locations",
  displayName: "Allowed Resource Locations",
  description: "Restricts resources to approved Azure regions",
  policyRule: {
    if: {
      field: "location",
      notIn: ["eastus", "westus", "centralus"],
    },
    then: {
      effect: "deny",
    },
  },
});
```

### Enforce Naming Conventions

```python
new PolicyDefinition(this, "naming-convention", {
  name: "enforce-naming-convention",
  displayName: "Enforce Resource Naming Convention",
  policyRule: {
    if: {
      field: "name",
      notMatch: "^[a-z0-9-]+$",
    },
    then: {
      effect: "deny",
    },
  },
});
```

### Audit Missing Tags

```python
new PolicyDefinition(this, "audit-tags", {
  name: "audit-required-tags",
  displayName: "Audit Resources Missing Required Tags",
  policyRule: {
    if: {
      anyOf: [
        {
          field: "tags['CostCenter']",
          exists: "false",
        },
        {
          field: "tags['Environment']",
          exists: "false",
        },
      ],
    },
    then: {
      effect: "audit",
    },
  },
});
```

## Related Constructs

* **Policy Assignments**: Use policy definitions by assigning them to scopes (subscriptions, resource groups)
* **Role Definitions**: Define custom RBAC roles for Azure resources
* **Role Assignments**: Assign roles to identities for access control

## Troubleshooting

### Common Issues

1. **Policy Not Taking Effect**

   * Check policy assignment scope
   * Verify policy mode matches resource type
   * Allow time for policy evaluation (can take 15-30 minutes)
2. **Validation Errors**

   * Ensure policyRule is valid JSON
   * Check parameter types and values
   * Verify field names match Azure resource properties
3. **Scope Issues**

   * Policy definitions are subscription-scoped
   * Ensure proper RBAC permissions
   * Check management group hierarchy if applicable

## Contributing

Contributions are welcome! Please refer to the main project's contributing guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
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


class PolicyDefinition(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policydefinition.PolicyDefinition",
):
    '''Unified Azure Policy Definition implementation.

    This class provides a single, version-aware implementation for managing Azure
    Policy Definitions. It automatically handles version resolution, schema validation,
    and property transformation.

    Note: Policy definitions are deployed at subscription or management group scope.
    Unlike most Azure resources, they do not have a location property as they are
    not region-specific.

    Example::

        // Policy definition with parameters:
        const policyDefinition = new PolicyDefinition(this, "policy", {
          name: "require-tag-policy",
          displayName: "Require tag on resources",
          policyRule: {
            if: {
              field: "[concat('tags[', parameters('tagName'), ']')]",
              exists: "false"
            },
            then: {
              effect: "deny"
            }
          },
          parameters: {
            tagName: {
              type: "String",
              metadata: {
                displayName: "Tag Name"
              }
            }
          }
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        policy_rule: typing.Any,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Any = None,
        mode: typing.Optional[builtins.str] = None,
        parameters: typing.Any = None,
        policy_type: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Policy Definition using the VersionedAzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param policy_rule: The policy rule as a JSON object Defines the if/then logic that determines policy enforcement This is required for all policy definitions.
        :param description: The policy definition description Provides detailed information about what the policy enforces.
        :param display_name: The display name of the policy definition Provides a human-readable name for the policy.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata for the policy definition Used to store additional information like category, version, etc.
        :param mode: The policy mode Determines which resource types will be evaluated. Default: "All"
        :param parameters: Parameters for the policy definition Allows policy assignments to provide values that are used in the policy rule.
        :param policy_type: The type of policy definition. Default: "Custom"
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
            type_hints = typing.get_type_hints(_typecheckingstub__d4e28903a06a72000244427e86989df6a69cc84776e7713a5ea3956006690e7b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = PolicyDefinitionProps(
            policy_rule=policy_rule,
            description=description,
            display_name=display_name,
            ignore_changes=ignore_changes,
            metadata=metadata,
            mode=mode,
            parameters=parameters,
            policy_type=policy_type,
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

        Note: Policy definitions do not have a location property as they are
        subscription or management group scoped resources.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc9e10dbd4e5283400118fc3a590380383ba2659249c97ae1faf47ef976729d7)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="customizeResourceConfig")
    def _customize_resource_config(self, config: typing.Any) -> typing.Any:
        '''Customizes the AZAPI ResourceConfig for policy-specific requirements.

        Policy definitions require special handling because:

        1. They contain complex nested objects (ARM templates in DeployIfNotExists policies)
        2. They use Azure Policy expressions like [field()], [parameters()], [variables()]
           which are NOT Terraform interpolations but Azure-native expressions
        3. Schema validation may strip unknown properties from deeply nested structures

        :param config: - The base ResourceConfig.

        :return: Modified ResourceConfig with policy-specific settings

        :override: true
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d51b9a44e8620493aa3fd63ad76bd0951072b15d9e32625134dbeec45cec1581)
            check_type(argname="argument config", value=config, expected_type=type_hints["config"])
        return typing.cast(typing.Any, jsii.invoke(self, "customizeResourceConfig", [config]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Policy Definitions.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @jsii.member(jsii_name="supportsTags")
    def _supports_tags(self) -> builtins.bool:
        '''Policy Definitions do not support tags at the resource level Tags are not a valid property for Microsoft.Authorization/policyDefinitions.

        :return: false - Policy Definitions cannot have tags

        :override: true
        '''
        return typing.cast(builtins.bool, jsii.invoke(self, "supportsTags", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="policyMode")
    def policy_mode(self) -> builtins.str:
        '''Get the policy mode.'''
        return typing.cast(builtins.str, jsii.get(self, "policyMode"))

    @builtins.property
    @jsii.member(jsii_name="policyType")
    def policy_type(self) -> builtins.str:
        '''Get the policy type.'''
        return typing.cast(builtins.str, jsii.get(self, "policyType"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "PolicyDefinitionProps":
        '''The input properties for this Policy Definition instance.'''
        return typing.cast("PolicyDefinitionProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policydefinition.PolicyDefinitionBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class PolicyDefinitionBody:
    def __init__(
        self,
        *,
        properties: typing.Union["PolicyDefinitionProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Policy Definition API calls This matches the Azure REST API schema for policy definitions.

        :param properties: The properties of the policy definition.
        '''
        if isinstance(properties, dict):
            properties = PolicyDefinitionProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0657ed07126b893992a523233fa3e437c3251a22d3ed4c9a0e0df9d02677dc69)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "PolicyDefinitionProperties":
        '''The properties of the policy definition.'''
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("PolicyDefinitionProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyDefinitionBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policydefinition.PolicyDefinitionProperties",
    jsii_struct_bases=[],
    name_mapping={
        "policy_rule": "policyRule",
        "description": "description",
        "display_name": "displayName",
        "metadata": "metadata",
        "mode": "mode",
        "parameters": "parameters",
        "policy_type": "policyType",
    },
)
class PolicyDefinitionProperties:
    def __init__(
        self,
        *,
        policy_rule: typing.Any,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        metadata: typing.Any = None,
        mode: typing.Optional[builtins.str] = None,
        parameters: typing.Any = None,
        policy_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties interface for Azure Policy Definition This is required for JSII compliance to support multi-language code generation.

        :param policy_rule: The policy rule object.
        :param description: The policy definition description.
        :param display_name: The display name of the policy definition.
        :param metadata: Metadata for the policy definition.
        :param mode: The policy mode.
        :param parameters: Parameters for the policy definition.
        :param policy_type: The type of policy definition.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b1115e6ead4210b872bf81e576586720e443667206cf657a2af3f4e2e7964c2)
            check_type(argname="argument policy_rule", value=policy_rule, expected_type=type_hints["policy_rule"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
            check_type(argname="argument policy_type", value=policy_type, expected_type=type_hints["policy_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "policy_rule": policy_rule,
        }
        if description is not None:
            self._values["description"] = description
        if display_name is not None:
            self._values["display_name"] = display_name
        if metadata is not None:
            self._values["metadata"] = metadata
        if mode is not None:
            self._values["mode"] = mode
        if parameters is not None:
            self._values["parameters"] = parameters
        if policy_type is not None:
            self._values["policy_type"] = policy_type

    @builtins.property
    def policy_rule(self) -> typing.Any:
        '''The policy rule object.'''
        result = self._values.get("policy_rule")
        assert result is not None, "Required property 'policy_rule' is missing"
        return typing.cast(typing.Any, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The policy definition description.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''The display name of the policy definition.'''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metadata(self) -> typing.Any:
        '''Metadata for the policy definition.'''
        result = self._values.get("metadata")
        return typing.cast(typing.Any, result)

    @builtins.property
    def mode(self) -> typing.Optional[builtins.str]:
        '''The policy mode.'''
        result = self._values.get("mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(self) -> typing.Any:
        '''Parameters for the policy definition.'''
        result = self._values.get("parameters")
        return typing.cast(typing.Any, result)

    @builtins.property
    def policy_type(self) -> typing.Optional[builtins.str]:
        '''The type of policy definition.'''
        result = self._values.get("policy_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyDefinitionProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policydefinition.PolicyDefinitionProps",
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
        "policy_rule": "policyRule",
        "description": "description",
        "display_name": "displayName",
        "ignore_changes": "ignoreChanges",
        "metadata": "metadata",
        "mode": "mode",
        "parameters": "parameters",
        "policy_type": "policyType",
    },
)
class PolicyDefinitionProps(_AzapiResourceProps_141a2340):
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
        policy_rule: typing.Any,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Any = None,
        mode: typing.Optional[builtins.str] = None,
        parameters: typing.Any = None,
        policy_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Policy Definition.

        Extends AzapiResourceProps with Policy Definition specific properties

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
        :param policy_rule: The policy rule as a JSON object Defines the if/then logic that determines policy enforcement This is required for all policy definitions.
        :param description: The policy definition description Provides detailed information about what the policy enforces.
        :param display_name: The display name of the policy definition Provides a human-readable name for the policy.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata for the policy definition Used to store additional information like category, version, etc.
        :param mode: The policy mode Determines which resource types will be evaluated. Default: "All"
        :param parameters: Parameters for the policy definition Allows policy assignments to provide values that are used in the policy rule.
        :param policy_type: The type of policy definition. Default: "Custom"
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ccbdb84b0b985105c2d0fe9b91c8b618a099c872fe29f9344a6d87ae9f5ae6a5)
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
            check_type(argname="argument policy_rule", value=policy_rule, expected_type=type_hints["policy_rule"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
            check_type(argname="argument policy_type", value=policy_type, expected_type=type_hints["policy_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "policy_rule": policy_rule,
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
        if description is not None:
            self._values["description"] = description
        if display_name is not None:
            self._values["display_name"] = display_name
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if metadata is not None:
            self._values["metadata"] = metadata
        if mode is not None:
            self._values["mode"] = mode
        if parameters is not None:
            self._values["parameters"] = parameters
        if policy_type is not None:
            self._values["policy_type"] = policy_type

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
    def policy_rule(self) -> typing.Any:
        '''The policy rule as a JSON object Defines the if/then logic that determines policy enforcement This is required for all policy definitions.

        Example::

            {
              if: {
                field: "tags['Environment']",
                exists: "false"
              },
              then: {
                effect: "deny"
              }
            }
        '''
        result = self._values.get("policy_rule")
        assert result is not None, "Required property 'policy_rule' is missing"
        return typing.cast(typing.Any, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The policy definition description Provides detailed information about what the policy enforces.

        Example::

            "Enforces a required tag and its value on resources"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''The display name of the policy definition Provides a human-readable name for the policy.

        Example::

            "Require tag and its value on resources"
        '''
        result = self._values.get("display_name")
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
    def metadata(self) -> typing.Any:
        '''Metadata for the policy definition Used to store additional information like category, version, etc.

        Example::

            {
              category: "Tags",
              version: "1.0.0"
            }
        '''
        result = self._values.get("metadata")
        return typing.cast(typing.Any, result)

    @builtins.property
    def mode(self) -> typing.Optional[builtins.str]:
        '''The policy mode Determines which resource types will be evaluated.

        :default: "All"

        Example::

            "All", "Indexed", "Microsoft.KeyVault.Data"
        '''
        result = self._values.get("mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parameters(self) -> typing.Any:
        '''Parameters for the policy definition Allows policy assignments to provide values that are used in the policy rule.

        Example::

            {
              tagName: {
                type: "String",
                metadata: {
                  displayName: "Tag Name",
                  description: "Name of the tag to enforce"
                }
              }
            }
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Any, result)

    @builtins.property
    def policy_type(self) -> typing.Optional[builtins.str]:
        '''The type of policy definition.

        :default: "Custom"

        Example::

            "Custom", "BuiltIn", "Static", "NotSpecified"
        '''
        result = self._values.get("policy_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyDefinitionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "PolicyDefinition",
    "PolicyDefinitionBody",
    "PolicyDefinitionProperties",
    "PolicyDefinitionProps",
]

publication.publish()

def _typecheckingstub__d4e28903a06a72000244427e86989df6a69cc84776e7713a5ea3956006690e7b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    policy_rule: typing.Any,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Any = None,
    mode: typing.Optional[builtins.str] = None,
    parameters: typing.Any = None,
    policy_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__cc9e10dbd4e5283400118fc3a590380383ba2659249c97ae1faf47ef976729d7(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d51b9a44e8620493aa3fd63ad76bd0951072b15d9e32625134dbeec45cec1581(
    config: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0657ed07126b893992a523233fa3e437c3251a22d3ed4c9a0e0df9d02677dc69(
    *,
    properties: typing.Union[PolicyDefinitionProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b1115e6ead4210b872bf81e576586720e443667206cf657a2af3f4e2e7964c2(
    *,
    policy_rule: typing.Any,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    metadata: typing.Any = None,
    mode: typing.Optional[builtins.str] = None,
    parameters: typing.Any = None,
    policy_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ccbdb84b0b985105c2d0fe9b91c8b618a099c872fe29f9344a6d87ae9f5ae6a5(
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
    policy_rule: typing.Any,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Any = None,
    mode: typing.Optional[builtins.str] = None,
    parameters: typing.Any = None,
    policy_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
