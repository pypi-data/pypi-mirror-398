import json
import setuptools

kwargs = json.loads(
    """
{
    "name": "gammarers.aws-sns-slack-message-lambda-subscription",
    "version": "1.0.24",
    "description": "This AWS CDK Construct is designed to post messages sent from an SNS topic to a Slack Webhook via a Lambda function.",
    "license": "Apache-2.0",
    "url": "https://github.com/gammarers/aws-sns-slack-message-lambda-subscription.git",
    "long_description_content_type": "text/markdown",
    "author": "yicr<yicr@users.noreply.github.com>",
    "bdist_wheel": {
        "universal": true
    },
    "project_urls": {
        "Source": "https://github.com/gammarers/aws-sns-slack-message-lambda-subscription.git"
    },
    "package_dir": {
        "": "src"
    },
    "packages": [
        "gammarers.aws_sns_slack_message_lambda_subscription",
        "gammarers.aws_sns_slack_message_lambda_subscription._jsii"
    ],
    "package_data": {
        "gammarers.aws_sns_slack_message_lambda_subscription._jsii": [
            "aws-sns-slack-message-lambda-subscription@1.0.24.jsii.tgz"
        ],
        "gammarers.aws_sns_slack_message_lambda_subscription": [
            "py.typed"
        ]
    },
    "python_requires": "~=3.9",
    "install_requires": [
        "aws-cdk-lib>=2.189.1, <3.0.0",
        "constructs>=10.0.5, <11.0.0",
        "gammarers.aws-resource-naming>=0.10.1, <0.11.0",
        "jsii>=1.122.0, <2.0.0",
        "publication>=0.0.3",
        "typeguard==2.13.3"
    ],
    "classifiers": [
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Typing :: Typed",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved"
    ],
    "scripts": []
}
"""
)

with open("README.md", encoding="utf8") as fp:
    kwargs["long_description"] = fp.read()


setuptools.setup(**kwargs)
