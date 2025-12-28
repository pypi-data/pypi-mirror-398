r'''
# AWS SNS Slack Message Lambda Subscription

[![GitHub](https://img.shields.io/github/license/gammarers/aws-sns-slack-message-lambda-subscription?style=flat-square)](https://github.com/gammarers/aws-sns-slack-message-lambda-subscription/blob/main/LICENSE)
[![npm (scoped)](https://img.shields.io/npm/v/@gammarers/aws-sns-slack-message-lambda-subscription?style=flat-square)](https://www.npmjs.com/package/@gammarers/aws-sns-slack-message-lambda-subscription)
[![PyPI](https://img.shields.io/pypi/v/gammarers.aws-sns-slack-message-lambda-subscription?style=flat-square)](https://pypi.org/project/gammarers.aws-sns-slack-message-lambda-subscription/)
[![Nuget](https://img.shields.io/nuget/v/Gammarers.CDK.AWS.SNSSlackMessageLambdaSubscription?style=flat-square)](https://www.nuget.org/packages/Gammarers.CDK.AWS.SNSSlackMessageLambdaSubscription/)
[![GitHub Workflow Status (branch)](https://img.shields.io/github/actions/workflow/status/gammarers/aws-sns-slack-message-lambda-subscription/release.yml?branch=main&label=release&style=flat-square)](https://github.com/gammarers/aws-sns-slack-message-lambda-subscription/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/gammarers/aws-sns-slack-message-lambda-subscription?sort=semver&style=flat-square)](https://github.com/gammarers/aws-sns-slack-message-lambda-subscription/releases)

This AWS CDK Construct is designed to post messages sent from an SNS topic to a Slack Webhook via a Lambda function. The Lambda function accepts JSON text as a message, formats it for Slack, and sends it to the Slack Webhook API.

## Incoming Sample Message

![](./images/example.png)

## Installation

### TypeScript

#### install by npm

```shell
npm install @gammarers/aws-sns-slack-message-lambda-subscription
```

#### install by yarn

```shell
yarn add @gammarers/aws-sns-slack-message-lambda-subscription
```

### Python

```shell
pip install gammarers.aws-sns-slack-message-lambda-subscription
```

### C# / .NET

```shell
dotnet add package Gammarers.CDK.AWS.SNSSlackMessageLambdaSubscription
```

## Example

### Please save it in AWS Secrets Manager in the following format.

get your slack webhook url parts

```text
https://hooks.slack.com/services/<workspace>/<channel>/<whebook>
```

| SecretKey 	 | SecretValue 	   |
|-------------|-----------------|
| Workspace 	 | <workspace> 	 |
| Channel   	 | <channel>   	 |
| Webhook   	 | <whebook>   	 |

### Code

```python
import { SNSSlackMessageLambdaSubscription } from '@gammarer/aws-sns-slack-message-lambda-subscription';

declare const topic: sns.Topic;

new SNSSlackMessageLambdaSubscription(stack, 'SNSSlackMessageLambdaSubscription', {
  topic,
  slackWebhookSecretName: 'slak-webhook', // alredy saved slack webhook info.
});
```

```json
{
    "text": ":mega: *TEST*",
    "attachments": [{
        "color": "#2eb886",
        "title": "CodePipeline pipeline execution *SUCCEED*",
        "title_link": "https://github.com/yicr",
        "fields": [
            {
                "title": "Pipeline",
                "value": "pipeline-name"
            }
        ]
    }]
}
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

import aws_cdk.aws_sns as _aws_cdk_aws_sns_ceddda9d
import constructs as _constructs_77d1e7e8
import gammarers.aws_resource_naming as _gammarers_aws_resource_naming_22f917da


@jsii.data_type(
    jsii_type="@gammarers/aws-sns-slack-message-lambda-subscription.ResourceCustomNaming",
    jsii_struct_bases=[],
    name_mapping={
        "function_name": "functionName",
        "function_role_name": "functionRoleName",
        "type": "type",
    },
)
class ResourceCustomNaming:
    def __init__(
        self,
        *,
        function_name: builtins.str,
        function_role_name: builtins.str,
        type: "_gammarers_aws_resource_naming_22f917da.ResourceNamingType",
    ) -> None:
        '''
        :param function_name: 
        :param function_role_name: 
        :param type: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eceaaf51f4fef770856fa1cb8888228abc0e280ca1c0e736b5476de9fa5e7213)
            check_type(argname="argument function_name", value=function_name, expected_type=type_hints["function_name"])
            check_type(argname="argument function_role_name", value=function_role_name, expected_type=type_hints["function_role_name"])
            check_type(argname="argument type", value=type, expected_type=type_hints["type"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "function_name": function_name,
            "function_role_name": function_role_name,
            "type": type,
        }

    @builtins.property
    def function_name(self) -> builtins.str:
        result = self._values.get("function_name")
        assert result is not None, "Required property 'function_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def function_role_name(self) -> builtins.str:
        result = self._values.get("function_role_name")
        assert result is not None, "Required property 'function_role_name' is missing"
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


class SNSSlackMessageLambdaSubscription(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="@gammarers/aws-sns-slack-message-lambda-subscription.SNSSlackMessageLambdaSubscription",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        slack_webhook_secret_name: builtins.str,
        topic: "_aws_cdk_aws_sns_ceddda9d.ITopic",
        resource_naming_option: typing.Optional[typing.Union[typing.Union["ResourceCustomNaming", typing.Dict[builtins.str, typing.Any]], typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param slack_webhook_secret_name: 
        :param topic: 
        :param resource_naming_option: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3c2a51ce60a706686abad8be7da1cc2f2e7b9f9b51b825d76353d14db2f31582)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = SNSSlackMessageLambdaSubscriptionProps(
            slack_webhook_secret_name=slack_webhook_secret_name,
            topic=topic,
            resource_naming_option=resource_naming_option,
        )

        jsii.create(self.__class__, self, [scope, id, props])


@jsii.data_type(
    jsii_type="@gammarers/aws-sns-slack-message-lambda-subscription.SNSSlackMessageLambdaSubscriptionProps",
    jsii_struct_bases=[],
    name_mapping={
        "slack_webhook_secret_name": "slackWebhookSecretName",
        "topic": "topic",
        "resource_naming_option": "resourceNamingOption",
    },
)
class SNSSlackMessageLambdaSubscriptionProps:
    def __init__(
        self,
        *,
        slack_webhook_secret_name: builtins.str,
        topic: "_aws_cdk_aws_sns_ceddda9d.ITopic",
        resource_naming_option: typing.Optional[typing.Union[typing.Union["ResourceCustomNaming", typing.Dict[builtins.str, typing.Any]], typing.Union["_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming", typing.Dict[builtins.str, typing.Any]]]] = None,
    ) -> None:
        '''
        :param slack_webhook_secret_name: 
        :param topic: 
        :param resource_naming_option: 
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__e8cb1041f01bfb1ba61f3e9aec3eddb941ee9408cee2f907c7c2215261511803)
            check_type(argname="argument slack_webhook_secret_name", value=slack_webhook_secret_name, expected_type=type_hints["slack_webhook_secret_name"])
            check_type(argname="argument topic", value=topic, expected_type=type_hints["topic"])
            check_type(argname="argument resource_naming_option", value=resource_naming_option, expected_type=type_hints["resource_naming_option"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "slack_webhook_secret_name": slack_webhook_secret_name,
            "topic": topic,
        }
        if resource_naming_option is not None:
            self._values["resource_naming_option"] = resource_naming_option

    @builtins.property
    def slack_webhook_secret_name(self) -> builtins.str:
        result = self._values.get("slack_webhook_secret_name")
        assert result is not None, "Required property 'slack_webhook_secret_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def topic(self) -> "_aws_cdk_aws_sns_ceddda9d.ITopic":
        result = self._values.get("topic")
        assert result is not None, "Required property 'topic' is missing"
        return typing.cast("_aws_cdk_aws_sns_ceddda9d.ITopic", result)

    @builtins.property
    def resource_naming_option(
        self,
    ) -> typing.Optional[typing.Union["ResourceCustomNaming", "_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming"]]:
        result = self._values.get("resource_naming_option")
        return typing.cast(typing.Optional[typing.Union["ResourceCustomNaming", "_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming"]], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "SNSSlackMessageLambdaSubscriptionProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ResourceCustomNaming",
    "SNSSlackMessageLambdaSubscription",
    "SNSSlackMessageLambdaSubscriptionProps",
]

publication.publish()

def _typecheckingstub__eceaaf51f4fef770856fa1cb8888228abc0e280ca1c0e736b5476de9fa5e7213(
    *,
    function_name: builtins.str,
    function_role_name: builtins.str,
    type: _gammarers_aws_resource_naming_22f917da.ResourceNamingType,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3c2a51ce60a706686abad8be7da1cc2f2e7b9f9b51b825d76353d14db2f31582(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    slack_webhook_secret_name: builtins.str,
    topic: _aws_cdk_aws_sns_ceddda9d.ITopic,
    resource_naming_option: typing.Optional[typing.Union[typing.Union[ResourceCustomNaming, typing.Dict[builtins.str, typing.Any]], typing.Union[_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__e8cb1041f01bfb1ba61f3e9aec3eddb941ee9408cee2f907c7c2215261511803(
    *,
    slack_webhook_secret_name: builtins.str,
    topic: _aws_cdk_aws_sns_ceddda9d.ITopic,
    resource_naming_option: typing.Optional[typing.Union[typing.Union[ResourceCustomNaming, typing.Dict[builtins.str, typing.Any]], typing.Union[_gammarers_aws_resource_naming_22f917da.ResourceDefaultNaming, typing.Dict[builtins.str, typing.Any]]]] = None,
) -> None:
    """Type checking stubs"""
    pass
