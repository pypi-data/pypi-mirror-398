# AWS RDS Database Running Schedule Stack

[![GitHub](https://img.shields.io/github/license/gammarers/aws-rds-database-running-schedule-stack?style=flat-square)](https://github.com/gammarers/aws-rds-database-running-schedule-stack/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-rds-database-running-schedule-stack?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-rds-database-running-schedule-stack)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-rds-database-running-schedule-stack?style=flat-square)](https://pypi.org/project/gammarers.aws-rds-database-running-schedule-stack/)
[![Nuget](https://img.shields.io/nuget/v/Gammarers.CDK.AWS.RdsDatabaseRunningScheduleStack?style=flat-square)](https://www.nuget.org/packages/Gammarers.CDK.AWS.RdsDatabaseRunningScheduleStack/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-rds-database-running-schedule-stack/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-rds-database-running-schedule-stack/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-rds-database-running-schedule-stack?sort=semver&style=flat-square)](https://github.com/gammarers/aws-rds-database-running-schedule-stack/releases)

[![View on Construct Hub](https://constructs.dev/badge?package=@gammarers/aws-rds-database-running-schedule-stack)](https://constructs.dev/packages/@gammarers/aws-rds-database-running-schedule-stack)

This AWS CDK Construct Stack controls the starting and stopping of RDS DB instances and clusters based on specified tags, ensuring they only run during working hours. It uses EventBridge Scheduler to trigger a StepFunctions State Machine at the start and end of the working hours(default 07:50(UTC) - 21:10(UTC)), which then starts or stops the databases depending on the mode.

> [!WARNING]
> v2.3.0:
> Stack props add option resourceNamingOption
> default ResourceNamingType.DEFAULT is cdk generated name
> f you want to maintain compatibility with versions below `v2.3.0`, please include the following settings (ResourceNamingType.AUTO).
>
> ```python
> new RDSDatabaseRunningScheduleStack(app, 'RDSDatabaseRunningScheduleStack', {
>   targetResource: {
>     tagKey: 'WorkHoursRunning',
>     tagValues: ['YES'],
>   },
>   resourceNamingOption: {
>     type: ResourceNamingType.AUTO, // HERE
>   },
> });
> ```

## Fixed

* RDS Aurora Cluster
* RDS Instance

## Resources

This construct creating resource list.

* EventBridge Scheduler execution role
* EventBridge Scheduler
* StepFunctions StateMahcine (star or stop controle)
* StepFunctions StateMahcine execution role

## Install

### TypeScript

#### install by npm

```shell
npm install @gammarers/aws-rds-database-running-schedule-stack
```

#### install by yarn

```shell
yarn add @gammarers/aws-rds-database-running-schedule-stack
```

#### install by pnpm

```shell
pnpm add @gammarers/aws-rds-database-running-schedule-stack
```

#### install by bun

```shell
bun add @gammarers/aws-rds-database-running-schedule-stack
```

### Python

```shell
pip install gammarers.aws-rds-database-running-schedule-stack
```

### C# / .NET

```shell
dotnet add package Gammarers.CDK.AWS.RdsDatabaseRunningScheduleStack
```

## Example

```python
import { RDSDatabaseRunningScheduleStack, ResourceNamingType } from '@gammarer/aws-rds-database-running-schedule-stack';

new RDSDatabaseRunningScheduleStack(app, 'RDSDatabaseRunningScheduleStack', {
  targetResource: {
    tagKey: 'WorkHoursRunning', // already tagging to rds instance or cluster
    tagValues: ['YES'], // already tagging to rds instance or cluster
  },
  enableScheduling: true,
  startSchedule: {
    timezone: 'Asia/Tokyo',
    minute: '55',
    hour: '8',
    week: 'MON-FRI',
  },
  stopSchedule: {
    timezone: 'Asia/Tokyo',
    minute: '5',
    hour: '19',
    week: 'MON-FRI',
  },
  resourceNamingOption: {
    type: ResourceNamingType.AUTO, // DEFAULT or AUTO or CUSTOM
  },
  notifications: {
    emails: [ // "Incoming Sample Message - EMAIL"
      'foo@example.com',
      'bar@example.net',
    ],
    slack: { // "Incoming Sample Message - EMAIL"
      webhookSecretName: 'example/slack/webhook',
    },
  },
});
```

## Incoming Sample Message

### EMAIL

![](./images/example-email.png)

### Slack

![](./images/example-slack.png)

## License

This project is licensed under the Apache-2.0 License.
