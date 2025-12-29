r'''
# Azure Role Definition Construct

This module provides a CDK for Terraform (CDKTF) construct for managing Azure RBAC Role Definitions using the AZAPI provider. Role definitions define custom roles with specific permissions that can be assigned to users, groups, or service principals through role assignments.

## Features

* **Version-Aware Schema Management**: Automatic handling of API version resolution and schema validation
* **Custom RBAC Roles**: Define custom roles with granular permissions
* **Control Plane Actions**: Specify allowed and denied management operations
* **Data Plane Actions**: Define permissions for data operations within resources
* **Flexible Scoping**: Assign roles at subscription, resource group, or management group level
* **Type Safety**: Full TypeScript support with comprehensive type definitions
* **JSII Compliance**: Multi-language support (TypeScript, Python, Java, C#, Go)

## AZAPI Provider Benefits

This construct uses the AZAPI provider, which offers several advantages:

* **Day-0 Support**: Access to new Azure features immediately upon release
* **Consistent API**: Direct mapping to Azure REST API structure
* **Reduced Complexity**: No need to wait for provider updates
* **Better Compatibility**: Works seamlessly with the latest Azure features

## Installation

```bash
npm install @cdktf/terraform-cdk-constructs
```

## Supported API Versions

| API Version | Support Level | Release Date | Status |
|-------------|---------------|--------------|--------|
| 2022-04-01  | Active        | 2022-04-01   | Latest |

## Basic Usage

### Create a Simple Read-Only Role

```python
import { RoleDefinition } from "@cdktf/terraform-cdk-constructs/azure-roledefinition";

const vmReaderRole = new RoleDefinition(this, "vm-reader", {
  name: "vm-reader-role",
  roleName: "Virtual Machine Reader",
  description: "Can view virtual machines and their properties",
  permissions: [
    {
      actions: [
        "Microsoft.Compute/virtualMachines/read",
        "Microsoft.Compute/virtualMachines/instanceView/read",
        "Microsoft.Network/networkInterfaces/read"
      ]
    }
  ],
  assignableScopes: [
    "/subscriptions/00000000-0000-0000-0000-000000000000"
  ]
});
```

## Advanced Features

### Role with Data Plane Permissions

Create a role with both control plane and data plane permissions for comprehensive access management:

```python
const storageOperator = new RoleDefinition(this, "storage-operator", {
  name: "storage-operator-role",
  roleName: "Storage Operator",
  description: "Can manage storage accounts and read/write blob data",
  permissions: [
    {
      // Control plane actions - manage storage accounts
      actions: [
        "Microsoft.Storage/storageAccounts/read",
        "Microsoft.Storage/storageAccounts/write",
        "Microsoft.Storage/storageAccounts/listkeys/action"
      ],
      // Explicitly deny delete operations
      notActions: [
        "Microsoft.Storage/storageAccounts/delete"
      ],
      // Data plane actions - read and write blobs
      dataActions: [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"
      ],
      // Explicitly deny delete operations on data plane
      notDataActions: [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete"
      ]
    }
  ],
  assignableScopes: [
    "/subscriptions/00000000-0000-0000-0000-000000000000"
  ]
});
```

### Multiple Assignable Scopes

Define a role that can be assigned at multiple levels:

```python
const multiScopeRole = new RoleDefinition(this, "multi-scope", {
  name: "multi-scope-role",
  roleName: "Multi-Scope Operator",
  description: "Can be assigned at subscription, resource group, or management group level",
  permissions: [
    {
      actions: [
        "Microsoft.Resources/subscriptions/read",
        "Microsoft.Resources/subscriptions/resourceGroups/read"
      ]
    }
  ],
  assignableScopes: [
    "/subscriptions/00000000-0000-0000-0000-000000000000",
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg1",
    "/providers/Microsoft.Management/managementGroups/mg1"
  ]
});
```

### Complex Permission Combinations

Create sophisticated roles with multiple permission objects:

```python
const complexRole = new RoleDefinition(this, "complex-role", {
  name: "complex-role",
  roleName: "Complex Operator Role",
  description: "Role with multiple permission sets",
  permissions: [
    {
      // Compute permissions
      actions: ["Microsoft.Compute/virtualMachines/read"],
      notActions: []
    },
    {
      // Storage permissions
      actions: ["Microsoft.Storage/storageAccounts/read"],
      dataActions: [
        "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
      ]
    },
    {
      // Network permissions
      actions: [
        "Microsoft.Network/virtualNetworks/read",
        "Microsoft.Network/networkInterfaces/read"
      ]
    }
  ],
  assignableScopes: [
    "/subscriptions/00000000-0000-0000-0000-000000000000"
  ]
});
```

## Properties

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `roleName` | string | Display name of the role (1-128 characters) |
| `permissions` | RoleDefinitionPermission[] | Array of permission objects defining role capabilities |
| `assignableScopes` | string[] | Scopes where the role can be assigned |

### Optional Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | string | Auto-generated | Resource name for the role definition |
| `description` | string | - | Detailed description of the role (max 1024 characters) |
| `type` | string | "CustomRole" | Role type (CustomRole or BuiltInRole) |
| `apiVersion` | string | "2022-04-01" | Azure API version to use |
| `ignoreChanges` | string[] | - | Properties to ignore during updates |

### Permission Object Structure

```python
interface RoleDefinitionPermission {
  actions?: string[];        // Control plane allowed actions
  notActions?: string[];     // Control plane denied actions
  dataActions?: string[];    // Data plane allowed actions
  notDataActions?: string[]; // Data plane denied actions
}
```

## Available Outputs

The RoleDefinition construct exposes these outputs:

* `id`: Full resource ID of the role definition
* `name`: Name of the role definition
* `resourceId`: Alias for id (for use in other resources)
* `roleName`: Display name of the role
* `roleType`: Type of role (CustomRole or BuiltInRole)

## Common Permission Patterns

### Reader Pattern

```python
permissions: [{
  actions: ["Microsoft.Resources/subscriptions/read"]
}]
```

### Contributor Pattern

```python
permissions: [{
  actions: ["*"],
  notActions: [
    "Microsoft.Authorization/roleAssignments/write",
    "Microsoft.Authorization/roleAssignments/delete"
  ]
}]
```

### Service-Specific Reader

```python
permissions: [{
  actions: [
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/disks/read",
    "Microsoft.Compute/snapshots/read"
  ]
}]
```

### Data Plane Access

```python
permissions: [{
  dataActions: [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"
  ]
}]
```

## Relationship with Role Assignment

After creating a Role Definition, use the RoleAssignment service to assign the role to principals:

```python
import { RoleDefinition } from "@cdktf/terraform-cdk-constructs/azure-roledefinition";
import { RoleAssignment } from "@cdktf/terraform-cdk-constructs/azure-roleassignment";

// Create custom role
const customRole = new RoleDefinition(this, "custom-role", {
  roleName: "Custom Operator",
  permissions: [
    {
      actions: ["Microsoft.Compute/virtualMachines/read"]
    }
  ],
  assignableScopes: [
    "/subscriptions/00000000-0000-0000-0000-000000000000"
  ]
});

// Assign the role to a principal (user, group, or service principal)
const assignment = new RoleAssignment(this, "role-assignment", {
  name: "custom-role-assignment",
  roleDefinitionId: customRole.id,
  principalId: "00000000-0000-0000-0000-000000000000", // User/Group/SP Object ID
  scope: "/subscriptions/00000000-0000-0000-0000-000000000000"
});
```

## Best Practices

### 1. Principle of Least Privilege

Grant only the minimum permissions required for the role's purpose:

```python
// Good: Specific permissions
permissions: [{
  actions: [
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Compute/virtualMachines/start/action"
  ]
}]

// Avoid: Overly broad permissions
permissions: [{
  actions: ["*"]
}]
```

### 2. Use NotActions Carefully

NotActions exclude permissions from a broader grant. Use them to create exceptions:

```python
permissions: [{
  actions: ["Microsoft.Compute/virtualMachines/*"],
  notActions: [
    "Microsoft.Compute/virtualMachines/delete",
    "Microsoft.Compute/virtualMachines/write"
  ]
}]
```

### 3. Document Role Purpose

Provide clear descriptions:

```python
const role = new RoleDefinition(this, "role", {
  roleName: "VM Operator",
  description: "Can start, stop, and restart VMs. Cannot create, modify, or delete VMs. Intended for operations team.",
  // ...
});
```

### 4. Scope Appropriately

Limit assignable scopes to only where needed:

```python
// Good: Limited to specific resource group
assignableScopes: [
  "/subscriptions/sub-id/resourceGroups/production-vms"
]

// Avoid: Too broad if not necessary
assignableScopes: [
  "/subscriptions/sub-id"
]
```

### 5. Separate Control and Data Plane

Understand the difference between actions and dataActions:

```python
permissions: [{
  // Control plane: Manage the resource itself
  actions: ["Microsoft.Storage/storageAccounts/read"],

  // Data plane: Access data within the resource
  dataActions: [
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
  ]
}]
```

### 6. Test Permissions

Always test that the role grants the intended access and nothing more:

1. Assign the role to a test principal
2. Verify the principal can perform allowed actions
3. Verify the principal cannot perform denied actions
4. Check at all intended assignable scopes

## Understanding Actions

### Wildcard Usage

* `*`: All actions
* `Microsoft.Compute/*`: All actions in Compute resource provider
* `Microsoft.Compute/virtualMachines/*`: All actions on VMs

### Action Format

Actions follow the pattern: `{Provider}/{ResourceType}/{Operation}`

Examples:

* `Microsoft.Compute/virtualMachines/read`
* `Microsoft.Network/virtualNetworks/write`
* `Microsoft.Storage/storageAccounts/listkeys/action`

### Control Plane vs Data Plane

* **Control Plane (actions)**: Manage Azure resources

  * Example: Create VM, delete storage account
* **Data Plane (dataActions)**: Access data in resources

  * Example: Read blob, write to queue

## Migration Notes

This implementation uses the AZAPI provider with version-aware schema management. When migrating from other implementations:

1. Role definitions are subscription or management group scoped (no location property)
2. Use the `permissions` array to define role capabilities
3. Specify `assignableScopes` to control where the role can be assigned
4. The construct automatically resolves to the latest API version unless pinned

## Troubleshooting

### Role Not Appearing in Portal

* Wait a few minutes for replication
* Check that you're viewing the correct subscription/scope
* Verify the role was created successfully via API

### Permission Denied When Using Role

* Check that the role includes the required actions
* Verify the assignable scopes include the target scope
* Ensure the role has been assigned to the principal

### Role Cannot Be Deleted

* Check if any role assignments reference this role definition
* Remove all assignments before deleting the definition

## Additional Resources

* [Azure RBAC Documentation](https://docs.microsoft.com/azure/role-based-access-control/)
* [Azure Resource Provider Operations](https://docs.microsoft.com/azure/role-based-access-control/resource-provider-operations)
* [AZAPI Provider Documentation](https://registry.terraform.io/providers/Azure/azapi/latest/docs)
* [Custom Roles in Azure](https://docs.microsoft.com/azure/role-based-access-control/custom-roles)
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


class RoleDefinition(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roledefinition.RoleDefinition",
):
    '''Unified Azure Role Definition implementation.

    This class provides a single, version-aware implementation for managing Azure
    Role Definitions. It automatically handles version resolution, schema validation,
    and property transformation.

    Note: Role definitions are tenant-specific resources deployed at subscription or
    management group scope. Unlike most Azure resources, they do not have a location
    property as they are not region-specific.

    Example::

        Basic custom role definition for read-only access to compute resources
        
        Advanced features like data plane actions and complex permissions are supported
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        assignable_scopes: typing.Sequence[builtins.str],
        permissions: typing.Sequence[typing.Union["RoleDefinitionPermission", typing.Dict[builtins.str, typing.Any]]],
        role_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        type: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Role Definition using the VersionedAzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param assignable_scopes: An array of scopes where this role can be assigned Can include subscription, resource group, or management group scopes Required property.
        :param permissions: An array of permissions objects that define what actions the role can perform Required property.
        :param role_name: The name of the role definition This is the display name shown in the Azure portal Required property.
        :param description: The role definition description Provides detailed information about what the role allows.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param type: The type of role definition. Default: "CustomRole"
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
            type_hints = typing.get_type_hints(_typecheckingstub__2fef2b822ec6c9c4f11fe52cc2c69e592b1af1da2e1fd4477d8ef9eba048817b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = RoleDefinitionProps(
            assignable_scopes=assignable_scopes,
            permissions=permissions,
            role_name=role_name,
            description=description,
            ignore_changes=ignore_changes,
            type=type,
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

        Note: Role definitions do not have a location property as they are
        tenant-specific resources deployed at subscription or management group scope.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cf0d4e21c9ac4678b576f5d4474c0559e5c29bcf7ea68bd8f6cd878e80b87c94)
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
        '''Overrides the name resolution to generate deterministic GUIDs for role definitions.

        Role definitions require GUID format IDs. This implementation generates a deterministic
        UUID based on the role definition's key properties to ensure:

        - Same GUID is generated on re-deployments with same parameters
        - Idempotent deployments (no duplicate role definitions)
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

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Role Definitions.'''
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
    def props(self) -> "RoleDefinitionProps":
        '''The input properties for this Role Definition instance.'''
        return typing.cast("RoleDefinitionProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Get the full resource identifier for use in other Azure resources Alias for the id property.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="roleName")
    def role_name(self) -> builtins.str:
        '''Get the role name.'''
        return typing.cast(builtins.str, jsii.get(self, "roleName"))

    @builtins.property
    @jsii.member(jsii_name="roleType")
    def role_type(self) -> builtins.str:
        '''Get the role type.'''
        return typing.cast(builtins.str, jsii.get(self, "roleType"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roledefinition.RoleDefinitionBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class RoleDefinitionBody:
    def __init__(
        self,
        *,
        properties: typing.Union["RoleDefinitionProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Role Definition API calls This matches the Azure REST API schema for role definitions.

        :param properties: The properties of the role definition.
        '''
        if isinstance(properties, dict):
            properties = RoleDefinitionProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__658a75c59d9656508fb8bcc48fd1a65adca8190b7915477f5db35f368a56ae0b)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "RoleDefinitionProperties":
        '''The properties of the role definition.'''
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("RoleDefinitionProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleDefinitionBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roledefinition.RoleDefinitionPermission",
    jsii_struct_bases=[],
    name_mapping={
        "actions": "actions",
        "data_actions": "dataActions",
        "not_actions": "notActions",
        "not_data_actions": "notDataActions",
    },
)
class RoleDefinitionPermission:
    def __init__(
        self,
        *,
        actions: typing.Optional[typing.Sequence[builtins.str]] = None,
        data_actions: typing.Optional[typing.Sequence[builtins.str]] = None,
        not_actions: typing.Optional[typing.Sequence[builtins.str]] = None,
        not_data_actions: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Permission configuration for role definitions Defines what actions the role can perform on control plane and data plane.

        :param actions: Array of allowed control plane actions Actions are operations that can be performed on Azure resources.
        :param data_actions: Array of allowed data plane actions Data actions are operations that can be performed on data within resources.
        :param not_actions: Array of excluded control plane actions Actions that are explicitly denied even if included in actions array.
        :param not_data_actions: Array of excluded data plane actions Data actions that are explicitly denied.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f588c4fffce97519cd008de94d4f04def3625510fc43bffbcd8d3a3830a8a98f)
            check_type(argname="argument actions", value=actions, expected_type=type_hints["actions"])
            check_type(argname="argument data_actions", value=data_actions, expected_type=type_hints["data_actions"])
            check_type(argname="argument not_actions", value=not_actions, expected_type=type_hints["not_actions"])
            check_type(argname="argument not_data_actions", value=not_data_actions, expected_type=type_hints["not_data_actions"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if actions is not None:
            self._values["actions"] = actions
        if data_actions is not None:
            self._values["data_actions"] = data_actions
        if not_actions is not None:
            self._values["not_actions"] = not_actions
        if not_data_actions is not None:
            self._values["not_data_actions"] = not_data_actions

    @builtins.property
    def actions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of allowed control plane actions Actions are operations that can be performed on Azure resources.

        Example::

            ["Microsoft.Compute/virtualMachines/read", "Microsoft.Compute/virtualMachines/start/action"]
        '''
        result = self._values.get("actions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def data_actions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of allowed data plane actions Data actions are operations that can be performed on data within resources.

        Example::

            ["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"]
        '''
        result = self._values.get("data_actions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def not_actions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of excluded control plane actions Actions that are explicitly denied even if included in actions array.

        Example::

            ["Microsoft.Compute/virtualMachines/delete"]
        '''
        result = self._values.get("not_actions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def not_data_actions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of excluded data plane actions Data actions that are explicitly denied.

        Example::

            ["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete"]
        '''
        result = self._values.get("not_data_actions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleDefinitionPermission(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roledefinition.RoleDefinitionProperties",
    jsii_struct_bases=[],
    name_mapping={
        "assignable_scopes": "assignableScopes",
        "permissions": "permissions",
        "role_name": "roleName",
        "description": "description",
        "type": "type",
    },
)
class RoleDefinitionProperties:
    def __init__(
        self,
        *,
        assignable_scopes: typing.Sequence[builtins.str],
        permissions: typing.Sequence[typing.Union[RoleDefinitionPermission, typing.Dict[builtins.str, typing.Any]]],
        role_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties interface for Azure Role Definition This is required for JSII compliance to support multi-language code generation.

        :param assignable_scopes: An array of assignable scopes.
        :param permissions: An array of permissions objects.
        :param role_name: The name of the role definition.
        :param description: The role definition description.
        :param type: The type of role definition.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3cb1be498f140293c3e71a86f50f74083d6f178d782095522ee810a1bc63e338)
            check_type(argname="argument assignable_scopes", value=assignable_scopes, expected_type=type_hints["assignable_scopes"])
            check_type(argname="argument permissions", value=permissions, expected_type=type_hints["permissions"])
            check_type(argname="argument role_name", value=role_name, expected_type=type_hints["role_name"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "assignable_scopes": assignable_scopes,
            "permissions": permissions,
            "role_name": role_name,
        }
        if description is not None:
            self._values["description"] = description
        if type is not None:
            self._values["type"] = type

    @builtins.property
    def assignable_scopes(self) -> typing.List[builtins.str]:
        '''An array of assignable scopes.'''
        result = self._values.get("assignable_scopes")
        assert result is not None, "Required property 'assignable_scopes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def permissions(self) -> typing.List[RoleDefinitionPermission]:
        '''An array of permissions objects.'''
        result = self._values.get("permissions")
        assert result is not None, "Required property 'permissions' is missing"
        return typing.cast(typing.List[RoleDefinitionPermission], result)

    @builtins.property
    def role_name(self) -> builtins.str:
        '''The name of the role definition.'''
        result = self._values.get("role_name")
        assert result is not None, "Required property 'role_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The role definition description.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def type(self) -> typing.Optional[builtins.str]:
        '''The type of role definition.'''
        result = self._values.get("type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleDefinitionProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_roledefinition.RoleDefinitionProps",
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
        "assignable_scopes": "assignableScopes",
        "permissions": "permissions",
        "role_name": "roleName",
        "description": "description",
        "ignore_changes": "ignoreChanges",
        "type": "type",
    },
)
class RoleDefinitionProps(_AzapiResourceProps_141a2340):
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
        assignable_scopes: typing.Sequence[builtins.str],
        permissions: typing.Sequence[typing.Union[RoleDefinitionPermission, typing.Dict[builtins.str, typing.Any]]],
        role_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the unified Azure Role Definition.

        Extends AzapiResourceProps with Role Definition specific properties

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
        :param assignable_scopes: An array of scopes where this role can be assigned Can include subscription, resource group, or management group scopes Required property.
        :param permissions: An array of permissions objects that define what actions the role can perform Required property.
        :param role_name: The name of the role definition This is the display name shown in the Azure portal Required property.
        :param description: The role definition description Provides detailed information about what the role allows.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param type: The type of role definition. Default: "CustomRole"
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9684eee6796fce0c807b512e8975a3c52e0e59686b2a875682d6dc6c32876333)
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
            check_type(argname="argument assignable_scopes", value=assignable_scopes, expected_type=type_hints["assignable_scopes"])
            check_type(argname="argument permissions", value=permissions, expected_type=type_hints["permissions"])
            check_type(argname="argument role_name", value=role_name, expected_type=type_hints["role_name"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "assignable_scopes": assignable_scopes,
            "permissions": permissions,
            "role_name": role_name,
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
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if type is not None:
            self._values["type"] = type

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
    def assignable_scopes(self) -> typing.List[builtins.str]:
        '''An array of scopes where this role can be assigned Can include subscription, resource group, or management group scopes Required property.

        Example::

            ["/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-name"]
        '''
        result = self._values.get("assignable_scopes")
        assert result is not None, "Required property 'assignable_scopes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def permissions(self) -> typing.List[RoleDefinitionPermission]:
        '''An array of permissions objects that define what actions the role can perform Required property.

        Example::

            [
              {
                actions: ["Microsoft.Compute/virtualMachines/read"],
                notActions: [],
                dataActions: [],
                notDataActions: []
              }
            ]
        '''
        result = self._values.get("permissions")
        assert result is not None, "Required property 'permissions' is missing"
        return typing.cast(typing.List[RoleDefinitionPermission], result)

    @builtins.property
    def role_name(self) -> builtins.str:
        '''The name of the role definition This is the display name shown in the Azure portal Required property.

        Example::

            "Virtual Machine Reader"
        '''
        result = self._values.get("role_name")
        assert result is not None, "Required property 'role_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The role definition description Provides detailed information about what the role allows.

        Example::

            "Can view virtual machines and their properties"
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
    def type(self) -> typing.Optional[builtins.str]:
        '''The type of role definition.

        :default: "CustomRole"

        Example::

            "CustomRole", "BuiltInRole"
        '''
        result = self._values.get("type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RoleDefinitionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "RoleDefinition",
    "RoleDefinitionBody",
    "RoleDefinitionPermission",
    "RoleDefinitionProperties",
    "RoleDefinitionProps",
]

publication.publish()

def _typecheckingstub__2fef2b822ec6c9c4f11fe52cc2c69e592b1af1da2e1fd4477d8ef9eba048817b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    assignable_scopes: typing.Sequence[builtins.str],
    permissions: typing.Sequence[typing.Union[RoleDefinitionPermission, typing.Dict[builtins.str, typing.Any]]],
    role_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__cf0d4e21c9ac4678b576f5d4474c0559e5c29bcf7ea68bd8f6cd878e80b87c94(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__658a75c59d9656508fb8bcc48fd1a65adca8190b7915477f5db35f368a56ae0b(
    *,
    properties: typing.Union[RoleDefinitionProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f588c4fffce97519cd008de94d4f04def3625510fc43bffbcd8d3a3830a8a98f(
    *,
    actions: typing.Optional[typing.Sequence[builtins.str]] = None,
    data_actions: typing.Optional[typing.Sequence[builtins.str]] = None,
    not_actions: typing.Optional[typing.Sequence[builtins.str]] = None,
    not_data_actions: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3cb1be498f140293c3e71a86f50f74083d6f178d782095522ee810a1bc63e338(
    *,
    assignable_scopes: typing.Sequence[builtins.str],
    permissions: typing.Sequence[typing.Union[RoleDefinitionPermission, typing.Dict[builtins.str, typing.Any]]],
    role_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9684eee6796fce0c807b512e8975a3c52e0e59686b2a875682d6dc6c32876333(
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
    assignable_scopes: typing.Sequence[builtins.str],
    permissions: typing.Sequence[typing.Union[RoleDefinitionPermission, typing.Dict[builtins.str, typing.Any]]],
    role_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
