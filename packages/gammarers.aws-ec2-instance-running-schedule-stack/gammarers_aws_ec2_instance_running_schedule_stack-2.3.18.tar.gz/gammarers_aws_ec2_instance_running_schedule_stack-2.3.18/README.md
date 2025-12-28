# AWS EC2 Instance Running Schedule Stack

[![GitHub](https://img.shields.io/github/license/gammarers/aws-ec2-instance-running-schedule-stack?style=flat-square)](https://github.com/gammarers/aws-ec2-instance-running-schedule-stack/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-ec2-instance-running-schedule-stack?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-ec2-instance-running-schedule-stack)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-ec2-instance-running-schedule-stack?style=flat-square)](https://pypi.org/project/gammarers.aws-ec2-instance-running-schedule-stack/)
[![Nuget](https://img.shields.io/nuget/v/Gammarers.CDK.AWS.EC2InstanceRunningScheduleStack?style=flat-square)](https://www.nuget.org/packages/Gammarers.CDK.AWS.EC2InstanceRunningScheduleStack/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-ec2-instance-running-schedule-stack/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-ec2-instance-running-schedule-stack/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-ec2-instance-running-schedule-stack?sort=semver&style=flat-square)](https://github.com/gammarers/aws-ec2-instance-running-schedule-stack/releases)

[![View on Construct Hub](https://constructs.dev/badge?package=@gammarers/aws-ec2-instance-running-schedule-stack)](https://constructs.dev/packages/@gammarers/aws-ec2-instance-running-schedule-stack)

This is an AWS CDK Construct to make EC2 instance running schedule (only running while working hours(start/stop)).

## Fixed

* EC2 Instance

## Resources

This construct creating resource list.

* EventBridge Scheduler execution role
* EventBridge Scheduler
* Step Functions State machine
* Step Functions State machine role

## State Machine Execution Flow

![](./images/state-machine.png)

## Install

### TypeScript

#### install by npm

```shell
npm install @gammarer/aws-ec2-instance-running-schedule-stack
```

#### install by yarn

```shell
yarn add @gammarer/aws-ec2-instance-running-schedule-stack
```

### Python

```shell
pip install gammarer.aws-ec2-instance-running-schedule-stack
```

### C# / .NET

```shell
dotnet add package Gammarer.CDK.AWS.Ec2InstanceRunningScheduleStack
```

## Example

```python
import { Ec2InstanceRunningScheduleStack } from '@gammarer/aws-ec2-instance-running-schedule-stack';

new EC2InstanceRunningScheduleStack(app, 'EC2InstanceRunningScheduleStack', {
  targetResource: {
    tagKey: 'WorkHoursRunning',
    tagValues: ['YES'],
  },
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
  notifications: { // OPTIONAL NOTIFICATION
    emails: [  // OPTIONAL SEND EMAIL FROM SNS
      'foo@example.com',
      'bar@example.net',
    ],
  },
});
```

## License

This project is licensed under the Apache-2.0 License.
