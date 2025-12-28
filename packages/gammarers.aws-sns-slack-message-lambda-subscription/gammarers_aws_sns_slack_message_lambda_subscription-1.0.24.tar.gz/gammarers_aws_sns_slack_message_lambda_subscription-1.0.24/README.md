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
