r'''
# Azure Virtual Network Manager

This module provides a high-level TypeScript construct for managing Azure Virtual Network Managers using the Terraform CDK and Azure AZAPI provider.

Azure Virtual Network Manager (AVNM) is a centralized network management service that enables you to manage connectivity and security policies for your virtual networks at scale across subscriptions and management groups.

## Table of Contents

* [Why Use Azure Virtual Network Manager?](#why-use-azure-virtual-network-manager)
* [Why Use AZAPI Provider?](#why-use-azapi-provider)
* [Features](#features)
* [Supported API Versions](#supported-api-versions)
* [Installation](#installation)
* [Basic Usage](#basic-usage)
* [Advanced Usage](#advanced-usage)
* [API Reference](#api-reference)

  * [VirtualNetworkManager](#virtualnetworkmanager)
  * [NetworkGroup](#networkgroup)
  * [NetworkGroupStaticMember](#networkgroupstaticmember)
  * [ConnectivityConfiguration](#connectivityconfiguration)
  * [SecurityAdminConfiguration](#securityadminconfiguration)
  * [SecurityAdminRuleCollection](#securityadminrulecollection)
  * [SecurityAdminRule](#securityadminrule)
* [Child Resources](#child-resources)
* [IPAM (IP Address Management)](#ipam-ip-address-management)

  * [Features](#features-1)
  * [Basic Usage](#basic-usage-1)
  * [CIDR Validation Utilities](#cidr-validation-utilities)
  * [Regional Limitations](#regional-limitations)
  * [Best Practices](#best-practices-1)
  * [Complete IPAM Example](#complete-ipam-example)
  * [API Reference](#api-reference-1)
  * [Troubleshooting](#troubleshooting-1)
* [Complete End-to-End Example](#complete-end-to-end-example)
* [Best Practices](#best-practices)
* [Troubleshooting](#troubleshooting)
* [Related Constructs](#related-constructs)
* [Additional Resources](#additional-resources)

## Why Use Azure Virtual Network Manager?

* **Centralized Management**: Manage connectivity and security across multiple virtual networks from a single location
* **Policy-Based Configuration**: Apply consistent network policies across your organization
* **Scalability**: Manage thousands of virtual networks efficiently
* **Flexibility**: Support for both subscription and management group scopes
* **Advanced Features**: Connectivity configurations, security admin rules, and routing configurations

## Why Use AZAPI Provider?

* **Latest Azure Features**: Access new Azure Virtual Network Manager features immediately upon release without waiting for Terraform provider updates
* **Automatic API Version Management**: Seamlessly switch between API versions or use the latest by default
* **Type-Safe Properties**: Full TypeScript type definitions with comprehensive validation
* **No Provider Lag**: Direct access to Azure Resource Manager APIs means zero delay for new features

## Features

* **Multiple API Version Support**: Automatically supports the 2 most recent stable API versions (2024-05-01, 2023-11-01)
* **Automatic Version Resolution**: Uses the latest API version by default
* **Version Pinning**: Lock to a specific API version for stability
* **Type-Safe**: Full TypeScript support with comprehensive interfaces
* **JSII Compatible**: Can be used from TypeScript, Python, Java, and C#
* **Terraform Outputs**: Automatic creation of outputs for easy reference
* **Tag Management**: Built-in methods for managing resource tags
* **Complete Child Resource Support**: All child resource types fully implemented

  * Network Groups - Logical containers for VNets/subnets
  * Network Group Static Members - Add specific resources to groups
  * Connectivity Configurations - Mesh and hub-spoke topologies
  * Security Admin Configurations - High-priority security policies
  * Security Admin Rule Collections - Group related security rules
  * Security Admin Rules - Individual Allow/Deny/AlwaysAllow rules
  * **IPAM Pools** - IP address management with hierarchical pools
  * **IPAM Pool Static CIDRs** - Static CIDR allocations within pools
* **IPAM Features**: Centralized IP address management with overlap prevention and validation utilities
* **Flexible Usage Patterns**: Choose between convenience methods or direct instantiation

## Supported API Versions

| Version | Support Level | Release Date | Notes |
|---------|--------------|--------------|-------|
| 2024-05-01 | Active (Latest) | 2024-05-01 | Recommended for new deployments with full routing, security, and connectivity features |
| 2023-11-01 | Maintenance | 2023-11-01 | Stable release with core Network Manager features |

## Installation

This module is part of the `@microsoft/terraform-cdk-constructs` package.

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Basic Usage

### Simple Virtual Network Manager with Subscription Scope

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import { VirtualNetworkManager } from "@microsoft/terraform-cdk-constructs/azure-virtualnetworkmanager";

const app = new App();
const stack = new TerraformStack(app, "network-manager-stack");

// Configure the Azure provider
new AzapiProvider(stack, "azapi", {});

// Create a resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "my-resource-group",
  location: "eastus",
});

// Create a Virtual Network Manager
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "my-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
  description: "Network manager for production environment",
  tags: {
    Environment: "Production",
    ManagedBy: "Terraform",
  },
});

app.synth();
```

## Advanced Usage

### Network Manager with Management Group Scope

```python
const vnm = new VirtualNetworkManager(stack, "vnm-mg", {
  name: "enterprise-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    managementGroups: [
      "/providers/Microsoft.Management/managementGroups/my-mg-id",
    ],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin", "Routing"],
  description: "Enterprise-wide network management",
  tags: {
    Environment: "Production",
    Scope: "Enterprise",
  },
});
```

### Network Manager with Multiple Scopes

```python
const vnm = new VirtualNetworkManager(stack, "vnm-multi-scope", {
  name: "multi-scope-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: [
      "/subscriptions/00000000-0000-0000-0000-000000000000",
      "/subscriptions/11111111-1111-1111-1111-111111111111",
    ],
    managementGroups: [
      "/providers/Microsoft.Management/managementGroups/my-mg-id",
    ],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
  description: "Network manager spanning multiple subscriptions and management groups",
});
```

### All Scope Access Types

```python
const vnm = new VirtualNetworkManager(stack, "vnm-full-access", {
  name: "full-feature-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: [
    "Connectivity",   // Manage virtual network connectivity
    "SecurityAdmin",  // Manage security admin rules
    "Routing",        // Manage routing configurations
  ],
  description: "Network manager with all features enabled",
});
```

### Pinning to a Specific API Version

```python
const vnm = new VirtualNetworkManager(stack, "vnm-pinned", {
  name: "stable-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  apiVersion: "2023-11-01", // Pin to specific version
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
  description: "Network manager with pinned API version",
});
```

### Using Outputs

```python
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "my-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
});

// Access Network Manager ID for use in other resources
console.log(vnm.id); // Terraform interpolation string
console.log(vnm.resourceName); // Network manager name

// Use outputs for cross-stack references
new TerraformOutput(stack, "vnm-id", {
  value: vnm.idOutput,
});

new TerraformOutput(stack, "vnm-scope", {
  value: vnm.scopeOutput,
});
```

### Tag Management

```python
const vnm = new VirtualNetworkManager(stack, "vnm-tags", {
  name: "tagged-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
  tags: {
    Environment: "Production",
  },
});

// Add a tag
vnm.addTag("CostCenter", "Engineering");

// Remove a tag
vnm.removeTag("Environment");
```

### Ignore Changes Lifecycle

```python
const vnm = new VirtualNetworkManager(stack, "vnm-ignore-changes", {
  name: "lifecycle-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
  tags: {
    ManagedBy: "Terraform",
  },
  ignoreChanges: ["tags"], // Ignore changes to tags
});
```

## API Reference

### VirtualNetworkManager

The main construct for creating and managing Azure Virtual Network Managers.

#### VirtualNetworkManagerProps

Configuration properties for the Virtual Network Manager construct.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the Virtual Network Manager (2-64 characters, alphanumeric, underscores, hyphens, periods) |
| `location` | `string` | Yes | Azure region where the network manager will be deployed |
| `resourceGroupName` | `string` | Yes | Name of the resource group where the network manager will be created |
| `networkManagerScopes` | [`NetworkManagerScopes`](#networkmanagerscopes) | Yes | Defines the scope of management (management groups and/or subscriptions) |
| `networkManagerScopeAccesses` | `("Connectivity" \| "SecurityAdmin" \| "Routing")[]` | Yes | Array of features enabled for the network manager |
| `description` | `string` | No | Optional description of the network manager |
| `tags` | `{ [key: string]: string }` | No | Resource tags for organization and cost tracking |
| `apiVersion` | `string` | No | Pin to a specific API version (e.g., "2024-05-01") |
| `ignoreChanges` | `string[]` | No | Properties to ignore during updates (e.g., ["tags"]) |

### NetworkManagerScopes

Defines the management scope for the Virtual Network Manager. At least one of `managementGroups` or `subscriptions` must be specified.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `managementGroups` | `string[]` | No* | Array of management group IDs (e.g., ["/providers/Microsoft.Management/managementGroups/mg1"]) |
| `subscriptions` | `string[]` | No* | Array of subscription IDs (e.g., ["/subscriptions/00000000-0000-0000-0000-000000000000"]) |

*At least one of `managementGroups` or `subscriptions` is required.

### Network Manager Scope Accesses

The `networkManagerScopeAccesses` property defines which features are enabled for the Network Manager:

* **`Connectivity`**: Enables management of connectivity configurations (hub-and-spoke, mesh topologies)
* **`SecurityAdmin`**: Enables management of security admin rules across virtual networks
* **`Routing`**: Enables management of routing configurations (requires 2024-05-01 or later)

### Public Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `string` | The Azure resource ID of the Virtual Network Manager |
| `resourceName` | `string` | The name of the Virtual Network Manager |
| `tags` | `{ [key: string]: string }` | The tags assigned to the Virtual Network Manager |

### Outputs

The construct automatically creates Terraform outputs:

* **`id`**: The Virtual Network Manager resource ID
* **`name`**: The Virtual Network Manager name
* **`location`**: The Virtual Network Manager location
* **`tags`**: The Virtual Network Manager tags
* **`scope`**: The management scope (subscriptions and/or management groups)
* **`scopeAccesses`**: The enabled features (Connectivity, SecurityAdmin, Routing)

### VirtualNetworkManager Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| [`addTag()`](#addtag) | `key: string, value: string` | `void` | Add a tag to the Virtual Network Manager |
| [`removeTag()`](#removetag) | `key: string` | `void` | Remove a tag from the Virtual Network Manager |
| [`addNetworkGroup()`](#addnetworkgroup) | `id: string, props: Omit<NetworkGroupProps, 'networkManagerId'>` | `NetworkGroup` | Convenience method to create a NetworkGroup |
| [`addConnectivityConfiguration()`](#addconnectivityconfiguration) | `id: string, props: Omit<ConnectivityConfigurationProps, 'networkManagerId'>` | `ConnectivityConfiguration` | Convenience method to create a ConnectivityConfiguration |
| [`addSecurityAdminConfiguration()`](#addsecurityadminconfiguration) | `id: string, props: Omit<SecurityAdminConfigurationProps, 'networkManagerId'>` | `SecurityAdminConfiguration` | Convenience method to create a SecurityAdminConfiguration |

#### addTag()

```python
public addTag(key: string, value: string): void
```

Add a tag to the Virtual Network Manager. Note: This modifies the construct props but requires a new deployment to take effect.

#### removeTag()

```python
public removeTag(key: string): void
```

Remove a tag from the Virtual Network Manager. Note: This modifies the construct props but requires a new deployment to take effect.

#### addNetworkGroup()

```python
public addNetworkGroup(
  id: string,
  props: Omit<NetworkGroupProps, "networkManagerId">
): NetworkGroup
```

Convenience method to create a NetworkGroup with the networkManagerId automatically set.

**Example:**

```python
const prodGroup = networkManager.addNetworkGroup("prod-group", {
  name: "production-vnets",
  description: "Production virtual networks",
  memberType: "VirtualNetwork"
});
```

#### addConnectivityConfiguration()

```python
public addConnectivityConfiguration(
  id: string,
  props: Omit<ConnectivityConfigurationProps, "networkManagerId">
): ConnectivityConfiguration
```

Convenience method to create a ConnectivityConfiguration with the networkManagerId automatically set.

**Example:**

```python
const hubSpoke = networkManager.addConnectivityConfiguration("hub-spoke", {
  name: "production-hub-spoke",
  connectivityTopology: "HubAndSpoke",
  appliesToGroups: [{ networkGroupId: prodGroup.id }],
  hubs: [{ resourceId: hubVnet.id, resourceType: "Microsoft.Network/virtualNetworks" }]
});
```

#### addSecurityAdminConfiguration()

```python
public addSecurityAdminConfiguration(
  id: string,
  props: Omit<SecurityAdminConfigurationProps, "networkManagerId">
): SecurityAdminConfiguration
```

Convenience method to create a SecurityAdminConfiguration with the networkManagerId automatically set.

**Example:**

```python
const securityConfig = networkManager.addSecurityAdminConfiguration("security", {
  name: "production-security",
  description: "High-priority security rules for production"
});
```

### NetworkGroup

See the [Network Groups](#network-groups) section for detailed documentation.

### NetworkGroupStaticMember

See the [Network Group Static Members](#network-group-static-members) section for detailed documentation.

### ConnectivityConfiguration

See the [Connectivity Configurations](#connectivity-configurations) section for detailed documentation.

### SecurityAdminConfiguration

See the [Security Admin Configurations](#security-admin-configurations) section for detailed documentation.

### SecurityAdminRuleCollection

See the [Security Admin Rule Collections](#security-admin-rule-collections) section for detailed documentation.

### SecurityAdminRule

See the [Security Admin Rules](#security-admin-rules) section for detailed documentation.

## Best Practices

### 1. Scope Configuration

**Use Subscription Scope for Isolated Environments:**

```python
// ✅ Recommended for isolated environments
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "dev-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
});
```

**Use Management Group Scope for Enterprise-Wide Management:**

```python
// ✅ Recommended for enterprise scenarios
const vnm = new VirtualNetworkManager(stack, "vnm-enterprise", {
  name: "enterprise-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    managementGroups: [
      "/providers/Microsoft.Management/managementGroups/root-mg",
    ],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
});
```

### 2. Network Manager Scope Access

Only enable the features you need:

```python
// ✅ Good - Enable only required features
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "connectivity-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"], // Only connectivity
});
```

### 3. Naming Conventions

Follow Azure naming conventions:

```python
// ✅ Good - Descriptive, follows conventions
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "prod-eastus-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
});
```

### 4. Tag Management

Apply consistent tags for better organization:

```python
// ✅ Recommended - Comprehensive tagging
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "my-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
  tags: {
    Environment: "Production",
    CostCenter: "Engineering",
    ManagedBy: "Terraform",
    Project: "Network-Infrastructure",
  },
});
```

### 5. Use Latest API Version for New Deployments

Unless you have specific requirements, use the default (latest) API version:

```python
// ✅ Recommended - Uses latest version automatically
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "my-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
});
```

### 6. Pin API Versions for Production Stability

For production workloads, consider pinning to a specific API version:

```python
// ✅ Production-ready - Pinned version
const vnm = new VirtualNetworkManager(stack, "vnm", {
  name: "prod-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  apiVersion: "2024-05-01",
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
});
```

## Child Resources

Azure Virtual Network Manager supports several child resources that enable powerful network management capabilities. This module implements all essential child resources with full TypeScript support.

### Available Child Resources

* **[Network Groups](#network-groups)**: Logical containers for virtual networks or subnets
* **[Network Group Static Members](#network-group-static-members)**: Add specific VNets/subnets to groups
* **[Connectivity Configurations](#connectivity-configurations)**: Define mesh or hub-and-spoke topologies
* **[Security Admin Configurations](#security-admin-configurations)**: High-priority security policies
* **[Security Admin Rule Collections](#security-admin-rule-collections)**: Group related security rules
* **[Security Admin Rules](#security-admin-rules)**: Individual security rules (Allow, Deny, AlwaysAllow)

### Usage Patterns

This module supports two usage patterns (Option A - Hybrid Approach):

#### 1. Convenience Methods (Recommended for Simple Cases)

Use the convenience methods on the [`VirtualNetworkManager`](#virtualnetworkmanager) instance:

```python
// Create network group using convenience method
const prodGroup = networkManager.addNetworkGroup("prod-group", {
  name: "production-vnets",
  description: "Production virtual networks",
  memberType: "VirtualNetwork"
});

// Create connectivity configuration using convenience method
networkManager.addConnectivityConfiguration("mesh-config", {
  name: "mesh-topology",
  connectivityTopology: "Mesh",
  appliesToGroups: [{ networkGroupId: prodGroup.id }]
});
```

**Benefits:**

* Less verbose (networkManagerId is set automatically)
* Natural parent-child relationship
* Cleaner code for simple scenarios

#### 2. Direct Instantiation (For Complex Scenarios)

Create child resources directly with full control:

```python
// Create network group with direct instantiation
const hubGroup = new NetworkGroup(this, "hub-group", {
  name: "hub-vnets",
  networkManagerId: networkManager.id,
  description: "Hub virtual networks",
  memberType: "VirtualNetwork"
});

// Create connectivity configuration with direct instantiation
const hubSpoke = new ConnectivityConfiguration(this, "hub-spoke", {
  name: "hub-spoke-topology",
  networkManagerId: networkManager.id,
  connectivityTopology: "HubAndSpoke",
  appliesToGroups: [{ networkGroupId: hubGroup.id }],
  hubs: [{ resourceId: hubVnet.id, resourceType: "Microsoft.Network/virtualNetworks" }]
});
```

**Benefits:**

* Full flexibility
* Better for complex cross-stack scenarios
* Explicit parent references

**When to Use Each:**

* Use convenience methods for simple, single-stack deployments
* Use direct instantiation when you need more control or cross-stack references

## Network Groups

Network Groups are logical containers for virtual networks or subnets. They're the foundation for applying connectivity, security, or routing configurations at scale.

### NetworkGroupProps

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the network group |
| `networkManagerId` | `string` | Yes | Resource ID of the parent Network Manager |
| `description` | `string` | No | Optional description |
| `memberType` | `"VirtualNetwork" \| "Subnet"` | No | Type of members (defaults to mixed if not specified) |
| `apiVersion` | `string` | No | Pin to specific API version |
| `ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

### Network Group Examples

#### Basic Network Group

```python
// Using convenience method
const prodGroup = networkManager.addNetworkGroup("prod-group", {
  name: "production-vnets",
  description: "Production virtual networks",
  memberType: "VirtualNetwork"
});

// Using direct instantiation
const devGroup = new NetworkGroup(this, "dev-group", {
  name: "development-vnets",
  networkManagerId: networkManager.id,
  description: "Development virtual networks",
  memberType: "VirtualNetwork"
});
```

#### Network Group for Subnets

```python
const subnetGroup = new NetworkGroup(this, "subnet-group", {
  name: "dmz-subnets",
  networkManagerId: networkManager.id,
  description: "DMZ subnets across multiple VNets",
  memberType: "Subnet"
});
```

## Network Group Static Members

Static Members explicitly add virtual networks or subnets to a network group. This provides precise control over group membership (as opposed to dynamic membership via Azure Policy).

### NetworkGroupStaticMemberProps

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the static member |
| `networkGroupId` | `string` | Yes | Resource ID of the parent Network Group |
| `resourceId` | `string` | Yes | Full resource ID of the VNet or Subnet to add |
| `apiVersion` | `string` | No | Pin to specific API version |
| `ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

### Static Member Examples

#### Adding VNets to a Network Group

```python
// Add production VNet to production group
new NetworkGroupStaticMember(this, "prod-vnet1-member", {
  name: "prod-vnet1",
  networkGroupId: productionGroup.id,
  resourceId: prodVnet1.id
});

// Add another VNet to the same group
new NetworkGroupStaticMember(this, "prod-vnet2-member", {
  name: "prod-vnet2",
  networkGroupId: productionGroup.id,
  resourceId: prodVnet2.id
});
```

#### Adding Subnets to a Network Group

```python
// Add specific subnet to DMZ group
new NetworkGroupStaticMember(this, "dmz-subnet-member", {
  name: "dmz-subnet1",
  networkGroupId: dmzSubnetGroup.id,
  resourceId: subnet.id  // Subnet resource ID
});
```

## Connectivity Configurations

Connectivity Configurations define network topology (mesh or hub-and-spoke) for virtual networks. They enable automated peering management at scale.

### ConnectivityConfigurationProps

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the connectivity configuration |
| `networkManagerId` | `string` | Yes | Resource ID of the parent Network Manager |
| `connectivityTopology` | `"Mesh" \| "HubAndSpoke"` | Yes | Topology type |
| `appliesToGroups` | [`ConnectivityGroupItem[]`](#connectivitygroupitem) | Yes | Network groups to apply configuration to |
| `hubs` | [`Hub[]`](#hub) | No* | Hub VNets (required for HubAndSpoke) |
| `description` | `string` | No | Optional description |
| `isGlobal` | `boolean` | No | Enable global mesh (default: false) |
| `deleteExistingPeering` | `boolean` | No | Delete existing peerings (default: false) |
| `apiVersion` | `string` | No | Pin to specific API version |
| `ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

*Required when `connectivityTopology` is "HubAndSpoke"

#### ConnectivityGroupItem

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `networkGroupId` | `string` | Yes | Network Group resource ID |
| `useHubGateway` | `boolean` | No | Use hub gateway for spoke-to-spoke traffic |
| `isGlobal` | `boolean` | No | Enable global connectivity |
| `groupConnectivity` | `"None" \| "DirectlyConnected"` | No | Group connectivity mode |

#### Hub

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `resourceId` | `string` | Yes | Hub VNet resource ID |
| `resourceType` | `string` | Yes | Resource type (typically "Microsoft.Network/virtualNetworks") |

### Connectivity Configuration Examples

#### Mesh Topology

```python
// Using convenience method
const meshConfig = networkManager.addConnectivityConfiguration("mesh", {
  name: "dev-mesh-topology",
  connectivityTopology: "Mesh",
  description: "Full mesh for development VNets",
  appliesToGroups: [
    {
      networkGroupId: devGroup.id,
      groupConnectivity: "DirectlyConnected",
      isGlobal: false
    }
  ],
  deleteExistingPeering: true,
  isGlobal: false
});

// Using direct instantiation
const regionalMesh = new ConnectivityConfiguration(this, "regional-mesh", {
  name: "regional-mesh",
  networkManagerId: networkManager.id,
  connectivityTopology: "Mesh",
  description: "Regional mesh for test environments",
  appliesToGroups: [
    {
      networkGroupId: testGroup.id,
      groupConnectivity: "DirectlyConnected"
    }
  ]
});
```

#### Hub-and-Spoke Topology

```python
// Using convenience method
const hubSpoke = networkManager.addConnectivityConfiguration("hub-spoke", {
  name: "production-hub-spoke",
  connectivityTopology: "HubAndSpoke",
  description: "Hub-spoke for production with gateway transit",
  appliesToGroups: [
    {
      networkGroupId: productionGroup.id,
      useHubGateway: true,  // Enable gateway transit
      isGlobal: false
    }
  ],
  hubs: [
    {
      resourceId: hubVnet.id,
      resourceType: "Microsoft.Network/virtualNetworks"
    }
  ],
  deleteExistingPeering: true
});

// Using direct instantiation with multiple hubs
const multiRegionHubSpoke = new ConnectivityConfiguration(this, "multi-hub", {
  name: "multi-region-hub-spoke",
  networkManagerId: networkManager.id,
  connectivityTopology: "HubAndSpoke",
  description: "Multi-region hub-spoke topology",
  appliesToGroups: [
    {
      networkGroupId: globalGroup.id,
      useHubGateway: true,
      isGlobal: true  // Enable global mesh between regions
    }
  ],
  hubs: [
    {
      resourceId: eastUsHub.id,
      resourceType: "Microsoft.Network/virtualNetworks"
    },
    {
      resourceId: westUsHub.id,
      resourceType: "Microsoft.Network/virtualNetworks"
    }
  ],
  isGlobal: true
});
```

## Security Admin Configurations

Security Admin Configurations define high-priority security rules that are evaluated **BEFORE** traditional Network Security Groups (NSGs). This enables centralized security policy enforcement that cannot be overridden by individual teams.

### SecurityAdminConfigurationProps

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the security admin configuration |
| `networkManagerId` | `string` | Yes | Resource ID of the parent Network Manager |
| `description` | `string` | No | Optional description |
| `applyOnNetworkIntentPolicyBasedServices` | `string[]` | No | Services to apply config on |
| `apiVersion` | `string` | No | Pin to specific API version |
| `ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

### Security Admin Configuration Examples

```python
// Using convenience method
const securityConfig = networkManager.addSecurityAdminConfiguration("security", {
  name: "org-security-policies",
  description: "Organization-wide security enforcement"
});

// Using direct instantiation with service configuration
const securityConfig = new SecurityAdminConfiguration(this, "security-config", {
  name: "production-security",
  networkManagerId: networkManager.id,
  description: "High-priority security rules for production",
  applyOnNetworkIntentPolicyBasedServices: ["None"]
});
```

## Security Admin Rule Collections

Rule Collections group related security admin rules together and define which network groups receive those rules.

### SecurityAdminRuleCollectionProps

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the rule collection |
| `securityAdminConfigurationId` | `string` | Yes | Resource ID of the parent Security Admin Configuration |
| `description` | `string` | No | Optional description |
| `appliesToGroups` | [`SecurityAdminConfigurationRuleGroupItem[]`](#securityadminconfigurationrulegroupitem) | Yes | Network groups to apply rules to |
| `apiVersion` | `string` | No | Pin to specific API version |
| `ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

#### SecurityAdminConfigurationRuleGroupItem

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `networkGroupId` | `string` | Yes | Network Group resource ID |

### Rule Collection Examples

```python
// Rule collection for blocking high-risk ports
const blockHighRiskPorts = new SecurityAdminRuleCollection(this, "block-ports", {
  name: "block-high-risk-ports",
  securityAdminConfigurationId: securityConfig.id,
  description: "Block SSH, RDP, and other high-risk ports from internet",
  appliesToGroups: [
    { networkGroupId: productionGroup.id },
    { networkGroupId: stagingGroup.id }
  ]
});

// Rule collection for allowing monitoring traffic
const allowMonitoring = new SecurityAdminRuleCollection(this, "allow-monitoring", {
  name: "allow-monitoring-traffic",
  securityAdminConfigurationId: securityConfig.id,
  description: "Always allow monitoring and security scanner traffic",
  appliesToGroups: [
    { networkGroupId: productionGroup.id },
    { networkGroupId: stagingGroup.id },
    { networkGroupId: devGroup.id }
  ]
});
```

## Security Admin Rules

Security Admin Rules define individual security policies with three action types:

* **Allow**: Permits traffic, but NSG can still deny it
* **Deny**: Blocks traffic immediately, no further evaluation
* **AlwaysAllow**: Forces traffic to be allowed, overriding NSG denies

### SecurityAdminRuleProps

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | `string` | Yes | Name of the rule |
| `ruleCollectionId` | `string` | Yes | Resource ID of the parent Rule Collection |
| `priority` | `number` | Yes | Priority (1-4096, lower = higher priority) |
| `action` | `"Allow" \| "Deny" \| "AlwaysAllow"` | Yes | Action to take when rule matches |
| `direction` | `"Inbound" \| "Outbound"` | Yes | Traffic direction |
| `protocol` | `"Tcp" \| "Udp" \| "Icmp" \| "Esp" \| "Ah" \| "Any"` | Yes | Protocol |
| `description` | `string` | No | Optional description |
| `sourcePortRanges` | `string[]` | No | Source port ranges (default: ["*"]) |
| `destinationPortRanges` | `string[]` | No | Destination port ranges (default: ["*"]) |
| `sources` | [`AddressPrefixItem[]`](#addressprefixitem) | No | Source addresses (default: all) |
| `destinations` | [`AddressPrefixItem[]`](#addressprefixitem) | No | Destination addresses (default: all) |
| `apiVersion` | `string` | No | Pin to specific API version |
| `ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

#### AddressPrefixItem

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `addressPrefix` | `string` | Yes | IP address, CIDR, service tag, or "*" |
| `addressPrefixType` | `"IPPrefix" \| "ServiceTag"` | Yes | Type of address prefix |

### Security Admin Rule Examples

#### Deny Rules - Block High-Risk Ports

```python
// Block SSH from internet
new SecurityAdminRule(this, "block-ssh", {
  name: "block-ssh-from-internet",
  ruleCollectionId: blockHighRiskPorts.id,
  description: "Block SSH access from internet",
  priority: 100,
  action: "Deny",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["22"],
  sources: [
    {
      addressPrefix: "Internet",
      addressPrefixType: "ServiceTag"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});

// Block RDP from internet
new SecurityAdminRule(this, "block-rdp", {
  name: "block-rdp-from-internet",
  ruleCollectionId: blockHighRiskPorts.id,
  description: "Block RDP access from internet",
  priority: 110,
  action: "Deny",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["3389"],
  sources: [
    {
      addressPrefix: "Internet",
      addressPrefixType: "ServiceTag"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});

// Block multiple database ports
new SecurityAdminRule(this, "block-databases", {
  name: "block-database-ports",
  ruleCollectionId: blockHighRiskPorts.id,
  description: "Block direct database access from internet",
  priority: 120,
  action: "Deny",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["1433", "3306", "5432", "27017"],  // SQL, MySQL, PostgreSQL, MongoDB
  sources: [
    {
      addressPrefix: "Internet",
      addressPrefixType: "ServiceTag"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});
```

#### AlwaysAllow Rules - Mandatory Allow

```python
// Always allow monitoring traffic
new SecurityAdminRule(this, "always-allow-monitoring", {
  name: "always-allow-monitoring",
  ruleCollectionId: allowMonitoring.id,
  description: "Always allow traffic from monitoring systems - cannot be blocked by NSG",
  priority: 50,
  action: "AlwaysAllow",
  direction: "Inbound",
  protocol: "Any",
  sourcePortRanges: ["*"],
  destinationPortRanges: ["*"],
  sources: [
    {
      addressPrefix: "10.255.0.0/24",  // Monitoring network
      addressPrefixType: "IPPrefix"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});

// Always allow Azure security scanners
new SecurityAdminRule(this, "always-allow-security-scanners", {
  name: "always-allow-security-scanners",
  ruleCollectionId: allowMonitoring.id,
  description: "Always allow traffic from security scanners",
  priority: 60,
  action: "AlwaysAllow",
  direction: "Inbound",
  protocol: "Any",
  sources: [
    {
      addressPrefix: "AzureSecurityCenter",
      addressPrefixType: "ServiceTag"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});
```

#### Allow Rules - Permissive (NSG Can Override)

```python
// Allow HTTPS - NSG can still deny if needed
new SecurityAdminRule(this, "allow-https", {
  name: "allow-https",
  ruleCollectionId: allowMonitoring.id,
  description: "Allow HTTPS traffic - NSG can still override",
  priority: 200,
  action: "Allow",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["443"],
  sources: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});

// Allow HTTP only from specific networks
new SecurityAdminRule(this, "allow-http-internal", {
  name: "allow-http-internal",
  ruleCollectionId: allowMonitoring.id,
  description: "Allow HTTP from internal networks only",
  priority: 210,
  action: "Allow",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["80"],
  sources: [
    {
      addressPrefix: "10.0.0.0/8",
      addressPrefixType: "IPPrefix"
    },
    {
      addressPrefix: "172.16.0.0/12",
      addressPrefixType: "IPPrefix"
    }
  ],
  destinations: [
    {
      addressPrefix: "*",
      addressPrefixType: "IPPrefix"
    }
  ]
});
```

## IPAM (IP Address Management)

Azure Virtual Network Manager IPAM helps you manage IP address spaces at scale, preventing overlaps and enabling hierarchical allocation.

### Features

* **Centralized IP Management**: Manage IP addresses across multiple VNets from a single location
* **Overlap Prevention**: Automatic validation to prevent overlapping CIDR blocks
* **Hierarchical Pools**: Support for parent-child pool relationships for organized IP allocation
* **Static Allocations**: Reserve specific CIDR blocks within pools for dedicated purposes
* **CIDR Validation Utilities**: Built-in utilities for validating and analyzing CIDR blocks

### Basic Usage

#### Create Root IPAM Pool

```python
import { IpamPool } from "@microsoft/terraform-cdk-constructs/azure-virtualnetworkmanager";

const ipamPool = new IpamPool(this, "RootPool", {
  name: "production-pool",
  location: "eastus",
  networkManagerId: networkManager.id,
  addressPrefixes: ["10.0.0.0/8"],
  description: "Root IP address pool for production workloads",
  displayName: "Production Root Pool",
});
```

#### Create Static CIDR Allocation

```python
import { IpamPoolStaticCidr } from "@microsoft/terraform-cdk-constructs/azure-virtualnetworkmanager";

const staticAllocation = new IpamPoolStaticCidr(this, "EastUSAllocation", {
  name: "eastus-vnet-allocation",
  ipamPoolId: ipamPool.id,
  addressPrefixes: ["10.1.0.0/16"],
  description: "Reserved for East US VNet",
});
```

#### Hierarchical Pools

```python
// Parent pool
const parentPool = new IpamPool(this, "ParentPool", {
  name: "parent-pool",
  location: "eastus",
  networkManagerId: networkManager.id,
  addressPrefixes: ["10.0.0.0/8"],
  description: "Organization-wide IP address pool",
});

// Child pool
const childPool = new IpamPool(this, "ChildPool", {
  name: "child-pool-eastus",
  location: "eastus",
  networkManagerId: networkManager.id,
  addressPrefixes: ["10.1.0.0/16"],
  parentPoolName: parentPool.props.name,
  description: "Child pool for East US region",
});
```

### CIDR Validation Utilities

The IPAM constructs include built-in CIDR validation utilities exported as functions:

```python
import {
  isValidCidr,
  cidrsOverlap,
  calculateAddressCount,
  isSubnet,
} from "@microsoft/terraform-cdk-constructs/azure-virtualnetworkmanager";

// Validate CIDR format
const isValid = isValidCidr("10.0.0.0/8"); // true

// Check for overlaps
const overlap = cidrsOverlap("10.0.0.0/8", "10.1.0.0/16"); // true

// Calculate address count
const count = calculateAddressCount("10.0.0.0/24"); // 256

// Validate subnet relationship
const isSubnetOf = isSubnet("10.1.0.0/16", "10.0.0.0/8"); // true
```

### Regional Limitations

**IMPORTANT:** IPAM is **NOT available** in the following regions:

* Chile Central
* Jio India West
* Malaysia West
* Qatar Central
* South Africa West
* West India
* West US 3

Ensure you deploy your IPAM pools in supported regions.

### Best Practices

1. **Plan IP Address Space**: Design your IP address hierarchy before implementation
2. **Use Root Pools**: Start with large root pools (e.g., /8) for maximum flexibility
3. **Hierarchical Organization**: Organize pools by region, environment, or application
4. **Static Allocations**: Reserve specific blocks for known VNets or services
5. **Validation**: Always validate CIDRs before creating pools to catch errors early
6. **Documentation**: Document the purpose and allocation plan for each pool

### Complete IPAM Example

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import {
  VirtualNetworkManager,
  IpamPool,
  IpamPoolStaticCidr,
} from "@microsoft/terraform-cdk-constructs/azure-virtualnetworkmanager";

const app = new App();
const stack = new TerraformStack(app, "ipam-stack");

// Configure provider
new AzapiProvider(stack, "azapi", {});

// Create resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "rg-ipam-demo",
  location: "eastus",
});

// Create Network Manager
const networkManager = new VirtualNetworkManager(stack, "vnm", {
  name: "ipam-network-manager",
  location: "eastus",
  resourceGroupName: resourceGroup.props.name,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"],
  },
  networkManagerScopeAccesses: ["Connectivity"],
  description: "Network manager with IPAM capabilities",
});

// Create root IPAM pool
const rootPool = new IpamPool(stack, "RootPool", {
  name: "root-pool",
  location: "eastus",
  networkManagerId: networkManager.id,
  addressPrefixes: ["10.0.0.0/8"],
  displayName: "Production Root Pool",
  description: "Root IP address pool for all production workloads",
});

// Create regional child pool
const eastUSPool = new IpamPool(stack, "EastUSPool", {
  name: "eastus-pool",
  location: "eastus",
  networkManagerId: networkManager.id,
  addressPrefixes: ["10.1.0.0/16"],
  parentPoolName: rootPool.props.name,
  displayName: "East US Region Pool",
  description: "IP pool for East US region",
});

// Allocate static CIDR for specific VNet
new IpamPoolStaticCidr(stack, "WebTierAllocation", {
  name: "web-tier-allocation",
  ipamPoolId: eastUSPool.id,
  addressPrefixes: ["10.1.10.0/24"],
  description: "Reserved for web tier VNet",
});

app.synth();
```

### API Reference

#### IpamPool

The main construct for creating and managing IPAM pools.

**Constructor**: `new IpamPool(scope: Construct, id: string, props: IpamPoolProps)`

**Properties**:

Property | Type | Required | Description |
|----------|------|----------|-------------|
`name` | `string` | Yes | Name of the IPAM pool (2-64 characters) |
`location` | `string` | Yes | Azure region where the pool will be deployed |
`networkManagerId` | `string` | Yes | Resource ID of the parent Network Manager |
`addressPrefixes` | `string[]` | Yes | Array of CIDR blocks (e.g., ["10.0.0.0/8"]) |
`description` | `string` | No | Optional description of the pool |
`displayName` | `string` | No | Friendly display name for the pool |
`parentPoolName` | `string` | No | Name of parent pool for hierarchical pools |
`tags` | `{ [key: string]: string }` | No | Resource tags |
`apiVersion` | `string` | No | Pin to specific API version |
`ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

**Public Properties**:

Property | Type | Description |
|----------|------|-------------|
`id` | `string` | The Azure resource ID of the IPAM pool |
`resourceName` | `string` | The name of the IPAM pool |
`totalAddressCount` | `number` | Total number of IP addresses in the pool |
`provisioningState` | `string` | The provisioning state of the pool |

**Outputs**:

* `id`: The IPAM pool resource ID
* `name`: The IPAM pool name
* `location`: The IPAM pool location
* `provisioningState`: The provisioning state

#### IpamPoolStaticCidr

The construct for creating static CIDR allocations within IPAM pools.

**Constructor**: `new IpamPoolStaticCidr(scope: Construct, id: string, props: IpamPoolStaticCidrProps)`

**Properties**:

Property | Type | Required | Description |
|----------|------|----------|-------------|
`name` | `string` | Yes | Name of the static CIDR allocation |
`ipamPoolId` | `string` | Yes | Resource ID of the parent IPAM pool |
`addressPrefixes` | `string[]` | Yes | Array of CIDR blocks to allocate |
`description` | `string` | No | Optional description |
`numberOfIPAddresses` | `string` | No | IP count (auto-calculated if not provided) |
`apiVersion` | `string` | No | Pin to specific API version |
`ignoreChanges` | `string[]` | No | Lifecycle ignore changes |

**Public Properties**:

Property | Type | Description |
|----------|------|-------------|
`id` | `string` | The Azure resource ID of the static CIDR |
`resourceName` | `string` | The name of the static CIDR |
`calculatedAddressCount` | `number` | Number of addresses in the CIDR block |

**Outputs**:

* `id`: The static CIDR resource ID
* `name`: The static CIDR name
* `addressPrefix`: The CIDR address prefix

#### CIDR Validation Functions

Utility functions for CIDR validation and analysis.

**Functions**:

Function | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
`isValidCidr()` | `cidr: string` | `boolean` | Validates if a string is valid CIDR notation |
`isPrivateRange()` | `cidr: string` | `boolean` | Checks if CIDR is within private IP ranges |
`cidrsOverlap()` | `cidr1: string, cidr2: string` | `boolean` | Checks if two CIDR blocks overlap |
`isSubnet()` | `childCidr: string, parentCidr: string` | `boolean` | Validates if child CIDR is within parent CIDR |
`calculateAddressCount()` | `cidr: string` | `number` | Calculates number of IP addresses in CIDR |
`isValidPrefixLength()` | `cidr: string, min: number, max: number` | `boolean` | Validates prefix length is within range |
`validateCidr()` | `cidr: string` | `CidrValidationResult` | Validates CIDR and returns detailed errors/warnings |
`parseCidr()` | `cidr: string` | `ParsedCidr` | Parses CIDR into structured information |
`checkOverlap()` | `cidr1: string, cidr2: string` | `boolean` | Checks if two CIDRs overlap |
`validateNoOverlaps()` | `cidrs: string[]` | `CidrValidationResult` | Validates that multiple CIDRs don't overlap |
`isContained()` | `parentCidr: string, childCidr: string` | `boolean` | Checks if child CIDR is contained in parent |
`validateContainment()` | `parentCidr: string, childCidrs: string[]` | `CidrValidationResult` | Validates multiple child CIDRs are contained in parent |

### Troubleshooting

**Error: "Invalid CIDR notation"**

* Ensure CIDR uses correct format: `x.x.x.x/y` where y is 0-32
* Verify octets are 0-255
* Use [`isValidCidr()`](src/azure-virtualnetworkmanager/lib/utils/cidr-validator.ts) to validate before creating pools

**Error: "Address prefixes overlap"**

* Check for overlapping CIDRs within the same pool
* Use [`cidrsOverlap()`](src/azure-virtualnetworkmanager/lib/utils/cidr-validator.ts) to detect conflicts
* Ensure no two address prefixes in the same pool overlap

**Error: "Region not supported"**

* Verify your region supports IPAM (see Regional Limitations above)
* Consider using a different supported region
* Check Azure documentation for the latest regional availability

**Error: "CIDR not within parent pool"**

* Ensure child pool CIDR is a subset of parent pool
* Use [`isSubnet()`](src/azure-virtualnetworkmanager/lib/utils/cidr-validator.ts) to verify parent-child relationship
* Parent pool must contain all child pool address prefixes

**Error: "At least one address prefix is required"**

* Provide at least one valid CIDR block in the `addressPrefixes` array
* Ensure the array is not empty

## Complete End-to-End Example

Here's a comprehensive example showing a realistic AVNM setup with all child resources:

```python
import { App, TerraformStack } from "cdktf";
import { AzapiProvider } from "@microsoft/terraform-cdk-constructs/core-azure";
import { ResourceGroup } from "@microsoft/terraform-cdk-constructs/azure-resourcegroup";
import { VirtualNetwork } from "@microsoft/terraform-cdk-constructs/azure-virtualnetwork";
import { Subnet } from "@microsoft/terraform-cdk-constructs/azure-subnet";
import {
  VirtualNetworkManager,
  NetworkGroup,
  NetworkGroupStaticMember,
  ConnectivityConfiguration,
  SecurityAdminConfiguration,
  SecurityAdminRuleCollection,
  SecurityAdminRule
} from "@microsoft/terraform-cdk-constructs/azure-virtualnetworkmanager";

const app = new App();
const stack = new TerraformStack(app, "avnm-complete-example");

// Configure provider
new AzapiProvider(stack, "azapi", {});

// Create resource group
const resourceGroup = new ResourceGroup(stack, "rg", {
  name: "rg-network-management",
  location: "eastus",
  tags: {
    Environment: "Production",
    ManagedBy: "Terraform"
  }
});

// =============================================================================
// CREATE VIRTUAL NETWORKS
// =============================================================================

// Hub VNet
const hubVnet = new VirtualNetwork(stack, "hub-vnet", {
  name: "vnet-hub-eastus",
  location: resourceGroup.props.location!,
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.0.0.0/16"] }
});

new Subnet(stack, "hub-subnet", {
  name: "subnet-gateway",
  resourceGroupId: resourceGroup.id,
  virtualNetworkName: hubVnet.props.name!,
  virtualNetworkId: hubVnet.id,
  addressPrefix: "10.0.1.0/24"
});

// Production Spoke VNet
const prodVnet = new VirtualNetwork(stack, "prod-vnet", {
  name: "vnet-prod-eastus",
  location: resourceGroup.props.location!,
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.1.0.0/16"] },
  tags: { Environment: "Production" }
});

new Subnet(stack, "prod-subnet", {
  name: "subnet-app",
  resourceGroupId: resourceGroup.id,
  virtualNetworkName: prodVnet.props.name!,
  virtualNetworkId: prodVnet.id,
  addressPrefix: "10.1.1.0/24"
});

// Staging VNet
const stagingVnet = new VirtualNetwork(stack, "staging-vnet", {
  name: "vnet-staging-eastus",
  location: resourceGroup.props.location!,
  resourceGroupId: resourceGroup.id,
  addressSpace: { addressPrefixes: ["10.2.0.0/16"] },
  tags: { Environment: "Staging" }
});

new Subnet(stack, "staging-subnet", {
  name: "subnet-app",
  resourceGroupId: resourceGroup.id,
  virtualNetworkName: stagingVnet.props.name!,
  virtualNetworkId: stagingVnet.id,
  addressPrefix: "10.2.1.0/24"
});

// =============================================================================
// CREATE VIRTUAL NETWORK MANAGER
// =============================================================================

const networkManager = new VirtualNetworkManager(stack, "vnm", {
  name: "vnm-enterprise",
  location: resourceGroup.props.location!,
  resourceGroupName: resourceGroup.props.name!,
  networkManagerScopes: {
    subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"]
  },
  networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"],
  description: "Enterprise network management for production workloads",
  tags: {
    Environment: "Production",
    Purpose: "Network-Management"
  }
});

// =============================================================================
// CREATE NETWORK GROUPS (Using both patterns)
// =============================================================================

// Production group using convenience method
const productionGroup = networkManager.addNetworkGroup("prod-group", {
  name: "ng-production",
  description: "Production virtual networks",
  memberType: "VirtualNetwork"
});

// Staging group using convenience method
const stagingGroup = networkManager.addNetworkGroup("staging-group", {
  name: "ng-staging",
  description: "Staging virtual networks",
  memberType: "VirtualNetwork"
});

// Hub group using direct instantiation
const hubGroup = new NetworkGroup(stack, "hub-group", {
  name: "ng-hub",
  networkManagerId: networkManager.id,
  description: "Hub virtual network",
  memberType: "VirtualNetwork"
});

// =============================================================================
// ADD VNETS TO GROUPS
// =============================================================================

new NetworkGroupStaticMember(stack, "prod-vnet-member", {
  name: "member-prod-vnet",
  networkGroupId: productionGroup.id,
  resourceId: prodVnet.id
});

new NetworkGroupStaticMember(stack, "staging-vnet-member", {
  name: "member-staging-vnet",
  networkGroupId: stagingGroup.id,
  resourceId: stagingVnet.id
});

new NetworkGroupStaticMember(stack, "hub-vnet-member", {
  name: "member-hub-vnet",
  networkGroupId: hubGroup.id,
  resourceId: hubVnet.id
});

// =============================================================================
// CREATE CONNECTIVITY CONFIGURATIONS
// =============================================================================

// Hub-spoke for production
networkManager.addConnectivityConfiguration("hub-spoke-prod", {
  name: "conn-hub-spoke-production",
  connectivityTopology: "HubAndSpoke",
  description: "Hub-spoke topology for production with gateway transit",
  appliesToGroups: [
    {
      networkGroupId: productionGroup.id,
      useHubGateway: true,
      isGlobal: false
    }
  ],
  hubs: [
    {
      resourceId: hubVnet.id,
      resourceType: "Microsoft.Network/virtualNetworks"
    }
  ],
  deleteExistingPeering: true
});

// Mesh for non-production
new ConnectivityConfiguration(stack, "mesh-nonprod", {
  name: "conn-mesh-nonprod",
  networkManagerId: networkManager.id,
  connectivityTopology: "Mesh",
  description: "Mesh connectivity for staging environments",
  appliesToGroups: [
    {
      networkGroupId: stagingGroup.id,
      groupConnectivity: "DirectlyConnected",
      isGlobal: false
    }
  ],
  deleteExistingPeering: true,
  isGlobal: false
});

// =============================================================================
// CREATE SECURITY ADMIN CONFIGURATION
// =============================================================================

const securityConfig = networkManager.addSecurityAdminConfiguration("security", {
  name: "sec-org-policies",
  description: "Organization-wide security policies and controls"
});

// =============================================================================
// CREATE RULE COLLECTIONS
// =============================================================================

// Collection for blocking high-risk ports
const blockHighRiskPorts = new SecurityAdminRuleCollection(stack, "block-ports", {
  name: "rc-block-high-risk-ports",
  securityAdminConfigurationId: securityConfig.id,
  description: "Block SSH, RDP, and database ports from internet",
  appliesToGroups: [
    { networkGroupId: productionGroup.id },
    { networkGroupId: stagingGroup.id }
  ]
});

// Collection for mandatory allows
const mandatoryAllows = new SecurityAdminRuleCollection(stack, "mandatory-allows", {
  name: "rc-mandatory-allows",
  securityAdminConfigurationId: securityConfig.id,
  description: "Always allow monitoring and security scanner traffic",
  appliesToGroups: [
    { networkGroupId: productionGroup.id },
    { networkGroupId: stagingGroup.id },
    { networkGroupId: hubGroup.id }
  ]
});

// =============================================================================
// CREATE SECURITY ADMIN RULES
// =============================================================================

// Block SSH from internet (Deny action)
new SecurityAdminRule(stack, "block-ssh", {
  name: "rule-block-ssh",
  ruleCollectionId: blockHighRiskPorts.id,
  description: "Block SSH access from internet",
  priority: 100,
  action: "Deny",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["22"],
  sources: [
    { addressPrefix: "Internet", addressPrefixType: "ServiceTag" }
  ],
  destinations: [
    { addressPrefix: "*", addressPrefixType: "IPPrefix" }
  ]
});

// Block RDP from internet (Deny action)
new SecurityAdminRule(stack, "block-rdp", {
  name: "rule-block-rdp",
  ruleCollectionId: blockHighRiskPorts.id,
  description: "Block RDP access from internet",
  priority: 110,
  action: "Deny",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["3389"],
  sources: [
    { addressPrefix: "Internet", addressPrefixType: "ServiceTag" }
  ],
  destinations: [
    { addressPrefix: "*", addressPrefixType: "IPPrefix" }
  ]
});

// Block database ports from internet (Deny action)
new SecurityAdminRule(stack, "block-databases", {
  name: "rule-block-databases",
  ruleCollectionId: blockHighRiskPorts.id,
  description: "Block direct database access from internet",
  priority: 120,
  action: "Deny",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["1433", "3306", "5432"],
  sources: [
    { addressPrefix: "Internet", addressPrefixType: "ServiceTag" }
  ],
  destinations: [
    { addressPrefix: "*", addressPrefixType: "IPPrefix" }
  ]
});

// Always allow monitoring traffic (AlwaysAllow action)
new SecurityAdminRule(stack, "always-allow-monitoring", {
  name: "rule-always-allow-monitoring",
  ruleCollectionId: mandatoryAllows.id,
  description: "Always allow monitoring traffic - cannot be blocked by NSG",
  priority: 50,
  action: "AlwaysAllow",
  direction: "Inbound",
  protocol: "Any",
  sourcePortRanges: ["*"],
  destinationPortRanges: ["*"],
  sources: [
    { addressPrefix: "10.255.0.0/24", addressPrefixType: "IPPrefix" }
  ],
  destinations: [
    { addressPrefix: "*", addressPrefixType: "IPPrefix" }
  ]
});

// Allow HTTPS traffic (Allow action - NSG can override)
new SecurityAdminRule(stack, "allow-https", {
  name: "rule-allow-https",
  ruleCollectionId: mandatoryAllows.id,
  description: "Allow HTTPS traffic - NSG can still deny if needed",
  priority: 200,
  action: "Allow",
  direction: "Inbound",
  protocol: "Tcp",
  destinationPortRanges: ["443"],
  sources: [
    { addressPrefix: "*", addressPrefixType: "IPPrefix" }
  ],
  destinations: [
    { addressPrefix: "*", addressPrefixType: "IPPrefix" }
  ]
});

app.synth();
```

This example demonstrates:

1. **Network Manager Setup**: Creating a manager with subscription scope
2. **Network Groups**: Using both convenience methods and direct instantiation
3. **Static Members**: Adding specific VNets to groups
4. **Connectivity**: Both hub-spoke and mesh topologies
5. **Security**: Complete security admin configuration with multiple rule types
6. **Best Practices**: Organized structure with clear separation of concerns

## Troubleshooting

### Common Issues

1. **Scope Configuration Errors**: Ensure at least one of `managementGroups` or `subscriptions` is specified in `networkManagerScopes`.
2. **Permission Issues**: Ensure your Azure service principal has the appropriate permissions:

   * `Network Contributor` role on the resource group
   * Appropriate permissions on target subscriptions or management groups
3. **API Version Errors**: If you encounter API version errors, verify the version is supported (2024-05-01 or 2023-11-01).
4. **Naming Conflicts**: Virtual Network Manager names must be unique within a resource group. Use descriptive, unique names.
5. **Feature Availability**: Some features like Routing configurations require API version 2024-05-01 or later.

## Related Constructs

* [`ResourceGroup`](../azure-resourcegroup/README.md) - Azure Resource Groups
* [`VirtualNetwork`](../azure-virtualnetwork/README.md) - Azure Virtual Networks
* [`NetworkSecurityGroup`](../azure-networksecuritygroup/README.md) - Network Security Groups

## Additional Resources

### Azure Documentation

* [Azure Virtual Network Manager Overview](https://learn.microsoft.com/en-us/azure/virtual-network-manager/)
* [Network Groups](https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-network-groups)
* [Connectivity Configurations](https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-connectivity-configuration)
* [Security Admin Rules](https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-security-admins)
* [Hub-and-Spoke Topology](https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-connectivity-configuration#hub-and-spoke-topology)
* [Mesh Topology](https://learn.microsoft.com/en-us/azure/virtual-network-manager/concept-connectivity-configuration#mesh-topology)

### API References

* [Azure Virtual Network Manager REST API](https://learn.microsoft.com/en-us/rest/api/networkmanager/)
* [Network Groups API](https://learn.microsoft.com/en-us/rest/api/networkmanager/network-groups)
* [Connectivity Configurations API](https://learn.microsoft.com/en-us/rest/api/networkmanager/connectivity-configurations)
* [Security Admin Configurations API](https://learn.microsoft.com/en-us/rest/api/networkmanager/security-admin-configurations)

### Terraform & CDK

* [Terraform CDK Documentation](https://developer.hashicorp.com/terraform/cdktf)
* [Azure AZAPI Provider Documentation](https://registry.terraform.io/providers/Azure/azapi/latest/docs)

## Contributing

Contributions are welcome! Please see the [Contributing Guide](../../CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
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
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.AddConnectivityConfigurationProps",
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
        "applies_to_groups": "appliesToGroups",
        "connectivity_topology": "connectivityTopology",
        "delete_existing_peering": "deleteExistingPeering",
        "description": "description",
        "hubs": "hubs",
        "ignore_changes": "ignoreChanges",
        "is_global": "isGlobal",
    },
)
class AddConnectivityConfigurationProps(_AzapiResourceProps_141a2340):
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
        applies_to_groups: typing.Sequence[typing.Union["ConnectivityGroupItem", typing.Dict[builtins.str, typing.Any]]],
        connectivity_topology: builtins.str,
        delete_existing_peering: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        hubs: typing.Optional[typing.Sequence[typing.Union["Hub", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        is_global: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Properties for adding a ConnectivityConfiguration via the convenience method This interface excludes networkManagerId as it's automatically set.

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
        :param applies_to_groups: Network groups to apply this configuration to Each item specifies a network group and how it should connect.
        :param connectivity_topology: Connectivity topology type - HubAndSpoke: Central hub with spoke VNets - Mesh: All VNets can communicate directly.
        :param delete_existing_peering: Delete existing peerings when applying this configuration. Default: false
        :param description: Optional description of the connectivity configuration.
        :param hubs: Hub VNets for hub-and-spoke topology Required when connectivityTopology is "HubAndSpoke".
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param is_global: Enable global mesh connectivity Allows mesh connectivity across regions. Default: false
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9067cda1c1ca6604c5b19911c0aee21f4e9e0620d601c9afdba212b26c447e2d)
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
            check_type(argname="argument applies_to_groups", value=applies_to_groups, expected_type=type_hints["applies_to_groups"])
            check_type(argname="argument connectivity_topology", value=connectivity_topology, expected_type=type_hints["connectivity_topology"])
            check_type(argname="argument delete_existing_peering", value=delete_existing_peering, expected_type=type_hints["delete_existing_peering"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument hubs", value=hubs, expected_type=type_hints["hubs"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument is_global", value=is_global, expected_type=type_hints["is_global"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "applies_to_groups": applies_to_groups,
            "connectivity_topology": connectivity_topology,
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
        if delete_existing_peering is not None:
            self._values["delete_existing_peering"] = delete_existing_peering
        if description is not None:
            self._values["description"] = description
        if hubs is not None:
            self._values["hubs"] = hubs
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if is_global is not None:
            self._values["is_global"] = is_global

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
    def applies_to_groups(self) -> typing.List["ConnectivityGroupItem"]:
        '''Network groups to apply this configuration to Each item specifies a network group and how it should connect.'''
        result = self._values.get("applies_to_groups")
        assert result is not None, "Required property 'applies_to_groups' is missing"
        return typing.cast(typing.List["ConnectivityGroupItem"], result)

    @builtins.property
    def connectivity_topology(self) -> builtins.str:
        '''Connectivity topology type - HubAndSpoke: Central hub with spoke VNets - Mesh: All VNets can communicate directly.

        Example::

            "Mesh"
        '''
        result = self._values.get("connectivity_topology")
        assert result is not None, "Required property 'connectivity_topology' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def delete_existing_peering(self) -> typing.Optional[builtins.bool]:
        '''Delete existing peerings when applying this configuration.

        :default: false
        '''
        result = self._values.get("delete_existing_peering")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the connectivity configuration.

        Example::

            "Hub-and-spoke topology for production workloads"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def hubs(self) -> typing.Optional[typing.List["Hub"]]:
        '''Hub VNets for hub-and-spoke topology Required when connectivityTopology is "HubAndSpoke".

        Example::

            [{ resourceId: "/subscriptions/.../virtualNetworks/hub-vnet", resourceType: "Microsoft.Network/virtualNetworks" }]
        '''
        result = self._values.get("hubs")
        return typing.cast(typing.Optional[typing.List["Hub"]], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def is_global(self) -> typing.Optional[builtins.bool]:
        '''Enable global mesh connectivity Allows mesh connectivity across regions.

        :default: false
        '''
        result = self._values.get("is_global")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AddConnectivityConfigurationProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.AddIpamPoolProps",
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
        "address_prefixes": "addressPrefixes",
        "description": "description",
        "display_name": "displayName",
        "ignore_changes": "ignoreChanges",
        "parent_pool_name": "parentPoolName",
    },
)
class AddIpamPoolProps(_AzapiResourceProps_141a2340):
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
        address_prefixes: typing.Sequence[builtins.str],
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parent_pool_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for adding an IpamPool via the convenience method This interface excludes networkManagerId as it's automatically set.

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
        :param address_prefixes: IP address prefixes for the pool Must be valid CIDR notation (e.g., "10.0.0.0/8") Multiple prefixes must not overlap.
        :param description: Optional description of the IPAM pool.
        :param display_name: Optional friendly display name.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param parent_pool_name: Name of parent pool for hierarchical pools Leave empty/undefined for root pools.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4ef1b60542c80aedd698ead341c83c9ab8812f6600a6a68f400f020b584e2130)
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
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument parent_pool_name", value=parent_pool_name, expected_type=type_hints["parent_pool_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
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
        if parent_pool_name is not None:
            self._values["parent_pool_name"] = parent_pool_name

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
    def address_prefixes(self) -> typing.List[builtins.str]:
        '''IP address prefixes for the pool Must be valid CIDR notation (e.g., "10.0.0.0/8") Multiple prefixes must not overlap.

        Example::

            ["10.0.0.0/8", "172.16.0.0/12"]
        '''
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the IPAM pool.

        Example::

            "Production IP address pool for East US region"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''Optional friendly display name.

        Example::

            "East US Production Pool"
        '''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def parent_pool_name(self) -> typing.Optional[builtins.str]:
        '''Name of parent pool for hierarchical pools Leave empty/undefined for root pools.

        Example::

            "root-pool"
        '''
        result = self._values.get("parent_pool_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AddIpamPoolProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.AddNetworkGroupProps",
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
        "description": "description",
        "ignore_changes": "ignoreChanges",
        "member_type": "memberType",
    },
)
class AddNetworkGroupProps(_AzapiResourceProps_141a2340):
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
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        member_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for adding a NetworkGroup via the convenience method This interface excludes networkManagerId as it's automatically set.

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
        :param description: Optional description of the network group.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param member_type: Type of members in this network group. Default: undefined (can contain both VirtualNetwork and Subnet members)
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c8953b486069d04eee14dbd37c1c98147b6aebdd8762a6dcaf93e02cd248a5bb)
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
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument member_type", value=member_type, expected_type=type_hints["member_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
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
        if member_type is not None:
            self._values["member_type"] = member_type

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
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the network group.

        Example::

            "Production virtual networks for region East US"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def member_type(self) -> typing.Optional[builtins.str]:
        '''Type of members in this network group.

        :default: undefined (can contain both VirtualNetwork and Subnet members)

        Example::

            "Subnet"
        '''
        result = self._values.get("member_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AddNetworkGroupProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.AddSecurityAdminConfigurationProps",
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
        "apply_on_network_intent_policy_based_services": "applyOnNetworkIntentPolicyBasedServices",
        "description": "description",
        "ignore_changes": "ignoreChanges",
    },
)
class AddSecurityAdminConfigurationProps(_AzapiResourceProps_141a2340):
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
        apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for adding a SecurityAdminConfiguration via the convenience method This interface excludes networkManagerId as it's automatically set.

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
        :param apply_on_network_intent_policy_based_services: Services to apply the security admin configuration on.
        :param description: Optional description of the security admin configuration.
        :param ignore_changes: The lifecycle rules to ignore changes.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e762870ecd662ea069dec416817d543c9a8fc2b66397cb08ff21d7e97505b574)
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
            check_type(argname="argument apply_on_network_intent_policy_based_services", value=apply_on_network_intent_policy_based_services, expected_type=type_hints["apply_on_network_intent_policy_based_services"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
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
        if apply_on_network_intent_policy_based_services is not None:
            self._values["apply_on_network_intent_policy_based_services"] = apply_on_network_intent_policy_based_services
        if description is not None:
            self._values["description"] = description
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes

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
    def apply_on_network_intent_policy_based_services(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        '''Services to apply the security admin configuration on.

        Example::

            ["All"]
        '''
        result = self._values.get("apply_on_network_intent_policy_based_services")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the security admin configuration.

        Example::

            "Organization-wide security rules for production workloads"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AddSecurityAdminConfigurationProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.AddressPrefixItem",
    jsii_struct_bases=[],
    name_mapping={
        "address_prefix": "addressPrefix",
        "address_prefix_type": "addressPrefixType",
    },
)
class AddressPrefixItem:
    def __init__(
        self,
        *,
        address_prefix: typing.Optional[builtins.str] = None,
        address_prefix_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Address prefix item for sources or destinations.

        :param address_prefix: 
        :param address_prefix_type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0e4ddf951b63d0f5ce781f49a76c09701d5028bcc2f424a4cc463abf14536198)
            check_type(argname="argument address_prefix", value=address_prefix, expected_type=type_hints["address_prefix"])
            check_type(argname="argument address_prefix_type", value=address_prefix_type, expected_type=type_hints["address_prefix_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if address_prefix is not None:
            self._values["address_prefix"] = address_prefix
        if address_prefix_type is not None:
            self._values["address_prefix_type"] = address_prefix_type

    @builtins.property
    def address_prefix(self) -> typing.Optional[builtins.str]:
        result = self._values.get("address_prefix")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def address_prefix_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("address_prefix_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AddressPrefixItem(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.CidrValidationResult",
    jsii_struct_bases=[],
    name_mapping={"errors": "errors", "valid": "valid", "warnings": "warnings"},
)
class CidrValidationResult:
    def __init__(
        self,
        *,
        errors: typing.Sequence[builtins.str],
        valid: builtins.bool,
        warnings: typing.Sequence[builtins.str],
    ) -> None:
        '''Result of CIDR validation operations.

        :param errors: List of validation errors.
        :param valid: Whether the validation passed.
        :param warnings: List of validation warnings.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fe9782844d5cce439426f3b2fe6540622615e1bb02269b283ee2483698c4111f)
            check_type(argname="argument errors", value=errors, expected_type=type_hints["errors"])
            check_type(argname="argument valid", value=valid, expected_type=type_hints["valid"])
            check_type(argname="argument warnings", value=warnings, expected_type=type_hints["warnings"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "errors": errors,
            "valid": valid,
            "warnings": warnings,
        }

    @builtins.property
    def errors(self) -> typing.List[builtins.str]:
        '''List of validation errors.'''
        result = self._values.get("errors")
        assert result is not None, "Required property 'errors' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def valid(self) -> builtins.bool:
        '''Whether the validation passed.'''
        result = self._values.get("valid")
        assert result is not None, "Required property 'valid' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def warnings(self) -> typing.List[builtins.str]:
        '''List of validation warnings.'''
        result = self._values.get("warnings")
        assert result is not None, "Required property 'warnings' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CidrValidationResult(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ConnectivityConfiguration(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.ConnectivityConfiguration",
):
    '''Azure Virtual Network Manager Connectivity Configuration implementation.

    Connectivity configurations define the network topology (mesh or hub-and-spoke) for
    virtual networks. They enable automated peering management at scale and support both
    regional and global connectivity scenarios.

    Example::

        // Mesh topology:
        const meshConfig = new ConnectivityConfiguration(this, "mesh", {
          name: "development-mesh",
          networkManagerId: networkManager.id,
          description: "Mesh for development VNets",
          connectivityTopology: "Mesh",
          appliesToGroups: [{
            networkGroupId: devGroup.id,
            groupConnectivity: "DirectlyConnected",
            isGlobal: false
          }],
          isGlobal: false
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        applies_to_groups: typing.Sequence[typing.Union["ConnectivityGroupItem", typing.Dict[builtins.str, typing.Any]]],
        connectivity_topology: builtins.str,
        network_manager_id: builtins.str,
        delete_existing_peering: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        hubs: typing.Optional[typing.Sequence[typing.Union["Hub", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        is_global: typing.Optional[builtins.bool] = None,
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
        '''Creates a new Azure Virtual Network Manager Connectivity Configuration using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param applies_to_groups: Network groups to apply this configuration to Each item specifies a network group and how it should connect.
        :param connectivity_topology: Connectivity topology type - HubAndSpoke: Central hub with spoke VNets - Mesh: All VNets can communicate directly.
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param delete_existing_peering: Delete existing peerings when applying this configuration. Default: false
        :param description: Optional description of the connectivity configuration.
        :param hubs: Hub VNets for hub-and-spoke topology Required when connectivityTopology is "HubAndSpoke".
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param is_global: Enable global mesh connectivity Allows mesh connectivity across regions. Default: false
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
            type_hints = typing.get_type_hints(_typecheckingstub__d1ff32f53e75259a5a3d4754e183ce80c858ae2f0f9b1730fb52b423e1caef7f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ConnectivityConfigurationProps(
            applies_to_groups=applies_to_groups,
            connectivity_topology=connectivity_topology,
            network_manager_id=network_manager_id,
            delete_existing_peering=delete_existing_peering,
            description=description,
            hubs=hubs,
            ignore_changes=ignore_changes,
            is_global=is_global,
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
            type_hints = typing.get_type_hints(_typecheckingstub__7b262c98cad6d0553aef0d36bfdf17e7fc11ae842759700686341dd153d4aa43)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Connectivity Configuration Connectivity Configurations are scoped to Network Managers.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__053c84ec0645a236be4d383be7e0409703f3c567088abe3fb65394a6c05e01f5)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Connectivity Configurations.'''
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
    def props(self) -> "ConnectivityConfigurationProps":
        '''The input properties for this Connectivity Configuration instance.'''
        return typing.cast("ConnectivityConfigurationProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Connectivity Configuration.'''
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
    @jsii.member(jsii_name="topology")
    def topology(self) -> builtins.str:
        '''Get the connectivity topology type.'''
        return typing.cast(builtins.str, jsii.get(self, "topology"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.ConnectivityConfigurationBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class ConnectivityConfigurationBody:
    def __init__(
        self,
        *,
        properties: typing.Union["ConnectivityConfigurationProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Connectivity Configuration API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = ConnectivityConfigurationProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f488d7ef1b83639e2f05268d756710a7e6d455e01af72c9faed253e2c5d8ff0b)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "ConnectivityConfigurationProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("ConnectivityConfigurationProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ConnectivityConfigurationBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.ConnectivityConfigurationProperties",
    jsii_struct_bases=[],
    name_mapping={
        "applies_to_groups": "appliesToGroups",
        "connectivity_topology": "connectivityTopology",
        "delete_existing_peering": "deleteExistingPeering",
        "description": "description",
        "hubs": "hubs",
        "is_global": "isGlobal",
    },
)
class ConnectivityConfigurationProperties:
    def __init__(
        self,
        *,
        applies_to_groups: typing.Sequence[typing.Union["ConnectivityGroupItem", typing.Dict[builtins.str, typing.Any]]],
        connectivity_topology: builtins.str,
        delete_existing_peering: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        hubs: typing.Optional[typing.Sequence[typing.Union["Hub", typing.Dict[builtins.str, typing.Any]]]] = None,
        is_global: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Properties for Connectivity Configuration body.

        :param applies_to_groups: 
        :param connectivity_topology: 
        :param delete_existing_peering: 
        :param description: 
        :param hubs: 
        :param is_global: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e7f6ff7f657ef34c950d8200ccedba92bb4eb603d5e731f65664ebe81b917c34)
            check_type(argname="argument applies_to_groups", value=applies_to_groups, expected_type=type_hints["applies_to_groups"])
            check_type(argname="argument connectivity_topology", value=connectivity_topology, expected_type=type_hints["connectivity_topology"])
            check_type(argname="argument delete_existing_peering", value=delete_existing_peering, expected_type=type_hints["delete_existing_peering"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument hubs", value=hubs, expected_type=type_hints["hubs"])
            check_type(argname="argument is_global", value=is_global, expected_type=type_hints["is_global"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "applies_to_groups": applies_to_groups,
            "connectivity_topology": connectivity_topology,
        }
        if delete_existing_peering is not None:
            self._values["delete_existing_peering"] = delete_existing_peering
        if description is not None:
            self._values["description"] = description
        if hubs is not None:
            self._values["hubs"] = hubs
        if is_global is not None:
            self._values["is_global"] = is_global

    @builtins.property
    def applies_to_groups(self) -> typing.List["ConnectivityGroupItem"]:
        result = self._values.get("applies_to_groups")
        assert result is not None, "Required property 'applies_to_groups' is missing"
        return typing.cast(typing.List["ConnectivityGroupItem"], result)

    @builtins.property
    def connectivity_topology(self) -> builtins.str:
        result = self._values.get("connectivity_topology")
        assert result is not None, "Required property 'connectivity_topology' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def delete_existing_peering(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("delete_existing_peering")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def hubs(self) -> typing.Optional[typing.List["Hub"]]:
        result = self._values.get("hubs")
        return typing.cast(typing.Optional[typing.List["Hub"]], result)

    @builtins.property
    def is_global(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("is_global")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ConnectivityConfigurationProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.ConnectivityConfigurationProps",
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
        "applies_to_groups": "appliesToGroups",
        "connectivity_topology": "connectivityTopology",
        "network_manager_id": "networkManagerId",
        "delete_existing_peering": "deleteExistingPeering",
        "description": "description",
        "hubs": "hubs",
        "ignore_changes": "ignoreChanges",
        "is_global": "isGlobal",
    },
)
class ConnectivityConfigurationProps(_AzapiResourceProps_141a2340):
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
        applies_to_groups: typing.Sequence[typing.Union["ConnectivityGroupItem", typing.Dict[builtins.str, typing.Any]]],
        connectivity_topology: builtins.str,
        network_manager_id: builtins.str,
        delete_existing_peering: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        hubs: typing.Optional[typing.Sequence[typing.Union["Hub", typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        is_global: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager Connectivity Configuration.

        Extends AzapiResourceProps with Connectivity Configuration specific properties

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
        :param applies_to_groups: Network groups to apply this configuration to Each item specifies a network group and how it should connect.
        :param connectivity_topology: Connectivity topology type - HubAndSpoke: Central hub with spoke VNets - Mesh: All VNets can communicate directly.
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param delete_existing_peering: Delete existing peerings when applying this configuration. Default: false
        :param description: Optional description of the connectivity configuration.
        :param hubs: Hub VNets for hub-and-spoke topology Required when connectivityTopology is "HubAndSpoke".
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param is_global: Enable global mesh connectivity Allows mesh connectivity across regions. Default: false
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__52a7359b599ad07d1908828c4605eb7f0d1616917586f4ed136af9dea4c59585)
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
            check_type(argname="argument applies_to_groups", value=applies_to_groups, expected_type=type_hints["applies_to_groups"])
            check_type(argname="argument connectivity_topology", value=connectivity_topology, expected_type=type_hints["connectivity_topology"])
            check_type(argname="argument network_manager_id", value=network_manager_id, expected_type=type_hints["network_manager_id"])
            check_type(argname="argument delete_existing_peering", value=delete_existing_peering, expected_type=type_hints["delete_existing_peering"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument hubs", value=hubs, expected_type=type_hints["hubs"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument is_global", value=is_global, expected_type=type_hints["is_global"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "applies_to_groups": applies_to_groups,
            "connectivity_topology": connectivity_topology,
            "network_manager_id": network_manager_id,
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
        if delete_existing_peering is not None:
            self._values["delete_existing_peering"] = delete_existing_peering
        if description is not None:
            self._values["description"] = description
        if hubs is not None:
            self._values["hubs"] = hubs
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if is_global is not None:
            self._values["is_global"] = is_global

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
    def applies_to_groups(self) -> typing.List["ConnectivityGroupItem"]:
        '''Network groups to apply this configuration to Each item specifies a network group and how it should connect.'''
        result = self._values.get("applies_to_groups")
        assert result is not None, "Required property 'applies_to_groups' is missing"
        return typing.cast(typing.List["ConnectivityGroupItem"], result)

    @builtins.property
    def connectivity_topology(self) -> builtins.str:
        '''Connectivity topology type - HubAndSpoke: Central hub with spoke VNets - Mesh: All VNets can communicate directly.

        Example::

            "Mesh"
        '''
        result = self._values.get("connectivity_topology")
        assert result is not None, "Required property 'connectivity_topology' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def network_manager_id(self) -> builtins.str:
        '''Resource ID of the parent Network Manager.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm"
        '''
        result = self._values.get("network_manager_id")
        assert result is not None, "Required property 'network_manager_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def delete_existing_peering(self) -> typing.Optional[builtins.bool]:
        '''Delete existing peerings when applying this configuration.

        :default: false
        '''
        result = self._values.get("delete_existing_peering")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the connectivity configuration.

        Example::

            "Hub-and-spoke topology for production workloads"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def hubs(self) -> typing.Optional[typing.List["Hub"]]:
        '''Hub VNets for hub-and-spoke topology Required when connectivityTopology is "HubAndSpoke".

        Example::

            [{ resourceId: "/subscriptions/.../virtualNetworks/hub-vnet", resourceType: "Microsoft.Network/virtualNetworks" }]
        '''
        result = self._values.get("hubs")
        return typing.cast(typing.Optional[typing.List["Hub"]], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def is_global(self) -> typing.Optional[builtins.bool]:
        '''Enable global mesh connectivity Allows mesh connectivity across regions.

        :default: false
        '''
        result = self._values.get("is_global")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ConnectivityConfigurationProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.ConnectivityGroupItem",
    jsii_struct_bases=[],
    name_mapping={
        "network_group_id": "networkGroupId",
        "group_connectivity": "groupConnectivity",
        "is_global": "isGlobal",
        "use_hub_gateway": "useHubGateway",
    },
)
class ConnectivityGroupItem:
    def __init__(
        self,
        *,
        network_group_id: builtins.str,
        group_connectivity: typing.Optional[builtins.str] = None,
        is_global: typing.Optional[builtins.bool] = None,
        use_hub_gateway: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Network group reference for connectivity configuration.

        :param network_group_id: 
        :param group_connectivity: 
        :param is_global: 
        :param use_hub_gateway: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eb61833fbaa1cfdc48376948e6ee5a955d10784354894bfef1bc936a8ce46ab5)
            check_type(argname="argument network_group_id", value=network_group_id, expected_type=type_hints["network_group_id"])
            check_type(argname="argument group_connectivity", value=group_connectivity, expected_type=type_hints["group_connectivity"])
            check_type(argname="argument is_global", value=is_global, expected_type=type_hints["is_global"])
            check_type(argname="argument use_hub_gateway", value=use_hub_gateway, expected_type=type_hints["use_hub_gateway"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_group_id": network_group_id,
        }
        if group_connectivity is not None:
            self._values["group_connectivity"] = group_connectivity
        if is_global is not None:
            self._values["is_global"] = is_global
        if use_hub_gateway is not None:
            self._values["use_hub_gateway"] = use_hub_gateway

    @builtins.property
    def network_group_id(self) -> builtins.str:
        result = self._values.get("network_group_id")
        assert result is not None, "Required property 'network_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def group_connectivity(self) -> typing.Optional[builtins.str]:
        result = self._values.get("group_connectivity")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def is_global(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("is_global")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def use_hub_gateway(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("use_hub_gateway")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ConnectivityGroupItem(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.Hub",
    jsii_struct_bases=[],
    name_mapping={"resource_id": "resourceId", "resource_type": "resourceType"},
)
class Hub:
    def __init__(
        self,
        *,
        resource_id: builtins.str,
        resource_type: builtins.str,
    ) -> None:
        '''Hub configuration for hub-and-spoke topology.

        :param resource_id: 
        :param resource_type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__58c9c055f69994425655e1bd56b47d4bc4fc45630b7391a69478a2944dbbb8b5)
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "resource_id": resource_id,
            "resource_type": resource_type,
        }

    @builtins.property
    def resource_id(self) -> builtins.str:
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_type(self) -> builtins.str:
        result = self._values.get("resource_type")
        assert result is not None, "Required property 'resource_type' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Hub(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class IpamPool(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPool",
):
    '''Azure Virtual Network Manager IPAM Pool implementation.

    IPAM Pools provide centralized IP address management for virtual networks,
    enabling automatic CIDR allocation, overlap prevention, and hierarchical
    address space organization. They are essential for managing IP addresses
    at scale across multiple virtual networks and subscriptions.

    Example::

        // Hierarchical pool with parent reference:
        const childPool = new IpamPool(this, "eastus-pool", {
          name: "eastus-pool",
          location: "eastus",
          networkManagerId: networkManager.id,
          addressPrefixes: ["10.1.0.0/16"],
          parentPoolName: "production-pool",
          description: "East US regional pool"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        address_prefixes: typing.Sequence[builtins.str],
        network_manager_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parent_pool_name: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Virtual Network Manager IPAM Pool using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param address_prefixes: IP address prefixes for the pool Must be valid CIDR notation (e.g., "10.0.0.0/8") Multiple prefixes must not overlap.
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param description: Optional description of the IPAM pool.
        :param display_name: Optional friendly display name.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param parent_pool_name: Name of parent pool for hierarchical pools Leave empty/undefined for root pools.
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
            type_hints = typing.get_type_hints(_typecheckingstub__478fc237f17c3abd500163dd06e9d933e2c663a76352e1c0669faf9c18d02983)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = IpamPoolProps(
            address_prefixes=address_prefixes,
            network_manager_id=network_manager_id,
            description=description,
            display_name=display_name,
            ignore_changes=ignore_changes,
            parent_pool_name=parent_pool_name,
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
            type_hints = typing.get_type_hints(_typecheckingstub__f1b5825e99d9e0955cd52540fb724e8a0b11c80035a3a25d32db9d5bfa2dd846)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the IPAM Pool IPAM Pools are scoped to Network Managers.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2efba36cdf487fb1b14d1ce5fbb195ee1637f0757605f6522b7a73a47d1caade)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for IPAM Pools.'''
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
    def props(self) -> "IpamPoolProps":
        '''The input properties for this IPAM Pool instance.'''
        return typing.cast("IpamPoolProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceName")
    def resource_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceName"))

    @builtins.property
    @jsii.member(jsii_name="totalAddressCount")
    def total_address_count(self) -> jsii.Number:
        '''Calculate total number of IP addresses in this pool Sums up all addresses from all CIDR blocks.

        :return: Total count of IP addresses across all prefixes

        Example::

            const pool = new IpamPool(this, "pool", {
              addressPrefixes: ["10.0.0.0/24", "10.1.0.0/24"]
            });
            console.log(pool.totalAddressCount); // 512 (256 + 256)
        '''
        return typing.cast(jsii.Number, jsii.get(self, "totalAddressCount"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class IpamPoolBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["IpamPoolProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure IPAM Pool API calls.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = IpamPoolProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__06488cb4f1d496e46e5d857153ac0208e29af9521cfe41a86003ce88daef0d1d)
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
    def properties(self) -> "IpamPoolProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("IpamPoolProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpamPoolBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolProperties",
    jsii_struct_bases=[],
    name_mapping={
        "address_prefixes": "addressPrefixes",
        "description": "description",
        "display_name": "displayName",
        "parent_pool_name": "parentPoolName",
    },
)
class IpamPoolProperties:
    def __init__(
        self,
        *,
        address_prefixes: typing.Sequence[builtins.str],
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        parent_pool_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for IPAM Pool body.

        :param address_prefixes: 
        :param description: 
        :param display_name: 
        :param parent_pool_name: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7f8e99cafa7ef3b7de0dd6b963e4a27e1795de84bf286b26b3dd5e41aefeb9ab)
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument parent_pool_name", value=parent_pool_name, expected_type=type_hints["parent_pool_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
        }
        if description is not None:
            self._values["description"] = description
        if display_name is not None:
            self._values["display_name"] = display_name
        if parent_pool_name is not None:
            self._values["parent_pool_name"] = parent_pool_name

    @builtins.property
    def address_prefixes(self) -> typing.List[builtins.str]:
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parent_pool_name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("parent_pool_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpamPoolProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolProps",
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
        "address_prefixes": "addressPrefixes",
        "network_manager_id": "networkManagerId",
        "description": "description",
        "display_name": "displayName",
        "ignore_changes": "ignoreChanges",
        "parent_pool_name": "parentPoolName",
    },
)
class IpamPoolProps(_AzapiResourceProps_141a2340):
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
        address_prefixes: typing.Sequence[builtins.str],
        network_manager_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parent_pool_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager IPAM Pool.

        Extends AzapiResourceProps with IPAM Pool specific properties

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
        :param address_prefixes: IP address prefixes for the pool Must be valid CIDR notation (e.g., "10.0.0.0/8") Multiple prefixes must not overlap.
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param description: Optional description of the IPAM pool.
        :param display_name: Optional friendly display name.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param parent_pool_name: Name of parent pool for hierarchical pools Leave empty/undefined for root pools.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a1e87725ac84c620b8638278addf40bd21d197632007e0210f62fdecf2d991c3)
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
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
            check_type(argname="argument network_manager_id", value=network_manager_id, expected_type=type_hints["network_manager_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument display_name", value=display_name, expected_type=type_hints["display_name"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument parent_pool_name", value=parent_pool_name, expected_type=type_hints["parent_pool_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
            "network_manager_id": network_manager_id,
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
        if parent_pool_name is not None:
            self._values["parent_pool_name"] = parent_pool_name

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
    def address_prefixes(self) -> typing.List[builtins.str]:
        '''IP address prefixes for the pool Must be valid CIDR notation (e.g., "10.0.0.0/8") Multiple prefixes must not overlap.

        Example::

            ["10.0.0.0/8", "172.16.0.0/12"]
        '''
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def network_manager_id(self) -> builtins.str:
        '''Resource ID of the parent Network Manager.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm"
        '''
        result = self._values.get("network_manager_id")
        assert result is not None, "Required property 'network_manager_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the IPAM pool.

        Example::

            "Production IP address pool for East US region"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def display_name(self) -> typing.Optional[builtins.str]:
        '''Optional friendly display name.

        Example::

            "East US Production Pool"
        '''
        result = self._values.get("display_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def parent_pool_name(self) -> typing.Optional[builtins.str]:
        '''Name of parent pool for hierarchical pools Leave empty/undefined for root pools.

        Example::

            "root-pool"
        '''
        result = self._values.get("parent_pool_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpamPoolProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class IpamPoolStaticCidr(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolStaticCidr",
):
    '''Azure Virtual Network Manager IPAM Pool Static CIDR implementation.

    Static CIDRs explicitly allocate IP address blocks within an IPAM pool,
    providing precise control over address space reservations. This is useful
    for manual IP address management or reserving specific ranges for particular
    purposes within the larger pool.

    Example::

        // Allocate with explicit IP count:
        const staticCidr = new IpamPoolStaticCidr(this, "database-servers", {
          name: "db-servers-cidr",
          ipamPoolId: ipamPool.id,
          addressPrefixes: ["10.0.2.0/24"],
          description: "Reserved for database servers",
          apiVersion: "2024-05-01"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        address_prefixes: typing.Sequence[builtins.str],
        ipam_pool_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
        '''Creates a new Azure Virtual Network Manager IPAM Pool Static CIDR using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param address_prefixes: Array of IP address prefixes in CIDR notation Must be valid CIDR format (e.g., ["10.0.0.0/24"]) Must be contained within the parent pool's address space.
        :param ipam_pool_id: Resource ID of the parent IPAM Pool.
        :param description: Optional description of the static CIDR allocation.
        :param ignore_changes: The lifecycle rules to ignore changes.
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
            type_hints = typing.get_type_hints(_typecheckingstub__eb4df849139f35ea82eba3f6495e5592b7cc63a88da8362965ae492598b7336b)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = IpamPoolStaticCidrProps(
            address_prefixes=address_prefixes,
            ipam_pool_id=ipam_pool_id,
            description=description,
            ignore_changes=ignore_changes,
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
        '''Creates the resource body for the Azure API call Note: Child resources do not include location or tags.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee6fbdb9dd4215a9694e78c5d30b790b5886141a04d95f4d752d86f12e30bab2)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Static CIDR Static CIDRs are scoped to IPAM Pools.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1d14ddd57e8b26a1dc99e79ea7f3a98637e8d1a7596b4c78c1ac667ae8ab6018)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Static CIDRs.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="addressPrefixes")
    def address_prefixes(self) -> typing.List[builtins.str]:
        '''Get the address prefixes of this Static CIDR Returns the input addressPrefixes array.'''
        return typing.cast(typing.List[builtins.str], jsii.get(self, "addressPrefixes"))

    @builtins.property
    @jsii.member(jsii_name="addressPrefixOutput")
    def address_prefix_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "addressPrefixOutput"))

    @builtins.property
    @jsii.member(jsii_name="calculatedAddressCount")
    def calculated_address_count(self) -> jsii.Number:
        '''Get the calculated number of IP addresses in this CIDR block This is automatically calculated from the CIDR prefix at construct creation time.

        :return: Total count of IP addresses in the CIDR block

        Example::

            const staticCidr = new IpamPoolStaticCidr(this, "cidr", {
              addressPrefixes: ["10.0.1.0/24"]
            });
            console.log(staticCidr.calculatedAddressCount); // 256
        '''
        return typing.cast(jsii.Number, jsii.get(self, "calculatedAddressCount"))

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
    def props(self) -> "IpamPoolStaticCidrProps":
        '''The input properties for this Static CIDR instance.'''
        return typing.cast("IpamPoolStaticCidrProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Static CIDR.'''
        return typing.cast(builtins.str, jsii.get(self, "provisioningState"))

    @builtins.property
    @jsii.member(jsii_name="resourceName")
    def resource_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceName"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolStaticCidrBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class IpamPoolStaticCidrBody:
    def __init__(
        self,
        *,
        properties: typing.Union["IpamPoolStaticCidrProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Static CIDR API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = IpamPoolStaticCidrProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a6206392e666bb5236ace2451d32e2438bd940b6245959f8420928a91d11f1df)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "IpamPoolStaticCidrProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("IpamPoolStaticCidrProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpamPoolStaticCidrBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolStaticCidrProperties",
    jsii_struct_bases=[],
    name_mapping={"address_prefixes": "addressPrefixes", "description": "description"},
)
class IpamPoolStaticCidrProperties:
    def __init__(
        self,
        *,
        address_prefixes: typing.Sequence[builtins.str],
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for Static CIDR body.

        :param address_prefixes: 
        :param description: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13c9c9827a4dd6bb3bb47f08c26fa9f85627064954d227f717628179da7aacc2)
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
        }
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def address_prefixes(self) -> typing.List[builtins.str]:
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpamPoolStaticCidrProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.IpamPoolStaticCidrProps",
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
        "address_prefixes": "addressPrefixes",
        "ipam_pool_id": "ipamPoolId",
        "description": "description",
        "ignore_changes": "ignoreChanges",
    },
)
class IpamPoolStaticCidrProps(_AzapiResourceProps_141a2340):
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
        address_prefixes: typing.Sequence[builtins.str],
        ipam_pool_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager IPAM Pool Static CIDR.

        Extends AzapiResourceProps with Static CIDR specific properties

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
        :param address_prefixes: Array of IP address prefixes in CIDR notation Must be valid CIDR format (e.g., ["10.0.0.0/24"]) Must be contained within the parent pool's address space.
        :param ipam_pool_id: Resource ID of the parent IPAM Pool.
        :param description: Optional description of the static CIDR allocation.
        :param ignore_changes: The lifecycle rules to ignore changes.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__026a1c71e560d8d377bb28676a42ec08b6937b6ab584bc6e989c9a87a46a68aa)
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
            check_type(argname="argument address_prefixes", value=address_prefixes, expected_type=type_hints["address_prefixes"])
            check_type(argname="argument ipam_pool_id", value=ipam_pool_id, expected_type=type_hints["ipam_pool_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "address_prefixes": address_prefixes,
            "ipam_pool_id": ipam_pool_id,
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
    def address_prefixes(self) -> typing.List[builtins.str]:
        '''Array of IP address prefixes in CIDR notation Must be valid CIDR format (e.g., ["10.0.0.0/24"]) Must be contained within the parent pool's address space.

        Example::

            ["10.0.1.0/24"]
        '''
        result = self._values.get("address_prefixes")
        assert result is not None, "Required property 'address_prefixes' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def ipam_pool_id(self) -> builtins.str:
        '''Resource ID of the parent IPAM Pool.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm/ipamPools/prod-pool"
        '''
        result = self._values.get("ipam_pool_id")
        assert result is not None, "Required property 'ipam_pool_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the static CIDR allocation.

        Example::

            "Reserved for production web servers"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "IpamPoolStaticCidrProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class NetworkGroup(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroup",
):
    '''Azure Virtual Network Manager Network Group implementation.

    Network Groups are logical containers for virtual networks or subnets that allow you to
    apply connectivity, security, or routing configurations at scale. They are a foundational
    component required by connectivity configurations, security admin configurations, and
    routing configurations.

    Example::

        // Network group with explicit version pinning:
        const devGroup = new NetworkGroup(this, "dev-group", {
          name: "development-vnets",
          networkManagerId: networkManager.id,
          apiVersion: "2024-05-01",
          description: "Development virtual networks"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        network_manager_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        member_type: typing.Optional[builtins.str] = None,
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
        '''Creates a new Azure Virtual Network Manager Network Group using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param description: Optional description of the network group.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param member_type: Type of members in this network group. Default: undefined (can contain both VirtualNetwork and Subnet members)
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
            type_hints = typing.get_type_hints(_typecheckingstub__82b257d3748ba2718b6f141ec0c5214286a9db1ccad9fdb7c1e730c0ed4794cf)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = NetworkGroupProps(
            network_manager_id=network_manager_id,
            description=description,
            ignore_changes=ignore_changes,
            member_type=member_type,
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
            type_hints = typing.get_type_hints(_typecheckingstub__8c88f333525baf98ffdda159d1da4c6da25b597cb8ca98bc65b7609ca32dd9d7)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Network Group Network Groups are scoped to Network Managers.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3f1c558c14dc1978789dba46f4692eadae5f6fd3814e2ce81b440c6c518f39f5)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Network Groups.'''
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
    def props(self) -> "NetworkGroupProps":
        '''The input properties for this Network Group instance.'''
        return typing.cast("NetworkGroupProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Network Group.'''
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
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class NetworkGroupBody:
    def __init__(
        self,
        *,
        properties: typing.Optional[typing.Union["NetworkGroupProperties", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''The resource body interface for Azure Network Group API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = NetworkGroupProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e0068555a8322d50865dfac53c54fbed95d7c828cc11858159ece52dc93fa154)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if properties is not None:
            self._values["properties"] = properties

    @builtins.property
    def properties(self) -> typing.Optional["NetworkGroupProperties"]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional["NetworkGroupProperties"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkGroupBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupProperties",
    jsii_struct_bases=[],
    name_mapping={"description": "description", "member_type": "memberType"},
)
class NetworkGroupProperties:
    def __init__(
        self,
        *,
        description: typing.Optional[builtins.str] = None,
        member_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for Network Group body.

        :param description: 
        :param member_type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c0ecad6ba61dce163e3aee8cc642ba6c6cc83b1c540d7d6f2654bb2358aac15d)
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument member_type", value=member_type, expected_type=type_hints["member_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if description is not None:
            self._values["description"] = description
        if member_type is not None:
            self._values["member_type"] = member_type

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def member_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("member_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkGroupProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupProps",
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
        "network_manager_id": "networkManagerId",
        "description": "description",
        "ignore_changes": "ignoreChanges",
        "member_type": "memberType",
    },
)
class NetworkGroupProps(_AzapiResourceProps_141a2340):
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
        network_manager_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        member_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager Network Group.

        Extends AzapiResourceProps with Network Group specific properties

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
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param description: Optional description of the network group.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param member_type: Type of members in this network group. Default: undefined (can contain both VirtualNetwork and Subnet members)
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__36c9e7efa2e26645fca2a92f623cb73ab4b0f3c5563709e1c3a0b20a6c6225ea)
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
            check_type(argname="argument network_manager_id", value=network_manager_id, expected_type=type_hints["network_manager_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument member_type", value=member_type, expected_type=type_hints["member_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_manager_id": network_manager_id,
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
        if member_type is not None:
            self._values["member_type"] = member_type

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
    def network_manager_id(self) -> builtins.str:
        '''Resource ID of the parent Network Manager.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm"
        '''
        result = self._values.get("network_manager_id")
        assert result is not None, "Required property 'network_manager_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the network group.

        Example::

            "Production virtual networks for region East US"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def member_type(self) -> typing.Optional[builtins.str]:
        '''Type of members in this network group.

        :default: undefined (can contain both VirtualNetwork and Subnet members)

        Example::

            "Subnet"
        '''
        result = self._values.get("member_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkGroupProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class NetworkGroupStaticMember(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupStaticMember",
):
    '''Azure Virtual Network Manager Network Group Static Member implementation.

    Static members explicitly add virtual networks or subnets to a network group,
    providing precise control over which resources receive configurations applied
    to the network group. This is in contrast to dynamic membership via Azure Policy.

    Example::

        // Add a subnet to a network group:
        const subnetMember = new NetworkGroupStaticMember(this, "subnet-member", {
          name: "prod-subnet1-member",
          networkGroupId: productionGroup.id,
          resourceId: subnet.id,
          apiVersion: "2024-05-01"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        network_group_id: builtins.str,
        resource_id: builtins.str,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
        '''Creates a new Azure Virtual Network Manager Network Group Static Member using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param network_group_id: Resource ID of the parent Network Group.
        :param resource_id: Full resource ID of the VNet or Subnet to add to the group.
        :param ignore_changes: The lifecycle rules to ignore changes.
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
            type_hints = typing.get_type_hints(_typecheckingstub__6d0e17b9bb9eda9e6538a0876e13673232b7b38d44d4995e93cb2539c1b823a8)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = NetworkGroupStaticMemberProps(
            network_group_id=network_group_id,
            resource_id=resource_id,
            ignore_changes=ignore_changes,
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
            type_hints = typing.get_type_hints(_typecheckingstub__b0e19fd04334bf1e574f9f4b6c42f644f7ae32a8323db8e7b1f8a552634f627b)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Static Member Static Members are scoped to Network Groups.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0c7d5f780f8128a9a5ef2837b33540a02fafa8011ebe1b9ebd753f33d289bc0a)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Static Members.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="memberResourceId")
    def member_resource_id(self) -> builtins.str:
        '''Get the resource ID of the member VNet or Subnet Returns the input resourceId since Azure API doesn't return it in the response.'''
        return typing.cast(builtins.str, jsii.get(self, "memberResourceId"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "NetworkGroupStaticMemberProps":
        '''The input properties for this Static Member instance.'''
        return typing.cast("NetworkGroupStaticMemberProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="region")
    def region(self) -> builtins.str:
        '''Get the region of the member resource.'''
        return typing.cast(builtins.str, jsii.get(self, "region"))

    @builtins.property
    @jsii.member(jsii_name="resourceIdOutput")
    def resource_id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "resourceIdOutput"))

    @builtins.property
    @jsii.member(jsii_name="resourceName")
    def resource_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceName"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupStaticMemberBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class NetworkGroupStaticMemberBody:
    def __init__(
        self,
        *,
        properties: typing.Union["NetworkGroupStaticMemberProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Static Member API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = NetworkGroupStaticMemberProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cce8e848a076bf2506663c5e18bbdd762b3a696b68631b92f04a0cc696cd45ed)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "NetworkGroupStaticMemberProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("NetworkGroupStaticMemberProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkGroupStaticMemberBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupStaticMemberProperties",
    jsii_struct_bases=[],
    name_mapping={"resource_id": "resourceId"},
)
class NetworkGroupStaticMemberProperties:
    def __init__(self, *, resource_id: builtins.str) -> None:
        '''Properties for Static Member body.

        :param resource_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1cc7781ff2de59c4c986102638ca9f730c9c956e4b7a934085c0a1f1a4abad01)
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "resource_id": resource_id,
        }

    @builtins.property
    def resource_id(self) -> builtins.str:
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkGroupStaticMemberProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkGroupStaticMemberProps",
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
        "network_group_id": "networkGroupId",
        "resource_id": "resourceId",
        "ignore_changes": "ignoreChanges",
    },
)
class NetworkGroupStaticMemberProps(_AzapiResourceProps_141a2340):
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
        network_group_id: builtins.str,
        resource_id: builtins.str,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager Network Group Static Member.

        Extends AzapiResourceProps with Static Member specific properties

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
        :param network_group_id: Resource ID of the parent Network Group.
        :param resource_id: Full resource ID of the VNet or Subnet to add to the group.
        :param ignore_changes: The lifecycle rules to ignore changes.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed067b52b2d49a1109878c2894cd9d4e26e955a2207984b18c825840afac9b7f)
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
            check_type(argname="argument network_group_id", value=network_group_id, expected_type=type_hints["network_group_id"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_group_id": network_group_id,
            "resource_id": resource_id,
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
    def network_group_id(self) -> builtins.str:
        '''Resource ID of the parent Network Group.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm/networkGroups/prod-group"
        '''
        result = self._values.get("network_group_id")
        assert result is not None, "Required property 'network_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''Full resource ID of the VNet or Subnet to add to the group.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet1/subnets/subnet1"
        '''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkGroupStaticMemberProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.NetworkManagerScopes",
    jsii_struct_bases=[],
    name_mapping={
        "management_groups": "managementGroups",
        "subscriptions": "subscriptions",
    },
)
class NetworkManagerScopes:
    def __init__(
        self,
        *,
        management_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
        subscriptions: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Scope configuration for Virtual Network Manager.

        :param management_groups: Array of management group IDs that define the scope.
        :param subscriptions: Array of subscription IDs that define the scope.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8653db1d179467fedc47bfffee702aa755f160d3c3253bb13482b4e9345793da)
            check_type(argname="argument management_groups", value=management_groups, expected_type=type_hints["management_groups"])
            check_type(argname="argument subscriptions", value=subscriptions, expected_type=type_hints["subscriptions"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if management_groups is not None:
            self._values["management_groups"] = management_groups
        if subscriptions is not None:
            self._values["subscriptions"] = subscriptions

    @builtins.property
    def management_groups(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of management group IDs that define the scope.

        Example::

            ["/providers/Microsoft.Management/managementGroups/mg1"]
        '''
        result = self._values.get("management_groups")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def subscriptions(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of subscription IDs that define the scope.

        Example::

            ["/subscriptions/00000000-0000-0000-0000-000000000000"]
        '''
        result = self._values.get("subscriptions")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "NetworkManagerScopes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.ParsedCidr",
    jsii_struct_bases=[],
    name_mapping={
        "cidr": "cidr",
        "first_ip": "firstIp",
        "last_ip": "lastIp",
        "netmask": "netmask",
        "network": "network",
        "prefix": "prefix",
        "total_addresses": "totalAddresses",
    },
)
class ParsedCidr:
    def __init__(
        self,
        *,
        cidr: builtins.str,
        first_ip: builtins.str,
        last_ip: builtins.str,
        netmask: builtins.str,
        network: builtins.str,
        prefix: jsii.Number,
        total_addresses: jsii.Number,
    ) -> None:
        '''Parsed CIDR information.

        :param cidr: Original CIDR notation (e.g., "10.0.0.0/8").
        :param first_ip: First usable IP address.
        :param last_ip: Last usable IP address.
        :param netmask: Network mask (e.g., "255.0.0.0").
        :param network: Network address (e.g., "10.0.0.0").
        :param prefix: Prefix length (e.g., 8).
        :param total_addresses: Total number of addresses in the range.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f7b0dc08f0f7a342fe1806c118c4af5b6dd83ed356981e32a236fd8bad09d6a6)
            check_type(argname="argument cidr", value=cidr, expected_type=type_hints["cidr"])
            check_type(argname="argument first_ip", value=first_ip, expected_type=type_hints["first_ip"])
            check_type(argname="argument last_ip", value=last_ip, expected_type=type_hints["last_ip"])
            check_type(argname="argument netmask", value=netmask, expected_type=type_hints["netmask"])
            check_type(argname="argument network", value=network, expected_type=type_hints["network"])
            check_type(argname="argument prefix", value=prefix, expected_type=type_hints["prefix"])
            check_type(argname="argument total_addresses", value=total_addresses, expected_type=type_hints["total_addresses"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cidr": cidr,
            "first_ip": first_ip,
            "last_ip": last_ip,
            "netmask": netmask,
            "network": network,
            "prefix": prefix,
            "total_addresses": total_addresses,
        }

    @builtins.property
    def cidr(self) -> builtins.str:
        '''Original CIDR notation (e.g., "10.0.0.0/8").'''
        result = self._values.get("cidr")
        assert result is not None, "Required property 'cidr' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def first_ip(self) -> builtins.str:
        '''First usable IP address.'''
        result = self._values.get("first_ip")
        assert result is not None, "Required property 'first_ip' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def last_ip(self) -> builtins.str:
        '''Last usable IP address.'''
        result = self._values.get("last_ip")
        assert result is not None, "Required property 'last_ip' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def netmask(self) -> builtins.str:
        '''Network mask (e.g., "255.0.0.0").'''
        result = self._values.get("netmask")
        assert result is not None, "Required property 'netmask' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def network(self) -> builtins.str:
        '''Network address (e.g., "10.0.0.0").'''
        result = self._values.get("network")
        assert result is not None, "Required property 'network' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def prefix(self) -> jsii.Number:
        '''Prefix length (e.g., 8).'''
        result = self._values.get("prefix")
        assert result is not None, "Required property 'prefix' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def total_addresses(self) -> jsii.Number:
        '''Total number of addresses in the range.'''
        result = self._values.get("total_addresses")
        assert result is not None, "Required property 'total_addresses' is missing"
        return typing.cast(jsii.Number, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ParsedCidr(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SecurityAdminConfiguration(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminConfiguration",
):
    '''Azure Virtual Network Manager Security Admin Configuration implementation.

    Security admin configurations define high-priority security rules that are evaluated
    BEFORE traditional Network Security Groups (NSGs). This allows organizations to enforce
    security policies that cannot be overridden by individual teams managing NSGs.

    Key features:

    - Three action types: Allow (NSG can still deny), Deny (stops traffic), AlwaysAllow (forces allow)
    - Higher priority than NSG rules
    - Centralized security policy enforcement
    - Can block high-risk ports organization-wide

    Example::

        // Configuration with service-specific settings:
        const securityConfig = new SecurityAdminConfiguration(this, "security-config", {
          name: "org-security-rules",
          networkManagerId: networkManager.id,
          description: "Organization-wide security enforcement",
          applyOnNetworkIntentPolicyBasedServices: ["None"],
          apiVersion: "2024-05-01"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        network_manager_id: builtins.str,
        apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
        '''Creates a new Azure Virtual Network Manager Security Admin Configuration using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param apply_on_network_intent_policy_based_services: Services to apply the security admin configuration on.
        :param description: Optional description of the security admin configuration.
        :param ignore_changes: The lifecycle rules to ignore changes.
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
            type_hints = typing.get_type_hints(_typecheckingstub__3f2b6969e8dbe1c88d520863369c1989f1511ed1e9f4f2b114ab79b1d631ec25)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SecurityAdminConfigurationProps(
            network_manager_id=network_manager_id,
            apply_on_network_intent_policy_based_services=apply_on_network_intent_policy_based_services,
            description=description,
            ignore_changes=ignore_changes,
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
            type_hints = typing.get_type_hints(_typecheckingstub__323a90192e6e57bbec48015b1fbb222d3eced4a8779d62df8833d5bfd4dfb3e9)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Security Admin Configuration Security Admin Configurations are scoped to Network Managers.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e15489bde546ec2d9226bdede73bdecefb8becfbe640de8dac7fb27ed4b8191)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Security Admin Configurations.'''
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
    def props(self) -> "SecurityAdminConfigurationProps":
        '''The input properties for this Security Admin Configuration instance.'''
        return typing.cast("SecurityAdminConfigurationProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Security Admin Configuration.'''
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
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminConfigurationBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class SecurityAdminConfigurationBody:
    def __init__(
        self,
        *,
        properties: typing.Optional[typing.Union["SecurityAdminConfigurationProperties", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''The resource body interface for Azure Security Admin Configuration API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = SecurityAdminConfigurationProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6fbd16501e04c88e7df93b3bdfd01f98df7f2d8bd536e0bca8eb5ab06bc529aa)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if properties is not None:
            self._values["properties"] = properties

    @builtins.property
    def properties(self) -> typing.Optional["SecurityAdminConfigurationProperties"]:
        result = self._values.get("properties")
        return typing.cast(typing.Optional["SecurityAdminConfigurationProperties"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminConfigurationBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminConfigurationProperties",
    jsii_struct_bases=[],
    name_mapping={
        "apply_on_network_intent_policy_based_services": "applyOnNetworkIntentPolicyBasedServices",
        "description": "description",
    },
)
class SecurityAdminConfigurationProperties:
    def __init__(
        self,
        *,
        apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for Security Admin Configuration body.

        :param apply_on_network_intent_policy_based_services: 
        :param description: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d5a853ec4c24f7afeeaebb18839f42b8fcc3dc9c2c3bbd3971059f82e5ebddcc)
            check_type(argname="argument apply_on_network_intent_policy_based_services", value=apply_on_network_intent_policy_based_services, expected_type=type_hints["apply_on_network_intent_policy_based_services"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if apply_on_network_intent_policy_based_services is not None:
            self._values["apply_on_network_intent_policy_based_services"] = apply_on_network_intent_policy_based_services
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def apply_on_network_intent_policy_based_services(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("apply_on_network_intent_policy_based_services")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminConfigurationProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminConfigurationProps",
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
        "network_manager_id": "networkManagerId",
        "apply_on_network_intent_policy_based_services": "applyOnNetworkIntentPolicyBasedServices",
        "description": "description",
        "ignore_changes": "ignoreChanges",
    },
)
class SecurityAdminConfigurationProps(_AzapiResourceProps_141a2340):
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
        network_manager_id: builtins.str,
        apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager Security Admin Configuration.

        Extends AzapiResourceProps with Security Admin Configuration specific properties

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
        :param network_manager_id: Resource ID of the parent Network Manager.
        :param apply_on_network_intent_policy_based_services: Services to apply the security admin configuration on.
        :param description: Optional description of the security admin configuration.
        :param ignore_changes: The lifecycle rules to ignore changes.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dfdea866c08ed9716ebddf5359d0b23963abd102ed5ad99e48cfa8ac5e4df544)
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
            check_type(argname="argument network_manager_id", value=network_manager_id, expected_type=type_hints["network_manager_id"])
            check_type(argname="argument apply_on_network_intent_policy_based_services", value=apply_on_network_intent_policy_based_services, expected_type=type_hints["apply_on_network_intent_policy_based_services"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_manager_id": network_manager_id,
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
        if apply_on_network_intent_policy_based_services is not None:
            self._values["apply_on_network_intent_policy_based_services"] = apply_on_network_intent_policy_based_services
        if description is not None:
            self._values["description"] = description
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes

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
    def network_manager_id(self) -> builtins.str:
        '''Resource ID of the parent Network Manager.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm"
        '''
        result = self._values.get("network_manager_id")
        assert result is not None, "Required property 'network_manager_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def apply_on_network_intent_policy_based_services(
        self,
    ) -> typing.Optional[typing.List[builtins.str]]:
        '''Services to apply the security admin configuration on.

        Example::

            ["All"]
        '''
        result = self._values.get("apply_on_network_intent_policy_based_services")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the security admin configuration.

        Example::

            "Organization-wide security rules for production workloads"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminConfigurationProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminConfigurationRuleGroupItem",
    jsii_struct_bases=[],
    name_mapping={"network_group_id": "networkGroupId"},
)
class SecurityAdminConfigurationRuleGroupItem:
    def __init__(self, *, network_group_id: builtins.str) -> None:
        '''Network group reference for rule collection.

        :param network_group_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0cc16b8007d9b7bad7f0cfea9cd8d692e6f99a19a2c8c81e54f3e6b6ab49e2ef)
            check_type(argname="argument network_group_id", value=network_group_id, expected_type=type_hints["network_group_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_group_id": network_group_id,
        }

    @builtins.property
    def network_group_id(self) -> builtins.str:
        result = self._values.get("network_group_id")
        assert result is not None, "Required property 'network_group_id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminConfigurationRuleGroupItem(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SecurityAdminRule(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRule",
):
    '''Azure Virtual Network Manager Security Admin Rule implementation.

    Security admin rules define high-priority security policies that are evaluated BEFORE
    traditional Network Security Groups (NSGs). This enables centralized security enforcement
    that cannot be overridden by individual teams.

    Key concepts:

    - Priority: Lower numbers = higher priority (evaluated first)
    - Allow: Permits traffic, but NSG can still deny it
    - Deny: Blocks traffic immediately, no further evaluation
    - AlwaysAllow: Forces traffic to be allowed, overriding NSG denies

    Example::

        // Always allow monitoring traffic:
        const allowMonitoring = new SecurityAdminRule(this, "allow-monitoring", {
          name: "always-allow-monitoring",
          ruleCollectionId: ruleCollection.id,
          description: "Always allow traffic from monitoring systems",
          priority: 50,
          action: "AlwaysAllow",
          direction: "Inbound",
          protocol: "Any",
          sources: [{ addressPrefix: "10.0.0.0/24", addressPrefixType: "IPPrefix" }],
          destinations: [{ addressPrefix: "*", addressPrefixType: "IPPrefix" }]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        action: builtins.str,
        direction: builtins.str,
        priority: jsii.Number,
        protocol: builtins.str,
        rule_collection_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        destinations: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        sources: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
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
        '''Creates a new Azure Virtual Network Manager Security Admin Rule using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param action: Action to take when the rule matches - Allow: Allow traffic (NSG can still deny) - Deny: Deny traffic (stops evaluation) - AlwaysAllow: Force allow (overrides NSG denies).
        :param direction: Direction of traffic this rule applies to.
        :param priority: Priority of the rule (1-4096, lower number = higher priority) Rules with lower priority numbers are evaluated first.
        :param protocol: Protocol this rule applies to.
        :param rule_collection_id: Resource ID of the parent Rule Collection.
        :param description: Optional description of the security admin rule.
        :param destination_port_ranges: Destination port ranges Use ["*"] for all ports or specify ranges. Default: ["*"]
        :param destinations: Destination addresses or network groups.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param source_port_ranges: Source port ranges Use ["*"] for all ports or specify ranges like ["80", "443", "8000-8999"]. Default: ["*"]
        :param sources: Source addresses or network groups.
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
            type_hints = typing.get_type_hints(_typecheckingstub__89d935e5abacdfbf4ff98fa7f2dd8e725ebab87891bf3e85987c2943f5a16c3d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SecurityAdminRuleProps(
            action=action,
            direction=direction,
            priority=priority,
            protocol=protocol,
            rule_collection_id=rule_collection_id,
            description=description,
            destination_port_ranges=destination_port_ranges,
            destinations=destinations,
            ignore_changes=ignore_changes,
            source_port_ranges=source_port_ranges,
            sources=sources,
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
            type_hints = typing.get_type_hints(_typecheckingstub__d4ca993d0401daf2b427e35d0e4aa7b64cdf0435684ce0d83614c2d482b01cec)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Security Admin Rule Security Admin Rules are scoped to Rule Collections.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__84e42ae57c0008a7dc018fab49950ef2d6eff598bc8b0283a9c8aace4cd41c3e)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Security Admin Rules.'''
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
    def props(self) -> "SecurityAdminRuleProps":
        '''The input properties for this Security Admin Rule instance.'''
        return typing.cast("SecurityAdminRuleProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Security Admin Rule.'''
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
    @jsii.member(jsii_name="ruleAction")
    def rule_action(self) -> builtins.str:
        '''Get the action of the rule.'''
        return typing.cast(builtins.str, jsii.get(self, "ruleAction"))

    @builtins.property
    @jsii.member(jsii_name="rulePriority")
    def rule_priority(self) -> jsii.Number:
        '''Get the priority of the rule.'''
        return typing.cast(jsii.Number, jsii.get(self, "rulePriority"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleBody",
    jsii_struct_bases=[],
    name_mapping={"kind": "kind", "properties": "properties"},
)
class SecurityAdminRuleBody:
    def __init__(
        self,
        *,
        kind: builtins.str,
        properties: typing.Union["SecurityAdminRuleProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Security Admin Rule API calls.

        :param kind: 
        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = SecurityAdminRuleProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8b490d90710f75641f1f537a504078302eb0773da843d9a8be43072aa346ed26)
            check_type(argname="argument kind", value=kind, expected_type=type_hints["kind"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "kind": kind,
            "properties": properties,
        }

    @builtins.property
    def kind(self) -> builtins.str:
        result = self._values.get("kind")
        assert result is not None, "Required property 'kind' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> "SecurityAdminRuleProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("SecurityAdminRuleProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminRuleBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SecurityAdminRuleCollection(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleCollection",
):
    '''Azure Virtual Network Manager Security Admin Rule Collection implementation.

    Rule collections group related security admin rules together and define which network
    groups receive those rules. This allows for organized rule management and targeted
    application of security policies.

    Example::

        // Rule collection applied to multiple network groups:
        const allowMonitoring = new SecurityAdminRuleCollection(this, "allow-monitoring", {
          name: "allow-monitoring-traffic",
          securityAdminConfigurationId: securityConfig.id,
          description: "Always allow monitoring and security scanner traffic",
          appliesToGroups: [
            { networkGroupId: productionGroup.id },
            { networkGroupId: stagingGroup.id }
          ],
          apiVersion: "2024-05-01"
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        applies_to_groups: typing.Sequence[typing.Union[SecurityAdminConfigurationRuleGroupItem, typing.Dict[builtins.str, typing.Any]]],
        security_admin_configuration_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
        '''Creates a new Azure Virtual Network Manager Security Admin Rule Collection using the AzapiResource framework.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param applies_to_groups: Network groups to apply this rule collection to Each item specifies a network group that will receive these rules.
        :param security_admin_configuration_id: Resource ID of the parent Security Admin Configuration.
        :param description: Optional description of the rule collection.
        :param ignore_changes: The lifecycle rules to ignore changes.
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
            type_hints = typing.get_type_hints(_typecheckingstub__995acee61067cd90a82200a2d8d7213bb388ec3b0fc3a7d11e462244e93df4be)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SecurityAdminRuleCollectionProps(
            applies_to_groups=applies_to_groups,
            security_admin_configuration_id=security_admin_configuration_id,
            description=description,
            ignore_changes=ignore_changes,
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
            type_hints = typing.get_type_hints(_typecheckingstub__06be4f8a1f38e7a92702375cb71d01dfdef143ead620c9e444cbb65fdf55c591)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Rule Collection Rule Collections are scoped to Security Admin Configurations.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d735be05638eb29792d970d794f377eaa3a669a8d00f81fcc46621f9c7886c2b)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Rule Collections.'''
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
    def props(self) -> "SecurityAdminRuleCollectionProps":
        '''The input properties for this Rule Collection instance.'''
        return typing.cast("SecurityAdminRuleCollectionProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="provisioningState")
    def provisioning_state(self) -> builtins.str:
        '''Get the provisioning state of the Rule Collection.'''
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
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleCollectionBody",
    jsii_struct_bases=[],
    name_mapping={"properties": "properties"},
)
class SecurityAdminRuleCollectionBody:
    def __init__(
        self,
        *,
        properties: typing.Union["SecurityAdminRuleCollectionProperties", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''The resource body interface for Azure Rule Collection API calls.

        :param properties: 
        '''
        if isinstance(properties, dict):
            properties = SecurityAdminRuleCollectionProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56c4c02fea0425f4895f3016c25f08dcc6c0c7ae2d50eed64ecc315ba34feefb)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
        }

    @builtins.property
    def properties(self) -> "SecurityAdminRuleCollectionProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("SecurityAdminRuleCollectionProperties", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminRuleCollectionBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleCollectionProperties",
    jsii_struct_bases=[],
    name_mapping={
        "applies_to_groups": "appliesToGroups",
        "description": "description",
    },
)
class SecurityAdminRuleCollectionProperties:
    def __init__(
        self,
        *,
        applies_to_groups: typing.Sequence[typing.Union[SecurityAdminConfigurationRuleGroupItem, typing.Dict[builtins.str, typing.Any]]],
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for Rule Collection body.

        :param applies_to_groups: 
        :param description: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3dab1df423dfe9db6be3aa4c4f23fb50be285bd95163799a70b53403c8cf1e53)
            check_type(argname="argument applies_to_groups", value=applies_to_groups, expected_type=type_hints["applies_to_groups"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "applies_to_groups": applies_to_groups,
        }
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def applies_to_groups(self) -> typing.List[SecurityAdminConfigurationRuleGroupItem]:
        result = self._values.get("applies_to_groups")
        assert result is not None, "Required property 'applies_to_groups' is missing"
        return typing.cast(typing.List[SecurityAdminConfigurationRuleGroupItem], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminRuleCollectionProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleCollectionProps",
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
        "applies_to_groups": "appliesToGroups",
        "security_admin_configuration_id": "securityAdminConfigurationId",
        "description": "description",
        "ignore_changes": "ignoreChanges",
    },
)
class SecurityAdminRuleCollectionProps(_AzapiResourceProps_141a2340):
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
        applies_to_groups: typing.Sequence[typing.Union[SecurityAdminConfigurationRuleGroupItem, typing.Dict[builtins.str, typing.Any]]],
        security_admin_configuration_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager Security Admin Rule Collection.

        Extends AzapiResourceProps with Rule Collection specific properties

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
        :param applies_to_groups: Network groups to apply this rule collection to Each item specifies a network group that will receive these rules.
        :param security_admin_configuration_id: Resource ID of the parent Security Admin Configuration.
        :param description: Optional description of the rule collection.
        :param ignore_changes: The lifecycle rules to ignore changes.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9b38b587a662f7c374e0a3cdd126baaf383015ec7238725c3459275ddb32f5ca)
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
            check_type(argname="argument applies_to_groups", value=applies_to_groups, expected_type=type_hints["applies_to_groups"])
            check_type(argname="argument security_admin_configuration_id", value=security_admin_configuration_id, expected_type=type_hints["security_admin_configuration_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "applies_to_groups": applies_to_groups,
            "security_admin_configuration_id": security_admin_configuration_id,
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
    def applies_to_groups(self) -> typing.List[SecurityAdminConfigurationRuleGroupItem]:
        '''Network groups to apply this rule collection to Each item specifies a network group that will receive these rules.'''
        result = self._values.get("applies_to_groups")
        assert result is not None, "Required property 'applies_to_groups' is missing"
        return typing.cast(typing.List[SecurityAdminConfigurationRuleGroupItem], result)

    @builtins.property
    def security_admin_configuration_id(self) -> builtins.str:
        '''Resource ID of the parent Security Admin Configuration.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm/securityAdminConfigurations/config"
        '''
        result = self._values.get("security_admin_configuration_id")
        assert result is not None, "Required property 'security_admin_configuration_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the rule collection.

        Example::

            "Rules to block high-risk ports"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminRuleCollectionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleProperties",
    jsii_struct_bases=[],
    name_mapping={
        "action": "action",
        "direction": "direction",
        "priority": "priority",
        "protocol": "protocol",
        "description": "description",
        "destination_port_ranges": "destinationPortRanges",
        "destinations": "destinations",
        "source_port_ranges": "sourcePortRanges",
        "sources": "sources",
    },
)
class SecurityAdminRuleProperties:
    def __init__(
        self,
        *,
        action: builtins.str,
        direction: builtins.str,
        priority: jsii.Number,
        protocol: builtins.str,
        description: typing.Optional[builtins.str] = None,
        destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        destinations: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
        source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        sources: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Properties for Security Admin Rule body.

        :param action: 
        :param direction: 
        :param priority: 
        :param protocol: 
        :param description: 
        :param destination_port_ranges: 
        :param destinations: 
        :param source_port_ranges: 
        :param sources: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__550219bc2e504a27914d875da5be1438430413cd0d71e248ef3e7b3d4426b7de)
            check_type(argname="argument action", value=action, expected_type=type_hints["action"])
            check_type(argname="argument direction", value=direction, expected_type=type_hints["direction"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument protocol", value=protocol, expected_type=type_hints["protocol"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument destination_port_ranges", value=destination_port_ranges, expected_type=type_hints["destination_port_ranges"])
            check_type(argname="argument destinations", value=destinations, expected_type=type_hints["destinations"])
            check_type(argname="argument source_port_ranges", value=source_port_ranges, expected_type=type_hints["source_port_ranges"])
            check_type(argname="argument sources", value=sources, expected_type=type_hints["sources"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "action": action,
            "direction": direction,
            "priority": priority,
            "protocol": protocol,
        }
        if description is not None:
            self._values["description"] = description
        if destination_port_ranges is not None:
            self._values["destination_port_ranges"] = destination_port_ranges
        if destinations is not None:
            self._values["destinations"] = destinations
        if source_port_ranges is not None:
            self._values["source_port_ranges"] = source_port_ranges
        if sources is not None:
            self._values["sources"] = sources

    @builtins.property
    def action(self) -> builtins.str:
        result = self._values.get("action")
        assert result is not None, "Required property 'action' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def direction(self) -> builtins.str:
        result = self._values.get("direction")
        assert result is not None, "Required property 'direction' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def priority(self) -> jsii.Number:
        result = self._values.get("priority")
        assert result is not None, "Required property 'priority' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def protocol(self) -> builtins.str:
        result = self._values.get("protocol")
        assert result is not None, "Required property 'protocol' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_port_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("destination_port_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def destinations(self) -> typing.Optional[typing.List[AddressPrefixItem]]:
        result = self._values.get("destinations")
        return typing.cast(typing.Optional[typing.List[AddressPrefixItem]], result)

    @builtins.property
    def source_port_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("source_port_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def sources(self) -> typing.Optional[typing.List[AddressPrefixItem]]:
        result = self._values.get("sources")
        return typing.cast(typing.Optional[typing.List[AddressPrefixItem]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminRuleProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.SecurityAdminRuleProps",
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
        "action": "action",
        "direction": "direction",
        "priority": "priority",
        "protocol": "protocol",
        "rule_collection_id": "ruleCollectionId",
        "description": "description",
        "destination_port_ranges": "destinationPortRanges",
        "destinations": "destinations",
        "ignore_changes": "ignoreChanges",
        "source_port_ranges": "sourcePortRanges",
        "sources": "sources",
    },
)
class SecurityAdminRuleProps(_AzapiResourceProps_141a2340):
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
        action: builtins.str,
        direction: builtins.str,
        priority: jsii.Number,
        protocol: builtins.str,
        rule_collection_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        destinations: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        sources: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager Security Admin Rule.

        Extends AzapiResourceProps with Security Admin Rule specific properties

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
        :param action: Action to take when the rule matches - Allow: Allow traffic (NSG can still deny) - Deny: Deny traffic (stops evaluation) - AlwaysAllow: Force allow (overrides NSG denies).
        :param direction: Direction of traffic this rule applies to.
        :param priority: Priority of the rule (1-4096, lower number = higher priority) Rules with lower priority numbers are evaluated first.
        :param protocol: Protocol this rule applies to.
        :param rule_collection_id: Resource ID of the parent Rule Collection.
        :param description: Optional description of the security admin rule.
        :param destination_port_ranges: Destination port ranges Use ["*"] for all ports or specify ranges. Default: ["*"]
        :param destinations: Destination addresses or network groups.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param source_port_ranges: Source port ranges Use ["*"] for all ports or specify ranges like ["80", "443", "8000-8999"]. Default: ["*"]
        :param sources: Source addresses or network groups.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__21b9010c419654c3ef2dbde67860d35b2c60135746f420c03e42b77628426c84)
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
            check_type(argname="argument action", value=action, expected_type=type_hints["action"])
            check_type(argname="argument direction", value=direction, expected_type=type_hints["direction"])
            check_type(argname="argument priority", value=priority, expected_type=type_hints["priority"])
            check_type(argname="argument protocol", value=protocol, expected_type=type_hints["protocol"])
            check_type(argname="argument rule_collection_id", value=rule_collection_id, expected_type=type_hints["rule_collection_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument destination_port_ranges", value=destination_port_ranges, expected_type=type_hints["destination_port_ranges"])
            check_type(argname="argument destinations", value=destinations, expected_type=type_hints["destinations"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument source_port_ranges", value=source_port_ranges, expected_type=type_hints["source_port_ranges"])
            check_type(argname="argument sources", value=sources, expected_type=type_hints["sources"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "action": action,
            "direction": direction,
            "priority": priority,
            "protocol": protocol,
            "rule_collection_id": rule_collection_id,
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
        if destination_port_ranges is not None:
            self._values["destination_port_ranges"] = destination_port_ranges
        if destinations is not None:
            self._values["destinations"] = destinations
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if source_port_ranges is not None:
            self._values["source_port_ranges"] = source_port_ranges
        if sources is not None:
            self._values["sources"] = sources

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
    def action(self) -> builtins.str:
        '''Action to take when the rule matches - Allow: Allow traffic (NSG can still deny) - Deny: Deny traffic (stops evaluation) - AlwaysAllow: Force allow (overrides NSG denies).

        Example::

            "AlwaysAllow"
        '''
        result = self._values.get("action")
        assert result is not None, "Required property 'action' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def direction(self) -> builtins.str:
        '''Direction of traffic this rule applies to.

        Example::

            "Outbound"
        '''
        result = self._values.get("direction")
        assert result is not None, "Required property 'direction' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def priority(self) -> jsii.Number:
        '''Priority of the rule (1-4096, lower number = higher priority) Rules with lower priority numbers are evaluated first.

        Example::

            100
        '''
        result = self._values.get("priority")
        assert result is not None, "Required property 'priority' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def protocol(self) -> builtins.str:
        '''Protocol this rule applies to.

        Example::

            "Any"
        '''
        result = self._values.get("protocol")
        assert result is not None, "Required property 'protocol' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def rule_collection_id(self) -> builtins.str:
        '''Resource ID of the parent Rule Collection.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.Network/networkManagers/vnm/securityAdminConfigurations/config/ruleCollections/collection"
        '''
        result = self._values.get("rule_collection_id")
        assert result is not None, "Required property 'rule_collection_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the security admin rule.

        Example::

            "Block SSH access from internet"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def destination_port_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Destination port ranges Use ["*"] for all ports or specify ranges.

        :default: ["*"]

        Example::

            ["3389", "5985-5986"]
        '''
        result = self._values.get("destination_port_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def destinations(self) -> typing.Optional[typing.List[AddressPrefixItem]]:
        '''Destination addresses or network groups.

        Example::

            [{ addressPrefix: "Internet", addressPrefixType: "ServiceTag" }]
        '''
        result = self._values.get("destinations")
        return typing.cast(typing.Optional[typing.List[AddressPrefixItem]], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def source_port_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Source port ranges Use ["*"] for all ports or specify ranges like ["80", "443", "8000-8999"].

        :default: ["*"]

        Example::

            ["80", "443"]
        '''
        result = self._values.get("source_port_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def sources(self) -> typing.Optional[typing.List[AddressPrefixItem]]:
        '''Source addresses or network groups.

        Example::

            [{ addressPrefix: "10.0.0.0/8", addressPrefixType: "IPPrefix" }]
        '''
        result = self._values.get("sources")
        return typing.cast(typing.Optional[typing.List[AddressPrefixItem]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SecurityAdminRuleProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class VirtualNetworkManager(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.VirtualNetworkManager",
):
    '''Azure Virtual Network Manager implementation.

    This class provides a single, version-aware implementation that handles
    version resolution, schema validation, and property transformation while maintaining
    full backward compatibility.

    Example::

        // Usage with explicit version pinning:
        const networkManager = new VirtualNetworkManager(this, "manager", {
          name: "my-network-manager",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          apiVersion: "2024-05-01",
          networkManagerScopes: {
            subscriptions: ["/subscriptions/00000000-0000-0000-0000-000000000000"]
          },
          networkManagerScopeAccesses: ["Connectivity", "SecurityAdmin"]
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        network_manager_scope_accesses: typing.Sequence[builtins.str],
        network_manager_scopes: typing.Union[NetworkManagerScopes, typing.Dict[builtins.str, typing.Any]],
        resource_group_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
        '''Creates a new Azure Virtual Network Manager using the AzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation. It maintains full backward compatibility
        with existing Virtual Network Manager implementations.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param network_manager_scope_accesses: Array of features enabled for the network manager Valid values: "Connectivity", "SecurityAdmin", "Routing".
        :param network_manager_scopes: Defines the scope of management (management groups and/or subscriptions) At least one of managementGroups or subscriptions must be specified.
        :param resource_group_id: Resource ID of the resource group where the network manager will be created.
        :param description: Optional description of the network manager.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
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
            type_hints = typing.get_type_hints(_typecheckingstub__948ae326bcac3d52772b9f9b8500de54d16359633dbaf94c5fe5d27c799b8816)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = VirtualNetworkManagerProps(
            network_manager_scope_accesses=network_manager_scope_accesses,
            network_manager_scopes=network_manager_scopes,
            resource_group_id=resource_group_id,
            description=description,
            ignore_changes=ignore_changes,
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

    @jsii.member(jsii_name="addConnectivityConfiguration")
    def add_connectivity_configuration(
        self,
        id: builtins.str,
        *,
        applies_to_groups: typing.Sequence[typing.Union[ConnectivityGroupItem, typing.Dict[builtins.str, typing.Any]]],
        connectivity_topology: builtins.str,
        delete_existing_peering: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        hubs: typing.Optional[typing.Sequence[typing.Union[Hub, typing.Dict[builtins.str, typing.Any]]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        is_global: typing.Optional[builtins.bool] = None,
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
    ) -> ConnectivityConfiguration:
        '''Convenience method to create a ConnectivityConfiguration.

        This is a helper method that creates a ConnectivityConfiguration with the
        networkManagerId automatically set to this Network Manager's ID.

        :param id: - The unique identifier for the connectivity configuration construct.
        :param applies_to_groups: Network groups to apply this configuration to Each item specifies a network group and how it should connect.
        :param connectivity_topology: Connectivity topology type - HubAndSpoke: Central hub with spoke VNets - Mesh: All VNets can communicate directly.
        :param delete_existing_peering: Delete existing peerings when applying this configuration. Default: false
        :param description: Optional description of the connectivity configuration.
        :param hubs: Hub VNets for hub-and-spoke topology Required when connectivityTopology is "HubAndSpoke".
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param is_global: Enable global mesh connectivity Allows mesh connectivity across regions. Default: false
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

        :return: The created ConnectivityConfiguration instance

        Example::

            const hubSpoke = networkManager.addConnectivityConfiguration("hub-spoke", {
              name: "production-hub-spoke",
              connectivityTopology: "HubAndSpoke",
              appliesToGroups: [{ networkGroupId: prodGroup.id }],
              hubs: [{ resourceId: hubVnet.id, resourceType: "Microsoft.Network/virtualNetworks" }]
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1c8a65b5c9b61c2b5e0054f35f9af295681dec331d601e42fdca917122649c1e)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AddConnectivityConfigurationProps(
            applies_to_groups=applies_to_groups,
            connectivity_topology=connectivity_topology,
            delete_existing_peering=delete_existing_peering,
            description=description,
            hubs=hubs,
            ignore_changes=ignore_changes,
            is_global=is_global,
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

        return typing.cast(ConnectivityConfiguration, jsii.invoke(self, "addConnectivityConfiguration", [id, props]))

    @jsii.member(jsii_name="addIpamPool")
    def add_ipam_pool(
        self,
        id: builtins.str,
        *,
        address_prefixes: typing.Sequence[builtins.str],
        description: typing.Optional[builtins.str] = None,
        display_name: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        parent_pool_name: typing.Optional[builtins.str] = None,
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
    ) -> IpamPool:
        '''Convenience method to create an IpamPool.

        This is a helper method that creates an IpamPool with the networkManagerId
        automatically set to this Network Manager's ID. You can also create IpamPools
        directly using: new IpamPool(scope, id, { networkManagerId: vnm.id, ...props })

        :param id: - The unique identifier for the IPAM pool construct.
        :param address_prefixes: IP address prefixes for the pool Must be valid CIDR notation (e.g., "10.0.0.0/8") Multiple prefixes must not overlap.
        :param description: Optional description of the IPAM pool.
        :param display_name: Optional friendly display name.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param parent_pool_name: Name of parent pool for hierarchical pools Leave empty/undefined for root pools.
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

        :return: The created IpamPool instance

        Example::

            const ipamPool = networkManager.addIpamPool("prod-pool", {
              name: "production-pool",
              location: "eastus",
              addressPrefixes: ["10.0.0.0/8"],
              description: "Production IP address pool",
              displayName: "Production Pool"
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__179a76045ae005ae8883fff58026a066feac3ad00b4b29ee68592e539b7d5840)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AddIpamPoolProps(
            address_prefixes=address_prefixes,
            description=description,
            display_name=display_name,
            ignore_changes=ignore_changes,
            parent_pool_name=parent_pool_name,
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

        return typing.cast(IpamPool, jsii.invoke(self, "addIpamPool", [id, props]))

    @jsii.member(jsii_name="addNetworkGroup")
    def add_network_group(
        self,
        id: builtins.str,
        *,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        member_type: typing.Optional[builtins.str] = None,
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
    ) -> NetworkGroup:
        '''Convenience method to create a NetworkGroup.

        This is a helper method that creates a NetworkGroup with the networkManagerId
        automatically set to this Network Manager's ID. You can also create NetworkGroups
        directly using: new NetworkGroup(scope, id, { networkManagerId: vnm.id, ...props })

        :param id: - The unique identifier for the network group construct.
        :param description: Optional description of the network group.
        :param ignore_changes: The lifecycle rules to ignore changes.
        :param member_type: Type of members in this network group. Default: undefined (can contain both VirtualNetwork and Subnet members)
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

        :return: The created NetworkGroup instance

        Example::

            const prodGroup = networkManager.addNetworkGroup("prod-group", {
              name: "production-vnets",
              description: "Production virtual networks",
              memberType: "VirtualNetwork"
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__57d98e78bce93b2ab43ca1fdfaf1ad93002f24daa6f2b0285486466a3d21055b)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AddNetworkGroupProps(
            description=description,
            ignore_changes=ignore_changes,
            member_type=member_type,
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

        return typing.cast(NetworkGroup, jsii.invoke(self, "addNetworkGroup", [id, props]))

    @jsii.member(jsii_name="addSecurityAdminConfiguration")
    def add_security_admin_configuration(
        self,
        id: builtins.str,
        *,
        apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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
    ) -> SecurityAdminConfiguration:
        '''Convenience method to create a SecurityAdminConfiguration.

        This is a helper method that creates a SecurityAdminConfiguration with the
        networkManagerId automatically set to this Network Manager's ID.

        :param id: - The unique identifier for the security admin configuration construct.
        :param apply_on_network_intent_policy_based_services: Services to apply the security admin configuration on.
        :param description: Optional description of the security admin configuration.
        :param ignore_changes: The lifecycle rules to ignore changes.
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

        :return: The created SecurityAdminConfiguration instance

        Example::

            const securityConfig = networkManager.addSecurityAdminConfiguration("security", {
              name: "production-security",
              description: "High-priority security rules for production"
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f8e8e3653af2d2de847c56cbbb45a835b8cb75635f81ba5968bf8de8208efb9f)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AddSecurityAdminConfigurationProps(
            apply_on_network_intent_policy_based_services=apply_on_network_intent_policy_based_services,
            description=description,
            ignore_changes=ignore_changes,
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

        return typing.cast(SecurityAdminConfiguration, jsii.invoke(self, "addSecurityAdminConfiguration", [id, props]))

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Add a tag to the Virtual Network Manager Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e31606711aff3d4e56c87d9eaf03a85a8be1170ad7e8738b0e67e1b759dc0ca1)
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
            type_hints = typing.get_type_hints(_typecheckingstub__b6a056a991fc21e9b24d59db7202c5b9de837195487eb04de769f92a6fce04a6)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the Virtual Network Manager Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c164365cdc645d58840f31b583f81b72cf282acb94bb42a5805f81b39466ddcd)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="resolveParentId")
    def _resolve_parent_id(self, props: typing.Any) -> builtins.str:
        '''Resolves the parent resource ID for the Network Manager Network Managers are scoped to resource groups.

        :param props: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2afd50e262858169f0714aeaa0348790ae12e6ea00566a97326fb8c472d3c667)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for Virtual Network Managers.'''
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
    def props(self) -> "VirtualNetworkManagerProps":
        '''The input properties for this Virtual Network Manager instance.'''
        return typing.cast("VirtualNetworkManagerProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="resourceName")
    def resource_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceName"))

    @builtins.property
    @jsii.member(jsii_name="scopeAccessesOutput")
    def scope_accesses_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "scopeAccessesOutput"))

    @builtins.property
    @jsii.member(jsii_name="scopeOutput")
    def scope_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "scopeOutput"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.VirtualNetworkManagerBody",
    jsii_struct_bases=[],
    name_mapping={"location": "location", "properties": "properties", "tags": "tags"},
)
class VirtualNetworkManagerBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["VirtualNetworkManagerProperties", typing.Dict[builtins.str, typing.Any]],
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure Virtual Network Manager API calls.

        :param location: 
        :param properties: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = VirtualNetworkManagerProperties(**properties)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c23bcec99dcce6cd54645c408bdbc4c136773a579b4aece1f0935938e883e8f5)
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
    def properties(self) -> "VirtualNetworkManagerProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("VirtualNetworkManagerProperties", result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkManagerBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.VirtualNetworkManagerProperties",
    jsii_struct_bases=[],
    name_mapping={
        "network_manager_scope_accesses": "networkManagerScopeAccesses",
        "network_manager_scopes": "networkManagerScopes",
        "description": "description",
    },
)
class VirtualNetworkManagerProperties:
    def __init__(
        self,
        *,
        network_manager_scope_accesses: typing.Sequence[builtins.str],
        network_manager_scopes: typing.Union[NetworkManagerScopes, typing.Dict[builtins.str, typing.Any]],
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Properties for Virtual Network Manager body.

        :param network_manager_scope_accesses: 
        :param network_manager_scopes: 
        :param description: 
        '''
        if isinstance(network_manager_scopes, dict):
            network_manager_scopes = NetworkManagerScopes(**network_manager_scopes)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__839408946e19e8af0874bf39f94a3aff4f4a681404ed35169d2eda5b4d53d0c2)
            check_type(argname="argument network_manager_scope_accesses", value=network_manager_scope_accesses, expected_type=type_hints["network_manager_scope_accesses"])
            check_type(argname="argument network_manager_scopes", value=network_manager_scopes, expected_type=type_hints["network_manager_scopes"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_manager_scope_accesses": network_manager_scope_accesses,
            "network_manager_scopes": network_manager_scopes,
        }
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def network_manager_scope_accesses(self) -> typing.List[builtins.str]:
        result = self._values.get("network_manager_scope_accesses")
        assert result is not None, "Required property 'network_manager_scope_accesses' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def network_manager_scopes(self) -> NetworkManagerScopes:
        result = self._values.get("network_manager_scopes")
        assert result is not None, "Required property 'network_manager_scopes' is missing"
        return typing.cast(NetworkManagerScopes, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkManagerProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_virtualnetworkmanager.VirtualNetworkManagerProps",
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
        "network_manager_scope_accesses": "networkManagerScopeAccesses",
        "network_manager_scopes": "networkManagerScopes",
        "resource_group_id": "resourceGroupId",
        "description": "description",
        "ignore_changes": "ignoreChanges",
    },
)
class VirtualNetworkManagerProps(_AzapiResourceProps_141a2340):
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
        network_manager_scope_accesses: typing.Sequence[builtins.str],
        network_manager_scopes: typing.Union[NetworkManagerScopes, typing.Dict[builtins.str, typing.Any]],
        resource_group_id: builtins.str,
        description: typing.Optional[builtins.str] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Properties for the Azure Virtual Network Manager.

        Extends AzapiResourceProps with Virtual Network Manager specific properties

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
        :param network_manager_scope_accesses: Array of features enabled for the network manager Valid values: "Connectivity", "SecurityAdmin", "Routing".
        :param network_manager_scopes: Defines the scope of management (management groups and/or subscriptions) At least one of managementGroups or subscriptions must be specified.
        :param resource_group_id: Resource ID of the resource group where the network manager will be created.
        :param description: Optional description of the network manager.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(network_manager_scopes, dict):
            network_manager_scopes = NetworkManagerScopes(**network_manager_scopes)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4a0ec3aabe1ac825a2de49864b7c49b117c3023bae215a177640ee55ed5a8e87)
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
            check_type(argname="argument network_manager_scope_accesses", value=network_manager_scope_accesses, expected_type=type_hints["network_manager_scope_accesses"])
            check_type(argname="argument network_manager_scopes", value=network_manager_scopes, expected_type=type_hints["network_manager_scopes"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "network_manager_scope_accesses": network_manager_scope_accesses,
            "network_manager_scopes": network_manager_scopes,
            "resource_group_id": resource_group_id,
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
    def network_manager_scope_accesses(self) -> typing.List[builtins.str]:
        '''Array of features enabled for the network manager Valid values: "Connectivity", "SecurityAdmin", "Routing".

        Example::

            ["Connectivity", "SecurityAdmin"]
        '''
        result = self._values.get("network_manager_scope_accesses")
        assert result is not None, "Required property 'network_manager_scope_accesses' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def network_manager_scopes(self) -> NetworkManagerScopes:
        '''Defines the scope of management (management groups and/or subscriptions) At least one of managementGroups or subscriptions must be specified.'''
        result = self._values.get("network_manager_scopes")
        assert result is not None, "Required property 'network_manager_scopes' is missing"
        return typing.cast(NetworkManagerScopes, result)

    @builtins.property
    def resource_group_id(self) -> builtins.str:
        '''Resource ID of the resource group where the network manager will be created.

        Example::

            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/my-rg"
        '''
        result = self._values.get("resource_group_id")
        assert result is not None, "Required property 'resource_group_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Optional description of the network manager.

        Example::

            "Central network management for production workloads"
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed.

        Example::

            ["tags"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VirtualNetworkManagerProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AddConnectivityConfigurationProps",
    "AddIpamPoolProps",
    "AddNetworkGroupProps",
    "AddSecurityAdminConfigurationProps",
    "AddressPrefixItem",
    "CidrValidationResult",
    "ConnectivityConfiguration",
    "ConnectivityConfigurationBody",
    "ConnectivityConfigurationProperties",
    "ConnectivityConfigurationProps",
    "ConnectivityGroupItem",
    "Hub",
    "IpamPool",
    "IpamPoolBody",
    "IpamPoolProperties",
    "IpamPoolProps",
    "IpamPoolStaticCidr",
    "IpamPoolStaticCidrBody",
    "IpamPoolStaticCidrProperties",
    "IpamPoolStaticCidrProps",
    "NetworkGroup",
    "NetworkGroupBody",
    "NetworkGroupProperties",
    "NetworkGroupProps",
    "NetworkGroupStaticMember",
    "NetworkGroupStaticMemberBody",
    "NetworkGroupStaticMemberProperties",
    "NetworkGroupStaticMemberProps",
    "NetworkManagerScopes",
    "ParsedCidr",
    "SecurityAdminConfiguration",
    "SecurityAdminConfigurationBody",
    "SecurityAdminConfigurationProperties",
    "SecurityAdminConfigurationProps",
    "SecurityAdminConfigurationRuleGroupItem",
    "SecurityAdminRule",
    "SecurityAdminRuleBody",
    "SecurityAdminRuleCollection",
    "SecurityAdminRuleCollectionBody",
    "SecurityAdminRuleCollectionProperties",
    "SecurityAdminRuleCollectionProps",
    "SecurityAdminRuleProperties",
    "SecurityAdminRuleProps",
    "VirtualNetworkManager",
    "VirtualNetworkManagerBody",
    "VirtualNetworkManagerProperties",
    "VirtualNetworkManagerProps",
]

publication.publish()

def _typecheckingstub__9067cda1c1ca6604c5b19911c0aee21f4e9e0620d601c9afdba212b26c447e2d(
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
    applies_to_groups: typing.Sequence[typing.Union[ConnectivityGroupItem, typing.Dict[builtins.str, typing.Any]]],
    connectivity_topology: builtins.str,
    delete_existing_peering: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    hubs: typing.Optional[typing.Sequence[typing.Union[Hub, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    is_global: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4ef1b60542c80aedd698ead341c83c9ab8812f6600a6a68f400f020b584e2130(
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
    address_prefixes: typing.Sequence[builtins.str],
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parent_pool_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c8953b486069d04eee14dbd37c1c98147b6aebdd8762a6dcaf93e02cd248a5bb(
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
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    member_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e762870ecd662ea069dec416817d543c9a8fc2b66397cb08ff21d7e97505b574(
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
    apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0e4ddf951b63d0f5ce781f49a76c09701d5028bcc2f424a4cc463abf14536198(
    *,
    address_prefix: typing.Optional[builtins.str] = None,
    address_prefix_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fe9782844d5cce439426f3b2fe6540622615e1bb02269b283ee2483698c4111f(
    *,
    errors: typing.Sequence[builtins.str],
    valid: builtins.bool,
    warnings: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d1ff32f53e75259a5a3d4754e183ce80c858ae2f0f9b1730fb52b423e1caef7f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    applies_to_groups: typing.Sequence[typing.Union[ConnectivityGroupItem, typing.Dict[builtins.str, typing.Any]]],
    connectivity_topology: builtins.str,
    network_manager_id: builtins.str,
    delete_existing_peering: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    hubs: typing.Optional[typing.Sequence[typing.Union[Hub, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    is_global: typing.Optional[builtins.bool] = None,
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

def _typecheckingstub__7b262c98cad6d0553aef0d36bfdf17e7fc11ae842759700686341dd153d4aa43(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__053c84ec0645a236be4d383be7e0409703f3c567088abe3fb65394a6c05e01f5(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f488d7ef1b83639e2f05268d756710a7e6d455e01af72c9faed253e2c5d8ff0b(
    *,
    properties: typing.Union[ConnectivityConfigurationProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e7f6ff7f657ef34c950d8200ccedba92bb4eb603d5e731f65664ebe81b917c34(
    *,
    applies_to_groups: typing.Sequence[typing.Union[ConnectivityGroupItem, typing.Dict[builtins.str, typing.Any]]],
    connectivity_topology: builtins.str,
    delete_existing_peering: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    hubs: typing.Optional[typing.Sequence[typing.Union[Hub, typing.Dict[builtins.str, typing.Any]]]] = None,
    is_global: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__52a7359b599ad07d1908828c4605eb7f0d1616917586f4ed136af9dea4c59585(
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
    applies_to_groups: typing.Sequence[typing.Union[ConnectivityGroupItem, typing.Dict[builtins.str, typing.Any]]],
    connectivity_topology: builtins.str,
    network_manager_id: builtins.str,
    delete_existing_peering: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    hubs: typing.Optional[typing.Sequence[typing.Union[Hub, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    is_global: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb61833fbaa1cfdc48376948e6ee5a955d10784354894bfef1bc936a8ce46ab5(
    *,
    network_group_id: builtins.str,
    group_connectivity: typing.Optional[builtins.str] = None,
    is_global: typing.Optional[builtins.bool] = None,
    use_hub_gateway: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__58c9c055f69994425655e1bd56b47d4bc4fc45630b7391a69478a2944dbbb8b5(
    *,
    resource_id: builtins.str,
    resource_type: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__478fc237f17c3abd500163dd06e9d933e2c663a76352e1c0669faf9c18d02983(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    address_prefixes: typing.Sequence[builtins.str],
    network_manager_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parent_pool_name: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__f1b5825e99d9e0955cd52540fb724e8a0b11c80035a3a25d32db9d5bfa2dd846(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2efba36cdf487fb1b14d1ce5fbb195ee1637f0757605f6522b7a73a47d1caade(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__06488cb4f1d496e46e5d857153ac0208e29af9521cfe41a86003ce88daef0d1d(
    *,
    location: builtins.str,
    properties: typing.Union[IpamPoolProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7f8e99cafa7ef3b7de0dd6b963e4a27e1795de84bf286b26b3dd5e41aefeb9ab(
    *,
    address_prefixes: typing.Sequence[builtins.str],
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    parent_pool_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a1e87725ac84c620b8638278addf40bd21d197632007e0210f62fdecf2d991c3(
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
    address_prefixes: typing.Sequence[builtins.str],
    network_manager_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parent_pool_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb4df849139f35ea82eba3f6495e5592b7cc63a88da8362965ae492598b7336b(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    address_prefixes: typing.Sequence[builtins.str],
    ipam_pool_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__ee6fbdb9dd4215a9694e78c5d30b790b5886141a04d95f4d752d86f12e30bab2(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1d14ddd57e8b26a1dc99e79ea7f3a98637e8d1a7596b4c78c1ac667ae8ab6018(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a6206392e666bb5236ace2451d32e2438bd940b6245959f8420928a91d11f1df(
    *,
    properties: typing.Union[IpamPoolStaticCidrProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13c9c9827a4dd6bb3bb47f08c26fa9f85627064954d227f717628179da7aacc2(
    *,
    address_prefixes: typing.Sequence[builtins.str],
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__026a1c71e560d8d377bb28676a42ec08b6937b6ab584bc6e989c9a87a46a68aa(
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
    address_prefixes: typing.Sequence[builtins.str],
    ipam_pool_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__82b257d3748ba2718b6f141ec0c5214286a9db1ccad9fdb7c1e730c0ed4794cf(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    network_manager_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    member_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__8c88f333525baf98ffdda159d1da4c6da25b597cb8ca98bc65b7609ca32dd9d7(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3f1c558c14dc1978789dba46f4692eadae5f6fd3814e2ce81b440c6c518f39f5(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e0068555a8322d50865dfac53c54fbed95d7c828cc11858159ece52dc93fa154(
    *,
    properties: typing.Optional[typing.Union[NetworkGroupProperties, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c0ecad6ba61dce163e3aee8cc642ba6c6cc83b1c540d7d6f2654bb2358aac15d(
    *,
    description: typing.Optional[builtins.str] = None,
    member_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__36c9e7efa2e26645fca2a92f623cb73ab4b0f3c5563709e1c3a0b20a6c6225ea(
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
    network_manager_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    member_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d0e17b9bb9eda9e6538a0876e13673232b7b38d44d4995e93cb2539c1b823a8(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    network_group_id: builtins.str,
    resource_id: builtins.str,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__b0e19fd04334bf1e574f9f4b6c42f644f7ae32a8323db8e7b1f8a552634f627b(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0c7d5f780f8128a9a5ef2837b33540a02fafa8011ebe1b9ebd753f33d289bc0a(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cce8e848a076bf2506663c5e18bbdd762b3a696b68631b92f04a0cc696cd45ed(
    *,
    properties: typing.Union[NetworkGroupStaticMemberProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1cc7781ff2de59c4c986102638ca9f730c9c956e4b7a934085c0a1f1a4abad01(
    *,
    resource_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed067b52b2d49a1109878c2894cd9d4e26e955a2207984b18c825840afac9b7f(
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
    network_group_id: builtins.str,
    resource_id: builtins.str,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8653db1d179467fedc47bfffee702aa755f160d3c3253bb13482b4e9345793da(
    *,
    management_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
    subscriptions: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f7b0dc08f0f7a342fe1806c118c4af5b6dd83ed356981e32a236fd8bad09d6a6(
    *,
    cidr: builtins.str,
    first_ip: builtins.str,
    last_ip: builtins.str,
    netmask: builtins.str,
    network: builtins.str,
    prefix: jsii.Number,
    total_addresses: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3f2b6969e8dbe1c88d520863369c1989f1511ed1e9f4f2b114ab79b1d631ec25(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    network_manager_id: builtins.str,
    apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__323a90192e6e57bbec48015b1fbb222d3eced4a8779d62df8833d5bfd4dfb3e9(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e15489bde546ec2d9226bdede73bdecefb8becfbe640de8dac7fb27ed4b8191(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6fbd16501e04c88e7df93b3bdfd01f98df7f2d8bd536e0bca8eb5ab06bc529aa(
    *,
    properties: typing.Optional[typing.Union[SecurityAdminConfigurationProperties, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d5a853ec4c24f7afeeaebb18839f42b8fcc3dc9c2c3bbd3971059f82e5ebddcc(
    *,
    apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dfdea866c08ed9716ebddf5359d0b23963abd102ed5ad99e48cfa8ac5e4df544(
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
    network_manager_id: builtins.str,
    apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0cc16b8007d9b7bad7f0cfea9cd8d692e6f99a19a2c8c81e54f3e6b6ab49e2ef(
    *,
    network_group_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__89d935e5abacdfbf4ff98fa7f2dd8e725ebab87891bf3e85987c2943f5a16c3d(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    action: builtins.str,
    direction: builtins.str,
    priority: jsii.Number,
    protocol: builtins.str,
    rule_collection_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    destinations: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    sources: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
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

def _typecheckingstub__d4ca993d0401daf2b427e35d0e4aa7b64cdf0435684ce0d83614c2d482b01cec(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__84e42ae57c0008a7dc018fab49950ef2d6eff598bc8b0283a9c8aace4cd41c3e(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8b490d90710f75641f1f537a504078302eb0773da843d9a8be43072aa346ed26(
    *,
    kind: builtins.str,
    properties: typing.Union[SecurityAdminRuleProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__995acee61067cd90a82200a2d8d7213bb388ec3b0fc3a7d11e462244e93df4be(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    applies_to_groups: typing.Sequence[typing.Union[SecurityAdminConfigurationRuleGroupItem, typing.Dict[builtins.str, typing.Any]]],
    security_admin_configuration_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__06be4f8a1f38e7a92702375cb71d01dfdef143ead620c9e444cbb65fdf55c591(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d735be05638eb29792d970d794f377eaa3a669a8d00f81fcc46621f9c7886c2b(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56c4c02fea0425f4895f3016c25f08dcc6c0c7ae2d50eed64ecc315ba34feefb(
    *,
    properties: typing.Union[SecurityAdminRuleCollectionProperties, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3dab1df423dfe9db6be3aa4c4f23fb50be285bd95163799a70b53403c8cf1e53(
    *,
    applies_to_groups: typing.Sequence[typing.Union[SecurityAdminConfigurationRuleGroupItem, typing.Dict[builtins.str, typing.Any]]],
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9b38b587a662f7c374e0a3cdd126baaf383015ec7238725c3459275ddb32f5ca(
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
    applies_to_groups: typing.Sequence[typing.Union[SecurityAdminConfigurationRuleGroupItem, typing.Dict[builtins.str, typing.Any]]],
    security_admin_configuration_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__550219bc2e504a27914d875da5be1438430413cd0d71e248ef3e7b3d4426b7de(
    *,
    action: builtins.str,
    direction: builtins.str,
    priority: jsii.Number,
    protocol: builtins.str,
    description: typing.Optional[builtins.str] = None,
    destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    destinations: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
    source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    sources: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__21b9010c419654c3ef2dbde67860d35b2c60135746f420c03e42b77628426c84(
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
    action: builtins.str,
    direction: builtins.str,
    priority: jsii.Number,
    protocol: builtins.str,
    rule_collection_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    destination_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    destinations: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    source_port_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    sources: typing.Optional[typing.Sequence[typing.Union[AddressPrefixItem, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__948ae326bcac3d52772b9f9b8500de54d16359633dbaf94c5fe5d27c799b8816(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    network_manager_scope_accesses: typing.Sequence[builtins.str],
    network_manager_scopes: typing.Union[NetworkManagerScopes, typing.Dict[builtins.str, typing.Any]],
    resource_group_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__1c8a65b5c9b61c2b5e0054f35f9af295681dec331d601e42fdca917122649c1e(
    id: builtins.str,
    *,
    applies_to_groups: typing.Sequence[typing.Union[ConnectivityGroupItem, typing.Dict[builtins.str, typing.Any]]],
    connectivity_topology: builtins.str,
    delete_existing_peering: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    hubs: typing.Optional[typing.Sequence[typing.Union[Hub, typing.Dict[builtins.str, typing.Any]]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    is_global: typing.Optional[builtins.bool] = None,
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

def _typecheckingstub__179a76045ae005ae8883fff58026a066feac3ad00b4b29ee68592e539b7d5840(
    id: builtins.str,
    *,
    address_prefixes: typing.Sequence[builtins.str],
    description: typing.Optional[builtins.str] = None,
    display_name: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    parent_pool_name: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__57d98e78bce93b2ab43ca1fdfaf1ad93002f24daa6f2b0285486466a3d21055b(
    id: builtins.str,
    *,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    member_type: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__f8e8e3653af2d2de847c56cbbb45a835b8cb75635f81ba5968bf8de8208efb9f(
    id: builtins.str,
    *,
    apply_on_network_intent_policy_based_services: typing.Optional[typing.Sequence[builtins.str]] = None,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
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

def _typecheckingstub__e31606711aff3d4e56c87d9eaf03a85a8be1170ad7e8738b0e67e1b759dc0ca1(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b6a056a991fc21e9b24d59db7202c5b9de837195487eb04de769f92a6fce04a6(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c164365cdc645d58840f31b583f81b72cf282acb94bb42a5805f81b39466ddcd(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2afd50e262858169f0714aeaa0348790ae12e6ea00566a97326fb8c472d3c667(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c23bcec99dcce6cd54645c408bdbc4c136773a579b4aece1f0935938e883e8f5(
    *,
    location: builtins.str,
    properties: typing.Union[VirtualNetworkManagerProperties, typing.Dict[builtins.str, typing.Any]],
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__839408946e19e8af0874bf39f94a3aff4f4a681404ed35169d2eda5b4d53d0c2(
    *,
    network_manager_scope_accesses: typing.Sequence[builtins.str],
    network_manager_scopes: typing.Union[NetworkManagerScopes, typing.Dict[builtins.str, typing.Any]],
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4a0ec3aabe1ac825a2de49864b7c49b117c3023bae215a177640ee55ed5a8e87(
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
    network_manager_scope_accesses: typing.Sequence[builtins.str],
    network_manager_scopes: typing.Union[NetworkManagerScopes, typing.Dict[builtins.str, typing.Any]],
    resource_group_id: builtins.str,
    description: typing.Optional[builtins.str] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass
