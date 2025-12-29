r'''
# Azure Policy Assignment Construct

This module provides a unified, version-aware implementation for managing Azure Policy Assignments using the AZAPI provider and CDK for Terraform.

## Overview

Azure Policy Assignments apply policy definitions to specific scopes (subscription, resource group, or resource) and provide parameter values for policy enforcement. Policy assignments can configure enforcement modes, managed identities for remediation, and custom non-compliance messages.

## Key Features

* **AZAPI Provider Integration**: Direct ARM API access for reliable deployments
* **Version-Aware**: Automatically uses the latest stable API version (2022-06-01)
* **Schema-Driven Validation**: Built-in validation based on Azure API schemas
* **Type-Safe**: Full TypeScript support with comprehensive interfaces
* **JSII Compatible**: Can be used from multiple programming languages
* **Flexible Scoping**: Support for subscription, resource group, and resource-level assignments
* **Enforcement Modes**: Control whether policies are enforced or audited
* **Managed Identity Support**: Enable remediation for deployIfNotExists and modify policies
* **Scope Exclusions**: Exclude specific scopes from policy evaluation

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

### Simple Policy Assignment

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { PolicyDefinition } from "@microsoft/terraform-cdk-constructs/azure-policydefinition";
import { PolicyAssignment } from "@microsoft/terraform-cdk-constructs/azure-policyassignment";

class MyStack extends TerraformStack {
  constructor(scope: App, name: string) {
    super(scope, name);

    // Configure the AZAPI provider
    new AzapiProvider(this, "azapi", {});

    // First create or reference a policy definition
    const policyDef = new PolicyDefinition(this, "require-tags", {
      name: "require-environment-tag",
      policyRule: {
        if: {
          field: "tags['Environment']",
          exists: "false",
        },
        then: {
          effect: "deny",
        },
      },
    });

    // Then assign the policy to a scope
    const assignment = new PolicyAssignment(this, "tag-assignment", {
      name: "require-tags-on-rg",
      displayName: "Require Environment Tag on Resources",
      description: "Ensures all resources in this resource group have an Environment tag",
      policyDefinitionId: policyDef.id,
      scope: "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg",
    });

    console.log("Assignment ID:", assignment.id);
  }
}

const app = new App();
new MyStack(app, "my-stack");
app.synth();
```

### Assignment with Parameters

```python
const assignment = new PolicyAssignment(this, "tag-assignment", {
  name: "require-environment-tag",
  displayName: "Require Environment Tag",
  policyDefinitionId: parameterizedPolicyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  parameters: {
    tagName: {
      value: "Environment",
    },
    allowedValues: {
      value: ["Development", "Staging", "Production"],
    },
    effect: {
      value: "deny",
    },
  },
});
```

### Assignment with Built-in Policy

```python
// Reference a built-in Azure policy
const assignment = new PolicyAssignment(this, "builtin-assignment", {
  name: "audit-vm-managed-disks",
  displayName: "Audit VMs without Managed Disks",
  policyDefinitionId:
    "/providers/Microsoft.Authorization/policyDefinitions/06a78e20-9358-41c9-923c-fb736d382a4d",
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  enforcementMode: "Default",
});
```

## Advanced Features

### Enforcement Modes

Control whether the policy is enforced or only audited:

```python
// Audit mode - policy is evaluated but not enforced
const auditAssignment = new PolicyAssignment(this, "audit-assignment", {
  name: "audit-policy",
  displayName: "Audit Policy (DoNotEnforce)",
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  enforcementMode: "DoNotEnforce", // Audit only
});

// Enforcement mode - policy is actively enforced (default)
const enforceAssignment = new PolicyAssignment(this, "enforce-assignment", {
  name: "enforce-policy",
  displayName: "Enforce Policy (Default)",
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  enforcementMode: "Default", // Actively enforced
});
```

### Managed Identity for Remediation

For policies with deployIfNotExists or modify effects, add a managed identity:

```python
const assignment = new PolicyAssignment(this, "remediation-assignment", {
  name: "deploy-vm-monitoring",
  displayName: "Deploy VM Monitoring Extension",
  policyDefinitionId: deployPolicyId,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  identity: {
    type: "SystemAssigned",
  },
});

// Or use a user-assigned identity
const userIdentityAssignment = new PolicyAssignment(
  this,
  "user-identity-assignment",
  {
    name: "deploy-with-user-identity",
    policyDefinitionId: deployPolicyId,
    scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
    identity: {
      type: "UserAssigned",
      userAssignedIdentities: {
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-identity":
          {},
      },
    },
  },
);
```

### Scope Exclusions

Exclude specific scopes from policy evaluation:

```python
const assignment = new PolicyAssignment(this, "with-exclusions", {
  name: "subscription-policy-with-exclusions",
  displayName: "Subscription Policy with Exclusions",
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  notScopes: [
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/excluded-rg",
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-rg",
  ],
});
```

### Custom Non-Compliance Messages

Provide helpful messages when resources are non-compliant:

```python
const assignment = new PolicyAssignment(this, "with-messages", {
  name: "tag-policy",
  displayName: "Require Resource Tags",
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  nonComplianceMessages: [
    {
      message:
        "All resources must have the required tags. Please add the Environment tag with an appropriate value.",
    },
  ],
});
```

### Explicit API Version

```python
const assignment = new PolicyAssignment(this, "pinned-version", {
  name: "my-assignment",
  apiVersion: "2022-06-01", // Pin to specific version for stability
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
});
```

### Using Outputs

```python
const assignment = new PolicyAssignment(this, "assignment", {
  name: "my-assignment",
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
});

// Use the assignment ID in other resources
new TerraformOutput(this, "assignment-id", {
  value: assignment.id,
});

// Access assignment properties
console.log("Policy Definition ID:", assignment.policyDefinitionId);
console.log("Assignment Scope:", assignment.assignmentScope);
console.log("Enforcement Mode:", assignment.enforcementMode);
```

## Complete Properties Documentation

### PolicyAssignmentProps

| Property                 | Type     | Required | Default   | Description                                           |
| ------------------------ | -------- | -------- | --------- | ----------------------------------------------------- |
| `name`                   | string   | No*     | Construct | Name of the policy assignment                         |
| `policyDefinitionId`     | string   | **Yes**  | -         | ID of the policy definition to assign                 |
| `scope`                  | string   | **Yes**  | -         | Scope where the policy is assigned                    |
| `displayName`            | string   | No       | -         | Display name for the assignment                       |
| `description`            | string   | No       | -         | Description of the assignment                         |
| `enforcementMode`        | string   | No       | "Default" | Default or DoNotEnforce                               |
| `parameters`             | object   | No       | -         | Parameter values for the policy                       |
| `metadata`               | object   | No       | -         | Additional metadata                                   |
| `identity`               | object   | No       | -         | Managed identity configuration                        |
| `notScopes`              | string[] | No       | -         | Scopes to exclude from policy evaluation              |
| `nonComplianceMessages`  | array    | No       | -         | Custom non-compliance messages                        |
| `apiVersion`             | string   | No       | latest    | Specific API version to use                           |
| `ignoreChanges`          | string[] | No       | -         | Properties to ignore during Terraform updates         |
| `enableValidation`       | boolean  | No       | true      | Enable schema validation                              |
| `enableMigrationAnalysis`| boolean  | No       | false     | Enable migration analysis between versions            |
| `enableTransformation`   | boolean  | No       | true      | Enable property transformation                        |

*If `name` is not provided, the construct ID will be used as the assignment name.

## Supported API Versions

| Version    | Support Level | Release Date | Notes                               |
| ---------- | ------------- | ------------ | ----------------------------------- |
| 2022-06-01 | Active        | 2022-06-01   | Latest stable version (recommended) |

## Policy Assignment Concepts

### Scoping Levels

Policy assignments can be applied at different organizational levels:

#### Subscription Scope

```python
scope: "/subscriptions/00000000-0000-0000-0000-000000000000";
```

Applies to all resources in the subscription (unless excluded via notScopes)

#### Resource Group Scope

```python
scope:
  "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg";
```

Applies to all resources in the resource group

#### Resource Scope

```python
scope:
  "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/mystorage";
```

Applies to a specific resource

### Enforcement Modes

* **Default**: Policy effect is enforced during resource creation/update (deny, modify, deployIfNotExists)
* **DoNotEnforce**: Policy is evaluated but the effect is not enforced (audit only mode)

Use DoNotEnforce to test policies without impacting resources, then switch to Default when ready.

### Identity Types

Managed identities are required for policy assignments that use deployIfNotExists or modify effects:

* **SystemAssigned**: Azure automatically creates and manages an identity for the assignment
* **UserAssigned**: You provide an existing managed identity
* **None**: No identity (use for audit and deny policies)

The identity needs appropriate RBAC permissions (typically Contributor or specific resource permissions) to perform remediation actions.

## Available Outputs

Policy Assignment constructs expose the following outputs:

* `id`: The Azure resource ID of the policy assignment
* `name`: The name of the policy assignment
* `resourceId`: Alias for the ID (for consistency with other constructs)
* `policyDefinitionId`: The ID of the assigned policy definition
* `assignmentScope`: The scope where the policy is assigned
* `enforcementMode`: The enforcement mode of the assignment

## Best Practices

1. **Start with DoNotEnforce Mode**

   * Test new assignments in audit mode first
   * Monitor compliance reports before enforcing
   * Gradually roll out enforcement after validation
2. **Use Descriptive Names**

   * Make assignment purpose clear from the name
   * Include scope information in display name
   * Document the assignment's intent
3. **Provide Non-Compliance Messages**

   * Help users understand why resources are non-compliant
   * Include remediation steps in messages
   * Be specific and actionable
4. **Scope Appropriately**

   * Apply policies at the right organizational level
   * Use subscription scope for organization-wide policies
   * Use resource group scope for environment-specific policies
5. **Use Parameters Effectively**

   * Reuse policy definitions with different parameter values
   * Provide appropriate defaults in policy definitions
   * Document parameter requirements
6. **Configure Identity Correctly**

   * Add managed identity for deployIfNotExists and modify policies
   * Grant minimum required permissions (least privilege)
   * Use user-assigned identities for shared remediation scenarios
7. **Monitor and Review**

   * Regularly review compliance reports
   * Address non-compliant resources
   * Update policies and assignments as requirements change
8. **Document Exclusions**

   * Clearly document why scopes are excluded
   * Regularly review exclusions for continued validity
   * Minimize the use of exclusions

## Examples

### Assign Tag Policy at Subscription Level

```python
const tagPolicy = new PolicyDefinition(this, "tag-policy", {
  name: "require-cost-center",
  policyRule: {
    if: {
      field: "tags['CostCenter']",
      exists: "false",
    },
    then: {
      effect: "deny",
    },
  },
});

const tagAssignment = new PolicyAssignment(this, "sub-tag-assignment", {
  name: "require-cost-center-sub",
  displayName: "Require CostCenter Tag on All Resources",
  description: "Denies resource creation without CostCenter tag",
  policyDefinitionId: tagPolicy.id,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
  nonComplianceMessages: [
    {
      message:
        "Resources must have a CostCenter tag for billing purposes. Contact your team lead for the appropriate cost center code.",
    },
  ],
});
```

### Audit Mode Testing

```python
// Test a policy in audit mode before enforcing
const testAssignment = new PolicyAssignment(this, "test-assignment", {
  name: "test-location-policy",
  displayName: "Test Location Restriction (Audit Only)",
  description: "Testing location policy in audit mode",
  policyDefinitionId: locationPolicyId,
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/test-rg",
  enforcementMode: "DoNotEnforce", // Audit only
  metadata: {
    testPhase: "audit",
    plannedEnforcement: "2024-02-01",
  },
});
```

### Remediation with Managed Identity

```python
const remediationPolicy = new PolicyDefinition(this, "deploy-backup", {
  name: "deploy-vm-backup",
  policyRule: {
    if: {
      field: "type",
      equals: "Microsoft.Compute/virtualMachines",
    },
    then: {
      effect: "deployIfNotExists",
      details: {
        type: "Microsoft.RecoveryServices/backupprotecteditems",
        deploymentScope: "subscription",
        // ... deployment template
      },
    },
  },
});

const remediationAssignment = new PolicyAssignment(
  this,
  "backup-assignment",
  {
    name: "deploy-vm-backup-assignment",
    displayName: "Deploy VM Backup Configuration",
    description:
      "Automatically deploys backup configuration for virtual machines",
    policyDefinitionId: remediationPolicy.id,
    scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
    identity: {
      type: "SystemAssigned",
    },
  },
);

// Note: You would also need to create a role assignment to grant
// the managed identity permissions to deploy backup configurations
```

### Multiple Assignments for Different Environments

```python
const environments = ["dev", "staging", "prod"];

environments.forEach((env) => {
  const rgScope = `/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/${env}-rg`;

  new PolicyAssignment(this, `${env}-assignment`, {
    name: `require-tags-${env}`,
    displayName: `Require Tags in ${env.toUpperCase()} Environment`,
    policyDefinitionId: tagPolicyId,
    scope: rgScope,
    parameters: {
      environmentTag: {
        value: env,
      },
    },
    metadata: {
      environment: env,
      assignedBy: "terraform-cdk",
    },
  });
});
```

## Relationship with Policy Definitions

Policy Assignments apply Policy Definitions to specific scopes. The typical workflow is:

1. **Create or Reference a Policy Definition**: Define the rules and conditions
2. **Create a Policy Assignment**: Apply the definition to a scope with specific parameters
3. **Monitor Compliance**: Review compliance reports and take remediation actions

```python
// Step 1: Create a policy definition
const policyDef = new PolicyDefinition(this, "policy", {
  name: "my-policy",
  policyRule: {
    /* ... */
  },
});

// Step 2: Assign the policy to a scope
const assignment = new PolicyAssignment(this, "assignment", {
  name: "my-assignment",
  policyDefinitionId: policyDef.id,
  scope: "/subscriptions/...",
});

// Step 3: Monitor compliance via Azure Portal or API
```

## Related Constructs

* **Policy Definitions**: Define the rules and effects to enforce
* **Role Assignments**: Grant permissions for managed identities to perform remediation
* **Resource Groups**: Common scope for policy assignments
* **Management Groups**: Higher-level scope for organization-wide policies

## Troubleshooting

### Common Issues

1. **Policy Not Taking Effect**

   * Allow time for policy evaluation (15-30 minutes)
   * Check enforcement mode (DoNotEnforce vs Default)
   * Verify scope is correct
   * Check for exclusions in notScopes
2. **Remediation Failures**

   * Verify managed identity is configured
   * Check RBAC permissions for the identity
   * Review deployment template in policy definition
   * Check Azure Activity Log for detailed errors
3. **Compliance Not Showing**

   * Wait for compliance evaluation cycle
   * Trigger manual compliance scan
   * Verify assignment is deployed successfully
   * Check assignment scope matches resources
4. **Parameter Errors**

   * Ensure parameter types match policy definition
   * Check parameter names are correct
   * Verify values are in allowed ranges
   * Review parameter schema in policy definition

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


class PolicyAssignment(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policyassignment.PolicyAssignment",
):
    '''Unified Azure Policy Assignment implementation.

    This class provides a single, version-aware implementation for managing Azure
    Policy Assignments. It automatically handles version resolution, schema validation,
    and property transformation.

    Note: Policy assignments can be deployed at subscription, resource group, or resource scope.
    Like policy definitions, they do not have a location property as they are not region-specific.

    Example::

        // Policy assignment with managed identity:
        const assignment = new PolicyAssignment(this, "assignment", {
          name: "deploy-monitoring-assignment",
          policyDefinitionId: "/providers/Microsoft.Authorization/policyDefinitions/policy-id",
          scope: "/subscriptions/00000000-0000-0000-0000-000000000000",
          identity: {
            type: "SystemAssigned"
          }
        });
    '''

    def __init__(
        self,
        scope_: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        policy_definition_id: builtins.str,
        scope: builtins.str,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        enforcement_mode: typing.Optional[builtins.str] = None,
        identity: typing.Optional[typing.Union["PolicyAssignmentIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Any = None,
        non_compliance_messages: typing.Optional[typing.Sequence[typing.Union["PolicyAssignmentNonComplianceMessage", typing.Dict[builtins.str, typing.Any]]]] = None,
        not_scopes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parameters: typing.Any = None,
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
        '''Creates a new Azure Policy Assignment using the VersionedAzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope_: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param policy_definition_id: The policy definition ID to assign This can be a built-in or custom policy definition Required property.
        :param scope: The scope at which the policy assignment is applied Can be a subscription, resource group, or resource Required property.
        :param description: The policy assignment description Provides detailed information about the assignment.
        :param display_name: The display name of the policy assignment Provides a human-readable name for the assignment.
        :param enforcement_mode: The enforcement mode of the policy assignment. Default: "Default"
        :param identity: The managed identity associated with the policy assignment Required for policies with deployIfNotExists or modify effects.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata for the policy assignment Used to store additional information like assignedBy, parameterScopes, etc.
        :param non_compliance_messages: The non-compliance messages for the policy assignment Provides custom messages when resources are non-compliant.
        :param not_scopes: The policy's excluded scopes Resources within these scopes will not be evaluated by the policy.
        :param parameters: Parameters for the policy assignment Provides values for parameters defined in the policy definition.
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
            type_hints = typing.get_type_hints(_typecheckingstub__b6c3e6215342f45065c68b88b112bc1b9fbcf287c3d80aad8be323d200967981)
            check_type(argname="argument scope_", value=scope_, expected_type=type_hints["scope_"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = PolicyAssignmentProps(
            policy_definition_id=policy_definition_id,
            scope=scope,
            description=description,
            display_name=display_name,
            enforcement_mode=enforcement_mode,
            identity=identity,
            ignore_changes=ignore_changes,
            metadata=metadata,
            non_compliance_messages=non_compliance_messages,
            not_scopes=not_scopes,
            parameters=parameters,
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

        jsii.create(self.__class__, self, [scope_, id, props])

    @jsii.member(jsii_name="apiSchema")
    def _api_schema(self) -> _ApiSchema_5ce0490e:
        '''Gets the API schema for the resolved version Uses the framework's schema resolution to get the appropriate schema.'''
        return typing.cast(_ApiSchema_5ce0490e, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call Transforms the input properties into the JSON format expected by Azure REST API  Note: Policy assignments do not have a location property as they are scoped resources (subscription, resource group, or resource level).

        The scope property is NOT included in the body as it's read-only and
        automatically derived from the parentId.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2651048ae2c1dffb133469d426738a91f28f456532a1779b9719fe08ac462b53)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Overrides parent ID resolution to use the scope from props Policy assignments are scoped resources where the scope IS the parent.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4502d939384282498a7a75d3635a53008d6c1bb2b41c82dc3a26122f74cfea27)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Policy Assignments.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @jsii.member(jsii_name="supportsTags")
    def _supports_tags(self) -> builtins.bool:
        '''Policy Assignments do not support tags at the resource level Tags are not a valid property for Microsoft.Authorization/policyAssignments.

        :return: false - Policy Assignments cannot have tags

        :override: true
        '''
        return typing.cast(builtins.bool, jsii.invoke(self, "supportsTags", []))

    @builtins.property
    @jsii.member(jsii_name="assignmentScope")
    def assignment_scope(self) -> builtins.str:
        '''Get the scope of this policy assignment.'''
        return typing.cast(builtins.str, jsii.get(self, "assignmentScope"))

    @builtins.property
    @jsii.member(jsii_name="enforcementMode")
    def enforcement_mode(self) -> builtins.str:
        '''Get the enforcement mode.'''
        return typing.cast(builtins.str, jsii.get(self, "enforcementMode"))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="policyDefinitionId")
    def policy_definition_id(self) -> builtins.str:
        '''Get the policy definition ID this assignment references.'''
        return typing.cast(builtins.str, jsii.get(self, "policyDefinitionId"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "PolicyAssignmentProps":
        '''The input properties for this Policy Assignment instance.'''
        return typing.cast("PolicyAssignmentProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policyassignment.PolicyAssignmentBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties", "identity": "identity"},
)
class PolicyAssignmentBody:
    def __init__(
        self,
        *,
        properties: typing.Union["PolicyAssignmentProperties", typing.Dict[builtins.str, typing.Any]],
        identity: typing.Optional[typing.Union["PolicyAssignmentIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''The resource body interface for Azure Policy Assignment API calls This matches the Azure REST API schema for policy assignments.

        :param properties: The properties of the policy assignment.
        :param identity: The managed identity associated with the policy assignment.
        '''
        if isinstance(properties, dict):
            properties = PolicyAssignmentProperties(**properties)
        if isinstance(identity, dict):
            identity = PolicyAssignmentIdentity(**identity)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b4e38131e2f5d96555cf74d77029408bc15b407ed638a9c60015fe72278054e9)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }
        if identity is not None:
            self._values["identity"] = identity

    @builtins.property
    def properties(self) -> "PolicyAssignmentProperties":
        '''The properties of the policy assignment.'''
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("PolicyAssignmentProperties", result)

    @builtins.property
    def identity(self) -> typing.Optional["PolicyAssignmentIdentity"]:
        '''The managed identity associated with the policy assignment.'''
        result = self._values.get("identity")
        return typing.cast(typing.Optional["PolicyAssignmentIdentity"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyAssignmentBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policyassignment.PolicyAssignmentIdentity",
    jsii_struct_bases=[],
    name_mapping={
        "type": "type",
        "user_assigned_identities": "userAssignedIdentities",
    },
)
class PolicyAssignmentIdentity:
    def __init__(
        self,
        *,
        type: builtins.str,
        user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    ) -> None:
        '''Identity configuration for policy assignments Required for policies with deployIfNotExists or modify effects.

        :param type: The type of managed identity.
        :param user_assigned_identities: The user assigned identities associated with the policy assignment Required when type is UserAssigned.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c2a025cd97ce39cf7e9ae599e81ce348afbfffb044b85709aa8d04e768c11702)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument user_assigned_identities", value=user_assigned_identities, expected_type=type_hints["user_assigned_identities"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }
        if user_assigned_identities is not None:
            self._values["user_assigned_identities"] = user_assigned_identities

    @builtins.property
    def type(self) -> builtins.str:
        '''The type of managed identity.

        Example::

            "SystemAssigned", "UserAssigned", "None"
        '''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def user_assigned_identities(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''The user assigned identities associated with the policy assignment Required when type is UserAssigned.

        Example::

            {
              "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity": {}
            }
        '''
        result = self._values.get("user_assigned_identities")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyAssignmentIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policyassignment.PolicyAssignmentNonComplianceMessage",
    jsii_struct_bases=[],
    name_mapping={
        "message": "message",
        "policy_definition_reference_id": "policyDefinitionReferenceId",
    },
)
class PolicyAssignmentNonComplianceMessage:
    def __init__(
        self,
        *,
        message: builtins.str,
        policy_definition_reference_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Non-compliance message configuration.

        :param message: The non-compliance message for the policy assignment.
        :param policy_definition_reference_id: The policy definition reference ID within a policy set definition Optional - if specified, this message applies only to the specified policy within the set.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13128265132e31e45e79c77f8538f3eeeff8996f50d9b8b47a7291f67b234fc2)
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
            check_type(argname="argument policy_definition_reference_id", value=policy_definition_reference_id, expected_type=type_hints["policy_definition_reference_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "message": message,
        }
        if policy_definition_reference_id is not None:
            self._values["policy_definition_reference_id"] = policy_definition_reference_id

    @builtins.property
    def message(self) -> builtins.str:
        '''The non-compliance message for the policy assignment.'''
        result = self._values.get("message")
        assert result is not None, "Required property 'message' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def policy_definition_reference_id(self) -> typing.Optional[builtins.str]:
        '''The policy definition reference ID within a policy set definition Optional - if specified, this message applies only to the specified policy within the set.'''
        result = self._values.get("policy_definition_reference_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyAssignmentNonComplianceMessage(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policyassignment.PolicyAssignmentProperties",
    jsii_struct_bases=[],
    name_mapping={
        "policy_definition_id": "policyDefinitionId",
        "scope": "scope",
        "description": "description",
        "display_name": "displayName",
        "enforcement_mode": "enforcementMode",
        "metadata": "metadata",
        "non_compliance_messages": "nonComplianceMessages",
        "not_scopes": "notScopes",
        "parameters": "parameters",
    },
)
class PolicyAssignmentProperties:
    def __init__(
        self,
        *,
        policy_definition_id: builtins.str,
        scope: builtins.str,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        enforcement_mode: typing.Optional[builtins.str] = None,
        metadata: typing.Any = None,
        non_compliance_messages: typing.Optional[typing.Sequence[typing.Union[PolicyAssignmentNonComplianceMessage, typing.Dict[builtins.str, typing.Any]]]] = None,
        not_scopes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parameters: typing.Any = None,
    ) -> None:
        '''Properties interface for Azure Policy Assignment This is required for JSII compliance to support multi-language code generation.

        :param policy_definition_id: The policy definition ID.
        :param scope: The scope of the policy assignment.
        :param description: The policy assignment description.
        :param display_name: The display name of the policy assignment.
        :param enforcement_mode: The enforcement mode.
        :param metadata: Metadata for the policy assignment.
        :param non_compliance_messages: The non-compliance messages.
        :param not_scopes: The policy's excluded scopes.
        :param parameters: Parameters for the policy assignment.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e6119156b7a32ea4d6553da0e3451d18708a242c5d22d6747cc5191aacd4ca5)
            check_type(argname="argument policy_definition_id", value=policy_definition_id, expected_type=type_hints["policy_definition_id"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument enforcement_mode", value=enforcement_mode, expected_type=type_hints["enforcement_mode"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
            check_type(argname="argument non_compliance_messages", value=non_compliance_messages, expected_type=type_hints["non_compliance_messages"])
            check_type(argname="argument not_scopes", value=not_scopes, expected_type=type_hints["not_scopes"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "policy_definition_id": policy_definition_id,
            "scope": scope,
        }
        if description is not None:
            self._values["description"] = description
        if display_name is not None:
            self._values["display_name"] = display_name
        if enforcement_mode is not None:
            self._values["enforcement_mode"] = enforcement_mode
        if metadata is not None:
            self._values["metadata"] = metadata
        if non_compliance_messages is not None:
            self._values["non_compliance_messages"] = non_compliance_messages
        if not_scopes is not None:
            self._values["not_scopes"] = not_scopes
        if parameters is not None:
            self._values["parameters"] = parameters

    @builtins.property
    def policy_definition_id(self) -> builtins.str:
        '''The policy definition ID.'''
        result = self._values.get("policy_definition_id")
        assert result is not None, "Required property 'policy_definition_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scope(self) -> builtins.str:
        '''The scope of the policy assignment.'''
        result = self._values.get("scope")
        assert result is not None, "Required property 'scope' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The policy assignment description.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''The display name of the policy assignment.'''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enforcement_mode(self) -> typing.Optional[builtins.str]:
        '''The enforcement mode.'''
        result = self._values.get("enforcement_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def metadata(self) -> typing.Any:
        '''Metadata for the policy assignment.'''
        result = self._values.get("metadata")
        return typing.cast(typing.Any, result)

    @builtins.property
    def non_compliance_messages(
        self,
    ) -> typing.Optional[typing.List[PolicyAssignmentNonComplianceMessage]]:
        '''The non-compliance messages.'''
        result = self._values.get("non_compliance_messages")
        return typing.cast(typing.Optional[typing.List[PolicyAssignmentNonComplianceMessage]], result)

    @builtins.property
    def not_scopes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The policy's excluded scopes.'''
        result = self._values.get("not_scopes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def parameters(self) -> typing.Any:
        '''Parameters for the policy assignment.'''
        result = self._values.get("parameters")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyAssignmentProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_policyassignment.PolicyAssignmentProps",
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
        "policy_definition_id": "policyDefinitionId",
        "scope": "scope",
        "description": "description",
        "display_name": "displayName",
        "enforcement_mode": "enforcementMode",
        "identity": "identity",
        "ignore_changes": "ignoreChanges",
        "metadata": "metadata",
        "non_compliance_messages": "nonComplianceMessages",
        "not_scopes": "notScopes",
        "parameters": "parameters",
    },
)
class PolicyAssignmentProps(_AzapiResourceProps_141a2340):
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
        policy_definition_id: builtins.str,
        scope: builtins.str,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        enforcement_mode: typing.Optional[builtins.str] = None,
        identity: typing.Optional[typing.Union[PolicyAssignmentIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        metadata: typing.Any = None,
        non_compliance_messages: typing.Optional[typing.Sequence[typing.Union[PolicyAssignmentNonComplianceMessage, typing.Dict[builtins.str, typing.Any]]]] = None,
        not_scopes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parameters: typing.Any = None,
    ) -> None:
        '''Properties for the unified Azure Policy Assignment.

        Extends AzapiResourceProps with Policy Assignment specific properties

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
        :param policy_definition_id: The policy definition ID to assign This can be a built-in or custom policy definition Required property.
        :param scope: The scope at which the policy assignment is applied Can be a subscription, resource group, or resource Required property.
        :param description: The policy assignment description Provides detailed information about the assignment.
        :param display_name: The display name of the policy assignment Provides a human-readable name for the assignment.
        :param enforcement_mode: The enforcement mode of the policy assignment. Default: "Default"
        :param identity: The managed identity associated with the policy assignment Required for policies with deployIfNotExists or modify effects.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param metadata: Metadata for the policy assignment Used to store additional information like assignedBy, parameterScopes, etc.
        :param non_compliance_messages: The non-compliance messages for the policy assignment Provides custom messages when resources are non-compliant.
        :param not_scopes: The policy's excluded scopes Resources within these scopes will not be evaluated by the policy.
        :param parameters: Parameters for the policy assignment Provides values for parameters defined in the policy definition.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(identity, dict):
            identity = PolicyAssignmentIdentity(**identity)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5f4c63cf6d402827fbfc3ab71a25499f8def2702537c51da54dbcfa2ab94dff3)
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
            check_type(argname="argument policy_definition_id", value=policy_definition_id, expected_type=type_hints["policy_definition_id"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument enforcement_mode", value=enforcement_mode, expected_type=type_hints["enforcement_mode"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument metadata", value=metadata, expected_type=type_hints["metadata"])
            check_type(argname="argument non_compliance_messages", value=non_compliance_messages, expected_type=type_hints["non_compliance_messages"])
            check_type(argname="argument not_scopes", value=not_scopes, expected_type=type_hints["not_scopes"])
            check_type(argname="argument parameters", value=parameters, expected_type=type_hints["parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "policy_definition_id": policy_definition_id,
            "scope": scope,
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
        if enforcement_mode is not None:
            self._values["enforcement_mode"] = enforcement_mode
        if identity is not None:
            self._values["identity"] = identity
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if metadata is not None:
            self._values["metadata"] = metadata
        if non_compliance_messages is not None:
            self._values["non_compliance_messages"] = non_compliance_messages
        if not_scopes is not None:
            self._values["not_scopes"] = not_scopes
        if parameters is not None:
            self._values["parameters"] = parameters

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
    def policy_definition_id(self) -> builtins.str:
        '''The policy definition ID to assign This can be a built-in or custom policy definition Required property.

        Example::

            "/providers/Microsoft.Authorization/policyDefinitions/06a78e20-9358-41c9-923c-fb736d382a4d" (built-in)
        '''
        result = self._values.get("policy_definition_id")
        assert result is not None, "Required property 'policy_definition_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scope(self) -> builtins.str:
        '''The scope at which the policy assignment is applied Can be a subscription, resource group, or resource Required property.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-name"
        '''
        result = self._values.get("scope")
        assert result is not None, "Required property 'scope' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The policy assignment description Provides detailed information about the assignment.

        Example::

            "Enforces required tags on all resources in production environment"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''The display name of the policy assignment Provides a human-readable name for the assignment.

        Example::

            "Require tag on resources in production"
        '''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enforcement_mode(self) -> typing.Optional[builtins.str]:
        '''The enforcement mode of the policy assignment.

        :default: "Default"

        Example::

            "DoNotEnforce" - Policy effect is not enforced (audit only)
        '''
        result = self._values.get("enforcement_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def identity(self) -> typing.Optional[PolicyAssignmentIdentity]:
        '''The managed identity associated with the policy assignment Required for policies with deployIfNotExists or modify effects.

        Example::

            {
              type: "SystemAssigned"
            }
        '''
        result = self._values.get("identity")
        return typing.cast(typing.Optional[PolicyAssignmentIdentity], result)

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
        '''Metadata for the policy assignment Used to store additional information like assignedBy, parameterScopes, etc.

        Example::

            {
              assignedBy: "admin@example.com",
              parameterScopes: {}
            }
        '''
        result = self._values.get("metadata")
        return typing.cast(typing.Any, result)

    @builtins.property
    def non_compliance_messages(
        self,
    ) -> typing.Optional[typing.List[PolicyAssignmentNonComplianceMessage]]:
        '''The non-compliance messages for the policy assignment Provides custom messages when resources are non-compliant.

        Example::

            [
              {
                message: "Resource must have the Environment tag"
              }
            ]
        '''
        result = self._values.get("non_compliance_messages")
        return typing.cast(typing.Optional[typing.List[PolicyAssignmentNonComplianceMessage]], result)

    @builtins.property
    def not_scopes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The policy's excluded scopes Resources within these scopes will not be evaluated by the policy.

        Example::

            ["/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/excluded-rg"]
        '''
        result = self._values.get("not_scopes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def parameters(self) -> typing.Any:
        '''Parameters for the policy assignment Provides values for parameters defined in the policy definition.

        Example::

            {
              tagName: {
                value: "Environment"
              },
              tagValue: {
                value: "Production"
              }
            }
        '''
        result = self._values.get("parameters")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PolicyAssignmentProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "PolicyAssignment",
    "PolicyAssignmentBody",
    "PolicyAssignmentIdentity",
    "PolicyAssignmentNonComplianceMessage",
    "PolicyAssignmentProperties",
    "PolicyAssignmentProps",
]

publication.publish()

def _typecheckingstub__b6c3e6215342f45065c68b88b112bc1b9fbcf287c3d80aad8be323d200967981(
    scope_: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    policy_definition_id: builtins.str,
    scope: builtins.str,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    enforcement_mode: typing.Optional[builtins.str] = None,
    identity: typing.Optional[typing.Union[PolicyAssignmentIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Any = None,
    non_compliance_messages: typing.Optional[typing.Sequence[typing.Union[PolicyAssignmentNonComplianceMessage, typing.Dict[builtins.str, typing.Any]]]] = None,
    not_scopes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parameters: typing.Any = None,
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

def _typecheckingstub__2651048ae2c1dffb133469d426738a91f28f456532a1779b9719fe08ac462b53(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4502d939384282498a7a75d3635a53008d6c1bb2b41c82dc3a26122f74cfea27(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b4e38131e2f5d96555cf74d77029408bc15b407ed638a9c60015fe72278054e9(
    *,
    properties: typing.Union[PolicyAssignmentProperties, typing.Dict[builtins.str, typing.Any]],
    identity: typing.Optional[typing.Union[PolicyAssignmentIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2a025cd97ce39cf7e9ae599e81ce348afbfffb044b85709aa8d04e768c11702(
    *,
    type: builtins.str,
    user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13128265132e31e45e79c77f8538f3eeeff8996f50d9b8b47a7291f67b234fc2(
    *,
    message: builtins.str,
    policy_definition_reference_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e6119156b7a32ea4d6553da0e3451d18708a242c5d22d6747cc5191aacd4ca5(
    *,
    policy_definition_id: builtins.str,
    scope: builtins.str,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    enforcement_mode: typing.Optional[builtins.str] = None,
    metadata: typing.Any = None,
    non_compliance_messages: typing.Optional[typing.Sequence[typing.Union[PolicyAssignmentNonComplianceMessage, typing.Dict[builtins.str, typing.Any]]]] = None,
    not_scopes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parameters: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5f4c63cf6d402827fbfc3ab71a25499f8def2702537c51da54dbcfa2ab94dff3(
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
    policy_definition_id: builtins.str,
    scope: builtins.str,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    enforcement_mode: typing.Optional[builtins.str] = None,
    identity: typing.Optional[typing.Union[PolicyAssignmentIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    metadata: typing.Any = None,
    non_compliance_messages: typing.Optional[typing.Sequence[typing.Union[PolicyAssignmentNonComplianceMessage, typing.Dict[builtins.str, typing.Any]]]] = None,
    not_scopes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parameters: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass
