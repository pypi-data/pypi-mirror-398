r'''
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


class EC2InstanceRunningScheduleStack(
    _aws_cdk_ceddda9d.Stack,
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.EC2InstanceRunningScheduleStack",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        target_resource: typing.Union["TargetResource", typing.Dict[builtins.str, typing.Any]],
        log_option: typing.Optional[typing.Union["LogOption", typing.Dict[builtins.str, typing.Any]]] = None,
        notifications: typing.Optional[typing.Union["Notifications", typing.Dict[builtins.str, typing.Any]]] = None,
        start_schedule: typing.Optional[typing.Union["Schedule", typing.Dict[builtins.str, typing.Any]]] = None,
        stop_schedule: typing.Optional[typing.Union["Schedule", typing.Dict[builtins.str, typing.Any]]] = None,
        timeout: typing.Optional[typing.Union["Timeout", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param target_resource: 
        :param log_option: 
        :param notifications: 
        :param start_schedule: 
        :param stop_schedule: 
        :param timeout: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6e9fa8afb9b8a866557cd3e54deae940f017fba36efedf608f45c0e2ced78d8c)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = EC2InstanceRunningScheduleStackProps(
            target_resource=target_resource,
            log_option=log_option,
            notifications=notifications,
            start_schedule=start_schedule,
            stop_schedule=stop_schedule,
            timeout=timeout,
        )

        jsii.create(self.__class__, self, [scope, id, props])


@jsii.data_type(
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.EC2InstanceRunningScheduleStackProps",
    jsii_struct_bases=[],
    name_mapping={
        "target_resource": "targetResource",
        "log_option": "logOption",
        "notifications": "notifications",
        "start_schedule": "startSchedule",
        "stop_schedule": "stopSchedule",
        "timeout": "timeout",
    },
)
class EC2InstanceRunningScheduleStackProps:
    def __init__(
        self,
        *,
        target_resource: typing.Union["TargetResource", typing.Dict[builtins.str, typing.Any]],
        log_option: typing.Optional[typing.Union["LogOption", typing.Dict[builtins.str, typing.Any]]] = None,
        notifications: typing.Optional[typing.Union["Notifications", typing.Dict[builtins.str, typing.Any]]] = None,
        start_schedule: typing.Optional[typing.Union["Schedule", typing.Dict[builtins.str, typing.Any]]] = None,
        stop_schedule: typing.Optional[typing.Union["Schedule", typing.Dict[builtins.str, typing.Any]]] = None,
        timeout: typing.Optional[typing.Union["Timeout", typing.Dict[builtins.str, typing.Any]]] = None,
    ) -> None:
        '''
        :param target_resource: 
        :param log_option: 
        :param notifications: 
        :param start_schedule: 
        :param stop_schedule: 
        :param timeout: 
        '''
        if isinstance(target_resource, dict):
            target_resource = TargetResource(**target_resource)
        if isinstance(log_option, dict):
            log_option = LogOption(**log_option)
        if isinstance(notifications, dict):
            notifications = Notifications(**notifications)
        if isinstance(start_schedule, dict):
            start_schedule = Schedule(**start_schedule)
        if isinstance(stop_schedule, dict):
            stop_schedule = Schedule(**stop_schedule)
        if isinstance(timeout, dict):
            timeout = Timeout(**timeout)
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__bd3840ac0e638f51987f97cf9f08a0f261b6d0733de456d897c0f0c47d3d910f)
            check_type(argname="argument target_resource", value=target_resource, expected_type=type_hints["target_resource"])
            check_type(argname="argument log_option", value=log_option, expected_type=type_hints["log_option"])
            check_type(argname="argument notifications", value=notifications, expected_type=type_hints["notifications"])
            check_type(argname="argument start_schedule", value=start_schedule, expected_type=type_hints["start_schedule"])
            check_type(argname="argument stop_schedule", value=stop_schedule, expected_type=type_hints["stop_schedule"])
            check_type(argname="argument timeout", value=timeout, expected_type=type_hints["timeout"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "target_resource": target_resource,
        }
        if log_option is not None:
            self._values["log_option"] = log_option
        if notifications is not None:
            self._values["notifications"] = notifications
        if start_schedule is not None:
            self._values["start_schedule"] = start_schedule
        if stop_schedule is not None:
            self._values["stop_schedule"] = stop_schedule
        if timeout is not None:
            self._values["timeout"] = timeout

    @builtins.property
    def target_resource(self) -> "TargetResource":
        result = self._values.get("target_resource")
        assert result is not None, "Required property 'target_resource' is missing"
        return typing.cast("TargetResource", result)

    @builtins.property
    def log_option(self) -> typing.Optional["LogOption"]:
        result = self._values.get("log_option")
        return typing.cast(typing.Optional["LogOption"], result)

    @builtins.property
    def notifications(self) -> typing.Optional["Notifications"]:
        result = self._values.get("notifications")
        return typing.cast(typing.Optional["Notifications"], result)

    @builtins.property
    def start_schedule(self) -> typing.Optional["Schedule"]:
        result = self._values.get("start_schedule")
        return typing.cast(typing.Optional["Schedule"], result)

    @builtins.property
    def stop_schedule(self) -> typing.Optional["Schedule"]:
        result = self._values.get("stop_schedule")
        return typing.cast(typing.Optional["Schedule"], result)

    @builtins.property
    def timeout(self) -> typing.Optional["Timeout"]:
        result = self._values.get("timeout")
        return typing.cast(typing.Optional["Timeout"], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "EC2InstanceRunningScheduleStackProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.LogOption",
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
            type_hints = typing.get_type_hints(_typecheckingstub__283ad632a9bc210753cd28affe0193161f16c956a4ab28f37f5672ce2d2d6cf6)
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
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.Notifications",
    jsii_struct_bases=[],
    name_mapping={"emails": "emails"},
)
class Notifications:
    def __init__(
        self,
        *,
        emails: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param emails: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__8a238aacc87d45ffeb542f7d7cd8f00bb64d968f86d925a49062febf2929c562)
            check_type(argname="argument emails", value=emails, expected_type=type_hints["emails"])
        self._values: typing.Dict[builtins.str, typing.Any] = {}
        if emails is not None:
            self._values["emails"] = emails

    @builtins.property
    def emails(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("emails")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Notifications(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.Schedule",
    jsii_struct_bases=[],
    name_mapping={
        "timezone": "timezone",
        "hour": "hour",
        "minute": "minute",
        "week": "week",
    },
)
class Schedule:
    def __init__(
        self,
        *,
        timezone: builtins.str,
        hour: typing.Optional[builtins.str] = None,
        minute: typing.Optional[builtins.str] = None,
        week: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param timezone: 
        :param hour: 
        :param minute: 
        :param week: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__5cab99d4e24dd8c01f0d1b30619ac60b0c1df3da96be70369656b554128d5464)
            check_type(argname="argument timezone", value=timezone, expected_type=type_hints["timezone"])
            check_type(argname="argument hour", value=hour, expected_type=type_hints["hour"])
            check_type(argname="argument minute", value=minute, expected_type=type_hints["minute"])
            check_type(argname="argument week", value=week, expected_type=type_hints["week"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "timezone": timezone,
        }
        if hour is not None:
            self._values["hour"] = hour
        if minute is not None:
            self._values["minute"] = minute
        if week is not None:
            self._values["week"] = week

    @builtins.property
    def timezone(self) -> builtins.str:
        result = self._values.get("timezone")
        assert result is not None, "Required property 'timezone' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def hour(self) -> typing.Optional[builtins.str]:
        result = self._values.get("hour")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def minute(self) -> typing.Optional[builtins.str]:
        result = self._values.get("minute")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def week(self) -> typing.Optional[builtins.str]:
        result = self._values.get("week")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "Schedule(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


@jsii.data_type(
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.TargetResource",
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
            type_hints = typing.get_type_hints(_typecheckingstub__1b979250af53afa0059cdb56e2d1921b4b657918c69908def8757a96dd7b9304)
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
    jsii_type="@gammarers/aws-ec2-instance-running-schedule-stack.Timeout",
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
            type_hints = typing.get_type_hints(_typecheckingstub__e443e21596f4b708a59c6d9d0efd7802371d5ee514df49d4b9b9093cb57a58e8)
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
    "EC2InstanceRunningScheduleStack",
    "EC2InstanceRunningScheduleStackProps",
    "LogOption",
    "Notifications",
    "Schedule",
    "TargetResource",
    "Timeout",
]

publication.publish()

def _typecheckingstub__6e9fa8afb9b8a866557cd3e54deae940f017fba36efedf608f45c0e2ced78d8c(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    target_resource: typing.Union[TargetResource, typing.Dict[builtins.str, typing.Any]],
    log_option: typing.Optional[typing.Union[LogOption, typing.Dict[builtins.str, typing.Any]]] = None,
    notifications: typing.Optional[typing.Union[Notifications, typing.Dict[builtins.str, typing.Any]]] = None,
    start_schedule: typing.Optional[typing.Union[Schedule, typing.Dict[builtins.str, typing.Any]]] = None,
    stop_schedule: typing.Optional[typing.Union[Schedule, typing.Dict[builtins.str, typing.Any]]] = None,
    timeout: typing.Optional[typing.Union[Timeout, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__bd3840ac0e638f51987f97cf9f08a0f261b6d0733de456d897c0f0c47d3d910f(
    *,
    target_resource: typing.Union[TargetResource, typing.Dict[builtins.str, typing.Any]],
    log_option: typing.Optional[typing.Union[LogOption, typing.Dict[builtins.str, typing.Any]]] = None,
    notifications: typing.Optional[typing.Union[Notifications, typing.Dict[builtins.str, typing.Any]]] = None,
    start_schedule: typing.Optional[typing.Union[Schedule, typing.Dict[builtins.str, typing.Any]]] = None,
    stop_schedule: typing.Optional[typing.Union[Schedule, typing.Dict[builtins.str, typing.Any]]] = None,
    timeout: typing.Optional[typing.Union[Timeout, typing.Dict[builtins.str, typing.Any]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__283ad632a9bc210753cd28affe0193161f16c956a4ab28f37f5672ce2d2d6cf6(
    *,
    machine_log_level: typing.Optional[_aws_cdk_aws_stepfunctions_ceddda9d.LogLevel] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__8a238aacc87d45ffeb542f7d7cd8f00bb64d968f86d925a49062febf2929c562(
    *,
    emails: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__5cab99d4e24dd8c01f0d1b30619ac60b0c1df3da96be70369656b554128d5464(
    *,
    timezone: builtins.str,
    hour: typing.Optional[builtins.str] = None,
    minute: typing.Optional[builtins.str] = None,
    week: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1b979250af53afa0059cdb56e2d1921b4b657918c69908def8757a96dd7b9304(
    *,
    tag_key: builtins.str,
    tag_values: typing.Sequence[builtins.str],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e443e21596f4b708a59c6d9d0efd7802371d5ee514df49d4b9b9093cb57a58e8(
    *,
    state_machine_timeout: typing.Optional[_aws_cdk_ceddda9d.Duration] = None,
) -> None:
    """Type checking stubs"""
    pass
