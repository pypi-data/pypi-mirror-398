r'''
# AWS RDS Database Auto Running Protection Stack

[![GitHub](https://img.shields.io/github/license/gammarers/aws-rds-database-auto-running-protection-stack?style=flat-square)](https://github.com/gammarers/aws-rds-database-auto-running-protection-stack/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-rds-database-auto-running-protection-stack?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-rds-database-auto-running-protection-stack)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-rds-database-auto-running-protection-stack?style=flat-square)](https://pypi.org/project/gammarers.aws-rds-database-auto-running-protection-stack/)
[![Nuget](https://img.shields.io/nuget/v/Gammarers.CDK.AWS.RDSDatabaseAutoRunningProtectionStack?style=flat-square)](https://www.nuget.org/packages/Gammarers.CDK.AWS.RDSDatabaseAutoRunningProtectionStack/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-rds-database-auto-running-protection-stack/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-rds-database-auto-running-protection-stack/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-rds-database-auto-running-protection-stack?sort=semver&style=flat-square)](https://github.com/gammarers/aws-rds-database-auto-running-protection-stack/releases)

[![View on Construct Hub](https://constructs.dev/badge?package=@gammarers/aws-rds-database-auto-running-protection-stack)](https://constructs.dev/packages/@gammarers/aws-rds-database-auto-running-protection-stack)

This constructor stack includes a function to automatically stop a database or cluster that will automatically start in 7 days.

> [!WARNING]
> v2.1.0:
> Stack props add option resourceNamingOption
> default ResourceNamingType.DEFAULT is cdk generated name
> if you want to maintain compatibility with versions below `v2.1.0`, please include the following settings (ResourceNamingType.AUTO).
>
> ```python
> new RDSDatabaseAutoRunningProtectionStack(app, 'RDSDatabaseAutoRunningProtectionStack', {
>   stackName: 'rds-database-auto-running-protection-stack',
>   targetResource: {
>     tagKey: 'AutoRunningProtection',
>     tagValues: ['YES'],
>   },
>   resourceNamingOption: {
>     type: RDSDatabaseAutoRunningProtectionStackResourceNamingType.AUTO, // HERE
>   },
> });
> ```

## Resources

This construct creating resource list.

* StepFunctions(StateMachine)
* IAM Role (StepFunctions)
* IAM Policy (StepFunctions)
* EventBridge
* IAM Role (EventBridge)

## Install

### TypeScript

#### install by npm

```shell
npm install @gammarers/aws-rds-database-auto-running-protection-stack
```

#### install by yarn

```shell
yarn add @gammarers/aws-rds-database-auto-running-protection-stack
```

#### install by pnpm

```shell
pnpm add @gammarers/aws-rds-database-auto-running-protection-stack
```

#### install by bun

```shell
bun add @gammarers/aws-rds-database-auto-running-protection-stack
```

### Python

```shell
pip install gammarers.aws-rds-database-auto-running-protection-stack
```

### C# / .NET

```shell
dotnet add package Gammarers.CDK.AWS.RDSDatabaseAutoRunningProtectionStack
```

## Example

### Code

```python
import { RDSDatabaseAutoRunningProtectionStack } from '@gammarers/aws-rds-database-auto-running-protection-stack';

new RDSDatabaseAutoRunningProtectionStack(app, 'RDSDatabaseAutoRunningProtectionStack', {
  stackName: 'rds-database-auto-running-protection-stack',
  targetResource: {
    tagKey: 'AutoRunningProtection',
    tagValues: ['YES'],
  },
  resourceNamingOption: {
    type: RDSDatabaseAutoRunningProtectionStackResourceNamingType.DEFAULT,
  },
  notifications: {
    emails: [ // "Incoming Sample Message - EMAIL"
      'foo@example.com',
      'bar@example.net',
    ],
    slack: { // "Incoming Sample Message - Slack"
      webhookSecretName: 'example/slack/webhook', // Slack webhook secret
    },
  },
});
```

### Slack webhook secret

Please save it in AWS Secrets Manager in the following format.

get your slack webhook url parts

```text
https://hooks.slack.com/services/<workspace>/<channel>/<whebook>
```

| SecretKey 	 | SecretValue 	   |
|-------------|-----------------|
| Workspace 	 | <workspace> 	 |
| Channel   	 | <channel>   	 |
| Webhook   	 | <whebook>   	 |

## Incoming Sample Message

### EMAIL

![](./images/example-email.png)

### Slack

![](./images/example-slack.png)

## License

This project is licensed under the Apache-2.0 License.
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

from ._jsii import *

import aws_cdk as _aws_cdk_ceddda9d
import aws_cdk.aws_stepfunctions as _aws_cdk_aws_stepfunctions_ceddda9d
import constructs as _constructs_77d1e7e8
import gammarers.aws_resource_naming as _gammarers_aws_resource_naming_22f917da


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.LogOption",
    jsii_struct_bases=[],
    name_mapping={"machine_log_level": "machineLogLevel"},
)
class LogOption:
    def __init__(
        self,
        *,
        machine_log_level: typing.Optional["_aws_cdk_aws_stepfunctions_ceddda9d.LogLevel"] = None,
    ) -> None:
        '''
        :param machine_log_level: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__0e695c65120a26566e3b1da2c283ffd65b205e848edf601c0e4413f96382028d)
            check_type(argname="argument machine_log_level", value=machine_log_level, expected_type=type_hints["machine_log_level"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if machine_log_level is not None:
            self._values["machine_log_level"] = machine_log_level

    @builtins.property
    def machine_log_level(
        self,
    ) -> typing.Optional["_aws_cdk_aws_stepfunctions_ceddda9d.LogLevel"]:
        result = self._values.get("machine_log_level")
        return typing.cast(typing.Optional["_aws_cdk_aws_stepfunctions_ceddda9d.LogLevel"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "LogOption(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.Notifications",
    jsii_struct_bases=[],
    name_mapping={"emails": "emails", "slack": "slack"},
)
class Notifications:
    def __init__(
        self,
        *,
        emails: typing.Optional[typing.Sequence[builtins.str]] = None,
        slack: typing.Optional[typing.Union["Slack", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param emails: 
        :param slack: 
        '''
        if isinstance(slack, dict):
            slack = Slack(**slack)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a1f97813ccd432edd13bc8e51df42efe9b6d3a01d26e99deaeb319cc9d58d204)
            check_type(argname="argument emails", value=emails, expected_type=type_hints["emails"])
            check_type(argname="argument slack", value=slack, expected_type=type_hints["slack"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if emails is not None:
            self._values["emails"] = emails
        if slack is not None:
            self._values["slack"] = slack

    @builtins.property
    def emails(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("emails")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    @builtins.property
    def slack(self) -> typing.Optional["Slack"]:
        result = self._values.get("slack")
        return typing.cast(typing.Optional["Slack"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Notifications(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


class RDSDatabaseAutoRunningProtectionStack(
    _aws_cdk_ceddda9d.Stack,
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.RDSDatabaseAutoRunningProtectionStack",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        target_resource: typing.Union["TargetResource", typing.Dict[builtins.str, typing.Any]],
        enable_rule: typing.Optional[builtins.bool] = None,
        log_option: typing.Optional[typing.Union["LogOption", typing.Dict[builtins.str, typing.Any]]] = None,
        notifications: typing.Optional[typing.Union["Notifications", typing.Dict[builtins.str, typing.Any]]] = None,
        resource_naming_option: typing.Optional[typing.Union[typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming", typing.Dict[builtins.str, typing.Any]], typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceAutoNaming", typing.Dict[builtins.str, typing.Any]], typing.Union["ResourceCustomNaming", typing.Dict[builtins.str, typing.Any]]]] = None,
        timeout: typing.Optional[typing.Union["Timeout", typing.Dict[builtins.str, typing.Any]]] = None,
        analytics_reporting: typing.Optional[builtins.bool] = None,
        cross_region_references: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        env: typing.Optional[typing.Union["_aws_cdk_ceddda9d.Environment", typing.Dict[builtins.str, typing.Any]]] = None,
        permissions_boundary: typing.Optional["_aws_cdk_ceddda9d.PermissionsBoundary"] = None,
        stack_name: typing.Optional[builtins.str] = None,
        suppress_template_indentation: typing.Optional[builtins.bool] = None,
        synthesizer: typing.Optional["_aws_cdk_ceddda9d.IStackSynthesizer"] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        termination_protection: typing.Optional[builtins.bool] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param target_resource: 
        :param enable_rule: 
        :param log_option: 
        :param notifications: 
        :param resource_naming_option: 
        :param timeout: 
        :param analytics_reporting: Include runtime versioning information in this Stack. Default: ``analyticsReporting`` setting of containing ``App``, or value of 'aws:cdk:version-reporting' context key
        :param cross_region_references: Enable this flag to allow native cross region stack references. Enabling this will create a CloudFormation custom resource in both the producing stack and consuming stack in order to perform the export/import This feature is currently experimental Default: false
        :param description: A description of the stack. Default: - No description.
        :param env: The AWS environment (account/region) where this stack will be deployed. Set the ``region``/``account`` fields of ``env`` to either a concrete value to select the indicated environment (recommended for production stacks), or to the values of environment variables ``CDK_DEFAULT_REGION``/``CDK_DEFAULT_ACCOUNT`` to let the target environment depend on the AWS credentials/configuration that the CDK CLI is executed under (recommended for development stacks). If the ``Stack`` is instantiated inside a ``Stage``, any undefined ``region``/``account`` fields from ``env`` will default to the same field on the encompassing ``Stage``, if configured there. If either ``region`` or ``account`` are not set nor inherited from ``Stage``, the Stack will be considered "*environment-agnostic*"". Environment-agnostic stacks can be deployed to any environment but may not be able to take advantage of all features of the CDK. For example, they will not be able to use environmental context lookups such as ``ec2.Vpc.fromLookup`` and will not automatically translate Service Principals to the right format based on the environment's AWS partition, and other such enhancements. Default: - The environment of the containing ``Stage`` if available, otherwise create the stack will be environment-agnostic.
        :param permissions_boundary: Options for applying a permissions boundary to all IAM Roles and Users created within this Stage. Default: - no permissions boundary is applied
        :param stack_name: Name to deploy the stack with. Default: - Derived from construct path.
        :param suppress_template_indentation: Enable this flag to suppress indentation in generated CloudFormation templates. If not specified, the value of the ``@aws-cdk/core:suppressTemplateIndentation`` context key will be used. If that is not specified, then the default value ``false`` will be used. Default: - the value of ``@aws-cdk/core:suppressTemplateIndentation``, or ``false`` if that is not set.
        :param synthesizer: Synthesis method to use while deploying this stack. The Stack Synthesizer controls aspects of synthesis and deployment, like how assets are referenced and what IAM roles to use. For more information, see the README of the main CDK package. If not specified, the ``defaultStackSynthesizer`` from ``App`` will be used. If that is not specified, ``DefaultStackSynthesizer`` is used if ``@aws-cdk/core:newStyleStackSynthesis`` is set to ``true`` or the CDK major version is v2. In CDK v1 ``LegacyStackSynthesizer`` is the default if no other synthesizer is specified. Default: - The synthesizer specified on ``App``, or ``DefaultStackSynthesizer`` otherwise.
        :param tags: Stack tags that will be applied to all the taggable resources and the stack itself. Default: {}
        :param termination_protection: Whether to enable termination protection for this stack. Default: false
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__983f6a01dacab988c39e7e1ead11de82110ca7e9d16eeed9b0d69ed44f9f5872)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = RDSDatabaseAutoRunningProtectionStackProps(
            target_resource=target_resource,
            enable_rule=enable_rule,
            log_option=log_option,
            notifications=notifications,
            resource_naming_option=resource_naming_option,
            timeout=timeout,
            analytics_reporting=analytics_reporting,
            cross_region_references=cross_region_references,
            description=description,
            env=env,
            permissions_boundary=permissions_boundary,
            stack_name=stack_name,
            suppress_template_indentation=suppress_template_indentation,
            synthesizer=synthesizer,
            tags=tags,
            termination_protection=termination_protection,
        )

        jsii.create(self.__class__, self, [scope, id, props])


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.RDSDatabaseAutoRunningProtectionStackProps",
    jsii_struct_bases=[_aws_cdk_ceddda9d.StackProps],
    name_mapping={
        "analytics_reporting": "analyticsReporting",
        "cross_region_references": "crossRegionReferences",
        "description": "description",
        "env": "env",
        "permissions_boundary": "permissionsBoundary",
        "stack_name": "stackName",
        "suppress_template_indentation": "suppressTemplateIndentation",
        "synthesizer": "synthesizer",
        "tags": "tags",
        "termination_protection": "terminationProtection",
        "target_resource": "targetResource",
        "enable_rule": "enableRule",
        "log_option": "logOption",
        "notifications": "notifications",
        "resource_naming_option": "resourceNamingOption",
        "timeout": "timeout",
    },
)
class RDSDatabaseAutoRunningProtectionStackProps(_aws_cdk_ceddda9d.StackProps):
    def __init__(
        self,
        *,
        analytics_reporting: typing.Optional[builtins.bool] = None,
        cross_region_references: typing.Optional[builtins.bool] = None,
        description: typing.Optional[builtins.str] = None,
        env: typing.Optional[typing.Union["_aws_cdk_ceddda9d.Environment", typing.Dict[builtins.str, typing.Any]]] = None,
        permissions_boundary: typing.Optional["_aws_cdk_ceddda9d.PermissionsBoundary"] = None,
        stack_name: typing.Optional[builtins.str] = None,
        suppress_template_indentation: typing.Optional[builtins.bool] = None,
        synthesizer: typing.Optional["_aws_cdk_ceddda9d.IStackSynthesizer"] = None,
        tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
        termination_protection: typing.Optional[builtins.bool] = None,
        target_resource: typing.Union["TargetResource", typing.Dict[builtins.str, typing.Any]],
        enable_rule: typing.Optional[builtins.bool] = None,
        log_option: typing.Optional[typing.Union["LogOption", typing.Dict[builtins.str, typing.Any]]] = None,
        notifications: typing.Optional[typing.Union["Notifications", typing.Dict[builtins.str, typing.Any]]] = None,
        resource_naming_option: typing.Optional[typing.Union[typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming", typing.Dict[builtins.str, typing.Any]], typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceAutoNaming", typing.Dict[builtins.str, typing.Any]], typing.Union["ResourceCustomNaming", typing.Dict[builtins.str, typing.Any]]]] = None,
        timeout: typing.Optional[typing.Union["Timeout", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param analytics_reporting: Include runtime versioning information in this Stack. Default: ``analyticsReporting`` setting of containing ``App``, or value of 'aws:cdk:version-reporting' context key
        :param cross_region_references: Enable this flag to allow native cross region stack references. Enabling this will create a CloudFormation custom resource in both the producing stack and consuming stack in order to perform the export/import This feature is currently experimental Default: false
        :param description: A description of the stack. Default: - No description.
        :param env: The AWS environment (account/region) where this stack will be deployed. Set the ``region``/``account`` fields of ``env`` to either a concrete value to select the indicated environment (recommended for production stacks), or to the values of environment variables ``CDK_DEFAULT_REGION``/``CDK_DEFAULT_ACCOUNT`` to let the target environment depend on the AWS credentials/configuration that the CDK CLI is executed under (recommended for development stacks). If the ``Stack`` is instantiated inside a ``Stage``, any undefined ``region``/``account`` fields from ``env`` will default to the same field on the encompassing ``Stage``, if configured there. If either ``region`` or ``account`` are not set nor inherited from ``Stage``, the Stack will be considered "*environment-agnostic*"". Environment-agnostic stacks can be deployed to any environment but may not be able to take advantage of all features of the CDK. For example, they will not be able to use environmental context lookups such as ``ec2.Vpc.fromLookup`` and will not automatically translate Service Principals to the right format based on the environment's AWS partition, and other such enhancements. Default: - The environment of the containing ``Stage`` if available, otherwise create the stack will be environment-agnostic.
        :param permissions_boundary: Options for applying a permissions boundary to all IAM Roles and Users created within this Stage. Default: - no permissions boundary is applied
        :param stack_name: Name to deploy the stack with. Default: - Derived from construct path.
        :param suppress_template_indentation: Enable this flag to suppress indentation in generated CloudFormation templates. If not specified, the value of the ``@aws-cdk/core:suppressTemplateIndentation`` context key will be used. If that is not specified, then the default value ``false`` will be used. Default: - the value of ``@aws-cdk/core:suppressTemplateIndentation``, or ``false`` if that is not set.
        :param synthesizer: Synthesis method to use while deploying this stack. The Stack Synthesizer controls aspects of synthesis and deployment, like how assets are referenced and what IAM roles to use. For more information, see the README of the main CDK package. If not specified, the ``defaultStackSynthesizer`` from ``App`` will be used. If that is not specified, ``DefaultStackSynthesizer`` is used if ``@aws-cdk/core:newStyleStackSynthesis`` is set to ``true`` or the CDK major version is v2. In CDK v1 ``LegacyStackSynthesizer`` is the default if no other synthesizer is specified. Default: - The synthesizer specified on ``App``, or ``DefaultStackSynthesizer`` otherwise.
        :param tags: Stack tags that will be applied to all the taggable resources and the stack itself. Default: {}
        :param termination_protection: Whether to enable termination protection for this stack. Default: false
        :param target_resource: 
        :param enable_rule: 
        :param log_option: 
        :param notifications: 
        :param resource_naming_option: 
        :param timeout: 
        '''
        if isinstance(env, dict):
            env = _aws_cdk_ceddda9d.Environment(**env)
        if isinstance(target_resource, dict):
            target_resource = TargetResource(**target_resource)
        if isinstance(log_option, dict):
            log_option = LogOption(**log_option)
        if isinstance(notifications, dict):
            notifications = Notifications(**notifications)
        if isinstance(timeout, dict):
            timeout = Timeout(**timeout)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__20eb7b10c40d8f8ab8440675658ba9a77a4d23f69f0bb794c3d5a6ee6f59e55f)
            check_type(argname="argument analytics_reporting", value=analytics_reporting, expected_type=type_hints["analytics_reporting"])
            check_type(argname="argument cross_region_references", value=cross_region_references, expected_type=type_hints["cross_region_references"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
            check_type(argname="argument env", value=env, expected_type=type_hints["env"])
            check_type(argname="argument permissions_boundary", value=permissions_boundary, expected_type=type_hints["permissions_boundary"])
            check_type(argname="argument stack_name", value=stack_name, expected_type=type_hints["stack_name"])
            check_type(argname="argument suppress_template_indentation", value=suppress_template_indentation, expected_type=type_hints["suppress_template_indentation"])
            check_type(argname="argument synthesizer", value=synthesizer, expected_type=type_hints["synthesizer"])
            check_type(argname="argument tags", value=tags, expected_type=type_hints["tags"])
            check_type(argname="argument termination_protection", value=termination_protection, expected_type=type_hints["termination_protection"])
            check_type(argname="argument target_resource", value=target_resource, expected_type=type_hints["target_resource"])
            check_type(argname="argument enable_rule", value=enable_rule, expected_type=type_hints["enable_rule"])
            check_type(argname="argument log_option", value=log_option, expected_type=type_hints["log_option"])
            check_type(argname="argument notifications", value=notifications, expected_type=type_hints["notifications"])
            check_type(argname="argument resource_naming_option", value=resource_naming_option, expected_type=type_hints["resource_naming_option"])
            check_type(argname="argument timeout", value=timeout, expected_type=type_hints["timeout"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "target_resource": target_resource,
        }
        if analytics_reporting is not None:
            self._values["analytics_reporting"] = analytics_reporting
        if cross_region_references is not None:
            self._values["cross_region_references"] = cross_region_references
        if description is not None:
            self._values["description"] = description
        if env is not None:
            self._values["env"] = env
        if permissions_boundary is not None:
            self._values["permissions_boundary"] = permissions_boundary
        if stack_name is not None:
            self._values["stack_name"] = stack_name
        if suppress_template_indentation is not None:
            self._values["suppress_template_indentation"] = suppress_template_indentation
        if synthesizer is not None:
            self._values["synthesizer"] = synthesizer
        if tags is not None:
            self._values["tags"] = tags
        if termination_protection is not None:
            self._values["termination_protection"] = termination_protection
        if enable_rule is not None:
            self._values["enable_rule"] = enable_rule
        if log_option is not None:
            self._values["log_option"] = log_option
        if notifications is not None:
            self._values["notifications"] = notifications
        if resource_naming_option is not None:
            self._values["resource_naming_option"] = resource_naming_option
        if timeout is not None:
            self._values["timeout"] = timeout

    @builtins.property
    def analytics_reporting(self) -> typing.Optional[builtins.bool]:
        '''Include runtime versioning information in this Stack.

        :default:

        ``analyticsReporting`` setting of containing ``App``, or value of
        'aws:cdk:version-reporting' context key
        '''
        result = self._values.get("analytics_reporting")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def cross_region_references(self) -> typing.Optional[builtins.bool]:
        '''Enable this flag to allow native cross region stack references.

        Enabling this will create a CloudFormation custom resource
        in both the producing stack and consuming stack in order to perform the export/import

        This feature is currently experimental

        :default: false
        '''
        result = self._values.get("cross_region_references")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''A description of the stack.

        :default: - No description.
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def env(self) -> typing.Optional["_aws_cdk_ceddda9d.Environment"]:
        '''The AWS environment (account/region) where this stack will be deployed.

        Set the ``region``/``account`` fields of ``env`` to either a concrete value to
        select the indicated environment (recommended for production stacks), or to
        the values of environment variables
        ``CDK_DEFAULT_REGION``/``CDK_DEFAULT_ACCOUNT`` to let the target environment
        depend on the AWS credentials/configuration that the CDK CLI is executed
        under (recommended for development stacks).

        If the ``Stack`` is instantiated inside a ``Stage``, any undefined
        ``region``/``account`` fields from ``env`` will default to the same field on the
        encompassing ``Stage``, if configured there.

        If either ``region`` or ``account`` are not set nor inherited from ``Stage``, the
        Stack will be considered "*environment-agnostic*"". Environment-agnostic
        stacks can be deployed to any environment but may not be able to take
        advantage of all features of the CDK. For example, they will not be able to
        use environmental context lookups such as ``ec2.Vpc.fromLookup`` and will not
        automatically translate Service Principals to the right format based on the
        environment's AWS partition, and other such enhancements.

        :default:

        - The environment of the containing ``Stage`` if available,
        otherwise create the stack will be environment-agnostic.

        Example::

            // Use a concrete account and region to deploy this stack to:
            // `.account` and `.region` will simply return these values.
            new Stack(app, 'Stack1', {
              env: {
                account: '123456789012',
                region: 'us-east-1'
              },
            });
            
            // Use the CLI's current credentials to determine the target environment:
            // `.account` and `.region` will reflect the account+region the CLI
            // is configured to use (based on the user CLI credentials)
            new Stack(app, 'Stack2', {
              env: {
                account: process.env.CDK_DEFAULT_ACCOUNT,
                region: process.env.CDK_DEFAULT_REGION
              },
            });
            
            // Define multiple stacks stage associated with an environment
            const myStage = new Stage(app, 'MyStage', {
              env: {
                account: '123456789012',
                region: 'us-east-1'
              }
            });
            
            // both of these stacks will use the stage's account/region:
            // `.account` and `.region` will resolve to the concrete values as above
            new MyStack(myStage, 'Stack1');
            new YourStack(myStage, 'Stack2');
            
            // Define an environment-agnostic stack:
            // `.account` and `.region` will resolve to `{ "Ref": "AWS::AccountId" }` and `{ "Ref": "AWS::Region" }` respectively.
            // which will only resolve to actual values by CloudFormation during deployment.
            new MyStack(app, 'Stack1');
        '''
        result = self._values.get("env")
        return typing.cast(typing.Optional["_aws_cdk_ceddda9d.Environment"], result)

    @builtins.property
    def permissions_boundary(
        self,
    ) -> typing.Optional["_aws_cdk_ceddda9d.PermissionsBoundary"]:
        '''Options for applying a permissions boundary to all IAM Roles and Users created within this Stage.

        :default: - no permissions boundary is applied
        '''
        result = self._values.get("permissions_boundary")
        return typing.cast(typing.Optional["_aws_cdk_ceddda9d.PermissionsBoundary"], result)

    @builtins.property
    def stack_name(self) -> typing.Optional[builtins.str]:
        '''Name to deploy the stack with.

        :default: - Derived from construct path.
        '''
        result = self._values.get("stack_name")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def suppress_template_indentation(self) -> typing.Optional[builtins.bool]:
        '''Enable this flag to suppress indentation in generated CloudFormation templates.

        If not specified, the value of the ``@aws-cdk/core:suppressTemplateIndentation``
        context key will be used. If that is not specified, then the
        default value ``false`` will be used.

        :default: - the value of ``@aws-cdk/core:suppressTemplateIndentation``, or ``false`` if that is not set.
        '''
        result = self._values.get("suppress_template_indentation")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def synthesizer(self) -> typing.Optional["_aws_cdk_ceddda9d.IStackSynthesizer"]:
        '''Synthesis method to use while deploying this stack.

        The Stack Synthesizer controls aspects of synthesis and deployment,
        like how assets are referenced and what IAM roles to use. For more
        information, see the README of the main CDK package.

        If not specified, the ``defaultStackSynthesizer`` from ``App`` will be used.
        If that is not specified, ``DefaultStackSynthesizer`` is used if
        ``@aws-cdk/core:newStyleStackSynthesis`` is set to ``true`` or the CDK major
        version is v2. In CDK v1 ``LegacyStackSynthesizer`` is the default if no
        other synthesizer is specified.

        :default: - The synthesizer specified on ``App``, or ``DefaultStackSynthesizer`` otherwise.
        '''
        result = self._values.get("synthesizer")
        return typing.cast(typing.Optional["_aws_cdk_ceddda9d.IStackSynthesizer"], result)

    @builtins.property
    def tags(self) -> typing.Optional[typing.Mapping[builtins.str, builtins.str]]:
        '''Stack tags that will be applied to all the taggable resources and the stack itself.

        :default: {}
        '''
        result = self._values.get("tags")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, builtins.str]], result)

    @builtins.property
    def termination_protection(self) -> typing.Optional[builtins.bool]:
        '''Whether to enable termination protection for this stack.

        :default: false
        '''
        result = self._values.get("termination_protection")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def target_resource(self) -> "TargetResource":
        result = self._values.get("target_resource")
        assert result is not None, "Required property 'target_resource' is missing"
        return typing.cast("TargetResource", result)

    @builtins.property
    def enable_rule(self) -> typing.Optional[builtins.bool]:
        result = self._values.get("enable_rule")
        return typing.cast(typing.Optional[builtins.bool], result)

    @builtins.property
    def log_option(self) -> typing.Optional["LogOption"]:
        result = self._values.get("log_option")
        return typing.cast(typing.Optional["LogOption"], result)

    @builtins.property
    def notifications(self) -> typing.Optional["Notifications"]:
        result = self._values.get("notifications")
        return typing.cast(typing.Optional["Notifications"], result)

    @builtins.property
    def resource_naming_option(
        self,
    ) -> typing.Optional[typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming", "_gammarers_aws_resource_naming_22f917da.ResourceAutoNaming", "ResourceCustomNaming"]]:
        result = self._values.get("resource_naming_option")
        return typing.cast(typing.Optional[typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming", "_gammarers_aws_resource_naming_22f917da.ResourceAutoNaming", "ResourceCustomNaming"]], result)

    @builtins.property
    def timeout(self) -> typing.Optional["Timeout"]:
        result = self._values.get("timeout")
        return typing.cast(typing.Optional["Timeout"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "RDSDatabaseAutoRunningProtectionStackProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.ResourceCustomNaming",
    jsii_struct_bases=[],
    name_mapping={
        "start_cluster_event_catch_rule_name": "startClusterEventCatchRuleName",
        "start_event_catch_rule_role_name": "startEventCatchRuleRoleName",
        "start_instance_event_catch_rule_name": "startInstanceEventCatchRuleName",
        "state_machine_name": "stateMachineName",
        "state_machine_role_name": "stateMachineRoleName",
        "type": "type",
    },
)
class ResourceCustomNaming:
    def __init__(
        self,
        *,
        start_cluster_event_catch_rule_name: builtins.str,
        start_event_catch_rule_role_name: builtins.str,
        start_instance_event_catch_rule_name: builtins.str,
        state_machine_name: builtins.str,
        state_machine_role_name: builtins.str,
        type: "_gammarers_aws_resource_naming_22f917da.ResourceNamingType",
    ) -> None:
        '''
        :param start_cluster_event_catch_rule_name: 
        :param start_event_catch_rule_role_name: 
        :param start_instance_event_catch_rule_name: 
        :param state_machine_name: 
        :param state_machine_role_name: 
        :param type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b08fc47cfe2dc5c647800bb73a1a4d5d59d49aee7bb66da50baeadb9a2f4357f)
            check_type(argname="argument start_cluster_event_catch_rule_name", value=start_cluster_event_catch_rule_name, expected_type=type_hints["start_cluster_event_catch_rule_name"])
            check_type(argname="argument start_event_catch_rule_role_name", value=start_event_catch_rule_role_name, expected_type=type_hints["start_event_catch_rule_role_name"])
            check_type(argname="argument start_instance_event_catch_rule_name", value=start_instance_event_catch_rule_name, expected_type=type_hints["start_instance_event_catch_rule_name"])
            check_type(argname="argument state_machine_name", value=state_machine_name, expected_type=type_hints["state_machine_name"])
            check_type(argname="argument state_machine_role_name", value=state_machine_role_name, expected_type=type_hints["state_machine_role_name"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "start_cluster_event_catch_rule_name": start_cluster_event_catch_rule_name,
            "start_event_catch_rule_role_name": start_event_catch_rule_role_name,
            "start_instance_event_catch_rule_name": start_instance_event_catch_rule_name,
            "state_machine_name": state_machine_name,
            "state_machine_role_name": state_machine_role_name,
            "type": type,
        }

    @builtins.property
    def start_cluster_event_catch_rule_name(self) -> builtins.str:
        result = self._values.get("start_cluster_event_catch_rule_name")
        assert result is not None, "Required property 'start_cluster_event_catch_rule_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def start_event_catch_rule_role_name(self) -> builtins.str:
        result = self._values.get("start_event_catch_rule_role_name")
        assert result is not None, "Required property 'start_event_catch_rule_role_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def start_instance_event_catch_rule_name(self) -> builtins.str:
        result = self._values.get("start_instance_event_catch_rule_name")
        assert result is not None, "Required property 'start_instance_event_catch_rule_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def state_machine_name(self) -> builtins.str:
        result = self._values.get("state_machine_name")
        assert result is not None, "Required property 'state_machine_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def state_machine_role_name(self) -> builtins.str:
        result = self._values.get("state_machine_role_name")
        assert result is not None, "Required property 'state_machine_role_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def type(self) -> "_gammarers_aws_resource_naming_22f917da.ResourceNamingType":
        result = self._values.get("type")
        assert result is not None, "Required property 'type' is missing"
        return typing.cast("_gammarers_aws_resource_naming_22f917da.ResourceNamingType", result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ResourceCustomNaming(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.Slack",
    jsii_struct_bases=[],
    name_mapping={"webhook_secret_name": "webhookSecretName"},
)
class Slack:
    def __init__(self, *, webhook_secret_name: builtins.str) -> None:
        '''
        :param webhook_secret_name: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__cfac7c53e98ff15446c34e20d7e47a4148faaaa3b6384da25871e7fb8bd13bc8)
            check_type(argname="argument webhook_secret_name", value=webhook_secret_name, expected_type=type_hints["webhook_secret_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "webhook_secret_name": webhook_secret_name,
        }

    @builtins.property
    def webhook_secret_name(self) -> builtins.str:
        result = self._values.get("webhook_secret_name")
        assert result is not None, "Required property 'webhook_secret_name' is missing"
        return typing.cast(builtins.str, result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Slack(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.TargetResource",
    jsii_struct_bases=[],
    name_mapping={"tag_key": "tagKey", "tag_values": "tagValues"},
)
class TargetResource:
    def __init__(
        self,
        *,
        tag_key: builtins.str,
        tag_values: typing.Sequence[builtins.str],
    ) -> None:
        '''
        :param tag_key: 
        :param tag_values: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4cee11dd8fd6f411fd9b19762c078370378e6b5b96bf7c81e75f94d9e94ab0ac)
            check_type(argname="argument tag_key", value=tag_key, expected_type=type_hints["tag_key"])
            check_type(argname="argument tag_values", value=tag_values, expected_type=type_hints["tag_values"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "tag_key": tag_key,
            "tag_values": tag_values,
        }

    @builtins.property
    def tag_key(self) -> builtins.str:
        result = self._values.get("tag_key")
        assert result is not None, "Required property 'tag_key' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def tag_values(self) -> typing.List[builtins.str]:
        result = self._values.get("tag_values")
        assert result is not None, "Required property 'tag_values' is missing"
        return typing.cast(typing.List[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "TargetResource(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-rds-database-auto-running-protection-stack.Timeout",
    jsii_struct_bases=[],
    name_mapping={"state_machine_timeout": "stateMachineTimeout"},
)
class Timeout:
    def __init__(
        self,
        *,
        state_machine_timeout: typing.Optional["_aws_cdk_ceddda9d.Duration"] = None,
    ) -> None:
        '''
        :param state_machine_timeout: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2f6d7d30a490abe7618ccb579da048c0686fd111cf14c38167582e977588dc29)
            check_type(argname="argument state_machine_timeout", value=state_machine_timeout, expected_type=type_hints["state_machine_timeout"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if state_machine_timeout is not None:
            self._values["state_machine_timeout"] = state_machine_timeout

    @builtins.property
    def state_machine_timeout(self) -> typing.Optional["_aws_cdk_ceddda9d.Duration"]:
        result = self._values.get("state_machine_timeout")
        return typing.cast(typing.Optional["_aws_cdk_ceddda9d.Duration"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Timeout(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "LogOption",
    "Notifications",
    "RDSDatabaseAutoRunningProtectionStack",
    "RDSDatabaseAutoRunningProtectionStackProps",
    "ResourceCustomNaming",
    "Slack",
    "TargetResource",
    "Timeout",
]

publication.publish()

def _typecheckingstub__0e695c65120a26566e3b1da2c283ffd65b205e848edf601c0e4413f96382028d(
    *,
    machine_log_level: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.LogLevel] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a1f97813ccd432edd13bc8e51df42efe9b6d3a01d26e99deaeb319cc9d58d204(
    *,
    emails: typing.Optional[typing.Sequence[builtins.str]] = None,
    slack: typing.Optional[typing.Union[Slack, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__983f6a01dacab988c39e7e1ead11de82110ca7e9d16eeed9b0d69ed44f9f5872(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    target_resource: typing.Union[TargetResource, typing.Dict[builtins.str, typing.Any]],
    enable_rule: typing.Optional[builtins.bool] = None,
    log_option: typing.Optional[typing.Union[LogOption, typing.Dict[builtins.str, typing.Any]]] = None,
    notifications: typing.Optional[typing.Union[Notifications, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_naming_option: typing.Optional[typing.Union[typing.Union[_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming, typing.Dict[builtins.str, typing.Any]], typing.Union[_gammarers_aws_resource_naming_22f917da.ResourceAutoNaming, typing.Dict[builtins.str, typing.Any]], typing.Union[ResourceCustomNaming, typing.Dict[builtins.str, typing.Any]]]] = None,
    timeout: typing.Optional[typing.Union[Timeout, typing.Dict[builtins.str, typing.Any]]] = None,
    analytics_reporting: typing.Optional[builtins.bool] = None,
    cross_region_references: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    env: typing.Optional[typing.Union[_aws_cdk_ceddda9d.Environment, typing.Dict[builtins.str, typing.Any]]] = None,
    permissions_boundary: typing.Optional[_aws_cdk_ceddda9d.PermissionsBoundary] = None,
    stack_name: typing.Optional[builtins.str] = None,
    suppress_template_indentation: typing.Optional[builtins.bool] = None,
    synthesizer: typing.Optional[_aws_cdk_ceddda9d.IStackSynthesizer] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    termination_protection: typing.Optional[builtins.bool] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__20eb7b10c40d8f8ab8440675658ba9a77a4d23f69f0bb794c3d5a6ee6f59e55f(
    *,
    analytics_reporting: typing.Optional[builtins.bool] = None,
    cross_region_references: typing.Optional[builtins.bool] = None,
    description: typing.Optional[builtins.str] = None,
    env: typing.Optional[typing.Union[_aws_cdk_ceddda9d.Environment, typing.Dict[builtins.str, typing.Any]]] = None,
    permissions_boundary: typing.Optional[_aws_cdk_ceddda9d.PermissionsBoundary] = None,
    stack_name: typing.Optional[builtins.str] = None,
    suppress_template_indentation: typing.Optional[builtins.bool] = None,
    synthesizer: typing.Optional[_aws_cdk_ceddda9d.IStackSynthesizer] = None,
    tags: typing.Optional[typing.Mapping[builtins.str, builtins.str]] = None,
    termination_protection: typing.Optional[builtins.bool] = None,
    target_resource: typing.Union[TargetResource, typing.Dict[builtins.str, typing.Any]],
    enable_rule: typing.Optional[builtins.bool] = None,
    log_option: typing.Optional[typing.Union[LogOption, typing.Dict[builtins.str, typing.Any]]] = None,
    notifications: typing.Optional[typing.Union[Notifications, typing.Dict[builtins.str, typing.Any]]] = None,
    resource_naming_option: typing.Optional[typing.Union[typing.Union[_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming, typing.Dict[builtins.str, typing.Any]], typing.Union[_gammarers_aws_resource_naming_22f917da.ResourceAutoNaming, typing.Dict[builtins.str, typing.Any]], typing.Union[ResourceCustomNaming, typing.Dict[builtins.str, typing.Any]]]] = None,
    timeout: typing.Optional[typing.Union[Timeout, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__b08fc47cfe2dc5c647800bb73a1a4d5d59d49aee7bb66da50baeadb9a2f4357f(
    *,
    start_cluster_event_catch_rule_name: builtins.str,
    start_event_catch_rule_role_name: builtins.str,
    start_instance_event_catch_rule_name: builtins.str,
    state_machine_name: builtins.str,
    state_machine_role_name: builtins.str,
    type: _gammarers_aws_resource_naming_22f917da.ResourceNamingType,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__cfac7c53e98ff15446c34e20d7e47a4148faaaa3b6384da25871e7fb8bd13bc8(
    *,
    webhook_secret_name: builtins.str,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4cee11dd8fd6f411fd9b19762c078370378e6b5b96bf7c81e75f94d9e94ab0ac(
    *,
    tag_key: builtins.str,
    tag_values: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2f6d7d30a490abe7618ccb579da048c0686fd111cf14c38167582e977588dc29(
    *,
    state_machine_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
) -> None:
    """Type checking stubs"""
    pass
