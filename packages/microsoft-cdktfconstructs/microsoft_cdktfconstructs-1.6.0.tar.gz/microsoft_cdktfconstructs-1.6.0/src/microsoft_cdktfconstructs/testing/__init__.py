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
    CIContext as _CIContext_5b1a1014,
    ResourceMetadata as _ResourceMetadata_74a6c06a,
    TestRunMetadata as _TestRunMetadata_604a56a9,
    TestRunOptions as _TestRunOptions_ec76b894,
)


class AssertionReturn(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.testing.AssertionReturn",
):
    def __init__(self, message: builtins.str, success: builtins.bool) -> None:
        '''Create an AssertionReturn.

        :param message: - String message containing information about the result of the assertion.
        :param success: - Boolean success denoting the success of the assertion.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e4424adf816304584e5b49191f3cf234782616e3cc6563fc4d46eab3dc232f7d)
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
            check_type(argname="argument success", value=success, expected_type=type_hints["success"])
        jsii.create(self.__class__, self, [message, success])

    @builtins.property
    @jsii.member(jsii_name="message")
    def message(self) -> builtins.str:
        '''- String message containing information about the result of the assertion.'''
        return typing.cast(builtins.str, jsii.get(self, "message"))

    @builtins.property
    @jsii.member(jsii_name="success")
    def success(self) -> builtins.bool:
        '''- Boolean success denoting the success of the assertion.'''
        return typing.cast(builtins.bool, jsii.get(self, "success"))


class BaseTestStack(
    _cdktf_9a9027ec.TerraformStack,
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.testing.BaseTestStack",
):
    '''Base stack for integration tests with optional metadata support.

    When metadata is enabled, automatically generates unique test run IDs,
    injects system tags, and provides utilities for resource naming.
    '''

    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        test_run_options: typing.Optional[typing.Union[_TestRunOptions_ec76b894, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param test_run_options: Test run configuration options.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e5dbe190b3ce570f12d2c3aef73e3a9e9fbe5270f5747b04f53197ce21f2cd43)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        options = BaseTestStackOptions(test_run_options=test_run_options)

        jsii.create(self.__class__, self, [scope, id, options])

    @jsii.member(jsii_name="generateResourceName")
    def generate_resource_name(
        self,
        resource_type: builtins.str,
        custom_identifier: typing.Optional[builtins.str] = None,
    ) -> builtins.str:
        '''Generates a unique resource name with proper Azure compliance.

        :param resource_type: - Azure resource type (e.g., 'Microsoft.Resources/resourceGroups').
        :param custom_identifier: - Optional custom identifier (defaults to test name).

        :return: Unique, Azure-compliant resource name

        :throws: Error if metadata is not initialized

        Example::

            const stack = new BaseTestStack(app, 'test-storage', { testRunOptions: {} });
            const rgName = stack.generateResourceName('Microsoft.Resources/resourceGroups');
            // Returns: 'rg-test-storage-a1b2c3'
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__71da378033fd2f3af339c3c356d1ee32b661fe9bfe7ef134b8937632dd1417d4)
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument custom_identifier", value=custom_identifier, expected_type=type_hints["custom_identifier"])
        return typing.cast(builtins.str, jsii.invoke(self, "generateResourceName", [resource_type, custom_identifier]))

    @jsii.member(jsii_name="registeredResources")
    def registered_resources(self) -> typing.List[_ResourceMetadata_74a6c06a]:
        '''Retrieves all registered resources.

        :return: Array of registered resource metadata
        '''
        return typing.cast(typing.List[_ResourceMetadata_74a6c06a], jsii.invoke(self, "registeredResources", []))

    @jsii.member(jsii_name="registerResource")
    def register_resource(
        self,
        resource_id: builtins.str,
        resource_type: builtins.str,
        name: builtins.str,
        location: typing.Optional[builtins.str] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    ) -> None:
        '''Registers a resource for tracking and cleanup verification.

        :param resource_id: - Azure resource ID.
        :param resource_type: - Azure resource type.
        :param name: - Resource name.
        :param location: - Optional resource location.
        :param tags: - Optional resource tags.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bfe314ecd0ec412a21a8342e5c155460dc6eb538107c00740b9f1b746ed3bf6c)
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
        return typing.cast(None, jsii.invoke(self, "registerResource", [resource_id, resource_type, name, location, tags]))

    @jsii.member(jsii_name="systemTags")
    def system_tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''Generates system tags for resources (only available when metadata is present).

        :return: Integration test system tags

        :throws: Error if metadata is not initialized
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.invoke(self, "systemTags", []))

    @builtins.property
    @jsii.member(jsii_name="name")
    def name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "name"))

    @builtins.property
    @jsii.member(jsii_name="metadata")
    def metadata(self) -> typing.Optional[_TestRunMetadata_604a56a9]:
        '''Optional test run metadata (only present when using BaseTestStackOptions).'''
        return typing.cast(typing.Optional[_TestRunMetadata_604a56a9], jsii.get(self, "metadata"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.BaseTestStackOptions",
    jsii_struct_bases=[],
    name_mapping={"test_run_options": "testRunOptions"},
)
class BaseTestStackOptions:
    def __init__(
        self,
        *,
        test_run_options: typing.Optional[typing.Union[_TestRunOptions_ec76b894, typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''Options for BaseTestStack constructor.

        :param test_run_options: Test run configuration options.
        '''
        if isinstance(test_run_options, dict):
            test_run_options = _TestRunOptions_ec76b894(**test_run_options)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__943b682c6a7b391a4c811a3620d66b068e46220c0cb26565d43b4e3ffa21e0b3)
            check_type(argname="argument test_run_options", value=test_run_options, expected_type=type_hints["test_run_options"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if test_run_options is not None:
            self._values["test_run_options"] = test_run_options

    @builtins.property
    def test_run_options(self) -> typing.Optional[_TestRunOptions_ec76b894]:
        '''Test run configuration options.'''
        result = self._values.get("test_run_options")
        return typing.cast(typing.Optional[_TestRunOptions_ec76b894], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BaseTestStackOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.CIContext",
    jsii_struct_bases=[],
    name_mapping={
        "platform": "platform",
        "branch": "branch",
        "commit_sha": "commitSha",
        "commit_sha_short": "commitShaShort",
        "pipeline_id": "pipelineId",
        "repository": "repository",
        "run_id": "runId",
        "run_number": "runNumber",
    },
)
class CIContext:
    def __init__(
        self,
        *,
        platform: builtins.str,
        branch: typing.Optional[builtins.str] = None,
        commit_sha: typing.Optional[builtins.str] = None,
        commit_sha_short: typing.Optional[builtins.str] = None,
        pipeline_id: typing.Optional[builtins.str] = None,
        repository: typing.Optional[builtins.str] = None,
        run_id: typing.Optional[builtins.str] = None,
        run_number: typing.Optional[builtins.str] = None,
    ) -> None:
        '''CI/CD pipeline context.

        Extracted from environment variables during test execution.
        Enables tracing resources back to specific pipeline runs.

        :param platform: CI platform ('github-actions', 'azure-devops', 'generic-ci', 'local').
        :param branch: Git branch name.
        :param commit_sha: Git commit SHA (full).
        :param commit_sha_short: Git commit SHA (short, 7 chars).
        :param pipeline_id: GitHub Actions workflow ID or equivalent.
        :param repository: Git repository name.
        :param run_id: GitHub Actions run ID or equivalent.
        :param run_number: GitHub Actions run number or equivalent.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3b36e3e7bb1a0365fdcfbb466b5f1b8f0aadd5cbc32b65f44c11f03a9e1b4a60)
            check_type(argname="argument platform", value=platform, expected_type=type_hints["platform"])
            check_type(argname="argument branch", value=branch, expected_type=type_hints["branch"])
            check_type(argname="argument commit_sha", value=commit_sha, expected_type=type_hints["commit_sha"])
            check_type(argname="argument commit_sha_short", value=commit_sha_short, expected_type=type_hints["commit_sha_short"])
            check_type(argname="argument pipeline_id", value=pipeline_id, expected_type=type_hints["pipeline_id"])
            check_type(argname="argument repository", value=repository, expected_type=type_hints["repository"])
            check_type(argname="argument run_id", value=run_id, expected_type=type_hints["run_id"])
            check_type(argname="argument run_number", value=run_number, expected_type=type_hints["run_number"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "platform": platform,
        }
        if branch is not None:
            self._values["branch"] = branch
        if commit_sha is not None:
            self._values["commit_sha"] = commit_sha
        if commit_sha_short is not None:
            self._values["commit_sha_short"] = commit_sha_short
        if pipeline_id is not None:
            self._values["pipeline_id"] = pipeline_id
        if repository is not None:
            self._values["repository"] = repository
        if run_id is not None:
            self._values["run_id"] = run_id
        if run_number is not None:
            self._values["run_number"] = run_number

    @builtins.property
    def platform(self) -> builtins.str:
        '''CI platform ('github-actions', 'azure-devops', 'generic-ci', 'local').'''
        result = self._values.get("platform")
        assert result is not None, "Required property 'platform' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def branch(self) -> typing.Optional[builtins.str]:
        '''Git branch name.'''
        result = self._values.get("branch")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def commit_sha(self) -> typing.Optional[builtins.str]:
        '''Git commit SHA (full).'''
        result = self._values.get("commit_sha")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def commit_sha_short(self) -> typing.Optional[builtins.str]:
        '''Git commit SHA (short, 7 chars).'''
        result = self._values.get("commit_sha_short")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def pipeline_id(self) -> typing.Optional[builtins.str]:
        '''GitHub Actions workflow ID or equivalent.'''
        result = self._values.get("pipeline_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def repository(self) -> typing.Optional[builtins.str]:
        '''Git repository name.'''
        result = self._values.get("repository")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def run_id(self) -> typing.Optional[builtins.str]:
        '''GitHub Actions run ID or equivalent.'''
        result = self._values.get("run_id")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def run_number(self) -> typing.Optional[builtins.str]:
        '''GitHub Actions run number or equivalent.'''
        result = self._values.get("run_number")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CIContext(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.CleanupOptions",
    jsii_struct_bases=[],
    name_mapping={
        "dry_run": "dryRun",
        "min_age_hours": "minAgeHours",
        "max_resources": "maxResources",
        "resource_groups": "resourceGroups",
        "subscription": "subscription",
    },
)
class CleanupOptions:
    def __init__(
        self,
        *,
        dry_run: builtins.bool,
        min_age_hours: jsii.Number,
        max_resources: typing.Optional[jsii.Number] = None,
        resource_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
        subscription: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Options for cleanup operations.

        :param dry_run: Whether to perform dry-run (no actual deletion).
        :param min_age_hours: Minimum age in hours before resource can be cleaned up Set to 0 to force cleanup of all resources regardless of age (bypasses safety checks).
        :param max_resources: Maximum number of resources to clean up in one operation.
        :param resource_groups: Specific resource groups to target (optional).
        :param subscription: Azure subscription ID to target (optional).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f04c7375ae118059acfa4e857a52ed84c454f1367c6751c4d630679b8c7de572)
            check_type(argname="argument dry_run", value=dry_run, expected_type=type_hints["dry_run"])
            check_type(argname="argument min_age_hours", value=min_age_hours, expected_type=type_hints["min_age_hours"])
            check_type(argname="argument max_resources", value=max_resources, expected_type=type_hints["max_resources"])
            check_type(argname="argument resource_groups", value=resource_groups, expected_type=type_hints["resource_groups"])
            check_type(argname="argument subscription", value=subscription, expected_type=type_hints["subscription"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "dry_run": dry_run,
            "min_age_hours": min_age_hours,
        }
        if max_resources is not None:
            self._values["max_resources"] = max_resources
        if resource_groups is not None:
            self._values["resource_groups"] = resource_groups
        if subscription is not None:
            self._values["subscription"] = subscription

    @builtins.property
    def dry_run(self) -> builtins.bool:
        '''Whether to perform dry-run (no actual deletion).'''
        result = self._values.get("dry_run")
        assert result is not None, "Required property 'dry_run' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def min_age_hours(self) -> jsii.Number:
        '''Minimum age in hours before resource can be cleaned up Set to 0 to force cleanup of all resources regardless of age (bypasses safety checks).'''
        result = self._values.get("min_age_hours")
        assert result is not None, "Required property 'min_age_hours' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def max_resources(self) -> typing.Optional[jsii.Number]:
        '''Maximum number of resources to clean up in one operation.'''
        result = self._values.get("max_resources")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def resource_groups(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Specific resource groups to target (optional).'''
        result = self._values.get("resource_groups")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def subscription(self) -> typing.Optional[builtins.str]:
        '''Azure subscription ID to target (optional).'''
        result = self._values.get("subscription")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CleanupOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.CleanupResult",
    jsii_struct_bases=[],
    name_mapping={
        "deleted": "deleted",
        "failed": "failed",
        "skipped": "skipped",
        "errors": "errors",
    },
)
class CleanupResult:
    def __init__(
        self,
        *,
        deleted: jsii.Number,
        failed: jsii.Number,
        skipped: jsii.Number,
        errors: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''Result of cleanup operation.

        :param deleted: Number of resources successfully deleted.
        :param failed: Number of resources that failed to delete.
        :param skipped: Number of resources skipped (e.g., too young).
        :param errors: Detailed error messages for failures.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__091ba1291d9030ff94bf5c58a8fbb5c0883baf68899559deb3692e160a952565)
            check_type(argname="argument deleted", value=deleted, expected_type=type_hints["deleted"])
            check_type(argname="argument failed", value=failed, expected_type=type_hints["failed"])
            check_type(argname="argument skipped", value=skipped, expected_type=type_hints["skipped"])
            check_type(argname="argument errors", value=errors, expected_type=type_hints["errors"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "deleted": deleted,
            "failed": failed,
            "skipped": skipped,
        }
        if errors is not None:
            self._values["errors"] = errors

    @builtins.property
    def deleted(self) -> jsii.Number:
        '''Number of resources successfully deleted.'''
        result = self._values.get("deleted")
        assert result is not None, "Required property 'deleted' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def failed(self) -> jsii.Number:
        '''Number of resources that failed to delete.'''
        result = self._values.get("failed")
        assert result is not None, "Required property 'failed' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def skipped(self) -> jsii.Number:
        '''Number of resources skipped (e.g., too young).'''
        result = self._values.get("skipped")
        assert result is not None, "Required property 'skipped' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def errors(self) -> typing.Optional[typing.List[builtins.str]]:
        '''Detailed error messages for failures.'''
        result = self._values.get("errors")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "CleanupResult(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.OrphanedResource",
    jsii_struct_bases=[],
    name_mapping={
        "age_hours": "ageHours",
        "cleanup_after": "cleanupAfter",
        "created_at": "createdAt",
        "location": "location",
        "name": "name",
        "resource_group": "resourceGroup",
        "resource_id": "resourceId",
        "resource_type": "resourceType",
        "test_name": "testName",
        "test_run_id": "testRunId",
    },
)
class OrphanedResource:
    def __init__(
        self,
        *,
        age_hours: jsii.Number,
        cleanup_after: datetime.datetime,
        created_at: datetime.datetime,
        location: builtins.str,
        name: builtins.str,
        resource_group: builtins.str,
        resource_id: builtins.str,
        resource_type: builtins.str,
        test_name: builtins.str,
        test_run_id: builtins.str,
    ) -> None:
        '''Orphaned resource information.

        :param age_hours: Age in hours since creation.
        :param cleanup_after: Cleanup after timestamp from tags.
        :param created_at: Creation timestamp from tags.
        :param location: Resource location.
        :param name: Resource name.
        :param resource_group: Resource group name.
        :param resource_id: Azure resource ID.
        :param resource_type: Azure resource type.
        :param test_name: Test name from tags.
        :param test_run_id: Test run ID from tags.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f3170e629b63a459e2e6c9cf7591600142ac2c927fae95d6c4a7a5ec23321037)
            check_type(argname="argument age_hours", value=age_hours, expected_type=type_hints["age_hours"])
            check_type(argname="argument cleanup_after", value=cleanup_after, expected_type=type_hints["cleanup_after"])
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument resource_group", value=resource_group, expected_type=type_hints["resource_group"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument test_name", value=test_name, expected_type=type_hints["test_name"])
            check_type(argname="argument test_run_id", value=test_run_id, expected_type=type_hints["test_run_id"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "age_hours": age_hours,
            "cleanup_after": cleanup_after,
            "created_at": created_at,
            "location": location,
            "name": name,
            "resource_group": resource_group,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "test_name": test_name,
            "test_run_id": test_run_id,
        }

    @builtins.property
    def age_hours(self) -> jsii.Number:
        '''Age in hours since creation.'''
        result = self._values.get("age_hours")
        assert result is not None, "Required property 'age_hours' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def cleanup_after(self) -> datetime.datetime:
        '''Cleanup after timestamp from tags.'''
        result = self._values.get("cleanup_after")
        assert result is not None, "Required property 'cleanup_after' is missing"
        return typing.cast(datetime.datetime, result)

    @builtins.property
    def created_at(self) -> datetime.datetime:
        '''Creation timestamp from tags.'''
        result = self._values.get("created_at")
        assert result is not None, "Required property 'created_at' is missing"
        return typing.cast(datetime.datetime, result)

    @builtins.property
    def location(self) -> builtins.str:
        '''Resource location.'''
        result = self._values.get("location")
        assert result is not None, "Required property 'location' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Resource name.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_group(self) -> builtins.str:
        '''Resource group name.'''
        result = self._values.get("resource_group")
        assert result is not None, "Required property 'resource_group' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''Azure resource ID.'''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_type(self) -> builtins.str:
        '''Azure resource type.'''
        result = self._values.get("resource_type")
        assert result is not None, "Required property 'resource_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def test_name(self) -> builtins.str:
        '''Test name from tags.'''
        result = self._values.get("test_name")
        assert result is not None, "Required property 'test_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def test_run_id(self) -> builtins.str:
        '''Test run ID from tags.'''
        result = self._values.get("test_run_id")
        assert result is not None, "Required property 'test_run_id' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "OrphanedResource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class ResourceCleanupService(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.testing.ResourceCleanupService",
):
    '''Main cleanup service class.'''

    def __init__(self) -> None:
        jsii.create(self.__class__, self, [])

    @jsii.member(jsii_name="checkAzureCliAvailable")
    def check_azure_cli_available(self) -> builtins.bool:
        '''Checks if Azure CLI is available.'''
        return typing.cast(builtins.bool, jsii.invoke(self, "checkAzureCliAvailable", []))

    @jsii.member(jsii_name="queryAzureResourcesByTags")
    def query_azure_resources_by_tags(
        self,
        tags: typing.Mapping[builtins.str, builtins.str],
        subscription: typing.Optional[builtins.str] = None,
    ) -> typing.List[typing.Any]:
        '''Queries Azure Resource Graph for resources by tags.

        Returns empty array on errors for graceful degradation.

        :param tags: -
        :param subscription: -
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1a506a87e2cb4975438d86d49d44110e52b965b638c66c86f555eb5bba1202f3)
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument subscription", value=subscription, expected_type=type_hints["subscription"])
        return typing.cast(typing.List[typing.Any], jsii.invoke(self, "queryAzureResourcesByTags", [tags, subscription]))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.ResourceMetadata",
    jsii_struct_bases=[],
    name_mapping={
        "created_at": "createdAt",
        "name": "name",
        "resource_id": "resourceId",
        "resource_type": "resourceType",
        "tags": "tags",
        "test_run_id": "testRunId",
        "destroyed": "destroyed",
        "destroyed_at": "destroyedAt",
        "location": "location",
    },
)
class ResourceMetadata:
    def __init__(
        self,
        *,
        created_at: datetime.datetime,
        name: builtins.str,
        resource_id: builtins.str,
        resource_type: builtins.str,
        tags: typing.Mapping[builtins.str, builtins.str],
        test_run_id: builtins.str,
        destroyed: typing.Optional[builtins.bool] = None,
        destroyed_at: typing.Optional[datetime.datetime] = None,
        location: typing.Optional[builtins.str] = None,
    ) -> None:
        '''Metadata for an individual resource created during testing.

        :param created_at: Timestamp when resource was created.
        :param name: Resource name.
        :param resource_id: Azure resource ID.
        :param resource_type: Azure resource type (e.g., 'Microsoft.Resources/resourceGroups').
        :param tags: Resource tags.
        :param test_run_id: Test run ID that created this resource.
        :param destroyed: Whether this resource was successfully destroyed.
        :param destroyed_at: Timestamp when resource was destroyed.
        :param location: Resource location (Azure region).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__55fbddfe910f29c0991bd3099cb89bedd1de511a50d50537f5d930fdbdceb287)
            check_type(argname="argument created_at", value=created_at, expected_type=type_hints["created_at"])
            check_type(argname="argument name", value=name, expected_type=type_hints["name"])
            check_type(argname="argument resource_id", value=resource_id, expected_type=type_hints["resource_id"])
            check_type(argname="argument resource_type", value=resource_type, expected_type=type_hints["resource_type"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument test_run_id", value=test_run_id, expected_type=type_hints["test_run_id"])
            check_type(argname="argument destroyed", value=destroyed, expected_type=type_hints["destroyed"])
            check_type(argname="argument destroyed_at", value=destroyed_at, expected_type=type_hints["destroyed_at"])
            check_type(argname="argument location", value=location, expected_type=type_hints["location"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "created_at": created_at,
            "name": name,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "tags": tags,
            "test_run_id": test_run_id,
        }
        if destroyed is not None:
            self._values["destroyed"] = destroyed
        if destroyed_at is not None:
            self._values["destroyed_at"] = destroyed_at
        if location is not None:
            self._values["location"] = location

    @builtins.property
    def created_at(self) -> datetime.datetime:
        '''Timestamp when resource was created.'''
        result = self._values.get("created_at")
        assert result is not None, "Required property 'created_at' is missing"
        return typing.cast(datetime.datetime, result)

    @builtins.property
    def name(self) -> builtins.str:
        '''Resource name.'''
        result = self._values.get("name")
        assert result is not None, "Required property 'name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_id(self) -> builtins.str:
        '''Azure resource ID.'''
        result = self._values.get("resource_id")
        assert result is not None, "Required property 'resource_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def resource_type(self) -> builtins.str:
        '''Azure resource type (e.g., 'Microsoft.Resources/resourceGroups').'''
        result = self._values.get("resource_type")
        assert result is not None, "Required property 'resource_type' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''Resource tags.'''
        result = self._values.get("tags")
        assert result is not None, "Required property 'tags' is missing"
        return typing.cast(typing.Mapping[builtins.str, builtins.str], result)

    @builtins.property
    def test_run_id(self) -> builtins.str:
        '''Test run ID that created this resource.'''
        result = self._values.get("test_run_id")
        assert result is not None, "Required property 'test_run_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def destroyed(self) -> typing.Optional[builtins.bool]:
        '''Whether this resource was successfully destroyed.'''
        result = self._values.get("destroyed")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def destroyed_at(self) -> typing.Optional[datetime.datetime]:
        '''Timestamp when resource was destroyed.'''
        result = self._values.get("destroyed_at")
        return typing.cast(typing.Optional[datetime.datetime], result)

    @builtins.property
    def location(self) -> typing.Optional[builtins.str]:
        '''Resource location (Azure region).'''
        result = self._values.get("location")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceMetadata(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class TestRunMetadata(
    metaclass=jsii.JSIIMeta,
    jsii_type="@microsoft/terraform-cdk-constructs.testing.TestRunMetadata",
):
    '''Metadata for an integration test run.

    Generated once per test execution and shared across all resources
    in that test. Provides unique identification, temporal tracking,
    and CI/CD context.
    '''

    def __init__(
        self,
        test_name: builtins.str,
        *,
        auto_cleanup: typing.Optional[builtins.bool] = None,
        cleanup_policy: typing.Optional[builtins.str] = None,
        max_age_hours: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Creates new test run metadata.

        :param test_name: - Test name (will be sanitized).
        :param auto_cleanup: Enable automated cleanup (default: true).
        :param cleanup_policy: Cleanup policy (default: 'immediate').
        :param max_age_hours: Maximum age in hours before cleanup eligible (default: 4).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__69f3faf20cf560cc8c6069d303e6c75daf437b00da9350706169b3814ea7b643)
            check_type(argname="argument test_name", value=test_name, expected_type=type_hints["test_name"])
        options = _TestRunOptions_ec76b894(
            auto_cleanup=auto_cleanup,
            cleanup_policy=cleanup_policy,
            max_age_hours=max_age_hours,
        )

        jsii.create(self.__class__, self, [test_name, options])

    @jsii.member(jsii_name="generateSystemTags")
    def generate_system_tags(self) -> typing.Mapping[builtins.str, builtins.str]:
        '''Generates system tags for resources.

        :return: Integration test system tags
        '''
        return typing.cast(typing.Mapping[builtins.str, builtins.str], jsii.invoke(self, "generateSystemTags", []))

    @jsii.member(jsii_name="isCleanupEligible")
    def is_cleanup_eligible(
        self,
        now: typing.Optional[datetime.datetime] = None,
    ) -> builtins.bool:
        '''Checks if resources from this run are eligible for cleanup.

        :param now: - Current time (defaults to now).

        :return: Whether cleanup is eligible
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__09b8130892e05a00162c169c1462d7d41f004e2b574c695871bd5473634e1290)
            check_type(argname="argument now", value=now, expected_type=type_hints["now"])
        return typing.cast(builtins.bool, jsii.invoke(self, "isCleanupEligible", [now]))

    @jsii.member(jsii_name="toJSON")
    def to_json(self) -> typing.Mapping[builtins.str, typing.Any]:
        '''Serializes metadata to JSON for logging.

        :return: JSON-serializable object
        '''
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "toJSON", []))

    @builtins.property
    @jsii.member(jsii_name="autoCleanup")
    def auto_cleanup(self) -> builtins.bool:
        '''Enable automated cleanup.'''
        return typing.cast(builtins.bool, jsii.get(self, "autoCleanup"))

    @builtins.property
    @jsii.member(jsii_name="cleanupAfter")
    def cleanup_after(self) -> datetime.datetime:
        '''Cleanup after timestamp (createdAt + maxAgeHours).'''
        return typing.cast(datetime.datetime, jsii.get(self, "cleanupAfter"))

    @builtins.property
    @jsii.member(jsii_name="cleanupPolicy")
    def cleanup_policy(self) -> builtins.str:
        '''Cleanup policy.'''
        return typing.cast(builtins.str, jsii.get(self, "cleanupPolicy"))

    @builtins.property
    @jsii.member(jsii_name="createdAt")
    def created_at(self) -> datetime.datetime:
        '''Timestamp when the test run started.'''
        return typing.cast(datetime.datetime, jsii.get(self, "createdAt"))

    @builtins.property
    @jsii.member(jsii_name="maxAgeHours")
    def max_age_hours(self) -> jsii.Number:
        '''Maximum age in hours before cleanup eligible.'''
        return typing.cast(jsii.Number, jsii.get(self, "maxAgeHours"))

    @builtins.property
    @jsii.member(jsii_name="runId")
    def run_id(self) -> builtins.str:
        '''Unique identifier for this test run (UUID v4).'''
        return typing.cast(builtins.str, jsii.get(self, "runId"))

    @builtins.property
    @jsii.member(jsii_name="testName")
    def test_name(self) -> builtins.str:
        '''Sanitized test name from the describe block.'''
        return typing.cast(builtins.str, jsii.get(self, "testName"))

    @builtins.property
    @jsii.member(jsii_name="ciContext")
    def ci_context(self) -> typing.Optional[_CIContext_5b1a1014]:
        '''CI/CD context (populated from environment variables).'''
        return typing.cast(typing.Optional[_CIContext_5b1a1014], jsii.get(self, "ciContext"))


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.TestRunOptions",
    jsii_struct_bases=[],
    name_mapping={
        "auto_cleanup": "autoCleanup",
        "cleanup_policy": "cleanupPolicy",
        "max_age_hours": "maxAgeHours",
    },
)
class TestRunOptions:
    def __init__(
        self,
        *,
        auto_cleanup: typing.Optional[builtins.bool] = None,
        cleanup_policy: typing.Optional[builtins.str] = None,
        max_age_hours: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Test run configuration options.

        :param auto_cleanup: Enable automated cleanup (default: true).
        :param cleanup_policy: Cleanup policy (default: 'immediate').
        :param max_age_hours: Maximum age in hours before cleanup eligible (default: 4).
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__77ffb9ddb416832ca82f3b67eb82223e1332628415fc7565a916491a559d3d68)
            check_type(argname="argument auto_cleanup", value=auto_cleanup, expected_type=type_hints["auto_cleanup"])
            check_type(argname="argument cleanup_policy", value=cleanup_policy, expected_type=type_hints["cleanup_policy"])
            check_type(argname="argument max_age_hours", value=max_age_hours, expected_type=type_hints["max_age_hours"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if auto_cleanup is not None:
            self._values["auto_cleanup"] = auto_cleanup
        if cleanup_policy is not None:
            self._values["cleanup_policy"] = cleanup_policy
        if max_age_hours is not None:
            self._values["max_age_hours"] = max_age_hours

    @builtins.property
    def auto_cleanup(self) -> typing.Optional[builtins.bool]:
        '''Enable automated cleanup (default: true).'''
        result = self._values.get("auto_cleanup")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def cleanup_policy(self) -> typing.Optional[builtins.str]:
        '''Cleanup policy (default: 'immediate').'''
        result = self._values.get("cleanup_policy")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def max_age_hours(self) -> typing.Optional[jsii.Number]:
        '''Maximum age in hours before cleanup eligible (default: 4).'''
        result = self._values.get("max_age_hours")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TestRunOptions(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@microsoft/terraform-cdk-constructs.testing.VerificationResult",
    jsii_struct_bases=[],
    name_mapping={
        "message": "message",
        "orphaned_resources": "orphanedResources",
        "success": "success",
        "expected_count": "expectedCount",
        "found_count": "foundCount",
    },
)
class VerificationResult:
    def __init__(
        self,
        *,
        message: builtins.str,
        orphaned_resources: typing.Sequence[builtins.str],
        success: builtins.bool,
        expected_count: typing.Optional[jsii.Number] = None,
        found_count: typing.Optional[jsii.Number] = None,
    ) -> None:
        '''Result of resource cleanup verification.

        :param message: Human-readable message describing the result.
        :param orphaned_resources: List of orphaned resource IDs (if any).
        :param success: Whether verification succeeded (all resources deleted).
        :param expected_count: Number of resources expected to be deleted.
        :param found_count: Number of resources actually found.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1a3bbcee23e49c79624e8df86b8dc7d9f4dfe038c3edaf3a5101cb19d3d7b8b4)
            check_type(argname="argument message", value=message, expected_type=type_hints["message"])
            check_type(argname="argument orphaned_resources", value=orphaned_resources, expected_type=type_hints["orphaned_resources"])
            check_type(argname="argument success", value=success, expected_type=type_hints["success"])
            check_type(argname="argument expected_count", value=expected_count, expected_type=type_hints["expected_count"])
            check_type(argname="argument found_count", value=found_count, expected_type=type_hints["found_count"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "message": message,
            "orphaned_resources": orphaned_resources,
            "success": success,
        }
        if expected_count is not None:
            self._values["expected_count"] = expected_count
        if found_count is not None:
            self._values["found_count"] = found_count

    @builtins.property
    def message(self) -> builtins.str:
        '''Human-readable message describing the result.'''
        result = self._values.get("message")
        assert result is not None, "Required property 'message' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def orphaned_resources(self) -> typing.List[builtins.str]:
        '''List of orphaned resource IDs (if any).'''
        result = self._values.get("orphaned_resources")
        assert result is not None, "Required property 'orphaned_resources' is missing"
        return typing.cast(typing.List[builtins.str], result)

    @builtins.property
    def success(self) -> builtins.bool:
        '''Whether verification succeeded (all resources deleted).'''
        result = self._values.get("success")
        assert result is not None, "Required property 'success' is missing"
        return typing.cast(builtins.bool, result)

    @builtins.property
    def expected_count(self) -> typing.Optional[jsii.Number]:
        '''Number of resources expected to be deleted.'''
        result = self._values.get("expected_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    @builtins.property
    def found_count(self) -> typing.Optional[jsii.Number]:
        '''Number of resources actually found.'''
        result = self._values.get("found_count")
        return typing.cast(typing.Optional[jsii.Number], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "VerificationResult(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "AssertionReturn",
    "BaseTestStack",
    "BaseTestStackOptions",
    "CIContext",
    "CleanupOptions",
    "CleanupResult",
    "OrphanedResource",
    "ResourceCleanupService",
    "ResourceMetadata",
    "TestRunMetadata",
    "TestRunOptions",
    "VerificationResult",
]

publication.publish()

def _typecheckingstub__e4424adf816304584e5b49191f3cf234782616e3cc6563fc4d46eab3dc232f7d(
    message: builtins.str,
    success: builtins.bool,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e5dbe190b3ce570f12d2c3aef73e3a9e9fbe5270f5747b04f53197ce21f2cd43(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    test_run_options: typing.Optional[typing.Union[_TestRunOptions_ec76b894, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__71da378033fd2f3af339c3c356d1ee32b661fe9bfe7ef134b8937632dd1417d4(
    resource_type: builtins.str,
    custom_identifier: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bfe314ecd0ec412a21a8342e5c155460dc6eb538107c00740b9f1b746ed3bf6c(
    resource_id: builtins.str,
    resource_type: builtins.str,
    name: builtins.str,
    location: typing.Optional[builtins.str] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__943b682c6a7b391a4c811a3620d66b068e46220c0cb26565d43b4e3ffa21e0b3(
    *,
    test_run_options: typing.Optional[typing.Union[_TestRunOptions_ec76b894, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3b36e3e7bb1a0365fdcfbb466b5f1b8f0aadd5cbc32b65f44c11f03a9e1b4a60(
    *,
    platform: builtins.str,
    branch: typing.Optional[builtins.str] = None,
    commit_sha: typing.Optional[builtins.str] = None,
    commit_sha_short: typing.Optional[builtins.str] = None,
    pipeline_id: typing.Optional[builtins.str] = None,
    repository: typing.Optional[builtins.str] = None,
    run_id: typing.Optional[builtins.str] = None,
    run_number: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f04c7375ae118059acfa4e857a52ed84c454f1367c6751c4d630679b8c7de572(
    *,
    dry_run: builtins.bool,
    min_age_hours: jsii.Number,
    max_resources: typing.Optional[jsii.Number] = None,
    resource_groups: typing.Optional[typing.Sequence[builtins.str]] = None,
    subscription: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__091ba1291d9030ff94bf5c58a8fbb5c0883baf68899559deb3692e160a952565(
    *,
    deleted: jsii.Number,
    failed: jsii.Number,
    skipped: jsii.Number,
    errors: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f3170e629b63a459e2e6c9cf7591600142ac2c927fae95d6c4a7a5ec23321037(
    *,
    age_hours: jsii.Number,
    cleanup_after: datetime.datetime,
    created_at: datetime.datetime,
    location: builtins.str,
    name: builtins.str,
    resource_group: builtins.str,
    resource_id: builtins.str,
    resource_type: builtins.str,
    test_name: builtins.str,
    test_run_id: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1a506a87e2cb4975438d86d49d44110e52b965b638c66c86f555eb5bba1202f3(
    tags: typing.Mapping[builtins.str, builtins.str],
    subscription: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__55fbddfe910f29c0991bd3099cb89bedd1de511a50d50537f5d930fdbdceb287(
    *,
    created_at: datetime.datetime,
    name: builtins.str,
    resource_id: builtins.str,
    resource_type: builtins.str,
    tags: typing.Mapping[builtins.str, builtins.str],
    test_run_id: builtins.str,
    destroyed: typing.Optional[builtins.bool] = None,
    destroyed_at: typing.Optional[datetime.datetime] = None,
    location: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__69f3faf20cf560cc8c6069d303e6c75daf437b00da9350706169b3814ea7b643(
    test_name: builtins.str,
    *,
    auto_cleanup: typing.Optional[builtins.bool] = None,
    cleanup_policy: typing.Optional[builtins.str] = None,
    max_age_hours: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__09b8130892e05a00162c169c1462d7d41f004e2b574c695871bd5473634e1290(
    now: typing.Optional[datetime.datetime] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__77ffb9ddb416832ca82f3b67eb82223e1332628415fc7565a916491a559d3d68(
    *,
    auto_cleanup: typing.Optional[builtins.bool] = None,
    cleanup_policy: typing.Optional[builtins.str] = None,
    max_age_hours: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1a3bbcee23e49c79624e8df86b8dc7d9f4dfe038c3edaf3a5101cb19d3d7b8b4(
    *,
    message: builtins.str,
    orphaned_resources: typing.Sequence[builtins.str],
    success: builtins.bool,
    expected_count: typing.Optional[jsii.Number] = None,
    found_count: typing.Optional[jsii.Number] = None,
) -> None:
    """Type checking stubs"""
    pass
