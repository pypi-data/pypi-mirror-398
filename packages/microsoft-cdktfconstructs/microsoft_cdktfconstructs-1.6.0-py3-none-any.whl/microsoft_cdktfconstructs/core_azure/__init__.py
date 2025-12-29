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
from .. import (
    AzapiProviderConfig as _AzapiProviderConfig_3cfa09e3,
    AzapiProviderEndpoint as _AzapiProviderEndpoint_ac1351fa,
    DataAzapiClientConfigConfig as _DataAzapiClientConfigConfig_2fa921a7,
    DataAzapiClientConfigTimeouts as _DataAzapiClientConfigTimeouts_60de1877,
    DataAzapiClientConfigTimeoutsOutputReference as _DataAzapiClientConfigTimeoutsOutputReference_b8bf1947,
    DataAzapiResourceConfig as _DataAzapiResourceConfig_3eca9668,
    DataAzapiResourceIdentity as _DataAzapiResourceIdentity_3125d9eb,
    DataAzapiResourceIdentityList as _DataAzapiResourceIdentityList_ffff0399,
    DataAzapiResourceIdentityOutputReference as _DataAzapiResourceIdentityOutputReference_d111e2d1,
    DataAzapiResourceRetry as _DataAzapiResourceRetry_68065f43,
    DataAzapiResourceRetryOutputReference as _DataAzapiResourceRetryOutputReference_3a9a985d,
    DataAzapiResourceTimeouts as _DataAzapiResourceTimeouts_a892ce9b,
    DataAzapiResourceTimeoutsOutputReference as _DataAzapiResourceTimeoutsOutputReference_824b781b,
    ResourceActionConfig as _ResourceActionConfig_2267cc37,
    ResourceActionRetry as _ResourceActionRetry_9fc7b6fd,
    ResourceActionRetryOutputReference as _ResourceActionRetryOutputReference_2c40390c,
    ResourceActionTimeouts as _ResourceActionTimeouts_e30653fd,
    ResourceActionTimeoutsOutputReference as _ResourceActionTimeoutsOutputReference_13d5cf9c,
    ResourceConfig as _ResourceConfig_04e2532f,
    ResourceIdentity as _ResourceIdentity_d0fe12c0,
    ResourceIdentityList as _ResourceIdentityList_4a7b5836,
    ResourceIdentityOutputReference as _ResourceIdentityOutputReference_ca99d26d,
    ResourceRetry as _ResourceRetry_50237e4f,
    ResourceRetryOutputReference as _ResourceRetryOutputReference_4a94fdab,
    ResourceTimeouts as _ResourceTimeouts_0b401feb,
    ResourceTimeoutsOutputReference as _ResourceTimeoutsOutputReference_e98b2440,
    UpdateResourceConfig as _UpdateResourceConfig_d768a9b2,
    UpdateResourceRetry as _UpdateResourceRetry_9d4b8e25,
    UpdateResourceRetryOutputReference as _UpdateResourceRetryOutputReference_c5ac7a83,
    UpdateResourceTimeouts as _UpdateResourceTimeouts_49a4241d,
    UpdateResourceTimeoutsOutputReference as _UpdateResourceTimeoutsOutputReference_876e6cc3,
)
from ..azure_actiongroup import ActionGroupProps as _ActionGroupProps_572d2b68
from ..azure_activitylogalert import (
    ActivityLogAlertProps as _ActivityLogAlertProps_f1779054
)
from ..azure_diagnosticsettings import (
    DiagnosticSettingsProps as _DiagnosticSettingsProps_cc0fa615
)
from ..azure_metricalert import MetricAlertProps as _MetricAlertProps_a18d777f


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ApiSchema",
    jsii_struct_bases=[],
    name_mapping={
        "properties": "properties",
        "required": "required",
        "resource_type": "resourceType",
        "version": "version",
        "deprecated": "deprecated",
        "optional": "optional",
        "transformation_rules": "transformationRules",
        "validation_rules": "validationRules",
    },
)
class ApiSchema:
    def __init__(
        self,
        *,
        properties: typing.Mapping[builtins.str, typing.Union["PropertyDefinition", typing.Dict[builtins.str, typing.Any]]],
        required: typing.Sequence[builtins.str],
        resource_type: builtins.str,
        version: builtins.str,
        deprecated: typing.Optional[typing.Sequence[builtins.str]] = None,
        optional: typing.Optional[typing.Sequence[builtins.str]] = None,
        transformation_rules: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        validation_rules: typing.Optional[typing.Sequence[typing.Union["PropertyValidation", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''API Schema definition using TypeScript objects.

        Defines the complete schema for an API version including all properties,
        validation rules, and transformation mappings. This schema-driven approach
        enables automatic validation, transformation, and multi-language support.

        :param properties: Dictionary of property definitions keyed by property name Each property defines its type, validation, and metadata.
        :param required: Array of property names that are required Properties listed here must be provided by the user.
        :param resource_type: The Azure resource type this schema applies to.
        :param version: The API version this schema represents.
        :param deprecated: Array of property names that are deprecated Usage of these properties will generate warnings.
        :param optional: Array of property names that are optional Used for documentation and validation optimization.
        :param transformation_rules: Property transformation rules for schema mapping Maps input property names to target property names.
        :param validation_rules: Property-specific validation rules Applied in addition to individual property validation.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d8cc5e877912404285c4a1a4fb2ead49797841e8fb27ff8c48c2e63167fd148b)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument required", value=required, expected_type=type_hints["required"])
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
            check_type(argname="argument deprecated", value=deprecated, expected_type=type_hints["deprecated"])
            check_type(argname="argument optional", value=optional, expected_type=type_hints["optional"])
            check_type(argname="argument transformation_rules", value=transformation_rules, expected_type=type_hints["transformation_rules"])
            check_type(argname="argument validation_rules", value=validation_rules, expected_type=type_hints["validation_rules"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "properties": properties,
            "required": required,
            "resource_type": resource_type,
            "version": version,
        }
        if deprecated is not None:
            self._values["deprecated"] = deprecated
        if optional is not None:
            self._values["optional"] = optional
        if transformation_rules is not None:
            self._values["transformation_rules"] = transformation_rules
        if validation_rules is not None:
            self._values["validation_rules"] = validation_rules

    @builtins.property
    def properties(self) -> typing.Mapping[builtins.str, "PropertyDefinition"]:
        '''Dictionary of property definitions keyed by property name Each property defines its type, validation, and metadata.

        Example::

            { "location": { type: "string", required: true } }
        '''
        result = self._values.get("properties")
        assert result is not None, "Required property 'properties' is missing"
        return typing.cast(typing.Mapping[builtins.str, "PropertyDefinition"], result)

    @builtins.property
    def required(self) -> typing.List[builtins.str]:
        '''Array of property names that are required Properties listed here must be provided by the user.'''
        result = self._values.get("required")
        assert result is not None, "Required property 'required' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def resource_type(self) -> builtins.str:
        '''The Azure resource type this schema applies to.

        Example::

            "Microsoft.Resources/resourceGroups"
        '''
        result = self._values.get("resource_type")
        assert result is not None, "Required property 'resource_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def version(self) -> builtins.str:
        '''The API version this schema represents.

        Example::

            "2024-11-01"
        '''
        result = self._values.get("version")
        assert result is not None, "Required property 'version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def deprecated(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of property names that are deprecated Usage of these properties will generate warnings.'''
        result = self._values.get("deprecated")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def optional(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of property names that are optional Used for documentation and validation optimization.'''
        result = self._values.get("optional")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def transformation_rules(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Property transformation rules for schema mapping Maps input property names to target property names.

        Example::

            { "oldName": "newName" }
        '''
        result = self._values.get("transformation_rules")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def validation_rules(self) -> typing.Optional[typing.List["PropertyValidation"]]:
        '''Property-specific validation rules Applied in addition to individual property validation.'''
        result = self._values.get("validation_rules")
        return typing.cast(typing.Optional[typing.List["PropertyValidation"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ApiSchema(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ApiVersionManager(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ApiVersionManager",
):
    '''ApiVersionManager singleton class for centralized version management.

    This class manages API versions for Azure resources, providing version resolution,
    compatibility analysis, and migration guidance. It implements a JSII-compliant
    singleton pattern for thread-safe operations across multiple language bindings.

    Key Features:

    - Thread-safe singleton implementation
    - Version registry management with full lifecycle support
    - Advanced version resolution with constraint-based selection
    - Comprehensive migration analysis with effort estimation
    - Extensive validation and error handling

    Example::

        const manager = ApiVersionManager.getInstance();
        manager.registerResourceType('Microsoft.Resources/resourceGroups', versions);
        const latest = manager.getLatestVersion('Microsoft.Resources/resourceGroups');
        const analysis = manager.analyzeMigration('Microsoft.Resources/resourceGroups', '2024-01-01', '2024-11-01');
    '''

    @jsii.member(jsii_name="instance")
    @builtins.classmethod
    def instance(cls) -> "ApiVersionManager":
        '''Gets the singleton instance of ApiVersionManager.

        This method implements a thread-safe singleton pattern that's compatible
        with JSII multi-language bindings. The instance is lazily created on
        first access and reused for all subsequent calls.

        :return: The singleton ApiVersionManager instance

        Example::

            const manager = ApiVersionManager.instance();
        '''
        return typing.cast("ApiVersionManager", jsii.sinvoke(cls, "instance", []))

    @jsii.member(jsii_name="analyzeMigration")
    def analyze_migration(
        self,
        resource_type: builtins.str,
        from_version: builtins.str,
        to_version: builtins.str,
    ) -> "MigrationAnalysis":
        '''Analyzes migration requirements between two versions.

        Performs comprehensive analysis of the migration path between source and
        target versions, including compatibility assessment, breaking changes
        identification, effort estimation, and upgrade feasibility.

        :param resource_type: - The Azure resource type.
        :param from_version: - The source version to migrate from.
        :param to_version: - The target version to migrate to.

        :return: Detailed migration analysis results

        :throws: Error if resourceType is not registered

        Example::

            const analysis = manager.analyzeMigration(
              'Microsoft.Resources/resourceGroups',
              '2024-01-01',
              '2024-11-01'
            );
            
            console.log(`Compatible: ${analysis.compatible}`);
            console.log(`Effort: ${analysis.estimatedEffort}`);
            console.log(`Breaking changes: ${analysis.breakingChanges.length}`);
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__92f24aa1042dca0f0e9b67956e5ac1c99285ed812c2660bcae26a8c8a39ec798)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument from_version", value=from_version, expected_type=type_hints["from_version"])
            check_type(argname="argument to_version", value=to_version, expected_type=type_hints["to_version"])
        return typing.cast("MigrationAnalysis", jsii.invoke(self, "analyzeMigration", [resource_type, from_version, to_version]))

    @jsii.member(jsii_name="latestVersion")
    def latest_version(
        self,
        resource_type: builtins.str,
    ) -> typing.Optional[builtins.str]:
        '''Gets the latest active version for a resource type.

        Returns the most recent version with ACTIVE support level. If no active
        versions are found, returns the most recent version regardless of support level.

        :param resource_type: - The Azure resource type to get the latest version for.

        :return: The latest version string, or undefined if the resource type is not registered

        Example::

            const latest = manager.latestVersion('Microsoft.Resources/resourceGroups');
            // Returns: "2024-11-01"
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c6802aa02200e054813137481cf20a27e58984a2c2d1ac27f19d674387594fdc)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
        return typing.cast(typing.Optional[builtins.str], jsii.invoke(self, "latestVersion", [resource_type]))

    @jsii.member(jsii_name="registeredResourceTypes")
    def registered_resource_types(self) -> typing.List[builtins.str]:
        '''Gets all registered resource types.

        Returns an array of all Azure resource types that have been registered
        with the version manager.

        :return: Array of registered resource type strings

        Example::

            const resourceTypes = manager.registeredResourceTypes();
            // Returns: ["Microsoft.Resources/resourceGroups", "Microsoft.Storage/storageAccounts", ...]
        '''
        return typing.cast(typing.List[builtins.str], jsii.invoke(self, "registeredResourceTypes", []))

    @jsii.member(jsii_name="registerResourceType")
    def register_resource_type(
        self,
        resource_type: builtins.str,
        versions: typing.Sequence[typing.Union["VersionConfig", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''Registers a resource type with its version configurations.

        This method stores version metadata for a specific Azure resource type,
        including schemas, lifecycle information, and migration data. It validates
        the input and maintains internal indexes for efficient lookups.

        :param resource_type: - The Azure resource type (e.g., 'Microsoft.Resources/resourceGroups').
        :param versions: - Array of version configurations for the resource type.

        :throws: Error if version configurations are invalid

        Example::

            manager.registerResourceType('Microsoft.Resources/resourceGroups', [
              {
                version: '2024-01-01',
                schema: { resourceType: 'Microsoft.Resources/resourceGroups', version: '2024-01-01', properties: {}, required: [] },
                supportLevel: VersionSupportLevel.ACTIVE,
                releaseDate: '2024-01-01'
              }
            ]);
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__258468ab165c63cc98f68ab5890771f9f7cb5d5e80e4229d03140708298effe5)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument versions", value=versions, expected_type=type_hints["versions"])
        return typing.cast(None, jsii.invoke(self, "registerResourceType", [resource_type, versions]))

    @jsii.member(jsii_name="supportedVersions")
    def supported_versions(
        self,
        resource_type: builtins.str,
    ) -> typing.List[builtins.str]:
        '''Gets all supported versions for a resource type.

        Returns an array of all registered version strings for the specified
        resource type, sorted by release date (newest first).

        :param resource_type: - The Azure resource type.

        :return: Array of supported version strings, empty if resource type not registered

        Example::

            const versions = manager.supportedVersions('Microsoft.Resources/resourceGroups');
            // Returns: ["2024-11-01", "2024-01-01", "2023-07-01"]
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fb77480c2569fc25c0b5e80e521a00b13c0757db68aef2cdd53ee3d0c3968480)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
        return typing.cast(typing.List[builtins.str], jsii.invoke(self, "supportedVersions", [resource_type]))

    @jsii.member(jsii_name="validateVersionSupport")
    def validate_version_support(
        self,
        resource_type: builtins.str,
        version: builtins.str,
    ) -> builtins.bool:
        '''Validates whether a version is supported for a resource type.

        Checks if the specified version is registered and available for use
        with the given resource type.

        :param resource_type: - The Azure resource type.
        :param version: - The version to validate.

        :return: True if the version is supported, false otherwise

        Example::

            if (manager.validateVersionSupport('Microsoft.Resources/resourceGroups', '2024-01-01')) {
              // Version is supported, proceed with resource creation
            } else {
              // Handle unsupported version
            }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07391b3a9dfa1e820637464775a351b226c27bd8864b9d17c0cf7b5b14174d9c)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        return typing.cast(builtins.bool, jsii.invoke(self, "validateVersionSupport", [resource_type, version]))

    @jsii.member(jsii_name="versionConfig")
    def version_config(
        self,
        resource_type: builtins.str,
        version: builtins.str,
    ) -> typing.Optional["VersionConfig"]:
        '''Gets the configuration for a specific version of a resource type.

        Retrieves the complete version configuration including schema, lifecycle
        information, breaking changes, and migration metadata.

        :param resource_type: - The Azure resource type.
        :param version: - The specific version to retrieve.

        :return: The version configuration, or undefined if not found

        Example::

            const config = manager.versionConfig('Microsoft.Resources/resourceGroups', '2024-01-01');
            if (config) {
              console.log(`Support level: ${config.supportLevel}`);
              console.log(`Release date: ${config.releaseDate}`);
            }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__68b2969a72a2e232d2e7c70c7ec7b69ff1d3505b07b24c58bd8104b8e787fecd)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        return typing.cast(typing.Optional["VersionConfig"], jsii.invoke(self, "versionConfig", [resource_type, version]))

    @jsii.member(jsii_name="versionLifecycle")
    def version_lifecycle(
        self,
        resource_type: builtins.str,
        version: builtins.str,
    ) -> typing.Optional["VersionLifecycle"]:
        '''Gets version lifecycle information for a specific version.

        Provides lifecycle metadata including current phase, transition dates,
        and projected sunset timeline.

        :param resource_type: - The Azure resource type.
        :param version: - The version to get lifecycle information for.

        :return: Version lifecycle information, or undefined if not found

        Example::

            const lifecycle = manager.versionLifecycle('Microsoft.Resources/resourceGroups', '2024-01-01');
            if (lifecycle) {
              console.log(`Current phase: ${lifecycle.phase}`);
              console.log(`Sunset date: ${lifecycle.estimatedSunsetDate}`);
            }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f62aa7dc4291470534670e29625675e40b1210aa8c0e44d850c1110ad6be8ad1)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
        return typing.cast(typing.Optional["VersionLifecycle"], jsii.invoke(self, "versionLifecycle", [resource_type, version]))


class AzapiProvider(
    _cdktf_9a9027ec.TerraformProvider,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiProvider",
):
    '''Represents a {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs azapi}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        alias: typing.Optional[builtins.str] = None,
        auxiliary_tenant_ids: typing.Optional[typing.Sequence[builtins.str]] = None,
        client_certificate: typing.Optional[builtins.str] = None,
        client_certificate_password: typing.Optional[builtins.str] = None,
        client_certificate_path: typing.Optional[builtins.str] = None,
        client_id: typing.Optional[builtins.str] = None,
        client_id_file_path: typing.Optional[builtins.str] = None,
        client_secret: typing.Optional[builtins.str] = None,
        client_secret_file_path: typing.Optional[builtins.str] = None,
        custom_correlation_request_id: typing.Optional[builtins.str] = None,
        default_location: typing.Optional[builtins.str] = None,
        default_name: typing.Optional[builtins.str] = None,
        default_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        disable_correlation_request_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        disable_default_output: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        disable_instance_discovery: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        disable_terraform_partner_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        enable_preflight: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        endpoint: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_AzapiProviderEndpoint_ac1351fa, typing.Dict[builtins.str, typing.Any]]]]] = None,
        environment: typing.Optional[builtins.str] = None,
        ignore_no_op_changes: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        maximum_busy_retry_attempts: typing.Optional[jsii.Number] = None,
        oidc_azure_service_connection_id: typing.Optional[builtins.str] = None,
        oidc_request_token: typing.Optional[builtins.str] = None,
        oidc_request_url: typing.Optional[builtins.str] = None,
        oidc_token: typing.Optional[builtins.str] = None,
        oidc_token_file_path: typing.Optional[builtins.str] = None,
        partner_id: typing.Optional[builtins.str] = None,
        skip_provider_registration: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        subscription_id: typing.Optional[builtins.str] = None,
        tenant_id: typing.Optional[builtins.str] = None,
        use_aks_workload_identity: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        use_cli: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        use_msi: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        use_oidc: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs azapi} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param alias: Alias name. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#alias AzapiProvider#alias}
        :param auxiliary_tenant_ids: List of auxiliary Tenant IDs required for multi-tenancy and cross-tenant scenarios. This can also be sourced from the ``ARM_AUXILIARY_TENANT_IDS`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#auxiliary_tenant_ids AzapiProvider#auxiliary_tenant_ids}
        :param client_certificate: A base64-encoded PKCS#12 bundle to be used as the client certificate for authentication. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE`` environment variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate AzapiProvider#client_certificate}
        :param client_certificate_password: The password associated with the Client Certificate. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE_PASSWORD`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate_password AzapiProvider#client_certificate_password}
        :param client_certificate_path: The path to the Client Certificate associated with the Service Principal which should be used. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE_PATH`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate_path AzapiProvider#client_certificate_path}
        :param client_id: The Client ID which should be used. This can also be sourced from the ``ARM_CLIENT_ID``, ``AZURE_CLIENT_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_id AzapiProvider#client_id}
        :param client_id_file_path: The path to a file containing the Client ID which should be used. This can also be sourced from the ``ARM_CLIENT_ID_FILE_PATH`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_id_file_path AzapiProvider#client_id_file_path}
        :param client_secret: The Client Secret which should be used. This can also be sourced from the ``ARM_CLIENT_SECRET`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_secret AzapiProvider#client_secret}
        :param client_secret_file_path: The path to a file containing the Client Secret which should be used. For use When authenticating as a Service Principal using a Client Secret. This can also be sourced from the ``ARM_CLIENT_SECRET_FILE_PATH`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_secret_file_path AzapiProvider#client_secret_file_path}
        :param custom_correlation_request_id: The value of the ``x-ms-correlation-request-id`` header, otherwise an auto-generated UUID will be used. This can also be sourced from the ``ARM_CORRELATION_REQUEST_ID`` environment variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#custom_correlation_request_id AzapiProvider#custom_correlation_request_id}
        :param default_location: The default Azure Region where the azure resource should exist. The ``location`` in each resource block can override the ``default_location``. Changing this forces new resources to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_location AzapiProvider#default_location}
        :param default_name: The default name to create the azure resource. The ``name`` in each resource block can override the ``default_name``. Changing this forces new resources to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_name AzapiProvider#default_name}
        :param default_tags: A mapping of tags which should be assigned to the azure resource as default tags. The``tags`` in each resource block can override the ``default_tags``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_tags AzapiProvider#default_tags}
        :param disable_correlation_request_id: This will disable the x-ms-correlation-request-id header. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_correlation_request_id AzapiProvider#disable_correlation_request_id}
        :param disable_default_output: Disable default output. The default is false. When set to false, the provider will output the read-only properties if ``response_export_values`` is not specified in the resource block. When set to true, the provider will disable this output. This can also be sourced from the ``ARM_DISABLE_DEFAULT_OUTPUT`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_default_output AzapiProvider#disable_default_output}
        :param disable_instance_discovery: Disables Instance Discovery, which validates that the Authority is valid and known by the Microsoft Entra instance metadata service at ``https://login.microsoft.com`` before authenticating. This should only be enabled when the configured authority is known to be valid and trustworthy - such as when running against Azure Stack or when ``environment`` is set to ``custom``. This can also be specified via the ``ARM_DISABLE_INSTANCE_DISCOVERY`` environment variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_instance_discovery AzapiProvider#disable_instance_discovery}
        :param disable_terraform_partner_id: Disable sending the Terraform Partner ID if a custom ``partner_id`` isn't specified, which allows Microsoft to better understand the usage of Terraform. The Partner ID does not give HashiCorp any direct access to usage information. This can also be sourced from the ``ARM_DISABLE_TERRAFORM_PARTNER_ID`` environment variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_terraform_partner_id AzapiProvider#disable_terraform_partner_id}
        :param enable_preflight: Enable Preflight Validation. The default is false. When set to true, the provider will use Preflight to do static validation before really deploying a new resource. When set to false, the provider will disable this validation. This can also be sourced from the ``ARM_ENABLE_PREFLIGHT`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#enable_preflight AzapiProvider#enable_preflight}
        :param endpoint: The Azure API Endpoint Configuration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#endpoint AzapiProvider#endpoint}
        :param environment: The Cloud Environment which should be used. Possible values are ``public``, ``usgovernment``, ``china`` and ``custom``. Defaults to ``public``. This can also be sourced from the ``ARM_ENVIRONMENT`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#environment AzapiProvider#environment}
        :param ignore_no_op_changes: Ignore no-op changes for ``azapi_resource``. The default is true. When set to true, the provider will suppress changes in the ``azapi_resource`` if the ``body`` in the new API version still matches the remote state. When set to false, the provider will not suppress these changes. This can also be sourced from the ``ARM_IGNORE_NO_OP_CHANGES`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#ignore_no_op_changes AzapiProvider#ignore_no_op_changes}
        :param maximum_busy_retry_attempts: DEPRECATED - The maximum number of retries to attempt if the Azure API returns an HTTP 408, 429, 500, 502, 503, or 504 response. The default is ``32767``, this allows the provider to rely on the resource timeout values rather than a maximum retry count. The resource-specific retry configuration may additionally be used to retry on other errors and conditions. This property will be removed in a future version. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#maximum_busy_retry_attempts AzapiProvider#maximum_busy_retry_attempts}
        :param oidc_azure_service_connection_id: The Azure Pipelines Service Connection ID to use for authentication. This can also be sourced from the ``ARM_ADO_PIPELINE_SERVICE_CONNECTION_ID``, ``ARM_OIDC_AZURE_SERVICE_CONNECTION_ID``, or ``AZURESUBSCRIPTION_SERVICE_CONNECTION_ID`` Environment Variables. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_azure_service_connection_id AzapiProvider#oidc_azure_service_connection_id}
        :param oidc_request_token: The bearer token for the request to the OIDC provider. This can also be sourced from the ``ARM_OIDC_REQUEST_TOKEN``, ``ACTIONS_ID_TOKEN_REQUEST_TOKEN``, or ``SYSTEM_ACCESSTOKEN`` Environment Variables. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_request_token AzapiProvider#oidc_request_token}
        :param oidc_request_url: The URL for the OIDC provider from which to request an ID token. This can also be sourced from the ``ARM_OIDC_REQUEST_URL``, ``ACTIONS_ID_TOKEN_REQUEST_URL``, or ``SYSTEM_OIDCREQUESTURI`` Environment Variables. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_request_url AzapiProvider#oidc_request_url}
        :param oidc_token: The ID token when authenticating using OpenID Connect (OIDC). This can also be sourced from the ``ARM_OIDC_TOKEN`` environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_token AzapiProvider#oidc_token}
        :param oidc_token_file_path: The path to a file containing an ID token when authenticating using OpenID Connect (OIDC). This can also be sourced from the ``ARM_OIDC_TOKEN_FILE_PATH``, ``AZURE_FEDERATED_TOKEN_FILE`` environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_token_file_path AzapiProvider#oidc_token_file_path}
        :param partner_id: A GUID/UUID that is `registered <https://docs.microsoft.com/azure/marketplace/azure-partner-customer-usage-attribution#register-guids-and-offers>`_ with Microsoft to facilitate partner resource usage attribution. This can also be sourced from the ``ARM_PARTNER_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#partner_id AzapiProvider#partner_id}
        :param skip_provider_registration: Should the Provider skip registering the Resource Providers it supports? This can also be sourced from the ``ARM_SKIP_PROVIDER_REGISTRATION`` Environment Variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#skip_provider_registration AzapiProvider#skip_provider_registration}
        :param subscription_id: The Subscription ID which should be used. This can also be sourced from the ``ARM_SUBSCRIPTION_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#subscription_id AzapiProvider#subscription_id}
        :param tenant_id: The Tenant ID should be used. This can also be sourced from the ``ARM_TENANT_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#tenant_id AzapiProvider#tenant_id}
        :param use_aks_workload_identity: Should AKS Workload Identity be used for Authentication? This can also be sourced from the ``ARM_USE_AKS_WORKLOAD_IDENTITY`` Environment Variable. Defaults to ``false``. When set, ``client_id``, ``tenant_id`` and ``oidc_token_file_path`` will be detected from the environment and do not need to be specified. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_aks_workload_identity AzapiProvider#use_aks_workload_identity}
        :param use_cli: Should Azure CLI be used for authentication? This can also be sourced from the ``ARM_USE_CLI`` environment variable. Defaults to ``true``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_cli AzapiProvider#use_cli}
        :param use_msi: Should Managed Identity be used for Authentication? This can also be sourced from the ``ARM_USE_MSI`` Environment Variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_msi AzapiProvider#use_msi}
        :param use_oidc: Should OIDC be used for Authentication? This can also be sourced from the ``ARM_USE_OIDC`` Environment Variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_oidc AzapiProvider#use_oidc}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5f52ff2d70292dbdfed6d184e238a41b86653521bafe707ddbb8b8f9497b9648)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = _AzapiProviderConfig_3cfa09e3(
            alias=alias,
            auxiliary_tenant_ids=auxiliary_tenant_ids,
            client_certificate=client_certificate,
            client_certificate_password=client_certificate_password,
            client_certificate_path=client_certificate_path,
            client_id=client_id,
            client_id_file_path=client_id_file_path,
            client_secret=client_secret,
            client_secret_file_path=client_secret_file_path,
            custom_correlation_request_id=custom_correlation_request_id,
            default_location=default_location,
            default_name=default_name,
            default_tags=default_tags,
            disable_correlation_request_id=disable_correlation_request_id,
            disable_default_output=disable_default_output,
            disable_instance_discovery=disable_instance_discovery,
            disable_terraform_partner_id=disable_terraform_partner_id,
            enable_preflight=enable_preflight,
            endpoint=endpoint,
            environment=environment,
            ignore_no_op_changes=ignore_no_op_changes,
            maximum_busy_retry_attempts=maximum_busy_retry_attempts,
            oidc_azure_service_connection_id=oidc_azure_service_connection_id,
            oidc_request_token=oidc_request_token,
            oidc_request_url=oidc_request_url,
            oidc_token=oidc_token,
            oidc_token_file_path=oidc_token_file_path,
            partner_id=partner_id,
            skip_provider_registration=skip_provider_registration,
            subscription_id=subscription_id,
            tenant_id=tenant_id,
            use_aks_workload_identity=use_aks_workload_identity,
            use_cli=use_cli,
            use_msi=use_msi,
            use_oidc=use_oidc,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a AzapiProvider resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the AzapiProvider to import.
        :param import_from_id: The id of the existing AzapiProvider that should be imported. Refer to the {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the AzapiProvider to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cb1c97cbd37e743a6f02fd49654ccb7fbd87bb756cf4bb899c52abe40de45ac3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="resetAlias")
    def reset_alias(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAlias", []))

    @jsii.member(jsii_name="resetAuxiliaryTenantIds")
    def reset_auxiliary_tenant_ids(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAuxiliaryTenantIds", []))

    @jsii.member(jsii_name="resetClientCertificate")
    def reset_client_certificate(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientCertificate", []))

    @jsii.member(jsii_name="resetClientCertificatePassword")
    def reset_client_certificate_password(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientCertificatePassword", []))

    @jsii.member(jsii_name="resetClientCertificatePath")
    def reset_client_certificate_path(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientCertificatePath", []))

    @jsii.member(jsii_name="resetClientId")
    def reset_client_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientId", []))

    @jsii.member(jsii_name="resetClientIdFilePath")
    def reset_client_id_file_path(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientIdFilePath", []))

    @jsii.member(jsii_name="resetClientSecret")
    def reset_client_secret(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientSecret", []))

    @jsii.member(jsii_name="resetClientSecretFilePath")
    def reset_client_secret_file_path(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetClientSecretFilePath", []))

    @jsii.member(jsii_name="resetCustomCorrelationRequestId")
    def reset_custom_correlation_request_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCustomCorrelationRequestId", []))

    @jsii.member(jsii_name="resetDefaultLocation")
    def reset_default_location(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultLocation", []))

    @jsii.member(jsii_name="resetDefaultName")
    def reset_default_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultName", []))

    @jsii.member(jsii_name="resetDefaultTags")
    def reset_default_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDefaultTags", []))

    @jsii.member(jsii_name="resetDisableCorrelationRequestId")
    def reset_disable_correlation_request_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisableCorrelationRequestId", []))

    @jsii.member(jsii_name="resetDisableDefaultOutput")
    def reset_disable_default_output(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisableDefaultOutput", []))

    @jsii.member(jsii_name="resetDisableInstanceDiscovery")
    def reset_disable_instance_discovery(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisableInstanceDiscovery", []))

    @jsii.member(jsii_name="resetDisableTerraformPartnerId")
    def reset_disable_terraform_partner_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDisableTerraformPartnerId", []))

    @jsii.member(jsii_name="resetEnablePreflight")
    def reset_enable_preflight(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEnablePreflight", []))

    @jsii.member(jsii_name="resetEndpoint")
    def reset_endpoint(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEndpoint", []))

    @jsii.member(jsii_name="resetEnvironment")
    def reset_environment(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetEnvironment", []))

    @jsii.member(jsii_name="resetIgnoreNoOpChanges")
    def reset_ignore_no_op_changes(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreNoOpChanges", []))

    @jsii.member(jsii_name="resetMaximumBusyRetryAttempts")
    def reset_maximum_busy_retry_attempts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaximumBusyRetryAttempts", []))

    @jsii.member(jsii_name="resetOidcAzureServiceConnectionId")
    def reset_oidc_azure_service_connection_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOidcAzureServiceConnectionId", []))

    @jsii.member(jsii_name="resetOidcRequestToken")
    def reset_oidc_request_token(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOidcRequestToken", []))

    @jsii.member(jsii_name="resetOidcRequestUrl")
    def reset_oidc_request_url(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOidcRequestUrl", []))

    @jsii.member(jsii_name="resetOidcToken")
    def reset_oidc_token(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOidcToken", []))

    @jsii.member(jsii_name="resetOidcTokenFilePath")
    def reset_oidc_token_file_path(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetOidcTokenFilePath", []))

    @jsii.member(jsii_name="resetPartnerId")
    def reset_partner_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetPartnerId", []))

    @jsii.member(jsii_name="resetSkipProviderRegistration")
    def reset_skip_provider_registration(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSkipProviderRegistration", []))

    @jsii.member(jsii_name="resetSubscriptionId")
    def reset_subscription_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSubscriptionId", []))

    @jsii.member(jsii_name="resetTenantId")
    def reset_tenant_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTenantId", []))

    @jsii.member(jsii_name="resetUseAksWorkloadIdentity")
    def reset_use_aks_workload_identity(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUseAksWorkloadIdentity", []))

    @jsii.member(jsii_name="resetUseCli")
    def reset_use_cli(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUseCli", []))

    @jsii.member(jsii_name="resetUseMsi")
    def reset_use_msi(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUseMsi", []))

    @jsii.member(jsii_name="resetUseOidc")
    def reset_use_oidc(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUseOidc", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="aliasInput")
    def alias_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "aliasInput"))

    @builtins.property
    @jsii.member(jsii_name="auxiliaryTenantIdsInput")
    def auxiliary_tenant_ids_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "auxiliaryTenantIdsInput"))

    @builtins.property
    @jsii.member(jsii_name="clientCertificateInput")
    def client_certificate_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientCertificateInput"))

    @builtins.property
    @jsii.member(jsii_name="clientCertificatePasswordInput")
    def client_certificate_password_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientCertificatePasswordInput"))

    @builtins.property
    @jsii.member(jsii_name="clientCertificatePathInput")
    def client_certificate_path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientCertificatePathInput"))

    @builtins.property
    @jsii.member(jsii_name="clientIdFilePathInput")
    def client_id_file_path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientIdFilePathInput"))

    @builtins.property
    @jsii.member(jsii_name="clientIdInput")
    def client_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientIdInput"))

    @builtins.property
    @jsii.member(jsii_name="clientSecretFilePathInput")
    def client_secret_file_path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientSecretFilePathInput"))

    @builtins.property
    @jsii.member(jsii_name="clientSecretInput")
    def client_secret_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientSecretInput"))

    @builtins.property
    @jsii.member(jsii_name="customCorrelationRequestIdInput")
    def custom_correlation_request_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customCorrelationRequestIdInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultLocationInput")
    def default_location_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultLocationInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultNameInput")
    def default_name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultNameInput"))

    @builtins.property
    @jsii.member(jsii_name="defaultTagsInput")
    def default_tags_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "defaultTagsInput"))

    @builtins.property
    @jsii.member(jsii_name="disableCorrelationRequestIdInput")
    def disable_correlation_request_id_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableCorrelationRequestIdInput"))

    @builtins.property
    @jsii.member(jsii_name="disableDefaultOutputInput")
    def disable_default_output_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableDefaultOutputInput"))

    @builtins.property
    @jsii.member(jsii_name="disableInstanceDiscoveryInput")
    def disable_instance_discovery_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableInstanceDiscoveryInput"))

    @builtins.property
    @jsii.member(jsii_name="disableTerraformPartnerIdInput")
    def disable_terraform_partner_id_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableTerraformPartnerIdInput"))

    @builtins.property
    @jsii.member(jsii_name="enablePreflightInput")
    def enable_preflight_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enablePreflightInput"))

    @builtins.property
    @jsii.member(jsii_name="endpointInput")
    def endpoint_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]], jsii.get(self, "endpointInput"))

    @builtins.property
    @jsii.member(jsii_name="environmentInput")
    def environment_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "environmentInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreNoOpChangesInput")
    def ignore_no_op_changes_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreNoOpChangesInput"))

    @builtins.property
    @jsii.member(jsii_name="maximumBusyRetryAttemptsInput")
    def maximum_busy_retry_attempts_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maximumBusyRetryAttemptsInput"))

    @builtins.property
    @jsii.member(jsii_name="oidcAzureServiceConnectionIdInput")
    def oidc_azure_service_connection_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcAzureServiceConnectionIdInput"))

    @builtins.property
    @jsii.member(jsii_name="oidcRequestTokenInput")
    def oidc_request_token_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcRequestTokenInput"))

    @builtins.property
    @jsii.member(jsii_name="oidcRequestUrlInput")
    def oidc_request_url_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcRequestUrlInput"))

    @builtins.property
    @jsii.member(jsii_name="oidcTokenFilePathInput")
    def oidc_token_file_path_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcTokenFilePathInput"))

    @builtins.property
    @jsii.member(jsii_name="oidcTokenInput")
    def oidc_token_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcTokenInput"))

    @builtins.property
    @jsii.member(jsii_name="partnerIdInput")
    def partner_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "partnerIdInput"))

    @builtins.property
    @jsii.member(jsii_name="skipProviderRegistrationInput")
    def skip_provider_registration_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "skipProviderRegistrationInput"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionIdInput")
    def subscription_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "subscriptionIdInput"))

    @builtins.property
    @jsii.member(jsii_name="tenantIdInput")
    def tenant_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "tenantIdInput"))

    @builtins.property
    @jsii.member(jsii_name="useAksWorkloadIdentityInput")
    def use_aks_workload_identity_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useAksWorkloadIdentityInput"))

    @builtins.property
    @jsii.member(jsii_name="useCliInput")
    def use_cli_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useCliInput"))

    @builtins.property
    @jsii.member(jsii_name="useMsiInput")
    def use_msi_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useMsiInput"))

    @builtins.property
    @jsii.member(jsii_name="useOidcInput")
    def use_oidc_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useOidcInput"))

    @builtins.property
    @jsii.member(jsii_name="alias")
    def alias(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "alias"))

    @alias.setter
    def alias(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f1c9f1106e180ed693d2c3f6b55fe72fbe6a1b03def305ce8ebd26a12ff7b7df)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "alias", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="auxiliaryTenantIds")
    def auxiliary_tenant_ids(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "auxiliaryTenantIds"))

    @auxiliary_tenant_ids.setter
    def auxiliary_tenant_ids(
        self,
        value: typing.Optional[typing.List[builtins.str]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1100caec1f9ce1d5d2cf41740b7d293af0d13c01bcd7014fda2d8c61846ad13d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "auxiliaryTenantIds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientCertificate")
    def client_certificate(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientCertificate"))

    @client_certificate.setter
    def client_certificate(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__24ae50953ef429d98c84f0b542e6b051fe1822f0d666041a342e914236e4187d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientCertificate", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientCertificatePassword")
    def client_certificate_password(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientCertificatePassword"))

    @client_certificate_password.setter
    def client_certificate_password(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5ae54181a82e260516380fd9de4c51a1ee1936d05f68cc92a24125f950b6a82d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientCertificatePassword", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientCertificatePath")
    def client_certificate_path(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientCertificatePath"))

    @client_certificate_path.setter
    def client_certificate_path(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__10caefac7cd044dfc01663c278a29b1e24389797ba96d3ec8afb75392b531465)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientCertificatePath", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientId")
    def client_id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientId"))

    @client_id.setter
    def client_id(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5014b63b8dc6e84933d227c2f96b650fc231d7ab32ad9451fb763e5ef3793d34)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientIdFilePath")
    def client_id_file_path(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientIdFilePath"))

    @client_id_file_path.setter
    def client_id_file_path(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9d3f0a61afcf21bbed272f0b86b97f45d4ecd1a3eb2f3cf853ca1def616282dc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientIdFilePath", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientSecret")
    def client_secret(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientSecret"))

    @client_secret.setter
    def client_secret(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__addcfcaeee63fdcb41a65094c4a261abc261abc25aecd180948483d26d2c1f81)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientSecret", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="clientSecretFilePath")
    def client_secret_file_path(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "clientSecretFilePath"))

    @client_secret_file_path.setter
    def client_secret_file_path(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b74c4d90b7a6059b2c5f5e584a0b441e7ceda6aa39fa3fc321894158d378d5be)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "clientSecretFilePath", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="customCorrelationRequestId")
    def custom_correlation_request_id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "customCorrelationRequestId"))

    @custom_correlation_request_id.setter
    def custom_correlation_request_id(
        self,
        value: typing.Optional[builtins.str],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d32a8694785784b9c81bab4659c373caf87fafe8ff0a427461a9d908feb38147)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "customCorrelationRequestId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="defaultLocation")
    def default_location(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultLocation"))

    @default_location.setter
    def default_location(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__27c927d37364c6fea10c49ee1370691b19e7e592b844a72be12b9c2bd53b2214)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultLocation", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="defaultName")
    def default_name(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "defaultName"))

    @default_name.setter
    def default_name(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__901c18ecd89be7fd89797c6af9765fe336dea1893de27a28f9e62ac55bc31875)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultName", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="defaultTags")
    def default_tags(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "defaultTags"))

    @default_tags.setter
    def default_tags(
        self,
        value: typing.Optional[typing.Mapping[builtins.str, builtins.str]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8160704f9f2999ccada99078d914953ab104324b354fbddabfb94e1917e06c67)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "defaultTags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="disableCorrelationRequestId")
    def disable_correlation_request_id(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableCorrelationRequestId"))

    @disable_correlation_request_id.setter
    def disable_correlation_request_id(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8bcafe1f0985ac771f972dddd9b40e5b109fd915cd651f6dea355c93867bad80)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "disableCorrelationRequestId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="disableDefaultOutput")
    def disable_default_output(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableDefaultOutput"))

    @disable_default_output.setter
    def disable_default_output(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d67e731b58ff35e098fb0072371fad7c475cd4b25c50abdaa608931589e316a7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "disableDefaultOutput", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="disableInstanceDiscovery")
    def disable_instance_discovery(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableInstanceDiscovery"))

    @disable_instance_discovery.setter
    def disable_instance_discovery(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2cf7e835f39db60318f461d809f74a62f9346349f8ea065aee0e2a1df7e1ad14)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "disableInstanceDiscovery", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="disableTerraformPartnerId")
    def disable_terraform_partner_id(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "disableTerraformPartnerId"))

    @disable_terraform_partner_id.setter
    def disable_terraform_partner_id(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cff1d2efc0bb220160cdac950162f4c5222d49e49239351ee750a5f908e14cd1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "disableTerraformPartnerId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="enablePreflight")
    def enable_preflight(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "enablePreflight"))

    @enable_preflight.setter
    def enable_preflight(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__71947faeec1318898617e0ed293d012268c2237fcb652622821551433abd5e75)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "enablePreflight", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="endpoint")
    def endpoint(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]], jsii.get(self, "endpoint"))

    @endpoint.setter
    def endpoint(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__65c72397129b56e6353a15dfc9ff5d22393377a0509b9e18d46d778df9842192)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "endpoint", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="environment")
    def environment(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "environment"))

    @environment.setter
    def environment(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__397d6d0d941514e57a0834d4462117535e609d0136129531104513cd1befe72f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "environment", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreNoOpChanges")
    def ignore_no_op_changes(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreNoOpChanges"))

    @ignore_no_op_changes.setter
    def ignore_no_op_changes(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__09dbe68ef34c5fcd3c7a5981cb86689f964c4f1ad79f1169b2cf26df854dd500)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreNoOpChanges", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maximumBusyRetryAttempts")
    def maximum_busy_retry_attempts(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maximumBusyRetryAttempts"))

    @maximum_busy_retry_attempts.setter
    def maximum_busy_retry_attempts(self, value: typing.Optional[jsii.Number]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2553ea1e0d1bc71a16054d752d20242041c20104919cee3e0329e32bb606d0ea)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maximumBusyRetryAttempts", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="oidcAzureServiceConnectionId")
    def oidc_azure_service_connection_id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcAzureServiceConnectionId"))

    @oidc_azure_service_connection_id.setter
    def oidc_azure_service_connection_id(
        self,
        value: typing.Optional[builtins.str],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__93263d916ada198f1b62843a3878aaa2459de859c08837ee147a0365ecbcf258)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "oidcAzureServiceConnectionId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="oidcRequestToken")
    def oidc_request_token(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcRequestToken"))

    @oidc_request_token.setter
    def oidc_request_token(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bc1615135f90617e10d411b299b693e785bfbeed61ea173051a11a706a815bba)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "oidcRequestToken", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="oidcRequestUrl")
    def oidc_request_url(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcRequestUrl"))

    @oidc_request_url.setter
    def oidc_request_url(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__033db5b8de90649f523b05b37faf1fbecb698506444a0fe82650b44f2ca16753)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "oidcRequestUrl", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="oidcToken")
    def oidc_token(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcToken"))

    @oidc_token.setter
    def oidc_token(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__233d6e8b14f46b907d1c3ef3f7d84e5a23b3e1749217ef95d39b1d2a9bb0cbf9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "oidcToken", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="oidcTokenFilePath")
    def oidc_token_file_path(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "oidcTokenFilePath"))

    @oidc_token_file_path.setter
    def oidc_token_file_path(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2729d037c671785954c8f07d4cb9b0a5b6d44911ffd9cad1e5c0f2edfdf07203)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "oidcTokenFilePath", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="partnerId")
    def partner_id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "partnerId"))

    @partner_id.setter
    def partner_id(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3ddc2a511e1479e3cb8408d9b245d7b8961390179d6a6765331608b414853bbb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "partnerId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="skipProviderRegistration")
    def skip_provider_registration(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "skipProviderRegistration"))

    @skip_provider_registration.setter
    def skip_provider_registration(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8dc7835fba47cc9e9559bef526326a5d9c45a79e56d5524a5fdb5061517e9ff3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "skipProviderRegistration", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "subscriptionId"))

    @subscription_id.setter
    def subscription_id(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d98f67f7e27d1e5277d2356f4d8c4c1ea70ff70a2ed565dd0bbbb38fa832a150)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "subscriptionId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tenantId")
    def tenant_id(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "tenantId"))

    @tenant_id.setter
    def tenant_id(self, value: typing.Optional[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__99ebb90abbcc7995eec074da3fe0f87973120bf3dc9fcdf1e45b08447ff60be5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tenantId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="useAksWorkloadIdentity")
    def use_aks_workload_identity(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useAksWorkloadIdentity"))

    @use_aks_workload_identity.setter
    def use_aks_workload_identity(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e5ada225338a6cd5464f0c24e0b5007a13ef86219cf5f9afb81e61c74090a90)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "useAksWorkloadIdentity", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="useCli")
    def use_cli(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useCli"))

    @use_cli.setter
    def use_cli(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1b1b7d9e8027fd62bf455106d70fae15c8e06bec52154c7c33f1831611aa9869)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "useCli", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="useMsi")
    def use_msi(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useMsi"))

    @use_msi.setter
    def use_msi(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b69e7ba1a072bde82ef951fb89489e5849884ccf2feecd8267952040b6634a82)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "useMsi", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="useOidc")
    def use_oidc(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "useOidc"))

    @use_oidc.setter
    def use_oidc(
        self,
        value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__96708422318163444a6c09b2eaf40a575ec9819054fdb741ec5f24c64820a318)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "useOidc", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiProviderConfig",
    jsii_struct_bases=[],
    name_mapping={
        "alias": "alias",
        "auxiliary_tenant_ids": "auxiliaryTenantIds",
        "client_certificate": "clientCertificate",
        "client_certificate_password": "clientCertificatePassword",
        "client_certificate_path": "clientCertificatePath",
        "client_id": "clientId",
        "client_id_file_path": "clientIdFilePath",
        "client_secret": "clientSecret",
        "client_secret_file_path": "clientSecretFilePath",
        "custom_correlation_request_id": "customCorrelationRequestId",
        "default_location": "defaultLocation",
        "default_name": "defaultName",
        "default_tags": "defaultTags",
        "disable_correlation_request_id": "disableCorrelationRequestId",
        "disable_default_output": "disableDefaultOutput",
        "disable_instance_discovery": "disableInstanceDiscovery",
        "disable_terraform_partner_id": "disableTerraformPartnerId",
        "enable_preflight": "enablePreflight",
        "endpoint": "endpoint",
        "environment": "environment",
        "ignore_no_op_changes": "ignoreNoOpChanges",
        "maximum_busy_retry_attempts": "maximumBusyRetryAttempts",
        "oidc_azure_service_connection_id": "oidcAzureServiceConnectionId",
        "oidc_request_token": "oidcRequestToken",
        "oidc_request_url": "oidcRequestUrl",
        "oidc_token": "oidcToken",
        "oidc_token_file_path": "oidcTokenFilePath",
        "partner_id": "partnerId",
        "skip_provider_registration": "skipProviderRegistration",
        "subscription_id": "subscriptionId",
        "tenant_id": "tenantId",
        "use_aks_workload_identity": "useAksWorkloadIdentity",
        "use_cli": "useCli",
        "use_msi": "useMsi",
        "use_oidc": "useOidc",
    },
)
class AzapiProviderConfig:
    def __init__(
        self,
        *,
        alias: typing.Optional[builtins.str] = None,
        auxiliary_tenant_ids: typing.Optional[typing.Sequence[builtins.str]] = None,
        client_certificate: typing.Optional[builtins.str] = None,
        client_certificate_password: typing.Optional[builtins.str] = None,
        client_certificate_path: typing.Optional[builtins.str] = None,
        client_id: typing.Optional[builtins.str] = None,
        client_id_file_path: typing.Optional[builtins.str] = None,
        client_secret: typing.Optional[builtins.str] = None,
        client_secret_file_path: typing.Optional[builtins.str] = None,
        custom_correlation_request_id: typing.Optional[builtins.str] = None,
        default_location: typing.Optional[builtins.str] = None,
        default_name: typing.Optional[builtins.str] = None,
        default_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        disable_correlation_request_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        disable_default_output: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        disable_instance_discovery: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        disable_terraform_partner_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        enable_preflight: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        endpoint: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_AzapiProviderEndpoint_ac1351fa, typing.Dict[builtins.str, typing.Any]]]]] = None,
        environment: typing.Optional[builtins.str] = None,
        ignore_no_op_changes: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        maximum_busy_retry_attempts: typing.Optional[jsii.Number] = None,
        oidc_azure_service_connection_id: typing.Optional[builtins.str] = None,
        oidc_request_token: typing.Optional[builtins.str] = None,
        oidc_request_url: typing.Optional[builtins.str] = None,
        oidc_token: typing.Optional[builtins.str] = None,
        oidc_token_file_path: typing.Optional[builtins.str] = None,
        partner_id: typing.Optional[builtins.str] = None,
        skip_provider_registration: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        subscription_id: typing.Optional[builtins.str] = None,
        tenant_id: typing.Optional[builtins.str] = None,
        use_aks_workload_identity: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        use_cli: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        use_msi: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        use_oidc: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ) -> None:
        '''
        :param alias: Alias name. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#alias AzapiProvider#alias}
        :param auxiliary_tenant_ids: List of auxiliary Tenant IDs required for multi-tenancy and cross-tenant scenarios. This can also be sourced from the ``ARM_AUXILIARY_TENANT_IDS`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#auxiliary_tenant_ids AzapiProvider#auxiliary_tenant_ids}
        :param client_certificate: A base64-encoded PKCS#12 bundle to be used as the client certificate for authentication. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE`` environment variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate AzapiProvider#client_certificate}
        :param client_certificate_password: The password associated with the Client Certificate. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE_PASSWORD`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate_password AzapiProvider#client_certificate_password}
        :param client_certificate_path: The path to the Client Certificate associated with the Service Principal which should be used. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE_PATH`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate_path AzapiProvider#client_certificate_path}
        :param client_id: The Client ID which should be used. This can also be sourced from the ``ARM_CLIENT_ID``, ``AZURE_CLIENT_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_id AzapiProvider#client_id}
        :param client_id_file_path: The path to a file containing the Client ID which should be used. This can also be sourced from the ``ARM_CLIENT_ID_FILE_PATH`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_id_file_path AzapiProvider#client_id_file_path}
        :param client_secret: The Client Secret which should be used. This can also be sourced from the ``ARM_CLIENT_SECRET`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_secret AzapiProvider#client_secret}
        :param client_secret_file_path: The path to a file containing the Client Secret which should be used. For use When authenticating as a Service Principal using a Client Secret. This can also be sourced from the ``ARM_CLIENT_SECRET_FILE_PATH`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_secret_file_path AzapiProvider#client_secret_file_path}
        :param custom_correlation_request_id: The value of the ``x-ms-correlation-request-id`` header, otherwise an auto-generated UUID will be used. This can also be sourced from the ``ARM_CORRELATION_REQUEST_ID`` environment variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#custom_correlation_request_id AzapiProvider#custom_correlation_request_id}
        :param default_location: The default Azure Region where the azure resource should exist. The ``location`` in each resource block can override the ``default_location``. Changing this forces new resources to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_location AzapiProvider#default_location}
        :param default_name: The default name to create the azure resource. The ``name`` in each resource block can override the ``default_name``. Changing this forces new resources to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_name AzapiProvider#default_name}
        :param default_tags: A mapping of tags which should be assigned to the azure resource as default tags. The``tags`` in each resource block can override the ``default_tags``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_tags AzapiProvider#default_tags}
        :param disable_correlation_request_id: This will disable the x-ms-correlation-request-id header. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_correlation_request_id AzapiProvider#disable_correlation_request_id}
        :param disable_default_output: Disable default output. The default is false. When set to false, the provider will output the read-only properties if ``response_export_values`` is not specified in the resource block. When set to true, the provider will disable this output. This can also be sourced from the ``ARM_DISABLE_DEFAULT_OUTPUT`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_default_output AzapiProvider#disable_default_output}
        :param disable_instance_discovery: Disables Instance Discovery, which validates that the Authority is valid and known by the Microsoft Entra instance metadata service at ``https://login.microsoft.com`` before authenticating. This should only be enabled when the configured authority is known to be valid and trustworthy - such as when running against Azure Stack or when ``environment`` is set to ``custom``. This can also be specified via the ``ARM_DISABLE_INSTANCE_DISCOVERY`` environment variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_instance_discovery AzapiProvider#disable_instance_discovery}
        :param disable_terraform_partner_id: Disable sending the Terraform Partner ID if a custom ``partner_id`` isn't specified, which allows Microsoft to better understand the usage of Terraform. The Partner ID does not give HashiCorp any direct access to usage information. This can also be sourced from the ``ARM_DISABLE_TERRAFORM_PARTNER_ID`` environment variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_terraform_partner_id AzapiProvider#disable_terraform_partner_id}
        :param enable_preflight: Enable Preflight Validation. The default is false. When set to true, the provider will use Preflight to do static validation before really deploying a new resource. When set to false, the provider will disable this validation. This can also be sourced from the ``ARM_ENABLE_PREFLIGHT`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#enable_preflight AzapiProvider#enable_preflight}
        :param endpoint: The Azure API Endpoint Configuration. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#endpoint AzapiProvider#endpoint}
        :param environment: The Cloud Environment which should be used. Possible values are ``public``, ``usgovernment``, ``china`` and ``custom``. Defaults to ``public``. This can also be sourced from the ``ARM_ENVIRONMENT`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#environment AzapiProvider#environment}
        :param ignore_no_op_changes: Ignore no-op changes for ``azapi_resource``. The default is true. When set to true, the provider will suppress changes in the ``azapi_resource`` if the ``body`` in the new API version still matches the remote state. When set to false, the provider will not suppress these changes. This can also be sourced from the ``ARM_IGNORE_NO_OP_CHANGES`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#ignore_no_op_changes AzapiProvider#ignore_no_op_changes}
        :param maximum_busy_retry_attempts: DEPRECATED - The maximum number of retries to attempt if the Azure API returns an HTTP 408, 429, 500, 502, 503, or 504 response. The default is ``32767``, this allows the provider to rely on the resource timeout values rather than a maximum retry count. The resource-specific retry configuration may additionally be used to retry on other errors and conditions. This property will be removed in a future version. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#maximum_busy_retry_attempts AzapiProvider#maximum_busy_retry_attempts}
        :param oidc_azure_service_connection_id: The Azure Pipelines Service Connection ID to use for authentication. This can also be sourced from the ``ARM_ADO_PIPELINE_SERVICE_CONNECTION_ID``, ``ARM_OIDC_AZURE_SERVICE_CONNECTION_ID``, or ``AZURESUBSCRIPTION_SERVICE_CONNECTION_ID`` Environment Variables. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_azure_service_connection_id AzapiProvider#oidc_azure_service_connection_id}
        :param oidc_request_token: The bearer token for the request to the OIDC provider. This can also be sourced from the ``ARM_OIDC_REQUEST_TOKEN``, ``ACTIONS_ID_TOKEN_REQUEST_TOKEN``, or ``SYSTEM_ACCESSTOKEN`` Environment Variables. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_request_token AzapiProvider#oidc_request_token}
        :param oidc_request_url: The URL for the OIDC provider from which to request an ID token. This can also be sourced from the ``ARM_OIDC_REQUEST_URL``, ``ACTIONS_ID_TOKEN_REQUEST_URL``, or ``SYSTEM_OIDCREQUESTURI`` Environment Variables. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_request_url AzapiProvider#oidc_request_url}
        :param oidc_token: The ID token when authenticating using OpenID Connect (OIDC). This can also be sourced from the ``ARM_OIDC_TOKEN`` environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_token AzapiProvider#oidc_token}
        :param oidc_token_file_path: The path to a file containing an ID token when authenticating using OpenID Connect (OIDC). This can also be sourced from the ``ARM_OIDC_TOKEN_FILE_PATH``, ``AZURE_FEDERATED_TOKEN_FILE`` environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_token_file_path AzapiProvider#oidc_token_file_path}
        :param partner_id: A GUID/UUID that is `registered <https://docs.microsoft.com/azure/marketplace/azure-partner-customer-usage-attribution#register-guids-and-offers>`_ with Microsoft to facilitate partner resource usage attribution. This can also be sourced from the ``ARM_PARTNER_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#partner_id AzapiProvider#partner_id}
        :param skip_provider_registration: Should the Provider skip registering the Resource Providers it supports? This can also be sourced from the ``ARM_SKIP_PROVIDER_REGISTRATION`` Environment Variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#skip_provider_registration AzapiProvider#skip_provider_registration}
        :param subscription_id: The Subscription ID which should be used. This can also be sourced from the ``ARM_SUBSCRIPTION_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#subscription_id AzapiProvider#subscription_id}
        :param tenant_id: The Tenant ID should be used. This can also be sourced from the ``ARM_TENANT_ID`` Environment Variable. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#tenant_id AzapiProvider#tenant_id}
        :param use_aks_workload_identity: Should AKS Workload Identity be used for Authentication? This can also be sourced from the ``ARM_USE_AKS_WORKLOAD_IDENTITY`` Environment Variable. Defaults to ``false``. When set, ``client_id``, ``tenant_id`` and ``oidc_token_file_path`` will be detected from the environment and do not need to be specified. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_aks_workload_identity AzapiProvider#use_aks_workload_identity}
        :param use_cli: Should Azure CLI be used for authentication? This can also be sourced from the ``ARM_USE_CLI`` environment variable. Defaults to ``true``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_cli AzapiProvider#use_cli}
        :param use_msi: Should Managed Identity be used for Authentication? This can also be sourced from the ``ARM_USE_MSI`` Environment Variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_msi AzapiProvider#use_msi}
        :param use_oidc: Should OIDC be used for Authentication? This can also be sourced from the ``ARM_USE_OIDC`` Environment Variable. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_oidc AzapiProvider#use_oidc}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5c2d9ce1864149731ee5f4d20a3601e0f1e161198cb204166cbe6a14c60dee57)
            check_type(argname="argument alias", value=alias, expected_type=type_hints["alias"])
            check_type(argname="argument auxiliary_tenant_ids", value=auxiliary_tenant_ids, expected_type=type_hints["auxiliary_tenant_ids"])
            check_type(argname="argument client_certificate", value=client_certificate, expected_type=type_hints["client_certificate"])
            check_type(argname="argument client_certificate_password", value=client_certificate_password, expected_type=type_hints["client_certificate_password"])
            check_type(argname="argument client_certificate_path", value=client_certificate_path, expected_type=type_hints["client_certificate_path"])
            check_type(argname="argument client_id", value=client_id, expected_type=type_hints["client_id"])
            check_type(argname="argument client_id_file_path", value=client_id_file_path, expected_type=type_hints["client_id_file_path"])
            check_type(argname="argument client_secret", value=client_secret, expected_type=type_hints["client_secret"])
            check_type(argname="argument client_secret_file_path", value=client_secret_file_path, expected_type=type_hints["client_secret_file_path"])
            check_type(argname="argument custom_correlation_request_id", value=custom_correlation_request_id, expected_type=type_hints["custom_correlation_request_id"])
            check_type(argname="argument default_location", value=default_location, expected_type=type_hints["default_location"])
            check_type(argname="argument default_name", value=default_name, expected_type=type_hints["default_name"])
            check_type(argname="argument default_tags", value=default_tags, expected_type=type_hints["default_tags"])
            check_type(argname="argument disable_correlation_request_id", value=disable_correlation_request_id, expected_type=type_hints["disable_correlation_request_id"])
            check_type(argname="argument disable_default_output", value=disable_default_output, expected_type=type_hints["disable_default_output"])
            check_type(argname="argument disable_instance_discovery", value=disable_instance_discovery, expected_type=type_hints["disable_instance_discovery"])
            check_type(argname="argument disable_terraform_partner_id", value=disable_terraform_partner_id, expected_type=type_hints["disable_terraform_partner_id"])
            check_type(argname="argument enable_preflight", value=enable_preflight, expected_type=type_hints["enable_preflight"])
            check_type(argname="argument endpoint", value=endpoint, expected_type=type_hints["endpoint"])
            check_type(argname="argument environment", value=environment, expected_type=type_hints["environment"])
            check_type(argname="argument ignore_no_op_changes", value=ignore_no_op_changes, expected_type=type_hints["ignore_no_op_changes"])
            check_type(argname="argument maximum_busy_retry_attempts", value=maximum_busy_retry_attempts, expected_type=type_hints["maximum_busy_retry_attempts"])
            check_type(argname="argument oidc_azure_service_connection_id", value=oidc_azure_service_connection_id, expected_type=type_hints["oidc_azure_service_connection_id"])
            check_type(argname="argument oidc_request_token", value=oidc_request_token, expected_type=type_hints["oidc_request_token"])
            check_type(argname="argument oidc_request_url", value=oidc_request_url, expected_type=type_hints["oidc_request_url"])
            check_type(argname="argument oidc_token", value=oidc_token, expected_type=type_hints["oidc_token"])
            check_type(argname="argument oidc_token_file_path", value=oidc_token_file_path, expected_type=type_hints["oidc_token_file_path"])
            check_type(argname="argument partner_id", value=partner_id, expected_type=type_hints["partner_id"])
            check_type(argname="argument skip_provider_registration", value=skip_provider_registration, expected_type=type_hints["skip_provider_registration"])
            check_type(argname="argument subscription_id", value=subscription_id, expected_type=type_hints["subscription_id"])
            check_type(argname="argument tenant_id", value=tenant_id, expected_type=type_hints["tenant_id"])
            check_type(argname="argument use_aks_workload_identity", value=use_aks_workload_identity, expected_type=type_hints["use_aks_workload_identity"])
            check_type(argname="argument use_cli", value=use_cli, expected_type=type_hints["use_cli"])
            check_type(argname="argument use_msi", value=use_msi, expected_type=type_hints["use_msi"])
            check_type(argname="argument use_oidc", value=use_oidc, expected_type=type_hints["use_oidc"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if alias is not None:
            self._values["alias"] = alias
        if auxiliary_tenant_ids is not None:
            self._values["auxiliary_tenant_ids"] = auxiliary_tenant_ids
        if client_certificate is not None:
            self._values["client_certificate"] = client_certificate
        if client_certificate_password is not None:
            self._values["client_certificate_password"] = client_certificate_password
        if client_certificate_path is not None:
            self._values["client_certificate_path"] = client_certificate_path
        if client_id is not None:
            self._values["client_id"] = client_id
        if client_id_file_path is not None:
            self._values["client_id_file_path"] = client_id_file_path
        if client_secret is not None:
            self._values["client_secret"] = client_secret
        if client_secret_file_path is not None:
            self._values["client_secret_file_path"] = client_secret_file_path
        if custom_correlation_request_id is not None:
            self._values["custom_correlation_request_id"] = custom_correlation_request_id
        if default_location is not None:
            self._values["default_location"] = default_location
        if default_name is not None:
            self._values["default_name"] = default_name
        if default_tags is not None:
            self._values["default_tags"] = default_tags
        if disable_correlation_request_id is not None:
            self._values["disable_correlation_request_id"] = disable_correlation_request_id
        if disable_default_output is not None:
            self._values["disable_default_output"] = disable_default_output
        if disable_instance_discovery is not None:
            self._values["disable_instance_discovery"] = disable_instance_discovery
        if disable_terraform_partner_id is not None:
            self._values["disable_terraform_partner_id"] = disable_terraform_partner_id
        if enable_preflight is not None:
            self._values["enable_preflight"] = enable_preflight
        if endpoint is not None:
            self._values["endpoint"] = endpoint
        if environment is not None:
            self._values["environment"] = environment
        if ignore_no_op_changes is not None:
            self._values["ignore_no_op_changes"] = ignore_no_op_changes
        if maximum_busy_retry_attempts is not None:
            self._values["maximum_busy_retry_attempts"] = maximum_busy_retry_attempts
        if oidc_azure_service_connection_id is not None:
            self._values["oidc_azure_service_connection_id"] = oidc_azure_service_connection_id
        if oidc_request_token is not None:
            self._values["oidc_request_token"] = oidc_request_token
        if oidc_request_url is not None:
            self._values["oidc_request_url"] = oidc_request_url
        if oidc_token is not None:
            self._values["oidc_token"] = oidc_token
        if oidc_token_file_path is not None:
            self._values["oidc_token_file_path"] = oidc_token_file_path
        if partner_id is not None:
            self._values["partner_id"] = partner_id
        if skip_provider_registration is not None:
            self._values["skip_provider_registration"] = skip_provider_registration
        if subscription_id is not None:
            self._values["subscription_id"] = subscription_id
        if tenant_id is not None:
            self._values["tenant_id"] = tenant_id
        if use_aks_workload_identity is not None:
            self._values["use_aks_workload_identity"] = use_aks_workload_identity
        if use_cli is not None:
            self._values["use_cli"] = use_cli
        if use_msi is not None:
            self._values["use_msi"] = use_msi
        if use_oidc is not None:
            self._values["use_oidc"] = use_oidc

    @builtins.property
    def alias(self) -> typing.Optional[builtins.str]:
        '''Alias name.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#alias AzapiProvider#alias}
        '''
        result = self._values.get("alias")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def auxiliary_tenant_ids(self) -> typing.Optional[typing.List[builtins.str]]:
        '''List of auxiliary Tenant IDs required for multi-tenancy and cross-tenant scenarios.

        This can also be sourced from the ``ARM_AUXILIARY_TENANT_IDS`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#auxiliary_tenant_ids AzapiProvider#auxiliary_tenant_ids}
        '''
        result = self._values.get("auxiliary_tenant_ids")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def client_certificate(self) -> typing.Optional[builtins.str]:
        '''A base64-encoded PKCS#12 bundle to be used as the client certificate for authentication.

        This can also be sourced from the ``ARM_CLIENT_CERTIFICATE`` environment variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate AzapiProvider#client_certificate}
        '''
        result = self._values.get("client_certificate")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def client_certificate_password(self) -> typing.Optional[builtins.str]:
        '''The password associated with the Client Certificate. This can also be sourced from the ``ARM_CLIENT_CERTIFICATE_PASSWORD`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate_password AzapiProvider#client_certificate_password}
        '''
        result = self._values.get("client_certificate_password")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def client_certificate_path(self) -> typing.Optional[builtins.str]:
        '''The path to the Client Certificate associated with the Service Principal which should be used.

        This can also be sourced from the ``ARM_CLIENT_CERTIFICATE_PATH`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_certificate_path AzapiProvider#client_certificate_path}
        '''
        result = self._values.get("client_certificate_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def client_id(self) -> typing.Optional[builtins.str]:
        '''The Client ID which should be used. This can also be sourced from the ``ARM_CLIENT_ID``, ``AZURE_CLIENT_ID`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_id AzapiProvider#client_id}
        '''
        result = self._values.get("client_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def client_id_file_path(self) -> typing.Optional[builtins.str]:
        '''The path to a file containing the Client ID which should be used.

        This can also be sourced from the ``ARM_CLIENT_ID_FILE_PATH`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_id_file_path AzapiProvider#client_id_file_path}
        '''
        result = self._values.get("client_id_file_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def client_secret(self) -> typing.Optional[builtins.str]:
        '''The Client Secret which should be used. This can also be sourced from the ``ARM_CLIENT_SECRET`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_secret AzapiProvider#client_secret}
        '''
        result = self._values.get("client_secret")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def client_secret_file_path(self) -> typing.Optional[builtins.str]:
        '''The path to a file containing the Client Secret which should be used.

        For use When authenticating as a Service Principal using a Client Secret. This can also be sourced from the ``ARM_CLIENT_SECRET_FILE_PATH`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#client_secret_file_path AzapiProvider#client_secret_file_path}
        '''
        result = self._values.get("client_secret_file_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def custom_correlation_request_id(self) -> typing.Optional[builtins.str]:
        '''The value of the ``x-ms-correlation-request-id`` header, otherwise an auto-generated UUID will be used.

        This can also be sourced from the ``ARM_CORRELATION_REQUEST_ID`` environment variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#custom_correlation_request_id AzapiProvider#custom_correlation_request_id}
        '''
        result = self._values.get("custom_correlation_request_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def default_location(self) -> typing.Optional[builtins.str]:
        '''The default Azure Region where the azure resource should exist.

        The ``location`` in each resource block can override the ``default_location``. Changing this forces new resources to be created.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_location AzapiProvider#default_location}
        '''
        result = self._values.get("default_location")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def default_name(self) -> typing.Optional[builtins.str]:
        '''The default name to create the azure resource.

        The ``name`` in each resource block can override the ``default_name``. Changing this forces new resources to be created.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_name AzapiProvider#default_name}
        '''
        result = self._values.get("default_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def default_tags(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of tags which should be assigned to the azure resource as default tags.

        The``tags`` in each resource block can override the ``default_tags``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#default_tags AzapiProvider#default_tags}
        '''
        result = self._values.get("default_tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def disable_correlation_request_id(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''This will disable the x-ms-correlation-request-id header.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_correlation_request_id AzapiProvider#disable_correlation_request_id}
        '''
        result = self._values.get("disable_correlation_request_id")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def disable_default_output(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Disable default output.

        The default is false. When set to false, the provider will output the read-only properties if ``response_export_values`` is not specified in the resource block. When set to true, the provider will disable this output. This can also be sourced from the ``ARM_DISABLE_DEFAULT_OUTPUT`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_default_output AzapiProvider#disable_default_output}
        '''
        result = self._values.get("disable_default_output")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def disable_instance_discovery(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Disables Instance Discovery, which validates that the Authority is valid and known by the Microsoft Entra instance metadata service at ``https://login.microsoft.com`` before authenticating. This should only be enabled when the configured authority is known to be valid and trustworthy - such as when running against Azure Stack or when ``environment`` is set to ``custom``. This can also be specified via the ``ARM_DISABLE_INSTANCE_DISCOVERY`` environment variable. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_instance_discovery AzapiProvider#disable_instance_discovery}
        '''
        result = self._values.get("disable_instance_discovery")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def disable_terraform_partner_id(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Disable sending the Terraform Partner ID if a custom ``partner_id`` isn't specified, which allows Microsoft to better understand the usage of Terraform.

        The Partner ID does not give HashiCorp any direct access to usage information. This can also be sourced from the ``ARM_DISABLE_TERRAFORM_PARTNER_ID`` environment variable. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#disable_terraform_partner_id AzapiProvider#disable_terraform_partner_id}
        '''
        result = self._values.get("disable_terraform_partner_id")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def enable_preflight(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Enable Preflight Validation.

        The default is false. When set to true, the provider will use Preflight to do static validation before really deploying a new resource. When set to false, the provider will disable this validation. This can also be sourced from the ``ARM_ENABLE_PREFLIGHT`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#enable_preflight AzapiProvider#enable_preflight}
        '''
        result = self._values.get("enable_preflight")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def endpoint(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]]:
        '''The Azure API Endpoint Configuration.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#endpoint AzapiProvider#endpoint}
        '''
        result = self._values.get("endpoint")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]], result)

    @builtins.property
    def environment(self) -> typing.Optional[builtins.str]:
        '''The Cloud Environment which should be used.

        Possible values are ``public``, ``usgovernment``, ``china`` and ``custom``. Defaults to ``public``. This can also be sourced from the ``ARM_ENVIRONMENT`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#environment AzapiProvider#environment}
        '''
        result = self._values.get("environment")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def ignore_no_op_changes(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Ignore no-op changes for ``azapi_resource``.

        The default is true. When set to true, the provider will suppress changes in the ``azapi_resource`` if the ``body`` in the new API version still matches the remote state. When set to false, the provider will not suppress these changes. This can also be sourced from the ``ARM_IGNORE_NO_OP_CHANGES`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#ignore_no_op_changes AzapiProvider#ignore_no_op_changes}
        '''
        result = self._values.get("ignore_no_op_changes")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def maximum_busy_retry_attempts(self) -> typing.Optional[jsii.Number]:
        '''DEPRECATED - The maximum number of retries to attempt if the Azure API returns an HTTP 408, 429, 500, 502, 503, or 504 response.

        The default is ``32767``, this allows the provider to rely on the resource timeout values rather than a maximum retry count. The resource-specific retry configuration may additionally be used to retry on other errors and conditions. This property will be removed in a future version.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#maximum_busy_retry_attempts AzapiProvider#maximum_busy_retry_attempts}
        '''
        result = self._values.get("maximum_busy_retry_attempts")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def oidc_azure_service_connection_id(self) -> typing.Optional[builtins.str]:
        '''The Azure Pipelines Service Connection ID to use for authentication.

        This can also be sourced from the ``ARM_ADO_PIPELINE_SERVICE_CONNECTION_ID``, ``ARM_OIDC_AZURE_SERVICE_CONNECTION_ID``, or ``AZURESUBSCRIPTION_SERVICE_CONNECTION_ID`` Environment Variables.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_azure_service_connection_id AzapiProvider#oidc_azure_service_connection_id}
        '''
        result = self._values.get("oidc_azure_service_connection_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_request_token(self) -> typing.Optional[builtins.str]:
        '''The bearer token for the request to the OIDC provider.

        This can also be sourced from the ``ARM_OIDC_REQUEST_TOKEN``, ``ACTIONS_ID_TOKEN_REQUEST_TOKEN``, or ``SYSTEM_ACCESSTOKEN`` Environment Variables.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_request_token AzapiProvider#oidc_request_token}
        '''
        result = self._values.get("oidc_request_token")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_request_url(self) -> typing.Optional[builtins.str]:
        '''The URL for the OIDC provider from which to request an ID token.

        This can also be sourced from the ``ARM_OIDC_REQUEST_URL``, ``ACTIONS_ID_TOKEN_REQUEST_URL``, or ``SYSTEM_OIDCREQUESTURI`` Environment Variables.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_request_url AzapiProvider#oidc_request_url}
        '''
        result = self._values.get("oidc_request_url")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_token(self) -> typing.Optional[builtins.str]:
        '''The ID token when authenticating using OpenID Connect (OIDC). This can also be sourced from the ``ARM_OIDC_TOKEN`` environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_token AzapiProvider#oidc_token}
        '''
        result = self._values.get("oidc_token")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def oidc_token_file_path(self) -> typing.Optional[builtins.str]:
        '''The path to a file containing an ID token when authenticating using OpenID Connect (OIDC).

        This can also be sourced from the ``ARM_OIDC_TOKEN_FILE_PATH``, ``AZURE_FEDERATED_TOKEN_FILE`` environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#oidc_token_file_path AzapiProvider#oidc_token_file_path}
        '''
        result = self._values.get("oidc_token_file_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def partner_id(self) -> typing.Optional[builtins.str]:
        '''A GUID/UUID that is `registered <https://docs.microsoft.com/azure/marketplace/azure-partner-customer-usage-attribution#register-guids-and-offers>`_ with Microsoft to facilitate partner resource usage attribution. This can also be sourced from the ``ARM_PARTNER_ID`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#partner_id AzapiProvider#partner_id}
        '''
        result = self._values.get("partner_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def skip_provider_registration(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Should the Provider skip registering the Resource Providers it supports?

        This can also be sourced from the ``ARM_SKIP_PROVIDER_REGISTRATION`` Environment Variable. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#skip_provider_registration AzapiProvider#skip_provider_registration}
        '''
        result = self._values.get("skip_provider_registration")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def subscription_id(self) -> typing.Optional[builtins.str]:
        '''The Subscription ID which should be used. This can also be sourced from the ``ARM_SUBSCRIPTION_ID`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#subscription_id AzapiProvider#subscription_id}
        '''
        result = self._values.get("subscription_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def tenant_id(self) -> typing.Optional[builtins.str]:
        '''The Tenant ID should be used. This can also be sourced from the ``ARM_TENANT_ID`` Environment Variable.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#tenant_id AzapiProvider#tenant_id}
        '''
        result = self._values.get("tenant_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def use_aks_workload_identity(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Should AKS Workload Identity be used for Authentication?

        This can also be sourced from the ``ARM_USE_AKS_WORKLOAD_IDENTITY`` Environment Variable. Defaults to ``false``. When set, ``client_id``, ``tenant_id`` and ``oidc_token_file_path`` will be detected from the environment and do not need to be specified.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_aks_workload_identity AzapiProvider#use_aks_workload_identity}
        '''
        result = self._values.get("use_aks_workload_identity")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def use_cli(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Should Azure CLI be used for authentication?

        This can also be sourced from the ``ARM_USE_CLI`` environment variable. Defaults to ``true``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_cli AzapiProvider#use_cli}
        '''
        result = self._values.get("use_cli")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def use_msi(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Should Managed Identity be used for Authentication?

        This can also be sourced from the ``ARM_USE_MSI`` Environment Variable. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_msi AzapiProvider#use_msi}
        '''
        result = self._values.get("use_msi")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def use_oidc(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Should OIDC be used for Authentication? This can also be sourced from the ``ARM_USE_OIDC`` Environment Variable. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#use_oidc AzapiProvider#use_oidc}
        '''
        result = self._values.get("use_oidc")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AzapiProviderConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiProviderEndpoint",
    jsii_struct_bases=[],
    name_mapping={
        "active_directory_authority_host": "activeDirectoryAuthorityHost",
        "resource_manager_audience": "resourceManagerAudience",
        "resource_manager_endpoint": "resourceManagerEndpoint",
    },
)
class AzapiProviderEndpoint:
    def __init__(
        self,
        *,
        active_directory_authority_host: typing.Optional[builtins.str] = None,
        resource_manager_audience: typing.Optional[builtins.str] = None,
        resource_manager_endpoint: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param active_directory_authority_host: The Azure Active Directory login endpoint to use. This can also be sourced from the ``ARM_ACTIVE_DIRECTORY_AUTHORITY_HOST`` Environment Variable. Defaults to ``https://login.microsoftonline.com/`` for public cloud. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#active_directory_authority_host AzapiProvider#active_directory_authority_host}
        :param resource_manager_audience: The resource ID to obtain AD tokens for. This can also be sourced from the ``ARM_RESOURCE_MANAGER_AUDIENCE`` Environment Variable. Defaults to ``https://management.core.windows.net/`` for public cloud. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#resource_manager_audience AzapiProvider#resource_manager_audience}
        :param resource_manager_endpoint: The Azure Resource Manager endpoint to use. This can also be sourced from the ``ARM_RESOURCE_MANAGER_ENDPOINT`` Environment Variable. Defaults to ``https://management.azure.com/`` for public cloud. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#resource_manager_endpoint AzapiProvider#resource_manager_endpoint}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__830572394f7c616e27c3a43fd25c5db052d11cd675b3f460dafa8aa610b638e5)
            check_type(argname="argument active_directory_authority_host", value=active_directory_authority_host, expected_type=type_hints["active_directory_authority_host"])
            check_type(argname="argument resource_manager_audience", value=resource_manager_audience, expected_type=type_hints["resource_manager_audience"])
            check_type(argname="argument resource_manager_endpoint", value=resource_manager_endpoint, expected_type=type_hints["resource_manager_endpoint"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if active_directory_authority_host is not None:
            self._values["active_directory_authority_host"] = active_directory_authority_host
        if resource_manager_audience is not None:
            self._values["resource_manager_audience"] = resource_manager_audience
        if resource_manager_endpoint is not None:
            self._values["resource_manager_endpoint"] = resource_manager_endpoint

    @builtins.property
    def active_directory_authority_host(self) -> typing.Optional[builtins.str]:
        '''The Azure Active Directory login endpoint to use.

        This can also be sourced from the ``ARM_ACTIVE_DIRECTORY_AUTHORITY_HOST`` Environment Variable. Defaults to ``https://login.microsoftonline.com/`` for public cloud.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#active_directory_authority_host AzapiProvider#active_directory_authority_host}
        '''
        result = self._values.get("active_directory_authority_host")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def resource_manager_audience(self) -> typing.Optional[builtins.str]:
        '''The resource ID to obtain AD tokens for.

        This can also be sourced from the ``ARM_RESOURCE_MANAGER_AUDIENCE`` Environment Variable. Defaults to ``https://management.core.windows.net/`` for public cloud.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#resource_manager_audience AzapiProvider#resource_manager_audience}
        '''
        result = self._values.get("resource_manager_audience")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def resource_manager_endpoint(self) -> typing.Optional[builtins.str]:
        '''The Azure Resource Manager endpoint to use.

        This can also be sourced from the ``ARM_RESOURCE_MANAGER_ENDPOINT`` Environment Variable. Defaults to ``https://management.azure.com/`` for public cloud.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs#resource_manager_endpoint AzapiProvider#resource_manager_endpoint}
        '''
        result = self._values.get("resource_manager_endpoint")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AzapiProviderEndpoint(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AzapiResource(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIAbstractClass,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiResource",
):
    '''Abstract base class for version-aware Azure resource management.

    AzapiResource provides a unified framework for creating Azure resources
    with automatic version management, schema validation, property transformation,
    and migration analysis. It extends the existing AzapiResource class while
    maintaining full backward compatibility.

    This class implements the core framework that enables:

    - Automatic resolution of the latest API version when none is specified
    - Explicit version pinning for environments requiring stability
    - Schema-driven property validation and transformation
    - Migration analysis with breaking change detection
    - Deprecation warnings and upgrade recommendations

    Subclasses must implement the abstract methods to provide resource-specific
    configuration while the framework handles all version management complexity.

    Example::

        Usage with explicit version pinning:
        new MyResource(this, "resource", {
        name: "my-resource",
        location: "eastus",
        apiVersion: "2024-01-01" // Pin to specific version
        });
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        api_version: typing.Optional[builtins.str] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        location: typing.Optional[builtins.str] = None,
        monitoring: typing.Optional[typing.Union["MonitoringConfig", typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Creates a new AzapiResource instance.

        The constructor handles all framework initialization including version resolution,
        schema loading, property validation, transformation, and migration analysis.
        It maintains full backward compatibility with the AzapiResource constructor.

        :param scope: - The scope in which to define this construct.
        :param id: - The unique identifier for this instance.
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
            type_hints = typing.get_type_hints(_typecheckingstub__a4721714cda0833dfab6bea66f4fcdda2ddd209c9d016453c0d10e942d7f8e6f)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AzapiResourceProps(
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

    @jsii.member(jsii_name="registerSchemas")
    @builtins.classmethod
    def register_schemas(
        cls,
        resource_type: builtins.str,
        versions: typing.Sequence[typing.Union["VersionConfig", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''Static helper for child classes to register their schemas in static initializers.

        This method should be called in a static initializer block of each child class
        to register all supported API versions and their schemas with the ApiVersionManager.
        The static block runs once when the class is first loaded, ensuring schemas are
        registered before any instances are created.

        :param resource_type: - The Azure resource type (e.g., "Microsoft.Network/virtualNetworks").
        :param versions: - Array of version configurations containing schemas.

        Example::

            static {
              AzapiResource.registerSchemas(
                "Microsoft.Network/virtualNetworks",
                ALL_VIRTUAL_NETWORK_VERSIONS
              );
            }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c9d77099c005d007eb35d3e704837eca906f47188729a0d22306b01d1cc5bcc7)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument versions", value=versions, expected_type=type_hints["versions"])
        return typing.cast(None, jsii.sinvoke(cls, "registerSchemas", [resource_type, versions]))

    @jsii.member(jsii_name="addAccess")
    def add_access(
        self,
        object_id: builtins.str,
        role_definition_name: builtins.str,
    ) -> None:
        '''Adds an access role assignment for a specified Azure AD object.

        Note: This method creates role assignments using AZAPI instead of AzureRM provider.

        :param object_id: - The unique identifier of the Azure AD object.
        :param role_definition_name: - The name of the Azure RBAC role to be assigned.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e3c6d0bbaaddfb2eb45725897b5741efcaafb15d11569a8c6ca43aec008d6f9)
            check_type(argname="argument object_id", value=object_id, expected_type=type_hints["object_id"])
            check_type(argname="argument role_definition_name", value=role_definition_name, expected_type=type_hints["role_definition_name"])
        return typing.cast(None, jsii.invoke(self, "addAccess", [object_id, role_definition_name]))

    @jsii.member(jsii_name="addTag")
    def add_tag(self, key: builtins.str, value: builtins.str) -> None:
        '''Adds a tag to this resource. The tag will be included in the Azure resource.

        This method provides proper immutability by storing tags separately from props.
        Tags added via this method are combined with tags from props and included in
        the deployed Azure resource.

        **Important:** In CDK for Terraform, tags should ideally be set during resource
        construction via props. While this method allows adding tags after construction,
        those tags are only included if added before the Terraform configuration is
        synthesized. For best results, add all tags via props or call addTag() in the
        same scope where the resource is created.

        :param key: - The tag key.
        :param value: - The tag value.

        :throws: Error if the resource type does not support tags
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d90d32b2c297a1cdd94e973a7a8ed52e0f58c521022cf8be08b469c16c969fa6)
            check_type(argname="argument key", value=key, expected_type=type_hints["key"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "addTag", [key, value]))

    @jsii.member(jsii_name="allTags")
    def _all_tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''Protected method to retrieve all tags for use in createResourceBody implementations.

        Subclasses should use this method when creating resource bodies to ensure
        all tags (from props and addTag()) are included in the Azure resource.
        Uses a non-getter name to avoid JSII conflicts with the tags property.

        :return: Object containing all tags
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.invoke(self, "allTags", []))

    @jsii.member(jsii_name="analyzeMigrationTo")
    def analyze_migration_to(self, target_version: builtins.str) -> "MigrationAnalysis":
        '''Analyzes migration from current version to a target version.

        This method enables external tools to analyze migration requirements
        between versions for planning and automation purposes.

        :param target_version: - The target version to analyze migration to.

        :return: Detailed migration analysis results
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eced9286cb219641203ebbff3ce49fce70e326392feac6f14f6120bcd29842c0)
            check_type(argname="argument target_version", value=target_version, expected_type=type_hints["target_version"])
        return typing.cast("MigrationAnalysis", jsii.invoke(self, "analyzeMigrationTo", [target_version]))

    @jsii.member(jsii_name="apiSchema")
    @abc.abstractmethod
    def _api_schema(self) -> ApiSchema:
        '''Gets the API schema for the resolved version.

        This method should return the complete API schema for the resolved version,
        including all property definitions, validation rules, and transformation
        mappings. Use the resolveSchema() helper method for standard schema resolution.

        :return: The API schema for the resolved version
        '''
        ...

    @jsii.member(jsii_name="createAzapiDataSource")
    def _create_azapi_data_source(
        self,
        resource_id: builtins.str,
    ) -> _cdktf_9a9027ec.TerraformDataSource:
        '''Creates an AZAPI data source for reading existing resources.

        :param resource_id: - The full resource ID.

        :return: The created Terraform data source
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__755d63a36b48dbba857c45666e500c94186ae6d8c99bdb8998197d9dc7173bed)
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
        return typing.cast(_cdktf_9a9027ec.TerraformDataSource, jsii.invoke(self, "createAzapiDataSource", [resource_id]))

    @jsii.member(jsii_name="createAzapiResource")
    def _create_azapi_resource(
        self,
        properties: typing.Mapping[builtins.str, typing.Any],
        parent_id: builtins.str,
        name: builtins.str,
        location: typing.Optional[builtins.str] = None,
        parent_resource: typing.Optional["AzapiResource"] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> _cdktf_9a9027ec.TerraformResource:
        '''Creates the underlying AZAPI Terraform resource using the generated provider classes.

        :param properties: - The properties object to send to the Azure API (should include location if needed).
        :param parent_id: - The parent resource ID (e.g., subscription or resource group).
        :param name: - The name of the resource.
        :param location: - The location of the resource (optional, only for top-level resources without location in body).
        :param parent_resource: - The parent resource for dependency tracking.
        :param depends_on: - Explicit dependencies for this resource.
        :param tags: - Tags to apply to the resource (passed separately from body for proper idempotency).

        :return: The created AZAPI resource
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3db285232c50fdf23460379819cb2891917267d1cb22577f50f8db0debd80b0a)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
            check_type(argname="argument parent_id", value=parent_id, expected_type=type_hints["parent_id"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument parent_resource", value=parent_resource, expected_type=type_hints["parent_resource"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        return typing.cast(_cdktf_9a9027ec.TerraformResource, jsii.invoke(self, "createAzapiResource", [properties, parent_id, name, location, parent_resource, depends_on, tags]))

    @jsii.member(jsii_name="createMonitoringResources")
    def _create_monitoring_resources(
        self,
        *,
        action_groups: typing.Optional[typing.Sequence[typing.Union[_ActionGroupProps_572d2b68, typing.Dict[builtins.str, typing.Any]]]] = None,
        activity_log_alerts: typing.Optional[typing.Sequence[typing.Union[_ActivityLogAlertProps_f1779054, typing.Dict[builtins.str, typing.Any]]]] = None,
        diagnostic_settings: typing.Optional[typing.Union[_DiagnosticSettingsProps_cc0fa615, typing.Dict[builtins.str, typing.Any]]] = None,
        enabled: typing.Optional[builtins.bool] = None,
        metric_alerts: typing.Optional[typing.Sequence[typing.Union[_MetricAlertProps_a18d777f, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Creates monitoring resources based on the monitoring configuration.

        This method is called automatically during construction if monitoring is configured.
        It creates action groups, metric alerts, and activity log alerts as child constructs.

        Protected to allow subclasses to override or extend monitoring behavior.

        :param action_groups: Action groups to create for this resource Creates new ActionGroup instances as child constructs.
        :param activity_log_alerts: Activity log alerts configuration Creates ActivityLogAlert instances for this resource's operations.
        :param diagnostic_settings: Diagnostic settings configuration Uses the full DiagnosticSettings construct for consistency.
        :param enabled: Whether monitoring is enabled. Default: true
        :param metric_alerts: Metric alerts configuration Creates MetricAlert instances scoped to this resource.
        '''
        config = MonitoringConfig(
            action_groups=action_groups,
            activity_log_alerts=activity_log_alerts,
            diagnostic_settings=diagnostic_settings,
            enabled=enabled,
            metric_alerts=metric_alerts,
        )

        return typing.cast(None, jsii.ainvoke(self, "createMonitoringResources", [config]))

    @jsii.member(jsii_name="createResourceBody")
    @abc.abstractmethod
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call.

        This method should transform the input properties into the JSON body format
        expected by the Azure REST API for the resolved version. The framework will
        have already applied any necessary property transformations and validation.

        :param props: - The processed and validated properties for the resource.

        :return: The resource body object to send to Azure API
        '''
        ...

    @jsii.member(jsii_name="customizeResourceConfig")
    def _customize_resource_config(self, config: typing.Any) -> typing.Any:
        '''Allows child classes to customize the ResourceConfig before resource creation.

        Override this method to add resource-specific configuration like:

        - schemaValidationEnabled: false (for resources with complex nested structures)
        - ignoreMissingProperty: true (for resources with dynamic/unknown properties)
        - ignoreNullProperty: true (for resources that should skip null values)

        :param config: - The base ResourceConfig that will be used to create the resource.

        :return: The potentially modified ResourceConfig

        Example::

            protected customizeResourceConfig(config: ResourceConfig): ResourceConfig {
              return {
                ...config,
                schemaValidationEnabled: false,
                ignoreMissingProperty: true,
              };
            }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__10ba7daf985da96e3075a4105cbfd96117ade31d5e1545ad6953babac62af9f4)
            check_type(argname="argument config", value=config, expected_type=type_hints["config"])
        return typing.cast(typing.Any, jsii.invoke(self, "customizeResourceConfig", [config]))

    @jsii.member(jsii_name="defaultLocation")
    def _default_location(self) -> typing.Optional[builtins.str]:
        '''Override in child classes to provide default location.

        :return: Default location or undefined
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.invoke(self, "defaultLocation", []))

    @jsii.member(jsii_name="defaultVersion")
    @abc.abstractmethod
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.

        This method should return a sensible default version that can be used
        as a fallback if the ApiVersionManager doesn't have any versions registered
        for this resource type.

        :return: The default API version string (e.g., "2024-11-01")
        '''
        ...

    @jsii.member(jsii_name="initialize")
    def _initialize(
        self,
        *,
        api_version: typing.Optional[builtins.str] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        location: typing.Optional[builtins.str] = None,
        monitoring: typing.Optional[typing.Union["MonitoringConfig", typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Protected initialization method called after the constructor completes.

        This method is called at the end of the constructor to perform initialization
        that requires calling abstract methods. Child classes can override this method
        if they need to extend initialization logic, but they MUST call super.initialize(props).

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
        props = AzapiResourceProps(
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

        return typing.cast(None, jsii.invoke(self, "initialize", [props]))

    @jsii.member(jsii_name="latestVersion")
    def latest_version(self) -> typing.Optional[builtins.str]:
        '''Gets the latest available version for this resource type.

        This method provides access to the latest version resolution logic
        for use in subclasses or external tooling.

        :return: The latest available version, or undefined if none found
        '''
        return typing.cast(typing.Optional[builtins.str], jsii.invoke(self, "latestVersion", []))

    @jsii.member(jsii_name="parentResourceForLocation")
    def _parent_resource_for_location(self) -> typing.Optional["AzapiResource"]:
        '''Override in child classes to specify parent resource for location inheritance.

        :return: Parent resource or undefined
        '''
        return typing.cast(typing.Optional["AzapiResource"], jsii.invoke(self, "parentResourceForLocation", []))

    @jsii.member(jsii_name="requiresLocation")
    def _requires_location(self) -> builtins.bool:
        '''Override in child classes to indicate if location is required.

        :return: true if location is mandatory for this resource type
        '''
        return typing.cast(builtins.bool, jsii.invoke(self, "requiresLocation", []))

    @jsii.member(jsii_name="resolveLocation")
    def _resolve_location(
        self,
        *,
        api_version: typing.Optional[builtins.str] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        location: typing.Optional[builtins.str] = None,
        monitoring: typing.Optional[typing.Union["MonitoringConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> typing.Optional[builtins.str]:
        '''Resolves location using template method pattern Priority: props.location > parent location > default location > validation.

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
        props = AzapiResourceProps(
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

        return typing.cast(typing.Optional[builtins.str], jsii.invoke(self, "resolveLocation", [props]))

    @jsii.member(jsii_name="resolveName")
    def _resolve_name(
        self,
        *,
        api_version: typing.Optional[builtins.str] = None,
        enable_migration_analysis: typing.Optional[builtins.bool] = None,
        enable_transformation: typing.Optional[builtins.bool] = None,
        enable_validation: typing.Optional[builtins.bool] = None,
        location: typing.Optional[builtins.str] = None,
        monitoring: typing.Optional[typing.Union["MonitoringConfig", typing.Dict[builtins.str, typing.Any]]] = None,
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
        '''Resolves the name for this resource.

        This method centralizes name resolution logic. By default, it uses the
        provided name or falls back to the construct ID.

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

        :return: The resolved resource name
        '''
        props = AzapiResourceProps(
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
        '''Resolves the parent resource ID for this resource.

        Override this method in child resource classes (like Subnet) that need
        custom parent ID resolution logic. By default, this delegates to the
        private _determineParentId method which handles standard resource types.

        :param props: - The resource properties.

        :return: The parent resource ID
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8fd7d7af1b1f70a2a68d9355dfe71212e4290f9cd199ab17f1f353c9de0856f4)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(builtins.str, jsii.invoke(self, "resolveParentId", [props]))

    @jsii.member(jsii_name="resolveSchema")
    def _resolve_schema(self) -> ApiSchema:
        '''Helper method for standard schema resolution.

        Subclasses can use this method to resolve the schema for the current version
        from the ApiVersionManager. This provides a standard implementation that
        most resources can use without custom logic.

        :return: The API schema for the resolved version

        :throws: Error if the schema cannot be resolved
        '''
        return typing.cast(ApiSchema, jsii.invoke(self, "resolveSchema", []))

    @jsii.member(jsii_name="resourceType")
    @abc.abstractmethod
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for this resource.

        This method should return the full Azure resource type identifier that
        will be used for API calls and version management.

        :return: The Azure resource type (e.g., "Microsoft.Resources/resourceGroups")
        '''
        ...

    @jsii.member(jsii_name="supportedVersions")
    def supported_versions(self) -> typing.List[builtins.str]:
        '''Gets all supported versions for this resource type.

        This method provides access to the version registry for use in
        subclasses or external tooling.

        :return: Array of supported version strings, sorted by release date
        '''
        return typing.cast(typing.List[builtins.str], jsii.invoke(self, "supportedVersions", []))

    @jsii.member(jsii_name="supportsTags")
    def _supports_tags(self) -> builtins.bool:
        '''Override in child classes to indicate if the resource type supports tags Some Azure resources (e.g., Policy Definitions, Policy Assignments) do not support tags.

        :return: true if the resource supports tags (default), false otherwise
        '''
        return typing.cast(builtins.bool, jsii.invoke(self, "supportsTags", []))

    @jsii.member(jsii_name="updateAzapiResource")
    def _update_azapi_resource(
        self,
        properties: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        '''Updates the resource with new properties.

        :param properties: - The new properties to apply.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__424021683fb308922508cd77d045a339a92d97f4168a27a40c9e95c69904129d)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        return typing.cast(None, jsii.invoke(self, "updateAzapiResource", [properties]))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        '''The Azure resource ID.

        This property is automatically derived from the underlying Terraform resource.
        Child classes no longer need to implement this property.
        '''
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="monitoringActionGroups")
    def _monitoring_action_groups(self) -> typing.List[_constructs_77d1e7e8.Construct]:
        return typing.cast(typing.List[_constructs_77d1e7e8.Construct], jsii.get(self, "monitoringActionGroups"))

    @builtins.property
    @jsii.member(jsii_name="monitoringActivityLogAlerts")
    def _monitoring_activity_log_alerts(
        self,
    ) -> typing.List[_constructs_77d1e7e8.Construct]:
        return typing.cast(typing.List[_constructs_77d1e7e8.Construct], jsii.get(self, "monitoringActivityLogAlerts"))

    @builtins.property
    @jsii.member(jsii_name="monitoringMetricAlerts")
    def _monitoring_metric_alerts(self) -> typing.List[_constructs_77d1e7e8.Construct]:
        return typing.cast(typing.List[_constructs_77d1e7e8.Construct], jsii.get(self, "monitoringMetricAlerts"))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        '''The name of the resource.'''
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="output")
    def output(self) -> _cdktf_9a9027ec.TerraformOutput:
        '''Gets the resource as a Terraform output value.'''
        return typing.cast(_cdktf_9a9027ec.TerraformOutput, jsii.get(self, "output"))

    @builtins.property
    @jsii.member(jsii_name="resource")
    def resource(self) -> _cdktf_9a9027ec.TerraformResource:
        '''Gets the underlying Terraform resource for use in dependency declarations This allows explicit dependency management between resources.'''
        return typing.cast(_cdktf_9a9027ec.TerraformResource, jsii.get(self, "resource"))

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        '''Gets the full resource ID.'''
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''All tags on this resource (readonly view).

        This getter provides convenient access to all tags including those from props
        and those added dynamically via addTag(). Returns a copy to maintain immutability.
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tags"))

    @builtins.property
    @jsii.member(jsii_name="location")
    def location(self) -> typing.Optional[builtins.str]:
        '''The location of the resource (optional - not all resources have a location) Child resources typically inherit location from their parent.'''
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "location"))

    @builtins.property
    @jsii.member(jsii_name="apiVersion")
    def _api_version(self) -> builtins.str:
        '''The API version to use for this resource.'''
        return typing.cast(builtins.str, jsii.get(self, "apiVersion"))

    @_api_version.setter
    def _api_version(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5a6fc267f48e1a4b955fd59f8b54d2bcacc974d59df70195e687d6b138ae0d90)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "apiVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="resolvedApiVersion")
    def resolved_api_version(self) -> builtins.str:
        '''The resolved API version being used for this resource instance.

        This is the actual version that will be used for the Azure API call,
        either explicitly specified in props or automatically resolved to
        the latest active version.
        '''
        return typing.cast(builtins.str, jsii.get(self, "resolvedApiVersion"))

    @resolved_api_version.setter
    def resolved_api_version(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a7561d40e2812de40aeea89e1ce25d06a4c8a3de58639df6ce11265c2bdfc84c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "resolvedApiVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="schema")
    def schema(self) -> ApiSchema:
        '''The API schema for the resolved version.

        Contains the complete schema definition including properties, validation
        rules, and transformation mappings for the resolved API version.
        '''
        return typing.cast(ApiSchema, jsii.get(self, "schema"))

    @schema.setter
    def schema(self, value: ApiSchema) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__330b9f717665caf4df824d5ddf137bb83beb83acb37a2af9e63692b3c26cd8fd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "schema", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.TerraformResource:
        '''The underlying AZAPI Terraform resource.'''
        return typing.cast(_cdktf_9a9027ec.TerraformResource, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.TerraformResource) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4422d40a75fd6644d732d2f70ac2b2e20869c9df36c45d46f72995c4ef6dbb6f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="versionConfig")
    def version_config(self) -> "VersionConfig":
        '''The version configuration for the resolved version.

        Contains lifecycle information, breaking changes, and migration metadata
        for the resolved API version.
        '''
        return typing.cast("VersionConfig", jsii.get(self, "versionConfig"))

    @version_config.setter
    def version_config(self, value: "VersionConfig") -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__13cc2f6914aa6c6c86f3c1e6f152c82d7bad801ca829353201ea24e9af9c7710)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "versionConfig", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="migrationAnalysis")
    def migration_analysis(self) -> typing.Optional["MigrationAnalysis"]:
        '''Migration analysis results.

        Available after construction if migration analysis is enabled and a
        previous version can be determined for comparison.
        '''
        return typing.cast(typing.Optional["MigrationAnalysis"], jsii.get(self, "migrationAnalysis"))

    @migration_analysis.setter
    def migration_analysis(self, value: typing.Optional["MigrationAnalysis"]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a9471ff5145389f28356530f7b05ba78be0ea22b0f92f7503fd7d4a29d9382e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "migrationAnalysis", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="validationResult")
    def validation_result(self) -> typing.Optional["ValidationResult"]:
        '''Validation results for the resource properties.

        Available after construction if validation is enabled. Contains detailed
        information about any validation errors or warnings.
        '''
        return typing.cast(typing.Optional["ValidationResult"], jsii.get(self, "validationResult"))

    @validation_result.setter
    def validation_result(self, value: typing.Optional["ValidationResult"]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c897e83c2cd923993c13bfb95b002ff4fb9349b074b7b3f71846f0f205b3957d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "validationResult", value) # pyright: ignore[reportArgumentType]


class _AzapiResourceProxy(AzapiResource):
    @jsii.member(jsii_name="apiSchema")
    def _api_schema(self) -> ApiSchema:
        '''Gets the API schema for the resolved version.

        This method should return the complete API schema for the resolved version,
        including all property definitions, validation rules, and transformation
        mappings. Use the resolveSchema() helper method for standard schema resolution.

        :return: The API schema for the resolved version
        '''
        return typing.cast(ApiSchema, jsii.invoke(self, "apiSchema", []))

    @jsii.member(jsii_name="createResourceBody")
    def _create_resource_body(self, props: typing.Any) -> typing.Any:
        '''Creates the resource body for the Azure API call.

        This method should transform the input properties into the JSON body format
        expected by the Azure REST API for the resolved version. The framework will
        have already applied any necessary property transformations and validation.

        :param props: - The processed and validated properties for the resource.

        :return: The resource body object to send to Azure API
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7ee6fd8d016c3a0923c1ab35bbc84ceafc199abaaa7fcc0d3376b5f0cf1d7dfc)
            check_type(argname="argument props", value=props, expected_type=type_hints["props"])
        return typing.cast(typing.Any, jsii.invoke(self, "createResourceBody", [props]))

    @jsii.member(jsii_name="defaultVersion")
    def _default_version(self) -> builtins.str:
        '''Gets the default API version to use when no explicit version is specified.

        This method should return a sensible default version that can be used
        as a fallback if the ApiVersionManager doesn't have any versions registered
        for this resource type.

        :return: The default API version string (e.g., "2024-11-01")
        '''
        return typing.cast(builtins.str, jsii.invoke(self, "defaultVersion", []))

    @jsii.member(jsii_name="resourceType")
    def _resource_type(self) -> builtins.str:
        '''Gets the Azure resource type for this resource.

        This method should return the full Azure resource type identifier that
        will be used for API calls and version management.

        :return: The Azure resource type (e.g., "Microsoft.Resources/resourceGroups")
        '''
        return typing.cast(builtins.str, jsii.invoke(self, "resourceType", []))

# Adding a "__jsii_proxy_class__(): typing.Type" function to the abstract class
typing.cast(typing.Any, AzapiResource).__jsii_proxy_class__ = lambda : _AzapiResourceProxy


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiResourceProps",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
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
    },
)
class AzapiResourceProps(_cdktf_9a9027ec.TerraformMetaArguments):
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
        monitoring: typing.Optional[typing.Union["MonitoringConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        name: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Properties for versioned Azure resources.

        Combines base resource properties with version management capabilities
        and advanced configuration options for the unified framework.

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
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(monitoring, dict):
            monitoring = MonitoringConfig(**monitoring)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fc684e976d0c2057d010cbc36995d833ef6ed29ec007f64de818df4dab296f01)
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
    def monitoring(self) -> typing.Optional["MonitoringConfig"]:
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
        return typing.cast(typing.Optional["MonitoringConfig"], result)

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

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AzapiResourceProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class AzapiRoleAssignment(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiRoleAssignment",
):
    '''AZAPI-based role assignment construct.'''

    def __init__(
        self,
        scope_: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        object_id: builtins.str,
        role_definition_name: builtins.str,
        scope: builtins.str,
    ) -> None:
        '''
        :param scope_: -
        :param id: -
        :param object_id: 
        :param role_definition_name: 
        :param scope: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6d50cedef30ce6690304c852135c42b5f4e2b56e2a82f908f17e712cd3bd869a)
            check_type(argname="argument scope_", value=scope_, expected_type=type_hints["scope_"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = AzapiRoleAssignmentProps(
            object_id=object_id, role_definition_name=role_definition_name, scope=scope
        )

        jsii.create(self.__class__, self, [scope_, id, props])


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.AzapiRoleAssignmentProps",
    jsii_struct_bases=[],
    name_mapping={
        "object_id": "objectId",
        "role_definition_name": "roleDefinitionName",
        "scope": "scope",
    },
)
class AzapiRoleAssignmentProps:
    def __init__(
        self,
        *,
        object_id: builtins.str,
        role_definition_name: builtins.str,
        scope: builtins.str,
    ) -> None:
        '''Properties for AZAPI role assignment.

        :param object_id: 
        :param role_definition_name: 
        :param scope: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d4609725af1b10d08aee153d59b533985111e99c29c5131e94df4e9c415ae7e1)
            check_type(argname="argument object_id", value=object_id, expected_type=type_hints["object_id"])
            check_type(argname="argument role_definition_name", value=role_definition_name, expected_type=type_hints["role_definition_name"])
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "object_id": object_id,
            "role_definition_name": role_definition_name,
            "scope": scope,
        }

    @builtins.property
    def object_id(self) -> builtins.str:
        result = self._values.get("object_id")
        assert result is not None, "Required property 'object_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def role_definition_name(self) -> builtins.str:
        result = self._values.get("role_definition_name")
        assert result is not None, "Required property 'role_definition_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def scope(self) -> builtins.str:
        result = self._values.get("scope")
        assert result is not None, "Required property 'scope' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "AzapiRoleAssignmentProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.BreakingChange",
    jsii_struct_bases=[],
    name_mapping={
        "change_type": "changeType",
        "description": "description",
        "migration_path": "migrationPath",
        "new_value": "newValue",
        "old_value": "oldValue",
        "property": "property",
    },
)
class BreakingChange:
    def __init__(
        self,
        *,
        change_type: builtins.str,
        description: builtins.str,
        migration_path: typing.Optional[builtins.str] = None,
        new_value: typing.Optional[builtins.str] = None,
        old_value: typing.Optional[builtins.str] = None,
        property: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Breaking change documentation.

        Documents a breaking change between API versions to enable automated
        migration analysis and provide guidance to developers.

        :param change_type: The type of breaking change Must be one of the BreakingChangeType constants.
        :param description: Human-readable description of the breaking change Explains the impact and reasoning behind the change.
        :param migration_path: Guidance on how to migrate from old to new format Should include code examples where applicable.
        :param new_value: The new value or format Shows developers what to change to.
        :param old_value: The old value or format (for reference) Helps developers understand what changed.
        :param property: The property name affected by the breaking change Omit for schema-level changes.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5a2b0c56a331e150374ca548fdc3492dbd2ea177890ea38bd8b402d4c3b94492)
            check_type(argname="argument change_type", value=change_type, expected_type=type_hints["change_type"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument migration_path", value=migration_path, expected_type=type_hints["migration_path"])
            check_type(argname="argument new_value", value=new_value, expected_type=type_hints["new_value"])
            check_type(argname="argument old_value", value=old_value, expected_type=type_hints["old_value"])
            check_type(argname="argument property", value=property, expected_type=type_hints["property"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "change_type": change_type,
            "description": description,
        }
        if migration_path is not None:
            self._values["migration_path"] = migration_path
        if new_value is not None:
            self._values["new_value"] = new_value
        if old_value is not None:
            self._values["old_value"] = old_value
        if property is not None:
            self._values["property"] = property

    @builtins.property
    def change_type(self) -> builtins.str:
        '''The type of breaking change Must be one of the BreakingChangeType constants.'''
        result = self._values.get("change_type")
        assert result is not None, "Required property 'change_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> builtins.str:
        '''Human-readable description of the breaking change Explains the impact and reasoning behind the change.'''
        result = self._values.get("description")
        assert result is not None, "Required property 'description' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def migration_path(self) -> typing.Optional[builtins.str]:
        '''Guidance on how to migrate from old to new format Should include code examples where applicable.'''
        result = self._values.get("migration_path")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def new_value(self) -> typing.Optional[builtins.str]:
        '''The new value or format Shows developers what to change to.'''
        result = self._values.get("new_value")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def old_value(self) -> typing.Optional[builtins.str]:
        '''The old value or format (for reference) Helps developers understand what changed.'''
        result = self._values.get("old_value")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def property(self) -> typing.Optional[builtins.str]:
        '''The property name affected by the breaking change Omit for schema-level changes.'''
        result = self._values.get("property")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BreakingChange(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class BreakingChangeType(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.BreakingChangeType",
):
    '''Breaking change types for migration analysis.

    Categorizes the types of breaking changes that can occur between API versions
    to enable automated migration analysis and tooling.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_REMOVED")
    def PROPERTY_REMOVED(cls) -> builtins.str:
        '''Property has been removed from the API.'''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_REMOVED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_RENAMED")
    def PROPERTY_RENAMED(cls) -> builtins.str:
        '''Property has been renamed.'''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_RENAMED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_REQUIRED")
    def PROPERTY_REQUIRED(cls) -> builtins.str:
        '''Previously optional property is now required.'''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_REQUIRED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PROPERTY_TYPE_CHANGED")
    def PROPERTY_TYPE_CHANGED(cls) -> builtins.str:
        '''Property data type has changed.'''
        return typing.cast(builtins.str, jsii.sget(cls, "PROPERTY_TYPE_CHANGED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="SCHEMA_RESTRUCTURED")
    def SCHEMA_RESTRUCTURED(cls) -> builtins.str:
        '''Overall schema structure has been reorganized.'''
        return typing.cast(builtins.str, jsii.sget(cls, "SCHEMA_RESTRUCTURED"))


class DataAzapiClientConfig(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiClientConfig",
):
    '''Represents a {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config azapi_client_config}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        timeouts: typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config azapi_client_config} Data Source.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#timeouts DataAzapiClientConfig#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__685e62c05228470248e5e91289bda44dbcc610f0e629b9a9531e49e442654053)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = _DataAzapiClientConfigConfig_2fa921a7(
            timeouts=timeouts,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a DataAzapiClientConfig resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataAzapiClientConfig to import.
        :param import_from_id: The id of the existing DataAzapiClientConfig that should be imported. Refer to the {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataAzapiClientConfig to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7bb75f11668ae6ffef7d746577510b7396815558615f8657d9d93e4bb5e6b993)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(self, *, read: typing.Optional[builtins.str] = None) -> None:
        '''
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#read DataAzapiClientConfig#read}
        '''
        value = _DataAzapiClientConfigTimeouts_60de1877(read=read)

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="objectId")
    def object_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "objectId"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionId")
    def subscription_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "subscriptionId"))

    @builtins.property
    @jsii.member(jsii_name="subscriptionResourceId")
    def subscription_resource_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "subscriptionResourceId"))

    @builtins.property
    @jsii.member(jsii_name="tenantId")
    def tenant_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "tenantId"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> _DataAzapiClientConfigTimeoutsOutputReference_b8bf1947:
        return typing.cast(_DataAzapiClientConfigTimeoutsOutputReference_b8bf1947, jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "timeoutsInput"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiClientConfigConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "timeouts": "timeouts",
    },
)
class DataAzapiClientConfigConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        timeouts: typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#timeouts DataAzapiClientConfig#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(timeouts, dict):
            timeouts = _DataAzapiClientConfigTimeouts_60de1877(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7cd2cba78213211895ed59fdf0db98bed8881cf45941c834125e50ceb435ebf)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
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
        if timeouts is not None:
            self._values["timeouts"] = timeouts

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
    def timeouts(self) -> typing.Optional[_DataAzapiClientConfigTimeouts_60de1877]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#timeouts DataAzapiClientConfig#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional[_DataAzapiClientConfigTimeouts_60de1877], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAzapiClientConfigConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiClientConfigTimeouts",
    jsii_struct_bases=[],
    name_mapping={"read": "read"},
)
class DataAzapiClientConfigTimeouts:
    def __init__(self, *, read: typing.Optional[builtins.str] = None) -> None:
        '''
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#read DataAzapiClientConfig#read}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8798fa5e7398d64d1289116aeda31bf00e2b4d9d6953c3a6c9752938f7518138)
            check_type(argname="argument read", value=read, expected_type=type_hints["read"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if read is not None:
            self._values["read"] = read

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/client_config#read DataAzapiClientConfig#read}
        '''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAzapiClientConfigTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataAzapiClientConfigTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiClientConfigTimeoutsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__abf2c0976a35ef1e36956ac766e1bc65001340faf9983bfc42a735a03bb3277b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetRead")
    def reset_read(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRead", []))

    @builtins.property
    @jsii.member(jsii_name="readInput")
    def read_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "readInput"))

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__232df675d4c646245d1891bbafc62faf2c850f202c6b557b7329cd9e4496115b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, _cdktf_9a9027ec.IResolvable]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cd8f46f6199851a0d1c095c23ffb8b097a2deb398cef11bd2bb6f2bde342a932)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class DataAzapiResource(
    _cdktf_9a9027ec.TerraformDataSource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResource",
):
    '''Represents a {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource azapi_resource}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        type: builtins.str,
        headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        ignore_not_found: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        name: typing.Optional[builtins.str] = None,
        parent_id: typing.Optional[builtins.str] = None,
        query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        resource_id: typing.Optional[builtins.str] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_DataAzapiResourceRetry_68065f43, typing.Dict[builtins.str, typing.Any]]] = None,
        timeouts: typing.Optional[typing.Union[_DataAzapiResourceTimeouts_a892ce9b, typing.Dict[builtins.str, typing.Any]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource azapi_resource} Data Source.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#type DataAzapiResource#type}
        :param headers: A map of headers to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#headers DataAzapiResource#headers}
        :param ignore_not_found: If set to ``true``, the data source will not fail when the specified resource is not found (HTTP 404). Identifier attributes (``id``, ``name``, ``parent_id``, ``resource_id``) will still be populated based on inputs; other computed attributes (``output``, ``location``, ``identity``, ``tags``) will be null/empty. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#ignore_not_found DataAzapiResource#ignore_not_found}
        :param name: Specifies the name of the Azure resource. Exactly one of the arguments ``name`` or ``resource_id`` must be set. It could be omitted if the ``type`` is ``Microsoft.Resources/subscriptions``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#name DataAzapiResource#name}
        :param parent_id: The ID of the azure resource in which this resource is created. It supports different kinds of deployment scope for **top level** resources: - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group. - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group. - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to. - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60 - tenant scope: ``parent_id`` should be / For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet. For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#parent_id DataAzapiResource#parent_id}
        :param query_parameters: A map of query parameters to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#query_parameters DataAzapiResource#query_parameters}
        :param resource_id: The ID of the Azure resource to retrieve. Exactly one of the arguments ``name`` or ``resource_id`` must be set. It could be omitted if the ``type`` is ``Microsoft.Resources/subscriptions``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#resource_id DataAzapiResource#resource_id}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#response_export_values DataAzapiResource#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#retry DataAzapiResource#retry}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#timeouts DataAzapiResource#timeouts}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2e3f70bb9f1b1d5147ee09de64606e7a6f4a46910c044fb82010b8665ae97859)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = _DataAzapiResourceConfig_3eca9668(
            type=type,
            headers=headers,
            ignore_not_found=ignore_not_found,
            name=name,
            parent_id=parent_id,
            query_parameters=query_parameters,
            resource_id=resource_id,
            response_export_values=response_export_values,
            retry=retry,
            timeouts=timeouts,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a DataAzapiResource resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the DataAzapiResource to import.
        :param import_from_id: The id of the existing DataAzapiResource that should be imported. Refer to the {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the DataAzapiResource to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0c216ec7e210cad0029d06bc5c1d6da3d41e70bd8ec3f6097f5f4bc879255157)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putRetry")
    def put_retry(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#error_message_regex DataAzapiResource#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#interval_seconds DataAzapiResource#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#max_interval_seconds DataAzapiResource#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#multiplier DataAzapiResource#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#randomization_factor DataAzapiResource#randomization_factor}
        '''
        value = _DataAzapiResourceRetry_68065f43(
            error_message_regex=error_message_regex,
            interval_seconds=interval_seconds,
            max_interval_seconds=max_interval_seconds,
            multiplier=multiplier,
            randomization_factor=randomization_factor,
        )

        return typing.cast(None, jsii.invoke(self, "putRetry", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(self, *, read: typing.Optional[builtins.str] = None) -> None:
        '''
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#read DataAzapiResource#read}
        '''
        value = _DataAzapiResourceTimeouts_a892ce9b(read=read)

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetHeaders")
    def reset_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHeaders", []))

    @jsii.member(jsii_name="resetIgnoreNotFound")
    def reset_ignore_not_found(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreNotFound", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @jsii.member(jsii_name="resetParentId")
    def reset_parent_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetParentId", []))

    @jsii.member(jsii_name="resetQueryParameters")
    def reset_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetQueryParameters", []))

    @jsii.member(jsii_name="resetResourceId")
    def reset_resource_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetResourceId", []))

    @jsii.member(jsii_name="resetResponseExportValues")
    def reset_response_export_values(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetResponseExportValues", []))

    @jsii.member(jsii_name="resetRetry")
    def reset_retry(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetry", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="exists")
    def exists(self) -> _cdktf_9a9027ec.IResolvable:
        return typing.cast(_cdktf_9a9027ec.IResolvable, jsii.get(self, "exists"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="identity")
    def identity(self) -> _DataAzapiResourceIdentityList_ffff0399:
        return typing.cast(_DataAzapiResourceIdentityList_ffff0399, jsii.get(self, "identity"))

    @builtins.property
    @jsii.member(jsii_name="location")
    def location(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "location"))

    @builtins.property
    @jsii.member(jsii_name="output")
    def output(self) -> _cdktf_9a9027ec.AnyMap:
        return typing.cast(_cdktf_9a9027ec.AnyMap, jsii.get(self, "output"))

    @builtins.property
    @jsii.member(jsii_name="retry")
    def retry(self) -> _DataAzapiResourceRetryOutputReference_3a9a985d:
        return typing.cast(_DataAzapiResourceRetryOutputReference_3a9a985d, jsii.get(self, "retry"))

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> _cdktf_9a9027ec.StringMap:
        return typing.cast(_cdktf_9a9027ec.StringMap, jsii.get(self, "tags"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> _DataAzapiResourceTimeoutsOutputReference_824b781b:
        return typing.cast(_DataAzapiResourceTimeoutsOutputReference_824b781b, jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="headersInput")
    def headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "headersInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreNotFoundInput")
    def ignore_not_found_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreNotFoundInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="parentIdInput")
    def parent_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "parentIdInput"))

    @builtins.property
    @jsii.member(jsii_name="queryParametersInput")
    def query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "queryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="resourceIdInput")
    def resource_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "resourceIdInput"))

    @builtins.property
    @jsii.member(jsii_name="responseExportValuesInput")
    def response_export_values_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "responseExportValuesInput"))

    @builtins.property
    @jsii.member(jsii_name="retryInput")
    def retry_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceRetry_68065f43]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceRetry_68065f43]], jsii.get(self, "retryInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceTimeouts_a892ce9b]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceTimeouts_a892ce9b]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="headers")
    def headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "headers"))

    @headers.setter
    def headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__17be5a603dc466a085995bc28bb2aca223a8cd7b7939e12beddb6b1de26c6bdb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "headers", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreNotFound")
    def ignore_not_found(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ignoreNotFound"))

    @ignore_not_found.setter
    def ignore_not_found(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e728cda86461e0ca16b758ae81cd12b2f4d93194842e7afd36d4bc2625aebeaf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreNotFound", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56ea85689a24c4fea3386afb17cdaeb44fe16f6d65c44dd7672cf9c875a3c710)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="parentId")
    def parent_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "parentId"))

    @parent_id.setter
    def parent_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6bd01ffe1870f788a35b632e5dd6f0cebf273810bbb4da3a3fb24f615653e115)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "parentId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="queryParameters")
    def query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "queryParameters"))

    @query_parameters.setter
    def query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5d3b0b2058bc5038c2556c50a18a985d23295095dfe367e61735a03dfc685ede)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "queryParameters", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @resource_id.setter
    def resource_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__642c01afd28ba62b44899f49114898fb746f4e856d75c160108556050a6bcb43)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "resourceId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="responseExportValues")
    def response_export_values(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "responseExportValues"))

    @response_export_values.setter
    def response_export_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b658fbd88d335a6b2c3860c27d0187f5734f0b880029e56329c1c305c29a6244)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "responseExportValues", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eecf1855c5030dccfeb79952d75af3ac37bc5d9fdd8cb1fb8a775dc6058e5d4c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "type": "type",
        "headers": "headers",
        "ignore_not_found": "ignoreNotFound",
        "name": "name",
        "parent_id": "parentId",
        "query_parameters": "queryParameters",
        "resource_id": "resourceId",
        "response_export_values": "responseExportValues",
        "retry": "retry",
        "timeouts": "timeouts",
    },
)
class DataAzapiResourceConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        type: builtins.str,
        headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        ignore_not_found: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        name: typing.Optional[builtins.str] = None,
        parent_id: typing.Optional[builtins.str] = None,
        query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        resource_id: typing.Optional[builtins.str] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_DataAzapiResourceRetry_68065f43, typing.Dict[builtins.str, typing.Any]]] = None,
        timeouts: typing.Optional[typing.Union[_DataAzapiResourceTimeouts_a892ce9b, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#type DataAzapiResource#type}
        :param headers: A map of headers to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#headers DataAzapiResource#headers}
        :param ignore_not_found: If set to ``true``, the data source will not fail when the specified resource is not found (HTTP 404). Identifier attributes (``id``, ``name``, ``parent_id``, ``resource_id``) will still be populated based on inputs; other computed attributes (``output``, ``location``, ``identity``, ``tags``) will be null/empty. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#ignore_not_found DataAzapiResource#ignore_not_found}
        :param name: Specifies the name of the Azure resource. Exactly one of the arguments ``name`` or ``resource_id`` must be set. It could be omitted if the ``type`` is ``Microsoft.Resources/subscriptions``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#name DataAzapiResource#name}
        :param parent_id: The ID of the azure resource in which this resource is created. It supports different kinds of deployment scope for **top level** resources: - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group. - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group. - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to. - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60 - tenant scope: ``parent_id`` should be / For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet. For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#parent_id DataAzapiResource#parent_id}
        :param query_parameters: A map of query parameters to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#query_parameters DataAzapiResource#query_parameters}
        :param resource_id: The ID of the Azure resource to retrieve. Exactly one of the arguments ``name`` or ``resource_id`` must be set. It could be omitted if the ``type`` is ``Microsoft.Resources/subscriptions``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#resource_id DataAzapiResource#resource_id}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#response_export_values DataAzapiResource#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#retry DataAzapiResource#retry}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#timeouts DataAzapiResource#timeouts}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(retry, dict):
            retry = _DataAzapiResourceRetry_68065f43(**retry)
        if isinstance(timeouts, dict):
            timeouts = _DataAzapiResourceTimeouts_a892ce9b(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cebd3cc17128138fcc5742efad986faceadeb4614211734e344e82d3d0bd80ac)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument headers", value=headers, expected_type=type_hints["headers"])
            check_type(argname="argument ignore_not_found", value=ignore_not_found, expected_type=type_hints["ignore_not_found"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parent_id", value=parent_id, expected_type=type_hints["parent_id"])
            check_type(argname="argument query_parameters", value=query_parameters, expected_type=type_hints["query_parameters"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument response_export_values", value=response_export_values, expected_type=type_hints["response_export_values"])
            check_type(argname="argument retry", value=retry, expected_type=type_hints["retry"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
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
        if headers is not None:
            self._values["headers"] = headers
        if ignore_not_found is not None:
            self._values["ignore_not_found"] = ignore_not_found
        if name is not None:
            self._values["name"] = name
        if parent_id is not None:
            self._values["parent_id"] = parent_id
        if query_parameters is not None:
            self._values["query_parameters"] = query_parameters
        if resource_id is not None:
            self._values["resource_id"] = resource_id
        if response_export_values is not None:
            self._values["response_export_values"] = response_export_values
        if retry is not None:
            self._values["retry"] = retry
        if timeouts is not None:
            self._values["timeouts"] = timeouts

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
    def type(self) -> builtins.str:
        '''In a format like ``<resource-type>@<api-version>``.

        ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#type DataAzapiResource#type}
        '''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def headers(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A map of headers to include in the request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#headers DataAzapiResource#headers}
        '''
        result = self._values.get("headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def ignore_not_found(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''If set to ``true``, the data source will not fail when the specified resource is not found (HTTP 404).

        Identifier attributes (``id``, ``name``, ``parent_id``, ``resource_id``) will still be populated based on inputs; other computed attributes (``output``, ``location``, ``identity``, ``tags``) will be null/empty. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#ignore_not_found DataAzapiResource#ignore_not_found}
        '''
        result = self._values.get("ignore_not_found")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Specifies the name of the Azure resource.

        Exactly one of the arguments ``name`` or ``resource_id`` must be set. It could be omitted if the ``type`` is ``Microsoft.Resources/subscriptions``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#name DataAzapiResource#name}
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parent_id(self) -> typing.Optional[builtins.str]:
        '''The ID of the azure resource in which this resource is created.

        It supports different kinds of deployment scope for **top level** resources:

        - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group.

          - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group.
          - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to.
          - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60
          - tenant scope: ``parent_id`` should be /

        For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet.

        For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#parent_id DataAzapiResource#parent_id}
        '''
        result = self._values.get("parent_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A map of query parameters to include in the request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#query_parameters DataAzapiResource#query_parameters}
        '''
        result = self._values.get("query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    @builtins.property
    def resource_id(self) -> typing.Optional[builtins.str]:
        '''The ID of the Azure resource to retrieve.

        Exactly one of the arguments ``name`` or ``resource_id`` must be set. It could be omitted if the ``type`` is ``Microsoft.Resources/subscriptions``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#resource_id DataAzapiResource#resource_id}
        '''
        result = self._values.get("resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def response_export_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''The attribute can accept either a list or a map.

        - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output::

             {
             	properties = {
             		loginServer = "registry1.azurecr.io"
             		policies = {
             			quarantinePolicy = {
             				status = "disabled"
             			}
             		}
             	}
             }
        - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output::

             {
             	"login_server" = "registry1.azurecr.io"
             	"quarantine_status" = "disabled"
             }

        To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#response_export_values DataAzapiResource#response_export_values}
        '''
        result = self._values.get("response_export_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def retry(self) -> typing.Optional[_DataAzapiResourceRetry_68065f43]:
        '''The retry object supports the following attributes:.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#retry DataAzapiResource#retry}
        '''
        result = self._values.get("retry")
        return typing.cast(typing.Optional[_DataAzapiResourceRetry_68065f43], result)

    @builtins.property
    def timeouts(self) -> typing.Optional[_DataAzapiResourceTimeouts_a892ce9b]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#timeouts DataAzapiResource#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional[_DataAzapiResourceTimeouts_a892ce9b], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAzapiResourceConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceIdentity",
    jsii_struct_bases=[],
    name_mapping={},
)
class DataAzapiResourceIdentity:
    def __init__(self) -> None:
        self._values: typing.Dict[builtins.str, typing.Any] = {}

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAzapiResourceIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataAzapiResourceIdentityList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceIdentityList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7d0a2f08cf90a765e2a5c75bf2f54ca217874c74cc101b60ad8285df1ddbdff4)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(
        self,
        index: jsii.Number,
    ) -> _DataAzapiResourceIdentityOutputReference_d111e2d1:
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__28578cf004319abb07e45539466f40c279781f0e54518de61a48076b174368b8)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast(_DataAzapiResourceIdentityOutputReference_d111e2d1, jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__45492207e839be0fae7571f208e779349cbd6ea0976bb7cc949c6f6574eae7bc)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1f3858e0d37244f1de2467ff7f07c0f1ffade94c77a09bb46c883ec172b09de6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__85d854de81ba1757d28c8e697da93820a9cc92742188471be3af14c143eee40d)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]


class DataAzapiResourceIdentityOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceIdentityOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c1da9edf25149972d00ecc2ce5f42abe3d0c46b35bc649447fa4a2109201efb5)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @builtins.property
    @jsii.member(jsii_name="identityIds")
    def identity_ids(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "identityIds"))

    @builtins.property
    @jsii.member(jsii_name="principalId")
    def principal_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "principalId"))

    @builtins.property
    @jsii.member(jsii_name="tenantId")
    def tenant_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "tenantId"))

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(self) -> typing.Optional[_DataAzapiResourceIdentity_3125d9eb]:
        return typing.cast(typing.Optional[_DataAzapiResourceIdentity_3125d9eb], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[_DataAzapiResourceIdentity_3125d9eb],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b3f668acb5d19587676ac74033acc0e20c50f69c191fd4789a33802f90a5a5b8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceRetry",
    jsii_struct_bases=[],
    name_mapping={
        "error_message_regex": "errorMessageRegex",
        "interval_seconds": "intervalSeconds",
        "max_interval_seconds": "maxIntervalSeconds",
        "multiplier": "multiplier",
        "randomization_factor": "randomizationFactor",
    },
)
class DataAzapiResourceRetry:
    def __init__(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#error_message_regex DataAzapiResource#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#interval_seconds DataAzapiResource#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#max_interval_seconds DataAzapiResource#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#multiplier DataAzapiResource#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#randomization_factor DataAzapiResource#randomization_factor}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2fde1e2438eb2111b35e61c12026b80a4b5be36fa5dd7f3fdb0691a16d53972c)
            check_type(argname="argument error_message_regex", value=error_message_regex, expected_type=type_hints["error_message_regex"])
            check_type(argname="argument interval_seconds", value=interval_seconds, expected_type=type_hints["interval_seconds"])
            check_type(argname="argument max_interval_seconds", value=max_interval_seconds, expected_type=type_hints["max_interval_seconds"])
            check_type(argname="argument multiplier", value=multiplier, expected_type=type_hints["multiplier"])
            check_type(argname="argument randomization_factor", value=randomization_factor, expected_type=type_hints["randomization_factor"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "error_message_regex": error_message_regex,
        }
        if interval_seconds is not None:
            self._values["interval_seconds"] = interval_seconds
        if max_interval_seconds is not None:
            self._values["max_interval_seconds"] = max_interval_seconds
        if multiplier is not None:
            self._values["multiplier"] = multiplier
        if randomization_factor is not None:
            self._values["randomization_factor"] = randomization_factor

    @builtins.property
    def error_message_regex(self) -> typing.List[builtins.str]:
        '''A list of regular expressions to match against error messages.

        If any of the regular expressions match, the request will be retried.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#error_message_regex DataAzapiResource#error_message_regex}
        '''
        result = self._values.get("error_message_regex")
        assert result is not None, "Required property 'error_message_regex' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The base number of seconds to wait between retries. Default is ``10``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#interval_seconds DataAzapiResource#interval_seconds}
        '''
        result = self._values.get("interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of seconds to wait between retries. Default is ``180``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#max_interval_seconds DataAzapiResource#max_interval_seconds}
        '''
        result = self._values.get("max_interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def multiplier(self) -> typing.Optional[jsii.Number]:
        '''The multiplier to apply to the interval between retries. Default is ``1.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#multiplier DataAzapiResource#multiplier}
        '''
        result = self._values.get("multiplier")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def randomization_factor(self) -> typing.Optional[jsii.Number]:
        '''The randomization factor to apply to the interval between retries.

        The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#randomization_factor DataAzapiResource#randomization_factor}
        '''
        result = self._values.get("randomization_factor")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAzapiResourceRetry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataAzapiResourceRetryOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceRetryOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70fc36706131a7daeac907364a44502378fd31daf03eae3053240f6bf90bc09d)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetIntervalSeconds")
    def reset_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIntervalSeconds", []))

    @jsii.member(jsii_name="resetMaxIntervalSeconds")
    def reset_max_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxIntervalSeconds", []))

    @jsii.member(jsii_name="resetMultiplier")
    def reset_multiplier(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMultiplier", []))

    @jsii.member(jsii_name="resetRandomizationFactor")
    def reset_randomization_factor(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRandomizationFactor", []))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegexInput")
    def error_message_regex_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "errorMessageRegexInput"))

    @builtins.property
    @jsii.member(jsii_name="intervalSecondsInput")
    def interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "intervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSecondsInput")
    def max_interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxIntervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="multiplierInput")
    def multiplier_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "multiplierInput"))

    @builtins.property
    @jsii.member(jsii_name="randomizationFactorInput")
    def randomization_factor_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "randomizationFactorInput"))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegex")
    def error_message_regex(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "errorMessageRegex"))

    @error_message_regex.setter
    def error_message_regex(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be4408de96d73ca59a9c824846d7a5564db35f1c3f41e36288944ba903f9eb8b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "errorMessageRegex", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="intervalSeconds")
    def interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "intervalSeconds"))

    @interval_seconds.setter
    def interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ca5eeb7aaa8737563a94864b225330de2345c4523f18132789423476b3453cf3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "intervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSeconds")
    def max_interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxIntervalSeconds"))

    @max_interval_seconds.setter
    def max_interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4285c70b1258d9f488fd11b5534d8bc4e0bce324032e4d4e64055e3101a5b111)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxIntervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="multiplier")
    def multiplier(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "multiplier"))

    @multiplier.setter
    def multiplier(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e924b8a796b6e299135cd54946af45f93f21124efc37dd3354a5f344854dda5a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "multiplier", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="randomizationFactor")
    def randomization_factor(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "randomizationFactor"))

    @randomization_factor.setter
    def randomization_factor(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d2845a7d4fb3731d1d4b865f80d2c96fb9b9f5efb344a7b33b61c27adb8d36da)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "randomizationFactor", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceRetry_68065f43]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceRetry_68065f43]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceRetry_68065f43]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e51039bf7274cab585ae7ca2f7c21be512ace15163277c5bf184e7d9c08b396e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceTimeouts",
    jsii_struct_bases=[],
    name_mapping={"read": "read"},
)
class DataAzapiResourceTimeouts:
    def __init__(self, *, read: typing.Optional[builtins.str] = None) -> None:
        '''
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#read DataAzapiResource#read}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a6a2487e6ee6f20c3257b4dcdf4d8388c201531a92aeb3d7864119a42d4cf4b5)
            check_type(argname="argument read", value=read, expected_type=type_hints["read"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if read is not None:
            self._values["read"] = read

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/data-sources/resource#read DataAzapiResource#read}
        '''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DataAzapiResourceTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class DataAzapiResourceTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DataAzapiResourceTimeoutsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__48286f4d645543f79c8c2c640e17c7eb3918f092a73a9024b17ba0ce71b97a2b)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetRead")
    def reset_read(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRead", []))

    @builtins.property
    @jsii.member(jsii_name="readInput")
    def read_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "readInput"))

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b3611e62549a64bcf4d2aaef70455c90ca1b0a7c5b481c5813ad4ac6bd1f0ab9)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceTimeouts_a892ce9b]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceTimeouts_a892ce9b]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceTimeouts_a892ce9b]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1641e8e314ca7674f3f177a5bde4c2f55b319ab869fa390e4d84d43d02b07f4b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DiagnosticLogConfig",
    jsii_struct_bases=[],
    name_mapping={
        "enabled": "enabled",
        "category": "category",
        "category_group": "categoryGroup",
        "retention_policy": "retentionPolicy",
    },
)
class DiagnosticLogConfig:
    def __init__(
        self,
        *,
        enabled: builtins.bool,
        category: typing.Optional[builtins.str] = None,
        category_group: typing.Optional[builtins.str] = None,
        retention_policy: typing.Optional[typing.Union["RetentionPolicyConfig", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Log configuration for diagnostic settings.

        :param enabled: 
        :param category: 
        :param category_group: 
        :param retention_policy: 
        '''
        if isinstance(retention_policy, dict):
            retention_policy = RetentionPolicyConfig(**retention_policy)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6dcda887e53237d494c848709ef111cb4b898a5a32b4f78be95d1807ccb339c1)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument category", value=category, expected_type=type_hints["category"])
            check_type(argname="argument category_group", value=category_group, expected_type=type_hints["category_group"])
            check_type(argname="argument retention_policy", value=retention_policy, expected_type=type_hints["retention_policy"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "enabled": enabled,
        }
        if category is not None:
            self._values["category"] = category
        if category_group is not None:
            self._values["category_group"] = category_group
        if retention_policy is not None:
            self._values["retention_policy"] = retention_policy

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def category(self) -> typing.Optional[builtins.str]:
        result = self._values.get("category")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def category_group(self) -> typing.Optional[builtins.str]:
        result = self._values.get("category_group")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def retention_policy(self) -> typing.Optional["RetentionPolicyConfig"]:
        result = self._values.get("retention_policy")
        return typing.cast(typing.Optional["RetentionPolicyConfig"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DiagnosticLogConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.DiagnosticMetricConfig",
    jsii_struct_bases=[],
    name_mapping={
        "enabled": "enabled",
        "category": "category",
        "retention_policy": "retentionPolicy",
        "time_grain": "timeGrain",
    },
)
class DiagnosticMetricConfig:
    def __init__(
        self,
        *,
        enabled: builtins.bool,
        category: typing.Optional[builtins.str] = None,
        retention_policy: typing.Optional[typing.Union["RetentionPolicyConfig", typing.Dict[builtins.str, typing.Any]]] = None,
        time_grain: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Metric configuration for diagnostic settings.

        :param enabled: 
        :param category: Metric category name (used in newer API versions).
        :param retention_policy: 
        :param time_grain: Time grain for metrics in ISO 8601 duration format (used in API version 2016-09-01, e.g., "PT1M").
        '''
        if isinstance(retention_policy, dict):
            retention_policy = RetentionPolicyConfig(**retention_policy)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__be038e31fc9d9bdf95d4a04be710bb132e548324e9eddb130c218b7cd36448d6)
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument category", value=category, expected_type=type_hints["category"])
            check_type(argname="argument retention_policy", value=retention_policy, expected_type=type_hints["retention_policy"])
            check_type(argname="argument time_grain", value=time_grain, expected_type=type_hints["time_grain"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "enabled": enabled,
        }
        if category is not None:
            self._values["category"] = category
        if retention_policy is not None:
            self._values["retention_policy"] = retention_policy
        if time_grain is not None:
            self._values["time_grain"] = time_grain

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def category(self) -> typing.Optional[builtins.str]:
        '''Metric category name (used in newer API versions).'''
        result = self._values.get("category")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def retention_policy(self) -> typing.Optional["RetentionPolicyConfig"]:
        result = self._values.get("retention_policy")
        return typing.cast(typing.Optional["RetentionPolicyConfig"], result)

    @builtins.property
    def time_grain(self) -> typing.Optional[builtins.str]:
        '''Time grain for metrics in ISO 8601 duration format (used in API version 2016-09-01, e.g., "PT1M").'''
        result = self._values.get("time_grain")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DiagnosticMetricConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.MigrationAnalysis",
    jsii_struct_bases=[],
    name_mapping={
        "automatic_upgrade_possible": "automaticUpgradePossible",
        "breaking_changes": "breakingChanges",
        "compatible": "compatible",
        "estimated_effort": "estimatedEffort",
        "from_version": "fromVersion",
        "to_version": "toVersion",
        "warnings": "warnings",
    },
)
class MigrationAnalysis:
    def __init__(
        self,
        *,
        automatic_upgrade_possible: builtins.bool,
        breaking_changes: typing.Sequence[typing.Union[BreakingChange, typing.Dict[builtins.str, typing.Any]]],
        compatible: builtins.bool,
        estimated_effort: builtins.str,
        from_version: builtins.str,
        to_version: builtins.str,
        warnings: typing.Sequence[builtins.str],
    ) -> None:
        '''Migration analysis result.

        Results of analyzing the migration path between two API versions.
        Provides compatibility assessment, effort estimation, and detailed
        guidance for version transitions.

        :param automatic_upgrade_possible: Whether automatic upgrade tooling can handle this migration If true, migration can be largely automated.
        :param breaking_changes: Array of breaking changes that affect the migration Each change includes guidance on how to handle it.
        :param compatible: Whether the migration is backward compatible If true, migration should be straightforward.
        :param estimated_effort: Estimated effort required for the migration Must be one of the MigrationEffort constants.
        :param from_version: Source API version being migrated from.
        :param to_version: Target API version being migrated to.
        :param warnings: Array of non-breaking warnings about the migration May include deprecation notices or recommendations.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a5ca794ab8e8c4c037f3a3758f0414eb9de7ac2b3717ca348dfe5b6f16c913c9)
            check_type(argname="argument automatic_upgrade_possible", value=automatic_upgrade_possible, expected_type=type_hints["automatic_upgrade_possible"])
            check_type(argname="argument breaking_changes", value=breaking_changes, expected_type=type_hints["breaking_changes"])
            check_type(argname="argument compatible", value=compatible, expected_type=type_hints["compatible"])
            check_type(argname="argument estimated_effort", value=estimated_effort, expected_type=type_hints["estimated_effort"])
            check_type(argname="argument from_version", value=from_version, expected_type=type_hints["from_version"])
            check_type(argname="argument to_version", value=to_version, expected_type=type_hints["to_version"])
            check_type(argname="argument warnings", value=warnings, expected_type=type_hints["warnings"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "automatic_upgrade_possible": automatic_upgrade_possible,
            "breaking_changes": breaking_changes,
            "compatible": compatible,
            "estimated_effort": estimated_effort,
            "from_version": from_version,
            "to_version": to_version,
            "warnings": warnings,
        }

    @builtins.property
    def automatic_upgrade_possible(self) -> builtins.bool:
        '''Whether automatic upgrade tooling can handle this migration If true, migration can be largely automated.'''
        result = self._values.get("automatic_upgrade_possible")
        assert result is not None, "Required property 'automatic_upgrade_possible' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def breaking_changes(self) -> typing.List[BreakingChange]:
        '''Array of breaking changes that affect the migration Each change includes guidance on how to handle it.'''
        result = self._values.get("breaking_changes")
        assert result is not None, "Required property 'breaking_changes' is missing"
        return typing.cast(typing.List[BreakingChange], result)

    @builtins.property
    def compatible(self) -> builtins.bool:
        '''Whether the migration is backward compatible If true, migration should be straightforward.'''
        result = self._values.get("compatible")
        assert result is not None, "Required property 'compatible' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def estimated_effort(self) -> builtins.str:
        '''Estimated effort required for the migration Must be one of the MigrationEffort constants.'''
        result = self._values.get("estimated_effort")
        assert result is not None, "Required property 'estimated_effort' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def from_version(self) -> builtins.str:
        '''Source API version being migrated from.

        Example::

            "2024-01-01"
        '''
        result = self._values.get("from_version")
        assert result is not None, "Required property 'from_version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def to_version(self) -> builtins.str:
        '''Target API version being migrated to.

        Example::

            "2024-11-01"
        '''
        result = self._values.get("to_version")
        assert result is not None, "Required property 'to_version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def warnings(self) -> typing.List[builtins.str]:
        '''Array of non-breaking warnings about the migration May include deprecation notices or recommendations.'''
        result = self._values.get("warnings")
        assert result is not None, "Required property 'warnings' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MigrationAnalysis(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class MigrationEffort(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.MigrationEffort",
):
    '''Migration effort estimation for version transitions.

    Helps developers understand the complexity of migrating between versions
    and plan development resources accordingly.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="BREAKING")
    def BREAKING(cls) -> builtins.str:
        '''Breaking changes - major refactoring required Estimated time: > 3 days.'''
        return typing.cast(builtins.str, jsii.sget(cls, "BREAKING"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="HIGH")
    def HIGH(cls) -> builtins.str:
        '''High effort - significant manual changes required Estimated time: 1-3 days.'''
        return typing.cast(builtins.str, jsii.sget(cls, "HIGH"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="LOW")
    def LOW(cls) -> builtins.str:
        '''Low effort - mostly automatic with minimal manual changes Estimated time: < 1 hour.'''
        return typing.cast(builtins.str, jsii.sget(cls, "LOW"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="MEDIUM")
    def MEDIUM(cls) -> builtins.str:
        '''Medium effort - some manual changes required Estimated time: 1-8 hours.'''
        return typing.cast(builtins.str, jsii.sget(cls, "MEDIUM"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.MonitoringConfig",
    jsii_struct_bases=[],
    name_mapping={
        "action_groups": "actionGroups",
        "activity_log_alerts": "activityLogAlerts",
        "diagnostic_settings": "diagnosticSettings",
        "enabled": "enabled",
        "metric_alerts": "metricAlerts",
    },
)
class MonitoringConfig:
    def __init__(
        self,
        *,
        action_groups: typing.Optional[typing.Sequence[typing.Union[_ActionGroupProps_572d2b68, typing.Dict[builtins.str, typing.Any]]]] = None,
        activity_log_alerts: typing.Optional[typing.Sequence[typing.Union[_ActivityLogAlertProps_f1779054, typing.Dict[builtins.str, typing.Any]]]] = None,
        diagnostic_settings: typing.Optional[typing.Union[_DiagnosticSettingsProps_cc0fa615, typing.Dict[builtins.str, typing.Any]]] = None,
        enabled: typing.Optional[builtins.bool] = None,
        metric_alerts: typing.Optional[typing.Sequence[typing.Union[_MetricAlertProps_a18d777f, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Monitoring configuration for Azure resources.

        Provides integrated monitoring capabilities including diagnostic settings,
        metric alerts, and activity log alerts. All monitoring is optional and
        disabled by default.

        :param action_groups: Action groups to create for this resource Creates new ActionGroup instances as child constructs.
        :param activity_log_alerts: Activity log alerts configuration Creates ActivityLogAlert instances for this resource's operations.
        :param diagnostic_settings: Diagnostic settings configuration Uses the full DiagnosticSettings construct for consistency.
        :param enabled: Whether monitoring is enabled. Default: true
        :param metric_alerts: Metric alerts configuration Creates MetricAlert instances scoped to this resource.
        '''
        if isinstance(diagnostic_settings, dict):
            diagnostic_settings = _DiagnosticSettingsProps_cc0fa615(**diagnostic_settings)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5679643d28f130dcb384544fdb30a5b1373794e977ad6e1cf34d138fd5b26ff2)
            check_type(argname="argument action_groups", value=action_groups, expected_type=type_hints["action_groups"])
            check_type(argname="argument activity_log_alerts", value=activity_log_alerts, expected_type=type_hints["activity_log_alerts"])
            check_type(argname="argument diagnostic_settings", value=diagnostic_settings, expected_type=type_hints["diagnostic_settings"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
            check_type(argname="argument metric_alerts", value=metric_alerts, expected_type=type_hints["metric_alerts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if action_groups is not None:
            self._values["action_groups"] = action_groups
        if activity_log_alerts is not None:
            self._values["activity_log_alerts"] = activity_log_alerts
        if diagnostic_settings is not None:
            self._values["diagnostic_settings"] = diagnostic_settings
        if enabled is not None:
            self._values["enabled"] = enabled
        if metric_alerts is not None:
            self._values["metric_alerts"] = metric_alerts

    @builtins.property
    def action_groups(self) -> typing.Optional[typing.List[_ActionGroupProps_572d2b68]]:
        '''Action groups to create for this resource Creates new ActionGroup instances as child constructs.'''
        result = self._values.get("action_groups")
        return typing.cast(typing.Optional[typing.List[_ActionGroupProps_572d2b68]], result)

    @builtins.property
    def activity_log_alerts(
        self,
    ) -> typing.Optional[typing.List[_ActivityLogAlertProps_f1779054]]:
        '''Activity log alerts configuration Creates ActivityLogAlert instances for this resource's operations.'''
        result = self._values.get("activity_log_alerts")
        return typing.cast(typing.Optional[typing.List[_ActivityLogAlertProps_f1779054]], result)

    @builtins.property
    def diagnostic_settings(self) -> typing.Optional[_DiagnosticSettingsProps_cc0fa615]:
        '''Diagnostic settings configuration Uses the full DiagnosticSettings construct for consistency.'''
        result = self._values.get("diagnostic_settings")
        return typing.cast(typing.Optional[_DiagnosticSettingsProps_cc0fa615], result)

    @builtins.property
    def enabled(self) -> typing.Optional[builtins.bool]:
        '''Whether monitoring is enabled.

        :default: true
        '''
        result = self._values.get("enabled")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def metric_alerts(self) -> typing.Optional[typing.List[_MetricAlertProps_a18d777f]]:
        '''Metric alerts configuration Creates MetricAlert instances scoped to this resource.'''
        result = self._values.get("metric_alerts")
        return typing.cast(typing.Optional[typing.List[_MetricAlertProps_a18d777f]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "MonitoringConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.PropertyDefinition",
    jsii_struct_bases=[],
    name_mapping={
        "data_type": "dataType",
        "added_in_version": "addedInVersion",
        "default_value": "defaultValue",
        "deprecated": "deprecated",
        "description": "description",
        "removed_in_version": "removedInVersion",
        "required": "required",
        "validation": "validation",
    },
)
class PropertyDefinition:
    def __init__(
        self,
        *,
        data_type: builtins.str,
        added_in_version: typing.Optional[builtins.str] = None,
        default_value: typing.Any = None,
        deprecated: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        removed_in_version: typing.Optional[builtins.str] = None,
        required: typing.Optional[builtins.bool] = None,
        validation: typing.Optional[typing.Sequence[typing.Union["ValidationRule", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''Property definition for API schema.

        Defines the characteristics, validation rules, and metadata for a single
        property in an API schema. This enables type validation, transformation,
        and documentation generation.

        :param data_type: The data type of the property Must be one of the PropertyType constants.
        :param added_in_version: The API version in which this property was added Used for compatibility analysis and migration planning.
        :param default_value: Default value to use if property is not provided Type must match the property type.
        :param deprecated: Whether this property is deprecated If true, usage warnings will be generated. Default: false
        :param description: Human-readable description of the property Used for documentation generation and IDE support.
        :param removed_in_version: The API version in which this property was removed Used for compatibility analysis and migration planning.
        :param required: Whether this property is required If true, the property must be provided by the user. Default: false
        :param validation: Array of validation rules to apply to this property Rules are evaluated in order and all must pass.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3add32040853efb922ea28aa1f44ae789c41571741cdbdfa1a866ebc7d824f93)
            check_type(argname="argument data_type", value=data_type, expected_type=type_hints["data_type"])
            check_type(argname="argument added_in_version", value=added_in_version, expected_type=type_hints["added_in_version"])
            check_type(argname="argument default_value", value=default_value, expected_type=type_hints["default_value"])
            check_type(argname="argument deprecated", value=deprecated, expected_type=type_hints["deprecated"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument removed_in_version", value=removed_in_version, expected_type=type_hints["removed_in_version"])
            check_type(argname="argument required", value=required, expected_type=type_hints["required"])
            check_type(argname="argument validation", value=validation, expected_type=type_hints["validation"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "data_type": data_type,
        }
        if added_in_version is not None:
            self._values["added_in_version"] = added_in_version
        if default_value is not None:
            self._values["default_value"] = default_value
        if deprecated is not None:
            self._values["deprecated"] = deprecated
        if description is not None:
            self._values["description"] = description
        if removed_in_version is not None:
            self._values["removed_in_version"] = removed_in_version
        if required is not None:
            self._values["required"] = required
        if validation is not None:
            self._values["validation"] = validation

    @builtins.property
    def data_type(self) -> builtins.str:
        '''The data type of the property Must be one of the PropertyType constants.'''
        result = self._values.get("data_type")
        assert result is not None, "Required property 'data_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def added_in_version(self) -> typing.Optional[builtins.str]:
        '''The API version in which this property was added Used for compatibility analysis and migration planning.

        Example::

            "2024-01-01"
        '''
        result = self._values.get("added_in_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def default_value(self) -> typing.Any:
        '''Default value to use if property is not provided Type must match the property type.'''
        result = self._values.get("default_value")
        return typing.cast(typing.Any, result)

    @builtins.property
    def deprecated(self) -> typing.Optional[builtins.bool]:
        '''Whether this property is deprecated If true, usage warnings will be generated.

        :default: false
        '''
        result = self._values.get("deprecated")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''Human-readable description of the property Used for documentation generation and IDE support.'''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def removed_in_version(self) -> typing.Optional[builtins.str]:
        '''The API version in which this property was removed Used for compatibility analysis and migration planning.

        Example::

            "2025-01-01"
        '''
        result = self._values.get("removed_in_version")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def required(self) -> typing.Optional[builtins.bool]:
        '''Whether this property is required If true, the property must be provided by the user.

        :default: false
        '''
        result = self._values.get("required")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def validation(self) -> typing.Optional[typing.List["ValidationRule"]]:
        '''Array of validation rules to apply to this property Rules are evaluated in order and all must pass.'''
        result = self._values.get("validation")
        return typing.cast(typing.Optional[typing.List["ValidationRule"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PropertyDefinition(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.PropertyMapping",
    jsii_struct_bases=[],
    name_mapping={
        "source_property": "sourceProperty",
        "target_property": "targetProperty",
        "default_value": "defaultValue",
        "required": "required",
        "transformer": "transformer",
    },
)
class PropertyMapping:
    def __init__(
        self,
        *,
        source_property: builtins.str,
        target_property: builtins.str,
        default_value: typing.Any = None,
        required: typing.Optional[builtins.bool] = None,
        transformer: typing.Optional[typing.Union["PropertyTransformer", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Property mapping definition.

        Defines how a property should be mapped from source to target schema,
        including any transformations or default values to apply.

        :param source_property: The name of the source property.
        :param target_property: The name of the target property.
        :param default_value: Default value to use if source property is not provided.
        :param required: Whether this property is required in the target schema. Default: false
        :param transformer: Optional transformer to apply during mapping.
        '''
        if isinstance(transformer, dict):
            transformer = PropertyTransformer(**transformer)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__53d90887b98a1b5b0eaef72badcb9950bc7cca36bf4a14f7c1df5b787f4376b8)
            check_type(argname="argument source_property", value=source_property, expected_type=type_hints["source_property"])
            check_type(argname="argument target_property", value=target_property, expected_type=type_hints["target_property"])
            check_type(argname="argument default_value", value=default_value, expected_type=type_hints["default_value"])
            check_type(argname="argument required", value=required, expected_type=type_hints["required"])
            check_type(argname="argument transformer", value=transformer, expected_type=type_hints["transformer"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "source_property": source_property,
            "target_property": target_property,
        }
        if default_value is not None:
            self._values["default_value"] = default_value
        if required is not None:
            self._values["required"] = required
        if transformer is not None:
            self._values["transformer"] = transformer

    @builtins.property
    def source_property(self) -> builtins.str:
        '''The name of the source property.'''
        result = self._values.get("source_property")
        assert result is not None, "Required property 'source_property' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def target_property(self) -> builtins.str:
        '''The name of the target property.'''
        result = self._values.get("target_property")
        assert result is not None, "Required property 'target_property' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def default_value(self) -> typing.Any:
        '''Default value to use if source property is not provided.'''
        result = self._values.get("default_value")
        return typing.cast(typing.Any, result)

    @builtins.property
    def required(self) -> typing.Optional[builtins.bool]:
        '''Whether this property is required in the target schema.

        :default: false
        '''
        result = self._values.get("required")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def transformer(self) -> typing.Optional["PropertyTransformer"]:
        '''Optional transformer to apply during mapping.'''
        result = self._values.get("transformer")
        return typing.cast(typing.Optional["PropertyTransformer"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PropertyMapping(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class PropertyTransformationType(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.PropertyTransformationType",
):
    '''Property transformation types for schema mapping.

    Defines the types of transformations that can be applied when mapping
    properties between different schema versions.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="CUSTOM_FUNCTION")
    def CUSTOM_FUNCTION(cls) -> builtins.str:
        '''Apply custom transformation function.'''
        return typing.cast(builtins.str, jsii.sget(cls, "CUSTOM_FUNCTION"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="DIRECT_COPY")
    def DIRECT_COPY(cls) -> builtins.str:
        '''Direct copy with no transformation.'''
        return typing.cast(builtins.str, jsii.sget(cls, "DIRECT_COPY"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="STRUCTURE_TRANSFORMATION")
    def STRUCTURE_TRANSFORMATION(cls) -> builtins.str:
        '''Transform object structure.'''
        return typing.cast(builtins.str, jsii.sget(cls, "STRUCTURE_TRANSFORMATION"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="VALUE_MAPPING")
    def VALUE_MAPPING(cls) -> builtins.str:
        '''Map values using a lookup table.'''
        return typing.cast(builtins.str, jsii.sget(cls, "VALUE_MAPPING"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.PropertyTransformer",
    jsii_struct_bases=[],
    name_mapping={"transformation_type": "transformationType", "config": "config"},
)
class PropertyTransformer:
    def __init__(
        self,
        *,
        transformation_type: builtins.str,
        config: typing.Any = None,
    ) -> None:
        '''Property transformation interface for schema mapping.

        Defines how properties should be transformed when mapping between
        different schema versions or formats.

        :param transformation_type: The type of transformation to apply Must be one of the PropertyTransformationType constants.
        :param config: Configuration object for the transformation Structure depends on the transformation type.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__29703eea24077745913d21668a111630be5e56e0452d286b44e563e0842b5883)
            check_type(argname="argument transformation_type", value=transformation_type, expected_type=type_hints["transformation_type"])
            check_type(argname="argument config", value=config, expected_type=type_hints["config"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "transformation_type": transformation_type,
        }
        if config is not None:
            self._values["config"] = config

    @builtins.property
    def transformation_type(self) -> builtins.str:
        '''The type of transformation to apply Must be one of the PropertyTransformationType constants.'''
        result = self._values.get("transformation_type")
        assert result is not None, "Required property 'transformation_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def config(self) -> typing.Any:
        '''Configuration object for the transformation Structure depends on the transformation type.'''
        result = self._values.get("config")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PropertyTransformer(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class PropertyType(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.PropertyType",
):
    '''Property type enumeration for schema definitions.

    Defines the basic data types supported in API schemas for validation
    and transformation purposes.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="ANY")
    def ANY(cls) -> builtins.str:
        '''Any data type (no validation).'''
        return typing.cast(builtins.str, jsii.sget(cls, "ANY"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="ARRAY")
    def ARRAY(cls) -> builtins.str:
        '''Array data type (ordered collection).'''
        return typing.cast(builtins.str, jsii.sget(cls, "ARRAY"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="BOOLEAN")
    def BOOLEAN(cls) -> builtins.str:
        '''Boolean data type (true/false).'''
        return typing.cast(builtins.str, jsii.sget(cls, "BOOLEAN"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="NUMBER")
    def NUMBER(cls) -> builtins.str:
        '''Numeric data type (integer or float).'''
        return typing.cast(builtins.str, jsii.sget(cls, "NUMBER"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="OBJECT")
    def OBJECT(cls) -> builtins.str:
        '''Object data type (key-value pairs).'''
        return typing.cast(builtins.str, jsii.sget(cls, "OBJECT"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="STRING")
    def STRING(cls) -> builtins.str:
        '''String data type.'''
        return typing.cast(builtins.str, jsii.sget(cls, "STRING"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.PropertyValidation",
    jsii_struct_bases=[],
    name_mapping={"property": "property", "rules": "rules"},
)
class PropertyValidation:
    def __init__(
        self,
        *,
        property: builtins.str,
        rules: typing.Sequence[typing.Union["ValidationRule", typing.Dict[builtins.str, typing.Any]]],
    ) -> None:
        '''Property validation configuration.

        Defines validation rules that apply to specific properties,
        enabling complex validation scenarios and cross-property validation.

        :param property: The name of the property this validation applies to.
        :param rules: Array of validation rules to apply to this property Rules are evaluated in order and all must pass.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7207a6b3ce8a39e6fbdcbacd7c93f221b35b52f943d66e4609f3a815c3bfe97c)
            check_type(argname="argument property", value=property, expected_type=type_hints["property"])
            check_type(argname="argument rules", value=rules, expected_type=type_hints["rules"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "property": property,
            "rules": rules,
        }

    @builtins.property
    def property(self) -> builtins.str:
        '''The name of the property this validation applies to.'''
        result = self._values.get("property")
        assert result is not None, "Required property 'property' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def rules(self) -> typing.List["ValidationRule"]:
        '''Array of validation rules to apply to this property Rules are evaluated in order and all must pass.'''
        result = self._values.get("rules")
        assert result is not None, "Required property 'rules' is missing"
        return typing.cast(typing.List["ValidationRule"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "PropertyValidation(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class Resource(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.Resource",
):
    '''Represents a {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource azapi_resource}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        type: builtins.str,
        body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        create_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        create_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        delete_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        delete_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        identity: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_ResourceIdentity_d0fe12c0, typing.Dict[builtins.str, typing.Any]]]]] = None,
        ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ignore_null_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        location: typing.Optional[builtins.str] = None,
        locks: typing.Optional[typing.Sequence[builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        parent_id: typing.Optional[builtins.str] = None,
        read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        replace_triggers_external_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        replace_triggers_refs: typing.Optional[typing.Sequence[builtins.str]] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_ResourceRetry_50237e4f, typing.Dict[builtins.str, typing.Any]]] = None,
        schema_validation_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union[_ResourceTimeouts_0b401feb, typing.Dict[builtins.str, typing.Any]]] = None,
        update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource azapi_resource} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#type Resource#type}
        :param body: A dynamic attribute that contains the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#body Resource#body}
        :param create_headers: A mapping of headers to be sent with the create request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create_headers Resource#create_headers}
        :param create_query_parameters: A mapping of query parameters to be sent with the create request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create_query_parameters Resource#create_query_parameters}
        :param delete_headers: A mapping of headers to be sent with the delete request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete_headers Resource#delete_headers}
        :param delete_query_parameters: A mapping of query parameters to be sent with the delete request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete_query_parameters Resource#delete_query_parameters}
        :param identity: identity block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#identity Resource#identity}
        :param ignore_casing: Whether ignore the casing of the property names in the response body. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_casing Resource#ignore_casing}
        :param ignore_missing_property: Whether ignore not returned properties like credentials in ``body`` to suppress plan-diff. Defaults to ``true``. It's recommend to enable this option when some sensitive properties are not returned in response body, instead of setting them in ``lifecycle.ignore_changes`` because it will make the sensitive fields unable to update. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_missing_property Resource#ignore_missing_property}
        :param ignore_null_property: When set to ``true``, the provider will ignore properties whose values are ``null`` in the ``body``. These properties will not be included in the request body sent to the API, and the difference will not be shown in the plan output. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_null_property Resource#ignore_null_property}
        :param location: The location of the Azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#location Resource#location}
        :param locks: A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#locks Resource#locks}
        :param name: Specifies the name of the azure resource. Changing this forces a new resource to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#name Resource#name}
        :param parent_id: The ID of the azure resource in which this resource is created. It supports different kinds of deployment scope for **top level** resources: - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group. - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group. - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to. - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60 - tenant scope: ``parent_id`` should be / For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet. For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#parent_id Resource#parent_id}
        :param read_headers: A mapping of headers to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read_headers Resource#read_headers}
        :param read_query_parameters: A mapping of query parameters to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read_query_parameters Resource#read_query_parameters}
        :param replace_triggers_external_values: Will trigger a replace of the resource when the value changes and is not ``null``. This can be used by practitioners to force a replace of the resource when certain values change, e.g. changing the SKU of a virtual machine based on the value of variables or locals. The value is a ``dynamic``, so practitioners can compose the input however they wish. For a "break glass" set the value to ``null`` to prevent the plan modifier taking effect. If you have ``null`` values that you do want to be tracked as affecting the resource replacement, include these inside an object. Advanced use cases are possible and resource replacement can be triggered by values external to the resource, for example when a dependent resource changes. e.g. to replace a resource when either the SKU or os_type attributes change:: resource "azapi_resource" "example" { name = var.name type = "Microsoft.Network/publicIPAddresses@2023-11-01" parent_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example" body = { properties = { sku = var.sku zones = var.zones } } replace_triggers_external_values = [ var.sku, var.zones, ] } Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#replace_triggers_external_values Resource#replace_triggers_external_values}
        :param replace_triggers_refs: A list of paths in the current Terraform configuration. When the values at these paths change, the resource will be replaced. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#replace_triggers_refs Resource#replace_triggers_refs}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#response_export_values Resource#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#retry Resource#retry}
        :param schema_validation_enabled: Whether enabled the validation on ``type`` and ``body`` with embedded schema. Defaults to ``true``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#schema_validation_enabled Resource#schema_validation_enabled}
        :param sensitive_body: A dynamic attribute that contains the write-only properties of the request body. This will be merge-patched to the body to construct the actual request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#sensitive_body Resource#sensitive_body}
        :param sensitive_body_version: A map where the key is the path to the property in ``sensitive_body`` and the value is the version of the property. The key is a string in the format of ``path.to.property[index].subproperty``, where ``index`` is the index of the item in an array. When the version is changed, the property will be included in the request body, otherwise it will be omitted from the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#sensitive_body_version Resource#sensitive_body_version}
        :param tags: A mapping of tags which should be assigned to the Azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#tags Resource#tags}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#timeouts Resource#timeouts}
        :param update_headers: A mapping of headers to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update_headers Resource#update_headers}
        :param update_query_parameters: A mapping of query parameters to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update_query_parameters Resource#update_query_parameters}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c189527db639961ba7cc72fae190953180434f2ab82164f9d0a14ac4dd47c619)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = _ResourceConfig_04e2532f(
            type=type,
            body=body,
            create_headers=create_headers,
            create_query_parameters=create_query_parameters,
            delete_headers=delete_headers,
            delete_query_parameters=delete_query_parameters,
            identity=identity,
            ignore_casing=ignore_casing,
            ignore_missing_property=ignore_missing_property,
            ignore_null_property=ignore_null_property,
            location=location,
            locks=locks,
            name=name,
            parent_id=parent_id,
            read_headers=read_headers,
            read_query_parameters=read_query_parameters,
            replace_triggers_external_values=replace_triggers_external_values,
            replace_triggers_refs=replace_triggers_refs,
            response_export_values=response_export_values,
            retry=retry,
            schema_validation_enabled=schema_validation_enabled,
            sensitive_body=sensitive_body,
            sensitive_body_version=sensitive_body_version,
            tags=tags,
            timeouts=timeouts,
            update_headers=update_headers,
            update_query_parameters=update_query_parameters,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a Resource resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the Resource to import.
        :param import_from_id: The id of the existing Resource that should be imported. Refer to the {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the Resource to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dc987a34e45df8c36de43f210b64d4a1303b00ffa8a33b78a04a135951671f7d)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putIdentity")
    def put_identity(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_ResourceIdentity_d0fe12c0, typing.Dict[builtins.str, typing.Any]]]],
    ) -> None:
        '''
        :param value: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7b081b2b98e2bc215dbc8dd2df8a969512a7473fa2a0578c7d47cc25e111f720)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        return typing.cast(None, jsii.invoke(self, "putIdentity", [value]))

    @jsii.member(jsii_name="putRetry")
    def put_retry(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#error_message_regex Resource#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#interval_seconds Resource#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#max_interval_seconds Resource#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#multiplier Resource#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#randomization_factor Resource#randomization_factor}
        '''
        value = _ResourceRetry_50237e4f(
            error_message_regex=error_message_regex,
            interval_seconds=interval_seconds,
            max_interval_seconds=max_interval_seconds,
            multiplier=multiplier,
            randomization_factor=randomization_factor,
        )

        return typing.cast(None, jsii.invoke(self, "putRetry", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create Resource#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete Resource#delete}
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read Resource#read}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update Resource#update}
        '''
        value = _ResourceTimeouts_0b401feb(
            create=create, delete=delete, read=read, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetBody")
    def reset_body(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBody", []))

    @jsii.member(jsii_name="resetCreateHeaders")
    def reset_create_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreateHeaders", []))

    @jsii.member(jsii_name="resetCreateQueryParameters")
    def reset_create_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreateQueryParameters", []))

    @jsii.member(jsii_name="resetDeleteHeaders")
    def reset_delete_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeleteHeaders", []))

    @jsii.member(jsii_name="resetDeleteQueryParameters")
    def reset_delete_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDeleteQueryParameters", []))

    @jsii.member(jsii_name="resetIdentity")
    def reset_identity(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIdentity", []))

    @jsii.member(jsii_name="resetIgnoreCasing")
    def reset_ignore_casing(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreCasing", []))

    @jsii.member(jsii_name="resetIgnoreMissingProperty")
    def reset_ignore_missing_property(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreMissingProperty", []))

    @jsii.member(jsii_name="resetIgnoreNullProperty")
    def reset_ignore_null_property(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreNullProperty", []))

    @jsii.member(jsii_name="resetLocation")
    def reset_location(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLocation", []))

    @jsii.member(jsii_name="resetLocks")
    def reset_locks(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLocks", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @jsii.member(jsii_name="resetParentId")
    def reset_parent_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetParentId", []))

    @jsii.member(jsii_name="resetReadHeaders")
    def reset_read_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReadHeaders", []))

    @jsii.member(jsii_name="resetReadQueryParameters")
    def reset_read_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReadQueryParameters", []))

    @jsii.member(jsii_name="resetReplaceTriggersExternalValues")
    def reset_replace_triggers_external_values(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReplaceTriggersExternalValues", []))

    @jsii.member(jsii_name="resetReplaceTriggersRefs")
    def reset_replace_triggers_refs(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReplaceTriggersRefs", []))

    @jsii.member(jsii_name="resetResponseExportValues")
    def reset_response_export_values(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetResponseExportValues", []))

    @jsii.member(jsii_name="resetRetry")
    def reset_retry(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetry", []))

    @jsii.member(jsii_name="resetSchemaValidationEnabled")
    def reset_schema_validation_enabled(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSchemaValidationEnabled", []))

    @jsii.member(jsii_name="resetSensitiveBody")
    def reset_sensitive_body(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSensitiveBody", []))

    @jsii.member(jsii_name="resetSensitiveBodyVersion")
    def reset_sensitive_body_version(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSensitiveBodyVersion", []))

    @jsii.member(jsii_name="resetTags")
    def reset_tags(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTags", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="resetUpdateHeaders")
    def reset_update_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdateHeaders", []))

    @jsii.member(jsii_name="resetUpdateQueryParameters")
    def reset_update_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdateQueryParameters", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="identity")
    def identity(self) -> _ResourceIdentityList_4a7b5836:
        return typing.cast(_ResourceIdentityList_4a7b5836, jsii.get(self, "identity"))

    @builtins.property
    @jsii.member(jsii_name="output")
    def output(self) -> _cdktf_9a9027ec.AnyMap:
        return typing.cast(_cdktf_9a9027ec.AnyMap, jsii.get(self, "output"))

    @builtins.property
    @jsii.member(jsii_name="retry")
    def retry(self) -> _ResourceRetryOutputReference_4a94fdab:
        return typing.cast(_ResourceRetryOutputReference_4a94fdab, jsii.get(self, "retry"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> _ResourceTimeoutsOutputReference_e98b2440:
        return typing.cast(_ResourceTimeoutsOutputReference_e98b2440, jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="bodyInput")
    def body_input(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "bodyInput"))

    @builtins.property
    @jsii.member(jsii_name="createHeadersInput")
    def create_headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "createHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="createQueryParametersInput")
    def create_query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "createQueryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteHeadersInput")
    def delete_headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "deleteHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteQueryParametersInput")
    def delete_query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "deleteQueryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="identityInput")
    def identity_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]], jsii.get(self, "identityInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreCasingInput")
    def ignore_casing_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreCasingInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreMissingPropertyInput")
    def ignore_missing_property_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreMissingPropertyInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreNullPropertyInput")
    def ignore_null_property_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreNullPropertyInput"))

    @builtins.property
    @jsii.member(jsii_name="locationInput")
    def location_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "locationInput"))

    @builtins.property
    @jsii.member(jsii_name="locksInput")
    def locks_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "locksInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="parentIdInput")
    def parent_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "parentIdInput"))

    @builtins.property
    @jsii.member(jsii_name="readHeadersInput")
    def read_headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "readHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="readQueryParametersInput")
    def read_query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "readQueryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="replaceTriggersExternalValuesInput")
    def replace_triggers_external_values_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "replaceTriggersExternalValuesInput"))

    @builtins.property
    @jsii.member(jsii_name="replaceTriggersRefsInput")
    def replace_triggers_refs_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "replaceTriggersRefsInput"))

    @builtins.property
    @jsii.member(jsii_name="responseExportValuesInput")
    def response_export_values_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "responseExportValuesInput"))

    @builtins.property
    @jsii.member(jsii_name="retryInput")
    def retry_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceRetry_50237e4f]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceRetry_50237e4f]], jsii.get(self, "retryInput"))

    @builtins.property
    @jsii.member(jsii_name="schemaValidationEnabledInput")
    def schema_validation_enabled_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "schemaValidationEnabledInput"))

    @builtins.property
    @jsii.member(jsii_name="sensitiveBodyInput")
    def sensitive_body_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "sensitiveBodyInput"))

    @builtins.property
    @jsii.member(jsii_name="sensitiveBodyVersionInput")
    def sensitive_body_version_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "sensitiveBodyVersionInput"))

    @builtins.property
    @jsii.member(jsii_name="tagsInput")
    def tags_input(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "tagsInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceTimeouts_0b401feb]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceTimeouts_0b401feb]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="updateHeadersInput")
    def update_headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "updateHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="updateQueryParametersInput")
    def update_query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "updateQueryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="body")
    def body(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "body"))

    @body.setter
    def body(self, value: typing.Mapping[builtins.str, typing.Any]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3bf2d0b4f4091dc508788dffb68420f8a40989a0cc807c6aa95d12e8e3acc419)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "body", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="createHeaders")
    def create_headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "createHeaders"))

    @create_headers.setter
    def create_headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__503670241d5362945f51defaaed4838625e41f6104400e62d1d539a1e718810b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "createHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="createQueryParameters")
    def create_query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "createQueryParameters"))

    @create_query_parameters.setter
    def create_query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__337daf2cd77ce8984162b4fc3744a8045ca63d6c86d5ee0a2c034844a2b4057f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "createQueryParameters", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="deleteHeaders")
    def delete_headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "deleteHeaders"))

    @delete_headers.setter
    def delete_headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5151ef48c6821aad1a627120bdcf8fe236efc7dbcf28d1612ced082280d5a923)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "deleteHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="deleteQueryParameters")
    def delete_query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "deleteQueryParameters"))

    @delete_query_parameters.setter
    def delete_query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26b92a8fc3db0482dd26328c25725ea8d36b8091c2f61ae9c92992b8a00f6cc5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "deleteQueryParameters", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreCasing")
    def ignore_casing(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ignoreCasing"))

    @ignore_casing.setter
    def ignore_casing(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6a4dc82422fde02c28f431f8e7195b2127bca03b7df47af52aee2ff12094006e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreCasing", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreMissingProperty")
    def ignore_missing_property(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ignoreMissingProperty"))

    @ignore_missing_property.setter
    def ignore_missing_property(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b1782dbf7b02ed52961a4205503aca187b7106b3a0bfd3cafae71e2f88a092c7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreMissingProperty", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreNullProperty")
    def ignore_null_property(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ignoreNullProperty"))

    @ignore_null_property.setter
    def ignore_null_property(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e8c25d48a5b70eb1e518b0635971afebd6c11842770d31864e05a8be476279b3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreNullProperty", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="location")
    def location(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "location"))

    @location.setter
    def location(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__73f14c846d034e14a520c66cdb57b4c55f0d3715d3e92b8569f62f7937340117)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "location", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="locks")
    def locks(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "locks"))

    @locks.setter
    def locks(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__aedf7f459f1356c3e5ff931bace09a9cfddf8e50c7f7d90e20759cf291ecc974)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "locks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ee347af926f652f52cb877e9330b07606675f9169969519103a9fc2619d9b7a3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="parentId")
    def parent_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "parentId"))

    @parent_id.setter
    def parent_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__774b6b1f0022e2d05d3da015a0bd0f0bd6c9bd8201acb30dba6e76cb283eebef)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "parentId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="readHeaders")
    def read_headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "readHeaders"))

    @read_headers.setter
    def read_headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__56331a8abb7293b345d6de794002d608b9af38d109b4b3b30416849325989f20)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "readHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="readQueryParameters")
    def read_query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "readQueryParameters"))

    @read_query_parameters.setter
    def read_query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0edd044ca4c1100f5081c96be9e4375da437d298023b89429d4742608874cd20)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "readQueryParameters", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="replaceTriggersExternalValues")
    def replace_triggers_external_values(
        self,
    ) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "replaceTriggersExternalValues"))

    @replace_triggers_external_values.setter
    def replace_triggers_external_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bca9d36f05ea5051b413431827cab24afb5efdd948157f0dbbe41afbe5051a06)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "replaceTriggersExternalValues", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="replaceTriggersRefs")
    def replace_triggers_refs(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "replaceTriggersRefs"))

    @replace_triggers_refs.setter
    def replace_triggers_refs(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e75b1cb543a8d893effae76cab0d990fb26fb0bae7406e4951fbd8799db2f0ec)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "replaceTriggersRefs", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="responseExportValues")
    def response_export_values(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "responseExportValues"))

    @response_export_values.setter
    def response_export_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed79344335f9a7bd4866c2c6f4e00fa759b2bf53dbe72fc1f936f06b9b7fffc7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "responseExportValues", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="schemaValidationEnabled")
    def schema_validation_enabled(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "schemaValidationEnabled"))

    @schema_validation_enabled.setter
    def schema_validation_enabled(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ce5960fea582f733a7c35926c657f2af81f47e03dffff6da5ce07a765ac34b04)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "schemaValidationEnabled", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sensitiveBody")
    def sensitive_body(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "sensitiveBody"))

    @sensitive_body.setter
    def sensitive_body(self, value: typing.Mapping[builtins.str, typing.Any]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__647da92e77401455ca531dcad90f1148a1eed51de6584aa221ae85bafbf9a7a6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sensitiveBody", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sensitiveBodyVersion")
    def sensitive_body_version(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "sensitiveBodyVersion"))

    @sensitive_body_version.setter
    def sensitive_body_version(
        self,
        value: typing.Mapping[builtins.str, builtins.str],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eed382229ea51745837ae7636ac301d9a8efa2817c2d08865f6b23b2fff2cad6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sensitiveBodyVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="tags")
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "tags"))

    @tags.setter
    def tags(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__94232a5bc0d4b95dab2199eb4df2ac8ac4243241bf1498a92a018e16d021c524)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "tags", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__31ce26b84c95c3464ede767cf4fd3c6de430fb6ba87ad1516e0b7625c810bbff)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="updateHeaders")
    def update_headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "updateHeaders"))

    @update_headers.setter
    def update_headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fc3ef6602372c9803775076264a3e4fb0d3a2a76fd9e798ca883e4c9ddb7ddb7)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "updateHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="updateQueryParameters")
    def update_query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "updateQueryParameters"))

    @update_query_parameters.setter
    def update_query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__dba8ccd73a1fd12b5f0a34cdf34ac452fb3c1d4a0da795697e734f3848ffcbba)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "updateQueryParameters", value) # pyright: ignore[reportArgumentType]


class ResourceAction(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceAction",
):
    '''Represents a {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action azapi_resource_action}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        resource_id: builtins.str,
        type: builtins.str,
        action: typing.Optional[builtins.str] = None,
        body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        locks: typing.Optional[typing.Sequence[builtins.str]] = None,
        method: typing.Optional[builtins.str] = None,
        query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_ResourceActionRetry_9fc7b6fd, typing.Dict[builtins.str, typing.Any]]] = None,
        sensitive_response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        timeouts: typing.Optional[typing.Union[_ResourceActionTimeouts_e30653fd, typing.Dict[builtins.str, typing.Any]]] = None,
        when: typing.Optional[builtins.str] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action azapi_resource_action} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param resource_id: The ID of an existing Azure source. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#resource_id ResourceAction#resource_id}
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#type ResourceAction#type}
        :param action: The name of the resource action. It's also possible to make HTTP requests towards the resource ID if leave this field empty. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#action ResourceAction#action}
        :param body: A dynamic attribute that contains the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#body ResourceAction#body}
        :param headers: A map of headers to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#headers ResourceAction#headers}
        :param locks: A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#locks ResourceAction#locks}
        :param method: Specifies the HTTP method of the azure resource action. Allowed values are ``POST``, ``PATCH``, ``PUT`` and ``DELETE``. Defaults to ``POST``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#method ResourceAction#method}
        :param query_parameters: A map of query parameters to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#query_parameters ResourceAction#query_parameters}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#response_export_values ResourceAction#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#retry ResourceAction#retry}
        :param sensitive_response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#sensitive_response_export_values ResourceAction#sensitive_response_export_values}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#timeouts ResourceAction#timeouts}
        :param when: When to perform the action, value must be one of: ``apply``, ``destroy``. Default is ``apply``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#when ResourceAction#when}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ed7211cf6cfb3e62134dffb3412feffbc3f7e0fc1e3e24c6bd728da81a420360)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = _ResourceActionConfig_2267cc37(
            resource_id=resource_id,
            type=type,
            action=action,
            body=body,
            headers=headers,
            locks=locks,
            method=method,
            query_parameters=query_parameters,
            response_export_values=response_export_values,
            retry=retry,
            sensitive_response_export_values=sensitive_response_export_values,
            timeouts=timeouts,
            when=when,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a ResourceAction resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the ResourceAction to import.
        :param import_from_id: The id of the existing ResourceAction that should be imported. Refer to the {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the ResourceAction to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8ef57bb505f471358a36593a267eb570da997b3ec024c65acaec1682351584dc)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putRetry")
    def put_retry(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#error_message_regex ResourceAction#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#interval_seconds ResourceAction#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#max_interval_seconds ResourceAction#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#multiplier ResourceAction#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#randomization_factor ResourceAction#randomization_factor}
        '''
        value = _ResourceActionRetry_9fc7b6fd(
            error_message_regex=error_message_regex,
            interval_seconds=interval_seconds,
            max_interval_seconds=max_interval_seconds,
            multiplier=multiplier,
            randomization_factor=randomization_factor,
        )

        return typing.cast(None, jsii.invoke(self, "putRetry", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#create ResourceAction#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#delete ResourceAction#delete}
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#read ResourceAction#read}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#update ResourceAction#update}
        '''
        value = _ResourceActionTimeouts_e30653fd(
            create=create, delete=delete, read=read, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetAction")
    def reset_action(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetAction", []))

    @jsii.member(jsii_name="resetBody")
    def reset_body(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBody", []))

    @jsii.member(jsii_name="resetHeaders")
    def reset_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetHeaders", []))

    @jsii.member(jsii_name="resetLocks")
    def reset_locks(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLocks", []))

    @jsii.member(jsii_name="resetMethod")
    def reset_method(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMethod", []))

    @jsii.member(jsii_name="resetQueryParameters")
    def reset_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetQueryParameters", []))

    @jsii.member(jsii_name="resetResponseExportValues")
    def reset_response_export_values(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetResponseExportValues", []))

    @jsii.member(jsii_name="resetRetry")
    def reset_retry(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetry", []))

    @jsii.member(jsii_name="resetSensitiveResponseExportValues")
    def reset_sensitive_response_export_values(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSensitiveResponseExportValues", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="resetWhen")
    def reset_when(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetWhen", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="output")
    def output(self) -> _cdktf_9a9027ec.AnyMap:
        return typing.cast(_cdktf_9a9027ec.AnyMap, jsii.get(self, "output"))

    @builtins.property
    @jsii.member(jsii_name="retry")
    def retry(self) -> _ResourceActionRetryOutputReference_2c40390c:
        return typing.cast(_ResourceActionRetryOutputReference_2c40390c, jsii.get(self, "retry"))

    @builtins.property
    @jsii.member(jsii_name="sensitiveOutput")
    def sensitive_output(self) -> _cdktf_9a9027ec.AnyMap:
        return typing.cast(_cdktf_9a9027ec.AnyMap, jsii.get(self, "sensitiveOutput"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> _ResourceActionTimeoutsOutputReference_13d5cf9c:
        return typing.cast(_ResourceActionTimeoutsOutputReference_13d5cf9c, jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="actionInput")
    def action_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "actionInput"))

    @builtins.property
    @jsii.member(jsii_name="bodyInput")
    def body_input(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "bodyInput"))

    @builtins.property
    @jsii.member(jsii_name="headersInput")
    def headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "headersInput"))

    @builtins.property
    @jsii.member(jsii_name="locksInput")
    def locks_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "locksInput"))

    @builtins.property
    @jsii.member(jsii_name="methodInput")
    def method_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "methodInput"))

    @builtins.property
    @jsii.member(jsii_name="queryParametersInput")
    def query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "queryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="resourceIdInput")
    def resource_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "resourceIdInput"))

    @builtins.property
    @jsii.member(jsii_name="responseExportValuesInput")
    def response_export_values_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "responseExportValuesInput"))

    @builtins.property
    @jsii.member(jsii_name="retryInput")
    def retry_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionRetry_9fc7b6fd]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionRetry_9fc7b6fd]], jsii.get(self, "retryInput"))

    @builtins.property
    @jsii.member(jsii_name="sensitiveResponseExportValuesInput")
    def sensitive_response_export_values_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "sensitiveResponseExportValuesInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionTimeouts_e30653fd]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionTimeouts_e30653fd]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="whenInput")
    def when_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "whenInput"))

    @builtins.property
    @jsii.member(jsii_name="action")
    def action(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "action"))

    @action.setter
    def action(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4802a184f17f2b66276dcd1eb7bf805f5f8a1d4981a0a36420566ed5816ce157)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "action", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="body")
    def body(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "body"))

    @body.setter
    def body(self, value: typing.Mapping[builtins.str, typing.Any]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cc11d08f3d72223c6f8c21ad488b3e63a4854a901f8dd3e8e2b9a52b4330becf)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "body", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="headers")
    def headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "headers"))

    @headers.setter
    def headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d570e5194a31996c4fc765927b86bded081860957843c6c177603669636be17b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "headers", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="locks")
    def locks(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "locks"))

    @locks.setter
    def locks(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7d4e9070e6dcc3548dd0ee6db6ba54eb1806f29d382a5f98732c73b98e25605)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "locks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="method")
    def method(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "method"))

    @method.setter
    def method(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7bfcfc749c1be9f37d8f4a9dc82d34f3c65bc8956187f7ab4b8bdbd34d03047f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "method", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="queryParameters")
    def query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "queryParameters"))

    @query_parameters.setter
    def query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c803dc9d35193a715b32bb4a538623fbc4cce33637036ef2b143908f18153f42)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "queryParameters", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @resource_id.setter
    def resource_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__118661828927020e7455b74337b2969bfe2421dc0f91ff3777820d45df0fc488)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "resourceId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="responseExportValues")
    def response_export_values(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "responseExportValues"))

    @response_export_values.setter
    def response_export_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__427e45d3f340a164eaf38b4914bd43cc58ac59226eecf28930970b36d6d245d2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "responseExportValues", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sensitiveResponseExportValues")
    def sensitive_response_export_values(
        self,
    ) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "sensitiveResponseExportValues"))

    @sensitive_response_export_values.setter
    def sensitive_response_export_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6ee811c7d7e38a8ee4151f7bcec0e734fdfdec213fd1defe12b974345ab32846)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sensitiveResponseExportValues", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e0918a878fb046e63784bdd0532b893eee6524b724e4d1abed1c6589b362ec71)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="when")
    def when(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "when"))

    @when.setter
    def when(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__26b275abdad403e0e7384c8d1daba084994eb30d8fdecae8f5883810fdd6cb8c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "when", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceActionConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "resource_id": "resourceId",
        "type": "type",
        "action": "action",
        "body": "body",
        "headers": "headers",
        "locks": "locks",
        "method": "method",
        "query_parameters": "queryParameters",
        "response_export_values": "responseExportValues",
        "retry": "retry",
        "sensitive_response_export_values": "sensitiveResponseExportValues",
        "timeouts": "timeouts",
        "when": "when",
    },
)
class ResourceActionConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        resource_id: builtins.str,
        type: builtins.str,
        action: typing.Optional[builtins.str] = None,
        body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        locks: typing.Optional[typing.Sequence[builtins.str]] = None,
        method: typing.Optional[builtins.str] = None,
        query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_ResourceActionRetry_9fc7b6fd, typing.Dict[builtins.str, typing.Any]]] = None,
        sensitive_response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        timeouts: typing.Optional[typing.Union[_ResourceActionTimeouts_e30653fd, typing.Dict[builtins.str, typing.Any]]] = None,
        when: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param resource_id: The ID of an existing Azure source. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#resource_id ResourceAction#resource_id}
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#type ResourceAction#type}
        :param action: The name of the resource action. It's also possible to make HTTP requests towards the resource ID if leave this field empty. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#action ResourceAction#action}
        :param body: A dynamic attribute that contains the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#body ResourceAction#body}
        :param headers: A map of headers to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#headers ResourceAction#headers}
        :param locks: A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#locks ResourceAction#locks}
        :param method: Specifies the HTTP method of the azure resource action. Allowed values are ``POST``, ``PATCH``, ``PUT`` and ``DELETE``. Defaults to ``POST``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#method ResourceAction#method}
        :param query_parameters: A map of query parameters to include in the request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#query_parameters ResourceAction#query_parameters}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#response_export_values ResourceAction#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#retry ResourceAction#retry}
        :param sensitive_response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#sensitive_response_export_values ResourceAction#sensitive_response_export_values}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#timeouts ResourceAction#timeouts}
        :param when: When to perform the action, value must be one of: ``apply``, ``destroy``. Default is ``apply``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#when ResourceAction#when}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(retry, dict):
            retry = _ResourceActionRetry_9fc7b6fd(**retry)
        if isinstance(timeouts, dict):
            timeouts = _ResourceActionTimeouts_e30653fd(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3f400e091f05d2eacb197f50aa1c9cb5b66fb8d2cf52487205e9daf3f9f3f5be)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument action", value=action, expected_type=type_hints["action"])
            check_type(argname="argument body", value=body, expected_type=type_hints["body"])
            check_type(argname="argument headers", value=headers, expected_type=type_hints["headers"])
            check_type(argname="argument locks", value=locks, expected_type=type_hints["locks"])
            check_type(argname="argument method", value=method, expected_type=type_hints["method"])
            check_type(argname="argument query_parameters", value=query_parameters, expected_type=type_hints["query_parameters"])
            check_type(argname="argument response_export_values", value=response_export_values, expected_type=type_hints["response_export_values"])
            check_type(argname="argument retry", value=retry, expected_type=type_hints["retry"])
            check_type(argname="argument sensitive_response_export_values", value=sensitive_response_export_values, expected_type=type_hints["sensitive_response_export_values"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
            check_type(argname="argument when", value=when, expected_type=type_hints["when"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "resource_id": resource_id,
            "type": type,
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
        if action is not None:
            self._values["action"] = action
        if body is not None:
            self._values["body"] = body
        if headers is not None:
            self._values["headers"] = headers
        if locks is not None:
            self._values["locks"] = locks
        if method is not None:
            self._values["method"] = method
        if query_parameters is not None:
            self._values["query_parameters"] = query_parameters
        if response_export_values is not None:
            self._values["response_export_values"] = response_export_values
        if retry is not None:
            self._values["retry"] = retry
        if sensitive_response_export_values is not None:
            self._values["sensitive_response_export_values"] = sensitive_response_export_values
        if timeouts is not None:
            self._values["timeouts"] = timeouts
        if when is not None:
            self._values["when"] = when

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
    def resource_id(self) -> builtins.str:
        '''The ID of an existing Azure source.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#resource_id ResourceAction#resource_id}
        '''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> builtins.str:
        '''In a format like ``<resource-type>@<api-version>``.

        ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#type ResourceAction#type}
        '''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def action(self) -> typing.Optional[builtins.str]:
        '''The name of the resource action.

        It's also possible to make HTTP requests towards the resource ID if leave this field empty.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#action ResourceAction#action}
        '''
        result = self._values.get("action")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def body(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''A dynamic attribute that contains the request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#body ResourceAction#body}
        '''
        result = self._values.get("body")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def headers(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A map of headers to include in the request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#headers ResourceAction#headers}
        '''
        result = self._values.get("headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def locks(self) -> typing.Optional[typing.List[builtins.str]]:
        '''A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#locks ResourceAction#locks}
        '''
        result = self._values.get("locks")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def method(self) -> typing.Optional[builtins.str]:
        '''Specifies the HTTP method of the azure resource action.

        Allowed values are ``POST``, ``PATCH``, ``PUT`` and ``DELETE``. Defaults to ``POST``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#method ResourceAction#method}
        '''
        result = self._values.get("method")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A map of query parameters to include in the request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#query_parameters ResourceAction#query_parameters}
        '''
        result = self._values.get("query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    @builtins.property
    def response_export_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''The attribute can accept either a list or a map.

        - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output::

             {
             	properties = {
             		loginServer = "registry1.azurecr.io"
             		policies = {
             			quarantinePolicy = {
             				status = "disabled"
             			}
             		}
             	}
             }
        - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output::

             {
             	"login_server" = "registry1.azurecr.io"
             	"quarantine_status" = "disabled"
             }

        To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#response_export_values ResourceAction#response_export_values}
        '''
        result = self._values.get("response_export_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def retry(self) -> typing.Optional[_ResourceActionRetry_9fc7b6fd]:
        '''The retry object supports the following attributes:.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#retry ResourceAction#retry}
        '''
        result = self._values.get("retry")
        return typing.cast(typing.Optional[_ResourceActionRetry_9fc7b6fd], result)

    @builtins.property
    def sensitive_response_export_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''The attribute can accept either a list or a map.

        - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output::

             {
             	properties = {
             		loginServer = "registry1.azurecr.io"
             		policies = {
             			quarantinePolicy = {
             				status = "disabled"
             			}
             		}
             	}
             }
        - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output::

             {
             	"login_server" = "registry1.azurecr.io"
             	"quarantine_status" = "disabled"
             }

        To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#sensitive_response_export_values ResourceAction#sensitive_response_export_values}
        '''
        result = self._values.get("sensitive_response_export_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def timeouts(self) -> typing.Optional[_ResourceActionTimeouts_e30653fd]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#timeouts ResourceAction#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional[_ResourceActionTimeouts_e30653fd], result)

    @builtins.property
    def when(self) -> typing.Optional[builtins.str]:
        '''When to perform the action, value must be one of: ``apply``, ``destroy``. Default is ``apply``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#when ResourceAction#when}
        '''
        result = self._values.get("when")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceActionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceActionRetry",
    jsii_struct_bases=[],
    name_mapping={
        "error_message_regex": "errorMessageRegex",
        "interval_seconds": "intervalSeconds",
        "max_interval_seconds": "maxIntervalSeconds",
        "multiplier": "multiplier",
        "randomization_factor": "randomizationFactor",
    },
)
class ResourceActionRetry:
    def __init__(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#error_message_regex ResourceAction#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#interval_seconds ResourceAction#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#max_interval_seconds ResourceAction#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#multiplier ResourceAction#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#randomization_factor ResourceAction#randomization_factor}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0aa17ff925f2207e7e26fd17277d1c176a2bdbaa68aa0f639997a7fa05ca0768)
            check_type(argname="argument error_message_regex", value=error_message_regex, expected_type=type_hints["error_message_regex"])
            check_type(argname="argument interval_seconds", value=interval_seconds, expected_type=type_hints["interval_seconds"])
            check_type(argname="argument max_interval_seconds", value=max_interval_seconds, expected_type=type_hints["max_interval_seconds"])
            check_type(argname="argument multiplier", value=multiplier, expected_type=type_hints["multiplier"])
            check_type(argname="argument randomization_factor", value=randomization_factor, expected_type=type_hints["randomization_factor"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "error_message_regex": error_message_regex,
        }
        if interval_seconds is not None:
            self._values["interval_seconds"] = interval_seconds
        if max_interval_seconds is not None:
            self._values["max_interval_seconds"] = max_interval_seconds
        if multiplier is not None:
            self._values["multiplier"] = multiplier
        if randomization_factor is not None:
            self._values["randomization_factor"] = randomization_factor

    @builtins.property
    def error_message_regex(self) -> typing.List[builtins.str]:
        '''A list of regular expressions to match against error messages.

        If any of the regular expressions match, the request will be retried.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#error_message_regex ResourceAction#error_message_regex}
        '''
        result = self._values.get("error_message_regex")
        assert result is not None, "Required property 'error_message_regex' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The base number of seconds to wait between retries. Default is ``10``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#interval_seconds ResourceAction#interval_seconds}
        '''
        result = self._values.get("interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of seconds to wait between retries. Default is ``180``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#max_interval_seconds ResourceAction#max_interval_seconds}
        '''
        result = self._values.get("max_interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def multiplier(self) -> typing.Optional[jsii.Number]:
        '''The multiplier to apply to the interval between retries. Default is ``1.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#multiplier ResourceAction#multiplier}
        '''
        result = self._values.get("multiplier")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def randomization_factor(self) -> typing.Optional[jsii.Number]:
        '''The randomization factor to apply to the interval between retries.

        The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#randomization_factor ResourceAction#randomization_factor}
        '''
        result = self._values.get("randomization_factor")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceActionRetry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResourceActionRetryOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceActionRetryOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__044aba673a12de559b99c371dce11c2511cf30f570d06603c4b5d1e72e44603c)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetIntervalSeconds")
    def reset_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIntervalSeconds", []))

    @jsii.member(jsii_name="resetMaxIntervalSeconds")
    def reset_max_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxIntervalSeconds", []))

    @jsii.member(jsii_name="resetMultiplier")
    def reset_multiplier(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMultiplier", []))

    @jsii.member(jsii_name="resetRandomizationFactor")
    def reset_randomization_factor(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRandomizationFactor", []))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegexInput")
    def error_message_regex_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "errorMessageRegexInput"))

    @builtins.property
    @jsii.member(jsii_name="intervalSecondsInput")
    def interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "intervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSecondsInput")
    def max_interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxIntervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="multiplierInput")
    def multiplier_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "multiplierInput"))

    @builtins.property
    @jsii.member(jsii_name="randomizationFactorInput")
    def randomization_factor_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "randomizationFactorInput"))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegex")
    def error_message_regex(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "errorMessageRegex"))

    @error_message_regex.setter
    def error_message_regex(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8716ca1a26a47ba52d8afbbf6339afcaf7f8022a61ff0f21cbc64c2bd9bd3577)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "errorMessageRegex", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="intervalSeconds")
    def interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "intervalSeconds"))

    @interval_seconds.setter
    def interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c124095bf9aed741aed2623777da4d3f54b3d49015f94b3d41e66571807fa542)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "intervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSeconds")
    def max_interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxIntervalSeconds"))

    @max_interval_seconds.setter
    def max_interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__974183ffc819fbc428c8be6a73aa387e921f185320582d404dbc3881826f2430)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxIntervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="multiplier")
    def multiplier(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "multiplier"))

    @multiplier.setter
    def multiplier(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c07fe5d92db5958faa7557f79121a465920ad01b8a99004fe1befa94bdf471f1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "multiplier", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="randomizationFactor")
    def randomization_factor(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "randomizationFactor"))

    @randomization_factor.setter
    def randomization_factor(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__968667ca7137bf50f95a410d554ac0888d7f421ce603e25758f09bee7a9fff2b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "randomizationFactor", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionRetry_9fc7b6fd]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionRetry_9fc7b6fd]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionRetry_9fc7b6fd]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3a17979ab57d586c4adc3ea8c1aef8bfed3352dea9d8835e6a63a3363903b866)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceActionTimeouts",
    jsii_struct_bases=[],
    name_mapping={
        "create": "create",
        "delete": "delete",
        "read": "read",
        "update": "update",
    },
)
class ResourceActionTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#create ResourceAction#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#delete ResourceAction#delete}
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#read ResourceAction#read}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#update ResourceAction#update}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__53cc427a1fb084147d0f29e0000dca7fd21f91c99ffa05604718b5ef17d6e266)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
            check_type(argname="argument read", value=read, expected_type=type_hints["read"])
            check_type(argname="argument update", value=update, expected_type=type_hints["update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete
        if read is not None:
            self._values["read"] = read
        if update is not None:
            self._values["update"] = update

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#create ResourceAction#create}
        '''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#delete ResourceAction#delete}
        '''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#read ResourceAction#read}
        '''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource_action#update ResourceAction#update}
        '''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceActionTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResourceActionTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceActionTimeoutsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a0c258872b4b82cfa9f4d7d4ae4b70267974e2dce3aa29a76bceb9f514bb7526)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @jsii.member(jsii_name="resetRead")
    def reset_read(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRead", []))

    @jsii.member(jsii_name="resetUpdate")
    def reset_update(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdate", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="readInput")
    def read_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "readInput"))

    @builtins.property
    @jsii.member(jsii_name="updateInput")
    def update_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "updateInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ec5a7d28f49e2c7c3a9e4fecaf186c8e0a4e19863add1c419d5ed060856be5c1)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77b6b0391aa6f1efae940ae23a2dd8aa367627c5469e518e52001ee7d4c68fb6)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7684aabb9384c92d4c6f3e970d1f77e31ce6c05fa59ddff7e0b73e48c24fbddd)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5c967c72f8bf6d03e63852d252f8629d570ebbd61107d571ea8f23be04127c24)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionTimeouts_e30653fd]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionTimeouts_e30653fd]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionTimeouts_e30653fd]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9845d8a028c4221d05a56dbb071314406d17d9ec7a74a93553532d769fde4a5b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "type": "type",
        "body": "body",
        "create_headers": "createHeaders",
        "create_query_parameters": "createQueryParameters",
        "delete_headers": "deleteHeaders",
        "delete_query_parameters": "deleteQueryParameters",
        "identity": "identity",
        "ignore_casing": "ignoreCasing",
        "ignore_missing_property": "ignoreMissingProperty",
        "ignore_null_property": "ignoreNullProperty",
        "location": "location",
        "locks": "locks",
        "name": "name",
        "parent_id": "parentId",
        "read_headers": "readHeaders",
        "read_query_parameters": "readQueryParameters",
        "replace_triggers_external_values": "replaceTriggersExternalValues",
        "replace_triggers_refs": "replaceTriggersRefs",
        "response_export_values": "responseExportValues",
        "retry": "retry",
        "schema_validation_enabled": "schemaValidationEnabled",
        "sensitive_body": "sensitiveBody",
        "sensitive_body_version": "sensitiveBodyVersion",
        "tags": "tags",
        "timeouts": "timeouts",
        "update_headers": "updateHeaders",
        "update_query_parameters": "updateQueryParameters",
    },
)
class ResourceConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        type: builtins.str,
        body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        create_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        create_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        delete_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        delete_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        identity: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_ResourceIdentity_d0fe12c0, typing.Dict[builtins.str, typing.Any]]]]] = None,
        ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ignore_null_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        location: typing.Optional[builtins.str] = None,
        locks: typing.Optional[typing.Sequence[builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        parent_id: typing.Optional[builtins.str] = None,
        read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        replace_triggers_external_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        replace_triggers_refs: typing.Optional[typing.Sequence[builtins.str]] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_ResourceRetry_50237e4f, typing.Dict[builtins.str, typing.Any]]] = None,
        schema_validation_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union[_ResourceTimeouts_0b401feb, typing.Dict[builtins.str, typing.Any]]] = None,
        update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#type Resource#type}
        :param body: A dynamic attribute that contains the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#body Resource#body}
        :param create_headers: A mapping of headers to be sent with the create request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create_headers Resource#create_headers}
        :param create_query_parameters: A mapping of query parameters to be sent with the create request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create_query_parameters Resource#create_query_parameters}
        :param delete_headers: A mapping of headers to be sent with the delete request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete_headers Resource#delete_headers}
        :param delete_query_parameters: A mapping of query parameters to be sent with the delete request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete_query_parameters Resource#delete_query_parameters}
        :param identity: identity block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#identity Resource#identity}
        :param ignore_casing: Whether ignore the casing of the property names in the response body. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_casing Resource#ignore_casing}
        :param ignore_missing_property: Whether ignore not returned properties like credentials in ``body`` to suppress plan-diff. Defaults to ``true``. It's recommend to enable this option when some sensitive properties are not returned in response body, instead of setting them in ``lifecycle.ignore_changes`` because it will make the sensitive fields unable to update. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_missing_property Resource#ignore_missing_property}
        :param ignore_null_property: When set to ``true``, the provider will ignore properties whose values are ``null`` in the ``body``. These properties will not be included in the request body sent to the API, and the difference will not be shown in the plan output. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_null_property Resource#ignore_null_property}
        :param location: The location of the Azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#location Resource#location}
        :param locks: A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#locks Resource#locks}
        :param name: Specifies the name of the azure resource. Changing this forces a new resource to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#name Resource#name}
        :param parent_id: The ID of the azure resource in which this resource is created. It supports different kinds of deployment scope for **top level** resources: - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group. - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group. - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to. - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60 - tenant scope: ``parent_id`` should be / For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet. For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#parent_id Resource#parent_id}
        :param read_headers: A mapping of headers to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read_headers Resource#read_headers}
        :param read_query_parameters: A mapping of query parameters to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read_query_parameters Resource#read_query_parameters}
        :param replace_triggers_external_values: Will trigger a replace of the resource when the value changes and is not ``null``. This can be used by practitioners to force a replace of the resource when certain values change, e.g. changing the SKU of a virtual machine based on the value of variables or locals. The value is a ``dynamic``, so practitioners can compose the input however they wish. For a "break glass" set the value to ``null`` to prevent the plan modifier taking effect. If you have ``null`` values that you do want to be tracked as affecting the resource replacement, include these inside an object. Advanced use cases are possible and resource replacement can be triggered by values external to the resource, for example when a dependent resource changes. e.g. to replace a resource when either the SKU or os_type attributes change:: resource "azapi_resource" "example" { name = var.name type = "Microsoft.Network/publicIPAddresses@2023-11-01" parent_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example" body = { properties = { sku = var.sku zones = var.zones } } replace_triggers_external_values = [ var.sku, var.zones, ] } Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#replace_triggers_external_values Resource#replace_triggers_external_values}
        :param replace_triggers_refs: A list of paths in the current Terraform configuration. When the values at these paths change, the resource will be replaced. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#replace_triggers_refs Resource#replace_triggers_refs}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#response_export_values Resource#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#retry Resource#retry}
        :param schema_validation_enabled: Whether enabled the validation on ``type`` and ``body`` with embedded schema. Defaults to ``true``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#schema_validation_enabled Resource#schema_validation_enabled}
        :param sensitive_body: A dynamic attribute that contains the write-only properties of the request body. This will be merge-patched to the body to construct the actual request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#sensitive_body Resource#sensitive_body}
        :param sensitive_body_version: A map where the key is the path to the property in ``sensitive_body`` and the value is the version of the property. The key is a string in the format of ``path.to.property[index].subproperty``, where ``index`` is the index of the item in an array. When the version is changed, the property will be included in the request body, otherwise it will be omitted from the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#sensitive_body_version Resource#sensitive_body_version}
        :param tags: A mapping of tags which should be assigned to the Azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#tags Resource#tags}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#timeouts Resource#timeouts}
        :param update_headers: A mapping of headers to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update_headers Resource#update_headers}
        :param update_query_parameters: A mapping of query parameters to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update_query_parameters Resource#update_query_parameters}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(retry, dict):
            retry = _ResourceRetry_50237e4f(**retry)
        if isinstance(timeouts, dict):
            timeouts = _ResourceTimeouts_0b401feb(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e7d8345dad5f4d2cf356b3e32814b9a20a248746615e1c4c64b9b235b6b4e65c)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument body", value=body, expected_type=type_hints["body"])
            check_type(argname="argument create_headers", value=create_headers, expected_type=type_hints["create_headers"])
            check_type(argname="argument create_query_parameters", value=create_query_parameters, expected_type=type_hints["create_query_parameters"])
            check_type(argname="argument delete_headers", value=delete_headers, expected_type=type_hints["delete_headers"])
            check_type(argname="argument delete_query_parameters", value=delete_query_parameters, expected_type=type_hints["delete_query_parameters"])
            check_type(argname="argument identity", value=identity, expected_type=type_hints["identity"])
            check_type(argname="argument ignore_casing", value=ignore_casing, expected_type=type_hints["ignore_casing"])
            check_type(argname="argument ignore_missing_property", value=ignore_missing_property, expected_type=type_hints["ignore_missing_property"])
            check_type(argname="argument ignore_null_property", value=ignore_null_property, expected_type=type_hints["ignore_null_property"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument locks", value=locks, expected_type=type_hints["locks"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parent_id", value=parent_id, expected_type=type_hints["parent_id"])
            check_type(argname="argument read_headers", value=read_headers, expected_type=type_hints["read_headers"])
            check_type(argname="argument read_query_parameters", value=read_query_parameters, expected_type=type_hints["read_query_parameters"])
            check_type(argname="argument replace_triggers_external_values", value=replace_triggers_external_values, expected_type=type_hints["replace_triggers_external_values"])
            check_type(argname="argument replace_triggers_refs", value=replace_triggers_refs, expected_type=type_hints["replace_triggers_refs"])
            check_type(argname="argument response_export_values", value=response_export_values, expected_type=type_hints["response_export_values"])
            check_type(argname="argument retry", value=retry, expected_type=type_hints["retry"])
            check_type(argname="argument schema_validation_enabled", value=schema_validation_enabled, expected_type=type_hints["schema_validation_enabled"])
            check_type(argname="argument sensitive_body", value=sensitive_body, expected_type=type_hints["sensitive_body"])
            check_type(argname="argument sensitive_body_version", value=sensitive_body_version, expected_type=type_hints["sensitive_body_version"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
            check_type(argname="argument update_headers", value=update_headers, expected_type=type_hints["update_headers"])
            check_type(argname="argument update_query_parameters", value=update_query_parameters, expected_type=type_hints["update_query_parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
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
        if body is not None:
            self._values["body"] = body
        if create_headers is not None:
            self._values["create_headers"] = create_headers
        if create_query_parameters is not None:
            self._values["create_query_parameters"] = create_query_parameters
        if delete_headers is not None:
            self._values["delete_headers"] = delete_headers
        if delete_query_parameters is not None:
            self._values["delete_query_parameters"] = delete_query_parameters
        if identity is not None:
            self._values["identity"] = identity
        if ignore_casing is not None:
            self._values["ignore_casing"] = ignore_casing
        if ignore_missing_property is not None:
            self._values["ignore_missing_property"] = ignore_missing_property
        if ignore_null_property is not None:
            self._values["ignore_null_property"] = ignore_null_property
        if location is not None:
            self._values["location"] = location
        if locks is not None:
            self._values["locks"] = locks
        if name is not None:
            self._values["name"] = name
        if parent_id is not None:
            self._values["parent_id"] = parent_id
        if read_headers is not None:
            self._values["read_headers"] = read_headers
        if read_query_parameters is not None:
            self._values["read_query_parameters"] = read_query_parameters
        if replace_triggers_external_values is not None:
            self._values["replace_triggers_external_values"] = replace_triggers_external_values
        if replace_triggers_refs is not None:
            self._values["replace_triggers_refs"] = replace_triggers_refs
        if response_export_values is not None:
            self._values["response_export_values"] = response_export_values
        if retry is not None:
            self._values["retry"] = retry
        if schema_validation_enabled is not None:
            self._values["schema_validation_enabled"] = schema_validation_enabled
        if sensitive_body is not None:
            self._values["sensitive_body"] = sensitive_body
        if sensitive_body_version is not None:
            self._values["sensitive_body_version"] = sensitive_body_version
        if tags is not None:
            self._values["tags"] = tags
        if timeouts is not None:
            self._values["timeouts"] = timeouts
        if update_headers is not None:
            self._values["update_headers"] = update_headers
        if update_query_parameters is not None:
            self._values["update_query_parameters"] = update_query_parameters

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
    def type(self) -> builtins.str:
        '''In a format like ``<resource-type>@<api-version>``.

        ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#type Resource#type}
        '''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def body(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''A dynamic attribute that contains the request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#body Resource#body}
        '''
        result = self._values.get("body")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def create_headers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of headers to be sent with the create request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create_headers Resource#create_headers}
        '''
        result = self._values.get("create_headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def create_query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A mapping of query parameters to be sent with the create request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create_query_parameters Resource#create_query_parameters}
        '''
        result = self._values.get("create_query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    @builtins.property
    def delete_headers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of headers to be sent with the delete request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete_headers Resource#delete_headers}
        '''
        result = self._values.get("delete_headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def delete_query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A mapping of query parameters to be sent with the delete request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete_query_parameters Resource#delete_query_parameters}
        '''
        result = self._values.get("delete_query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    @builtins.property
    def identity(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]]:
        '''identity block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#identity Resource#identity}
        '''
        result = self._values.get("identity")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]], result)

    @builtins.property
    def ignore_casing(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Whether ignore the casing of the property names in the response body. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_casing Resource#ignore_casing}
        '''
        result = self._values.get("ignore_casing")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def ignore_missing_property(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Whether ignore not returned properties like credentials in ``body`` to suppress plan-diff.

        Defaults to ``true``. It's recommend to enable this option when some sensitive properties are not returned in response body, instead of setting them in ``lifecycle.ignore_changes`` because it will make the sensitive fields unable to update.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_missing_property Resource#ignore_missing_property}
        '''
        result = self._values.get("ignore_missing_property")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def ignore_null_property(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''When set to ``true``, the provider will ignore properties whose values are ``null`` in the ``body``.

        These properties will not be included in the request body sent to the API, and the difference will not be shown in the plan output. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#ignore_null_property Resource#ignore_null_property}
        '''
        result = self._values.get("ignore_null_property")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def location(self) -> typing.Optional[builtins.str]:
        '''The location of the Azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#location Resource#location}
        '''
        result = self._values.get("location")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def locks(self) -> typing.Optional[typing.List[builtins.str]]:
        '''A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#locks Resource#locks}
        '''
        result = self._values.get("locks")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Specifies the name of the azure resource. Changing this forces a new resource to be created.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#name Resource#name}
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parent_id(self) -> typing.Optional[builtins.str]:
        '''The ID of the azure resource in which this resource is created.

        It supports different kinds of deployment scope for **top level** resources:

        - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group.

          - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group.
          - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to.
          - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60
          - tenant scope: ``parent_id`` should be /

        For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet.

        For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#parent_id Resource#parent_id}
        '''
        result = self._values.get("parent_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read_headers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of headers to be sent with the read request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read_headers Resource#read_headers}
        '''
        result = self._values.get("read_headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def read_query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A mapping of query parameters to be sent with the read request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read_query_parameters Resource#read_query_parameters}
        '''
        result = self._values.get("read_query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    @builtins.property
    def replace_triggers_external_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''Will trigger a replace of the resource when the value changes and is not ``null``.

        This can be used by practitioners to force a replace of the resource when certain values change, e.g. changing the SKU of a virtual machine based on the value of variables or locals. The value is a ``dynamic``, so practitioners can compose the input however they wish. For a "break glass" set the value to ``null`` to prevent the plan modifier taking effect.
        If you have ``null`` values that you do want to be tracked as affecting the resource replacement, include these inside an object.
        Advanced use cases are possible and resource replacement can be triggered by values external to the resource, for example when a dependent resource changes.

        e.g. to replace a resource when either the SKU or os_type attributes change::

           resource "azapi_resource" "example" {
             name      = var.name
             type      = "Microsoft.Network/publicIPAddresses@2023-11-01"
             parent_id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example"
             body = {
               properties = {
                 sku   = var.sku
                 zones = var.zones
               }
             }

             replace_triggers_external_values = [
               var.sku,
               var.zones,
             ]
           }

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#replace_triggers_external_values Resource#replace_triggers_external_values}
        '''
        result = self._values.get("replace_triggers_external_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def replace_triggers_refs(self) -> typing.Optional[typing.List[builtins.str]]:
        '''A list of paths in the current Terraform configuration.

        When the values at these paths change, the resource will be replaced.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#replace_triggers_refs Resource#replace_triggers_refs}
        '''
        result = self._values.get("replace_triggers_refs")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def response_export_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''The attribute can accept either a list or a map.

        - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output::

             {
             	properties = {
             		loginServer = "registry1.azurecr.io"
             		policies = {
             			quarantinePolicy = {
             				status = "disabled"
             			}
             		}
             	}
             }
        - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output::

             {
             	"login_server" = "registry1.azurecr.io"
             	"quarantine_status" = "disabled"
             }

        To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#response_export_values Resource#response_export_values}
        '''
        result = self._values.get("response_export_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def retry(self) -> typing.Optional[_ResourceRetry_50237e4f]:
        '''The retry object supports the following attributes:.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#retry Resource#retry}
        '''
        result = self._values.get("retry")
        return typing.cast(typing.Optional[_ResourceRetry_50237e4f], result)

    @builtins.property
    def schema_validation_enabled(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Whether enabled the validation on ``type`` and ``body`` with embedded schema. Defaults to ``true``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#schema_validation_enabled Resource#schema_validation_enabled}
        '''
        result = self._values.get("schema_validation_enabled")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def sensitive_body(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''A dynamic attribute that contains the write-only properties of the request body.

        This will be merge-patched to the body to construct the actual request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#sensitive_body Resource#sensitive_body}
        '''
        result = self._values.get("sensitive_body")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def sensitive_body_version(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A map where the key is the path to the property in ``sensitive_body`` and the value is the version of the property.

        The key is a string in the format of ``path.to.property[index].subproperty``, where ``index`` is the index of the item in an array. When the version is changed, the property will be included in the request body, otherwise it will be omitted from the request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#sensitive_body_version Resource#sensitive_body_version}
        '''
        result = self._values.get("sensitive_body_version")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of tags which should be assigned to the Azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#tags Resource#tags}
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def timeouts(self) -> typing.Optional[_ResourceTimeouts_0b401feb]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#timeouts Resource#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional[_ResourceTimeouts_0b401feb], result)

    @builtins.property
    def update_headers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of headers to be sent with the update request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update_headers Resource#update_headers}
        '''
        result = self._values.get("update_headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def update_query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A mapping of query parameters to be sent with the update request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update_query_parameters Resource#update_query_parameters}
        '''
        result = self._values.get("update_query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceIdentity",
    jsii_struct_bases=[],
    name_mapping={"type": "type", "identity_ids": "identityIds"},
)
class ResourceIdentity:
    def __init__(
        self,
        *,
        type: builtins.str,
        identity_ids: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param type: The Type of Identity which should be used for this azure resource. Possible values are ``SystemAssigned``, ``UserAssigned`` and ``SystemAssigned,UserAssigned``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#type Resource#type}
        :param identity_ids: A list of User Managed Identity ID's which should be assigned to the azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#identity_ids Resource#identity_ids}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__824ac13fa7c89e099cd79c98acc96fb6f37e51b26bdf1ddf0af4040c739c5c28)
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument identity_ids", value=identity_ids, expected_type=type_hints["identity_ids"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
        }
        if identity_ids is not None:
            self._values["identity_ids"] = identity_ids

    @builtins.property
    def type(self) -> builtins.str:
        '''The Type of Identity which should be used for this azure resource. Possible values are ``SystemAssigned``, ``UserAssigned`` and ``SystemAssigned,UserAssigned``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#type Resource#type}
        '''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def identity_ids(self) -> typing.Optional[typing.List[builtins.str]]:
        '''A list of User Managed Identity ID's which should be assigned to the azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#identity_ids Resource#identity_ids}
        '''
        result = self._values.get("identity_ids")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceIdentity(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResourceIdentityList(
    _cdktf_9a9027ec.ComplexList,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceIdentityList",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        wraps_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param wraps_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__46d9e3d2b3f8fdcaf468ac6cdd9f5772b72eedbfd61a3732d77c91ba5cb443e7)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument wraps_set", value=wraps_set, expected_type=type_hints["wraps_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, wraps_set])

    @jsii.member(jsii_name="get")
    def get(self, index: jsii.Number) -> _ResourceIdentityOutputReference_ca99d26d:
        '''
        :param index: the index of the item to return.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__079c11d725773b0d9bf067c41f4f586822b001a392cf492baf4f8d3f89bffc1a)
            check_type(argname="argument index", value=index, expected_type=type_hints["index"])
        return typing.cast(_ResourceIdentityOutputReference_ca99d26d, jsii.invoke(self, "get", [index]))

    @builtins.property
    @jsii.member(jsii_name="terraformAttribute")
    def _terraform_attribute(self) -> builtins.str:
        '''The attribute on the parent resource this class is referencing.'''
        return typing.cast(builtins.str, jsii.get(self, "terraformAttribute"))

    @_terraform_attribute.setter
    def _terraform_attribute(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2ab91a8ff96a791f066486fcc51e54fbd07b041a6e63acd4715dd81d1c529808)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformAttribute", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="terraformResource")
    def _terraform_resource(self) -> _cdktf_9a9027ec.IInterpolatingParent:
        '''The parent resource.'''
        return typing.cast(_cdktf_9a9027ec.IInterpolatingParent, jsii.get(self, "terraformResource"))

    @_terraform_resource.setter
    def _terraform_resource(self, value: _cdktf_9a9027ec.IInterpolatingParent) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b03f453f0d095d6a8130ba47ba55a550a7076f633fe6c39474b13adde51cef69)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "terraformResource", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="wrapsSet")
    def _wraps_set(self) -> builtins.bool:
        '''whether the list is wrapping a set (will add tolist() to be able to access an item via an index).'''
        return typing.cast(builtins.bool, jsii.get(self, "wrapsSet"))

    @_wraps_set.setter
    def _wraps_set(self, value: builtins.bool) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__002b631a4672d92fdbde7fd3e4b1ab0754efdf6ca1265454967eb253bf76f6ee)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "wrapsSet", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7dad453e6a46e27aeab2aaefcf1b85e0a8950613236d933599a9b23e3dfbaa11)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


class ResourceIdentityOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceIdentityOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
        complex_object_index: jsii.Number,
        complex_object_is_from_set: builtins.bool,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        :param complex_object_index: the index of this item in the list.
        :param complex_object_is_from_set: whether the list is wrapping a set (will add tolist() to be able to access an item via an index).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fecedec25f0125f481722e357b287473ad081d58c716306f8f628a9906a10a51)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
            check_type(argname="argument complex_object_index", value=complex_object_index, expected_type=type_hints["complex_object_index"])
            check_type(argname="argument complex_object_is_from_set", value=complex_object_is_from_set, expected_type=type_hints["complex_object_is_from_set"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute, complex_object_index, complex_object_is_from_set])

    @jsii.member(jsii_name="resetIdentityIds")
    def reset_identity_ids(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIdentityIds", []))

    @builtins.property
    @jsii.member(jsii_name="principalId")
    def principal_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "principalId"))

    @builtins.property
    @jsii.member(jsii_name="tenantId")
    def tenant_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "tenantId"))

    @builtins.property
    @jsii.member(jsii_name="identityIdsInput")
    def identity_ids_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "identityIdsInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="identityIds")
    def identity_ids(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "identityIds"))

    @identity_ids.setter
    def identity_ids(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7500f71fdcdd20f2b0f7f36552f2bae7bfd912e4cb15891630e18fbbd5ddb90f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "identityIds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__478e7a7661e631c20769d4f72dff33655c9fb9b6dfd4dbcd1c8b039ea7d43301)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceIdentity_d0fe12c0]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceIdentity_d0fe12c0]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceIdentity_d0fe12c0]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5cae33a9a43572b88227cb083ddc6094faebef35d7e0eb9a0c2a5b2e2315db1a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceRetry",
    jsii_struct_bases=[],
    name_mapping={
        "error_message_regex": "errorMessageRegex",
        "interval_seconds": "intervalSeconds",
        "max_interval_seconds": "maxIntervalSeconds",
        "multiplier": "multiplier",
        "randomization_factor": "randomizationFactor",
    },
)
class ResourceRetry:
    def __init__(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#error_message_regex Resource#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#interval_seconds Resource#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#max_interval_seconds Resource#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#multiplier Resource#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#randomization_factor Resource#randomization_factor}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__70cdc81762c3f46abd55220e2098614ee848b34d9ef2540f0a7af2a039ddefeb)
            check_type(argname="argument error_message_regex", value=error_message_regex, expected_type=type_hints["error_message_regex"])
            check_type(argname="argument interval_seconds", value=interval_seconds, expected_type=type_hints["interval_seconds"])
            check_type(argname="argument max_interval_seconds", value=max_interval_seconds, expected_type=type_hints["max_interval_seconds"])
            check_type(argname="argument multiplier", value=multiplier, expected_type=type_hints["multiplier"])
            check_type(argname="argument randomization_factor", value=randomization_factor, expected_type=type_hints["randomization_factor"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "error_message_regex": error_message_regex,
        }
        if interval_seconds is not None:
            self._values["interval_seconds"] = interval_seconds
        if max_interval_seconds is not None:
            self._values["max_interval_seconds"] = max_interval_seconds
        if multiplier is not None:
            self._values["multiplier"] = multiplier
        if randomization_factor is not None:
            self._values["randomization_factor"] = randomization_factor

    @builtins.property
    def error_message_regex(self) -> typing.List[builtins.str]:
        '''A list of regular expressions to match against error messages.

        If any of the regular expressions match, the request will be retried.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#error_message_regex Resource#error_message_regex}
        '''
        result = self._values.get("error_message_regex")
        assert result is not None, "Required property 'error_message_regex' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The base number of seconds to wait between retries. Default is ``10``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#interval_seconds Resource#interval_seconds}
        '''
        result = self._values.get("interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of seconds to wait between retries. Default is ``180``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#max_interval_seconds Resource#max_interval_seconds}
        '''
        result = self._values.get("max_interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def multiplier(self) -> typing.Optional[jsii.Number]:
        '''The multiplier to apply to the interval between retries. Default is ``1.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#multiplier Resource#multiplier}
        '''
        result = self._values.get("multiplier")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def randomization_factor(self) -> typing.Optional[jsii.Number]:
        '''The randomization factor to apply to the interval between retries.

        The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#randomization_factor Resource#randomization_factor}
        '''
        result = self._values.get("randomization_factor")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceRetry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResourceRetryOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceRetryOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1007cf1cd9d498a580e1e2446590f0f7de56e649816269bc96e5f65fce91a934)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetIntervalSeconds")
    def reset_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIntervalSeconds", []))

    @jsii.member(jsii_name="resetMaxIntervalSeconds")
    def reset_max_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxIntervalSeconds", []))

    @jsii.member(jsii_name="resetMultiplier")
    def reset_multiplier(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMultiplier", []))

    @jsii.member(jsii_name="resetRandomizationFactor")
    def reset_randomization_factor(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRandomizationFactor", []))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegexInput")
    def error_message_regex_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "errorMessageRegexInput"))

    @builtins.property
    @jsii.member(jsii_name="intervalSecondsInput")
    def interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "intervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSecondsInput")
    def max_interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxIntervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="multiplierInput")
    def multiplier_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "multiplierInput"))

    @builtins.property
    @jsii.member(jsii_name="randomizationFactorInput")
    def randomization_factor_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "randomizationFactorInput"))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegex")
    def error_message_regex(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "errorMessageRegex"))

    @error_message_regex.setter
    def error_message_regex(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6cf0453b8d455ebda239ef2d15e351a9ba3d3ac318095e5551a7c809a6f245af)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "errorMessageRegex", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="intervalSeconds")
    def interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "intervalSeconds"))

    @interval_seconds.setter
    def interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f46f28ab1c187e0a1dbde301e2a393e736a2514afe5718fea8f5de7cc6370eb0)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "intervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSeconds")
    def max_interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxIntervalSeconds"))

    @max_interval_seconds.setter
    def max_interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__07a4b466a76af2935685e4214c0496d831bbb9d70c3b3d899ca923f64d381a1b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxIntervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="multiplier")
    def multiplier(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "multiplier"))

    @multiplier.setter
    def multiplier(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cdfc9e42f293b87ab1a4d3cf3558328afb30f1d8efaaababe6d836cd82a5837e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "multiplier", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="randomizationFactor")
    def randomization_factor(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "randomizationFactor"))

    @randomization_factor.setter
    def randomization_factor(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a8396f9879afba7299f44b4c307dc79c8128e783a32cc49fec91aa2452be1e69)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "randomizationFactor", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceRetry_50237e4f]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceRetry_50237e4f]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceRetry_50237e4f]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b8ed4bdead82941d48abf75056f62acb0faf072ed5aaac20e2c11eeb1fd2fc6b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceTimeouts",
    jsii_struct_bases=[],
    name_mapping={
        "create": "create",
        "delete": "delete",
        "read": "read",
        "update": "update",
    },
)
class ResourceTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create Resource#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete Resource#delete}
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read Resource#read}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update Resource#update}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5fef205e8aa0951cff0b7cb2580a414239092590da5cdddd8cf04db2b84500d4)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
            check_type(argname="argument read", value=read, expected_type=type_hints["read"])
            check_type(argname="argument update", value=update, expected_type=type_hints["update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete
        if read is not None:
            self._values["read"] = read
        if update is not None:
            self._values["update"] = update

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#create Resource#create}
        '''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#delete Resource#delete}
        '''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#read Resource#read}
        '''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/resource#update Resource#update}
        '''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResourceTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ResourceTimeoutsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c985873f2f2884beaff3f4e69024cc9fb6909dd15557e9b26abcd8730c9dbb9)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @jsii.member(jsii_name="resetRead")
    def reset_read(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRead", []))

    @jsii.member(jsii_name="resetUpdate")
    def reset_update(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdate", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="readInput")
    def read_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "readInput"))

    @builtins.property
    @jsii.member(jsii_name="updateInput")
    def update_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "updateInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__643f89856bef08221777391c4a6597d6ae2af9553d145f88804330e5ef6bdfce)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fa95d792de620b8b4c313868dd8667755e18255c786ec9ce33d8da96e6faa74e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ccad8ceb2d266f8cba2a2296ed98c85d47d0398103b36e07dd54763080636bf2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__237178dfa5ea8be8f1f85083b6ba7c8abaefbdada288687a3594df0ca8c44b0e)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceTimeouts_0b401feb]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceTimeouts_0b401feb]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceTimeouts_0b401feb]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e99a1d57e8c572123f9373816985bb1fc5e9374c9ffbe951ea0a9b18420beaa)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.RetentionPolicyConfig",
    jsii_struct_bases=[],
    name_mapping={"days": "days", "enabled": "enabled"},
)
class RetentionPolicyConfig:
    def __init__(self, *, days: jsii.Number, enabled: builtins.bool) -> None:
        '''Retention policy configuration.

        :param days: 
        :param enabled: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__304f4fb562352365278a87145329dffd0dd2ef5135da08e2f7e7801e37e416bd)
            check_type(argname="argument days", value=days, expected_type=type_hints["days"])
            check_type(argname="argument enabled", value=enabled, expected_type=type_hints["enabled"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "days": days,
            "enabled": enabled,
        }

    @builtins.property
    def days(self) -> jsii.Number:
        result = self._values.get("days")
        assert result is not None, "Required property 'days' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def enabled(self) -> builtins.bool:
        result = self._values.get("enabled")
        assert result is not None, "Required property 'enabled' is missing"
        return typing.cast(builtins.bool, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RetentionPolicyConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class SchemaMapper(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.SchemaMapper",
):
    '''SchemaMapper class for property transformation and validation.

    This class provides a comprehensive property transformation engine that enables
    mapping between different API schema versions with full validation support.
    It implements JSII-compliant patterns for multi-language code generation.

    The SchemaMapper handles:

    - Property transformation between schema versions
    - Validation against API schema definitions
    - Default value injection for new properties
    - Nested object and array processing
    - Detailed error reporting with property paths

    Example::

        const schema: ApiSchema = {
          resourceType: 'Microsoft.Resources/resourceGroups',
          version: '2024-11-01',
          properties: {
            name: { dataType: PropertyType.STRING, required: true },
            location: { dataType: PropertyType.STRING, required: true }
          },
          required: ['name', 'location']
        };
        
        const mapper = SchemaMapper.create(schema);
        const result = mapper.validateProperties({ name: 'myRG', location: 'eastus' });
    '''

    @jsii.member(jsii_name="create")
    @builtins.classmethod
    def create(
        cls,
        *,
        properties: typing.Mapping[builtins.str, typing.Union[PropertyDefinition, typing.Dict[builtins.str, typing.Any]]],
        required: typing.Sequence[builtins.str],
        resource_type: builtins.str,
        version: builtins.str,
        deprecated: typing.Optional[typing.Sequence[builtins.str]] = None,
        optional: typing.Optional[typing.Sequence[builtins.str]] = None,
        transformation_rules: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        validation_rules: typing.Optional[typing.Sequence[typing.Union[PropertyValidation, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> "SchemaMapper":
        '''Creates a new SchemaMapper instance for the specified schema.

        This factory method creates a SchemaMapper configured for a specific API schema.
        The schema defines the structure, validation rules, and transformation mappings
        that will be used for property operations.

        :param properties: Dictionary of property definitions keyed by property name Each property defines its type, validation, and metadata.
        :param required: Array of property names that are required Properties listed here must be provided by the user.
        :param resource_type: The Azure resource type this schema applies to.
        :param version: The API version this schema represents.
        :param deprecated: Array of property names that are deprecated Usage of these properties will generate warnings.
        :param optional: Array of property names that are optional Used for documentation and validation optimization.
        :param transformation_rules: Property transformation rules for schema mapping Maps input property names to target property names.
        :param validation_rules: Property-specific validation rules Applied in addition to individual property validation.

        :return: A new SchemaMapper instance configured with the provided schema

        :throws: Error if the schema is invalid or missing required properties

        Example::

            const schema: ApiSchema = {
              resourceType: 'Microsoft.Resources/resourceGroups',
              version: '2024-11-01',
              properties: { name: { dataType: PropertyType.STRING, required: true } },
              required: ['name']
            };
            const mapper = SchemaMapper.create(schema);
        '''
        schema = ApiSchema(
            properties=properties,
            required=required,
            resource_type=resource_type,
            version=version,
            deprecated=deprecated,
            optional=optional,
            transformation_rules=transformation_rules,
            validation_rules=validation_rules,
        )

        return typing.cast("SchemaMapper", jsii.sinvoke(cls, "create", [schema]))

    @jsii.member(jsii_name="applyDefaults")
    def apply_defaults(self, properties: typing.Any) -> typing.Any:
        '''Applies default values to properties based on schema definitions.

        This method injects default values for properties that are not provided
        but have default values defined in the schema. It preserves existing
        property values and only adds defaults for missing properties.

        :param properties: - The properties to apply defaults to.

        :return: New properties object with default values applied

        Example::

            const props = { name: 'myRG' };
            const withDefaults = mapper.applyDefaults(props);
            // If schema defines location default as 'eastus':
            // Result: { name: 'myRG', location: 'eastus' }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__058174c0ed978f08ab76647564b62df40a9bb19b60ced7efb4854a8687d88921)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        return typing.cast(typing.Any, jsii.invoke(self, "applyDefaults", [properties]))

    @jsii.member(jsii_name="mapProperty")
    def map_property(
        self,
        property_name: builtins.str,
        value: typing.Any,
        *,
        data_type: builtins.str,
        added_in_version: typing.Optional[builtins.str] = None,
        default_value: typing.Any = None,
        deprecated: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        removed_in_version: typing.Optional[builtins.str] = None,
        required: typing.Optional[builtins.bool] = None,
        validation: typing.Optional[typing.Sequence[typing.Union["ValidationRule", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> typing.Any:
        '''Maps a single property value using transformation rules.

        This method applies transformation logic to a single property value based on
        the target property definition. It handles type conversion, value mapping,
        and custom transformations.

        :param property_name: - The name of the property being mapped.
        :param value: - The source value to transform.
        :param data_type: The data type of the property Must be one of the PropertyType constants.
        :param added_in_version: The API version in which this property was added Used for compatibility analysis and migration planning.
        :param default_value: Default value to use if property is not provided Type must match the property type.
        :param deprecated: Whether this property is deprecated If true, usage warnings will be generated. Default: false
        :param description: Human-readable description of the property Used for documentation generation and IDE support.
        :param removed_in_version: The API version in which this property was removed Used for compatibility analysis and migration planning.
        :param required: Whether this property is required If true, the property must be provided by the user. Default: false
        :param validation: Array of validation rules to apply to this property Rules are evaluated in order and all must pass.

        :return: The transformed property value

        :throws: Error if the transformation fails or types are incompatible

        Example::

            const targetProp = { dataType: PropertyType.STRING, required: true };
            const mapped = mapper.mapProperty('name', 'myResourceGroup', targetProp);
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d00f07f703a0c63e06d066282353d59682aea54af60b51f6e778997215ff4e85)
            check_type(argname="argument property_name", value=property_name, expected_type=type_hints["property_name"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        target_property = PropertyDefinition(
            data_type=data_type,
            added_in_version=added_in_version,
            default_value=default_value,
            deprecated=deprecated,
            description=description,
            removed_in_version=removed_in_version,
            required=required,
            validation=validation,
        )

        return typing.cast(typing.Any, jsii.invoke(self, "mapProperty", [property_name, value, target_property]))

    @jsii.member(jsii_name="transformProperties")
    def transform_properties(
        self,
        source_props: typing.Any,
        *,
        properties: typing.Mapping[builtins.str, typing.Union[PropertyDefinition, typing.Dict[builtins.str, typing.Any]]],
        required: typing.Sequence[builtins.str],
        resource_type: builtins.str,
        version: builtins.str,
        deprecated: typing.Optional[typing.Sequence[builtins.str]] = None,
        optional: typing.Optional[typing.Sequence[builtins.str]] = None,
        transformation_rules: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        validation_rules: typing.Optional[typing.Sequence[typing.Union[PropertyValidation, typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> typing.Any:
        '''Transforms properties from source format to target schema format.

        This method applies transformation rules to convert properties from one schema
        format to another. It handles property renaming, restructuring, type conversion,
        and nested object/array transformations based on the target schema definition.

        :param source_props: - The source properties to transform.
        :param properties: Dictionary of property definitions keyed by property name Each property defines its type, validation, and metadata.
        :param required: Array of property names that are required Properties listed here must be provided by the user.
        :param resource_type: The Azure resource type this schema applies to.
        :param version: The API version this schema represents.
        :param deprecated: Array of property names that are deprecated Usage of these properties will generate warnings.
        :param optional: Array of property names that are optional Used for documentation and validation optimization.
        :param transformation_rules: Property transformation rules for schema mapping Maps input property names to target property names.
        :param validation_rules: Property-specific validation rules Applied in addition to individual property validation.

        :return: The transformed properties matching the target schema format

        :throws: Error if transformation fails due to incompatible types or missing mappings

        Example::

            const sourceProps = { oldName: 'value', location: 'eastus' };
            const targetSchema = {
              transformationRules: { oldName: 'newName' },
              properties: { newName: { dataType: PropertyType.STRING } }
            };
            const transformed = mapper.transformProperties(sourceProps, targetSchema);
            // Result: { newName: 'value', location: 'eastus' }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f5ccb65f61577e810ec730c69ec406b6e5d3b5509aa8b0001ebfcf663e63a645)
            check_type(argname="argument source_props", value=source_props, expected_type=type_hints["source_props"])
        target_schema = ApiSchema(
            properties=properties,
            required=required,
            resource_type=resource_type,
            version=version,
            deprecated=deprecated,
            optional=optional,
            transformation_rules=transformation_rules,
            validation_rules=validation_rules,
        )

        return typing.cast(typing.Any, jsii.invoke(self, "transformProperties", [source_props, target_schema]))

    @jsii.member(jsii_name="validateProperties")
    def validate_properties(self, properties: typing.Any) -> "ValidationResult":
        '''Validates properties against the schema definition.

        This method performs comprehensive validation of properties against the
        configured schema. It checks required properties, data types, validation rules,
        and provides detailed error reporting with property path information.

        :param properties: - The properties to validate.

        :return: Detailed validation results including errors and warnings

        Example::

            const properties = { name: 'myRG', location: 'eastus', tags: { env: 'dev' } };
            const result = mapper.validateProperties(properties);
            
            if (!result.valid) {
              console.log('Validation errors:', result.errors);
              console.log('Property errors:', result.propertyErrors);
            }
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1605f668462eb352fe4acef398fb9da9de5d251b23c0c7fd3cb1adcecb7d8578)
            check_type(argname="argument properties", value=properties, expected_type=type_hints["properties"])
        return typing.cast("ValidationResult", jsii.invoke(self, "validateProperties", [properties]))


class UpdateResource(
    _cdktf_9a9027ec.TerraformResource,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.UpdateResource",
):
    '''Represents a {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource azapi_update_resource}.'''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        type: builtins.str,
        body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        locks: typing.Optional[typing.Sequence[builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        parent_id: typing.Optional[builtins.str] = None,
        read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        resource_id: typing.Optional[builtins.str] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_UpdateResourceRetry_9d4b8e25, typing.Dict[builtins.str, typing.Any]]] = None,
        sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union[_UpdateResourceTimeouts_49a4241d, typing.Dict[builtins.str, typing.Any]]] = None,
        update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
        count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
        depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
        for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
        lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
        provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ) -> None:
        '''Create a new {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource azapi_update_resource} Resource.

        :param scope: The scope in which to define this construct.
        :param id: The scoped construct ID. Must be unique amongst siblings in the same scope
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#type UpdateResource#type}
        :param body: A dynamic attribute that contains the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#body UpdateResource#body}
        :param ignore_casing: Whether ignore the casing of the property names in the response body. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#ignore_casing UpdateResource#ignore_casing}
        :param ignore_missing_property: Whether ignore not returned properties like credentials in ``body`` to suppress plan-diff. Defaults to ``true``. It's recommend to enable this option when some sensitive properties are not returned in response body, instead of setting them in ``lifecycle.ignore_changes`` because it will make the sensitive fields unable to update. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#ignore_missing_property UpdateResource#ignore_missing_property}
        :param locks: A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#locks UpdateResource#locks}
        :param name: Specifies the name of the Azure resource. Changing this forces a new resource to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#name UpdateResource#name}
        :param parent_id: The ID of the azure resource in which this resource is created. It supports different kinds of deployment scope for **top level** resources: - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group. - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group. - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to. - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60 - tenant scope: ``parent_id`` should be / For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet. For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#parent_id UpdateResource#parent_id}
        :param read_headers: A mapping of headers to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read_headers UpdateResource#read_headers}
        :param read_query_parameters: A mapping of query parameters to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read_query_parameters UpdateResource#read_query_parameters}
        :param resource_id: The ID of an existing Azure source. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#resource_id UpdateResource#resource_id}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#response_export_values UpdateResource#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#retry UpdateResource#retry}
        :param sensitive_body: A dynamic attribute that contains the write-only properties of the request body. This will be merge-patched to the body to construct the actual request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#sensitive_body UpdateResource#sensitive_body}
        :param sensitive_body_version: A map where the key is the path to the property in ``sensitive_body`` and the value is the version of the property. The key is a string in the format of ``path.to.property[index].subproperty``, where ``index`` is the index of the item in an array. When the version is changed, the property will be included in the request body, otherwise it will be omitted from the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#sensitive_body_version UpdateResource#sensitive_body_version}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#timeouts UpdateResource#timeouts}
        :param update_headers: A mapping of headers to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update_headers UpdateResource#update_headers}
        :param update_query_parameters: A mapping of query parameters to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update_query_parameters UpdateResource#update_query_parameters}
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9eda0e4199e3ed020d907c935ee7d0fa52de04f194e33663f0a89a25b73dbe26)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        config = _UpdateResourceConfig_d768a9b2(
            type=type,
            body=body,
            ignore_casing=ignore_casing,
            ignore_missing_property=ignore_missing_property,
            locks=locks,
            name=name,
            parent_id=parent_id,
            read_headers=read_headers,
            read_query_parameters=read_query_parameters,
            resource_id=resource_id,
            response_export_values=response_export_values,
            retry=retry,
            sensitive_body=sensitive_body,
            sensitive_body_version=sensitive_body_version,
            timeouts=timeouts,
            update_headers=update_headers,
            update_query_parameters=update_query_parameters,
            connection=connection,
            count=count,
            depends_on=depends_on,
            for_each=for_each,
            lifecycle=lifecycle,
            provider=provider,
            provisioners=provisioners,
        )

        jsii.create(self.__class__, self, [scope, id, config])

    @jsii.member(jsii_name="generateConfigForImport")
    @builtins.classmethod
    def generate_config_for_import(
        cls,
        scope: _constructs_77d1e7e8.Construct,
        import_to_id: builtins.str,
        import_from_id: builtins.str,
        provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    ) -> _cdktf_9a9027ec.ImportableResource:
        '''Generates CDKTF code for importing a UpdateResource resource upon running "cdktf plan ".

        :param scope: The scope in which to define this construct.
        :param import_to_id: The construct id used in the generated config for the UpdateResource to import.
        :param import_from_id: The id of the existing UpdateResource that should be imported. Refer to the {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#import import section} in the documentation of this resource for the id to use
        :param provider: ? Optional instance of the provider where the UpdateResource to import is found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__285b4b8df6ea1bbe89681bd47c939d689791844433922408806679d00fcfcef3)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument import_to_id", value=import_to_id, expected_type=type_hints["import_to_id"])
            check_type(argname="argument import_from_id", value=import_from_id, expected_type=type_hints["import_from_id"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
        return typing.cast(_cdktf_9a9027ec.ImportableResource, jsii.sinvoke(cls, "generateConfigForImport", [scope, import_to_id, import_from_id, provider]))

    @jsii.member(jsii_name="putRetry")
    def put_retry(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#error_message_regex UpdateResource#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#interval_seconds UpdateResource#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#max_interval_seconds UpdateResource#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#multiplier UpdateResource#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#randomization_factor UpdateResource#randomization_factor}
        '''
        value = _UpdateResourceRetry_9d4b8e25(
            error_message_regex=error_message_regex,
            interval_seconds=interval_seconds,
            max_interval_seconds=max_interval_seconds,
            multiplier=multiplier,
            randomization_factor=randomization_factor,
        )

        return typing.cast(None, jsii.invoke(self, "putRetry", [value]))

    @jsii.member(jsii_name="putTimeouts")
    def put_timeouts(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#create UpdateResource#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#delete UpdateResource#delete}
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read UpdateResource#read}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update UpdateResource#update}
        '''
        value = _UpdateResourceTimeouts_49a4241d(
            create=create, delete=delete, read=read, update=update
        )

        return typing.cast(None, jsii.invoke(self, "putTimeouts", [value]))

    @jsii.member(jsii_name="resetBody")
    def reset_body(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetBody", []))

    @jsii.member(jsii_name="resetIgnoreCasing")
    def reset_ignore_casing(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreCasing", []))

    @jsii.member(jsii_name="resetIgnoreMissingProperty")
    def reset_ignore_missing_property(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIgnoreMissingProperty", []))

    @jsii.member(jsii_name="resetLocks")
    def reset_locks(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetLocks", []))

    @jsii.member(jsii_name="resetName")
    def reset_name(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetName", []))

    @jsii.member(jsii_name="resetParentId")
    def reset_parent_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetParentId", []))

    @jsii.member(jsii_name="resetReadHeaders")
    def reset_read_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReadHeaders", []))

    @jsii.member(jsii_name="resetReadQueryParameters")
    def reset_read_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetReadQueryParameters", []))

    @jsii.member(jsii_name="resetResourceId")
    def reset_resource_id(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetResourceId", []))

    @jsii.member(jsii_name="resetResponseExportValues")
    def reset_response_export_values(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetResponseExportValues", []))

    @jsii.member(jsii_name="resetRetry")
    def reset_retry(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRetry", []))

    @jsii.member(jsii_name="resetSensitiveBody")
    def reset_sensitive_body(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSensitiveBody", []))

    @jsii.member(jsii_name="resetSensitiveBodyVersion")
    def reset_sensitive_body_version(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetSensitiveBodyVersion", []))

    @jsii.member(jsii_name="resetTimeouts")
    def reset_timeouts(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetTimeouts", []))

    @jsii.member(jsii_name="resetUpdateHeaders")
    def reset_update_headers(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdateHeaders", []))

    @jsii.member(jsii_name="resetUpdateQueryParameters")
    def reset_update_query_parameters(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdateQueryParameters", []))

    @jsii.member(jsii_name="synthesizeAttributes")
    def _synthesize_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeAttributes", []))

    @jsii.member(jsii_name="synthesizeHclAttributes")
    def _synthesize_hcl_attributes(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "synthesizeHclAttributes", []))

    @jsii.python.classproperty
    @jsii.member(jsii_name="tfResourceType")
    def TF_RESOURCE_TYPE(cls) -> builtins.str:
        return typing.cast(builtins.str, jsii.sget(cls, "tfResourceType"))

    @builtins.property
    @jsii.member(jsii_name="id")
    def id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "id"))

    @builtins.property
    @jsii.member(jsii_name="output")
    def output(self) -> _cdktf_9a9027ec.AnyMap:
        return typing.cast(_cdktf_9a9027ec.AnyMap, jsii.get(self, "output"))

    @builtins.property
    @jsii.member(jsii_name="retry")
    def retry(self) -> _UpdateResourceRetryOutputReference_c5ac7a83:
        return typing.cast(_UpdateResourceRetryOutputReference_c5ac7a83, jsii.get(self, "retry"))

    @builtins.property
    @jsii.member(jsii_name="timeouts")
    def timeouts(self) -> _UpdateResourceTimeoutsOutputReference_876e6cc3:
        return typing.cast(_UpdateResourceTimeoutsOutputReference_876e6cc3, jsii.get(self, "timeouts"))

    @builtins.property
    @jsii.member(jsii_name="bodyInput")
    def body_input(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "bodyInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreCasingInput")
    def ignore_casing_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreCasingInput"))

    @builtins.property
    @jsii.member(jsii_name="ignoreMissingPropertyInput")
    def ignore_missing_property_input(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], jsii.get(self, "ignoreMissingPropertyInput"))

    @builtins.property
    @jsii.member(jsii_name="locksInput")
    def locks_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "locksInput"))

    @builtins.property
    @jsii.member(jsii_name="nameInput")
    def name_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "nameInput"))

    @builtins.property
    @jsii.member(jsii_name="parentIdInput")
    def parent_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "parentIdInput"))

    @builtins.property
    @jsii.member(jsii_name="readHeadersInput")
    def read_headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "readHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="readQueryParametersInput")
    def read_query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "readQueryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="resourceIdInput")
    def resource_id_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "resourceIdInput"))

    @builtins.property
    @jsii.member(jsii_name="responseExportValuesInput")
    def response_export_values_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "responseExportValuesInput"))

    @builtins.property
    @jsii.member(jsii_name="retryInput")
    def retry_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceRetry_9d4b8e25]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceRetry_9d4b8e25]], jsii.get(self, "retryInput"))

    @builtins.property
    @jsii.member(jsii_name="sensitiveBodyInput")
    def sensitive_body_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], jsii.get(self, "sensitiveBodyInput"))

    @builtins.property
    @jsii.member(jsii_name="sensitiveBodyVersionInput")
    def sensitive_body_version_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "sensitiveBodyVersionInput"))

    @builtins.property
    @jsii.member(jsii_name="timeoutsInput")
    def timeouts_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceTimeouts_49a4241d]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceTimeouts_49a4241d]], jsii.get(self, "timeoutsInput"))

    @builtins.property
    @jsii.member(jsii_name="typeInput")
    def type_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "typeInput"))

    @builtins.property
    @jsii.member(jsii_name="updateHeadersInput")
    def update_headers_input(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], jsii.get(self, "updateHeadersInput"))

    @builtins.property
    @jsii.member(jsii_name="updateQueryParametersInput")
    def update_query_parameters_input(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], jsii.get(self, "updateQueryParametersInput"))

    @builtins.property
    @jsii.member(jsii_name="body")
    def body(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "body"))

    @body.setter
    def body(self, value: typing.Mapping[builtins.str, typing.Any]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ef3ab5110927b26ec4e35190ba1fb039205da6afc65e1d149cb24dc3318b739b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "body", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreCasing")
    def ignore_casing(self) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ignoreCasing"))

    @ignore_casing.setter
    def ignore_casing(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f84b46cf749e40dc0e26a55356dd001b385c07bffb5f7f1aa131043b2803adca)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreCasing", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="ignoreMissingProperty")
    def ignore_missing_property(
        self,
    ) -> typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]:
        return typing.cast(typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable], jsii.get(self, "ignoreMissingProperty"))

    @ignore_missing_property.setter
    def ignore_missing_property(
        self,
        value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0af53d0052492bae1435dbf26df821355dcd48596dc1029344d48fa92f52d127)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "ignoreMissingProperty", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="locks")
    def locks(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "locks"))

    @locks.setter
    def locks(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3e87570905a6f6e9fe79320fddfb8e10a1519503f6acca1067ed0ac6f33174b8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "locks", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @name.setter
    def name(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cec6d6dc05cff9dc43a4515baab54a3a05dea3ebf9246e9cd8452273ad80d5ce)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "name", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="parentId")
    def parent_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "parentId"))

    @parent_id.setter
    def parent_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a22c5878d3e6f25d793610dfe1e51d227b756be9da98dcebc40b3277f6ccfb28)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "parentId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="readHeaders")
    def read_headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "readHeaders"))

    @read_headers.setter
    def read_headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8ad7fdd64374f6f9698b8a2d85b077464d43035b3d9646fcce0ae6ff5fd82905)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "readHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="readQueryParameters")
    def read_query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "readQueryParameters"))

    @read_query_parameters.setter
    def read_query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__49a215695d780543d72d505a2b468ae7c34bc39f5294f21cea97fc6e7f59ea3f)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "readQueryParameters", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="resourceId")
    def resource_id(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "resourceId"))

    @resource_id.setter
    def resource_id(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c7c201e303bb80bca4ec7b3a395a918d8a2b4f54d6f763e9935e9ad7c70e95d3)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "resourceId", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="responseExportValues")
    def response_export_values(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "responseExportValues"))

    @response_export_values.setter
    def response_export_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__9248ded17460f9422d30b6b122011a1dce094a566c458b52e339150f27a4442b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "responseExportValues", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sensitiveBody")
    def sensitive_body(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "sensitiveBody"))

    @sensitive_body.setter
    def sensitive_body(self, value: typing.Mapping[builtins.str, typing.Any]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e860dec433546ec4aba9c60cb54c9028770f4c80aa243e3fd9bcd5b8401bab2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sensitiveBody", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="sensitiveBodyVersion")
    def sensitive_body_version(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "sensitiveBodyVersion"))

    @sensitive_body_version.setter
    def sensitive_body_version(
        self,
        value: typing.Mapping[builtins.str, builtins.str],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3473867c4721bd437a53fec1da17012f62acdfb21bb30b9506e1f47907e67f1a)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "sensitiveBodyVersion", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="type")
    def type(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "type"))

    @type.setter
    def type(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0f7e0c3458ce4c1004698f53795ff6aa4aa82f9ccd59ad4d54f4006735edf1c5)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "type", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="updateHeaders")
    def update_headers(self) -> typing.Mapping[builtins.str, builtins.str]:
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.get(self, "updateHeaders"))

    @update_headers.setter
    def update_headers(self, value: typing.Mapping[builtins.str, builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e00bb79f56f169325ac02872e90fdfe9be22a47a723be4044b0f6aec41cd4f39)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "updateHeaders", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="updateQueryParameters")
    def update_query_parameters(
        self,
    ) -> typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        return typing.cast(typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]], jsii.get(self, "updateQueryParameters"))

    @update_query_parameters.setter
    def update_query_parameters(
        self,
        value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__88612cdde8a74df9a9637f8defa8612f932b2262d52a6ea5e082be4db80e12eb)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "updateQueryParameters", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.UpdateResourceConfig",
    jsii_struct_bases=[_cdktf_9a9027ec.TerraformMetaArguments],
    name_mapping={
        "connection": "connection",
        "count": "count",
        "depends_on": "dependsOn",
        "for_each": "forEach",
        "lifecycle": "lifecycle",
        "provider": "provider",
        "provisioners": "provisioners",
        "type": "type",
        "body": "body",
        "ignore_casing": "ignoreCasing",
        "ignore_missing_property": "ignoreMissingProperty",
        "locks": "locks",
        "name": "name",
        "parent_id": "parentId",
        "read_headers": "readHeaders",
        "read_query_parameters": "readQueryParameters",
        "resource_id": "resourceId",
        "response_export_values": "responseExportValues",
        "retry": "retry",
        "sensitive_body": "sensitiveBody",
        "sensitive_body_version": "sensitiveBodyVersion",
        "timeouts": "timeouts",
        "update_headers": "updateHeaders",
        "update_query_parameters": "updateQueryParameters",
    },
)
class UpdateResourceConfig(_cdktf_9a9027ec.TerraformMetaArguments):
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
        type: builtins.str,
        body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
        locks: typing.Optional[typing.Sequence[builtins.str]] = None,
        name: typing.Optional[builtins.str] = None,
        parent_id: typing.Optional[builtins.str] = None,
        read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
        resource_id: typing.Optional[builtins.str] = None,
        response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        retry: typing.Optional[typing.Union[_UpdateResourceRetry_9d4b8e25, typing.Dict[builtins.str, typing.Any]]] = None,
        sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        timeouts: typing.Optional[typing.Union[_UpdateResourceTimeouts_49a4241d, typing.Dict[builtins.str, typing.Any]]] = None,
        update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    ) -> None:
        '''
        :param connection: 
        :param count: 
        :param depends_on: 
        :param for_each: 
        :param lifecycle: 
        :param provider: 
        :param provisioners: 
        :param type: In a format like ``<resource-type>@<api-version>``. ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#type UpdateResource#type}
        :param body: A dynamic attribute that contains the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#body UpdateResource#body}
        :param ignore_casing: Whether ignore the casing of the property names in the response body. Defaults to ``false``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#ignore_casing UpdateResource#ignore_casing}
        :param ignore_missing_property: Whether ignore not returned properties like credentials in ``body`` to suppress plan-diff. Defaults to ``true``. It's recommend to enable this option when some sensitive properties are not returned in response body, instead of setting them in ``lifecycle.ignore_changes`` because it will make the sensitive fields unable to update. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#ignore_missing_property UpdateResource#ignore_missing_property}
        :param locks: A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#locks UpdateResource#locks}
        :param name: Specifies the name of the Azure resource. Changing this forces a new resource to be created. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#name UpdateResource#name}
        :param parent_id: The ID of the azure resource in which this resource is created. It supports different kinds of deployment scope for **top level** resources: - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group. - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group. - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to. - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60 - tenant scope: ``parent_id`` should be / For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet. For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#parent_id UpdateResource#parent_id}
        :param read_headers: A mapping of headers to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read_headers UpdateResource#read_headers}
        :param read_query_parameters: A mapping of query parameters to be sent with the read request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read_query_parameters UpdateResource#read_query_parameters}
        :param resource_id: The ID of an existing Azure source. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#resource_id UpdateResource#resource_id}
        :param response_export_values: The attribute can accept either a list or a map. - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output:: { properties = { loginServer = "registry1.azurecr.io" policies = { quarantinePolicy = { status = "disabled" } } } } - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output:: { "login_server" = "registry1.azurecr.io" "quarantine_status" = "disabled" } To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#response_export_values UpdateResource#response_export_values}
        :param retry: The retry object supports the following attributes:. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#retry UpdateResource#retry}
        :param sensitive_body: A dynamic attribute that contains the write-only properties of the request body. This will be merge-patched to the body to construct the actual request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#sensitive_body UpdateResource#sensitive_body}
        :param sensitive_body_version: A map where the key is the path to the property in ``sensitive_body`` and the value is the version of the property. The key is a string in the format of ``path.to.property[index].subproperty``, where ``index`` is the index of the item in an array. When the version is changed, the property will be included in the request body, otherwise it will be omitted from the request body. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#sensitive_body_version UpdateResource#sensitive_body_version}
        :param timeouts: timeouts block. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#timeouts UpdateResource#timeouts}
        :param update_headers: A mapping of headers to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update_headers UpdateResource#update_headers}
        :param update_query_parameters: A mapping of query parameters to be sent with the update request. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update_query_parameters UpdateResource#update_query_parameters}
        '''
        if isinstance(lifecycle, dict):
            lifecycle = _cdktf_9a9027ec.TerraformResourceLifecycle(**lifecycle)
        if isinstance(retry, dict):
            retry = _UpdateResourceRetry_9d4b8e25(**retry)
        if isinstance(timeouts, dict):
            timeouts = _UpdateResourceTimeouts_49a4241d(**timeouts)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ad3357543fe7228eb0d63c9f81d73d5f9cb0cda4e2c9dd9ef50f1f9076651fa6)
            check_type(argname="argument connection", value=connection, expected_type=type_hints["connection"])
            check_type(argname="argument count", value=count, expected_type=type_hints["count"])
            check_type(argname="argument depends_on", value=depends_on, expected_type=type_hints["depends_on"])
            check_type(argname="argument for_each", value=for_each, expected_type=type_hints["for_each"])
            check_type(argname="argument lifecycle", value=lifecycle, expected_type=type_hints["lifecycle"])
            check_type(argname="argument provider", value=provider, expected_type=type_hints["provider"])
            check_type(argname="argument provisioners", value=provisioners, expected_type=type_hints["provisioners"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
            check_type(argname="argument body", value=body, expected_type=type_hints["body"])
            check_type(argname="argument ignore_casing", value=ignore_casing, expected_type=type_hints["ignore_casing"])
            check_type(argname="argument ignore_missing_property", value=ignore_missing_property, expected_type=type_hints["ignore_missing_property"])
            check_type(argname="argument locks", value=locks, expected_type=type_hints["locks"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument parent_id", value=parent_id, expected_type=type_hints["parent_id"])
            check_type(argname="argument read_headers", value=read_headers, expected_type=type_hints["read_headers"])
            check_type(argname="argument read_query_parameters", value=read_query_parameters, expected_type=type_hints["read_query_parameters"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument response_export_values", value=response_export_values, expected_type=type_hints["response_export_values"])
            check_type(argname="argument retry", value=retry, expected_type=type_hints["retry"])
            check_type(argname="argument sensitive_body", value=sensitive_body, expected_type=type_hints["sensitive_body"])
            check_type(argname="argument sensitive_body_version", value=sensitive_body_version, expected_type=type_hints["sensitive_body_version"])
            check_type(argname="argument timeouts", value=timeouts, expected_type=type_hints["timeouts"])
            check_type(argname="argument update_headers", value=update_headers, expected_type=type_hints["update_headers"])
            check_type(argname="argument update_query_parameters", value=update_query_parameters, expected_type=type_hints["update_query_parameters"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "type": type,
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
        if body is not None:
            self._values["body"] = body
        if ignore_casing is not None:
            self._values["ignore_casing"] = ignore_casing
        if ignore_missing_property is not None:
            self._values["ignore_missing_property"] = ignore_missing_property
        if locks is not None:
            self._values["locks"] = locks
        if name is not None:
            self._values["name"] = name
        if parent_id is not None:
            self._values["parent_id"] = parent_id
        if read_headers is not None:
            self._values["read_headers"] = read_headers
        if read_query_parameters is not None:
            self._values["read_query_parameters"] = read_query_parameters
        if resource_id is not None:
            self._values["resource_id"] = resource_id
        if response_export_values is not None:
            self._values["response_export_values"] = response_export_values
        if retry is not None:
            self._values["retry"] = retry
        if sensitive_body is not None:
            self._values["sensitive_body"] = sensitive_body
        if sensitive_body_version is not None:
            self._values["sensitive_body_version"] = sensitive_body_version
        if timeouts is not None:
            self._values["timeouts"] = timeouts
        if update_headers is not None:
            self._values["update_headers"] = update_headers
        if update_query_parameters is not None:
            self._values["update_query_parameters"] = update_query_parameters

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
    def type(self) -> builtins.str:
        '''In a format like ``<resource-type>@<api-version>``.

        ``<resource-type>`` is the Azure resource type, for example, ``Microsoft.Storage/storageAccounts``. ``<api-version>`` is version of the API used to manage this azure resource.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#type UpdateResource#type}
        '''
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def body(self) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''A dynamic attribute that contains the request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#body UpdateResource#body}
        '''
        result = self._values.get("body")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def ignore_casing(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Whether ignore the casing of the property names in the response body. Defaults to ``false``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#ignore_casing UpdateResource#ignore_casing}
        '''
        result = self._values.get("ignore_casing")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def ignore_missing_property(
        self,
    ) -> typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]]:
        '''Whether ignore not returned properties like credentials in ``body`` to suppress plan-diff.

        Defaults to ``true``. It's recommend to enable this option when some sensitive properties are not returned in response body, instead of setting them in ``lifecycle.ignore_changes`` because it will make the sensitive fields unable to update.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#ignore_missing_property UpdateResource#ignore_missing_property}
        '''
        result = self._values.get("ignore_missing_property")
        return typing.cast(typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]], result)

    @builtins.property
    def locks(self) -> typing.Optional[typing.List[builtins.str]]:
        '''A list of ARM resource IDs which are used to avoid create/modify/delete azapi resources at the same time.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#locks UpdateResource#locks}
        '''
        result = self._values.get("locks")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def name(self) -> typing.Optional[builtins.str]:
        '''Specifies the name of the Azure resource. Changing this forces a new resource to be created.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#name UpdateResource#name}
        '''
        result = self._values.get("name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def parent_id(self) -> typing.Optional[builtins.str]:
        '''The ID of the azure resource in which this resource is created.

        It supports different kinds of deployment scope for **top level** resources:

        - resource group scope: ``parent_id`` should be the ID of a resource group, it's recommended to manage a resource group by azurerm_resource_group.

          - management group scope: ``parent_id`` should be the ID of a management group, it's recommended to manage a management group by azurerm_management_group.
          - extension scope: ``parent_id`` should be the ID of the resource you're adding the extension to.
          - subscription scope: ``parent_id`` should be like \\x60/subscriptions/00000000-0000-0000-0000-000000000000\\x60
          - tenant scope: ``parent_id`` should be /

        For child level resources, the ``parent_id`` should be the ID of its parent resource, for example, subnet resource's ``parent_id`` is the ID of the vnet.

        For type ``Microsoft.Resources/resourceGroups``, the ``parent_id`` could be omitted, it defaults to subscription ID specified in provider or the default subscription (You could check the default subscription by azure cli command: ``az account show``).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#parent_id UpdateResource#parent_id}
        '''
        result = self._values.get("parent_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read_headers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of headers to be sent with the read request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read_headers UpdateResource#read_headers}
        '''
        result = self._values.get("read_headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def read_query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A mapping of query parameters to be sent with the read request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read_query_parameters UpdateResource#read_query_parameters}
        '''
        result = self._values.get("read_query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    @builtins.property
    def resource_id(self) -> typing.Optional[builtins.str]:
        '''The ID of an existing Azure source.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#resource_id UpdateResource#resource_id}
        '''
        result = self._values.get("resource_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def response_export_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''The attribute can accept either a list or a map.

        - **List**: A list of paths that need to be exported from the response body. Setting it to ``["*"]`` will export the full response body. Here's an example. If it sets to ``["properties.loginServer", "properties.policies.quarantinePolicy.status"]``, it will set the following HCL object to the computed property output::

             {
             	properties = {
             		loginServer = "registry1.azurecr.io"
             		policies = {
             			quarantinePolicy = {
             				status = "disabled"
             			}
             		}
             	}
             }
        - **Map**: A map where the key is the name for the result and the value is a JMESPath query string to filter the response. Here's an example. If it sets to ``{"login_server": "properties.loginServer", "quarantine_status": "properties.policies.quarantinePolicy.status"}``, it will set the following HCL object to the computed property output::

             {
             	"login_server" = "registry1.azurecr.io"
             	"quarantine_status" = "disabled"
             }

        To learn more about JMESPath, visit `JMESPath <https://jmespath.org/>`_.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#response_export_values UpdateResource#response_export_values}
        '''
        result = self._values.get("response_export_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def retry(self) -> typing.Optional[_UpdateResourceRetry_9d4b8e25]:
        '''The retry object supports the following attributes:.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#retry UpdateResource#retry}
        '''
        result = self._values.get("retry")
        return typing.cast(typing.Optional[_UpdateResourceRetry_9d4b8e25], result)

    @builtins.property
    def sensitive_body(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''A dynamic attribute that contains the write-only properties of the request body.

        This will be merge-patched to the body to construct the actual request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#sensitive_body UpdateResource#sensitive_body}
        '''
        result = self._values.get("sensitive_body")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def sensitive_body_version(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A map where the key is the path to the property in ``sensitive_body`` and the value is the version of the property.

        The key is a string in the format of ``path.to.property[index].subproperty``, where ``index`` is the index of the item in an array. When the version is changed, the property will be included in the request body, otherwise it will be omitted from the request body.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#sensitive_body_version UpdateResource#sensitive_body_version}
        '''
        result = self._values.get("sensitive_body_version")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def timeouts(self) -> typing.Optional[_UpdateResourceTimeouts_49a4241d]:
        '''timeouts block.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#timeouts UpdateResource#timeouts}
        '''
        result = self._values.get("timeouts")
        return typing.cast(typing.Optional[_UpdateResourceTimeouts_49a4241d], result)

    @builtins.property
    def update_headers(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''A mapping of headers to be sent with the update request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update_headers UpdateResource#update_headers}
        '''
        result = self._values.get("update_headers")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def update_query_parameters(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]]:
        '''A mapping of query parameters to be sent with the update request.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update_query_parameters UpdateResource#update_query_parameters}
        '''
        result = self._values.get("update_query_parameters")
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UpdateResourceConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.UpdateResourceRetry",
    jsii_struct_bases=[],
    name_mapping={
        "error_message_regex": "errorMessageRegex",
        "interval_seconds": "intervalSeconds",
        "max_interval_seconds": "maxIntervalSeconds",
        "multiplier": "multiplier",
        "randomization_factor": "randomizationFactor",
    },
)
class UpdateResourceRetry:
    def __init__(
        self,
        *,
        error_message_regex: typing.Sequence[builtins.str],
        interval_seconds: typing.Optional[jsii.Number] = None,
        max_interval_seconds: typing.Optional[jsii.Number] = None,
        multiplier: typing.Optional[jsii.Number] = None,
        randomization_factor: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''
        :param error_message_regex: A list of regular expressions to match against error messages. If any of the regular expressions match, the request will be retried. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#error_message_regex UpdateResource#error_message_regex}
        :param interval_seconds: The base number of seconds to wait between retries. Default is ``10``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#interval_seconds UpdateResource#interval_seconds}
        :param max_interval_seconds: The maximum number of seconds to wait between retries. Default is ``180``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#max_interval_seconds UpdateResource#max_interval_seconds}
        :param multiplier: The multiplier to apply to the interval between retries. Default is ``1.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#multiplier UpdateResource#multiplier}
        :param randomization_factor: The randomization factor to apply to the interval between retries. The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#randomization_factor UpdateResource#randomization_factor}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0d5b8baae8cd5cb861a1dc62211543930a038a166682d039c1a45479b20491a0)
            check_type(argname="argument error_message_regex", value=error_message_regex, expected_type=type_hints["error_message_regex"])
            check_type(argname="argument interval_seconds", value=interval_seconds, expected_type=type_hints["interval_seconds"])
            check_type(argname="argument max_interval_seconds", value=max_interval_seconds, expected_type=type_hints["max_interval_seconds"])
            check_type(argname="argument multiplier", value=multiplier, expected_type=type_hints["multiplier"])
            check_type(argname="argument randomization_factor", value=randomization_factor, expected_type=type_hints["randomization_factor"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "error_message_regex": error_message_regex,
        }
        if interval_seconds is not None:
            self._values["interval_seconds"] = interval_seconds
        if max_interval_seconds is not None:
            self._values["max_interval_seconds"] = max_interval_seconds
        if multiplier is not None:
            self._values["multiplier"] = multiplier
        if randomization_factor is not None:
            self._values["randomization_factor"] = randomization_factor

    @builtins.property
    def error_message_regex(self) -> typing.List[builtins.str]:
        '''A list of regular expressions to match against error messages.

        If any of the regular expressions match, the request will be retried.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#error_message_regex UpdateResource#error_message_regex}
        '''
        result = self._values.get("error_message_regex")
        assert result is not None, "Required property 'error_message_regex' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The base number of seconds to wait between retries. Default is ``10``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#interval_seconds UpdateResource#interval_seconds}
        '''
        result = self._values.get("interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def max_interval_seconds(self) -> typing.Optional[jsii.Number]:
        '''The maximum number of seconds to wait between retries. Default is ``180``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#max_interval_seconds UpdateResource#max_interval_seconds}
        '''
        result = self._values.get("max_interval_seconds")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def multiplier(self) -> typing.Optional[jsii.Number]:
        '''The multiplier to apply to the interval between retries. Default is ``1.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#multiplier UpdateResource#multiplier}
        '''
        result = self._values.get("multiplier")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def randomization_factor(self) -> typing.Optional[jsii.Number]:
        '''The randomization factor to apply to the interval between retries.

        The formula for the randomized interval is: ``RetryInterval * (random value in range [1 - RandomizationFactor, 1 + RandomizationFactor])``. Therefore set to zero ``0.0`` for no randomization. Default is ``0.5``.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#randomization_factor UpdateResource#randomization_factor}
        '''
        result = self._values.get("randomization_factor")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UpdateResourceRetry(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class UpdateResourceRetryOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.UpdateResourceRetryOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__ebda5c7056c926d3b255cca43c22019fb02f6aac93bff7009f8ea6c3cc1c2ab6)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetIntervalSeconds")
    def reset_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetIntervalSeconds", []))

    @jsii.member(jsii_name="resetMaxIntervalSeconds")
    def reset_max_interval_seconds(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMaxIntervalSeconds", []))

    @jsii.member(jsii_name="resetMultiplier")
    def reset_multiplier(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetMultiplier", []))

    @jsii.member(jsii_name="resetRandomizationFactor")
    def reset_randomization_factor(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRandomizationFactor", []))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegexInput")
    def error_message_regex_input(self) -> typing.Optional[typing.List[builtins.str]]:
        return typing.cast(typing.Optional[typing.List[builtins.str]], jsii.get(self, "errorMessageRegexInput"))

    @builtins.property
    @jsii.member(jsii_name="intervalSecondsInput")
    def interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "intervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSecondsInput")
    def max_interval_seconds_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "maxIntervalSecondsInput"))

    @builtins.property
    @jsii.member(jsii_name="multiplierInput")
    def multiplier_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "multiplierInput"))

    @builtins.property
    @jsii.member(jsii_name="randomizationFactorInput")
    def randomization_factor_input(self) -> typing.Optional[jsii.Number]:
        return typing.cast(typing.Optional[jsii.Number], jsii.get(self, "randomizationFactorInput"))

    @builtins.property
    @jsii.member(jsii_name="errorMessageRegex")
    def error_message_regex(self) -> typing.List[builtins.str]:
        return typing.cast(typing.List[builtins.str], jsii.get(self, "errorMessageRegex"))

    @error_message_regex.setter
    def error_message_regex(self, value: typing.List[builtins.str]) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__92361988bbce84dd9d1d3bc74f54436199a87be8a9c73bd9e140e29ebe5887a2)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "errorMessageRegex", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="intervalSeconds")
    def interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "intervalSeconds"))

    @interval_seconds.setter
    def interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__631bb17d86bf4be984e60b4650bde9204f34b5ea91c12ce9ec5c00e5f8295561)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "intervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="maxIntervalSeconds")
    def max_interval_seconds(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "maxIntervalSeconds"))

    @max_interval_seconds.setter
    def max_interval_seconds(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__d310bb6dad7d7a235f02a5b442dcfc7b1d544581fb975140759ea469d79f51f8)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "maxIntervalSeconds", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="multiplier")
    def multiplier(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "multiplier"))

    @multiplier.setter
    def multiplier(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__40963906464be7b6ce6756054abad818f8b34d8a4b3b5f7b21ee442f85d04a80)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "multiplier", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="randomizationFactor")
    def randomization_factor(self) -> jsii.Number:
        return typing.cast(jsii.Number, jsii.get(self, "randomizationFactor"))

    @randomization_factor.setter
    def randomization_factor(self, value: jsii.Number) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3b7c86c5c874519c7e9ea205355d1d179236c1d1133cf978942b82c606662d39)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "randomizationFactor", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceRetry_9d4b8e25]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceRetry_9d4b8e25]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceRetry_9d4b8e25]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__de11ead1a94222d05289b8f1e9523a9db0efb7528a272f0a1e631f4f3bac71d4)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.UpdateResourceTimeouts",
    jsii_struct_bases=[],
    name_mapping={
        "create": "create",
        "delete": "delete",
        "read": "read",
        "update": "update",
    },
)
class UpdateResourceTimeouts:
    def __init__(
        self,
        *,
        create: typing.Optional[builtins.str] = None,
        delete: typing.Optional[builtins.str] = None,
        read: typing.Optional[builtins.str] = None,
        update: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param create: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#create UpdateResource#create}
        :param delete: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#delete UpdateResource#delete}
        :param read: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled. Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read UpdateResource#read}
        :param update: A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update UpdateResource#update}
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bcdbf03a33d37dc19009197844c57b4fda75d0cfe4af718df5626d451b799944)
            check_type(argname="argument create", value=create, expected_type=type_hints["create"])
            check_type(argname="argument delete", value=delete, expected_type=type_hints["delete"])
            check_type(argname="argument read", value=read, expected_type=type_hints["read"])
            check_type(argname="argument update", value=update, expected_type=type_hints["update"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if create is not None:
            self._values["create"] = create
        if delete is not None:
            self._values["delete"] = delete
        if read is not None:
            self._values["read"] = read
        if update is not None:
            self._values["update"] = update

    @builtins.property
    def create(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#create UpdateResource#create}
        '''
        result = self._values.get("create")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def delete(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Setting a timeout for a Delete operation is only applicable if changes are saved into state before the destroy operation occurs.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#delete UpdateResource#delete}
        '''
        result = self._values.get("delete")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def read(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours). Read operations occur during any refresh or planning operation when refresh is enabled.

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#read UpdateResource#read}
        '''
        result = self._values.get("read")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def update(self) -> typing.Optional[builtins.str]:
        '''A string that can be `parsed as a duration <https://pkg.go.dev/time#ParseDuration>`_ consisting of numbers and unit suffixes, such as "30s" or "2h45m". Valid time units are "s" (seconds), "m" (minutes), "h" (hours).

        Docs at Terraform Registry: {@link https://registry.terraform.io/providers/azure/azapi/2.7.0/docs/resources/update_resource#update UpdateResource#update}
        '''
        result = self._values.get("update")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "UpdateResourceTimeouts(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class UpdateResourceTimeoutsOutputReference(
    _cdktf_9a9027ec.ComplexObject,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.UpdateResourceTimeoutsOutputReference",
):
    def __init__(
        self,
        terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
        terraform_attribute: builtins.str,
    ) -> None:
        '''
        :param terraform_resource: The parent resource.
        :param terraform_attribute: The attribute on the parent resource this class is referencing.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__67c15cb83acd7ff5eaef04c835b9bc31459304d2cc1a77dae0fd9503c02c0d57)
            check_type(argname="argument terraform_resource", value=terraform_resource, expected_type=type_hints["terraform_resource"])
            check_type(argname="argument terraform_attribute", value=terraform_attribute, expected_type=type_hints["terraform_attribute"])
        jsii.create(self.__class__, self, [terraform_resource, terraform_attribute])

    @jsii.member(jsii_name="resetCreate")
    def reset_create(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetCreate", []))

    @jsii.member(jsii_name="resetDelete")
    def reset_delete(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetDelete", []))

    @jsii.member(jsii_name="resetRead")
    def reset_read(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetRead", []))

    @jsii.member(jsii_name="resetUpdate")
    def reset_update(self) -> None:
        return typing.cast(None, jsii.invoke(self, "resetUpdate", []))

    @builtins.property
    @jsii.member(jsii_name="createInput")
    def create_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "createInput"))

    @builtins.property
    @jsii.member(jsii_name="deleteInput")
    def delete_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "deleteInput"))

    @builtins.property
    @jsii.member(jsii_name="readInput")
    def read_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "readInput"))

    @builtins.property
    @jsii.member(jsii_name="updateInput")
    def update_input(self) -> typing.Optional[builtins.str]:
        return typing.cast(typing.Optional[builtins.str], jsii.get(self, "updateInput"))

    @builtins.property
    @jsii.member(jsii_name="create")
    def create(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "create"))

    @create.setter
    def create(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__49ac4ad9686ad51df1cafaf60a45a4c3d772a8ee6a1bc1e0e32ef294067f3f09)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "create", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="delete")
    def delete(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "delete"))

    @delete.setter
    def delete(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__c28e72346e89a134672bbd748a71df6efa53af0ddef1779d619d0e6aab17d239)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "delete", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="read")
    def read(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "read"))

    @read.setter
    def read(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__96333ffdeee6bcbf5d971c4129770b919396944cd51d437d3e776e48491ebb9c)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "read", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="update")
    def update(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "update"))

    @update.setter
    def update(self, value: builtins.str) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__010bcdf50a18aecf5d36481988a217dc2a85f12be134263a9bd5e936f92d002b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "update", value) # pyright: ignore[reportArgumentType]

    @builtins.property
    @jsii.member(jsii_name="internalValue")
    def internal_value(
        self,
    ) -> typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceTimeouts_49a4241d]]:
        return typing.cast(typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceTimeouts_49a4241d]], jsii.get(self, "internalValue"))

    @internal_value.setter
    def internal_value(
        self,
        value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceTimeouts_49a4241d]],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__283da7d43df676ee2bbea19830ece2fed14a4fcfea65962ba64eed7bb7671608)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "internalValue", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ValidationResult",
    jsii_struct_bases=[],
    name_mapping={
        "errors": "errors",
        "valid": "valid",
        "warnings": "warnings",
        "property_errors": "propertyErrors",
    },
)
class ValidationResult:
    def __init__(
        self,
        *,
        errors: typing.Sequence[builtins.str],
        valid: builtins.bool,
        warnings: typing.Sequence[builtins.str],
        property_errors: typing.Optional[typing.Mapping[builtins.str, typing.Sequence[builtins.str]]] = None,
    ) -> None:
        '''Validation result interface.

        Results of validating properties against a schema.
        Provides detailed error and warning information for debugging
        and user feedback.

        :param errors: Array of validation error messages Empty if validation passed.
        :param valid: Whether validation passed If false, the errors array will contain details.
        :param warnings: Array of validation warning messages Non-blocking issues that should be addressed.
        :param property_errors: Property-specific error messages Maps property names to arrays of error messages.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a26593924c01e78ae0e6cdc013ea94dd03fd53c4ac0043e15cce684cdfcde86a)
            check_type(argname="argument errors", value=errors, expected_type=type_hints["errors"])
            check_type(argname="argument valid", value=valid, expected_type=type_hints["valid"])
            check_type(argname="argument warnings", value=warnings, expected_type=type_hints["warnings"])
            check_type(argname="argument property_errors", value=property_errors, expected_type=type_hints["property_errors"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "errors": errors,
            "valid": valid,
            "warnings": warnings,
        }
        if property_errors is not None:
            self._values["property_errors"] = property_errors

    @builtins.property
    def errors(self) -> typing.List[builtins.str]:
        '''Array of validation error messages Empty if validation passed.'''
        result = self._values.get("errors")
        assert result is not None, "Required property 'errors' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def valid(self) -> builtins.bool:
        '''Whether validation passed If false, the errors array will contain details.'''
        result = self._values.get("valid")
        assert result is not None, "Required property 'valid' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def warnings(self) -> typing.List[builtins.str]:
        '''Array of validation warning messages Non-blocking issues that should be addressed.'''
        result = self._values.get("warnings")
        assert result is not None, "Required property 'warnings' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def property_errors(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.List[builtins.str]]]:
        '''Property-specific error messages Maps property names to arrays of error messages.'''
        result = self._values.get("property_errors")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.List[builtins.str]]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ValidationResult(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ValidationRule",
    jsii_struct_bases=[],
    name_mapping={"rule_type": "ruleType", "message": "message", "value": "value"},
)
class ValidationRule:
    def __init__(
        self,
        *,
        rule_type: builtins.str,
        message: typing.Optional[builtins.str] = None,
        value: typing.Any = None,
    ) -> None:
        '''Validation rule definition for property validation.

        Defines a single validation rule that can be applied to a property
        to ensure data integrity and provide user feedback.

        :param rule_type: The type of validation rule to apply Must be one of the ValidationRuleType constants.
        :param message: Custom error message to display when validation fails If not provided, a default message will be generated.
        :param value: The value or parameter for the validation rule Type depends on the validation rule type.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3b2834414beb5ad67c4dcba2220e905cc2438660d2407682ac8276a246b23ab4)
            check_type(argname="argument rule_type", value=rule_type, expected_type=type_hints["rule_type"])
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "rule_type": rule_type,
        }
        if message is not None:
            self._values["message"] = message
        if value is not None:
            self._values["value"] = value

    @builtins.property
    def rule_type(self) -> builtins.str:
        '''The type of validation rule to apply Must be one of the ValidationRuleType constants.'''
        result = self._values.get("rule_type")
        assert result is not None, "Required property 'rule_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def message(self) -> typing.Optional[builtins.str]:
        '''Custom error message to display when validation fails If not provided, a default message will be generated.'''
        result = self._values.get("message")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def value(self) -> typing.Any:
        '''The value or parameter for the validation rule Type depends on the validation rule type.

        Example::

            For VALUE_RANGE: { min: 0, max: 100 }
        '''
        result = self._values.get("value")
        return typing.cast(typing.Any, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ValidationRule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ValidationRuleType(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.ValidationRuleType",
):
    '''Validation rule types for property validation.

    Defines the types of validation rules that can be applied to properties
    for input validation and data integrity.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="CUSTOM_VALIDATION")
    def CUSTOM_VALIDATION(cls) -> builtins.str:
        '''Custom validation function.'''
        return typing.cast(builtins.str, jsii.sget(cls, "CUSTOM_VALIDATION"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PATTERN_MATCH")
    def PATTERN_MATCH(cls) -> builtins.str:
        '''Validate property value matches regex pattern.'''
        return typing.cast(builtins.str, jsii.sget(cls, "PATTERN_MATCH"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="REQUIRED")
    def REQUIRED(cls) -> builtins.str:
        '''Property is required and cannot be undefined.'''
        return typing.cast(builtins.str, jsii.sget(cls, "REQUIRED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="TYPE_CHECK")
    def TYPE_CHECK(cls) -> builtins.str:
        '''Validate property type matches expected type.'''
        return typing.cast(builtins.str, jsii.sget(cls, "TYPE_CHECK"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="VALUE_RANGE")
    def VALUE_RANGE(cls) -> builtins.str:
        '''Validate property value is within specified range.'''
        return typing.cast(builtins.str, jsii.sget(cls, "VALUE_RANGE"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.VersionChangeLog",
    jsii_struct_bases=[],
    name_mapping={
        "change_type": "changeType",
        "description": "description",
        "affected_property": "affectedProperty",
        "breaking": "breaking",
    },
)
class VersionChangeLog:
    def __init__(
        self,
        *,
        change_type: builtins.str,
        description: builtins.str,
        affected_property: typing.Optional[builtins.str] = None,
        breaking: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''Version changelog entry.

        Documents changes made in a specific version for transparency
        and to help developers understand version evolution.

        :param change_type: The type of change (added, changed, deprecated, removed, fixed).
        :param description: Brief description of the change.
        :param affected_property: Property or feature affected by the change.
        :param breaking: Whether this change is breaking. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0536d827ebd3845ac3208a5b704ca8af9b3eb6af4e1ff000188c9c9676430ee3)
            check_type(argname="argument change_type", value=change_type, expected_type=type_hints["change_type"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument affected_property", value=affected_property, expected_type=type_hints["affected_property"])
            check_type(argname="argument breaking", value=breaking, expected_type=type_hints["breaking"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "change_type": change_type,
            "description": description,
        }
        if affected_property is not None:
            self._values["affected_property"] = affected_property
        if breaking is not None:
            self._values["breaking"] = breaking

    @builtins.property
    def change_type(self) -> builtins.str:
        '''The type of change (added, changed, deprecated, removed, fixed).'''
        result = self._values.get("change_type")
        assert result is not None, "Required property 'change_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> builtins.str:
        '''Brief description of the change.'''
        result = self._values.get("description")
        assert result is not None, "Required property 'description' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def affected_property(self) -> typing.Optional[builtins.str]:
        '''Property or feature affected by the change.'''
        result = self._values.get("affected_property")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def breaking(self) -> typing.Optional[builtins.bool]:
        '''Whether this change is breaking.

        :default: false
        '''
        result = self._values.get("breaking")
        return typing.cast(typing.Optional[builtins.bool], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VersionChangeLog(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.VersionConfig",
    jsii_struct_bases=[],
    name_mapping={
        "release_date": "releaseDate",
        "schema": "schema",
        "support_level": "supportLevel",
        "version": "version",
        "breaking_changes": "breakingChanges",
        "change_log": "changeLog",
        "deprecation_date": "deprecationDate",
        "migration_guide": "migrationGuide",
        "sunset_date": "sunsetDate",
    },
)
class VersionConfig:
    def __init__(
        self,
        *,
        release_date: builtins.str,
        schema: typing.Union[ApiSchema, typing.Dict[builtins.str, typing.Any]],
        support_level: builtins.str,
        version: builtins.str,
        breaking_changes: typing.Optional[typing.Sequence[typing.Union[BreakingChange, typing.Dict[builtins.str, typing.Any]]]] = None,
        change_log: typing.Optional[typing.Sequence[typing.Union[VersionChangeLog, typing.Dict[builtins.str, typing.Any]]]] = None,
        deprecation_date: typing.Optional[builtins.str] = None,
        migration_guide: typing.Optional[builtins.str] = None,
        sunset_date: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Version configuration interface.

        Complete configuration for an API version including schema, lifecycle
        information, and migration metadata. This is the primary interface
        for version management and automated tooling.

        :param release_date: Date when this version was released Used for lifecycle management and compatibility analysis.
        :param schema: The complete API schema for this version Defines all properties, validation, and transformation rules.
        :param support_level: Current support level for this version Must be one of the VersionSupportLevel constants.
        :param version: The API version string.
        :param breaking_changes: Array of breaking changes introduced in this version Used for migration analysis and automated tooling.
        :param change_log: Array of changes made in this version Provides transparency and helps with troubleshooting.
        :param deprecation_date: Date when this version was deprecated (if applicable) Indicates when migration planning should begin.
        :param migration_guide: URL or path to detailed migration guide Provides comprehensive migration instructions.
        :param sunset_date: Date when this version will be sunset (if known) Indicates deadline for migration completion.
        '''
        if isinstance(schema, dict):
            schema = ApiSchema(**schema)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__30ea000de9bab60a00211f861755279fa8ac81d6d5707396b7818357811593b7)
            check_type(argname="argument release_date", value=release_date, expected_type=type_hints["release_date"])
            check_type(argname="argument schema", value=schema, expected_type=type_hints["schema"])
            check_type(argname="argument support_level", value=support_level, expected_type=type_hints["support_level"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
            check_type(argname="argument breaking_changes", value=breaking_changes, expected_type=type_hints["breaking_changes"])
            check_type(argname="argument change_log", value=change_log, expected_type=type_hints["change_log"])
            check_type(argname="argument deprecation_date", value=deprecation_date, expected_type=type_hints["deprecation_date"])
            check_type(argname="argument migration_guide", value=migration_guide, expected_type=type_hints["migration_guide"])
            check_type(argname="argument sunset_date", value=sunset_date, expected_type=type_hints["sunset_date"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "release_date": release_date,
            "schema": schema,
            "support_level": support_level,
            "version": version,
        }
        if breaking_changes is not None:
            self._values["breaking_changes"] = breaking_changes
        if change_log is not None:
            self._values["change_log"] = change_log
        if deprecation_date is not None:
            self._values["deprecation_date"] = deprecation_date
        if migration_guide is not None:
            self._values["migration_guide"] = migration_guide
        if sunset_date is not None:
            self._values["sunset_date"] = sunset_date

    @builtins.property
    def release_date(self) -> builtins.str:
        '''Date when this version was released Used for lifecycle management and compatibility analysis.

        Example::

            "2024-11-01"
        '''
        result = self._values.get("release_date")
        assert result is not None, "Required property 'release_date' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def schema(self) -> ApiSchema:
        '''The complete API schema for this version Defines all properties, validation, and transformation rules.'''
        result = self._values.get("schema")
        assert result is not None, "Required property 'schema' is missing"
        return typing.cast(ApiSchema, result)

    @builtins.property
    def support_level(self) -> builtins.str:
        '''Current support level for this version Must be one of the VersionSupportLevel constants.'''
        result = self._values.get("support_level")
        assert result is not None, "Required property 'support_level' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def version(self) -> builtins.str:
        '''The API version string.

        Example::

            "2024-11-01"
        '''
        result = self._values.get("version")
        assert result is not None, "Required property 'version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def breaking_changes(self) -> typing.Optional[typing.List[BreakingChange]]:
        '''Array of breaking changes introduced in this version Used for migration analysis and automated tooling.'''
        result = self._values.get("breaking_changes")
        return typing.cast(typing.Optional[typing.List[BreakingChange]], result)

    @builtins.property
    def change_log(self) -> typing.Optional[typing.List[VersionChangeLog]]:
        '''Array of changes made in this version Provides transparency and helps with troubleshooting.'''
        result = self._values.get("change_log")
        return typing.cast(typing.Optional[typing.List[VersionChangeLog]], result)

    @builtins.property
    def deprecation_date(self) -> typing.Optional[builtins.str]:
        '''Date when this version was deprecated (if applicable) Indicates when migration planning should begin.

        Example::

            "2025-11-01"
        '''
        result = self._values.get("deprecation_date")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def migration_guide(self) -> typing.Optional[builtins.str]:
        '''URL or path to detailed migration guide Provides comprehensive migration instructions.

        Example::

            "/docs/migration-guides/v2024-11-01"
        '''
        result = self._values.get("migration_guide")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def sunset_date(self) -> typing.Optional[builtins.str]:
        '''Date when this version will be sunset (if known) Indicates deadline for migration completion.

        Example::

            "2026-11-01"
        '''
        result = self._values.get("sunset_date")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VersionConfig(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.VersionConstraints",
    jsii_struct_bases=[],
    name_mapping={
        "exclude_deprecated": "excludeDeprecated",
        "not_older_than": "notOlderThan",
        "required_features": "requiredFeatures",
        "support_level": "supportLevel",
    },
)
class VersionConstraints:
    def __init__(
        self,
        *,
        exclude_deprecated: typing.Optional[builtins.bool] = None,
        not_older_than: typing.Optional[datetime.datetime] = None,
        required_features: typing.Optional[typing.Sequence[builtins.str]] = None,
        support_level: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Version selection constraints.

        Defines constraints for automatic version selection to help
        choose the most appropriate version based on requirements.

        :param exclude_deprecated: Whether to exclude deprecated versions. Default: true
        :param not_older_than: Minimum release date for version selection Versions older than this date will be excluded.
        :param required_features: Array of required features that the version must support.
        :param support_level: Required support level Must be one of the VersionSupportLevel constants.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a01f7ff7cafc62faf653ded740578c692fb5c65435d8192cda2a2086d8f53bff)
            check_type(argname="argument exclude_deprecated", value=exclude_deprecated, expected_type=type_hints["exclude_deprecated"])
            check_type(argname="argument not_older_than", value=not_older_than, expected_type=type_hints["not_older_than"])
            check_type(argname="argument required_features", value=required_features, expected_type=type_hints["required_features"])
            check_type(argname="argument support_level", value=support_level, expected_type=type_hints["support_level"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if exclude_deprecated is not None:
            self._values["exclude_deprecated"] = exclude_deprecated
        if not_older_than is not None:
            self._values["not_older_than"] = not_older_than
        if required_features is not None:
            self._values["required_features"] = required_features
        if support_level is not None:
            self._values["support_level"] = support_level

    @builtins.property
    def exclude_deprecated(self) -> typing.Optional[builtins.bool]:
        '''Whether to exclude deprecated versions.

        :default: true
        '''
        result = self._values.get("exclude_deprecated")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def not_older_than(self) -> typing.Optional[datetime.datetime]:
        '''Minimum release date for version selection Versions older than this date will be excluded.'''
        result = self._values.get("not_older_than")
        return typing.cast(typing.Optional[datetime.datetime], result)

    @builtins.property
    def required_features(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Array of required features that the version must support.'''
        result = self._values.get("required_features")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def support_level(self) -> typing.Optional[builtins.str]:
        '''Required support level Must be one of the VersionSupportLevel constants.'''
        result = self._values.get("support_level")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VersionConstraints(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.VersionLifecycle",
    jsii_struct_bases=[],
    name_mapping={
        "phase": "phase",
        "version": "version",
        "estimated_sunset_date": "estimatedSunsetDate",
        "next_phase": "nextPhase",
        "transition_date": "transitionDate",
    },
)
class VersionLifecycle:
    def __init__(
        self,
        *,
        phase: builtins.str,
        version: builtins.str,
        estimated_sunset_date: typing.Optional[builtins.str] = None,
        next_phase: typing.Optional[builtins.str] = None,
        transition_date: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Version lifecycle management.

        Tracks the current phase and transition timeline for an API version
        to enable proactive lifecycle management.

        :param phase: Current lifecycle phase Must be one of the VersionPhase constants.
        :param version: The API version string.
        :param estimated_sunset_date: Estimated date when version will be sunset Used for long-term planning.
        :param next_phase: Next planned phase in the lifecycle Must be one of the VersionPhase constants.
        :param transition_date: Date when the current phase was entered.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__fd5b3e936cf265cf7f19877c816ea9a636b3ed03018c60e711aaed3378b2a8a4)
            check_type(argname="argument phase", value=phase, expected_type=type_hints["phase"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
            check_type(argname="argument estimated_sunset_date", value=estimated_sunset_date, expected_type=type_hints["estimated_sunset_date"])
            check_type(argname="argument next_phase", value=next_phase, expected_type=type_hints["next_phase"])
            check_type(argname="argument transition_date", value=transition_date, expected_type=type_hints["transition_date"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "phase": phase,
            "version": version,
        }
        if estimated_sunset_date is not None:
            self._values["estimated_sunset_date"] = estimated_sunset_date
        if next_phase is not None:
            self._values["next_phase"] = next_phase
        if transition_date is not None:
            self._values["transition_date"] = transition_date

    @builtins.property
    def phase(self) -> builtins.str:
        '''Current lifecycle phase Must be one of the VersionPhase constants.'''
        result = self._values.get("phase")
        assert result is not None, "Required property 'phase' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def version(self) -> builtins.str:
        '''The API version string.'''
        result = self._values.get("version")
        assert result is not None, "Required property 'version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def estimated_sunset_date(self) -> typing.Optional[builtins.str]:
        '''Estimated date when version will be sunset Used for long-term planning.

        Example::

            "2026-11-01"
        '''
        result = self._values.get("estimated_sunset_date")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def next_phase(self) -> typing.Optional[builtins.str]:
        '''Next planned phase in the lifecycle Must be one of the VersionPhase constants.'''
        result = self._values.get("next_phase")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def transition_date(self) -> typing.Optional[builtins.str]:
        '''Date when the current phase was entered.

        Example::

            "2024-11-01"
        '''
        result = self._values.get("transition_date")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VersionLifecycle(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class VersionPhase(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.VersionPhase",
):
    '''Version lifecycle phases.

    Defines the phases in an API version's lifecycle from initial
    development through sunset.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="ACTIVE")
    def ACTIVE(cls) -> builtins.str:
        '''Active phase - fully supported and recommended.'''
        return typing.cast(builtins.str, jsii.sget(cls, "ACTIVE"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="DEPRECATED")
    def DEPRECATED(cls) -> builtins.str:
        '''Deprecated phase - migration recommended.'''
        return typing.cast(builtins.str, jsii.sget(cls, "DEPRECATED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="MAINTENANCE")
    def MAINTENANCE(cls) -> builtins.str:
        '''Maintenance phase - bug fixes only.'''
        return typing.cast(builtins.str, jsii.sget(cls, "MAINTENANCE"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="PREVIEW")
    def PREVIEW(cls) -> builtins.str:
        '''Preview/beta phase - not recommended for production.'''
        return typing.cast(builtins.str, jsii.sget(cls, "PREVIEW"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="SUNSET")
    def SUNSET(cls) -> builtins.str:
        '''Sunset phase - no longer supported.'''
        return typing.cast(builtins.str, jsii.sget(cls, "SUNSET"))


class VersionSupportLevel(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.core_azure.VersionSupportLevel",
):
    '''Version support level enumeration for API lifecycle management.

    Defines the current support status of an API version to help developers
    understand maintenance commitments and migration planning.
    '''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.python.classproperty
    @jsii.member(jsii_name="ACTIVE")
    def ACTIVE(cls) -> builtins.str:
        '''Active support - full feature development and bug fixes Recommended for new development.'''
        return typing.cast(builtins.str, jsii.sget(cls, "ACTIVE"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="DEPRECATED")
    def DEPRECATED(cls) -> builtins.str:
        '''Deprecated - security fixes only, migration recommended Should not be used for new development.'''
        return typing.cast(builtins.str, jsii.sget(cls, "DEPRECATED"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="MAINTENANCE")
    def MAINTENANCE(cls) -> builtins.str:
        '''Maintenance support - critical bug fixes only, no new features Stable for production use but consider migration planning.'''
        return typing.cast(builtins.str, jsii.sget(cls, "MAINTENANCE"))

    @jsii.python.classproperty
    @jsii.member(jsii_name="SUNSET")
    def SUNSET(cls) -> builtins.str:
        '''Sunset - no longer supported, immediate migration required May be removed in future releases.'''
        return typing.cast(builtins.str, jsii.sget(cls, "SUNSET"))


__all__ = [
    "ApiSchema",
    "ApiVersionManager",
    "AzapiProvider",
    "AzapiProviderConfig",
    "AzapiProviderEndpoint",
    "AzapiResource",
    "AzapiResourceProps",
    "AzapiRoleAssignment",
    "AzapiRoleAssignmentProps",
    "BreakingChange",
    "BreakingChangeType",
    "DataAzapiClientConfig",
    "DataAzapiClientConfigConfig",
    "DataAzapiClientConfigTimeouts",
    "DataAzapiClientConfigTimeoutsOutputReference",
    "DataAzapiResource",
    "DataAzapiResourceConfig",
    "DataAzapiResourceIdentity",
    "DataAzapiResourceIdentityList",
    "DataAzapiResourceIdentityOutputReference",
    "DataAzapiResourceRetry",
    "DataAzapiResourceRetryOutputReference",
    "DataAzapiResourceTimeouts",
    "DataAzapiResourceTimeoutsOutputReference",
    "DiagnosticLogConfig",
    "DiagnosticMetricConfig",
    "MigrationAnalysis",
    "MigrationEffort",
    "MonitoringConfig",
    "PropertyDefinition",
    "PropertyMapping",
    "PropertyTransformationType",
    "PropertyTransformer",
    "PropertyType",
    "PropertyValidation",
    "Resource",
    "ResourceAction",
    "ResourceActionConfig",
    "ResourceActionRetry",
    "ResourceActionRetryOutputReference",
    "ResourceActionTimeouts",
    "ResourceActionTimeoutsOutputReference",
    "ResourceConfig",
    "ResourceIdentity",
    "ResourceIdentityList",
    "ResourceIdentityOutputReference",
    "ResourceRetry",
    "ResourceRetryOutputReference",
    "ResourceTimeouts",
    "ResourceTimeoutsOutputReference",
    "RetentionPolicyConfig",
    "SchemaMapper",
    "UpdateResource",
    "UpdateResourceConfig",
    "UpdateResourceRetry",
    "UpdateResourceRetryOutputReference",
    "UpdateResourceTimeouts",
    "UpdateResourceTimeoutsOutputReference",
    "ValidationResult",
    "ValidationRule",
    "ValidationRuleType",
    "VersionChangeLog",
    "VersionConfig",
    "VersionConstraints",
    "VersionLifecycle",
    "VersionPhase",
    "VersionSupportLevel",
]

publication.publish()

def _typecheckingstub__d8cc5e877912404285c4a1a4fb2ead49797841e8fb27ff8c48c2e63167fd148b(
    *,
    properties: typing.Mapping[builtins.str, typing.Union[PropertyDefinition, typing.Dict[builtins.str, typing.Any]]],
    required: typing.Sequence[builtins.str],
    resource_type: builtins.str,
    version: builtins.str,
    deprecated: typing.Optional[typing.Sequence[builtins.str]] = None,
    optional: typing.Optional[typing.Sequence[builtins.str]] = None,
    transformation_rules: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    validation_rules: typing.Optional[typing.Sequence[typing.Union[PropertyValidation, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__92f24aa1042dca0f0e9b67956e5ac1c99285ed812c2660bcae26a8c8a39ec798(
    resource_type: builtins.str,
    from_version: builtins.str,
    to_version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c6802aa02200e054813137481cf20a27e58984a2c2d1ac27f19d674387594fdc(
    resource_type: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__258468ab165c63cc98f68ab5890771f9f7cb5d5e80e4229d03140708298effe5(
    resource_type: builtins.str,
    versions: typing.Sequence[typing.Union[VersionConfig, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fb77480c2569fc25c0b5e80e521a00b13c0757db68aef2cdd53ee3d0c3968480(
    resource_type: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07391b3a9dfa1e820637464775a351b226c27bd8864b9d17c0cf7b5b14174d9c(
    resource_type: builtins.str,
    version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__68b2969a72a2e232d2e7c70c7ec7b69ff1d3505b07b24c58bd8104b8e787fecd(
    resource_type: builtins.str,
    version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f62aa7dc4291470534670e29625675e40b1210aa8c0e44d850c1110ad6be8ad1(
    resource_type: builtins.str,
    version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5f52ff2d70292dbdfed6d184e238a41b86653521bafe707ddbb8b8f9497b9648(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    alias: typing.Optional[builtins.str] = None,
    auxiliary_tenant_ids: typing.Optional[typing.Sequence[builtins.str]] = None,
    client_certificate: typing.Optional[builtins.str] = None,
    client_certificate_password: typing.Optional[builtins.str] = None,
    client_certificate_path: typing.Optional[builtins.str] = None,
    client_id: typing.Optional[builtins.str] = None,
    client_id_file_path: typing.Optional[builtins.str] = None,
    client_secret: typing.Optional[builtins.str] = None,
    client_secret_file_path: typing.Optional[builtins.str] = None,
    custom_correlation_request_id: typing.Optional[builtins.str] = None,
    default_location: typing.Optional[builtins.str] = None,
    default_name: typing.Optional[builtins.str] = None,
    default_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    disable_correlation_request_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    disable_default_output: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    disable_instance_discovery: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    disable_terraform_partner_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    enable_preflight: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    endpoint: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_AzapiProviderEndpoint_ac1351fa, typing.Dict[builtins.str, typing.Any]]]]] = None,
    environment: typing.Optional[builtins.str] = None,
    ignore_no_op_changes: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    maximum_busy_retry_attempts: typing.Optional[jsii.Number] = None,
    oidc_azure_service_connection_id: typing.Optional[builtins.str] = None,
    oidc_request_token: typing.Optional[builtins.str] = None,
    oidc_request_url: typing.Optional[builtins.str] = None,
    oidc_token: typing.Optional[builtins.str] = None,
    oidc_token_file_path: typing.Optional[builtins.str] = None,
    partner_id: typing.Optional[builtins.str] = None,
    skip_provider_registration: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    subscription_id: typing.Optional[builtins.str] = None,
    tenant_id: typing.Optional[builtins.str] = None,
    use_aks_workload_identity: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    use_cli: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    use_msi: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    use_oidc: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cb1c97cbd37e743a6f02fd49654ccb7fbd87bb756cf4bb899c52abe40de45ac3(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f1c9f1106e180ed693d2c3f6b55fe72fbe6a1b03def305ce8ebd26a12ff7b7df(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1100caec1f9ce1d5d2cf41740b7d293af0d13c01bcd7014fda2d8c61846ad13d(
    value: typing.Optional[typing.List[builtins.str]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__24ae50953ef429d98c84f0b542e6b051fe1822f0d666041a342e914236e4187d(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5ae54181a82e260516380fd9de4c51a1ee1936d05f68cc92a24125f950b6a82d(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__10caefac7cd044dfc01663c278a29b1e24389797ba96d3ec8afb75392b531465(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5014b63b8dc6e84933d227c2f96b650fc231d7ab32ad9451fb763e5ef3793d34(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9d3f0a61afcf21bbed272f0b86b97f45d4ecd1a3eb2f3cf853ca1def616282dc(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__addcfcaeee63fdcb41a65094c4a261abc261abc25aecd180948483d26d2c1f81(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b74c4d90b7a6059b2c5f5e584a0b441e7ceda6aa39fa3fc321894158d378d5be(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d32a8694785784b9c81bab4659c373caf87fafe8ff0a427461a9d908feb38147(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__27c927d37364c6fea10c49ee1370691b19e7e592b844a72be12b9c2bd53b2214(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__901c18ecd89be7fd89797c6af9765fe336dea1893de27a28f9e62ac55bc31875(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8160704f9f2999ccada99078d914953ab104324b354fbddabfb94e1917e06c67(
    value: typing.Optional[typing.Mapping[builtins.str, builtins.str]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8bcafe1f0985ac771f972dddd9b40e5b109fd915cd651f6dea355c93867bad80(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d67e731b58ff35e098fb0072371fad7c475cd4b25c50abdaa608931589e316a7(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2cf7e835f39db60318f461d809f74a62f9346349f8ea065aee0e2a1df7e1ad14(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cff1d2efc0bb220160cdac950162f4c5222d49e49239351ee750a5f908e14cd1(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__71947faeec1318898617e0ed293d012268c2237fcb652622821551433abd5e75(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__65c72397129b56e6353a15dfc9ff5d22393377a0509b9e18d46d778df9842192(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_AzapiProviderEndpoint_ac1351fa]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__397d6d0d941514e57a0834d4462117535e609d0136129531104513cd1befe72f(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__09dbe68ef34c5fcd3c7a5981cb86689f964c4f1ad79f1169b2cf26df854dd500(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2553ea1e0d1bc71a16054d752d20242041c20104919cee3e0329e32bb606d0ea(
    value: typing.Optional[jsii.Number],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__93263d916ada198f1b62843a3878aaa2459de859c08837ee147a0365ecbcf258(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bc1615135f90617e10d411b299b693e785bfbeed61ea173051a11a706a815bba(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__033db5b8de90649f523b05b37faf1fbecb698506444a0fe82650b44f2ca16753(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__233d6e8b14f46b907d1c3ef3f7d84e5a23b3e1749217ef95d39b1d2a9bb0cbf9(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2729d037c671785954c8f07d4cb9b0a5b6d44911ffd9cad1e5c0f2edfdf07203(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3ddc2a511e1479e3cb8408d9b245d7b8961390179d6a6765331608b414853bbb(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8dc7835fba47cc9e9559bef526326a5d9c45a79e56d5524a5fdb5061517e9ff3(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d98f67f7e27d1e5277d2356f4d8c4c1ea70ff70a2ed565dd0bbbb38fa832a150(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__99ebb90abbcc7995eec074da3fe0f87973120bf3dc9fcdf1e45b08447ff60be5(
    value: typing.Optional[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e5ada225338a6cd5464f0c24e0b5007a13ef86219cf5f9afb81e61c74090a90(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1b1b7d9e8027fd62bf455106d70fae15c8e06bec52154c7c33f1831611aa9869(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b69e7ba1a072bde82ef951fb89489e5849884ccf2feecd8267952040b6634a82(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__96708422318163444a6c09b2eaf40a575ec9819054fdb741ec5f24c64820a318(
    value: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5c2d9ce1864149731ee5f4d20a3601e0f1e161198cb204166cbe6a14c60dee57(
    *,
    alias: typing.Optional[builtins.str] = None,
    auxiliary_tenant_ids: typing.Optional[typing.Sequence[builtins.str]] = None,
    client_certificate: typing.Optional[builtins.str] = None,
    client_certificate_password: typing.Optional[builtins.str] = None,
    client_certificate_path: typing.Optional[builtins.str] = None,
    client_id: typing.Optional[builtins.str] = None,
    client_id_file_path: typing.Optional[builtins.str] = None,
    client_secret: typing.Optional[builtins.str] = None,
    client_secret_file_path: typing.Optional[builtins.str] = None,
    custom_correlation_request_id: typing.Optional[builtins.str] = None,
    default_location: typing.Optional[builtins.str] = None,
    default_name: typing.Optional[builtins.str] = None,
    default_tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    disable_correlation_request_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    disable_default_output: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    disable_instance_discovery: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    disable_terraform_partner_id: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    enable_preflight: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    endpoint: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_AzapiProviderEndpoint_ac1351fa, typing.Dict[builtins.str, typing.Any]]]]] = None,
    environment: typing.Optional[builtins.str] = None,
    ignore_no_op_changes: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    maximum_busy_retry_attempts: typing.Optional[jsii.Number] = None,
    oidc_azure_service_connection_id: typing.Optional[builtins.str] = None,
    oidc_request_token: typing.Optional[builtins.str] = None,
    oidc_request_url: typing.Optional[builtins.str] = None,
    oidc_token: typing.Optional[builtins.str] = None,
    oidc_token_file_path: typing.Optional[builtins.str] = None,
    partner_id: typing.Optional[builtins.str] = None,
    skip_provider_registration: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    subscription_id: typing.Optional[builtins.str] = None,
    tenant_id: typing.Optional[builtins.str] = None,
    use_aks_workload_identity: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    use_cli: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    use_msi: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    use_oidc: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__830572394f7c616e27c3a43fd25c5db052d11cd675b3f460dafa8aa610b638e5(
    *,
    active_directory_authority_host: typing.Optional[builtins.str] = None,
    resource_manager_audience: typing.Optional[builtins.str] = None,
    resource_manager_endpoint: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a4721714cda0833dfab6bea66f4fcdda2ddd209c9d016453c0d10e942d7f8e6f(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    api_version: typing.Optional[builtins.str] = None,
    enable_migration_analysis: typing.Optional[builtins.bool] = None,
    enable_transformation: typing.Optional[builtins.bool] = None,
    enable_validation: typing.Optional[builtins.bool] = None,
    location: typing.Optional[builtins.str] = None,
    monitoring: typing.Optional[typing.Union[MonitoringConfig, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__c9d77099c005d007eb35d3e704837eca906f47188729a0d22306b01d1cc5bcc7(
    resource_type: builtins.str,
    versions: typing.Sequence[typing.Union[VersionConfig, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6e3c6d0bbaaddfb2eb45725897b5741efcaafb15d11569a8c6ca43aec008d6f9(
    object_id: builtins.str,
    role_definition_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d90d32b2c297a1cdd94e973a7a8ed52e0f58c521022cf8be08b469c16c969fa6(
    key: builtins.str,
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eced9286cb219641203ebbff3ce49fce70e326392feac6f14f6120bcd29842c0(
    target_version: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__755d63a36b48dbba857c45666e500c94186ae6d8c99bdb8998197d9dc7173bed(
    resource_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3db285232c50fdf23460379819cb2891917267d1cb22577f50f8db0debd80b0a(
    properties: typing.Mapping[builtins.str, typing.Any],
    parent_id: builtins.str,
    name: builtins.str,
    location: typing.Optional[builtins.str] = None,
    parent_resource: typing.Optional[AzapiResource] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__10ba7daf985da96e3075a4105cbfd96117ade31d5e1545ad6953babac62af9f4(
    config: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8fd7d7af1b1f70a2a68d9355dfe71212e4290f9cd199ab17f1f353c9de0856f4(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__424021683fb308922508cd77d045a339a92d97f4168a27a40c9e95c69904129d(
    properties: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5a6fc267f48e1a4b955fd59f8b54d2bcacc974d59df70195e687d6b138ae0d90(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a7561d40e2812de40aeea89e1ce25d06a4c8a3de58639df6ce11265c2bdfc84c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__330b9f717665caf4df824d5ddf137bb83beb83acb37a2af9e63692b3c26cd8fd(
    value: ApiSchema,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4422d40a75fd6644d732d2f70ac2b2e20869c9df36c45d46f72995c4ef6dbb6f(
    value: _cdktf_9a9027ec.TerraformResource,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__13cc2f6914aa6c6c86f3c1e6f152c82d7bad801ca829353201ea24e9af9c7710(
    value: VersionConfig,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a9471ff5145389f28356530f7b05ba78be0ea22b0f92f7503fd7d4a29d9382e(
    value: typing.Optional[MigrationAnalysis],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c897e83c2cd923993c13bfb95b002ff4fb9349b074b7b3f71846f0f205b3957d(
    value: typing.Optional[ValidationResult],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7ee6fd8d016c3a0923c1ab35bbc84ceafc199abaaa7fcc0d3376b5f0cf1d7dfc(
    props: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fc684e976d0c2057d010cbc36995d833ef6ed29ec007f64de818df4dab296f01(
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
    monitoring: typing.Optional[typing.Union[MonitoringConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    name: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6d50cedef30ce6690304c852135c42b5f4e2b56e2a82f908f17e712cd3bd869a(
    scope_: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    object_id: builtins.str,
    role_definition_name: builtins.str,
    scope: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d4609725af1b10d08aee153d59b533985111e99c29c5131e94df4e9c415ae7e1(
    *,
    object_id: builtins.str,
    role_definition_name: builtins.str,
    scope: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5a2b0c56a331e150374ca548fdc3492dbd2ea177890ea38bd8b402d4c3b94492(
    *,
    change_type: builtins.str,
    description: builtins.str,
    migration_path: typing.Optional[builtins.str] = None,
    new_value: typing.Optional[builtins.str] = None,
    old_value: typing.Optional[builtins.str] = None,
    property: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__685e62c05228470248e5e91289bda44dbcc610f0e629b9a9531e49e442654053(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    timeouts: typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__7bb75f11668ae6ffef7d746577510b7396815558615f8657d9d93e4bb5e6b993(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7cd2cba78213211895ed59fdf0db98bed8881cf45941c834125e50ceb435ebf(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    timeouts: typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8798fa5e7398d64d1289116aeda31bf00e2b4d9d6953c3a6c9752938f7518138(
    *,
    read: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__abf2c0976a35ef1e36956ac766e1bc65001340faf9983bfc42a735a03bb3277b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__232df675d4c646245d1891bbafc62faf2c850f202c6b557b7329cd9e4496115b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cd8f46f6199851a0d1c095c23ffb8b097a2deb398cef11bd2bb6f2bde342a932(
    value: typing.Optional[typing.Union[_DataAzapiClientConfigTimeouts_60de1877, _cdktf_9a9027ec.IResolvable]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2e3f70bb9f1b1d5147ee09de64606e7a6f4a46910c044fb82010b8665ae97859(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    type: builtins.str,
    headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ignore_not_found: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    name: typing.Optional[builtins.str] = None,
    parent_id: typing.Optional[builtins.str] = None,
    query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    resource_id: typing.Optional[builtins.str] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_DataAzapiResourceRetry_68065f43, typing.Dict[builtins.str, typing.Any]]] = None,
    timeouts: typing.Optional[typing.Union[_DataAzapiResourceTimeouts_a892ce9b, typing.Dict[builtins.str, typing.Any]]] = None,
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

def _typecheckingstub__0c216ec7e210cad0029d06bc5c1d6da3d41e70bd8ec3f6097f5f4bc879255157(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__17be5a603dc466a085995bc28bb2aca223a8cd7b7939e12beddb6b1de26c6bdb(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e728cda86461e0ca16b758ae81cd12b2f4d93194842e7afd36d4bc2625aebeaf(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56ea85689a24c4fea3386afb17cdaeb44fe16f6d65c44dd7672cf9c875a3c710(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6bd01ffe1870f788a35b632e5dd6f0cebf273810bbb4da3a3fb24f615653e115(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5d3b0b2058bc5038c2556c50a18a985d23295095dfe367e61735a03dfc685ede(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__642c01afd28ba62b44899f49114898fb746f4e856d75c160108556050a6bcb43(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b658fbd88d335a6b2c3860c27d0187f5734f0b880029e56329c1c305c29a6244(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eecf1855c5030dccfeb79952d75af3ac37bc5d9fdd8cb1fb8a775dc6058e5d4c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cebd3cc17128138fcc5742efad986faceadeb4614211734e344e82d3d0bd80ac(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    type: builtins.str,
    headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ignore_not_found: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    name: typing.Optional[builtins.str] = None,
    parent_id: typing.Optional[builtins.str] = None,
    query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    resource_id: typing.Optional[builtins.str] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_DataAzapiResourceRetry_68065f43, typing.Dict[builtins.str, typing.Any]]] = None,
    timeouts: typing.Optional[typing.Union[_DataAzapiResourceTimeouts_a892ce9b, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7d0a2f08cf90a765e2a5c75bf2f54ca217874c74cc101b60ad8285df1ddbdff4(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__28578cf004319abb07e45539466f40c279781f0e54518de61a48076b174368b8(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__45492207e839be0fae7571f208e779349cbd6ea0976bb7cc949c6f6574eae7bc(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1f3858e0d37244f1de2467ff7f07c0f1ffade94c77a09bb46c883ec172b09de6(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__85d854de81ba1757d28c8e697da93820a9cc92742188471be3af14c143eee40d(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c1da9edf25149972d00ecc2ce5f42abe3d0c46b35bc649447fa4a2109201efb5(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b3f668acb5d19587676ac74033acc0e20c50f69c191fd4789a33802f90a5a5b8(
    value: typing.Optional[_DataAzapiResourceIdentity_3125d9eb],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2fde1e2438eb2111b35e61c12026b80a4b5be36fa5dd7f3fdb0691a16d53972c(
    *,
    error_message_regex: typing.Sequence[builtins.str],
    interval_seconds: typing.Optional[jsii.Number] = None,
    max_interval_seconds: typing.Optional[jsii.Number] = None,
    multiplier: typing.Optional[jsii.Number] = None,
    randomization_factor: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70fc36706131a7daeac907364a44502378fd31daf03eae3053240f6bf90bc09d(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be4408de96d73ca59a9c824846d7a5564db35f1c3f41e36288944ba903f9eb8b(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ca5eeb7aaa8737563a94864b225330de2345c4523f18132789423476b3453cf3(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4285c70b1258d9f488fd11b5534d8bc4e0bce324032e4d4e64055e3101a5b111(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e924b8a796b6e299135cd54946af45f93f21124efc37dd3354a5f344854dda5a(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d2845a7d4fb3731d1d4b865f80d2c96fb9b9f5efb344a7b33b61c27adb8d36da(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e51039bf7274cab585ae7ca2f7c21be512ace15163277c5bf184e7d9c08b396e(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceRetry_68065f43]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a6a2487e6ee6f20c3257b4dcdf4d8388c201531a92aeb3d7864119a42d4cf4b5(
    *,
    read: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__48286f4d645543f79c8c2c640e17c7eb3918f092a73a9024b17ba0ce71b97a2b(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b3611e62549a64bcf4d2aaef70455c90ca1b0a7c5b481c5813ad4ac6bd1f0ab9(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1641e8e314ca7674f3f177a5bde4c2f55b319ab869fa390e4d84d43d02b07f4b(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _DataAzapiResourceTimeouts_a892ce9b]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6dcda887e53237d494c848709ef111cb4b898a5a32b4f78be95d1807ccb339c1(
    *,
    enabled: builtins.bool,
    category: typing.Optional[builtins.str] = None,
    category_group: typing.Optional[builtins.str] = None,
    retention_policy: typing.Optional[typing.Union[RetentionPolicyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__be038e31fc9d9bdf95d4a04be710bb132e548324e9eddb130c218b7cd36448d6(
    *,
    enabled: builtins.bool,
    category: typing.Optional[builtins.str] = None,
    retention_policy: typing.Optional[typing.Union[RetentionPolicyConfig, typing.Dict[builtins.str, typing.Any]]] = None,
    time_grain: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a5ca794ab8e8c4c037f3a3758f0414eb9de7ac2b3717ca348dfe5b6f16c913c9(
    *,
    automatic_upgrade_possible: builtins.bool,
    breaking_changes: typing.Sequence[typing.Union[BreakingChange, typing.Dict[builtins.str, typing.Any]]],
    compatible: builtins.bool,
    estimated_effort: builtins.str,
    from_version: builtins.str,
    to_version: builtins.str,
    warnings: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5679643d28f130dcb384544fdb30a5b1373794e977ad6e1cf34d138fd5b26ff2(
    *,
    action_groups: typing.Optional[typing.Sequence[typing.Union[_ActionGroupProps_572d2b68, typing.Dict[builtins.str, typing.Any]]]] = None,
    activity_log_alerts: typing.Optional[typing.Sequence[typing.Union[_ActivityLogAlertProps_f1779054, typing.Dict[builtins.str, typing.Any]]]] = None,
    diagnostic_settings: typing.Optional[typing.Union[_DiagnosticSettingsProps_cc0fa615, typing.Dict[builtins.str, typing.Any]]] = None,
    enabled: typing.Optional[builtins.bool] = None,
    metric_alerts: typing.Optional[typing.Sequence[typing.Union[_MetricAlertProps_a18d777f, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3add32040853efb922ea28aa1f44ae789c41571741cdbdfa1a866ebc7d824f93(
    *,
    data_type: builtins.str,
    added_in_version: typing.Optional[builtins.str] = None,
    default_value: typing.Any = None,
    deprecated: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    removed_in_version: typing.Optional[builtins.str] = None,
    required: typing.Optional[builtins.bool] = None,
    validation: typing.Optional[typing.Sequence[typing.Union[ValidationRule, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__53d90887b98a1b5b0eaef72badcb9950bc7cca36bf4a14f7c1df5b787f4376b8(
    *,
    source_property: builtins.str,
    target_property: builtins.str,
    default_value: typing.Any = None,
    required: typing.Optional[builtins.bool] = None,
    transformer: typing.Optional[typing.Union[PropertyTransformer, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__29703eea24077745913d21668a111630be5e56e0452d286b44e563e0842b5883(
    *,
    transformation_type: builtins.str,
    config: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7207a6b3ce8a39e6fbdcbacd7c93f221b35b52f943d66e4609f3a815c3bfe97c(
    *,
    property: builtins.str,
    rules: typing.Sequence[typing.Union[ValidationRule, typing.Dict[builtins.str, typing.Any]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c189527db639961ba7cc72fae190953180434f2ab82164f9d0a14ac4dd47c619(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    type: builtins.str,
    body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    create_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    create_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    delete_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    delete_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    identity: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_ResourceIdentity_d0fe12c0, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ignore_null_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    location: typing.Optional[builtins.str] = None,
    locks: typing.Optional[typing.Sequence[builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    parent_id: typing.Optional[builtins.str] = None,
    read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    replace_triggers_external_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    replace_triggers_refs: typing.Optional[typing.Sequence[builtins.str]] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_ResourceRetry_50237e4f, typing.Dict[builtins.str, typing.Any]]] = None,
    schema_validation_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[_ResourceTimeouts_0b401feb, typing.Dict[builtins.str, typing.Any]]] = None,
    update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
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

def _typecheckingstub__dc987a34e45df8c36de43f210b64d4a1303b00ffa8a33b78a04a135951671f7d(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7b081b2b98e2bc215dbc8dd2df8a969512a7473fa2a0578c7d47cc25e111f720(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_ResourceIdentity_d0fe12c0, typing.Dict[builtins.str, typing.Any]]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3bf2d0b4f4091dc508788dffb68420f8a40989a0cc807c6aa95d12e8e3acc419(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__503670241d5362945f51defaaed4838625e41f6104400e62d1d539a1e718810b(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__337daf2cd77ce8984162b4fc3744a8045ca63d6c86d5ee0a2c034844a2b4057f(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5151ef48c6821aad1a627120bdcf8fe236efc7dbcf28d1612ced082280d5a923(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26b92a8fc3db0482dd26328c25725ea8d36b8091c2f61ae9c92992b8a00f6cc5(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6a4dc82422fde02c28f431f8e7195b2127bca03b7df47af52aee2ff12094006e(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b1782dbf7b02ed52961a4205503aca187b7106b3a0bfd3cafae71e2f88a092c7(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e8c25d48a5b70eb1e518b0635971afebd6c11842770d31864e05a8be476279b3(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__73f14c846d034e14a520c66cdb57b4c55f0d3715d3e92b8569f62f7937340117(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__aedf7f459f1356c3e5ff931bace09a9cfddf8e50c7f7d90e20759cf291ecc974(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ee347af926f652f52cb877e9330b07606675f9169969519103a9fc2619d9b7a3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__774b6b1f0022e2d05d3da015a0bd0f0bd6c9bd8201acb30dba6e76cb283eebef(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__56331a8abb7293b345d6de794002d608b9af38d109b4b3b30416849325989f20(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0edd044ca4c1100f5081c96be9e4375da437d298023b89429d4742608874cd20(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bca9d36f05ea5051b413431827cab24afb5efdd948157f0dbbe41afbe5051a06(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e75b1cb543a8d893effae76cab0d990fb26fb0bae7406e4951fbd8799db2f0ec(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed79344335f9a7bd4866c2c6f4e00fa759b2bf53dbe72fc1f936f06b9b7fffc7(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ce5960fea582f733a7c35926c657f2af81f47e03dffff6da5ce07a765ac34b04(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__647da92e77401455ca531dcad90f1148a1eed51de6584aa221ae85bafbf9a7a6(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__eed382229ea51745837ae7636ac301d9a8efa2817c2d08865f6b23b2fff2cad6(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__94232a5bc0d4b95dab2199eb4df2ac8ac4243241bf1498a92a018e16d021c524(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__31ce26b84c95c3464ede767cf4fd3c6de430fb6ba87ad1516e0b7625c810bbff(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fc3ef6602372c9803775076264a3e4fb0d3a2a76fd9e798ca883e4c9ddb7ddb7(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__dba8ccd73a1fd12b5f0a34cdf34ac452fb3c1d4a0da795697e734f3848ffcbba(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ed7211cf6cfb3e62134dffb3412feffbc3f7e0fc1e3e24c6bd728da81a420360(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    resource_id: builtins.str,
    type: builtins.str,
    action: typing.Optional[builtins.str] = None,
    body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    locks: typing.Optional[typing.Sequence[builtins.str]] = None,
    method: typing.Optional[builtins.str] = None,
    query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_ResourceActionRetry_9fc7b6fd, typing.Dict[builtins.str, typing.Any]]] = None,
    sensitive_response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    timeouts: typing.Optional[typing.Union[_ResourceActionTimeouts_e30653fd, typing.Dict[builtins.str, typing.Any]]] = None,
    when: typing.Optional[builtins.str] = None,
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

def _typecheckingstub__8ef57bb505f471358a36593a267eb570da997b3ec024c65acaec1682351584dc(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4802a184f17f2b66276dcd1eb7bf805f5f8a1d4981a0a36420566ed5816ce157(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cc11d08f3d72223c6f8c21ad488b3e63a4854a901f8dd3e8e2b9a52b4330becf(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d570e5194a31996c4fc765927b86bded081860957843c6c177603669636be17b(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7d4e9070e6dcc3548dd0ee6db6ba54eb1806f29d382a5f98732c73b98e25605(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7bfcfc749c1be9f37d8f4a9dc82d34f3c65bc8956187f7ab4b8bdbd34d03047f(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c803dc9d35193a715b32bb4a538623fbc4cce33637036ef2b143908f18153f42(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__118661828927020e7455b74337b2969bfe2421dc0f91ff3777820d45df0fc488(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__427e45d3f340a164eaf38b4914bd43cc58ac59226eecf28930970b36d6d245d2(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6ee811c7d7e38a8ee4151f7bcec0e734fdfdec213fd1defe12b974345ab32846(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e0918a878fb046e63784bdd0532b893eee6524b724e4d1abed1c6589b362ec71(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__26b275abdad403e0e7384c8d1daba084994eb30d8fdecae8f5883810fdd6cb8c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3f400e091f05d2eacb197f50aa1c9cb5b66fb8d2cf52487205e9daf3f9f3f5be(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    resource_id: builtins.str,
    type: builtins.str,
    action: typing.Optional[builtins.str] = None,
    body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    locks: typing.Optional[typing.Sequence[builtins.str]] = None,
    method: typing.Optional[builtins.str] = None,
    query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_ResourceActionRetry_9fc7b6fd, typing.Dict[builtins.str, typing.Any]]] = None,
    sensitive_response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    timeouts: typing.Optional[typing.Union[_ResourceActionTimeouts_e30653fd, typing.Dict[builtins.str, typing.Any]]] = None,
    when: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0aa17ff925f2207e7e26fd17277d1c176a2bdbaa68aa0f639997a7fa05ca0768(
    *,
    error_message_regex: typing.Sequence[builtins.str],
    interval_seconds: typing.Optional[jsii.Number] = None,
    max_interval_seconds: typing.Optional[jsii.Number] = None,
    multiplier: typing.Optional[jsii.Number] = None,
    randomization_factor: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__044aba673a12de559b99c371dce11c2511cf30f570d06603c4b5d1e72e44603c(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8716ca1a26a47ba52d8afbbf6339afcaf7f8022a61ff0f21cbc64c2bd9bd3577(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c124095bf9aed741aed2623777da4d3f54b3d49015f94b3d41e66571807fa542(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__974183ffc819fbc428c8be6a73aa387e921f185320582d404dbc3881826f2430(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c07fe5d92db5958faa7557f79121a465920ad01b8a99004fe1befa94bdf471f1(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__968667ca7137bf50f95a410d554ac0888d7f421ce603e25758f09bee7a9fff2b(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3a17979ab57d586c4adc3ea8c1aef8bfed3352dea9d8835e6a63a3363903b866(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionRetry_9fc7b6fd]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__53cc427a1fb084147d0f29e0000dca7fd21f91c99ffa05604718b5ef17d6e266(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    read: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a0c258872b4b82cfa9f4d7d4ae4b70267974e2dce3aa29a76bceb9f514bb7526(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ec5a7d28f49e2c7c3a9e4fecaf186c8e0a4e19863add1c419d5ed060856be5c1(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77b6b0391aa6f1efae940ae23a2dd8aa367627c5469e518e52001ee7d4c68fb6(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7684aabb9384c92d4c6f3e970d1f77e31ce6c05fa59ddff7e0b73e48c24fbddd(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5c967c72f8bf6d03e63852d252f8629d570ebbd61107d571ea8f23be04127c24(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9845d8a028c4221d05a56dbb071314406d17d9ec7a74a93553532d769fde4a5b(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceActionTimeouts_e30653fd]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e7d8345dad5f4d2cf356b3e32814b9a20a248746615e1c4c64b9b235b6b4e65c(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    type: builtins.str,
    body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    create_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    create_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    delete_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    delete_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    identity: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Sequence[typing.Union[_ResourceIdentity_d0fe12c0, typing.Dict[builtins.str, typing.Any]]]]] = None,
    ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ignore_null_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    location: typing.Optional[builtins.str] = None,
    locks: typing.Optional[typing.Sequence[builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    parent_id: typing.Optional[builtins.str] = None,
    read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    replace_triggers_external_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    replace_triggers_refs: typing.Optional[typing.Sequence[builtins.str]] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_ResourceRetry_50237e4f, typing.Dict[builtins.str, typing.Any]]] = None,
    schema_validation_enabled: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[_ResourceTimeouts_0b401feb, typing.Dict[builtins.str, typing.Any]]] = None,
    update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__824ac13fa7c89e099cd79c98acc96fb6f37e51b26bdf1ddf0af4040c739c5c28(
    *,
    type: builtins.str,
    identity_ids: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__46d9e3d2b3f8fdcaf468ac6cdd9f5772b72eedbfd61a3732d77c91ba5cb443e7(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    wraps_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__079c11d725773b0d9bf067c41f4f586822b001a392cf492baf4f8d3f89bffc1a(
    index: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2ab91a8ff96a791f066486fcc51e54fbd07b041a6e63acd4715dd81d1c529808(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b03f453f0d095d6a8130ba47ba55a550a7076f633fe6c39474b13adde51cef69(
    value: _cdktf_9a9027ec.IInterpolatingParent,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__002b631a4672d92fdbde7fd3e4b1ab0754efdf6ca1265454967eb253bf76f6ee(
    value: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7dad453e6a46e27aeab2aaefcf1b85e0a8950613236d933599a9b23e3dfbaa11(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.List[_ResourceIdentity_d0fe12c0]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fecedec25f0125f481722e357b287473ad081d58c716306f8f628a9906a10a51(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
    complex_object_index: jsii.Number,
    complex_object_is_from_set: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7500f71fdcdd20f2b0f7f36552f2bae7bfd912e4cb15891630e18fbbd5ddb90f(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__478e7a7661e631c20769d4f72dff33655c9fb9b6dfd4dbcd1c8b039ea7d43301(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5cae33a9a43572b88227cb083ddc6094faebef35d7e0eb9a0c2a5b2e2315db1a(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceIdentity_d0fe12c0]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__70cdc81762c3f46abd55220e2098614ee848b34d9ef2540f0a7af2a039ddefeb(
    *,
    error_message_regex: typing.Sequence[builtins.str],
    interval_seconds: typing.Optional[jsii.Number] = None,
    max_interval_seconds: typing.Optional[jsii.Number] = None,
    multiplier: typing.Optional[jsii.Number] = None,
    randomization_factor: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1007cf1cd9d498a580e1e2446590f0f7de56e649816269bc96e5f65fce91a934(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6cf0453b8d455ebda239ef2d15e351a9ba3d3ac318095e5551a7c809a6f245af(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f46f28ab1c187e0a1dbde301e2a393e736a2514afe5718fea8f5de7cc6370eb0(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__07a4b466a76af2935685e4214c0496d831bbb9d70c3b3d899ca923f64d381a1b(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cdfc9e42f293b87ab1a4d3cf3558328afb30f1d8efaaababe6d836cd82a5837e(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a8396f9879afba7299f44b4c307dc79c8128e783a32cc49fec91aa2452be1e69(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b8ed4bdead82941d48abf75056f62acb0faf072ed5aaac20e2c11eeb1fd2fc6b(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceRetry_50237e4f]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5fef205e8aa0951cff0b7cb2580a414239092590da5cdddd8cf04db2b84500d4(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    read: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c985873f2f2884beaff3f4e69024cc9fb6909dd15557e9b26abcd8730c9dbb9(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__643f89856bef08221777391c4a6597d6ae2af9553d145f88804330e5ef6bdfce(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fa95d792de620b8b4c313868dd8667755e18255c786ec9ce33d8da96e6faa74e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ccad8ceb2d266f8cba2a2296ed98c85d47d0398103b36e07dd54763080636bf2(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__237178dfa5ea8be8f1f85083b6ba7c8abaefbdada288687a3594df0ca8c44b0e(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e99a1d57e8c572123f9373816985bb1fc5e9374c9ffbe951ea0a9b18420beaa(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _ResourceTimeouts_0b401feb]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__304f4fb562352365278a87145329dffd0dd2ef5135da08e2f7e7801e37e416bd(
    *,
    days: jsii.Number,
    enabled: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__058174c0ed978f08ab76647564b62df40a9bb19b60ced7efb4854a8687d88921(
    properties: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d00f07f703a0c63e06d066282353d59682aea54af60b51f6e778997215ff4e85(
    property_name: builtins.str,
    value: typing.Any,
    *,
    data_type: builtins.str,
    added_in_version: typing.Optional[builtins.str] = None,
    default_value: typing.Any = None,
    deprecated: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    removed_in_version: typing.Optional[builtins.str] = None,
    required: typing.Optional[builtins.bool] = None,
    validation: typing.Optional[typing.Sequence[typing.Union[ValidationRule, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f5ccb65f61577e810ec730c69ec406b6e5d3b5509aa8b0001ebfcf663e63a645(
    source_props: typing.Any,
    *,
    properties: typing.Mapping[builtins.str, typing.Union[PropertyDefinition, typing.Dict[builtins.str, typing.Any]]],
    required: typing.Sequence[builtins.str],
    resource_type: builtins.str,
    version: builtins.str,
    deprecated: typing.Optional[typing.Sequence[builtins.str]] = None,
    optional: typing.Optional[typing.Sequence[builtins.str]] = None,
    transformation_rules: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    validation_rules: typing.Optional[typing.Sequence[typing.Union[PropertyValidation, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1605f668462eb352fe4acef398fb9da9de5d251b23c0c7fd3cb1adcecb7d8578(
    properties: typing.Any,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9eda0e4199e3ed020d907c935ee7d0fa52de04f194e33663f0a89a25b73dbe26(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    type: builtins.str,
    body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    locks: typing.Optional[typing.Sequence[builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    parent_id: typing.Optional[builtins.str] = None,
    read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    resource_id: typing.Optional[builtins.str] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_UpdateResourceRetry_9d4b8e25, typing.Dict[builtins.str, typing.Any]]] = None,
    sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[_UpdateResourceTimeouts_49a4241d, typing.Dict[builtins.str, typing.Any]]] = None,
    update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
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

def _typecheckingstub__285b4b8df6ea1bbe89681bd47c939d689791844433922408806679d00fcfcef3(
    scope: _constructs_77d1e7e8.Construct,
    import_to_id: builtins.str,
    import_from_id: builtins.str,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ef3ab5110927b26ec4e35190ba1fb039205da6afc65e1d149cb24dc3318b739b(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f84b46cf749e40dc0e26a55356dd001b385c07bffb5f7f1aa131043b2803adca(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0af53d0052492bae1435dbf26df821355dcd48596dc1029344d48fa92f52d127(
    value: typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3e87570905a6f6e9fe79320fddfb8e10a1519503f6acca1067ed0ac6f33174b8(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cec6d6dc05cff9dc43a4515baab54a3a05dea3ebf9246e9cd8452273ad80d5ce(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a22c5878d3e6f25d793610dfe1e51d227b756be9da98dcebc40b3277f6ccfb28(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8ad7fdd64374f6f9698b8a2d85b077464d43035b3d9646fcce0ae6ff5fd82905(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__49a215695d780543d72d505a2b468ae7c34bc39f5294f21cea97fc6e7f59ea3f(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c7c201e303bb80bca4ec7b3a395a918d8a2b4f54d6f763e9935e9ad7c70e95d3(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__9248ded17460f9422d30b6b122011a1dce094a566c458b52e339150f27a4442b(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6e860dec433546ec4aba9c60cb54c9028770f4c80aa243e3fd9bcd5b8401bab2(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3473867c4721bd437a53fec1da17012f62acdfb21bb30b9506e1f47907e67f1a(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0f7e0c3458ce4c1004698f53795ff6aa4aa82f9ccd59ad4d54f4006735edf1c5(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e00bb79f56f169325ac02872e90fdfe9be22a47a723be4044b0f6aec41cd4f39(
    value: typing.Mapping[builtins.str, builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__88612cdde8a74df9a9637f8defa8612f932b2262d52a6ea5e082be4db80e12eb(
    value: typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.List[builtins.str]]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ad3357543fe7228eb0d63c9f81d73d5f9cb0cda4e2c9dd9ef50f1f9076651fa6(
    *,
    connection: typing.Optional[typing.Union[typing.Union[_cdktf_9a9027ec.SSHProvisionerConnection, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.WinrmProvisionerConnection, typing.Dict[builtins.str, typing.Any]]]] = None,
    count: typing.Optional[typing.Union[jsii.Number, _cdktf_9a9027ec.TerraformCount]] = None,
    depends_on: typing.Optional[typing.Sequence[_cdktf_9a9027ec.ITerraformDependable]] = None,
    for_each: typing.Optional[_cdktf_9a9027ec.ITerraformIterator] = None,
    lifecycle: typing.Optional[typing.Union[_cdktf_9a9027ec.TerraformResourceLifecycle, typing.Dict[builtins.str, typing.Any]]] = None,
    provider: typing.Optional[_cdktf_9a9027ec.TerraformProvider] = None,
    provisioners: typing.Optional[typing.Sequence[typing.Union[typing.Union[_cdktf_9a9027ec.FileProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.LocalExecProvisioner, typing.Dict[builtins.str, typing.Any]], typing.Union[_cdktf_9a9027ec.RemoteExecProvisioner, typing.Dict[builtins.str, typing.Any]]]]] = None,
    type: builtins.str,
    body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    ignore_casing: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    ignore_missing_property: typing.Optional[typing.Union[builtins.bool, _cdktf_9a9027ec.IResolvable]] = None,
    locks: typing.Optional[typing.Sequence[builtins.str]] = None,
    name: typing.Optional[builtins.str] = None,
    parent_id: typing.Optional[builtins.str] = None,
    read_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    read_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
    resource_id: typing.Optional[builtins.str] = None,
    response_export_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    retry: typing.Optional[typing.Union[_UpdateResourceRetry_9d4b8e25, typing.Dict[builtins.str, typing.Any]]] = None,
    sensitive_body: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    sensitive_body_version: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    timeouts: typing.Optional[typing.Union[_UpdateResourceTimeouts_49a4241d, typing.Dict[builtins.str, typing.Any]]] = None,
    update_headers: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    update_query_parameters: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, typing.Mapping[builtins.str, typing.Sequence[builtins.str]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0d5b8baae8cd5cb861a1dc62211543930a038a166682d039c1a45479b20491a0(
    *,
    error_message_regex: typing.Sequence[builtins.str],
    interval_seconds: typing.Optional[jsii.Number] = None,
    max_interval_seconds: typing.Optional[jsii.Number] = None,
    multiplier: typing.Optional[jsii.Number] = None,
    randomization_factor: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__ebda5c7056c926d3b255cca43c22019fb02f6aac93bff7009f8ea6c3cc1c2ab6(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__92361988bbce84dd9d1d3bc74f54436199a87be8a9c73bd9e140e29ebe5887a2(
    value: typing.List[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__631bb17d86bf4be984e60b4650bde9204f34b5ea91c12ce9ec5c00e5f8295561(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__d310bb6dad7d7a235f02a5b442dcfc7b1d544581fb975140759ea469d79f51f8(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__40963906464be7b6ce6756054abad818f8b34d8a4b3b5f7b21ee442f85d04a80(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3b7c86c5c874519c7e9ea205355d1d179236c1d1133cf978942b82c606662d39(
    value: jsii.Number,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__de11ead1a94222d05289b8f1e9523a9db0efb7528a272f0a1e631f4f3bac71d4(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceRetry_9d4b8e25]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bcdbf03a33d37dc19009197844c57b4fda75d0cfe4af718df5626d451b799944(
    *,
    create: typing.Optional[builtins.str] = None,
    delete: typing.Optional[builtins.str] = None,
    read: typing.Optional[builtins.str] = None,
    update: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__67c15cb83acd7ff5eaef04c835b9bc31459304d2cc1a77dae0fd9503c02c0d57(
    terraform_resource: _cdktf_9a9027ec.IInterpolatingParent,
    terraform_attribute: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__49ac4ad9686ad51df1cafaf60a45a4c3d772a8ee6a1bc1e0e32ef294067f3f09(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__c28e72346e89a134672bbd748a71df6efa53af0ddef1779d619d0e6aab17d239(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__96333ffdeee6bcbf5d971c4129770b919396944cd51d437d3e776e48491ebb9c(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__010bcdf50a18aecf5d36481988a217dc2a85f12be134263a9bd5e936f92d002b(
    value: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__283da7d43df676ee2bbea19830ece2fed14a4fcfea65962ba64eed7bb7671608(
    value: typing.Optional[typing.Union[_cdktf_9a9027ec.IResolvable, _UpdateResourceTimeouts_49a4241d]],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a26593924c01e78ae0e6cdc013ea94dd03fd53c4ac0043e15cce684cdfcde86a(
    *,
    errors: typing.Sequence[builtins.str],
    valid: builtins.bool,
    warnings: typing.Sequence[builtins.str],
    property_errors: typing.Optional[typing.Mapping[builtins.str, typing.Sequence[builtins.str]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3b2834414beb5ad67c4dcba2220e905cc2438660d2407682ac8276a246b23ab4(
    *,
    rule_type: builtins.str,
    message: typing.Optional[builtins.str] = None,
    value: typing.Any = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__0536d827ebd3845ac3208a5b704ca8af9b3eb6af4e1ff000188c9c9676430ee3(
    *,
    change_type: builtins.str,
    description: builtins.str,
    affected_property: typing.Optional[builtins.str] = None,
    breaking: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__30ea000de9bab60a00211f861755279fa8ac81d6d5707396b7818357811593b7(
    *,
    release_date: builtins.str,
    schema: typing.Union[ApiSchema, typing.Dict[builtins.str, typing.Any]],
    support_level: builtins.str,
    version: builtins.str,
    breaking_changes: typing.Optional[typing.Sequence[typing.Union[BreakingChange, typing.Dict[builtins.str, typing.Any]]]] = None,
    change_log: typing.Optional[typing.Sequence[typing.Union[VersionChangeLog, typing.Dict[builtins.str, typing.Any]]]] = None,
    deprecation_date: typing.Optional[builtins.str] = None,
    migration_guide: typing.Optional[builtins.str] = None,
    sunset_date: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a01f7ff7cafc62faf653ded740578c692fb5c65435d8192cda2a2086d8f53bff(
    *,
    exclude_deprecated: typing.Optional[builtins.bool] = None,
    not_older_than: typing.Optional[datetime.datetime] = None,
    required_features: typing.Optional[typing.Sequence[builtins.str]] = None,
    support_level: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__fd5b3e936cf265cf7f19877c816ea9a636b3ed03018c60e711aaed3378b2a8a4(
    *,
    phase: builtins.str,
    version: builtins.str,
    estimated_sunset_date: typing.Optional[builtins.str] = None,
    next_phase: typing.Optional[builtins.str] = None,
    transition_date: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
