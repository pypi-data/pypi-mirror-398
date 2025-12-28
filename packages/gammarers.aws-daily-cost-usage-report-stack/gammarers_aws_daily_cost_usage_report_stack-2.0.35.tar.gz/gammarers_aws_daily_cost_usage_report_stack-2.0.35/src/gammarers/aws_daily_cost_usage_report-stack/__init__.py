r'''
# AWS Daily Cost Usage Report Stack

[![GitHub](https://img.shields.io/github/license/gammarers/aws-daily-cost-usage-report-stack?style=flat-square)](https://github.com/gammarers/aws-daily-cost-usage-report-stack/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-daily-cost-usage-report-stack?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-daily-cost-usage-report-stack)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-daily-cost-usage-report-stack?style=flat-square)](https://pypi.org/project/gammarers.aws-daily-cost-usage-report-stack/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-daily-cost-usage-report-stack/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-daily-cost-usage-report-stack/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-daily-cost-usage-report-stack?sort=semver&style=flat-square)](https://github.com/gammarers/aws-daily-cost-usage-report-stack/releases)

AWS Cost And Usage report to Slack on daily 09:01.

* Report type

  * Services

    * This is Cost by AWS Services.
  * Accounts

    * This is Cost by Linked Account (when organization master account)

## Resources

This construct creating resource list.

* Lambda function execution role
* Lambda function
* EventBridge Scheduler execution role
* EventBridge Scheduler

## Install

### TypeScript

#### use by npm

```shell
npm install @gammarers/aws-daily-cost-usage-report-stack
```

#### use by yarn

```shell
yarn add @gammarers/aws-daily-cost-usage-report-stack
```

### Python

```shell
pip install gammarers.aws-daily-cost-usage-report-stack
```

## Example

```shell
npm install @gammarers/aws-daily-cost-usage-report-stack
```

```python
import { CostGroupType, DailyCostUsageReportStack } from '@gammarer/aws-daily-cost-usage-report-stack';

new DailyCostUsageReportStack(app, 'DailyCostUsageReportStack', {
  slackToken: 'xoxb-11111111111-XXXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX',
  slackChannel: 'example-channel',
  costGroupType: CostGroupType.SERVICES,
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
import constructs as _constructs_77d1e7e8


@jsii.enum(jsii_type="@gammarers/aws-daily-cost-usage-report-stack.CostGroupType")
class CostGroupType(enum.Enum):
    ACCOUNTS = "ACCOUNTS"
    SERVICES = "SERVICES"


class DailyCostUsageReportStack(
    _aws_cdk_ceddda9d.Stack,
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-daily-cost-usage-report-stack.DailyCostUsageReportStack",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        cost_group_type: "CostGroupType",
        slack_channel: builtins.str,
        slack_token: builtins.str,
        schedule_timezone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param cost_group_type: 
        :param slack_channel: 
        :param slack_token: 
        :param schedule_timezone: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2ada65ca4f4b40187091fc62325d3467fd6f065f964b49c8acb808bade62a151)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = DailyCostUsageReportStackProps(
            cost_group_type=cost_group_type,
            slack_channel=slack_channel,
            slack_token=slack_token,
            schedule_timezone=schedule_timezone,
        )

        jsii.create(self.__class__, self, [scope, id, props])


@jsii.data_type(
    jsii_type="@gammarers/aws-daily-cost-usage-report-stack.DailyCostUsageReportStackProps",
    jsii_struct_bases=[],
    name_mapping={
        "cost_group_type": "costGroupType",
        "slack_channel": "slackChannel",
        "slack_token": "slackToken",
        "schedule_timezone": "scheduleTimezone",
    },
)
class DailyCostUsageReportStackProps:
    def __init__(
        self,
        *,
        cost_group_type: "CostGroupType",
        slack_channel: builtins.str,
        slack_token: builtins.str,
        schedule_timezone: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param cost_group_type: 
        :param slack_channel: 
        :param slack_token: 
        :param schedule_timezone: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__a262b8bcfa6f9f7c8dc4650e84ed3e52b48326be80ba6eb38d930f731ce870f5)
            check_type(argname="argument cost_group_type", value=cost_group_type, expected_type=type_hints["cost_group_type"])
            check_type(argname="argument slack_channel", value=slack_channel, expected_type=type_hints["slack_channel"])
            check_type(argname="argument slack_token", value=slack_token, expected_type=type_hints["slack_token"])
            check_type(argname="argument schedule_timezone", value=schedule_timezone, expected_type=type_hints["schedule_timezone"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cost_group_type": cost_group_type,
            "slack_channel": slack_channel,
            "slack_token": slack_token,
        }
        if schedule_timezone is not None:
            self._values["schedule_timezone"] = schedule_timezone

    @builtins.property
    def cost_group_type(self) -> "CostGroupType":
        result = self._values.get("cost_group_type")
        assert result is not None, "Required property 'cost_group_type' is missing"
        return typing.cast("CostGroupType", result)

    @builtins.property
    def slack_channel(self) -> builtins.str:
        result = self._values.get("slack_channel")
        assert result is not None, "Required property 'slack_channel' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def slack_token(self) -> builtins.str:
        result = self._values.get("slack_token")
        assert result is not None, "Required property 'slack_token' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def schedule_timezone(self) -> typing.Optional[builtins.str]:
        result = self._values.get("schedule_timezone")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "DailyCostUsageReportStackProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "CostGroupType",
    "DailyCostUsageReportStack",
    "DailyCostUsageReportStackProps",
]

publication.publish()

def _typecheckingstub__2ada65ca4f4b40187091fc62325d3467fd6f065f964b49c8acb808bade62a151(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    cost_group_type: CostGroupType,
    slack_channel: builtins.str,
    slack_token: builtins.str,
    schedule_timezone: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__a262b8bcfa6f9f7c8dc4650e84ed3e52b48326be80ba6eb38d930f731ce870f5(
    *,
    cost_group_type: CostGroupType,
    slack_channel: builtins.str,
    slack_token: builtins.str,
    schedule_timezone: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
