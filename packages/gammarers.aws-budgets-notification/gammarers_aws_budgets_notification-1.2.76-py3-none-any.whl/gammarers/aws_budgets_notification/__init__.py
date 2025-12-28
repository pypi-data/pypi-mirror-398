r'''
# AWS Budgets Notification

[![GitHub](https://img.shields.io/github/license/gammarers/aws-budgets-notification?style=flat-square)](https://github.com/gammarers/aws-budgets-notification/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-budgets-notification?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-budgets-notification)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-budgets-notification?style=flat-square)](https://pypi.org/project/gammarers.aws-budgets-notification/)
[![Nuget](https://img.shields.io/nuget/v/gammarers.CDK.AWS.BudgetNotification?style=flat-square)](https://www.nuget.org/packages/Gammarers.CDK.AWS.BudgetNotification/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-budgets-notification/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-budgets-notification/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-budgets-notification?sort=semver&style=flat-square)](https://github.com/gammarers/aws-budgets-notification/releases)

[![View on Construct Hub](https://constructs.dev/badge?package=@gammarers/aws-budgets-notification)](https://constructs.dev/packages/@gammarers/aws-budgets-notification)

A construct library for creating AWS Budgets Notification to Slack with the AWS CDK.

## Resources

This construct creating resource list.

* SNS Topic
* ChatBot SlackChannelConfiguration
* Budgets (linked account count or self)

## Install

### TypeScript

```shell
npm install @gammarers/aws-budgets-notification
# or
yarn add @gammarers/aws-budgets-notification
```

### Python

```shell
pip install gammarers.aws-budgets-notification
```

### C# / .NET

```shell
dotnet add package Gammarers.CDK.AWS.BudgetNotification
```

## Example

```python
import { BudgetsNotification } from '@gammarers/aws-budgets-notification';

new BudgetsNotification(stack, 'BudgetsNotification', {
  slackWorkspaceId: 'T0XXXX111', // already AWS account linked your Slack.
  slackChannelId: 'XXXXXXXX', // already created your slack channel.
  budgetLimitAmount: 50,
  // optional linked account list
  linkedAccounts: [
    '111111111111',
    '222222222222',
  ],
});
```

![example notification](./docs/slack-notification-image.png)

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

import constructs as _constructs_77d1e7e8


class BudgetsNotification(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-budgets-notification.BudgetsNotification",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        budget_limit_amount: jsii.Number,
        slack_channel_id: builtins.str,
        slack_workspace_id: builtins.str,
        linked_accounts: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param budget_limit_amount: 
        :param slack_channel_id: 
        :param slack_workspace_id: 
        :param linked_accounts: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__b3189bfbcfeb78ae3e4a91d7fdfc5ecf9417a65a40cfe6d316b58792d33b51e0)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = BudgetsNotificationProps(
            budget_limit_amount=budget_limit_amount,
            slack_channel_id=slack_channel_id,
            slack_workspace_id=slack_workspace_id,
            linked_accounts=linked_accounts,
        )

        jsii.create(self.__class__, self, [scope, id, props])


@jsii.data_type(
    jsii_type="@gammarers/aws-budgets-notification.BudgetsNotificationProps",
    jsii_struct_bases=[],
    name_mapping={
        "budget_limit_amount": "budgetLimitAmount",
        "slack_channel_id": "slackChannelId",
        "slack_workspace_id": "slackWorkspaceId",
        "linked_accounts": "linkedAccounts",
    },
)
class BudgetsNotificationProps:
    def __init__(
        self,
        *,
        budget_limit_amount: jsii.Number,
        slack_channel_id: builtins.str,
        slack_workspace_id: builtins.str,
        linked_accounts: typing.Optional[typing.Sequence[builtins.str]] = None,
    ) -> None:
        '''
        :param budget_limit_amount: 
        :param slack_channel_id: 
        :param slack_workspace_id: 
        :param linked_accounts: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__550eb1b0cfb784d610323b7c558fae15b0500dee994b1f56fa2b5fb176fce52b)
            check_type(argname="argument budget_limit_amount", value=budget_limit_amount, expected_type=type_hints["budget_limit_amount"])
            check_type(argname="argument slack_channel_id", value=slack_channel_id, expected_type=type_hints["slack_channel_id"])
            check_type(argname="argument slack_workspace_id", value=slack_workspace_id, expected_type=type_hints["slack_workspace_id"])
            check_type(argname="argument linked_accounts", value=linked_accounts, expected_type=type_hints["linked_accounts"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "budget_limit_amount": budget_limit_amount,
            "slack_channel_id": slack_channel_id,
            "slack_workspace_id": slack_workspace_id,
        }
        if linked_accounts is not None:
            self._values["linked_accounts"] = linked_accounts

    @builtins.property
    def budget_limit_amount(self) -> jsii.Number:
        result = self._values.get("budget_limit_amount")
        assert result is not None, "Required property 'budget_limit_amount' is missing"
        return typing.cast(jsii.Number, result)

    @builtins.property
    def slack_channel_id(self) -> builtins.str:
        result = self._values.get("slack_channel_id")
        assert result is not None, "Required property 'slack_channel_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def slack_workspace_id(self) -> builtins.str:
        result = self._values.get("slack_workspace_id")
        assert result is not None, "Required property 'slack_workspace_id' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def linked_accounts(self) -> typing.Optional[typing.List[builtins.str]]:
        result = self._values.get("linked_accounts")
        return typing.cast(typing.Optional[typing.List[builtins.str]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "BudgetsNotificationProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "BudgetsNotification",
    "BudgetsNotificationProps",
]

publication.publish()

def _typecheckingstub__b3189bfbcfeb78ae3e4a91d7fdfc5ecf9417a65a40cfe6d316b58792d33b51e0(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    budget_limit_amount: jsii.Number,
    slack_channel_id: builtins.str,
    slack_workspace_id: builtins.str,
    linked_accounts: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__550eb1b0cfb784d610323b7c558fae15b0500dee994b1f56fa2b5fb176fce52b(
    *,
    budget_limit_amount: jsii.Number,
    slack_channel_id: builtins.str,
    slack_workspace_id: builtins.str,
    linked_accounts: typing.Optional[typing.Sequence[builtins.str]] = None,
) -> None:
    """Type checking stubs"""
    pass
