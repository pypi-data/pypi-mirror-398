r'''
# Azure Kubernetes Service (AKS) Module

This module provides a unified, version-aware Azure Kubernetes Service (AKS) cluster construct using the VersionedAzapiResource framework.

## Table of Contents

* [Features](#features)
* [Installation](#installation)
* [Supported API Versions](#supported-api-versions)
* [Basic Usage](#basic-usage)
* [Advanced Usage](#advanced-usage)

  * [Version Pinning](#version-pinning)
  * [Multiple Node Pools](#multiple-node-pools)
  * [Advanced Networking](#advanced-networking)
  * [Security Configuration](#security-configuration)
  * [Auto-Scaling](#auto-scaling)
  * [Add-ons Configuration](#add-ons-configuration)
  * [Private Cluster](#private-cluster)
  * [Windows Node Pools](#windows-node-pools)
* [Configuration Reference](#configuration-reference)

  * [Required Properties](#required-properties)
  * [Optional Properties](#optional-properties)
  * [Node Pool Configuration](#node-pool-configuration)
  * [Network Profile](#network-profile)
  * [Security Features](#security-features)
  * [Add-ons](#add-ons)
* [Outputs](#outputs)
* [API Version Management](#api-version-management)
* [Best Practices](#best-practices)
* [Contributing](#contributing)
* [License](#license)

## Features

* **Automatic Version Management**: Defaults to the latest stable API version (2025-08-01)
* **Version Pinning**: Explicitly specify API versions for stability
* **Multiple Node Pools**: Support for system and user node pools with different configurations
* **Advanced Networking**: Azure CNI, Kubenet, custom VNET integration
* **Identity Management**: SystemAssigned and UserAssigned managed identities
* **Security**: Azure Active Directory integration, RBAC, private clusters, workload identity
* **Auto-Scaling**: Cluster and pod auto-scaling capabilities
* **Add-ons**: Built-in support for monitoring, policy, and other Azure services
* **Windows Support**: Windows and Linux node pools in the same cluster
* **Schema Validation**: Automatic validation of properties against API schemas
* **Multi-Language Support**: Full JSII compliance for TypeScript, Python, Java, and .NET
* **Type Safety**: Complete TypeScript type definitions

## Installation

```bash
npm install @microsoft/terraform-cdk-constructs
```

## Supported API Versions

| API Version | Status | Features |
|-------------|--------|----------|
| 2025-05-01  | ✅ Active | Stable release with comprehensive AKS features |
| 2025-07-01  | ✅ Active | Enhanced security and performance features |
| 2025-08-01  | ✅ Active, Latest | Latest API version with newest features and improvements |

## Basic Usage

Create a basic AKS cluster with a system node pool:

```python
import { AksCluster } from '@microsoft/terraform-cdk-constructs/azure-aks';
import { Group } from '@microsoft/terraform-cdk-constructs/azure-resourcegroup';

// Create a resource group
const resourceGroup = new Group(this, 'rg', {
  name: 'rg-aks-example',
  location: 'eastus',
});

// Create an AKS cluster
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [{
    name: 'default',
    count: 3,
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
  }],
  identity: {
    type: 'SystemAssigned',
  },
  tags: {
    environment: 'production',
    project: 'myapp',
  },
});
```

## Advanced Usage

### Version Pinning

Pin to a specific API version for stability:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  apiVersion: '2025-07-01', // Pin to specific version
  dnsPrefix: 'myaks',
  kubernetesVersion: '1.28.3',
  agentPoolProfiles: [{
    name: 'system',
    count: 3,
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
  }],
  identity: {
    type: 'SystemAssigned',
  },
});
```

### Multiple Node Pools

Configure multiple node pools for different workload types:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [
    {
      name: 'system',
      count: 3,
      vmSize: 'Standard_D2s_v3',
      mode: 'System',
      osDiskSizeGB: 128,
      availabilityZones: ['1', '2', '3'],
    },
    {
      name: 'user',
      count: 5,
      vmSize: 'Standard_D4s_v3',
      mode: 'User',
      enableAutoScaling: true,
      minCount: 3,
      maxCount: 10,
      nodeLabels: {
        workload: 'compute-intensive',
      },
      nodeTaints: ['workload=compute:NoSchedule'],
    },
  ],
  identity: {
    type: 'SystemAssigned',
  },
});
```

### Advanced Networking

Configure Azure CNI with custom networking:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [{
    name: 'system',
    count: 3,
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
    vnetSubnetID: '/subscriptions/.../subnets/aks-subnet',
  }],
  identity: {
    type: 'SystemAssigned',
  },
  networkProfile: {
    networkPlugin: 'azure',
    networkPolicy: 'azure',
    serviceCidr: '10.0.0.0/16',
    dnsServiceIP: '10.0.0.10',
    loadBalancerSku: 'standard',
    outboundType: 'loadBalancer',
  },
});
```

### Security Configuration

Enable Azure Active Directory integration and RBAC:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [{
    name: 'system',
    count: 3,
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
  }],
  identity: {
    type: 'SystemAssigned',
  },
  enableRBAC: true,
  aadProfile: {
    managed: true,
    enableAzureRBAC: true,
    adminGroupObjectIDs: ['group-id-1', 'group-id-2'],
  },
  securityProfile: {
    workloadIdentity: {
      enabled: true,
    },
    defender: {
      enabled: true,
      logAnalyticsWorkspaceResourceId: '/subscriptions/.../workspaces/my-workspace',
    },
  },
  disableLocalAccounts: true,
});
```

### Auto-Scaling

Configure cluster auto-scaler with custom settings:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [{
    name: 'system',
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
    enableAutoScaling: true,
    minCount: 3,
    maxCount: 10,
  }],
  identity: {
    type: 'SystemAssigned',
  },
  autoScalerProfile: {
    scaleDownDelayAfterAdd: '10m',
    scaleDownUnneededTime: '10m',
    scaleDownUtilizationThreshold: '0.5',
    maxGracefulTerminationSec: '600',
    scanInterval: '10s',
  },
  workloadAutoScalerProfile: {
    keda: {
      enabled: true,
    },
    verticalPodAutoscaler: {
      enabled: true,
    },
  },
});
```

### Add-ons Configuration

Enable monitoring and policy add-ons:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [{
    name: 'system',
    count: 3,
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
  }],
  identity: {
    type: 'SystemAssigned',
  },
  addonProfiles: {
    omsagent: {
      enabled: true,
      config: {
        logAnalyticsWorkspaceResourceID: '/subscriptions/.../workspaces/my-workspace',
      },
    },
    azurepolicy: {
      enabled: true,
    },
    azureKeyvaultSecretsProvider: {
      enabled: true,
      config: {
        enableSecretRotation: 'true',
        rotationPollInterval: '2m',
      },
    },
  },
});
```

### Private Cluster

Create a private AKS cluster:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [{
    name: 'system',
    count: 3,
    vmSize: 'Standard_D2s_v3',
    mode: 'System',
    vnetSubnetID: '/subscriptions/.../subnets/aks-subnet',
  }],
  identity: {
    type: 'SystemAssigned',
  },
  apiServerAccessProfile: {
    enablePrivateCluster: true,
    privateDNSZone: 'system',
    enablePrivateClusterPublicFQDN: false,
  },
  publicNetworkAccess: 'Disabled',
  networkProfile: {
    networkPlugin: 'azure',
    serviceCidr: '10.0.0.0/16',
    dnsServiceIP: '10.0.0.10',
  },
});
```

### Windows Node Pools

Configure Windows and Linux node pools:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'my-aks-cluster',
  location: 'eastus',
  resourceGroupId: resourceGroup.id,
  dnsPrefix: 'myaks',
  agentPoolProfiles: [
    {
      name: 'system',
      count: 3,
      vmSize: 'Standard_D2s_v3',
      mode: 'System',
      osType: 'Linux',
    },
    {
      name: 'winpool',
      count: 3,
      vmSize: 'Standard_D4s_v3',
      mode: 'User',
      osType: 'Windows',
    },
  ],
  identity: {
    type: 'SystemAssigned',
  },
  windowsProfile: {
    adminUsername: 'azureuser',
    adminPassword: 'P@ssw0rd1234!',
    licenseType: 'Windows_Server',
  },
  networkProfile: {
    networkPlugin: 'azure',
    serviceCidr: '10.0.0.0/16',
    dnsServiceIP: '10.0.0.10',
  },
});
```

## Configuration Reference

### Required Properties

* **`name`** (string): The name of the AKS cluster. Must be 1-63 characters, start and end with alphanumeric, and can contain hyphens.
* **`location`** (string): The Azure region where the cluster will be created (e.g., 'eastus', 'westus2').
* **`resourceGroupId`** (string): Resource group ID where the AKS cluster will be created.
* **`dnsPrefix`** (string): DNS prefix for the cluster. Must be 1-54 characters, start and end with alphanumeric, and can contain hyphens.
* **`agentPoolProfiles`** (array): Array of agent pool configurations. At least one agent pool is required.
* **`identity`** (object): The identity configuration for the AKS cluster (SystemAssigned or UserAssigned).

### Optional Properties

* **`apiVersion`** (string): API version to use. Defaults to latest (2025-08-01).
* **`sku`** (object): The SKU (pricing tier) for the cluster.

  * `name`: SKU name ('Base' or 'Standard')
  * `tier`: SKU tier ('Free', 'Standard', 'Premium')
* **`kubernetesVersion`** (string): Kubernetes version (e.g., '1.28.3', '1.29.0').
* **`enableRBAC`** (boolean): Enable Kubernetes Role-Based Access Control. Default: true.
* **`nodeResourceGroup`** (string): Name of the resource group for cluster nodes. Auto-generated if not specified.
* **`tags`** (object): Key-value pairs for resource tagging.
* **`ignoreChanges`** (array): Properties to ignore during updates (e.g., ['kubernetesVersion']).

### Node Pool Configuration

Each agent pool profile supports:

* **`name`** (string, required): Name of the node pool (12 characters max, lowercase alphanumeric).
* **`vmSize`** (string, required): VM size for nodes (e.g., 'Standard_D2s_v3').
* **`mode`** (string): Node pool mode ('System' or 'User'). Default: 'User'.
* **`count`** (number): Number of nodes. Required if not using auto-scaling.
* **`enableAutoScaling`** (boolean): Enable auto-scaling for the node pool.
* **`minCount`** (number): Minimum node count when auto-scaling is enabled.
* **`maxCount`** (number): Maximum node count when auto-scaling is enabled.
* **`osType`** (string): Operating system type ('Linux' or 'Windows'). Default: 'Linux'.
* **`osDiskSizeGB`** (number): OS disk size in GB.
* **`osDiskType`** (string): OS disk type ('Managed', 'Ephemeral').
* **`vnetSubnetID`** (string): Subnet ID for node pool networking.
* **`podSubnetID`** (string): Subnet ID for pod networking (Azure CNI overlay).
* **`availabilityZones`** (array): Availability zones for nodes (e.g., ['1', '2', '3']).
* **`maxPods`** (number): Maximum pods per node.
* **`nodeLabels`** (object): Kubernetes labels for nodes.
* **`nodeTaints`** (array): Kubernetes taints for nodes.
* **`enableEncryptionAtHost`** (boolean): Enable encryption at host.
* **`enableUltraSSD`** (boolean): Enable Ultra SSD support.
* **`enableFIPS`** (boolean): Enable FIPS 140-2 compliance.

### Network Profile

* **`networkPlugin`** (string): Network plugin ('azure', 'kubenet', 'none').
* **`networkPolicy`** (string): Network policy ('azure', 'calico', 'cilium').
* **`networkMode`** (string): Network mode ('transparent', 'bridge').
* **`podCidr`** (string): CIDR range for pods (Kubenet only).
* **`serviceCidr`** (string): CIDR range for services.
* **`dnsServiceIP`** (string): IP address for DNS service.
* **`dockerBridgeCidr`** (string): CIDR range for Docker bridge.
* **`outboundType`** (string): Outbound routing method ('loadBalancer', 'userDefinedRouting', 'managedNATGateway').
* **`loadBalancerSku`** (string): Load balancer SKU ('basic', 'standard').
* **`loadBalancerProfile`** (object): Load balancer configuration.

### Security Features

* **`aadProfile`** (object): Azure Active Directory integration.

  * `managed`: Enable managed AAD integration.
  * `enableAzureRBAC`: Enable Azure RBAC for Kubernetes authorization.
  * `adminGroupObjectIDs`: AAD group IDs with admin access.
  * `tenantID`: Azure AD tenant ID.
* **`apiServerAccessProfile`** (object): API server access configuration.

  * `authorizedIPRanges`: IP ranges allowed to access API server.
  * `enablePrivateCluster`: Enable private cluster.
  * `privateDNSZone`: Private DNS zone configuration.
  * `disableRunCommand`: Disable run command for security.
* **`securityProfile`** (object): Security settings.

  * `workloadIdentity`: Workload identity configuration.
  * `defender`: Microsoft Defender for Containers.
  * `imageCleaner`: Automated image cleanup.
  * `azureKeyVaultKms`: Azure Key Vault KMS integration.
* **`disableLocalAccounts`** (boolean): Disable local Kubernetes accounts.
* **`publicNetworkAccess`** (string): Public network access ('Enabled' or 'Disabled').

### Add-ons

Common add-ons (configured via `addonProfiles`):

* **`omsagent`**: Azure Monitor for containers
* **`azurepolicy`**: Azure Policy for Kubernetes
* **`azureKeyvaultSecretsProvider`**: Azure Key Vault secrets provider
* **`ingressApplicationGateway`**: Application Gateway Ingress Controller
* **`openServiceMesh`**: Open Service Mesh
* **`gitops`**: GitOps with Flux

Each addon has:

* `enabled` (boolean): Enable/disable the addon
* `config` (object): Addon-specific configuration

## Outputs

The AksCluster construct provides the following outputs:

```python
// Direct properties
aksCluster.id                    // The resource ID
aksCluster.fqdn                  // The FQDN of the cluster
aksCluster.privateFqdn           // The private FQDN (if private cluster)
aksCluster.kubeConfig            // Kubernetes configuration (sensitive)
aksCluster.currentKubernetesVersion  // Current Kubernetes version
aksCluster.nodeResourceGroupName // Node resource group name

// Terraform outputs
aksCluster.idOutput              // TerraformOutput for ID
aksCluster.nameOutput            // TerraformOutput for name
aksCluster.locationOutput        // TerraformOutput for location
aksCluster.tagsOutput            // TerraformOutput for tags
aksCluster.fqdnOutput            // TerraformOutput for FQDN
aksCluster.kubeConfigOutput      // TerraformOutput for kubeConfig (sensitive)
```

## API Version Management

### Automatic Latest Version

By default, the construct uses the latest stable API version:

```python
const aksCluster = new AksCluster(this, 'aks', {
  // No apiVersion specified - uses latest (2025-08-01)
  name: 'my-aks-cluster',
  // ... other properties
});
```

### Version Pinning

Pin to a specific version for stability:

```python
const aksCluster = new AksCluster(this, 'aks', {
  apiVersion: '2025-07-01', // Pin to specific version
  name: 'my-aks-cluster',
  // ... other properties
});
```

### Version Migration

When migrating between versions, the framework provides:

* Schema validation for the target version
* Migration warnings for deprecated properties
* Breaking change detection
* Automatic property transformation where possible

## Best Practices

### Production Deployments

1. **Use SystemAssigned Identity**: Prefer SystemAssigned managed identity over service principals for better security and easier management.

```python
identity: {
  type: 'SystemAssigned',
}
```

1. **Enable Auto-Scaling**: Configure auto-scaling for production workloads to handle varying loads.

```python
agentPoolProfiles: [{
  enableAutoScaling: true,
  minCount: 3,
  maxCount: 10,
}]
```

1. **Use Standard Tier SKU**: Use Standard tier for production clusters to get SLA guarantees.

```python
sku: {
  name: 'Standard',
  tier: 'Standard',
}
```

1. **Configure Network Policies**: Enable network policies for security.

```python
networkProfile: {
  networkPlugin: 'azure',
  networkPolicy: 'azure', // or 'calico'
}
```

1. **Enable Monitoring**: Always enable monitoring for production clusters.

```python
addonProfiles: {
  omsagent: {
    enabled: true,
    config: {
      logAnalyticsWorkspaceResourceID: workspaceId,
    },
  },
}
```

1. **Use Availability Zones**: Deploy nodes across availability zones for high availability.

```python
agentPoolProfiles: [{
  availabilityZones: ['1', '2', '3'],
}]
```

1. **Implement RBAC**: Enable RBAC and Azure AD integration.

```python
enableRBAC: true,
aadProfile: {
  managed: true,
  enableAzureRBAC: true,
}
```

1. **Private Clusters for Sensitive Workloads**: Use private clusters for enhanced security.

```python
apiServerAccessProfile: {
  enablePrivateCluster: true,
}
```

1. **Separate System and User Node Pools**: Use dedicated system node pools for critical workloads.

```python
agentPoolProfiles: [
  { name: 'system', mode: 'System' },
  { name: 'user', mode: 'User' },
]
```

1. **Version Pinning for Stability**: Pin API versions in production to avoid unexpected changes.

```python
apiVersion: '2025-07-01',
```

## Contributing

Contributions are welcome! Please see the [Contributing Guide](../../CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.

## Monitoring

The AKS Cluster construct provides built-in monitoring capabilities through the `defaultMonitoring()` static method.

### Default Monitoring Configuration

```python
import { AksCluster } from '@cdktf/azure-aks';
import { ActionGroup } from '@cdktf/azure-actiongroup';
import { LogAnalyticsWorkspace } from '@cdktf/azure-loganalyticsworkspace';

const actionGroup = new ActionGroup(this, 'alerts', {
  // ... action group configuration
});

const workspace = new LogAnalyticsWorkspace(this, 'logs', {
  // ... workspace configuration
});

const aksCluster = new AksCluster(this, 'aks', {
  name: 'myakscluster',
  location: 'eastus',
  resourceGroupName: resourceGroup.name,
  // ... other properties
  monitoring: AksCluster.defaultMonitoring(
    actionGroup.id,
    workspace.id
  )
});
```

### Monitored Metrics

The default monitoring configuration includes:

1. **Node CPU Alert**

   * Metric: `node_cpu_usage_percentage`
   * Threshold: 80% (default)
   * Severity: Warning (2)
   * Triggers when node CPU usage exceeds threshold
2. **Node Memory Alert**

   * Metric: `node_memory_working_set_percentage`
   * Threshold: 80% (default)
   * Severity: Warning (2)
   * Triggers when node memory usage exceeds threshold
3. **Failed Pods Alert**

   * Metric: `kube_pod_status_phase` (Failed phase)
   * Threshold: 0 (any failed pod)
   * Severity: Error (1)
   * Triggers when pods enter failed state
4. **Cluster Deletion Alert**

   * Tracks AKS cluster deletion via Activity Log
   * Severity: Informational

### Custom Monitoring Configuration

Customize thresholds and severities:

```python
const aksCluster = new AksCluster(this, 'aks', {
  name: 'myakscluster',
  location: 'eastus',
  resourceGroupName: resourceGroup.name,
  monitoring: AksCluster.defaultMonitoring(
    actionGroup.id,
    workspace.id,
    {
      nodeCpuThreshold: 90,              // Higher CPU threshold
      nodeMemoryThreshold: 85,           // Higher memory threshold
      failedPodThreshold: 5,             // Alert only if >5 pods fail
      nodeCpuAlertSeverity: 1,          // Critical for CPU
      enableFailedPodAlert: false,       // Disable pod monitoring
    }
  )
});
```

### Monitoring Options

All available options:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `nodeCpuThreshold` | number | 80 | Node CPU usage percentage threshold |
| `nodeMemoryThreshold` | number | 80 | Node memory usage percentage threshold |
| `failedPodThreshold` | number | 0 | Failed pod count threshold |
| `enableNodeCpuAlert` | boolean | true | Enable/disable node CPU alert |
| `enableNodeMemoryAlert` | boolean | true | Enable/disable node memory alert |
| `enableFailedPodAlert` | boolean | true | Enable/disable failed pod alert |
| `enableDeletionAlert` | boolean | true | Enable/disable deletion tracking |
| `nodeCpuAlertSeverity` | 0|1|2|3|4 | 2 | Node CPU alert severity (0=Critical, 4=Verbose) |
| `nodeMemoryAlertSeverity` | 0|1|2|3|4 | 2 | Node memory alert severity |
| `failedPodAlertSeverity` | 0|1|2|3|4 | 1 | Failed pod alert severity |
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


class AksCluster(
    _AzapiResource_7e7f5b39,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksCluster",
):
    '''Unified Azure Kubernetes Service cluster implementation.

    This class provides a single, version-aware implementation that automatically handles version
    resolution, schema validation, and property transformation while maintaining full JSII compliance.

    The class uses the VersionedAzapiResource framework to provide:

    - Automatic latest version resolution (2025-07-01 as of this implementation)
    - Support for explicit version pinning when stability is required
    - Schema-driven property validation and transformation
    - Migration analysis and deprecation warnings
    - Full JSII compliance for multi-language support

    Example::

        // AKS cluster with explicit version pinning and advanced networking:
        const aksCluster = new AksCluster(this, "aks", {
          name: "my-aks-cluster",
          location: "eastus",
          resourceGroupId: resourceGroup.id,
          apiVersion: "2025-07-01",
          dnsPrefix: "myaks",
          kubernetesVersion: "1.28.3",
          agentPoolProfiles: [{
            name: "system",
            count: 3,
            vmSize: "Standard_D2s_v3",
            mode: "System",
            vnetSubnetID: subnet.id
          }],
          identity: {
            type: "SystemAssigned"
          },
          networkProfile: {
            networkPlugin: "azure",
            serviceCidr: "10.0.0.0/16",
            dnsServiceIP: "10.0.0.10"
          },
          enableRBAC: true
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        agent_pool_profiles: typing.Sequence[typing.Union["AksClusterAgentPoolProfile", typing.Dict[builtins.str, typing.Any]]],
        dns_prefix: builtins.str,
        aad_profile: typing.Optional[typing.Union["AksClusterAadProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        addon_profiles: typing.Optional[typing.Mapping[builtins.str, typing.Union["AksClusterAddonProfile", typing.Dict[builtins.str, typing.Any]]]] = None,
        api_server_access_profile: typing.Optional[typing.Union["AksClusterApiServerAccessProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        auto_scaler_profile: typing.Optional[typing.Union["AksClusterAutoScalerProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        disable_local_accounts: typing.Optional[builtins.bool] = None,
        disk_encryption_set_id: typing.Optional[builtins.str] = None,
        enable_rbac: typing.Optional[builtins.bool] = None,
        fqdn: typing.Optional[builtins.str] = None,
        http_proxy_config: typing.Optional[typing.Union["AksClusterHttpProxyConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union["AksClusterIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        kubernetes_version: typing.Optional[builtins.str] = None,
        linux_profile: typing.Optional[typing.Union["AksClusterLinuxProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        network_profile: typing.Optional[typing.Union["AksClusterNetworkProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        node_resource_group: typing.Optional[builtins.str] = None,
        oidc_issuer_profile: typing.Optional[typing.Union["AksClusterOidcIssuerProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        private_fqdn: typing.Optional[builtins.str] = None,
        public_network_access: typing.Optional[builtins.str] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        security_profile: typing.Optional[typing.Union["AksClusterSecurityProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        service_principal_profile: typing.Optional[typing.Union["AksClusterServicePrincipalProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        sku: typing.Optional[typing.Union["AksClusterSku", typing.Dict[builtins.str, typing.Any]]] = None,
        storage_profile: typing.Optional[typing.Union["AksClusterStorageProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        support_plan: typing.Optional[builtins.str] = None,
        windows_profile: typing.Optional[typing.Union["AksClusterWindowsProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        workload_auto_scaler_profile: typing.Optional[typing.Union["AksClusterWorkloadAutoScalerProfile", typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Creates a new Azure Kubernetes Service cluster using the VersionedAzapiResource framework.

        The constructor automatically handles version resolution, schema registration,
        validation, and resource creation.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
        :param agent_pool_profiles: The agent pool profiles for the cluster node pools At least one agent pool is required.
        :param dns_prefix: DNS prefix for the cluster.
        :param aad_profile: The Azure Active Directory integration configuration.
        :param addon_profiles: The addon profiles for cluster addons.
        :param api_server_access_profile: The API server access configuration.
        :param auto_scaler_profile: The auto-scaler configuration for the cluster.
        :param disable_local_accounts: Whether to disable local accounts. Default: false
        :param disk_encryption_set_id: The resource ID of the disk encryption set for encrypting disks.
        :param enable_rbac: Whether to enable Kubernetes Role-Based Access Control. Default: true
        :param fqdn: The FQDN for the cluster (read-only).
        :param http_proxy_config: The HTTP proxy configuration.
        :param identity: The identity configuration for the AKS cluster.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed or should not trigger updates.
        :param kubernetes_version: The Kubernetes version for the cluster.
        :param linux_profile: The Linux profile for SSH access.
        :param network_profile: The network configuration for the cluster.
        :param node_resource_group: The name of the resource group for cluster nodes If not specified, Azure will auto-generate the name.
        :param oidc_issuer_profile: The OIDC issuer profile for workload identity.
        :param private_fqdn: The private FQDN for the cluster (read-only).
        :param public_network_access: Whether the cluster is accessible from the public internet.
        :param resource_group_id: Resource group ID where the AKS cluster will be created.
        :param security_profile: The security profile for the cluster.
        :param service_principal_profile: The service principal profile for the cluster.
        :param sku: The SKU (pricing tier) for the AKS cluster.
        :param storage_profile: The storage profile for CSI drivers.
        :param support_plan: The support plan for the cluster.
        :param windows_profile: The Windows profile for Windows node pools.
        :param workload_auto_scaler_profile: The workload auto-scaler profile.
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
            type_hints = typing.get_type_hints(_typecheckingstub__1d287fdfd0aef1ba7e5ef73c249cce142f68d09b133fc16d778c5e80c8640791)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AksClusterProps(
            agent_pool_profiles=agent_pool_profiles,
            dns_prefix=dns_prefix,
            aad_profile=aad_profile,
            addon_profiles=addon_profiles,
            api_server_access_profile=api_server_access_profile,
            auto_scaler_profile=auto_scaler_profile,
            disable_local_accounts=disable_local_accounts,
            disk_encryption_set_id=disk_encryption_set_id,
            enable_rbac=enable_rbac,
            fqdn=fqdn,
            http_proxy_config=http_proxy_config,
            identity=identity,
            ignore_changes=ignore_changes,
            kubernetes_version=kubernetes_version,
            linux_profile=linux_profile,
            network_profile=network_profile,
            node_resource_group=node_resource_group,
            oidc_issuer_profile=oidc_issuer_profile,
            private_fqdn=private_fqdn,
            public_network_access=public_network_access,
            resource_group_id=resource_group_id,
            security_profile=security_profile,
            service_principal_profile=service_principal_profile,
            sku=sku,
            storage_profile=storage_profile,
            support_plan=support_plan,
            windows_profile=windows_profile,
            workload_auto_scaler_profile=workload_auto_scaler_profile,
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
        enable_deletion_alert: typing.Optional[builtins.bool] = None,
        enable_failed_pod_alert: typing.Optional[builtins.bool] = None,
        enable_node_cpu_alert: typing.Optional[builtins.bool] = None,
        enable_node_memory_alert: typing.Optional[builtins.bool] = None,
        failed_pod_alert_severity: typing.Optional[jsii.Number] = None,
        failed_pod_threshold: typing.Optional[jsii.Number] = None,
        node_cpu_alert_severity: typing.Optional[jsii.Number] = None,
        node_cpu_threshold: typing.Optional[jsii.Number] = None,
        node_memory_alert_severity: typing.Optional[jsii.Number] = None,
        node_memory_threshold: typing.Optional[jsii.Number] = None,
    ) -> _MonitoringConfig_7c28df74:
        '''Returns a production-ready monitoring configuration for AKS Clusters.

        This static factory method provides a complete MonitoringConfig with sensible defaults
        for AKS monitoring including node CPU, node memory, failed pod alerts, and deletion tracking.

        :param action_group_id: - The resource ID of the action group for alert notifications.
        :param workspace_id: - Optional Log Analytics workspace ID for diagnostic settings.
        :param enable_deletion_alert: Whether to enable AKS cluster deletion alert. Default: true
        :param enable_failed_pod_alert: Whether to enable failed pod alert. Default: true
        :param enable_node_cpu_alert: Whether to enable node CPU usage alert. Default: true
        :param enable_node_memory_alert: Whether to enable node memory usage alert. Default: true
        :param failed_pod_alert_severity: Severity level for failed pod alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose). Default: 1
        :param failed_pod_threshold: Threshold for failed pod count. Default: 0
        :param node_cpu_alert_severity: Severity level for node CPU alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose). Default: 2
        :param node_cpu_threshold: Threshold for node CPU usage percentage (0-100). Default: 80
        :param node_memory_alert_severity: Severity level for node memory alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose). Default: 2
        :param node_memory_threshold: Threshold for node memory usage percentage (0-100). Default: 80

        :return: A complete MonitoringConfig object ready to use in AksCluster props

        Example::

            // Custom thresholds and severities
            const aksCluster = new AksCluster(this, "aks", {
              // ... other properties ...
              monitoring: AksCluster.defaultMonitoring(
                actionGroup.id,
                workspace.id,
                {
                  nodeCpuThreshold: 90,
                  nodeMemoryThreshold: 90,
                  enableFailedPodAlert: false
                }
              )
            });
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__22175093416726718ef82aa45e47267e8e5951f976505e616eb946f6922de479)
            check_type(argname="argument action_group_id", value=action_group_id, expected_type=type_hints["action_group_id"])
            check_type(argname="argument workspace_id", value=workspace_id, expected_type=type_hints["workspace_id"])
        options = AksClusterMonitoringOptions(
            enable_deletion_alert=enable_deletion_alert,
            enable_failed_pod_alert=enable_failed_pod_alert,
            enable_node_cpu_alert=enable_node_cpu_alert,
            enable_node_memory_alert=enable_node_memory_alert,
            failed_pod_alert_severity=failed_pod_alert_severity,
            failed_pod_threshold=failed_pod_threshold,
            node_cpu_alert_severity=node_cpu_alert_severity,
            node_cpu_threshold=node_cpu_threshold,
            node_memory_alert_severity=node_memory_alert_severity,
            node_memory_threshold=node_memory_threshold,
        )

        return typing.cast(_MonitoringConfig_7c28df74, jsii.sinvoke(cls, "defaultMonitoring", [action_group_id, workspace_id, options]))

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Add a tag to the AKS Cluster Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ba4d615c49692c85ebd809eeed9c003424add70c06d72d333f12609d395ef345)
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
            type_hints = typing.get_type_hints(_typecheckingstub__4d2b71e9afe17e71358af1e7947ca82bc7c1bb76d7fe786ea9e2e4319d92cbe3)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified Returns the most recent stable version as the default.'''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="removeTag")
    def remove_tag(self, key: builtins.str) -> None:
        '''Remove a tag from the AKS Cluster Note: This modifies the construct props but requires a new deployment to take effect.

        :param key: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26bff6dd6a3426004dc9c10d17b9417c494437331cf5c06a3da02b0d0fcf8bad)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
        return typing.cast(None, jsii.invoke(self, "removeTag", [key]))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Indicates that this resource requires a location.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for AKS Clusters.'''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

    @builtins.property
    @jsii.member(jsii_name="currentKubernetesVersion")
    def current_kubernetes_version(self) -> builtins.str:
        '''Get the current Kubernetes version running on the cluster.'''
        return typing.cast(builtins.str, jsii.get(self, "currentKubernetesVersion"))

    @builtins.property
    @jsii.member(jsii_name="fqdn")
    def fqdn(self) -> builtins.str:
        '''Get the FQDN of the cluster.'''
        return typing.cast(builtins.str, jsii.get(self, "fqdn"))

    @builtins.property
    @jsii.member(jsii_name="fqdnOutput")
    def fqdn_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "fqdnOutput"))

    @builtins.property
    @jsii.member(jsii_name="idOutput")
    def id_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "idOutput"))

    @builtins.property
    @jsii.member(jsii_name="kubeConfig")
    def kube_config(self) -> builtins.str:
        '''Get the Kubernetes configuration for the cluster.

        This retrieves the cluster admin credentials using an azapi_resource_action.
        The kubeConfig is base64 encoded and contains the full kubectl configuration.
        '''
        return typing.cast(builtins.str, jsii.get(self, "kubeConfig"))

    @builtins.property
    @jsii.member(jsii_name="locationOutput")
    def location_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "locationOutput"))

    @builtins.property
    @jsii.member(jsii_name="nameOutput")
    def name_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "nameOutput"))

    @builtins.property
    @jsii.member(jsii_name="nodeResourceGroupName")
    def node_resource_group_name(self) -> builtins.str:
        '''Get the node resource group name.'''
        return typing.cast(builtins.str, jsii.get(self, "nodeResourceGroupName"))

    @builtins.property
    @jsii.member(jsii_name="privateFqdn")
    def private_fqdn(self) -> builtins.str:
        '''Get the private FQDN of the cluster (if private cluster is enabled).'''
        return typing.cast(builtins.str, jsii.get(self, "privateFqdn"))

    @builtins.property
    @jsii.member(jsii_name="props")
    def props(self) -> "AksClusterProps":
        '''The input properties for this AKS Cluster instance.'''
        return typing.cast("AksClusterProps", jsii.get(self, "props"))

    @builtins.property
    @jsii.member(jsii_name="tagsOutput")
    def tags_output(self) -> _cdktf_9a9027ec.TerraformOutput:
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "tagsOutput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterAadProfile",
    jsii_struct_bases=[],
    name_mapping={
        "admin_group_object_i_ds": "adminGroupObjectIDs",
        "client_app_id": "clientAppID",
        "enable_azure_rbac": "enableAzureRBAC",
        "managed": "managed",
        "server_app_id": "serverAppID",
        "server_app_secret": "serverAppSecret",
        "tenant_id": "tenantID",
    },
)
class AksClusterAadProfile:
    def __init__(
        self,
        *,
        admin_group_object_i_ds: typing.Optional[typing.Sequence[builtins.str]] = None,
        client_app_id: typing.Optional[builtins.str] = None,
        enable_azure_rbac: typing.Optional[builtins.bool] = None,
        managed: typing.Optional[builtins.bool] = None,
        server_app_id: typing.Optional[builtins.str] = None,
        server_app_secret: typing.Optional[builtins.str] = None,
        tenant_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''AAD (Azure Active Directory) profile.

        :param admin_group_object_i_ds: 
        :param client_app_id: 
        :param enable_azure_rbac: 
        :param managed: 
        :param server_app_id: 
        :param server_app_secret: 
        :param tenant_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bdcbdf8e40c590e406a17d41599b96e365936e2e2fda1dfc8b8bc1f0e631f849)
            check_type(argname="argument admin_group_object_i_ds", value=admin_group_object_i_ds, expected_type=type_hints["admin_group_object_i_ds"])
            check_type(argname="argument client_app_id", value=client_app_id, expected_type=type_hints["client_app_id"])
            check_type(argname="argument enable_azure_rbac", value=enable_azure_rbac, expected_type=type_hints["enable_azure_rbac"])
            check_type(argname="argument managed", value=managed, expected_type=type_hints["managed"])
            check_type(argname="argument server_app_id", value=server_app_id, expected_type=type_hints["server_app_id"])
            check_type(argname="argument server_app_secret", value=server_app_secret, expected_type=type_hints["server_app_secret"])
            check_type(argname="argument tenant_id", value=tenant_id, expected_type=type_hints["tenant_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if admin_group_object_i_ds is not None:
            self._values["admin_group_object_i_ds"] = admin_group_object_i_ds
        if client_app_id is not None:
            self._values["client_app_id"] = client_app_id
        if enable_azure_rbac is not None:
            self._values["enable_azure_rbac"] = enable_azure_rbac
        if managed is not None:
            self._values["managed"] = managed
        if server_app_id is not None:
            self._values["server_app_id"] = server_app_id
        if server_app_secret is not None:
            self._values["server_app_secret"] = server_app_secret
        if tenant_id is not None:
            self._values["tenant_id"] = tenant_id

    @builtins.property
    def admin_group_object_i_ds(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("admin_group_object_i_ds")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def client_app_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("client_app_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_azure_rbac(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_azure_rbac")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def managed(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("managed")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def server_app_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("server_app_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def server_app_secret(self) -> typing.Optional[builtins.str]:
        result = self._values.get("server_app_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tenant_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("tenant_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterAadProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterAddonProfile",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled", "config": "config"},
)
class AksClusterAddonProfile:
    def __init__(
        self,
        *,
        enabled: builtins.bool,
        config: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Individual addon profile.

        :param enabled: 
        :param config: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1b8acfa20a2d86195ce86c0dddb47aefc714060f974c49527be77ba3d7bffbf2)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument config", value=config, expected_type=type_hints["config"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "enabled": enabled,
        }
        if config is not None:
            self._values["config"] = config

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def config(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("config")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterAddonProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterAgentPoolProfile",
    jsii_struct_bases=[],
    name_mapping={
        "name": "name",
        "vm_size": "vmSize",
        "availability_zones": "availabilityZones",
        "count": "count",
        "enable_auto_scaling": "enableAutoScaling",
        "enable_encryption_at_host": "enableEncryptionAtHost",
        "enable_fips": "enableFIPS",
        "enable_node_public_ip": "enableNodePublicIP",
        "enable_ultra_ssd": "enableUltraSSD",
        "kubelet_config": "kubeletConfig",
        "linux_os_config": "linuxOSConfig",
        "max_count": "maxCount",
        "max_pods": "maxPods",
        "min_count": "minCount",
        "mode": "mode",
        "node_labels": "nodeLabels",
        "node_public_ip_prefix_id": "nodePublicIPPrefixID",
        "node_taints": "nodeTaints",
        "os_disk_size_gb": "osDiskSizeGB",
        "os_disk_type": "osDiskType",
        "os_type": "osType",
        "pod_subnet_id": "podSubnetID",
        "scale_set_eviction_policy": "scaleSetEvictionPolicy",
        "scale_set_priority": "scaleSetPriority",
        "spot_max_price": "spotMaxPrice",
        "type": "type",
        "vnet_subnet_id": "vnetSubnetID",
    },
)
class AksClusterAgentPoolProfile:
    def __init__(
        self,
        *,
        name: builtins.str,
        vm_size: builtins.str,
        availability_zones: typing.Optional[typing.Sequence[builtins.str]] = None,
        count: typing.Optional[jsii.Number] = None,
        enable_auto_scaling: typing.Optional[builtins.bool] = None,
        enable_encryption_at_host: typing.Optional[builtins.bool] = None,
        enable_fips: typing.Optional[builtins.bool] = None,
        enable_node_public_ip: typing.Optional[builtins.bool] = None,
        enable_ultra_ssd: typing.Optional[builtins.bool] = None,
        kubelet_config: typing.Optional[typing.Union["AksClusterKubeletConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        linux_os_config: typing.Optional[typing.Union["AksClusterLinuxOSConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        max_count: typing.Optional[jsii.Number] = None,
        max_pods: typing.Optional[jsii.Number] = None,
        min_count: typing.Optional[jsii.Number] = None,
        mode: typing.Optional[builtins.str] = None,
        node_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        node_public_ip_prefix_id: typing.Optional[builtins.str] = None,
        node_taints: typing.Optional[typing.Sequence[builtins.str]] = None,
        os_disk_size_gb: typing.Optional[jsii.Number] = None,
        os_disk_type: typing.Optional[builtins.str] = None,
        os_type: typing.Optional[builtins.str] = None,
        pod_subnet_id: typing.Optional[builtins.str] = None,
        scale_set_eviction_policy: typing.Optional[builtins.str] = None,
        scale_set_priority: typing.Optional[builtins.str] = None,
        spot_max_price: typing.Optional[jsii.Number] = None,
        type: typing.Optional[builtins.str] = None,
        vnet_subnet_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Agent pool profile for AKS node pools.

        :param name: 
        :param vm_size: 
        :param availability_zones: 
        :param count: 
        :param enable_auto_scaling: 
        :param enable_encryption_at_host: 
        :param enable_fips: 
        :param enable_node_public_ip: 
        :param enable_ultra_ssd: 
        :param kubelet_config: 
        :param linux_os_config: 
        :param max_count: 
        :param max_pods: 
        :param min_count: 
        :param mode: 
        :param node_labels: 
        :param node_public_ip_prefix_id: 
        :param node_taints: 
        :param os_disk_size_gb: 
        :param os_disk_type: 
        :param os_type: 
        :param pod_subnet_id: 
        :param scale_set_eviction_policy: 
        :param scale_set_priority: 
        :param spot_max_price: 
        :param type: 
        :param vnet_subnet_id: 
        '''
        if isinstance(kubelet_config, dict):
            kubelet_config = AksClusterKubeletConfig(**kubelet_config)
        if isinstance(linux_os_config, dict):
            linux_os_config = AksClusterLinuxOSConfig(**linux_os_config)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5a63ac30d56de20d2eb235afe483c75902391cde9814867a631d6ac5ac306d87)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument vm_size", value=vm_size, expected_type=type_hints["vm_size"])
            check_type(argname="argument availability_zones", value=availability_zones, expected_type=type_hints["availability_zones"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument enable_auto_scaling", value=enable_auto_scaling, expected_type=type_hints["enable_auto_scaling"])
            check_type(argname="argument enable_encryption_at_host", value=enable_encryption_at_host, expected_type=type_hints["enable_encryption_at_host"])
            check_type(argname="argument enable_fips", value=enable_fips, expected_type=type_hints["enable_fips"])
            check_type(argname="argument enable_node_public_ip", value=enable_node_public_ip, expected_type=type_hints["enable_node_public_ip"])
            check_type(argname="argument enable_ultra_ssd", value=enable_ultra_ssd, expected_type=type_hints["enable_ultra_ssd"])
            check_type(argname="argument kubelet_config", value=kubelet_config, expected_type=type_hints["kubelet_config"])
            check_type(argname="argument linux_os_config", value=linux_os_config, expected_type=type_hints["linux_os_config"])
            check_type(argname="argument max_count", value=max_count, expected_type=type_hints["max_count"])
            check_type(argname="argument max_pods", value=max_pods, expected_type=type_hints["max_pods"])
            check_type(argname="argument min_count", value=min_count, expected_type=type_hints["min_count"])
            check_type(argname="argument mode", value=mode, expected_type=type_hints["mode"])
            check_type(argname="argument node_labels", value=node_labels, expected_type=type_hints["node_labels"])
            check_type(argname="argument node_public_ip_prefix_id", value=node_public_ip_prefix_id, expected_type=type_hints["node_public_ip_prefix_id"])
            check_type(argname="argument node_taints", value=node_taints, expected_type=type_hints["node_taints"])
            check_type(argname="argument os_disk_size_gb", value=os_disk_size_gb, expected_type=type_hints["os_disk_size_gb"])
            check_type(argname="argument os_disk_type", value=os_disk_type, expected_type=type_hints["os_disk_type"])
            check_type(argname="argument os_type", value=os_type, expected_type=type_hints["os_type"])
            check_type(argname="argument pod_subnet_id", value=pod_subnet_id, expected_type=type_hints["pod_subnet_id"])
            check_type(argname="argument scale_set_eviction_policy", value=scale_set_eviction_policy, expected_type=type_hints["scale_set_eviction_policy"])
            check_type(argname="argument scale_set_priority", value=scale_set_priority, expected_type=type_hints["scale_set_priority"])
            check_type(argname="argument spot_max_price", value=spot_max_price, expected_type=type_hints["spot_max_price"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument vnet_subnet_id", value=vnet_subnet_id, expected_type=type_hints["vnet_subnet_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "name": name,
            "vm_size": vm_size,
        }
        if availability_zones is not None:
            self._values["availability_zones"] = availability_zones
        if count is not None:
            self._values["count"] = count
        if enable_auto_scaling is not None:
            self._values["enable_auto_scaling"] = enable_auto_scaling
        if enable_encryption_at_host is not None:
            self._values["enable_encryption_at_host"] = enable_encryption_at_host
        if enable_fips is not None:
            self._values["enable_fips"] = enable_fips
        if enable_node_public_ip is not None:
            self._values["enable_node_public_ip"] = enable_node_public_ip
        if enable_ultra_ssd is not None:
            self._values["enable_ultra_ssd"] = enable_ultra_ssd
        if kubelet_config is not None:
            self._values["kubelet_config"] = kubelet_config
        if linux_os_config is not None:
            self._values["linux_os_config"] = linux_os_config
        if max_count is not None:
            self._values["max_count"] = max_count
        if max_pods is not None:
            self._values["max_pods"] = max_pods
        if min_count is not None:
            self._values["min_count"] = min_count
        if mode is not None:
            self._values["mode"] = mode
        if node_labels is not None:
            self._values["node_labels"] = node_labels
        if node_public_ip_prefix_id is not None:
            self._values["node_public_ip_prefix_id"] = node_public_ip_prefix_id
        if node_taints is not None:
            self._values["node_taints"] = node_taints
        if os_disk_size_gb is not None:
            self._values["os_disk_size_gb"] = os_disk_size_gb
        if os_disk_type is not None:
            self._values["os_disk_type"] = os_disk_type
        if os_type is not None:
            self._values["os_type"] = os_type
        if pod_subnet_id is not None:
            self._values["pod_subnet_id"] = pod_subnet_id
        if scale_set_eviction_policy is not None:
            self._values["scale_set_eviction_policy"] = scale_set_eviction_policy
        if scale_set_priority is not None:
            self._values["scale_set_priority"] = scale_set_priority
        if spot_max_price is not None:
            self._values["spot_max_price"] = spot_max_price
        if type is not None:
            self._values["type"] = type
        if vnet_subnet_id is not None:
            self._values["vnet_subnet_id"] = vnet_subnet_id

    @builtins.property
    def name(self) -> builtins.str:
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def vm_size(self) -> builtins.str:
        result = self._values.get("vm_size")
        assert result is not None, "Required property 'vm_size' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def availability_zones(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("availability_zones")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def enable_auto_scaling(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_auto_scaling")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_encryption_at_host(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_encryption_at_host")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_fips(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_fips")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_node_public_ip(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_node_public_ip")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_ultra_ssd(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_ultra_ssd")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def kubelet_config(self) -> typing.Optional["AksClusterKubeletConfig"]:
        result = self._values.get("kubelet_config")
        return typing.cast(typing.Optional["AksClusterKubeletConfig"], result)

    @builtins.property
    def linux_os_config(self) -> typing.Optional["AksClusterLinuxOSConfig"]:
        result = self._values.get("linux_os_config")
        return typing.cast(typing.Optional["AksClusterLinuxOSConfig"], result)

    @builtins.property
    def max_count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("max_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_pods(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("max_pods")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def min_count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("min_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def node_labels(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("node_labels")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def node_public_ip_prefix_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("node_public_ip_prefix_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def node_taints(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("node_taints")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def os_disk_size_gb(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("os_disk_size_gb")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def os_disk_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("os_disk_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def os_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("os_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pod_subnet_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("pod_subnet_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_set_eviction_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_set_eviction_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_set_priority(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_set_priority")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def spot_max_price(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("spot_max_price")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def vnet_subnet_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("vnet_subnet_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterAgentPoolProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterApiServerAccessProfile",
    jsii_struct_bases=[],
    name_mapping={
        "authorized_ip_ranges": "authorizedIPRanges",
        "disable_run_command": "disableRunCommand",
        "enable_private_cluster": "enablePrivateCluster",
        "enable_private_cluster_public_fqdn": "enablePrivateClusterPublicFQDN",
        "enable_vnet_integration": "enableVnetIntegration",
        "private_dns_zone": "privateDNSZone",
        "subnet_id": "subnetId",
    },
)
class AksClusterApiServerAccessProfile:
    def __init__(
        self,
        *,
        authorized_ip_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
        disable_run_command: typing.Optional[builtins.bool] = None,
        enable_private_cluster: typing.Optional[builtins.bool] = None,
        enable_private_cluster_public_fqdn: typing.Optional[builtins.bool] = None,
        enable_vnet_integration: typing.Optional[builtins.bool] = None,
        private_dns_zone: typing.Optional[builtins.str] = None,
        subnet_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''API server access profile.

        :param authorized_ip_ranges: 
        :param disable_run_command: 
        :param enable_private_cluster: 
        :param enable_private_cluster_public_fqdn: 
        :param enable_vnet_integration: 
        :param private_dns_zone: 
        :param subnet_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__85d2b0bd7162a5ea2d58f2fc9e22085f011a515adaa110f4b1fbef38db530190)
            check_type(argname="argument authorized_ip_ranges", value=authorized_ip_ranges, expected_type=type_hints["authorized_ip_ranges"])
            check_type(argname="argument disable_run_command", value=disable_run_command, expected_type=type_hints["disable_run_command"])
            check_type(argname="argument enable_private_cluster", value=enable_private_cluster, expected_type=type_hints["enable_private_cluster"])
            check_type(argname="argument enable_private_cluster_public_fqdn", value=enable_private_cluster_public_fqdn, expected_type=type_hints["enable_private_cluster_public_fqdn"])
            check_type(argname="argument enable_vnet_integration", value=enable_vnet_integration, expected_type=type_hints["enable_vnet_integration"])
            check_type(argname="argument private_dns_zone", value=private_dns_zone, expected_type=type_hints["private_dns_zone"])
            check_type(argname="argument subnet_id", value=subnet_id, expected_type=type_hints["subnet_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if authorized_ip_ranges is not None:
            self._values["authorized_ip_ranges"] = authorized_ip_ranges
        if disable_run_command is not None:
            self._values["disable_run_command"] = disable_run_command
        if enable_private_cluster is not None:
            self._values["enable_private_cluster"] = enable_private_cluster
        if enable_private_cluster_public_fqdn is not None:
            self._values["enable_private_cluster_public_fqdn"] = enable_private_cluster_public_fqdn
        if enable_vnet_integration is not None:
            self._values["enable_vnet_integration"] = enable_vnet_integration
        if private_dns_zone is not None:
            self._values["private_dns_zone"] = private_dns_zone
        if subnet_id is not None:
            self._values["subnet_id"] = subnet_id

    @builtins.property
    def authorized_ip_ranges(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("authorized_ip_ranges")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def disable_run_command(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("disable_run_command")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_private_cluster(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_private_cluster")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_private_cluster_public_fqdn(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_private_cluster_public_fqdn")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_vnet_integration(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_vnet_integration")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def private_dns_zone(self) -> typing.Optional[builtins.str]:
        result = self._values.get("private_dns_zone")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def subnet_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("subnet_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterApiServerAccessProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterAutoScalerProfile",
    jsii_struct_bases=[],
    name_mapping={
        "balance_similar_node_groups": "balanceSimilarNodeGroups",
        "expander": "expander",
        "max_empty_bulk_delete": "maxEmptyBulkDelete",
        "max_graceful_termination_sec": "maxGracefulTerminationSec",
        "max_node_provision_time": "maxNodeProvisionTime",
        "max_total_unready_percentage": "maxTotalUnreadyPercentage",
        "new_pod_scale_up_delay": "newPodScaleUpDelay",
        "ok_total_unready_count": "okTotalUnreadyCount",
        "scale_down_delay_after_add": "scaleDownDelayAfterAdd",
        "scale_down_delay_after_delete": "scaleDownDelayAfterDelete",
        "scale_down_delay_after_failure": "scaleDownDelayAfterFailure",
        "scale_down_unneeded_time": "scaleDownUnneededTime",
        "scale_down_unready_time": "scaleDownUnreadyTime",
        "scale_down_utilization_threshold": "scaleDownUtilizationThreshold",
        "scan_interval": "scanInterval",
        "skip_nodes_with_local_storage": "skipNodesWithLocalStorage",
        "skip_nodes_with_system_pods": "skipNodesWithSystemPods",
    },
)
class AksClusterAutoScalerProfile:
    def __init__(
        self,
        *,
        balance_similar_node_groups: typing.Optional[builtins.str] = None,
        expander: typing.Optional[builtins.str] = None,
        max_empty_bulk_delete: typing.Optional[builtins.str] = None,
        max_graceful_termination_sec: typing.Optional[builtins.str] = None,
        max_node_provision_time: typing.Optional[builtins.str] = None,
        max_total_unready_percentage: typing.Optional[builtins.str] = None,
        new_pod_scale_up_delay: typing.Optional[builtins.str] = None,
        ok_total_unready_count: typing.Optional[builtins.str] = None,
        scale_down_delay_after_add: typing.Optional[builtins.str] = None,
        scale_down_delay_after_delete: typing.Optional[builtins.str] = None,
        scale_down_delay_after_failure: typing.Optional[builtins.str] = None,
        scale_down_unneeded_time: typing.Optional[builtins.str] = None,
        scale_down_unready_time: typing.Optional[builtins.str] = None,
        scale_down_utilization_threshold: typing.Optional[builtins.str] = None,
        scan_interval: typing.Optional[builtins.str] = None,
        skip_nodes_with_local_storage: typing.Optional[builtins.str] = None,
        skip_nodes_with_system_pods: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Auto-scaler profile.

        :param balance_similar_node_groups: 
        :param expander: 
        :param max_empty_bulk_delete: 
        :param max_graceful_termination_sec: 
        :param max_node_provision_time: 
        :param max_total_unready_percentage: 
        :param new_pod_scale_up_delay: 
        :param ok_total_unready_count: 
        :param scale_down_delay_after_add: 
        :param scale_down_delay_after_delete: 
        :param scale_down_delay_after_failure: 
        :param scale_down_unneeded_time: 
        :param scale_down_unready_time: 
        :param scale_down_utilization_threshold: 
        :param scan_interval: 
        :param skip_nodes_with_local_storage: 
        :param skip_nodes_with_system_pods: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5f28492551fcbf758be78cfd663d2e5ae185c8437ccaba11c7c849be6cb10315)
            check_type(argname="argument balance_similar_node_groups", value=balance_similar_node_groups, expected_type=type_hints["balance_similar_node_groups"])
            check_type(argname="argument expander", value=expander, expected_type=type_hints["expander"])
            check_type(argname="argument max_empty_bulk_delete", value=max_empty_bulk_delete, expected_type=type_hints["max_empty_bulk_delete"])
            check_type(argname="argument max_graceful_termination_sec", value=max_graceful_termination_sec, expected_type=type_hints["max_graceful_termination_sec"])
            check_type(argname="argument max_node_provision_time", value=max_node_provision_time, expected_type=type_hints["max_node_provision_time"])
            check_type(argname="argument max_total_unready_percentage", value=max_total_unready_percentage, expected_type=type_hints["max_total_unready_percentage"])
            check_type(argname="argument new_pod_scale_up_delay", value=new_pod_scale_up_delay, expected_type=type_hints["new_pod_scale_up_delay"])
            check_type(argname="argument ok_total_unready_count", value=ok_total_unready_count, expected_type=type_hints["ok_total_unready_count"])
            check_type(argname="argument scale_down_delay_after_add", value=scale_down_delay_after_add, expected_type=type_hints["scale_down_delay_after_add"])
            check_type(argname="argument scale_down_delay_after_delete", value=scale_down_delay_after_delete, expected_type=type_hints["scale_down_delay_after_delete"])
            check_type(argname="argument scale_down_delay_after_failure", value=scale_down_delay_after_failure, expected_type=type_hints["scale_down_delay_after_failure"])
            check_type(argname="argument scale_down_unneeded_time", value=scale_down_unneeded_time, expected_type=type_hints["scale_down_unneeded_time"])
            check_type(argname="argument scale_down_unready_time", value=scale_down_unready_time, expected_type=type_hints["scale_down_unready_time"])
            check_type(argname="argument scale_down_utilization_threshold", value=scale_down_utilization_threshold, expected_type=type_hints["scale_down_utilization_threshold"])
            check_type(argname="argument scan_interval", value=scan_interval, expected_type=type_hints["scan_interval"])
            check_type(argname="argument skip_nodes_with_local_storage", value=skip_nodes_with_local_storage, expected_type=type_hints["skip_nodes_with_local_storage"])
            check_type(argname="argument skip_nodes_with_system_pods", value=skip_nodes_with_system_pods, expected_type=type_hints["skip_nodes_with_system_pods"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if balance_similar_node_groups is not None:
            self._values["balance_similar_node_groups"] = balance_similar_node_groups
        if expander is not None:
            self._values["expander"] = expander
        if max_empty_bulk_delete is not None:
            self._values["max_empty_bulk_delete"] = max_empty_bulk_delete
        if max_graceful_termination_sec is not None:
            self._values["max_graceful_termination_sec"] = max_graceful_termination_sec
        if max_node_provision_time is not None:
            self._values["max_node_provision_time"] = max_node_provision_time
        if max_total_unready_percentage is not None:
            self._values["max_total_unready_percentage"] = max_total_unready_percentage
        if new_pod_scale_up_delay is not None:
            self._values["new_pod_scale_up_delay"] = new_pod_scale_up_delay
        if ok_total_unready_count is not None:
            self._values["ok_total_unready_count"] = ok_total_unready_count
        if scale_down_delay_after_add is not None:
            self._values["scale_down_delay_after_add"] = scale_down_delay_after_add
        if scale_down_delay_after_delete is not None:
            self._values["scale_down_delay_after_delete"] = scale_down_delay_after_delete
        if scale_down_delay_after_failure is not None:
            self._values["scale_down_delay_after_failure"] = scale_down_delay_after_failure
        if scale_down_unneeded_time is not None:
            self._values["scale_down_unneeded_time"] = scale_down_unneeded_time
        if scale_down_unready_time is not None:
            self._values["scale_down_unready_time"] = scale_down_unready_time
        if scale_down_utilization_threshold is not None:
            self._values["scale_down_utilization_threshold"] = scale_down_utilization_threshold
        if scan_interval is not None:
            self._values["scan_interval"] = scan_interval
        if skip_nodes_with_local_storage is not None:
            self._values["skip_nodes_with_local_storage"] = skip_nodes_with_local_storage
        if skip_nodes_with_system_pods is not None:
            self._values["skip_nodes_with_system_pods"] = skip_nodes_with_system_pods

    @builtins.property
    def balance_similar_node_groups(self) -> typing.Optional[builtins.str]:
        result = self._values.get("balance_similar_node_groups")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def expander(self) -> typing.Optional[builtins.str]:
        result = self._values.get("expander")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_empty_bulk_delete(self) -> typing.Optional[builtins.str]:
        result = self._values.get("max_empty_bulk_delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_graceful_termination_sec(self) -> typing.Optional[builtins.str]:
        result = self._values.get("max_graceful_termination_sec")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_node_provision_time(self) -> typing.Optional[builtins.str]:
        result = self._values.get("max_node_provision_time")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_total_unready_percentage(self) -> typing.Optional[builtins.str]:
        result = self._values.get("max_total_unready_percentage")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def new_pod_scale_up_delay(self) -> typing.Optional[builtins.str]:
        result = self._values.get("new_pod_scale_up_delay")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ok_total_unready_count(self) -> typing.Optional[builtins.str]:
        result = self._values.get("ok_total_unready_count")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_down_delay_after_add(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_down_delay_after_add")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_down_delay_after_delete(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_down_delay_after_delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_down_delay_after_failure(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_down_delay_after_failure")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_down_unneeded_time(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_down_unneeded_time")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_down_unready_time(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_down_unready_time")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scale_down_utilization_threshold(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scale_down_utilization_threshold")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def scan_interval(self) -> typing.Optional[builtins.str]:
        result = self._values.get("scan_interval")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_nodes_with_local_storage(self) -> typing.Optional[builtins.str]:
        result = self._values.get("skip_nodes_with_local_storage")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_nodes_with_system_pods(self) -> typing.Optional[builtins.str]:
        result = self._values.get("skip_nodes_with_system_pods")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterAutoScalerProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterAzureKeyVaultKms",
    jsii_struct_bases=[],
    name_mapping={
        "enabled": "enabled",
        "key_id": "keyId",
        "key_vault_network_access": "keyVaultNetworkAccess",
        "key_vault_resource_id": "keyVaultResourceId",
    },
)
class AksClusterAzureKeyVaultKms:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        key_id: typing.Optional[builtins.str] = None,
        key_vault_network_access: typing.Optional[builtins.str] = None,
        key_vault_resource_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Azure Key Vault KMS configuration.

        :param enabled: 
        :param key_id: 
        :param key_vault_network_access: 
        :param key_vault_resource_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__da543fdbfd1a1bdbb7da17f521dc3eae8d77779621c27db8017f62820523ee7b)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument key_id", value=key_id, expected_type=type_hints["key_id"])
            check_type(argname="argument key_vault_network_access", value=key_vault_network_access, expected_type=type_hints["key_vault_network_access"])
            check_type(argname="argument key_vault_resource_id", value=key_vault_resource_id, expected_type=type_hints["key_vault_resource_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if key_id is not None:
            self._values["key_id"] = key_id
        if key_vault_network_access is not None:
            self._values["key_vault_network_access"] = key_vault_network_access
        if key_vault_resource_id is not None:
            self._values["key_vault_resource_id"] = key_vault_resource_id

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def key_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("key_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def key_vault_network_access(self) -> typing.Optional[builtins.str]:
        result = self._values.get("key_vault_network_access")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def key_vault_resource_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("key_vault_resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterAzureKeyVaultKms(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterBlobCSIDriver",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class AksClusterBlobCSIDriver:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''Blob CSI driver.

        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed38fbd794526e83f9f2b3e7fb1ba17008dbed0bc5754f6e89775ed3dfe0e853)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterBlobCSIDriver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterBody",
    jsii_struct_bases=[],
    name_mapping={
        "location": "location",
        "properties": "properties",
        "identity": "identity",
        "sku": "sku",
        "tags": "tags",
    },
)
class AksClusterBody:
    def __init__(
        self,
        *,
        location: builtins.str,
        properties: typing.Union["AksClusterBodyProperties", typing.Dict[builtins.str, typing.Any]],
        identity: typing.Optional[typing.Union["AksClusterIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
        sku: typing.Optional[typing.Union["AksClusterSku", typing.Dict[builtins.str, typing.Any]]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''The resource body interface for Azure AKS API calls.

        :param location: 
        :param properties: 
        :param identity: 
        :param sku: 
        :param tags: 
        '''
        if isinstance(properties, dict):
            properties = AksClusterBodyProperties(**properties)
        if isinstance(identity, dict):
            identity = AksClusterIdentity(**identity)
        if isinstance(sku, dict):
            sku = AksClusterSku(**sku)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__baf743af72de779ee5955acf7b022ed77e8b9ba636c6421f6eef46740525703c)
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "location": location,
            "properties": properties,
        }
        if identity is not None:
            self._values["identity"] = identity
        if sku is not None:
            self._values["sku"] = sku
        if tags is not None:
            self._values["tags"] = tags

    @builtins.property
    def location(self) -> builtins.str:
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def properties(self) -> "AksClusterBodyProperties":
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast("AksClusterBodyProperties", result)

    @builtins.property
    def identity(self) -> typing.Optional["AksClusterIdentity"]:
        result = self._values.get("identity")
        return typing.cast(typing.Optional["AksClusterIdentity"], result)

    @builtins.property
    def sku(self) -> typing.Optional["AksClusterSku"]:
        result = self._values.get("sku")
        return typing.cast(typing.Optional["AksClusterSku"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterBody(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterBodyProperties",
    jsii_struct_bases=[],
    name_mapping={
        "agent_pool_profiles": "agentPoolProfiles",
        "dns_prefix": "dnsPrefix",
        "aad_profile": "aadProfile",
        "addon_profiles": "addonProfiles",
        "api_server_access_profile": "apiServerAccessProfile",
        "auto_scaler_profile": "autoScalerProfile",
        "disable_local_accounts": "disableLocalAccounts",
        "disk_encryption_set_id": "diskEncryptionSetID",
        "enable_rbac": "enableRBAC",
        "fqdn": "fqdn",
        "http_proxy_config": "httpProxyConfig",
        "kubernetes_version": "kubernetesVersion",
        "linux_profile": "linuxProfile",
        "network_profile": "networkProfile",
        "node_resource_group": "nodeResourceGroup",
        "oidc_issuer_profile": "oidcIssuerProfile",
        "private_fqdn": "privateFQDN",
        "public_network_access": "publicNetworkAccess",
        "security_profile": "securityProfile",
        "service_principal_profile": "servicePrincipalProfile",
        "storage_profile": "storageProfile",
        "support_plan": "supportPlan",
        "windows_profile": "windowsProfile",
        "workload_auto_scaler_profile": "workloadAutoScalerProfile",
    },
)
class AksClusterBodyProperties:
    def __init__(
        self,
        *,
        agent_pool_profiles: typing.Sequence[typing.Union[AksClusterAgentPoolProfile, typing.Dict[builtins.str, typing.Any]]],
        dns_prefix: builtins.str,
        aad_profile: typing.Optional[typing.Union[AksClusterAadProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        addon_profiles: typing.Optional[typing.Mapping[builtins.str, typing.Union[AksClusterAddonProfile, typing.Dict[builtins.str, typing.Any]]]] = None,
        api_server_access_profile: typing.Optional[typing.Union[AksClusterApiServerAccessProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_scaler_profile: typing.Optional[typing.Union[AksClusterAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        disable_local_accounts: typing.Optional[builtins.bool] = None,
        disk_encryption_set_id: typing.Optional[builtins.str] = None,
        enable_rbac: typing.Optional[builtins.bool] = None,
        fqdn: typing.Optional[builtins.str] = None,
        http_proxy_config: typing.Optional[typing.Union["AksClusterHttpProxyConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        kubernetes_version: typing.Optional[builtins.str] = None,
        linux_profile: typing.Optional[typing.Union["AksClusterLinuxProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        network_profile: typing.Optional[typing.Union["AksClusterNetworkProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        node_resource_group: typing.Optional[builtins.str] = None,
        oidc_issuer_profile: typing.Optional[typing.Union["AksClusterOidcIssuerProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        private_fqdn: typing.Optional[builtins.str] = None,
        public_network_access: typing.Optional[builtins.str] = None,
        security_profile: typing.Optional[typing.Union["AksClusterSecurityProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        service_principal_profile: typing.Optional[typing.Union["AksClusterServicePrincipalProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        storage_profile: typing.Optional[typing.Union["AksClusterStorageProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        support_plan: typing.Optional[builtins.str] = None,
        windows_profile: typing.Optional[typing.Union["AksClusterWindowsProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        workload_auto_scaler_profile: typing.Optional[typing.Union["AksClusterWorkloadAutoScalerProfile", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''AKS Cluster properties for the request body.

        :param agent_pool_profiles: 
        :param dns_prefix: 
        :param aad_profile: 
        :param addon_profiles: 
        :param api_server_access_profile: 
        :param auto_scaler_profile: 
        :param disable_local_accounts: 
        :param disk_encryption_set_id: 
        :param enable_rbac: 
        :param fqdn: 
        :param http_proxy_config: 
        :param kubernetes_version: 
        :param linux_profile: 
        :param network_profile: 
        :param node_resource_group: 
        :param oidc_issuer_profile: 
        :param private_fqdn: 
        :param public_network_access: 
        :param security_profile: 
        :param service_principal_profile: 
        :param storage_profile: 
        :param support_plan: 
        :param windows_profile: 
        :param workload_auto_scaler_profile: 
        '''
        if isinstance(aad_profile, dict):
            aad_profile = AksClusterAadProfile(**aad_profile)
        if isinstance(api_server_access_profile, dict):
            api_server_access_profile = AksClusterApiServerAccessProfile(**api_server_access_profile)
        if isinstance(auto_scaler_profile, dict):
            auto_scaler_profile = AksClusterAutoScalerProfile(**auto_scaler_profile)
        if isinstance(http_proxy_config, dict):
            http_proxy_config = AksClusterHttpProxyConfig(**http_proxy_config)
        if isinstance(linux_profile, dict):
            linux_profile = AksClusterLinuxProfile(**linux_profile)
        if isinstance(network_profile, dict):
            network_profile = AksClusterNetworkProfile(**network_profile)
        if isinstance(oidc_issuer_profile, dict):
            oidc_issuer_profile = AksClusterOidcIssuerProfile(**oidc_issuer_profile)
        if isinstance(security_profile, dict):
            security_profile = AksClusterSecurityProfile(**security_profile)
        if isinstance(service_principal_profile, dict):
            service_principal_profile = AksClusterServicePrincipalProfile(**service_principal_profile)
        if isinstance(storage_profile, dict):
            storage_profile = AksClusterStorageProfile(**storage_profile)
        if isinstance(windows_profile, dict):
            windows_profile = AksClusterWindowsProfile(**windows_profile)
        if isinstance(workload_auto_scaler_profile, dict):
            workload_auto_scaler_profile = AksClusterWorkloadAutoScalerProfile(**workload_auto_scaler_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__806f1127fedc29edc4713bdb6db5e7be4b4355e0a08759a24850d84ca7e16374)
            check_type(argname="argument agent_pool_profiles", value=agent_pool_profiles, expected_type=type_hints["agent_pool_profiles"])
            check_type(argname="argument dns_prefix", value=dns_prefix, expected_type=type_hints["dns_prefix"])
            check_type(argname="argument aad_profile", value=aad_profile, expected_type=type_hints["aad_profile"])
            check_type(argname="argument addon_profiles", value=addon_profiles, expected_type=type_hints["addon_profiles"])
            check_type(argname="argument api_server_access_profile", value=api_server_access_profile, expected_type=type_hints["api_server_access_profile"])
            check_type(argname="argument auto_scaler_profile", value=auto_scaler_profile, expected_type=type_hints["auto_scaler_profile"])
            check_type(argname="argument disable_local_accounts", value=disable_local_accounts, expected_type=type_hints["disable_local_accounts"])
            check_type(argname="argument disk_encryption_set_id", value=disk_encryption_set_id, expected_type=type_hints["disk_encryption_set_id"])
            check_type(argname="argument enable_rbac", value=enable_rbac, expected_type=type_hints["enable_rbac"])
            check_type(argname="argument fqdn", value=fqdn, expected_type=type_hints["fqdn"])
            check_type(argname="argument http_proxy_config", value=http_proxy_config, expected_type=type_hints["http_proxy_config"])
            check_type(argname="argument kubernetes_version", value=kubernetes_version, expected_type=type_hints["kubernetes_version"])
            check_type(argname="argument linux_profile", value=linux_profile, expected_type=type_hints["linux_profile"])
            check_type(argname="argument network_profile", value=network_profile, expected_type=type_hints["network_profile"])
            check_type(argname="argument node_resource_group", value=node_resource_group, expected_type=type_hints["node_resource_group"])
            check_type(argname="argument oidc_issuer_profile", value=oidc_issuer_profile, expected_type=type_hints["oidc_issuer_profile"])
            check_type(argname="argument private_fqdn", value=private_fqdn, expected_type=type_hints["private_fqdn"])
            check_type(argname="argument public_network_access", value=public_network_access, expected_type=type_hints["public_network_access"])
            check_type(argname="argument security_profile", value=security_profile, expected_type=type_hints["security_profile"])
            check_type(argname="argument service_principal_profile", value=service_principal_profile, expected_type=type_hints["service_principal_profile"])
            check_type(argname="argument storage_profile", value=storage_profile, expected_type=type_hints["storage_profile"])
            check_type(argname="argument support_plan", value=support_plan, expected_type=type_hints["support_plan"])
            check_type(argname="argument windows_profile", value=windows_profile, expected_type=type_hints["windows_profile"])
            check_type(argname="argument workload_auto_scaler_profile", value=workload_auto_scaler_profile, expected_type=type_hints["workload_auto_scaler_profile"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "agent_pool_profiles": agent_pool_profiles,
            "dns_prefix": dns_prefix,
        }
        if aad_profile is not None:
            self._values["aad_profile"] = aad_profile
        if addon_profiles is not None:
            self._values["addon_profiles"] = addon_profiles
        if api_server_access_profile is not None:
            self._values["api_server_access_profile"] = api_server_access_profile
        if auto_scaler_profile is not None:
            self._values["auto_scaler_profile"] = auto_scaler_profile
        if disable_local_accounts is not None:
            self._values["disable_local_accounts"] = disable_local_accounts
        if disk_encryption_set_id is not None:
            self._values["disk_encryption_set_id"] = disk_encryption_set_id
        if enable_rbac is not None:
            self._values["enable_rbac"] = enable_rbac
        if fqdn is not None:
            self._values["fqdn"] = fqdn
        if http_proxy_config is not None:
            self._values["http_proxy_config"] = http_proxy_config
        if kubernetes_version is not None:
            self._values["kubernetes_version"] = kubernetes_version
        if linux_profile is not None:
            self._values["linux_profile"] = linux_profile
        if network_profile is not None:
            self._values["network_profile"] = network_profile
        if node_resource_group is not None:
            self._values["node_resource_group"] = node_resource_group
        if oidc_issuer_profile is not None:
            self._values["oidc_issuer_profile"] = oidc_issuer_profile
        if private_fqdn is not None:
            self._values["private_fqdn"] = private_fqdn
        if public_network_access is not None:
            self._values["public_network_access"] = public_network_access
        if security_profile is not None:
            self._values["security_profile"] = security_profile
        if service_principal_profile is not None:
            self._values["service_principal_profile"] = service_principal_profile
        if storage_profile is not None:
            self._values["storage_profile"] = storage_profile
        if support_plan is not None:
            self._values["support_plan"] = support_plan
        if windows_profile is not None:
            self._values["windows_profile"] = windows_profile
        if workload_auto_scaler_profile is not None:
            self._values["workload_auto_scaler_profile"] = workload_auto_scaler_profile

    @builtins.property
    def agent_pool_profiles(self) -> typing.List[AksClusterAgentPoolProfile]:
        result = self._values.get("agent_pool_profiles")
        assert result is not None, "Required property 'agent_pool_profiles' is missing"
        return typing.cast(typing.List[AksClusterAgentPoolProfile], result)

    @builtins.property
    def dns_prefix(self) -> builtins.str:
        result = self._values.get("dns_prefix")
        assert result is not None, "Required property 'dns_prefix' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def aad_profile(self) -> typing.Optional[AksClusterAadProfile]:
        result = self._values.get("aad_profile")
        return typing.cast(typing.Optional[AksClusterAadProfile], result)

    @builtins.property
    def addon_profiles(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, AksClusterAddonProfile]]:
        result = self._values.get("addon_profiles")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, AksClusterAddonProfile]], result)

    @builtins.property
    def api_server_access_profile(
        self,
    ) -> typing.Optional[AksClusterApiServerAccessProfile]:
        result = self._values.get("api_server_access_profile")
        return typing.cast(typing.Optional[AksClusterApiServerAccessProfile], result)

    @builtins.property
    def auto_scaler_profile(self) -> typing.Optional[AksClusterAutoScalerProfile]:
        result = self._values.get("auto_scaler_profile")
        return typing.cast(typing.Optional[AksClusterAutoScalerProfile], result)

    @builtins.property
    def disable_local_accounts(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("disable_local_accounts")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def disk_encryption_set_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("disk_encryption_set_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_rbac(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_rbac")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def fqdn(self) -> typing.Optional[builtins.str]:
        result = self._values.get("fqdn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def http_proxy_config(self) -> typing.Optional["AksClusterHttpProxyConfig"]:
        result = self._values.get("http_proxy_config")
        return typing.cast(typing.Optional["AksClusterHttpProxyConfig"], result)

    @builtins.property
    def kubernetes_version(self) -> typing.Optional[builtins.str]:
        result = self._values.get("kubernetes_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def linux_profile(self) -> typing.Optional["AksClusterLinuxProfile"]:
        result = self._values.get("linux_profile")
        return typing.cast(typing.Optional["AksClusterLinuxProfile"], result)

    @builtins.property
    def network_profile(self) -> typing.Optional["AksClusterNetworkProfile"]:
        result = self._values.get("network_profile")
        return typing.cast(typing.Optional["AksClusterNetworkProfile"], result)

    @builtins.property
    def node_resource_group(self) -> typing.Optional[builtins.str]:
        result = self._values.get("node_resource_group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_issuer_profile(self) -> typing.Optional["AksClusterOidcIssuerProfile"]:
        result = self._values.get("oidc_issuer_profile")
        return typing.cast(typing.Optional["AksClusterOidcIssuerProfile"], result)

    @builtins.property
    def private_fqdn(self) -> typing.Optional[builtins.str]:
        result = self._values.get("private_fqdn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def public_network_access(self) -> typing.Optional[builtins.str]:
        result = self._values.get("public_network_access")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_profile(self) -> typing.Optional["AksClusterSecurityProfile"]:
        result = self._values.get("security_profile")
        return typing.cast(typing.Optional["AksClusterSecurityProfile"], result)

    @builtins.property
    def service_principal_profile(
        self,
    ) -> typing.Optional["AksClusterServicePrincipalProfile"]:
        result = self._values.get("service_principal_profile")
        return typing.cast(typing.Optional["AksClusterServicePrincipalProfile"], result)

    @builtins.property
    def storage_profile(self) -> typing.Optional["AksClusterStorageProfile"]:
        result = self._values.get("storage_profile")
        return typing.cast(typing.Optional["AksClusterStorageProfile"], result)

    @builtins.property
    def support_plan(self) -> typing.Optional[builtins.str]:
        result = self._values.get("support_plan")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def windows_profile(self) -> typing.Optional["AksClusterWindowsProfile"]:
        result = self._values.get("windows_profile")
        return typing.cast(typing.Optional["AksClusterWindowsProfile"], result)

    @builtins.property
    def workload_auto_scaler_profile(
        self,
    ) -> typing.Optional["AksClusterWorkloadAutoScalerProfile"]:
        result = self._values.get("workload_auto_scaler_profile")
        return typing.cast(typing.Optional["AksClusterWorkloadAutoScalerProfile"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterBodyProperties(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterDefenderSecurityMonitoring",
    jsii_struct_bases=[],
    name_mapping={
        "enabled": "enabled",
        "log_analytics_workspace_resource_id": "logAnalyticsWorkspaceResourceId",
    },
)
class AksClusterDefenderSecurityMonitoring:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        log_analytics_workspace_resource_id: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Defender security monitoring.

        :param enabled: 
        :param log_analytics_workspace_resource_id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7a248ddfdc5022e908f5100def54d6d797e4100c8ce486bfd45d29b04ee18f51)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument log_analytics_workspace_resource_id", value=log_analytics_workspace_resource_id, expected_type=type_hints["log_analytics_workspace_resource_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if log_analytics_workspace_resource_id is not None:
            self._values["log_analytics_workspace_resource_id"] = log_analytics_workspace_resource_id

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_analytics_workspace_resource_id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("log_analytics_workspace_resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterDefenderSecurityMonitoring(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterDiskCSIDriver",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled", "version": "version"},
)
class AksClusterDiskCSIDriver:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        version: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Disk CSI driver.

        :param enabled: 
        :param version: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__62513b02011a704d7b04fbabaf5987134079273661e24d74574b80aaa2461368)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if version is not None:
            self._values["version"] = version

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def version(self) -> typing.Optional[builtins.str]:
        result = self._values.get("version")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterDiskCSIDriver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterEffectiveOutboundIP",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class AksClusterEffectiveOutboundIP:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Effective outbound IP.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f1c105913fa15501b1a02038d0fc7f3f6918bdb73da1284f625eab123171d1af)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterEffectiveOutboundIP(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterFileCSIDriver",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class AksClusterFileCSIDriver:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''File CSI driver.

        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee47928b98ee4db355f8bfec9d2449dc2c1cdba415a5bd80da648590b009d236)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterFileCSIDriver(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterGmsaProfile",
    jsii_struct_bases=[],
    name_mapping={
        "dns_server": "dnsServer",
        "enabled": "enabled",
        "root_domain_name": "rootDomainName",
    },
)
class AksClusterGmsaProfile:
    def __init__(
        self,
        *,
        dns_server: typing.Optional[builtins.str] = None,
        enabled: typing.Optional[builtins.bool] = None,
        root_domain_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''GMSA profile for Windows.

        :param dns_server: 
        :param enabled: 
        :param root_domain_name: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a03ea030a627e1e6383fdd3bba22dc6c716fc5487479996942ce55d7d266a8db)
            check_type(argname="argument dns_server", value=dns_server, expected_type=type_hints["dns_server"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument root_domain_name", value=root_domain_name, expected_type=type_hints["root_domain_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dns_server is not None:
            self._values["dns_server"] = dns_server
        if enabled is not None:
            self._values["enabled"] = enabled
        if root_domain_name is not None:
            self._values["root_domain_name"] = root_domain_name

    @builtins.property
    def dns_server(self) -> typing.Optional[builtins.str]:
        result = self._values.get("dns_server")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def root_domain_name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("root_domain_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterGmsaProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterHttpProxyConfig",
    jsii_struct_bases=[],
    name_mapping={
        "http_proxy": "httpProxy",
        "https_proxy": "httpsProxy",
        "no_proxy": "noProxy",
        "trusted_ca": "trustedCa",
    },
)
class AksClusterHttpProxyConfig:
    def __init__(
        self,
        *,
        http_proxy: typing.Optional[builtins.str] = None,
        https_proxy: typing.Optional[builtins.str] = None,
        no_proxy: typing.Optional[typing.Sequence[builtins.str]] = None,
        trusted_ca: typing.Optional[builtins.str] = None,
    ) -> None:
        '''HTTP proxy configuration.

        :param http_proxy: 
        :param https_proxy: 
        :param no_proxy: 
        :param trusted_ca: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__94a6f8945b7dffe36c03aa585ef64ee053869dc6d717976f2391bcd72a748eaf)
            check_type(argname="argument http_proxy", value=http_proxy, expected_type=type_hints["http_proxy"])
            check_type(argname="argument https_proxy", value=https_proxy, expected_type=type_hints["https_proxy"])
            check_type(argname="argument no_proxy", value=no_proxy, expected_type=type_hints["no_proxy"])
            check_type(argname="argument trusted_ca", value=trusted_ca, expected_type=type_hints["trusted_ca"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if http_proxy is not None:
            self._values["http_proxy"] = http_proxy
        if https_proxy is not None:
            self._values["https_proxy"] = https_proxy
        if no_proxy is not None:
            self._values["no_proxy"] = no_proxy
        if trusted_ca is not None:
            self._values["trusted_ca"] = trusted_ca

    @builtins.property
    def http_proxy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("http_proxy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def https_proxy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("https_proxy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def no_proxy(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("no_proxy")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def trusted_ca(self) -> typing.Optional[builtins.str]:
        result = self._values.get("trusted_ca")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterHttpProxyConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterIdentity",
    jsii_struct_bases=[],
    name_mapping={
        "type": "type",
        "user_assigned_identities": "userAssignedIdentities",
    },
)
class AksClusterIdentity:
    def __init__(
        self,
        *,
        type: builtins.str,
        user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    ) -> None:
        '''Identity configuration for AKS Cluster.

        :param type: 
        :param user_assigned_identities: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a4b4c4123f350176a104d66cda6a4ce251fcbf6b1cc8d07ee95b83be6e02cde)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument user_assigned_identities", value=user_assigned_identities, expected_type=type_hints["user_assigned_identities"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }
        if user_assigned_identities is not None:
            self._values["user_assigned_identities"] = user_assigned_identities

    @builtins.property
    def type(self) -> builtins.str:
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def user_assigned_identities(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        result = self._values.get("user_assigned_identities")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterImageCleaner",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled", "interval_hours": "intervalHours"},
)
class AksClusterImageCleaner:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        interval_hours: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Image cleaner configuration.

        :param enabled: 
        :param interval_hours: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__415d44f954f0469ae478fc6a3dcc8ca0c2c24a27384828d791256677454b3b88)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument interval_hours", value=interval_hours, expected_type=type_hints["interval_hours"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if interval_hours is not None:
            self._values["interval_hours"] = interval_hours

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def interval_hours(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("interval_hours")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterImageCleaner(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterKeda",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class AksClusterKeda:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''KEDA configuration.

        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__54fa7b2f0ede20ec8771cb8a7b343a0be4604a7aa233da0f10da505fdb7316be)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterKeda(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterKubeletConfig",
    jsii_struct_bases=[],
    name_mapping={
        "allowed_unsafe_sysctls": "allowedUnsafeSysctls",
        "container_log_max_files": "containerLogMaxFiles",
        "container_log_max_size_mb": "containerLogMaxSizeMB",
        "cpu_cfs_quota": "cpuCfsQuota",
        "cpu_cfs_quota_period": "cpuCfsQuotaPeriod",
        "cpu_manager_policy": "cpuManagerPolicy",
        "fail_swap_on": "failSwapOn",
        "image_gc_high_threshold": "imageGcHighThreshold",
        "image_gc_low_threshold": "imageGcLowThreshold",
        "pod_max_pids": "podMaxPids",
        "topology_manager_policy": "topologyManagerPolicy",
    },
)
class AksClusterKubeletConfig:
    def __init__(
        self,
        *,
        allowed_unsafe_sysctls: typing.Optional[typing.Sequence[builtins.str]] = None,
        container_log_max_files: typing.Optional[jsii.Number] = None,
        container_log_max_size_mb: typing.Optional[jsii.Number] = None,
        cpu_cfs_quota: typing.Optional[builtins.bool] = None,
        cpu_cfs_quota_period: typing.Optional[builtins.str] = None,
        cpu_manager_policy: typing.Optional[builtins.str] = None,
        fail_swap_on: typing.Optional[builtins.bool] = None,
        image_gc_high_threshold: typing.Optional[jsii.Number] = None,
        image_gc_low_threshold: typing.Optional[jsii.Number] = None,
        pod_max_pids: typing.Optional[jsii.Number] = None,
        topology_manager_policy: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Kubelet configuration.

        :param allowed_unsafe_sysctls: 
        :param container_log_max_files: 
        :param container_log_max_size_mb: 
        :param cpu_cfs_quota: 
        :param cpu_cfs_quota_period: 
        :param cpu_manager_policy: 
        :param fail_swap_on: 
        :param image_gc_high_threshold: 
        :param image_gc_low_threshold: 
        :param pod_max_pids: 
        :param topology_manager_policy: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8df6b00212e1fa9e88180561c58771f27a28e79463dafa623342e2c2bfb14dbd)
            check_type(argname="argument allowed_unsafe_sysctls", value=allowed_unsafe_sysctls, expected_type=type_hints["allowed_unsafe_sysctls"])
            check_type(argname="argument container_log_max_files", value=container_log_max_files, expected_type=type_hints["container_log_max_files"])
            check_type(argname="argument container_log_max_size_mb", value=container_log_max_size_mb, expected_type=type_hints["container_log_max_size_mb"])
            check_type(argname="argument cpu_cfs_quota", value=cpu_cfs_quota, expected_type=type_hints["cpu_cfs_quota"])
            check_type(argname="argument cpu_cfs_quota_period", value=cpu_cfs_quota_period, expected_type=type_hints["cpu_cfs_quota_period"])
            check_type(argname="argument cpu_manager_policy", value=cpu_manager_policy, expected_type=type_hints["cpu_manager_policy"])
            check_type(argname="argument fail_swap_on", value=fail_swap_on, expected_type=type_hints["fail_swap_on"])
            check_type(argname="argument image_gc_high_threshold", value=image_gc_high_threshold, expected_type=type_hints["image_gc_high_threshold"])
            check_type(argname="argument image_gc_low_threshold", value=image_gc_low_threshold, expected_type=type_hints["image_gc_low_threshold"])
            check_type(argname="argument pod_max_pids", value=pod_max_pids, expected_type=type_hints["pod_max_pids"])
            check_type(argname="argument topology_manager_policy", value=topology_manager_policy, expected_type=type_hints["topology_manager_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if allowed_unsafe_sysctls is not None:
            self._values["allowed_unsafe_sysctls"] = allowed_unsafe_sysctls
        if container_log_max_files is not None:
            self._values["container_log_max_files"] = container_log_max_files
        if container_log_max_size_mb is not None:
            self._values["container_log_max_size_mb"] = container_log_max_size_mb
        if cpu_cfs_quota is not None:
            self._values["cpu_cfs_quota"] = cpu_cfs_quota
        if cpu_cfs_quota_period is not None:
            self._values["cpu_cfs_quota_period"] = cpu_cfs_quota_period
        if cpu_manager_policy is not None:
            self._values["cpu_manager_policy"] = cpu_manager_policy
        if fail_swap_on is not None:
            self._values["fail_swap_on"] = fail_swap_on
        if image_gc_high_threshold is not None:
            self._values["image_gc_high_threshold"] = image_gc_high_threshold
        if image_gc_low_threshold is not None:
            self._values["image_gc_low_threshold"] = image_gc_low_threshold
        if pod_max_pids is not None:
            self._values["pod_max_pids"] = pod_max_pids
        if topology_manager_policy is not None:
            self._values["topology_manager_policy"] = topology_manager_policy

    @builtins.property
    def allowed_unsafe_sysctls(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("allowed_unsafe_sysctls")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def container_log_max_files(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("container_log_max_files")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def container_log_max_size_mb(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("container_log_max_size_mb")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def cpu_cfs_quota(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("cpu_cfs_quota")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def cpu_cfs_quota_period(self) -> typing.Optional[builtins.str]:
        result = self._values.get("cpu_cfs_quota_period")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def cpu_manager_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("cpu_manager_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def fail_swap_on(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("fail_swap_on")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def image_gc_high_threshold(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("image_gc_high_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def image_gc_low_threshold(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("image_gc_low_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def pod_max_pids(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("pod_max_pids")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def topology_manager_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("topology_manager_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterKubeletConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterLinuxOSConfig",
    jsii_struct_bases=[],
    name_mapping={
        "swap_file_size_mb": "swapFileSizeMB",
        "sysctls": "sysctls",
        "transparent_huge_page_defrag": "transparentHugePageDefrag",
        "transparent_huge_page_enabled": "transparentHugePageEnabled",
    },
)
class AksClusterLinuxOSConfig:
    def __init__(
        self,
        *,
        swap_file_size_mb: typing.Optional[jsii.Number] = None,
        sysctls: typing.Optional[typing.Union["AksClusterSysctlConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        transparent_huge_page_defrag: typing.Optional[builtins.str] = None,
        transparent_huge_page_enabled: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Linux OS configuration.

        :param swap_file_size_mb: 
        :param sysctls: 
        :param transparent_huge_page_defrag: 
        :param transparent_huge_page_enabled: 
        '''
        if isinstance(sysctls, dict):
            sysctls = AksClusterSysctlConfig(**sysctls)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__908b895e22d866e935a203fdf1e1777c0ce22cf373c92d034fb9a2fee6285ba2)
            check_type(argname="argument swap_file_size_mb", value=swap_file_size_mb, expected_type=type_hints["swap_file_size_mb"])
            check_type(argname="argument sysctls", value=sysctls, expected_type=type_hints["sysctls"])
            check_type(argname="argument transparent_huge_page_defrag", value=transparent_huge_page_defrag, expected_type=type_hints["transparent_huge_page_defrag"])
            check_type(argname="argument transparent_huge_page_enabled", value=transparent_huge_page_enabled, expected_type=type_hints["transparent_huge_page_enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if swap_file_size_mb is not None:
            self._values["swap_file_size_mb"] = swap_file_size_mb
        if sysctls is not None:
            self._values["sysctls"] = sysctls
        if transparent_huge_page_defrag is not None:
            self._values["transparent_huge_page_defrag"] = transparent_huge_page_defrag
        if transparent_huge_page_enabled is not None:
            self._values["transparent_huge_page_enabled"] = transparent_huge_page_enabled

    @builtins.property
    def swap_file_size_mb(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("swap_file_size_mb")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def sysctls(self) -> typing.Optional["AksClusterSysctlConfig"]:
        result = self._values.get("sysctls")
        return typing.cast(typing.Optional["AksClusterSysctlConfig"], result)

    @builtins.property
    def transparent_huge_page_defrag(self) -> typing.Optional[builtins.str]:
        result = self._values.get("transparent_huge_page_defrag")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def transparent_huge_page_enabled(self) -> typing.Optional[builtins.str]:
        result = self._values.get("transparent_huge_page_enabled")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterLinuxOSConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterLinuxProfile",
    jsii_struct_bases=[],
    name_mapping={"admin_username": "adminUsername", "ssh": "ssh"},
)
class AksClusterLinuxProfile:
    def __init__(
        self,
        *,
        admin_username: builtins.str,
        ssh: typing.Union["AksClusterSshConfiguration", typing.Dict[builtins.str, typing.Any]],
    ) -> None:
        '''Linux profile.

        :param admin_username: 
        :param ssh: 
        '''
        if isinstance(ssh, dict):
            ssh = AksClusterSshConfiguration(**ssh)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a3cb4f3fc81efda6c93459507bb8de667e992775d04ec1302dd23e4158321fdf)
            check_type(argname="argument admin_username", value=admin_username, expected_type=type_hints["admin_username"])
            check_type(argname="argument ssh", value=ssh, expected_type=type_hints["ssh"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "admin_username": admin_username,
            "ssh": ssh,
        }

    @builtins.property
    def admin_username(self) -> builtins.str:
        result = self._values.get("admin_username")
        assert result is not None, "Required property 'admin_username' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def ssh(self) -> "AksClusterSshConfiguration":
        result = self._values.get("ssh")
        assert result is not None, "Required property 'ssh' is missing"
        return typing.cast("AksClusterSshConfiguration", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterLinuxProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterLoadBalancerProfile",
    jsii_struct_bases=[],
    name_mapping={
        "allocated_outbound_ports": "allocatedOutboundPorts",
        "effective_outbound_i_ps": "effectiveOutboundIPs",
        "enable_multiple_standard_load_balancers": "enableMultipleStandardLoadBalancers",
        "idle_timeout_in_minutes": "idleTimeoutInMinutes",
        "managed_outbound_i_ps": "managedOutboundIPs",
        "outbound_ip_prefixes": "outboundIPPrefixes",
        "outbound_i_ps": "outboundIPs",
    },
)
class AksClusterLoadBalancerProfile:
    def __init__(
        self,
        *,
        allocated_outbound_ports: typing.Optional[jsii.Number] = None,
        effective_outbound_i_ps: typing.Optional[typing.Sequence[typing.Union[AksClusterEffectiveOutboundIP, typing.Dict[builtins.str, typing.Any]]]] = None,
        enable_multiple_standard_load_balancers: typing.Optional[builtins.bool] = None,
        idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
        managed_outbound_i_ps: typing.Optional[typing.Union["AksClusterManagedOutboundIPs", typing.Dict[builtins.str, typing.Any]]] = None,
        outbound_ip_prefixes: typing.Optional[typing.Union["AksClusterOutboundIPPrefixes", typing.Dict[builtins.str, typing.Any]]] = None,
        outbound_i_ps: typing.Optional[typing.Union["AksClusterOutboundIPs", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Load balancer profile.

        :param allocated_outbound_ports: 
        :param effective_outbound_i_ps: 
        :param enable_multiple_standard_load_balancers: 
        :param idle_timeout_in_minutes: 
        :param managed_outbound_i_ps: 
        :param outbound_ip_prefixes: 
        :param outbound_i_ps: 
        '''
        if isinstance(managed_outbound_i_ps, dict):
            managed_outbound_i_ps = AksClusterManagedOutboundIPs(**managed_outbound_i_ps)
        if isinstance(outbound_ip_prefixes, dict):
            outbound_ip_prefixes = AksClusterOutboundIPPrefixes(**outbound_ip_prefixes)
        if isinstance(outbound_i_ps, dict):
            outbound_i_ps = AksClusterOutboundIPs(**outbound_i_ps)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__357da0f7eaa143f5db73e6fc0ac9b9cc6a77fb2054cfc20fe1758157082245b8)
            check_type(argname="argument allocated_outbound_ports", value=allocated_outbound_ports, expected_type=type_hints["allocated_outbound_ports"])
            check_type(argname="argument effective_outbound_i_ps", value=effective_outbound_i_ps, expected_type=type_hints["effective_outbound_i_ps"])
            check_type(argname="argument enable_multiple_standard_load_balancers", value=enable_multiple_standard_load_balancers, expected_type=type_hints["enable_multiple_standard_load_balancers"])
            check_type(argname="argument idle_timeout_in_minutes", value=idle_timeout_in_minutes, expected_type=type_hints["idle_timeout_in_minutes"])
            check_type(argname="argument managed_outbound_i_ps", value=managed_outbound_i_ps, expected_type=type_hints["managed_outbound_i_ps"])
            check_type(argname="argument outbound_ip_prefixes", value=outbound_ip_prefixes, expected_type=type_hints["outbound_ip_prefixes"])
            check_type(argname="argument outbound_i_ps", value=outbound_i_ps, expected_type=type_hints["outbound_i_ps"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if allocated_outbound_ports is not None:
            self._values["allocated_outbound_ports"] = allocated_outbound_ports
        if effective_outbound_i_ps is not None:
            self._values["effective_outbound_i_ps"] = effective_outbound_i_ps
        if enable_multiple_standard_load_balancers is not None:
            self._values["enable_multiple_standard_load_balancers"] = enable_multiple_standard_load_balancers
        if idle_timeout_in_minutes is not None:
            self._values["idle_timeout_in_minutes"] = idle_timeout_in_minutes
        if managed_outbound_i_ps is not None:
            self._values["managed_outbound_i_ps"] = managed_outbound_i_ps
        if outbound_ip_prefixes is not None:
            self._values["outbound_ip_prefixes"] = outbound_ip_prefixes
        if outbound_i_ps is not None:
            self._values["outbound_i_ps"] = outbound_i_ps

    @builtins.property
    def allocated_outbound_ports(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("allocated_outbound_ports")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def effective_outbound_i_ps(
        self,
    ) -> typing.Optional[typing.List[AksClusterEffectiveOutboundIP]]:
        result = self._values.get("effective_outbound_i_ps")
        return typing.cast(typing.Optional[typing.List[AksClusterEffectiveOutboundIP]], result)

    @builtins.property
    def enable_multiple_standard_load_balancers(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_multiple_standard_load_balancers")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def idle_timeout_in_minutes(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("idle_timeout_in_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def managed_outbound_i_ps(self) -> typing.Optional["AksClusterManagedOutboundIPs"]:
        result = self._values.get("managed_outbound_i_ps")
        return typing.cast(typing.Optional["AksClusterManagedOutboundIPs"], result)

    @builtins.property
    def outbound_ip_prefixes(self) -> typing.Optional["AksClusterOutboundIPPrefixes"]:
        result = self._values.get("outbound_ip_prefixes")
        return typing.cast(typing.Optional["AksClusterOutboundIPPrefixes"], result)

    @builtins.property
    def outbound_i_ps(self) -> typing.Optional["AksClusterOutboundIPs"]:
        result = self._values.get("outbound_i_ps")
        return typing.cast(typing.Optional["AksClusterOutboundIPs"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterLoadBalancerProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterManagedOutboundIPProfile",
    jsii_struct_bases=[],
    name_mapping={"count": "count"},
)
class AksClusterManagedOutboundIPProfile:
    def __init__(self, *, count: typing.Optional[jsii.Number] = None) -> None:
        '''Managed outbound IP profile.

        :param count: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eb189f46d2da79ff38dadb2d3f04cbff91cc560e143c95616cae248d2e7015cf)
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if count is not None:
            self._values["count"] = count

    @builtins.property
    def count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("count")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterManagedOutboundIPProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterManagedOutboundIPs",
    jsii_struct_bases=[],
    name_mapping={"count": "count", "count_i_pv6": "countIPv6"},
)
class AksClusterManagedOutboundIPs:
    def __init__(
        self,
        *,
        count: typing.Optional[jsii.Number] = None,
        count_i_pv6: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Managed outbound IPs.

        :param count: 
        :param count_i_pv6: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7ea8913e4155425befcece8115d2f020f72973a7c8f310572d7feb3594d557a8)
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument count_i_pv6", value=count_i_pv6, expected_type=type_hints["count_i_pv6"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if count is not None:
            self._values["count"] = count
        if count_i_pv6 is not None:
            self._values["count_i_pv6"] = count_i_pv6

    @builtins.property
    def count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def count_i_pv6(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("count_i_pv6")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterManagedOutboundIPs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterMonitoringOptions",
    jsii_struct_bases=[],
    name_mapping={
        "enable_deletion_alert": "enableDeletionAlert",
        "enable_failed_pod_alert": "enableFailedPodAlert",
        "enable_node_cpu_alert": "enableNodeCpuAlert",
        "enable_node_memory_alert": "enableNodeMemoryAlert",
        "failed_pod_alert_severity": "failedPodAlertSeverity",
        "failed_pod_threshold": "failedPodThreshold",
        "node_cpu_alert_severity": "nodeCpuAlertSeverity",
        "node_cpu_threshold": "nodeCpuThreshold",
        "node_memory_alert_severity": "nodeMemoryAlertSeverity",
        "node_memory_threshold": "nodeMemoryThreshold",
    },
)
class AksClusterMonitoringOptions:
    def __init__(
        self,
        *,
        enable_deletion_alert: typing.Optional[builtins.bool] = None,
        enable_failed_pod_alert: typing.Optional[builtins.bool] = None,
        enable_node_cpu_alert: typing.Optional[builtins.bool] = None,
        enable_node_memory_alert: typing.Optional[builtins.bool] = None,
        failed_pod_alert_severity: typing.Optional[jsii.Number] = None,
        failed_pod_threshold: typing.Optional[jsii.Number] = None,
        node_cpu_alert_severity: typing.Optional[jsii.Number] = None,
        node_cpu_threshold: typing.Optional[jsii.Number] = None,
        node_memory_alert_severity: typing.Optional[jsii.Number] = None,
        node_memory_threshold: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Configuration options for AKS Cluster monitoring.

        :param enable_deletion_alert: Whether to enable AKS cluster deletion alert. Default: true
        :param enable_failed_pod_alert: Whether to enable failed pod alert. Default: true
        :param enable_node_cpu_alert: Whether to enable node CPU usage alert. Default: true
        :param enable_node_memory_alert: Whether to enable node memory usage alert. Default: true
        :param failed_pod_alert_severity: Severity level for failed pod alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose). Default: 1
        :param failed_pod_threshold: Threshold for failed pod count. Default: 0
        :param node_cpu_alert_severity: Severity level for node CPU alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose). Default: 2
        :param node_cpu_threshold: Threshold for node CPU usage percentage (0-100). Default: 80
        :param node_memory_alert_severity: Severity level for node memory alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose). Default: 2
        :param node_memory_threshold: Threshold for node memory usage percentage (0-100). Default: 80
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__700a5cfbc9d5eae92ed4cd7f7feab013900b7e322beef7fe90331d2b6342c0b7)
            check_type(argname="argument enable_deletion_alert", value=enable_deletion_alert, expected_type=type_hints["enable_deletion_alert"])
            check_type(argname="argument enable_failed_pod_alert", value=enable_failed_pod_alert, expected_type=type_hints["enable_failed_pod_alert"])
            check_type(argname="argument enable_node_cpu_alert", value=enable_node_cpu_alert, expected_type=type_hints["enable_node_cpu_alert"])
            check_type(argname="argument enable_node_memory_alert", value=enable_node_memory_alert, expected_type=type_hints["enable_node_memory_alert"])
            check_type(argname="argument failed_pod_alert_severity", value=failed_pod_alert_severity, expected_type=type_hints["failed_pod_alert_severity"])
            check_type(argname="argument failed_pod_threshold", value=failed_pod_threshold, expected_type=type_hints["failed_pod_threshold"])
            check_type(argname="argument node_cpu_alert_severity", value=node_cpu_alert_severity, expected_type=type_hints["node_cpu_alert_severity"])
            check_type(argname="argument node_cpu_threshold", value=node_cpu_threshold, expected_type=type_hints["node_cpu_threshold"])
            check_type(argname="argument node_memory_alert_severity", value=node_memory_alert_severity, expected_type=type_hints["node_memory_alert_severity"])
            check_type(argname="argument node_memory_threshold", value=node_memory_threshold, expected_type=type_hints["node_memory_threshold"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enable_deletion_alert is not None:
            self._values["enable_deletion_alert"] = enable_deletion_alert
        if enable_failed_pod_alert is not None:
            self._values["enable_failed_pod_alert"] = enable_failed_pod_alert
        if enable_node_cpu_alert is not None:
            self._values["enable_node_cpu_alert"] = enable_node_cpu_alert
        if enable_node_memory_alert is not None:
            self._values["enable_node_memory_alert"] = enable_node_memory_alert
        if failed_pod_alert_severity is not None:
            self._values["failed_pod_alert_severity"] = failed_pod_alert_severity
        if failed_pod_threshold is not None:
            self._values["failed_pod_threshold"] = failed_pod_threshold
        if node_cpu_alert_severity is not None:
            self._values["node_cpu_alert_severity"] = node_cpu_alert_severity
        if node_cpu_threshold is not None:
            self._values["node_cpu_threshold"] = node_cpu_threshold
        if node_memory_alert_severity is not None:
            self._values["node_memory_alert_severity"] = node_memory_alert_severity
        if node_memory_threshold is not None:
            self._values["node_memory_threshold"] = node_memory_threshold

    @builtins.property
    def enable_deletion_alert(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable AKS cluster deletion alert.

        :default: true
        '''
        result = self._values.get("enable_deletion_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_failed_pod_alert(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable failed pod alert.

        :default: true
        '''
        result = self._values.get("enable_failed_pod_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_node_cpu_alert(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable node CPU usage alert.

        :default: true
        '''
        result = self._values.get("enable_node_cpu_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def enable_node_memory_alert(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable node memory usage alert.

        :default: true
        '''
        result = self._values.get("enable_node_memory_alert")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def failed_pod_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for failed pod alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose).

        :default: 1
        '''
        result = self._values.get("failed_pod_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def failed_pod_threshold(self) -> typing.Optional[jsii.Number]:
        '''Threshold for failed pod count.

        :default: 0
        '''
        result = self._values.get("failed_pod_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def node_cpu_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for node CPU alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose).

        :default: 2
        '''
        result = self._values.get("node_cpu_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def node_cpu_threshold(self) -> typing.Optional[jsii.Number]:
        '''Threshold for node CPU usage percentage (0-100).

        :default: 80
        '''
        result = self._values.get("node_cpu_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def node_memory_alert_severity(self) -> typing.Optional[jsii.Number]:
        '''Severity level for node memory alert (0=Critical, 1=Error, 2=Warning, 3=Informational, 4=Verbose).

        :default: 2
        '''
        result = self._values.get("node_memory_alert_severity")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def node_memory_threshold(self) -> typing.Optional[jsii.Number]:
        '''Threshold for node memory usage percentage (0-100).

        :default: 80
        '''
        result = self._values.get("node_memory_threshold")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterMonitoringOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterNatGatewayProfile",
    jsii_struct_bases=[],
    name_mapping={
        "effective_outbound_i_ps": "effectiveOutboundIPs",
        "idle_timeout_in_minutes": "idleTimeoutInMinutes",
        "managed_outbound_ip_profile": "managedOutboundIPProfile",
    },
)
class AksClusterNatGatewayProfile:
    def __init__(
        self,
        *,
        effective_outbound_i_ps: typing.Optional[typing.Sequence[typing.Union[AksClusterEffectiveOutboundIP, typing.Dict[builtins.str, typing.Any]]]] = None,
        idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
        managed_outbound_ip_profile: typing.Optional[typing.Union[AksClusterManagedOutboundIPProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''NAT Gateway profile.

        :param effective_outbound_i_ps: 
        :param idle_timeout_in_minutes: 
        :param managed_outbound_ip_profile: 
        '''
        if isinstance(managed_outbound_ip_profile, dict):
            managed_outbound_ip_profile = AksClusterManagedOutboundIPProfile(**managed_outbound_ip_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__68ff60799c0f080481eba0dabbbecd91b80859476cbe8c37e6e8b15029eb7c25)
            check_type(argname="argument effective_outbound_i_ps", value=effective_outbound_i_ps, expected_type=type_hints["effective_outbound_i_ps"])
            check_type(argname="argument idle_timeout_in_minutes", value=idle_timeout_in_minutes, expected_type=type_hints["idle_timeout_in_minutes"])
            check_type(argname="argument managed_outbound_ip_profile", value=managed_outbound_ip_profile, expected_type=type_hints["managed_outbound_ip_profile"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if effective_outbound_i_ps is not None:
            self._values["effective_outbound_i_ps"] = effective_outbound_i_ps
        if idle_timeout_in_minutes is not None:
            self._values["idle_timeout_in_minutes"] = idle_timeout_in_minutes
        if managed_outbound_ip_profile is not None:
            self._values["managed_outbound_ip_profile"] = managed_outbound_ip_profile

    @builtins.property
    def effective_outbound_i_ps(
        self,
    ) -> typing.Optional[typing.List[AksClusterEffectiveOutboundIP]]:
        result = self._values.get("effective_outbound_i_ps")
        return typing.cast(typing.Optional[typing.List[AksClusterEffectiveOutboundIP]], result)

    @builtins.property
    def idle_timeout_in_minutes(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("idle_timeout_in_minutes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def managed_outbound_ip_profile(
        self,
    ) -> typing.Optional[AksClusterManagedOutboundIPProfile]:
        result = self._values.get("managed_outbound_ip_profile")
        return typing.cast(typing.Optional[AksClusterManagedOutboundIPProfile], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterNatGatewayProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterNetworkProfile",
    jsii_struct_bases=[],
    name_mapping={
        "dns_service_ip": "dnsServiceIP",
        "docker_bridge_cidr": "dockerBridgeCidr",
        "ip_families": "ipFamilies",
        "load_balancer_profile": "loadBalancerProfile",
        "load_balancer_sku": "loadBalancerSku",
        "nat_gateway_profile": "natGatewayProfile",
        "network_mode": "networkMode",
        "network_plugin": "networkPlugin",
        "network_policy": "networkPolicy",
        "outbound_type": "outboundType",
        "pod_cidr": "podCidr",
        "pod_cidrs": "podCidrs",
        "service_cidr": "serviceCidr",
        "service_cidrs": "serviceCidrs",
    },
)
class AksClusterNetworkProfile:
    def __init__(
        self,
        *,
        dns_service_ip: typing.Optional[builtins.str] = None,
        docker_bridge_cidr: typing.Optional[builtins.str] = None,
        ip_families: typing.Optional[typing.Sequence[builtins.str]] = None,
        load_balancer_profile: typing.Optional[typing.Union[AksClusterLoadBalancerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        load_balancer_sku: typing.Optional[builtins.str] = None,
        nat_gateway_profile: typing.Optional[typing.Union[AksClusterNatGatewayProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        network_mode: typing.Optional[builtins.str] = None,
        network_plugin: typing.Optional[builtins.str] = None,
        network_policy: typing.Optional[builtins.str] = None,
        outbound_type: typing.Optional[builtins.str] = None,
        pod_cidr: typing.Optional[builtins.str] = None,
        pod_cidrs: typing.Optional[typing.Sequence[builtins.str]] = None,
        service_cidr: typing.Optional[builtins.str] = None,
        service_cidrs: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Network profile for AKS cluster.

        :param dns_service_ip: 
        :param docker_bridge_cidr: 
        :param ip_families: 
        :param load_balancer_profile: 
        :param load_balancer_sku: 
        :param nat_gateway_profile: 
        :param network_mode: 
        :param network_plugin: 
        :param network_policy: 
        :param outbound_type: 
        :param pod_cidr: 
        :param pod_cidrs: 
        :param service_cidr: 
        :param service_cidrs: 
        '''
        if isinstance(load_balancer_profile, dict):
            load_balancer_profile = AksClusterLoadBalancerProfile(**load_balancer_profile)
        if isinstance(nat_gateway_profile, dict):
            nat_gateway_profile = AksClusterNatGatewayProfile(**nat_gateway_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__967e08c3da7ceaca31f4b4e6ff5c59af5d1e1570e7c97f1db2336f604ae62ed4)
            check_type(argname="argument dns_service_ip", value=dns_service_ip, expected_type=type_hints["dns_service_ip"])
            check_type(argname="argument docker_bridge_cidr", value=docker_bridge_cidr, expected_type=type_hints["docker_bridge_cidr"])
            check_type(argname="argument ip_families", value=ip_families, expected_type=type_hints["ip_families"])
            check_type(argname="argument load_balancer_profile", value=load_balancer_profile, expected_type=type_hints["load_balancer_profile"])
            check_type(argname="argument load_balancer_sku", value=load_balancer_sku, expected_type=type_hints["load_balancer_sku"])
            check_type(argname="argument nat_gateway_profile", value=nat_gateway_profile, expected_type=type_hints["nat_gateway_profile"])
            check_type(argname="argument network_mode", value=network_mode, expected_type=type_hints["network_mode"])
            check_type(argname="argument network_plugin", value=network_plugin, expected_type=type_hints["network_plugin"])
            check_type(argname="argument network_policy", value=network_policy, expected_type=type_hints["network_policy"])
            check_type(argname="argument outbound_type", value=outbound_type, expected_type=type_hints["outbound_type"])
            check_type(argname="argument pod_cidr", value=pod_cidr, expected_type=type_hints["pod_cidr"])
            check_type(argname="argument pod_cidrs", value=pod_cidrs, expected_type=type_hints["pod_cidrs"])
            check_type(argname="argument service_cidr", value=service_cidr, expected_type=type_hints["service_cidr"])
            check_type(argname="argument service_cidrs", value=service_cidrs, expected_type=type_hints["service_cidrs"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if dns_service_ip is not None:
            self._values["dns_service_ip"] = dns_service_ip
        if docker_bridge_cidr is not None:
            self._values["docker_bridge_cidr"] = docker_bridge_cidr
        if ip_families is not None:
            self._values["ip_families"] = ip_families
        if load_balancer_profile is not None:
            self._values["load_balancer_profile"] = load_balancer_profile
        if load_balancer_sku is not None:
            self._values["load_balancer_sku"] = load_balancer_sku
        if nat_gateway_profile is not None:
            self._values["nat_gateway_profile"] = nat_gateway_profile
        if network_mode is not None:
            self._values["network_mode"] = network_mode
        if network_plugin is not None:
            self._values["network_plugin"] = network_plugin
        if network_policy is not None:
            self._values["network_policy"] = network_policy
        if outbound_type is not None:
            self._values["outbound_type"] = outbound_type
        if pod_cidr is not None:
            self._values["pod_cidr"] = pod_cidr
        if pod_cidrs is not None:
            self._values["pod_cidrs"] = pod_cidrs
        if service_cidr is not None:
            self._values["service_cidr"] = service_cidr
        if service_cidrs is not None:
            self._values["service_cidrs"] = service_cidrs

    @builtins.property
    def dns_service_ip(self) -> typing.Optional[builtins.str]:
        result = self._values.get("dns_service_ip")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def docker_bridge_cidr(self) -> typing.Optional[builtins.str]:
        result = self._values.get("docker_bridge_cidr")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ip_families(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("ip_families")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def load_balancer_profile(self) -> typing.Optional[AksClusterLoadBalancerProfile]:
        result = self._values.get("load_balancer_profile")
        return typing.cast(typing.Optional[AksClusterLoadBalancerProfile], result)

    @builtins.property
    def load_balancer_sku(self) -> typing.Optional[builtins.str]:
        result = self._values.get("load_balancer_sku")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def nat_gateway_profile(self) -> typing.Optional[AksClusterNatGatewayProfile]:
        result = self._values.get("nat_gateway_profile")
        return typing.cast(typing.Optional[AksClusterNatGatewayProfile], result)

    @builtins.property
    def network_mode(self) -> typing.Optional[builtins.str]:
        result = self._values.get("network_mode")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def network_plugin(self) -> typing.Optional[builtins.str]:
        result = self._values.get("network_plugin")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def network_policy(self) -> typing.Optional[builtins.str]:
        result = self._values.get("network_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def outbound_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("outbound_type")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pod_cidr(self) -> typing.Optional[builtins.str]:
        result = self._values.get("pod_cidr")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pod_cidrs(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("pod_cidrs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def service_cidr(self) -> typing.Optional[builtins.str]:
        result = self._values.get("service_cidr")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def service_cidrs(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("service_cidrs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterNetworkProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterOidcIssuerProfile",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled", "issuer_url": "issuerURL"},
)
class AksClusterOidcIssuerProfile:
    def __init__(
        self,
        *,
        enabled: typing.Optional[builtins.bool] = None,
        issuer_url: typing.Optional[builtins.str] = None,
    ) -> None:
        '''OIDC issuer profile.

        :param enabled: 
        :param issuer_url: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0465c1752edb538cfb5e9cb855c50af83e323a1c21ff4731e82a717383e0d9fc)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument issuer_url", value=issuer_url, expected_type=type_hints["issuer_url"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled
        if issuer_url is not None:
            self._values["issuer_url"] = issuer_url

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def issuer_url(self) -> typing.Optional[builtins.str]:
        result = self._values.get("issuer_url")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterOidcIssuerProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterOutboundIPPrefixes",
    jsii_struct_bases=[],
    name_mapping={"public_ip_prefixes": "publicIPPrefixes"},
)
class AksClusterOutboundIPPrefixes:
    def __init__(
        self,
        *,
        public_ip_prefixes: typing.Optional[typing.Sequence[typing.Union["AksClusterResourceReference", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Outbound IP prefixes.

        :param public_ip_prefixes: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a61fa88e1f0ddede724539f453ce09cd4adf89c469170e9b6e8aba9e4f305fa)
            check_type(argname="argument public_ip_prefixes", value=public_ip_prefixes, expected_type=type_hints["public_ip_prefixes"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if public_ip_prefixes is not None:
            self._values["public_ip_prefixes"] = public_ip_prefixes

    @builtins.property
    def public_ip_prefixes(
        self,
    ) -> typing.Optional[typing.List["AksClusterResourceReference"]]:
        result = self._values.get("public_ip_prefixes")
        return typing.cast(typing.Optional[typing.List["AksClusterResourceReference"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterOutboundIPPrefixes(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterOutboundIPs",
    jsii_struct_bases=[],
    name_mapping={"public_i_ps": "publicIPs"},
)
class AksClusterOutboundIPs:
    def __init__(
        self,
        *,
        public_i_ps: typing.Optional[typing.Sequence[typing.Union["AksClusterResourceReference", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Outbound IPs.

        :param public_i_ps: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9f3f3ce8d65ac44601439a466eb35943e0707e973979209d8e3b13387693ea34)
            check_type(argname="argument public_i_ps", value=public_i_ps, expected_type=type_hints["public_i_ps"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if public_i_ps is not None:
            self._values["public_i_ps"] = public_i_ps

    @builtins.property
    def public_i_ps(
        self,
    ) -> typing.Optional[typing.List["AksClusterResourceReference"]]:
        result = self._values.get("public_i_ps")
        return typing.cast(typing.Optional[typing.List["AksClusterResourceReference"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterOutboundIPs(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterProps",
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
        "agent_pool_profiles": "agentPoolProfiles",
        "dns_prefix": "dnsPrefix",
        "aad_profile": "aadProfile",
        "addon_profiles": "addonProfiles",
        "api_server_access_profile": "apiServerAccessProfile",
        "auto_scaler_profile": "autoScalerProfile",
        "disable_local_accounts": "disableLocalAccounts",
        "disk_encryption_set_id": "diskEncryptionSetID",
        "enable_rbac": "enableRBAC",
        "fqdn": "fqdn",
        "http_proxy_config": "httpProxyConfig",
        "identity": "identity",
        "ignore_changes": "ignoreChanges",
        "kubernetes_version": "kubernetesVersion",
        "linux_profile": "linuxProfile",
        "network_profile": "networkProfile",
        "node_resource_group": "nodeResourceGroup",
        "oidc_issuer_profile": "oidcIssuerProfile",
        "private_fqdn": "privateFQDN",
        "public_network_access": "publicNetworkAccess",
        "resource_group_id": "resourceGroupId",
        "security_profile": "securityProfile",
        "service_principal_profile": "servicePrincipalProfile",
        "sku": "sku",
        "storage_profile": "storageProfile",
        "support_plan": "supportPlan",
        "windows_profile": "windowsProfile",
        "workload_auto_scaler_profile": "workloadAutoScalerProfile",
    },
)
class AksClusterProps(_AzapiResourceProps_141a2340):
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
        agent_pool_profiles: typing.Sequence[typing.Union[AksClusterAgentPoolProfile, typing.Dict[builtins.str, typing.Any]]],
        dns_prefix: builtins.str,
        aad_profile: typing.Optional[typing.Union[AksClusterAadProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        addon_profiles: typing.Optional[typing.Mapping[builtins.str, typing.Union[AksClusterAddonProfile, typing.Dict[builtins.str, typing.Any]]]] = None,
        api_server_access_profile: typing.Optional[typing.Union[AksClusterApiServerAccessProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        auto_scaler_profile: typing.Optional[typing.Union[AksClusterAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        disable_local_accounts: typing.Optional[builtins.bool] = None,
        disk_encryption_set_id: typing.Optional[builtins.str] = None,
        enable_rbac: typing.Optional[builtins.bool] = None,
        fqdn: typing.Optional[builtins.str] = None,
        http_proxy_config: typing.Optional[typing.Union[AksClusterHttpProxyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
        identity: typing.Optional[typing.Union[AksClusterIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
        ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
        kubernetes_version: typing.Optional[builtins.str] = None,
        linux_profile: typing.Optional[typing.Union[AksClusterLinuxProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        network_profile: typing.Optional[typing.Union[AksClusterNetworkProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        node_resource_group: typing.Optional[builtins.str] = None,
        oidc_issuer_profile: typing.Optional[typing.Union[AksClusterOidcIssuerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        private_fqdn: typing.Optional[builtins.str] = None,
        public_network_access: typing.Optional[builtins.str] = None,
        resource_group_id: typing.Optional[builtins.str] = None,
        security_profile: typing.Optional[typing.Union["AksClusterSecurityProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        service_principal_profile: typing.Optional[typing.Union["AksClusterServicePrincipalProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        sku: typing.Optional[typing.Union["AksClusterSku", typing.Dict[builtins.str, typing.Any]]] = None,
        storage_profile: typing.Optional[typing.Union["AksClusterStorageProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        support_plan: typing.Optional[builtins.str] = None,
        windows_profile: typing.Optional[typing.Union["AksClusterWindowsProfile", typing.Dict[builtins.str, typing.Any]]] = None,
        workload_auto_scaler_profile: typing.Optional[typing.Union["AksClusterWorkloadAutoScalerProfile", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Properties for the unified Azure Kubernetes Service cluster.

        Extends AzapiResourceProps with AKS-specific properties

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
        :param agent_pool_profiles: The agent pool profiles for the cluster node pools At least one agent pool is required.
        :param dns_prefix: DNS prefix for the cluster.
        :param aad_profile: The Azure Active Directory integration configuration.
        :param addon_profiles: The addon profiles for cluster addons.
        :param api_server_access_profile: The API server access configuration.
        :param auto_scaler_profile: The auto-scaler configuration for the cluster.
        :param disable_local_accounts: Whether to disable local accounts. Default: false
        :param disk_encryption_set_id: The resource ID of the disk encryption set for encrypting disks.
        :param enable_rbac: Whether to enable Kubernetes Role-Based Access Control. Default: true
        :param fqdn: The FQDN for the cluster (read-only).
        :param http_proxy_config: The HTTP proxy configuration.
        :param identity: The identity configuration for the AKS cluster.
        :param ignore_changes: The lifecycle rules to ignore changes Useful for properties that are externally managed or should not trigger updates.
        :param kubernetes_version: The Kubernetes version for the cluster.
        :param linux_profile: The Linux profile for SSH access.
        :param network_profile: The network configuration for the cluster.
        :param node_resource_group: The name of the resource group for cluster nodes If not specified, Azure will auto-generate the name.
        :param oidc_issuer_profile: The OIDC issuer profile for workload identity.
        :param private_fqdn: The private FQDN for the cluster (read-only).
        :param public_network_access: Whether the cluster is accessible from the public internet.
        :param resource_group_id: Resource group ID where the AKS cluster will be created.
        :param security_profile: The security profile for the cluster.
        :param service_principal_profile: The service principal profile for the cluster.
        :param sku: The SKU (pricing tier) for the AKS cluster.
        :param storage_profile: The storage profile for CSI drivers.
        :param support_plan: The support plan for the cluster.
        :param windows_profile: The Windows profile for Windows node pools.
        :param workload_auto_scaler_profile: The workload auto-scaler profile.
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = _MonitoringConfig_7c28df74(**monitoring)
        if isinstance(aad_profile, dict):
            aad_profile = AksClusterAadProfile(**aad_profile)
        if isinstance(api_server_access_profile, dict):
            api_server_access_profile = AksClusterApiServerAccessProfile(**api_server_access_profile)
        if isinstance(auto_scaler_profile, dict):
            auto_scaler_profile = AksClusterAutoScalerProfile(**auto_scaler_profile)
        if isinstance(http_proxy_config, dict):
            http_proxy_config = AksClusterHttpProxyConfig(**http_proxy_config)
        if isinstance(identity, dict):
            identity = AksClusterIdentity(**identity)
        if isinstance(linux_profile, dict):
            linux_profile = AksClusterLinuxProfile(**linux_profile)
        if isinstance(network_profile, dict):
            network_profile = AksClusterNetworkProfile(**network_profile)
        if isinstance(oidc_issuer_profile, dict):
            oidc_issuer_profile = AksClusterOidcIssuerProfile(**oidc_issuer_profile)
        if isinstance(security_profile, dict):
            security_profile = AksClusterSecurityProfile(**security_profile)
        if isinstance(service_principal_profile, dict):
            service_principal_profile = AksClusterServicePrincipalProfile(**service_principal_profile)
        if isinstance(sku, dict):
            sku = AksClusterSku(**sku)
        if isinstance(storage_profile, dict):
            storage_profile = AksClusterStorageProfile(**storage_profile)
        if isinstance(windows_profile, dict):
            windows_profile = AksClusterWindowsProfile(**windows_profile)
        if isinstance(workload_auto_scaler_profile, dict):
            workload_auto_scaler_profile = AksClusterWorkloadAutoScalerProfile(**workload_auto_scaler_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5eb4b1478ac33861d98f32854ef8fae14f3e5fad9514868f6ff4223ee859c526)
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
            check_type(argname="argument agent_pool_profiles", value=agent_pool_profiles, expected_type=type_hints["agent_pool_profiles"])
            check_type(argname="argument dns_prefix", value=dns_prefix, expected_type=type_hints["dns_prefix"])
            check_type(argname="argument aad_profile", value=aad_profile, expected_type=type_hints["aad_profile"])
            check_type(argname="argument addon_profiles", value=addon_profiles, expected_type=type_hints["addon_profiles"])
            check_type(argname="argument api_server_access_profile", value=api_server_access_profile, expected_type=type_hints["api_server_access_profile"])
            check_type(argname="argument auto_scaler_profile", value=auto_scaler_profile, expected_type=type_hints["auto_scaler_profile"])
            check_type(argname="argument disable_local_accounts", value=disable_local_accounts, expected_type=type_hints["disable_local_accounts"])
            check_type(argname="argument disk_encryption_set_id", value=disk_encryption_set_id, expected_type=type_hints["disk_encryption_set_id"])
            check_type(argname="argument enable_rbac", value=enable_rbac, expected_type=type_hints["enable_rbac"])
            check_type(argname="argument fqdn", value=fqdn, expected_type=type_hints["fqdn"])
            check_type(argname="argument http_proxy_config", value=http_proxy_config, expected_type=type_hints["http_proxy_config"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument ignore_changes", value=ignore_changes, expected_type=type_hints["ignore_changes"])
            check_type(argname="argument kubernetes_version", value=kubernetes_version, expected_type=type_hints["kubernetes_version"])
            check_type(argname="argument linux_profile", value=linux_profile, expected_type=type_hints["linux_profile"])
            check_type(argname="argument network_profile", value=network_profile, expected_type=type_hints["network_profile"])
            check_type(argname="argument node_resource_group", value=node_resource_group, expected_type=type_hints["node_resource_group"])
            check_type(argname="argument oidc_issuer_profile", value=oidc_issuer_profile, expected_type=type_hints["oidc_issuer_profile"])
            check_type(argname="argument private_fqdn", value=private_fqdn, expected_type=type_hints["private_fqdn"])
            check_type(argname="argument public_network_access", value=public_network_access, expected_type=type_hints["public_network_access"])
            check_type(argname="argument resource_group_id", value=resource_group_id, expected_type=type_hints["resource_group_id"])
            check_type(argname="argument security_profile", value=security_profile, expected_type=type_hints["security_profile"])
            check_type(argname="argument service_principal_profile", value=service_principal_profile, expected_type=type_hints["service_principal_profile"])
            check_type(argname="argument sku", value=sku, expected_type=type_hints["sku"])
            check_type(argname="argument storage_profile", value=storage_profile, expected_type=type_hints["storage_profile"])
            check_type(argname="argument support_plan", value=support_plan, expected_type=type_hints["support_plan"])
            check_type(argname="argument windows_profile", value=windows_profile, expected_type=type_hints["windows_profile"])
            check_type(argname="argument workload_auto_scaler_profile", value=workload_auto_scaler_profile, expected_type=type_hints["workload_auto_scaler_profile"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "agent_pool_profiles": agent_pool_profiles,
            "dns_prefix": dns_prefix,
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
        if aad_profile is not None:
            self._values["aad_profile"] = aad_profile
        if addon_profiles is not None:
            self._values["addon_profiles"] = addon_profiles
        if api_server_access_profile is not None:
            self._values["api_server_access_profile"] = api_server_access_profile
        if auto_scaler_profile is not None:
            self._values["auto_scaler_profile"] = auto_scaler_profile
        if disable_local_accounts is not None:
            self._values["disable_local_accounts"] = disable_local_accounts
        if disk_encryption_set_id is not None:
            self._values["disk_encryption_set_id"] = disk_encryption_set_id
        if enable_rbac is not None:
            self._values["enable_rbac"] = enable_rbac
        if fqdn is not None:
            self._values["fqdn"] = fqdn
        if http_proxy_config is not None:
            self._values["http_proxy_config"] = http_proxy_config
        if identity is not None:
            self._values["identity"] = identity
        if ignore_changes is not None:
            self._values["ignore_changes"] = ignore_changes
        if kubernetes_version is not None:
            self._values["kubernetes_version"] = kubernetes_version
        if linux_profile is not None:
            self._values["linux_profile"] = linux_profile
        if network_profile is not None:
            self._values["network_profile"] = network_profile
        if node_resource_group is not None:
            self._values["node_resource_group"] = node_resource_group
        if oidc_issuer_profile is not None:
            self._values["oidc_issuer_profile"] = oidc_issuer_profile
        if private_fqdn is not None:
            self._values["private_fqdn"] = private_fqdn
        if public_network_access is not None:
            self._values["public_network_access"] = public_network_access
        if resource_group_id is not None:
            self._values["resource_group_id"] = resource_group_id
        if security_profile is not None:
            self._values["security_profile"] = security_profile
        if service_principal_profile is not None:
            self._values["service_principal_profile"] = service_principal_profile
        if sku is not None:
            self._values["sku"] = sku
        if storage_profile is not None:
            self._values["storage_profile"] = storage_profile
        if support_plan is not None:
            self._values["support_plan"] = support_plan
        if windows_profile is not None:
            self._values["windows_profile"] = windows_profile
        if workload_auto_scaler_profile is not None:
            self._values["workload_auto_scaler_profile"] = workload_auto_scaler_profile

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
    def agent_pool_profiles(self) -> typing.List[AksClusterAgentPoolProfile]:
        '''The agent pool profiles for the cluster node pools At least one agent pool is required.

        Example::

            [{ name: "default", count: 3, vmSize: "Standard_D2s_v3", mode: "System" }]
        '''
        result = self._values.get("agent_pool_profiles")
        assert result is not None, "Required property 'agent_pool_profiles' is missing"
        return typing.cast(typing.List[AksClusterAgentPoolProfile], result)

    @builtins.property
    def dns_prefix(self) -> builtins.str:
        '''DNS prefix for the cluster.

        Example::

            "myakscluster"
        '''
        result = self._values.get("dns_prefix")
        assert result is not None, "Required property 'dns_prefix' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def aad_profile(self) -> typing.Optional[AksClusterAadProfile]:
        '''The Azure Active Directory integration configuration.'''
        result = self._values.get("aad_profile")
        return typing.cast(typing.Optional[AksClusterAadProfile], result)

    @builtins.property
    def addon_profiles(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, AksClusterAddonProfile]]:
        '''The addon profiles for cluster addons.'''
        result = self._values.get("addon_profiles")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, AksClusterAddonProfile]], result)

    @builtins.property
    def api_server_access_profile(
        self,
    ) -> typing.Optional[AksClusterApiServerAccessProfile]:
        '''The API server access configuration.'''
        result = self._values.get("api_server_access_profile")
        return typing.cast(typing.Optional[AksClusterApiServerAccessProfile], result)

    @builtins.property
    def auto_scaler_profile(self) -> typing.Optional[AksClusterAutoScalerProfile]:
        '''The auto-scaler configuration for the cluster.'''
        result = self._values.get("auto_scaler_profile")
        return typing.cast(typing.Optional[AksClusterAutoScalerProfile], result)

    @builtins.property
    def disable_local_accounts(self) -> typing.Optional[builtins.bool]:
        '''Whether to disable local accounts.

        :default: false
        '''
        result = self._values.get("disable_local_accounts")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def disk_encryption_set_id(self) -> typing.Optional[builtins.str]:
        '''The resource ID of the disk encryption set for encrypting disks.'''
        result = self._values.get("disk_encryption_set_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_rbac(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable Kubernetes Role-Based Access Control.

        :default: true
        '''
        result = self._values.get("enable_rbac")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def fqdn(self) -> typing.Optional[builtins.str]:
        '''The FQDN for the cluster (read-only).'''
        result = self._values.get("fqdn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def http_proxy_config(self) -> typing.Optional[AksClusterHttpProxyConfig]:
        '''The HTTP proxy configuration.'''
        result = self._values.get("http_proxy_config")
        return typing.cast(typing.Optional[AksClusterHttpProxyConfig], result)

    @builtins.property
    def identity(self) -> typing.Optional[AksClusterIdentity]:
        '''The identity configuration for the AKS cluster.

        Example::

            { type: "UserAssigned", userAssignedIdentities: { "/subscriptions/.../resourceGroups/.../providers/Microsoft.ManagedIdentity/userAssignedIdentities/myIdentity": {} } }
        '''
        result = self._values.get("identity")
        return typing.cast(typing.Optional[AksClusterIdentity], result)

    @builtins.property
    def ignore_changes(self) -> typing.Optional[typing.List[builtins.str]]:
        '''The lifecycle rules to ignore changes Useful for properties that are externally managed or should not trigger updates.

        Example::

            ["kubernetesVersion", "agentPoolProfiles"]
        '''
        result = self._values.get("ignore_changes")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def kubernetes_version(self) -> typing.Optional[builtins.str]:
        '''The Kubernetes version for the cluster.

        Example::

            "1.29.0"
        '''
        result = self._values.get("kubernetes_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def linux_profile(self) -> typing.Optional[AksClusterLinuxProfile]:
        '''The Linux profile for SSH access.'''
        result = self._values.get("linux_profile")
        return typing.cast(typing.Optional[AksClusterLinuxProfile], result)

    @builtins.property
    def network_profile(self) -> typing.Optional[AksClusterNetworkProfile]:
        '''The network configuration for the cluster.'''
        result = self._values.get("network_profile")
        return typing.cast(typing.Optional[AksClusterNetworkProfile], result)

    @builtins.property
    def node_resource_group(self) -> typing.Optional[builtins.str]:
        '''The name of the resource group for cluster nodes If not specified, Azure will auto-generate the name.'''
        result = self._values.get("node_resource_group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_issuer_profile(self) -> typing.Optional[AksClusterOidcIssuerProfile]:
        '''The OIDC issuer profile for workload identity.'''
        result = self._values.get("oidc_issuer_profile")
        return typing.cast(typing.Optional[AksClusterOidcIssuerProfile], result)

    @builtins.property
    def private_fqdn(self) -> typing.Optional[builtins.str]:
        '''The private FQDN for the cluster (read-only).'''
        result = self._values.get("private_fqdn")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def public_network_access(self) -> typing.Optional[builtins.str]:
        '''Whether the cluster is accessible from the public internet.

        Example::

            "Disabled"
        '''
        result = self._values.get("public_network_access")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def resource_group_id(self) -> typing.Optional[builtins.str]:
        '''Resource group ID where the AKS cluster will be created.'''
        result = self._values.get("resource_group_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def security_profile(self) -> typing.Optional["AksClusterSecurityProfile"]:
        '''The security profile for the cluster.'''
        result = self._values.get("security_profile")
        return typing.cast(typing.Optional["AksClusterSecurityProfile"], result)

    @builtins.property
    def service_principal_profile(
        self,
    ) -> typing.Optional["AksClusterServicePrincipalProfile"]:
        '''The service principal profile for the cluster.'''
        result = self._values.get("service_principal_profile")
        return typing.cast(typing.Optional["AksClusterServicePrincipalProfile"], result)

    @builtins.property
    def sku(self) -> typing.Optional["AksClusterSku"]:
        '''The SKU (pricing tier) for the AKS cluster.

        Example::

            { name: "Standard", tier: "Standard" }
        '''
        result = self._values.get("sku")
        return typing.cast(typing.Optional["AksClusterSku"], result)

    @builtins.property
    def storage_profile(self) -> typing.Optional["AksClusterStorageProfile"]:
        '''The storage profile for CSI drivers.'''
        result = self._values.get("storage_profile")
        return typing.cast(typing.Optional["AksClusterStorageProfile"], result)

    @builtins.property
    def support_plan(self) -> typing.Optional[builtins.str]:
        '''The support plan for the cluster.

        Example::

            "AKSLongTermSupport"
        '''
        result = self._values.get("support_plan")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def windows_profile(self) -> typing.Optional["AksClusterWindowsProfile"]:
        '''The Windows profile for Windows node pools.'''
        result = self._values.get("windows_profile")
        return typing.cast(typing.Optional["AksClusterWindowsProfile"], result)

    @builtins.property
    def workload_auto_scaler_profile(
        self,
    ) -> typing.Optional["AksClusterWorkloadAutoScalerProfile"]:
        '''The workload auto-scaler profile.'''
        result = self._values.get("workload_auto_scaler_profile")
        return typing.cast(typing.Optional["AksClusterWorkloadAutoScalerProfile"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterResourceReference",
    jsii_struct_bases=[],
    name_mapping={"id": "id"},
)
class AksClusterResourceReference:
    def __init__(self, *, id: typing.Optional[builtins.str] = None) -> None:
        '''Resource reference.

        :param id: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bd203f4d62a443fbd7df18c3e8a3c8b7d0bcb2ccf954ba2c9ac360e7287d1f78)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if id is not None:
            self._values["id"] = id

    @builtins.property
    def id(self) -> typing.Optional[builtins.str]:
        result = self._values.get("id")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterResourceReference(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterSecurityProfile",
    jsii_struct_bases=[],
    name_mapping={
        "azure_key_vault_kms": "azureKeyVaultKms",
        "defender": "defender",
        "image_cleaner": "imageCleaner",
        "workload_identity": "workloadIdentity",
    },
)
class AksClusterSecurityProfile:
    def __init__(
        self,
        *,
        azure_key_vault_kms: typing.Optional[typing.Union[AksClusterAzureKeyVaultKms, typing.Dict[builtins.str, typing.Any]]] = None,
        defender: typing.Optional[typing.Union[AksClusterDefenderSecurityMonitoring, typing.Dict[builtins.str, typing.Any]]] = None,
        image_cleaner: typing.Optional[typing.Union[AksClusterImageCleaner, typing.Dict[builtins.str, typing.Any]]] = None,
        workload_identity: typing.Optional[typing.Union["AksClusterWorkloadIdentity", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Security profile.

        :param azure_key_vault_kms: 
        :param defender: 
        :param image_cleaner: 
        :param workload_identity: 
        '''
        if isinstance(azure_key_vault_kms, dict):
            azure_key_vault_kms = AksClusterAzureKeyVaultKms(**azure_key_vault_kms)
        if isinstance(defender, dict):
            defender = AksClusterDefenderSecurityMonitoring(**defender)
        if isinstance(image_cleaner, dict):
            image_cleaner = AksClusterImageCleaner(**image_cleaner)
        if isinstance(workload_identity, dict):
            workload_identity = AksClusterWorkloadIdentity(**workload_identity)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c2e4820006e7c39242874301b84c362d8d5da6edfbcbba7cc26ce356dd5ee94c)
            check_type(argname="argument azure_key_vault_kms", value=azure_key_vault_kms, expected_type=type_hints["azure_key_vault_kms"])
            check_type(argname="argument defender", value=defender, expected_type=type_hints["defender"])
            check_type(argname="argument image_cleaner", value=image_cleaner, expected_type=type_hints["image_cleaner"])
            check_type(argname="argument workload_identity", value=workload_identity, expected_type=type_hints["workload_identity"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if azure_key_vault_kms is not None:
            self._values["azure_key_vault_kms"] = azure_key_vault_kms
        if defender is not None:
            self._values["defender"] = defender
        if image_cleaner is not None:
            self._values["image_cleaner"] = image_cleaner
        if workload_identity is not None:
            self._values["workload_identity"] = workload_identity

    @builtins.property
    def azure_key_vault_kms(self) -> typing.Optional[AksClusterAzureKeyVaultKms]:
        result = self._values.get("azure_key_vault_kms")
        return typing.cast(typing.Optional[AksClusterAzureKeyVaultKms], result)

    @builtins.property
    def defender(self) -> typing.Optional[AksClusterDefenderSecurityMonitoring]:
        result = self._values.get("defender")
        return typing.cast(typing.Optional[AksClusterDefenderSecurityMonitoring], result)

    @builtins.property
    def image_cleaner(self) -> typing.Optional[AksClusterImageCleaner]:
        result = self._values.get("image_cleaner")
        return typing.cast(typing.Optional[AksClusterImageCleaner], result)

    @builtins.property
    def workload_identity(self) -> typing.Optional["AksClusterWorkloadIdentity"]:
        result = self._values.get("workload_identity")
        return typing.cast(typing.Optional["AksClusterWorkloadIdentity"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterSecurityProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterServicePrincipalProfile",
    jsii_struct_bases=[],
    name_mapping={"client_id": "clientId", "secret": "secret"},
)
class AksClusterServicePrincipalProfile:
    def __init__(
        self,
        *,
        client_id: builtins.str,
        secret: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Service principal profile.

        :param client_id: 
        :param secret: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__196e8b319a4b1e1d9e197aa10d46963817d1c6263eee893714779913cf327318)
            check_type(argname="argument client_id", value=client_id, expected_type=type_hints["client_id"])
            check_type(argname="argument secret", value=secret, expected_type=type_hints["secret"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "client_id": client_id,
        }
        if secret is not None:
            self._values["secret"] = secret

    @builtins.property
    def client_id(self) -> builtins.str:
        result = self._values.get("client_id")
        assert result is not None, "Required property 'client_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def secret(self) -> typing.Optional[builtins.str]:
        result = self._values.get("secret")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterServicePrincipalProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterSku",
    jsii_struct_bases=[],
    name_mapping={"name": "name", "tier": "tier"},
)
class AksClusterSku:
    def __init__(
        self,
        *,
        name: typing.Optional[builtins.str] = None,
        tier: typing.Optional[builtins.str] = None,
    ) -> None:
        '''SKU for Azure Kubernetes Service.

        :param name: 
        :param tier: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c3bea3398400f1a12db673795b2e9d158ed01a7da52e96cd32bd46e9a2a715bb)
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument tier", value=tier, expected_type=type_hints["tier"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if name is not None:
            self._values["name"] = name
        if tier is not None:
            self._values["tier"] = tier

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tier(self) -> typing.Optional[builtins.str]:
        result = self._values.get("tier")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterSku(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterSnapshotController",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class AksClusterSnapshotController:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''Snapshot controller.

        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__707c21455361e0b337d109a2d2cc54e928dafbd5eb58725d2fc6282fcad2adce)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterSnapshotController(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterSshConfiguration",
    jsii_struct_bases=[],
    name_mapping={"public_keys": "publicKeys"},
)
class AksClusterSshConfiguration:
    def __init__(
        self,
        *,
        public_keys: typing.Sequence[typing.Union["AksClusterSshPublicKey", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''SSH configuration.

        :param public_keys: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__91521a35af54389a7d22c4bc215bed63deb208b8997113d8989e7f6b4a22e082)
            check_type(argname="argument public_keys", value=public_keys, expected_type=type_hints["public_keys"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "public_keys": public_keys,
        }

    @builtins.property
    def public_keys(self) -> typing.List["AksClusterSshPublicKey"]:
        result = self._values.get("public_keys")
        assert result is not None, "Required property 'public_keys' is missing"
        return typing.cast(typing.List["AksClusterSshPublicKey"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterSshConfiguration(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterSshPublicKey",
    jsii_struct_bases=[],
    name_mapping={"key_data": "keyData"},
)
class AksClusterSshPublicKey:
    def __init__(self, *, key_data: builtins.str) -> None:
        '''SSH public key.

        :param key_data: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70dcfc930eec0040d1f14c95f78f805defe450202bf2d91e6658c7e81f29bcc0)
            check_type(argname="argument key_data", value=key_data, expected_type=type_hints["key_data"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "key_data": key_data,
        }

    @builtins.property
    def key_data(self) -> builtins.str:
        result = self._values.get("key_data")
        assert result is not None, "Required property 'key_data' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterSshPublicKey(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterStorageProfile",
    jsii_struct_bases=[],
    name_mapping={
        "blob_csi_driver": "blobCSIDriver",
        "disk_csi_driver": "diskCSIDriver",
        "file_csi_driver": "fileCSIDriver",
        "snapshot_controller": "snapshotController",
    },
)
class AksClusterStorageProfile:
    def __init__(
        self,
        *,
        blob_csi_driver: typing.Optional[typing.Union[AksClusterBlobCSIDriver, typing.Dict[builtins.str, typing.Any]]] = None,
        disk_csi_driver: typing.Optional[typing.Union[AksClusterDiskCSIDriver, typing.Dict[builtins.str, typing.Any]]] = None,
        file_csi_driver: typing.Optional[typing.Union[AksClusterFileCSIDriver, typing.Dict[builtins.str, typing.Any]]] = None,
        snapshot_controller: typing.Optional[typing.Union[AksClusterSnapshotController, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Storage profile.

        :param blob_csi_driver: 
        :param disk_csi_driver: 
        :param file_csi_driver: 
        :param snapshot_controller: 
        '''
        if isinstance(blob_csi_driver, dict):
            blob_csi_driver = AksClusterBlobCSIDriver(**blob_csi_driver)
        if isinstance(disk_csi_driver, dict):
            disk_csi_driver = AksClusterDiskCSIDriver(**disk_csi_driver)
        if isinstance(file_csi_driver, dict):
            file_csi_driver = AksClusterFileCSIDriver(**file_csi_driver)
        if isinstance(snapshot_controller, dict):
            snapshot_controller = AksClusterSnapshotController(**snapshot_controller)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c4aec98be4aa2863e4603613df5718b36c575283a73e118d86e97bf6a19a4b23)
            check_type(argname="argument blob_csi_driver", value=blob_csi_driver, expected_type=type_hints["blob_csi_driver"])
            check_type(argname="argument disk_csi_driver", value=disk_csi_driver, expected_type=type_hints["disk_csi_driver"])
            check_type(argname="argument file_csi_driver", value=file_csi_driver, expected_type=type_hints["file_csi_driver"])
            check_type(argname="argument snapshot_controller", value=snapshot_controller, expected_type=type_hints["snapshot_controller"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if blob_csi_driver is not None:
            self._values["blob_csi_driver"] = blob_csi_driver
        if disk_csi_driver is not None:
            self._values["disk_csi_driver"] = disk_csi_driver
        if file_csi_driver is not None:
            self._values["file_csi_driver"] = file_csi_driver
        if snapshot_controller is not None:
            self._values["snapshot_controller"] = snapshot_controller

    @builtins.property
    def blob_csi_driver(self) -> typing.Optional[AksClusterBlobCSIDriver]:
        result = self._values.get("blob_csi_driver")
        return typing.cast(typing.Optional[AksClusterBlobCSIDriver], result)

    @builtins.property
    def disk_csi_driver(self) -> typing.Optional[AksClusterDiskCSIDriver]:
        result = self._values.get("disk_csi_driver")
        return typing.cast(typing.Optional[AksClusterDiskCSIDriver], result)

    @builtins.property
    def file_csi_driver(self) -> typing.Optional[AksClusterFileCSIDriver]:
        result = self._values.get("file_csi_driver")
        return typing.cast(typing.Optional[AksClusterFileCSIDriver], result)

    @builtins.property
    def snapshot_controller(self) -> typing.Optional[AksClusterSnapshotController]:
        result = self._values.get("snapshot_controller")
        return typing.cast(typing.Optional[AksClusterSnapshotController], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterStorageProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterSysctlConfig",
    jsii_struct_bases=[],
    name_mapping={
        "fs_aio_max_nr": "fsAioMaxNr",
        "fs_file_max": "fsFileMax",
        "fs_inotify_max_user_watches": "fsInotifyMaxUserWatches",
        "fs_nr_open": "fsNrOpen",
        "kernel_threads_max": "kernelThreadsMax",
        "net_core_netdev_max_backlog": "netCoreNetdevMaxBacklog",
        "net_core_optmem_max": "netCoreOptmemMax",
        "net_core_rmem_default": "netCoreRmemDefault",
        "net_core_rmem_max": "netCoreRmemMax",
        "net_core_somaxconn": "netCoreSomaxconn",
        "net_core_wmem_default": "netCoreWmemDefault",
        "net_core_wmem_max": "netCoreWmemMax",
        "net_ipv4_ip_local_port_range": "netIpv4IpLocalPortRange",
        "net_ipv4_neigh_default_gc_thresh1": "netIpv4NeighDefaultGcThresh1",
        "net_ipv4_neigh_default_gc_thresh2": "netIpv4NeighDefaultGcThresh2",
        "net_ipv4_neigh_default_gc_thresh3": "netIpv4NeighDefaultGcThresh3",
        "net_ipv4_tcp_fin_timeout": "netIpv4TcpFinTimeout",
        "net_ipv4_tcpkeepalive_intvl": "netIpv4TcpkeepaliveIntvl",
        "net_ipv4_tcp_keepalive_probes": "netIpv4TcpKeepaliveProbes",
        "net_ipv4_tcp_keepalive_time": "netIpv4TcpKeepaliveTime",
        "net_ipv4_tcp_max_syn_backlog": "netIpv4TcpMaxSynBacklog",
        "net_ipv4_tcp_tw_reuse": "netIpv4TcpTwReuse",
        "net_netfilter_nf_conntrack_buckets": "netNetfilterNfConntrackBuckets",
        "net_netfilter_nf_conntrack_max": "netNetfilterNfConntrackMax",
        "vm_max_map_count": "vmMaxMapCount",
        "vm_swappiness": "vmSwappiness",
        "vm_vfs_cache_pressure": "vmVfsCachePressure",
    },
)
class AksClusterSysctlConfig:
    def __init__(
        self,
        *,
        fs_aio_max_nr: typing.Optional[jsii.Number] = None,
        fs_file_max: typing.Optional[jsii.Number] = None,
        fs_inotify_max_user_watches: typing.Optional[jsii.Number] = None,
        fs_nr_open: typing.Optional[jsii.Number] = None,
        kernel_threads_max: typing.Optional[jsii.Number] = None,
        net_core_netdev_max_backlog: typing.Optional[jsii.Number] = None,
        net_core_optmem_max: typing.Optional[jsii.Number] = None,
        net_core_rmem_default: typing.Optional[jsii.Number] = None,
        net_core_rmem_max: typing.Optional[jsii.Number] = None,
        net_core_somaxconn: typing.Optional[jsii.Number] = None,
        net_core_wmem_default: typing.Optional[jsii.Number] = None,
        net_core_wmem_max: typing.Optional[jsii.Number] = None,
        net_ipv4_ip_local_port_range: typing.Optional[builtins.str] = None,
        net_ipv4_neigh_default_gc_thresh1: typing.Optional[jsii.Number] = None,
        net_ipv4_neigh_default_gc_thresh2: typing.Optional[jsii.Number] = None,
        net_ipv4_neigh_default_gc_thresh3: typing.Optional[jsii.Number] = None,
        net_ipv4_tcp_fin_timeout: typing.Optional[jsii.Number] = None,
        net_ipv4_tcpkeepalive_intvl: typing.Optional[jsii.Number] = None,
        net_ipv4_tcp_keepalive_probes: typing.Optional[jsii.Number] = None,
        net_ipv4_tcp_keepalive_time: typing.Optional[jsii.Number] = None,
        net_ipv4_tcp_max_syn_backlog: typing.Optional[jsii.Number] = None,
        net_ipv4_tcp_tw_reuse: typing.Optional[builtins.bool] = None,
        net_netfilter_nf_conntrack_buckets: typing.Optional[jsii.Number] = None,
        net_netfilter_nf_conntrack_max: typing.Optional[jsii.Number] = None,
        vm_max_map_count: typing.Optional[jsii.Number] = None,
        vm_swappiness: typing.Optional[jsii.Number] = None,
        vm_vfs_cache_pressure: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Sysctl configuration.

        :param fs_aio_max_nr: 
        :param fs_file_max: 
        :param fs_inotify_max_user_watches: 
        :param fs_nr_open: 
        :param kernel_threads_max: 
        :param net_core_netdev_max_backlog: 
        :param net_core_optmem_max: 
        :param net_core_rmem_default: 
        :param net_core_rmem_max: 
        :param net_core_somaxconn: 
        :param net_core_wmem_default: 
        :param net_core_wmem_max: 
        :param net_ipv4_ip_local_port_range: 
        :param net_ipv4_neigh_default_gc_thresh1: 
        :param net_ipv4_neigh_default_gc_thresh2: 
        :param net_ipv4_neigh_default_gc_thresh3: 
        :param net_ipv4_tcp_fin_timeout: 
        :param net_ipv4_tcpkeepalive_intvl: 
        :param net_ipv4_tcp_keepalive_probes: 
        :param net_ipv4_tcp_keepalive_time: 
        :param net_ipv4_tcp_max_syn_backlog: 
        :param net_ipv4_tcp_tw_reuse: 
        :param net_netfilter_nf_conntrack_buckets: 
        :param net_netfilter_nf_conntrack_max: 
        :param vm_max_map_count: 
        :param vm_swappiness: 
        :param vm_vfs_cache_pressure: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__43af6eba048e638aa04c5127875ed96383f9cde8f9dd7fd46f33a26354f337aa)
            check_type(argname="argument fs_aio_max_nr", value=fs_aio_max_nr, expected_type=type_hints["fs_aio_max_nr"])
            check_type(argname="argument fs_file_max", value=fs_file_max, expected_type=type_hints["fs_file_max"])
            check_type(argname="argument fs_inotify_max_user_watches", value=fs_inotify_max_user_watches, expected_type=type_hints["fs_inotify_max_user_watches"])
            check_type(argname="argument fs_nr_open", value=fs_nr_open, expected_type=type_hints["fs_nr_open"])
            check_type(argname="argument kernel_threads_max", value=kernel_threads_max, expected_type=type_hints["kernel_threads_max"])
            check_type(argname="argument net_core_netdev_max_backlog", value=net_core_netdev_max_backlog, expected_type=type_hints["net_core_netdev_max_backlog"])
            check_type(argname="argument net_core_optmem_max", value=net_core_optmem_max, expected_type=type_hints["net_core_optmem_max"])
            check_type(argname="argument net_core_rmem_default", value=net_core_rmem_default, expected_type=type_hints["net_core_rmem_default"])
            check_type(argname="argument net_core_rmem_max", value=net_core_rmem_max, expected_type=type_hints["net_core_rmem_max"])
            check_type(argname="argument net_core_somaxconn", value=net_core_somaxconn, expected_type=type_hints["net_core_somaxconn"])
            check_type(argname="argument net_core_wmem_default", value=net_core_wmem_default, expected_type=type_hints["net_core_wmem_default"])
            check_type(argname="argument net_core_wmem_max", value=net_core_wmem_max, expected_type=type_hints["net_core_wmem_max"])
            check_type(argname="argument net_ipv4_ip_local_port_range", value=net_ipv4_ip_local_port_range, expected_type=type_hints["net_ipv4_ip_local_port_range"])
            check_type(argname="argument net_ipv4_neigh_default_gc_thresh1", value=net_ipv4_neigh_default_gc_thresh1, expected_type=type_hints["net_ipv4_neigh_default_gc_thresh1"])
            check_type(argname="argument net_ipv4_neigh_default_gc_thresh2", value=net_ipv4_neigh_default_gc_thresh2, expected_type=type_hints["net_ipv4_neigh_default_gc_thresh2"])
            check_type(argname="argument net_ipv4_neigh_default_gc_thresh3", value=net_ipv4_neigh_default_gc_thresh3, expected_type=type_hints["net_ipv4_neigh_default_gc_thresh3"])
            check_type(argname="argument net_ipv4_tcp_fin_timeout", value=net_ipv4_tcp_fin_timeout, expected_type=type_hints["net_ipv4_tcp_fin_timeout"])
            check_type(argname="argument net_ipv4_tcpkeepalive_intvl", value=net_ipv4_tcpkeepalive_intvl, expected_type=type_hints["net_ipv4_tcpkeepalive_intvl"])
            check_type(argname="argument net_ipv4_tcp_keepalive_probes", value=net_ipv4_tcp_keepalive_probes, expected_type=type_hints["net_ipv4_tcp_keepalive_probes"])
            check_type(argname="argument net_ipv4_tcp_keepalive_time", value=net_ipv4_tcp_keepalive_time, expected_type=type_hints["net_ipv4_tcp_keepalive_time"])
            check_type(argname="argument net_ipv4_tcp_max_syn_backlog", value=net_ipv4_tcp_max_syn_backlog, expected_type=type_hints["net_ipv4_tcp_max_syn_backlog"])
            check_type(argname="argument net_ipv4_tcp_tw_reuse", value=net_ipv4_tcp_tw_reuse, expected_type=type_hints["net_ipv4_tcp_tw_reuse"])
            check_type(argname="argument net_netfilter_nf_conntrack_buckets", value=net_netfilter_nf_conntrack_buckets, expected_type=type_hints["net_netfilter_nf_conntrack_buckets"])
            check_type(argname="argument net_netfilter_nf_conntrack_max", value=net_netfilter_nf_conntrack_max, expected_type=type_hints["net_netfilter_nf_conntrack_max"])
            check_type(argname="argument vm_max_map_count", value=vm_max_map_count, expected_type=type_hints["vm_max_map_count"])
            check_type(argname="argument vm_swappiness", value=vm_swappiness, expected_type=type_hints["vm_swappiness"])
            check_type(argname="argument vm_vfs_cache_pressure", value=vm_vfs_cache_pressure, expected_type=type_hints["vm_vfs_cache_pressure"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if fs_aio_max_nr is not None:
            self._values["fs_aio_max_nr"] = fs_aio_max_nr
        if fs_file_max is not None:
            self._values["fs_file_max"] = fs_file_max
        if fs_inotify_max_user_watches is not None:
            self._values["fs_inotify_max_user_watches"] = fs_inotify_max_user_watches
        if fs_nr_open is not None:
            self._values["fs_nr_open"] = fs_nr_open
        if kernel_threads_max is not None:
            self._values["kernel_threads_max"] = kernel_threads_max
        if net_core_netdev_max_backlog is not None:
            self._values["net_core_netdev_max_backlog"] = net_core_netdev_max_backlog
        if net_core_optmem_max is not None:
            self._values["net_core_optmem_max"] = net_core_optmem_max
        if net_core_rmem_default is not None:
            self._values["net_core_rmem_default"] = net_core_rmem_default
        if net_core_rmem_max is not None:
            self._values["net_core_rmem_max"] = net_core_rmem_max
        if net_core_somaxconn is not None:
            self._values["net_core_somaxconn"] = net_core_somaxconn
        if net_core_wmem_default is not None:
            self._values["net_core_wmem_default"] = net_core_wmem_default
        if net_core_wmem_max is not None:
            self._values["net_core_wmem_max"] = net_core_wmem_max
        if net_ipv4_ip_local_port_range is not None:
            self._values["net_ipv4_ip_local_port_range"] = net_ipv4_ip_local_port_range
        if net_ipv4_neigh_default_gc_thresh1 is not None:
            self._values["net_ipv4_neigh_default_gc_thresh1"] = net_ipv4_neigh_default_gc_thresh1
        if net_ipv4_neigh_default_gc_thresh2 is not None:
            self._values["net_ipv4_neigh_default_gc_thresh2"] = net_ipv4_neigh_default_gc_thresh2
        if net_ipv4_neigh_default_gc_thresh3 is not None:
            self._values["net_ipv4_neigh_default_gc_thresh3"] = net_ipv4_neigh_default_gc_thresh3
        if net_ipv4_tcp_fin_timeout is not None:
            self._values["net_ipv4_tcp_fin_timeout"] = net_ipv4_tcp_fin_timeout
        if net_ipv4_tcpkeepalive_intvl is not None:
            self._values["net_ipv4_tcpkeepalive_intvl"] = net_ipv4_tcpkeepalive_intvl
        if net_ipv4_tcp_keepalive_probes is not None:
            self._values["net_ipv4_tcp_keepalive_probes"] = net_ipv4_tcp_keepalive_probes
        if net_ipv4_tcp_keepalive_time is not None:
            self._values["net_ipv4_tcp_keepalive_time"] = net_ipv4_tcp_keepalive_time
        if net_ipv4_tcp_max_syn_backlog is not None:
            self._values["net_ipv4_tcp_max_syn_backlog"] = net_ipv4_tcp_max_syn_backlog
        if net_ipv4_tcp_tw_reuse is not None:
            self._values["net_ipv4_tcp_tw_reuse"] = net_ipv4_tcp_tw_reuse
        if net_netfilter_nf_conntrack_buckets is not None:
            self._values["net_netfilter_nf_conntrack_buckets"] = net_netfilter_nf_conntrack_buckets
        if net_netfilter_nf_conntrack_max is not None:
            self._values["net_netfilter_nf_conntrack_max"] = net_netfilter_nf_conntrack_max
        if vm_max_map_count is not None:
            self._values["vm_max_map_count"] = vm_max_map_count
        if vm_swappiness is not None:
            self._values["vm_swappiness"] = vm_swappiness
        if vm_vfs_cache_pressure is not None:
            self._values["vm_vfs_cache_pressure"] = vm_vfs_cache_pressure

    @builtins.property
    def fs_aio_max_nr(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("fs_aio_max_nr")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def fs_file_max(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("fs_file_max")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def fs_inotify_max_user_watches(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("fs_inotify_max_user_watches")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def fs_nr_open(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("fs_nr_open")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def kernel_threads_max(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("kernel_threads_max")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_netdev_max_backlog(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_netdev_max_backlog")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_optmem_max(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_optmem_max")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_rmem_default(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_rmem_default")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_rmem_max(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_rmem_max")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_somaxconn(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_somaxconn")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_wmem_default(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_wmem_default")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_core_wmem_max(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_core_wmem_max")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_ip_local_port_range(self) -> typing.Optional[builtins.str]:
        result = self._values.get("net_ipv4_ip_local_port_range")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def net_ipv4_neigh_default_gc_thresh1(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_neigh_default_gc_thresh1")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_neigh_default_gc_thresh2(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_neigh_default_gc_thresh2")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_neigh_default_gc_thresh3(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_neigh_default_gc_thresh3")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_tcp_fin_timeout(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_tcp_fin_timeout")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_tcpkeepalive_intvl(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_tcpkeepalive_intvl")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_tcp_keepalive_probes(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_tcp_keepalive_probes")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_tcp_keepalive_time(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_tcp_keepalive_time")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_tcp_max_syn_backlog(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_ipv4_tcp_max_syn_backlog")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_ipv4_tcp_tw_reuse(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("net_ipv4_tcp_tw_reuse")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def net_netfilter_nf_conntrack_buckets(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_netfilter_nf_conntrack_buckets")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def net_netfilter_nf_conntrack_max(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("net_netfilter_nf_conntrack_max")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def vm_max_map_count(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("vm_max_map_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def vm_swappiness(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("vm_swappiness")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def vm_vfs_cache_pressure(self) -> typing.Optional[jsii.Number]:
        result = self._values.get("vm_vfs_cache_pressure")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterSysctlConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterVerticalPodAutoscaler",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class AksClusterVerticalPodAutoscaler:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''Vertical pod autoscaler.

        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bd1834d21bbc620fb6c84cc0feb3971e5a7c099ba2d885e479f9dc0cea67ee6f)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterVerticalPodAutoscaler(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterWindowsProfile",
    jsii_struct_bases=[],
    name_mapping={
        "admin_username": "adminUsername",
        "admin_password": "adminPassword",
        "enable_csi_proxy": "enableCSIProxy",
        "gmsa_profile": "gmsaProfile",
        "license_type": "licenseType",
    },
)
class AksClusterWindowsProfile:
    def __init__(
        self,
        *,
        admin_username: builtins.str,
        admin_password: typing.Optional[builtins.str] = None,
        enable_csi_proxy: typing.Optional[builtins.bool] = None,
        gmsa_profile: typing.Optional[typing.Union[AksClusterGmsaProfile, typing.Dict[builtins.str, typing.Any]]] = None,
        license_type: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Windows profile.

        :param admin_username: 
        :param admin_password: 
        :param enable_csi_proxy: 
        :param gmsa_profile: 
        :param license_type: 
        '''
        if isinstance(gmsa_profile, dict):
            gmsa_profile = AksClusterGmsaProfile(**gmsa_profile)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__94f35baefd65bc096feb737adb69a479310f150e8806458a5e5ec89e5e2c4145)
            check_type(argname="argument admin_username", value=admin_username, expected_type=type_hints["admin_username"])
            check_type(argname="argument admin_password", value=admin_password, expected_type=type_hints["admin_password"])
            check_type(argname="argument enable_csi_proxy", value=enable_csi_proxy, expected_type=type_hints["enable_csi_proxy"])
            check_type(argname="argument gmsa_profile", value=gmsa_profile, expected_type=type_hints["gmsa_profile"])
            check_type(argname="argument license_type", value=license_type, expected_type=type_hints["license_type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "admin_username": admin_username,
        }
        if admin_password is not None:
            self._values["admin_password"] = admin_password
        if enable_csi_proxy is not None:
            self._values["enable_csi_proxy"] = enable_csi_proxy
        if gmsa_profile is not None:
            self._values["gmsa_profile"] = gmsa_profile
        if license_type is not None:
            self._values["license_type"] = license_type

    @builtins.property
    def admin_username(self) -> builtins.str:
        result = self._values.get("admin_username")
        assert result is not None, "Required property 'admin_username' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def admin_password(self) -> typing.Optional[builtins.str]:
        result = self._values.get("admin_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def enable_csi_proxy(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_csi_proxy")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def gmsa_profile(self) -> typing.Optional[AksClusterGmsaProfile]:
        result = self._values.get("gmsa_profile")
        return typing.cast(typing.Optional[AksClusterGmsaProfile], result)

    @builtins.property
    def license_type(self) -> typing.Optional[builtins.str]:
        result = self._values.get("license_type")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterWindowsProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterWorkloadAutoScalerProfile",
    jsii_struct_bases=[],
    name_mapping={"keda": "keda", "vertical_pod_autoscaler": "verticalPodAutoscaler"},
)
class AksClusterWorkloadAutoScalerProfile:
    def __init__(
        self,
        *,
        keda: typing.Optional[typing.Union[AksClusterKeda, typing.Dict[builtins.str, typing.Any]]] = None,
        vertical_pod_autoscaler: typing.Optional[typing.Union[AksClusterVerticalPodAutoscaler, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Workload auto-scaler profile.

        :param keda: 
        :param vertical_pod_autoscaler: 
        '''
        if isinstance(keda, dict):
            keda = AksClusterKeda(**keda)
        if isinstance(vertical_pod_autoscaler, dict):
            vertical_pod_autoscaler = AksClusterVerticalPodAutoscaler(**vertical_pod_autoscaler)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b669d856557e7356e859c33e9b613b745678b50fc01880aebc6f4b4b6b01dae2)
            check_type(argname="argument keda", value=keda, expected_type=type_hints["keda"])
            check_type(argname="argument vertical_pod_autoscaler", value=vertical_pod_autoscaler, expected_type=type_hints["vertical_pod_autoscaler"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if keda is not None:
            self._values["keda"] = keda
        if vertical_pod_autoscaler is not None:
            self._values["vertical_pod_autoscaler"] = vertical_pod_autoscaler

    @builtins.property
    def keda(self) -> typing.Optional[AksClusterKeda]:
        result = self._values.get("keda")
        return typing.cast(typing.Optional[AksClusterKeda], result)

    @builtins.property
    def vertical_pod_autoscaler(
        self,
    ) -> typing.Optional[AksClusterVerticalPodAutoscaler]:
        result = self._values.get("vertical_pod_autoscaler")
        return typing.cast(typing.Optional[AksClusterVerticalPodAutoscaler], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterWorkloadAutoScalerProfile(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.azure_aks.AksClusterWorkloadIdentity",
    jsii_struct_bases=[],
    name_mapping={"enabled": "enabled"},
)
class AksClusterWorkloadIdentity:
    def __init__(self, *, enabled: typing.Optional[builtins.bool] = None) -> None:
        '''Workload identity configuration.

        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d05c02a9088b204b12ce8e074222a127fb14a2d40efccf18a7a7d3f6e7a779e1)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if enabled is not None:
            self._values["enabled"] = enabled

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AksClusterWorkloadIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AksCluster",
    "AksClusterAadProfile",
    "AksClusterAddonProfile",
    "AksClusterAgentPoolProfile",
    "AksClusterApiServerAccessProfile",
    "AksClusterAutoScalerProfile",
    "AksClusterAzureKeyVaultKms",
    "AksClusterBlobCSIDriver",
    "AksClusterBody",
    "AksClusterBodyProperties",
    "AksClusterDefenderSecurityMonitoring",
    "AksClusterDiskCSIDriver",
    "AksClusterEffectiveOutboundIP",
    "AksClusterFileCSIDriver",
    "AksClusterGmsaProfile",
    "AksClusterHttpProxyConfig",
    "AksClusterIdentity",
    "AksClusterImageCleaner",
    "AksClusterKeda",
    "AksClusterKubeletConfig",
    "AksClusterLinuxOSConfig",
    "AksClusterLinuxProfile",
    "AksClusterLoadBalancerProfile",
    "AksClusterManagedOutboundIPProfile",
    "AksClusterManagedOutboundIPs",
    "AksClusterMonitoringOptions",
    "AksClusterNatGatewayProfile",
    "AksClusterNetworkProfile",
    "AksClusterOidcIssuerProfile",
    "AksClusterOutboundIPPrefixes",
    "AksClusterOutboundIPs",
    "AksClusterProps",
    "AksClusterResourceReference",
    "AksClusterSecurityProfile",
    "AksClusterServicePrincipalProfile",
    "AksClusterSku",
    "AksClusterSnapshotController",
    "AksClusterSshConfiguration",
    "AksClusterSshPublicKey",
    "AksClusterStorageProfile",
    "AksClusterSysctlConfig",
    "AksClusterVerticalPodAutoscaler",
    "AksClusterWindowsProfile",
    "AksClusterWorkloadAutoScalerProfile",
    "AksClusterWorkloadIdentity",
]

publication.publish()

def _typecheckingstub__1d287fdfd0aef1ba7e5ef73c249cce142f68d09b133fc16d778c5e80c8640791(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    agent_pool_profiles: typing.Sequence[typing.Union[AksClusterAgentPoolProfile, typing.Dict[builtins.str, typing.Any]]],
    dns_prefix: builtins.str,
    aad_profile: typing.Optional[typing.Union[AksClusterAadProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    addon_profiles: typing.Optional[typing.Mapping[builtins.str, typing.Union[AksClusterAddonProfile, typing.Dict[builtins.str, typing.Any]]]] = None,
    api_server_access_profile: typing.Optional[typing.Union[AksClusterApiServerAccessProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_scaler_profile: typing.Optional[typing.Union[AksClusterAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    disable_local_accounts: typing.Optional[builtins.bool] = None,
    disk_encryption_set_id: typing.Optional[builtins.str] = None,
    enable_rbac: typing.Optional[builtins.bool] = None,
    fqdn: typing.Optional[builtins.str] = None,
    http_proxy_config: typing.Optional[typing.Union[AksClusterHttpProxyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[AksClusterIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    kubernetes_version: typing.Optional[builtins.str] = None,
    linux_profile: typing.Optional[typing.Union[AksClusterLinuxProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    network_profile: typing.Optional[typing.Union[AksClusterNetworkProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    node_resource_group: typing.Optional[builtins.str] = None,
    oidc_issuer_profile: typing.Optional[typing.Union[AksClusterOidcIssuerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    private_fqdn: typing.Optional[builtins.str] = None,
    public_network_access: typing.Optional[builtins.str] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    security_profile: typing.Optional[typing.Union[AksClusterSecurityProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    service_principal_profile: typing.Optional[typing.Union[AksClusterServicePrincipalProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    sku: typing.Optional[typing.Union[AksClusterSku, typing.Dict[builtins.str, typing.Any]]] = None,
    storage_profile: typing.Optional[typing.Union[AksClusterStorageProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    support_plan: typing.Optional[builtins.str] = None,
    windows_profile: typing.Optional[typing.Union[AksClusterWindowsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    workload_auto_scaler_profile: typing.Optional[typing.Union[AksClusterWorkloadAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__22175093416726718ef82aa45e47267e8e5951f976505e616eb946f6922de479(
    action_group_id: builtins.str,
    workspace_id: typing.Optional[builtins.str] = None,
    *,
    enable_deletion_alert: typing.Optional[builtins.bool] = None,
    enable_failed_pod_alert: typing.Optional[builtins.bool] = None,
    enable_node_cpu_alert: typing.Optional[builtins.bool] = None,
    enable_node_memory_alert: typing.Optional[builtins.bool] = None,
    failed_pod_alert_severity: typing.Optional[jsii.Number] = None,
    failed_pod_threshold: typing.Optional[jsii.Number] = None,
    node_cpu_alert_severity: typing.Optional[jsii.Number] = None,
    node_cpu_threshold: typing.Optional[jsii.Number] = None,
    node_memory_alert_severity: typing.Optional[jsii.Number] = None,
    node_memory_threshold: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ba4d615c49692c85ebd809eeed9c003424add70c06d72d333f12609d395ef345(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4d2b71e9afe17e71358af1e7947ca82bc7c1bb76d7fe786ea9e2e4319d92cbe3(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26bff6dd6a3426004dc9c10d17b9417c494437331cf5c06a3da02b0d0fcf8bad(
    key: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bdcbdf8e40c590e406a17d41599b96e365936e2e2fda1dfc8b8bc1f0e631f849(
    *,
    admin_group_object_i_ds: typing.Optional[typing.Sequence[builtins.str]] = None,
    client_app_id: typing.Optional[builtins.str] = None,
    enable_azure_rbac: typing.Optional[builtins.bool] = None,
    managed: typing.Optional[builtins.bool] = None,
    server_app_id: typing.Optional[builtins.str] = None,
    server_app_secret: typing.Optional[builtins.str] = None,
    tenant_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1b8acfa20a2d86195ce86c0dddb47aefc714060f974c49527be77ba3d7bffbf2(
    *,
    enabled: builtins.bool,
    config: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5a63ac30d56de20d2eb235afe483c75902391cde9814867a631d6ac5ac306d87(
    *,
    name: builtins.str,
    vm_size: builtins.str,
    availability_zones: typing.Optional[typing.Sequence[builtins.str]] = None,
    count: typing.Optional[jsii.Number] = None,
    enable_auto_scaling: typing.Optional[builtins.bool] = None,
    enable_encryption_at_host: typing.Optional[builtins.bool] = None,
    enable_fips: typing.Optional[builtins.bool] = None,
    enable_node_public_ip: typing.Optional[builtins.bool] = None,
    enable_ultra_ssd: typing.Optional[builtins.bool] = None,
    kubelet_config: typing.Optional[typing.Union[AksClusterKubeletConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    linux_os_config: typing.Optional[typing.Union[AksClusterLinuxOSConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    max_count: typing.Optional[jsii.Number] = None,
    max_pods: typing.Optional[jsii.Number] = None,
    min_count: typing.Optional[jsii.Number] = None,
    mode: typing.Optional[builtins.str] = None,
    node_labels: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    node_public_ip_prefix_id: typing.Optional[builtins.str] = None,
    node_taints: typing.Optional[typing.Sequence[builtins.str]] = None,
    os_disk_size_gb: typing.Optional[jsii.Number] = None,
    os_disk_type: typing.Optional[builtins.str] = None,
    os_type: typing.Optional[builtins.str] = None,
    pod_subnet_id: typing.Optional[builtins.str] = None,
    scale_set_eviction_policy: typing.Optional[builtins.str] = None,
    scale_set_priority: typing.Optional[builtins.str] = None,
    spot_max_price: typing.Optional[jsii.Number] = None,
    type: typing.Optional[builtins.str] = None,
    vnet_subnet_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__85d2b0bd7162a5ea2d58f2fc9e22085f011a515adaa110f4b1fbef38db530190(
    *,
    authorized_ip_ranges: typing.Optional[typing.Sequence[builtins.str]] = None,
    disable_run_command: typing.Optional[builtins.bool] = None,
    enable_private_cluster: typing.Optional[builtins.bool] = None,
    enable_private_cluster_public_fqdn: typing.Optional[builtins.bool] = None,
    enable_vnet_integration: typing.Optional[builtins.bool] = None,
    private_dns_zone: typing.Optional[builtins.str] = None,
    subnet_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5f28492551fcbf758be78cfd663d2e5ae185c8437ccaba11c7c849be6cb10315(
    *,
    balance_similar_node_groups: typing.Optional[builtins.str] = None,
    expander: typing.Optional[builtins.str] = None,
    max_empty_bulk_delete: typing.Optional[builtins.str] = None,
    max_graceful_termination_sec: typing.Optional[builtins.str] = None,
    max_node_provision_time: typing.Optional[builtins.str] = None,
    max_total_unready_percentage: typing.Optional[builtins.str] = None,
    new_pod_scale_up_delay: typing.Optional[builtins.str] = None,
    ok_total_unready_count: typing.Optional[builtins.str] = None,
    scale_down_delay_after_add: typing.Optional[builtins.str] = None,
    scale_down_delay_after_delete: typing.Optional[builtins.str] = None,
    scale_down_delay_after_failure: typing.Optional[builtins.str] = None,
    scale_down_unneeded_time: typing.Optional[builtins.str] = None,
    scale_down_unready_time: typing.Optional[builtins.str] = None,
    scale_down_utilization_threshold: typing.Optional[builtins.str] = None,
    scan_interval: typing.Optional[builtins.str] = None,
    skip_nodes_with_local_storage: typing.Optional[builtins.str] = None,
    skip_nodes_with_system_pods: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__da543fdbfd1a1bdbb7da17f521dc3eae8d77779621c27db8017f62820523ee7b(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    key_id: typing.Optional[builtins.str] = None,
    key_vault_network_access: typing.Optional[builtins.str] = None,
    key_vault_resource_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed38fbd794526e83f9f2b3e7fb1ba17008dbed0bc5754f6e89775ed3dfe0e853(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__baf743af72de779ee5955acf7b022ed77e8b9ba636c6421f6eef46740525703c(
    *,
    location: builtins.str,
    properties: typing.Union[AksClusterBodyProperties, typing.Dict[builtins.str, typing.Any]],
    identity: typing.Optional[typing.Union[AksClusterIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    sku: typing.Optional[typing.Union[AksClusterSku, typing.Dict[builtins.str, typing.Any]]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__806f1127fedc29edc4713bdb6db5e7be4b4355e0a08759a24850d84ca7e16374(
    *,
    agent_pool_profiles: typing.Sequence[typing.Union[AksClusterAgentPoolProfile, typing.Dict[builtins.str, typing.Any]]],
    dns_prefix: builtins.str,
    aad_profile: typing.Optional[typing.Union[AksClusterAadProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    addon_profiles: typing.Optional[typing.Mapping[builtins.str, typing.Union[AksClusterAddonProfile, typing.Dict[builtins.str, typing.Any]]]] = None,
    api_server_access_profile: typing.Optional[typing.Union[AksClusterApiServerAccessProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_scaler_profile: typing.Optional[typing.Union[AksClusterAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    disable_local_accounts: typing.Optional[builtins.bool] = None,
    disk_encryption_set_id: typing.Optional[builtins.str] = None,
    enable_rbac: typing.Optional[builtins.bool] = None,
    fqdn: typing.Optional[builtins.str] = None,
    http_proxy_config: typing.Optional[typing.Union[AksClusterHttpProxyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    kubernetes_version: typing.Optional[builtins.str] = None,
    linux_profile: typing.Optional[typing.Union[AksClusterLinuxProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    network_profile: typing.Optional[typing.Union[AksClusterNetworkProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    node_resource_group: typing.Optional[builtins.str] = None,
    oidc_issuer_profile: typing.Optional[typing.Union[AksClusterOidcIssuerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    private_fqdn: typing.Optional[builtins.str] = None,
    public_network_access: typing.Optional[builtins.str] = None,
    security_profile: typing.Optional[typing.Union[AksClusterSecurityProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    service_principal_profile: typing.Optional[typing.Union[AksClusterServicePrincipalProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    storage_profile: typing.Optional[typing.Union[AksClusterStorageProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    support_plan: typing.Optional[builtins.str] = None,
    windows_profile: typing.Optional[typing.Union[AksClusterWindowsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    workload_auto_scaler_profile: typing.Optional[typing.Union[AksClusterWorkloadAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7a248ddfdc5022e908f5100def54d6d797e4100c8ce486bfd45d29b04ee18f51(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    log_analytics_workspace_resource_id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__62513b02011a704d7b04fbabaf5987134079273661e24d74574b80aaa2461368(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    version: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1c105913fa15501b1a02038d0fc7f3f6918bdb73da1284f625eab123171d1af(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ee47928b98ee4db355f8bfec9d2449dc2c1cdba415a5bd80da648590b009d236(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a03ea030a627e1e6383fdd3bba22dc6c716fc5487479996942ce55d7d266a8db(
    *,
    dns_server: typing.Optional[builtins.str] = None,
    enabled: typing.Optional[builtins.bool] = None,
    root_domain_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94a6f8945b7dffe36c03aa585ef64ee053869dc6d717976f2391bcd72a748eaf(
    *,
    http_proxy: typing.Optional[builtins.str] = None,
    https_proxy: typing.Optional[builtins.str] = None,
    no_proxy: typing.Optional[typing.Sequence[builtins.str]] = None,
    trusted_ca: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a4b4c4123f350176a104d66cda6a4ce251fcbf6b1cc8d07ee95b83be6e02cde(
    *,
    type: builtins.str,
    user_assigned_identities: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__415d44f954f0469ae478fc6a3dcc8ca0c2c24a27384828d791256677454b3b88(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    interval_hours: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__54fa7b2f0ede20ec8771cb8a7b343a0be4604a7aa233da0f10da505fdb7316be(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8df6b00212e1fa9e88180561c58771f27a28e79463dafa623342e2c2bfb14dbd(
    *,
    allowed_unsafe_sysctls: typing.Optional[typing.Sequence[builtins.str]] = None,
    container_log_max_files: typing.Optional[jsii.Number] = None,
    container_log_max_size_mb: typing.Optional[jsii.Number] = None,
    cpu_cfs_quota: typing.Optional[builtins.bool] = None,
    cpu_cfs_quota_period: typing.Optional[builtins.str] = None,
    cpu_manager_policy: typing.Optional[builtins.str] = None,
    fail_swap_on: typing.Optional[builtins.bool] = None,
    image_gc_high_threshold: typing.Optional[jsii.Number] = None,
    image_gc_low_threshold: typing.Optional[jsii.Number] = None,
    pod_max_pids: typing.Optional[jsii.Number] = None,
    topology_manager_policy: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__908b895e22d866e935a203fdf1e1777c0ce22cf373c92d034fb9a2fee6285ba2(
    *,
    swap_file_size_mb: typing.Optional[jsii.Number] = None,
    sysctls: typing.Optional[typing.Union[AksClusterSysctlConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    transparent_huge_page_defrag: typing.Optional[builtins.str] = None,
    transparent_huge_page_enabled: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a3cb4f3fc81efda6c93459507bb8de667e992775d04ec1302dd23e4158321fdf(
    *,
    admin_username: builtins.str,
    ssh: typing.Union[AksClusterSshConfiguration, typing.Dict[builtins.str, typing.Any]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__357da0f7eaa143f5db73e6fc0ac9b9cc6a77fb2054cfc20fe1758157082245b8(
    *,
    allocated_outbound_ports: typing.Optional[jsii.Number] = None,
    effective_outbound_i_ps: typing.Optional[typing.Sequence[typing.Union[AksClusterEffectiveOutboundIP, typing.Dict[builtins.str, typing.Any]]]] = None,
    enable_multiple_standard_load_balancers: typing.Optional[builtins.bool] = None,
    idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    managed_outbound_i_ps: typing.Optional[typing.Union[AksClusterManagedOutboundIPs, typing.Dict[builtins.str, typing.Any]]] = None,
    outbound_ip_prefixes: typing.Optional[typing.Union[AksClusterOutboundIPPrefixes, typing.Dict[builtins.str, typing.Any]]] = None,
    outbound_i_ps: typing.Optional[typing.Union[AksClusterOutboundIPs, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eb189f46d2da79ff38dadb2d3f04cbff91cc560e143c95616cae248d2e7015cf(
    *,
    count: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7ea8913e4155425befcece8115d2f020f72973a7c8f310572d7feb3594d557a8(
    *,
    count: typing.Optional[jsii.Number] = None,
    count_i_pv6: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__700a5cfbc9d5eae92ed4cd7f7feab013900b7e322beef7fe90331d2b6342c0b7(
    *,
    enable_deletion_alert: typing.Optional[builtins.bool] = None,
    enable_failed_pod_alert: typing.Optional[builtins.bool] = None,
    enable_node_cpu_alert: typing.Optional[builtins.bool] = None,
    enable_node_memory_alert: typing.Optional[builtins.bool] = None,
    failed_pod_alert_severity: typing.Optional[jsii.Number] = None,
    failed_pod_threshold: typing.Optional[jsii.Number] = None,
    node_cpu_alert_severity: typing.Optional[jsii.Number] = None,
    node_cpu_threshold: typing.Optional[jsii.Number] = None,
    node_memory_alert_severity: typing.Optional[jsii.Number] = None,
    node_memory_threshold: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__68ff60799c0f080481eba0dabbbecd91b80859476cbe8c37e6e8b15029eb7c25(
    *,
    effective_outbound_i_ps: typing.Optional[typing.Sequence[typing.Union[AksClusterEffectiveOutboundIP, typing.Dict[builtins.str, typing.Any]]]] = None,
    idle_timeout_in_minutes: typing.Optional[jsii.Number] = None,
    managed_outbound_ip_profile: typing.Optional[typing.Union[AksClusterManagedOutboundIPProfile, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__967e08c3da7ceaca31f4b4e6ff5c59af5d1e1570e7c97f1db2336f604ae62ed4(
    *,
    dns_service_ip: typing.Optional[builtins.str] = None,
    docker_bridge_cidr: typing.Optional[builtins.str] = None,
    ip_families: typing.Optional[typing.Sequence[builtins.str]] = None,
    load_balancer_profile: typing.Optional[typing.Union[AksClusterLoadBalancerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    load_balancer_sku: typing.Optional[builtins.str] = None,
    nat_gateway_profile: typing.Optional[typing.Union[AksClusterNatGatewayProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    network_mode: typing.Optional[builtins.str] = None,
    network_plugin: typing.Optional[builtins.str] = None,
    network_policy: typing.Optional[builtins.str] = None,
    outbound_type: typing.Optional[builtins.str] = None,
    pod_cidr: typing.Optional[builtins.str] = None,
    pod_cidrs: typing.Optional[typing.Sequence[builtins.str]] = None,
    service_cidr: typing.Optional[builtins.str] = None,
    service_cidrs: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0465c1752edb538cfb5e9cb855c50af83e323a1c21ff4731e82a717383e0d9fc(
    *,
    enabled: typing.Optional[builtins.bool] = None,
    issuer_url: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a61fa88e1f0ddede724539f453ce09cd4adf89c469170e9b6e8aba9e4f305fa(
    *,
    public_ip_prefixes: typing.Optional[typing.Sequence[typing.Union[AksClusterResourceReference, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9f3f3ce8d65ac44601439a466eb35943e0707e973979209d8e3b13387693ea34(
    *,
    public_i_ps: typing.Optional[typing.Sequence[typing.Union[AksClusterResourceReference, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5eb4b1478ac33861d98f32854ef8fae14f3e5fad9514868f6ff4223ee859c526(
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
    agent_pool_profiles: typing.Sequence[typing.Union[AksClusterAgentPoolProfile, typing.Dict[builtins.str, typing.Any]]],
    dns_prefix: builtins.str,
    aad_profile: typing.Optional[typing.Union[AksClusterAadProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    addon_profiles: typing.Optional[typing.Mapping[builtins.str, typing.Union[AksClusterAddonProfile, typing.Dict[builtins.str, typing.Any]]]] = None,
    api_server_access_profile: typing.Optional[typing.Union[AksClusterApiServerAccessProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    auto_scaler_profile: typing.Optional[typing.Union[AksClusterAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    disable_local_accounts: typing.Optional[builtins.bool] = None,
    disk_encryption_set_id: typing.Optional[builtins.str] = None,
    enable_rbac: typing.Optional[builtins.bool] = None,
    fqdn: typing.Optional[builtins.str] = None,
    http_proxy_config: typing.Optional[typing.Union[AksClusterHttpProxyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    identity: typing.Optional[typing.Union[AksClusterIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
    ignore_changes: typing.Optional[typing.Sequence[builtins.str]] = None,
    kubernetes_version: typing.Optional[builtins.str] = None,
    linux_profile: typing.Optional[typing.Union[AksClusterLinuxProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    network_profile: typing.Optional[typing.Union[AksClusterNetworkProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    node_resource_group: typing.Optional[builtins.str] = None,
    oidc_issuer_profile: typing.Optional[typing.Union[AksClusterOidcIssuerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    private_fqdn: typing.Optional[builtins.str] = None,
    public_network_access: typing.Optional[builtins.str] = None,
    resource_group_id: typing.Optional[builtins.str] = None,
    security_profile: typing.Optional[typing.Union[AksClusterSecurityProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    service_principal_profile: typing.Optional[typing.Union[AksClusterServicePrincipalProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    sku: typing.Optional[typing.Union[AksClusterSku, typing.Dict[builtins.str, typing.Any]]] = None,
    storage_profile: typing.Optional[typing.Union[AksClusterStorageProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    support_plan: typing.Optional[builtins.str] = None,
    windows_profile: typing.Optional[typing.Union[AksClusterWindowsProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    workload_auto_scaler_profile: typing.Optional[typing.Union[AksClusterWorkloadAutoScalerProfile, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bd203f4d62a443fbd7df18c3e8a3c8b7d0bcb2ccf954ba2c9ac360e7287d1f78(
    *,
    id: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c2e4820006e7c39242874301b84c362d8d5da6edfbcbba7cc26ce356dd5ee94c(
    *,
    azure_key_vault_kms: typing.Optional[typing.Union[AksClusterAzureKeyVaultKms, typing.Dict[builtins.str, typing.Any]]] = None,
    defender: typing.Optional[typing.Union[AksClusterDefenderSecurityMonitoring, typing.Dict[builtins.str, typing.Any]]] = None,
    image_cleaner: typing.Optional[typing.Union[AksClusterImageCleaner, typing.Dict[builtins.str, typing.Any]]] = None,
    workload_identity: typing.Optional[typing.Union[AksClusterWorkloadIdentity, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__196e8b319a4b1e1d9e197aa10d46963817d1c6263eee893714779913cf327318(
    *,
    client_id: builtins.str,
    secret: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c3bea3398400f1a12db673795b2e9d158ed01a7da52e96cd32bd46e9a2a715bb(
    *,
    name: typing.Optional[builtins.str] = None,
    tier: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__707c21455361e0b337d109a2d2cc54e928dafbd5eb58725d2fc6282fcad2adce(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__91521a35af54389a7d22c4bc215bed63deb208b8997113d8989e7f6b4a22e082(
    *,
    public_keys: typing.Sequence[typing.Union[AksClusterSshPublicKey, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70dcfc930eec0040d1f14c95f78f805defe450202bf2d91e6658c7e81f29bcc0(
    *,
    key_data: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c4aec98be4aa2863e4603613df5718b36c575283a73e118d86e97bf6a19a4b23(
    *,
    blob_csi_driver: typing.Optional[typing.Union[AksClusterBlobCSIDriver, typing.Dict[builtins.str, typing.Any]]] = None,
    disk_csi_driver: typing.Optional[typing.Union[AksClusterDiskCSIDriver, typing.Dict[builtins.str, typing.Any]]] = None,
    file_csi_driver: typing.Optional[typing.Union[AksClusterFileCSIDriver, typing.Dict[builtins.str, typing.Any]]] = None,
    snapshot_controller: typing.Optional[typing.Union[AksClusterSnapshotController, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__43af6eba048e638aa04c5127875ed96383f9cde8f9dd7fd46f33a26354f337aa(
    *,
    fs_aio_max_nr: typing.Optional[jsii.Number] = None,
    fs_file_max: typing.Optional[jsii.Number] = None,
    fs_inotify_max_user_watches: typing.Optional[jsii.Number] = None,
    fs_nr_open: typing.Optional[jsii.Number] = None,
    kernel_threads_max: typing.Optional[jsii.Number] = None,
    net_core_netdev_max_backlog: typing.Optional[jsii.Number] = None,
    net_core_optmem_max: typing.Optional[jsii.Number] = None,
    net_core_rmem_default: typing.Optional[jsii.Number] = None,
    net_core_rmem_max: typing.Optional[jsii.Number] = None,
    net_core_somaxconn: typing.Optional[jsii.Number] = None,
    net_core_wmem_default: typing.Optional[jsii.Number] = None,
    net_core_wmem_max: typing.Optional[jsii.Number] = None,
    net_ipv4_ip_local_port_range: typing.Optional[builtins.str] = None,
    net_ipv4_neigh_default_gc_thresh1: typing.Optional[jsii.Number] = None,
    net_ipv4_neigh_default_gc_thresh2: typing.Optional[jsii.Number] = None,
    net_ipv4_neigh_default_gc_thresh3: typing.Optional[jsii.Number] = None,
    net_ipv4_tcp_fin_timeout: typing.Optional[jsii.Number] = None,
    net_ipv4_tcpkeepalive_intvl: typing.Optional[jsii.Number] = None,
    net_ipv4_tcp_keepalive_probes: typing.Optional[jsii.Number] = None,
    net_ipv4_tcp_keepalive_time: typing.Optional[jsii.Number] = None,
    net_ipv4_tcp_max_syn_backlog: typing.Optional[jsii.Number] = None,
    net_ipv4_tcp_tw_reuse: typing.Optional[builtins.bool] = None,
    net_netfilter_nf_conntrack_buckets: typing.Optional[jsii.Number] = None,
    net_netfilter_nf_conntrack_max: typing.Optional[jsii.Number] = None,
    vm_max_map_count: typing.Optional[jsii.Number] = None,
    vm_swappiness: typing.Optional[jsii.Number] = None,
    vm_vfs_cache_pressure: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bd1834d21bbc620fb6c84cc0feb3971e5a7c099ba2d885e479f9dc0cea67ee6f(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94f35baefd65bc096feb737adb69a479310f150e8806458a5e5ec89e5e2c4145(
    *,
    admin_username: builtins.str,
    admin_password: typing.Optional[builtins.str] = None,
    enable_csi_proxy: typing.Optional[builtins.bool] = None,
    gmsa_profile: typing.Optional[typing.Union[AksClusterGmsaProfile, typing.Dict[builtins.str, typing.Any]]] = None,
    license_type: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b669d856557e7356e859c33e9b613b745678b50fc01880aebc6f4b4b6b01dae2(
    *,
    keda: typing.Optional[typing.Union[AksClusterKeda, typing.Dict[builtins.str, typing.Any]]] = None,
    vertical_pod_autoscaler: typing.Optional[typing.Union[AksClusterVerticalPodAutoscaler, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d05c02a9088b204b12ce8e074222a127fb14a2d40efccf18a7a7d3f6e7a779e1(
    *,
    enabled: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass
