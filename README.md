# CDK Use Cases
The CDK Use Cases library is an open-source collection of AWS Cloud Development Kit (AWS CDK) uses cases.

## Table of Contents

1. [About this library](#about-this-library)
2. [Module naming](#module-naming)
4. [Security](#security)
5. [License](#license)

## About this library

This library provides multi-service, well-architected patterns for quickly defining solutions in code. The goal of CDK Use Cases is to accelerate the experience for developers to build solutions. The patterns included in this library are not [AWS Solutions Constructs](https://github.com/awslabs/aws-solutions-constructs), and have been built using [JSii](https://github.com/aws/jsii) to expose their functionality in multiple languages.

The patterns defined in CDK Use Cases are high level, multi-service abstractions of AWS CDK constructs that have default configurations based on well-architected best practices. The library is organized into logical modules using object-oriented techniques to create each architectural pattern model.

Here you will not find resources to learn how to use CDK or general coding examples. For that, take a look at [AWS CDK Examples](https://github.com/aws-samples/aws-cdk-examples).

## Module naming

The CDK Use Cases library is organized into several modules, each one covering a specific use case. The module name indicates the services it involves. For example, `custom-cloud9-ssm` deploys a Cloud9 environment and applies a configuration to its EC2 instance using an SSM Document.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

***

© Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.

