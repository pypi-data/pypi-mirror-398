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
