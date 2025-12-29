r'''
# Azure Role Assignment Construct

This module provides a CDK construct for managing Azure Role Assignments using the AZAPI provider. Role assignments grant specific permissions (roles) to security principals (users, groups, service principals, managed identities) at a particular scope (subscription, resource group, or resource).

## Table of Contents

* [Features](#features)
* [Installation](#installation)
* [Basic Usage](#basic-usage)
* [Advanced Usage](#advanced-usage)
* [Properties](#properties)
* [Outputs](#outputs)
* [API Versions](#api-versions)
* [Principal Types](#principal-types)
* [Built-in Roles](#built-in-roles)
* [Best Practices](#best-practices)
* [Examples](#examples)

## Features

* **Version-Aware Resource Management**: Automatic API version resolution with support for explicit version pinning
* **Schema-Driven Validation**: Built-in property validation with comprehensive error messages
* **Principal Types**: Support for User, Group, ServicePrincipal, ForeignGroup, and Device principals
* **Conditional Access (ABAC)**: Attribute-Based Access Control with condition expressions
* **Flexible Scoping**: Assign roles at subscription, resource group, or individual resource scope
* **Delegated Managed Identity**: Support for delegated identity scenarios with group assignments
* **Built-in and Custom Roles**: Works with both Azure built-in roles and custom role definitions
* **JSII Compliance**: Full support for multi-language bindings

## Why Use AZAPI Provider?

The AZAPI provider offers several advantages for managing role assignments:

1. **Latest API Support**: Access to the newest Azure features without waiting for provider updates
2. **Consistent Interface**: Unified approach across all Azure resources
3. **Version Flexibility**: Pin to specific API versions or use latest automatically
4. **Full Feature Coverage**: Support for all Azure properties including preview features
5. **Type Safety**: Strong typing and validation for all resource properties

## Installation

This construct is part of the terraform-cdk-constructs library:

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Basic Usage

### Assign Built-in Reader Role

```python
import { RoleAssignment } from '@microsoft/terraform-cdk-constructs/azure-roleassignment';
import { AzapiProvider } from '@microsoft/terraform-cdk-constructs/core-azure';

// Configure the AZAPI provider
new AzapiProvider(this, 'azapi', {});

// Assign Reader role to a user at subscription scope
const readerAssignment = new RoleAssignment(this, 'reader-assignment', {
  name: 'reader-assignment',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7', // Reader
  principalId: '00000000-0000-0000-0000-000000000000', // User Object ID from Azure AD
  scope: '/subscriptions/00000000-0000-0000-0000-000000000000',
  principalType: 'User',
  description: 'Grants read access to all resources in the subscription',
});
```

### Assign Role to Service Principal

```python
const contributorAssignment = new RoleAssignment(this, 'sp-contributor', {
  name: 'sp-contributor-assignment',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c', // Contributor
  principalId: servicePrincipal.objectId,
  scope: resourceGroup.id,
  principalType: 'ServicePrincipal',
  description: 'Grants contributor access to the application service principal',
});
```

## Advanced Usage

### Conditional Assignment with ABAC

Attribute-Based Access Control (ABAC) allows you to add conditions to role assignments:

```python
// Limit access to specific storage containers
const conditionalAssignment = new RoleAssignment(this, 'conditional-access', {
  name: 'conditional-storage-access',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe', // Storage Blob Data Contributor
  principalId: user.objectId,
  scope: storageAccount.id,
  principalType: 'User',
  condition: "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringEquals 'logs'",
  conditionVersion: '2.0',
  description: 'Grants blob data contributor access only to the logs container',
});
```

### Assign Custom Role Definition

```python
import { RoleDefinition } from '@microsoft/terraform-cdk-constructs/azure-roledefinition';

// Create a custom role definition
const customRole = new RoleDefinition(this, 'custom-role', {
  name: 'vm-operator',
  roleName: 'Virtual Machine Operator',
  description: 'Can start, stop, and restart virtual machines',
  permissions: [{
    actions: [
      'Microsoft.Compute/virtualMachines/start/action',
      'Microsoft.Compute/virtualMachines/restart/action',
      'Microsoft.Compute/virtualMachines/powerOff/action',
      'Microsoft.Compute/virtualMachines/read',
    ],
    notActions: [],
    dataActions: [],
    notDataActions: [],
  }],
  assignableScopes: ['/subscriptions/00000000-0000-0000-0000-000000000000'],
});

// Assign the custom role
new RoleAssignment(this, 'custom-role-assignment', {
  name: 'vm-operator-assignment',
  roleDefinitionId: customRole.id,
  principalId: '00000000-0000-0000-0000-000000000000',
  scope: '/subscriptions/00000000-0000-0000-0000-000000000000',
  principalType: 'User',
  description: 'Assigns custom VM Operator role to user',
});
```

### Group Assignment with Delegated Managed Identity

```python
// Assign role to a group using a delegated managed identity
const groupAssignment = new RoleAssignment(this, 'group-assignment', {
  name: 'group-with-delegated-identity',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7', // Reader
  principalId: group.objectId,
  scope: '/subscriptions/00000000-0000-0000-0000-000000000000',
  principalType: 'Group',
  delegatedManagedIdentityResourceId: '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity',
  description: 'Group assignment using delegated managed identity',
});
```

### Resource Group Scoped Assignment

```python
const rgAssignment = new RoleAssignment(this, 'rg-contributor', {
  name: 'rg-contributor-assignment',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c', // Contributor
  principalId: '00000000-0000-0000-0000-000000000000',
  scope: '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-resource-group',
  principalType: 'User',
  description: 'Grants contributor access only to this resource group',
});
```

### Individual Resource Scoped Assignment

```python
const resourceAssignment = new RoleAssignment(this, 'storage-contributor', {
  name: 'storage-contributor-assignment',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/ba92f5b4-2d11-453d-a403-e96b0029c9fe', // Storage Blob Data Contributor
  principalId: managedIdentity.principalId,
  scope: '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/mystorageaccount',
  principalType: 'ServicePrincipal',
  description: 'Grants blob data contributor access to this specific storage account',
});
```

## Properties

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `roleDefinitionId` | string | The role definition ID to assign (built-in or custom role) |
| `principalId` | string | The Object ID of the principal (user, group, service principal, managed identity) |
| `scope` | string | The scope at which the role is assigned (subscription, resource group, or resource) |

### Optional Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | string | Auto-generated | The name of the role assignment resource |
| `principalType` | string | undefined | Type of principal: User, Group, ServicePrincipal, ForeignGroup, Device |
| `description` | string | undefined | Description of why the assignment was made |
| `condition` | string | undefined | ABAC condition expression to limit access |
| `conditionVersion` | string | undefined | Version of condition syntax (e.g., "2.0") |
| `delegatedManagedIdentityResourceId` | string | undefined | Resource ID of delegated managed identity (for group assignments) |
| `apiVersion` | string | "2022-04-01" | Explicit API version to use |
| `tags` | object | {} | Tags to apply to the role assignment |
| `ignoreChanges` | string[] | [] | Properties to ignore during updates |

## Outputs

The [`RoleAssignment`](lib/role-assignment.ts:188) construct provides the following outputs:

| Output | Type | Description |
|--------|------|-------------|
| `id` | string | The resource ID of the role assignment |
| `name` | string | The name of the role assignment |
| `resourceId` | string | Alias for the id property |
| `roleDefinitionId` | string | The role definition ID that was assigned |
| `principalId` | string | The principal ID that was granted the role |
| `assignmentScope` | string | The scope at which the role was assigned |
| `principalType` | string | undefined | The type of principal (if specified) |

## API Versions

### Supported Versions

| Version | Support Level | Release Date | Notes |
|---------|---------------|--------------|-------|
| [2022-04-01](lib/role-assignment-schemas.ts:145) | Active (Latest) | 2022-04-01 | Full support for ABAC conditional assignments and delegated managed identities |

### Version Selection

```python
// Use latest version (default)
new RoleAssignment(this, 'assignment', {
  roleDefinitionId: '...',
  principalId: '...',
  scope: '...',
});

// Pin to specific version
new RoleAssignment(this, 'assignment', {
  roleDefinitionId: '...',
  principalId: '...',
  scope: '...',
  apiVersion: '2022-04-01',
});
```

## Principal Types

### User

An Azure AD user account.

```python
principalType: 'User'
```

### Group

An Azure AD group. Can be used with delegated managed identity.

```python
principalType: 'Group'
```

### ServicePrincipal

An application or service principal (including managed identities).

```python
principalType: 'ServicePrincipal'
```

### ForeignGroup

A group from an external directory (B2B collaboration).

```python
principalType: 'ForeignGroup'
```

### Device

A device identity from Azure AD.

```python
principalType: 'Device'
```

## Built-in Roles

### Common Built-in Role Definition IDs

| Role Name | Role ID | Description |
|-----------|---------|-------------|
| Owner | `8e3af657-a8ff-443c-a75c-2fe8c4bcb635` | Full access to all resources including the ability to assign roles |
| Contributor | `b24988ac-6180-42a0-ab88-20f7382dd24c` | Full access to all resources but cannot assign roles |
| Reader | `acdd72a7-3385-48ef-bd42-f606fba81ae7` | View all resources but cannot make changes |
| User Access Administrator | `18d7d88d-d35e-4fb5-a5c3-7773c20a72d9` | Manage user access to Azure resources |
| Storage Blob Data Contributor | `ba92f5b4-2d11-453d-a403-e96b0029c9fe` | Read, write, and delete Azure Storage containers and blobs |
| Storage Blob Data Reader | `2a2b9908-6ea1-4ae2-8e65-a410df84e7d1` | Read Azure Storage containers and blobs |
| Key Vault Secrets User | `4633458b-17de-408a-b874-0445c86b69e6` | Read secret contents from Key Vault |
| Virtual Machine Contributor | `9980e02c-c2be-4d73-94e8-173b1dc7cf3c` | Manage virtual machines but not the virtual network or storage account they're connected to |

For a complete list, see [Azure Built-in Roles](https://docs.microsoft.com/azure/role-based-access-control/built-in-roles).

## Best Practices

### 1. Principle of Least Privilege

Always assign the minimum permissions required:

```python
// ❌ Bad: Overly permissive
roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635' // Owner

// ✅ Good: Specific permissions
roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7' // Reader
```

### 2. Specific Scopes

Assign roles at the narrowest scope possible:

```python
// ❌ Bad: Subscription-wide access when not needed
scope: '/subscriptions/00000000-0000-0000-0000-000000000000'

// ✅ Good: Resource group or resource-specific
scope: '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg'
```

### 3. Always Specify Principal Type

Improves performance and clarity:

```python
// ✅ Good
new RoleAssignment(this, 'assignment', {
  // ...
  principalType: 'ServicePrincipal',  // Explicit type
});
```

### 4. Use Conditional Access When Appropriate

Limit access further with ABAC conditions:

```python
new RoleAssignment(this, 'conditional', {
  // ...
  condition: "@Resource[Microsoft.Storage/storageAccounts:name] StringStartsWith 'prod'",
  conditionVersion: '2.0',
});
```

### 5. Document Assignments

Use descriptions to explain why assignments exist:

```python
new RoleAssignment(this, 'assignment', {
  // ...
  description: 'Grants read access to monitoring team for incident response. Approved by Security-12345.',
});
```

### 6. Prefer Custom Roles

Create custom roles for specific needs instead of using broad built-in roles:

```python
// Create custom role with exact permissions needed
const customRole = new RoleDefinition(this, 'custom', {
  roleName: 'Specific Task Operator',
  permissions: [/* only required actions */],
  assignableScopes: [/* specific scopes */],
});
```

### 7. Use Managed Identities

Prefer managed identities over service principals:

```python
// ✅ Good: System-assigned managed identity
principalId: virtualMachine.identity.principalId,
principalType: 'ServicePrincipal',
```

### 8. Regular Audits

Periodically review and remove unnecessary role assignments. Use tags to track:

```python
new RoleAssignment(this, 'assignment', {
  // ...
  tags: {
    owner: 'team-name',
    purpose: 'data-processing',
    reviewDate: '2024-12-31',
  },
});
```

## Examples

### Example 1: Multi-Region Monitoring Setup

```python
const regions = ['eastus', 'westus', 'northeurope'];

regions.forEach(region => {
  new RoleAssignment(this, `monitoring-${region}`, {
    name: `monitoring-reader-${region}`,
    roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/43d0d8ad-25c7-4714-9337-8ba259a9fe05', // Monitoring Reader
    principalId: monitoringServicePrincipal.objectId,
    scope: `/subscriptions/${subscriptionId}/resourceGroups/rg-${region}`,
    principalType: 'ServicePrincipal',
    description: `Monitoring access for ${region} resources`,
    tags: {
      region,
      purpose: 'monitoring',
    },
  });
});
```

### Example 2: Separation of Duties

```python
// Development team: Contributor at resource group level
new RoleAssignment(this, 'dev-team-contributor', {
  name: 'dev-team-rg-contributor',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c',
  principalId: devTeamGroup.objectId,
  scope: devResourceGroup.id,
  principalType: 'Group',
  description: 'Development team can manage resources in dev environment',
});

// Operations team: Reader at subscription, Contributor at production RG
new RoleAssignment(this, 'ops-team-reader', {
  name: 'ops-team-subscription-reader',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7',
  principalId: opsTeamGroup.objectId,
  scope: `/subscriptions/${subscriptionId}`,
  principalType: 'Group',
  description: 'Operations team can view all resources',
});

new RoleAssignment(this, 'ops-team-contributor', {
  name: 'ops-team-prod-contributor',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c',
  principalId: opsTeamGroup.objectId,
  scope: prodResourceGroup.id,
  principalType: 'Group',
  description: 'Operations team can manage production resources',
});
```

### Example 3: Temporary Access

```python
// Grant temporary elevated access (remember to remove after use)
new RoleAssignment(this, 'temp-access', {
  name: 'temp-contributor-access',
  roleDefinitionId: '/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c',
  principalId: contractor.objectId,
  scope: temporaryResourceGroup.id,
  principalType: 'User',
  description: 'Temporary access for migration project. Remove after 2024-06-30.',
  tags: {
    temporary: 'true',
    expiryDate: '2024-06-30',
    ticketNumber: 'PROJ-12345',
  },
});
```

## Relationship with Role Definition

Role assignments and role definitions work together to implement Azure RBAC:

* **Role Definition**: Defines WHAT permissions are granted (actions, dataActions, etc.)
* **Role Assignment**: Defines WHO gets those permissions and WHERE (scope)

```python
import { RoleDefinition } from '@microsoft/terraform-cdk-constructs/azure-roledefinition';
import { RoleAssignment } from '@microsoft/terraform-cdk-constructs/azure-roleassignment';

// Step 1: Define what permissions are needed
const customRole = new RoleDefinition(this, 'data-processor-role', {
  name: 'data-processor',
  roleName: 'Data Processor',
  permissions: [{
    actions: ['Microsoft.Storage/storageAccounts/blobServices/containers/read'],
    dataActions: [
      'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read',
      'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write',
    ],
  }],
  assignableScopes: ['/subscriptions/00000000-0000-0000-0000-000000000000'],
});

// Step 2: Assign those permissions to a principal
new RoleAssignment(this, 'processor-assignment', {
  name: 'data-processor-assignment',
  roleDefinitionId: customRole.id,
  principalId: dataProcessorApp.principalId,
  scope: storageAccount.id,
  principalType: 'ServicePrincipal',
  description: 'Grants data processing application access to storage',
});
```

## Additional Resources

* [Azure RBAC Documentation](https://docs.microsoft.com/azure/role-based-access-control/)
* [Azure Built-in Roles](https://docs.microsoft.com/azure/role-based-access-control/built-in-roles)
* [Azure ABAC Conditions](https://docs.microsoft.com/azure/role-based-access-control/conditions-overview)
* [Best Practices for Azure RBAC](https://docs.microsoft.com/azure/role-based-access-control/best-practices)
* [Azure Role Assignments REST API](https://docs.microsoft.com/rest/api/authorization/role-assignments)
* [Managed Identities for Azure Resources](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)

## License

This module is part of the terraform-cdk-constructs project and is licensed under the MIT License.
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


class RoleAssignment(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roleassignment.RoleAssignment",
):
    '''Unified Azure Role Assignment implementation.

    This class provides a single, version-aware implementation for managing Azure
    Role Assignments. It automatically handles version resolution, schema validation,
    and property transformation.

    **Important Notes:**

    - Role assignments are scoped resources deployed at subscription, resource group,
      or resource level. They do not have a location property as they are not region-specific.
    - The ``name`` property (inherited from AzapiResourceProps) is not used. Azure automatically
      generates a deterministic GUID for role assignment names based on the deployment context.
      This ensures idempotent deployments without duplicate role assignments.

    Example::

        Conditional assignment with ABAC - Limit access to specific storage containers
        
        const assignment = new RoleAssignment(this, "conditional-assignment", {
          roleDefinitionId: storageRole.id,
          principalId: user.objectId,
          scope: storageAccount.id,
          principalType: "User",
          condition: "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringEquals 'logs'",
          conditionVersion: "2.0",
          description: "Grants access only to the logs container",
        });
    '''

    def __init__(
        self,
        scope_: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        principal_id: builtins.str,
        role_definition_id: builtins.str,
        scope: builtins.str,
        condition: typing.Optional[builtins.str] = None,
        condition_version: typing.Optional[builtins.str] = None,
        delegated_managed_identity_resource_id: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        principal_type: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Role Assignment using the VersionedAzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope_: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param principal_id: The principal ID (object ID) to which the role is assigned This can be a user, group, service principal, or managed identity Required property.
        :param role_definition_id: The role definition ID to assign This can be a built-in or custom role definition Required property.
        :param scope: The scope at which the role assignment is applied Can be a subscription, resource group, or resource Required property.
        :param condition: The conditions on the role assignment Limits the resources it applies to using ABAC expressions Requires conditionVersion to be set when used.
        :param condition_version: Version of the condition syntax Required when condition is specified. Default: undefined
        :param delegated_managed_identity_resource_id: The delegated Azure Resource Id which contains a Managed Identity Applicable only when the principalType is Group Used for scenarios where a group assignment should use a specific managed identity.
        :param description: The role assignment description Provides detailed information about why the assignment was made.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param principal_type: The type of principal Specifies what kind of identity is being assigned the role. Default: undefined (Azure will auto-detect)
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
            type_hints = typing.get_type_hints(_typecheckingstub__1da60cb3330a3d0b7dc41016fb5241f0754043f822a8a8dc33ceccf08392e271)
            check_type(argname="argument scope_", value=scope_, expected_type=type_hints["scope_"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = RoleAssignmentProps(
            principal_id=principal_id,
            role_definition_id=role_definition_id,
            scope=scope,
            condition=condition,
            condition_version=condition_version,
            delegated_managed_identity_resource_id=delegated_managed_identity_resource_id,
            description=description,
            ignore_changes=ignore_changes,
            principal_type=principal_type,
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
        '''Creates the resource body for the Azure API call Transforms the input properties into the JSON format expected by Azure REST API  Note: Role assignments do not have a location property as they are scoped resources (subscription, resource group, or resource level).

        The scope property is NOT included in the body as it's read-only and
        automatically derived from the parentId.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bf94ff9ec9077d888ae9e0a0b61acfd7123cffee63d4df06546c6077c61398e3)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveName")
    def _resolve_name(
        self,
        *,
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
    ) -> builtins.str:
        '''Overrides the name resolution to generate deterministic GUIDs for role assignments.

        Role assignments require GUID format IDs. This implementation generates a deterministic
        UUID based on the role assignment's key properties to ensure:

        - Same GUID is generated on re-deployments with same parameters
        - Idempotent deployments (no duplicate role assignments)
        - Consistent behavior across deployment runs

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
        props = _AzapiResourceProps_141a2340(
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

        return typing.cast(builtins.str, jsii.invoke(self, "resolveName", [props]))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Overrides parent ID resolution to use the scope from props Role assignments are scoped resources where the scope IS the parent.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a8386d57aacafb67caf09dfc3560a7fe9f69865994251a32150204ab269495f7)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Role Assignments.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="assignmentScope")
    def assignment_scope(self) -> builtins.str:
        '''Get the scope of this role assignment.'''
        return typing.cast(builtins.str, jsii.get(self, "assignmentScope"))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="principalId")
    def principal_id(self) -> builtins.str:
        '''Get the principal ID that was granted this role.'''
        return typing.cast(builtins.str, jsii.get(self, "principalId"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "RoleAssignmentProps":
        '''The input properties for this Role Assignment instance.'''
        return typing.cast("RoleAssignmentProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="roleDefinitionId")
    def role_definition_id(self) -> builtins.str:
        '''Get the role definition ID this assignment references.'''
        return typing.cast(builtins.str, jsii.get(self, "roleDefinitionId"))

    @builtins.property
    @jsii.member(jsii_name="principalType")
    def principal_type(self) -> typing.Optional[builtins.str]:
        '''Get the principal type.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "principalType"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roleassignment.RoleAssignmentBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class RoleAssignmentBody:
    def __init__(
        self,
        *,
        properties: typing.Union["RoleAssignmentProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Role Assignment API calls This matches the Azure REST API schema for role assignments.

        :param properties: The properties of the role assignment.
        '''
        if isinstance(properties, dict):
            properties = RoleAssignmentProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__021512c25fea6cfbd0c472677bf6c035731d283f50156efd8bb3776441553538)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "RoleAssignmentProperties":
        '''The properties of the role assignment.'''
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("RoleAssignmentProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleAssignmentBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roleassignment.RoleAssignmentProperties",
    jsii_struct_bases=[],
    name_mapping={
        "principal_id": "principalId",
        "role_definition_id": "roleDefinitionId",
        "scope": "scope",
        "condition": "condition",
        "condition_version": "conditionVersion",
        "delegated_managed_identity_resource_id": "delegatedManagedIdentityResourceId",
        "description": "description",
        "principal_type": "principalType",
    },
)
class RoleAssignmentProperties:
    def __init__(
        self,
        *,
        principal_id: builtins.str,
        role_definition_id: builtins.str,
        scope: builtins.str,
        condition: typing.Optional[builtins.str] = None,
        condition_version: typing.Optional[builtins.str] = None,
        delegated_managed_identity_resource_id: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        principal_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties interface for Azure Role Assignment This is required for JSII compliance to support multi-language code generation.

        :param principal_id: The principal ID.
        :param role_definition_id: The role definition ID.
        :param scope: The scope of the role assignment.
        :param condition: The conditions on the role assignment.
        :param condition_version: Version of the condition syntax.
        :param delegated_managed_identity_resource_id: The delegated managed identity resource ID.
        :param description: The role assignment description.
        :param principal_type: The type of principal.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__82106c1931b1c4a76126d2b820e5048900dcb85f22b9b551372346771508a9b6)
            check_type(argname="argument principal_id", value=principal_id, expected_type=type_hints["principal_id"])
            check_type(argname="argument role_definition_id", value=role_definition_id, expected_type=type_hints["role_definition_id"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument condition", value=condition, expected_type=type_hints["condition"])
            check_type(argname="argument condition_version", value=condition_version, expected_type=type_hints["condition_version"])
            check_type(argname="argument delegated_managed_identity_resource_id", value=delegated_managed_identity_resource_id, expected_type=type_hints["delegated_managed_identity_resource_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument principal_type", value=principal_type, expected_type=type_hints["principal_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "principal_id": principal_id,
            "role_definition_id": role_definition_id,
            "scope": scope,
        }
        if condition is not None:
            self._values["condition"] = condition
        if condition_version is not None:
            self._values["condition_version"] = condition_version
        if delegated_managed_identity_resource_id is not None:
            self._values["delegated_managed_identity_resource_id"] = delegated_managed_identity_resource_id
        if description is not None:
            self._values["description"] = description
        if principal_type is not None:
            self._values["principal_type"] = principal_type

    @builtins.property
    def principal_id(self) -> builtins.str:
        '''The principal ID.'''
        result = self._values.get("principal_id")
        assert result is not None, "Required property 'principal_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_definition_id(self) -> builtins.str:
        '''The role definition ID.'''
        result = self._values.get("role_definition_id")
        assert result is not None, "Required property 'role_definition_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scope(self) -> builtins.str:
        '''The scope of the role assignment.'''
        result = self._values.get("scope")
        assert result is not None, "Required property 'scope' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def condition(self) -> typing.Optional[builtins.str]:
        '''The conditions on the role assignment.'''
        result = self._values.get("condition")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def condition_version(self) -> typing.Optional[builtins.str]:
        '''Version of the condition syntax.'''
        result = self._values.get("condition_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delegated_managed_identity_resource_id(self) -> typing.Optional[builtins.str]:
        '''The delegated managed identity resource ID.'''
        result = self._values.get("delegated_managed_identity_resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The role assignment description.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def principal_type(self) -> typing.Optional[builtins.str]:
        '''The type of principal.'''
        result = self._values.get("principal_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleAssignmentProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roleassignment.RoleAssignmentProps",
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
        "principal_id": "principalId",
        "role_definition_id": "roleDefinitionId",
        "scope": "scope",
        "condition": "condition",
        "condition_version": "conditionVersion",
        "delegated_managed_identity_resource_id": "delegatedManagedIdentityResourceId",
        "description": "description",
        "ignore_changes": "ignoreChanges",
        "principal_type": "principalType",
    },
)
class RoleAssignmentProps(_AzapiResourceProps_141a2340):
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
        principal_id: builtins.str,
        role_definition_id: builtins.str,
        scope: builtins.str,
        condition: typing.Optional[builtins.str] = None,
        condition_version: typing.Optional[builtins.str] = None,
        delegated_managed_identity_resource_id: typing.Optional[builtins.str] = None,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        principal_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Role Assignment.

        Extends AzapiResourceProps with Role Assignment specific properties.

        **Note on the ``name`` property:** While this interface inherits the ``name`` property
        from AzapiResourceProps, it is not used for role assignments. Azure role assignments
        require GUID format names, which are automatically generated by the construct.
        Any user-provided name value will be ignored in favor of Azure's deterministic
        GUID generation based on the deployment context.

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
        :param principal_id: The principal ID (object ID) to which the role is assigned This can be a user, group, service principal, or managed identity Required property.
        :param role_definition_id: The role definition ID to assign This can be a built-in or custom role definition Required property.
        :param scope: The scope at which the role assignment is applied Can be a subscription, resource group, or resource Required property.
        :param condition: The conditions on the role assignment Limits the resources it applies to using ABAC expressions Requires conditionVersion to be set when used.
        :param condition_version: Version of the condition syntax Required when condition is specified. Default: undefined
        :param delegated_managed_identity_resource_id: The delegated Azure Resource Id which contains a Managed Identity Applicable only when the principalType is Group Used for scenarios where a group assignment should use a specific managed identity.
        :param description: The role assignment description Provides detailed information about why the assignment was made.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param principal_type: The type of principal Specifies what kind of identity is being assigned the role. Default: undefined (Azure will auto-detect)
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__910942308b6409a1928584d46407d03271dc4eff41a246d3366001aedceb85e7)
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
            check_type(argname="argument principal_id", value=principal_id, expected_type=type_hints["principal_id"])
            check_type(argname="argument role_definition_id", value=role_definition_id, expected_type=type_hints["role_definition_id"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument condition", value=condition, expected_type=type_hints["condition"])
            check_type(argname="argument condition_version", value=condition_version, expected_type=type_hints["condition_version"])
            check_type(argname="argument delegated_managed_identity_resource_id", value=delegated_managed_identity_resource_id, expected_type=type_hints["delegated_managed_identity_resource_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument principal_type", value=principal_type, expected_type=type_hints["principal_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "principal_id": principal_id,
            "role_definition_id": role_definition_id,
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
        if condition is not None:
            self._values["condition"] = condition
        if condition_version is not None:
            self._values["condition_version"] = condition_version
        if delegated_managed_identity_resource_id is not None:
            self._values["delegated_managed_identity_resource_id"] = delegated_managed_identity_resource_id
        if description is not None:
            self._values["description"] = description
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if principal_type is not None:
            self._values["principal_type"] = principal_type

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
    def principal_id(self) -> builtins.str:
        '''The principal ID (object ID) to which the role is assigned This can be a user, group, service principal, or managed identity Required property.

        Example::

            "00000000-0000-0000-0000-000000000000"
        '''
        result = self._values.get("principal_id")
        assert result is not None, "Required property 'principal_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_definition_id(self) -> builtins.str:
        '''The role definition ID to assign This can be a built-in or custom role definition Required property.

        Example::

            "/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c" (Contributor)
        '''
        result = self._values.get("role_definition_id")
        assert result is not None, "Required property 'role_definition_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scope(self) -> builtins.str:
        '''The scope at which the role assignment is applied Can be a subscription, resource group, or resource Required property.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-name/providers/Microsoft.Storage/storageAccounts/storage-name"
        '''
        result = self._values.get("scope")
        assert result is not None, "Required property 'scope' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def condition(self) -> typing.Optional[builtins.str]:
        '''The conditions on the role assignment Limits the resources it applies to using ABAC expressions Requires conditionVersion to be set when used.

        Example::

            "@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringEquals 'logs'"
        '''
        result = self._values.get("condition")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def condition_version(self) -> typing.Optional[builtins.str]:
        '''Version of the condition syntax Required when condition is specified.

        :default: undefined

        Example::

            "2.0"
        '''
        result = self._values.get("condition_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delegated_managed_identity_resource_id(self) -> typing.Optional[builtins.str]:
        '''The delegated Azure Resource Id which contains a Managed Identity Applicable only when the principalType is Group Used for scenarios where a group assignment should use a specific managed identity.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/identity"
        '''
        result = self._values.get("delegated_managed_identity_resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The role assignment description Provides detailed information about why the assignment was made.

        Example::

            "Grants read access to monitoring team for resource diagnostics"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["description"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def principal_type(self) -> typing.Optional[builtins.str]:
        '''The type of principal Specifies what kind of identity is being assigned the role.

        :default: undefined (Azure will auto-detect)

        Example::

            "Device" - A device identity
        '''
        result = self._values.get("principal_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleAssignmentProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "RoleAssignment",
    "RoleAssignmentBody",
    "RoleAssignmentProperties",
    "RoleAssignmentProps",
]

publication.publish()

def _typecheckingstub__1da60cb3330a3d0b7dc41016fb5241f0754043f822a8a8dc33ceccf08392e271(
    scope_: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    principal_id: builtins.str,
    role_definition_id: builtins.str,
    scope: builtins.str,
    condition: typing.Optional[builtins.str] = None,
    condition_version: typing.Optional[builtins.str] = None,
    delegated_managed_identity_resource_id: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    principal_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__bf94ff9ec9077d888ae9e0a0b61acfd7123cffee63d4df06546c6077c61398e3(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a8386d57aacafb67caf09dfc3560a7fe9f69865994251a32150204ab269495f7(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__021512c25fea6cfbd0c472677bf6c035731d283f50156efd8bb3776441553538(
    *,
    properties: typing.Union[RoleAssignmentProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82106c1931b1c4a76126d2b820e5048900dcb85f22b9b551372346771508a9b6(
    *,
    principal_id: builtins.str,
    role_definition_id: builtins.str,
    scope: builtins.str,
    condition: typing.Optional[builtins.str] = None,
    condition_version: typing.Optional[builtins.str] = None,
    delegated_managed_identity_resource_id: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    principal_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__910942308b6409a1928584d46407d03271dc4eff41a246d3366001aedceb85e7(
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
    principal_id: builtins.str,
    role_definition_id: builtins.str,
    scope: builtins.str,
    condition: typing.Optional[builtins.str] = None,
    condition_version: typing.Optional[builtins.str] = None,
    delegated_managed_identity_resource_id: typing.Optional[builtins.str] = None,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    principal_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
